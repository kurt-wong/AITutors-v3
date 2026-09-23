# FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE

```text
Document ID:           OD-01-PROPOSAL-v4R
Title:                 OD-01 Frozen Spec Change Proposal — Option Provenance / Unified Provenance Model
Document Type:         Decision Record
Status:                DRAFT
Authority Level:       Proposal — change proposal authority
Registration Level:    Pending L1 Registration
Normative:             NO
Derived From:          OD-01 · OD-01-A…J · OD-01R-01…10 · F-OD01-01…08 · F-OD01R-01…10 · F-OD01V3-01…10 · F-OD01V4-01…03 · F-OD01V4R-01…10 · P04 · L0 00/10/20/50（只读）· 90/91 · 69 §5
May Change:            本 Proposal 文本；配套 CR-002 Candidate 引用一致性
Must Not Change:       L0 00–50 · L0-META 90/91 · Frozen Contract / P01–P25 · Gate/Admission/Question Core · Production · Preprocessing · Schema · Corpus · Migration
Related Records:       CONTRACT-CHANGE-RECORD-CR-002-OD-01.md · OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md · OD-01-PROPOSAL-V4-SELF-REVIEW.md（Self Review only）
Supersedes:            OD-01 Proposal v4
Superseded By:         —
Gate State Authority:  NO
Effective:             NOT EFFECTIVE
```

> **OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE**（不表示 L0 已修改或已生效）。
> Frozen Spec tree = `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`（UNCHANGED）。
> Proposal 服从 90/91；不发明治理体系。Authority Level ≠ Registration Level。

**核心方向（不得改变）：** Artifact-first · Artifact-authoritative · Single provenance authority · No V3 rediscovery（Artifact 路径）· Fail closed。

**流程（OD-01-J）：** Proposal v4R → **DSH 外部验证**（非 Self Review）→ Owner 批准 → 正式 re-freeze。本轮不执行 re-freeze。

**审查边界（F-OD01V4R-01）：**

```text
Self Review = 内部检查（本仓自审报告）；不得作为 DSH 证据。
DSH Review  = 外部验证（DSH 独立出具）；唯一可进入 OD-01-J 证据链的审查类型。
OD-01-J 不得引用 Self Review 报告作为 DSH 证据。
```

---

## 0. ID Mapping（F-OD01V4R-07）— 一问一号，不重编历史

| Original Finding | Remediation / Owner ID | Final ID（本轮起唯一） | Status |
|------------------|------------------------|------------------------|--------|
| F-OD01-01 | OD-01R / v2 已收 | **OD-01F-01** | VERIFIED |
| F-OD01-02 | OD-01R / v2 已收 | **OD-01F-02** | VERIFIED |
| F-OD01-03 | OD-01R / v2 已收 | **OD-01F-03** | VERIFIED |
| F-OD01-04 | OD-01R / v2 已收 | **OD-01F-04** | VERIFIED |
| F-OD01-05 | OD-01R / v2 已收 | **OD-01F-05** | VERIFIED |
| F-OD01-06 | OD-01R / v2 已收 | **OD-01F-06** | VERIFIED |
| F-OD01-07 | OD-01R / v2 已收 | **OD-01F-07** | VERIFIED |
| F-OD01-08 | OD-01R / v2 已收 | **OD-01F-08** | VERIFIED |
| F-OD01R-01…10 | OD-01R-01…10 | **OD-01F-11…20** | VERIFIED |
| F-OD01V3-01…10 | R-01…10 | **OD-01F-21…30** | VERIFIED |
| F-OD01V4-01…03 | （Self Review） | **OD-01F-31…33** | PENDING |
| F-OD01V4R-01 | （本轮） | **OD-01F-34** | VERIFIED |
| F-OD01V4R-02 | （本轮） | **OD-01F-35** | VERIFIED |
| F-OD01V4R-03 | （本轮） | **OD-01F-36** | VERIFIED |
| F-OD01V4R-04 | （本轮） | **OD-01F-37** | VERIFIED |
| F-OD01V4R-05 | （本轮） | **OD-01F-38** | VERIFIED |
| F-OD01V4R-06 | （本轮） | **OD-01F-39** | VERIFIED |
| F-OD01V4R-07 | （本轮） | **OD-01F-40** | VERIFIED |
| F-OD01V4R-08 | （本轮） | **OD-01F-41** | VERIFIED |
| F-OD01V4R-09 | （本轮） | **OD-01F-42** | VERIFIED |
| F-OD01V4R-10 | （本轮） | **OD-01F-43** | VERIFIED |

