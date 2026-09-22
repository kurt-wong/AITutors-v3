# P04 + P08 Owner Decision Evidence Investigation

> **Status**: `INVESTIGATION` / **NON-AUTHORITATIVE** / **OWNER DECISION INPUT**  
> **Verdict status**: both P04 and P08 = `OWNER DECISION REQUIRED` (this file does **not** close either decision)  
> **Scope**: factual evidence only — **no** production code / tests / schema / migration / Frozen Spec / Frozen Contract / v0.3 Contract / Owner Decision Package edits  
> **Security**: no secrets in this report; runtime credentials remain in `.env` only  

## 0. Evidence base (repo / commit / primary artifacts)

| Role | Local path | Remote | HEAD @ investigation |
|---|---|---|---|
| Producer / Preprocessing | `D:\Project\Papers` | `kurt-wong/Aitutors-preprocessing` | `2b92898f05f6541a5fc65c8300cb8a59a06c4928` |
| Consumer / V3 | `D:\Project\AITutors-v3` | `kurt-wong/AITutors-v3` | `830211c1cfa821d3ece36a1db31df693d138e8bc` |
| Integration / Owner record | `D:\Project\AITutor-X` | `kurt-wong/AITutorX` | `5618b0075d34f5e0763682d75a9f223202a3e9cb` |

**Primary data artifacts**

| Artifact | Path | Role |
|---|---|---|
| Resolver IR (88 files) | `Papers/data/resolver_ref_r52/resolver_ir.json` | Producer semantic IR face; sha256 `fbcf41ab025fd786614b52d63270160868a2f49ab63121f012905c79f65b04a5` |
| Interface census | `Papers/data/producer_interface_census.json` | unit-level key census (4,609 units / 166 manifests) |
| Ocr-markdown tree | `Papers/Ocr-markdown/**/*.manifest.json` | actual manifests (166 files) |
| Consumer B2 report | `AITutors-v3/backend/scripts/preprocessing_consumer/consumer-report-b2-r2.json` | live consumer summary |

**Evidence labels used below**: `OBSERVED` = code/data measured this run · `DERIVED` = arithmetic from OBSERVED · `OPEN` / `OWNER DECISION REQUIRED` = not decided here.

**Discipline**: code evidence > actual Producer artifact > actual V3 run data > Contract > interpretation.

---

# P04 — OPTION-LABEL EVIDENCE

## 1. OBSERVED FACTS

1. **OBSERVED** — Producer `manifest` unit schema exposes options **only** as whole-block line range `options_lines: [start, end] | null` (`reslice_pipeline.py` prompt schema lines 255, 271; census `manifest.unit_level_keys.options_lines = 3936`). No unit key encodes per-option label, per-option text, per-option line, or per-option evidence.
2. **OBSERVED** — On **71 ADMITTED** (1,664 units): choice-family `original_question_type` ∈ {`single_choice`,`multiple_choice`,`true_false`} = **1,108** units (single 1042 + multiple 66 + true_false 0); `options_lines` non-null = **945**; null = **163**; non-choice = **556**. Units with any non-`options_lines` option-* key = **0**.
3. **OBSERVED** — Resolver IR (Producer) carries whole options span only under `provenance.source_lines.options_lines` (945/1664); IR `content.options_lines` = sliced text lines of that whole block. No per-label structure is synthesized in IR.
4. **OBSERVED** — V3 `manifest_reader.py` reads `options_lines` only (`ManifestUnit.options_lines`); no option label/text fields.
5. **OBSERVED** — V3 `annotation_adapter._leaf_content` **does not declare** `content.options` for choice units; comment documents intentional non-fabrication (lines 66–70). When `original_question_type ∈ {single_choice, multiple_choice, true_false}` and `options_lines` present, adapter appends known_gap `OPTION_LABEL_SPAN_UNAVAILABLE` (`annotation_adapter.py:92-101`, constant line 40). Test `test_choice_type_gap_is_explicit_not_fabricated` asserts gap code and `"options" not in content`.
6. **OBSERVED** — V3 `runner_b2._try_options_region` builds **one** ResolvedSpan with `role="options"` (whole region) and explicitly does **not** manufacture per-label A/B/C/D (`runner_b2.py:265-270`). `resolved_span_adapter` similarly emits one `role="option"` span from `options_lines` (lines 96–98).
7. **OBSERVED** — V3 `IRBuilder._content_items` requires per-label `content.options[].label` to emit `IRContent(role="option", label=…)` with `span_id = sp-<unit>.option.<label>` (`compile/ir.py:182-189`). `validate_ir` marks choice without declared options as `incomplete` with reason `options missing for choice type` (`ir.py:256-259`).
8. **OBSERVED** — `runner_b2` skips non-`ready` units **before** Gate (`runner_b2.py:408-420`). Consumer report `consumer-report-b2-r2.json`: `ready_total=289`, `skipped_total=582`, `gate_auto_approve=0`, `gate_rejected=0`, `gate_pending_review=289`. Gap codes are not embedded as numeric `code` keys in that report JSON (known_gaps live in SemanticAnnotation payload when built via adapter).
9. **OBSERVED** — `OPTION_LABEL_SPAN_UNAVAILABLE` is **defined and emitted only** in `annotation_adapter` (+ exported + test). Grep of `backend/app/**` for `OPTION_LABEL` = **0 hits**. Gate / Compiler / Admission **do not read** this gap code.
10. **OBSERVED** — `runner_b3.py` and `gate_b/gate_b2b1_option_region.py` are **experiment harnesses** that **recover** labels by parsing text inside `options_lines` at runtime (`_detect_labels_in_region` / Layer 2 structure extraction). They do **not** persist per-label evidence into Producer artifacts or production IR spans. Producer-side option evidence authority is not upgraded by these scripts.
11. **OBSERVED** — Frozen Spec `Docs/V3_SPEC/**` contains **no** `flags` / `answer_evidence` / `OPTION_LABEL` tokens as Gate rules (`grep` = no matches). Frozen Contract v0.2 freeze scope = six items (Identity / Scope / Semantic Boundary / Path Non-Identity / Identity-only Recovery / Source Bytes Capability) — **does not include** option-label evidence design (`PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` §0.1).
12. **OBSERVED** — v0.3 draft IPM row `options_lines`: whole-block keep; per-label missing = GAP; `unsup`(label); ban fabricate A/B/C (`INFORMATION-PRESERVATION-MATRIX` line 60). Open decision OD-V3-06 / Owner package OD-P04 = `OWNER DECISION REQUIRED`.

