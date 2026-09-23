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

---

## OD-01R — DSH F-OD01R-01～10 Owner Finding Disposition（正式 Owner Decision）

```text
RECORD-TYPE: OWNER DECISION / FINDING DISPOSITION
AUTHORITY: OWNER DECISION（非 MIMO 建议 / 非 DSH 建议 / 非 Proposal 自述）
SOURCE: DSH targeted review F-OD01R-01…F-OD01R-10
DATE: 2026-09-23
BINDING: YES
EFFECT: 指导 OD-01 Proposal v3 + CR-002 治理化；不修改 Frozen Spec / Contract / 代码
```

> 本节是 **Owner Decision**。证据链：`DSH Finding → Owner Decision（本节）→ Implementation Instruction（Proposal v3 / CR-002）`。
> 不改变既有 OD-01～OD-05 / G-01 / G-02 语义；仅追加 R-01～R-10 处置。

| ID | Finding（DSH） | Owner Decision | Required Action | Status |
|----|-----------------|----------------|-----------------|--------|
| **OD-01R-01** | CR-002 位于 `Docs/COORDINATION/`，不能仅凭自称成为正式 L1 | **ACCEPTED** | 按 `90/91` 完成正式 L1 登记；不得自创 L1 目录/层级/状态；不得改治理规则迁就 CR-002；若无法合法登记 → 登记注册条件未满足（保留 Future registration path），**不得声称已为正式 L1** | **PENDING**（见下方 R-01 判定） |
| **OD-01R-02** | Proposal / CR-002 治理格式不合规（含自创 `L1-proposal`） | **ACCEPTED** | 使用 `90 §4` + `91 §5` 出生证明字段（含 Derives From / May Change / Must Not Change）；合法 Status / 层级 / 引用；废止 `L1-proposal` | **VERIFIED** |
| **OD-01R-03** | OD-01 对 Frozen Spec 影响分类不实（非「普通新增」） | **ACCEPTED** | 逐条重判 CHANGE-3/4/5；`00 §5` 非目标解除 = 约束放宽；`20 §5.3` V3 option 边界规则 = 删除/替换；如实登记，禁止压低级别 | **VERIFIED** |
| **OD-01R-04** | 只写 Artifact Path，未覆盖 Native Path | **ACCEPTED** | 同时表达 Path A（Native）与 Path B（Artifact/Adapter）；禁止两套语义标准；汇聚 Canonical V3 IR；覆盖 Native / Adapter / ResolvedRun / Canonical IR | **VERIFIED** |
| **OD-01R-05** | explicit diff 影响面不全 | **ACCEPTED** | 补 `10 §4:107-108`、`20 §6.2`、`50:51`；全树检索其余真实 affected clauses；完整影响面，不为凑数加无关章节 | **VERIFIED** |
| **OD-01R-06** | 不得要求一切 provenance 都有 `line_ref` | **ACCEPTED** | 按 form 定义 locator；禁止给 table_cell / image_region / 多来源编造 `line_ref` 或假连续行区间 | **VERIFIED** |
| **OD-01R-07** | 两个解析状态字段命名冲突 | **ACCEPTED** | 拆开 Provenance Resolution vs Option/Evidence Resolution；用现有 Frozen vocabulary 命名；不擅自改生产 Schema；若需新 Schema 字段 → STOP → 走本 CR | **VERIFIED** |
| **OD-01R-08** | `degraded` 与 fail-closed 关系不清 | **ACCEPTED** | `degraded` 不是后门；无法可靠验证 → fail closed；禁止 `degraded → 正常 Admission` 隐式行为 | **VERIFIED** |
| **OD-01R-09** | 缺正式 Owner Decision / Finding Disposition 记录 | **ACCEPTED** | 在本文件正式登记 R-01～R-10 为 Owner Decision（本节） | **VERIFIED** |
| **OD-01R-10** | `options_unresolved` 坐标错误；`sp-M1` 章节错误 | **ACCEPTED** | 给出准确 L0 coordinate；`sp-M1` = `20 §5.5`（非 `20 §6.1`）；全文检索同类错误 | **VERIFIED** |