历史编号保留于 Original 列；**不得重编号**。新问题自 **OD-01F-44** 起递增。

---

## 1. 缺口基线（现有 / 真缺口 / 延后 / 非目标）

| 能力 / 形态 | 判定 | Frozen 依据 | OD-01 关系 |
|-------------|------|-------------|------------|
| `granularity: line` | 现有能力 | `20 §5.5` | 吸收为 `line` form |
| `line_character` + offsets | 现有能力（单行多选项） | `20 §5.5` | 正式化为 `line_character` form（同一坐标） |
| Role spans / text_hash / 解析级联 | 现有能力 | `20` `10 §6.3` `10 §8` | 保持 |
| per-label IR option source_span | 现有能力（部分） | `20 §6.1`（`sp-Q1-A`） | 补单链路语义 |
| `options_lines` | 现有义务 | P04.2 | 保持 |
| polymorphic option provenance | **真缺口** | 无 form 维度 | 本 change set 新增 |
| `multiple_source_spans` | **真缺口** | 单区间 | 新增 |
| `other` 开放 form | **真缺口** | 无 | 新增 |
| `table_cell` option 定位 | 延后 + 非目标 | `00 §5` `10 §4` `20 §5.5` | **CHANGE-4** 放宽子集 |
| `fragment` | 延后 + 非目标 | 同上 | 保持延后 |
| 文档级 cell 完整索引 | 非目标 | `00 §5` | 保持 |
| `image_region` | 真缺口 | 无 | `other` 实例（非顶级 form） |
| 降级态（见 Future Consideration） | **本轮不纳入** | — | 不进入 change set |
| V3 无条件 option 边界发现 | 现有规定 | `20 §5.3` | **CHANGE-5** 删除/替换 |

---

## 2. 字段与状态（F-OD01V4R-03/05/06/08）

### 2.1 Authority Level（≠ Registration Level）

| 对象 | Authority Level | 含义 |
|------|-----------------|------|
| Owner Decision 记录 | **decision authority** | 裁决权威 |
| 本 Proposal | **change proposal authority** | 变更提案权威 |
| CR-002 | **registration / change tracking authority** | 注册与变更跟踪权威 |
| （并行字段）**Registration Level** | **L1 status tracking** | 仅跟踪 L1 注册进度，**不是** Authority |

### 2.2 唯一 span 解析命名（F-OD01V4R-05）

| 层 | **唯一命名** | 值域 | 含义 |
|----|--------------|------|------|
| provenance/span 解析 | **`span_resolution`** | `exact / normalized / contextual / fuzzy / ambiguous / missing / incomplete` | span/provenance 解析质量 |
| option 证据 | `option_evidence_status` | `resolved / unresolved / incomplete` | option 证据可用性 |
| answer 结论 | `answer_status` | `source_located / complete / verified_correct` | 答案三字段 |
| IR 完备 | `semantic_status` | `ready / incomplete` | 可否进 Compiler |

**二选一结果：`span_resolution`。** Change Set 将 L0 示例中的历史字段名统一为 `span_resolution`（见 CI-4/CI-6）。**禁止**两套解析字段并存。Current 原文引用中的历史字段名仅为逐字对照，**不是**第二套定义。

### 2.3 治理状态词（仅用冻结体系已有词）

允许用于本记录族：`APPROVED` · `PENDING` · `VERIFIED` · `NOT EFFECTIVE` · `NOT REGISTERED`（以及 90 Status Header 既有的 `DRAFT` / `NOT RELEASED`）。  
不确定时用 `PENDING`。**不发明新状态词**；模糊完成态与顺序态按 `91 §3.2` 禁用（不在本文展开禁用词形）。

### 2.4 Future Consideration（非正式状态）

降级质量标记 **不在** 本轮 Frozen Spec 修改范围。若未来需要，另案 Change Proposal。  
不完整或不可靠 → `unresolved` / `incomplete` / review / fail closed。

