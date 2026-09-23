# FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE

```text
STATUS: PROPOSAL REVISED — PENDING OWNER AUTHORIZATION
AUTHORITY: FROZEN SPEC CHANGE PROPOSAL (NOT YET EFFECTIVE)
PURPOSE: OD-01 incorporation into Frozen Resolved Span ontology
OWNER-DECISION: OD-01 APPROVED (design) + F-OD01-01~08 Owner dispositions ACCEPTED
FROZEN-SPEC-INCORPORATION: PENDING
L1 CHANGE RECORD: CREATED (see CONTRACT-CHANGE-RECORD-CR-002-OD-01.md)
RE-FREEZE: NOT DONE
OWNER AUTHORIZATION: REQUIRED
REVISION: v2 — reconciles DSH findings F-OD01-01 … F-OD01-08
```

> **这是 Proposal，不是已生效的 Frozen Spec 修改。**
> 没有 Owner 后续明确 Freeze Order / re-freeze，不得把它标成已经修改 Frozen Spec。
> 当前生效 Frozen Spec 仍为 `Docs/V3_SPEC/**` @ tree `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`（unchanged）。
> **本文件不直接编辑 `Docs/V3_SPEC/**`。**
> **NOT EFFECTIVE / 尚未修改 Frozen Spec / 尚未 re-freeze / 尚未进入 Phase 1。**

**Related:**
- `OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md`（D1 / OD-01）
- `CONTRACT-CHANGE-RECORD-CR-002-OD-01.md`（L1 Contract Change Record）
- Frozen Contract P04（`PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` §P04）
- `Docs/V3_SPEC/00_Master_Spec.md` §5
- `Docs/V3_SPEC/20_Document_Pipeline.md` §5.3 / §5.5 / §6.1 / §7.2 / §7.3
- `Docs/V3_SPEC/10_Data_Model.md` §6.3 / §8
- `Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md`（L0-META：R1/R2、CHANGE-0…5、§11）
- DSH：`AITutor-X/Docs/60_REPORTS/OD-01-FROZEN-SPEC-PROPOSAL-DSH-ADVERSARIAL-REVIEW.md`

---

## 0. Finding 处置矩阵（D3）

| Finding | Owner Decision | Action | Status |
|---------|----------------|--------|--------|
| F-OD01-01 | ACCEPT | 补完整 Resolved Span baseline（line / line_character / offsets / table_cell / multiple_source_spans / other / fragment / image_region） | RESOLVED IN PROPOSAL |
| F-OD01-02 | ACCEPT | 补完整条款级 explicit diff（含 00 / 20 / 10 相关条款） | RESOLVED IN PROPOSAL |
| F-OD01-03 | ACCEPT + Owner 裁决 | Producer Artifact 为 option segmentation 唯一权威；同步改写冲突的 `20 §5.3` | RESOLVED IN PROPOSAL |
| F-OD01-04 | ACCEPT + Owner 裁决 | 定义 provenance → Resolved Span → IR 单链路权威与冲突规则 | RESOLVED IN PROPOSAL |
| F-OD01-05 | ACCEPT + Owner 裁决 | 统一 fail-closed；钉死状态字段与 cardinality | RESOLVED IN PROPOSAL |
| F-OD01-06 | ACCEPT + Owner 裁决 | `image_region` 纳入 `other verifiable source provenance` 正式实例 | RESOLVED IN PROPOSAL |
| F-OD01-07 | ACCEPT + 强制执行 | 建立 L1 Contract Change Record（CR-002），登记分类/受影响层/回归范围 | RESOLVED IN GOVERNANCE |
| F-OD01-08 | ACCEPT | 修正错误引用 `sp-<unit>.option.<label>` → 规范示例 `sp-Q1-A` | RESOLVED IN PROPOSAL |

---

## 1. Problem（修订后）

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

**Current Frozen Resolved Span ontology**（`20_Document_Pipeline.md` / `10_Data_Model.md`）以 line-span / role span 为中心。它**已经具备** `line` / `line_character` + `start_offset`/`end_offset` 字符级定位能力（理由明文包括「单行多选项」），但**尚未**正式定义 polymorphic option provenance form 维度，也**不能完整表达** P04 的多态 option provenance（尤其 `table_cell`、`multiple_source_spans`、开放 `other`）。

因此 OD-01 裁决：**扩展 Frozen Resolved Span** —— 属 Frozen Spec Change，必须走：

```text
OD-01 Owner Decision
  → OD-01 Frozen Spec Change Proposal（本文件，修订版）
  → 条款级 explicit diff（本文件 §8，F-OD01-02）
  → L1 Contract Change Record（CR-002）
  → Owner Authorization
  → L0 Frozen Spec modification
  → re-freeze
```

**本任务只完成到：L1 Change Record 已建立并准备进入 Owner Authorization。**

---

## 2. Current Frozen Semantics — 完整现状基线（F-OD01-01 / F-OD01-08）

（生效中；本 Proposal **不修改**下列文本。）

### 2.1 Resolved Span 现状（不得把既有能力错误描述为「全部不存在」）

| Aspect | Current Frozen semantics | 既有能力判定 |
|--------|--------------------------|--------------|
| Primary line granularity | `granularity` ∈ `{line, line_character}`（`20 §5.5`） | **已存在** |
| Character-level offsets | `start_offset` / `end_offset`；`line_character` 必须能唯一定位「同行多题答案 / **单行多选项**」场景（`20 §5.5`） | **已存在**（字符级粒度 + offset） |
| Role spans | `stem` / `options` / `answer` / `explanation` 等 content role 的 span | **已存在** |
| Option granularity（现状） | `options` 为整区 role span；per-label 在 IR `content.options[label]`（`20 §6.1`）；`label` 在 `instance_role_contents.label`（options only，`10 §6.3`） | **已存在（部分）**；per-option provenance form **未正式定义** |
| Provenance verification | exact / normalized 解析级联（`20 §5.2`）+ `text_hash == SHA256(text.encode("utf-8"))`（`10 §6.3`）+ 禁止 double span consumption | **已存在** |
| Example span_id keys（规范示例） | `sp-Q1-stem` / `sp-Q1-A` / `sp-Q1-answer` / `sp-M1`（`20 §6.1`） | **已存在**；见 §2.4 引用更正 |
| Storage | `instance_role_contents.source_span` JSONB（应用层 invariant，非 FK；`10 §6.3`） | **已存在** |
| `table_cell` | `granularity` 注明「table_cell/fragment **延后**，见 00 §5」；`00 §5` 将「文档级表格 cell/fragment 字符粒度索引」列为**明确非目标（M1 不做）** | **延后 / 非目标**（不是「ontology 空白」，而是冻结的明确不做） |
| `fragment` | 与 `table_cell` 同列延后；`00 §5` 同条非目标 | **延后**；**OD-01 本轮不解除 `fragment` 延后** |
| `multiple_source_spans` | 现行 ResolvedSpan 为单一行区间（`start_line_ref`/`end_line_ref`/`line_refs`），不连续多段**无法表达** | **真缺口** |
| `other verifiable source provenance` | 无开放 form | **真缺口** |
| `image_region` | 无正式承载；语料实测存在图片化选项 | **真缺口**（本轮按 F-OD01-06 裁决纳入 `other`） |
| `char_span_in_line`（P04 用语） | 与既有 `granularity: line_character` + `start/end_offset` **实质能力重合** | **不是全新坐标系**；是既有字符级能力的 **provenance form 正式化命名**（见 §2.2） |

