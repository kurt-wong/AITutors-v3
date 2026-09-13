# Phase I-5-1: Integration Boundary Analysis

Status: Manifest Capability Check Complete
Date: 2026-09-10
Predecessor: 65_PHASE_I5_SCOPE_FREEZE.md (I-5-0)

---

## 1. V3 Actual Data Flow (from code)

```
Document
  └── DocumentSourceVersion (body_text, body_hash, line_count)
        └── DocumentSourceLine (line_ref="P1L007", seq, page_no, text, line_hash)
              └── DocumentSourceSpan (line_ref, seq, text, font, size, flags, bbox, origin, span_hash)

SemanticAnnotation (payload: semantic_units[])
  └── question_label / option_label / answer_zone / explanation_zone
  └── Forbidden: line_ref, resolved_span, final_line_ids, 正文

SourceResolver.resolve(annotation_payload) → ResolvedRun
  └── ResolvedSpan (span_id="sp-Q1.stem", start_line_ref, end_line_ref, line_refs, text_hash)
  └── UnresolvedReference (reference_id, role, resolution_status)

IRBuilder → IR
  └── IRNode (unit_id, unit_type, question_number, original_question_type)
  └── IRContent (role, span_id)

Compiler → CompiledSnapshot
  └── CompiledLeaf (从 ResolvedSpan.line_refs → SourceLineView.text slice)
```

---

## 2. Manifest Field → V3 Contract Mapping

### 2.1 Line Reference Fields

| Manifest Field | V3 Target | Mapping | Status |
|---|---|---|---|
| `stem_lines: [7,7]` | `ResolvedSpan` with `role="stem"` | seq 7→7 → `line_refs=("P1L007",)` | **Direct** |
| `options_lines: [9,9]` | `ResolvedSpan` with `role="option"` | seq 9→9 → per-option spans needed | **Needs split** |
| `answer_lines: [155,155]` | `ResolvedSpan` with `role="answer"` | seq 155→155 → `line_refs=("P2L031",)` | **Direct** |
| `explanation_lines: [157,165]` | `ResolvedSpan` with `role="explanation"` | seq 157→165 → 9 lines | **Direct** |
| `material_lines: [55,70]` | `ResolvedSpan` with `role="material"` | composite only | **Direct** |
| `questions_lines: [55,106]` | Covered by material_lines | composite is atomic unit | **See §5** |

**Key finding**: V3 `DocumentSourceLine.seq` is an integer assigned during Seal. Manifest line numbers are integers from the OCR markdown file. These are the same numbering system IF the OCR markdown is sealed as-is (line N in markdown = seq N in V3). Verified experimentally.

### 2.2 Semantic Fields

| Manifest Field | V3 Target | Mapping | Status |
|---|---|---|---|
| `unit_id: "Q1"` | `IRNode.unit_id` | Direct string copy | **Direct** |
| `unit_type: "standalone_question"` | `IRNode.unit_type` | V3 uses `standalone_question` / `composite_unit` | **Compatible** |
| `question_numbers: [1]` | `IRNode.question_number` | `str(question_numbers[0])` | **Direct** |
| `original_question_type: "single_choice"` | `IRNode.original_question_type` | 12 canonical types in V3 | **Needs mapping table** |

### 2.3 Forbidden Fields (confirmed)

| Manifest Field | Reason |
|---|---|
| `annotation_meta` | Upstream generation metadata |
| `model` | Provider provenance |
| `source_file` | Upstream path |

---

## 3. Path A vs Path B Analysis

### Path A: Manifest → Annotation payload → Existing Resolver

**Problem**: Resolver's marker-matching re-introduces Phase I-4 failure mode. Manifest already knows the structure.

**Verdict**: Path A defeats the purpose.

### Path B: Manifest → Direct ResolvedSpan construction → IR

**Key question**: Can we construct `ResolvedSpan` objects directly from manifest line numbers, bypassing Resolver?

**Verdict**: Path B is technically feasible. Verified with real data: 21/21 units produce ready IR nodes, 21 CompiledLeaf objects generated successfully.

---

## 4. Manifest Capability Check (2026-09-10)

Three questions verified against real pilot manifests.

### 4.1 Composite Sub-question Boundaries

**Question**: Does manifest carry sub-question boundary information for composite units?

**Evidence** (Geography manifest, 19 units, 16 composite):

```json
{
  "unit_id": "U1-2",
  "unit_type": "composite_question",
  "question_numbers": [1, 2],
  "material_lines": [17, 18],
  "questions_lines": [17, 25],
  "stem_lines": null,
  "answer_lines": [525, 525]
}
```

`questions_lines=[17,25]` is a range covering material (17-18) + both sub-questions (19-25). No sub-question boundary markers exist.

