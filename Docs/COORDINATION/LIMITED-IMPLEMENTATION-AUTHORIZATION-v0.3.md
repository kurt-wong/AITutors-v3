# LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3

```text
STATUS: OWNER APPROVED
AUTHORITY: LIMITED IMPLEMENTATION AUTHORIZATION
PURPOSE: SCOPE-BOUNDED IMPLEMENTATION PERMISSION
OWNER-APPROVED: YES
ENTERED-INTO-GIT: YES (G-01)
```

> 本授权是 **LIMITED**。
> 只授权实施已经由 Frozen Spec / Frozen Contract / Owner Decision 明确的内容。
> 实施过程中不得因为发现设计缺口而自行扩大 Contract、Frozen Spec、Schema、Gate、Admission 或 Authority 语义。
> Implementation Plan 获批 ≠ unrestricted schema authorization。

> **Ratification / Provenance 注记（2026-09-25，M-03）**
>
> 本注记**只**补 provenance 落点；**不**是新的 Owner approval，**不**扩大任何授权范围。
>
> ```text
> 原始 Owner approval 的来源
>   = 本 instrument（v0.3）内容的 Owner 批准，属【仓外任务授权载体】，不在 repository 内。
>     仓内对应登记 = OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md 的 G-01
>       （"Implementation Plan + Limited Implementation Authorization 必须进入 Git"，
>         APPROVED — executed）
>     —— G-01 是【入 Git 登记】，不是内容批准的原始载体，两者不得混同。
>
> 后续仓内编辑（2026-09-24 起）
>   = 解释性修正（如下方 Frozen Spec: 行的 scope clarification）。
>     只做【解释范围收窄 / 澄清指称对象】：
>       未扩大任何授权范围 · 未放宽任何 forbidden scope ·
>       未改 Authority Order · 未改任何 STOP condition · 未改 phase order / terminology 限制。
>
> 当前正文 ≠ 重新伪造的 Owner approval
>   = 本注记不主张「当前正文 == Owner 批准时的原始文本」，也不主张该等式成立。
>     现行正文 = 原始批准文本 + 后续仅收窄解释范围的修正 的【合成状态】。
>     头部 STATUS: OWNER APPROVED 的语义一律不变，不在本注记中被重新签发或重新批准。
>
> ratification 机制状态
>   = 仓内【有】可复用机制：current-ratification 模式（OD-01-R3 — CURRENT OWNER RATIFICATION，
>       current ratification ≠ historical authorization）+ 入 Git 登记（G-01）。
>     仓内【无】一份独立可解析的「Owner 批准文本原件」。
>   ⇒ 复用上述既有机制落 provenance；【不新建】Owner approval 机制，【不新建】registry。
>     本注记不构成、也不伪造任何新的 Owner approval。
> ```

---

## 1. Authority Order

```text
Frozen Spec
    >
Frozen Contract
    >
Owner Decisions
    >
Implementation Plan
    >
Implementation
```

发现 Frozen Contract 与 Frozen Spec 冲突：

```text
STOP → 记录冲突 → Owner Decision
```

不得自行解决。不得通过 Implementation PR「顺便修正」Frozen Contract。

**已冻结、不得重新打开：** P01–P25（含 P04/P07/P08/P15–P19 CLOSED）· Historical Source Reprocessing Principle · Question Core / Metadata Boundary · Source-derived Metadata · LLM-derived Metadata · Post-Admission Enrichment · Identity / SHA256 语义 · Producer / Preprocessing / V3 Consumer Boundary 职责划分。

---

## 2. Terminology Rules（mandatory）

```text
Unit Type:
  standalone_unit
  composite_unit

Question Type:
  single_choice | multiple_choice | true_false | fill_in | short_answer |
  essay | cloze | reading | grammar_fill | vocabulary_fill |
  seven_to_five | reading_expression
```

**不存在 `Standalone Question`。** `standalone_question` 只能作为历史/Producer/Legacy vocabulary 被识别和记录。

禁止：

- 代码中新增 `Standalone Question` 概念；
- 文档中把 `standalone_question` 当成当前 V3 Question Type；
- 建立 `standalone_question → canonical_question_type` 兼容模型；
- Unit 语义使用 `standalone_unit / composite_unit` 以外的 canonical 值。

历史数据：

```text
Legacy vocabulary → current preprocessing → canonical unit/question vocabulary
```

而不是在 V3 中建立兼容类型。

---

## 3. Approved Direction（binding）

### 3.1 Historical Source Reprocessing — AUTHORIZED IN PRINCIPLE

```text
Original Historical Source
  → Current AITutors-preprocessing
  → Current-standard Preprocessing Artifact
  → V3 Consumer Boundary
  → Identity Verification
  → IR → Gate → Admission
```

必须遵守：

