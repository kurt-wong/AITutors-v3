# B2-B5 Subjective / Sub-question / Material Domain Contract Adjudication (CORRECTED)

> **Core Principle**: Domain Contract First. We verify whether V3 can express these structures, NOT expand parser capability.
>
> **Binding Principle**: Legal address != legal evidence. answer_lines pointing to content does not mean that content IS the answer.
>
> **Correction**: Resolver does NOT reject invalid evidence. Gate marks as pending_review.

---

## 0. Formal Retraction of Original B2-B5 Conclusions

**Date**: 2026-09-11
**Status**: Original conclusions RETRACTED based on real test evidence

### Retracted Claims

| Original Claim | Status | Corrected Understanding |
|----------------|--------|------------------------|
| Resolver rejects invalid evidence | **RETRACTED** | Resolver only validates structural validity |
| Gate rejects invalid evidence | **RETRACTED** | Gate grammar returns None → pending_review |
| 157 targets automatically rejected | **RETRACTED** | 157 targets require manual review adjudication |

### Evidence for Retraction

**Test Evidence** (tests/test_gate_c_invalid_binding.py, 11/11 PASS):

1. **Resolver behavior**: All structurally-valid answer spans resolve with status=exact, regardless of semantic content
   - EXPLANATION_REGION → RESOLVED (exact)
   - SEPARATOR_REGION → RESOLVED (exact)
   - QUESTION_REGION → RESOLVED (exact)

2. **Gate grammar behavior**: Invalid content returns None (cannot determine), not False (rejected)
   - verify(single_choice, 【考点】..., labels) → None
   - verify(single_choice, ---, labels) → None

3. **Admission behavior**: Grammar failure → pending_review (not auto_approve, not rejected)
   - _leaf_grammar() converts None → (False, answer not expressible as canonical value)
   - False adds to auto_blockers → decision = pending_review

### Three-State Decision Model (Verified)

Grammar Result:
- True → valid → auto_approve
- False → invalid → pending_review
- None → cannot determine → pending_review

**Key Principle**: None ≠ False. Machine cannot determine ≠ Machine rejects.

### 157 Targets Status

**Status**: UNRESOLVED / REVIEW REQUIRED

**NOT proven**:
- All 157 are correct bindings
- All 157 are incorrect bindings
- All 157 can be auto-admitted
- All 157 will pass manual review

**Current route**: PENDING_REVIEW → manual adjudication required

---

## 1. Scope

Analyzed **706 targets** from the frozen corpus:

| Category | Description | Count |
|----------|-------------|-------|
| S1 | Standalone + Subjective | 469 |
| S2 | Composite + Sub-question | 94 |
| S3 | Composite + Material + Subjective | 143 |

---

## 2. Domain Contract Matrix (Corrected)

| Structure | Representable | Invalid Binding Evidence | Suspicious | Total |
|-----------|:------------:|:-----------------------:|:----------:|:-----:|
| S1: Standalone Subjective | 281 | 183 | 5 | 469 |
| S2: Composite + Sub-question | 79 | 10 | 5 | 94 |
| S3: Composite + Material + Subjective | 69 | 74 | 0 | 143 |
| **Total** | **429** | **267** | **10** | **706** |

---

## 3. Invalid Binding Evidence Breakdown

| Reason | Count | Description |
|--------|:-----:|-------------|
| EMPTY_REGION | 120 | S1 targets with no answer content (NOT invalid evidence) |
| WRONG_REGION | 56 | Content doesn't match expected answer format |
| EXPLANATION_REGION | 49 | Contains explanation markers (【考点】etc.) |
| SEPARATOR_REGION | 27 | Points to markdown separators (---) |
| QUESTION_REGION | 15 | Points to question patterns |
| SUSPICIOUS_CONTENT | 10 | Very short content (<5 chars) - NOT definitive |
| **Total** | **277** | |

**Gate C Corpus**: 157 targets (excluding EMPTY_REGION and SUSPICIOUS_CONTENT)

---

## 4. Key Architectural Finding (CORRECTED)