### OD-01R-01 — 正式 L1 落位判定（注册条件未满足；保留 Future registration path）

> **未归层声明（90:47）：** `Docs/COORDINATION/` 不在 `90 §1.2` 目录模型内，属 **未归层**；未归层文档不得引用为权威。CR-002 / 本文件均不得充当 L0/L1/L2 权威来源。
> **单向表述：** 不是「没有 L1 落点」。注册条件未满足；保留 Future registration path；禁止第二 registry。

按 `90` / `91` 只读核对结果：

| 规则来源 | 内容 |
|----------|------|
| `90 §1` | L1 = **Contract Change Record**；修改 L0 的唯一入口；未走完流程不得生效 |
| `90 §1.2` | `Docs/V3_SPEC/` 允许「补 Change Record；**新增 L1**」；禁止「直接编辑；隐式改变」 |
| `90 §11` | L0 **实际修改后**必须在 Change Audit Record 登记（先例 CR-001 嵌于 `90 §11`） |
| `91 §5` | 新文档必须齐备出生证明（Document ID … Gate State Authority） |
| `91 §5.1` | 创建门槛四项；DG 期间冻结新建治理文档（指 90/91/82/84 类元治理文档） |
| `91 §3.1` | 合法 Status 含 `NOT RELEASED`（先例：`67`） |
| 先例 `67` | CHANGE-4/5 候选，位于 `Docs/DECISIONS/`，**NOT RELEASED**，**不是**已注册正式 L1 |

**障碍：**

1. 正式「新增 L1」落位在 `Docs/V3_SPEC/`（`90 §1.2`）。
2. 本轮硬边界要求 **Frozen Spec tree hash 保持 `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f` 不变**。
3. 向 `Docs/V3_SPEC/` 新增任何文件（含 L1）都会改变该 tree hash。
4. 既有目录模型内**没有**第二处正式 L1 registry。
5. `Docs/COORDINATION/` **不在** `90 §1.2` 目录模型内。
6. **不得**修改 `90/91` 规则迁就 CR-002；**不得**自创 L1 目录/层级/状态体系。

**判定（binding）：**

```text
按照 Frozen Document Governance，CR-002 当前【不是】已经正式注册的 L1 Change Record。
CR-002 = L1 candidate / NOT RELEASED（对齐 67 先例）
REGISTRATION PATH = 有效未来路径；当前 Candidate only；intentionally deferred
禁止声称：CR-002 已是正式注册 L1 / 已生效 / 已授权改 L0
```

### OD-01R-03 — CHANGE 分类裁决（禁止压低）

| 对象 | 原 Frozen Rule | OD-01 变化 | 实际变化 | **CHANGE** | Gate |
|------|----------------|------------|----------|------------|------|
| `00 §5` table cell/fragment 非目标 | 「文档级表格 cell/fragment 字符粒度索引」= M1 非目标 | table_cell 在 **option provenance 子集**解除延后 | **放宽既有非目标约束**（fragment / 完整表格索引仍非目标） | **CHANGE-4 Constraint Relaxation** | **四道门（69 §5）** |
| `20 §5.3` option_label | 「按 A/B/C/D 顺序；每项到下一标签/下一题结束」= V3 侧 option 边界发现 | Path B：Producer = segmentation authority；V3 **不得** rediscovery | **删除/替换**既有 V3 无条件 option 边界规则 | **CHANGE-5 Constraint Removal**（+ 新规 CHANGE-2/3） | **四道门（69 §5）** |
| `20 §5.5` 延后注 + form | table_cell/fragment 延后；无 form 维度 | form 维度 + 解除 table_cell option 子集延后 | 改既有规定 + 新增强制 | CHANGE-4 / CHANGE-2 / CHANGE-3 | 四道门（并入上列） |
| `20 §7.2` Compiler | 只从 line / line_character 提取 | 扩展至新 form | 改变既有规定的行为 | **CHANGE-3** | 受影响层回归 |
| 其余（10 §4/§6.3/§8、20 §6.1/§6.2/§7.3、50） | 见 Proposal v3 diff | 见 Proposal v3 diff | 见逐条 | CHANGE-1/2/3 | 见 CR-002 |

