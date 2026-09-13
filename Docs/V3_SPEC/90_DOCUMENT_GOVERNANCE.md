# 90 — Document Governance：规范管理规范（元规范）

**Document Type**: Governance Meta-Spec
**Authority Level**: **L0-META**（治理元规范；**不属**业务 Frozen Spec 00–50）
**Status**: ACTIVE
**Normative**: YES（对**文档治理流程**规范；**不定义任何业务语义**）
**Supersedes**: `82 §1`（Authority Matrix）/ `82 §2`（CHANGE 分类）/ `82 §9`（Status Header）/ `82 §11`（读取顺序）——见 §8
**Superseded By**: —
**Gate State Authority**: NO（Gate 状态权威仍是 **82 §3**）

**Date**: 2026-09-13
**性质**：本文档**不是业务 Spec**。它规定「规范如何被管理」，不含任何
annotation / resolver / gate / admission 的业务语义。

---

## 0. 为什么需要元规范

V3 的优势是**先冻结约束，再允许实现**。但演进中出现了一个新风险：

```text
Frozen Spec → Decision Record 解释 Spec → Closure Report 再解释 Decision Record
           → 代码依据最新解释演进
```

这就是 **Architecture Drift**。82 号已意识到并建立 Authority Matrix，方向正确；
本文档把该模型提升为**元规范**，并把82 降为治理执行记录（§8）。

**最高原则**：

> **L3 / L4 / L5 永远不能改变 L0 / L1。**
> **L2 只能解释与裁决，不能修改 L0。**

---

## 1. 文档等级（L0–L5）

| Level | 文档类型 | 例子 | 权限 | 禁止 |
|---|---|---|---|---|
| **L0** | **Frozen Spec** | `00` `10` `20` `30` `40` `50` | **定义系统事实**。唯一 Schema Source of Truth = `20` | 不得被 L2–L5 隐式修改 |
| **L1** | **Contract Change Record** | 暂无（`67` 是候选，**NOT RELEASED**） | **修改 L0 的唯一入口** | 未走完流程不得生效 |
| **L2** | **Architecture Decision Record** | `69` `70` `75` `80` `81` `82` `90`、Closure 记录 | 对具体问题**解释与裁决** | **不得产生新的架构事实**；超出裁决范围即失效 |
| **L3** | **Gate Report** | `74` `80` §状态块 `81` §9 `83` §4 | **证明状态**，须引 L0/L1/L2 | **不得定义规则**；Gate 状态只能**引用** 82 §3 |
| **L4** | **Experiment Report** | `60`–`66` `68` `71`–`73` `76`–`79`、I-5-1 | **提供证据** | **不得单独支撑 PASS / CLOSED**；不得把实验结论升为架构事实 |
| **L5** | **Status / log / restart** | `Status.md` `log.md` `restart-prompt.md` `bugs.md` | 项目管理与索引 | 不得与 82 §3 矛盾；矛盾即该文档 stale |

**未归层 = 不得引用为权威。** 见 `docs_audit/authority_matrix.yaml`（机器可读全表）。

### 1.1 与旧 A–E 五层的对应

| 旧（82 §1.2） | 新（本文档） | 变化 |
|---|---|---|
| A Frozen Spec | **L0** | 不变 |
| — | **L1 Contract Change Record** | **新增成层**——修改 L0 的唯一门 |
| B Decision Record | **L2** | 不变 |
| C Phase Report | **L3 + L4** | **拆分**——Gate 报告与实验报告权限不同 |
| D Status | **L5** | 不变 |
| E Experimental | 并入 **L4** | 不再单列 |

---

## 2. 核心规则（冻结）

### R1 — L0 只能经 L1 修改

任何 L2–L5 文档**不得**改写、扩充、或「事实上修订」L0 语义。
新增强制 invariant 同样需要 L1（见 §3 CHANGE-2）。

### R2 — L2 不得产生新的架构事实

L2 只能**解释** L0 已有事实，或**裁决** L0 未覆盖的具体问题。
若 L2 的裁决要成为系统事实，必须走 L1。

> **错误**：`81 §5.1：line_refs 永远在 manifest`（20 未定义 → 这是提案，不是事实）
> **正确**：`81 §5.1：建议 manifest-only，待 Binding Authority Decision`（82 §5 已如此标注）

### R3 — L3 只能证明状态，且必须引用权威

L3 报告 Gate 状态时**必须**写成：

> Gate X：状态（依据 **82 §3**，日期）

**禁止**只写「Gate X CLOSED」而不带范围限定与依据。
**禁止**在 L3 中定义新的 Gate 通过条件。