## 2. ACTUAL PRODUCER OUTPUT

### 2.1 options data structure (choice)

| Question | OBSERVED answer |
|---|---|
| How are options represented? | Single interval `options_lines: [int,int] \| null` on unit |
| Option labels A/B/C/D saved? | **No** structured field |
| Per-option text saved as structured text? | **No** (only whole-block **line slice text** in IR `content.options_lines` / `content` after span slice) |
| Per-option source line? | **No** |
| Per-option evidence? | **No** |
| Whole options block line range? | **Yes** — `options_lines` on manifest + `provenance.source_lines.options_lines` on IR |

Schema source: `Papers/scripts/reslice_pipeline.py` output JSON (prompt v2.x); confirmed on disk across 71 ADMITTED manifests (unit key presence: `options_lines` on 1,386 units overall; 945 with non-null among choice).

### 2.2 Actual counts — 71 ADMITTED (resolver IR join → 71 manifests, 1,664 units)

| Metric | Count |
|---|---:|
| choice-family units | 1,108 |
| choice with `options_lines` present | 945 |
| choice with `options_lines` null | 163 |
| with option **label** field | **0** |
| with option **text** field (structured) | **0** |
| with whole `options_lines` | **945** (choice) / 945 in IR source_lines |
| with **per-option line anchor** | **0** |
| with **per-option evidence** | **0** |
| completely unable to locate options block | **163** choice units with null `options_lines` |
| able to locate options **block** but not labels | **945** |

### 2.3 Prompt versions on ADMITTED

`reslice-pilot-v2.1` = 38 files · `reslice-pilot-v2.3` = 33 files. Neither prompt version on this face emits `answer_evidence` (see P08); neither emits per-label option structure.

**Current Producer actual capability (not aspirational)**: whole-region option line anchoring + deterministic IR slice of those lines. **Not** per-label evidence.

## 3. ACTUAL V3 CONSUMPTION

| Stage | What happens to options |
|---|---|
| Producer → Boundary (`manifest_reader`) | `options_lines` **PRESENT** (tuple) |
| Boundary identity / unit_type normalize | options untouched |
| Annotation Adapter | **does not declare** `content.options`; may emit `OPTION_LABEL_SPAN_UNAVAILABLE` in `producer_boundary.known_gaps` |
| Resolved Span (runner_b2) | **one** span `sp-<id>.options` (role `options`) from whole range |
| Resolved Span (resolved_span_adapter) | one span `sp-<id>.option` (role `option`, no label) |
| V3 IRBuilder | no `option` IRContent without label declaration → choice → `semantic_status=incomplete` (`options missing for choice type`) |
| Compiler | only compiles `ready` nodes → choice incomplete → **no leaves** |
| Gate (`policy.evaluate`) | **not reached** for incomplete (runner skips); Gate code never reads `OPTION_LABEL_SPAN_UNAVAILABLE` |
| Admission | not reached for those skipped units |
| Persistence | SemanticAnnotation payload may store `known_gaps`; IR/DB leaves for incomplete choice not produced |

## 4. CURRENT GAP

| Gap | Label |
|---|---|
| Producer does not store per-option-label spans/evidence | `OBSERVED` Producer capability limit |
| V3 IR format requires per-label option content for `ready` choice | `OBSERVED` (Frozen pipeline 20 §6/§7 + `ir.py`) |
| Adapter honest non-declaration → incomplete for choice with options | `OBSERVED` intentional (no fabricate) |
| Gap code registered only in adapter, not consumed by Gate/Admission | `OBSERVED` |
| Whether to upgrade Producer vs permanently accept whole-span + incomplete / limited auto | **`OWNER DECISION REQUIRED` (OD-P04)** — not decided here |