- Legacy Preprocessing Artifact 不直接迁移；
- 不 patch historical artifact；
- 不进行 V3 compatibility adaptation；
- 不直接修改数据库使历史数据入库；
- `pending_review` 经人工处理后必须重新经过完整标准链路；
- 每次根据原始内容计算 `source_content_sha256`；
- Source SHA 是内容身份，不是阶段标识。

**重要限制：历史 Corpus 暂不进行大规模正式 rerun。** 先完成当前实施阶段及小规模/金样验证。仅当达到 Phase 4 Entry Criteria 后，才执行正式 Historical Rerun。

**Historical Rerun: AUTHORIZED IN PRINCIPLE / EXECUTE AFTER IMPLEMENTATION VERIFICATION。**

### 3.2 Production Entry — Artifact-first / Artifact-authoritative（OD-04）

正式生产路径逐步统一为：

```text
Original Source
  → AITutors-preprocessing
  → Preprocessing Artifact
  → V3 Consumer Boundary
  → V3 IR / Compiler / Gate / Admission
```

现有 `TaskExecutor → LLM annotation → GateService` **不得**继续作为可绕过正式 Consumer Boundary、独立产生 Canonical V3 数据的第二 Authority Path。

实施时必须：

1. 先确认现有 production path 的实际用途；
2. 确认哪些代码属于旧/并行入口；
3. 设计统一 Boundary 接入；
4. **不得**为了统一入口直接删除现有代码；
5. **不得**擅自改变 Frozen Gate / Admission 语义。

若需改变 Frozen Spec 才能完成统一：`STOP → Owner Decision`。

区分：`semantic authority` vs `execution infrastructure` vs `fallback / internal service`。

### 3.3 Source-derived Metadata Authority — OD-02

- Authority = Original Source → AITutors-preprocessing → verified Source-derived Metadata；
- LLM Annotation = `annotation claim` only，不得静默覆盖 verified Source-derived Metadata；
- Conflict-as-signal：双保留 + Source-derived 为 authoritative + claim 为 non-authoritative + conflict 默认非 Admission blocker；
- 除非 Frozen Spec 明确规定，不得自行把 conflict 提升为 Gate condition。

### 3.4 Evidence Persistence — OD-03

- 完整可追溯；不得 silent discard；
- 可追溯到 Original Source；可关联 Question / Candidate / Admission decision；可解释 Gate / Review / Resolution；
- 不得因保存 Evidence 改变 Question Core；
- 优先复用现有 Frozen Schema 结构；
- **不预先锁定 persistence table**；
- 必须改 V3 Frozen Schema → `STOP → Proposal → Owner`。

### 3.5 Schema Change Boundary — OD-05（硬性 STOP）

**允许：** 使用现有 Schema；使用现有合法字段；修正代码与 Frozen Schema 的不一致；为已有 Frozen 属性补齐实现；**Producer-side / Preprocessing Artifact Schema 在 Contract 语义内可扩展**。

**不允许自行新增 Frozen Data Model 属性**，特别是：

- `Docs/V3_SPEC/10_Data_Model`
- `Docs/V3_SPEC/20_Document_Pipeline`
- Question / QuestionInstance 正式字段
- Gate / Admission formal state
- 新的正式 authority field

若「Contract 要求保存但 Frozen Schema 没有位置」：

```text
记录 Schema Gap → 说明现有 Schema 为何无法承载 → STOP → Owner Decision / Frozen Spec Change
```

**不得自行 ALTER TABLE。** Implementation Plan 不构成 Frozen Schema modification authorization。

### 3.6 Question Core / Metadata Boundary（frozen）

```text
Question Core → Admission
Source-derived Metadata → 随 Question 保存（可靠可得时）
LLM-derived Metadata → Post-Admission Enrichment
Post-Admission Enrichment → 不得反向阻塞已完成的 Admission
```

- 不得因 metadata 缺失把不完整 Question 当成完整 Question；
- difficulty / knowledge_nodes / skills 等 **不得**成为普通 Admission 前置条件（除非 Frozen Spec 明文升格某字段）。

### 3.7 Explanation Enrichment（P15–P19，frozen）

- 已有原始 explanation → preserve → **NEVER overwrite**；
- 缺少 explanation → Admission 后 async：MIMO generate → DeepSeek validate；
- 失败：最多一次 retry；第二次失败 → `suspended`；
- Enrichment failure **不得 rollback Admission**；
- P15 只是 explanation-specific generation/overwrite rule — **不得**实现成「Post-Admission 只能生成 explanation」；difficulty/knowledge_nodes/skills 仍属 Post-Admission Enrichment。

### 3.8 P04 / P07 scope（implementation authorized after OD-01 re-freeze for P04 span ontology）

