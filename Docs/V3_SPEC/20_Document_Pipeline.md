# AI Tutor V3 — 文档解析与题目编译管线（Annotation → Resolver → IR → Compiler → Gate）

Version: v1.2（Baseline—Frozen，2026-09-05）
Status: V3 收敛基线（20 分册）— 已落实对抗性审查 3×P0 + 6×P1 与冻结前 2 条文字钉死，冻结
Date: 2026-09-05
Supersedes: `Docs/V3_DOCUMENT_PIPELINE.md`（起草输入）;上位约束 `00_Master_Spec.md`
（不可修改）;落库契约 `10_Data_Model.md`（v1.2，字段权威）;任务/审计 `30`
（stage 执行与预算）;字段权威参考 `docs_archive/2026-09-03/00-04 v0.3` 系列契约

> 本分册只定义**阶段对象的 in-flight 契约**：Semantic Annotation（L2）manifest、
> Semantic Reference、Source Resolver、Semantic Question IR、Deterministic Compiler、
> Evidence/Semantic Gate、Answer 三字段。**每个阶段的持久化去向一律由 10 定义**；
> 本分册不引入任何新数据库表。术语裁决以 `README.md` §2 为准。

---

## 1. 定位：本分册回答"10 的 Candidate payload 是怎么被稳定产出的"

10 定义了 A/B/C 三域表：B=sealed source，C=annotation + candidate 快照，
A=admission 后 live 实体。**10 没有定义"中间对象长什么样"**——那是本分册的职责。

```text
10 持久化                    20 阶段对象（transient，本分册）
─────────                   ─────────────────────────────
document_source_versions ←─ L1 seal（见 10 §4，此处不再重复）
semantic_annotations     ←─ Semantic Annotation manifest（§4 本册）
（无独立表）               ←─ Source Resolver run（transient，§5 本册）
（无独立表）               ←─ Semantic Question IR（transient，§6 本册）
（无独立表）               ←─ Deterministic Compiler 输出（transient，§7 本册）
admission_candidates     ←─ Candidate payload 快照（含 IR/resolved spans/gate 证据，10 §5.3）
admission_events + A 域   ←─ Admission Transaction（10 §5.4）
```

**第二数据模型禁令**：Resolver run / IR / Compiled snapshot 是纯 transient 处理对象；
它们在 M1 的持久化形态是 `admission_candidates.payload`（完整快照）+
`input_identity` / `build_versions`（重放身份）。任何"为 Resolver/IR 另建一套中间表"
的提议都违反 10 的裁剪决定与 00 P5，除非有明确的跨阶段复用/审计需求并经评审。

---

## 2. 与 10 的逐表契约锚点（本分册每节最终落向 10 哪张表）

| 20 节 | 阶段对象 | in-flight | 持久化（10） |
|---|---|---|---|
| §4 | Semantic Annotation | manifest | 10 §5.1 `semantic_annotations.payload` |
| §5 | Source Resolver | resolved spans/relations | 仅并入 IR 与 candidate payload（无表） |
| §6 | Semantic Question IR | units + dependencies | 仅并入 candidate payload（无表） |
| §7 | Deterministic Compiler | compiled roles + display_hint | 仅并入 candidate payload（无表） |
| §8 | Gate | 分层 pass/fail + decision | 10 §5.2 `gate_decision`/`decision_status` |
| 10 §5.4 | Admission | 物化 A 域 | question/instance/role/material/image/unit |

provenance 规约：任何阶段若需落持久化（annotation、candidate），必须带 10 §3 的
stage-scoped `logical_execution_stage/hash` + `attempt_id` + `source_version_id`；
Resolver/IR/Compiler 这些确定性阶段本身不产生独立的逻辑执行记录——它们共享
**compile stage** 的 (stage, hash)，见 §7.1。

---

## 3. 链上分工与不可违反的边界（00 P1/P2/P3 的管线化）

```text
LLM Semantic Annotation   → 语义 claim（判定题型/结构/依赖/归属/引用建议），无位置事实
Source Resolver           → 把 Semantic Reference 解析为 Resolved Span（确定性，不猜）
Semantic Question IR      → 已解析 question/composite 语义 + 依赖闭合（唯一 Compiler 输入）
Deterministic Compiler    → 从 resolved span 编译正文与 display_hint（确定性，不生成新文本）
Evidence/Semantic Gate    → 结构/来源/语义/准入四层判定（Admission Authority 属 Gate Policy）
Admission Transaction     → 原子物化 A 域（10 §5.4）
```

硬边界：

1. Source 只能被读取；Annotation/Resolver/Compiler/Gate 不得修改 sealed source。
2. Annotation 只携带 claim 与 Semantic Reference；**不携带 resolved span / line_ref /
   正文 / canonical type**。
3. IR 只接受已解析的 span；不接受未解析的 question_label 字符串。
4. Compiler 只做确定性编译，不改变 IR，不补语义。
5. Gate 只判断是否满足准入标准，不修改内容，不做语义猜测。
6. 从 Annotation 之后到 Candidate 之前，任何缺失只能 → incomplete/ambiguous，**禁止
   后处理规则补语义**（00 §5/§6：V2 "每修一个洞加一条特判"是禁止的）。

---

