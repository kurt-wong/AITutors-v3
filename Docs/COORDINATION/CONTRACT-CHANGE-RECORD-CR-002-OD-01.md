# CONTRACT-CHANGE-RECORD-CR-002-OD-01

```text
Document ID:           CR-002
Title:                 Change Proposal Record — OD-01 Option Provenance
Document Type:         Contract Change Record
Status:                NOT RELEASED
Authority Level:       L2-proposed
Purpose:               OD-01 变更跟踪与 L1 注册条件登记（Candidate）；不生效、不注册
Normative:             NO
Derives From:          OD-01 · OD-01-A…J · Proposal v4R · P04 · L0 00/10/20/50（只读）· 90/91 §3.1 · 69 §5
May Change:            本 Candidate 文本；与 Proposal v4R 引用一致性；Gate 行（仅 PENDING / 冻结枚举词）
Must Not Change:       L0 00–50 · 90/91 · Frozen Contract · Gate/Admission/Question Core · Production · Preprocessing · Schema · Corpus · Migration
Related Records:       FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md · OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md · Docs/REPORTS/OD-01V4R-FINAL-REMEDIATION-REPORT.md
Supersedes:            —
Superseded By:         —
Gate State Authority:  NO
Registration Level:    NOT REGISTERED
Current Version:       v4R-aligned（唯一 Current）
```

> **Status: NOT RELEASED**（`90 §4:376` / `91 §5:168` 枚举内；对齐先例 `67`）。  
> **CR-002 = Change Proposal Record**  
> **L1: NOT REGISTERED AS L1**（正文短语；不是 Status 字段值）  
> **Registration Level: NOT REGISTERED**  
> **生效语义：** Change candidate exists · Not effective · Not released · Not registered as L1。  
> Authority Level（L2-proposed）≠ Registration Level。

**目录归层：** 位于 `Docs/COORDINATION/`，**未归层**（不在 `90 §1.2` 目录模型；`90:47`：未归层 = 不得引用为权威）。

---

## 0. 注册表述 — 单向、无第二 registry

```text
CR-002 当前：
  Change Proposal Record
  Status: NOT RELEASED
  不生效（not effective）
  NOT REGISTERED AS L1

原因：
  尚未满足正式注册条件（见下四条）。

保留：
  Future registration path（唯一未来注册路径；不创建第二 registry）。
```

Formal L1 registration requires（Planning Category: Future Required Change）:

1. Owner approval  
2. Gate completion  
3. Frozen Spec commit  
4. 90/91 governance registration  

**禁止表述：** 「没有 L1 落点」「无法注册」「已注册 L1」。

---

## 1. Authority Level（冻结枚举）

| 字段 | 值 | 含义 |
|------|-----|------|
| Authority Level | **L2-proposed** | 冻结枚举值（`90 §4:375` / `91 §5:167`） |
| Registration Level | **NOT REGISTERED** | 仅注册状态 |

Owner Decision 记录 = L2。Proposal = L2-proposed。Self Review（REPORTS）= L3。  
**禁止**自创层级。**禁止** `Authority Level = L1`（除非已正式注册）。  
**Planning Category: Future Required Change** — 冻结枚举无法表达「决策/提案/变更记录」三分角色；本轮取最接近冻结值。

---

## 2. Owner Decision 依据

OD-01-A…J = OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE（历史原文；不重写）。  
方向：Artifact-first · Artifact-authoritative · Single provenance authority · No V3 rediscovery · Fail closed。

---

## 3. Change Set（与 Proposal v4R §6–§7 一致）

| Target | CHANGE | Gate |
|--------|--------|------|
| `README.md` §2 术语登记 | CHANGE-2（前置） | Future Required Change |
| `00 §5` | CHANGE-4 | 四道门 |
| `10 §4` | CHANGE-4 | 四道门 |
| `20 §5.3` | CHANGE-5 | 四道门 |
| `20 §5.5` | CHANGE-4+2（与 CI-12 合并全文） | 四道门 |
| `20 §6.1` `§6.2` `§7.2` | CHANGE-2/3 | PENDING |
| `20 §7.3` | CHANGE-1 | PENDING |
| `10 §6.3` `§8` | CHANGE-1/2 | PENDING |
| `50` bbox 行 | CHANGE-2/3 | PENDING |

- 解析字段唯一：**span_resolution**
- form 与 granularity：form=定位空间结构；granularity=解析粒度；M1 同名对偶标签，**非正交**
- offset：Unicode code point
- table_cell identity：**(source_version_id, table_id, row_index, column_index)**；`table_id` 生产来源**必须存在**（当前 Frozen Spec 未定义 → Future Required Change 确立后再写 Spec）
- README §2 须先登记：span_resolution / option_evidence_status / form

**CHANGE-3 / CHANGE-4 / CHANGE-5: ACKNOWLEDGED**（不降级；4/5 须四道门）。

---

## 4. Gate

| Gate | Finding Disposition |
|------|---------------------|
| A | PENDING |
| B | PENDING |
| C | PENDING |
| D | PENDING |

---

## 5. 审查边界

Historical Self Review = 内部检查。DSH Review = 外部验证。  
OD-01-J 只接受 DSH Review 作为外部证据。

---

## 6. 边界

```text
Frozen Spec:     UNCHANGED
Frozen Contract: UNCHANGED
Production:      UNCHANGED
Preprocessing:   UNCHANGED
Schema:          UNCHANGED
Corpus:          UNCHANGED
Migration:       NOT AUTHORIZED
Phase 1:         NOT ENTERED
Re-freeze:       NOT EXECUTED
```

Planning Category: Future Required Change → 正式 L1 登记 · CA-002 · table_id 生产来源 + table_cell identity 对齐 · README §2 术语登记 · Authority Level 角色值域。

---

## 7. Document control（非 Header 规范字段）

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` |
| Authority Level | L2-proposed |
| Registration Level | NOT REGISTERED |
| Status | NOT RELEASED |
| Content Predecessor | CR-002 v2（git 历史；非 Supersedes 文档清单项） |
| Audit ID（非 Header） | CA-002（Planning Category: Future Required Change） |