## 5. ACTUAL IMPACT

### What missing per-option evidence **does** affect

| Area | Impact | Evidence |
|---|---|---|
| Choice unit → V3 **ready IR** | **Yes, current path**: without declared per-label options, `validate_ir` → `incomplete` → runner skips Gate | `ir.py:256-259`, `runner_b2.py:408-420`, report skipped=582 |
| Choice **options content completeness** in IR | **Yes** — cannot bind `sp-*.option.<label>` | `ir.py:182-189` |
| Choice **grammar / strict-auto / label set** for Gate admission layer | **Yes, design-level** — auto path expects option labels (`policy` uses `leaf.options`; OD-P04 FACT-02); today those leaves often never exist for incomplete choice | `gate/policy.py` options loops; OD-P04 package |
| Answer correctness verification that **depends on option letters** | **Indirectly** — answer text may still be span-anchored via `answer_lines`; verification that must check “selected letter ∈ option set” needs labels | answer path separate (`runner_b2._answer_span`) |

### What missing per-option evidence **does not** affect

| Area | Why not |
|---|---|
| **Question Identity** | Identity = `source_content_sha256` + manifest identity fields (`question_numbers`, `section_ref`, …), not option labels |
| Non-choice units (short_answer / fill_in / …) | No `options_lines` requirement (`content_roles` options only `required_for_choice`) |
| Whole options **block** line anchoring for provenance | Already preserved (`options_lines` + IR `source_lines`) |
| Producer QC disposition / Interface Scope 87 / ADMITTED 71 | Independent of option-label grain |
| Frozen Spec QT / Unit Type / Answer grammar frozen sets | Frozen does not define per-label Producer evidence (OD-P04 Frozen Constraint = NONE) |

### Does it block Question from “entering V3”?

| Interpretation | OBSERVED |
|---|---|
| Enters Manifest Interface Scope / Identity M1–M5 | **Yes can enter** — identity gate does not require option labels |
| Enters Annotation payload + ResolvedRun | **Yes** — spans built from whole `options_lines` |
| Reaches `semantic_status=ready` for choice | **No under current adapter** (options not declared) |
| Reaches Gate evaluate / Admission candidate as ready choice | **No for incomplete** (skipped) |
| Non-choice ready path | Independent of P04 |

So: **not** a hard block on all V3 entry; **is** a hard block on **choice ready-IR → Gate/Admission** under the current honest adapter policy.

### Answer verification / Gate / Admission summary

| Question | OBSERVED |
|---|---|
| Affects Answer verification needing option inventory? | **Yes** if verification requires label set; **No** for pure answer_lines span location |
| Affects Gate directly via gap code? | **No** — Gate never reads `OPTION_LABEL_SPAN_UNAVAILABLE` |
| Affects Gate **indirectly** via incomplete skip? | **Yes** — choice never evaluated as ready |
| Affects Admission? | **Only** via whether a ready candidate exists; no Frozen admission rule cites option-label grain |

## 6. FROZEN / CONTRACT AUTHORITY

| Claim | Status |
|---|---|
| Per-option-label evidence required by Frozen Spec | **`NOT_DEFINED`** |
| Per-option-label evidence required by Frozen Contract v0.2 (six freeze items) | **`NOT_DEFINED`** (outside freeze scope §0.1) |
| v0.3 draft IPM: per-label missing must be registered GAP; ban fabricate A/B/C | **`DRAFT_ONLY`** (`INFORMATION-PRESERVATION-MATRIX` options_lines row) |
| Open decision OD-V3-06 / OD-P04 = Owner | **`DRAFT_ONLY`** / package `OWNER DECISION REQUIRED` |
| V3 IR requires per-label options for choice `ready` | **`FROZEN_DEFINED`** (pipeline 20 content_roles + IR invariants; code `ir.py`) |
| Conflict: Frozen IR shape vs Producer whole-span only | **`CONFLICT`-like gap is architectural** — resolved only by OD-P04 options (upgrade Producer vs accept incomplete/limited path); **not** a license to fabricate labels |

**No Frozen Authority currently mandates “Producer must ship per-option evidence.”** Equally, **no Frozen Authority forbids** registering whole-span as permanent `unsup` if Owner chooses that option (OD-P04 Option B in package).

## 7. OWNER DECISION INPUT

**If whole-span evidence is retained**

- Concrete losses: choice units stay `incomplete` under honest adapter → no ready leaves → no Gate/Admission auto path for those choice units; no stable `sp-*.option.<label>` for grammar/label inventory; `OPTION_LABEL_SPAN_UNAVAILABLE` remains adapter-only (not a Gate signal unless OD-P08 expands consumption).
- Non-losses: identity, whole options block provenance, non-choice pipeline, answer_lines location.

**If Producer upgrades to per-option evidence**

