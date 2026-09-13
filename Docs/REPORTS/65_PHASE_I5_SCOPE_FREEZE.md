# Phase I-5 Scope Freeze: Preprocessed Source Integration Feasibility

Authority Level: L4 — Experiment Report（D-03 归层 2026-09-13）
Normative: NO
Gate State Authority: NO（唯一权威 = 82 §3）
Status: HISTORICAL — **69 号已定性为 Evidence**
        （`69 §2`：`65 Path B | Experiment | 当前不需要 | Evidence`；
         `69 §65`：`Current Status: Experiment / Evidence Record`）。
        **Phase I-5 已 CLOSED**（69 裁决）。下方 §5 十二条是 **I-5 实验期 scope
        freeze 契约**，随 I-5 结束而成为历史；其中仍然有效的架构约束现行载体是
        **`63 §10.9`/`§10.10` 与 `81 §5.6`**，不是本文件。
        （2026-09-13 84 D-03：**不升 L2**——升 L2 会与 69 定性矛盾，且会造成
        第二来源。Disposition = **KEEP**。）
> 📌 **路径修正（残余审计 A-11，2026-09-13）**：本文 §- 表内
> `Docs/V3_SPEC/Closure/PHASE_I4_CLOSURE.md`、`Docs/V3_SPEC/63_…`、
> `Docs/V3_SPEC/64_…`、`Docs/V3_SPEC/65_…` 是 **DG-2 迁移前**路径，已失效；
> 现行均在 `Docs/REPORTS/`。正文保留为历史，不改写。
Status（原文）: Experiment Constraint (NOT a Domain Contract modification)
Applies From: Phase I-5 start until I-5-4 Decision
Predecessor: 63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md (§10.9, §10.10), PHASE_I4_CLOSURE.md

> **Phase I-5 Scope Freeze is an experiment constraint document. It does not modify the V3 domain contract defined by the Frozen Specification.**

---

## 1. Background

Phase I-4 established a measured negative result: span-level layout evidence (font, size, flags, bbox, origin) has 0% disambiguation rate for math PDF question-marker ambiguity (42 ambiguous targets, 0 resolved). Root cause: semantic role insufficiency, not geometric deficiency.

An external preprocessing pipeline (PaddleOCR-VL → LLM semantic annotation → manifest) has produced structural annotations for 17 pilot documents. Preliminary validation against 12 human-reviewed Grade 1/Grade 2 samples shows:

- 319/319 units with valid line references
- 319/319 answer coverage
- 42/42 Phase I-4 numeric markers correctly classified by manifest structural role
- 24/24 composite units with material ⊆ questions constraint satisfied

**This proves the manifest is internally consistent. It does NOT prove V3 integration feasibility.**

---

## 2. Phase I-5 Definition

> **Phase I-5 is an integration feasibility experiment, not a subsystem implementation.**

Core question:

> Can human-reviewed preprocessing artifacts enter the existing V3 pipeline through the smallest possible adapter, without breaking V3 architectural invariants, and produce a measurable improvement in end-to-end resolution/admission correctness?

---

## 3. Total Principle

> **Integrate the minimum semantic evidence required to eliminate the demonstrated ambiguity; do not import the preprocessing project's data model into V3.**

---

## 4. Architecture Boundary (Highest Priority Constraint)

> **Manifest may provide evidence about structure, but it may never become a second source of textual truth or a second semantic authority.**

```
Markdown Source
   │
   └── Source Evidence / 唯一正文事实
            ↑
            │ references (line numbers)
            │
Manifest ───┘
   │
   └── Structural Annotation Evidence
```

**Forbidden pattern:**

```
Manifest ─────→ V3 Semantic Source
Markdown ─────→ V3 Source
                         ↓
                    双重事实来源
```

**Forbidden operation:**

```
manifest.stem_lines
      ↓
复制正文
      ↓
成为新的 Source text
```

**Required operation:**

```
manifest.stem_lines
      ↓
定位 Markdown Source
      ↓
ResolvedSpan
      ↓
V3 IR
```

---

## 5. Twelve Constraints