## 4. Semantic Annotation（L2）契约

### 4.1 Envelope 与 Payload 分离

LLM 只输出**语义 payload**；Envelope 字段由 pipeline 注入。持久化：envelope 信息
（schema/version/run/source 元数据）进 10 `semantic_annotations` 列；`payload` 存
10 `semantic_annotations.payload`（JSONB）。

| 属于 | 字段 | 说明 |
|---|---|---|
| pipeline 注入（不进 payload） | annotation_schema / annotation_version / annotation_run_id / source_version_id / document_id / annotation_meta / metadata 最终判定 | LLM 不猜程序 ID，不混入坐标/版本 |
| LLM payload | document_metadata_claims / sections / semantic_units | 语义 claim 本体 |

### 4.2 Manifest 顶层

```json
{
  "annotation_schema": "semantic-metadata-annotation/v0.3",
  "source_version_id": "<uuid>",
  "document_metadata_claims": {"subject": null, "grade": null, "year": null, "school": null},
  "sections": [],
  "semantic_units": [],
  "annotation_meta": {"model": "...", "prompt_version": "...", "status": "complete", "warnings": []}
}
```

- `source_version_id` 指向 sealed version；`document_metadata_claims` 是 annotation claim，
  M1 **直接映射**为最终事实的 subject/grade（BUG-V3-021 终裁：删除 V2 遗留的「上传/文件名
  优先级（02 §15）」链；不再引用已删的 02 册）。
- `semantic_units` 以 question/composite 为中心；`annotation_meta` 是诊断元数据。

### 4.3 递归禁止字段（schema 校验，失败即 invalid，不过滤继续）

```json
["line_refs", "corrected_line_ids", "resolved_span", "final_line_ids",
 "canonical_question_type", "answer_text", "stem_text", "material_text",
 "options_text", "explanation_text"]
```

任意深度出现即整体判 invalid；LLM 不输出正文，答案正文由程序从答案来源切片。

### 4.4 Semantic Reference（受控引用，替代 V2 "Anchor"）

LLM 指认源位置时不输出行号、不转录正文，只输出受控 reference：

```json
{
  "role": "shared_material",
  "label": "M1",
  "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair", "text": "阅读下面短文"},
  "end_marker":   {"kind": "instruction_marker", "granularity": "multi_line_pair", "text": "根据上述材料回答第11～13题"}
}
```

kind 表：

| kind | 内容 | 禁携带 |
|---|---|---|
| question_label | 题号/子题号 `1`/`11` | 正文 |
| option_label | 选项字母 `A` | 正文 |
| blank_label | 空位标识 `第1空` | 正文 |
| instruction_marker | 源中短边界/任务指令 | 整段材料/题干/答案/详解 |
| answer_zone | `answer_table`/`inline_answer` | 答案正文 |
| explanation_zone | `inline_explanation` | 详解正文 |

规则（02 §4.2/§20.3 收敛）：

- instruction_marker 必须声明 `granularity`：`line_fragment`（单行内片段）/
  `single_line`（整行） / `multi_line_pair`（start/end 两个单行 marker）。**禁止跨行
  全文**。
- marker.text 规范化后必须在 source 中出现；缺失 → missing，多命中 → ambiguous，
  **不得猜第一匹配**。OCR 拆行仅在 Annotation 显式 `allow_continuation` 且拼接后仍
  唯一时允许，否则 ambiguous。
- Semantic Reference 不进入 Resolver 之外的地方当作坐标事实；它只是"引用建议"。

### 4.5 Semantic Unit（standalone / composite）

**standalone_question**：

```json
{
  "unit_id": "Q1", "unit_type": "standalone_question", "question_number": "1",
  "section_id": "SEC-1", "original_question_type": "single_choice",
  "content": {
    "stem":       {"role": "stem", "question_label": "1"},
    "options":    [{"label": "A", "role": "option", "question_label": "1"}],
    "answer":     {"role": "answer", "question_label": "1", "answer_zone": "answer_table"},
    "explanation":{"role": "explanation", "explanation_zone": "inline_explanation"}
  },
  "confidence": 0.98
}
```

**composite_unit**：`unit_id`（如 `U11-13`）+ `unit_type=composite_unit` +
`question_number_range` + `shared_components{material/word_bank/shared_option_pool/
task_instruction}` + `sub_questions[]`（每个含 stem/options/answer +
`depends_on[{type:"material_dependency", target:"M1", required:true}]` +
`requires_material_context`）。`sub_questions` 允许递归 `sub_sub_questions`，每层沿用
同一 content/dependency 模型。

契约要点：

- annotation **最多**带 `original_question_type`；`canonical_question_type` 属
  IR/Compiler，禁止出现在 LLM payload。
- `answer` 只声明"答案在答案表/题后答案区"，**不保存答案正文**。
- composite 原子性由 IR/Gate 不变量保证，不由 LLM 声明；`independent` 一词只保留给
  DISPLAY_CONTRACT 的独立题语义，composite 子题不得使用 `independence_after_material`
  等反向字段。
- blank/option/answer/image 必须有 owner（question 或 composite）；同一 document-local
  question 不得属于两个 unit。

**blank/image content 形态（BUG-V3-013 终裁，M1 minimal shape）**：