### 2.2 `char_span_in_line` 与既有 `line_character` 的关系（钉死）

```text
既有 Frozen Resolved Span 坐标：
  granularity = line_character
  start_offset / end_offset
  用途明文：唯一定位「同行多题答案 / 单行多选项」

OD-01 / P04 provenance form 名称：
  char_span_in_line
```

**关系裁决（本 Proposal 提出，待 Owner Authorization 后写入 L0）：**

- `char_span_in_line` **不是**第二套字符坐标。
- 它是既有 `line_character` + `start_offset`/`end_offset` 能力在 **option provenance form 维度**上的正式名称 / 映射别名。
- 落地时二者必须共享同一 offset 编码单位（UTF-8 code unit 或 Unicode scalar —— 仍属 §13 Owner 批准项 #2）。
- 不得把「新增 `char_span_in_line` form」误写成「当前完全没有字符级能力」。

### 2.3 `table_cell` / `fragment` / `multiple_source_spans` / `other` / `image_region` 状态

| 形态 | 现状 | 与本次变更关系 |
|------|------|----------------|
| `table_cell` | `20 §5.5` 延后注 + `00 §5` 明确非目标（文档级表格 cell/fragment 字符粒度索引） | OD-01 **部分解除**该非目标的 option-provenance 子集（见 §8.1）；**不**建立完整文档级表格索引 |
| `fragment` | 同上延后 | **保持延后**；OD-01 **不**把 `fragment` 升为 form |
| `multiple_source_spans` | 无法表达（单区间） | **新增 form**（有序 non-empty 列表） |
| `other verifiable source provenance` | 无 | **新增开放 form**（禁止不可验证 free-form） |
| `image_region` | 无 | **不**新增顶级 ontology type；作为 `other` 的**正式实例**（F-OD01-06） |
| `line_range` | 现有 line span 可吸收 | **KEEP / 吸收**现有 line span |
| `char_span_in_line` | 能力已有、form 名未正式 | **正式化命名**（映射 `line_character`+offset） |

### 2.4 引用更正（F-OD01-08）

| 错误表述 | 准确表述 |
|----------|----------|
| 「Example keys = `sp-<unit>.option.<label>`（IR 示例中的 role key / V3 Spec 要求）」 | Frozen Spec `20 §6.1` **示例** span_id 实为 `sp-Q1-stem` / `sp-Q1-A` / `sp-Q1-answer` / `sp-M1` |
| （混淆来源） | `sp-<unit>.option.<label>` 形态来自 **代码** `backend/app/domains/compile/ir.py` `_content_span_id`（`sp-{unit_id}.option.{label}`），**不是** Frozen Spec 示例原文 |

本修订**只修正文献/引用精度，不改变语义**。示例引用统一为规范中的 `sp-Q1-A`；代码构造名另行在实现层对齐，不在本 Proposal 改代码。

### 2.5 相关不变式（保持不变）

- `text_hash = SHA256(text.encode("utf-8"))`（P23 关联但独立于 `source_content_sha256`）
- Gate Provenance 层：exact/normalized + hash 一致 + no double consumption
- `content_roles`：`options` = `required_for_choice` for single_choice/multiple_choice/true_false
- Question Core 不因 provenance 扩展而改变
- P04.2：`options_lines` 必须保留（Producer 侧已要求；Consumer 不得删除）
- Question `dedup_key` 的 **canonical input 组合**不变（见 §8.5：仅明确输入来源，不改 identity 语义）

---

## 3. Owner Decision（OD-01）与 F-OD01-03/04/05/06 最终裁决

### 3.1 OD-01 核心裁决（不变）

**扩展 Frozen Resolved Span ontology**，使 P04 Option Provenance 成为正式 V3 可表达、可验证的 provenance 形态。

必须支持至少：

```text
line_range
char_span_in_line
table_cell
multiple_source_spans
other verifiable source provenance
```

Binding Requirements（D1 原文语义保持）：

1. `options[]` 保留 `label` + `text` + `provenance`
2. `options_lines` 不得删除
3. 禁止假设「一个 option = 一行」或「一个 option = 一个 span」
4. Table Cell 必须能够表达
5. Multiple Source Spans 必须能够表达
6. 不可可靠定位 → explicit `unresolved` / `QC_FAIL` / `INCOMPLETE`，不得猜测
7. V3 不得用 LLM 猜测 Option 边界代替 Preprocessing evidence

字段命名可由本 Proposal 建议；**语义不得被命名改写**。

### 3.2 F-OD01-03 — Option Segmentation Authority（Owner 最终裁决）

> **Producer Artifact 是 option segmentation 的权威来源。**

Producer 提供：

- option label
- option text
- option provenance / segmentation evidence

V3：

- **可以**验证（verification）
- **可以**检查一致性（consistency check）
- **可以**拒绝不可靠证据
- **可以** fail closed

V3：

- **不得**重新发现 option 边界（no rediscovery）
- **不得**形成第二套 option segmentation authority

**禁止模糊措辞**：不存在「V3 仍可自行推断、但通常相信 Producer」。Producer 证据缺失/不可靠时，路径是 **fail closed**，不是 fallback rediscovery。

**与现行 Frozen Spec 冲突的规则必须在 explicit diff 中改写**，包括 `20 §5.3` 现行：

```text
option_label：按 A/B/C/D 顺序；每项到下一标签/下一题结束；重复标签 → ambiguous；缺标签 → incomplete。
```

该条把 option 边界确定放在 V3 Resolver 侧，与「V3 不重新发现 option 结构」直接抵触。本 Proposal §8.3 给出取代文本。

### 3.3 F-OD01-04 — Provenance → Resolved Span → IR 单链路（Owner 最终裁决）

完整链路：

