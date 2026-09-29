"""P1 authorized hardening: tz-safe review time + state machine keys.
Does NOT touch multi-blank / N-values / Frozen Spec semantics.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.domains.evidence.models import CheckResult, ValidationEvent, enforce_state_transition
from app.domains.gate.admission import _parse_review_time


def _ev(at, result="validated", claim="Q1"):
    return ValidationEvent(
        event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=claim,
        validation_result=result,
        checks=(CheckResult(check_id="X", result="pass"),),
        validation_method="frozen_header_rule", validator="gate/v1",
        validated_at=at,
    )


class TestParseReviewTimeUtc:
    def test_missing_returns_aware_utc(self):
        dt = _parse_review_time(None)
        assert dt.tzinfo is not None
        assert dt.utcoffset().total_seconds() == 0

    def test_naive_iso_treated_as_utc(self):
        dt = _parse_review_time("2026-09-29T12:00:00")
        assert dt.tzinfo is not None
        assert dt.utcoffset().total_seconds() == 0
        assert dt.hour == 12

    def test_aware_non_utc_converted(self):
        dt = _parse_review_time("2026-09-29T14:00:00+02:00")
        assert dt.utcoffset().total_seconds() == 0
        assert dt.hour == 12

    def test_naive_review_time_does_not_typeerror_in_proof_and_store_path(self):
        # proof helper accepts naive; parse path must too
        from app.domains.evidence.proof import _to_utc_iso
        naive = datetime(2026, 9, 29, 12, 0, 0)
        parsed = _parse_review_time(naive.isoformat())
        assert parsed.tzinfo is not None
        assert _to_utc_iso(naive) == _to_utc_iso(parsed)


class TestEnforceStateTransitionTzSafe:
    def test_mixed_naive_aware_existing_no_typeerror(self):
        naive = datetime(2026, 9, 29, 12, 0, 0)
        aware = datetime(2026, 9, 29, 13, 0, 0, tzinfo=timezone.utc)
        existing = (_ev(naive, "validated"), _ev(aware, "validated"))
        # mixed should not TypeError; latest by UTC-normalized key = aware 13:00
        with pytest.raises(ValueError, match="INVALIDATED"):
            enforce_state_transition(existing, "validated", "Q1")

    def test_naive_only_latest_still_terminal(self):
        naive_rej = datetime(2026, 9, 29, 12, 0, 0)
        existing = (_ev(naive_rej, "rejected"),)
        with pytest.raises(ValueError, match="terminal"):
            enforce_state_transition(existing, "validated", "Q1")
