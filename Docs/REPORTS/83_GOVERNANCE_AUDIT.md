# 83 — I-5-G Document Governance Audit：全仓规范性语言扫描与分层对账

**Document Type**: Phase Report（审计结果）／其建议经裁决后可升为 Decision Record
**Authority Level**: C
**Status**: ACTIVE
**Normative**: NO
**Supersedes**: —
**Superseded By**: —
**Gate State Authority**: NO（唯一权威仍是 82 §3）

**Date**: 2026-09-13
> 📌 **路径说明（残余审计 A-11，2026-09-13）**：本文件表格内的
> `Docs/V3_SPEC/Closure/…`、`Docs/V3_SPEC/6x_…`、`Docs/V3_SPEC/71_…`、
> `backend/Docs/V3_SPEC/71_…` 等路径是 **DG-2 迁移前**的路径，现已失效——
> 本文件是**审计当时的快照**，记录的是彼时的仓库布局，**不改写**（Reconcile, don't rewrite）。
> 现行落点：Closure 与编号报告 → `Docs/REPORTS/`；71 号 → `Docs/DECISIONS/`（权威份）
> 与 `Docs/ARCHIVE/71_…_SUPERSEDED.md`（废止份）；`gate_b2a_three_task_report` → `Docs/REPORTS/`。
> 判断当前状态一律以 `82 §3` 为准。
**方法**: 机械扫描，**不重写任何文档**（Reconcile, don't rewrite）。
**脚本**: `backend/scripts/i5g_normative_scan.py`（只读；不 import `app/`，不碰 DB）

---

## 0. 本轮做什么 / 不做什么

**做**：全仓规范性标记计数 → 按 82 §1.2 分层 → 找出 (a) 未分类文档、
(b) 分层错误、(c) C 层自立规范、(d) Gate 状态行集中面、(e) 同号双份。

**不做**：不改 `20`；不发 67；不冻结 manifest-only；不写 Errata Decision；
不实现 Adapter；**不逐句改写历史报告**（只登记 + 标记）。

---

## 1. 扫描方法

**标记词**（大小写不敏感）：`must` `shall` `required` `必须` `不得` `只能` `唯一`
`权威` `冻结` `CLOSED` `PASS` `BLOCKED` `DEFERRED` `architecture` `contract`
`invariant`。

**重要限定**：标记词命中 ≠ 违规。A 层（Frozen Spec）**应该**高密度；
「只能证明 / 本实验采用」这类**限定主张范围**的用法是报告的正确写法。
本审计要找的是**在错误层级用规范性语言自立规则**。

---

## 2. 分层合计

| 层 | 文档数 | 行数 | 命中 | 密度 |
|---|---|---|---|---|
| **A — Frozen Spec** | 7 | 3163 | 410 | 13.0% |
| **B — Decision Record** | 7 | 3445 | 512 | 14.9% |
| **C — Phase Report** | 17 | 4672 | 291 | 6.2% |
| **D — Status** | 3 | 4558 | 842 | 18.5% |
| **UNCATEGORISED** | **5** | **837** | **61** | 7.3% |

A/B 层高密度**属正常**。风险集中在 **C 层的个别高密度文档**、**D 层的 Gate 状态行**、
以及 **5 份未分类文档**。

---

## 3. 审计发现

### G1 — 5 份文档在 V3_SPEC 树内但未分类（🔴 P0）

| 文档 | 行数 | 命中 | 自述 | 建议分层 |
|---|---|---|---|---|
| `Docs/V3_SPEC/Closure/PHASE_I2C_CLOSURE.md` | 161 | 6 | Phase closure | **B** |
| `Docs/V3_SPEC/Closure/PHASE_I2_REVISION_CLOSURE.md` | 142 | 13 | Phase closure | **B** |
| `Docs/V3_SPEC/Closure/PHASE_I3_CLOSURE.md` | 234 | 23 | `Status: CLOSED` / `Gate: PASS` | **B** |
| `Docs/V3_SPEC/Closure/PHASE_I4_CLOSURE.md` | 130 | 15 | `Closure Type: Valid Negative Result` | **B** |
| `backend/.../gate_b2a_three_task_report.md` | 170 | 4 | `Status: COMPLETE`，带 script + data 出处 | **C** |

**风险**：这 5 份共 837 行在 82 §1.2 无归属。其中 4 份是**正式关闭记录**
（`Closure`、`Status: CLOSED`、`Gate: PASS`），措辞读起来就是权威——Agent 完全可能
把它们当 A/B 层用。`PHASE_I3_CLOSURE.md:5` 直接写 `Gate: PASS`，而它**不在**82 §3
的 Gate 表内，无法对账。

**处置**：按上表重新归层并写入 82 §1.2。**不改写正文。**