- Required work (scope only, not a plan approval): extend unit schema (label + lines ± text hash); extend reslice prompt + QC validators; re-annotate or deterministic re-slice under Identity/IR regeneration constraints (Frozen Contract v0.2 §1.6 four guarantees if IR regenerated); V3 adapter must map labels → `content.options` + per-label spans (replace gap code path); experiments `runner_b3` / `gate_b2b1_option_region` become unnecessary as evidence source or become verification-only.
- Must solve: label vocabulary stability, multi-line options with figures (existing prompt already extends `options_lines` to last figure line), shared option pools (Frozen 20 notes shared pools out of current Producer shape).

**Is there a现实必须升级的强制需求？**

- **OBSERVED**: no Frozen clause currently **requires** upgrade.
- **OBSERVED**: choice `ready` + label-based auto **cannot complete** without either Producer upgrade **or** a different Consumer strategy (e.g. deterministic parse of whole region into labels — currently only **experimental** harnesses, not production IR evidence).
- Whether that constitutes a **must** is **`OWNER DECISION REQUIRED`** (OD-P04).

**Do not read this section as recommending A/B/C.**

## 8. VERDICT STATUS = OWNER DECISION REQUIRED

---

# P08 — FLAGS / BASIS / ANSWER_EVIDENCE

## 1. OBSERVED FACTS

1. **OBSERVED** — Three fields live on **different Producer layers**:
   - `flags` / `answers` table object: **Resolver IR** (computed in `resolver_reference.py`), **not** on manifest units of the 71 ADMITTED face.
   - `basis` / `basis_evidence` / `printed_provenance`: **both** manifest and IR (identity backfill writes manifest; IR copies verbatim).
   - `answer_evidence`: **manifest unit key** under prompt ≥ v2.4; **absent** on all IR-linked 88 manifests / all 71 ADMITTED / all 1,664 ADMITTED units.
2. **OBSERVED** — V3 production consumer path (`preprocessing_consumer/*`) **never greps** `flags` / `answer_table_unresolved` / `qc_verdict` (0 hits). OCR `SourceSpan.flags` (int bitmask) is a **different** field on `models/source.py` — not Producer string flags.
3. **OBSERVED** — `manifest_reader` **reads** `basis`, `basis_evidence`, `printed_provenance`, `answer_evidence.{type,lines,value}` (not `shared`); **does not read** Producer `flags` (not on manifest anyway for this face).
4. **OBSERVED** — `annotation_adapter` builds `semantic_units` **without** basis / flags / answer_evidence / printed_provenance → those fields are **not** in SemanticAnnotation `semantic_units` (payload only has identity-ish claims + units + `producer_boundary.normalization/known_gaps`).
5. **OBSERVED** — `runner_b2` uses `answer_lines or answer_evidence_lines` only as answer **span location**; **drops** `answer_evidence.type` / `.value` / `.shared`.
6. **OBSERVED** — `gate/policy.evaluate`, `compile/ir.py`, `gate/payload.py`, admission models: **no** reads of Producer `flags` / `basis` / `answer_evidence` (grep 0 in `app/domains/gate` and `app/domains/compile` for these tokens; models only OCR int flags).
7. **OBSERVED** — Frozen 20 §8 four layers = Structural / Provenance / Semantic / Admission — check list frozen (BUG-V3-024); **does not include** Producer `flags` / `basis` / `answer_evidence` as gate inputs. Annotation `confidence` explicitly **not** a decision trigger (20 §8.1).
8. **OBSERVED** — Frozen Contract v0.2 freeze six items do **not** define flags/basis/answer_evidence Gate rights. Cross-repo Integration Contract (Producer) **defines** `flags` string[] values and **bans** silent `answers.get(q,"")` defaults (G-BOUND / R-ACC-14).
9. **OBSERVED** — v0.3 IPM: `flags` must be kept (`丢 flag = violation`); “not yet in Gate strategy” marked CONSUMER GAP; `basis` keep + no unverified→printed_as_is; `answer_evidence` keep or register unsup. SAM: flags/QC/disposition = Producer authority band; `flags 非空 vs 无` → must be visible downstream.
10. **OBSERVED** — Owner package OD-P08 already records: reader partial / adapter drop / flags unread; Frozen Gate four layers do **not** contain flags — putting flags **into** Gate = strategy extension decision.

## 2. FIELD DEFINITIONS

### 2.1 `flags`

| Aspect | OBSERVED |
|---|---|
| Type | `string[]` on **IR unit** |
| Actual values (71 ADMITTED) | `answer_table_unresolved` = **502**; `answer_number_mismatch` = **91**; empty list units = **1071**; units with ≥1 flag = **593**; multi-flag units = **0** (502+91=593) |
| Meaning | Structural observations while building IR: (1) answer-region first-line number not in unit `question_numbers`; (2) answer table cells could not be attributed to this unit’s question numbers → unresolved slots |
| Produced by | **Deterministic Producer Resolver** (`resolver_reference._answer_flags`, `parse_answer_table` → `flags.append`) — **not** LLM, **not** human |
| On manifest? | **No** (0/71 manifests contain unit `flags`) |
| Nature | Structural **warning / provenance-adjacent quality flag** (string tokens), **no severity enum**, **no multi-flag stacking** in current data |
| Simultaneous flags | Possible in code (list append twice); **never observed** on ADMITTED |

