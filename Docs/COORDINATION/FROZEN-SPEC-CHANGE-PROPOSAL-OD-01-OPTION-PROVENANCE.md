# FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE

```text
Document ID:           OD-01-PROPOSAL-v4
Title:                 OD-01 Frozen Spec Change Proposal — Option Provenance / Unified Provenance Model
Document Type:         Decision Record
Authority:             Owner Decision / Proposal Record
Registration Level:    Pending L1 Registration
Status:                DRAFT
Normative:             NO
Purpose:               OD-01 option provenance 的完整 Current→Proposed 条款差异、缺口基线、三路径统一 provenance 与可采纳 Frozen Text
Derives From:          OD-01 · OD-01-A…J（OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE）· OD-01R-01…10 · F-OD01 / F-OD01R / F-OD01V3 · P04 · L0 00/10/20/50（只读）· 90/91 · 69 §5
May Change:            本 Proposal 文本；配套 CR-002 Candidate 文本引用一致性
Must Not Change:       L0 00–50 · L0-META 90/91 · Frozen Contract / P01–P25 · Gate/Admission/Question Core · Production · Preprocessing · Schema · Corpus
Supersedes:            OD-01 Proposal v3
Superseded By:         —
Gate State Authority:  NO
RE-FREEZE:             NOT EXECUTED
EFFECTIVE:             NOT EFFECTIVE
```

> **OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE**（不使用「已生效」含义）。
> Frozen Spec = `Docs/V3_SPEC/**` @ tree `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`（UNCHANGED）。
> 本文件 **不修改** `Docs/V3_SPEC/**`。Proposal 服从 Frozen Governance；不是 Proposal 定义治理规则。
> **OD-01-A…J = OWNER APPROVED RECORD；OD-01 design incorporation = PENDING EFFECTIVE FREEZE。**

**流程（OD-01-J）：** Proposal v4 → DSH 复核 → Owner 批准 → 正式 re-freeze。本轮 **不执行** re-freeze。

---

## 0. ID Mapping（R-09）

| Original Finding | Remediation ID | Owner Decision | Status |
|------------------|----------------|----------------|--------|
| F-OD01-01 | （v2 已收） | ACCEPTED | ADDRESSED |
| F-OD01-02 | （v2 已收） | ACCEPTED | ADDRESSED |
| F-OD01-03 | （v2/R 系列） | ACCEPTED | ADDRESSED |
| F-OD01-04 | （v2/R 系列） | ACCEPTED | ADDRESSED |
| F-OD01-05 | （v2/R 系列） | ACCEPTED | ADDRESSED |
| F-OD01-06 | （v2/R 系列） | ACCEPTED | ADDRESSED |
| F-OD01-07 | （v2/R 系列） | ACCEPTED | ADDRESSED |
| F-OD01-08 | （v2/R 系列） | ACCEPTED | ADDRESSED |
| F-OD01R-01 | OD-01R-01 | ACCEPTED | ADDRESSED |
| F-OD01R-02 | OD-01R-02 | ACCEPTED | ADDRESSED |
| F-OD01R-03 | OD-01R-03 | ACCEPTED | ADDRESSED |
| F-OD01R-04 | OD-01R-04 | ACCEPTED | ADDRESSED |
| F-OD01R-05 | OD-01R-05 | ACCEPTED | ADDRESSED |
| F-OD01R-06 | OD-01R-06 | ACCEPTED | ADDRESSED |
| F-OD01R-07 | OD-01R-07 | ACCEPTED | ADDRESSED |
| F-OD01R-08 | OD-01R-08 | ACCEPTED | ADDRESSED |
| F-OD01R-09 | OD-01R-09 | ACCEPTED | ADDRESSED |
| F-OD01R-10 | OD-01R-10 | ACCEPTED | ADDRESSED |
| F-OD01V3-01 | R-01 | OD-01-A/B | ADDRESSED |
| F-OD01V3-02 | R-02 | OD-01-A | ADDRESSED |
| F-OD01V3-03 | R-03 | OD-01-C | ADDRESSED |
| F-OD01V3-04 | R-04 | OD-01-H | ADDRESSED |
| F-OD01V3-05 | R-05 | OD-01-C | ADDRESSED |
| F-OD01V3-06 | R-06 | OD-01-F/G | ADDRESSED |
| F-OD01V3-07 | R-07 | OD-01-E | ADDRESSED |
| F-OD01V3-08 | R-08 | OD-01-F | ADDRESSED |
| F-OD01V3-09 | R-09 | — | ADDRESSED |
| F-OD01V3-10 | R-10 | OD-01-C | ADDRESSED |
| OD-01-A…J | Owner Decisions | APPROVED RECORD | PENDING EFFECTIVE FREEZE |