```json
{
  "blank": [{"blank_label": "1", "question_label": "1"}],
  "image": {"image_ref": {"figure_id": "fig-001"}}
}
```

- `blank`：list（或单 dict）；每项 `blank_label`（**必填**，unit 内 blank identity）+
  `question_label`（可选，闭合到具体 question）。术语统一用 `question_label`（V3 已有），
  不用 `question_number`。
- `image`：dict；`image_ref` 须 dict，`figure_id`（可选）是 **M1 唯一图像引用 identity**
  （不提前加 image_url/inline payload/bbox/file path，这些延后 D-6 Figure Contract）。
- **malformed shape（非 dict/list、缺必填 `blank_label`、`image_ref` 非 dict）→ fail-fast
  （ValueError），绝不 silent skip**；合法 shape 但引用对象不存在 → resolver
  missing/ambiguous/incomplete 状态（§5.5）。

### 4.6 关系与闭合（relations / mapping）

关系表：`contains`、`material_dependency`、`word_bank_dependency`、
`option_pool_dependency`、`blank_mapping`、`option_mapping`、`image_reference`、
`scoring_standard_of`。

闭合规则：同一 unit 的所有 dependency target 必须存在；blank/option/answer/image
映射必须闭合到具体 question/sub-question，悬空即 invalid；同一层依赖 target 必须能
回溯到该 unit 或祖先 unit 的 shared component（02 §9）。

### 4.7 Annotation 重试与 superseded（10 §5.1 `status` 的写入者）

- Resolver 判 `incomplete`（§5.2）→ **回 Annotation 聚焦重试**：新的一次 annotation
  逻辑执行（新 annotation stage 键），**不产生 candidate**。
- 重试成功的新 annotation 落库后，Application 提交步骤可把被替换的 annotation 置
  `superseded`（10 §5.1：valid / invalid / superseded）。**写入者是确定性 Application
  步骤，无 LLM。** `status` 只是生命周期状态，**不是默认选择器**（BUG-V3-009 终裁）。
- 消费规则（BUG-V3-009 终裁）：**M1 禁止 implicit/default annotation 选择**——所有消费
  annotation 的运行路径必须**显式提供 `annotation_id`**（candidate 的
  `input_identity.annotation_id` 指它实际消费的那条，10 §5.3）；不存在「默认最新
  annotation」。`annotation_id` 缺失或未解析到 valid annotation → **fail-fast**
  （RepositoryError），绝不自行查询「最新 annotation」。历史（含 superseded）行保留，
  供 00 P7 Rebuild 显式引用；禁止对同一 source 静默多消费 / 多 candidate 混指。

---

## 5. Source Resolver（Semantic Reference → Resolved Span）

### 5.1 输入输出与纯函数要求

输入：sealed `source_version_id` + annotation（payload）。输出：resolved spans +
resolved relations。约束：

- **确定性**：同输入同输出（10 §9 Exact Replay 的前提）。
- 不修改 annotation；不新增 source 行（IS-3：Resolver 不得在 seal 后回写 cell/
  fragment）。
- 只消费该 annotation 声明的 `source_version_id`，不假设与 active 一致。

### 5.2 解析级联与状态

```text
Exact Match → Normalized Match → Context/Structural Match → Fuzzy Match → Ambiguous/Missing
```

| status | 含义 | 可进入 ready IR | 去向 |
|---|---|---|---|
| exact | 唯一精确命中 | 是 | resolve |
| normalized | 规范化后唯一命中 | 是 | resolve |
| contextual | 逐条件证据闭合后唯一（见 5.4） | 是（必须逐项证据闭合） | resolve |
| fuzzy | 有近似候选，边界/语义不能唯一证明 | 否 | pending_review 候选 |
| ambiguous | 多候选无法确定 | 否 | pending_review 候选 |
| missing | 源中不存在 reference | 否 | pending_review 候选 |
| incomplete | Annotation 缺必要 claim/ref | 否 | 回 Annotation 聚焦重试 |

Normalized 至少处理：全半角、空白、中英文标点、OCR 转义噪音、题号前后缀；规范化后
仍多候选 → ambiguous，**不随机选择**，也不引入 "nearest" 作为自动可接受状态。

### 5.3 Role Resolution 规则（摘要）

- **question_label**：定位题号；stem 起点 = 确定性位置；终点只能由显式边界证据
  （下一题/option/answer/explanation/section boundary）闭合，无唯一边界 → incomplete，
  不得默认"最后一个内容行"。
- **option_label**：按 A/B/C/D 顺序；每项到下一标签/下一题结束；重复标签 →
  ambiguous；缺标签 → incomplete。
- **material**：用 instruction_marker start/end 精确定位；无显式 end 不得按下一题/
  section 自动扩展 → incomplete；须验证 span 不含子题 stem 专属内容、不与其他
  material/answer span 重叠。
- **answer**：`answer_zone=answer_table` 按 question_label 定位答案行；
  `inline_answer` 按【答案】区；Resolver 只输出答案 source span，不生成答案正文。
- **explanation**：定位【详解/解析】区；找不到完整区域 → ambiguous，不截断。
- **blank**：一个 blank 必须映射到一个 sub_question/answer；无闭合 → IR incomplete。
- **image**：reference 必须解析到 source version 图片索引；图须带 page/bbox/
  placement/source；无唯一图 → ambiguous，禁止跨题广播。

