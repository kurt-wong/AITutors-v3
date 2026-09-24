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

### 1.2 目录模型（DG-2 归位，2026-09-13 冻结）

**物理目录强制分层。** 层级不再只存在于 `authority_matrix.yaml` 里。

```text
AITutors-v3/
├── Docs/
│   ├── V3_SPEC/          L0 Frozen Spec + L0-META（90/91）—— 唯一冻结规范
│   ├── DECISIONS/        L2 Decision Records
│   ├── REPORTS/          L3/L4 Gate & Experiment Reports + Closure records
│   └── ARCHIVE/          SUPERSEDED / stale，保留为审计证据（不得引用）
├── Status.md             L5 — 当前项目状态快照
├── log.md                L5 — 时间线事件记录
├── bugs.md               L5 — 已确认问题列表
└── restart-prompt.md     L5 — Agent 恢复上下文入口
```

| 目录 | 层 | 允许 | 禁止 |
|---|---|---|---|
| `Docs/V3_SPEC/` | L0 / L0-META | 引用；补 Change Record；新增 L1 | 直接编辑；隐式改变 |
| `Docs/DECISIONS/` | L2 | 解释与裁决 | 产生新架构事实；修改 L0 |
| `Docs/REPORTS/` | L3 / L4 / L2-proposed | 证明状态；提供证据 | 定义规则；单独支撑 PASS |
| `Docs/ARCHIVE/` | deprecated | 审计证据 | **作为引用来源** |

**例外（冻结）**：4 个 JSON 测试语料（`gate_c_invalid_binding_corpus.json`、
`gate_b2b{3,4,5}_frozen_testset.json`）**留在 `backend/Docs/V3_SPEC/`**——
测试按路径读取（`backend/tests/test_b2b5_d_projection_safety.py:354`、
`test_c2_evidence_authority_e2e.py:54`），移动会打断测试。

**L0 文件名永久保持现状。** 改 L0 文件名本身是 CHANGE，须走 L1；且会打断全部
`file:line` 引用坐标。分层靠本节目录 + `authority_matrix.yaml` 表达。

### 1.3 根目录四份状态文件的职责（冻结）

| 文件 | 唯一职责 | 允许 | 禁止 |
|---|---|---|---|
| **`Status.md`** | **当前项目状态快照** | 当前阶段 / Gate 状态 / OPEN 问题 / 下一步 | 技术分析、长篇原因解释、设计决策 |
| **`log.md`** | **时间线事件记录**（类 git commit） | `日期 / Action / Decision / Reference` | 重新解释设计 |
| **`bugs.md`** | **已确认问题列表** | ID / Title / Impact / Status | 解决方案讨论 |
| **`restart-prompt.md`** | **Agent 恢复上下文入口** | 当前项目是什么 / 哪些文件权威 / 做到哪 / 下一步 | 保存历史讨论 |

**这四份是 L5，永远不得改变 L0/L1（`90 §2` 最高规则）。**

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
| **CA-001** | `40_Development_Rules.md` §5 | `0dd954d` | 2026-09-13 14:43 | 新增一条**强制**规则：「测量语义必须复刻真实 pipeline…**禁止**用近似文本代替…度量脚本必须能指出它复刻哪一段 pipeline，并有测试锁死该复刻语义」 | **CHANGE-2 Normative Addition** | **CLOSED — (b) ratified via CR-001** |
| **CA-003** | `10_Data_Model.md` §6.3 · `20_Document_Pipeline.md` §5.3 | `71f51f9` | 2026-09-24 | **OD-R-01 已批准业务语义的 Frozen Spec incorporation**（**不是**新的业务 Decision）：`10 §6.3` 新增「Answer 业务对象边界」条款（1 QuestionInstance → 1 Answer → N ordered values，禁止拆成多份 Answer）；`20 §5.3` blank 映射目标由 `sub_question/answer` 收窄为 `sub_question` 或「同一份 Answer 的一个有序值」 | `20 §5.3` = **CHANGE-3 Normative Modification**；`10 §6.3` = **CHANGE-2 Normative Addition**；主导 **CHANGE-3** | **CLOSED — ratified via CR-003** |
| **CA-004** | `20_Document_Pipeline.md` §4.5 / §6.1 | `f708370` | 2026-09-21（登记 2026-09-24） | question/unit canonical vocabulary correction：`unit_type` 规定值 `standalone_question` → `standalone_unit`（§4.5 / §6.1 各 2 处，含小节标题）+ `§4.5` 新增注（legacy 词汇定性 / canonical 断言 / **禁** `standalone_question`·`composite_question` 作 canonical / Question Type 与 Unit Type 正交**不得混用**）。**Frozen Spec change ≠ backend implementation change ≠ test evidence**（分列见 CA-004 详情 4.A/4.B/4.C） | **CHANGE-3 — Normative Modification**（含 CHANGE-2 新增禁令分量；不归 CHANGE-1） | **CLOSED — ratified via CR-004** |

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