**唯一编号原则：** 一个问题一个编号；本表为唯一映射。

---

## 1. 缺口基线表（OD-01-B / R-01）— 现有能力 / 真缺口 / 延后 / 非目标

| 能力 / 形态 | 判定 | Frozen 依据 | 与 OD-01 关系 |
|-------------|------|-------------|----------------|
| `granularity: line` | **现有能力** | `20 §5.5` | 吸收为 `line_range` |
| `granularity: line_character` + `start_offset`/`end_offset` | **现有能力**（明文服务「同行多题答案 / 单行多选项」） | `20 §5.5` | 正式化为 `char_span_in_line`（同一坐标，非第二套） |
| Role spans（stem/options/answer/explanation） | **现有能力** | `20 §5.5` / `10 §6.3` | 保持 |
| per-label IR `content.options[label].source_span` | **现有能力（部分）** | `20 §6.1` 示例 `sp-Q1-A` | 补链路权威语义 |
| `text_hash` / exact·normalized / no double consumption | **现有能力** | `10 §6.3` `10 §8` `20 §5.2` | 保持 |
| `options` 整区 role span + `options_lines` | **现有能力** | P04.2 / 契约 | `options_lines` 保持 |
| per-option polymorphic provenance form 维度 | **真缺口** | 无 form 维度 | **本变更新增** |
| `multiple_source_spans` | **真缺口**（单行区间无法表达不连续多段） | `20 §5.5` | **新增 form** |
| `other verifiable source provenance` | **真缺口** | 无开放 form | **新增 form** |
| `table_cell` option 定位 | **延后 + 非目标**（`00 §5` 明确非目标；`20 §5.5`/`10 §4` 延后/裁剪） | `00 §5` `10 §4:107-108` `20 §5.5` | **CHANGE-4 放宽**（仅 option provenance 子集） |
| `fragment` | **延后 + 非目标** | 同上 | **保持延后**（本轮不解除） |
| 文档级表格 cell 完整索引 | **非目标** | `00 §5` | **保持非目标** |
| `image_region` | **真缺口**（图片化选项；实测存在） | 无 | **不**新增顶级 type；作为 `other` 实例（见 §5） |
| `degraded` 语义状态 | **本轮不纳入**（OD-01-F） | — | **不进入**当前 Frozen Spec 修改范围 |
| `options_unresolved` 独立字段 | **不存在于 L0** | tree `b3eeb3e9…` 无此字段 | **禁止引入** |
| V3 无条件 option 边界发现（`20 §5.3`） | **现有规定** | `20 §5.3` | **CHANGE-5 删除/替换**（分路径，见 §4） |

**分析依据（不得删除）：** P04 语料最小充分集（line_range / char_span_in_line / table_cell / image_region·显式降级 / multi-span）；`20 §5.5` 既有 offset 能力；`00 §5` 非目标解除条件「待样本证明需要再加回」。

---

## 2. 状态词与命名收口（OD-01-F/G/H/I · R-04/R-06/R-08）

### 2.1 禁用与替换（R-04 / OD-01-H）

| 禁用 | 替换为 |
|------|--------|
| `DONE` | `ADDRESSED` / `VERIFIED` / `COMPLETED` / `PENDING` / `NOT EFFECTIVE`（按实际） |
| 自创 Status | **禁止**；只用治理允许词 |
| `L1-proposal` 等自创层级 | **禁止** |

### 2.2 权威表述（OD-01-I / R-10）

| 正确 | 禁止 |
|------|------|
| OWNER APPROVED RECORD / PENDING EFFECTIVE FREEZE | 「Owner Decision 已生效」 |
| Authority: Owner Decision / Proposal Record | 「Authority Level: L1」且同时写 NOT REGISTERED（逻辑冲突） |
| Registration Level: Pending L1 Registration | 暗示 CR-002 已是正式 L1 |