### 5.4 Contextual 自动通过条件（03 §4.2 收敛）

仅当以下全部满足才可当作 resolved 进入 **ready IR / 待审 Gate**。注意 resolved ≠ 自动
准入：**任一 content role 为 contextual 的候选不得自动 approve**（§8.2）——contextual
的用途是给人工审一份证据完整、可编译成 pending_review 候选的快照，而非获得 auto 资格：
(1) exact/normalized 无唯一候选且候选数>1；(2) 可仅凭 role/question_label/section
顺序/显式 dependency 收窄到恰 1 个；(3) 收窄只用 Annotation 已声明语义与 sealed
source 确定性边界，不推断缺失依赖、不按行号重叠补语义；(4) 边界证据来自显式 role
spec/answer_zone/instruction marker/下一 question 边界——若仍需文本相似度/nearest/
字符近似才成立 → 降级 fuzzy；(5) evidence 列出每个收窄步骤，任一候选无法被排除 →
ambiguous；(6) contextual 不得静默改 Annotation，保留候选集快照。

### 5.5 Resolved Span 输出

```json
{
  "span_id": "sp-Q1-stem", "source_version_id": "<uuid>",
  "start_line_ref": "P1L001", "end_line_ref": "P1L002",
  "line_refs": ["P1L001", "P1L002"],
  "granularity": "line",
  "start_offset": null, "end_offset": null,
  "text_hash": "<sha256>", "resolution_status": "exact",
  "evidence": ["question_label=1", "next_boundary=Q2"]
}
```

- `granularity` ∈ {line, line_character}（M1；table_cell/fragment 延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 必须能唯
  一定位"同行多题答案/单行多选项"场景。
- `text_hash` 由程序按该 span 实际内容计算；同一 source version 内 span 可重放。
- **Annotation 不得包含本结构**（只在 Resolver 及之后出现）。

Resolved Relation：

```json
{"from": "Q11", "to": "M1", "type": "material_dependency", "resolved_target_span": {"span_id": "sp-M1"}, "status": "resolved"}
```

关系必须全部 resolved，IR 才可 ready。

---

## 6. Semantic Question IR

IR 是 Resolver 与 Compiler 之间的唯一中间表示（README：V3 不再用裸 "Question IR"）。
IR 是 **已解析** 的：每个 content role 都带 resolved span；每个 dependency 都带
resolved target span。

### 6.1 结构

```json
{
  "ir_schema": "semantic-question-ir/v0.3",
  "source_version_id": "<uuid>",
  "annotation_id": "<uuid>",
  "units": []
}
```

**standalone unit**：

```json
{
  "unit_id": "Q1", "unit_type": "standalone_question", "question_number": "1",
  "content_roles": {"stem": "required", "options": "required_for_choice", "answer": "required", "explanation": "optional"},
  "content": {
    "stem":    {"source_span": {"span_id": "sp-Q1-stem"}, "status": "resolved"},
    "options": {"A": {"source_span": {"span_id": "sp-Q1-A"}, "status": "resolved"}},
    "answer":  {"source_span": {"span_id": "sp-Q1-answer"},
                "answer_status": {"source_located": true, "complete": true, "verified_correct": null}}
  },
  "relations": [],
  "semantic_status": "ready"
}
```

**composite unit**：`unit_id`（`U11-13`）+ `unit_type=composite_unit` +
`question_number_range` + `shared_components{material/word_bank/option_pool}`（各带
resolved span）+ `sub_questions[]`（每个子题同 standalone 的 content/answer_status/
relations，且必须有指向同 unit shared material 的 `material_dependency`）+
`semantic_status`。IR **不重复保存共享材料正文**，只保存 span 与关系。

### 6.2 IR 完整性不变量（03 §9 收敛）

1. role 是否必需按 content_roles + 题型解释；不得把 options 写成所有题型必填。
2. composite 的所有 sub_questions 同属一个 unit；递归子题回溯到最近父 unit。
3. 每个 material_dependency target 解析到同 unit shared material。
4. blank/option/answer 映射闭合，无悬空引用。
5. 一个 sub_question 不能同时属于两个 unit。
6. 共享材料只出现一次，不落在任何子题 stem span 内。
7. 任一子题 unresolved → composite 整体非 ready。
8. `semantic_status=ready` 才可进入 Compiler；`ready` 之前任何状态都不得进自动准入。

---

## 7. Deterministic Compiler（IR → Compiled Snapshot / Candidate payload）

### 7.1 边界与身份

Compiler 是 **compile stage**（resolver→ir→compiler→gate 整段）的确定性收口。它把
ready IR 编译成 10 §5.3 的 candidate payload。作为确定性阶段，**不单独产生逻辑执行
记录**；compile stage 的 `logical_execution_stage/hash` + `attempt_id` 记在最终
candidate（10 §5.2），输入侧身份记在 `input_identity`。

Compiler 允许：按 resolved span 提取文本、组装选项/子题/材料、映射 canonical
question type、生成 provenance 与 text_hash、计算 dedup 规范化键、组装 payload。

