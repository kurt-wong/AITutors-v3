# FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE

```text
STATUS: PROPOSAL — PENDING OWNER REVIEW
AUTHORITY: FROZEN SPEC CHANGE PROPOSAL (NOT YET EFFECTIVE)
PURPOSE: OD-01 incorporation into Frozen Resolved Span ontology
OWNER-DECISION: OD-01 APPROVED (design)
FROZEN-SPEC-INCORPORATION: PENDING
RE-FREEZE: NOT DONE
```

> **这是 Proposal，不是已生效的 Frozen Spec 修改。**
> 没有 Owner 后续明确 Freeze Order / re-freeze，不得把它标成已经修改 Frozen Spec。
> 当前生效 Frozen Spec 仍为 `Docs/V3_SPEC/**` @ tree `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`（unchanged）。

**Related:** `OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md` · Frozen Contract P04 · `Docs/V3_SPEC/20_Document_Pipeline.md` Resolved Span · `Docs/V3_SPEC/10_Data_Model.md`

---

## 1. Problem

P04（Frozen Contract，CLOSED）要求 Choice Question 具备正式 per-option 结构化证据：

```text
options[] = { label, text, provenance }
```

且 provenance 必须是 **polymorphic** 且 **可验证**，至少能表达：

- `line_range`
- `char_span_in_line`
- `table_cell`
- `multiple_source_spans`
- other verifiable source provenance

**Current Frozen Resolved Span ontology**（`20_Document_Pipeline.md` / `10_Data_Model.md`）以 line-span / role span 为中心，**不能完整表达** P04 的 polymorphic option provenance（尤其 `char_span_in_line`、`table_cell`、`multiple_source_spans`）。

因此 OD-01 裁决：**扩展 Frozen Resolved Span** — 属 Frozen Spec Change，必须走 Proposal → Owner review → re-freeze。

---

## 2. Current Frozen Semantics

（生效中；本 Proposal **不修改** 下列文本。）

### 2.1 Resolved Span（现状摘要）

| Aspect | Current Frozen semantics |
|--------|--------------------------|
| Primary granularity | Source line / line range（OCR/markdown 行） |
| Role spans | `stem` / `options` / `answer` / `explanation` 等 content role 的 span |
| Option granularity | `options` 为整区 role span；label 在 `instance_role_contents.label`（options only） |
| Provenance verification | exact / normalized + `text_hash == SHA256(raw text)`；禁止 double span consumption |
| Example keys | `sp-<unit>.option.<label>`（IR 示例中的 role key） |
| Storage | `instance_role_contents.source_span` JSONB（可承载扩展，但 ontology 未定义多态类型） |

### 2.2 相关不变式（保持不变）

- `text_hash = SHA256(text.encode("utf-8"))`（P23 关联但独立于 `source_content_sha256`）
- Gate Provenance 层：exact/normalized + hash 一致 + no double consumption
- `content_roles`：`options` = `required_for_choice` for single_choice/multiple_choice/true_false
- Question Core 不因 provenance 扩展而改变
- P04.2：`options_lines` 必须保留（Producer 侧已要求；Consumer 不得删除）

---

## 3. Owner Decision（OD-01）

**扩展 Frozen Resolved Span ontology**，使 P04 Option Provenance 成为正式 V3 可表达、可验证的 provenance 形态。

必须支持至少：

```text
line_range
char_span_in_line
table_cell
multiple_source_spans
other verifiable source provenance
```

强制（binding）：

1. `options[]` = `label` + `text` + `provenance`
2. `options_lines` 不得删除
3. 禁止假设「一个 option = 一行」或「一个 option = 一个 span」
4. Table Cell 必须可表达
5. Multiple Source Spans 必须可表达
6. 不可靠 → explicit `unresolved` / `QC_FAIL` / `INCOMPLETE`，不得猜测
7. V3 不得用 LLM 猜测 Option 边界代替 Preprocessing evidence

字段命名可由本 Proposal 建议，**语义不得改变**。

---

## 4. Required New Semantics（Proposed）

### 4.1 Ontology：`ResolvedSpan` polymorphic forms（PROPOSED）

在 Frozen Resolved Span 语义层增加 **provenance form** 维度（不改变 identity/hash 不变式）：

| Form | Proposed name（建议名） | Required payload | Notes |
|------|-------------------------|------------------|-------|
| Line range | `line_range` | `start_line`, `end_line`（1-based closed） | 兼容现有 line span |
| Char span in line | `char_span_in_line` | `line`, `start_char`, `end_char`（编码稳定；UTF-8 code unit 或 Unicode scalar — **re-freeze 时必须钉死一种**） | 切开同行内 A/B/C/D |
| Table cell | `table_cell` | 可验证 cell 坐标（如 `table_span` + `row`, `col` 或 HTML cell identity + 可回溯 raw） | 选项在表格内 |
| Multiple source spans | `multiple_source_spans` | `spans[]` = 有序 non-empty 列表，元素为其他 form | 选项跨多行/多块 |
| Other verifiable | `other` | `method` + `locator` + 可独立验证的回溯信息 | 禁止不可验证 free-form |

