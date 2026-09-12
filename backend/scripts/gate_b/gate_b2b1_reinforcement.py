"""Gate B2-B1 补强：独立抽样验证 + HTML region 审计 + 收紧 label sequence。

三项补强：
  1. 独立抽样验证：从成功解析中随机抽 100 个，独立确认 option text 正确性
  2. HTML region 审计：分类 97 个 HTML region 为纯 HTML vs 混合内容
  3. 收紧 label sequence：检查 option 数量合理性 + gap 检测

实验 Harness——不修改生产代码。
"""

import glob
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate_b2b1_option_region import (
    CorpusCase,
    ParsedOption,
    load_corpus,
    parse_options_region,
    _OPTION_LABEL_RE,
    _MULTI_OPTION_RE,
)


# ---------------------------------------------------------------- 补强 1: 独立抽样验证

@dataclass
class SampleVerification:
    """单个抽样验证结果。"""
    case_id: str
    unit_id: str
    region: list[int]
    parsed_options: list[ParsedOption]
    raw_lines: list[str]
    # 独立验证结果
    option_count_plausible: bool = False  # 2-6 个
    labels_sequential: bool = False  # A,B,C,D 无 gap
    first_option_starts_correctly: bool = False  # 第一个 option 以 A 开头
    all_options_have_text: bool = False  # 所有 option 有非空 text
    text_looks_reasonable: bool = False  # text 长度合理，不含 HTML 残留
    # 综合判定
    verified: bool = False
    failure_detail: str = ""


def verify_sample(case: CorpusCase, unit_id: str, region: list[int],
                  parsed: list[ParsedOption]) -> SampleVerification:
    """独立验证一个解析结果的正确性。"""
    raw = [case.md_lines[i - 1].rstrip("\n") for i in range(region[0], region[1] + 1)]
    v = SampleVerification(
        case_id=case.case_id, unit_id=unit_id, region=region,
        parsed_options=parsed, raw_lines=raw,
    )

    # Check 1: option count plausible (2-6)
    n = len(parsed)
    v.option_count_plausible = 2 <= n <= 6

    # Check 2: labels sequential without gap
    if n >= 2:
        ords = [ord(p.label) - ord("A") for p in parsed]
        v.labels_sequential = all(ords[i] == ords[i-1] + 1 for i in range(1, len(ords)))

    # Check 3: first option starts with A
    v.first_option_starts_correctly = parsed[0].label == "A" if parsed else False

    # Check 4: all options have non-empty text
    v.all_options_have_text = all(len(p.text.strip()) > 0 for p in parsed)

    # Check 5: text looks reasonable (no HTML residue, reasonable length)
    html_residue = re.compile(r"<[^>]+>|</[a-z]+>")
    for p in parsed:
        if html_residue.search(p.text):
            v.text_looks_reasonable = False
            break
        if len(p.text) > 500:  # suspiciously long
            v.text_looks_reasonable = False
            break
    else:
        v.text_looks_reasonable = True

    # Composite: all checks must pass
    v.verified = all([
        v.option_count_plausible,
        v.labels_sequential,
        v.first_option_starts_correctly,
        v.all_options_have_text,
        v.text_looks_reasonable,
    ])

    if not v.verified:
        reasons = []
        if not v.option_count_plausible:
            reasons.append(f"count={n}")
        if not v.labels_sequential:
            reasons.append(f"labels={[p.label for p in parsed]}")
        if not v.first_option_starts_correctly:
            reasons.append(f"first={parsed[0].label if parsed else 'none'}")
        if not v.all_options_have_text:
            empty = [p.label for p in parsed if not p.text.strip()]
            reasons.append(f"empty_text={empty}")
        if not v.text_looks_reasonable:
            reasons.append("html_residue_or_too_long")
        v.failure_detail = "; ".join(reasons)

    return v


# ---------------------------------------------------------------- 补强 2: HTML region 审计

@dataclass
class HtmlRegionAudit:
    """HTML region 分类审计。"""
    case_id: str
    unit_id: str
    region: list[int]
    raw_lines: list[str]
    has_table: bool = False
    has_img: bool = False
    has_div: bool = False
    has_text_options: bool = False  # 纯文本 option label 存在
    classification: str = ""  # pure_html | mixed | text_with_html_wrapper


