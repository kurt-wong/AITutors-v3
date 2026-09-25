# CR-004 — CONTRACT CHANGE RECORD：f708370 canonical Unit-Type vocabulary correction

```text
Document ID:           CR-004
Title:                 CONTRACT CHANGE RECORD — f708370 Canonical Unit-Type Vocabulary Correction
Document Type:         Contract Change Record
Authority Level:       L1
Status:                ACTIVE
Normative:             YES（对 L0 修改的生效授权与 provenance；不定义任何新业务语义）
Purpose:               为**既存** L0 修改 f708370（`20 §4.5` / `§6.1`）补齐 L1 provenance /
                       Change classification / audit 链。**不回滚、不重新设计 canonical
                       vocabulary、不重新裁决业务语义。** 不可合并差异见 §0.1。
Derives From:          L0 `README.md §2.2` 术语裁决（权威）· L0 `10 §5.2:290` / `§6.5:516`
                       （`unit_type` 闭集）· `IMPLEMENTATION-PLAN-v0.3.md §0b:83`
                       Terminology（mandatory）· `OD-P09` / `OD-P11` / `OD-2`（Unit Type 词面裁决）·
                       `90 §1 / §1.2 / §2 R1 / §3 / §4 / §11` · `91 §5 / §5.1`
May Change:            本 Change Record 自身的登记元数据
Must Not Change:       L0 业务语义 · L0-META 90/91 治理原则 · Frozen Contract · Schema · migration ·
                       Code · Corpus · canonical vocabulary 语义 · Question / Unit formal state ·
                       Gate / Admission semantics · 历史决策语义
Supersedes:            —
Superseded By:         —
Gate State Authority:  NO
```

> 本文件是 **L1 Contract Change Record**（`90 §1`：修改 L0 的唯一入口）。
> 它为 **f708370 已发生的 L0 修改**补 provenance，**不是**新的 Owner Decision，**不重新裁决**
> canonical Unit-Type vocabulary。
> 与 OD-R-01 的 `CR-003` **完全独立**：两条独立 change，各有独立 provenance 与独立 re-freeze 链（§8）。

---

## 0. `91 §5.1` 新文档创建门槛四问

| # | 必须证明 | 本记录的答案 |
|---|---|---|
| 1 | 为什么现有文档承载不了？（不可合并差异） | 见 §0.1 |
| 2 | 出生证明齐备 | 头块 13 项字段齐全（`91 §5`） |
| 3 | 权威归属明确 | `Authority Level: L1` ∈ `90 §1` / `91 §5:167`；未自创层级 |
| 4 | 允许改什么 / 禁止改什么 | `May Change` / `Must Not Change`（**含 L0**） |

### 0.1 与最近似文档的不可合并差异

| 最近似文档 | 为什么不能合并 |
|---|---|
| `CR-003`（OD-R-01） | 两条**不同** L0 change、不同 target（`10 §6.3`+`20 §5.3` vs `20 §4.5`+`§6.1`）、不同 Owner 来源。任务书 §15 明令「**不要把 f708370 重新并入 OD-R-01 的 CR-003**」；合并会使独立 provenance 消失。 |
| `90 §11` 内嵌 `CR-001` | 那是**事后历史追认**记录（CHANGE-2，目标 `40 §5`），不是可引用的活 L1；且并入审计日志会让审计载具兼任授权层（同 `CR-003 §0.1`）。 |
| `Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` | 未归层（`90:47`）+ `NOT RELEASED` / `NOT REGISTERED`，目标亦为另一变更（OD-01 Option Provenance）。 |
| `IMPLEMENTATION-PLAN-v0.3.md §0b:83` | 那是 authority 的**内容来源**，不是 L0 修改入口（`90 §2 R2`：Plan 不得修改 L0）。 |

**物理落点**：`90 §1.2:79` 对 `Docs/V3_SPEC/` 的允许列明文含「**新增 L1**」。**不创建第二套 registry。**

---

## 1. 标识