- P04：`options[]={label,text,provenance}`；保留 `options_lines`；polymorphic provenance；fail closed；V3 不得 rediscovery。（Resolved Span ontology 扩展见 OD-01 Proposal — **pending re-freeze**）
- P07：完善 `answer_table_unresolved` / `answer_number_mismatch` / `answers.cells` / mapping rules；信息必须保留；mapping 可验证；不猜测；unresolved 显式保留。
- **未授权** 为 `answer_table_unresolved` 新增 Gate/Admission 规则。`answer_table_unresolved ≠ 自动新增 Gate condition`。若认为必须改变 Gate/Admission 语义：`STOP → Owner Decision`。

### 3.9 `semantic_status=unknown`

**未授权** 自行创造新的正式 V3 Question state / schema。

遇 `semantic_status=unknown`：先按当前 Frozen Spec 已有语义处理。若现有规范无法表达：

```text
STOP
记录：当前输入 / 当前行为 / 为何现有状态无法表达 / 建议方案 / 影响范围
→ Owner Decision
```

禁止自行新增 `reviewable` / `needs_review` / `semantic_unknown` 等正式状态。

### 3.10 Material / Unit

不得重新引入 `Standalone Question` / `standalone_question` 作为当前 Question 类型。Material 讨论使用 `standalone_unit` / `composite_unit` / `material`。先检查既有 Frozen Spec / Owner Decision / CL-22 / OD-BLOCK-02；已有裁决则直接执行。仍冲突 → `STOP → Owner Decision`。不得顺手重新设计 Unit/Material 语义。

---

## 4. Implementation Phase Order

```text
Phase 0  Baseline Verification          [COMPLETE]
Phase 1  Preprocessing Contract Implementation
Phase 2  V3 Consumer Boundary
Phase 3  Admission Alignment
Phase 5  Post-Admission Enrichment
Phase 6  End-to-End Verification
Phase 4  Historical Source Rerun        [after implementation verification]
```

Historical Rerun 不作为开发过程中的活动数据集。

**Enrichment: AUTHORIZED IN PRINCIPLE / Schema Gap → STOP。**

**Phase 1 在 OD-01 Frozen Spec Change Proposal 完成 Owner review + re-freeze 之前不得启动 P04 Resolved Span ontology 相关实现。**（见 Owner task：OD-01 reconciliation 完成前不得进入 Phase 1。）

---

## 5. STOP Conditions（任一命中 → 立即停当前子任务并报告 Owner）

- A. Frozen Spec 冲突
- B. Frozen Contract 冲突
- C. 必须修改 Frozen Schema
- D. 必须新增 Question / Unit / Admission formal state
- E. 必须改变 Gate semantics
- F. 必须改变 Admission semantics
- G. 必须建立新的 Authority
- H. 无法确定历史 Owner Decision
- I. 发现现有架构存在两套不可兼容的正式入口
- J. 需要自行解释 Contract 未定义的语义

STOP 后不得「先实现再说」。

---

## 6. Forbidden Scope（本授权明确禁止）

- Phase 1 preprocessing implementation（在 OD-01 re-freeze 前）
- P04 production implementation（Resolved Span 部分）
- P07 production implementation
- V3 production code modification
- Gate modification
- Admission modification
- DB migration
- V3 Frozen Schema modification
- historical corpus rerun
- historical data migration
- X3 entry
- changing P01–P25
- reopening P04/P07/P08/P15–P19
- introducing new Question Type / Unit Type
- creating `Standalone Question`
- silently resolving Frozen Spec conflicts
- using implementation to override Owner Decisions
- using Contract to override Frozen Spec
- N-values / Value / OrderedValue model（含 value-level evidence binding）—— D-07/D-08 已裁 (3) 禁止再引入

### 6.1 Scope clarification（2026-09-29，不扩大授权）

§6 的 **modification** 指 **语义 / 架构 / Frozen 边界** 变更；**不含**在既定语义内的 bug fix、异常处理、回归/对抗测试补强与 hardening。后者属下表 A 栏（Owner 2026-09-29 确认）。本澄清**不**放宽 STOP Conditions，**不**允许 Gate/Admission/Frozen Schema **语义**变更。

---

## 6A. Implementation Boundary Matrix（2026-09-29 Owner 落界）

> 性质：在**既有**授权内钉死边界，非重新设计 V3、非新 Decision 文件。
> 前置：D-07/D-08 = DECIDED (3)（多空题 `sub_questions`；N-values NOT IMPLEMENTED）；OD-002 = C WORKING REFERENCE。

### A. 当前明确授权（可执行）

