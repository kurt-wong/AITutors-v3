# FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE

```text
Document ID:           OD-01-PROPOSAL-v4R
Title:                 OD-01 Frozen Spec Change Proposal — Option Provenance / Unified Provenance Model
Document Type:         Decision Record
Status:                PENDING
Purpose:               OD-01 option provenance 的 Current→Proposed 条款差异、缺口基线、三路径统一 provenance、可采纳 Frozen Text 与 Finding 映射
Authority Level:       Proposal Authority
Registration Level:    NOT REGISTERED
Normative:             NO
Derives From:          OD-01 · OD-01-A…J · OD-01R-01…10 · F-OD01-01…08 · F-OD01R-01…10 · F-OD01V3-01…10 · F-OD01V4-01…03 · F-OD01V4R-01…29 · P04 · L0 00/10/20/50（只读）· 90/91 §3.1 · 69 §5
May Change:            本 Proposal 文本；配套 CR-002 Candidate 引用一致性
Must Not Change:       L0 00–50 · L0-META 90/91 · Frozen Contract / P01–P25 · Gate/Admission/Question Core · Production · Preprocessing · Schema · Corpus · Migration
Related Records:       CONTRACT-CHANGE-RECORD-CR-002-OD-01.md · OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md · Docs/REPORTS/OD-01-PROPOSAL-V4-TARGETED-ADVERSARIAL-REVIEW.md（Historical Self Review）
Supersedes:            Previous Revision: Proposal v4
Superseded By:         —
Gate State Authority:  NO
Effective:             NOT EFFECTIVE
Current Version:       v4R（唯一 Current）
```

> 状态词仅用 `91 §3.1 Allowed Status` 词汇（本记录族实用集：APPROVED / PENDING / VERIFIED / NOT EFFECTIVE / NOT REGISTERED）。
> Frozen Spec tree = `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`（UNCHANGED）。
> **Authority Level 只描述决策权归属；Registration Level 单独描述注册状态。二者禁止混用。**
> 核心方向不变：Artifact-first · Artifact-authoritative · Single provenance authority · No V3 rediscovery（Artifact 路径）· Fail closed。

**审查边界：** Self Review = 内部检查（Historical Self Review 文档）。DSH Review = 外部验证。OD-01-J 证据链只接受 DSH Review。

**Planning Category（非 Status）：** `Future Required Change` · `Future Consideration` — 仅规划分类，不是状态值。

---

## 0. Finding → Fix Mapping（F-OD01V4R-15）— 唯一完整表

> 含 F-OD01V4R-01 … F-OD01V4R-29。历史 Finding 不删除、不重编号、无空号。Final ID 一问一号；新问题自 **OD-01F-63** 起。

