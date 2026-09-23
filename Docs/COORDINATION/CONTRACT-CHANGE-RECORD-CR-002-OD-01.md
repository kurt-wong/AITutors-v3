# CONTRACT-CHANGE-RECORD-CR-002-OD-01

```text
Document Type:       Contract Change Record
Authority Level:     L1
Status:              PROPOSED / OWNER AUTHORIZATION REQUIRED / NOT EFFECTIVE
Normative:           YES（对后续 L0 修改流程；对 L0 语义尚未生效）
Supersedes:          —
Superseded By:       —
Gate State Authority: NO
Change Record ID:    CR-002
Audit ID (planned):  CA-002（待 re-freeze 实际改 L0 时在 90 §11 登记）
Date:                2026-09-23
Revision:            v1 — established after F-OD01-01~08 Owner dispositions
```

> **本记录是修改 L0 的唯一入口（`90 R1`）：Contract Change Record。**
> **当前 NOT EFFECTIVE。尚未修改 Frozen Spec。尚未 re-freeze。**
> 未获 Owner Authorization 前，不得执行 L0 文本替换，不得宣称 OD-01 已写入 Frozen Spec。

---

## 0. 状态头（强制字段摘要）

| Field | Value |
|-------|-------|
| Document Type | Contract Change Record |
| Authority Level | L1 |
| Status | **PROPOSED / OWNER AUTHORIZATION REQUIRED / NOT EFFECTIVE** |
| Normative | YES（流程）/ 对 L0 语义 **尚未生效** |
| Supersedes | — |
| Superseded By | — |
| Gate State Authority | NO |

---

## 1. 为什么修改（Why）

1. **P04（Frozen Contract，CLOSED）** 要求 Choice Question 具备 per-option structured evidence：`options[] = {label, text, provenance}`，且 provenance 多态可验证。
2. **现行 Frozen Resolved Span** 具备 `line` / `line_character` + offsets，但**缺少**正式 polymorphic option provenance form（`table_cell` / `multiple_source_spans` / `other`），且 `00 §5` / `20 §5.5` 将 table_cell/fragment 明确延后。
3. **OD-01 Owner Decision** 裁决扩展 Frozen Resolved Span ontology，使 P04 Option Provenance 成为 V3 可表达、可验证的正式形态。
4. **DSH 对抗复核**（VERIFIED WITH FINDINGS，F-OD01-01…08）指出原 Proposal 基线不完整、条款 diff 不全、与 `20 §5.3` 冲突未处置、双 provenance 权威未定义、fail-closed 未钉死、image_region 缺口、L0 修改路径未走 L1、引用错误。Owner 已逐项 ACCEPT 并裁决。
5. 因此必须：**修订 Proposal（已完成）→ 建立本 L1 Change Record → 等待 Owner Authorization → 才能改 L0 → re-freeze**。

**OD-01 不借机改变 Gate、Admission、Question Core 等其他冻结语义。**

---

## 2. 修改哪些 L0 条款（Target）

| # | Target | 现行坐标 | 动作 |
|---|--------|----------|------|
| T1 | `Docs/V3_SPEC/00_Master_Spec.md` §5 非目标（table cell/fragment 字符粒度） | 约 `:274-275` | 部分解除 table_cell option-provenance 子集；fragment 仍延后 |
| T2 | `Docs/V3_SPEC/20_Document_Pipeline.md` §5.3 `option_label` | 约 `:280-281` | **取代**：Producer Artifact = option segmentation 唯一权威 |
| T3 | `Docs/V3_SPEC/20_Document_Pipeline.md` §5.5 Resolved Span + `granularity` | 约 `:308-324` / `:322` | 增加 provenance form 维度；改 table_cell 延后注 |
| T4 | `Docs/V3_SPEC/20_Document_Pipeline.md` §6.1 IR option `source_span` 示例语义 | 约 `:365-369` | 补单链路权威语义；示例 key 以 `sp-Q1-A` 为准 |
| T5 | `Docs/V3_SPEC/20_Document_Pipeline.md` §7.2 步 1 Compiler 提取 | 约 `:454` | 扩展至新 provenance form |
| T6 | `Docs/V3_SPEC/20_Document_Pipeline.md` §7.3 Question `dedup_key` | 约 `:523` | 注释性澄清 option 输入来源；**组合不变** |
| T7 | `Docs/V3_SPEC/10_Data_Model.md` §6.3 `source_span` JSONB | 约 `:458-471` | 划界：仅可验证 provenance 扩展；对齐 `00 §5` JSONB 红线 |
| T8 | `Docs/V3_SPEC/10_Data_Model.md` §8 不变量 2b/2c | 约 `:625-640` | 扩展 locator/hash 核验口径至新 form |