---

## 3. Provenance 定位规则（F-OD01V4R-04）— 分型；禁止一刀切

| Form | 必需定位 | 可选 | 禁止 |
|------|----------|------|------|
| `line`（= line_range） | **`line_ref` 必需**（start/end line） | — | 无定位却标 resolved |
| `line_character` | **`line_ref` + 字符 offset 必需** | — | 只给行不给 offset；伪造 offset |
| `table_cell` | **table identity 必需**（见 §5） | **`line_ref` 可选** | 「完全不需要任何定位」；无 table identity |
| `multiple_source_spans` | **多条 provenance entry 必需**（成员各带 form+locator） | — | 压成假连续区间；空列表标 resolved |
| `other`（含 image_region） | **显式 provenance 描述必需**（method+locator+可验证回溯） | — | 不可验证 free-form；伪造 line_ref |

**禁止**「所有 option 必须 line_ref」。  
**禁止**「table_cell 不需要任何定位」。  
resolved ⇒ form 1..n；禁止 0-span 静默通过。

---

## 4. 三路径统一 Provenance（Artifact-first；单 authority）

```text
Native  ──┐
Adapter ──┼──→ Unified Provenance Model → Canonical V3 IR → Gate / Admission
Artifact ─┘   （Producer options[] = segmentation 权威输入；不替代 Native authority）
```

- Artifact-first / Artifact-authoritative（Artifact 路径 segmentation）。
- Single provenance authority path；V3 消费层 **No second semantic authority**。
- **No V3 rediscovery**（Artifact 路径不得从 `options_lines` 重切 option）。
- Fail closed：不可靠 → `unresolved` / `incomplete` / review；禁止静默通过。

---

## 5. table_cell 唯一表示（F-OD01V4R-09）— 仅治理规则

**确定方案（唯一，无候选列表）：**

```text
table_cell identity =
  (source_version_id, table_id, row_index, col_index)

table_id     = 该 source_version 内 sealed 表结构节点的稳定标识
row_index    = 表内行号，1-based
col_index    = 表内列号，1-based
```

- **唯一性：** 同一 `source_version_id` 下 `(table_id, row_index, col_index)` 唯一定位一个单元格。
- **可验证：** 必须能回溯到该 cell 的 raw 文本证据；不能回溯 → `option_evidence_status` 非 resolved。
- **`line_ref`：** 可选辅助；**不得**伪造。
- 不涉及代码实现或 Schema DDL。

---

## 6. 字符偏移单位（F-OD01V4R-10）— 已选定

```text
offset 单位 = Unicode code point（Unicode scalar value）
start_char  = 行内起始 code point 下标，0-based，inclusive
end_char    = 行内结束 code point 下标，0-based，exclusive
```

**原因：** 与 UTF-8 / UTF-16 码元布局无关；与「字符」直觉一致；可跨编码稳定重放。  
**不留待决。** 落地校验必须按 code point 计数，不得改用 code unit 而不另行走 Change。

---

## 7. Change Items — Current → Proposed

> 结构：Current Rule → Problem/Limitation → Proposed Rule（= Proposed Frozen Text）→ Reason → Impact → Affected Frozen Sections。  
> Proposed 块可直接写入 Frozen Spec：无讨论语气、无未决项。

### CI-1 `00_Master_Spec.md` §5 — **CHANGE-4**

**Current Rule**

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20；待样本
  证明需要再加回）。
```

**Problem / Limitation：** option `table_cell` 被非目标挡住；限制原因 = M1 先做 line。  
**Proposed Rule**

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20）。
  option provenance 可使用 table_cell 定位（见 20 provenance form：table_cell）。
  fragment 字符粒度索引仍为非目标。完整文档级表格 cell 索引仍为非目标。
```

**Reason：** 样本证明 option table_cell 需要。 **Impact：** 放宽约束；非完整索引。  
**Affected：** `00 §5`；`10 §4`；`20 §5.5`。

---

### CI-2 `10_Data_Model.md` §4 — **CHANGE-4**

**Current Rule**

