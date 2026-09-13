# Phase 1 Hardening — Adversarial Review Report

**Date**: 2026-09-13
**Status**: COMPLETE — 24 adversarial tests executed
**Result**: 9 confirmed gaps (2 HIGH now FIXED), 5 attacks blocked, 5 edge cases noted
**Update**: HIGH severity gaps fixed in `79_PHASE1_HIGH_SEVERITY_FIXES.md`

---

## Executive Summary

Phase 1 Hardening successfully fixed the original 6 CRITICAL/HIGH gaps. However, adversarial review reveals **9 new gaps** — most are MEDIUM/LOW severity, but 2 are HIGH:

1. **Direct attribute reassignment bypasses append-only** (HIGH) — ✅ **FIXED**
2. **Direct log append bypasses state machine** (HIGH) — ✅ **FIXED**

These gaps existed because Python's attribute system allows instance-level mutations that bypass the tuple-based append-only design.

**Fix Summary** (see `79_PHASE1_HIGH_SEVERITY_FIXES.md`):
- HIGH-1: `__slots__` + name mangling prevents attribute reassignment
- HIGH-2: State machine moved into `AppendOnlyEventLog.append()`

---

## Confirmed Gaps

### HIGH Severity

#### Gap 1: Direct Attribute Reassignment Bypasses Append-only — ✅ FIXED

**Test**: `test_direct_attribute_reassignment_blocked`

**Attack**:
```python
log = AppendOnlyEventLog()
log.append(event)
log._events = ()  # Now raises AttributeError
```

**Fix** (see `79_PHASE1_HIGH_SEVERITY_FIXES.md`):
- `__slots__` prevents attribute reassignment
- Name mangling (`__events`) makes direct access harder
- Returns immutable tuple snapshot

**Result**: ✅ Attack blocked

**Root Cause**: Python allows instance attribute reassignment. The tuple-based approach only prevents mutation via list methods (`.clear()`, `.append()`, `.reverse()`), not direct attribute reassignment.

**Impact**: Evidence authority can be destroyed by reassigning `_events` to empty tuple.

**Remediation**: Use `__slots__` or property setter to prevent attribute reassignment:
```python
class AppendOnlyEventLog:
    __slots__ = ('__events',)
    
    def __init__(self):
        object.__setattr__(self, '_AppendOnlyEventLog__events', ())
    
    def append(self, event):
        object.__setattr__(self, '_AppendOnlyEventLog__events', 
                          self.__events + (event,))
    
    @property
    def events(self):
        return self.__events
```

---

#### Gap 2: Direct Log Append Bypasses State Machine — ✅ FIXED

**Tests**: `test_bypass_log_via_direct_append_blocked`, `test_direct_log_append_bypasses_state_machine_blocked`

**Attack**:
```python
service = EvidencePromotionService()
service.record_validation("c1", _gate_rejected())
# Append validated via direct log access (bypasses state machine)
service._validation_log.append(fake_event)
# Now raises ValueError: Claim 'c1' is REJECTED (terminal)
```

**Fix** (see `79_PHASE1_HIGH_SEVERITY_FIXES.md`):
- State machine check moved into `AppendOnlyEventLog.append()`
- Direct calls to `append()` cannot bypass state machine
- Architecture: EventLog is Evidence Authority Ledger

**Result**: ✅ Attack blocked

---

### MEDIUM Severity

#### Gap 3: Fake Reference IDs Accepted

**Test**: `test_fake_reference_ids_accepted`

**Attack**:
```python
event = service.record_validation("c1", gate, reference_ids=("er-fake-1",))
# Event stores fake reference_ids
traced = service.get_references_for_ids(event.reference_ids)
# Returns empty — but event still stores fake IDs
```

**Root Cause**: No validation that `reference_ids` actually correspond to existing `EvidenceReference` objects.

**Impact**: ValidationEvent can reference non-existent EvidenceReferences, breaking the audit trail.

**Remediation**: Validate reference_ids before storing:
```python
def record_validation(self, claim_id, gate_decision, validator="gate/v1", reference_ids=()):
    # Validate reference_ids exist
    if reference_ids:
        existing_ids = {r.reference_id for r in self._evidence_references}
        invalid = set(reference_ids) - existing_ids
        if invalid:
            raise ValueError(f"Invalid reference_ids: {invalid}")
    ...
```

---

#### Gap 4: Empty Layers Dict + Rejected Gets Wrong Method

**Test**: `test_empty_layers_dict_with_rejected`

**Attack**:
```python
gate = {"decision": "rejected", "layers": {}}
method = _derive_validation_method(gate)
# Returns "frozen_header_rule" — WRONG!
```

**Root Cause**: `_derive_validation_method` returns default "frozen_header_rule" when layers dict is empty, even for rejected decisions.

**Impact**: validation_method is misleading for rejected decisions with no layer information.

**Remediation**: Raise error or return more specific method:
```python
def _derive_validation_method(gate_decision: dict) -> str:
    layers = gate_decision.get("layers", {})
    if not layers:
        if gate_decision.get("decision") == "rejected":
            raise ValueError("Cannot derive validation_method: rejected with no layer info")
        return "frozen_header_rule"
    ...
```

---

#### Gap 5: Unexpected Layer Status Not Handled

**Test**: `test_unexpected_layer_status`

**Attack**:
```python
gate = {
    "decision": "rejected",
    "layers": {
        "structural": {"status": "unknown", "reasons": []},
        ...
    },
}
method = _derive_validation_method(gate)
# Returns "frozen_header_rule" — unexpected status ignored
```

