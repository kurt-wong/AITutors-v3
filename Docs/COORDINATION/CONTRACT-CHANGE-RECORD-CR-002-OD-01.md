# CONTRACT-CHANGE-RECORD-CR-002-OD-01

```text
Document ID:           CR-002
Title:                 Change Proposal Record — OD-01 Option Provenance
Document Type:         Contract Change Record（Candidate）
Status:                NOT RELEASED
Authority Level:       CR — registration / change tracking authority
Registration Level:    Pending L1 Registration
Normative:             NO
Derived From:          OD-01 · OD-01-A…J · Proposal v4R · P04 · L0 00/10/20/50（只读）· 90/91 · 69 §5
May Change:            本 Candidate 文本；与 Proposal v4R 引用一致性；Gate 行（仅有证据时用 VERIFIED/PENDING）
Must Not Change:       L0 00–50 · 90/91 · Frozen Contract · Gate/Admission/Question Core · Production · Preprocessing · Schema · Corpus · Migration
Related Records:       FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md · OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md
Supersedes:            CR-002 v2
Superseded By:         —
Gate State Authority:  NO
Change Record ID:      CR-002
Audit ID (planned):    CA-002（Future Required Change；绑定 Frozen Spec commit）
Date:                  2026-09-23
```

> **CR-002 = Change Proposal Record**  
> **Effective: NOT EFFECTIVE**  
> **L1: NOT REGISTERED**  
> **WAITING FOR FOUR-GATE APPROVAL**  
> **Location: `Docs/COORDINATION/`**（OD-01-C）  
> Authority Level ≠ Registration Level。

---

## 0. 定位（F-OD01V4R-06 / R-03 / R-05）

| 字段 | 值 | 含义 |
|------|-----|------|
| Authority Level | CR — registration / change tracking authority | 变更跟踪 |
| Registration Level | Pending L1 Registration | 仅 L1 进度跟踪 |
| Effective | NOT EFFECTIVE | 未生效 |
| L1 | NOT REGISTERED | 未注册 |

**Formal L1 registration requires:**

1. Owner approval  
2. Gate completion  
3. Frozen Spec commit  
4. 90/91 governance registration  

```text
Current status: Candidate only.
Registration is intentionally deferred until:
  Owner approval + Gate completion + Frozen Spec update.
Valid future registration path.
```

---

## 1. Owner Decision 依据

OD-01-A…J = OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE。  
核心方向不变：Artifact-first · Artifact-authoritative · Single provenance authority · No V3 rediscovery · Fail closed。

---

## 2. Change Set

权威文本 = Proposal v4R **§7 CI-1…CI-12 + §8 Appendix**。

| Target | CHANGE | Gate |
|--------|--------|------|
| `00 §5` | **CHANGE-4** | 四道门 |
| `10 §4` | **CHANGE-4** | 四道门 |
| `20 §5.3` | **CHANGE-5** | **四道门** |
| `20 §5.5` | **CHANGE-4+2** | **四道门** |
| `20 §6.1` `§6.2` `§7.2` | CHANGE-2/3 | PENDING |
| `20 §7.3` | CHANGE-1 | PENDING |
| `10 §6.3` `§8` | CHANGE-1/2 | PENDING |
| `50` bbox 行 | CHANGE-2/3 | PENDING |

**命名统一（F-OD01V4R-05）：** 解析字段唯一 = **`span_resolution`**（与 `option_evidence_status` / `answer_status` 分离）。  
**定位（F-OD01V4R-04）：** line→line_ref 必需；line_character→line_ref+offset 必需；table_cell→table identity 必需、line_ref 可选；multiple_source_spans→多 entry 必需；other→显式描述必需。  
**offset（F-OD01V4R-10）：** Unicode code point；0-based；start inclusive；end exclusive。  
**table_cell（F-OD01V4R-09）：** `(source_version_id, table_id, row_index, col_index)`，1-based row/col。

**UNCHANGED：** Gate/Admission/Question Core/词汇/dedup 组合/P01–P25/fragment 延后/**降级态不引入**/Schema/代码/Corpus/Preprocessing。

---

## 3. CHANGE-3 / CHANGE-4 / CHANGE-5（不降级）

```text
CHANGE-3: ACKNOWLEDGED
CHANGE-4: ACKNOWLEDGED — four-gate required
CHANGE-5: ACKNOWLEDGED — four-gate required
```

| 项 | 实际变化 | CHANGE |
|----|----------|--------|
| `00 §5` / `10 §4` | 约束放宽 | **CHANGE-4** |
| `20 §5.3` | 规则删除/替换 | **CHANGE-5** |
| `20 §5.5` | 延后放宽 + form | **CHANGE-4**（+2） |

---

## 4. 三路径

Native + Adapter + Artifact → Unified Provenance Model → Canonical V3 IR。  
Artifact provenance 不替代 Native authority；消费层禁止第二 semantic authority。

---

## 5. Gate

| Gate | Status |
|------|--------|
| A | PENDING |
| B | PENDING |
| C | PENDING |
| D | PENDING |

**WAITING FOR FOUR-GATE APPROVAL。**

---

## 6. 审查边界（F-OD01V4R-01）

Self Review = 内部检查。  
DSH Review = 外部验证。  
OD-01-J 证据链仅接受 **DSH Review**；不得引用 Self Review 报告作为 DSH 证据。

---

## 7. 边界

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
CR-002:          NOT EFFECTIVE / NOT REGISTERED
```

**Future Required Change：** 正式 L1 落位 `Docs/V3_SPEC/`；CA-002 登记 — 均在 Owner approval + Gates + Frozen Spec commit 之后。

---

## 8. Document control

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` |
| Authority Level | CR — registration / change tracking authority |
| Registration Level | Pending L1 Registration |
| Status | NOT RELEASED |
| Change Class | CHANGE-3 + CHANGE-4 + CHANGE-5 |
| Effective | NOT EFFECTIVE |
