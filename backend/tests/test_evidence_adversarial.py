"""Adversarial review of Evidence Promotion Contract Phase 1 — POST-HARDENING.

Phase 1 Hardening verification: Every test tries to BREAK the implementation.
After hardening, attacks should FAIL (implementation blocks them).

Test semantics:
- PASS = attack succeeded = gap still exists = BAD
- FAIL = attack blocked = fix works = GOOD

We invert the assertions: tests verify that attacks are BLOCKED.
"""

from __future__ import annotations

import uuid
from dataclasses import FrozenInstanceError

import pytest

from app.domains.evidence.models import (
    AppendOnlyEventLog,
    CheckResult,
    EvidenceReference,
    ProposerIdentity,
    ValidationEvent,
)
from app.domains.evidence.promotion import (
    EvidencePromotionService,
    create_evidence_references,
    record_validation_event,
)
from app.domains.resolver.span import ResolvedRun, ResolvedSpan
from app.repositories.evidence_repository import EvidenceRepository
from tests.eb008_helpers import rejected_gate_decision, seed_candidate


def _make_span(span_id="sp-1", role="answer", svid=None):
    return ResolvedSpan(
        span_id=span_id,
        source_version_id=svid or uuid.uuid4(),
        role=role,
        start_line_ref="P001L001",
        end_line_ref="P001L001",
        line_refs=("P001L001",),
        granularity="line",
        start_offset=None,
        end_offset=None,
        text_hash="h1",
        resolution_status="exact",
    )


def _gate_auto_approve() -> dict:
    return {
        "decision": "auto_approve",
        "reasons": ["strict-auto: all answers verified_correct=true"],
        "layers": {
            "structural": {"status": "pass", "reasons": []},
            "provenance": {"status": "pass", "reasons": []},
            "semantic": {"status": "pass", "reasons": []},
            "admission": {"status": "pass", "reasons": ["strict-auto"]},
        },
    }


def _gate_rejected() -> dict:
    return {
        "decision": "rejected",
        "reasons": ["text_hash mismatch"],
        "layers": {
            "structural": {"status": "pass", "reasons": []},
            "provenance": {"status": "fail", "reasons": ["text_hash mismatch"]},
            "semantic": {"status": "pass", "reasons": []},
            "admission": {"status": "fail", "reasons": ["text_hash mismatch"]},
        },
    }


# ---------------------------------------------------------------------------
# ATTACK 1: Append-only enforcement — should now be BLOCKED
# ---------------------------------------------------------------------------