> **B2-B5 proves that V3 must verify the semantic validity of preprocessing evidence, not just structural validity.**

**Correction**: The verification happens at the **Gate level**, not the Resolver level.

### Resolver (E): Structural Validity Only
```
Does answer zone exist?
Is question number found?
Does NOT validate semantic content
```

### Gate (G): Semantic Validation
```
Grammar verification:
- single_choice/multiple_choice/true_false → True/None
- other types → None

None means: pending_review (not rejected)
```

### Admission
```
Only approves if gate_decision == auto_approve
Otherwise: pending_review → manual review
```

---

## 5. Domain Expressiveness (Scope-Bounded)

**Claim**: Schema can express S1/S2/S3 structures.

**Evidence**: 
- S1: 281 representable targets
- S2: 79 representable targets  
- S3: 69 representable targets

**Status**: PASS / TEST-EVIDENCED / SCOPE-BOUNDED

**Scope**: Only proves expressiveness for the audited structures in the frozen corpus.

**Does NOT prove**: 
- IR can project these structures
- Compiler can compile them
- Admission can correctly persist them

---

## 6. Frozen Testset Corrections

Applied adversarial review findings:
- **audit_version**: B2-B5-B-v2-corrected
- **Principle**: Legal address != legal evidence
- **Reclassified**: 49 EXPLANATION_REGION + 27 SEPARATOR_REGION + 15 QUESTION_REGION = 91 targets
- **Marked suspicious**: 10 SUSPICIOUS_CONTENT targets (not definitive invalid)

---

## 7. Gate B2-B5 Status (CORRECTED)

| Phase | Status | Notes |
|-------|--------|-------|
| B2-B5-A: Classification | **CLOSED / PASS** | 706 targets classified, adversarial-corrected |
| B2-B5-B: Domain Expressiveness | **PASS / SCOPE-BOUNDED** | Schema supports S1/S2/S3 |
| B2-B5-C: Invalid Manual Review | **PARTIAL** | Gate marks pending_review, not rejected |
| B2-B5-D: E2E Subjective Projection | **OPEN** | Need real IR projection test |

---

## 8. Gate C Status (CORRECTED)

**Corpus**: 157 invalid binding evidence targets

**Actual V3 Behavior**:
- Resolver: resolves answer span (structural validity only)
- Gate: marks as `pending_review` (not `rejected`)
- Admission: requires manual review

**Key Correction**: 
> "Resolver rejects invalid binding evidence" is **FALSE**
> 
> Correct: "Gate marks invalid binding evidence as pending_review"

**Unit Tests**: 6/6 pass (but tests use wrong format - see adversarial review)

---

## 9. Adversarial Review Findings

See `73_B2B5_GATE_C_ADVERSARIAL_REVIEW.md` for full findings.

**Key findings**:
1. Tests use `line_refs` format, Resolver expects `answer_zone` + `question_label`
2. Resolver does NOT validate semantic content
3. Gate grammar returns `None` (pending_review), not `False` (rejected)
4. Test assertions are too weak or have logic errors

---

## 10. Next Steps

### B2-B5-C: Invalid Manual Review (Continue)
1. Fix test format to use `answer_zone` + `question_label`
2. Add integration tests for Gate → Admission flow
3. Test full corpus with correct payload format

### B2-B5-D: E2E Subjective Projection
Select representative S1/S2/S3 targets and verify:
```
preprocessing evidence
    ↓
Resolver validation (structural only)
    ↓
ResolvedSpan
    ↓
IR projection
    ↓
Compiler
    ↓
Gate grammar → pending_review
    ↓
Manual review → approve/reject
```

---

## 11. Conclusion (CORRECTED)

**Domain Contract analysis: PASS (scope-bounded)**

**B2-B5 overall: NOT CLOSED** until:
1. Invalid binding evidence manual review flow verified
2. At least one S1/S2/S3 E2E projection demonstrated

**Core principle preserved**: 
> Preprocessing manifest is not source of truth. It is a Binding Claim that must be verified.
>
> Verification happens at Gate level (grammar → pending_review), not Resolver level.