```text
Change Record ID : CR-004
Source Commit    : f708370065870d89ac4ba025a1d47e38c411314e（2026-09-21T12:25:53+08:00）
Parent Commit    : 13fdce08d2d2fb7f504c9938f1a129753b20f9e9
Audit ID         : 90 §11 CA-004
Target           : L0 Docs/V3_SPEC/20_Document_Pipeline.md §4.5 / §6.1
Date（事件）      : 2026-09-21
Date（登记）      : 2026-09-24（事后补记；不回溯、不改历史日期）
```

---

## 2. Owner authority（§11 / §14 判定）

> 本节引用的**任务书坐标**（`§11` / `§14` / `§22` / `§10A` / `§10C` / `§15` / `§5`）属**仓外任务授权载体**，
> 与仓内 L0 / L0-META 权威严格分列；对照与作用见 **§2.4**。

### 2.1 待证明命题

```text
standalone_question / composite_question 不得作为 canonical V3 Unit Type。
```

### 2.2 仓内可证明该命题的既有记录（本 L1 只**引用**，不新建）

| 记录 | 层 | 内容 |
|---|---|---|
| L0 `README.md §2.2`（`README:68` = 「术语裁决（**权威**）」） | **L0** | `\| standalone_unit \| 可独立解答的题 \| standalone_question / independent \|` ⇒ `standalone_unit` 是 V3 裁决术语，`standalone_question` 是「V2 曾用」。且 `00:10` / `10:14` / `20:13` 三分册均写「术语裁决以 `README.md` §2 为准」 |
| L0 `10_Data_Model.md §5.2:290`、`§6.5:516` | **L0** | `\| unit_type \| VARCHAR \| standalone_unit / composite_unit \|` —— **闭集**，不含 `standalone_question` / `composite_question` |
| `IMPLEMENTATION-PLAN-v0.3.md:83`（位于 `## 0b. Owner Decisions OD-01 ~ OD-05（reconciled into this plan）` 块内） | Plan（Binding Authority Chain 内） | 「**Terminology（mandatory）：** Canonical Unit Type 仅 `standalone_unit` / `composite_unit`。**禁止**将 `standalone_question` / `Standalone Question` 当作当前 V3 概念；仅可作历史/Producer/provenance 词汇。**禁止**建立 `standalone_question → canonical_question_type` 兼容模型。」 |
| `V3-CONTRACT-v0.3-OWNER-DECISION-PACKAGE.md`：`OD-P09`「Unit Type mapping 的唯一 runtime authority」、`OD-P11`「v0.2 UT 词面与 **OD-2 canonical 词面**消歧」；`IMPLEMENTATION-PLAN:158` 引 **OD-2**「Legacy Unit Type 仅经 Owner 授权确定性归一」 | Owner Decision Package | Unit Type 词面的 Owner 裁决载体 |

**判定**：命题**可被既有记录证明** ⇒ **不属于 §14 情况 C**，**未触发 STOP**。归 **§14 情况 B**
（无适用 L1，而 f708370 属 normative L0 modification ⇒ 创建最小 L1，引用既有记录）。

### 2.3 具名 instrument 的归属缺口（如实标注 = UNKNOWN）

```text
f708370 的 commit message 与代码注释所引的两个具名 instrument：
  「Owner D1」 / 「2026-09-20 Concept Correction」
在 Docs/ 内【无同名正式 Owner Decision / Decision Record】。全仓命中仅来自：
  · 20:177（由 f708370 自己写入）
  · backend 代码注释（ir.py:118 · gate/service.py:333 · boundary.py:15 · annotation_adapter.py:14）
  · backend 测试（test_m3_boundary_canonical_vocabulary.py:3 等，随 f708370 一并加入）
⇒ 具名归属标签 = UNKNOWN（attribution label unresolvable in-repo）
```

**处置**：本 L1 **不追认**任何新的 Owner Decision，**不把**该标签升格为正式记录，只引用 §2.2 的
既有记录作为 authority。若 Owner 日后补齐该具名 instrument，只需回填本节，**不改变**本 Change
Record 的任何结论。