| Finding ID | Final ID | Problem | Fix Location | Verification Evidence | Status |
|------------|----------|---------|--------------|----------------------|--------|
| F-OD01-01 | OD-01F-01 | Resolved Span 基线不完整 | Proposal §1 缺口基线 | 基线表含现有/缺口/延后/非目标 | VERIFIED |
| F-OD01-02 | OD-01F-02 | 条款级 diff 不全 | Proposal §7–§8 | CI-1…12 + Appendix | VERIFIED |
| F-OD01-03 | OD-01F-03 | 禁 rediscovery 与 §5.3 冲突 | CI-3 | CHANGE-5 取代文本 | VERIFIED |
| F-OD01-04 | OD-01F-04 | provenance 权威链路未定义 | Proposal §4 · CI-5 | 单链路 + conflict signal | VERIFIED |
| F-OD01-05 | OD-01F-05 | fail-closed 双字段歧义 | Proposal §2.2 · CI-6 | option_evidence_status 唯一 | VERIFIED |
| F-OD01-06 | OD-01F-06 | image_region 缺口 | CI-12 | other 实例；非顶级 form | VERIFIED |
| F-OD01-07 | OD-01F-07 | L0 修改路径未走治理 | CR-002 · §10 | Change Proposal Record 流程 | VERIFIED |
| F-OD01-08 | OD-01F-08 | 引用 sp-*.option.* 错误 | CI-5 | 示例 `sp-Q1-A` | VERIFIED |
| F-OD01R-01 | OD-01F-11 | CR-002 正式 L1 落位 | §10 · CR-002 §0 | NOT REGISTERED + 注册条件 | VERIFIED |
| F-OD01R-02 | OD-01F-12 | 治理 Header 不合规 | 全文档 Header | 字段齐备（见 F-17） | VERIFIED |
| F-OD01R-03 | OD-01F-13 | CHANGE 分类压低 | §9 | CHANGE-3/4/5 ACKNOWLEDGED | VERIFIED |
| F-OD01R-04 | OD-01F-14 | 未覆盖多路径 | Proposal §4 | Native/Adapter/Artifact | VERIFIED |
| F-OD01R-05 | OD-01F-15 | diff 影响面不全 | §8 | 含 10 §4 / 20 §6.2 / 50 | VERIFIED |
| F-OD01R-06 | OD-01F-16 | 定位方式一刀切 | Proposal §3 | 分型 locator | VERIFIED |
| F-OD01R-07 | OD-01F-17 | 解析状态字段冲突 | Proposal §2.2 | span_resolution 唯一 | VERIFIED |
| F-OD01R-08 | OD-01F-18 | fail-closed 关系不清 | Proposal §2.2 | 分层唯一承载 | VERIFIED |
| F-OD01R-09 | OD-01F-19 | 缺 Owner Decision 记录 | OWNER-DECISIONS | OD-01R / V4R 附录 | VERIFIED |
| F-OD01R-10 | OD-01F-20 | 引用坐标错误 | 历史处置 | sp-M1 等更正记录 | VERIFIED |
| F-OD01V3-01 | OD-01F-21 | v3 缺完整基线/diff | Proposal §1 · §7 | 已恢复 | VERIFIED |
| F-OD01V3-02 | OD-01F-22 | 缺 Proposed Frozen Text | CI-1…12 | 可复制文本块 | VERIFIED |
| F-OD01V3-03 | OD-01F-23 | CR-002 定位误解 | CR-002 §0 | Change Proposal Record | VERIFIED |
| F-OD01V3-04 | OD-01F-24 | 状态词不合规 | 全文档 | 仅 91 §3.1 实用集 | VERIFIED |
| F-OD01V3-05 | OD-01F-25 | Gap 表述不准确 | §10 | 注册条件未满足；有未来路径 | VERIFIED |
| F-OD01V3-06 | OD-01F-26 | degraded / 解析字段归属不清 | §2.2 · Planning | 字段分层；降级非本轮 | VERIFIED |
| F-OD01V3-07 | OD-01F-27 | 只写 Artifact 路径 | Proposal §4 | 三路径统一模型 | VERIFIED |
| F-OD01V3-08 | OD-01F-28 | fail-closed 多字段 | Proposal §2.2 | 唯一关系 | VERIFIED |
| F-OD01V3-09 | OD-01F-29 | ID 编号混乱 | §0 | 本表 | VERIFIED |
| F-OD01V3-10 | OD-01F-30 | Authority/Registration 混用 | §2.1 · Header | 分离字段 | VERIFIED |
| F-OD01V4-01 | OD-01F-31 | 编码单位待决 | Proposal §6 | Unicode code point 已选定 | VERIFIED |
| F-OD01V4-02 | OD-01F-32 | 50 文件名不一致 | §8 | 注明实名 | VERIFIED |
| F-OD01V4-03 | OD-01F-33 | 四道门未过 | §9 | 全 PENDING | VERIFIED |
| F-OD01V4R-01 | OD-01F-34 | Self Review 冒充 DSH | Historical Self Review | 边界声明 | VERIFIED |
| F-OD01V4R-02 | OD-01F-35 | Header 字段不全 | 全文档 | 含 Purpose 等 | VERIFIED |
| F-OD01V4R-03 | OD-01F-36 | 状态词 | 全文档 | 扫描 0 命中禁词 | VERIFIED |
| F-OD01V4R-04 | OD-01F-37 | locator 冲突 | Proposal §3 | 分型规则 | VERIFIED |
| F-OD01V4R-05 | OD-01F-38 | resolution 双名 | Proposal §2.2 | 仅 span_resolution | VERIFIED |
| F-OD01V4R-06 | OD-01F-39 | Authority Level | §2.1 | Decision/Proposal/Change Record Authority | VERIFIED |
| F-OD01V4R-07 | OD-01F-40 | ID Mapping | §0 | 本表 | VERIFIED |
| F-OD01V4R-08 | OD-01F-41 | 降级态夹带 | Planning Category | Future Consideration only | VERIFIED |
| F-OD01V4R-09 | OD-01F-42 | table_cell identity 草率 | CI-2 · Planning | 改为 Future Required Change | VERIFIED |
| F-OD01V4R-10 | OD-01F-43 | char offset 未定 | Proposal §6 | Unicode code point | VERIFIED |
| F-OD01V4R-11 | OD-01F-44 | DSH 外部登记：治理映射/表述收口不足 | 本表 §0 + §10 + Header | 映射含 01–29；表述单向 | VERIFIED |
| F-OD01V4R-12 | OD-01F-45 | DSH 外部登记：注册条件与 Gap 用语冲突 | §10 · CR-002 §0 | 单一表述 | VERIFIED |
| F-OD01V4R-13 | OD-01F-46 | DSH 外部登记：Header 字段名/缺 Purpose | 全文档 | Derives From + Purpose | VERIFIED |
| F-OD01V4R-14 | OD-01F-47 | DSH 外部登记：Authority 值域自定义 | §2.1 | 三值 Decision/Proposal/Change Record Authority | VERIFIED |
| F-OD01V4R-15 | OD-01F-48 | Finding→Fix 映射错配/缺失 | **本表 §0** | 29 行齐备；含 Evidence 列 | VERIFIED |
| F-OD01V4R-16 | OD-01F-49 | Governance Gap 双向表述 | **§10 · CR-002 §0** | 单向：条件未满足 + Future registration path | VERIFIED |
| F-OD01V4R-17 | OD-01F-50 | Header 缺 Purpose；来源字段名错误 | **全文档 Header** | Purpose 有；错误来源字段名 = 0 | VERIFIED |
| F-OD01V4R-18 | OD-01F-51 | Authority Level 混用 | **§2.1** | 仅决策权；≠ Registration Level | VERIFIED |
| F-OD01V4R-19 | OD-01F-52 | 状态词 / 引用 §3.2 | **全文档** | 仅 91 §3.1；禁词扫描空 | VERIFIED |
| F-OD01V4R-20 | OD-01F-53 | table_id 写成已有事实 | **CI-2 · §11** | Future Required Change；不声称 table_id 存在 | VERIFIED |
| F-OD01V4R-21 | OD-01F-54 | CI 缺 Current Rule | **§7 CI-1…12** | 六段结构齐备 | VERIFIED |
| F-OD01V4R-22 | OD-01F-55 | CI-4 verbatim/summary 混用 | **CI-4** | 明确标注 | VERIFIED |
| F-OD01V4R-23 | OD-01F-56 | form 双体系无解释 | **§3.1 术语表** | line_range↔line 等 | VERIFIED |
| F-OD01V4R-24 | OD-01F-57 | Self Review 格式 | **REPORTS 历史文档** | Historical Self Review | VERIFIED |
| F-OD01V4R-25 | OD-01F-58 | 外仓路径引用 | **全文档** | 仅本仓路径 | VERIFIED |
| F-OD01V4R-26 | OD-01F-59 | 机械替换痕迹 | **全文档** | 无替换式状态描述 | VERIFIED |
| F-OD01V4R-27 | OD-01F-60 | 来源字段名不统一 | **全文档** | 仅 Derives From | VERIFIED |
| F-OD01V4R-28 | OD-01F-61 | 拼写/多 Current | **全文档** | v4R 唯一 Current；Previous Revision | VERIFIED |
| F-OD01V4R-29 | OD-01F-62 | Future 词当 Status | **§11** | Planning Category only | VERIFIED |