### 2.2 `basis`

| Aspect | OBSERVED |
|---|---|
| Type | `string` |
| Declared vocabulary (6) | `answer_key` \| `shift` \| `keep` \| `printed_as_is` \| `explicit` \| `unverified` (`question_identity.py` header; Integration Contract §2) |
| Actual values (71 ADMITTED IR) | `printed_as_is` **1041** · `unverified` **596** · `shift` **18** · `answer_key` **9** · `keep` **0** · `explicit` **0** |
| Describes | **Question identity legitimacy** — why canonical question number is accepted (“为什么合法”), not Answer text quality, not whole-unit score (`question_identity` docstring) |
| Source vs judgment | **Provenance of identity decision** + evidence string; `unverified` = **uncertainty fact**, not a numeric quality score |
| Produced by | Deterministic backfill `phase2_identity_backfill.py` (migration PLAN ops → mode; else printed_from_stem → printed_as_is / unverified) + identity assign; IR copies `u.get("basis")` |
| Fact vs quality field | Primarily **identity provenance fact**; carries uncertainty when `unverified` |
| Companion `basis_evidence` | string with `L{line}` refs when available; empty **596** on ADMITTED (matches unverified 596); IPM: empty allowed, must not fabricate |
| Companion `printed_provenance` | `source_line` 1041 · `unknown` 596 · `migration_report` 27 |

### 2.3 `answer_evidence`

| Aspect | OBSERVED |
|---|---|
| Exact schema (prompt) | `{"type": enum, "lines": [s,e]\|null, "value": str\|null, "shared": bool}` |
| Type enum | `answer_lines` \| `inline_in_explanation` \| `answer_table` \| `range_string` \| `absent` (`AE_TYPES` in `reslice_pipeline.py`) |
| Contents | **Both**: source **line anchor** (`lines`) and optional **verbatim answer value** (`value`); `shared` = evidence region contains other units’ answers |
| Cardinality | **One object per unit** (not array) |
| vs `answers` (IR) | IR `answers` is **answer-table parse result** `{cells, method, answers, unresolved}` when answer span is single-line table — different structure from manifest `answer_evidence` |
| vs `basis` | Unrelated: basis = identity legitimacy; answer_evidence = where/how answer is evidenced in source |
| vs `answer_lines` | Parallel line anchors; `runner_b2` prefers `answer_lines` then falls back to `answer_evidence.lines` |
| Supports Answer → Source trace? | **Yes when present and `lines` non-null** (line range into source md). On **71 ADMITTED this key is absent** — so answer trace uses `answer_lines` only |
| On full Ocr-markdown (166 manifests) | **28 files / 906 units** have the key; types: `answer_lines` 472 · `answer_table` 223 · `inline_in_explanation` 178 · `range_string` 33 · `absent` 0 in samples |
| Intersection with IR 88 face | **0 files** — AE lives on other prompt versions (v2.4–v2.7), **not** on ADMITTED v2.1/v2.3 face |

## 3. ACTUAL VALUES / COUNTS (71 ADMITTED)

### flags

```text
flag value → count (units)
(answer_table_unresolved) → 502
(answer_number_mismatch)  → 91
no flag                   → 1071
has ≥1 flag               → 593
multi-flag                → 0
```

### basis

```text
printed_as_is → 1041
unverified    → 596
shift         → 18
answer_key    → 9
keep          → 0
explicit      → 0
total         → 1664
```

### answer_evidence (71 ADMITTED manifests)

```text
with answer_evidence key → 0
without                  → 1664
vs answer_lines consistent → N/A (key absent)
traceable via answer_evidence → 0
unverifiable answer_evidence on ADMITTED → 0 (absent ≠ invalid)
```

### Related IR answers / unresolved (flags side-effect)

```text
answers object present (table path)     → 528 units
answers.unresolved non-empty units      → 502   (= flag answer_table_unresolved)
answers.unresolved slots                → 596
answer_text present                     → 1664
```

## 4. PRODUCER GENERATION

| Field | Generator | Logic |
|---|---|---|
| `flags` | `resolver_reference.py` `build_unit_records` | `_answer_flags`: first answer line numeric prefix ∉ `question_numbers` → `answer_number_mismatch`; table `parse_answer_table` with non-empty `unresolved` → `answer_table_unresolved` |
| `basis` / `basis_evidence` / `printed_*` | `phase2_identity_backfill.py` + `question_identity.assign_identity` | PLAN mode or stem-line parse; fail-closed QC C13 on evidence |
| `answer_evidence` | **LLM annotation** via reslice prompt rule 4b (≥ v2.4) + schema validators in `reslice_pipeline` | Structured object; validators require type/lines/value/shared rules |
| IR assembly | `resolver_reference` copies basis* verbatim; computes flags; does **not** copy answer_evidence (field not on those manifests) | |

## 5. CONSUMER BOUNDARY