### G2 — 同号双份且内容不同：71 号（🔴 P0，本轮最重）

| 路径 | 大小 | 时间 | 标题 |
|---|---|---|---|
| `Docs/V3_SPEC/71_B2B5_SUBJECTIVE_SUBQUESTION_ADJUDICATION.md` | 6914 B | Sep 12 **21:33** | 「…**裁决记录**」 |
| `backend/Docs/V3_SPEC/71_B2B5_SUBJECTIVE_SUBQUESTION_ADJUDICATION.md` | 7783 B | Sep 12 **23:05** | 「…Domain Contract Adjudication **(CORRECTED)**」 |

`diff -q` 判定 **DIFFERENT**。

**风险**：这是比 C1 更糟的一类冲突——C1 是同一份文档的状态被两处不同解读，
这里是**两个不同文件抢同一个编号**，且无任何 supersede 声明。更危险的是：
**旧的那份在 `Docs/V3_SPEC/`（A 层目录）里**，按 82 §1.2 的路径直觉它「更权威」，
而它实际是被 CORRECTED 的那一版。Agent 从 root 树 grep 到 71 就会读到 stale 版。

**处置**：需裁决——(a) root 版判 stale，加 supersede 指针指向 backend 版；
(b) 或合并为一份。**本轮只登记，不擅自删除**（删除不可逆，且两份都是历史证据）。

### G3 — 分层错误：3 份（🟠 P1）

| 文档 | 现分层 | 自述 | 问题 | 建议 |
|---|---|---|---|---|
| `63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md` | C | **`Status: Frozen Constraint`**，`Applies From: Phase I-3 Closure onward` | 自称 Frozen Constraint 却被归 Informative | **待裁决 A 或 B**——升 A 须走 §2 正式变更流程，不能靠改标签 |
| `65_PHASE_I5_SCOPE_FREEZE.md` | C | 编号禁令表（`95-106` 行 12 条「不得 / 必须」） | 是 scope freeze 契约，不是阶段报告 | **B** |
| `68_QUESTION_STRUCTURE_DEFINITION.md` | C | — | 69 号已判为「Domain Definition Proposal」 | 保持 C，但须在 82 §1.2 注明 69 的定性 |

**65 的具体证据**（`65:95-106`）：`不得修改 SourceResolver` / `不得引入新的永久
Source 抽象` / `必须保留无 manifest 的原始 Source 路径` ——这是**约束清单**，
按 82 §1.4 规则 3 属 C 层违规；归 B 后违规自动消解。

### G4 — C 层自立规范（🟠 P1）

`74_B2B5_D_PROJECTION_SAFETY_REPORT.md`（C 层，密度 13.9%，77 命中）中存在
**对 V3 下达要求**的语句，而非引用上层契约：

| 行 | 原文要点 | 性质 |
|---|---|---|
| `74:224` | V3 Native Path **必须**自行保证 Source Evidence Binding 的安全性 | 对 V3 立规 |
| `74:226` | 若 preprocessing 接入 V3，它**必须**满足 V3 Evidence Contract | 对上游立规 |
| `74:283` | answer span **不得**与其他 structural region 重叠 | 立 Gate 规则 |
| `74:385` | Validated Evidence（**唯一**允许进入 IR） | 立 IR 准入规则 |
| `74:395-396` | **禁止** CLAIMED → IR / **禁止** PROPOSED → IR | 立 IR 准入规则 |
| `74:418` | Validation **必须**产生 append-only ValidationEvent | 立实现要求 |

**对照**：`74:94`「这个结果**只能**证明」是**正确用法**（限定主张范围），
不属违规。同文档内两种用法并存，说明问题不是「不会写」，而是**缺分类约束**。

**处置**：这些规则若要成立，须有 B 层裁决引用；否则改写为「本实验采用…」或
「根据 20 §X…」。**本轮只登记**——它们大多已被 `75 号`（C-1 设计冻结）以 B 层
身份承接，逐句改写属 Reconcile 阶段后续动作。

### G5 — Gate 状态行集中面（🟠 P1，聚合错误温床）

含 `Gate … CLOSED/PASS/BLOCKED/DEFERRED/CONDITIONAL` 的行数：

| 文档 | 层 | 行数 |
|---|---|---|
| `Status.md` | D | **45** |
| `69_ARCHITECTURE_REVIEW_ADJUDICATION.md` | B | **42** |
| `log.md` | D | 31 |
| `80_B2B5_CLOSURE.md` | B | 19 |
| `81_GATE_D_ADAPTER_BOUNDARY.md` | B | 15 |
| `restart-prompt.md` | D | 15 |
| `74_…PROJECTION_SAFETY_REPORT.md` | C | 5 |
| `82_…RECONCILIATION.md` | B（权威） | 8 |
| `gate_b2a_three_task_report.md` | **未分类** | 1 |