**总体：含 CHANGE-4 + CHANGE-5 → 必须四道门 + Change Record。**
**禁止**再写「这些不是 CHANGE-4/5，所以不需要对应 Gate」。

### OD-01R-01～10 有效范围

| Item | Effect |
|------|--------|
| OD-01R-01…10 | **Binding Owner Decision**；指导 Proposal v3 / CR-002 |
| OD-01 design | 仍为 APPROVED DESIGN / **PENDING FROZEN SPEC INCORPORATION** |
| Frozen Spec 00–50 | **UNCHANGED / NOT AUTHORIZED TO MODIFY** |
| Production / Schema / Corpus / Phase 1 / X3 | **UNCHANGED / NOT ENTERED** |

---


---

## OD-01-A…J — Owner Decision（OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE）

```text
RECORD-TYPE: OWNER DECISION
STATUS: OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE
AUTHORITY: Owner Decision（非 MIMO 建议 / 非 DSH 建议 / 非 Proposal 自述）
DATE: 2026-09-23
BINDING FOR EXECUTION: YES
EFFECT ON L0: NOT EFFECTIVE（PENDING EFFECTIVE FREEZE）
```

> 本节是 **Owner Decision**。**不使用「已生效」含义。**
> 证据链：Finding → Owner Decision（本节）→ Implementation Instruction（Proposal v4 / CR-002）。
> 不改变既有 OD-01～OD-05 / G-01 / G-02 / OD-01R-01…10 语义。

| ID | Decision | Required Action | Status |
|----|----------|-----------------|--------|
| **OD-01-A** | APPROVED | 恢复逐条 Frozen Text 级 Current → Proposed diff | VERIFIED IN v4 |
| **OD-01-B** | APPROVED | 保留「现有能力 / 真缺口 / 延后 / 非目标」缺口基线 | VERIFIED IN v4 |
| **OD-01-C** | APPROVED | CR-002 保持 COORDINATION；NOT EFFECTIVE / Candidate | VERIFIED |
| **OD-01-D** | APPROVED | CHANGE-3 / CHANGE-4 / CHANGE-5 全部承认；按四道门处理 | VERIFIED |
| **OD-01-E** | APPROVED | Native / Adapter / Artifact 统一 provenance 模型 | VERIFIED IN v4 |
| **OD-01-F** | APPROVED | **暂不新增 degraded**；不完整 → unresolved / review | VERIFIED IN v4 |
| **OD-01-G** | APPROVED | 拆分 resolution 命名；避免 option 与 answer 同名冲突 | VERIFIED IN v4 |
| **OD-01-H** | APPROVED | 删除模糊完成类状态词（91 §3.2）；仅用 APPROVED / PENDING / VERIFIED / NOT EFFECTIVE / NOT REGISTERED | VERIFIED |
| **OD-01-I** | APPROVED | OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE | VERIFIED |
| **OD-01-J** | APPROVED | 当前不 re-freeze；v4R → DSH 外部验证 → Owner 批准 → re-freeze | PENDING |

### OD-01-J 流程

```text
Proposal v4R
    → DSH 外部验证
    → Owner 批准
    → 正式 re-freeze
```

本轮 **不执行** re-freeze。Self Review ≠ DSH 外部验证；OD-01-J 只接受 DSH Review。

### 有效范围

| Item | Effect |
|------|--------|
| OD-01-A…J | OWNER APPROVED RECORD；指导 Proposal v4 / CR-002 |
| OD-01 design incorporation | PENDING EFFECTIVE FREEZE |
| Frozen Spec / Contract / Code / Schema / Corpus | UNCHANGED |
| Phase 1 / Migration / Re-freeze | NOT ENTERED / NOT AUTHORIZED / NOT EXECUTED |