```text
Producer Artifact
  manifest:  basis, basis_evidence, printed_provenance, sections, spans,
             answer_evidence? (NOT on 71 ADMITTED)
  resolver IR: flags, answers, basis*, provenance, content slices
      ↓
Consumer Boundary (manifest_reader + identity boundary)
  reads: spans, basis, basis_evidence, printed_provenance,
         answer_evidence.type/lines/value (if key present)
  does NOT read: flags, qc_verdict, disposition, answers.unresolved
      ↓
Annotation Adapter (annotation_adapter)
  emits: semantic_units roles (stem/answer/explanation/…), normalizations, known_gaps
  does NOT emit: flags, basis, basis_evidence, answer_evidence*, printed_provenance
      ↓
Resolved Span / IR
  spans: stem/answer/explanation/options-region/material…
  IRBuilder: content roles only; no flags/basis/answer_evidence fields
      ↓
Compiler → Gate → Admission → Persistence
  no Producer flags/basis/answer_evidence consumption
```

## 6. V3 CONSUMPTION (stage-by-stage)

| Field | Producer | Boundary (reader) | Annotation Adapter | Resolved Span | V3 IR | Compiler | Gate | Admission | Persistence (payload/DB) |
|---|---|---|---|---|---|---|---|---|---|
| `flags` (IR string[]) | **PRESENT** (IR only) | **ABSENT** (never read; not on manifest) | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** (≠ OCR int `flags`) |
| `basis` | **PRESENT** (manifest+IR) | **PRESENT** (`ManifestUnit.basis`) | **IGNORED** (not in semantic_units) | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** in annotation payload / no evidence row |
| `basis_evidence` | **PRESENT** | **PRESENT** | **IGNORED** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** |
| `answer_evidence` (manifest) | **ABSENT** on 71 ADMITTED; PRESENT elsewhere | **PRESENT** when key exists (type/lines/value; **shared not read**) | **IGNORED** (not in payload) | **TRANSFORMED**: `answer_evidence_lines` only as answer span **fallback** (`runner_b2:273-274`) | only as possible answer `span_id` resolution — **type/value/shared dropped** | uses compiled answer only | **ABSENT** as field | **ABSENT** as field | **ABSENT** as structured evidence object |
| `answers.unresolved` / table | **PRESENT** on IR with flags | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** |

**Cell legend**: PRESENT / ABSENT / TRANSFORMED / IGNORED (read then discarded downstream) / UNKNOWN (not observed unknown — none left UNKNOWN after this investigation).

### Code anchors

| Stage | File | Evidence |
|---|---|---|
| flags gen | `Papers/scripts/resolver_reference.py:109-164` | append + IR record |
| basis gen | `Papers/scripts/phase2_identity_backfill.py:69-96` | PLAN / stem |
| AE schema | `Papers/scripts/reslice_pipeline.py:158-258` | AE_TYPES + prompt |
| reader | `AITutors-v3/.../manifest_reader.py:44-51,79-100` | basis*, ae type/lines/value |
| adapter drop | `.../annotation_adapter.py` payload keys | no flags/basis/ae |
| answer fallback | `.../runner_b2.py:272-274` | `answer_lines or answer_evidence_lines` |
| gap option | `.../annotation_adapter.py:92-101` | OPTION_LABEL_SPAN_UNAVAILABLE |
| IR no flags | `backend/app/domains/compile/ir.py` | no tokens |
| Gate no flags | `backend/app/domains/gate/policy.py` | no tokens; four layers only |
| live run | `consumer-report-b2-r2.json` | ready 289 / skipped 582 / pending_review 289 / auto 0 |

## 7. INFORMATION LOSS

| Field | Lost or unused? | Where | Classification |
|---|---|---|---|
| `flags` | **Never enters Consumer** | Producer IR only | **Silent non-ingestion** at Boundary (worse than drop-after-read): information exists in Producer semantic layer but V3 manifest-centric path never loads it. IPM “丢 flag = violation” vs actual **never carried** = `OBSERVED` CONSUMER GAP |
| `qc_verdict` / `disposition` | Same | IR file-level | Not read by consumer package |
| `basis` / `basis_evidence` | **Read then dropped** at adapter | reader → payload | **Silent drop** of identity provenance from annotation payload (provenance header in reader claims retention for identity fields — unit-level basis is retained on `ManifestUnit` but not projected downstream) |
| `answer_evidence.type/value/shared` | Read (partially) then unused except lines fallback | reader / runner_b2 | **Partial TRANSFORM + IGNORE** |
| `answer_evidence` on ADMITTED | **Not produced** | Producer face | **Absent data**, not V3 loss |
| `answers.unresolved` | Never read | IR only | Silent non-ingestion |

**Three-way separation (required):**