### R4 — L4 只能提供证据，不得升格为结论

```text
Experimental PASS  ≠  Contract PASS  ≠  Gate PASS  ≠  Production Ready
```

例：`B2-A PASS` 只表示**该实验成立**，不得推出 `Gate B PASS`。
I-5-1 的「21/21 ready IR」是 **Historical / Directional**，**不可复现**
（无脚本、无测试、git 历史零提交），不得作为任何 PASS 依据。

### R5 — L5 不得与 82 §3 矛盾

矛盾即该 L5 文档 stale，以 82 §3 为准。
**每次 Gate 状态变更必须在同一 commit 内更新 82 §3。**

### R6 — 术语必须有冻结定义

被 ≥2 份文档使用的架构术语，**必须**在 L0 或 L2 中有定义。
定义形态不限于散文——**表格、状态机图、JSON schema、禁止字段清单同样算定义**
（检测器须识别，见 §5 Rule 3）。
使用未定义术语立规 = 违规。

### R7 — 引用闭包规则

> **任何 L2/L3/L4 文档中的规范性结论，必须存在向上的引用闭包。**

即：该结论必须能追溯到 L0/L1，或追溯到另一份已具备闭包的 L2 裁决。

```text
合法：
  81 §5.6「Adapter 不得解析文本」
      ↑ 引用 69 §Gate D 五条禁令 + 66 §7 明令

非法：
  81 §5.6「Adapter 不得解析文本」
      （无来源，自行定义）
```

**否则**会出现「这条规则不是 Spec 写的吗？但大家都这么认为」——规范性结论
失去可追溯来源，等同于 L2 偷偷产生新架构事实。

### R8 — 废止传播规则

`supersede` 不等于删除，但**废止必须可传播**：

若 `X supersedes Y §Z`，则 `Y §Z`：

1. **保留正文**（历史审计证据，不得改写或删除）
2. **不得作为引用来源**——新文档引用 `Y §Z` 即违规
3. **不得进入新文档的引用搜索结果**——扫描器须跳过已废止段落
4. **`docs_audit/` 须标记 `deprecated`**

**否则**历史文档仍会污染未来决策——A-01（`74` 的 Gate C BLOCKED）正是此类。

### R9 — Evidence 相关术语不可互换（永久规则）

> **`Validated Evidence` ≠ `verified_correct`。二者永不可互换或互相推导。**

| 术语 | 定义处 | 含义 | 层 |
|---|---|---|---|
| `Source Fragment` | L2 `75 §二` 状态机 `state: immutable` | 源切片本体 | 证据生命周期 |
| `Evidence Proposal` | L2 `75 §二` `state: untrusted` | 提议，未声明 | 证据生命周期 |
| `Evidence Claim` | L2 `75 §二` `state: awaiting validation` | 已声明，待验证 | 证据生命周期 |
| **`Validated Evidence`** | L2 `75 §二` `state: trusted`；`75 §4.5`「唯一可进入 IR」 | **已验证、可进 IR** | 证据生命周期 |
| `INVALIDATED` | L2 `75 §二` `state: terminal` | 撤销终态 | 证据生命周期 |
| **`verified_correct`** | **L0 `20 §8.3`** | **答案内容与权威答案/人工确认一致** | **Admission 结果** |

**`Verified Evidence` 全仓零使用，永久禁用**——它会与 `verified_correct` 产生
强语义关联，制造「已验证 = 答案正确」的误读。

**命名规范**：75 号的正式名称是 **`Evidence Promotion Contract`**。
其他文档使用的「Evidence Contract」是**未声明的简称**，须改为全称或显式等同
（见 `84 B-01`）。

### R10 — L2 不得创造新名词

> **L2 及以下文档不得引入新的架构术语，除非该术语已引用 L0 定义。**

未引用 L0 定义的新词，必须先进入 **Terminology Proposal** 流程并经裁决，
才能在文档与代码中使用。

**理由**：L2 数量已多（`80` `81` `82` `84` `90`…），未来开发者容易把
「81 Adapter Contract / 90 Meta Spec / 80 Gate Closure」一并当作 Frozen Spec。
术语是架构事实的载体——L2 若能自由造词，就等于能产生新的架构事实，违反 R2。

| 术语 | 状态 |
|---|---|
| `Evidence Promotion Contract` | ✅ 已有定义（L2 `75`） |
| `Validated Evidence` | ✅ 已有定义（L2 `75 §二` 状态机） |
| **`Binding Carrier`** | ⚠️ **未定义**，已登记为 PENDING（`82 §5`）——进入代码前须先定义 |
| **`External Claim`** | ⚠️ **未定义**（BIND-3 用语）——同上 |
| **`Semantic Authority`** | ⚠️ **未定义**（BIND-3 用语）——同上 |

