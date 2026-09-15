# P3.2 / EB-004 Experimental Enforcement Verification — Scope Document

**Date**: 2026-09-15
**Status**: DRAFT — awaiting Owner review
**Authority**: Owner approval 2026-09-15 (EXPERIMENT ONLY)
**Prerequisites**: claude4-attribution.json paper names corrected (84fd39f)

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
Experimental Adapter (EXPERIMENT CONSTRUCT — not production code)
    ↓
Resolved Evidence (adapter output)
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
| Experimental Adapter | **EXPERIMENT CONSTRUCT** — must not become second V3 |
| Resolved Evidence | Adapter output (derived, not authoritative) |
| Gate decision | V3 formal |
| Admission request | V3 formal |

**Critical constraint**: Experimental Adapter must be clearly separated from production code. If adapter logic is needed in production, it must go through separate L2 Decision.

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

**bypass path count is the critical metric.** It directly tests BUG-V3-048: does Admission actually depend on Evidence Authority, or only on gate_decision?

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

## 6. Deliverables

1. Experiment script (experimental, not production)
2. Results JSON with per-attack-vector outcomes
3. Findings report (bypass path analysis)
4. State.yaml update (FACT entries, confidence=OBSERVED)

---

## 7. Constraints

- Zero production code modification
- Zero Frozen Spec modification
- Zero Producer Contract modification
- Zero Gate policy modification
- Zero Admission semantics modification
- No rule relaxation for higher pass rate
- Experiment results ≠ architecture Decision
- No automatic workaround on experiment failure