> **安全阀**：若 Owner 认为「具名 instrument 缺失」本身即应触发 §22 STOP-1，请指示——
> 本记录可整体撤回（**仍不回滚 f708370**，只是不补该 provenance），不影响任何业务语义。

### 2.4 任务书坐标对照（provenance；**不引入新权威层**）

> **本节目的**：使本记录中引用的**外部任务书坐标**在未来可复核。
> **本节不做**：不把 task-book 搬进仓库、不复制外部原文、**不重新定义** `§22 STOP-1` / `STOP-8`、
> **不修改**其实质判据、**不把** task-book 宣称为 Frozen Spec、**不新增**权威层。
> 本节属头部 `May Change`（登记元数据 / provenance），**不改变** §3–§8 的任何结论、分类或 re-freeze 链。

**两类权威严格分列（不得混为一谈）**

| 类别 | 载体 | 仓内可解析 | 在本记录中的作用 |
|---|---|---|---|
| **仓内权威** | L0 `README.md §2.2` 术语裁决（权威）· L0 `10 §5.2:290` / `§6.5:516` `unit_type` 闭集 · L0-META `90` / `91` | **是** | 提供命题的**实质裁决内容**与**流程规则**（CHANGE 分类、L1 入口、审计登记） |
| **仓外任务授权载体** | 创建本补记任务的任务书（OD-R-01 / f708370 provenance remediation 任务链的 Owner 指令） | **否** | 只提供**本次补记动作的授权与流程约束**（何时 STOP、如何分类、允许改什么）。**不是**业务语义来源，**不是** Frozen Spec，**不得**与 README / Frozen Spec / Governance 并列为同一种权威 |

**任务书坐标 → 本记录中的作用（只记「承担什么作用」与「本记录做了什么判定动作」，不复述判据原文）**

| 坐标 | 在当前治理链中承担的作用 | 本记录在此坐标下采取的动作 |
|---|---|---|
| `§11` / `§14` | 判定 f708370 缺的是**流程（L1）**还是**权威**，据此决定 STOP 或补 L1 | §2.2 判定命题可由既有记录证明 ⇒ 归「情况 B」（无适用 L1 而属 normative L0 modification ⇒ 创建最小 L1 引用既有记录）；「情况 C」**未触发** |
| `§22 STOP-1` | 授权 / 权威无法确定时的停止条件 | §2.2 判定权威可证 ⇒ **未触发**；§2.3 的具名 instrument 缺口记为 UNKNOWN（归属标签问题，非权威缺失），并保留可整体撤回安全阀 |
| `§22 STOP-8` | 禁止重新设计 canonical vocabulary | §5 处置列为「不做」 |
| `§10A` | Change 分类不得因「修正词汇」自动降为 CHANGE-1 | §4.A 做 before / after semantic effect 实际比较后仍归 **CHANGE-3** 主导 |
| `§10C` | 测试改动只能是 verification evidence，不得升格为架构事实 | §4.C 分列并标注「不计入 Change classification」 |
| `§15` | f708370 **不得**并入 OD-R-01 的 `CR-003` | §0.1 / §8 保持两条独立 provenance 与独立 re-freeze 链 |
| `§5` | 未重跑 Phase 1、未重开 X2.6 M.3 | §6 记实现层回归 `NOT VERIFIED`，未伪造证据 |

**可复核性边界（如实）**：上表**只**使「本记录在该坐标下做了什么判断」可自证；
坐标本身的**判据原文**属外部任务授权载体、**不在仓内**，本表**不承担**使其可自证。
需判据原文时须回到任务授权载体，**不得**据本表推导或改写判据。

---

## 3. Target / Before / After

### Target — `Docs/V3_SPEC/20_Document_Pipeline.md`