Compiler 禁止：语义猜测、判断是否共享材料、猜测 blank/option/answer 映射、修改
Annotation/IR、在无 resolved span 时生成正文、生成 Source 中不存在的任何文本。

### 7.2 编译步骤

1. 逐 content role 从 resolved span（line / line_character）**确定性提取**正文 →
   `compiled_roles[]`，每个带 `text_hash`（= source slice hash，供 10 §8 2c 校验）。
2. canonical question type 映射：`original_question_type` → DISPLAY_CONTRACT
   `canonical_question_type`；**映射失败 = incomplete，不得以 NULL 静默入库**。
   content_roles 按 canonical type 的 role spec 判定（哪些 role required）。
   **映射为 exact passthrough（BUG-V3-014 终裁）**：`original ∈ 12 canonical → 原样`，
   否则 `None → incomplete`；禁 alias resolver（`single-choice`/`单选题` 不映射）。
3. shared material **只输出一次**，绝不复制进任何子题 stem。A 域 material 行
   （10 §6.4）的 `text` 在 Admission 内对 shared-material resolved span 做**确定性编译**
   得到；payload 不携带材料副本（只经 ir_snapshot 存 span + 关系）——材料正文从不进
   子题 stem，也不进任何 live 结构两份并存。
4. answer：从答案 source span **确定性提取**答案正文 + 置 `answer_status` 的
   `source_located/complete`；`verified_correct` 的置 true 规则见 §8.3。
5. figure_refs[]：由 image reference 的归属（owner=unit/sub_question + role）产出
   `(figure_id, role, order)`，仅当 figure 通过 IS-7（page/bbox/placement/source）。
6. 去重身份（**per 待物化实体**，非整个 candidate 一键）：规范化规则见 §7.3；
   **Admission 层不再二次 normalize**（10 §6.1 P1-2）。
   - 每个待物化 Question（standalone 或 composite 的每个 leaf，10 §6.1）基于其
     **own stem+options** canonical content 产一个 `dedup_key`——**不把共享材料内容
     混入子题键**（材料有独立去重，见下）；
   - 每个 shared material（10 §6.4）单独产一个 material `dedup_key`。
7. 每个待物化 Instance 产 `occurrence_key`（10 §6.2 下放构造）：`unit_id/question_number
   + resolved stem span` 的确定性组合（span 经 §7.3 canonical serialization 后 hash）。
8. 组装 10 §5.3 payload：`ir_snapshot / resolved_spans[] / compiled_roles[] /
   answer[] / figure_refs[] / knowledge_links[]（可选）/ evidence[] / display_hint`。
   `evidence[]` = **Resolver/Compiler 证据**（per-span resolution evidence + compile
   provenance，§5.5/§7.2.1/§7.2.2 摘要）；Gate 的 pass/fail+reasons 不在此处——属
   candidate 行 `gate_decision` 列（10 §5.2，见 §8.1 归属）。

display_hint = `{canonical_question_type, content_roles}`，保证与 DISPLAY_CONTRACT
兼容；Compiler 不得反向修改 IR。

### 7.3 Normalization Contract（dedup / occurrence / input 身份的共同地基）

第一性原理：Exact Replay（00 P7）与精确去重的正确性**完全取决于规范化规则的确定性**；
规则本身是 build 输入，必须版本化——否则规则一改，dedup_key / occurrence_key /
input_identity 各 hash / logical_execution_hash 全部漂移却无版本信号。

- **作用于**：`dedup_key`（per-Question、per-Material）、`occurrence_key`、
  `input_identity`（10 §9）、`logical_execution_hash`（10 §3）的计算输入。
- **规则**（Compiler 内唯一实现，禁止 Admission / Resolver 侧再实现第二份）：全半角
  折叠、空白与换行折叠、中英文标点归一、Unicode NFKC、题号/选项前后缀剥离；
  **LaTeX 数学环境内空白/换行折叠（structural，BUG-V3-015 终裁）**：`$...$`/`\[...\]`
  内 `\s+`→`""`；**不做符号/语义等价**（`\frac{1}{2}`≠`0.5`、`x^2`≠`x²`、
  `\sqrt{x^2}`≠`|x|`）。canonical identity ≠ mathematical equivalence。具体清单随
  实现评审固化，附 golden 正/反例（50）。
- **`text_hash` / `source_span` 保持 raw**：`text_hash` = source line/slice 的实际字节
  hash（10 §8 2c），**绝不套 normalization**；normalization 只作用于上述身份键。二者
  不可混用——这是 provenance 校验（2c/2d）不失效的前提。
- **跨行 text 的 canonical 拼接（BUG-V3-012 终裁）**：span 覆盖多行时，`text` =
  `"\n".join(line.text for line in span.line_refs)`（**按 `line_refs` 声明顺序，非行号重排**）；
  拼接符固定单个 `\n`（U+000A）；每行 `text` 原样（UTF-8），**不 strip / trim /
  whitespace-normalize / 插入额外空格**；单行 span = 该行 `text` 本身。`text_hash` 再对
  最终 `text.encode("utf-8")` 计算。
- **版本化**：normalization 规则版本记入 `build_versions`（10 §9）；升级走 Rebuild
  （新 compile 逻辑执行 + 新 candidate），不改旧行（10 §11）。

