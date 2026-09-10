# Phase I-4 Evidence Utilization Evaluation

Status: COMPLETE
Date: 2026-09-10
Experiment: I-4-2 Real PDF Replay
Conclusion: **Layout evidence provides NO measurable diagnostic value for current mathematical PDF marker ambiguity.**

---

## 1. Experiment Setup (Frozen Input)

### 1.1 Input Freeze

| Item | Value |
|------|-------|
| PDF | `af7c5353bd59a982268a81f9de9d68ade70ff8211a42955c22ff4af7664c6e38.pdf` |
| PDF SHA256 | `af7c5353bd59a982268a81f9de9d68ade70ff8211a42955c22ff4af7664c6e38` |
| Content | 2026 北京北师大实验中学高一（下）阶段测试一 数学 |
| Pages | 11 (questions 1-4 + answers 5-11) |
| source_version_id | `fa58a2d0-a116-495d-aa07-3f612b976402` |
| Lines | 2,377 |
| Spans | 3,641 |
| Figures | 11 |
| annotation_id | `932543ee-47ff-47e2-8fb4-6cf6769deb7f` |
| Annotation units | 19 questions (Q1-Q19) |
| Resolver targets | 51 (19 stem + 32 option) |

### 1.2 Algorithm Freeze

| Item | Value |
|------|-------|
| evidence.py commit | `7b5e8a8` + empty-marker fix |
| Weight constants | `_WEIGHT_ISOLATED_SPAN=0.3, _WEIGHT_FEW_SPANS=0.1, _WEIGHT_SMALL_BBOX=0.15, _WEIGHT_BOLD=0.1, _WEIGHT_EXACT_TEXT_MATCH=0.35, _WEIGHT_STARTS_WITH_MARKER=0.15` |
| Thresholds | `_SMALL_BBOX_THRESHOLD=500.0, _FEW_SPANS_THRESHOLD=2, _UNIQUE_GAP_THRESHOLD=0.2` |
| Weights tuned during experiment | **NO** |

---

## 2. Before: SourceResolver Baseline

| Metric | Value |
|--------|-------|
| Total references | 51 |
| Resolved | 9 |
| Unresolved | 42 |
| Resolution rate | 17.6% |
| Classification | `marker_ambiguous`: 42 |
| By role | stem: 10, option: 32 |

All 42 unresolved references are classified as `marker_ambiguous` — the Resolver found multiple candidate lines for each marker and could not disambiguate.

---

## 3. After: Evidence-Aware Analysis

| Metric | Value |
|--------|-------|
| Total analyzed | 42 |
| Unique with evidence | **0** |
| Still ambiguous | **42** |
| Unique rate | **0.0%** |

### 3.1 Score Distribution (top candidate)

| Score | Count | Interpretation |
|-------|-------|----------------|
| 0.90 | 33 | isolated + few_spans + small_bbox + exact_match |
| 0.70 | 8 | fewer factors hit |
| 0.40 | 1 | minimal factors |

### 3.2 Tie Analysis

| Metric | Value |
|--------|-------|
| Tied top-2 scores | **34/42 (81%)** |
| Meaning | Evidence scoring cannot distinguish between candidates |

### 3.3 Candidate Count Distribution

| Candidates | Refs |
|------------|------|
| 5-12 | 28 |
| 20 | 8 |
| 45-54 | 4 |
| 127-288 | 3 |

---

## 4. Root Cause Analysis

### 4.1 The Fundamental Problem

The math PDF contains thousands of isolated numeric spans. For marker "1":

| Rank | Line | Score | Text | Actual meaning |
|------|------|-------|------|----------------|
| 1 | P1L015 | 0.90 | "1" | Coordinate value in Q2 |
| 2 | P1L030 | 0.90 | "1" | Fraction numerator in Q2 options |
| 3 | P1L063 | 0.90 | "1" | Another numeric fragment |
| ... | ... | ... | ... | ... |
| **123** | **P1L006** | **0.30** | **"1. 已知弧长为5π..."** | **Actual Q1 start** |