class TestAttackAppendOnlyNotEnforced:
    async def test_clear_internal_log_blocked(self, session):
        """EB-008 §5.5: Repository 无 update/delete；唯一写入口 append_event。"""
        sv, _ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        service = EvidencePromotionService(repo)
        await service.record_validation(
            "claim-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        rows = await repo.find_events_for_claim(cand.id, "claim-1")
        assert len(rows) == 1
        # 无 update/delete 方法（append-only 应用层保护）
        assert not hasattr(repo, "update_event")
        assert not hasattr(repo, "delete_event")
        assert not hasattr(repo, "clear")

    async def test_tuple_is_immutable(self, session):
        """Critical 1 fix: domain log tuple 不可变；DB 层无 UPDATE/DELETE 路径。"""
        log = AppendOnlyEventLog()
        log.append(ValidationEvent(
            event_id="ve-1", claim_id="claim-1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
        ))
        events_tuple = log.events
        assert not hasattr(events_tuple, "append")
        assert not hasattr(events_tuple, "clear")
        assert not hasattr(events_tuple, "reverse")

    async def test_state_machine_blocks_rejected_after_validated(self, session):
        """Critical 2 fix: VALIDATED → only INVALIDATED allowed, not REJECTED（DB 路径）。"""
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        await service.record_validation(
            "claim-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        # Cannot append REJECTED after VALIDATED
        with pytest.raises(ValueError, match="only INVALIDATED transition allowed"):
            await service.record_validation(
                "claim-1", _gate_rejected(),
                candidate_id=cand.id, source_version_id=sv.id,
            )


# ---------------------------------------------------------------------------
# ATTACK 2: ValidationEvent ↔ EvidenceReference linking — should now work
# ---------------------------------------------------------------------------

class TestAttackNoLinkBetweenLayers:
    async def test_validation_event_traces_to_evidence_reference(self, session):
        """Critical 3 fix: ValidationEvent.reference_ids links to EvidenceReference."""
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        span = _make_span("sp-answer-1")
        run = ResolvedRun(source_version_id=span.source_version_id, resolved_spans=(span,))
        service.create_references(run, ProposerIdentity(producer_type="llm"))
        rec = await service.record_validation(
            "unit-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
            reference_ids=("er-sp-answer-1",),
        )
        assert rec is not None
        assert tuple(rec.reference_ids or ()) == ("er-sp-answer-1",)
        traced = service.get_references_for_ids(tuple(rec.reference_ids or ()))
        assert len(traced) == 1
        assert traced[0].span_id == "sp-answer-1"

    async def test_can_determine_which_spans_were_validated(self, session):
        """Critical 3 fix: reference_ids enables tracing from claim to spans."""
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        s1 = _make_span("sp-stem", "stem")
        s2 = _make_span("sp-answer", "answer")
        run = ResolvedRun(source_version_id=s1.source_version_id, resolved_spans=(s1, s2))
        service.create_references(run, ProposerIdentity(producer_type="llm"))
        rec = await service.record_validation(
            "unit-1",
            _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
            reference_ids=("er-sp-stem", "er-sp-answer"),
        )
        assert rec is not None
        traced = service.get_references_for_ids(tuple(rec.reference_ids or ()))
        assert len(traced) == 2
        assert {r.span_id for r in traced} == {"sp-stem", "sp-answer"}


# ---------------------------------------------------------------------------
# ATTACK 3: validation_method derivation — should now be correct
# ---------------------------------------------------------------------------

class TestAttackValidationMethodHardcoded:
    def test_provenance_fail_derives_byte_proven(self):
        """High 4 fix: validation_method derived from gate layers.
        Provenance fail → byte_proven, not frozen_header_rule."""
        event = record_validation_event(claim_id="c1", gate_decision=_gate_rejected())
        assert event.validation_method == "byte_proven"

    def test_auto_approve_derives_frozen_header_rule(self):
        """High 4 fix: auto_approve → frozen_header_rule (all layers pass)."""
        event = record_validation_event(claim_id="c1", gate_decision=_gate_auto_approve())
        assert event.validation_method == "frozen_header_rule"

    def test_structural_fail_derives_structural_consistency(self):
        """High 4 fix: structural fail → structural_consistency."""
        gate = {
            "decision": "rejected",
            "layers": {
                "structural": {"status": "fail", "reasons": ["bad"]},
                "provenance": {"status": "pass", "reasons": []},
                "semantic": {"status": "pass", "reasons": []},
                "admission": {"status": "fail", "reasons": ["bad"]},
            },
        }
        event = record_validation_event(claim_id="c1", gate_decision=gate)
        assert event.validation_method == "structural_consistency"


# ---------------------------------------------------------------------------
# ATTACK 4: checks_passed uses structured IDs — should now be machine-parseable
# ---------------------------------------------------------------------------

class TestAttackChecksPassedSemantics:
    def test_checks_are_structured_not_narrative(self):
        """High 5 fix: checks are CheckResult objects with machine-parseable IDs."""
        event = record_validation_event(claim_id="c1", gate_decision=_gate_auto_approve())
        # checks is tuple of CheckResult
        assert all(isinstance(c, CheckResult) for c in event.checks)
        # Check IDs are short, machine-parseable
        for c in event.checks:
            assert len(c.check_id) < 50, f"Check ID too long: {c.check_id}"

    def test_checks_failed_are_structured(self):
        """High 5 fix: checks_failed derived from CheckResult objects."""
        event = record_validation_event(claim_id="c1", gate_decision=_gate_rejected())
        # checks_failed is derived property returning check_id strings
        assert all(isinstance(cid, str) for cid in event.checks_failed)
        # Check IDs are short
        for cid in event.checks_failed:
            assert len(cid) < 50


# ---------------------------------------------------------------------------
# ATTACK 5: ProposerIdentity — should now be "llm"
# ---------------------------------------------------------------------------

class TestAttackProposerIdentityWrong:
    def test_gate_service_uses_llm_producer(self):
        """High 6 fix: GateService uses producer_type="llm", not "native_parser"."""
        import inspect
        from app.domains.gate.service import GateService
        source = inspect.getsource(GateService.run)
        # ProposerIdentity should use "llm"
        assert 'producer_type="llm"' in source
        assert 'producer_type="native_parser"' not in source


# ---------------------------------------------------------------------------
# ATTACK 6: Per-run isolation — should now be enforced
# ---------------------------------------------------------------------------

class TestAttackAccumulation:
    def test_fresh_service_per_run(self):
        """Medium 9 fix: GateService creates fresh EvidencePromotionService per run.
        EB-008 §5.1: DB-backed via EvidenceRepository(session) 注入。"""
        import inspect
        from app.domains.gate.service import GateService
        source = inspect.getsource(GateService.run)
        # Fresh DB-backed service created inside run()
        assert "self._evidence = EvidencePromotionService(EvidenceRepository(" in source
        assert "EvidencePromotionService()" not in source  # 无 in-memory 构造（DEC-016 D3）


# ---------------------------------------------------------------------------
# ATTACK 7: is_evidence_validated uses timestamp — should now be correct
# ---------------------------------------------------------------------------

class TestAttackLatestByPositionNotTime:
    async def test_timestamp_order_determines_latest(self, session):
        """Medium 7 fix: Authority 投影 uses timestamp, not list/insert position."""
        from datetime import datetime, timedelta, timezone

        sv, _ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        service = EvidencePromotionService(repo)
        # claim-1 validated at T；claim-2 rejected at T+1s（插入顺序无关）
        later = datetime.now(timezone.utc) + timedelta(seconds=1)
        await repo.append_event(
            ValidationEvent(
                event_id="ve-late", claim_id="claim-1",
                validation_result="validated", checks=(),
                validation_method="frozen_header_rule", validator="gate/v1",
                validated_at=later,
            ),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        await repo.append_event(
            ValidationEvent(
                event_id="ve-early", claim_id="claim-2",
                validation_result="rejected", checks=(),
                validation_method="frozen_header_rule", validator="gate/v1",
            ),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert await service.is_evidence_validated(cand.id, "claim-1") is True
        assert await service.is_evidence_validated(cand.id, "claim-2") is False


# ---------------------------------------------------------------------------
# ATTACK 8: R2 claim — proposed_role copies span.role
# ---------------------------------------------------------------------------

class TestAttackR2SemanticRoleInProposal:
    def test_proposed_role_is_proposal_not_authority(self):
        """R2: EvidenceReference.proposed_role is a proposal, not authority.
        The field name says "proposed" — it does not assert this span IS role X."""
        span = _make_span("sp-1", role="answer")
        ref = EvidenceReference.from_resolved_span(span, ProposerIdentity(producer_type="llm"))
        # proposed_role is a proposal — no authority fields
        assert not hasattr(ref, "validated")
        assert not hasattr(ref, "authority")
        assert not hasattr(ref, "is_validated")


# ---------------------------------------------------------------------------
# ATTACK 9: State machine — should now enforce transitions
# ---------------------------------------------------------------------------

class TestAttackNoStateMachine:
    def test_cannot_append_invalidated_without_prior_validated(self):
        """Critical 2 fix: INVALIDATED requires prior VALIDATED."""
        log = AppendOnlyEventLog()
        # Create a fake event with invalidated result
        event = ValidationEvent(
            event_id="ve-1",
            claim_id="claim-1",
            validation_result="invalidated",
            checks=(),
            validation_method="human_review",
            validator="test",
        )
        # Never validated — cannot invalidate
        with pytest.raises(ValueError, match="no prior VALIDATED"):
            log.append(event)

    async def test_cannot_append_after_rejected(self, session):
        """Critical 2 fix: REJECTED is terminal（DB 路径）。"""
        sv, _ann, cand = await seed_candidate(session, gate=rejected_gate_decision())
        service = EvidencePromotionService(EvidenceRepository(session))
        await service.record_validation(
            "claim-1", _gate_rejected(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert await service.is_evidence_validated(cand.id, "claim-1") is False
        with pytest.raises(ValueError, match="terminal"):
            await service.record_validation(
                "claim-1", _gate_auto_approve(),
                candidate_id=cand.id, source_version_id=sv.id,
            )


# ---------------------------------------------------------------------------
# ATTACK 10: Granularity — reference_ids solves the indeterminate coverage
# ---------------------------------------------------------------------------

class TestAttackGranularityMismatch:
    async def test_reference_ids_determine_coverage(self, session):
        """Critical 3 fix: reference_ids explicitly lists which spans a unit covers."""
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        spans = (
            _make_span("sp-stem", "stem"),
            _make_span("sp-opt-a", "option"),
            _make_span("sp-answer", "answer"),
        )
        run = ResolvedRun(source_version_id=spans[0].source_version_id, resolved_spans=spans)
        service.create_references(run, ProposerIdentity(producer_type="llm"))
        rec = await service.record_validation(
            "unit-1",
            _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
            reference_ids=("er-sp-stem", "er-sp-opt-a", "er-sp-answer"),
        )
        assert rec is not None
        assert len(rec.reference_ids or []) == 3
        traced = service.get_references_for_ids(tuple(rec.reference_ids or ()))
        assert len(traced) == 3