**可选处置（已裁决，见下方 CR-001）**：

| 选项 | 内容 | 代价 |
|---|---|---|
| ~~(a) 追认~~ | 补一份 Change Record，追认 CA-001 生效 | 未采纳 |
| **(b) 追认 CHANGE-2 + 补建 Change Record** | **保留 `40 §5` 现有文本，不回滚、不改 L0 内容** | **已采纳** |
| ~~(c) 挂起~~ | 标记 `PENDING RATIFICATION` | 未采纳 |

### CR-001 — Change Record（CHANGE-2 Normative Addition）

> **本记录是 `40 §5` 测量语义规则的正式 Change Record。**
> 按 `90 §3`，CHANGE-2 需 Change Record + 评审，**不需四道门**。

```text
Change Record ID : CR-001
Target           : L0 Docs/V3_SPEC/40_Development_Rules.md §5
Change Class     : CHANGE-2 — Normative Addition
Source Commit    : 0dd954d（2026-09-13 14:43）
Audit ID         : CA-001
Date             : 2026-09-13
```

**变更内容**（`40 §5` 新增一条）：

> - **测量语义必须复刻真实 pipeline（2026-09-13 教训，BUG-V3-044 对抗性审查）**：
>   覆盖率 / 回归 / 通过率等**度量实验**的输入，必须是上游组件的**真实输出切片**，
>   禁止用近似文本代替。反例：测 grammar 覆盖率时用「行内全部剩余文本」，而真实
>   pipeline 走的是 E 的 char-span 切片（本题号起点 → 下一题号起点，20 §5.5）——
>   两者不是同一个问题，会同时高估回归与低估收益，据此得出的裁决全部作废。
>   度量脚本必须能指出它复刻的是哪一段 pipeline，并有测试锁死该复刻语义。

**变更前**：`40 §5` 无此条。

**分类依据**：新增「指出复刻哪一段 pipeline」与「有测试锁死该复刻语义」两项
此前不存在的可验证要求 → 规范语义有变化 → **不是** CHANGE-1 Clarification。
按 `90 §3` 判定规则「拿不准往高里归」，归 CHANGE-2。

**正当性**：源自真实教训——BUG-V3-044 轮次的覆盖率测量曾用「行内剩余文本」
代替 E 的 char-span 切片，同时高估回归与低估收益，据此得出的裁决全部作废。
规则符合 V3 的证据哲学（测量必须复刻真实 pipeline 的数据语义）。

**流程缺陷（已确认）**：先改了 L0，后补治理手续。属 **procedural gap**，
非内容错误。

**Owner Decision（2026-09-13）**：

| 项 | 裁决 |
|---|---|
| `40 §5` 新增规则 | **保留** |
| CHANGE 类型 | **CHANGE-2 — Normative Addition** |
| 现状 | **未按流程生效 / procedural gap** |
| 补救 | **创建本 Change Record** |
| 四道门 | **不需要**（CHANGE-2 不属放宽/删除） |
| 修改 90 | **不需要** |
| 修改 Frozen Spec 内容 | **不需要** |
| 回滚 40 | **不回滚** |

**Review（2026-09-13，项目负责人）**：**ACCEPTED / EFFECTIVE**。

> 理由：规则本身正确且必要；为流程洁癖把正确规则撤掉再重加一遍没有意义。
> 正确做法是补齐 provenance：`40 §5 新增 → CA-001 → CR-001 → Review → Accepted`。

**生效后的治理效力**：`40 §5` 该条**自本记录 Accepted 起**具有完整 L0 效力。
在此之前「文本已存在 ≠ CHANGE-2 已完成生效」——这一区分用于避免倒置治理顺序。

**登记义务**：`90 §11` 自此对任何 L0 修改强制生效。**90 生效后的 L0 修改若
不在此登记，即为违规。**

### CA-003 — 详情（OD-R-01 Answer 业务对象边界）