| # | Constraint | Rationale |
|---|-----------|-----------|
| 1 | **不得修改 SourceResolver** | Manifest 价值尚未证明；Resolver 是现有 semantic authority |
| 2 | **不得引入新的永久 Source 抽象** | 实验阶段不得创建 domain entity |
| 3 | **不得修改 Source evidence 不变式** | Source = immutable fact；Manifest ≠ Source |
| 4 | **不得将 manifest metadata 视为 immutable source fact** | Manifest 是上游 semantic interpretation |
| 5 | **Markdown 内容是 Source evidence；Manifest 是 structural/semantic annotation** | 保持事实与解释的边界 |
| 6 | **测量真实 pipeline 结果，而非标注可用性** | 42/42 定位 ≠ 集成成功 |
| 7 | **使用已审核的高一/高二文档，覆盖多科目多题型** | 单一数学卷不足以证明通用性 |
| 8 | **主要成功指标：端到端 resolution/admission 正确性提升，且不在 Resolver 中引入新的 semantic inference** | 正确性 > 覆盖率 |
| 9 | **若实验未证明可测量的提升，不建立新的集成子系统** | No evidence of value → no subsystem |
| 10 | **永久架构变更仅在实验建立 measured integration benefit 后才可设计** | 防止实验变成架构开发 |
| 11 | **必须保留无 manifest 的原始 Source 路径** | 否则无法证明是增强而非替代 |
| 12 | **若接入 manifest 需要大量 domain entity / migration / workflow，必须暂停并重新做复杂度审查** | Complexity guardrail |

---

## 6. Candidate Evidence Classification

> **I-5-0 only defines which upstream fields may be observed as candidate structural evidence. Final admission into V3 contracts, persistence, or domain models is explicitly deferred to I-5-1.**

### Layer 1: Line Reference Evidence (Source references)

| Manifest Field | I-5-0 Status | Notes |
|---------------|-------------|-------|
| `stem_lines` | Candidate Evidence | 行号引用，指向 Source |
| `options_lines` | Candidate Evidence | 行号引用 |
| `answer_lines` | Candidate Evidence | 行号引用 |
| `explanation_lines` | Candidate Evidence | 行号引用 |
| `material_lines` | Candidate Evidence | composite 专用 |
| `questions_lines` | Candidate Evidence | composite 专用 |

### Layer 2: Semantic/Structural Evidence

| Manifest Field | I-5-0 Status | Notes |
|---------------|-------------|-------|
| `unit_id` | Experimental Mapping Identifier | upstream unit identifier，用于实验映射；≠ V3 Question identity |
| `unit_type` | Candidate Semantic Evidence | standalone/composite 分类 |
| `question_numbers` | Candidate Semantic Evidence | 可用于实验映射；不能直接成为 V3 identity |
| `original_question_type` | Candidate Semantic Evidence | 上游分类结果；≠ V3 canonical type；需通过 Adapter mapping |

### Layer 3: Deferred / Forbidden

| Manifest Field | I-5-0 Status | Notes |
|---------------|-------------|-------|
| `extra_lines` | Candidate, Not Committed | 目前无足够证据证明 V3 闭环需要 |
| `annotation_meta` | **Forbidden** | 上游生成元数据，非 Source structural evidence |
| `model` | **Forbidden** | provider/model provenance，不属于 V3 semantic input |
| `source_file` | **Forbidden** | 上游路径，不属于 V3 identity |

---

## 7. Critical Distinctions

### 7.1 unit_id ≠ V3 Identity

```
Manifest unit_id
≠
V3 Question identity
≠
Task ID
≠
Attempt ID
≠
QuestionInstance ID
```

`unit_id` is an upstream preprocessing unit identifier used only for experimental mapping:

```
manifest.unit_id
        ↓
experimental mapping
        ↓
V3 semantic unit / source span
```

### 7.2 original_question_type ≠ V3 Canonical Type

```
Manifest original_question_type  (上游分类)
        ↓
Adapter mapping
        ↓
V3 canonical semantic type      (V3 语义契约)
```

即使两边 enum 值恰好相同，也不得在 I-5-0 假设等价。是否 100% 对应是实验结果，不是前提。

---

## 8. Adapter Location

> **I-5 实验适配层不得进入 `backend/app/`。**

### Experimental execution code

```
experiments/phase_i5/
├── README.md
├── adapter.py          # manifest → experimental mapping
├── runner.py           # experiment execution
└── fixtures/           # test data references
```

### V3 contract/integration tests

```
backend/tests/phase_i5/
├── test_integration_feasibility.py
└── ...
```

### Boundary rule