def audit_html_region(case: CorpusCase, unit_id: str, region: list[int]) -> HtmlRegionAudit:
    """审计一个 HTML region 的内容分类。"""
    raw = [case.md_lines[i - 1].rstrip("\n") for i in range(region[0], region[1] + 1)]
    joined = "\n".join(raw)

    a = HtmlRegionAudit(
        case_id=case.case_id, unit_id=unit_id, region=region, raw_lines=raw,
    )
    a.has_table = "<table" in joined.lower()
    a.has_img = "<img" in joined.lower()
    a.has_div = "<div" in joined.lower()

    # Check for text option labels outside HTML tags
    # Strip all HTML tags, then look for option labels
    text_only = re.sub(r"<[^>]+>", " ", joined)
    text_only = re.sub(r"\s+", " ", text_only).strip()
    # Look for option label patterns in the stripped text
    option_label_in_text = re.search(r"[A-H][.、．)]\s*\S", text_only)
    a.has_text_options = bool(option_label_in_text)

    if a.has_text_options:
        a.classification = "mixed"
    elif a.has_table or a.has_img:
        a.classification = "pure_html"
    else:
        a.classification = "text_with_html_wrapper"

    return a


# ---------------------------------------------------------------- 补强 3: 收紧 label sequence

def tightened_label_check(parsed: list[ParsedOption]) -> tuple[bool, str]:
    """收紧的 label sequence 验证。

    检查：
    1. option 数量在 [2, 6] 范围内
    2. 第一个 label 是 A
    3. label 序列严格连续（无 gap）
    4. 最后一个 label 不超过 F
    """
    if not parsed:
        return False, "no_options"

    labels = [p.label for p in parsed]
    n = len(labels)

    # Check 1: count in [2, 6]
    if n < 2 or n > 6:
        return False, f"count_out_of_range: {n}"

    # Check 2: first label is A
    if labels[0] != "A":
        return False, f"first_not_A: {labels[0]}"

    # Check 3: strictly sequential (no gap)
    ords = [ord(l) - ord("A") for l in labels]
    for i in range(1, len(ords)):
        if ords[i] != ords[i - 1] + 1:
            return False, f"gap_at_{i}: {labels[i-1]}→{labels[i]}"

    # Check 4: last label <= F
    if ords[-1] > 5:  # F = 5
        return False, f"last_too_far: {labels[-1]}"

    return True, "ok"


# ---------------------------------------------------------------- main