**性质（先读）**：`71f51f9` 的两处 L0 修改**不是新的业务 Decision**；它们是
**OD-R-01 已批准业务语义的 Frozen Spec incorporation**。本条**不是** Owner Decision，
**不定义**任何新业务语义、**不改变** `90`/`91` 治理原则。

```text
Audit ID           : CA-003
Target             : L0 Docs/V3_SPEC/10_Data_Model.md §6.3
                     L0 Docs/V3_SPEC/20_Document_Pipeline.md §5.3
Source Commit      : 71f51f9（2026-09-24）
Owner Decision     : OD-R-01（Answer business-object boundary，APPROVED 2026-09-24）
L1 Change Record   : CR-003 — Docs/V3_SPEC/CR-003_CONTRACT_CHANGE_RECORD_OD-R-01.md
Change Class       : 20 §5.3 = CHANGE-3 — Normative Modification
                     10 §6.3 = CHANGE-2 — Normative Addition
                     主导分类 = CHANGE-3（90 §3「拿不准往高里归」）
Date               : 2026-09-24
```

**变更内容**：见 `CR-003 §2`（before / after 最小语义描述）。

**分类依据**：`20 §5.3` 把既有规定「一个 blank → 一个 sub_question/answer」收窄为
「sub_question 或**同一份 Answer 的一个有序值**」⇒ **改变既有规定的行为**，如实归
CHANGE-3（**不**降级为 CHANGE-1——CHANGE-1 要求规范语义零变化）。`10 §6.3` 在此前
**未规定**处新增强制约束 ⇒ CHANGE-2（与 `CR-001` 同型）。四道门仅适用 CHANGE-4/5
⇒ **不需要**。

**受影响层回归**：以静态一致性回归执行（本任务禁 code / runtime tests），覆盖 L0 文本层
与引用该 baseline 的现行断言层；逐项结果见 `CR-003 §7`。

**流程缺陷（已确认）**：先改 L0（`71f51f9`），后补治理手续。属 **procedural gap**，
非内容错误（对齐 CA-001 同型定性）。

**Owner Decision（2026-09-24）**：两处 L0 修改 **保留，不回滚**；OD-R-01 业务语义
**APPROVED**；补救 = 创建 `CR-003` + 本条 CA-003 + `10 §12`/`20 §12` 变更记录 +
Frozen Spec re-freeze 登记 + 受影响现行断言最小一致性修复。

**Review（2026-09-24，Owner）**：**ACCEPTED / EFFECTIVE**。
生效区分：CR-003 Accepted 之前「L0 文本已存在 ≠ CHANGE 已完成生效」；自 Accepted 起
两处修改具有完整 L0 效力。

**Re-freeze reference**：

```text
Previous Frozen Spec tree（= 9f1763e:Docs/V3_SPEC）
  = b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f   【历史 baseline，保留不改】
Incorporation tree（= 71f51f9:Docs/V3_SPEC）
  = 442172f40942368a4856231a742bf4d273242034
Re-freeze Frozen Spec tree
  = git rev-parse <CA-003 生效 commit>:Docs/V3_SPEC
权威登记 = CR-003 §10（commit 锚定）；字面值副本 = G-02 §6（非权威）
```

**编号说明**：`CA-002`/`CR-002` 已被 `Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md`
占用（NOT RELEASED / NOT REGISTERED / 未归层，本表内无 `CA-002`），本条取 **CA-003** 避免碰撞。

### CA-004 — 详情（f708370 canonical Unit-Type vocabulary correction）

**性质（先读）**：本条为**既存** L0 修改 `f708370`（2026-09-21）补 provenance / audit，
**不是**新的业务 Decision，**不回滚**该修改，**不重新裁决** canonical vocabulary。
与 CA-003 / OD-R-01 **完全独立**（任务书 §15：不得把 f708370 并入 CR-003）。

