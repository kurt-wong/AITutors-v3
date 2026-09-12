"""B2-B1 对抗验证：解析结果 vs 源文本逐项比对。

不是检查解析器输出的结构性质，而是把解析结果与源文本并排比对，
确认每个 option 的 text 是否忠实于源。

验证方法：
  1. 对每个抽样 case，输出源文本行
  2. 输出解析器产出的 option 列表
  3. 检查：解析出的所有 text 是否都能在源文本中找到对应内容
  4. 检查：源文本中的 option label 是否都被解析器捕获
  5. 检查：是否有 text 被错误拆分或合并
"""

import json
import os
import random
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate_b2b1_option_region import (
    load_corpus,
    parse_options_region,
)


def adversarial_verify(case, uid, region, parsed):
    """对抗性验证：解析结果是否忠实于源文本。

    返回 (pass, detail, raw_source, parsed_summary)。
    """
    start, end = region
    raw = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
    joined = "\n".join(raw)

    issues = []

    # ---- Check 1: 源文本中每个 option label 是否都被捕获 ----
    stripped = re.sub(r"<[^>]+>", " ", joined)
    independent_labels = set()
    for line in stripped.split("\n"):
        line = line.strip()
        if not line:
            continue
        # 行首 label（不要求 delimiter 后有空格）
        m = re.match(r"^[（(\[]?([A-H])[）)\]]?[.、．:：)）]", line)
        if m:
            independent_labels.add(m.group(1))
        # 行内 label（前面有空格，不要求后面有空格）
        for m in re.finditer(r"\s([A-H])[.、．:：)]", line):
            independent_labels.add(m.group(1))
        # 括号格式 (A) (B) (C) (D)
        for m in re.finditer(r"\(([A-H])\)", line):
            independent_labels.add(m.group(1))

    parsed_labels = set(p.label for p in parsed)
    missing_labels = independent_labels - parsed_labels
    if missing_labels:
        issues.append(f"missing_labels: {sorted(missing_labels)}")

    # ---- Check 2: 解析出的 text 是否能在源文本中找到 ----
    normalized_source = re.sub(r"\s+", "", stripped)
    for p in parsed:
        normalized_text = re.sub(r"\s+", "", p.text)
        if normalized_text and normalized_text not in normalized_source:
            words = [w for w in re.split(r"[\s,，。；;]+", p.text) if len(w) > 1]
            missing_words = [w for w in words if re.sub(r"\s+", "", w) not in normalized_source]
            if missing_words:
                issues.append(f"text_not_in_source[{p.label}]: missing {missing_words[:3]}")

    # ---- Check 3: 内容覆盖率 ----
    # 只计算非 label 的文本内容，剔除 label 开销
    source_content = re.sub(r"[（(\[]?[A-H][）)\]]?[.、．:：)）]", "", stripped)
    source_text_len = len(re.sub(r"\s+", "", source_content))
    parsed_text_len = sum(len(re.sub(r"\s+", "", p.text)) for p in parsed)
    if source_text_len > 0:
        coverage = parsed_text_len / source_text_len
        if coverage < 0.3:
            issues.append(f"low_coverage: {coverage:.1%} ({parsed_text_len}/{source_text_len})")

    # ---- Check 4: phantom labels ----
    phantom = parsed_labels - independent_labels
    if phantom:
        issues.append(f"phantom_labels: {sorted(phantom)}")

    passed = len(issues) == 0
    detail = "; ".join(issues) if issues else "ok"
    return passed, detail, raw, parsed


def main():
    base_dir = "D:/Project/Papers/Ocr-markdown"
    cases = load_corpus(base_dir)

    successful = []
    for case in cases:
        for mu in case.manifest_units:
            uid = mu.get("unit_id", "?")
            opt = mu.get("options_lines")
            if not opt or not isinstance(opt, list) or len(opt) != 2 or not opt[0] or not opt[1]:
                continue
            start, end = opt[0], opt[1]
            if start < 1 or end > len(case.md_lines) or start > end:
                continue
            raw = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
            joined = "\n".join(raw)
            if "<table" in joined.lower() or "<img" in joined.lower() or "<div" in joined.lower():
                continue
            parsed = parse_options_region(case.md_lines, start, end)
            if len(parsed) >= 2:
                successful.append((case, uid, [start, end], parsed))

    print(f"Non-HTML successful parses: {len(successful)}")

    random.seed(123)
    sample_size = min(50, len(successful))
    samples = random.sample(successful, sample_size)

    results = []
    for case, uid, region, parsed in samples:
        passed, detail, raw, _ = adversarial_verify(case, uid, region, parsed)
        results.append({
            "case_id": case.case_id,
            "unit_id": uid,
            "region": region,
            "passed": passed,
            "detail": detail,
            "raw_lines": raw,
            "parsed": [{"label": p.label, "text": p.text[:80]} for p in parsed],
        })

    passed_count = sum(1 for r in results if r["passed"])
    print(f"\nAdversarial verification: {passed_count}/{sample_size} pass "
          f"({passed_count/sample_size:.1%})")

    fail_reasons = {}
    for r in results:
        if not r["passed"]:
            for issue in r["detail"].split("; "):
                key = issue.split(":")[0].split("[")[0]
                fail_reasons[key] = fail_reasons.get(key, 0) + 1

    print(f"\nFailure reasons:")
    for reason, count in sorted(fail_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")

    failed = [r for r in results if not r["passed"]]
    print(f"\n{'='*60}")
    print(f"FAILED CASES ({len(failed)}) — source vs parsed")
    print(f"{'='*60}")
    for r in failed:
        print(f"\n--- {r['case_id']}/{r['unit_id']} ---")
        print(f"  Issues: {r['detail']}")
        print(f"  Source:")
        for line in r["raw_lines"][:6]:
            print(f"    | {line[:90]}")
        print(f"  Parsed:")
        for p in r["parsed"]:
            print(f"    {p['label']}. {p['text']}")

    passed_cases = [r for r in results if r["passed"]][:5]
    print(f"\n{'='*60}")
    print(f"PASSED CASES (sample 5) — for comparison")
    print(f"{'='*60}")
    for r in passed_cases:
        print(f"\n--- {r['case_id']}/{r['unit_id']} ---")
        print(f"  Source:")
        for line in r["raw_lines"][:6]:
            print(f"    | {line[:90]}")
        print(f"  Parsed:")
        for p in r["parsed"]:
            print(f"    {p['label']}. {p['text']}")

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_b2b1_adversarial.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "sample_size": sample_size,
            "passed": passed_count,
            "pass_rate": passed_count / sample_size if sample_size else 0,
            "failure_reasons": fail_reasons,
            "failed_cases": failed,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