```text
Original Source
    ↓
AITutors-preprocessing
    ↓
Preprocessing Artifact
    ↓
options[].provenance                    ← Producer 提供的输入证据
    ↓
V3 Consumer Boundary
    verification / normalization
    ↓
Frozen Resolved Span                    ← V3 验证/规范化后的标准 provenance 表达
    ↓
Canonical V3 IR
    options["A"].source_span            ← Canonical V3 IR 中的规范化表达
    ↓
Gate / Admission
```

三层职责：

| 层 | 字段/对象 | 职责 | 权威地位 |
|----|-----------|------|----------|
| Producer 输入证据 | `options[].provenance` | 提供 option segmentation + provenance 证据 | **输入证据**；不是下游第二 semantic authority |
| Frozen Resolved Span | Resolved Span（含 provenance form 维度） | V3 验证/规范化后的**标准 provenance 表达** | **验证后的规范表达** |
| Canonical V3 IR | `options["A"].source_span` | IR 中的规范化绑定 | **IR 规范化表达**（同一链路末端，非新权威） |

**不得形成两套或三套互相竞争的 provenance authority。**

冲突规则（Producer provenance 与 V3 验证结果冲突时）：

1. **不得静默覆盖**任何一侧；
2. **必须保留可追踪 conflict signal**（两侧原值 + 冲突类型 + 时间/阶段）；
3. 按既有 review / unresolved / fail-closed 机制处理（对齐 OD-02 conflict-as-signal 精神，但**不**借 OD-01 引入新的第二 semantic authority path）；
4. 在冲突未按既有机制收敛前，该 option **不得**进入正常 canonical option provenance / ready 路径。

与 OD-04 对齐：**禁止保留第二条具有独立 semantic authority 的正式 ingestion path。** Producer `options[].provenance` 在 Consumer Boundary 之后只作为可追溯证据与 conflict signal 输入，**不**并行驱动下游语义。

### 3.4 F-OD01-05 — 统一 Fail-Closed（Owner 最终裁决）

当 option 或其 provenance 无法可靠确定时：

```text
unresolved / incomplete / QC_FAIL
        ↓
不得伪造 provenance
        ↓
不得静默形成正常 canonical option provenance
        ↓
不得绕过既有安全边界（no double consumption / text_hash / Gate Provenance / Admission）
```

**唯一 fail-closed 承载模型（消除双字段歧义）：**

| 概念 | 字段/机制 | 唯一语义 |
|------|-----------|----------|
| Span 解析状态（既有） | Resolved Span `resolution_status` | 单 span 解析质量：`exact` / `normalized` / … / `incomplete` 等（沿用 `20 §5.2` 值域，本 Proposal 不扩值域除非 re-freeze 另决） |
| Option 解析状态（本 Proposal 钉死） | option `resolution_status` ∈ `{resolved, unresolved, incomplete}` | 该 option 是否具备可靠 label/text/provenance |
| QC / 整体拒绝 | `QC_FAIL` | QC 层拒绝；**不是** option 字段的同义词 |
| ~~`options_unresolved: true`~~ | **废止为独立语义字段** | 不得与 `unresolved` 并列构成第二套机制。若实现需要汇总位，只能是**派生只读摘要**（由 option 状态计算），**永不**作为唯一 fail-closed 载体，也**永不**单独使某 option「看起来已解析」 |

**Cardinality 钉死（消除 `0..n` vs「不得 0-span 静默通过」歧义）：**

| 场景 | `provenance` / forms cardinality | 合法性 |
|------|----------------------------------|--------|
| option `resolution_status = resolved` | **1..n**（至少一个 form） | 合法 |
| option `resolution_status = resolved` 且 forms = `[]` | — | **非法**（即「0-span 静默通过」被禁止） |
| option `resolution_status ∈ {unresolved, incomplete}` | 0..n（通常为空；允许保留 partial 证据但不得标 resolved） | 合法；状态本身承载 fail-closed |
| `multiple_source_spans.spans` | **有序 non-empty** | 与上述一致 |
| 伪造 span / 伪造 form / 伪造 locator | — | **禁止**；直接 unresolved / incomplete / QC_FAIL |

### 3.5 F-OD01-06 — `image_region` 处理（Owner 最终裁决）

> **`image_region` 纳入 `other verifiable source provenance` 的正式实例。**
> **本轮不新增 `image_region` 为 Frozen Resolved Span 顶级独立 ontology type。**

承载方式：

```text
form = "other"
method = "image_region"
```

可验证性要求（缺一不可；无法可靠确定 → fail closed）：

1. **Figure / Image identity**：必须指向 source figure 身份（对齐既有 `figure_id` / `source_figures` 概念；D-6 Figure Contract 相关字段语义不变）；
2. **可验证的位置或区域信息**：page / bbox / placement 等可回溯区域描述；
3. **必要的 degraded / unresolved 信息**：图片化选项在 Markdown/OCR 层无法恢复文字时，必须显式 `degraded` / `unresolved` 声明，**不得伪造** option text；
4. **无法可靠确定时 fail closed**：figure 唯一性、区域可回溯性、text↔image 一致性任一不成立 → `unresolved` / `incomplete` / `QC_FAIL`。

**不得因为当前样本比例较低（实测约 4/945）而忽略这一类真实语料。**

`fragment`：**不**因本条纳入；保持既有延后，除非另案 Owner Decision。

---

## 4. Required New Semantics（Proposed）

### 4.1 Ontology：`ResolvedSpan` polymorphic provenance forms（PROPOSED）

在 Frozen Resolved Span 语义层增加 **provenance form** 维度（不改变 identity/hash 不变量）：

| Form | Proposed name | Required payload | Notes |
|------|---------------|------------------|-------|
| Line range | `line_range` | `start_line`, `end_line`（1-based closed） | 兼容/吸收现有 line span |
| Char span in line | `char_span_in_line` | `line`, `start_char`, `end_char`（编码单位 re-freeze 时钉死一种） | **映射既有** `line_character` + `start_offset`/`end_offset`；切开同行内 A/B/C/D |
| Table cell | `table_cell` | 可验证 cell 坐标（如 `table_span` + `row`, `col` 或 HTML cell identity + 可回溯 raw） | 选项在表格内；仅解除 option-provenance 子集 |
| Multiple source spans | `multiple_source_spans` | `spans[]` = **有序 non-empty** 列表，元素为其他 form | 选项跨多行/多块 |
| Other verifiable | `other` | `method` + `locator` + 可独立验证回溯信息 | 禁止不可验证 free-form；`image_region` 为其正式实例（§3.5） |

每个 option 的 provenance 在 `resolved` 时应为 **1..n** 显式 form 结构；不可靠时 option 状态 `unresolved`/`incomplete`（或 QC 层 `QC_FAIL`），**不得 0-span 静默通过**（详见 §3.4）。

