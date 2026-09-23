# CONTRACT-CHANGE-RECORD-CR-002-OD-01

```text
Document ID:           CR-002
Title:                 Change Proposal Record — OD-01 Option Provenance
Document Type:         Contract Change Record
Status:                NOT REGISTERED
Purpose:               OD-01 变更跟踪与 L1 注册条件登记（Candidate）；不生效、不注册
Authority Level:       Change Record Authority
Registration Level:    NOT REGISTERED
Normative:             NO
Derives From:          OD-01 · OD-01-A…J · Proposal v4R · P04 · L0 00/10/20/50（只读）· 90/91 §3.1 · 69 §5
May Change:            本 Candidate 文本；与 Proposal v4R 引用一致性；Gate 行（仅 PENDING / VERIFIED）
Must Not Change:       L0 00–50 · 90/91 · Frozen Contract · Gate/Admission/Question Core · Production · Preprocessing · Schema · Corpus · Migration
Related Records:       FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md · OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md
Supersedes:            Previous Revision: CR-002 v2
Superseded By:         —
Gate State Authority:  NO
Change Record ID:      CR-002
Audit ID:              CA-002（Planning Category: Future Required Change）
Date:                  2026-09-23
Current Version:       v4R-aligned（唯一 Current）
Effective:             NOT EFFECTIVE
```

> **CR-002 = Change Proposal Record**  
> **Effective: NOT EFFECTIVE**  
> **L1: NOT REGISTERED**  
> **Registration Level: NOT REGISTERED**  
> **WAITING FOR FOUR-GATE APPROVAL**  
> Authority Level（Change Record Authority）≠ Registration Level。

---

## 0. 注册表述（F-OD01V4R-16）— 单向、无第二 registry

```text
CR-002 当前：
  Change Proposal Record
  NOT EFFECTIVE
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

## 1. Authority Level（F-OD01V4R-18）

| 字段 | 值 | 含义 |
|------|-----|------|
| Authority Level | **Change Record Authority** | 变更记录决策/跟踪权 |
| Registration Level | **NOT REGISTERED** | 仅注册状态 |

Owner Decision = Decision Authority。Proposal = Proposal Authority。**禁止** Authority Level = L1。

---

## 2. Owner Decision 依据

OD-01-A…J = OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE。  
方向：Artifact-first · Artifact-authoritative · Single provenance authority · No V3 rediscovery · Fail closed。

---

## 3. Change Set（与 Proposal v4R §6–§7 一致）

| Target | CHANGE | Gate |
|--------|--------|------|
| `00 §5` | CHANGE-4 | 四道门 |
| `10 §4` | CHANGE-4 | 四道门 |
| `20 §5.3` | CHANGE-5 | 四道门 |
| `20 §5.5` | CHANGE-4+2 | 四道门 |
| `20 §6.1` `§6.2` `§7.2` | CHANGE-2/3 | PENDING |
| `20 §7.3` | CHANGE-1 | PENDING |
| `10 §6.3` `§8` | CHANGE-1/2 | PENDING |
| `50` bbox 行 | CHANGE-2/3 | PENDING |

- 解析字段唯一：**span_resolution**
- form 术语：line_range→line；char_span_in_line→line_character
- offset：Unicode code point
- table_cell identity：**Future Required Change**（requires future Frozen Spec alignment；不声称 table_id 已存在）

**CHANGE-3 / CHANGE-4 / CHANGE-5: ACKNOWLEDGED**（不降级；4/5 须四道门）。

---

## 4. Gate

| Gate | Status |
|------|--------|
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

Planning Category: Future Required Change → 正式 L1 登记 · CA-002 · table_cell identity 对齐。

---

## 7. Document control

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` |
| Authority Level | Change Record Authority |
| Registration Level | NOT REGISTERED |
| Status | NOT REGISTERED |
| Effective | NOT EFFECTIVE |
| Current Version | v4R-aligned |