---

## 1. 缺口基线

| 形态 | 判定 | 依据 | OD-01 关系 |
|------|------|------|------------|
| line / line_character + offsets | 现有能力 | `20 §5.5` | form 术语见 §3.1 |
| Role spans / text_hash / 解析级联 | 现有能力 | `20` `10` | 保持 |
| options_lines | 现有义务 | P04.2 | 保持 |
| polymorphic option provenance | 真缺口 | — | 本 change set |
| multiple_source_spans / other | 真缺口 | — | 新增 |
| table_cell option 定位 | 延后+非目标 | `00 §5` `10 §4` `20 §5.5` | CHANGE-4 子集 |
| fragment / 完整 cell 索引 | 延后/非目标 | 同上 | 不解除 |
| image_region | 真缺口 | — | other 实例 |
| 降级质量标记 | 本轮不纳入 | — | Planning: Future Consideration |
| V3 无条件 option 边界发现 | 现有规定 | `20 §5.3` | CHANGE-5 删除/替换 |

---

## 2. Authority / 字段 / 状态

### 2.1 Authority Level（F-OD01V4R-18）— 只描述决策权

| 对象 | Authority Level |
|------|-----------------|
| Owner Decision | **Decision Authority** |
| Proposal | **Proposal Authority** |
| CR | **Change Record Authority** |