### 2.3 resolution 命名拆分（OD-01-G / R-06）— 禁止同名双 authority

| 层 | **唯一命名** | 词汇 / 值域 | 含义 | 明确不是 |
|----|--------------|-------------|------|----------|
| Provenance / span 解析 | **`span_resolution`**（= 现行 `20 §5.2` ResolvedStatus） | `exact / normalized / contextual / fuzzy / ambiguous / missing / incomplete` | provenance/span **本身**是否可靠解析 | 不是 option 整体可用性；不是 answer 结论 |
| Option 证据可用性 | **`option_evidence_status`** | `resolved / unresolved / incomplete` | 该 option 的 label/text/provenance 证据是否可用 | 不是 span 解析质量；不是 answer_status |
| Answer 结论字段 | **`answer_status`**（`10 §6.3`：`source_located / complete / verified_correct`） | 既有三字段 | 答案定位/完备/正确性 | 不是 option/provenance 解析 |
| IR 完备性 | **`semantic_status`**（`20 §6.2`） | `ready / incomplete` | 可否进 Compiler | 不得搬运 E 层状态 |

**禁止**两个不同 authority 使用同一字段名表达不同语义。

### 2.4 degraded（OD-01-F / R-06）

```text
degraded 不进入当前 Frozen Spec 修改范围。
本轮不新增 degraded 状态、不新增 degraded 字段。
不完整 / 不可靠情况 → option_evidence_status ∈ {unresolved, incomplete}
                   → 或 span_resolution ∈ {fuzzy, ambiguous, missing, incomplete}
                   → 进入 review / fail closed 路径。
```

`degraded` 若未来需要，属 **另案** Frozen Spec Change；不得在本 change set 中夹带。

### 2.5 Fail-closed 唯一状态关系（R-08 / OD-01-F）

```text
resolved:
  option_evidence_status = resolved
  且 span_resolution ∈ {exact, normalized, contextual}
  且 form locator 可验证
  → 可继续（仍须 Gate / Admission）

unresolved:
  option_evidence_status = unresolved
  → 不得静默通过；不得伪造 provenance；进入 review / fail closed

incomplete:
  option_evidence_status = incomplete
  或 semantic_status = incomplete
  → 不得 ready；不得静默通过

reviewable（可审快照，非放行）:
  span_resolution ∈ {fuzzy, ambiguous, missing} 等
  → pending_review 候选；不得当 resolved 用
```

**唯一承载：** `option_evidence_status` + `span_resolution` + `semantic_status`（分层，见 §2.3）。
**禁止**并行布尔位（如 `options_unresolved`）表达同一状态。
**禁止**多字段互相覆盖、互相绕过。

---

## 3. 三路径统一 Provenance 模型（OD-01-E / R-07）

> **Both Native Path and Artifact Path MUST produce equivalent semantic representation.**
> **Artifact provenance does not replace Native path authority.**
> **V3 consumption layer MUST NOT create a second semantic authority.**

```text
Path: Native
  Original Source → Seal → Annotation → Native Resolver
    → ResolvedSpan / ResolvedRun → Unified Provenance Model → Canonical V3 IR

Path: Adapter
  Original Source → Preprocessing Artifact → Adapter (verify/translate only)
    → ResolvedSpan / ResolvedRun → Unified Provenance Model → Canonical V3 IR

Path: Artifact（Producer 侧权威输入）
  Preprocessing Artifact
    options[] = {label, text, provenance}   ← Option Segmentation Authority（Path Artifact 输入）
    options_lines MUST KEEP
    → 供 Adapter/V3 Consumer verification / normalization
    → 不建立第二 semantic authority
```

| 路径 | Option / provenance 来源 | 消费层允许 | 消费层禁止 |
|------|--------------------------|------------|------------|
| **Native** | Native Resolver 确定性解析 | 首次解析；产出统一 provenance | LLM 猜边界；把 Native 规则冒充为 Artifact rediscovery 许可 |
| **Adapter** | 验证/翻译 Artifact 声明 | verify only | 第二 Resolver；rediscovery；自主生成 Source 内容 |
| **Artifact** | Producer `options[]` = segmentation + provenance 证据 | 提供输入证据 | 成为下游并行 semantic authority |

**汇聚不变量：**

