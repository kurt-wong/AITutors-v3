# 91 — Project Terminology：项目词汇宪法

**Document Type**: Governance Meta-Spec
**Authority Level**: **L0-META**（与 `90` 同级；定义**项目语言**，不定义业务语义）
**Status**: ACTIVE
**Normative**: YES（对**词汇使用**规范；**不定义任何业务事实**）
**Supersedes**: —
**Superseded By**: —
**Gate State Authority**: NO（唯一权威仍是 `82 §3`）

**Date**: 2026-09-13
**性质**：`90` 回答「**谁说了算**」；本文档回答「**这些词是什么意思**」。
二者互补，**都不含业务语义**。

---

## 0. 为什么需要词汇宪法

`90` 建立了文档权威层级，但**没有约束文档的语言**。结果是同一个字母在四个
维度上各指一件事，读者必须靠上下文猜：

```text
Phase B   ← 生命周期阶段？还是别的？
Step B    ← 执行步骤
Path B    ← 架构分支（Adapter/Manifest）
Gate B    ← 验证门槛
```

**实测用法（2026-09-13 扫描）**：

| 词 | 不同形态数 | 样例（按频次） |
|---|---|---|
| `Phase` | **16** | `Phase 1`(44) `Phase I-3`(25) `Phase 2`(25) `Phase I-4`(24) `Phase I-5`(17) `Phase I-2C`(8) `Phase R`(6) `Phase B`(3) `Phase I-5-G`(1) |
| `Step` | **8** | `Step B`(6) `Step C`(5) `Step 3`(4) `Step 0.5`(4) `Step B.5`(3) `Step 0`(2) |
| `Path` | 2 | `Path B`(106) `Path A`(3) |
| `Gate` | 11 | `Gate C`(62) `Gate B`(42) `Gate D`(34) `Gate B1`(19) `Gate A`(16) `Gate B2-A`(13) … |

**`Phase` 同时承载了两套不同编号体系**（罗马 `I-2C`/`I-3`/`I-4`/`I-5` 与
阿拉伯 `1`/`2`/`3`/`4`/`9`）**加一套单字母**（`R`/`B`）——这是本文档要解决的
核心问题。

---

## 1. 时间维度词

| 词 | **唯一允许含义** | **禁止含义** | 现行规范形态 |
|---|---|---|---|
| **`Phase`** | **项目生命周期阶段**（回答「项目处于什么时期」） | ❌ 单个任务 ❌ 实验轮次 ❌ 子步骤 | **罗马编号 `I-n`**：`I-2` `I-2C` `I-3` `I-4` `I-5`。子阶段用 `I-5-G` 形态 |
| **`Step`** | **Phase 内的执行顺序**（回答「下一步做什么」） | ❌ 架构路线 ❌ 生命周期阶段 | **阿拉伯编号** `Step 1` `Step 2`…；实验内的子步可用 `Step 0.5` |
| **`Gate`** | **验证门槛**（回答「是否满足通过条件」） | ❌ 开发阶段 ❌ 时间顺序 | 现行层级 `A` / `B` / `B1` / `B2-A` / `B2-B1`… / `C` / `D`，状态一律以 `82 §3` 为准 |
| **`Path`** | **架构 / 数据流分支**（回答「有几条运行路线」） | ❌ 时间阶段 ❌ 执行步骤 | **当前已登记两条**：`Path A` = Native（Resolver search/resolve）；`Path B` = Adapter/Manifest（verify only） |

### 1.3 Path 的登记制（不是永久冻结）

> **`Path` 一词保留给架构 / 数据流分支。**
> **当前已登记**：`Path A` — Native；`Path B` — Adapter/Manifest。
> **新增 Path 标识符必须经显式治理审查。**

**为什么不写「永久只有两条」**：那等于提前对未来架构空间做一个 CHANGE-5 /
constraint-removal 级别的承诺，当前项目没有理由这么做。**登记制**既消灭了
眼前的命名混乱，又不给未来套死。