| 并行字段 | 值 | 含义 |
|----------|-----|------|
| **Registration Level** | NOT REGISTERED / Pending L1 Registration | **仅**注册状态跟踪 |

**禁止** `Authority Level = L1`。**禁止** Authority Level 与 Registration 混用。

### 2.2 解析字段唯一命名（span_resolution）

| 层 | 唯一命名 | 值域 |
|----|----------|------|
| provenance/span 解析 | **span_resolution** | exact / normalized / contextual / fuzzy / ambiguous / missing / incomplete |
| option 证据 | option_evidence_status | resolved / unresolved / incomplete |
| answer 结论 | answer_status | source_located / complete / verified_correct |
| IR 完备 | semantic_status | ready / incomplete |

### 2.3 状态词（F-OD01V4R-19）— 引用 `91 §3.1 Allowed Status`

本记录族使用：`APPROVED` · `PENDING` · `VERIFIED` · `NOT EFFECTIVE` · `NOT REGISTERED`。  
不确定 → `PENDING`。不扩展状态集。不引用 `91 §3.2` 作正向定义。

---

## 3. 定位规则与 form 术语

### 3.1 Form 术语对应（F-OD01V4R-23）

| Producer / P04 / 调查用语 | L0 form 名 | 关系 |
|---------------------------|------------|------|
| `line_range` | **`line`** | 同一能力：行区间。Producer 用语 → L0 form 名映射；非两套坐标。 |
| `char_span_in_line` | **`line_character`** | 同一能力：行内字符区间 + offset。映射既有 `granularity: line_character`。 |
| `table_cell` | `table_cell` | 同名。 |
| `multiple_source_spans` | `multiple_source_spans` | 同名。 |
| `other` | `other` | 同名；`image_region` = `other` 的实例名（method）。 |

Change Set 统一采用 **L0 form 名**；Producer 用语仅作对照。

### 3.2 Locator（F-OD01V4R-04）

| Form | 必需 | 可选 | 禁止 |
|------|------|------|------|
| line | line_ref（start/end） | — | 无定位标 resolved |
| line_character | line_ref + character offset | — | 缺 offset；伪造 |
| table_cell | table cell 定位信息（identity 对齐见 §11） | line_ref | 「完全无定位」 |
| multiple_source_spans | 多条 provenance entry（成员各带 form+locator） | — | 假连续；空列表 resolved |
| other | 显式 provenance 描述（method+locator+可验证回溯） | — | 不可验证 free-form；伪造 line_ref |