| 范围 | 状态 | 说明 |
|---|---|---|
| EB-008 P1 后续实现修复 | ✅ AUTHORIZED | 已接受范围内的实现修正（含 A1 同类时间/异常边界） |
| 现有 Segment A 完善 | ✅ AUTHORIZED | **不**改 Frozen Schema 语义 |
| 测试补强 | ✅ AUTHORIZED | regression / adversarial |
| 代码质量修复 | ✅ AUTHORIZED | bug fix、异常处理、边界修复 |
| 现有 IR → Compiler → Admission 链优化 | ✅ AUTHORIZED | **保持**既定语义（含 OD-R-01/D-07/D-08 已裁读法） |

### B. 等待 Owner / D2/D3/D4（不得提前实现）

| 项目 | 状态 | 原因 |
|---|---|---|
| Authority assignment | ⏸ WAITING | OD-002 赋权 DEFERRED |
| Design v1.1 正式 authority 化 | ⏸ WAITING | 仅 WORKING REFERENCE |
| D2/D3/D4 对应实现扩展 | ⏸ WAITING | 需 authority 输入（OD-003 OPEN） |
| 代表性冲突规则扩展 | ⏸ WAITING | 避免实现未裁语义 |

### C. 明确禁止（当前）

| 禁止项 | 依据 |
|---|---|
| N-values / Value / OrderedValue / value-level evidence | D-07/D-08 = (3) |
| 修改 Frozen Spec / Frozen Schema / Frozen Contract | Authority Order |
| Gate / Admission **语义**变更 | §6 + STOP E/F |
| Migration / 数据迁移 / Gate 9 / approval_block 变更 | Migration Authorization = NOT AUTHORIZED |
| 为 R-5 加 signer / gate_run_id / event provenance | R-5 ACCEPTED；会重开 Authority 模型 |

### D. 阶段目标（硬）

```text
P0  EB-008 findings closure → regression stability → implementation confidence
P1  Segment A hardening + OD-R-01 representation consistency（按 (3)）+ Compiler/Admission edge cases
P2  等 OD-002 赋权 + OD-003 D2/D3/D4 之后再扩段
```

**不在本矩阵内**：新治理文档、历史报告清扫、批量改名、Migration Gate 启动。

---

## 7. Git / Commit Discipline

每个逻辑阶段形成可审计 commit。禁止：大量无关重构；顺手全项目格式化；无关 bug fix；删除历史 evidence；修改 Frozen Spec；修改 Frozen Contract；修改历史 corpus；migration；生产数据库直接 mutation。

每个 commit 必须能回答：**这个 commit 实现了哪个 Frozen Contract / Owner Decision 条款？**

---

## 8. Phase Evidence Requirement

每个 Phase 必须报告：

1. 实际修改的文件
2. 修改前后的 commit
3. 实际测试命令
4. 测试结果
5. 实际行为
6. 与 Frozen Contract / Owner Decision 的对应条款
7. 是否触及 Schema
8. 是否触及 Frozen Spec
9. 是否产生 Owner Decision
10. Exit Criteria 是否满足

禁止：「应该可以」「理论上没问题」「预计通过」「代码看起来正确」。

---

## 9. Final Authorization Summary

```text
Contract v0.3:
FROZEN
(Frozen Semantic Baseline = b743c5d)

Implementation Plan:
OWNER APPROVED

Implementation:
AUTHORIZED — LIMITED SCOPE

Historical Source Rerun:
AUTHORIZED IN PRINCIPLE
EXECUTE AFTER IMPLEMENTATION VERIFICATION

Enrichment:
AUTHORIZED IN PRINCIPLE
Schema Gap → STOP

Frozen Spec:
UNCHANGED w.r.t. OD-01 Option Provenance (that change is PROPOSAL only until re-freeze)
【scope clarification，2026-09-24】本行**只**限定 OD-01 Option Provenance 那条 change 的
状态，**不是**「当前 `Docs/V3_SPEC` tree 全局 UNCHANGED」的断言。全局 Frozen Spec tree
现状与 re-freeze 链见 `G-02-FREEZE-REGISTRATION-VERIFICATION.md` §6。

Frozen Contract:
UNCHANGED

Schema:
NO SELF-AUTHORIZED CHANGE
(Producer-side Artifact Schema extensible within Contract — OD-05)

Gate / Admission Semantics:
NO SELF-AUTHORIZED CHANGE

Question Core / Metadata Boundary:
FROZEN

Canonical Vocabulary:
FROZEN

"Standalone Question":
FORBIDDEN AS CURRENT V3 CONCEPT

Migration:
NOT AUTHORIZED

X3:
NOT ENTERED

Owner Decision:
REQUIRED WHEN A STOP CONDITION IS HIT
```

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md` |
| Status | OWNER APPROVED |
| Authority | LIMITED IMPLEMENTATION AUTHORIZATION |
| Owner Decision Record | `OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md` |
| Plan | `IMPLEMENTATION-PLAN-v0.3.md` |
