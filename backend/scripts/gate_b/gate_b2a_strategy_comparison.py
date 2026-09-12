"""Gate B2-A: Strategy Comparison on Clean Roles (stem + explanation).

在 B1-clean 的 common target set 上对比 Legacy Resolver（search）与 Path B（validation）。

对比单位：(case_id, unit_id, role) — 仅 stem 和 explanation。
两条路径使用相同 SourceLineView、相同 semantic projection。

实验 Harness——不修改生产代码。
"""

import glob
import json
import os
import sys
import uuid
from dataclasses import dataclass

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
    """加载所有 mapping 一致的 corpus cases（读原始源文件）。"""
    manifests = glob.glob(f"{base_dir}/**/*.manifest.json", recursive=True)
    cases = []
    for mp in sorted(manifests):
        with open(mp, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        src_file = manifest.get("source_file", "")
        if src_file and os.path.exists(src_file):
            md_path = src_file
        else:
            md_path = mp.replace(".manifest.json", ".md")
            if not os.path.exists(md_path):
                continue
        with open(md_path, "r", encoding="utf-8") as f:
            md_lines = f.readlines()
        max_line = 0
        for u in manifest.get("units", []):
            for fn in ("stem_lines", "options_lines", "answer_lines", "explanation_lines"):
                val = u.get(fn)
                if val and isinstance(val, list) and len(val) == 2 and val[1] and isinstance(val[1], int):
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


# ---------------------------------------------------------------- B1-clean targets

def extract_b1_clean_targets(case: CorpusCase) -> list[dict]:
    """提取 B1-clean 的 stem + explanation targets。

    B1-clean = range_valid AND content_valid。
    """
    targets = []
    for mu in case.manifest_units:
        uid = mu.get("unit_id", "?")

        # stem
        stem = mu.get("stem_lines")
        if stem and isinstance(stem, list) and len(stem) == 2 and stem[0] and stem[1]:
            start, end = stem[0], stem[1]
            if 1 <= start <= end <= len(case.md_lines):
                texts = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
                non_empty = [t for t in texts if t.strip()]
                if non_empty:
                    targets.append({
                        "case_id": case.case_id,
                        "unit_id": uid,
                        "role": "stem",
                        "line_range": stem,
                        "expected_text": "\n".join(texts),
                    })

        # explanation
        exp = mu.get("explanation_lines")
        if exp and isinstance(exp, list) and len(exp) == 2 and exp[0] and exp[1]:
            start, end = exp[0], exp[1]
            if 1 <= start <= end <= len(case.md_lines):
                texts = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
                non_empty = [t for t in texts if t.strip()]
                if non_empty:
                    targets.append({
                        "case_id": case.case_id,
                        "unit_id": uid,
                        "role": "explanation",
                        "line_range": exp,
                        "expected_text": "\n".join(texts),
                    })

    return targets


# ---------------------------------------------------------------- Legacy strategy

def build_legacy_annotation(case: CorpusCase) -> dict:
    """Manifest units → semantic-only annotation（无 line_refs）。"""
    semantic_units = []
    for mu in case.manifest_units:
        qn = mu.get("question_numbers", [None])[0]
        qn_str = str(qn) if qn is not None else ""
        content = {"stem": {"question_label": qn_str}}
        if mu.get("answer_lines"):
            content["answer"] = {"answer_zone": "answer_table", "question_label": qn_str}
        unit = {
            "unit_id": mu.get("unit_id", "?"),
            "original_question_type": mu.get("original_question_type", "single_choice"),
            "content": content,
        }
        if mu.get("unit_type") == "composite_unit":
            unit["unit_type"] = "composite_unit"
            unit["shared_components"] = {}
            unit["sub_questions"] = []
        semantic_units.append(unit)
    return {"semantic_units": semantic_units, "document_metadata_claims": {}}


def run_legacy_on_targets(
    case: CorpusCase,
    source_lines: tuple[SourceLineView, ...],
    targets: list[dict],
) -> list[dict]:
    """对每个 target，检查 Legacy Resolver 是否成功解析该 role。"""
    annotation = build_legacy_annotation(case)
    svid = uuid.uuid5(uuid.NAMESPACE_DNS, case.case_id)

    try:
        resolver = SourceResolver(source_version_id=svid, lines=source_lines)
        resolved_run = resolver.resolve(annotation)
    except Exception as e:
        return [{"target": t, "legacy_status": "error", "legacy_detail": str(e)} for t in targets]

    # Build lookup: unit_id -> resolved spans by role
    # ResolvedSpan.span_id 格式: "sp-{unit_id}.{role}" 或 "sp-{unit_id}.{role}.{label}"
    resolved_by_unit = {}
    for span in resolved_run.resolved_spans:
        sid = span.span_id  # e.g. "sp-Q2.stem"
        if sid.startswith("sp-"):
            parts = sid[3:].split(".")
            if len(parts) >= 2:
                uid = parts[0]
                resolved_by_unit.setdefault(uid, []).append(span)

    results = []
    for t in targets:
        uid = t["unit_id"]
        role = t["role"]
        spans = resolved_by_unit.get(uid, [])

        if role == "stem":
            stem_spans = [s for s in spans if s.role == "stem"]
            if stem_spans:
                results.append({"target": t, "legacy_status": "resolved",
                               "legacy_detail": f"{len(stem_spans)} stem spans"})
            else:
                results.append({"target": t, "legacy_status": "not_found",
                               "legacy_detail": "no stem span"})
        elif role == "explanation":
            exp_spans = [s for s in spans if s.role == "explanation"]
            if exp_spans:
                results.append({"target": t, "legacy_status": "resolved",
                               "legacy_detail": f"{len(exp_spans)} explanation spans"})
            else:
                results.append({"target": t, "legacy_status": "not_found",
                               "legacy_detail": "no explanation span"})
        else:
            results.append({"target": t, "legacy_status": "unknown_role", "legacy_detail": role})

    return results


# ---------------------------------------------------------------- Path B strategy

def run_path_b_on_targets(
    case: CorpusCase,
    source_lines: tuple[SourceLineView, ...],
    targets: list[dict],
) -> list[dict]:
    """对每个 target，执行 Path B 验证（range + content + role）。"""
    import re

    _ROLE_PATTERNS = {
        "stem": [
            r"^\d+\\?[.、．]", r"^\(", r"^<div", r"^<table", r"^#", r"^【",
        ],
        "explanation": [
            r"解析", r"详解", r"【解答】", r"【分析】", r"【点评】",
            r"因为", r"所以", r"故选",
        ],
    }

    results = []
    for t in targets:
        start, end = t["line_range"]
        texts = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
        non_empty = [tx for tx in texts if tx.strip()]

        if not non_empty:
            results.append({"target": t, "path_b_status": "content_empty",
                           "path_b_detail": "all lines empty"})
            continue

        first = non_empty[0].strip()
        patterns = _ROLE_PATTERNS.get(t["role"], [])
        if t["role"] == "explanation":
            matched = any(re.search(p, first) for p in patterns)
        else:
            matched = any(re.match(p, first) for p in patterns)

        if matched:
            results.append({"target": t, "path_b_status": "validated",
                           "path_b_detail": f"role matched: '{first[:40]}'"})
        else:
            results.append({"target": t, "path_b_status": "role_mismatch",
                           "path_b_detail": f"'{first[:40]}' doesn't match {t['role']}"})

    return results


# ---------------------------------------------------------------- experiment

def run_gate_b2a(base_dir: str = "D:/Project/Papers/Ocr-markdown") -> dict:
    """执行 Gate B2-A 对比实验。"""
    print("=" * 60)
    print("Gate B2-A: Strategy Comparison (stem + explanation)")
    print("=" * 60)

    cases = load_corpus(base_dir)
    print(f"\nCorpus: {len(cases)} cases")

    all_results = []
    total_targets = 0

    for i, case in enumerate(cases):
        source_lines = build_source_lines(case.md_lines)
        targets = extract_b1_clean_targets(case)
        if not targets:
            continue
        total_targets += len(targets)

        leg_results = run_legacy_on_targets(case, source_lines, targets)
        pb_results = run_path_b_on_targets(case, source_lines, targets)

        for leg, pb in zip(leg_results, pb_results):
            all_results.append({
                "case_id": case.case_id,
                "unit_id": leg["target"]["unit_id"],
                "role": leg["target"]["role"],
                "legacy_status": leg["legacy_status"],
                "legacy_detail": leg["legacy_detail"],
                "path_b_status": pb["path_b_status"],
                "path_b_detail": pb["path_b_detail"],
            })

        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(cases)} cases...")

    # Aggregate
    total = len(all_results)
    leg_resolved = sum(1 for r in all_results if r["legacy_status"] == "resolved")
    leg_unresolved = sum(1 for r in all_results if r["legacy_status"] == "unresolved")
    leg_not_found = sum(1 for r in all_results if r["legacy_status"] == "not_found")
    leg_error = sum(1 for r in all_results if r["legacy_status"] == "error")

    pb_validated = sum(1 for r in all_results if r["path_b_status"] == "validated")
    pb_role_mismatch = sum(1 for r in all_results if r["path_b_status"] == "role_mismatch")
    pb_content_empty = sum(1 for r in all_results if r["path_b_status"] == "content_empty")

    # By role
    by_role = {}
    for r in all_results:
        role = r["role"]
        if role not in by_role:
            by_role[role] = {"total": 0, "leg_resolved": 0, "pb_validated": 0}
        by_role[role]["total"] += 1
        if r["legacy_status"] == "resolved":
            by_role[role]["leg_resolved"] += 1
        if r["path_b_status"] == "validated":
            by_role[role]["pb_validated"] += 1

    # Agreement matrix
    both_ok = sum(1 for r in all_results if r["legacy_status"] == "resolved" and r["path_b_status"] == "validated")
    leg_only = sum(1 for r in all_results if r["legacy_status"] == "resolved" and r["path_b_status"] != "validated")
    pb_only = sum(1 for r in all_results if r["legacy_status"] != "resolved" and r["path_b_status"] == "validated")
    neither = sum(1 for r in all_results if r["legacy_status"] != "resolved" and r["path_b_status"] != "validated")

    comparison = {
        "total_targets": total,
        "legacy": {
            "resolved": leg_resolved,
            "unresolved": leg_unresolved,
            "not_found": leg_not_found,
            "error": leg_error,
            "resolution_rate": leg_resolved / total if total else 0,
        },
        "path_b": {
            "validated": pb_validated,
            "role_mismatch": pb_role_mismatch,
            "content_empty": pb_content_empty,
            "validation_rate": pb_validated / total if total else 0,
        },
        "by_role": by_role,
        "agreement": {
            "both_ok": both_ok,
            "legacy_only": leg_only,
            "path_b_only": pb_only,
            "neither": neither,
        },
    }

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nTotal B1-clean targets: {total}")
    print(f"\n--- Legacy Resolver (search) ---")
    print(f"Resolved: {leg_resolved} ({leg_resolved/total:.1%})")
    print(f"Unresolved: {leg_unresolved}")
    print(f"Not found: {leg_not_found}")
    print(f"Error: {leg_error}")
    print(f"\n--- Path B (validation) ---")
    print(f"Validated: {pb_validated} ({pb_validated/total:.1%})")
    print(f"Role mismatch: {pb_role_mismatch}")
    print(f"Content empty: {pb_content_empty}")
    print(f"\n--- By Role ---")
    for role, stats in sorted(by_role.items()):
        print(f"  {role}: total={stats['total']}, "
              f"legacy={stats['leg_resolved']} ({stats['leg_resolved']/stats['total']:.1%}), "
              f"path_b={stats['pb_validated']} ({stats['pb_validated']/stats['total']:.1%})")
    print(f"\n--- Agreement Matrix ---")
    print(f"Both OK: {both_ok}")
    print(f"Legacy only: {leg_only}")
    print(f"Path B only: {pb_only}")
    print(f"Neither: {neither}")

    return {"comparison": comparison, "all_results": all_results, "cases": cases}


if __name__ == "__main__":
    result = run_gate_b2a()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_b2a_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result["comparison"], f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_path}")