The correct answer (P1L006) ranks **123rd out of 190** because:
- It is NOT an isolated span (contains full question text)
- It does NOT exactly match "1" (it's "1. 已知弧长...")
- It only gets `starts_with_marker` (0.15) + `small_bbox` (0.15) = 0.30

Meanwhile, isolated "1" spans get `isolated_span` (0.3) + `few_spans` (0.1) + `small_bbox` (0.15) + `exact_text_match` (0.35) = 0.90.

### 4.2 Why Layout Evidence Fails Here

The evidence scoring model assumes:

> "A question number is likely an isolated, bold, small-bbox span that exactly matches the marker."

This assumption is **wrong for math PDFs** because:

1. **Math formulas produce thousands of isolated numeric spans** — coordinates, fractions, exponents, subscripts all appear as single-character spans
2. **Question numbers are embedded in text lines** — "1. 已知弧长..." is a multi-span line, not an isolated span
3. **Layout evidence alone cannot distinguish semantic roles** — "1" as question number vs "1" as coordinate value requires contextual understanding, not geometric properties

### 4.3 What Evidence CAN Tell Us

The evidence scoring successfully identifies:
- Which lines contain the marker text (candidate generation: 100% recall)
- Span-level properties (font, size, bold, bbox)
- Structural properties (isolated vs embedded)

But it **cannot** determine:
- Which occurrence is the semantically correct one
- Whether "1" means "question 1" or "coordinate 1" or "fraction 1/2"

---

## 5. Evaluation Metrics (§10.5 Required)

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total references | 51 | 51 | 0 |
| Resolved | 9 | 9 | 0 |
| marker_ambiguous | 42 | 42 | 0 |
| Unresolved | 42 | 42 | 0 |
| Evidence candidates found | N/A | 42/42 | 100% recall |
| Unique evidence winner | N/A | **0** | **0%** |
| Ties | N/A | 34 | 81% |
| Invalid markers | 0 | 0 | 0 |
| False improvement | N/A | 0 | 0 (no improvement claimed) |
| Correctness improvement | N/A | **0** | **0%** |

**Ambiguity reduction: 0**
**Correctness improvement: 0**

---

## 6. Conclusion (§10.8)

### Verdict: **Option 3 — Layout evidence has limited value for current mathematical PDF failures.**

The experiment conclusively demonstrates:

1. **Evidence scoring achieves 0% unique identification** on real math PDF data
2. **81% of candidates are tied** — the scoring model cannot differentiate
3. **Correct answers rank very low** (123/190, 165/288) because they don't match the "isolated span" heuristic
4. **The fundamental issue is semantic, not geometric** — distinguishing "question number 1" from "coordinate value 1" requires contextual/positional understanding that layout evidence alone cannot provide

### What This Means for V3 Architecture

The SourceSpan evidence (font, size, flags, bbox) is:
- ✅ Correctly preserved (Phase I-3)
- ✅ Correctly readable (Phase I-4-1)
- ❌ **Insufficient to resolve marker ambiguity** (Phase I-4-2)

The bottleneck is NOT missing evidence — it's missing **contextual reasoning** about what a marker means in its document context.

### Recommended Next Steps

1. **Do NOT modify Resolver** based on evidence scoring — it would not improve results
2. **Do NOT expand evidence.py** — more layout factors won't solve the semantic problem
3. **Investigate positional/contextual resolution** — e.g., question numbers appear in sequence, at line starts, after section headers
4. **Consider page-level structure** — questions are on pages 1-4, answers on pages 5-11; this page-level context is more discriminative than span-level layout

---

## 7. Reproducibility

```bash
cd backend
python -m scripts.evidence_replay --source-version-id fa58a2d0-a116-495d-aa07-3f612b976402 --output result.json
```

Same input + same code = same result (deterministic pipeline).