```text
M1 裁剪：document_source_tables / _cells / _fragments 不建
（00 §5 non-goal：文档级 cell/fragment 字符粒度延后）；source_figures 保留（M1
必需）。
```

**Problem / Limitation：** schema 裁剪语义与 option table_cell 冲突。  
**Proposed Rule**

```text
M1 裁剪：document_source_tables / _cells / _fragments 不建完整文档级索引
（00 §5 non-goal；fragment 延后不变）。source_figures 保留（M1 必需）。
option provenance 的 table_cell 定位使用 table identity（table_id, row_index,
col_index）并可回溯 raw；该允许不构成创建 document_source_tables / _cells /
_fragments 或修改数据库 schema 的授权。
```

**Reason：** 与 CI-1/§5 一致。 **Impact：** CHANGE-4；无 migration 授权。  
**Affected：** `10 §4`；`00 §5`。

---

### CI-3 `20_Document_Pipeline.md` §5.3 — **CHANGE-5**

**Current Rule**

```text
- **option_label**：按 A/B/C/D 顺序；每项到下一标签/下一题结束；重复标签 →
  ambiguous；缺标签 → incomplete。
```

**Problem / Limitation：** 与 Artifact 权威 / 禁 rediscovery 冲突。  
**Proposed Rule**

```text
- **option segmentation / option_label**：
  Artifact 路径：Preprocessing Artifact options[] 是 option segmentation 权威来源。
  V3 仅 verification / normalization / consistency check，并可 fail closed。
  V3 不得重新发现 option 边界，不得从 options_lines 切分 option。
  Native 路径：Native Resolver 确定性 role resolution 产出 option 边界（首次解析）。
  两路径必须产出语义等价 option 结构；V3 消费层不得建立第二套 segmentation
  authority。label 重复 → ambiguous；缺 label → incomplete。
```

**Reason：** 删除无条件 V3 发现规则。 **Impact：** CHANGE-5；四道门。  
**Affected：** `20 §5.3`；`20 §5.5`；`20 §6.1`；`20 §7.2`。

---

### CI-4 `20_Document_Pipeline.md` §5.5 — **CHANGE-4 + CHANGE-2**（含命名统一）

**Current Rule**（逐字，含历史字段名，仅对照）

```text
- `granularity` ∈ {line, line_character}（M1；table_cell/fragment 延后，见 00 §5）。
  （示例 JSON 历史解析字段名见 L0 本节原文；Change Set 统一为 span_resolution）
```

**Problem / Limitation：** 无 form 维度；解析字段命名待统一。  
**Proposed Rule**

```text
- `granularity` ∈ {line, line_character}（M1；fragment 延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 为
  Unicode code point（0-based，start inclusive，end exclusive），必须能唯一定位
  “同行多题答案/单行多选项”。
- Resolved Span 增加 provenance form 维度：
  form ∈ {line, line_character, table_cell, multiple_source_spans, other}。
  定位规则：
    line → line_ref 必需；
    line_character → line_ref + character offset 必需；
    table_cell → table identity（table_id, row_index, col_index）必需，line_ref 可选；
    multiple_source_spans → 多条 provenance entry 必需（成员各带 form 与 locator）；
    other → 显式 provenance 描述必需（method + locator + 可验证回溯）。
  禁止要求一切 form 具备 line_ref；禁止 table_cell 无任何定位；禁止伪造 line_ref。
  解析字段唯一命名为 span_resolution（值域同解析级联状态）。
  option_evidence_status=resolved 时 form 为 1..n。
```

**Reason：** F-OD01V4R-04/05/10；表达力。 **Impact：** CHANGE-4+2；四道门。  
**Affected：** `20 §5.5`；`10 §8`。

---

### CI-5 `20 §6.1` — **CHANGE-2 + CHANGE-1**

**Current Rule：** `"options": {"A": {"source_span": {"span_id": "sp-Q1-A"}, "status": "resolved"}}`

**Proposed Rule**

```text
option source_span 表达统一 provenance 模型中的规范化结果。链路：
  path-specific provenance evidence → V3 verification / normalization
  → unified provenance → IR source_span。
Native / Adapter / Artifact 不得形成互相竞争的 semantic authority。
冲突保留 conflict signal，不得静默覆盖，进入 review 或 fail closed。
示例 span_id 以 sp-Q1-A 为准。
```