---

## 11. Change Audit Record（L0 修改审计）

**任何对 L0 的修改，无论发生在 90 生效前或后，都必须在本节登记。**

| ID | 文件 | 提交 | 时间 | 修改内容 | 分类 | Decision |
|---|---|---|---|---|---|---|
| **CA-001** | `40_Development_Rules.md` §5 | `0dd954d` | 2026-09-13 14:43 | 新增一条**强制**规则：「测量语义必须复刻真实 pipeline…**禁止**用近似文本代替…度量脚本必须能指出它复刻哪一段 pipeline，并有测试锁死该复刻语义」 | **CHANGE-2 Normative Addition** | **PENDING** |

### CA-001 详情

**Before**（`40 §5` 原文）：无此条。

**After**（`0dd954d` 引入）：

> - **测量语义必须复刻真实 pipeline（2026-09-13 教训，BUG-V3-044 对抗性审查）**：
>   覆盖率 / 回归 / 通过率等**度量实验**的输入，必须是上游组件的**真实输出切片**，
>   禁止用近似文本代替。反例：测 grammar 覆盖率时用「行内全部剩余文本」，而真实
>   pipeline 走的是 E 的 char-span 切片（本题号起点 → 下一题号起点，20 §5.5）——
>   两者不是同一个问题，会同时高估回归与低估收益，据此得出的裁决全部作废。
>   度量脚本必须能指出它复刻的是哪一段 pipeline，并有测试锁死该复刻语义。

**为什么归 CHANGE-2**：使用「必须 / 禁止 / 必须能指出」，**新增了此前 40 §5
未规定的强制约束**。它不是 typo 修正（CHANGE-0）、不是同义改写（CHANGE-1）、
也没有放宽或删除任何既有约束（CHANGE-4/5）。按 90 §3 判定规则「拿不准往高里归」，
归 **CHANGE-2**。

**为什么不是 CHANGE-1 Clarification**：CHANGE-1 要求**规范语义零变化**。这条
新增了「度量脚本必须指出复刻哪一段 pipeline」与「须有测试锁死该复刻语义」两项
此前不存在的可验证要求——语义有变化。

**时序说明（缓解因素，非豁免）**：该修改发生在 90 生效**之前**（`0dd954d` 14:43；
90 建于 `c5a899f`），当时 CHANGE-0…5 分类尚未建立。但 `82 §2` 的分类与
「先冻结 Spec 再改代码」的项目原则均已存在。**时序不构成豁免**——本节的作用
正是把这类事后发现的 L0 修改拉回审计视野。

**内容本身的正当性**：规则源自真实教训——BUG-V3-044 轮次的覆盖率测量曾用
「行内剩余文本」代替 E 的 char-span 切片，导致同时高估回归与低估收益，
据此得出的裁决全部作废。**内容可辩护，但缺少 Change Record 是事实。**

**可选处置（待裁决，本节不自行决定）**：

| 选项 | 内容 | 代价 |
|---|---|---|
| **(a) 追认** | 补一份 Change Record，追认 CA-001 生效 | 承认流程违规但保留正确规则 |
| **(b) 撤回重走** | 回滚 `40` 该条，经 L1 正式流程重新加入 | 流程干净，但产生一次无谓回滚 |
| **(c) 挂起** | 标记 `PENDING RATIFICATION`，在下次 L0 修订时一并处理 | 规则暂处灰色地带 |

### 审计范围声明

本节**已审计** `0dd954d` 之后所有触及 L0 的提交。更早的 L0 修改（`10`/`20` 于
09-08/09-09，`30`/`50` 于 09-08）在提交信息中已自带 `errata` /
`Scope Freeze errata` / `spec-only, A-Guarded` 标记，属 90 之前的既有变更惯例，
不在本轮审计范围。

**90 生效后，任何 L0 修改若不在本节登记，即为违规。**

---

## 3. 规范变更分类（CHANGE-0…5，吸收自 82 §2）

**Errata 不应只处理「放宽」。新增强制 invariant 同样是正式变更。**

