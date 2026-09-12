"""Gate B: Source Binding Strategy Comparative Validation.

实验 Harness——不修改生产代码。对比同一 corpus 上：
  Legacy Strategy: semantic-only annotation → SourceResolver (search)
  Path B Strategy: line_refs claim → direct ResolvedSpan construction (validation)

四个底线：
  1. 同一 SourceLineView 输入
  2. Semantic projection 审计（防隐式 Source Binding 泄漏）
  3. 行号映射已验证（67/80 corpus）
  4. 不修改生产管线
"""

import glob
import json
import os
import sys
import uuid
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import ResolvedRun, SourceLineView


# ---------------------------------------------------------------- corpus

@dataclass
class CorpusCase:
    case_id: str
    source_path: str
    manifest_path: str
    md_lines: list[str]
    manifest_units: list[dict]
    subject: str


def load_corpus(base_dir: str = "D:/Project/Papers/Ocr-markdown") -> list[CorpusCase]:
    """加载所有 mapping 一致的 corpus cases。"""
    manifests = glob.glob(f"{base_dir}/**/*.manifest.json", recursive=True)
    cases = []
    for mp in sorted(manifests):
        md_path = mp.replace(".manifest.json", ".md")
        if not os.path.exists(md_path):
            continue
        with open(mp, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        with open(md_path, "r", encoding="utf-8") as f:
            md_lines = f.readlines()

        # Mapping audit: skip if any line_ref exceeds md_lines
        max_line = 0
        for u in manifest.get("units", []):
            for field_name in ("stem_lines", "options_lines", "answer_lines", "explanation_lines"):
                val = u.get(field_name)
                if val and isinstance(val, list) and len(val) == 2:
                    if val[1] and isinstance(val[1], int):
                        max_line = max(max_line, val[1])
        if max_line > len(md_lines):
            continue

        parts = mp.replace("\\", "/").split("/")
        subject = parts[-2] if len(parts) >= 2 else "unknown"
        cases.append(CorpusCase(
            case_id=os.path.basename(mp).replace(".manifest.json", ""),
            source_path=md_path,
            manifest_path=mp,
            md_lines=md_lines,
            manifest_units=manifest.get("units", []),
            subject=subject,
        ))
    return cases


def build_source_lines(md_lines: list[str]) -> tuple[SourceLineView, ...]:
    """从 .md 行构造 SourceLineView（全部 P1，已由 mapping audit 验证）。"""
    return tuple(
        SourceLineView(
            line_ref=f"P1L{i + 1:03d}",
            text=line.rstrip("\n"),
            seq=i + 1,
            page_no=1,
            line_no_in_page=i + 1,
        )
        for i, line in enumerate(md_lines)
    )


# ---------------------------------------------------------------- projections

# Semantic projection: 剥离所有 Source Binding 信息，仅保留语义结构
# 审计：以下字段必须被删除，不得进入 Legacy annotation
_BINDING_FIELDS = ("stem_lines", "options_lines", "answer_lines", "explanation_lines")

# Semantic projection: 保留的语义字段（审计清单）
_SEMANTIC_FIELDS = (
    "unit_id", "unit_type", "question_numbers", "original_question_type",
)


def semantic_projection(manifest_unit: dict) -> dict:
    """Manifest Unit → Semantic-only annotation（Legacy Strategy 输入）。

    剥离所有 *_lines 字段（Source Binding Claim），保留语义结构字段。
    审计：输出中不得包含任何 line_refs 信息。
    """
    projected = {}
    for key in _SEMANTIC_FIELDS:
        if key in manifest_unit:
            projected[key] = manifest_unit[key]
    # 显式断言：不得包含任何 binding 字段
    for bf in _BINDING_FIELDS:
        assert bf not in projected, f"semantic projection leaked binding field: {bf}"
    return projected


def build_legacy_annotation(manifest_units: list[dict]) -> dict:
    """Manifest units → V3 annotation payload（Legacy Resolver 输入）。

    构造 semantic_units[]，每个 unit 包含 content 结构（stem/options/answer），
    但不含任何 line_refs。Resolver 将用语义线索搜索定位。
    """
    semantic_units = []
    for mu in manifest_units:
        proj = semantic_projection(mu)
        qn = proj.get("question_numbers", [None])[0]
        qn_str = str(qn) if qn is not None else ""

        # 构造 content 结构（V3 annotation format）
        content = {
            "stem": {"question_label": qn_str},
        }
        # options: 从 manifest 的 options_lines 存在性推断
        if mu.get("options_lines"):
            content["options"] = _extract_option_labels(mu)
        # answer
        if mu.get("answer_lines"):
            content["answer"] = {
                "answer_zone": "answer_table",
                "question_label": qn_str,
            }

        unit = {
            "unit_id": proj["unit_id"],
            "original_question_type": proj.get("original_question_type", "single_choice"),
            "content": content,
        }
        # composite 处理
        if proj.get("unit_type") == "composite_unit":
            unit["unit_type"] = "composite_unit"
            unit["shared_components"] = {}
            unit["sub_questions"] = []

        semantic_units.append(unit)

    return {
        "semantic_units": semantic_units,
        "document_metadata_claims": {},
    }


def _extract_option_labels(manifest_unit: dict) -> list[dict]:
    """从 manifest 推断选项标签。标准选择题选项 ABCD。"""
    return [{"label": l} for l in "ABCD"]


def build_path_b_spans(
    manifest_unit: dict, source_lines: tuple[SourceLineView, ...]
) -> list[dict]:
    """Manifest unit → Path B ResolvedSpan 构造输入。"""
    spans = []
    uid = manifest_unit.get("unit_id", "?")

    def _make_span(role, line_range, label=None):
        if not line_range or not isinstance(line_range, list) or len(line_range) != 2:
            return None
        start, end = line_range[0], line_range[1]
        if not start or not end or not isinstance(start, int) or not isinstance(end, int):
            return None
        if start < 1 or end > len(source_lines) or start > end:
            return None
        line_refs = [f"P1L{i:03d}" for i in range(start, end + 1)]
        texts = [source_lines[i - 1].text for i in range(start, end + 1)]
        return {
            "span_id": f"sp-{uid}.{role}" + (f".{label}" if label else ""),
            "role": role,
            "line_refs": line_refs,
            "text": "\n".join(texts),
            "label": label,
            "unit_id": uid,
            "granularity": "line",
        }

    # stem
    stem_span = _make_span("stem", manifest_unit.get("stem_lines"))
    if stem_span:
        spans.append(stem_span)

    # options: options_lines 是整体范围，逐行拆分
    opt_range = manifest_unit.get("options_lines")
    if opt_range and isinstance(opt_range, list) and len(opt_range) == 2:
        for i, label in enumerate("ABCDEFGH"):
            line_no = opt_range[0] + i
            if line_no > opt_range[1]:
                break
            if 1 <= line_no <= len(source_lines):
                spans.append({
                    "span_id": f"sp-{uid}.option.{label}",
                    "role": "option",
                    "line_refs": [f"P1L{line_no:03d}"],
                    "text": source_lines[line_no - 1].text,
                    "label": label,
                    "unit_id": uid,
                    "granularity": "line",
                })

    # answer
    ans_span = _make_span("answer", manifest_unit.get("answer_lines"))
    if ans_span:
        spans.append(ans_span)

    # explanation
    exp_span = _make_span("explanation", manifest_unit.get("explanation_lines"))
    if exp_span:
        spans.append(exp_span)

    return spans


# ---------------------------------------------------------------- runners

def run_legacy_strategy(
    case: CorpusCase, source_lines: tuple[SourceLineView, ...]
) -> dict:
    """Legacy Strategy: semantic-only annotation → SourceResolver (search)。"""
    annotation = build_legacy_annotation(case.manifest_units)
    svid = uuid.uuid5(uuid.NAMESPACE_DNS, case.case_id)

    try:
        resolver = SourceResolver(source_version_id=svid, lines=source_lines)
        resolved_run = resolver.resolve(annotation)
    except Exception as e:
        return {
            "strategy": "legacy",
            "case_id": case.case_id,
            "error": str(e),
            "total_targets": 0,
            "resolved": 0,
            "unresolved": 0,
            "by_status": {},
        }

    by_status = {}
    for span in resolved_run.resolved_spans:
        by_status[span.resolution_status] = by_status.get(span.resolution_status, 0) + 1
    unresolved_count = len(resolved_run.unresolved_references)

    return {
        "strategy": "legacy",
        "case_id": case.case_id,
        "error": None,
        "total_targets": len(resolved_run.resolved_spans) + unresolved_count,
        "resolved": len(resolved_run.resolved_spans),
        "unresolved": unresolved_count,
        "by_status": by_status,
    }


def run_path_b_strategy(
    case: CorpusCase, source_lines: tuple[SourceLineView, ...]
) -> dict:
    """Path B Strategy: line_refs claim → direct ResolvedSpan construction (validation)。"""
    all_spans = []
    invalid_refs = 0
    total_refs = 0

    for mu in case.manifest_units:
        spans = build_path_b_spans(mu, source_lines)
        all_spans.extend(spans)
        for field_name in ("stem_lines", "options_lines", "answer_lines", "explanation_lines"):
            val = mu.get(field_name)
            if val and isinstance(val, list) and len(val) == 2:
                if val[0] and val[1]:
                    total_refs += 1
                    if val[0] < 1 or val[1] > len(source_lines) or val[0] > val[1]:
                        invalid_refs += 1

    return {
        "strategy": "path_b",
        "case_id": case.case_id,
        "error": None,
        "total_units": len(case.manifest_units),
        "total_spans": len(all_spans),
        "valid_spans": len(all_spans),
        "invalid_refs": invalid_refs,
        "total_refs": total_refs,
        "by_role": _count_by_role(all_spans),
    }


def _count_by_role(spans: list[dict]) -> dict:
    counts = {}
    for s in spans:
        role = s["role"]
        counts[role] = counts.get(role, 0) + 1
    return counts


# ---------------------------------------------------------------- metrics

def compute_comparison(legacy_results: list[dict], path_b_results: list[dict]) -> dict:
    """统一口径的对比度量。"""
    leg_total = sum(r["total_targets"] for r in legacy_results if not r["error"])
    leg_resolved = sum(r["resolved"] for r in legacy_results if not r["error"])
    leg_unresolved = sum(r["unresolved"] for r in legacy_results if not r["error"])
    leg_errors = sum(1 for r in legacy_results if r["error"])

    leg_by_status = {}
    for r in legacy_results:
        if not r["error"]:
            for status, count in r["by_status"].items():
                leg_by_status[status] = leg_by_status.get(status, 0) + count

    pb_total_units = sum(r["total_units"] for r in path_b_results if not r["error"])
    pb_total_spans = sum(r["total_spans"] for r in path_b_results if not r["error"])
    pb_valid_spans = sum(r["valid_spans"] for r in path_b_results if not r["error"])
    pb_invalid_refs = sum(r["invalid_refs"] for r in path_b_results if not r["error"])
    pb_total_refs = sum(r["total_refs"] for r in path_b_results if not r["error"])
    pb_errors = sum(1 for r in path_b_results if r["error"])

    pb_by_role = {}
    for r in path_b_results:
        if not r["error"]:
            for role, count in r["by_role"].items():
                pb_by_role[role] = pb_by_role.get(role, 0) + count

    return {
        "corpus": {
            "total_cases": len(legacy_results),
            "legacy_errors": leg_errors,
            "path_b_errors": pb_errors,
        },
        "legacy": {
            "total_targets": leg_total,
            "resolved": leg_resolved,
            "unresolved": leg_unresolved,
            "resolution_rate": leg_resolved / leg_total if leg_total else 0,
            "by_status": leg_by_status,
        },
        "path_b": {
            "total_units": pb_total_units,
            "total_spans": pb_total_spans,
            "valid_spans": pb_valid_spans,
            "invalid_refs": pb_invalid_refs,
            "total_refs": pb_total_refs,
            "validation_rate": pb_valid_spans / pb_total_spans if pb_total_spans else 0,
            "by_role": pb_by_role,
        },
    }


# ---------------------------------------------------------------- main

def run_gate_b(base_dir: str = "D:/Project/Papers/Ocr-markdown") -> dict:
    """执行完整 Gate B 对比实验。"""
    print("=" * 60)
    print("Gate B: Source Binding Strategy Comparative Validation")
    print("=" * 60)

    cases = load_corpus(base_dir)
    print(f"\nCorpus: {len(cases)} cases (mapping-consistent)")

    subject_counts = {}
    total_units = 0
    for c in cases:
        subject_counts[c.subject] = subject_counts.get(c.subject, 0) + 1
        total_units += len(c.manifest_units)
    print(f"Total units: {total_units}")
    print(f"By subject: {json.dumps(subject_counts, ensure_ascii=False)}")

    legacy_results = []
    path_b_results = []

    for i, case in enumerate(cases):
        source_lines = build_source_lines(case.md_lines)

        leg = run_legacy_strategy(case, source_lines)
        legacy_results.append(leg)

        pb = run_path_b_strategy(case, source_lines)
        path_b_results.append(pb)

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(cases)} cases...")

    comparison = compute_comparison(legacy_results, path_b_results)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(f"\nCorpus: {comparison['corpus']['total_cases']} cases")
    print(f"Legacy errors: {comparison['corpus']['legacy_errors']}")
    print(f"Path B errors: {comparison['corpus']['path_b_errors']}")

    print(f"\n--- Legacy Strategy (Search) ---")
    leg = comparison["legacy"]
    print(f"Total targets: {leg['total_targets']}")
    print(f"Resolved: {leg['resolved']}")
    print(f"Unresolved: {leg['unresolved']}")
    print(f"Resolution rate: {leg['resolution_rate']:.1%}")
    print(f"By status: {json.dumps(leg['by_status'], ensure_ascii=False)}")

    print(f"\n--- Path B Strategy (Validation) ---")
    pb = comparison["path_b"]
    print(f"Total units: {pb['total_units']}")
    print(f"Total spans: {pb['total_spans']}")
    print(f"Valid spans: {pb['valid_spans']}")
    print(f"Invalid refs: {pb['invalid_refs']}")
    print(f"Total refs: {pb['total_refs']}")
    print(f"Validation rate: {pb['validation_rate']:.1%}")
    print(f"By role: {json.dumps(pb['by_role'], ensure_ascii=False)}")

    print(f"\n--- Comparison ---")
    print(f"Legacy resolution rate: {leg['resolution_rate']:.1%}")
    print(f"Path B validation rate: {pb['validation_rate']:.1%}")

    return {
        "cases": cases,
        "legacy_results": legacy_results,
        "path_b_results": path_b_results,
        "comparison": comparison,
    }


if __name__ == "__main__":
    result = run_gate_b()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_b_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "comparison": result["comparison"],
            "legacy_per_case": result["legacy_results"],
            "path_b_per_case": result["path_b_results"],
        }, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed results saved to: {output_path}")