禁止「一切 option 必须 line_ref」。禁止「table_cell 不需要任何定位」。

### 3.3 字符 offset（F-OD01V4R-10）

Unicode code point；行内 0-based；start inclusive；end exclusive。已选定，不留待决。

---

## 4. 三路径统一 Provenance

```text
Native + Adapter + Artifact → Unified Provenance Model → Canonical V3 IR → Gate / Admission
```

- Artifact-first / Artifact-authoritative；Single provenance authority。
- No V3 rediscovery（Artifact 路径）。
- Fail closed。
- Artifact provenance 不替代 Native authority；消费层禁止第二 semantic authority。

---

## 5. table_cell identity（F-OD01V4R-20）— 不写成已有事实

```text
Planning Category: Future Required Change
声明：table_cell identity requires future Frozen Spec alignment。
```

- **不得**声称 `table_id` 已存在或已冻结。
- **不得**在本轮创建 schema / 新字段 / 实现。
- 治理层仅要求：table_cell **必须有可验证定位**；具体 identity 形状待与 Frozen Spec 对齐后另案写入 Change Set。
- （Previous Revision 中的候选形状仅作历史，不构成当前规范。）

---

## 6. Change Items（F-OD01V4R-21/22）

结构固定：**Current Rule → Problem → Proposed Frozen Text → Reason → Impact → Affected**。

### CI-1 `00_Master_Spec.md` §5 — CHANGE-4

**Current Rule**（verbatim）

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20；待样本
  证明需要再加回）。
```

**Problem：** option table_cell 被非目标阻挡。  
**Proposed Frozen Text**

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20）。
  option provenance 可使用 table_cell 定位（见 20 provenance form：table_cell）。
  fragment 字符粒度索引仍为非目标。完整文档级表格 cell 索引仍为非目标。
```

**Reason：** 样本证明需要。 **Impact：** 放宽约束。 **Affected：** `00 §5`；`10 §4`；`20 §5.5`。

### CI-2 `10_Data_Model.md` §4 — CHANGE-4

**Current Rule**（summary）

```text
M1 裁剪：document_source_tables / _cells / _fragments 不建；source_figures 保留。
```

**Problem：** 与 option table_cell 定位冲突。  
**Proposed Frozen Text**

```text
M1 裁剪：document_source_tables / _cells / _fragments 不建完整文档级索引
（00 §5 non-goal；fragment 延后不变）。source_figures 保留（M1 必需）。
option provenance 的 table_cell 必须具备可验证定位；identity 形状与 Frozen Spec
对齐前不得声称具体表标识已存在。本条不授权数据库 schema 变更。
```

**Reason：** 与 CI-1 一致。 **Impact：** CHANGE-4。 **Affected：** `10 §4`。

### CI-3 `20_Document_Pipeline.md` §5.3 — CHANGE-5

**Current Rule**（verbatim）

```text
- **option_label**：按 A/B/C/D 顺序；每项到下一标签/下一题结束；重复标签 →
  ambiguous；缺标签 → incomplete。
```

**Problem：** 与 Artifact 权威 / 禁 rediscovery 冲突。  
**Proposed Frozen Text**

```text
- **option segmentation / option_label**：
  Artifact 路径：Preprocessing Artifact options[] 是 option segmentation 权威来源。
  V3 仅 verification / normalization / consistency check，并可 fail closed。
  V3 不得重新发现 option 边界，不得从 options_lines 切分 option。
  Native 路径：Native Resolver 确定性 role resolution 产出 option 边界（首次解析）。
  两路径必须产出语义等价 option 结构；V3 消费层不得建立第二套 segmentation
  authority。label 重复 → ambiguous；缺 label → incomplete。
```