1. 三路径最终 **必须** 产出 **语义等价、结构一致** 的 Unified Provenance Model → Canonical V3 IR。
2. `ResolvedRun` 保持唯一消费入口（`90 §H-C`）。
3. Gate / Admission 只面对 Canonical IR；不因路径分叉出现两套语义。
4. Artifact provenance **不替代** Native path authority；V3 消费层 **不得** 再造 semantic authority。

---

## 4. Change Items — Current → Proposed（R-01/R-02）

> 每项：**Current Rule → Problem/Limitation → Proposed Rule → Reason → Impact → Affected Frozen Sections**。
> **Proposed Frozen Text** 块可直接复制进入 Frozen Spec：无解释语气、无 TODO、无未决内容。

### CI-1 `00_Master_Spec.md` §5 非目标（table cell/fragment）— **CHANGE-4**

**Current Rule**

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20；待样本
  证明需要再加回）。
```

**Problem / Limitation**

- option provenance 需要 `table_cell`；该条将其列为 M1 非目标。
- 原限制原因：M1 先闭合 line + 必要 inline；完整文档级 cell 索引成本高。
- 真正变化点：仅 **option provenance 子集**解除延后；完整索引与 `fragment` 仍不做。

**Proposed Rule**（= Proposed Frozen Text）

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20）。
  option provenance 可使用 table_cell 定位（见 20 provenance form：table_cell）。
  fragment 字符粒度索引仍为非目标。完整文档级表格 cell 索引仍为非目标。
```

**Reason：** 样本已证明 option table_cell 需要；非目标自带「待样本证明再加回」条件。

**Impact：** 放宽既有约束（CHANGE-4）；不授权完整表格索引；`fragment` 不变。

**Affected Frozen Sections：** `00_Master_Spec.md §5`；联动 `10_Data_Model.md §4`、`20_Document_Pipeline.md §5.5`。

---

### CI-2 `10_Data_Model.md` §4 M1 裁剪（`:107-108`）— **CHANGE-4**

**Current Rule**

```text
M1 裁剪：document_source_tables / _cells / _fragments 不建
（00 §5 non-goal：文档级 cell/fragment 字符粒度延后）；source_figures 保留（M1
必需）。
```

**Problem / Limitation**

- schema 侧投影了 `00 §5` 延后；与 option `table_cell` provenance 冲突。
- 原限制原因：M1 不建完整 cell/fragment 表。
- 真正变化点：option table_cell **provenance 定位**不被该裁剪禁止；**仍不**自动建 `_cells` 全表。

**Proposed Rule**（= Proposed Frozen Text）

```text
M1 裁剪：document_source_tables / _cells / _fragments 不建完整文档级索引
（00 §5 non-goal；fragment 延后不变）。source_figures 保留（M1 必需）。
option provenance 的 table_cell 定位允许指向可回溯表格单元格/raw 证据；
该允许不构成创建 document_source_tables / _cells / _fragments 的授权。
```

**Reason：** 与 CI-1 一致；避免「Spec 要求 table_cell 但 schema 语义禁止定位」。

**Impact：** CHANGE-4；**无** DB migration 授权。

**Affected Frozen Sections：** `10_Data_Model.md §4`；`00 §5`；`20 §5.5`。

---

### CI-3 `20_Document_Pipeline.md` §5.3 `option_label` — **CHANGE-5**

**Current Rule**

```text
- **option_label**：按 A/B/C/D 顺序；每项到下一标签/下一题结束；重复标签 →
  ambiguous；缺标签 → incomplete。
```

**Problem / Limitation**

- 原限制原因：Resolver 在 V3 侧按标签顺序确定 option 边界。
- 真正变化点：Artifact 路径下 Producer 为 Option Segmentation Authority；原「V3 无条件发现」规则被删除/替换；Native 路径保留确定性首次解析。

**Proposed Rule**（= Proposed Frozen Text）

```text
- **option segmentation / option_label**：
  Artifact 路径：Preprocessing Artifact options[] 是 option segmentation 权威来源
  （label、option text、provenance 由 Producer 提供）。V3 仅 verification /
  normalization / consistency check，并可拒绝不可靠证据或 fail closed。V3 不得
  重新发现或猜测 option 边界，不得从 options_lines 按标签扫描切分 option。
  Native 路径：由 Native Resolver 确定性 role resolution 产出 option 边界（首次解析）。
  两条路径必须产出语义等价的 option 结构；V3 消费层不得建立第二套 option
  segmentation authority。对 label 校验：重复标签 → ambiguous；缺标签 → incomplete。
```