**每个 option 的 `provenance` 应为 form 列表（0..n 显式结构；不可靠时整体 `unresolved`，不得 0-span 静默通过）。**

### 4.2 `options[]`（PROPOSED logical shape；非最终 DDL）

```text
options: [
  {
    label: string,          # e.g. "A"
    text: string,           # option text (source-grounded)
    provenance: [           # polymorphic, one or more
      { form: "line_range" | "char_span_in_line" | "table_cell"
        | "multiple_source_spans" | "other", ...form fields }
    ]
  }
]
# 或整体：
options_unresolved: true   # 当无法可靠形成 options[] 时
options_lines: [start,end] | null   # MUST KEEP（P04.2）
```

### 4.3 Verification rules（PROPOSED）

- 每个 provenance form 必须可映射回 Original Source 且可独立验证（与 P04.3 / P22 精神一致）。
- Gate Provenance 层扩展校验：form 合法 + locator 可解析 + text 与 locator 内容一致（normalized 级规则可后续细化）+ 不与其他已消费 span 冲突（沿用 no double consumption）。
- **不可靠 → fail closed**：`unresolved` / `INCOMPLETE` / `QC_FAIL`；禁止 silent fallback、禁止 partial fabricate。

### 4.4 Canonical semantics that remain UNCHANGED（explicit）

- Question Type / Unit Type 闭集不变
- `standalone_unit` / `composite_unit` 词汇不变；**不引入 `Standalone Question`**
- Admission 公式不变：Core + Frozen required + Identity/Evidence/Gate
- P01–P25 不变（P04 仍是 CLOSED 决策；本 Proposal 只是把 P04 语义落入 Frozen Resolved Span）
- Identity：`source_content_sha256` ⊥ `derived_text_hash`（P23）不变
- LLM-derived Metadata / Post-Admission Enrichment 边界不变
- `options_lines` 保留义务不变

---

## 5. Ontology Changes（summary）

| Change | Type |
|--------|------|
| Resolved Span gains polymorphic provenance forms | **ADD** ontology dimension |
| `line_range` remains valid form | **KEEP** (alias/absorb current line spans) |
| `char_span_in_line` / `table_cell` / `multiple_source_spans` / `other` | **ADD** |
| Option-level `options[]{label,text,provenance}` | **ADD** logical structure (P04) |
| `options_lines` | **KEEP mandatory** |
| Existing role spans / text_hash / source_content_sha256 | **UNCHANGED** |
| New Question Type / Unit Type | **NONE** |
| New Admission-required fields | **NONE**（provenance 扩展不升格 metadata 为 Admission 条件） |

---

## 6. Affected Components

| Component | Repo | Impact |
|-----------|------|--------|
| Preprocessing prompt / parser / validation | Aitutors-preprocessing | 产出 `options[]` + polymorphic provenance（Producer-side 可扩展 — OD-05） |
| Preprocessing Resolver IR | Aitutors-preprocessing | 拷贝 `options[]` / 保留 `options_lines` |
| Consumer Boundary / annotation adapter | AITutors-v3 | 消费 `options[]`；禁止 rediscovery |
| `ResolvedSpan` / `source_span` 消费 | AITutors-v3 | 解析 polymorphic forms |
| `IRBuilder` / `Compiler` | AITutors-v3 | option leaf 绑定 provenance |
| Gate Provenance 层 | AITutors-v3 | 校验 form/locator/text（**不新增 Gate condition 语义**；仅为已有 Provenance 层补齐能力） |
| `InstanceRoleContent.source_span` | AITutors-v3 | 可承载扩展 JSON；**DDL 是否变更待 Owner**（见 Compatibility） |
| Tests | both | 见 §8 |

---

## 7. Compatibility Impact

| Area | Impact | Assessment |
|------|--------|------------|
| Existing line-only spans | 仍可表示为 `line_range` | **Backward compatible**（语义上兼容） |
| Existing `source_span` JSONB | 可写入扩展 form；旧数据无 form 字段 | **Need explicit legacy reading rule**（建议：无 form = `line_range` 解释）— 待 Owner 确认 |
| Existing Resolved Span consumers | 必须识别 form；未知 form → fail closed | **Behavioral change** on malformed/unknown |
| Producer old artifacts | 无 `options[]` | **NOT patched**（Historical Source Reprocessing Principle）；重跑获得新 Artifact |
| `options_lines` | 必须保留 | **No break** |
| Canonical vocabulary | 不变 | **No break** |
| Question Core fields | 不变 | **No break** |
| Frozen `10_Data_Model` DDL 文本 | 若需正式新增列/注释 ontology | **Frozen Spec text change = this proposal**；非 DB migration 自动授权 |

**Migration Impact：** 本 Proposal **不授权** DB migration、corpus rewrite、artifact patch。历史路径仍为 Original Source → Current Preprocessing。

---

## 8. Test Impact（required after re-freeze）

**Preprocessing:**

- 正常 option extraction（`options[]` + `options_lines` 并存）
- 多行 option（`multiple_source_spans` / 跨行 `line_range`）
- 表格 option（`table_cell`）
- character-span provenance（`char_span_in_line`）
- 无法可靠识别 → `unresolved` / fail closed
- malformed option → 拒绝
- 禁止 silent fallback
- label/text/provenance 可验证

