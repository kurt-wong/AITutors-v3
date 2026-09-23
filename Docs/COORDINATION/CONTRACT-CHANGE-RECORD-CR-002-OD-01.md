# CONTRACT-CHANGE-RECORD-CR-002-OD-01

```text
Document ID:           CR-002
Title:                 Change Proposal Record — OD-01 Option Provenance / Unified Provenance Model
Document Type:         Contract Change Record（候选）
Authority:             Owner Decision / Proposal Record
Registration Level:    Pending L1 Registration
Status:                NOT RELEASED
Normative:             NO
Purpose:               OD-01 的 Change Proposal Record（Candidate）；登记 CHANGE-3/4/5、Gate、注册条件与授权边界
Derives From:          OD-01 · OD-01-A…J · OD-01R-01…10 · Proposal v4 · P04 · L0 00/10/20/50（只读）· 90/91 · 69 §5
May Change:            本 Candidate 文本；与 Proposal v4 引用一致性；Gate evidence/status（仅有证据时）
Must Not Change:       L0 00–50 · 90/91 · Frozen Contract / P01–P25 · Gate/Admission/Question Core · Production · Preprocessing · Schema · Corpus
Supersedes:            CR-002 v2
Superseded By:         —
Gate State Authority:  NO
Change Record ID:      CR-002
Audit ID (planned):    CA-002（仅在 Frozen Spec commit 后按 90 §11 登记）
Date:                  2026-09-23
```

> **CR-002 = Change Proposal Record**
> **NOT EFFECTIVE**
> **NOT REGISTERED AS L1**
> **WAITING FOR FOUR-GATE APPROVAL**
> **LOCATION: `Docs/COORDINATION/`**（OD-01-C：不进入 Frozen Spec）
>
> 不得将本文件表述为「已是正式 L1」「已注册 L1」「已生效」「可据此修改 L0」。

---

## 0. 定位声明（R-03 / R-10 / OD-01-C）

| 项 | 表述 |
|----|------|
| 文件性质 | **Change Proposal Record**（Candidate） |
| Authority | **Owner Decision / Proposal Record**（非「Authority Level: L1」） |
| Registration Level | **Pending L1 Registration** |
| Effect | **NOT EFFECTIVE** |
| L1 注册 | **NOT REGISTERED AS L1** |
| 流程位置 | **WAITING FOR FOUR-GATE APPROVAL** |
| 落点 | 保持 **COORDINATION**；**不**写入 `Docs/V3_SPEC/**` |

**Formal L1 registration requires:**

1. **Owner approval**
2. **Gate completion**（四道门，`69 §5`）
3. **Frozen Spec commit**
4. **90/91 governance registration**

```text
Current status: Candidate only.
Registration is intentionally deferred until:
  Owner approval +
  Gate completion +
  Frozen Spec update.
CR-002 has a valid future registration path.
```

（修正 v3「Governance Gap / 无合法落点」表述：**不是**没有落点，而是 **当前不注册**，因 Frozen Spec 尚未修改且四道门未完成。）

---

## 1. Why

1. P04 要求 Choice Question per-option structured evidence。
2. L0 缺 polymorphic option provenance form；`00 §5` / `10 §4` / `20 §5.5` 延后 table_cell/fragment。
3. OD-01 扩展统一 provenance 模型；OD-01-A…J 为 OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE。
4. OD-01V3 findings 要求恢复完整 diff、修正 CR-002 定位、状态词与路径说明。

**不改变** Gate / Admission / Question Core 等其他冻结语义。

---

## 2. Owner Decision 依据（PENDING EFFECTIVE FREEZE）

| ID | Decision | Action |
|----|----------|--------|
| OD-01-A | APPROVED | 恢复逐条 Frozen Text 级 diff |
| OD-01-B | APPROVED | 保留缺口基线（现有/真缺口/延后/非目标） |
| OD-01-C | APPROVED | CR-002 保持 COORDINATION；NOT EFFECTIVE / Candidate |
| OD-01-D | APPROVED | CHANGE-3/4/5 全部承认；四道门 |
| OD-01-E | APPROVED | Native / Adapter / Artifact 统一 provenance 模型 |
| OD-01-F | APPROVED | **暂不新增 degraded**；不完整 → unresolved / review |
| OD-01-G | APPROVED | 拆分 resolution 命名，避免 option / answer 同名冲突 |
| OD-01-H | APPROVED | 删除 `DONE` 状态词 |
| OD-01-I | APPROVED | OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE |
| OD-01-J | APPROVED | 当前不 re-freeze；v4 → DSH 复核 → Owner 批准 → re-freeze |

---

## 3. Change Set 范围