### 4.2 `options[]`（PROPOSED logical shape；非最终 DDL）

```text
options: [
  {
    label: string,                          # e.g. "A" —— 来自 Producer segmentation authority
    text: string,                           # option text；须与 verified provenance 定位内容一致
    resolution_status: "resolved" | "unresolved" | "incomplete",
    provenance: [                           # resolved 时 1..n；unresolved/incomplete 时不得伪造
      { form: "line_range" | "char_span_in_line" | "table_cell"
        | "multiple_source_spans" | "other", ...form fields }
    ],
    conflict_signal: object | null          # Producer 证据 vs V3 验证冲突时保留；默认 null
  }
]
options_lines: [start, end] | null          # MUST KEEP（P04.2）；与 options[] 并存
```

**不再使用**独立语义字段 `options_unresolved: true`（见 §3.4）。整体 options 无法可靠形成时，逐 option 或整体内容走既有 `unresolved`/`incomplete`/`QC_FAIL` 路径，而不是并行布尔位。

### 4.3 Verification rules（PROPOSED）

- 每个 provenance form 必须可映射回 Original Source 且可独立验证（与 P04.3 / P22 精神一致）。
- Gate Provenance 层扩展校验：form 合法 + locator 可解析 + text 与 locator 内容一致（normalized 级规则可后续细化）+ 不与其他已消费 span 冲突（沿用 no double consumption）。
- **option segmentation 不得 rediscovery**：V3 不得从 `options_lines` 自行切 option（见 §3.2 / §8.3）。
- **不可靠 → fail closed**：`unresolved` / `incomplete` / `QC_FAIL`；禁止 silent fallback、禁止 partial fabricate。
- Producer provenance 与验证结果冲突 → conflict signal 保留 + 不得静默覆盖（见 §3.3）。

### 4.4 Canonical semantics that remain UNCHANGED（explicit）

- Question Type / Unit Type 闭集不变
- `standalone_unit` / `composite_unit` 词汇不变；**不引入 `Standalone Question`**
- Admission 公式不变：Core + Frozen required + Identity/Evidence/Gate
- P01–P25 其他 Owner Decisions 不变（P04 仍是 CLOSED 决策；本 Proposal 只是把 P04 语义落入 Frozen Resolved Span）
- OD-02 / OD-03 / OD-04 / OD-05 / G-01 / G-02 不变
- Identity：`source_content_sha256` ⊥ `derived_text_hash`（P23）不变
- LLM-derived Metadata / Post-Admission Enrichment 边界不变
- `options_lines` 保留义务不变
- Gate 四层既有语义不变
- QT→UT 不建立全局映射
- 历史数据重新处理原则 / Migration policy / X3 entry condition 不变
- Question `dedup_key` 的 canonical input **组合**不变（type + own stem + own options；排除 shared material / answer / …）

---

## 5. Ontology Changes（summary）

| Change | Type |
|--------|------|
| Resolved Span gains polymorphic provenance forms | **ADD** ontology dimension |
| `line_range` remains valid form | **KEEP**（吸收当前 line spans） |
| `char_span_in_line` | **FORMALIZE**（映射既有 `line_character`+offset；ADD form name） |
| `table_cell` | **ADD form**（解除 option-provenance 子集延后；同步改写 `00 §5` 非目标） |
| `multiple_source_spans` / `other` | **ADD** |
| `image_region` | **ADD as `other` instance**（非顶级 type） |
| Option-level `options[]{label,text,provenance}` | **ADD** logical structure（P04） |
| `options_lines` | **KEEP mandatory** |
| `options_unresolved` 独立语义字段 | **DO NOT ADD / 明确废止** |
| `20 §5.3` option_label V3 边界规则 | **MODIFY**（Producer 为 segmentation authority） |
| Compiler `line / line_character` only 提取句 | **MODIFY**（扩展至新 form） |
| `00 §5` table cell/fragment 字符粒度非目标 | **MODIFY**（部分解除；`fragment` 仍延后） |
| Existing role spans / text_hash / source_content_sha256 | **UNCHANGED** |
| Question dedup_key composition | **UNCHANGED**（仅明确 option 输入来源） |
| New Question Type / Unit Type | **NONE** |
| New Admission-required fields | **NONE**（provenance 扩展不升格 metadata 为 Admission 条件） |

---

## 6. Affected Components（组件视图；条款视图见 §8）

| Component | Repo | Impact |
|-----------|------|--------|
| Preprocessing prompt / parser / validation | AITutors-preprocessing | 产出 `options[]` + polymorphic provenance（Producer-side 可扩展 → OD-05） |
| Preprocessing Resolver IR | AITutors-preprocessing | 拷贝 `options[]` / 保留 `options_lines` |
| Consumer Boundary / annotation adapter | AITutors-v3 | 消费 `options[]`；**禁止 rediscovery** |
| `ResolvedSpan` / `source_span` 消费 | AITutors-v3 | 解析 polymorphic forms |
| `IRBuilder` / `Compiler` | AITutors-v3 | option leaf 绑定 provenance |
| Gate Provenance 层 | AITutors-v3 | 校验 form/locator/text；**不新增 Gate condition 语义** |
| `InstanceRoleContent.source_span` | AITutors-v3 | 可承载扩展 JSON；**DDL 是否变更待 Owner** |
| Tests | both | 见 §12 |

**只读核对（本任务未修改）：** `backend/scripts/preprocessing_consumer/resolved_span_adapter.py`（现行仅 `granularity: "line"` + null offsets 的整区 role span）、`backend/app/domains/compile/ir.py` `_content_span_id`（代码构造名，非 Spec 示例）。

---

## 7. Compatibility Impact

| Area | Impact | Assessment |
|------|--------|------------|
| Existing line-only spans | 仍可表示为 `line_range` | **Backward compatible**（语义上兼容） |
| Existing `line_character` + offsets | 映射为 `char_span_in_line` form | **Compatible**（同一坐标，form 正式化） |
| Existing `source_span` JSONB | 可写入扩展 form；旧数据无 form 字段 | **Need explicit legacy reading rule**（建议：无 form = `line_range` 解释）→ 待 Owner 确认 |
| Existing Resolved Span consumers | 必须识别 form；未知 form → fail closed | **Behavioral change** on malformed/unknown |
| Producer old artifacts | 无 `options[]` | **NOT patched**（Historical Source Reprocessing Principle）；重跑获得新 Artifact |
| `options_lines` | 必须保留 | **No break** |
| Canonical vocabulary | 不变 | **No break** |
| Question Core fields | 不变 | **No break** |
| Question `dedup_key` composition | 不变 | **No break**（输入来源见 §8.5） |
| Frozen `10_Data_Model` DDL 文本 | 若需正式新增列/注释 ontology | **Frozen Spec text change = this proposal**；非 DB migration 自动授权 |