1. **Information Preservation** — Producer produced `flags` (502+91) and `basis` (1664); V3 boundary **does not preserve them into annotation payload / IR / Gate reasons**. IPM/SAM say they must remain visible → **gap OBSERVED**. `answer_evidence` not on ADMITTED → preservation gap **not applicable** on this face; applicable on other 28 AE files if those enter scope later.
2. **Evidence Authority** (SAM-style):
   - `flags` → **Producer structural observation / uncertainty** (`flags 即 UNC`); NOT Canonical V3 derived; NOT Source text itself (derived from structure+text).
   - `basis` → **Producer identity provenance** (claim about identity legitimacy); `unverified` = uncertainty; NOT Gate authority.
   - `answer_evidence` → **Producer annotation claim** (LLM claim of answer location/value) — closer to **Semantic Interpretation / Evidence claim**, not Source Fact; needs V3 Validation for authority elevation.
3. **Gate Authority** — **No Frozen grant** for flags/basis/answer_evidence to change Gate/Admission. Frozen 20 §8 checklist does not list them. Deriving `flag=answer_number_mismatch → Gate=reject` without Owner/rule authority would be **out of scope self-extension**.

## 8. AUTHORITY CLASSIFICATION

| Field | Authority band (OBSERVED classification vs SAM) | Elevates to Gate? |
|---|---|---|
| `flags` | Producer structural observation / UNC | **No Frozen authorization** |
| `basis` | Producer identity provenance / UNC when unverified | **No** |
| `answer_evidence` | Producer annotation evidence claim (unvalidated in V3 on ADMITTED: field absent) | **No** |
| `qc_verdict=PASS` + ADMITTED | Producer QC + disposition | Already only defines **eligibility for semantic consumption face**, **≠ V3 APPROVED** (SAM) |
| Gate decision | V3 Gate Policy only | — |

## 9. GATE / ADMISSION IMPACT

| Question | OBSERVED |
|---|---|
| Do flags currently affect Gate? | **No** (never read) |
| Do flags affect Admission? | **No** |
| Do basis / answer_evidence affect Gate/Admission? | **No** |
| Can they become review signals? | **Possible under OD-P08** — not implemented; IPM allows review queue mapping; **not decided here** |
| Is there Frozen support to make them hard Gate conditions today? | **No** — `NOT_DEFINED` / would be Gate **strategy extension** (package OD-P08 Frozen Constraint) |
| Does `flag=answer_number_mismatch` imply reject? | **No such Frozen rule** — must not auto-reject without authority |

## 10. FROZEN / CONTRACT AUTHORITY

| Topic | Status |
|---|---|
| flags / basis / answer_evidence as Frozen Gate conditions | **`NOT_DEFINED`** |
| Frozen four-layer Gate checklist (20 §8.1 BUG-V3-024) | **`FROZEN_DEFINED`** — layers do not include these fields |
| Frozen Contract v0.2 six items on these fields | **`NOT_DEFINED`** (out of freeze scope) |
| Cross-repo Integration Contract: flags string[] + no silent default on unresolved | **`CONTRACT_DEFINED`** (Producer→V3 contract doc; consumption duty text) |
| v0.3 IPM/SAM: must keep flags; GateUNK notes; ban drop as clean | **`DRAFT_ONLY`** |
| OD-P08 / OD-V3-18 Owner decision on payload vs Gate vs review queue | **`DRAFT_ONLY`** → **`OWNER DECISION REQUIRED`** |
| Conflict IPM “must keep” vs implementation never carrying flags | **`CONFLICT`** between draft contract intent and current code — not a Frozen conflict; resolution = OD-P08 + implementation authorization later |
| answer_evidence 1:1 V3 EvidenceReference | **`DRAFT_ONLY`** unsup until designed |

**Explicit**: current Frozen Authority **does not** support treating flags/basis/answer_evidence as direct Gate condition inputs.

## 11. OWNER DECISION INPUT

**Preservation gap (facts)**

- V3 today loses **flags** (never ingested), **basis*** (ingested at reader, dropped at adapter), **answer_evidence structure** (lines-only fallback; and **absent on ADMITTED**).
- Losing flags conflicts with draft IPM “必须保留 / 丢 flag = violation”.

**If “payload/provenance only” (visibility)**

- Satisfies preservation without touching Frozen four-layer Gate; requires adapter/payload field design + later CODE AUTHORIZATION (out of scope of this investigation).

**If “auto blocker / pending_review reason”**

- Still needs explicit mapping table (which flag → which decision); Frozen 20 §8 check-item list is frozen — adding items may require Frozen errata confirmation (as package OD-P08 notes).
- **Must not** invent fifth Gate layer casually (package).

**If “independent review queue”**

- Gate logic unchanged; evidence listed when pending_review — alignment with “Gate only pass/fail+reasons” and SAM review mapping.

**answer_evidence separate fact**

- On current 71 ADMITTED face, upgrading consumption of `answer_evidence` **cannot be validated in-place** — field does not exist there. Any AE strategy touches **other** corpus slices or future prompt versions (migration/regeneration questions → separate Owner items).

**No option recommendation is made here.**

## 12. VERDICT STATUS = OWNER DECISION REQUIRED

---

# P07 SUPPORTING FACTS — answer-table-unresolved

> **Only factual investigation. Does NOT close P07 / OD-V3-08 / related Owner items.**

