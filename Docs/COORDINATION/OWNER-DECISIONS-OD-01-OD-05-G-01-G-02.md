# OWNER-DECISIONS-OD-01-OD-05-G-01-G-02

```text
STATUS: RECORDED
AUTHORITY: OWNER DECISION RECORD
PURPOSE: FORMAL RECORD OF BINDING OWNER DECISIONS
SOURCE: DSH 独立对抗审查后 Owner 最终裁决
RECORDED-AT: 2026-09-23 (governance task OD-01~05 + G-01/G-02 reconciliation)
```

> 本文件是 Owner Decision Record。
> Authority Order：`Frozen Spec > Frozen Contract > Owner Decisions > Implementation Plan > Implementation`。
> 本记录不得覆盖 Frozen Spec / Frozen Contract；与之冲突时 STOP → Owner。
> **OD-01 = APPROVED DESIGN DECISION / PENDING FROZEN SPEC INCORPORATION**（不得视为已生效 Frozen Spec）。

---

## Summary Table

| ID | Decision | Status |
|----|----------|--------|
| **OD-01** | Extend Frozen Resolved Span（P04 Option Provenance ontology） | **APPROVED** — Frozen Spec Change Proposal **pending**；未 re-freeze 前不生效 |
| **OD-02** | Source-derived Metadata = Source Authority + Conflict-as-signal | **APPROVED** — binding now |
| **OD-03** | Evidence = Complete Traceability（不锁 persistence table） | **APPROVED** — binding now |
| **OD-04** | Production Entry = Artifact-first / Artifact-authoritative | **APPROVED** — binding now |
| **OD-05** | Producer-side Artifact Schema extensible / V3 Frozen Schema STOP | **APPROVED** — binding now |
| **G-01** | Implementation Plan + Limited Implementation Authorization must enter Git | **APPROVED** — executed in this task |
| **G-02** | `b743c5d → 7934844` = Freeze Registration only | **VERIFIED** |

---

## OD-01 — P04 Option Provenance（Extend Frozen Resolved Span）

### Owner Decision

**扩展 Frozen Resolved Span。** P04 要求的 Option Provenance 正式进入 V3 的 Frozen Resolved Span ontology。

必须支持至少：

```text
line_range
char_span_in_line
table_cell
multiple_source_spans
other verifiable source provenance
```

字段命名可提出实现建议，**不得改变上述语义**。

### Binding Requirements

1. `options[]` 保留 `label` + `text` + `provenance`。
2. `options_lines` **不得删除**（与 `options[]` 并存）。
3. 不得假设「一个 option = 一行」或「一个 option = 一个 span」。
4. Table Cell 必须能够表达。
5. Multiple Source Spans 必须能够表达。
6. 不可可靠定位的 Option：不得猜测；必须进入 explicit `unresolved` / `QC_FAIL` / `INCOMPLETE`。
7. V3 不得通过 LLM 自行猜测 Option 边界以代替 Preprocessing evidence。

### Critical Boundary

OD-01 明确触发 **Frozen Spec Change Required**。

```text
Owner Decision
  → Frozen Spec Change Proposal（本任务产出 D4）
  → explicit diff
  → Owner review
  → re-freeze
```

**在 re-freeze 之前：OD-01 是 APPROVED DESIGN DECISION / PENDING FROZEN SPEC INCORPORATION，不是已经生效的 Frozen Spec。**

禁止直接修改 Frozen Spec 并声称已生效。

Proposal 位置：`Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md`

---

## OD-02 — Source-derived Metadata Authority

### Owner Decision

采用 **A + Conflict-as-signal**。

### Authority

```text
Original Source
  → AITutors-preprocessing
  → verified Source-derived Metadata     = AUTHORITATIVE
```

LLM Annotation 只能提供 `annotation claim`，**不得静默覆盖**已验证的 Source-derived Metadata。

### Conflict-as-signal

当 `Source-derived value != Annotation claim`：

1. 两者均不得静默丢弃；
2. 保留 conflict signal；
3. Source-derived value 继续作为 **authoritative value**；
4. Annotation claim 保留为 **non-authoritative claim**；
5. conflict 本身默认 **不是** Admission blocker；
6. 除非 Frozen Spec 明确规定，否则不得自行把 conflict 提升为 Gate condition。

若必须修改 Frozen Spec 才能消除冲突：`STOP → Frozen Spec Change Proposal → Owner`。

本规则写入 Owner Decision Record + Implementation Plan + Semantic Authority / Information Preservation governance 记录；**不得自行扩大 Frozen Spec**。

---

## OD-03 — P08/P24 Evidence Persistence

### Owner Decision

**不预先指定 Evidence 必须进入某一个具体物理层。** 要求是 **完整可追溯**。

### Binding Requirements

1. Evidence 不得静默丢失；
2. 能追溯到 Original Source；
3. 能关联到对应 Question / Candidate / Admission decision；
4. 能解释 Gate / Review / Resolution；
5. 不得因为保存 Evidence 改变 Question Core；
6. 在现有 Frozen Schema 能表达的范围内 **优先复用现有结构**；
7. 若必须修改 V3 Frozen Schema：`STOP → Schema/Frozen Spec Change Proposal → Owner`。