**新文档禁止再用单字母命名 Phase / Step。**

### 1.1 现存命名冲突（登记，不改写）

| 冲突 | 说明 | 处置 |
|---|---|---|
| **`Phase B` / `Step B` / `Path B` / `Gate B` 四个共存** | 同一字母 B 在四个维度各指一件事 | **历史保留**；新文档**禁止**再用单字母命名 Phase/Step |
| **`Phase 1`/`2`/`3`/`4`/`9` 与 `Phase I-n` 是两套体系** | 前者是 **Evidence Promotion 内部子阶段**（`75`–`79`），后者是**项目生命周期** | 见 §1.2 |
| **`Phase I-5-G` / `I-5-1` / `I-5-0`** | `I-5` 的子阶段 | 合法；形态冻结为 `I-<n>-<sub>` |

### 1.2 两套 Phase 体系的区分（冻结）

| 体系 | 含义 | 现存项 | 建议改称 |
|---|---|---|---|
| **项目生命周期** | V3 整体所处时期 | `I-2` `I-2C` `I-3` `I-4` `I-5`（含 `I-5-0`/`I-5-1`/`I-5-G`） | **保持 `Phase I-n`**，是规范形态 |
| **Evidence Promotion 内部** | `75` 契约下的实现分期 | `Phase 1`（44 处）`Phase 2`（25 处）`Phase 3` `Phase 4` `Phase 9` | **新文档改称 `EP-Stage n`**（Evidence Promotion Stage）；历史保留 |

> **理由**：`Phase 1` 出现 44 次却与项目生命周期的 `Phase I-3`/`I-4` 完全不在
> 同一轴上。不改称就会不断被误读为「项目第一阶段」。

**不强制改写历史**（Reconcile, don't rewrite）；`90 §2 R8` 的废止传播规则适用于此。

---

## 2. 架构维度词

| 词 | **唯一允许含义** | 禁止 |
|---|---|---|
| **`Path`** | 架构分支（见 §1） | ❌ 时间阶段 |
| **`Pipeline`** | 处理链（`SealedSource → … → Admission`） | ❌ 单个组件 |
| **`Boundary`** | 责任边界（谁该做什么 / 不该做什么） | ❌ 物理接口 |
| **`Contract`** | **稳定约束**——必须能追溯到 L0/L1 或已闭包的 L2 裁决（`90 §2 R7`） | ❌ 实验约定 ❌ 临时设计 |

### 2.1 Contract 一词的使用门槛（冻结）

> **只有满足 `90 §2 R7` 引用闭包的约束才能称 `Contract`。**

L4 实验报告中的约定**不得**称 Contract——那是 `Experiment Convention`。

现存量检查：`75` 的 `Evidence Promotion Contract` ✅ 有闭包（L2 裁决 + 架构审查通过）；
`81` 的 `Adapter Contract` ✅ 有闭包（`69 §Gate D` + `66 §7`）。

---

## 3. 状态词（冻结集合）

### 3.1 允许的状态值

| 状态 | 含义 | 适用层 |
|---|---|---|
| **`OPEN`** | 已登记，未解决 | 全部 |
| **`PENDING`** | 等待外部条件 | 全部 |
| **`CONDITIONAL PASS`** | 部分满足，残留项显式列出 | L3 Gate |
| **`CLOSED`** | **满足其声明的定义条件**（须带范围限定） | L3 Gate |
| **`NOT STARTED`** | 未开工 | 全部 |
| **`DEFERRED`** | 显式延期，不视为失败也不视为完成 | 全部 |
| **`SUPERSEDED`** | 已被他文废止（正文保留，`90 §2 R8`） | 全部 |
| **`RETRACTED`** | 本文件自己撤回的结论 | L4 |
| **`ACTIVE`** | 现行有效 | 全部 |
| **`HISTORICAL`** | 历史记录，非现行 | 全部 |