| 位置 | Before | After |
|---|---|---|
| `§4.5` 小节标题 | `**standalone_question**：` | `**standalone_unit**：` |
| `§4.5` JSON 规定值 | `"unit_type": "standalone_question"` | `"unit_type": "standalone_unit"` |
| `§4.5` 注 | （无） | 新增：`standalone_question` = Producer legacy vocabulary（见 README §2.2 术语裁决）；V3 canonical Unit-Type 为 `standalone_unit`；Owner D1 明确禁止 `standalone_question` / `composite_question` 作为 canonical vocabulary；Question Type 与 Unit Type 是正交维度，不得混用 |
| `§6.1` 小节标题 | `**standalone unit**：` | `**standalone_unit**：` |
| `§6.1` JSON 规定值 | `"unit_type": "standalone_question"` | `"unit_type": "standalone_unit"` |

blob SHA-1（git 对象实测）：`20_Document_Pipeline.md`
`5f1c6d1da586285ad74182b26d9ef75ed40016d8` → `944479ee9d6f9ddcd4c547b30d663ede3e370c8d`。

---

## 4. Change Classification（`90 §3`）

### 4.A Frozen Spec 文字变化 → 主导 **CHANGE-3 — Normative Modification**

**before / after semantic effect 实际比较（§10A 要求：不因「修正词汇」自动归 CHANGE-1）**

| 维度 | before semantic effect | after semantic effect |
|---|---|---|
| Semantic Unit kind 名（`§4.5` 标题） | `standalone_question` | `standalone_unit` |
| Annotation / IR `unit_type` **规定值**（`§4.5` / `§6.1` JSON） | `"standalone_question"` | `"standalone_unit"` |
| 禁令 | 无 | **新增**：禁 `standalone_question` / `composite_question` 作 canonical vocabulary；Question Type 与 Unit Type 正交**不得混用** |
| 词汇定性 | 无 | **新增**：`standalone_question` = Producer legacy vocabulary |

**为什么不是 CHANGE-1（Clarification）**

1. `20 §4` / `§6` 是 **Semantic Unit 与 IR 形态的唯一规定处**。其 JSON `unit_type` 是管线契约的
   **规定值**，**不是** `10 §5.2` 列域的重复——`10 §5.2:290` 的 `unit_type` 是
   `admission_candidates.unit_type` 表列，`10 §6.5:516` 的是 `unit_groups.unit_type` 表列，
   与 Annotation / IR 字段**不在同一层**。改变其规定值 = **改变既有规定的行为**
   （按 `20` 实现的 IR 应产出的值变了）。
2. 新增注含**新禁令**（「不得混用」「禁止…作为 canonical vocabulary」）⇒ 规范语义**有新增**，
   直接否定 CHANGE-1 的「规范语义**零**变化」。

**为什么不是 CHANGE-4 / 5**：未放宽、未删除任何既有约束——是把规定值对齐 L0 既有闭集，并**新增**禁令。

**分类结论**：含 CHANGE-2 分量（新增禁令）+ CHANGE-3 主导（规定值改变 = 行为改变）。
按 `90 §3`「**拿不准往高里归**」→ **主导分类 = CHANGE-3 — Normative Modification**。
**流程**：Change Record + 受影响层回归；四道门 **不需要**（仅适用 CHANGE-4 / CHANGE-5）。

### 4.B backend IR 修改 → implementation consequence（**不是** L0 change）

```text
backend/app/domains/compile/ir.py  2 行（+2 / -2）
  :112  IRBuilder default   'standalone_question' → 'standalone_unit'
  :146  IRBuilder output    'standalone_question' → 'standalone_unit'
性质：implementation consequence —— 对 4.A 规定值变更的实现侧跟随。
【不伪装成 L0 change】【不计入 Change classification】
```

### 4.C tests → verification evidence（**不是**架构事实）

```text
backend/tests/test_m3_boundary_canonical_vocabulary.py   新增 150 行
backend/tests/test_x26_m1_acceptance_shapes.py           +17 / -4
性质：verification evidence（任务书 §10C）。
【不升格为架构事实】【不计入 Change classification】
```

> **四者严格分列**：Frozen Spec change（4.A） ≠ backend implementation change（4.B）
> ≠ test evidence（4.C） ≠ 本 Change Record（provenance）。**不得混为一个架构事实。**

---

## 5. Review / disposition

