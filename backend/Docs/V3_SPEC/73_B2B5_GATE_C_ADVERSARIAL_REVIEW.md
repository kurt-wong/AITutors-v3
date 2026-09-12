# B2-B5 / Gate C Adversarial Review

> **Date**: 2026-09-11
> **Principle**: Every conclusion must have real test evidence. No speculation.

---

## 1. Executive Summary

**B2-B5 claim "Resolver will reject invalid binding evidence" is FALSE.**

The Resolver only validates structural validity, not semantic validity. The Gate marks invalid content as `pending_review`, not `rejected`.

---

## 2. Adversarial Findings

### Attack 1: Test Format Error

**Claim**: Gate C tests verify Resolver rejection.

**Finding**: Tests use `answer_lines` format, but Resolver expects `answer_zone` + `question_label`.

**Evidence**:
```python
# Test uses:
"answer": {"answer_zone": "answer_lines", "line_refs": ["P1L006", "P1L007"]}

# Resolver expects:
"answer": {"answer_zone": "inline_answer", "question_label": "1"}
```

**Result**: Tests are testing the WRONG thing.

---

### Attack 2: Resolver Does NOT Validate Semantic Content

**Claim**: Resolver rejects invalid binding evidence.

**Finding**: Resolver resolves answer spans with status "exact" even for invalid content.

**Evidence**:
```
EXPLANATION_REGION: RESOLVED (status=exact)
SEPARATOR_REGION: RESOLVED (status=exact)
QUESTION_REGION: RESOLVED (status=exact)
SUSPICIOUS_CONTENT: RESOLVED (status=exact)
WRONG_REGION: RESOLVED (status=exact)
```

**Result**: 5/5 invalid content cases are RESOLVED, not rejected.

---

### Attack 3: Gate Grammar Returns None, Not False

**Claim**: Gate rejects invalid binding evidence.

**Finding**: Gate grammar returns `None` for invalid content, which means `pending_review`, not `rejected`.

**Evidence**:
```
"【考点】..." → None (pending_review)
"---" → None (pending_review)
"【解答】..." → None (pending_review)
```

**Result**: Invalid content goes to manual review, not automatic rejection.

---

### Attack 4: Test Assertions Too Weak

**Claim**: Tests verify rejection.

**Finding**: 4/5 assertions are too weak or have logic errors.

**Evidence**:
- `test_explanation_region_rejected`: allows partial overlap
- `test_separator_region_rejected`: allows separator if other lines exist
- `test_question_region_rejected`: logic error (checks unresolved only if no spans)
- `test_suspicious_content_needs_review`: vacuous (always true)

**Result**: Tests would pass even if Resolver auto-resolves everything.

---

### Attack 5: Missing Test Coverage

**Claim**: Gate C corpus has 157 targets.

**Finding**: 
- WRONG_REGION (56 targets): NO test
- Integration test: NONE
- Full corpus test: NONE

**Result**: Test coverage is incomplete.

---

## 3. Corrected Architecture Understanding

```
Resolver (E): Structural validity only
  - Does answer zone exist?
  - Is question number found?
  - Does NOT validate semantic content

Gate (G): 
  - Structural: spans traceable
  - Provenance: resolution exact/normalized
  - Semantic: composite consistency
  - Admission: grammar → None = pending_review

Admission: Only approves if Gate says auto_approve
```

---

## 4. Key Principle Clarification

**"Legal address ≠ legal evidence"** is enforced by:
- **Gate grammar** (not Resolver)
- Invalid content → `pending_review` (not `rejected`)
- Manual review required

**Resolver design**: "Can fail, but cannot guess"
- Validates structural validity only
- Does NOT make semantic judgments

---

## 5. B2-B5 Status Correction

| Phase | Original Claim | Corrected Status |
|-------|---------------|------------------|
| B2-B5-C: Invalid Fail-Closed | Resolver rejects 157 targets | **FALSE** - Resolver resolves them |
| Gate C: Reject invalid | Gate rejects | **FALSE** - Gate marks pending_review |

---

## 6. What This Means

1. **Invalid binding evidence will NOT be automatically rejected**
2. **It will be marked as pending_review for manual review**
3. **This is correct behavior for the architecture**
4. **The "fail-closed" principle is at the Gate level, not Resolver level**

---

## 7. Recommendations

1. **Update Gate C test specification** to reflect actual behavior
2. **Rename B2-B5-C** from "Invalid Fail-Closed" to "Invalid Manual Review"
3. **Add integration tests** for Gate → Admission flow
4. **Test full corpus** with correct payload format

---

## 8. Integration Test Evidence (VERIFIED)

**Date**: 2026-09-11
**Test File**: tests/test_gate_c_invalid_binding.py
**Result**: 11/11 PASS

### Integration Tests Added

**Test: test_leaf_grammar_valid_content_passes**
- Input: Valid content 'A' for single_choice
- Expected: (True, '')
- Actual: PASS

**Test: test_leaf_grammar_invalid_content_fails**
- Input: Invalid content (【考点】..., ---, 2, not an answer format)
- Expected: (False, 'answer not expressible as canonical value')
- Actual: PASS (4/4 cases)

**Test: test_leaf_grammar_none_type_returns_none**
- Input: Non-strict-auto type (subjective_short)
- Expected: None
- Actual: PASS

**Test: test_pending_review_blocks_auto_admission**
- Input: verify() with invalid content
- Expected: None (cannot determine)
- Actual: PASS
- Key: None ≠ False (pending_review, not rejected)

**Test: test_decision_logic_pending_review_path**
- Input: Grammar fail → auto_blockers
- Expected: decision = pending_review
- Actual: PASS
- Verified: pending_review ≠ auto_approve, pending_review ≠ rejected

### Formal Retraction Confirmed

**Original B2-B5 claims RETRACTED**:

| Claim | Status | Evidence |
|-------|--------|----------|
| Resolver rejects invalid evidence | RETRACTED | 5/5 invalid content resolved |
| Gate rejects invalid evidence | RETRACTED | Grammar returns None, not False |
| 157 targets automatically rejected | RETRACTED | All go to pending_review |

**Corrected understanding**:
- Resolver: structural validity only
- Gate: grammar None → pending_review
- Admission: requires manual review for pending_review

### 157 Targets Status

**Status**: UNRESOLVED / REVIEW REQUIRED

**NOT proven**:
- All 157 are correct bindings
- All 157 are incorrect bindings
- All 157 can be auto-admitted
- All 157 will pass manual review

**Current route**: PENDING_REVIEW → manual adjudication required

---

## 9. Related Documents

- `71_B2B5_SUBJECTIVE_SUBQUESTION_ADJUDICATION.md` - B2-B5 adjudication
- `72_GATE_C_INVALID_BINDING_TEST_SPEC.md` - Gate C test specification
- `gate_c_invalid_binding_corpus.json` - Gate C corpus