**Reason：** 删除「V3 无条件 option 边界发现」；对齐 OD-01 与 OD-01-E。

**Impact：** CHANGE-5 + CHANGE-2/3；四道门 REQUIRED。

**Affected Frozen Sections：** `20 §5.3`；联动 `20 §5.5`、`20 §6.1`、`20 §7.2`。

---

### CI-4 `20_Document_Pipeline.md` §5.5 Resolved Span / granularity — **CHANGE-4 + CHANGE-2**

**Current Rule**

```text
- `granularity` ∈ {line, line_character}（M1；table_cell/fragment 延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 必须能唯
  一定位"同行多题答案/单行多选项"场景。
```

**Problem / Limitation**

- 无 polymorphic provenance form；table_cell/fragment 延后；不连续多段无法表达。
- 原限制原因：M1 以 line 为中心。
- 真正变化点：增加 form 维度与分型 locator；table_cell option 子集延后解除。

**Proposed Rule**（= Proposed Frozen Text）

```text
- `granularity` ∈ {line, line_character}（M1；fragment 延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 必须能唯
  一定位"同行多题答案/单行多选项"场景。
- Resolved Span 增加 provenance form 维度（与 granularity 正交）：
  form ∈ {line_range, char_span_in_line, table_cell, multiple_source_spans, other}。
  char_span_in_line 映射 granularity=line_character 与 start_offset/end_offset（同一
  字符编码单位）。
  locator 分型：
    line_range → start_line, end_line；
    char_span_in_line → line, start_char, end_char；
    table_cell → 可验证 cell 身份与可回溯 raw（不要求 line_ref）；
    multiple_source_spans → spans[] 有序 non-empty，成员各带自身 form 与 locator
      （不得压成假连续行区间）；
    other → method + locator + 可独立验证回溯信息（不要求 line_ref）。
  禁止为满足旧 line 字段而伪造 line_ref。
  option_evidence_status=resolved 时 form 为 1..n；禁止 0-span 静默通过。
```

**Reason：** F-OD01 系列 / R-06；分型 locator。

**Impact：** CHANGE-4 + CHANGE-2；四道门 REQUIRED。

**Affected Frozen Sections：** `20 §5.5`；`00 §5`；`10 §8`。

---

### CI-5 `20_Document_Pipeline.md` §6.1 IR option `source_span` — **CHANGE-2 + CHANGE-1**

**Current Rule**

```text
"options": {"A": {"source_span": {"span_id": "sp-Q1-A"}, "status": "resolved"}},
```

（示例 key：`sp-Q1-A`。）

**Problem / Limitation**

- Producer provenance 与 IR source_span 权威关系未写入 L0。
- 真正变化点：统一 provenance 模型单链路语义（非新 authority）。

**Proposed Rule**（= Proposed Frozen Text）

```text
"options": {"A": {"source_span": {"span_id": "sp-Q1-A"}, "status": "resolved"}},
option source_span 表达统一 provenance 模型中的规范化结果。上游链路为：
  path-specific provenance evidence → V3 verification / normalization
  → unified provenance representation → IR source_span。
Native / Adapter / Artifact 不得形成互相竞争的 semantic authority。
冲突时保留可追踪 conflict signal，不得静默覆盖，并进入 review 或 fail closed。
```

**Reason：** OD-01-E；OD-04 对齐。

**Impact：** CHANGE-2+1。

**Affected Frozen Sections：** `20 §6.1`。

---

### CI-6 `20_Document_Pipeline.md` §6.2 状态隔离 — **CHANGE-2 + CHANGE-3**

**Current Rule**

```text
三层状态严格隔离：E ResolvedStatus ≠ F semantic_status（ready/incomplete）
≠ G gate_decision + decision_status。E 的解析状态不得搬运进 F。
```

**Problem / Limitation**

- option 证据可用性与 span 解析、answer 结论可能同名冲突（R-06/OD-01-G）。
- 真正变化点：显式分层命名；禁止同名双 authority。

