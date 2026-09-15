"""P3.2 / EB-004 Experimental Enforcement Verification.

Tests whether Admission Boundary blocks Evidence that does not satisfy
Evidence Authority requirements.

EXPERIMENT ONLY - no production code modification.
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


async def run_experiment():
    from app.core.hashing import sha256_hex
    from app.db.session import async_session_maker
    from app.domains.gate.admission import AdmissionService
    from app.models.source import DocumentSourceLine
    from app.repositories.snapshot_repository import SnapshotRepository
    from app.repositories.source_repository import SourceRepository

    results = {
        "experiment": "P3.2-EB-004-Enforcement-Verification",
        "attack_vectors": {},
        "bypass_paths": [],
        "summary": {},
    }

    async with async_session_maker() as session:
        src = SourceRepository(session)
        snap = SnapshotRepository(session)
        admission = AdmissionService(session)

        doc = await src.create_document(
            original_object_key=f"obj/{uuid.uuid4()}.pdf",
            original_sha256=sha256_hex(str(uuid.uuid4())),
            file_name="p32.pdf", file_type="pdf", upload_meta={},
            processing_status="sealed",
        )
        await session.flush()

        texts = ("1. stem", "A. a", "B. b", "C. c", "D. d", "hdr", "1. A")
        sv = await src.create_source_version(
            document_id=doc.id, artifact_kind="pdf", role="native",
            provider="native",
            body_text="\n".join(texts), body_hash=sha256_hex(list(texts)),
            integrity_hash=sha256_hex(list(texts)), page_count=1,
            line_count=len(texts), status="draft",
        )
        await session.flush()
        for i, t in enumerate(texts):
            await src.append_line(DocumentSourceLine(
                source_version_id=sv.id, line_ref=f"P1L{i+1:03d}", seq=i+1,
                page_no=1, line_no_in_page=i+1, text=t, block_type="text",
                line_hash=sha256_hex(t),
            ))
        await session.flush()
        await src.seal_version(sv.id)
        await session.flush()

        units = [{
            "unit_id": "Q1", "original_question_type": "single_choice",
            "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": l} for l in "ABCD"],
                "answer": {"answer_zone": "answer_table",
                           "question_label": "1"},
            },
        }]
        ann = await snap.create_semantic_annotation(
            source_version_id=sv.id,
            annotation_schema_version="semantic-metadata-annotation/v0.3",
            prompt_version="semantic-annotation/v1",
            model_config_hash=sha256_hex("m"),
            payload={
                "semantic_units": units,
                "document_metadata_claims": {"subject": "math",
                                              "grade": "3"},
            },
            status="valid", logical_execution_stage="ann",
            logical_execution_hash=sha256_hex("ann"),
        )
        await session.flush()

        async def make_cand(gd):
            c = await snap.create_admission_candidate(
                source_version_id=sv.id, annotation_id=ann.id,
                unit_type="standalone_unit", gate_decision=gd,
                build_versions={"compiler": "v1", "ir": "v1"},
                input_identity={"annotation_hash": sha256_hex("ann")},
                logical_execution_stage="gate",
                logical_execution_hash=sha256_hex("gate"),
                payload={
                    "ir_snapshot": {"units": [{
                        "unit_id": "Q1",
                        "unit_type": "standalone_question",
                        "original_question_type": "single_choice",
                        "question_number": "1",
                        "question_number_range": "1",
                        "sub_questions": [],
                    }]},
                    "compiled_roles": [{
                        "kind": "content", "unit_id": "Q1",
                        "role": "stem", "text": "s",
                        "text_hash": sha256_hex("s"),
                        "span_id": "sp-1", "line_refs": ["P1L001"],
                    }],
                    "answer": [{
                        "unit_id": "Q1", "text": "A",
                        "text_hash": sha256_hex("a"),
                        "span_id": "sp-2", "line_refs": ["P1L007"],
                        "source_located": True, "complete": True,
                    }],
                    "resolved_spans": [{
                        "span_id": "sp-1", "line_refs": ["P1L001"],
                        "granularity": "line",
                    }],
                },
                review_trail=[],
            )
            await session.flush()
            return c

        # N8: gate_decision=auto_approve, no ValidationEvent
        print("N8: gate_decision=auto_approve, no ValidationEvent...")
        c8 = await make_cand({"decision": "auto_approve", "layers": {}})
        try:
            await admission.approve(candidate_id=c8.id,
                                    provenance={"source": "auto_gate"})
            results["attack_vectors"]["N8"] = {
                "expected": "REJECT", "actual": "ACCEPTED",
                "bypass": True,
                "observation": "No Evidence Authority check",
            }
            results["bypass_paths"].append("N8")
            print("  BYPASS")
        except Exception as e:
            results["attack_vectors"]["N8"] = {
                "expected": "REJECT", "actual": "REJECTED",
                "bypass": False, "error": str(e),
            }
            print(f"  REJECTED: {e}")

        # N7: Direct Admission, no EvidencePromotion
        print("N7: Direct Admission, no EvidencePromotion...")
        c7 = await make_cand({"decision": "auto_approve", "layers": {}})
        try:
            await admission.approve(candidate_id=c7.id,
                                    provenance={"source": "auto_gate"})
            results["attack_vectors"]["N7"] = {
                "expected": "REJECT", "actual": "ACCEPTED",
                "bypass": True,
                "observation": "No EvidencePromotionService",
            }
            results["bypass_paths"].append("N7")
            print("  BYPASS")
        except Exception as e:
            results["attack_vectors"]["N7"] = {
                "expected": "REJECT", "actual": "REJECTED",
                "bypass": False, "error": str(e),
            }
            print(f"  REJECTED: {e}")

        # N1: EvidenceClaim without ValidationEvent
        print("N1: EvidenceClaim without ValidationEvent...")
        from app.domains.evidence.models import ProposerIdentity
        from app.domains.evidence.promotion import EvidencePromotionService
        from app.domains.resolver.span import ResolvedRun, ResolvedSpan

        promo = EvidencePromotionService()
        run = ResolvedRun(source_version_id=sv.id, resolved_spans=(ResolvedSpan(
            span_id="sp-1", source_version_id=sv.id, role="stem",
            start_line_ref="P1L001", end_line_ref="P1L001",
            line_refs=("P1L001",), granularity="line",
            start_offset=None, end_offset=None,
            text_hash=sha256_hex("s"), resolution_status="exact",
        ),))
        refs = promo.create_references(
            run, ProposerIdentity(producer_type="heuristic",
                                  pipeline_version="p32/v1"),
        )
        c1 = await make_cand({"decision": "auto_approve", "layers": {}})
        try:
            await admission.approve(candidate_id=c1.id,
                                    provenance={"source": "auto_gate"})
            results["attack_vectors"]["N1"] = {
                "expected": "REJECT", "actual": "ACCEPTED",
                "bypass": True,
                "observation": "EvidenceReference but no ValidationEvent",
            }
            results["bypass_paths"].append("N1")
            print("  BYPASS")
        except Exception as e:
            results["attack_vectors"]["N1"] = {
                "expected": "REJECT", "actual": "REJECTED",
                "bypass": False, "error": str(e),
            }
            print(f"  REJECTED: {e}")

        # N2: ValidationEvent with rejected result
        print("N2: ValidationEvent with rejected result...")
        promo2 = EvidencePromotionService()
        promo2.create_references(
            run, ProposerIdentity(producer_type="heuristic",
                                  pipeline_version="p32/v1"),
        )
        promo2.record_validation(
            claim_id="Q1",
            gate_decision={"decision": "rejected", "layers": {}},
            reference_ids=(refs[0].reference_id,),
        )
        iv = promo2.is_evidence_validated("Q1")
        print(f"  is_evidence_validated = {iv}")
        c2 = await make_cand({"decision": "auto_approve", "layers": {}})
        try:
            await admission.approve(candidate_id=c2.id,
                                    provenance={"source": "auto_gate"})
            results["attack_vectors"]["N2"] = {
                "expected": "REJECT", "actual": "ACCEPTED",
                "bypass": True,
                "observation": f"is_evidence_validated={iv}",
            }
            results["bypass_paths"].append("N2")
            print("  BYPASS")
        except Exception as e:
            results["attack_vectors"]["N2"] = {
                "expected": "REJECT", "actual": "REJECTED",
                "bypass": False, "error": str(e),
            }
            print(f"  REJECTED: {e}")

        results["summary"] = {
            "total_attacks": len(results["attack_vectors"]),
            "bypass_count": len(results["bypass_paths"]),
            "bypass_paths": results["bypass_paths"],
            "enforcement_effective": len(results["bypass_paths"]) == 0,
        }
        print(f"\n{'=' * 60}")
        print(f"Total: {results['summary']['total_attacks']}, "
              f"Bypass: {results['summary']['bypass_count']}")
        print(f"Enforcement effective: "
              f"{results['summary']['enforcement_effective']}")

    return results


def main():
    results = asyncio.run(run_experiment())
    out = Path(__file__).parent / "p32-enforcement-results.json"
    out.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