权威文本 = **Proposal v4 §4 CI-1…CI-12 + §5 Explicit Diff Appendix**。

| Target | CHANGE | Gate |
|--------|--------|------|
| `00 §5` table/fragment 非目标 | **CHANGE-4** | 四道门 |
| `10 §4` `_cells` 裁剪注 | **CHANGE-4** | 四道门 |
| `20 §5.3` option 边界规则 | **CHANGE-5** | **四道门** |
| `20 §5.5` form / 延后 | **CHANGE-4 + CHANGE-2** | 四道门 |
| `20 §6.1` / `§6.2` / `§7.2` | CHANGE-2/3 | 回归 |
| `20 §7.3` dedup | CHANGE-1 | 回归 |
| `10 §6.3` / `§8` | CHANGE-1/2 | 回归 / 联动 |
| `50` bbox 能力行（`50_Migration_Assets.md`） | CHANGE-2/3 | 回归 |

**UNCHANGED：** Gate 语义 · Admission · Question Core · 词汇 · dedup 组合 · P01–P25 · OD-02…G-02 · fragment 延后 · **degraded** · Schema · 代码 · Corpus · Preprocessing。

---

## 4. CHANGE-3 / CHANGE-4 / CHANGE-5（OD-01-D）

```text
CHANGE-3: ACKNOWLEDGED — Compiler 提取、状态分层、path-aware 行为等
CHANGE-4: ACKNOWLEDGED — 00 §5 / 10 §4 / 20 §5.5 约束放宽 — four-gate required
CHANGE-5: ACKNOWLEDGED — 20 §5.3 无条件 V3 option 边界规则删除/替换 — four-gate required
```

| 项 | 原 | 新 | 实际变化 | CHANGE |
|----|----|----|----------|--------|
| `00 §5` | table/fragment 非目标 | option table_cell 子集解除 | **放宽** | **CHANGE-4** |
| `10 §4` | `_cells` 等不建 | option table_cell 定位允许 | **放宽** | **CHANGE-4** |
| `20 §5.3` | V3 无条件发现 option 边界 | Artifact=Producer；Native=首次解析；禁第二 authority | **删除/替换** | **CHANGE-5** |
| `20 §5.5` | table_cell/fragment 延后 | option 子集解除 + form | **放宽 + 新增** | **CHANGE-4**（+2） |

**禁止**「不是 CHANGE-4/5 所以免四道门」。

---

## 5. 三路径（OD-01-E）

```text
Native  + Adapter  + Artifact
        ↓
Unified Provenance Model
        ↓
Canonical V3 IR → Gate / Admission
```

- Artifact provenance **不替代** Native path authority。
- V3 consumption layer **不得**建立第二 semantic authority。
- 三路径必须产出 **语义等价** 的统一 provenance 表示。

---

## 6. Fail-closed / 状态（OD-01-F/G）

| 命名 | 用途 |
|------|------|
| `span_resolution`（ResolvedStatus） | provenance/span 解析 |
| `option_evidence_status` | option 证据可用性 `{resolved, unresolved, incomplete}` |
| `answer_status` | 答案结论三字段 |
| `semantic_status` | IR 完备性 |

- **不新增 degraded**（OD-01-F）。
- 不完整 → `unresolved` / `incomplete` / review；禁止静默通过；禁止 `options_unresolved` 并行位。

---

## 7. Gate（四道门）— PENDING

| Gate | Requirement | Status |
|------|-------------|--------|
| A Identity Closure | identity 闭合 | **PENDING** |
| B Legacy / Path 对比 | corpus 对比 | **PENDING** |
| C Safety Invariant | C1–C6 | **PENDING** |
| D Adapter Boundary | 非第二 Resolver | **PENDING** |

**WAITING FOR FOUR-GATE APPROVAL。** 不得以 Proposal 完成或 DESIGN APPROVED 替代 Gate PASS。

---

## 8. 未授权事项

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
Push (L0):       NOT EXECUTED
CR-002:          NOT EFFECTIVE / NOT REGISTERED AS L1
```

**显式不主张：** 已注册 L1 · 已生效 · 四道门已通过 · 可改 L0 · 可 Phase 1 · CA-002 已登记。

---

## 9. Document control

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` |
| Kind | Change Proposal Record |
| Authority | Owner Decision / Proposal Record |
| Registration Level | Pending L1 Registration |
| Status | NOT RELEASED |
| Change Class | **CHANGE-3 + CHANGE-4 + CHANGE-5**（并含 1/2） |
| Source | Proposal **v4** |
| Effective | **NOT EFFECTIVE** |
| Location | COORDINATION（OD-01-C） |