**Reason：** 删除无条件 V3 发现规则。 **Impact：** CHANGE-5。 **Affected：** `20 §5.3` 及下游提取/IR。

### CI-4 `20_Document_Pipeline.md` §5.5 — CHANGE-4+2

**Current Rule**（**verbatim**，仅以下两行原文；不夹杂整理句）

```text
- `granularity` ∈ {line, line_character}（M1；table_cell/fragment 延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 必须能唯
  一定位"同行多题答案/单行多选项"场景。
```

（同节示例 JSON 与 Resolved Relation 示例为 **summary** 参照，不在此混入 verbatim 块。）

**Problem：** 无 form 维度；解析字段名待统一；offset 单位未写死。  
**Proposed Frozen Text**

```text
- `granularity` ∈ {line, line_character}（M1；fragment 延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 为
  Unicode code point（行内 0-based，start inclusive，end exclusive），必须能唯一定位
  “同行多题答案/单行多选项”。
- Resolved Span 增加 provenance form 维度（与 granularity 正交）：
  form ∈ {line, line_character, table_cell, multiple_source_spans, other}。
  Producer 用语映射：line_range → line；char_span_in_line → line_character。
  定位规则：
    line → line_ref 必需；
    line_character → line_ref + character offset 必需；
    table_cell → 可验证 table cell 定位必需（identity 形状另案对齐），line_ref 可选；
    multiple_source_spans → 多条 provenance entry 必需；
    other → 显式 provenance 描述必需。
  禁止要求一切 form 具备 line_ref；禁止 table_cell 无任何定位；禁止伪造 line_ref。
  解析字段唯一命名：span_resolution。
  option_evidence_status=resolved 时 form 为 1..n。
```

**Reason：** F-37/38/43/55/56。 **Impact：** CHANGE-4+2。 **Affected：** `20 §5.5`；`10 §8`。

### CI-5 `20 §6.1` — CHANGE-2+1

**Current Rule**（summary）

```text
IR content.options[label].source_span 示例 span_id：sp-Q1-A。
```

**Problem：** 链路权威未写入。  
**Proposed Frozen Text**

```text
option source_span 表达统一 provenance 模型中的规范化结果。链路：
  path-specific provenance evidence → V3 verification / normalization
  → unified provenance → IR source_span。
Native / Adapter / Artifact 不得形成互相竞争的 semantic authority。
冲突保留 conflict signal，不得静默覆盖，进入 review 或 fail closed。
示例 span_id 以 sp-Q1-A 为准。
```

**Reason：** 单 authority。 **Impact：** CHANGE-2+1。 **Affected：** `20 §6.1`。

### CI-6 `20 §6.2` — CHANGE-2+3

**Current Rule**（summary）

```text
三层状态隔离：E 解析状态 ≠ F semantic_status ≠ G gate/decision。
```

**Problem：** 解析/option/answer 命名可能冲突。  
**Proposed Frozen Text**

```text
状态分层（禁止同名双 authority）：
  span_resolution —— provenance/span 解析质量（唯一解析字段名）；
  option_evidence_status ∈ {resolved, unresolved, incomplete}；
  answer_status（source_located / complete / verified_correct）；
  semantic_status ∈ {ready, incomplete}。
禁止解析字段与 option/answer 字段同名混用。
option_evidence_status 不得由 span_resolution 自动推导为 resolved；
E 层状态不得搬运进 F/G。
```

**Reason：** 命名唯一。 **Impact：** CHANGE-2+3。 **Affected：** `20 §6.2`。

### CI-7 `20 §7.2` — CHANGE-3

**Current Rule**（summary）

```text
从 resolved span（line / line_character）确定性提取正文。
```

**Problem：** 未覆盖新 form；未禁 Artifact rediscovery。  
**Proposed Frozen Text**

```text
1. 逐 content role 从 resolved span（line / line_character 或 provenance form
   locator 所定位 slice）确定性提取正文 → compiled_roles[]，带 text_hash。
   option leaf label/text 按 §5.3 路径规则确定；正文与 verified locator slice
   一致。Artifact 路径禁止 rediscovery。
```