**Reason：** 单 authority。 **Impact：** CHANGE-2+1。 **Affected：** `20 §6.1`。

---

### CI-6 `20 §6.2` — **CHANGE-2 + CHANGE-3**

**Current Rule：** 三层状态隔离 E ≠ F ≠ G。

**Proposed Rule**

```text
状态分层（禁止同名双 authority）：
  span_resolution —— provenance/span 解析质量（唯一解析字段名）；
  option_evidence_status ∈ {resolved, unresolved, incomplete}；
  answer_status（source_located / complete / verified_correct）；
  semantic_status ∈ {ready, incomplete}。
禁止 span 解析字段与 option/answer 字段同名混用。
option_evidence_status 不得由 span_resolution 自动推导为 resolved；
E 层状态不得搬运进 F/G。
```

**Reason：** 命名唯一。 **Impact：** CHANGE-2+3。 **Affected：** `20 §6.2`。

---

### CI-7 `20 §7.2` — **CHANGE-3**

**Current Rule：** 从 resolved span（line / line_character）确定性提取。

**Proposed Rule**

```text
1. 逐 content role 从 resolved span（line / line_character 或 provenance form
   locator 所定位 slice）确定性提取正文 → compiled_roles[]，带 text_hash。
   option leaf label/text 按 §5.3 路径规则确定；正文与 verified locator slice
   一致。Artifact 路径禁止 rediscovery。
```

**Reason：** 与 CI-3/4 一致。 **Impact：** CHANGE-3。 **Affected：** `20 §7.2`。

---

### CI-8 `20 §7.3` — **CHANGE-1**

**Proposed Rule**

```text
Question dedup_key = canonical question type + own stem + own options
（label order；label 重复 fail-fast）；排除列表不变。
own options 来自统一 provenance 模型下已验证 option 结构。Question identity 不变。
```

**Reason：** 来源澄清。 **Impact：** CHANGE-1。 **Affected：** `20 §7.3`。

---

### CI-9 `10 §6.3` — **CHANGE-1 + CHANGE-2**

**Proposed Rule**

```text
source_span 是 JSONB，不是 FK，为应用层 provenance invariant（§8 2a-2d）。
JSONB 仅承载可验证 provenance 结构（form、locator、hash、span_resolution、
option_evidence_status），不得用 JSONB 隐式承载整个业务模型。本条不授权
schema 变更。
```

**Reason：** 00 §5 红线。 **Impact：** CHANGE-1+2。 **Affected：** `10 §6.3`。

---

### CI-10 `10 §8` 2b/2c — **CHANGE-2**

**Proposed Rule**

```text
2b line / line_character：line_ref（及 offset）∈ document_source_lines 且 slice
   存在。table_cell：table identity 可解析且 raw 可回溯。multiple_source_spans：
   逐成员满足对应 form 规则。other：显式描述可独立回溯。禁止伪造 line_ref。
   不可解析 → 不得视为 resolved。
2c resolved text_hash == form locator 所定位 slice 的实际 hash。
```

**Reason：** 分型真实性。 **Impact：** CHANGE-2。 **Affected：** `10 §8`。

---

### CI-11 `50` bbox 能力行 — **CHANGE-2 + CHANGE-3**

**Proposed Rule**

```text
| 图像/表格 bbox 定位能力 | 保留思想，重写 | source_figures（page/bbox/placement/source，IS-7）+ role 归属；option provenance 的 table_cell 使用 table identity，other(method=image_region) 使用 figure/region 身份；line_ref 可选，不得伪造 |
```

**Impact：** CHANGE-2+3。 **Affected：** `50_Migration_Assets.md`（任务书 `50_Interface_Contract` 对应此实名文件）。

---

### CI-12 `other` / `image_region` — **CHANGE-2**

**Proposed Rule**

```text
form=other 的实例 image_region 使用 method=image_region，并必须携带 figure/image
身份、可验证区域（page/bbox/placement 或等价 region）、可独立回溯信息。
image_region 不是顶级 provenance form。无法可靠确定时 option_evidence_status=
unresolved 或 incomplete 并进入 review / fail closed；不得伪造 option text。
fragment 不纳入 form 枚举。不引入降级态（Future Consideration only）。
```