### 3.2 禁止的状态词（新文档）

| 禁用 | 原因 |
|---|---|
| **`COMPLETE`** | 模糊——完成什么？完成到什么程度？现存量 **6 份文档**，历史保留，新文档禁用 |
| **`DONE`** | 同上。现存量 **1 份** |
| **`FINISHED`** | 同上。现存量 **0 份** |
| **`NEXT`** | 不是状态，是顺序。用 `Step n` 表达 |
| **`REVIEWED`** | 模糊——审查通过还是仅审查过？现存量 **3 份**，新文档改用 `ACTIVE` + 引用审查记录 |

### 3.3 `CLOSED` 的强制限定（与 `90 §2 R3` 一致）

> **`CLOSED` 不得单独出现。** 必须写成
> `CLOSED — <范围限定>（依据 82 §3，日期）`。

例：`Gate B2-B5: CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED（依据 82 §3）`。

---

## 4. 与 90 / 82 / 84 的分工

| 文档 | 回答 |
|---|---|
| **`90`** | **谁说了算**（文档权威层级 L0–L5、变更分类、扫描规则、读取顺序） |
| **`91`（本文档）** | **这些词是什么意思**（Phase/Step/Gate/Path、Contract 门槛、状态词冻结集） |
| **`82 §3`** | **现在什么状态**（Gate State Authority，唯一） |
| **`84`** | **哪里有冲突**（Conflict Ledger） |

**91 不修改任何业务语义，也不改变 90 的权威层级。** 二者同为 L0-META，
互不覆盖。

---

## 5. 新文档出生证明（Status Header 扩展）

`90 §4` 的 Status Header 在本文档下扩展为**出生证明**——回答「为什么存在 /
归属哪层 / 能改什么 / 不能改什么 / 依赖谁 / 能否被废止」：

```text
Document ID:      <编号>
Title:            <标题>
Document Type:    <Frozen Spec | Contract Change Record | Decision Record |
                   Governance Meta-Spec | Gate Report | Experiment Report | Status>
Authority Level:  <L0 | L0-META | L1 | L2 | L2-proposed | L3 | L4 | L5>
Status:           <ACTIVE | SUPERSEDED | HISTORICAL | DRAFT | CLOSED | NOT RELEASED>
Normative:        <YES | NO>
Purpose:          <一句话：本文档解决什么问题>
Derives From:     <本档结论向上闭包到哪些 L0/L1/L2 条目（90 §2 R7）>
May Change:       <本文档有权影响的范围>
Must Not Change:  <本文档无权触碰的范围（至少含 L0）>
Supersedes:       <doc list 或 —>
Superseded By:    <doc 或 —>
Gate State Authority: <YES | NO>   # 现行唯一 YES = 82 §3
```

**`Derives From` 是 R7 引用闭包的可机检落点**——扫描器可据此验证每个 L2/L3/L4
的规范性结论是否真有向上闭包。

**存量文档不强制回填**；下次实质修订时补。

### 5.1 文档创建门槛（冻结）

> **这是 DG 阶段要解决的根因。** 60+ 文档膨胀的根源不是编号乱，而是
> **没有「什么时候该建新文档」的门槛**——于是为了解决治理问题又不断创建
> 治理文档：`90 → 91 → 92 → 93 → …`，重演 60+ 的问题。

**创建任何新文档前，必须回答四项，缺一不可**：

| # | 必须证明 | 落点 |
|---|---|---|
| 1 | **为什么现有文档承载不了？** | 出生证明 `Purpose` 须说明它与最近似现有文档的**不可合并差异** |
| 2 | **出生证明齐备** | `91 §5` 全部字段，缺字段即不得创建 |
| 3 | **权威归属明确** | `Authority Level` ∈ `91 §1` / `90 §1` 已定义的层级；**不得自创层级** |
| 4 | **允许改什么 / 禁止改什么** | `May Change` / `Must Not Change`；`Must Not Change` **至少含 L0** |

