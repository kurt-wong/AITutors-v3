"""Phase 0.3-B Experiment: Source-Grounded Option Label Resolution.

用 548 个真实 skipped choice-type units 验证：
  options_region → Source marker detection → labels → per-label spans

实验规则（冻结）：
  1. 输入仅为 preprocessing 已提供的 options_region
  2. 不从 question_type 生成 labels
  3. labels 必须来自该 region 的实际 Source marker
  4. 复用现有 option_tokens / _label_offsets 的检测逻辑
  5. 不允许 equal split / 长度猜测 / LLM
  6. 无法确定 → unresolved / ambiguous
  7. 不修改 V3 production code
  8. 不写生产数据库

用法：
    cd backend
    python -m scripts.preprocessing_consumer.runner_b3 \
        --corpus "D:/Project/Papers/Ocr-markdown/reslice-p2-b1"
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.domains.resolver.match_normalization import normalize_text, option_tokens

from .manifest_reader import find_manifests, load_manifest
from .source_loader import load_source_lines

# 与 resolver.py:56 一致
_LABEL_RE = re.compile(r"(?<![\w])([A-Ha-h])\s*[.．、:)）]")

_CHOICE_TYPES = {"single_choice", "multiple_choice", "true_false"}


def _detect_labels_in_region(lines, start: int, end: int) -> list[str]:
    """从 options_region 的 Source 文本中检测实际存在的 option label markers。

    两阶段检测：
    1. 行首 marker（option_tokens，与 _line_has_option_token 一致）
    2. 同行 inline marker（_LABEL_RE，仅在已有行首 marker 的行上检测）

    返回按 Source 出现顺序排列的 unique labels。
    """
    labels: list[str] = []
    for line_no in range(start, min(end + 1, len(lines) + 1)):
        text = lines[line_no - 1].text
        norm = normalize_text(text)
        # 阶段 1：行首 marker
        for lab in "ABCDEFGH":
            if lab in option_tokens(norm, (lab,)) and lab not in labels:
                labels.append(lab)
        # 阶段 2：同行 inline marker（仅在本行已有行首 marker 时检测）
        line_has_start_marker = any(
            lab in option_tokens(norm, (lab,)) for lab in "ABCDEFGH"
        )
        if line_has_start_marker:
            for m in _LABEL_RE.finditer(text):
                lab = m.group(1).upper()
                if lab not in labels:
                    labels.append(lab)
    return labels


def _locate_labels_in_region(lines, start: int, end: int, labels: list[str]) -> dict:
    """在 options_region 内逐 label 定位（复用 _locate_options 的算法）。

    返回 {label: {"status": "ok"|"inline"|"ambiguous"|"incomplete",
                  "line_ref": str|None, "start_offset": int|None, "end_offset": int|None}}
    """
    found: dict[str, dict] = {}
    cursor_line = start  # 1-based

    for lab in labels:
        # 行首匹配
        starts = []
        for line_no in range(cursor_line, end + 1):
            norm = normalize_text(lines[line_no - 1].text)
            if lab in option_tokens(norm, (lab,)):
                starts.append(line_no)

        if len(starts) == 1:
            found[lab] = {
                "status": "ok",
                "line_ref": f"P1L{starts[0]:03d}",
                "start_offset": None,
                "end_offset": None,
                "line_no": starts[0],
            }
            cursor_line = starts[0]
            continue

        if len(starts) > 1:
            found[lab] = {"status": "ambiguous", "line_ref": None,
                          "start_offset": None, "end_offset": None}
            continue

        # Inline: 在前一个 option 行内查找
        if cursor_line >= start:
            text = lines[cursor_line - 1].text
            offs = [m.start() for m in _LABEL_RE.finditer(text)
                    if m.group(1).upper() == lab.upper()]
            if len(offs) == 1:
                found[lab] = {
                    "status": "inline",
                    "line_ref": f"P1L{cursor_line:03d}",
                    "start_offset": offs[0],
                    "end_offset": offs[0] + len(lab),
                    "line_no": cursor_line,
                }
                continue

        found[lab] = {"status": "incomplete", "line_ref": None,
                      "start_offset": None, "end_offset": None}

    return found


def _classify_result(detected: list[str], located: dict, start: int, end: int,
                     lines) -> str:
    """分类实验结果。"""
    if not detected:
        return "no_labels"
    if any(l["status"] == "ambiguous" for l in located.values()):
        return "ambiguous"
    if any(l["status"] == "incomplete" for l in located.values()):
        return "incomplete"
    # 全部 ok 或 inline
    # 检查顺序：label 在 Source 中应按字母顺序出现
    positions = []
    for lab in detected:
        entry = located[lab]
        pos = entry.get("line_no", 0) * 10000 + (entry.get("start_offset") or 0)
        positions.append(pos)
    if positions != sorted(positions):
        return "invalid_order"
    # 检查 span 是否都在 region 内
    for lab in detected:
        entry = located[lab]
        ln = entry.get("line_no", 0)
        if ln and (ln < start or ln > end):
            return "out_of_region"
    return "resolved"


def run_experiment(corpus_root: Path, output_path: Path):
    manifests = find_manifests(corpus_root)
    print(f"Found {len(manifests)} manifests")

    report = {
        "experiment": "phase0.3-b-option-label-resolution",
        "corpus": str(corpus_root),
        "total_manifests": len(manifests),
        "rules": [
            "input: options_region from preprocessing manifest only",
            "labels: detected from Source markers within region",
            "no question_type-based label generation",
            "no equal split / length guess / LLM",
            "unresolvable -> unresolved/ambiguous",
            "no V3 production code modification",
        ],
        "summary": {},
        "units": [],
    }

    summary = Counter()

    for i, mpath in enumerate(manifests):
        paper_id = mpath.stem.replace(".manifest", "")
        try:
            manifest = load_manifest(mpath)
        except Exception as exc:
            report["units"].append({"paper": paper_id, "error": f"manifest: {exc}"})
            continue

        source_path = Path(manifest.source_file)
        if not source_path.exists():
            report["units"].append({"paper": paper_id, "error": "source not found"})
            continue

        try:
            source_lines = load_source_lines(source_path)
        except Exception as exc:
            report["units"].append({"paper": paper_id, "error": f"source: {exc}"})
            continue

        for unit in manifest.units:
            if unit.original_question_type not in _CHOICE_TYPES:
                continue
            if not unit.options_lines:
                continue  # 32 个结构缺失不在本实验范围

            start, end = unit.options_lines
            n_lines = len(source_lines)
            if start < 1 or end > n_lines or start > end:
                result = "out_of_bounds"
                detected = []
                located = {}
            else:
                detected = _detect_labels_in_region(source_lines, start, end)
                located = _locate_labels_in_region(source_lines, start, end, detected)
                result = _classify_result(detected, located, start, end, source_lines)

            # 提取 Source 文本用于人工抽查
            region_text = []
            for ln in range(start, min(end + 1, n_lines + 1)):
                region_text.append(f"L{ln:03d}: {source_lines[ln - 1].text}")

            entry = {
                "paper": paper_id,
                "unit_id": unit.unit_id,
                "question_type": unit.original_question_type,
                "options_region": [start, end],
                "detected_labels": detected,
                "result": result,
                "located": located,
                "region_text": region_text,
            }
            report["units"].append(entry)
            summary[result] += 1

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(manifests)}] processed...")

    # 序列化
    report["summary"] = dict(summary)
    total = sum(summary.values())
    report["total_choice_units_with_region"] = total

    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n{'='*60}")
    print(f"Phase 0.3-B Experiment Results")
    print(f"{'='*60}")
    print(f"Total choice-type units with options_region: {total}")
    print()
    for k, v in sorted(summary.items(), key=lambda x: -x[1]):
        pct = v / total * 100 if total else 0
        print(f"  {k:20s}: {v:4d} ({pct:.1f}%)")
    print(f"\nReport: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 0.3-B: Source-Grounded Option Label Resolution"
    )
    parser.add_argument("--corpus", type=Path,
                        default=Path(r"D:\Project\Papers\Ocr-markdown\reslice-p2-b1"))
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "consumer-report-b3.json")
    args = parser.parse_args()
    run_experiment(args.corpus, args.output)


if __name__ == "__main__":
    main()
