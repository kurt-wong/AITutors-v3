# P3.2 / EB-004 Experimental Enforcement Verification — Scope Document

**Date**: 2026-09-15
**Status**: APPROVED WITH MINOR CLARIFICATIONS
**Authority**: Owner review 2026-09-15
**Prerequisites**: claude4-attribution.json paper names corrected (84fd39f)

## Owner Review Status

APPROVED WITH MINOR CLARIFICATIONS

This experiment validates enforcement behavior only.
It does not define Evidence Authority architecture,
Resolver boundary,
Producer Contract,
or future implementation decisions.

Experimental Adapter is an untrusted evidence producer.

Evidence Authority Validation is considered the control point under verification.

---

## 1. Scope

**Single question**: Can the Admission Boundary block Evidence that does not satisfy Evidence Authority requirements?

**Verifies**: Enforcement mechanism existence and effectiveness.

**Does NOT verify**:
- Evidence Authority final architecture design
- Whether Resolver should consume options_region
- How HTML should be handled
- How Producer Contract should be frozen

---

## 2. Inputs — Authority Chain

```text
SourceVersion (V3 formal object, sealed)
    ↓
Producer Evidence Region (from preprocessing manifest)
    ↓
Experimental Adapter (UNTRUSTED PRODUCER SIMULATION)
    ↓
Resolved Evidence (untrusted derived evidence)
    ↓
Evidence Authority Validation (CONTROL POINT UNDER VERIFICATION)
    ↓
Gate decision (V3 formal GateService)
    ↓
Admission request (V3 formal AdmissionService)
```

**Authority classification**:

| Object | Authority Level |
|---|---|
| SourceVersion | V3 formal (sealed, immutable) |
| Producer Evidence Region | Producer fact (from manifest) |
| Experimental Adapter | **UNTRUSTED** — no authority, producer simulation only |
| Resolved Evidence | **UNTRUSTED** derived evidence |
| Evidence Authority Validation | **CONTROL POINT** under verification |
| Gate decision | V3 formal |
| Admission request | V3 formal |

**Critical constraint**: Experimental Adapter has no authority. Its output must be treated as untrusted derived evidence. If adapter logic is needed in production, it must go through separate L2 Decision.

---

## 3. Metrics

| Metric | Definition | Target |
|---|---|---|
| valid evidence accepted | Legal Evidence passes Admission | 100% |
| invalid evidence rejected | Illegal Evidence blocked | 100% |
| unvalidated evidence rejected | Evidence without ValidationEvent blocked | 100% |
| cross-run evidence rejected | Evidence from different run blocked | 100% |
| mutated evidence rejected | Evidence modified after validation blocked | 100% |
| **bypass path count** | Paths that bypass Evidence Authority | **0** |

### Bypass Path Definition (frozen)

A bypass path exists when:

```text
Admission.success == true
AND
Evidence Authority validation == invalid OR absent
```

Any instance of illegal Evidence + Admission accepted counts as bypass.

**NOT counted as bypass**: Gate reject, Adapter failure, Validation failure.

---

## 4. Negative Acceptance — Attack Vectors

| ID | Attack | Expected Result |
|---|---|---|
| N1 | EvidenceClaim exists, but no ValidationEvent | REJECT |
| N2 | ValidationEvent exists, but invalid result | REJECT |
| N3 | Evidence from another run | REJECT |
| N4 | Evidence references wrong SourceVersion | REJECT |
| N5 | Evidence validity expired / invalidated | REJECT |
| N6 | Evidence payload mutated after validation | REJECT |
| **N7** | **Direct Admission attempt bypassing promotion** | **REJECT** |
| **N8** | **gate_decision=approve but Evidence Authority invalid** | **REJECT** |

**N7/N8 are core attack vectors.** They test whether Admission is controlled by Evidence Authority or solely by gate_decision.

---

## 5. Non-goals

This experiment does NOT decide:

- Whether options_region becomes a production Resolver input
- Whether HTML parsing belongs to Producer or Resolver
- Whether Resolver rules should change
- Whether Producer Contract should change
- Whether Evidence Authority architecture should be frozen
- Whether EB-005 should be implemented

**If experiment discovers issues**: OBSERVED → EVIDENCE → REPORT. No architecture changes.

---

## 6. Experiment Data Classification

Results must be classified into three levels. No mixing.

| Type | Meaning |
|---|---|
| OBSERVED | Direct experimental observation |
| INFERENCE | Analysis based on experimental results |
| DECISION | Architecture decision (Owner only) |

**Correct format**:
```text
OBSERVED: N8 admission accepted invalid evidence.
INFERENCE: Admission may depend only on gate_decision.
DECISION: Pending owner review.
```

**Incorrect format**:
```text
N8 failed. Therefore Admission must be redesigned.
```

---

## 7. Experimental Adapter Rules

### Allowed

- Construct valid evidence
- Construct invalid evidence
- Construct forged evidence
- Construct mutated evidence
- Construct stale evidence

### Forbidden

- Copy production Resolver
- Introduce preprocessing parser
- Auto-fix evidence
- Auto-fill metadata
- Use LLM to judge validity

**Reason**: Experiment tests whether Admission blocks wrong results, not whether adapter produces right results.

---

## 8. Deliverables

1. Experiment script (experimental, not production)
2. Results JSON with per-attack-vector outcomes
3. Findings report (bypass path analysis, OBSERVED/INFERENCE separated)
4. State.yaml update (FACT entries, confidence=OBSERVED)

---

## 9. Constraints

- Zero production code modification
- Zero Frozen Spec modification
- Zero Producer Contract modification
- Zero Gate policy modification
- Zero Admission semantics modification
- No rule relaxation for higher pass rate
- Experiment results ≠ architecture Decision
- No automatic workaround on experiment failure