**判定**：四项任一答不出 → **不得创建**，应改为在现有文档中增补章节。

**当前阶段的额外约束**：DG 期间**冻结新建治理文档**。`90`/`91`/`82`/`84` 已
分别承载「谁说了算 / 词是什么意思 / 现在什么状态 / 哪里有冲突」四个问题；
再建治理文档必须先证明这四份都承载不了。

**扫描器永远是候选生成器，不是裁决器**（见 §6.1）。

---

## 6. 当前阶段命名（冻结）

> **当前阶段 = `Documentation Governance Stabilization`（DG）**

**不叫** `Gate E` / `Step X` / `Phase Y`——`Gate` 是验证门槛、`Step` 是执行顺序、
`Phase` 是生命周期，三者都不是「治理工作包」的正确量词。

| 编号 | 内容 | 状态 |
|---|---|---|
| **DG-1** | 文档清点（Document Census）——全仓归层 + 四类问题扫描 | **IN PROGRESS**（`docs_audit/document_census.json`） |
| **DG-2** | 权威归属标注——每份 ACTIVE 文档补齐出生证明 | **NOT STARTED**（当前 **3/44**） |
| **DG-3** | 术语冻结——本文档 §1–§3 生效；`84` 重复概念项清零 | **BASELINE ESTABLISHED** |
| **DG-4** | 状态统一——状态词收敛到 §3.1 冻结集 | **NOT STARTED** |
| **DG-5** | 冲突清零——`84` OPEN 项归零 | **IN PROGRESS** |

**DG-5 处置顺序**：~~CA-001~~（**已 CLOSED，CR-001**）→ D-01 → C-01 → D-02。

**DG 全绿前不得进入 Binding Authority Decision，更不得实现 Adapter。**

**不要因为 DG-1 发现了 47 组重复阶段名就现在批量重命名**——先把治理规则本身
稳定下来，再处理历史文档。

### 6.1 扫描器永远是候选生成器，不是裁决器（冻结）

```text
Scanner → Candidate → Human / governance adjudication → Decision → Audit update
```

**禁止**：

```text
Scanner → Violation
```

否则 `91` 自己会成为另一个「隐形宪法」——扫描器输出被当成裁决结果。
`docs_audit/` 中的每一项都必须能被人工否决，且否决后须在 `84` 记录理由。

---

## 7. 显式不主张

1. **不主张**本文档可修改任何 L0 业务语义——它只约束词汇。
2. **不主张**历史文档的 `Phase 1` / `COMPLETE` / `Step B` 等用法已改写——
   **Reconcile, don't rewrite**；冻结的是**新文档**的用法。
3. **不主张** §1.2 的 `EP-Stage` 改称已执行——它是**建议**，须经裁决。
4. **不主张**本文档削弱 `90` 的权威层级或 `82 §3` 的 Gate State Authority。
5. **不主张** D-01 / C-01 / D-02 已裁决——三项仍 OPEN。
   （**CA-001 已 CLOSED**：Owner 裁决 (b)，经 `90 §11 CR-001` 追认为 CHANGE-2。）

---

## 8. 下一步

```text
本文档（91 号，词汇宪法）        ← 已立
        ↓
CA-001 → CLOSED（CR-001，CHANGE-2 追认）  ← 已完成
        ↓
DG-1 Document Census 收尾（人工核四类候选，排除误报）
        ↓
裁决 91 §1.2 的 EP-Stage 改称 → D-01 → C-01 → D-02
        ↓
DG-2 出生证明回填 → DG-4 状态统一 → DG-5 冲突清零
        ↓
Binding Authority Decision
```

**不碰 L0 内容、不发 67、不冻结 manifest-only、不实现 Adapter、不批量重命名历史文档。**
