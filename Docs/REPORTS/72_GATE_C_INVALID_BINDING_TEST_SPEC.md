# Gate C: Invalid Binding Evidence Test Specification (CORRECTED)

> **Core Principle**: Legal address != legal evidence
>
> **Correction**: Resolver does NOT reject invalid evidence. Gate marks as pending_review.

---

## 1. Objective

Verify that V3 correctly handles invalid binding evidence:
- 157 invalid/suspicious targets from B2-B5 corrections
- Resolver: structural validity only (no semantic validation)
- Gate: marks as `pending_review` (not `rejected`)
- Admission: requires manual review

---

## 2. Actual V3 Behavior

### Resolver (E)
```
Input: answer_zone + question_label
Output: ResolvedSpan (status=exact) if structurally valid
        UnresolvedReference if structurally invalid

Does NOT validate:
- Is this really answer content?
- Does it contain explanation markers?
- Is it a separator?
- Is it a question pattern?
```

### Gate (G)
```
Input: CompiledLeaf with answer text
Output: gate_decision

Grammar verification:
- single_choice/multiple_choice/true_false → True/None
- other types → None

None means: pending_review (not rejected)
```

### Admission
```
Input: candidate with gate_decision
Output: approve/reject

Only approves if gate_decision == auto_approve
Otherwise: pending_review → manual review
```

---

## 3. Invalid Binding Evidence Corpus

| Reason | Count | Description |
|--------|:-----:|-------------|
| WRONG_REGION | 56 | Content doesn't match expected format |
| EXPLANATION_REGION | 49 | Contains explanation markers |
| SEPARATOR_REGION | 27 | Points to markdown separators |
| QUESTION_REGION | 15 | Points to question patterns |
| SUSPICIOUS_CONTENT | 10 | Very short content (not definitive) |
| **Total** | **157** | |

---

## 4. Test Specification (Corrected)

### Test 4.1: Resolver Structural Validity

**Input**: Source with answer zone containing invalid content

**Expected Output**:
```
ResolvedRun:
  resolved_spans: [answer span with status=exact]
  unresolved_references: []
```

**Assertions**:
1. Resolver resolves answer span (structural validity)
2. No semantic validation performed
3. Status is "exact" (structurally valid)

### Test 4.2: Gate Grammar Verification

**Input**: Answer text with invalid content

**Expected Output**:
```
verify("single_choice", "【考点】...", labels) → None
verify("single_choice", "---", labels) → None
verify("single_choice", "A", labels) → True
```

**Assertions**:
1. Invalid content → None (pending_review)
2. Valid content → True (auto_approve candidate)
3. None is NOT False (not rejected)

### Test 4.3: Gate Decision

**Input**: Candidate with invalid answer content

**Expected Output**:
```
gate_decision:
  decision: "pending_review"
  reasons: ["leaf answer grammar: answer not expressible as canonical value"]
```

**Assertions**:
1. decision is "pending_review" (not "rejected")
2. reasons explain why
3. Candidate can be manually reviewed

### Test 4.4: Admission Block

**Input**: Attempt to auto-approve candidate with pending_review

**Expected Behavior**:
- `RepositoryError` raised
- `decision_status` remains `pending_review`
- No materialization occurs
- Manual review required

---

## 5. Security Invariants (Corrected)

### Invariant 1: No Auto-Approve for Invalid Evidence
```
For all invalid binding evidence targets:
  gate_decision.decision == "pending_review"
  # NOT auto_approve
```

### Invariant 2: Manual Review Required
```
For all invalid binding evidence targets:
  # Cannot be auto-approved
  # Requires human review
  # Reviewer can approve or reject
```

### Invariant 3: No Silent Materialization
```
For all invalid binding evidence targets:
  # No materialization without approval
  # approve() requires gate_decision=auto_approve or human approval
```

---

## 6. Test Execution Plan

### Phase 1: Unit Tests (Resolver)
```python
async def test_resolver_structural_validity():
    # Resolver resolves answer span for structurally valid input
    # Does NOT validate semantic content
    pass
```

### Phase 2: Unit Tests (Gate Grammar)
```python
async def test_grammar_invalid_content():
    # Invalid content → None (pending_review)
    # Valid content → True (auto_approve candidate)
    pass
```

### Phase 3: Integration Tests (Gate Decision)
```python
async def test_gate_pending_review():
    # Gate produces pending_review for invalid content
    # Not rejected, not auto_approve
    pass
```

### Phase 4: E2E Tests (Admission)
```python
async def test_admission_manual_review():
    # Cannot auto-approve pending_review
    # Requires human approval
    pass
```

---

## 7. Success Criteria (VERIFIED)

| Metric | Target | Actual | Status |
|--------|:------:|:------:|:------:|
| Invalid content → grammar None | All | 5/5 | PASS |
| Grammar None → pending_review | All | 5/5 | PASS |
| Invalid content → auto_approve | 0 | 0 | PASS |
| Invalid content → rejected | 0 | 0 | PASS |
| _leaf_grammar invalid → (False, ...) | All | 4/4 | PASS |
| _leaf_grammar valid → (True, '') | All | 1/1 | PASS |

**Test Evidence**: tests/test_gate_c_invalid_binding.py (11/11 PASS)

### Integration Test Results

**test_leaf_grammar_valid_content_passes**: PASS
- Valid content 'A' → (True, '')

**test_leaf_grammar_invalid_content_fails**: PASS
- Invalid content → (False, 'answer not expressible as canonical value')

**test_leaf_grammar_none_type_returns_none**: PASS
- Non-strict-auto type → None

**test_pending_review_blocks_auto_admission**: PASS
- verify() returns None for invalid content
- None ≠ False (pending_review, not rejected)

**test_decision_logic_pending_review_path**: PASS
- Grammar fail → auto_blockers → pending_review

---

## 8. Key Correction (RETRACTED)