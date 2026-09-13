"""Gate B2-A 三项补强审计.

任务 a: 提取并分类 15 个 Legacy-only cases (Legacy resolved, Path B not validated)
任务 b: 独立抽样验证 Path B 成功结果 (从 1820 个 stem validated 中抽样)
任务 c: 排除 explanation，输出仅 stem 的 comparative metric

实验 Harness——不修改生产代码。
"""

import glob
import json
import os
import random
import re
import sys
import uuid
from dataclasses import dataclass

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import ResolvedRun, SourceLineView


@dataclass
class CorpusCase:
    case_id: str
    source_path: str
    manifest_path: str
    md_lines: list[str]
    manifest_units: list[dict]
    subject: str


def load_corpus(base_dir: str = "D:/Project/Papers/Ocr-markdown") -> list[CorpusCase]:
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


def extract_stem_targets(case: CorpusCase) -> list[dict]:
    targets = []
    for mu in case.manifest_units:
        uid = mu.get("unit_id", "?")
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
                        "first_line": non_empty[0].strip(),
                    })
    return targets


def build_legacy_annotation(case: CorpusCase) -> dict:
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


def run_legacy(case, source_lines, targets):
    annotation = build_legacy_annotation(case)
    svid = uuid.uuid5(uuid.NAMESPACE_DNS, case.case_id)
    try:
        resolver = SourceResolver(source_version_id=svid, lines=source_lines)
        resolved_run = resolver.resolve(annotation)
    except Exception as e:
        return [{"target": t, "legacy_status": "error", "legacy_detail": str(e)} for t in targets]

    resolved_by_unit = {}
    for span in resolved_run.resolved_spans:
        sid = span.span_id
        if sid.startswith("sp-"):
            parts = sid[3:].split(".")
            if len(parts) >= 2:
                uid = parts[0]
                resolved_by_unit.setdefault(uid, []).append(span)

    results = []
    for t in targets:
        uid = t["unit_id"]
        spans = resolved_by_unit.get(uid, [])
        stem_spans = [s for s in spans if s.role == "stem"]
        if stem_spans:
            results.append({"target": t, "legacy_status": "resolved",
                           "legacy_detail": f"{len(stem_spans)} stem spans",
                           "legacy_spans": stem_spans})
        else:
            results.append({"target": t, "legacy_status": "not_found",
                           "legacy_detail": "no stem span", "legacy_spans": []})
    return results


_STEM_PATTERNS = [
    r"^\d+\\?[.、．]", r"^\(", r"^<div", r"^<table", r"^#", r"^【",
]


def run_path_b(case, targets):
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
        matched = any(re.match(p, first) for p in _STEM_PATTERNS)
        if matched:
            results.append({"target": t, "path_b_status": "validated",
                           "path_b_detail": f"role matched: '{first[:60]}'"})
        else:
            results.append({"target": t, "path_b_status": "role_mismatch",
                           "path_b_detail": f"'{first[:60]}' doesn't match stem"})
    return results


def classify_legacy_only(leg, pb, case):
    """分类 Legacy-only case 的失败原因."""
    first = leg["target"]["first_line"]
    if re.match(r"^[A-E][.、．)）]", first):
        return "option_marker_start", f"Starts with option marker: '{first[:50]}'"
    if re.match(r"^【", first):
        return "bracket_label", f"Starts with bracket label: '{first[:50]}'"
    if re.match(r"^<(table|div|tr|td|p)", first):
        return "html_start", f"Starts with HTML tag: '{first[:50]}'"
    if re.match(r"^(例|练习|习题|填空|判断|选择)", first):
        return "exercise_label", f"Starts with exercise label: '{first[:50]}'"
    if re.match(r"^\d+[^.、．]", first):
        return "number_no_dot", f"Number without standard dot: '{first[:50]}'"
    if not first:
        return "empty_first_line", "First line is empty after strip"
    return "no_pattern_match", f"No stem pattern matched: '{first[:50]}'"


def audit_task_a(all_results, cases_map):
    print("\n" + "=" * 60)
    print("TASK A: Legacy-only Cases Audit (stem only)")
    print("=" * 60)

    legacy_only = [
        r for r in all_results
        if r["legacy"]["legacy_status"] == "resolved" and r["path_b"]["path_b_status"] != "validated"
    ]
    print(f"\nTotal Legacy-only cases: {len(legacy_only)}")

    categories = {}
    details = []
    for r in legacy_only:
        cat, reason = classify_legacy_only(
            r["legacy"], r["path_b"], cases_map.get(r["case_id"])
        )
        categories[cat] = categories.get(cat, 0) + 1
        details.append({
            "case_id": r["case_id"],
            "unit_id": r["unit_id"],
            "first_line": r["legacy"]["target"]["first_line"][:80],
            "category": cat,
            "reason": reason,
            "legacy_detail": r["legacy"]["legacy_detail"],
            "path_b_detail": r["path_b"]["path_b_detail"],
        })

    print("\n--- Category Distribution ---")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    print("\n--- Case Details ---")
    for d in details:
        print(f"  [{d['case_id']}/{d['unit_id']}] {d['category']}")
        print(f"    First line: {d['first_line']}")
        print(f"    Path B: {d['path_b_detail']}")

    return {"total": len(legacy_only), "categories": categories, "details": details}


