# Phase I-4 Closure: Evidence Diagnostic Experiment

Authority Level: L2 — Decision Record（formal phase closure；D-02 归层 2026-09-13）
Document Type: Decision Record
Normative: NO（记录阶段裁决，不定义新架构事实 — 90 §2 R2）
Gate State Authority: NO（唯一权威 = 82 §3）

Status: **CLOSED**
Date: 2026-09-10
Closure Type: Valid Negative Result
Evidence: `64_PHASE_I4_EVIDENCE_EVALUATION.md`

---

## 1. Closure Statement

Phase I-4 has completed a full architectural experiment loop:

```
Phase I-3  →  Source layout evidence preserved
Phase I-4-1  →  Evidence read path + diagnostic layer built
Phase I-4-2  →  Real math PDF replay executed
Measurement  →  42 ambiguous → 42 ambiguous (0% reduction)
Conclusion   →  Span-level layout evidence insufficient
```

**Phase I-4 PASSED as an architectural experiment.** The goal was never to force a positive outcome — it was to determine, with measured evidence, whether layout evidence has diagnostic value for the current failure mode. It does not.

---

## 2. Implementation Results

| Component | Result |
|-----------|--------|
| SourceSpan preservation (I-3) | **PASS** |
| Evidence read path (I-4-1) | **PASS** |
| Evidence diagnostic layer (I-4-1) | **PASS** |
| Empty marker defensive boundary | **PASS** |
| Real PDF replay (I-4-2) | **PASS** |
| Experiment input freeze | **PASS** |
| No weight tuning during experiment | **PASS** |
| Before/After measurement | **PASS** |

## 3. Experiment Results

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| marker_ambiguous | 42 | 42 | **0** |
| Unique evidence winner | N/A | 0 | **0%** |
| Tied top-2 scores | N/A | 34/42 | 81% |
| Correctness improvement | N/A | 0 | **0%** |

**Negative Result frozen:** Span-level layout evidence (font, size, flags, bbox, origin) is insufficient to distinguish semantic roles of numeric markers in mathematical PDFs.

---

## 4. Root Cause

Layout evidence answers: *"Where is this character and what does it look like?"*
It cannot answer: *"What role does this character play in the document?"*

The correct answer line for Q1 ("1. 已知弧长为5π...") ranked **123rd out of 190 candidates** because isolated numeric fragments (coordinates, fractions) scored 0.90 while the actual question start line scored only 0.30.

This is an **information insufficiency problem**, not an algorithm deficiency. No amount of weight tuning can derive semantic roles from geometric properties alone.

---

## 5. What Is NOT Closed

Phase I-4 closure does NOT mean:

- SourceSpan evidence is useless (it correctly identifies candidates with 100% recall)
- The Source evidence preservation layer was unnecessary (it provides the foundation for future context investigation)
- All PDF types would show the same result (only mathematical PDFs with dense numeric content were evaluated)
- The Resolver is broken (its fail-loud behavior is correct per V3 invariants)

---

## 6. Explicit Non-Next-Steps

Until new measured evidence emerges, the following are **prohibited**:

| Prohibited Action | Reason |
|-------------------|--------|
| Tune evidence scoring weights | No measured benefit to optimize |
| Add new span-level layout heuristics | Same information class, same limitation |
| Add special rules for specific markers ("1", "2", etc.) | Overfitting to single PDF |
| Expand `evidence.py` into decision logic | Violates §10.2 Diagnostic Boundary |
| Build Document Layout Engine | Violates §10.7 No Premature Expansion |
| Modify Resolver based on evidence scoring | Would not improve results |

---

## 7. Next Direction (Not Yet Authorized)

The confirmed finding is:

> **The bottleneck is not span-level geometry, but document/page/section context.**

The next investigation should follow the same first-principles pattern as I-3 and I-4:

```
I-3 asked:  Is layout information present in Source?     → YES
I-4 asked:  Is layout information sufficient?             → NO
I-5 should: Is contextual information already present?
```

**Phase I-5 Context Sufficiency Investigation** (NOT STARTED) would:

1. Audit existing SourceLine/SourceSpan context (neighboring lines, page boundaries, line position)
2. Measure whether question numbers exhibit sequential patterns (1→2→3...)
3. Determine if page-level structure (question pages vs answer pages) provides discrimination
4. Only THEN decide whether the existing Source evidence is sufficient or a minimal new layer is needed

**I-5 must NOT begin with code.** It must begin with a context audit of the same frozen PDF experiment.

---

## 8. Architecture Principle Frozen

From this experiment, a new architectural principle is established (§10.9):

> **Evidence Sufficiency Before Architecture Expansion** — Before introducing a new structural layer, the project MUST first determine whether the required information already exists in the current immutable Source evidence.

---

## 9. Evidence Artifacts

| Artifact | Location |
|----------|----------|
| Evaluation report | `Docs/V3_SPEC/64_PHASE_I4_EVIDENCE_EVALUATION.md` |
| Replay script | `backend/scripts/evidence_replay.py` |
| Evidence module | `backend/app/domains/resolver/evidence.py` |
| Evidence tests | `backend/tests/test_evidence.py` (21 tests) |
| Guardrails | `Docs/V3_SPEC/63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md` §10 |