**Migration Impact：** 本 Proposal **不授权** DB migration、corpus rewrite、artifact patch。历史路径仍为 Original Source → Current Preprocessing。

---

## 8. 条款级 Explicit Diff（F-OD01-02）— 非生效文本

> 下列每项给出：**Current Frozen Text / Rule → Proposed Frozen Text / Rule → Change Reason → Impact**。
> **正式 L0 采纳必须经 L1（CR-002）+ Owner Authorization + re-freeze change set。**
> 本文件**不**直接编辑 `Docs/V3_SPEC/**`。

### 8.1 `00_Master_Spec.md` §5 明确非目标（table cell/fragment 字符粒度）

**Current Frozen Text / Rule**（`00 §5`）：

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20；待样本
  证明需要再加回）。
```

**Proposed Frozen Text / Rule**：

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20）。
  【OD-01 局部修订】option provenance 所需的 table_cell 定位能力已由样本证明需要，
  自本条修订生效后解除「table_cell」在 option provenance 子集上的延后（见 20 §5.5
  provenance form：table_cell）。fragment 仍为非目标/延后；完整文档级表格 cell 索引
  仍为非目标（仅 option provenance 子集解除）。
```

**Change Reason：** F-OD01-01/F-OD01-02：`table_cell` 不是在空白处新增，而是**部分废止/改写冻结的明确非目标**。不改写则 re-freeze 后内部自相矛盾。

**Impact：** 解除 option-provenance 子集；**不**授权完整文档级表格索引；`fragment` 保持非目标。属 **CHANGE-3 成分**（改变既有规定的行为/范围）。

### 8.2 `20_Document_Pipeline.md` §5.5 — `granularity` 枚举与延后注

**Current Frozen Text / Rule**（`20 §5.5`）：

```text
- `granularity` ∈ {line, line_character}（M1；table_cell/fragment 延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 必须能唯
  一定位"同行多题答案/单行多选项"场景。
```

**Proposed Frozen Text / Rule**：

```text
- `granularity` ∈ {line, line_character}（M1；fragment 仍延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 必须能唯
  一定位"同行多题答案/单行多选项"场景。
- 【OD-01】Resolved Span 增加 provenance form 维度（与 granularity 正交）：
  form ∈ {line_range, char_span_in_line, table_cell, multiple_source_spans, other}。
  char_span_in_line 映射 granularity=line_character + start_offset/end_offset（同一
  编码单位）；multiple_source_spans.spans 为有序 non-empty；other 必须 method+locator+
  可独立验证回溯信息；image_region 是 other 的正式实例（method=image_region），
  不是顶级 form。resolved option 的 form 序数为 1..n；禁止 0-span 静默通过。
```

**Change Reason：** F-OD01-01（基线完整）、F-OD01-02（条款完整）、F-OD01-05（cardinality）、F-OD01-06（image_region）。

**Impact：** 扩展可表达范围；`granularity` 枚举本身**不**强行加入 `table_cell`/`fragment` 为 granularity 值（table_cell 走 form 维度，避免与延后注冲突）。属 **CHANGE-2（新增 form）+ CHANGE-3（改延后注/范围）**。

### 8.3 `20_Document_Pipeline.md` §5.3 — `option_label` 解析规则（F-OD01-03 关键冲突）

**Current Frozen Text / Rule**（`20 §5.3`）：

```text
- **option_label**：按 A/B/C/D 顺序；每项到下一标签/下一题结束；重复标签 →
  ambiguous；缺标签 → incomplete。
```

**Proposed Frozen Text / Rule**：

```text
- **option segmentation / option_label**：Preprocessing Artifact `options[]` 是 option
  segmentation 的唯一权威来源（label、option text、segmentation / provenance evidence
  由 Producer 提供）。V3 仅 verification / normalization / consistency check，并可拒绝
  不可靠证据或 fail closed；V3 不得重新发现或猜测 option 边界，不得从 `options_lines`
  按标签扫描切分 option，不得形成第二套 option segmentation authority。
  Producer 证据缺失/不可靠/冲突未收敛 → unresolved / incomplete / QC_FAIL，不得回退到
  V3 自行推断。对 Producer 提供的 label 做校验时：重复标签 → ambiguous 或 fail-fast
  （按既有 label 重复规则）；缺标签 → incomplete。本条取代原「按 A/B/C/D 顺序；每项到
  下一标签/下一题结束」的 V3 侧 option 边界确定规则。
```

**Change Reason：** Owner 裁决 F-OD01-03：Producer Artifact 是 option segmentation 权威；现行 §5.3 与「禁 V3 rediscovery」直接冲突，必须显式取代，不得保留 fallback rediscovery。

**Impact：** 改变既有 Resolver option 边界行为 → **CHANGE-3（Normative Modification）**。测试面：禁 rediscovery、缺/伪 Producer options[] → fail closed、label 校验保留。**不**改变 Question Core / Gate / Admission 语义。

### 8.4 `20_Document_Pipeline.md` §7.2 步 1 — Compiler 确定性提取

**Current Frozen Text / Rule**（`20 §7.2`）：

```text
1. 逐 content role 从 resolved span（line / line_character）**确定性提取**正文 →
   `compiled_roles[]`，每个带 `text_hash`（= source slice hash，供 10 §8 2c 校验）。
```

**Proposed Frozen Text / Rule**：

```text
1. 逐 content role 从 resolved span（line / line_character / 其他 OD-01 provenance form
   所定位的 source slice）**确定性提取**正文 → `compiled_roles[]`，每个带 `text_hash`
   （= source slice hash，供 10 §8 2c 校验）。option leaf 的 label/text 来自 Preprocessing
   `options[]`（Producer segmentation authority），正文必须与 verified provenance locator
   所定位的 source slice 一致；provenance 进入 compiled source_span。禁止从 `options_lines`
   rediscovery 切分 option。
```

**Change Reason：** F-OD01-02：新增 form 后 Compiler 提取规则必须一并扩展，否则条款内部不一致。

**Impact：** 扩展确定性提取规则 → **CHANGE-3 成分**。text_hash / no generated prose 不变。

### 8.5 `20_Document_Pipeline.md` §7.3 — Question `dedup_key`（明确输入来源，不改组合）

**Current Frozen Text / Rule**（`20 §7.3`）：

```text
| Question `dedup_key` | canonical question type + own stem + own options
  （options 按 canonical label order 排序，声明序无关；label 重复 fail-fast） |
  排除 shared material / answer / explanation / image / question no. /
  page / source_version_id / unit_id / occurrence 信息
```