**风险**：C3（`81:11` 的聚合错误）正是在这类表面上产生的。`69` 有 42 行、
`Status.md` 有 45 行，是未来同类错误的最大温床。`69` 的 42 行大多是**带日期的
历史矩阵**（合法），但 §8 那条无日期路线图已造成 C2。

**处置**：82 §3.3 的状态声明模板（「Gate X：状态（依据 82 §3，日期）」）应成为
**新增** Gate 状态行的强制格式。存量不强制回填。

### G6 — D 层密度异常（🟡 P2）

`restart-prompt.md` 密度 **36.6%**，全仓最高。它是 Agent 重启后读的第一份文档，
高密度意味着 Agent 在读到 Frozen Spec 之前就已浸在大量规范性措辞中——这与
82 §11 强制读取顺序的初衷（先 82，再 00–50）部分冲突。

**处置**：**不压缩**（它是操作指令文档，规范性是其功能）。改由 82 §11 的读取顺序
约束：restart-prompt 只做**索引与指针**，具体规范必须指回 A/B 层。
属 Reconcile 阶段的后续动作，本轮不改。

---

## 4. I-5-G 完成条件对账（对照 82 §10）

| # | 条件 | 状态 |
|---|---|---|
| 1 | Authority Matrix 建立 | ✅ 82 §1 |
| 2 | Gate State Authority 建立 | ✅ 82 §3 |
| 3 | Supersession 关系清理 | 🟠 C1/C2/C3 已处理；**G2（71 号双份）待裁决** |
| 4 | ACTIVE 文档 authority/status 明确 | 🟠 §9 规范已立；**G1 五份待归层** |
| 5 | normative-looking phase/report 完成分类 | 🟠 **本报告 §3 即分类结果**；G3/G4 待处置 |
| 6 | Gate 状态不存在冲突 | 🟠 以 82 §3 对账中；**G5 集中面待立规** |
| 7 | Frozen Spec 不被隐式修改 | ✅ 82 §1.4 规则 1 |
| 8 | CHANGE-0…5 覆盖现有 Contract Change 候选 | 🟠 67=CHANGE-5、E1=CHANGE-2 已归；**63 升层若成立则需新 Change Record** |
| 9 | 67/69/74/80/81/82 关系可解释 | ✅ 82 §1.2 + §4 |
| 10 | 无未分类的 normative contradiction | 🟠 **G2 未解决前不成立** |

**结论：I-5-G 未完成。** 10 项中 3 项达成、6 项进行中、1 项被 G2 阻塞。
**不得进入 I-5-BIND。**

---

## 5. 显式不主张

1. **不主张** 标记词命中 = 违规（§1 已限定）。
2. **不主张** 本报告可修改任何 A 层语义——它是 C 层审计。
3. **不主张** G1–G6 已处置——本报告只**登记**，处置需裁决。
4. **不主张** 71 号两份中任一份应被删除——删除不可逆，两份都是审计证据。
5. **不主张** 63 号应升 A 层——自称 Frozen Constraint 不等于已是 Frozen Spec；
   升 A 须走 82 §2 正式变更流程。
6. **不主张** 本扫描穷尽了所有治理问题——它只覆盖指定标记词与 Gate 状态行模式。

---

## 6. 待裁决（按优先级）

| # | 问题 | 建议 |
|---|---|---|
| **1** | **G2**：71 号双份怎么处理？ | root 版判 stale + supersede 指针 → backend CORRECTED 版。**不删除** |
| **2** | **G1**：5 份未分类文档归层 | 4×Closure → **B**；`gate_b2a_three_task_report` → **C** |
| **3** | **G3-a**：63 号是 A 还是 B？ | 倾向 **B**（Decision Record，自述 Frozen Constraint）。升 A 须 Change Record |
| **4** | **G3-b**：65 号归 B | 是（scope freeze 契约） |
| **5** | **G4**：74 号的自立规范怎么处置 | 已被 75 号（B 层）承接的部分加指针；其余改写为引用式或限定式 |
| **6** | **G5**：Gate 状态行强制格式 | 82 §3.3 模板对**新增**行强制；存量不回填 |

---

## 7. 下一步

```text
本报告（83 号，I-5-G 审计）      ← 现在
        ↓
裁决 §6 六项
        ↓
82 §1.2 归层更新 + G1/G2/G3 处置（标记 supersede，不改写正文）
        ↓
G4 处置（指针 / 引用式改写，逐条）
        ↓
全仓一致性复查（重跑 i5g_normative_scan.py）
        ↓
I-5-G 10 项完成条件全绿 → Current Baseline declared
        ↓
I-5-BIND — Binding Authority Decision
```

**不碰 `20`、不发 67、不冻结 manifest-only、不实现 Adapter。**