| 类别 | 定义 | 需要什么 |
|---|---|---|
| **CHANGE-0 Editorial** | typo、编号、格式 | 轻量修订记录 |
| **CHANGE-1 Clarification** | 措辞澄清，**规范语义零变化** | Change Record（简） |
| **CHANGE-2 Normative Addition** | **新增**此前未规定的强制约束 | **Change Record + 评审**；**不必**走四道门 |
| **CHANGE-3 Normative Modification** | 改变既有规定的行为 | Change Record + 受影响层回归 |
| **CHANGE-4 Constraint Relaxation** | **放宽**既有约束 | **四道门 + Change Record** |
| **CHANGE-5 Constraint Removal** | **删除**既有约束 | **四道门 + Change Record** |

**判定规则：拿不准往高里归。** 归高了只是多走流程；归低了就是绕过治理。

**四道门（69 §5）仅适用 CHANGE-4 / CHANGE-5**——它为守住「放宽安全边界」而设。

| 候选 | 分类 | 状态 |
|---|---|---|
| `67`（删 `20:117` FORBIDDEN_FIELDS 的 `line_refs`） | **CHANGE-5** | **NOT RELEASED**（Gate B NOT CLOSED） |
| `E1`（Grammar `answer_text` 来源不变量 → `20 §8.4`） | **CHANGE-2** | PENDING（`20 §8.4` **沉默**，非写错） |
| `E2`（Adapter 边界 → `20 §3`） | CHANGE-3 | DEFERRED |
| `63` 若升 L0 | CHANGE-2/3 | 待裁决（自称 `Frozen Constraint` ≠ 已是 L0） |

---

## 4. Status Header 规范（强制）

**每份新文档必须以如下块开头**，使 Agent 无需猜测权威层级：

```text
Document Type:  <Frozen Spec | Contract Change Record | Decision Record |
                 Governance Meta-Spec | Gate Report | Experiment Report | Status>
Authority Level: <L0 | L1 | L2 | L3 | L4 | L5 | L0-META>
Status:         <ACTIVE | SUPERSEDED | HISTORICAL | DRAFT | CLOSED | NOT RELEASED>
Normative:      <YES | NO>
Supersedes:     <doc list 或 —>
Superseded By:  <doc 或 —>
Gate State Authority: <YES | NO>   # 现行唯一 YES = 82 §3
```

**存量文档不强制回填**（Reconcile, don't rewrite）；下次实质性修订时补上。

---

## 5. 冲突扫描规则（机械，不人工读全仓）

扫描产物落在 `docs_audit/`（机器可读）+ `84_CONFLICT_LEDGER.md`（人工裁决台账）。

### Rule 1 — Gate 状态冲突

搜索：`PASS` `CLOSED` `BLOCKED` `WAIT` `DEFERRED` `NEXT` `CONDITIONAL`
建立：`Gate × 文档 × 状态 × 权威级别` 矩阵 → 人工裁决。
**聚合规则（冻结）**：存在 CONDITIONAL 或 DEFERRED 子项时，父 Gate **不得**记 PASS/CLOSED。

### Rule 2 — 禁止词升级（L3/L4/L5）

下列词在 L3/L4/L5 中出现且**未引用 L0/L1** 即违规：

`guarantee` `solved` `authority` `must` `shall` `forbidden` `必须` `不得` `冻结`

> **细化**：`CLOSED` / `PASS` **不整体禁止**——L3 本职就是报告状态。规则是
> **必须引用 82 §3**，而非禁用词本身。

**正确用法**（L4 限定主张范围，**不违规**）：

> 「这个结果**只能**证明…」「**本实验采用**…」「**根据 20 §X**…」

### Rule 3 — Boundary 冲突

重点扫描这些边界词，建立「谁定义 / 谁生产 / 谁消费」关系图：

`Resolver` `Adapter` `Annotation` `Manifest` `line_refs` `Evidence`
`Source` `Authority` `IR` `Compiler` `Gate` `ResolvedSpan` `ResolvedRun`
`answer_text` `STRICT_AUTO_TYPES` `FORBIDDEN_FIELDS`

同一词在不同文档出现**对立极性**规定（既「必须 X」又「不得 X」）→ 进台账。

### Rule 4 — Ownership Matrix（必须可回答）

| 数据 | 唯一生产者 | 消费者 | 权威定义处 |
|---|---|---|---|
| SourceFragment / SourceLine | Seal（L0 `10 §4`） | Resolver / Adapter | L0 |
| Semantic Unit | Annotation | IRBuilder | L0 `20 §4` |
| `ResolvedSpan` | Resolver（Native）**或** Adapter（Path B） | IRBuilder / Compiler / Gate | L0 `20 §5.5` |
| `line_refs` | **PENDING**（BIND-1/2/3，`82 §5`） | Evidence Authority | **未冻结** |
| answer token | Grammar | Gate Policy | L0 `20 §8.4` |