**Proposed Frozen Text / Rule**：

```text
| Question `dedup_key` | canonical question type + own stem + own options
  （options 按 canonical label order 排序，声明序无关；label 重复 fail-fast） |
  排除 shared material / answer / explanation / image / question no. /
  page / source_version_id / unit_id / occurrence 信息
【OD-01 注释性修订，组合不变】own options 的 label/text 作为 dedup 输入，来自
  Producer `options[]`（segmentation authority）经 V3 verification 后的规范化结果，
  不是 V3 从 options_lines rediscovery 的切片。Question identity 语义不变；本条不
  改变排除列表，不改变 label order / fail-fast 规则。
```

**Change Reason：** F-OD01-02 指出 option 来源变更后 dedup 输入来源会变，必须显式声明；同时 OD-01 **不借机改变 Question Core / Question identity 语义**（任务非目标）。

**Impact：** **组合与 identity 语义 UNCHANGED**；仅输入来源注释。归类 **CHANGE-1（Clarification）成分**（规范语义零变化的措辞澄清）。若 Owner 认为注释仍构成 L0 文本变更，走同一 CR-002 即可。

### 8.6 `20_Document_Pipeline.md` §6.1 — IR `content.options[label].source_span` 与链路关系

**Current Frozen Text / Rule**（`20 §6.1` 示例语义）：

```text
"options": {"A": {"source_span": {"span_id": "sp-Q1-A"}, "status": "resolved"}},
```

（V3 侧 per-label option 的 Resolved Span 表征；示例 span_id 为 `sp-Q1-A`，**不是** `sp-<unit>.option.<label>`。）

**Proposed Frozen Text / Rule**：

```text
"options": {"A": {"source_span": {"span_id": "sp-Q1-A"}, "status": "resolved"}},
【OD-01 链路语义】options["A"].source_span 是 Canonical V3 IR 中的规范化 provenance
  表达；其上游唯一链路为 Preprocessing options[].provenance（Producer 输入证据）
  → V3 Consumer verification/normalization → Frozen Resolved Span → IR source_span。
  三层不是并列 semantic authority。冲突时保留 conflict signal，不得静默覆盖，按
  review / unresolved / fail-closed 处理。示例 span_id 以本节为准（如 sp-Q1-A）；
  代码构造名不得回写为 Spec 要求。
```

**Change Reason：** F-OD01-04（权威关系）+ F-OD01-08（引用精度）。

**Impact：** 澄清单一 provenance authority path，对齐 OD-04；**不**改变 IR 字段结构本身。归类 **CHANGE-2/1**（新增链路约束语义 + 引用澄清）。

### 8.7 `10_Data_Model.md` §8 — provenance 不变量对新 form 的核验口径

**Current Frozen Text / Rule**（`10 §8` 不变量 2b/2c 摘要）：

```text
2b `source_span.line_ref`（及 offset）∈ `document_source_lines(source_version_id)`
   且行内 slice 存在；
2c resolved `text_hash ==` 该 source line/slice 的实际 hash；
```

**Proposed Frozen Text / Rule**：

```text
2b `source_span.line_ref`（及 offset）∈ `document_source_lines(source_version_id)`
   且行内 slice 存在；【OD-01】其他 provenance form 的 locator 必须能解析到该
   source_version 下可验证 source 实体/切片（table_cell → 可回溯 cell/raw；
   multiple_source_spans → 逐 span 满足本条；other/image_region → figure/region
   identity + 可回溯区域）；不可解析 → 不得视为 resolved。
2c resolved `text_hash ==` 该 source line/slice（或 form locator 所定位切片）的
   实际 hash；
```

**Change Reason：** F-OD01-02/F-OD01-04：新 form 下 2b/2c 核验必须可扩展且不被绕过。

**Impact：** 应用层 invariant 扩展；**非** DB schema 变更；**非** FK 变更。归类 **CHANGE-2 成分**。

### 8.8 `10_Data_Model.md` §6.3 — `source_span` JSONB 边界（对齐 `00 §5` JSONB 非目标）

**Current Frozen Text / Rule**（`10 §6.3`）：

```text
`source_span` 是 JSONB，不是 FK——PostgreSQL 无法强制它的引用与 hash 真实性。
它是应用层 provenance invariant，由 Resolver/Compiler/Gate 验证（§8 不变量 2a-2d）。
```

**Proposed Frozen Text / Rule**：

```text
`source_span` 是 JSONB，不是 FK——PostgreSQL 无法强制它的引用与 hash 真实性。
它是应用层 provenance invariant，由 Resolver/Compiler/Gate 验证（§8 不变量 2a-2d）。
【OD-01】JSONB 仅承载可验证 provenance 结构化扩展（form/locator/hash/status），
不得用 JSONB 隐式承载整个业务模型（00 §5 非目标不变）。DDL 是否需要正式列注释
仍待 Owner（Proposal §13）；本条不自动授权 schema change。
```

**Change Reason：** DSH 指出扩展 JSONB 与 `00 §5`「用 JSONB 隐式承载整个业务模型」红线需划界。

**Impact：** 明确红线边界；**不**改 DDL。归类 **CHANGE-1/2（澄清 + 边界约束）**。

### 8.9 受影响 Frozen Spec 文件/条款清单（汇总）

| # | File | Clause / lines（现行坐标） | 动作 | Change class 成分 |
|---|------|---------------------------|------|-------------------|
| 1 | `00_Master_Spec.md` | §5 非目标 table cell/fragment（约 `:274-275`） | 部分解除 / 改写 | CHANGE-3 |
| 2 | `00_Master_Spec.md` | §5 JSONB 隐式业务模型非目标 | **不改正文**；在 10 §6.3 划界引用 | —（保持） |
| 3 | `20_Document_Pipeline.md` | §5.3 `option_label`（约 `:280-281`） | **取代**为 Producer segmentation authority | CHANGE-3 |
| 4 | `20_Document_Pipeline.md` | §5.5 granularity / 延后注（约 `:322`） | 扩展 form 维度；改延后注 | CHANGE-2 + CHANGE-3 |
| 5 | `20_Document_Pipeline.md` | §6.1 IR option source_span 示例语义（约 `:365-369`） | 补链路权威语义 + 引用更正 | CHANGE-2 + CHANGE-1 |
| 6 | `20_Document_Pipeline.md` | §7.2 步 1 Compiler 提取（约 `:454`） | 扩展 form 提取规则 | CHANGE-3 |
| 7 | `20_Document_Pipeline.md` | §7.3 Question `dedup_key`（约 `:523`） | 注释性澄清输入来源；组合不变 | CHANGE-1 |
| 8 | `10_Data_Model.md` | §6.3 `source_span` JSONB 约束注 | 划界 + form 扩展说明 | CHANGE-1 + CHANGE-2 |
| 9 | `10_Data_Model.md` | §8 不变量 2b/2c | 扩展 locator/hash 核验口径 | CHANGE-2 |
| 10 | （治理）`90_DOCUMENT_GOVERNANCE.md` §11 | Change Audit Record | re-freeze 时登记 CA / CR | 流程义务（非本轮 L0 编辑） |