#### 三 key 的 canonical input（冻结，防实现歧义）

| Key | canonical input（仅此组成） | 明确排除（不得参与 hash） |
|---|---|---|
| Question `dedup_key` | canonical question type + own stem + own options（options 按 canonical label order 排序，声明序无关；label 重复 fail-fast） | shared material / answer / explanation / image / question no. / page / source_version_id / unit_id / occurrence 信息 |
| Material `dedup_key` | canonical material type + own material compiled text | question / instance / unit / source location / source_version_id |
| Instance `occurrence_key` | document-local unit/question identity（unit_id + question_number）+ resolved stem span（§7.3 serialization） | **`question_id`**（occurrence identity 与 canonical Question ID 无关，支持同一 source occurrence 映射到同一已复用 Question） |

三键共同铁律：**Question identity ≠ Answer identity**（answer 变化不拆 Question）；
**Question canonical input 不含 shared material**（材料排版/OCR 差异不得把同一题拆裂，
材料走独立 material identity，10 §6.4 source-scoped）；`occurrence_key` 是 document-local
occurrence 身份，先于 question_id 存在。

**options canonical label order（BUG-V3-019 终裁）**：选项按 **label 的 UTF-8 字节字典序**
（Unicode 码点序，locale 无关）排序，与源声明序无关；对 choice 题（A/B/C/D 单 ASCII 大写）
与 DISPLAY_CONTRACT §0.2 自然序一致。label 重复（同一 label 出现两次）在 canonical
dedup serialization 时必须 **fail-fast**。排序由 Compiler 内唯一实现，Admission 侧复用
同一纯函数，禁第二份实现。

---

## 8. Evidence / Semantic Gate（分层 + decision_status）

### 8.1 四层与职责

| 层 | 检查 | 关键不变量 |
|---|---|---|
| Structural | payload schema 合法；必填字段；span 非空且 line_ref 在 source version 内；granularity/offset 与 role 一致；题型可解释 | — |
| Provenance | 所有正文可溯源；`text_hash` = source line/slice 实际 hash（10 §8 2c）；无 generated prose；exact/normalized 才自动；contextual 须附 evidence；fuzzy/ambiguous/missing 不自动过 | 10 §8 2a-2d |
| Semantic | standalone 无必需 material_dependency；composite 依赖完整；blank/option/answer 闭合；子题 image 归属正确；材料不重复；语义状态与 IR 一致 | IR 不变量 |
| Admission | 前三层全过 + answer 达自动标准 → approved；否则 pending_review/rejected | 10 §5.4 |

Gate **只产出 pass/fail + reasons**，不修改 content，不做语义猜测（00 §5）。
分层判定与 reasons **只写入 candidate 行 `gate_decision` 列**（10 §5.2），**不写回
payload**——payload 是不可变编译产物，其 `evidence[]` 仅含 Resolver/Compiler 证据
（P0-1 归属，§7.2.8）。

annotation 的 `confidence`（§4.5）是**诊断元数据**（annotation_meta），**不作 decision
触发**；pending_review 只由确定性状态触发（§8.2），防"LLM 自评分隐形掌权"（P1-6）。

### 8.2 decision_status 落库（与 10 §5.2/§5.4 对齐）

决策归属（P2）：`decision_status` 只由确定性 Gate Policy 或人工 approve/reject 写入；
LLM 调用不写本列。

- **自动 approve()**：三层全过 + answer 达自动标准。前置：**所有 content role 的 span
  resolution ∈ {exact, normalized}**——任一 role 为 contextual 即不得自动准入
  （contextual 可进 ready IR 供人工审，但不 byte-proven；见 §5.4/§8.3，P1-1）。
- fuzzy / ambiguous / missing / 未达 strict-auto grammar（§8.4）/ 需人工 →
  `pending_review`。**incomplete 不进 candidate**：回 Annotation 聚焦重试（§5.2/§4.7）。
- 结构/语义明确矛盾、证据不成立 → `rejected`（terminal，原因写 `gate_decision.reasons`）。
- `approved` 不是"我决定批准"：approve() 是**物化事务**（10 §5.4：物化 A 域 +
  admission_event + 置 approved 同事务；失败 rollback 保持 pending_review）。

**approve() 的两个合法入口**（P0-2；人工判定是 review_trail → approve() 的输入，
**不是对不可变 payload 的 UPDATE**）：

1. **自动路径**：payload 内全部 answer `verified_correct=true`（strict auto，§8.3/§8.4）。
2. **人工路径**：候选 `pending_review`，人工确认写入 **`review_trail`**（10 §5.2，append
   不覆盖）`{decision: approve, verified_by: human|golden, reviewer_id, confirmed_fields,
   time}`；`approve(candidate_id, decision_provenance)` 校验
   `decision_status=pending_review` 且（payload 自动 verified 全 true **或** review_trail
   有人工确认）。物化 A 域 answer 行时 `verified_correct = payload 值 ∨ 人工确认值`，
   来源记 review_trail / gate_decision。无任一入口的候选**永久 pending_review**，不得
   静默消失。