**指不出唯一生产者的字段 = 治理缺口**，进台账。

---

## 6. 高风险点（长期禁止）

### H-A — Evidence Authority 范围

`Evidence Validity ≠ Semantic Correctness` 是**冻结方向**。长期禁止把

```text
ValidatedEvidence → IR → Admission
```

误写成 `ValidatedEvidence = correct answer`。

> 现状风险：`Validated Evidence` 在 L3 `74` 中使用 10 次，**L0/L2 零定义**；
> `Verified Evidence` 全仓零使用；L0 `20 §8.3` 用的是 `verified_correct`。
> **三个近义词、只有一个有宪法地位**——已入 `84` 台账。

### H-B — Adapter / Manifest 权威（BIND-1）

Annotation（semantic）与 Manifest（binding）分层**方向正确**，但必须证明：

```text
semantic_unit.id  ←确定性 join→  manifest.binding.unit_id
```

**不得依赖**顺序 / 题号 / fuzzy match / stem 相似度——否则 Adapter 重新成为
Resolver，违反 L2 `81 §5.6`。**BIND-1 未解决前，`Binding Carrier = PENDING`。**

### H-C — 双轨一致性

```text
Native Path : Source → Resolver → ResolvedRun
Path B      : Source → preprocessing → Adapter → ResolvedRun
```

`ResolvedRun` **必须是唯一消费入口**。不得出现

```text
Native 下游消费 ResolvedRun  /  Adapter 下游消费 annotation_payload
```

两个世界。下游 IRBuilder / Compiler / Gate / Admission 对两条路径**完全一致**。

---

## 7. Agent 读取顺序（强制）

为防上下文污染——把旧结论、新结论、实验结论与用户最新要求「综合理解」后
自行创造一个不存在的 Contract——强制顺序：

```text
1. 90 号（本文档：治理规则）
2. 82 §3（Gate State Authority）+ 82 §10（Phase Baseline）
3. L0 Frozen Spec 00–50
4. 相关 L1 / L2 Decision Record
5. L3 Gate Report
6. L4 Experiment Report
7. L5 Status / 历史文档
```

**禁止「grep 到什么读什么」。**

---

## 8. 与 82 / 83 / 84 的关系

| 文档 | 定位（90 生效后） |
|---|---|
| **90（本文档）** | **治理元规范**。定义 L0–L5、核心规则、CHANGE 分类、扫描规则、读取顺序 |
| **82** | **治理执行记录**。保留 **§3 Gate State Authority（唯一）** + §4 Conflict Register + §5 BIND-1/2/3 + §10 Phase Baseline。§1/§2/§9/§11 **被 90 吸收** |
| **83** | L4 全仓形式扫描结果（G1–G6） |
| **84** | **Conflict Ledger**——全部争议点 / 交叉约束 / 潜在冲突的裁决台账 |
| `docs_audit/` | 机器可读扫描产物（`authority_matrix.yaml` / `contradiction_candidates.json` / `frozen_terms.json` / `scan_report.md`） |

**L3/L4/L5 永远不得改变 L0/L1；L2 不得修改 L0。** 本规则对 82/83/84 同样适用。

---

## 9. 显式不主张

1. **不主张**本文档可修改任何 L0 业务语义——它是元规范，不含业务事实。
2. **不主张** L0–L5 已覆盖全部现存文档——未归层者见 `docs_audit/authority_matrix.yaml`。
3. **不主张** `84` 台账中任何条目已裁决——全部 OPEN，待人工裁决。
4. **不主张**扫描穷尽了所有治理问题——只覆盖 §5 四条规则的机械可查部分。
5. **不主张** 82 的 Gate State Authority 被削弱——**82 §3 仍是唯一权威**。

---

## 10. 完成条件（Documentation Governance Pass）

1. ✅ L0–L5 元规范建立（本文档 §1）
2. ✅ 核心规则 R1–R6 冻结（§2）
3. ✅ CHANGE-0…5 分类（§3）
4. ✅ Status Header 规范（§4）
5. ✅ 扫描规则 Rule 1–4（§5）
6. 🟠 `docs_audit/` 四件产物生成并复核
7. 🟠 `84` 台账全部条目状态非空（OPEN / DECIDED / SUPERSEDED / INCORPORATED）
8. 🟠 全部现存文档归层完成（无 UNCATEGORISED）
9. 🟠 82 §1/§2/§9/§11 的吸收改写完成
10. 🔴 全仓无未登记的 normative contradiction

**10 项全绿前不得进入 Binding Authority Decision。**