---


---

---

## OD-01V4R-15…29 — Finding Disposition

```text
Document ID: OD-01-V4R-15-29-DISPOSITION
Title: OD-01V4R-15…29 Finding Disposition
Document Type: Decision Record
Status: PENDING
Authority Level: L2
Purpose: 登记 F-OD01V4R-15…29 的 Owner 裁决与落实位置
Normative: NO
Derives From: F-OD01V4R-15…29 · 90/91 §3.1 · Proposal v4R · Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md
May Change: Finding Disposition 列（非 Status 字段）
Must Not Change: L0 · Frozen Contract · Schema · Code · Corpus
Related Records: Proposal v4R · CR-002 · Docs/REPORTS/OD-01-PROPOSAL-V4-TARGETED-ADVERSARIAL-REVIEW.md · Docs/REPORTS/OD-01V4R-FINAL-REMEDIATION-REPORT.md
Supersedes: —
Superseded By: —
Gate State Authority: NO
Registration Level: NOT REGISTERED
```

> Status: PENDING（等待 effective freeze）。原「PENDING EFFECTIVE FREEZE」为描述短语，不是 Status 枚举值。  
> Authority Level: L2（冻结枚举）。不使用自创层级名。  
> 附录位于 `Docs/COORDINATION/` = **未归层**（90:47）。

完整映射以 **Proposal v4R §0** 为准（含 F-OD01V4R-01…29 全表）。本附录仅登记本轮 15–29 裁决。

| Finding ID | Final ID | Owner Decision | Status |
|------------|----------|----------------|--------|
| F-OD01V4R-15 | OD-01F-48 | APPROVED — 重建唯一 Mapping Table | VERIFIED |
| F-OD01V4R-16 | OD-01F-49 | APPROVED — Gap 单向化；保留 Future registration path | VERIFIED |
| F-OD01V4R-17 | OD-01F-50 | APPROVED — Header 含 Purpose；字段名 Derives From | VERIFIED |
| F-OD01V4R-18 | OD-01F-51 | APPROVED — Authority Level 仅决策权；与 Registration 分离 | VERIFIED |
| F-OD01V4R-19 | OD-01F-52 | APPROVED — Status 仅用 91 §3.1 允许词 | VERIFIED |
| F-OD01V4R-20 | OD-01F-53 | APPROVED — table_cell identity = Future Required Change | VERIFIED |
| F-OD01V4R-21 | OD-01F-54 | APPROVED — CI-1…12 保留 Current Rule 全结构 | VERIFIED |
| F-OD01V4R-22 | OD-01F-55 | APPROVED — CI-4 verbatim/summary 分离标注 | VERIFIED |
| F-OD01V4R-23 | OD-01F-56 | APPROVED — form 术语对应表 | VERIFIED |
| F-OD01V4R-24 | OD-01F-57 | APPROVED — Historical Self Review 格式 | VERIFIED |
| F-OD01V4R-25 | OD-01F-58 | APPROVED — 删除外仓路径 | VERIFIED |
| F-OD01V4R-26 | OD-01F-59 | APPROVED — 清除机械替换痕迹 | VERIFIED |
| F-OD01V4R-27 | OD-01F-60 | APPROVED — 统一 Derives From | VERIFIED |
| F-OD01V4R-28 | OD-01F-61 | APPROVED — v4R 唯一 Current Version | VERIFIED |
| F-OD01V4R-29 | OD-01F-62 | APPROVED — Future 词 = Planning Category only | VERIFIED |

---

## OD-01V4R-30…48 — Finding Disposition