完整 Current → Proposed 文本见 Proposal `FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` **§8 条款级 explicit diff**（本 CR 不复制全文，以该 §8 为唯一 diff 权威文本）。

**明确不修改（UNCHANGED）：**

- Gate 四层既有语义 / Admission 既有语义 / Question Core
- Question / Unit canonical vocabulary；QT→UT 不建立全局映射
- Question `dedup_key` canonical input **组合**（type + own stem + own options + 排除列表）
- P01–P25 其他 Owner Decisions；OD-02 / OD-03 / OD-04 / OD-05 / G-01 / G-02
- Identity：`source_content_sha256` ⊥ `derived_text_hash`
- `options_lines` 保留义务（P04.2）
- 历史数据重新处理原则 / Migration policy / X3 entry condition
- `fragment` 延后本身
- Database Schema / production code / preprocessing implementation / corpus

---

## 3. 修改前是什么（Before）

| 项 | Before |
|----|--------|
| Resolved Span form | 无 polymorphic provenance form 维度；`granularity ∈ {line, line_character}`；table_cell/fragment 延后 |
| 字符级能力 | **已有** `line_character` + `start_offset`/`end_offset`（「单行多选项」） |
| option 边界 | `20 §5.3`：V3 Resolver 按 A/B/C/D 顺序切 option |
| option provenance 双表征 | Producer `options[]`（P04）与 IR `content.options[label].source_span` **权威关系未定义** |
| fail-closed | P04.4 要求 `unresolved`/`INCOMPLETE`/`QC_FAIL`；Proposal v1 曾并存 `options_unresolved` 与 `0..n` 歧义 |
| image_region | 无承载说明 |
| Example span_id | v1 误写 `sp-<unit>.option.<label>` 为 Spec 示例 |
| L0 修改路径 | 未建立 L1 Contract Change Record；未按 `90 §3` 分类 |

---

## 4. 修改后是什么（After）

| 项 | After（本 CR 提议；**尚未写入 L0**） |
|----|--------------------------------------|
| Resolved Span form | 增加 form ∈ `{line_range, char_span_in_line, table_cell, multiple_source_spans, other}` |
| char_span_in_line | **映射**既有 `line_character`+offset；非第二坐标系 |
| table_cell | option-provenance 子集解除延后；完整文档级表格索引仍非目标 |
| fragment | **仍延后** |
| image_region | `other` 的正式实例：`form=other, method=image_region`（非顶级 type） |
| option 边界 | **Producer Artifact = option segmentation 唯一权威**；V3 只验证/规范化/拒绝/fail closed；**禁止 rediscovery** |
| `20 §5.3` | 原 V3 切 option 规则 **被取代**（无 fallback） |
| provenance 链路 | `options[].provenance`（Producer 证据）→ V3 verification/normalization → Frozen Resolved Span → IR `options["A"].source_span`；**单一 authority path** |
| 冲突 | 不得静默覆盖；保留 conflict signal；走 review / unresolved / fail-closed |
| fail-closed | option `resolution_status ∈ {resolved, unresolved, incomplete}` + QC 层 `QC_FAIL`；**废止独立 `options_unresolved` 语义字段**；resolved ⇒ provenance **1..n**；禁止 0-span 静默通过 |
| Example key | 规范示例 `sp-Q1-A`（`20 §6.1`）；代码构造名不得回写为 Spec |

---

## 5. 哪些语义保持不变（Invariants）

- Gate 四层 / Admission / Question Core / canonical vocabulary / QT→UT
- Question `dedup_key` 组合与 identity 语义
- `text_hash = SHA256(text.encode("utf-8"))`；no double consumption
- `options_lines` 必须保留
- Historical Source Reprocessing Principle（历史不 patch、不迁移、不兼容推导）
- 不新增 Question Type / Unit Type / Admission-required fields
- 不建立第二 semantic authority path（OD-04 对齐）
- P04 契约条文本身不改（语义落入 L0）