**Reason：** 一致。 **Impact：** CHANGE-3。 **Affected：** `20 §7.2`。

### CI-8 `20 §7.3` — CHANGE-1

**Current Rule**（summary）

```text
Question dedup_key = type + own stem + own options（label order；重复 fail-fast）。
```

**Problem：** 输入来源需澄清；组合不得改。  
**Proposed Frozen Text**

```text
Question dedup_key = canonical question type + own stem + own options
（label order；label 重复 fail-fast）；排除列表不变。
own options 来自统一 provenance 模型下已验证 option 结构。Question identity 不变。
```

**Reason：** 澄清。 **Impact：** CHANGE-1。 **Affected：** `20 §7.3`。

### CI-9 `10 §6.3` — CHANGE-1+2

**Current Rule**（summary）

```text
source_span 为 JSONB 应用层 provenance invariant，非 FK。
```

**Problem：** 需对齐 00 §5 JSONB 红线。  
**Proposed Frozen Text**

```text
source_span 是 JSONB，不是 FK，为应用层 provenance invariant（§8 2a-2d）。
JSONB 仅承载可验证 provenance 结构（form、locator、hash、span_resolution、
option_evidence_status），不得用 JSONB 隐式承载整个业务模型。本条不授权 schema 变更。
```

**Reason：** 红线。 **Impact：** CHANGE-1+2。 **Affected：** `10 §6.3`。

### CI-10 `10 §8` — CHANGE-2

**Current Rule**（summary）

```text
2b line_ref/offset 须在 source lines 内；2c text_hash 与 slice 一致。
```

**Problem：** 非 line form 需分型核验。  
**Proposed Frozen Text**

```text
2b line / line_character：line_ref（及 offset）∈ document_source_lines 且 slice
   存在。table_cell：可验证 cell 定位可解析且 raw 可回溯。multiple_source_spans：
   逐成员满足对应 form 规则。other：显式描述可独立回溯。禁止伪造 line_ref。
   不可解析 → 不得视为 resolved。
2c resolved text_hash == form locator 所定位 slice 的实际 hash。
```

**Reason：** 真实性。 **Impact：** CHANGE-2。 **Affected：** `10 §8`。

### CI-11 `50_Migration_Assets.md` bbox 行 — CHANGE-2+3

**Current Rule**（summary）

```text
图像/表格 bbox 定位能力：source_figures + role 归属。
```

**Problem：** option table/image provenance 需对齐。  
**Proposed Frozen Text**

```text
| 图像/表格 bbox 定位能力 | 保留思想，重写 | source_figures（page/bbox/placement/source，IS-7）+ role 归属；option provenance 的 table_cell 使用可验证 cell 定位，other(method=image_region) 使用 figure/region 身份；line_ref 可选，不得伪造 |
```

**Reason：** 对齐。 **Impact：** CHANGE-2+3。 **Affected：** `50_Migration_Assets.md`。

### CI-12 other / image_region — CHANGE-2

**Current Rule**（summary）

```text
无开放 other form；无 image_region 正式承载。
```

**Problem：** 图片化选项无法用 line 表达。  
**Proposed Frozen Text**

```text
form=other 的实例 image_region 使用 method=image_region，并必须携带 figure/image
身份、可验证区域（page/bbox/placement 或等价 region）、可独立回溯信息。
image_region 不是顶级 provenance form。无法可靠确定时 option_evidence_status=
unresolved 或 incomplete 并进入 review / fail closed；不得伪造 option text。
fragment 不纳入 form 枚举。不引入降级质量标记（Planning Category: Future Consideration）。
```

**Reason：** 覆盖真实语料形态。 **Impact：** CHANGE-2。 **Affected：** `20 §5.5`。

---

## 7. Explicit Diff Appendix