```text
Document ID: OD-01-V4R-30-48-DISPOSITION
Title: OD-01V4R-30…48 Finding Disposition
Document Type: Decision Record
Status: PENDING
Authority Level: L2
Purpose: 登记 F-OD01V4R-30…48 的 Owner 裁决与落实位置
Normative: NO
Derives From: F-OD01V4R-30…48 · 90/91 §3.1 · Proposal v4R · Docs/REPORTS/OD-01V4R-FINAL-REMEDIATION-REPORT.md
May Change: Finding Disposition 列（非 Status 字段）
Must Not Change: L0 · Frozen Contract · Schema · Code · Corpus
Related Records: Proposal v4R · CR-002 · Docs/REPORTS/OD-01V4R-FINAL-REMEDIATION-REPORT.md
Supersedes: —
Superseded By: —
Gate State Authority: NO
Registration Level: NOT REGISTERED
```

完整修复证据见 `Docs/REPORTS/OD-01V4R-FINAL-REMEDIATION-REPORT.md`。本附录登记裁决。

| Finding ID | Final ID | Owner Decision | Finding Disposition |
|------------|----------|----------------|---------------------|
| F-OD01V4R-30 | OD-01F-63 | APPROVED — 映射表按 DSH 基线重建；-14 跨仓复制单独登记 | TEXT-CORRECTED |
| F-OD01V4R-31 | OD-01F-64 | APPROVED — -08/-09/-10 Problem 按基线恢复 | TEXT-CORRECTED |
| F-OD01V4R-32 | OD-01F-65 | APPROVED — 09/10 填入 V3-11/12；无空号 | TEXT-CORRECTED |
| F-OD01V4R-33 | OD-01F-66 | APPROVED — README §2 列 Future Required Change target | REMEDIATED |
| F-OD01V4R-34 | OD-01F-67 | APPROVED — form/granularity 维度定义；禁称正交 | REMEDIATED |
| F-OD01V4R-35 | OD-01F-68 | APPROVED — locator 按 form 分型 | REMEDIATED |
| F-OD01V4R-36 | OD-01F-69 | APPROVED — table_cell identity 方案 B | REMEDIATED |
| F-OD01V4R-37 | OD-01F-70 | APPROVED — 20 §5.5 合并全文 | REMEDIATED |
| F-OD01V4R-38 | OD-01F-71 | APPROVED — 示例 span_resolution | REMEDIATED |
| F-OD01V4R-39 | OD-01F-72 | APPROVED — CR-002 Status=NOT RELEASED | TEXT-CORRECTED |
| F-OD01V4R-40 | OD-01F-73 | APPROVED — Authority Level 用冻结枚举 | TEXT-CORRECTED |
| F-OD01V4R-41 | OD-01F-74 | APPROVED — 状态词分层真陈述 | TEXT-CORRECTED |
| F-OD01V4R-42 | OD-01F-75 | APPROVED — D1 附录出生证明齐备 | TEXT-CORRECTED |
| F-OD01V4R-43 | OD-01F-76 | APPROVED — Self Review HISTORICAL + 字段齐备 | TEXT-CORRECTED |
| F-OD01V4R-44 | OD-01F-77 | APPROVED — 历史正文全文恢复 | BODY-RESTORED |
| F-OD01V4R-45 | OD-01F-78 | APPROVED — 移除 Gap 路径标题；登记未归层 | TEXT-CORRECTED |
| F-OD01V4R-46 | OD-01F-79 | APPROVED — Supersedes=—；非规范字段移出 Header | TEXT-CORRECTED |
| F-OD01V4R-47 | OD-01F-80 | APPROVED — V3 Problem 按基线恢复 | TEXT-CORRECTED |
| F-OD01V4R-48 | OD-01F-81 | APPROVED — OD-01-J 统一 v4R → DSH 外部验证 | TEXT-CORRECTED |

---


**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md` |
| Status | RECORDED |
| Authority | OWNER DECISION RECORD |
| Companion | `LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md` · `FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` · `G-02-FREEZE-REGISTRATION-VERIFICATION.md` · `IMPLEMENTATION-PLAN-v0.3.md` |