**Proposed Rule**（= Proposed Frozen Text）

```text
状态分层（禁止同名双 authority）：
  span_resolution（= ResolvedStatus，20 §5.2）—— provenance/span 解析质量；
  option_evidence_status ∈ {resolved, unresolved, incomplete} —— option 证据可用性；
  answer_status（source_located / complete / verified_correct）—— 答案结论字段；
  semantic_status ∈ {ready, incomplete} —— IR 完备性。
option_evidence_status 不得由 span_resolution 自动推导为 resolved；
answer_status 不得替代 option_evidence_status；
E 层状态不得搬运进 F/G（既有隔离保持）。
不完整或不可靠 → unresolved / incomplete / review；不得静默通过。
```

**Reason：** OD-01-G；R-06/R-08。

**Impact：** CHANGE-2+3。

**Affected Frozen Sections：** `20 §6.2`；`20 §5.2`；`10 §6.3`。

---

### CI-7 `20_Document_Pipeline.md` §7.2 Compiler 提取 — **CHANGE-3**

**Current Rule**

```text
1. 逐 content role 从 resolved span（line / line_character）**确定性提取**正文 →
   `compiled_roles[]`，每个带 `text_hash`（= source slice hash，供 10 §8 2c 校验）。
```

**Problem / Limitation**

- 仅 line / line_character；option 边界来源未分路径。
- 真正变化点：提取覆盖 form locator；Artifact 禁 rediscovery。

**Proposed Rule**（= Proposed Frozen Text）

```text
1. 逐 content role 从 resolved span（line / line_character 或 provenance form
   locator 所定位的 source slice）确定性提取正文 → compiled_roles[]，每个带
   text_hash（= source slice hash，供 10 §8 2c 校验）。
   option leaf 的 label/text 按 §5.3 路径规则来源确定；正文必须与 verified
   locator 所定位 slice 一致。Artifact 路径禁止从 options_lines rediscovery 切分
   option。
```

**Reason：** 与 CI-3/CI-4 一致。

**Impact：** CHANGE-3。

**Affected Frozen Sections：** `20 §7.2`。

---

### CI-8 `20_Document_Pipeline.md` §7.3 dedup_key — **CHANGE-1**

**Current Rule**

```text
Question dedup_key = canonical question type + own stem + own options
（options 按 canonical label order 排序，声明序无关；label 重复 fail-fast）
```

**Problem / Limitation**

- option 输入来源变更需澄清；**组合不得改**。
- 真正变化点：仅注释输入来源（分路径）。

**Proposed Rule**（= Proposed Frozen Text）

```text
Question dedup_key = canonical question type + own stem + own options
（options 按 canonical label order 排序，声明序无关；label 重复 fail-fast）
排除列表不变。own options 的 label/text 作为 dedup 输入，来自统一 provenance
模型下已验证的 option 结构（Artifact 路径为 Producer options[] 经 verification；
Native 路径为 Native Resolver 产出）。Question identity 语义不变。
```

**Reason：** 来源澄清；不改 Question Core。

**Impact：** CHANGE-1。

**Affected Frozen Sections：** `20 §7.3`。

---

### CI-9 `10_Data_Model.md` §6.3 `source_span` JSONB — **CHANGE-1 + CHANGE-2**

**Current Rule**

```text
source_span 是 JSONB，不是 FK。它是应用层 provenance invariant，由
Resolver/Compiler/Gate 验证（§8 不变量 2a-2d）。
```

**Problem / Limitation**

- 需划界 form 扩展 vs `00 §5`「JSONB 隐式业务模型」红线。
- 真正变化点：JSONB 仅承载可验证 provenance 结构；不授权 DDL。

**Proposed Rule**（= Proposed Frozen Text）

```text
source_span 是 JSONB，不是 FK。它是应用层 provenance invariant，由
Resolver/Compiler/Gate 验证（§8 不变量 2a-2d）。JSONB 仅承载可验证 provenance
结构（form、locator、hash、状态字段），不得用 JSONB 隐式承载整个业务模型
（00 §5 非目标不变）。本条不授权数据库 schema 变更。
```

**Reason：** JSONB 红线划界。

**Impact：** CHANGE-1+2。

**Affected Frozen Sections：** `10 §6.3`。

---

### CI-10 `10_Data_Model.md` §8 不变量 2b/2c — **CHANGE-2**