**明确不修改的条款（非目标）：** Gate 四层语义、Admission 语义、Question Core、Question/Unit canonical vocabulary、QT→UT 规则、P01–P25 其他决策、OD-02…G-02、历史重处理原则、Migration policy、X3 entry condition、`fragment` 延后本身。

---

## 9. Full Semantic Chain（必须形成的最终语义）

```text
Original Source
    ↓
AITutors-preprocessing
    ↓
Preprocessing Artifact
    ↓
options[].provenance
    ↓
V3 Consumer Boundary
    ↓
Identity / M1-M5 verification
    ↓
Frozen Resolved Span
    ↓
Canonical V3 IR
    ↓
Gate / Admission
```

其中：

> **Producer 提供 option segmentation 和 provenance 证据；V3 验证并规范化，不重新发现 option 边界。**

且：

> **OD-01 只解决 provenance / Resolved Span ontology 与相关 Frozen Spec 语义，不借机改变 Gate、Admission、Question Core 等其他冻结语义。**

---

## 10. 明确非目标 / 特别禁止

### 10.1 不改变

- Gate 四层既有语义
- Admission 既有语义
- Question Core
- Question / Unit canonical vocabulary
- QT→UT 不建立全局映射
- P01–P25 其他 Owner Decisions
- OD-02 / OD-03 / OD-04 / OD-05
- G-01 / G-02
- 历史数据重新处理原则
- Migration policy
- X3 entry condition
- `fragment` 延后（本轮不解除）

### 10.2 特别禁止（不得因为 OD-01）

- 修改数据库 Schema
- 修改生产代码
- 修改 preprocessing 实现
- 修改 Gate
- 修改 Admission
- 重跑历史语料
- 执行 migration
- **修改 Frozen Spec（本任务）**
- 宣布 re-freeze
- 进入 Phase 1

---

## 11. Change Classification / Affected Layers / Regression（F-OD01-07 要点；详见 CR-002）

### 11.1 变更分类（按 `90 §3`；拿不准往高里归）

| 成分 | 分类 | 依据 |
|------|------|------|
| 新增 polymorphic provenance form 维度 | CHANGE-2 | 新增强制可表达/可验证约束 |
| 新增 option `options[]` 结构语义落入 L0 | CHANGE-2 | 新增强制 invariant |
| 废止/改写 `00 §5` table_cell 延后非目标 | **CHANGE-3** | 改变既有规定的行为/范围 |
| 改 `20 §5.5` 延后注 / form 范围 | **CHANGE-3** | 改变既有规定 |
| 改 `20 §5.3` option 边界规则 | **CHANGE-3** | 改变既有规定的行为 |
| 改 `20 §7.2` Compiler 提取规则 | **CHANGE-3** | 改变既有规定的行为 |
| `dedup_key` 输入来源澄清 | CHANGE-1 | 组合不变的澄清 |
| 引用更正（sp-Q1-A） | CHANGE-0/1 | 编辑/澄清 |

**总体分类：CHANGE-3 — Normative Modification**（因含多项 CHANGE-3 成分；同时含 CHANGE-2 新增）。按 `90 §3`「拿不准往高里归」，**不得**只按 CHANGE-2 处理。

### 11.2 受影响层

| Layer | 是否受影响 | 说明 |
|-------|------------|------|
| L0 Frozen Spec（00/20/10 相关条款） | **YES** | 见 §8.9 |
| L0-META `90` | 流程登记义务 | §11 CA 登记在 re-freeze 时执行 |
| Frozen Contract P04 | **语义落入**；契约条文不改 | P04 已 CLOSED；本变更不改 P04 文本 |
| Consumer Boundary / Resolved Span / IR / Compiler / Gate Provenance（能力） | **YES（能力扩展）** | 不改 Gate condition 语义 |
| Gate Structural / Semantic / Admission | **NO（语义）** | 明确禁止 |
| DB Schema / Corpus / Preprocessing impl / Production code | **NO** | 本任务与 re-freeze 前均不改 |

### 11.3 所需回归范围（re-freeze 后、实现前的义务；本轮不执行）

1. Resolved Span 构造/解析/验证（全部 form + legacy 无 form 读取）
2. `char_span_in_line` ↔ `line_character`+offset 一致性
3. `table_cell` 可回溯与 fail closed
4. `multiple_source_spans` 有序 non-empty 与逐 span 校验
5. `other` / `image_region` identity+region+degraded 路径
6. option segmentation：消费 Producer `options[]`；**禁 rediscovery** 负向测试
7. fail-closed：unresolved / incomplete / QC_FAIL；禁止 0-span 静默通过
8. conflict signal：Producer vs V3 验证冲突保留且不静默覆盖
9. Compiler option leaf 提取 + text_hash（2c）
10. Gate Provenance form/locator/text 与 no double consumption 交互
11. Question dedup_key 输入来源（组合不变）回归
12. `options_lines` 与 `options[]` 并存保留

---

## 12. Test Impact（required after re-freeze + Owner Authorization）

**Preprocessing：**

- 正常 option extraction（`options[]` + `options_lines` 并存）
- 多行 option（`multiple_source_spans` / 跨行 `line_range`）
- 表格 option（`table_cell`）
- character-span provenance（`char_span_in_line`）
- 图片化选项（`other`/`image_region` + degraded）
- 无法可靠识别 → `unresolved` / fail closed
- malformed option → 拒绝
- 禁止 silent fallback
- label/text/provenance 可验证

**V3：**

- 消费 polymorphic provenance 各 form
- **禁止 V3 rediscovery**（不得从 `options_lines` 自行切 option）— 负向测试
- 未知 form / 坏 locator → fail closed
- 与 text_hash / double-consumption 规则交互
- 旧 line-only span 兼容读取（若 Owner 批准 legacy rule）
- conflict signal 路径

---

## 13. Owner Approval Required（修订后清单）