**唯一迁移入口（冻结）**：`decision_status` 的任何状态迁移必须经 Admission Service 的
`approve()` / `reject()` **唯一入口**完成；Repository / ORM / Review Service / Worker
一律不得直接 UPDATE `decision_status`。人工 Review 只能**追加 `review_trail`（证据）**，
不得直接改状态；Gate 只产生准入判定（写入 `gate_decision`），**不直接物化、不直接置
approved**——自动准入由 Application Service 依 Gate Decision 调 `approve()`，人工准入
由 Review/Application Service 依合法 `review_trail` 调**同一 `approve()`**，两条路径
汇入**同一个 Admission Transaction**（10 §5.4）。

Gate 不做语义猜测的边界：Gate 只能拒绝证据不足的候选，不能把错误内容改成正确内容
（00 P2：Gate Policy 拥有 Admission Authority，但基于 evidence）。

### 8.3 Answer 三字段与 verified_correct

```json
{"source_located": true, "complete": true, "verified_correct": null}
```

- `source_located`：Resolver/Compiler 找到答案来源。
- `complete`：按 question-type role spec 与答案边界，source 内容完整、无截断；选项/
  多值/单元格/跨行答案全部闭合。
- `verified_correct`：答案内容已与权威答案或人工确认一致。

approved（经 §8.2 的 approve()）的答案必须：source_located=true 且 complete=true 且
`verified_correct=true`——自动路径由 strict-auto 置 true，人工路径由 review_trail
确认（§8.2 人工路径）；**source_located=true 单独不得证明正确**。

verified_correct=true 的可自动来源（02 §14 收敛）仅限：
1. 教师版答案区（answer_table/inline_answer/solution_answer）来源（非 LLM fallback）；
2. Resolver exact/normalized + span/cell 唯一；
3. Compiler complete=true + role spec 闭合；
4. 无 PUA/替换符/未解析 LaTeX/截断等有损证据；
5. 通过该 canonical type 的 **Allowed-Answer Grammar**（§8.4）。

否则 verified_correct=null，Gate 只能给 pending_review。**LLM 输出、source_located、
旧 answer_extractor 子串回查均不能直接置 true。**

### 8.4 Allowed-Answer Grammar（strict auto 前置 DoD）

- 每个 canonical_question_type 一份 role-aware grammar（stem required；options
  required_for_choice/not_applicable；answer 声明允许 token 集与规范化；explanation
  optional）。
- 首批：single_choice（选项标签集合=该题实际 resolved labels）；multiple_choice
  （字母 canonical 去重）；true_false（**先补 DISPLAY_CONTRACT 的 T/F↔A/B canonical
  映射**，再启用 strict auto）；fill_in/short_answer/writing 本阶段不开放 strict auto
  grammar（verified_correct 只能由 human/golden 置 true）。
- 未覆盖题型不满足 strict auto 路径 → 不能自动 approved，进入 `pending_review`；其
  `verified_correct` 只能经人工路径（review_trail，`verified_by=human|golden`）置 true
  （§8.2 人工路径）。
- grammar 必须附 golden 正例/反例与测试；**禁止用解析器实现代替文档评审**。没有
  grammar 文档时，strict auto verified_correct 视为未实现（00 §7 硬门槛 5）。

### 8.5 Composite 原子性

composite 任一子题非 ready / 任一子题 answer 不达标 → 整个 composite 不得 approved；
candidate/reject 必须按整个 composite 返回，禁止部分子题 approved（03 §12.1）。

---

## 9. 落库契约与"无第二数据模型"自检

每阶段产物与 10 表一一对应（§2 表）；Resolver/IR/Compiler 三个 transient 对象不进
任何新表，其完整形态沉淀为 candidate payload。落库前必须带齐 provenance：
`source_version_id`、annotation stage 键（annotation 行）、compile stage 键 +
`input_identity` + `build_versions`（candidate 行）。

**Reviewer 7 项验收**（20 必须自证，供 golden/Gate 测试落点）：

| # | 验收 | 由谁保证 | 落点 |
|---|---|---|---|
| 1 | 不生成 Source 中不存在的正文 | Compiler 只从 resolved span 提取；annotation 禁正文 | §7.2.1 / §8.1 / 10 §8 2c-2d |
| 2 | 每个 live role 都有确定性 span | Resolver role rules；contextual 不自动准入 | §5.3 / §5.4 / §8.2 |
| 3 | composite 与 standalone 在 IR 层真正区分 | 语义依赖显式；IR 不变量 1/7 | §6.2 / 10 §8 inv.3 |
| 4 | Material 不复制进子题 stem | IR 只存 span+关系；Compiler 只输出一次 | §6.2.6 / §7.2.3 |
| 5 | Figure 正确归属 Instance+role | image reference owner + figure_refs | §5.3 image / §7.2.5 |
| 6 | answer 三字段真正独立 | source_located/complete/verified 分列判定 | §8.3 |
| 7 | 最终 Candidate 不需再调 LLM 即可 Admission | payload 快照自足 + verified 规则 | 10 §5.3 |

---

## 10. 与 P1-P7 的服从对照