**Current Rule**

```text
2b source_span.line_ref（及 offset）∈ document_source_lines(source_version_id)
   且行内 slice 存在；
2c resolved text_hash == 该 source line/slice 的实际 hash；
```

**Problem / Limitation**

- 一切 provenance 被隐含要求 line_ref（R-06 禁止编造）。
- 真正变化点：按 form locator 核验。

**Proposed Rule**（= Proposed Frozen Text）

```text
2b line 系 form：source_span.line_ref（及 offset）∈ document_source_lines(
   source_version_id) 且行内 slice 存在。非 line 系 form：locator 必须解析到该
   source_version 下可验证 source 实体或切片（table_cell → cell/raw；multiple_
   source_spans → 逐成员满足本条；other → method+locator 可回溯）。禁止伪造
   line_ref。不可解析 → 不得视为 resolved。
2c resolved text_hash == form locator 所定位 slice 的实际 hash；
```

**Reason：** R-06；分型真实性。

**Impact：** CHANGE-2。

**Affected Frozen Sections：** `10 §8`。

---

### CI-11 `50_Migration_Assets.md` 图像/表格 bbox 能力行 — **CHANGE-2 + CHANGE-3**

**Current Rule**

```text
| 图像/表格 bbox 定位能力 | 保留思想，重写 | source_figures（page/bbox/placement/source，IS-7）+ role 归属（10 §4.4/§6.6、20 §5.3/§7.2.5） |
```

**Problem / Limitation**

- option `table_cell` / `image_region` provenance 需与该能力对齐。
- 真正变化点：明确 image/table option provenance 使用既有 figure/region 身份，不伪造 line_ref。

**Proposed Rule**（= Proposed Frozen Text）

```text
| 图像/表格 bbox 定位能力 | 保留思想，重写 | source_figures（page/bbox/placement/source，IS-7）+ role 归属（10 §4.4/§6.6、20 §5.3/§7.2.5）；option provenance 的 table_cell 与 other(method=image_region) 使用可验证 cell/figure/region 身份，不要求、不得伪造 line_ref |
```

**Reason：** R-05/R-06；资产能力与 provenance 对齐。

**Impact：** CHANGE-2+3。

**Affected Frozen Sections：** `50` 表格定位能力行（约 `:51`）。

---

### CI-12 `other` / `image_region` 实例规则 — **CHANGE-2**

**Current Rule**（无开放 form；无 image_region）

**Problem / Limitation**

- 图片化选项无法用 line form 表达；不得因比例低忽略。

**Proposed Rule**（= Proposed Frozen Text）

```text
form=other 的正式实例 image_region 使用 method=image_region，并必须携带：
figure/image 身份（source_figures 关联）、可验证区域（page/bbox/placement 或等价
region）、可独立回溯信息。image_region 不是顶级 provenance form。
无法可靠确定 figure 身份或区域时 option_evidence_status=unresolved 或 incomplete
并进入 review / fail closed；不得伪造 option text 或 line_ref。
fragment 不因本条纳入 form 枚举。
```

**Reason：** F-OD01-06；OD-01-F（不引入 degraded：不可靠即 unresolved/incomplete/review）。

**Impact：** CHANGE-2。

**Affected Frozen Sections：** `20 §5.5` form 枚举；与 CI-4 同文。

---

## 5. Explicit Diff Appendix — Frozen Spec Change Set