**Resolution**: This is **by design**, not a gap. Composite questions are atomic units — questions sharing the same material are merged into one unit and enter V3 as a single node. No sub-question decomposition is needed or desired. The `questions_lines` field is informational; `material_lines` is sufficient for V3's IR construction.

**Impact on Adapter**: None. Composite units map directly to a single `IRNode` with `material_lines` → `role="material"` span.

### 4.2 Shared Answer Tables

**Question**: Does manifest provide per-question answer values, or only shared line references?

**Evidence** (Physics manifest, 24 units):

```
Q1-Q8  →  answer_lines=[472,472]   (8 units share one line)
Q9-Q18 →  answer_lines=[477,477]   (10 units share one line)
```

Source line 472 contains an HTML table:
```html
<table>
  <tr><td>1</td><td>2</td>...<td>8</td></tr>
  <tr><td>C</td><td>D</td>...<td>C</td></tr>
</table>
```

Annotated.md confirms LLM marked the region (`META:answer:start:1` ... `META:answer:end:8`) but did **not** extract individual answers.

Manifest has **no** `answer_text` field. Units only have `answer_lines`.

**Resolution**: Answer extraction from shared tables (HTML tables, continuous strings like "1-10 BACDBCCCDA") requires LLM semantic understanding. Rule-based parsing is fragile across format variations.

**This is a manifest expressiveness gap.** The preprocessing project needs to:
1. Extract individual answer values during LLM annotation phase
2. Add `answer_text` field to manifest schema per unit

**Impact on Adapter**: Adapter cannot extract answers from shared tables without violating the "no semantic inference" principle. For I-5-2, either:
- (a) Use only standalone questions with inline answers (no shared tables) as test input
- (b) Require preprocessing project to add `answer_text` to manifest schema

### 4.3 Options Splitting

**Question**: Does `options_lines` provide per-option spans or just a range?

**Evidence** (Math manifest): `options_lines: [9,9]` — single line range covering all options.

Additionally, `option_tokens()` from V3's resolver module fails on multi-option-per-line text:
```
option_tokens('A. xxx B. yyy C. zzz D. aaa', ('A','B','C','D'))
→ returns ('A',)  ← only first option detected
```

**Resolution**: Options splitting is structural recognition — the same class of task as answer extraction. Regex/rule-based splitting cannot enumerate all format variations (multi-option-per-line, mixed layout, OCR noise). This must be done by LLM during preprocessing.

**This is a manifest expressiveness gap.** The preprocessing project needs to:
1. Split options during LLM annotation phase
2. Provide per-option line ranges or character offsets in manifest (e.g. `options: [{label: "A", lines: [9,9]}, ...]`)

**Impact on Adapter**: Adapter receives pre-split options and constructs per-option spans mechanically. No parsing logic needed.

---

## 5. Composite Question Model (Revised)

Previous analysis treated `questions_lines` as a gap requiring sub-question derivation. **This was wrong.**

Composite questions are atomic units. V3's IR for a composite:

```
IRNode(
  unit_id="U1-2",
  unit_type="composite_unit",
  question_number="1",
  content=[
    IRContent(role="material", span_id="sp-U1-2.material"),
    IRContent(role="questions", span_id="sp-U1-2.questions"),
    IRContent(role="answer", span_id="sp-U1-2.answer"),
  ]
)
```

No `shared_components` + `sub_questions` decomposition. The manifest's `material_lines` → material span, and the rest of the unit's content fields map directly.

**Updated Adapter responsibility for composite units**: Map `material_lines` to a material ResolvedSpan. Map `questions_lines` to a questions ResolvedSpan (or ignore if material_lines already covers the relevant content). Map `answer_lines` to answer span. No sub-question boundary derivation needed.

---

## 6. Minimal Adapter Boundary

### Must do:
1. **Line number → line_ref mapping**: `seq N` → `"P{page}L{line:03d}"`
2. **Construct ResolvedSpan**: From manifest line ranges + Source lines
3. **Map unit_type**: `standalone_question` / `composite_question` → V3 enums
4. **Map original_question_type**: Manifest enum → V3 canonical enum (12 types)
5. **Compute text_hash**: SHA256 of sliced text for each span
6. **resolution_status = "exact"**: With semantic clarification that this means "exact source reference imported from trusted structural annotation", not "Resolver-derived textual match"
7. **Structural consistency checks**: line bounds, empty stems, missing answers, overlapping ranges