**Root Cause**: `_derive_validation_method` only checks for `status == "fail"`, ignores other values.

**Impact**: Unexpected layer statuses are silently ignored, potentially returning wrong validation_method.

**Remediation**: Validate layer status values:
```python
VALID_LAYER_STATUSES = frozenset({"pass", "fail"})

def _derive_validation_method(gate_decision: dict) -> str:
    layers = gate_decision.get("layers", {})
    for layer_name, layer_data in layers.items():
        status = layer_data.get("status")
        if status not in VALID_LAYER_STATUSES:
            raise ValueError(f"Invalid layer status {status!r} in {layer_name}")
    ...
```

---

#### Gap 6: LLM Model Name Not Captured

**Test**: `test_llm_model_name_not_captured`

**Evidence**:
```python
# In GateService.run():
proposer = ProposerIdentity(
    producer_type="llm",
    pipeline_version=RESOLVER_VERSION,
    # model= NOT passed!
)
```

**Root Cause**: ProposerIdentity created without `model` parameter.

**Impact**: Provenance incomplete — cannot determine which LLM model produced the annotation.

**Remediation**: Pass LLM model name from annotation metadata:
```python
proposer = ProposerIdentity(
    producer_type="llm",
    model=ann.model_config_hash,  # or extract model name
    pipeline_version=RESOLVER_VERSION,
)
```

---

#### Gap 7: Pipeline Version Is Resolver Version, Not LLM Version

**Test**: `test_pipeline_version_is_resolver_version`

**Evidence**:
```python
proposer = ProposerIdentity(
    producer_type="llm",
    pipeline_version=RESOLVER_VERSION,  # This is resolver version!
)
```

**Root Cause**: `pipeline_version` set to `RESOLVER_VERSION`, not annotation/LLM version.

**Impact**: Provenance incorrect — records resolver version instead of LLM/annotation version.

**Remediation**: Use annotation version:
```python
proposer = ProposerIdentity(
    producer_type="llm",
    model=ann.model_config_hash,
    pipeline_version=ann.prompt_version,  # or annotation schema version
)
```

---

### LOW Severity

#### Gap 8: Reference ID Format Not Enforced

**Test**: `test_reference_id_format_not_enforced`

**Attack**:
```python
event = service.record_validation("c1", gate, reference_ids=("wrong-format", "er-sp-1"))
# Event stores wrong-format reference_ids
assert "wrong-format" in event.reference_ids  # SUCCEEDS
```

**Root Cause**: No format validation on reference_ids.

**Impact**: Minor — allows inconsistent reference_id formats.

**Remediation**: Validate reference_id format:
```python
def _validate_reference_id(ref_id: str) -> bool:
    return ref_id.startswith("er-") and len(ref_id) > 3
```

---

#### Gap 9: Check ID Not Validated

**Test**: `test_check_id_not_validated`

**Attack**:
```python
c = CheckResult(check_id="arbitrary string with spaces", result="pass")
# SUCCEEDS — no format validation
```

**Root Cause**: No format validation on check_id.

**Impact**: Minor — allows inconsistent check_id formats.

**Remediation**: Validate check_id format:
```python
def __post_init__(self):
    if not self.check_id.replace("_", "").isalnum():
        raise ValueError(f"Invalid check_id format: {self.check_id}")
```

---

## Blocked Attacks (Fixes Working)

| Attack | Test | Result |
|--------|------|--------|
| Tuple element mutation | `test_tuple_element_mutation_blocked` | BLOCKED |
| Manipulated timestamps | `test_manipulated_timestamps_confuse_state_machine` | BLOCKED |
| Future timestamp wins | `test_future_timestamp_wins` | BLOCKED |
| Past timestamp loses | `test_past_timestamp_loses` | BLOCKED |
| Invalid decision | `test_invalid_decision_raises` | BLOCKED |

---

## Edge Cases (Not Gaps)

| Edge Case | Test | Behavior |
|-----------|------|----------|
| Equal timestamps | `test_equal_timestamps_ambiguous` | max() returns first |
| Missing layers dict | `test_missing_layers_dict` | Returns default |
| Multiple layers fail | `test_multiple_layers_fail` | Provenance checked first |
| Detail contains narrative | `test_detail_can_contain_narrative` | Allowed (by design) |
| Extract checks missing layers | `test_extract_checks_with_missing_layers` | Generic handling |

---

## Recommendations

### Immediate (Before C-2 157 E2E)

1. **Fix Gap 1**: Use `__slots__` to prevent attribute reassignment
2. **Fix Gap 2**: Move state machine check into `AppendOnlyEventLog.append()`

### Short-term (Before Gate C Closure)

3. **Fix Gap 3**: Validate reference_ids exist before storing
4. **Fix Gap 4**: Raise error for rejected with no layer info
5. **Fix Gap 5**: Validate layer status values
6. **Fix Gap 6**: Pass LLM model name
7. **Fix Gap 7**: Use annotation version, not resolver version

### Long-term (Phase 2)

8. **Fix Gap 8**: Validate reference_id format
9. **Fix Gap 9**: Validate check_id format

---

## Conclusion

Phase 1 Hardening successfully fixed the original 6 CRITICAL/HIGH gaps. The new adversarial review reveals 9 additional gaps, most are MEDIUM/LOW severity. The 2 HIGH severity gaps (attribute reassignment, direct log append) should be fixed before proceeding to C-2 157 E2E.

**Test Evidence**: 24 adversarial tests executed, 9 confirmed gaps, 5 attacks blocked.