Adapter **只能调用现有 V3 boundary**，不能创建新的 V3 Domain、Repository、ORM 或 Source Truth。

```
experiments/phase_i5
        │
        │ experimental adapter
        ↓
existing V3 application services
        │
        ↓
existing V3 domain
        │
        ↓
existing DB
```

**Forbidden:**

```
experimental manifest
       ↓
backend/app/new_domain/
       ↓
new ORM
       ↓
new migration
       ↓
new resolver
```

---

## 9. Stage Definitions

```
I-5-0  Scope Freeze（本文档）
       │  冻结边界，不设计实现
       ↓
I-5-1  Integration Boundary Analysis
       │  ├── Manifest 哪些字段真正有用？
       │  ├── 它们对应 V3 哪个已有 contract？
       │  ├── 是否可以只通过 Adapter？
       │  ├── 是否需要修改 Resolver？
       │  ├── 是否需要修改 Annotation？
       │  ├── 是否需要新增 Domain entity？
       │  ├── 是否需要 migration？
       │  └── 是否形成第二语义层？
       ↓
I-5-2  Minimal Adapter Design
       ↓
I-5-3  Experiment Execution
       │  ├── Baseline: 现有 Resolver 对相同 Source 的结果
       │  └── Manifest-assisted: 通过 Adapter 的结果
       ↓
I-5-4  Measurement & Decision
```

---

## 10. Measurement Dimensions

> **I-5-0 does NOT freeze specific numerical thresholds.**

Measurement dimensions are defined here; baseline population and thresholds are determined in I-5-1 based on actual data.

### Comparison: Baseline vs Manifest-assisted (相同 Source / 相同题目集合)

| # | Dimension | Notes |
|---|----------|-------|
| 1 | Resolver target resolution rate | |
| 2 | `semantic_status=ready` rate | |
| 3 | Gate pass rate | |
| 4 | Admission rate | |
| 5 | Ambiguity / unresolved 数量 | |
| 6 | **新增错误 resolution 数量** | 正确性 > 覆盖率 |
| 7 | 是否需要修改 V3 核心 Domain | 架构代价 |

> **错误地解析一题，比解析失败一题严重得多。** 与 V3 fail-loud 原则一致。

---

## 11. Decision Matrix (I-5-4)

| Outcome | Condition | Verdict |
|---------|-----------|---------|
| **A** | 端到端跑通，Resolver 正确率/可解析率显著改善，且无需破坏 V3 Source/Domain 边界 | **Integration feasible → 进入正式 Import Layer 设计** |
| **B** | 端到端跑通，但改善很小/无改善 | **Technically feasible but low value → 不继续扩展** |
| **C** | 必须修改核心 Resolver semantic authority / Source model 才能工作 | **Boundary conflict → 停止，重新设计** |
| **D** | 需要大量 Domain、ORM、Migration、workflow 或第二套 semantic model | **Complexity failure → 放弃或大幅简化** |
| **E** | 能提高 resolution，但引入错误匹配或事实污染 | **Correctness failure → 不接受** |

---

## 12. Evidence Artifacts

| Artifact | Location | Status |
|----------|----------|--------|
| Phase I-4 Closure | `Docs/V3_SPEC/Closure/PHASE_I4_CLOSURE.md` | CLOSED |
| Architecture Guardrails | `Docs/V3_SPEC/63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md` | Frozen |
| I-4 Evidence Evaluation | `Docs/V3_SPEC/64_PHASE_I4_EVIDENCE_EVALUATION.md` | Complete |
| Preprocessing Pilot Report | `D:\Project\Papers\reports\reslice_pilot_report.md` | 16/16 PASS |
| Integration Validation (319 units) | Session test output | 12/12 PASS, 0 errors |
| This Scope Freeze | `Docs/V3_SPEC/65_PHASE_I5_SCOPE_FREEZE.md` | Active |

---

## 13. Next Step

**I-5-1: Integration Boundary Analysis**

Analysis questions:
1. Manifest 哪些字段在 319-unit 实验数据中真正被消费？
2. 每个候选字段对应 V3 哪个已有 contract（SourceSpan / SemanticUnit / Annotation）？
3. 最小 Adapter 需要哪些转换逻辑？
4. 是否存在必须修改 Resolver 才能解决的场景？
5. Baseline 如何建立（相同 Source 走现有 pipeline 的结果）？

**No code until I-5-1 analysis is complete.**