| File | Section | Current | Proposed | Reason | Impact | Gate Required |
|------|---------|---------|----------|--------|--------|---------------|
| `00_Master_Spec.md` | §5 | table/fragment 非目标 | option table_cell 子集解除 | 样本 | CHANGE-4 | 四道门 |
| `10_Data_Model.md` | §4 | `_cells` 等不建 | option cell 定位允许；identity 另案 | 一致 | CHANGE-4 | 四道门 |
| `10_Data_Model.md` | §6.3 | JSONB invariant | + form 结构 | 红线 | CHANGE-1+2 | PENDING |
| `10_Data_Model.md` | §8 | line 系核验 | 分型 locator | F-37 | CHANGE-2 | 联动 |
| `20_Document_Pipeline.md` | §5.3 | V3 无条件发现 | 分路径；禁 rediscovery | F-03 | CHANGE-5 | 四道门 |
| `20_Document_Pipeline.md` | §5.5 | line 系；延后 | + form；span_resolution；code point | F-37/38/43 | CHANGE-4+2 | 四道门 |
| `20_Document_Pipeline.md` | §6.1 | sp-Q1-A | + 单链路 | F-04 | CHANGE-2+1 | PENDING |
| `20_Document_Pipeline.md` | §6.2 | E≠F≠G | + 命名唯一 | F-17 | CHANGE-2+3 | PENDING |
| `20_Document_Pipeline.md` | §7.2 | line 系提取 | + form；禁 rediscovery | 一致 | CHANGE-3 | PENDING |
| `20_Document_Pipeline.md` | §7.3 | dedup 组合 | 组合不变 | 防误改 | CHANGE-1 | PENDING |
| `50_Migration_Assets.md` | bbox 行 | figures | + cell/image 对齐 | 对齐 | CHANGE-2+3 | PENDING |

---

## 8. CHANGE 与 Gate

```text
CHANGE-3: ACKNOWLEDGED
CHANGE-4: ACKNOWLEDGED — four-gate required
CHANGE-5: ACKNOWLEDGED — four-gate required
```

| Gate | Status |
|------|--------|
| A | PENDING |
| B | PENDING |
| C | PENDING |
| D | PENDING |

---

## 9. CR-002 注册（F-OD01V4R-16 单向表述）

```text
CR-002 = Change Proposal Record
Effective: NOT EFFECTIVE
L1: NOT REGISTERED
Registration Level: NOT REGISTERED
Location: Docs/COORDINATION/（本仓）
```

**原因：** 尚未满足正式注册条件（下列四条未齐）。  
**不是**「没有 L1 落点」。**保留** Future registration path。**禁止**第二 registry。

Formal L1 registration requires（Planning Category: Future Required Change）:

1. Owner approval  
2. Gate completion  
3. Frozen Spec commit  
4. 90/91 governance registration  

---

## 10. Planning Category（F-OD01V4R-29）— 不是 Status

| 词 | 性质 | 用途 |
|----|------|------|
| **Future Required Change** | Planning Category | 将来必须做的变更项（如正式 L1 落位、CA-002、table_cell identity 对齐） |
| **Future Consideration** | Planning Category | 将来可选考虑（如降级质量标记） |

**不是 Status。** 不得填入 Status 字段。

| 项 | Category |
|----|----------|
| 正式 L1 写入治理登记点 | Future Required Change |
| CA-002 登记 | Future Required Change |
| table_cell identity 与 Frozen Spec 对齐 | Future Required Change |
| 降级质量标记 | Future Consideration |

---

## 11. 非目标

Gate/Admission/Question Core/词汇/QT→UT/P01–P25/OD-02…G-02/历史重处理/Migration/X3/fragment 延后/降级态/schema/代码/Corpus/Preprocessing/re-freeze/Phase 1。

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` |
| Current Version | v4R |
| Previous Revision | Proposal v4 |
| Authority Level | Proposal Authority |
| Registration Level | NOT REGISTERED |
| Status | PENDING |
| Effective | NOT EFFECTIVE |