```text
Audit ID           : CA-004
Target             : L0 Docs/V3_SPEC/20_Document_Pipeline.md §4.5 / §6.1
Source Commit      : f708370（2026-09-21T12:25:53+08:00；parent 13fdce08）
Owner authority    : L0 README §2.2 术语裁决（权威）· L0 10 §5.2:290 / §6.5:516 闭集 ·
                     IMPLEMENTATION-PLAN §0b:83 Terminology（mandatory）· OD-P09 / OD-P11 / OD-2
                     （命题「standalone_question / composite_question 不得作为 canonical V3
                     Unit Type」可被上述既有记录证明）
                     【UNKNOWN】具名 instrument「Owner D1」/「2026-09-20 Concept Correction」
                     在 Docs/ 内无同名正式记录；只记归属缺口，【不追认】新 Owner Decision
L1 Change Record   : CR-004 — Docs/V3_SPEC/CR-004_CONTRACT_CHANGE_RECORD_F708370-UNIT-VOCABULARY.md
Change Class       : CHANGE-3 — Normative Modification（主导；含 CHANGE-2 新增禁令分量）
                     依据 = 20 §4/§6 是 Semantic Unit / IR 形态的【唯一】规定处，其 unit_type
                     规定值改变 = 改变既有规定的行为；且新增注含新禁令 ⇒ 非 CHANGE-1
Date               : 事件 2026-09-21 · 登记 2026-09-24
```

**Before / After**：见 `CR-004 §3`（逐位置 before/after + blob SHA-1 实测）。

**四者分列（不得混为一个架构事实）**

```text
4.A  Frozen Spec change      = 20 §4.5 / §6.1 文字变化         → 计入 Change classification
4.B  implementation change   = backend/app/domains/compile/ir.py 2 行
                              （IRBuilder default / output）     → implementation consequence，不计入分类
4.C  test evidence           = test_m3_boundary_canonical_vocabulary.py（新增 150 行）
                              + test_x26_m1_acceptance_shapes.py（+17/-4）
                                                            → verification evidence，不是架构事实
4.D  本 Change Record        = provenance / classification / audit 登记
```

**受影响层回归**：本任务口径 **NOT VERIFIED**（未重跑实现层回归；任务书 §5 禁改 backend / 禁增测试 /
禁重跑 Phase 1）。f708370 时点的测试自述（Targeted 137 passed / Regression 197 passed）
按 **DOCUMENT CLAIM** 记录于 `CR-004 §6`，**不伪造**为本轮 regression evidence。

**Review / disposition（2026-09-24）**：**ACCEPTED / EFFECTIVE**；disposition = **registered**。
不回滚、不 reverse commit、不 rewrite history、不 force push。

**Re-freeze reference**（独立链，不并入 CA-003）：

```text
pre-f708370 tree（13fdce08:Docs/V3_SPEC）= fa1e953e7c4638236b298cf1c137aa2a107d5ea5
f708370 incorporation tree               = b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f
                                          （同值说明：亦即 OD-R-01 所称 previous / pre-OD-R-01 tree）
current / new tree = git rev-parse <CA-004 生效 commit>:Docs/V3_SPEC
权威登记 = CR-004 §8；字面值副本 = G-02 §6.2
```

### 审计范围声明（2026-09-24 重写为可验证枚举）

> **原表述已撤回**：本节原写「本节**已审计** `0dd954d` 之后所有触及 L0 的提交」。该完备性主张在
> `f708370` 漏出后**不成立**，现**撤回**，改为**逐笔枚举 + 逐笔处置**。本节**不再使用**
> 「所有都已审计」这类不可验证的完备性断言。

**枚举口径**：`git log -- Docs/V3_SPEC/{00,10,20,30,40,50}*.md`（L0 = Frozen Spec 00–50）。
**处置取值仅三种**：`registered` / `historical-exempt` / `Owner-disposed`。**不存在第四种**
`unknown but claim complete`。

#### (a) `0dd954d` 及其后触及 L0 的提交 —— 完整枚举，5 笔

| commit | target | date | disposition | provenance |
|---|---|---|---|---|
| `0dd954d` | `40 §5` | 2026-09-13 | **registered** | CA-001 → CR-001（CHANGE-2，ACCEPTED / EFFECTIVE） |
| `f708370` | `20 §4.5` / `20 §6.1` | 2026-09-21 | **registered** | CA-004 → CR-004（CHANGE-3 主导） |
| `71f51f9` | `10 §6.3` / `20 §5.3` | 2026-09-24 | **registered** | CA-003 → CR-003（CHANGE-3 主导 / CHANGE-2） |
| `60fa9ff` | `10 §12` / `20 §12` | 2026-09-24 | **registered** | 变更记录追加 = 本审计机制的登记动作本身（`README:138`「追加到分册尾部」）；**非规范语义变更**；由 CA-003 / CR-003 §7-E 覆盖 |
| `12493ca` | `CR-003`（L1，**非** L0 00–50） | 2026-09-24 | **registered** | WS-A 治理一致性修正（R-03/R-04/R-05/R-06）；触及 `Docs/V3_SPEC` 但**不触及 L0 00–50** ⇒ 非 L0 修改，按下方 (c) 静态检查点声明 |
| CA-004 登记所在 commit | `20 §12` / `90 §11` / 新增 `CR-004`（L1） | 2026-09-24 | **registered** | 变更记录追加 + 本节审计登记 + 新增 L1；`20 §12` 为**非规范语义**的 changelog 追加，由 CA-004 自身覆盖 |

