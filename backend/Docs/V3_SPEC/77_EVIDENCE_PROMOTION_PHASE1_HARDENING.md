# Evidence Promotion Contract — Phase 1 Hardening Report

**Date**: 2026-09-13
**Status**: COMPLETE — All 6 adversarial gaps fixed, 616 tests pass
**Spec**: 75_EVIDENCE_PROMOTION_CONTRACT.md v1.1.0

---

## Summary

Phase 1 Hardening addresses all 6 must-fix gaps identified in the adversarial review.
Each fix is verified by adversarial tests that confirm the attack is now blocked.

| Gap | Severity | Fix | Status |
|-----|----------|-----|--------|
| Append-only not enforced | CRITICAL | AppendOnlyEventLog (tuple-based) | ✅ FIXED |
| State machine not enforced | CRITICAL | _check_state_transition() | ✅ FIXED |
| ValidationEvent ↔ EvidenceReference no link | CRITICAL | reference_ids field | ✅ FIXED |
| validation_method hardcoded | HIGH | _derive_validation_method() | ✅ FIXED |
| checks non-structured | HIGH | CheckResult dataclass | ✅ FIXED |
| ProposerIdentity wrong | HIGH | producer_type="llm" | ✅ FIXED |
| Run accumulation | MEDIUM | Fresh service per run | ✅ FIXED |
| Latest by position not time | MEDIUM | max(validated_at) | ✅ FIXED |

---

## Fix Details

### Critical 1: Append-only Enforcement

**Problem**: `_validation_events` was a mutable Python list. External code could `.clear()`, `.append()`, or `.reverse()` it.

**Fix**: `AppendOnlyEventLog` class backed by immutable tuples.

```python
class AppendOnlyEventLog:
    def __init__(self):
        self._events: tuple[ValidationEvent, ...] = ()
    
    def append(self, event: ValidationEvent) -> None:
        self._events = self._events + (event,)  # creates new tuple
    
    @property
    def events(self) -> tuple[ValidationEvent, ...]:
        return self._events
```

**Verification**: 
- `test_clear_internal_log_blocked` — no clear() method exists
- `test_tuple_is_immutable` — tuple has no append/clear/reverse methods

---

### Critical 2: State Machine Enforcement

**Problem**: Any ValidationEvent could be appended at any time. REJECTED was not terminal. INVALIDATED could be appended without prior VALIDATED.

**Fix**: `_check_state_transition()` enforces allowed transitions:

```
proposed → validated (first auto_approve)
proposed → rejected (first reject)
validated → invalidated (source changed)
rejected → (terminal — no more events)
invalidated → (terminal — no more events)
```

**Verification**:
- `test_state_machine_rejected_terminal` — cannot append after REJECTED
- `test_cannot_append_invalidated_without_prior_validated` — INVALIDATED requires VALIDATED
- `test_state_machine_blocks_rejected_after_validated` — VALIDATED → only INVALIDATED

---

### Critical 3: ValidationEvent ↔ EvidenceReference Linking

**Problem**: ValidationEvent.claim_id was unit_id, EvidenceReference had span_id. No field connected them.

**Fix**: Added `reference_ids: tuple[str, ...]` field to ValidationEvent.

```python
@dataclass(frozen=True)
class ValidationEvent:
    ...
    reference_ids: tuple[str, ...] = ()  # links to EvidenceReference IDs
```

GateService now computes reference_ids when recording validation:

```python
span_ids = _extract_unit_span_ids(root, compiled)
ref_ids = tuple(f"er-{sid}" for sid in span_ids)
self._evidence.record_validation(root.unit_id, gate, reference_ids=ref_ids)
```

**Verification**:
- `test_validation_event_traces_to_evidence_reference` — can trace event → references
- `test_can_determine_which_spans_were_validated` — coverage is determinate
- `test_reference_ids_determine_coverage` — 3 spans explicitly linked

---

### High 4: validation_method Derivation

**Problem**: `validation_method` was hardcoded to "frozen_header_rule" for all outcomes.

**Fix**: `_derive_validation_method()` derives from gate layer statuses:

```python
def _derive_validation_method(gate_decision: dict) -> str:
    layers = gate_decision.get("layers", {})
    
    provenance = layers.get("provenance", {})
    if provenance.get("status") == "fail":
        return "byte_proven"
    
    structural = layers.get("structural", {})
    semantic = layers.get("semantic", {})
    if structural.get("status") == "fail" or semantic.get("status") == "fail":
        return "structural_consistency"
    
    return "frozen_header_rule"
```

**Verification**:
- `test_provenance_fail_derives_byte_proven` — provenance fail → byte_proven
- `test_structural_fail_derives_structural_consistency` — structural fail → structural_consistency
- `test_auto_approve_derives_frozen_header_rule` — all pass → frozen_header_rule

---

### High 5: Structured Check IDs

**Problem**: `checks_passed`/`checks_failed` contained narrative strings (50+ chars), not machine-parseable check IDs.

**Fix**: `CheckResult` frozen dataclass separates check_id from detail:

```python
@dataclass(frozen=True)
class CheckResult:
    check_id: str       # "TEXT_HASH_MATCH", "ROLE_OVERLAP", etc.
    result: str         # "pass" | "fail"
    detail: str | None = None  # human-readable description
```

ValidationEvent now uses `checks: tuple[CheckResult, ...]`, with derived properties:

```python
@property
def checks_passed(self) -> tuple[str, ...]:
    return tuple(c.check_id for c in self.checks if c.result == "pass")

@property
def checks_failed(self) -> tuple[str, ...]:
    return tuple(c.check_id for c in self.checks if c.result == "fail")
```

**Verification**:
- `test_checks_are_structured_not_narrative` — all checks are CheckResult objects
- `test_checks_failed_are_structured` — check IDs are short strings

---

### High 6: ProposerIdentity

**Problem**: GateService hardcoded `producer_type="native_parser"`. But annotation payload was LLM-produced.

**Fix**: Changed to `producer_type="llm"`:

```python
proposer = ProposerIdentity(
    producer_type="llm",  # was "native_parser"
    pipeline_version=RESOLVER_VERSION,
)
```

**Verification**:
- `test_gate_service_uses_llm_producer` — source contains `producer_type="llm"`

---

### Medium 7: Latest by Timestamp

**Problem**: `is_evidence_validated` used `events[-1]` (list position), not timestamp.

**Fix**: Uses `max(events, key=lambda e: e.validated_at)`:

```python
def is_evidence_validated(self, claim_id: str) -> bool:
    events = self.get_events_for_claim(claim_id)
    if not events:
        return False
    latest = max(events, key=lambda e: e.validated_at)  # timestamp, not position
    return latest.validation_result == "validated"
```

**Verification**:
- `test_timestamp_order_determines_latest` — out-of-order timestamps handled correctly

---

### Medium 9: Run Accumulation

**Problem**: `EvidencePromotionService` was created in `__init__`, accumulating across `run()` calls.

**Fix**: Fresh service created per `run()` call:

```python
async def run(self, ...):
    ...
    self._evidence = EvidencePromotionService()  # fresh per run
    ...
```

**Verification**:
- `test_fresh_service_per_run` — source contains `self._evidence = EvidencePromotionService()` inside run()

---

## Test Results

### Phase 1 Hardening Tests: 61 passed

```
tests/test_evidence_promotion.py: 36 passed
tests/test_evidence_adversarial.py: 25 passed (all attacks BLOCKED)
```

### Full Regression: 616 passed

```
tests/: 616 passed, 8 warnings in 57.41s
```

---

## Files Modified

| File | Change |
|------|--------|
| `app/domains/evidence/models.py` | Added CheckResult, AppendOnlyEventLog; updated ValidationEvent |
| `app/domains/evidence/promotion.py` | Added state machine, validation_method derivation, structured checks |
| `app/domains/evidence/__init__.py` | Exported CheckResult, AppendOnlyEventLog |
| `app/domains/gate/service.py` | Fixed ProposerIdentity, added reference_ids, per-run isolation |
| `tests/test_evidence_promotion.py` | Updated for new interface |
| `tests/test_evidence_adversarial.py` | Updated to verify attacks are blocked |

---

## Remaining Phase 2 Items

- EvidenceProposal / EvidenceClaim dataclasses
- DB persistence for ValidationEvent
- INVALIDATED complete support (human_review path)
- EvidenceBundle for unit-level grouping