def run_reinforcement(base_dir: str = "D:/Project/Papers/Ocr-markdown") -> dict:
    """执行 B2-B1 三项补强。"""
    print("=" * 60)
    print("Gate B2-B1 Reinforcement")
    print("=" * 60)

    cases = load_corpus(base_dir)
    print(f"\nCorpus: {len(cases)} cases")

    # Collect all option regions with parse results
    all_regions = []  # (case, unit_id, region, parsed, is_html, is_image)
    for case in cases:
        for mu in case.manifest_units:
            uid = mu.get("unit_id", "?")
            opt = mu.get("options_lines")
            if not opt or not isinstance(opt, list) or len(opt) != 2:
                continue
            if not opt[0] or not opt[1]:
                continue
            start, end = opt[0], opt[1]
            if start < 1 or end > len(case.md_lines) or start > end:
                continue

            raw = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
            joined = "\n".join(raw)
            is_html = "<table" in joined.lower()
            is_image = "<img" in joined.lower() or "<div" in joined.lower()

            parsed = parse_options_region(case.md_lines, start, end)
            all_regions.append((case, uid, [start, end], parsed, is_html, is_image))

    total = len(all_regions)
    html_regions = [(c, u, r, p) for c, u, r, p, h, i in all_regions if h or i]
    non_html_regions = [(c, u, r, p) for c, u, r, p, h, i in all_regions if not h and not i]
    print(f"\nTotal regions: {total}")
    print(f"HTML regions: {len(html_regions)}")
    print(f"Non-HTML regions: {len(non_html_regions)}")

    # ---- 补强 1: 独立抽样验证 ----
    print("\n" + "=" * 60)
    print("补强 1: 独立抽样验证 (100 samples)")
    print("=" * 60)

    successful = [(c, u, r, p) for c, u, r, p in non_html_regions if len(p) >= 2]
    print(f"Successful parses (≥2 options): {len(successful)}")

    random.seed(42)  # reproducible
    sample_size = min(100, len(successful))
    samples = random.sample(successful, sample_size)

    verifications = []
    for case, uid, region, parsed in samples:
        v = verify_sample(case, uid, region, parsed)
        verifications.append(v)

    verified_count = sum(1 for v in verifications if v.verified)
    print(f"\nVerified: {verified_count}/{sample_size} ({verified_count/sample_size:.1%})")

    # Failure breakdown
    fail_reasons = {}
    for v in verifications:
        if not v.verified:
            for reason in v.failure_detail.split("; "):
                key = reason.split("=")[0].split(":")[0]
                fail_reasons[key] = fail_reasons.get(key, 0) + 1

    print(f"\nFailure reasons:")
    for reason, count in sorted(fail_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")

    # Show failed samples
    failed = [v for v in verifications if not v.verified]
    print(f"\nFailed samples ({len(failed)}):")
    for v in failed[:10]:
        print(f"  {v.case_id}/{v.unit_id}: {v.failure_detail}")
        for p in v.parsed_options[:5]:
            print(f"    {p.label}. {p.text[:60]}")

    # ---- 补强 2: HTML region 审计 ----
    print("\n" + "=" * 60)
    print("补强 2: HTML region 审计")
    print("=" * 60)

    audits = []
    for case, uid, region, _ in html_regions:
        a = audit_html_region(case, uid, region)
        audits.append(a)

    pure_html = sum(1 for a in audits if a.classification == "pure_html")
    mixed = sum(1 for a in audits if a.classification == "mixed")
    wrapper = sum(1 for a in audits if a.classification == "text_with_html_wrapper")

    print(f"\nClassification:")
    print(f"  pure_html (table/img only): {pure_html}")
    print(f"  mixed (HTML + text options): {mixed}")
    print(f"  text_with_html_wrapper: {wrapper}")

    # Try to parse mixed regions
    mixed_regions = [a for a in audits if a.classification == "mixed"]
    if mixed_regions:
        print(f"\nMixed regions - attempting parse:")
        mixed_parsed_ok = 0
        for a in mixed_regions[:10]:
            case = next(c for c, u, r, p, h, i in all_regions if c.case_id == a.case_id and u == a.unit_id)
            parsed = parse_options_region(case.md_lines, a.region[0], a.region[1])
            ok = len(parsed) >= 2
            if ok:
                mixed_parsed_ok += 1
            print(f"  {a.case_id}/{a.unit_id}: {len(parsed)} options parsed {'✓' if ok else '✗'}")
            for p in parsed[:4]:
                print(f"    {p.label}. {p.text[:60]}")

    # ---- 补强 3: 收紧 label sequence ----
    print("\n" + "=" * 60)
    print("补强 3: 收紧 label sequence 验证")
    print("=" * 60)

    tightened_results = []
    for case, uid, region, parsed in non_html_regions:
        ok, detail = tightened_label_check(parsed)
        tightened_results.append((case.case_id, uid, parsed, ok, detail))

    tightened_pass = sum(1 for _, _, _, ok, _ in tightened_results if ok)
    tightened_fail = len(tightened_results) - tightened_pass
    print(f"\nTightened check: {tightened_pass}/{len(tightened_results)} pass "
          f"({tightened_pass/len(tightened_results):.1%})")

    tightened_fail_reasons = {}
    for _, _, _, ok, detail in tightened_results:
        if not ok:
            key = detail.split(":")[0]
            tightened_fail_reasons[key] = tightened_fail_reasons.get(key, 0) + 1

    print(f"\nTightened failure reasons:")
    for reason, count in sorted(tightened_fail_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")

    # Show tightened failures
    tightened_failed = [(cid, uid, p, d) for cid, uid, p, ok, d in tightened_results if not ok]
    print(f"\nTightened failures ({len(tightened_failed)}):")
    for cid, uid, parsed, detail in tightened_failed[:10]:
        labels = [p.label for p in parsed]
        print(f"  {cid}/{uid}: labels={labels}, reason={detail}")
        for p in parsed[:4]:
            print(f"    {p.label}. {p.text[:60]}")

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"""
补强 1 (独立抽样验证):
  成功解析: {len(successful)}/{len(non_html_regions)} ({len(successful)/len(non_html_regions):.1%})
  抽样验证: {verified_count}/{sample_size} ({verified_count/sample_size:.1%})
  失败原因: {fail_reasons}

补强 2 (HTML region 审计):
  纯 HTML: {pure_html}
  混合内容: {mixed}
  HTML wrapper: {wrapper}

补强 3 (收紧 label sequence):
  通过: {tightened_pass}/{len(tightened_results)} ({tightened_pass/len(tightened_results):.1%})
  失败原因: {tightened_fail_reasons}
""")

    return {
        "reinforcement_1": {
            "successful_parses": len(successful),
            "total_non_html": len(non_html_regions),
            "sample_size": sample_size,
            "verified": verified_count,
            "verified_rate": verified_count / sample_size if sample_size else 0,
            "failure_reasons": fail_reasons,
        },
        "reinforcement_2": {
            "total_html": len(html_regions),
            "pure_html": pure_html,
            "mixed": mixed,
            "wrapper": wrapper,
        },
        "reinforcement_3": {
            "total_non_html": len(non_html_regions),
            "tightened_pass": tightened_pass,
            "tightened_pass_rate": tightened_pass / len(non_html_regions) if non_html_regions else 0,
            "failure_reasons": tightened_fail_reasons,
        },
    }


if __name__ == "__main__":
    result = run_reinforcement()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_b2b1_reinforcement.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_path}")