| File | Section | Current | Proposed | Reason | Impact | Gate Required |
|------|---------|---------|----------|--------|--------|---------------|
| `00_Master_Spec.md` | §5 非目标 table/fragment | 全文延后 table/fragment 字符索引 | option table_cell 子集解除；fragment/完整索引仍非目标 | 样本证明需要 | CHANGE-4 | 四道门 |
| `10_Data_Model.md` | §4 `:107-108` | `_tables/_cells/_fragments` 不建 | 完整索引仍不建；option table_cell 定位允许 | 与 00 §5 一致 | CHANGE-4 | 四道门 |
| `10_Data_Model.md` | §6.3 source_span | JSONB invariant | + 仅可验证 provenance 结构；禁隐式业务模型 | 00 §5 红线 | CHANGE-1+2 | 回归 |
| `10_Data_Model.md` | §8 2b/2c | line_ref 必验 | form 分型 locator；禁伪造 line_ref | R-06 | CHANGE-2 | 四道门联动 |
| `20_Document_Pipeline.md` | §5.3 option_label | V3 无条件 A/B/C/D 发现 | Artifact=Producer authority；Native=确定性首次解析；禁第二 authority | OD-01/OD-01-E | **CHANGE-5** | **四道门** |
| `20_Document_Pipeline.md` | §5.5 granularity/延后 | line/line_character；table_cell/fragment 延后 | + form 维度与分型 locator；table_cell option 子集解除 | 表达力 | CHANGE-4+2 | 四道门 |
| `20_Document_Pipeline.md` | §6.1 option source_span | 示例 sp-Q1-A | + 统一 provenance 单链路 | OD-01-E | CHANGE-2+1 | 回归 |
| `20_Document_Pipeline.md` | §6.2 状态隔离 | E≠F≠G | + span_resolution / option_evidence_status / answer_status 分名 | OD-01-G | CHANGE-2+3 | 回归 |
| `20_Document_Pipeline.md` | §7.2 提取 | line/line_character only | + form locator；Artifact 禁 rediscovery | 一致性 | CHANGE-3 | 回归 |
| `20_Document_Pipeline.md` | §7.3 dedup_key | type+stem+options | 组合不变；来源分路径澄清 | 防 identity 误改 | CHANGE-1 | 回归 |
| `50_Migration_Assets.md` | 图像/表格 bbox 行 | source_figures 能力 | + option table_cell/image_region 对齐；禁伪造 line_ref | 资产对齐 | CHANGE-2+3 | 回归 |

**50_Interface_Contract** 任务书用语对应仓库文件 **`50_Migration_Assets.md`**（本 Change Set 按实际文件名登记）。

---

## 6. CHANGE 分类汇总（OD-01-D）

| CHANGE | 项 | Gate |
|--------|----|------|
| CHANGE-1 | CI-5/8/9 部分 | 回归 |
| CHANGE-2 | CI-4/5/6/9/10/12 | 回归；部分联动四道门 |
| CHANGE-3 | CI-3 部分/6/7/11 | 受影响层回归 |
| **CHANGE-4** | **CI-1/2/4** | **四道门（69 §5）** |
| **CHANGE-5** | **CI-3** | **四道门（69 §5）** |

```text
CHANGE-3: ACKNOWLEDGED
CHANGE-4: ACKNOWLEDGED — four-gate required
CHANGE-5: ACKNOWLEDGED — four-gate required
Re-freeze: NOT EXECUTED（OD-01-J）
```

### 四道门状态（有证据才算通过）

| Gate | Status |
|------|--------|
| Gate A Identity Closure | PENDING |
| Gate B Legacy / Path 对比 | PENDING |
| Gate C Safety Invariant | PENDING |
| Gate D Adapter Boundary | PENDING |

---

## 7. CR-002 注册条件（R-03 / R-05 / R-10 / OD-01-C）

```text
CR-002 = Change Proposal Record
NOT EFFECTIVE
NOT REGISTERED AS L1
WAITING FOR FOUR-GATE APPROVAL
LOCATION: Docs/COORDINATION/（OD-01-C：保持 COORDINATION，不进入 Frozen Spec）
```

**Formal L1 registration requires:**

1. Owner approval  
2. Gate completion（四道门）  
3. Frozen Spec commit  
4. 90/91 governance registration  

**Current status:** Candidate only。  
**Registration is intentionally deferred until:** Owner approval + Gate completion + Frozen Spec update。  
**CR-002 has a valid future registration path**（非「无合法落点」）。

---

## 8. 非目标（保持）

Gate 四层语义 · Admission · Question Core · Question/Unit 词汇 · QT→UT · P01–P25 · OD-02…G-02 · 历史重处理 · Migration policy · X3 · `fragment` 延后 · **degraded 新状态（OD-01-F）** · Schema/代码/Corpus/Preprocessing 修改 · re-freeze · Phase 1。

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` |
| Version | **v4** |
| Authority | Owner Decision / Proposal Record |
| Registration Level | Pending L1 Registration |
| Status | DRAFT |
| Effective | **NOT EFFECTIVE** |
| Frozen Spec | UNCHANGED (`b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`) |