**Impact：** CHANGE-2。 **Affected：** `20 §5.5` form 枚举。

---

## 8. Explicit Diff Appendix — Frozen Spec Change Set

| File | Section | Current | Proposed | Reason | Impact | Gate Required |
|------|---------|---------|----------|--------|--------|---------------|
| `00_Master_Spec.md` | §5 | table/fragment 非目标 | option table_cell 子集解除 | 样本 | **CHANGE-4** | 四道门 |
| `10_Data_Model.md` | §4 | `_cells` 等不建 | option table_cell 定位允许 | 一致 | **CHANGE-4** | 四道门 |
| `10_Data_Model.md` | §6.3 | JSONB invariant | + form 结构；禁隐式模型 | 红线 | CHANGE-1+2 | PENDING |
| `10_Data_Model.md` | §8 | line 系核验 | 分型 locator；禁伪造 line_ref | OD-01F-37 | CHANGE-2 | 四道门联动 |
| `20_Document_Pipeline.md` | §5.3 | V3 无条件发现 | Artifact/Native 分路径；禁 rediscovery | OD-01F-03 | **CHANGE-5** | **四道门** |
| `20_Document_Pipeline.md` | §5.5 | line/line_character；延后 | + form；span_resolution；code point offset | OD-01F-37/38/43 | **CHANGE-4+2** | **四道门** |
| `20_Document_Pipeline.md` | §6.1 | 示例 sp-Q1-A | + 统一 provenance 链路 | 单 authority | CHANGE-2+1 | PENDING |
| `20_Document_Pipeline.md` | §6.2 | E≠F≠G | + 命名唯一 | OD-01F-38 | CHANGE-2+3 | PENDING |
| `20_Document_Pipeline.md` | §7.2 | line 系提取 | + form locator；禁 rediscovery | 一致 | CHANGE-3 | PENDING |
| `20_Document_Pipeline.md` | §7.3 | dedup 组合 | 组合不变；来源澄清 | 防误改 | CHANGE-1 | PENDING |
| `50_Migration_Assets.md` | bbox 行 | figures 能力 | + table identity / image_region | 对齐 | CHANGE-2+3 | PENDING |

---

## 9. CHANGE 分类与 Gate（不降级）

```text
CHANGE-3: ACKNOWLEDGED
CHANGE-4: ACKNOWLEDGED — four-gate required
CHANGE-5: ACKNOWLEDGED — four-gate required
```

| Gate | Status |
|------|--------|
| A Identity Closure | PENDING |
| B Legacy / Path 对比 | PENDING |
| C Safety Invariant | PENDING |
| D Adapter Boundary | PENDING |

---

## 10. CR-002 注册（Authority ≠ Registration）

```text
CR-002 = Change Proposal Record
Effective: NOT EFFECTIVE
L1: NOT REGISTERED
Registration Level: Pending L1 Registration
Location: Docs/COORDINATION/
```

Formal L1 registration requires: Owner approval · Gate completion · Frozen Spec commit · 90/91 governance registration.  
Registration intentionally deferred until Owner approval + Gate completion + Frozen Spec update。  
Valid future registration path（非无落点）。

---

## 11. Future Required Change / Future Consideration

| 项 | 分类 | 说明 |
|----|------|------|
| 降级质量标记 | Future Consideration | 本轮禁止引入；另案 |
| 正式 L1 注入 `Docs/V3_SPEC/` | Future Required Change | 仅在 Owner approval + Gates + Frozen Spec commit 后 |
| CA-002 写入 `90 §11` | Future Required Change | 绑定实际 Frozen Spec commit |

---

## 12. 非目标

Gate/Admission/Question Core/词汇/QT→UT/P01–P25/OD-02…G-02/历史重处理/Migration/X3/`fragment` 延后/降级态/Schema/代码/Corpus/Preprocessing/re-freeze/Phase 1。

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` |
| Version | v4R |
| Authority Level | Proposal — change proposal authority |
| Registration Level | Pending L1 Registration |
| Status | DRAFT |
| Effective | NOT EFFECTIVE |
| Frozen Spec | UNCHANGED (`b3eeb3e9…`) |
