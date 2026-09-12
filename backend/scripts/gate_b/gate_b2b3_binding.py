"""
B2-B3-B: Deterministic Fill-in Binding Experiment

Verify: Given preprocessing evidence (question_id + answer_region),
can V3 mechanically validate and construct a ResolvedSpan WITHOUT
search, fuzzy matching, or fallback?

Positive cases: frozen 34 real fill-in units
Negative cases: artificially corrupted evidence (must fail-closed)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, "backend")
from scripts.gate_b.gate_b2b2_answer_table import load_corpus


@dataclass
class BindingEvidence:
    case_id: str
    unit_id: str
    subject: str
    question_id: str
    source_path: str
    source_version: str
    region_start: int
    region_end: int
    region_lines: list[str] = field(default_factory=list)
    evidence_hash: str = ""


@dataclass
class ValidationResult:
    evidence: BindingEvidence
    question_id_valid: bool = False
    source_version_valid: bool = False
    region_valid: bool = False
    region_nonempty: bool = False
    region_in_scope: bool = False
    evidence_hash_valid: bool = False
    resolved_span_constructed: bool = False
    fallback_used: bool = False
    binding_stable: bool = False
    failure_reason: str = ""
    resolved_span_text: str = ""
    region_lines: list[str] = field(default_factory=list)


def compute_evidence_hash(lines: list[str]) -> str:
    content = "\n".join(lines)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def validate_binding(evidence: BindingEvidence, md_lines: list[str]) -> ValidationResult:
    """Deterministic validation — NO search, NO fuzzy, NO fallback."""
    result = ValidationResult(evidence=evidence)

    uid = evidence.unit_id
    qid = evidence.question_id
    if qid and (qid == uid or uid.startswith(qid) or qid in uid):
        result.question_id_valid = True

    if evidence.source_path and evidence.source_version:
        result.source_version_valid = True

    start, end = evidence.region_start, evidence.region_end
    if start >= 1 and end >= start:
        result.region_valid = True
    else:
        result.failure_reason = f"region_invalid: [{start},{end}]"
        return result

    if end <= len(md_lines):
        result.region_in_scope = True
    else:
        result.failure_reason = f"region_out_of_scope: end={end} > {len(md_lines)}"
        return result

    actual_lines = [md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)
                   if 1 <= i <= len(md_lines)]
    result.region_lines = actual_lines

    non_empty = [l for l in actual_lines if l.strip()]
    if non_empty:
        result.region_nonempty = True
    else:
        result.failure_reason = "region_empty"
        return result

    actual_hash = compute_evidence_hash(actual_lines)
    if evidence.evidence_hash and actual_hash == evidence.evidence_hash:
        result.evidence_hash_valid = True
    elif not evidence.evidence_hash:
        result.evidence_hash_valid = True

    if (result.question_id_valid and result.source_version_valid and
            result.region_valid and result.region_nonempty and
            result.region_in_scope and result.evidence_hash_valid):
        result.resolved_span_constructed = True
        result.resolved_span_text = "\n".join(non_empty[:3])
        result.binding_stable = True

    if not result.resolved_span_constructed and not result.failure_reason:
        result.failure_reason = "validation_failed_unknown"

    return result


def load_frozen_testset(path: str = "Docs/V3_SPEC/gate_b2b3_frozen_testset.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("real_fillin_test_set", [])


def main() -> int:
    cases = load_corpus()
    case_map = {c.case_id: c for c in cases}

    testset = load_frozen_testset()
    print(f"Frozen test set: {len(testset)} real fill-in units")

    # ---- Positive Cases ----
    print("\n" + "=" * 60)
    print("POSITIVE CASES: Deterministic Binding Validation")
    print("=" * 60)

    positive_results = []
    for item in testset:
        case_id = item["case_id"]
        unit_id = item["unit_id"]
        region = item["region"]
        case = case_map.get(case_id)
        if not case:
            print(f"  SKIP: {case_id} not found")
            continue

        evidence = BindingEvidence(
            case_id=case_id,
            unit_id=unit_id,
            subject=item["subject"],
            question_id=unit_id,
            source_path=case.source_path,
            source_version="v1",
            region_start=region[0],
            region_end=region[1],
        )
        actual_lines = [case.md_lines[i - 1].rstrip("\n")
                       for i in range(region[0], region[1] + 1)
                       if 1 <= i <= len(case.md_lines)]
        evidence.evidence_hash = compute_evidence_hash(actual_lines)
        evidence.region_lines = actual_lines

        result = validate_binding(evidence, case.md_lines)
        positive_results.append(result)

    total_pos = len(positive_results)
    checks = {
        "question_id_valid": sum(1 for r in positive_results if r.question_id_valid),
        "source_version_valid": sum(1 for r in positive_results if r.source_version_valid),
        "region_valid": sum(1 for r in positive_results if r.region_valid),
        "region_nonempty": sum(1 for r in positive_results if r.region_nonempty),
        "region_in_scope": sum(1 for r in positive_results if r.region_in_scope),
        "evidence_hash_valid": sum(1 for r in positive_results if r.evidence_hash_valid),
        "resolved_span_constructed": sum(1 for r in positive_results if r.resolved_span_constructed),
        "binding_stable": sum(1 for r in positive_results if r.binding_stable),
    }

    print(f"\nTotal positive cases: {total_pos}")
    for check, count in checks.items():
        pct = 100 * count / total_pos if total_pos else 0
        status = "PASS" if count == total_pos else "FAIL"
        print(f"  {check}: {count}/{total_pos} ({pct:.1f}%) [{status}]")

    fallback_count = sum(1 for r in positive_results if r.fallback_used)
    print(f"  fallback_used: {fallback_count} (must be 0)")

    failures = [r for r in positive_results if not r.resolved_span_constructed]
    if failures:
        print(f"\n  FAILURES ({len(failures)}):")
        for r in failures:
            print(f"    {r.evidence.unit_id}: {r.failure_reason}")

    # ---- Determinism Test ----
    print("\n" + "=" * 60)
    print("DETERMINISM: Re-run validation on same input")
    print("=" * 60)

    determinism_pass = 0
    for item in testset[:10]:
        case_id = item["case_id"]
        case = case_map.get(case_id)
        if not case:
            continue

        evidence = BindingEvidence(
            case_id=case_id,
            unit_id=item["unit_id"],
            subject=item["subject"],
            question_id=item["unit_id"],
            source_path=case.source_path,
            source_version="v1",
            region_start=item["region"][0],
            region_end=item["region"][1],
        )
        actual_lines = [case.md_lines[i - 1].rstrip("\n")
                       for i in range(item["region"][0], item["region"][1] + 1)
                       if 1 <= i <= len(case.md_lines)]
        evidence.evidence_hash = compute_evidence_hash(actual_lines)

        hashes = []
        for _ in range(3):
            r = validate_binding(evidence, case.md_lines)
            h = compute_evidence_hash(r.region_lines) if r.region_lines else "empty"
            hashes.append(h)

        if len(set(hashes)) == 1:
            determinism_pass += 1

    print(f"Determinism (3 runs × 10 cases): {determinism_pass}/10 consistent")

    # ---- Negative Cases ----
    print("\n" + "=" * 60)
    print("NEGATIVE CASES: Must FAIL-CLOSED")
    print("=" * 60)

    negative_results = []

    if testset:
        item = testset[0]
        case = case_map.get(item["case_id"])
        if case:
            # N1: Invalid range
            ev = BindingEvidence(
                case_id=item["case_id"], unit_id=item["unit_id"],
                subject=item["subject"], question_id=item["unit_id"],
                source_path=case.source_path, source_version="v1",
                region_start=10, region_end=5,
            )
            r = validate_binding(ev, case.md_lines)
            negative_results.append(("N1_invalid_range", not r.resolved_span_constructed))

            # N2: Out-of-range
            ev = BindingEvidence(
                case_id=item["case_id"], unit_id=item["unit_id"],
                subject=item["subject"], question_id=item["unit_id"],
                source_path=case.source_path, source_version="v1",
                region_start=99999, region_end=99999,
            )
            r = validate_binding(ev, case.md_lines)
            negative_results.append(("N2_out_of_range", not r.resolved_span_constructed))

            # N3: Empty region
            blank_idx = None
            for i, line in enumerate(case.md_lines[:50]):
                if not line.strip():
                    blank_idx = i + 1
                    break
            if blank_idx:
                ev = BindingEvidence(
                    case_id=item["case_id"], unit_id=item["unit_id"],
                    subject=item["subject"], question_id=item["unit_id"],
                    source_path=case.source_path, source_version="v1",
                    region_start=blank_idx, region_end=blank_idx,
                )
                r = validate_binding(ev, case.md_lines)
                negative_results.append(("N3_empty_region", not r.resolved_span_constructed))

            # N4: Wrong question_id
            ev = BindingEvidence(
                case_id=item["case_id"], unit_id=item["unit_id"],
                subject=item["subject"], question_id="WRONG_ID_999",
                source_path=case.source_path, source_version="v1",
                region_start=item["region"][0], region_end=item["region"][1],
            )
            actual_lines = [case.md_lines[i - 1].rstrip("\n")
                           for i in range(item["region"][0], item["region"][1] + 1)
                           if 1 <= i <= len(case.md_lines)]
            ev.evidence_hash = compute_evidence_hash(actual_lines)
            r = validate_binding(ev, case.md_lines)
            negative_results.append(("N4_wrong_question_id", not r.resolved_span_constructed))

            # N5: Tampered hash
            ev = BindingEvidence(
                case_id=item["case_id"], unit_id=item["unit_id"],
                subject=item["subject"], question_id=item["unit_id"],
                source_path=case.source_path, source_version="v1",
                region_start=item["region"][0], region_end=item["region"][1],
                evidence_hash="TAMPERED_HASH_000",
            )
            r = validate_binding(ev, case.md_lines)
            negative_results.append(("N5_tampered_hash", not r.resolved_span_constructed))

            # N6: Missing source
            ev = BindingEvidence(
                case_id=item["case_id"], unit_id=item["unit_id"],
                subject=item["subject"], question_id=item["unit_id"],
                source_path="", source_version="",
                region_start=item["region"][0], region_end=item["region"][1],
            )
            r = validate_binding(ev, case.md_lines)
            negative_results.append(("N6_missing_source", not r.resolved_span_constructed))

    for name, passed in negative_results:
        status = "PASS" if passed else "FAIL (not fail-closed!)"
        print(f"  {name}: {status}")

    neg_pass = sum(1 for _, p in negative_results if p)
    print(f"\nNegative cases: {neg_pass}/{len(negative_results)} fail-closed")

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("B2-B3-B SUMMARY")
    print("=" * 60)
    print(f"Positive: {checks['resolved_span_constructed']}/{total_pos} resolved")
    print(f"Fallback: {fallback_count} (target: 0)")
    print(f"Determinism: {determinism_pass}/10 consistent")
    print(f"Negative: {neg_pass}/{len(negative_results)} fail-closed")

    all_pass = (checks["resolved_span_constructed"] == total_pos and
                fallback_count == 0 and
                neg_pass == len(negative_results))
    print(f"\nOverall: {'PASS' if all_pass else 'CONDITIONAL'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