#### (b) `0dd954d` 之前触及 L0 的提交 —— **historical-exempt**（一次性枚举登记）

`88e7a29`（2026-09-05 init V3 baseline）· `b02c16c` `60bc497` `95c1700` `5ae9853` ·
`ff64352` `a105bf8` `c6014f7` `3cca050` `9c1d43f` `b24b5a7` `19d236b` `5f0d3d0` `0b0a4d3`
（2026-09-08）· `5c9ecc9`（2026-09-09）

→ 全部 **historical-exempt**：均发生在 `90` 生效（`c5a899f`，2026-09-13 17:12）**之前**，
提交信息自带 `errata` / `Scope Freeze errata` / `spec-only, A-Guarded` / `docs(D-n)` /
`BUG-V3-xxx freeze` 等既有变更惯例标记。本条即为对该历史集合的**一次性枚举登记**，
使「已审计」成为**可验证**状态；**不改写**其历史内容。

#### (c) 静态检查点（R-02 —— 只记录最小治理要求，**不建机制**）

**不新建** CI / 数据库 / 服务 / 脚本框架 / 生产代码。仅记录一条可人工执行的检查要求：

> `Docs/V3_SPEC` tree hash 发生变化时，必须能在本节找到对应 CA 条目；
> 若该变化**不触及** L0 `00–50`（例如仅改 `90` / `91` / `README`，或新增 / 修改 L1 文件），
> 则在本节补一行声明其为「L0-META / L1 面改动，非 L0 修改」。仍**不使用**「已审计所有」表述。

既有 `90 §11`（登记义务）+ `G-02 §6`（tree hash 记录）+ `CR-003 §10` / `CR-004 §8`（re-freeze
identity）已足以形成「**L0 tree hash change → audit required**」闭环 ⇒ **不增加机制**。

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
| **90（本文档）** | **治理元规范**。定义 L0–L5、核心规则、CHANGE 分类、扫描规则、读取顺序。回答「**谁说了算**」 |
| **91** | **项目词汇宪法**（L0-META，与 90 同级互补）。定义 Phase/Step/Gate/Path、Contract 使用门槛、状态词冻结集、新文档出生证明。回答「**这些词是什么意思**」。**不修改业务语义，不改变 90 的权威层级** |
| **82** | **治理执行记录**。保留 **§3 Gate State Authority（唯一）** + §5 BIND-1/2/3 + §10 Phase Baseline。§1/§2/§9/§11 **被 90 吸收** |
| **83** | L4 全仓形式扫描结果（G1–G6） |
| **84** | **Conflict Ledger**——全部争议点 / 交叉约束 / 潜在冲突的裁决台账 |
| `docs_audit/` | 机器可读扫描产物（`authority_matrix.yaml` / `contradiction_candidates.json` / `frozen_terms.json` / `document_census.json` / `scan_report.md`） |

**L3/L4/L5 永远不得改变 L0/L1；L2 不得修改 L0。** 本规则对 82/83/84/91 同样适用。

### 8.1 当前阶段：Documentation Governance Stabilization（DG）

**不叫** `Gate E` / `Step X` / `Phase Y`——见 `91 §6`。
**DG 全绿前不得进入 Binding Authority Decision，更不得实现 Adapter。**

| 编号 | 内容 | 状态 |
|---|---|---|
| **DG-1** | Document Census——全仓归层 + 四类问题扫描 | **进行中**（`docs_audit/document_census.json`） |
| **DG-2** | 权威归属标注——每份 ACTIVE 文档补齐出生证明（`91 §5`） | 未开始（当前 **3/44**） |
| **DG-3** | 术语冻结——`91 §1–§3` 生效；`84` 重复概念项清零 | 基础已立 |
| **DG-4** | 状态统一——状态词收敛到 `91 §3.1` 冻结集 | 未开始 |
| **DG-5** | 冲突清零——`84` OPEN 项归零（含 **CA-001**） | 未开始 |

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