## F1 — Is `answer-table-unresolved` inside `flags`?

**Yes.** OBSERVED token = `answer_table_unresolved` ∈ IR unit `flags: string[]`.  
Not a manifest field. Not a separate top-level IR enum beyond the flags list.

## F2 — Where produced

`Papers/scripts/resolver_reference.py`:

- `parse_answer_table(line, question_numbers)` when answer span is single-line `<table>`.
- Keyed form: td cells with numeric prefixes; if a unit question number missing → `unresolved`.
- Positional form: `len(cells) != len(question_numbers)` → all questions unresolved.
- If `tbl["unresolved"]` non-empty → `flags.append("answer_table_unresolved")` and IR `answers = tbl`.

**Deterministic structural parse — not LLM.**

## F3 — Why produced

C-IN-7 / R19 semantics: **do not guess** answer attribution when table cells cannot be mapped to this unit’s question numbers.

## F4 — What it means

| Interpretation | OBSERVED |
|---|---|
| Real answer missing from source? | **Not necessarily** — table **exists** and cells are stored in `answers.cells` |
| Answer exists but Q→A map fails? | **Yes** — `answers.unresolved` lists question numbers; 502 units / **596 slots** |
| Silent empty answer? | Forbidden by Integration Contract (`answers.get(q,"")` ban) |

## F5 — Original answer-table evidence retained?

**Yes on IR**: `answers.cells`, `answers.method` (`td_by_question_number` | `td_positional`), `answers.answers` (partial), `answers.unresolved`, plus `answer_text` lines and `provenance.source_lines.answer_lines`.

## F6 — Does V3 receive it?

**No** on current consumer path:

- flags not read;
- IR `answers` object not consumed (V3 uses manifest `answer_lines` spans only);
- annotation payload has no unresolved list.

## F7 — Does V3 drop it?

**Never ingested** = effective **loss at Boundary** for V3 semantic payload/Gate/review.  
IPM still lists `answers.unrelated`… `answers.unresolved` as keep (`IPM` F section: 502 级 flag; 不得填假答案).

## F8 — Relation to P07 / P08

- **P07** (answer table mapping strategy) remains **OPEN** — this file does not propose resolve.
- **P08** consumption of `flags` is the channel through which `answer_table_unresolved` would become V3-visible at all.

---

# APPENDIX A — Owner question checklist (compressed answers)

## P04

1. **Now per-option evidence?** **No.**  
2. **What does whole-span support?** Block-level provenance, IR slice, experimental label recovery, honest gap registration.  
3. **What is lost without per-label?** Choice ready-IR, stable option spans for grammar/labels, Gate path for choice under current adapter.  
4. **Blocks entering V3?** Not identity/annotation entry; **blocks choice ready → Gate/Admission**.  
5. **Blocks Answer verification?** Only label-inventory-dependent checks; answer_lines location still works.  
6. **Affects Gate/Admission?** Indirectly via incomplete skip; gap code itself unused by Gate.  
7. **Only enhancement capability?** Partly — whole-span provenance works; **choice auto/readiness** is the hard dependency, Owner defines whether that is “enhancement” or “required product path” (OD-P04).  
8. **Producer upgrade work?** Schema+prompt+QC+IR regen constraints+V3 adapter mapping — listed in §7, not authorized here.

## P08

1. **flags?** IR `string[]` structural observations, 2 values observed.  
2. **basis?** Identity legitimacy vocabulary string + evidence.  
3. **answer_evidence?** Per-unit `{type,lines,value,shared}`; **0 on 71 ADMITTED**; 906 units on other files.  
4. **Who produces?** flags=Resolver deterministic; basis=identity backfill deterministic; answer_evidence=LLM prompt (where present).  
5. **Authority?** flags=Producer UNC observation; basis=Producer identity provenance; answer_evidence=Producer evidence claim.  
6. **Actual values?** See §3 tables.  
7. **Counts?** flags 502/91; basis 1041/596/18/9; AE 0 on ADMITTED.  
8. **V3 receives where?** basis*/AE-lines at reader only; flags never.  
9. **Dropped?** flags never in; basis* dropped at adapter; AE type/value/shared dropped.  
10. **Unused but present?** ManifestUnit.basis* held in memory for reader tests; not projected.  
11. **Review signal potential?** Yes as draft IPM suggests — **not implemented**.  
12. **Qualified as Gate condition today?** **No Frozen qualification.**  
13. **Frozen authorizes Gate extension?** **No.**

---

# APPENDIX B — Investigation non-actions

| Check | Result |
|---|---|
| production code changed | **NO** |
| tests changed | **NO** |
| schema changed | **NO** |
| migration changed | **NO** |
| Frozen Spec changed | **NO** |
| Frozen Contract changed | **NO** |
| v0.3 Contract / Owner Decision Package changed | **NO** |
| corpus / Producer artifacts regenerated | **NO** |
| P04 / P08 closed | **NO** |
| P07 closed | **NO** |
| implementation / migration started | **NO** |

---

*End of INVESTIGATION report — OWNER DECISION INPUT only.*