---

## 6. Change Classification（`90 §3`）

| 成分 | Class | 说明 |
|------|-------|------|
| 新增 polymorphic provenance form 维度 | CHANGE-2 Normative Addition | 新增强制可表达/可验证约束 |
| `options[]` 结构语义落入 L0 | CHANGE-2 | 新增强制 invariant |
| 废止/改写 `00 §5` table_cell 延后非目标 | **CHANGE-3** | 改变既有规定的行为/范围 |
| 改 `20 §5.5` 延后注 / form 范围 | **CHANGE-3** | 改变既有规定 |
| 改 `20 §5.3` option 边界规则 | **CHANGE-3** | 改变既有规定的行为 |
| 改 `20 §7.2` Compiler 提取规则 | **CHANGE-3** | 改变既有规定的行为 |
| `dedup_key` 输入来源澄清 | CHANGE-1 Clarification | 组合不变 |
| 引用更正 | CHANGE-0/1 | 编辑/澄清 |

**总体分类：CHANGE-3 — Normative Modification**

判定依据：含多项「改变既有规定的行为」；按 `90 §3`「**拿不准往高里归**」，不得只按 CHANGE-2。

**CHANGE-3 要求：Change Record + 受影响层回归。** 回归义务已登记（§8）；**本轮不执行回归**（实现未授权）。

四道门（`69 §5`）：本变更 **不是** CHANGE-4/5，**不需要**四道门。但 **需要 Owner Authorization** 后方可改 L0（本 CR 流程门）。

---

## 7. Affected Layers（受影响层）

| Layer | 受影响 | 回归要求 |
|-------|--------|----------|
| **L0 Frozen Spec** `00` / `20` / `10`（§2 所列条款） | YES | 条款一致性 + 见 §8 |
| L0-META `90` §11 Change Audit | 流程 | re-freeze 时登记 CA-002 |
| Frozen Contract P04 | 语义落入；条文不改 | 无契约文本回归 |
| Consumer Boundary / Resolved Span / IRBuilder / Compiler / Gate **Provenance 能力** | YES（能力扩展） | §8 全项 |
| Gate Structural / Semantic / Admission **语义** | NO | 禁止改动；负向确认测试 |
| Database Schema | NO | 禁止 migration |
| Preprocessing implementation | NO（本阶段） | 实现另令 |
| Production code | NO | 禁止 |
| Corpus | NO | 禁止重跑 |

---

## 8. Regression Requirements（受影响层回归范围）

> **义务登记于本 CR；执行前提是 Owner Authorization + re-freeze 完成 + 实现授权。**
> **本轮不执行任何回归测试。**

1. Resolved Span 构造/解析/验证（全部 form + legacy 无 form 读取）
2. `char_span_in_line` ↔ `line_character`+offset 一致性与编码单位
3. `table_cell` 可回溯 raw 与 fail closed
4. `multiple_source_spans` 有序 non-empty 与逐 span `10 §8` 2b/2c
5. `other` / `image_region`：figure identity + region + degraded/unresolved
6. option segmentation：仅消费 Producer `options[]`；**禁 rediscovery 负向测试**
7. fail-closed：`unresolved` / `incomplete` / `QC_FAIL`；resolved ⇒ provenance 1..n；禁止 0-span 静默通过；禁止独立 `options_unresolved` 复活
8. conflict signal：Producer provenance vs V3 验证冲突 → 保留信号、不静默覆盖、不进 ready
9. Compiler option leaf 提取 + `text_hash`（`10 §8` 2c）
10. Gate Provenance form/locator/text 校验 + no double consumption 交互
11. Question `dedup_key`：组合不变；输入来自 verified Producer options
12. `options_lines` 与 `options[]` 并存保留
13. 负向：不得新增 Gate condition / Admission 条件（OD-03/P14 边界）

---

## 9. Formal Chain 与当前停止点