**V3:**

- 消费 polymorphic provenance 各 form
- **禁止 V3 rediscovery**（不得从 `options_lines` 自行切 option）
- 未知 form / 坏 locator → fail closed
- 与 text_hash / double-consumption 规则交互
- 旧 line-only span 兼容读取（若 Owner 批准 legacy rule）

---

## 9. Gate / Compiler / IR Impact

| Layer | Impact |
|-------|--------|
| **IR** | option 节点携带 polymorphic provenance；`options_lines` region 并存 |
| **Compiler** | option leaf text + label 来自 Preprocessing `options[]`；provenance 进入 compiled source_span |
| **Gate Structural** | 无新 Question Type/Unit Type；choice 类型仍要求 options 完整 |
| **Gate Provenance** | 扩展校验 form 合法性与 locator 可验证性；**不把 flags 变成 Gate condition**（P14） |
| **Gate Semantic / Admission** | **无语义变更**（不因 provenance 扩展新增 Admission 条件） |
| **Authority** | 不建立新 Authority；Preprocessing structural/evidence 与 V3D 边界不变 |

---

## 10. Migration Impact

```text
NOT AUTHORIZED in this Proposal.
```

- 不改 DB migration
- 不 patch historical artifacts
- 不做 V3 compat derivation
- 历史 Choice 无 per-option 证据 → Historical Source Reprocessing（需单独执行令）

---

## 11. Risk

| Risk | Level | Mitigation |
|------|-------|------------|
| char offset 编码定义不一致（UTF-8 byte vs codepoint） | **HIGH** | re-freeze 时必须钉死一种并写入 Frozen 文本 |
| table_cell 坐标在 OCR/HTML 转换后不稳定 | **HIGH** | 要求 cell identity 可回溯 raw；否则 `unresolved` |
| Consumer 误把 line-only legacy span 当多态 | MED | 显式 legacy reading rule + fail closed on unknown form |
| 实现方把 provenance 扩展误当成 Gate 新条件 | MED | 本 Proposal §9 明确禁止；OD-03/P14 约束 |
| 与 P05 composite 内部结构混淆 | LOW | 不改变 composite = 一个 Question |
| 误把 Proposal 当已生效 Frozen Spec | **HIGH** | 文首 STATUS 显著声明；re-freeze 前禁止宣称生效 |

---

## 12. Rollback Considerations

- Proposal 阶段无生产变更 → 回滚 = 撤回 Proposal 文档（或标记 REJECTED）。
- re-freeze 后：回滚需新的 Owner Decision + Frozen Spec revision；**不得**在 Implementation 中单方面 revert ontology。
- Producer 已按新 shape 产出的 Artifact：若 re-freeze 被拒，Artifact 侧字段可保留在 Producer schema（OD-05）但 V3 不得按未生效 ontology 消费 — 届时 STOP。

---

## 13. Owner Approval Required

```text
[ ] 1. Approve ontology form names + field names as proposed (or amend)
[ ] 2. Pin char_span encoding unit (UTF-8 code units vs Unicode scalar values)
[ ] 3. Approve table_cell identity/locator form
[ ] 4. Approve legacy source_span reading rule (no form → line_range?)
[ ] 5. Approve whether InstanceRoleContent.source_span JSONB extension
       needs formal 10_Data_Model text update (vs JSON-only convention)
[ ] 6. Approve Gate Provenance validation depth (exact vs normalized for each form)
[ ] 7. Explicit Freeze Order / re-freeze of affected Frozen Spec sections
```

**在上述完成并 re-freeze 之前：**

```text
OD-01 = APPROVED DESIGN DECISION
PENDING FROZEN SPEC INCORPORATION
NOT EFFECTIVE AS FROZEN SPEC
Phase 1 P04 Resolved Span implementation: NOT STARTED
```

---

## 14. Explicit Diff Preview（illustrative；非生效文本）

**File (target):** `Docs/V3_SPEC/20_Document_Pipeline.md`（及必要时 `10_Data_Model.md`）

**Illustrative addition（PROPOSED，非正式）：**

```text
+ Resolved Span provenance forms (OD-01):
+   line_range | char_span_in_line | table_cell | multiple_source_spans | other
+ Option structured evidence (P04):
+   options[] = { label, text, provenance[] }
+   options_lines MUST be retained alongside options[]
+ Unreliable option location → options unresolved / QC_FAIL / INCOMPLETE
+ V3 MUST NOT rediscover options from options_lines via LLM guessing
```

正式 diff 将在 Owner 指示的 re-freeze change set 中以 track-change / 完整章节替换方式提出；**本文件不直接编辑 `Docs/V3_SPEC/**`**。

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` |
| Status | PROPOSAL — PENDING OWNER REVIEW |
| Authority | NOT EFFECTIVE until Owner Freeze Order |
| Owner Decision | OD-01 |
| Effective Frozen Spec | UNCHANGED (`Docs/V3_SPEC/**`) |