```text
[ ] 1. Approve ontology form names + field names as proposed (or amend)
[ ] 2. Pin char_span encoding unit (UTF-8 code units vs Unicode scalar values)
[ ] 3. Approve table_cell identity/locator form
[ ] 4. Approve legacy source_span reading rule (no form → line_range?)
[ ] 5. Approve whether InstanceRoleContent.source_span JSONB extension
       needs formal 10_Data_Model text update (vs JSON-only convention)
[ ] 6. Approve Gate Provenance validation depth (exact vs normalized for each form)
[ ] 7. Explicit Freeze Order / re-freeze of affected Frozen Spec sections
[ ] 8. Approve fail-closed model: option resolution_status {resolved,unresolved,
       incomplete} + QC_FAIL；废止独立 options_unresolved 语义字段；resolved ⇒
       provenance 1..n（禁止 0-span 静默通过）          ← F-OD01-05
[ ] 9. Confirm option segmentation authority = Producer Artifact only；
       20 §5.3 option_label 规则按 §8.3 取代（无 fallback rediscovery） ← F-OD01-03
[ ] 10. Confirm provenance single chain
        (options[].provenance → Frozen Resolved Span → IR source_span)
        + conflict signal 不得静默覆盖                      ← F-OD01-04
[ ] 11. Confirm image_region = other(method=image_region) 正式实例，非顶级 type
                                                         ← F-OD01-06
[ ] 12. Approve CR-002 change classification (CHANGE-3 overall) 与回归范围
                                                         ← F-OD01-07
```

**在上述完成并 re-freeze 之前：**

```text
OD-01 = APPROVED DESIGN DECISION
PENDING FROZEN SPEC INCORPORATION
NOT EFFECTIVE AS FROZEN SPEC
L1 Change Record CR-002 = PROPOSED / OWNER AUTHORIZATION REQUIRED / NOT EFFECTIVE
Phase 1 P04 Resolved Span implementation: NOT STARTED
Frozen Spec: UNCHANGED
```

---

## 14. Explicit Diff 范围声明

- 条款级 explicit diff 已在 **§8** 交付（F-OD01-02），覆盖 §8.9 清单中全部实际受影响条款。
- 正式 L0 文本采纳将在 Owner 指示的 re-freeze change set 中以 track-change / 完整章节替换方式提出。
- **本文件不直接编辑 `Docs/V3_SPEC/**`。**
- Illustrative 快捷摘要（非正式、非完整；完整以 §8 为准）：

```text
+ Resolved Span provenance forms (OD-01):
+   line_range | char_span_in_line | table_cell | multiple_source_spans | other
+   image_region = other(method=image_region)，非顶级 form
+ Option structured evidence (P04):
+   options[] = { label, text, provenance[] }  # resolved ⇒ provenance 1..n
+   options_lines MUST be retained alongside options[]
+ Option segmentation authority = Producer Artifact（V3 不 rediscovery）
+   20 §5.3 option_label V3 边界规则被取代
+ Fail-closed: option resolution_status + QC_FAIL；废止独立 options_unresolved
+ Unreliable → unresolved / incomplete / QC_FAIL；禁止伪造；禁止 0-span 静默通过
+ Provenance single chain + conflict signal；对齐 OD-04
+ 00 §5 table_cell option-provenance 子集解除；fragment 仍延后
+ Compiler 提取扩展至新 form；dedup_key 组合不变（输入来源澄清）
```

---

## 15. Risk

| Risk | Level | Mitigation |
|------|-------|------------|
| char offset 编码定义不一致（UTF-8 byte vs codepoint） | **HIGH** | re-freeze 时必须钉死一种并写入 Frozen 文本（§13 #2） |
| table_cell 坐标在 OCR/HTML 转换后不稳定 | **HIGH** | 要求 cell identity 可回溯 raw；否则 `unresolved` |
| Consumer 误把 line-only legacy span 当多态 | MED | 显式 legacy reading rule + fail closed on unknown form |
| 实现方把 provenance 扩展误当成 Gate 新条件 | MED | §14/§10 明确禁止；OD-03/P14 约束 |
| 与 P05 composite 内部结构混淆 | LOW | 不改变 composite = 一个 Question |
| 误把 Proposal / CR-002 当已生效 Frozen Spec | **HIGH** | 文首 STATUS 显著声明；re-freeze 前禁止宣称号称生效 |
| 双 provenance authority 复活（Producer 与 Resolver 并行切 option） | **HIGH** | §3.2/§8.3 明确取代 §5.3；禁 fallback rediscovery |
| fail-closed 双字段歧义回归 | MED | §3.4 唯一承载模型；废止独立 `options_unresolved` |

---

## 16. Rollback Considerations

- Proposal / CR-002 阶段无生产变更 → 回滚 = 撤回 Proposal / Change Record（或标 REJECTED）。
- re-freeze 后：回滚需新的 Owner Decision + Frozen Spec revision；**不得**在 Implementation 中单方面 revert ontology。
- Producer 已按新 shape 产出的 Artifact：若 re-freeze 被拒，Artifact 侧字段可保留在 Producer schema（OD-05）但 V3 不得按未生效 ontology 消费 —— 届时 STOP。

---

## 17. Governance 路径（F-OD01-07）

正式链路：

```text
OD-01 Owner Decision
        ↓
OD-01 Frozen Spec Change Proposal（本文件 v2）
        ↓
L1 Contract Change Record（CR-002）
        ↓
Owner Authorization
        ↓
L0 Frozen Spec modification
        ↓
re-freeze
```

**本次任务只完成到：L1 Change Record 已建立并准备进入 Owner Authorization。**

| Governance 项 | 状态 |
|---------------|------|
| Change classification | CHANGE-3 overall（含 CHANGE-2/1 成分）— 已登记 |
| Affected-layer identification | 已登记（§11.2） |
| Required regression scope | 已登记（§11.3）；**不在本轮执行** |
| Status header / registration | 本 Proposal 与 CR-002 已按 `90 §4` 补 Status Header |
| `90 §11` Change Audit Record | **待 re-freeze 时登记**（本轮 L0 未改，CA 行随实际 L0 commit 产生） |
| Owner Authorization | **REQUIRED / 未授予** |

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` |
| Document Type | Frozen Spec Change Proposal |
| Authority Level | L1-proposal（非 L0） |
| Status | **PROPOSED / OWNER AUTHORIZATION REQUIRED / NOT EFFECTIVE** |
| Normative | NO（对 L0 尚未生效） |
| Supersedes | 本文件 v1（2026-09-23 Proposal） |
| Superseded By | — |
| Gate State Authority | NO |
| Owner Decision | OD-01 + F-OD01-01~08 dispositions |
| L1 Change Record | `CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` |
| Effective Frozen Spec | **UNCHANGED** (`Docs/V3_SPEC/**` @ `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`) |
| Re-freeze | NOT DONE |
| Phase 1 | NOT ENTERED |