| 项 | 处置 |
|---|---|
| f708370 业务方向 | **保留，不回滚**（源自既有 canonical vocabulary 裁决，见 §2.2） |
| reverse commit / rewrite history / force push | **禁止** |
| Change classification | **CHANGE-3**（主导）· 四道门不需要 |
| 重新设计 canonical vocabulary | **不做**（§22 STOP-8） |
| 重新裁决业务语义 | **不做** |
| disposition | **registered — ratified via CR-004** |
| Review | **ACCEPTED / EFFECTIVE**（2026-09-24） |

**生效区分（对齐 CR-001 / CR-003）**：CR-004 Accepted 之前「L0 文本已存在 ≠ 该 CHANGE 已完成生效」。
自 Review **ACCEPTED / EFFECTIVE** 起，f708370 的 L0 修改具有完整 L0 效力。

---

## 6. 受影响层回归 —— 如实记录

```text
状态：NOT VERIFIED（本任务口径）—— 实现层回归【未在本任务重跑】
本任务做了什么：只做 provenance / classification / audit 登记
本任务没做什么：未改 backend、未增/改测试、未改 IR / Gate / Admission、
                未重跑 Phase 1、未重开 X2.6 M.3（任务书 §5 明令禁止）
```

**f708370 时点的 verification evidence（记录，不重跑、不伪造）** —— 来源 = 该 commit message 自述
（证据等级：**DOCUMENT CLAIM**，非本任务复验）：

```text
Targeted  : 137 passed, 0 failed
Regression: 197 passed, 0 failed
```

> **不得误读**：上述数字是 **f708370 当时的实现层测试结果**，**不是**本 Change Record 的
> 「受影响层回归已通过」证明。受影响层回归在本任务口径下 **NOT VERIFIED**。

---

## 7. Scope / Explicit Exclusions

```text
IN SCOPE：f708370 的 L0 文字变化之 provenance / classification / audit 闭环。

不裁决、不做（不得据本记录推导）：
- canonical vocabulary 的语义重设计
- Question / Unit formal state 新增
- Gate / Admission semantics
- Evidence / payload / answer_status / answer[] representation
- Database schema / migration / ORM
- 任何生产逻辑修改（含「顺便修好」其他问题）
- P04 / P07 重新裁决 · X3 entry · Phase 1 · Historical rerun
```

---

## 8. Re-freeze（独立链，**不并入** CR-003）

```text
pre-f708370 tree（= 13fdce08:Docs/V3_SPEC）
  = fa1e953e7c4638236b298cf1c137aa2a107d5ea5     【历史 baseline，保留不改】
        ↓
f708370 incorporation（= f708370:Docs/V3_SPEC）
  = b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f     【20 §4.5 / §6.1 词汇修正后的 L0】
        ↓
后续独立 change（OD-R-01 等）→ … → 本记录生效 commit 的 Docs/V3_SPEC tree
  = git rev-parse <本记录生效 commit>:Docs/V3_SPEC
```

**同值说明（非笔误）**：`b3eeb3e9…` **同时**是 f708370 的 incorporation tree 与
OD-R-01（`CR-003 §10`）所称的 previous / pre-OD-R-01 tree —— 两种称谓同指一物，链条自洽。

**Re-freeze identity 权威表述**：`Docs/V3_SPEC` git tree object，锚定于本记录生效 commit。
机械复核：`git rev-parse <生效 commit>:Docs/V3_SPEC`。
字面值可读副本（非权威）= `Docs/COORDINATION/G-02-FREEZE-REGISTRATION-VERIFICATION.md` §6.2。
字面值不自记于本文件（自指不动点），同 `CR-003 §10` 的处理。

**独立性（§15）**：本链**不并入** `CR-003`。f708370 是独立 change，有独立 provenance。

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/V3_SPEC/CR-004_CONTRACT_CHANGE_RECORD_F708370-UNIT-VOCABULARY.md` |
| Authority Level | L1 |
| Status | ACTIVE |
| Change Record ID | CR-004 |
| Audit ID | 90 §11 CA-004 |
| Registration Level | REGISTERED AS L1（第二条正式 L1） |