### Explicit Non-Decision

本轮 **不冻结** 具体 persistence table。禁止自行决定「Evidence 一律放 Candidate 表」或「一律新增 QuestionEvidence 表」，除非现有 Frozen Schema / Owner Decision 已明确允许。

**本轮冻结的是：Evidence Preservation + Traceability Requirement（非 storage layer）。**

---

## OD-04 — Production Entry Authority

### Owner Decision

正式确立 **Artifact-first / Artifact-authoritative**。

正式语义入口：

```text
Original Source
  → AITutors-preprocessing
  → Preprocessing Artifact
  → V3 Consumer Boundary
  → Identity Verification / M1–M5
  → Canonical V3 IR
  → Gate
  → Admission
```

### Important Boundary

Artifact-first / Artifact-authoritative **不等于** 立即删除 TaskExecutor。

必须先分析现有 `TaskExecutor` / `LLM Annotation` / `GateService` / `worker` 各自职责。

| 允许保留 | 禁止保留 |
|----------|----------|
| infrastructure | 第二条具有独立 semantic authority 的正式 ingestion path |
| execution capability | |
| fallback / internal service | |

必须明确区分：`semantic authority` · `execution infrastructure` · `fallback / internal service` — 三者不能混淆。

若现有代码需要修改 Frozen Data Model / Frozen Spec 才能实现：`STOP`。

---

## OD-05 — Frozen Schema Boundary

### Owner Decision

```text
Preprocessing / Producer-side Artifact Schema
  → 可以扩展（within Contract semantics）

V3 Frozen Schema
  → 不可由 Implementation 自行扩展
```

即：

```text
Preprocessing Artifact requirement
  → Producer-side can evolve
  → within Contract semantics
```

```text
V3 Frozen Schema insufficient
  → STOP
  → Frozen Spec Change Proposal
  → Owner Authorization
  → re-freeze
```

**Implementation Plan 不构成 Frozen Schema modification authorization。**

---

## G-01 — Governance Artifacts Must Enter Git

### Owner Decision

Implementation Plan + Limited Implementation Authorization **必须进入 Git**。

执行要求（本任务完成）：

1. `Docs/COORDINATION/IMPLEMENTATION-PLAN-v0.3.md` 纳入正式 Git baseline，且与最新裁决一致（含 Authority Order 修正、OD-01~05、禁错误术语、不把未授权 schema 写成既定事实）。
2. Limited Implementation Authorization 正式进入 Git，完整保留 scope / authority order / forbidden scope / stop conditions / phase order / terminology / historical rerun / migration / X3 限制。

---

## G-02 — `b743c5d → 7934844` Verification

### Owner Conclusion（binding wording）

```text
b743c5d remains the Frozen Semantic Baseline.
7934844 is the Freeze Registration / governance-state commit.
```

**禁止再表述为**「7934844 修改了 Frozen Semantic Baseline」或「7934844 是 Frozen Semantic Baseline」。

### Comparison Facts

```text
base        = b743c5daf0806ea00c84afb1b92ca2a3b5dbfc98
head        = 79348441dae0efce6855017b2b5c0491b08d6bb8
ahead_by    = 1
total_commits = 1
```

仅涉及 7 files（status/ledgers）：

- `PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md`
- `PREPROCESSING-V3-INFORMATION-PRESERVATION-MATRIX-v0.3-DRAFT.md`
- `PREPROCESSING-V3-OPEN-DECISIONS-v0.3-DRAFT.md`
- `PREPROCESSING-V3-SEMANTIC-AUTHORITY-MATRIX-v0.3-DRAFT.md`
- `V3-POST-ADMISSION-ENRICHMENT-CONTRACT-v0.3-DRAFT.md`
- `CURRENT.md`
- `state.yaml`

内容：Contract→`FROZEN`；Owner Approval=`APPROVED`；Frozen Baseline 登记为 `b743c5d`；Freeze timestamp；P01–P25 / P04/P07/P08/P15–P19 状态同步；CURRENT/state.yaml 同步。

**G-02 = VERIFIED.**

详细记录：`Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md`

---

## Terminology（mandatory，与 Frozen Canonical Vocabulary 一致）

```text
Canonical V3 Unit Types:
  standalone_unit
  composite_unit

Canonical V3 Question Types:
  Frozen Spec 12-value closed set only

Historical only（禁止作为当前 V3 concept）:
  standalone_question
  composite_question
  "Standalone Question"
```

---

## Effective Scope of This Record

| Item | Effect |
|------|--------|
| OD-02, OD-03, OD-04, OD-05, G-01, G-02 | **Binding immediately** |
| OD-01 | Design approved；**Frozen Spec incorporation pending**（see D4 Proposal） |
| P01–P25 / P04/P07/P08/P15–P19 | **NOT reopened / NOT changed** |
| Phase 1 implementation | **NOT STARTED** by this record |

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md` |
| Status | RECORDED |
| Authority | OWNER DECISION RECORD |
| Companion | `LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md` · `FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` · `G-02-FREEZE-REGISTRATION-VERIFICATION.md` · `IMPLEMENTATION-PLAN-v0.3.md` |