```text
OD-01 Owner Decision                          [DONE]
        ↓
OD-01 Frozen Spec Change Proposal v2          [DONE — revised after F-OD01-01~08]
        ↓
L1 Contract Change Record (CR-002)            [THIS DOCUMENT — CREATED]
        ↓
Owner Authorization                           [REQUIRED — NOT GRANTED]
        ↓
L0 Frozen Spec modification                   [NOT EXECUTED]
        ↓
re-freeze                                     [NOT EXECUTED]
```

**本次任务只完成到：L1 Change Record 已建立并准备进入 Owner Authorization。**

---

## 10. Owner Authorization 状态

| Item | Status |
|------|--------|
| Owner decisions OD-01 + F-OD01-01…08 | ACCEPTED / 已裁决 |
| Proposal v2（含 §8 explicit diff） | READY FOR REVIEW |
| CR-002 本记录 | READY FOR AUTHORIZATION |
| **Owner Authorization to modify L0** | **REQUIRED — NOT GRANTED** |
| Freeze Order / re-freeze | **NOT ISSUED / NOT DONE** |
| 当前是否已生效 | **NOT EFFECTIVE** |

### 待 Owner 勾选（与 Proposal §13 对齐）

```text
[ ] A. Authorize CR-002 as the L1 entry for OD-01 (CHANGE-3 overall)
[ ] B. Approve Target list T1–T8 and §8 explicit diff texts (or amend)
[ ] C. Confirm UNCHANGED list (§2 / §5)
[ ] D. Approve regression scope §8 (execution still gated by implementation auth)
[ ] E. Pin remaining technical choices (Proposal §13 #2–#6: encoding unit,
       table_cell locator, legacy reading rule, JSONB/DDL text, Gate validation depth)
[ ] F. Issue explicit Freeze Order for re-freeze change set
[ ] G. Plan 90 §11 CA-002 registration at actual L0 commit time
```

全部勾选并下达 Freeze Order 前：

```text
CR-002                 = PROPOSED / OWNER AUTHORIZATION REQUIRED / NOT EFFECTIVE
OD-01 as Frozen Spec   = NOT EFFECTIVE
Frozen Spec            = UNCHANGED
Production Code        = UNCHANGED
Schema                 = UNCHANGED
Corpus                 = UNCHANGED
Re-freeze              = NOT EXECUTED
Phase 1                = NOT ENTERED
```

---

## 11. Evidence / References

| Ref | Path / ID |
|-----|-----------|
| OD-01 Owner Decision | `Docs/COORDINATION/OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md` §OD-01 |
| F-OD01-01…08 dispositions | Owner ACCEPT（任务书）+ Proposal §0 |
| Proposal v2 + explicit diff | `Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` |
| DSH adversarial review | `AITutor-X/Docs/60_REPORTS/OD-01-FROZEN-SPEC-PROPOSAL-DSH-ADVERSARIAL-REVIEW.md` |
| L0-META | `Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md` R1/R2/§3/§4/§11 |
| Frozen Contract P04 | `PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` §P04 |
| Effective Frozen Spec tree | `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`（unchanged） |
| Prior CR 先例 | `90` CR-001（CHANGE-2，40 §5） |

---

## 12. 显式不主张

1. **不主张**本 CR 已获 Owner Authorization。
2. **不主张** L0 文本已修改或已 re-freeze。
3. **不主张** OD-01 已是生效 Frozen Spec。
4. **不主张**可以开始 Phase 1 / implementation / schema change / corpus rerun / migration。
5. **不主张**修改 Gate / Admission / Question Core。
6. **不主张** `90 §11` CA-002 已完成登记（登记绑定未来 L0 commit）。

---

## 13. Document control

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` |
| Change Record ID | CR-002 |
| Target | L0 `00_Master_Spec.md` / `20_Document_Pipeline.md` / `10_Data_Model.md`（条款见 §2） |
| Change Class | **CHANGE-3 — Normative Modification**（overall；含 CHANGE-2/1 成分） |
| Source Proposal | `FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` v2 |
| Audit ID | CA-002（planned；re-freeze 时登记） |
| Date | 2026-09-23 |
| Owner Authorization | **REQUIRED / NOT GRANTED** |
| Effective | **NOT EFFECTIVE** |
| Frozen Spec | **UNCHANGED** |