| 00 原则 | 本分册落点 |
|---|---|
| P1 最小闭环 M1 | 单条主链 = §4→§5→§6→§7→§8→(10 Admission)；无第二/legacy/特殊管线 |
| P2 LLM 无 Admission Authority | LLM 只产 annotation claim（§4）；Gate Policy 拥有判定（§8） |
| P3 Source 唯一事实源 | Compiler 只从 resolved span 产正文；annotation 禁正文（§4.3）；Provenance Gate 验 text_hash |
| P4 副作用显式 | 本分册阶段全为确定性 pure 步骤；唯一写入口 annotation 行 + candidate 行（§9） |
| P5 稳定由不变量保证 | §3 硬边界 + §6.2 IR 不变量；缺失一律 incomplete/ambiguous，禁止特判后处理 |
| P6 Idempotency | compile stage (stage, hash) + attempt_id（§7.1）；annotation stage 键（§4 注入） |
| P7 Replayability | input_identity + build_versions（§7.1/10 §9）；Exact Replay 前提 = §5.1 确定性 |

---

## 11. 词汇红线（README §2 强制，防 V2 回潮）

- 用 **Semantic Reference**，禁用 "Anchor / Anchor Corrector"。
- 用 **Resolved Span / line_ref（程序结果）**，Annotation JSON 禁 line_ref。
- 用 **Semantic Question IR**，不建裸 "Question IR" 对象名。
- 禁用语义词汇与代码：`corrected_line_ids`、`content_slicer`（按行切）、
  `nearest`（自动可接受）、按题号/学校/OCR 变体的特判分支、旧
  `quality_gate`/`admission_gate` R01-R18。
- 用 decision_status（pending_review/approved/rejected），不用
  "review/candidate" 状态混合词。

---

## 12. 变更记录

### 2026-09-05

- 建立 20 分册 v1.0：收敛起草 `V3_DOCUMENT_PIPELINE` + v0.3 00/01/02/03；固化
  Annotation Envelope/Payload 分离与递归禁字段；Semantic Reference 取代 Anchor；
  Resolver 级联与 contextual 条件；Semantic Question IR 不变量；Compiler 只从
  resolved span 产出 candidate payload；Gate 四层 + decision_status + answer 三字段 +
  Allowed-Answer Grammar 前置；§9"无第二数据模型"落库契约 + Reviewer 7 项验收表。

### 2026-09-05（v1.1，对抗性审查 3×P0 + 6×P1）

- P0-1 evidence 归属：`payload.evidence[]` 仅含 Resolver/Compiler 证据；Gate 的
  pass/fail+reasons 只进 candidate 行 `gate_decision` 列，不写回不可变 payload
  （§7.2.8、§8.1）。
- P0-2 approve() 双入口：自动（strict-auto verified）与人工（review_trail 确认 →
  `approve(candidate_id, decision_provenance)`）；物化 answer 的 `verified_correct =
  payload 值 ∨ 人工确认值`；消除非 auto 题永久 pending 死锁（§8.2/§8.3/§8.4）。
- P0-3 身份下放兑现：Compiler 改 **per 待物化实体**产键——每个 Question（含 composite
  leaf）独立 `dedup_key`（材料不混入子题键）+ 每个 shared material 独立 material
  `dedup_key` + 每个 Instance 独立 `occurrence_key`（§7.2.6-7.2.7）；新增 §7.3
  Normalization Contract（text_hash/source_span 保持 raw，规则版本化进 build_versions）。
- P1-1 contextual 不自动准入：任一 content role 为 contextual ⇒ 不得自动 approve，
  只作证据完整的待审快照（§5.4/§8.2/§9 验收 2）。
- P1-2 incomplete 不进 candidate + annotation superseded：新增 §4.7（10 §5.1 `status`
  写入者 = 确定性 Application 步骤；默认消费最新未 superseded；历史供 Rebuild）。
- P1-3 锚点收口：§9 Reviewer 验收"落点"列去 v0.3、改 10/20 内部锚点；10 两处节号
  引用由 10 v1.2.1 锚点 errata 修正（见 10 §12）。
- P1-4 material 正文重建路径：A 域 material `text` 在 Admission 内对 shared-material
  resolved span 确定性编译，payload 不复制材料副本（§7.2.3）。
- P1-5 词汇：删除 `approved=false` 布尔写法；`verified_by=human|golden` 定位于
  review_trail（§8.2/§8.4）。
- P1-6 `confidence` 限定为诊断元数据（annotation_meta），不作 decision 触发
  （§8.1）。

### 2026-09-05（v1.2-final-candidate，冻结前 2 条文字钉死）

- **唯一迁移入口（P0）**：`decision_status` 任何状态迁移必须经 Admission Service
  `approve()`/`reject()` 唯一入口；Repository/ORM/Review/Worker 不得直接 UPDATE；
  Review 只能追加 `review_trail`；Gate 只产判定（`gate_decision`）不直接物化；自动与
  人工两路径汇入同一 Admission Transaction（§8.2）。
- **三 key canonical input 钉死（P1）**：Question `dedup_key`（type+own stem+own
  options；不含 material/answer/explanation/image/no./page/source/unit）、Material
  `dedup_key`（type+own text；不含 question/instance/source location）、Instance
  `occurrence_key`（document-local unit/question + resolved stem span；**与 question_id
  无关**）（§7.3）。铁律：Question identity ≠ Answer identity；Question 不含共享材料。