def audit_task_b(all_results, sample_size=150, seed=42):
    print("\n" + "=" * 60)
    print(f"TASK B: Independent Sampling (stem validated, n={sample_size})")
    print("=" * 60)

    pb_validated = [
        r for r in all_results
        if r["path_b"]["path_b_status"] == "validated"
    ]
    print(f"\nTotal Path B validated stems: {len(pb_validated)}")

    rng = random.Random(seed)
    sample = rng.sample(pb_validated, min(sample_size, len(pb_validated)))

    pattern_dist = {}
    for r in sample:
        first = r["path_b"]["target"]["first_line"]
        if re.match(r"^\d+[.、．]", first):
            pattern_dist["number_dot"] = pattern_dist.get("number_dot", 0) + 1
        elif re.match(r"^\d+\\[.、．]", first):
            pattern_dist["number_escaped_dot"] = pattern_dist.get("number_escaped_dot", 0) + 1
        elif re.match(r"^\(", first):
            pattern_dist["paren"] = pattern_dist.get("paren", 0) + 1
        elif re.match(r"^【", first):
            pattern_dist["bracket"] = pattern_dist.get("bracket", 0) + 1
        elif re.match(r"^<", first):
            pattern_dist["html"] = pattern_dist.get("html", 0) + 1
        elif re.match(r"^#", first):
            pattern_dist["heading"] = pattern_dist.get("heading", 0) + 1
        else:
            pattern_dist["other"] = pattern_dist.get("other", 0) + 1

    print("\n--- Pattern Distribution (sample) ---")
    for pat, count in sorted(pattern_dist.items(), key=lambda x: -x[1]):
        print(f"  {pat}: {count} ({count/len(sample):.1%})")

    print("\n--- Random Inspection Samples (10) ---")
    inspect = rng.sample(sample, min(10, len(sample)))
    for r in inspect:
        first = r["path_b"]["target"]["first_line"]
        print(f"  [{r['case_id']}/{r['unit_id']}] {first[:70]}")

    return {
        "population": len(pb_validated),
        "sample_size": len(sample),
        "seed": seed,
        "pattern_distribution": pattern_dist,
        "inspection_samples": [
            {"case_id": r["case_id"], "unit_id": r["unit_id"],
             "first_line": r["path_b"]["target"]["first_line"][:80]}
            for r in inspect
        ],
    }


def audit_task_c(all_results):
    print("\n" + "=" * 60)
    print("TASK C: Stem-Only Comparative Metric")
    print("=" * 60)

    total = len(all_results)
    leg_resolved = sum(1 for r in all_results if r["legacy"]["legacy_status"] == "resolved")
    pb_validated = sum(1 for r in all_results if r["path_b"]["path_b_status"] == "validated")

    both_ok = sum(1 for r in all_results
                  if r["legacy"]["legacy_status"] == "resolved" and r["path_b"]["path_b_status"] == "validated")
    leg_only = sum(1 for r in all_results
                   if r["legacy"]["legacy_status"] == "resolved" and r["path_b"]["path_b_status"] != "validated")
    pb_only = sum(1 for r in all_results
                  if r["legacy"]["legacy_status"] != "resolved" and r["path_b"]["path_b_status"] == "validated")
    neither = sum(1 for r in all_results
                  if r["legacy"]["legacy_status"] != "resolved" and r["path_b"]["path_b_status"] != "validated")

    print(f"\nTotal stem targets: {total}")
    print(f"Legacy resolved: {leg_resolved} ({leg_resolved/total:.1%})")
    print(f"Path B validated: {pb_validated} ({pb_validated/total:.1%})")
    print(f"\nAgreement:")
    print(f"  Both OK: {both_ok}")
    print(f"  Legacy only: {leg_only}")
    print(f"  Path B only: {pb_only}")
    print(f"  Neither: {neither}")
    print(f"\nPath B improvement over Legacy: +{pb_validated - leg_resolved} targets")
    print(f"Path B coverage vs Legacy: {pb_validated/max(leg_resolved,1):.1f}x")

    return {
        "total_stem_targets": total,
        "legacy_resolved": leg_resolved,
        "legacy_rate": round(leg_resolved / total, 4),
        "path_b_validated": pb_validated,
        "path_b_rate": round(pb_validated / total, 4),
        "agreement": {
            "both_ok": both_ok,
            "legacy_only": leg_only,
            "path_b_only": pb_only,
            "neither": neither,
        },
        "improvement": pb_validated - leg_resolved,
        "coverage_ratio": round(pb_validated / max(leg_resolved, 1), 2),
    }


def main():
    base_dir = "D:/Project/Papers/Ocr-markdown"
    cases = load_corpus(base_dir)
    cases_map = {c.case_id: c for c in cases}
    print(f"Corpus: {len(cases)} cases")

    all_results = []
    for i, case in enumerate(cases):
        source_lines = build_source_lines(case.md_lines)
        targets = extract_stem_targets(case)
        if not targets:
            continue
        leg_results = run_legacy(case, source_lines, targets)
        pb_results = run_path_b(case, targets)
        for leg, pb in zip(leg_results, pb_results):
            all_results.append({
                "case_id": case.case_id,
                "unit_id": leg["target"]["unit_id"],
                "legacy": leg,
                "path_b": pb,
            })
        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(cases)}...")

    print(f"\nTotal stem targets: {len(all_results)}")

    task_a = audit_task_a(all_results, cases_map)
    task_b = audit_task_b(all_results)
    task_c = audit_task_c(all_results)

    output = {
        "task_a_legacy_only_audit": task_a,
        "task_b_sampling": task_b,
        "task_c_stem_only_metric": task_c,
    }
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_b2a_audit_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