### Must NOT do:
1. Parse shared answer tables (structural recognition → LLM's job)
2. Split options from raw text (structural recognition → LLM's job)
3. Derive sub-question boundaries (composite is atomic → no decomposition needed)
4. Any regex-based content interpretation
5. Modify SourceResolver
6. Create new Domain entities
7. Persist manifest as V3 data

### Prerequisites (preprocessing project):
The manifest must be fully expressive — providing all structural information V3 needs, so the Adapter is a pure mechanical translator:

1. `answer_text`: extracted per-question answer values (for shared answer tables)
2. `options`: per-option spans with line ranges or character offsets (not a single range)

Without these, the Adapter would need to re-derive structure — which contradicts the entire premise of the preprocessing approach.

---

## 7. I-5-2 Contract Freeze

### Input:
```
SealedSource (DocumentSourceVersion + DocumentSourceLine[])
+
Manifest (manifest.json)
```

NOT: annotated.md, LLM raw output, OCR raw result

### Output:
```
ResolvedRun (containing ResolvedSpan[])
```

Passed directly to `IRBuilder.build(resolved_run, annotation_payload, source_version_id, annotation_id)`.

### Pipeline:
```
Seal → Adapter → ResolvedRun → IRBuilder → Compiler → Gate → Admission
```

Bypasses: Resolver

> **更正（2026-09-13，Gate D 发现 1，见 81 号 §3/§5.2）**：原文写
> 「Bypasses: Annotation, Resolver」，**表述错误**。`IRBuilder.build()`
> 必需 `annotation_payload`，其 `semantic_units[]` / `unit_id` / `unit_type` /
> `content{}` 驱动全部语义结构，且 ResolvedSpan 的 span_id 约定
> （`sp-{unit_id}.{role}`）由 annotation 反推——绕过 Annotation 则连 span_id
> 都构造不出来。正确表述：**Bypasses: Resolver only**；Annotation 的语义工作
> 由 preprocessing 承担，产出 V3 形制 annotation_payload。

### Adapter responsibilities:
- line_ref expansion, hash computation, range validation, span construction
- structural consistency checks (line bounds, empty stems, missing answers)

### Adapter prohibitions:
- any content parsing or structural inference (options splitting, answer extraction, sub-question derivation)
- regex-based text interpretation

---

## 8. I-5 Success Criteria

Must prove:
1. **Source Integrity**: Manifest line_refs stably point to sealed source
2. **IR Compatibility**: ResolvedSpans generate valid Question IR / Composite IR
3. **Gate Compatibility**: Admission pre-checks still effective (stem non-empty, answer exists, roles consistent)

Do NOT need to prove:
- LLM slicing accuracy (preprocessing project's concern)
- OCR accuracy (preprocessing project's concern)
- Automation rate at scale (preprocessing project's concern)

---

## 9. Experimental Results (I-5-1)

14 tests conducted with real manifest + source data:

| # | Test | Result |
|---|------|--------|
| 1 | seq ↔ line_ref correspondence | PASS |
| 2 | Resolver on simple case | FAIL (all UNRESOLVED) |
| 3 | Direct ResolvedSpan construction | PASS |
| 4 | text_hash consistency vs Resolver | UNVERIFIABLE (Resolver failed) |
| 5 | option_tokens() multi-option split | FAIL (returns only first option) |
| 6 | Error rejection (out-of-range, overlap) | PASS |
| 7 | Real manifest line mapping (594 lines) | PASS |
| 8 | Real manifest ResolvedSpan construction | PASS |
| 9 | IRBuilder with direct ResolvedSpans | PASS (21/21 ready) |
| 10 | Options split (real data, 4 labels) | PASS |
| 11 | Option span construction | FAIL (full-range text, not split) |
| 12 | Full IRBuilder with options | PASS (21/21 ready) |
| 13 | Error rejection (4 types) | PASS |
| 14 | Compiler → CompiledLeaf | PASS (21 leaves) |

**Key findings**:
- Path B works: direct ResolvedSpan → IRBuilder → Compiler pipeline succeeds
- `option_tokens()` is insufficient; Adapter needs own parser
- Option spans must be split by character offset, not full-range coverage
- Resolver fails on simple cases (confirms Phase I-4 result)

---

## 10. Conclusion

**Manifest expressiveness is insufficient for full V3 integration.** Two gaps exist:
1. Shared answer tables lack extracted per-question answer values (`answer_text` missing)
2. Options are not pre-split (`options_lines` is a single range, not per-option spans)

Both are structural recognition tasks that belong to the preprocessing layer (LLM), not the V3 Adapter. The Adapter must be a pure mechanical translator — any rule-based content parsing in the Adapter contradicts the fundamental premise of the preprocessing approach.

**Path B is proven feasible** with real data for cases where manifest is sufficiently expressive (standalone questions with inline answers, composite atomic units).

**Prerequisites for full coverage** — preprocessing project must enhance manifest schema:
1. `answer_text` field: extracted answer value per unit
2. `options` field: per-option spans (line ranges or character offsets), not a single range

**Design principle**: Structure is recognized by LLM during preprocessing, consumed mechanically by V3. No structural inference in the Adapter — not even "deterministic" rule-based splitting. Regex cannot enumerate all format variations.

**Next step**: Discuss implementation approach before proceeding to I-5-2.
