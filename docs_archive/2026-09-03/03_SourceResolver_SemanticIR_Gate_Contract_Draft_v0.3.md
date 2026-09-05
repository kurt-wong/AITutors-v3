# Source Resolver + Semantic Question IR + Gate Contract Draft

Version: DRAFT-0.3
Status: 开发指引契约，供评审；未实施
Date: 2026-09-04
Supersedes: `03_SourceResolver_SemanticIR_Gate_Contract_Draft.md`
目的：补齐 Semantic Metadata Annotation 之后、Admission 之前的中间层契约，避免再次
回到“LLM line_id -> Content Slicer -> 字段非空 Gate”的旧管线。

## 0. v0.3 开发指引要点

本文件从“中间层草案”升级为“Resolver/IR/Compiler/Gate 实现契约”。
总纲见 `00_SemanticPipeline_Development_Guide_v0.3.md`。

v0.3 重点避免旧管线以下问题：

1. `correct_anchors`/`content_slicer` 在无 semantic IR 时切出伪正确内容。
2. Gate 在不知道依赖关系时，只用字段非空和文本相似度放行。
3. LLM 标为 composite，但 IR 中没有 material dependency，无法验证原子性。
4. 答案“在原文出现”被当成“答案完整且正确”。

因此本文件要求：Resolver 只能消费 Annotation 语义 claim 与 sealed source；
IR 必须是 Gate/Compiler 的唯一输入；任何 unresolved 内容不得进入自动 approval。

## 1. 覆盖范围

本文件定义：

1. Source Resolver 的输入、解析状态、resolved span。
2. Semantic Question IR 的语义模型。
3. Structural / Provenance / Semantic / Admission Gate 的职责。
4. Answer Verification 与最终 admission 状态。

本文件不定义：

- Immutable Source 持久化细节，见
  `01_ImmutableSource_Persistence_Contract_Draft_v0.3.md`。
- LLM Semantic Annotation 输出细节，见
  `02_SemanticMetadata_Annotation_Contract_Draft_v0.3.md`。

## 2. 原则

```text
LLM 输出语义，不输出坐标。
Source Resolver 把语义 reference 解析为坐标/span。
Semantic Question IR 保存已解析的 question 语义和依赖。
Deterministic Compiler 只负责把 IR 编译成最终对象。
Gate 判断结构、来源、语义和 admission，不做语义猜测。
```

line_ref、offset、span 只在 Resolver 及之后出现，不能回写 Annotation。

## 3. Source Resolver 输入

Source Resolver 接收：

```json
{
  "source_version_id": "uuid",
  "annotation_run_id": "uuid",
  "annotation": {}
}
```

其中：

- `source_version_id` 指向 sealed Immutable Source；
- `annotation` 是 `semantic-metadata-annotation` manifest；
- Resolver 只能读取 immutable source，不能改写它。

## 4. Source Resolver 状态机

对每个 semantic reference，Resolver 依次尝试：

```text
Exact Match
  -> Normalized Match
  -> Context / Structural Match
  -> Fuzzy Match
  -> Ambiguous / Missing
```

状态语义：

| status | 含义 | 是否可进入自动 Gate |
|---|---|---|
| exact | 唯一精确命中 | 是 |
| normalized | 规范化后唯一命中 | 是 |
| contextual | 见 §4.2，逐条件满足后唯一确定 | 是，必须逐项证据闭合 |
| fuzzy | 存在近似命中，边界不精确 | 否，进入 review/candidate |
| ambiguous | 多个候选无法确定 | 否 |
| missing | 源中不存在 reference | 否 |

### 4.1 精确/规范化规则

Normalized Match 至少处理：

- 全半角；
- 空格/换行/连续空白；
- 中英文标点差异；
- OCR 转义噪音；
- 题号前后缀。

Normalized Match 后仍出现多个候选时，不允许随机选择。

### 4.2 Contextual Match 自动通过条件

Contextual Match 只有在以下条件全部满足时才允许被当作 resolved 并进入自动 Gate：

1. Exact/Normalized 未产生唯一候选，且候选数 > 1。
2. Resolver 可用候选按 role、question_label、section 顺序和显式 dependency 收窄到
   恰好 1 个。
3. 收窄只使用 Annotation 已声明的语义信息和 sealed source 的确定性边界，不推断
   缺失的依赖、不按行号重叠补语义。
4. 边界证据来自显式 role spec/answer_zone/instruction marker/下一 question 边界；
   若仍需要文本相似度、nearest、字符级近似才成立，则状态降为 fuzzy，禁止自动通过。
5. 输出 evidence 必须列出每个收窄步骤；任一候选无法被 evidence 排除即进入 ambiguous。
6. contextual 结果不得静默修改 Annotation，且必须在 Resolver Run 中保留候选集快照。

## 5. Role Resolution 规则

### 5.1 question_label

- Resolver 找到题号/子题号位置；
- stem 起点按 question_label 的确定性位置确定；
- stem 终点只能由显式边界证据（下一 question/option/answer/explanation/section
  boundary）闭合；没有唯一边界时返回 incomplete，不得默认取“最后一个内容行”。

### 5.2 option_label

- Resolver 在 stem 之后按 A/B/C/D 顺序寻找选项标签；
- 每项从该标签到下一标签/下一题起点结束；
- 同题重复标签进入 ambiguous；
- 缺失标签进入 incomplete。

### 5.3 material

- 使用 `instruction_marker` 的 start/end 精确定位；
- 无显式 end 时，Resolver 不自动按下一题/section 扩展；若 Annotation 未提供可验证
  的 end 边界，材料返回 incomplete。
- 即使显式提供 start/end，仍须验证 span 内文本不含子题 stem 专属内容且不与其他
  material/answer span 重叠。

### 5.4 answer

- `answer_zone=answer_table`：按 question_label 在答案表中解析答案行；
- `answer_zone=inline_answer`：按题后【答案】区域解析；
- Resolver 输出答案 source span，不负责生成答案正文；
- 答案正文由 Compiler/Answer Verifier 从 span 中确定性提取。

### 5.5 explanation

- `explanation_zone=inline_explanation`：定位题后【详解】/【解析】区域；
- Resolver 只输出 source span；
- 找不到完整区域时进入 ambiguous，不截断。

### 5.6 blank

- blank 属于某个 stem span；
- Resolver 定位 blank label/空位；
- 一个 blank 必须映射到一个 sub_question/answer；
- 没有闭合映射时 IR 为 incomplete。

### 5.7 image

- image reference 必须解析到 source version 的图片索引；
- 图片必须有 page/bbox/placement/source/figure_id；
- 无唯一图片时进入 ambiguous，禁止跨题广播。

## 6. Resolved Source Span

Resolver 输出统一 span：

```json
{
  "span_id": "sp-Q1-stem",
  "source_version_id": "uuid",
  "start_line_ref": "P1L001",
  "end_line_ref": "P1L002",
  "line_refs": ["P1L001", "P1L002"],
  "granularity": "line",
  "start_offset": null,
  "end_offset": null,
  "cell_ref": null,
  "fragment_ref": null,
  "text_hash": "sha256",
  "resolution_status": "exact",
  "evidence": ["question_label=1", "next_boundary=Q2"]
}
```

约束：

- `start_line_ref` / `end_line_ref` 必须在 source version 中存在；
- `line_refs` 保持 source 顺序；
- `granularity` 必须为 `line`、`line_character`、`table_cell` 或
  `fragment`；默认 `line`。
- `granularity=line_character` 时，`start_offset/end_offset` 表示
  `start_line_ref`/`end_line_ref` 内的字符范围，必须能唯一定位“同行多题答案、
  单行多选项、行内空白”等场景。
- `granularity=table_cell` 时，`cell_ref` 必须引用 source version 内可回放的表格
  cell，如 `{"table_id":"T1","row":5,"column":2}`；禁止把整行当作答案。
- `granularity=fragment` 时，`fragment_ref` 指向 source index 中已定义的结构化
  fragment/cell span，不保存重新生成的正文。
- `text_hash` 由程序按该 span 实际内容计算，行级 span 按 line text，字符级/单元格
  span 按精确 fragment/cell text；
- 同一个 source version 中，span 必须可重放；
- Annotation 不得包含该结构。

## 7. Resolved Relation

```json
{
  "from": "Q11",
  "to": "M1",
  "type": "material_dependency",
  "resolved_target_span": {
    "span_id": "sp-M1"
  },
  "status": "resolved"
}
```

关系必须全部解析，才允许 Semantic IR 状态为 ready。

## 8. Semantic Question IR

Semantic Question IR 是 Resolver 与 Compiler 之间的唯一中间表示。

```json
{
  "ir_schema": "semantic-question-ir/v0.3",
  "source_version_id": "uuid",
  "annotation_run_id": "uuid",
  "resolver_run_id": "uuid",
  "units": []
}
```

### 8.1 standalone question IR

```json
{
  "unit_id": "Q1",
  "unit_type": "standalone_question",
  "question_number": "1",
  "canonical_question_type": "single_choice",
  "content_roles": {
    "stem": "required",
    "options": "required_for_choice",
    "answer": "required",
    "explanation": "optional"
  },
  "content": {
    "stem": {
      "source_span": {"span_id": "sp-Q1-stem"},
      "status": "resolved"
    },
    "options": {
      "A": {"source_span": {"span_id": "sp-Q1-A"}, "status": "resolved"},
      "B": {"source_span": {"span_id": "sp-Q1-B"}, "status": "resolved"}
    },
    "answer": {
      "source_span": {"span_id": "sp-Q1-answer"},
      "answer_status": {
        "source_located": true,
        "complete": true,
        "verified_correct": null
      }
    },
    "explanation": {
      "source_span": {"span_id": "sp-Q1-explanation"},
      "status": "resolved"
    }
  },
  "relations": [],
  "semantic_status": "ready"
}
```

### 8.2 composite unit IR

```json
{
  "unit_id": "U11-13",
  "unit_type": "composite_unit",
  "question_number_range": "11-13",
  "shared_components": {
    "material": {
      "source_span": {"span_id": "sp-M1"},
      "status": "resolved"
    },
    "word_bank": null,
    "shared_option_pool": null
  },
  "sub_questions": [
    {
      "question_id": "Q11",
      "question_number": "11",
      "canonical_question_type": "single_choice",
      "content_roles": {
        "stem": "required",
        "options": "required_for_choice",
        "answer": "required",
        "explanation": "optional"
      },
      "content": {
        "stem": {
          "source_span": {"span_id": "sp-Q11-stem"},
          "status": "resolved"
        },
        "options": {
          "A": {"source_span": {"span_id": "sp-Q11-A"}, "status": "resolved"}
        },
        "answer": {
          "source_span": {"span_id": "sp-Q11-answer"},
          "answer_status": {
            "source_located": true,
            "complete": true,
            "verified_correct": null
          }
        }
      },
      "relations": [
        {
          "type": "material_dependency",
          "target": "M1",
          "status": "resolved"
        }
      ],
      "semantic_status": "ready",
      "sub_sub_questions": []
    }
  ],
  "content_roles": {
    "stem": "required",
    "options": "required_for_choice",
    "answer": "required",
    "explanation": "optional"
  },
  "semantic_status": "ready"
}
```

IR 不重复保存共享材料正文，只保存 shared_components 的 source span 和子题关系。
`canonical_question_type` 是 IR/Compiler 的输出字段，Annotation 中禁止出现。
`sub_sub_questions` 与 `sub_questions` 结构相同，允许任意递归层数；各层
`content_roles` 按该层题型独立解释。

## 9. IR 完整性不变量

1. 每个 question/sub_question 的 role 是否存在，按 `content_roles` 与
   canonical_question_type 解释；不得把 options 写成所有题型必填。
2. composite 的所有 sub_questions 都属于同一个 unit；递归子题仍必须回溯到
   最近父 unit。
3. 每个 `material_dependency` 的 target 都能解析到同 unit 的 shared material。
4. blank/option/answer 映射闭合，不允许悬空引用；递归层同样闭合。
5. 一个 sub_question 不能同时属于两个 unit。
6. 共享材料只出现一次，不出现在子题 stem span 内。
7. 任一子题 unresolved，composite 整体不是 ready。

## 10. Deterministic Compiler 边界

Compiler 输入：

- sealed source version；
- Semantic Question IR；
- Resolved Source Span。

Compiler 输出：

- 与 DISPLAY_CONTRACT 兼容的 question/composite；
- 与 question_instances 兼容的来源信息；
- canonical_question_type 与 content_roles 的最终判定；
- materialized 正文；
- question_images 关联；
- source provenance。

Compiler 禁止：

- 判断题目是否共享材料；
- 猜测 blank/option/answer 映射；
- 修改 Annotation 或 IR；
- 在无 resolved span 时生成正文。

## 11. Gate 分层

### 11.1 Structural Gate

检查：

- JSON/IR schema 合法；
- 必需字段存在；
- span 非空；
- span line_ref 在 source version 内；
- span 的 granularity/offset/cell_ref 与角色要求一致；
- question 类型/编号可解释。

### 11.2 Provenance Gate

检查：

- 所有正文都能追溯到 Immutable Source；
- text_hash 与 source line/fragment/cell 的实际内容一致；
- no generated prose；
- exact/normalized 才能自动进入；
- contextual 必须附 evidence；
- fuzzy/ambiguous/missing 不能自动通过。

### 11.3 Semantic Gate

检查：

- standalone 没有必需 material dependency；
- composite 的依赖关系完整；
- blank/option/answer 闭合；
- 子题 image 归属正确；
- `requires_material_context` 或 `material_dependency` 不能单独证明“结合材料后可
  作答”，必须与 content_roles、resolved spans 和 boundary evidence 一起闭合；
- 名称映射：DISPLAY_CONTRACT 的“独立题 = 去掉材料后可独立解答”保留唯一权威语义；
  composite 子题不得使用 `independence_after_material` 字段；
- 语义状态与 IR 一致。

对于“去掉材料后能否独立作答”的语义正确性：

- Annotation 提供 semantic claim；
- IR 提供 resolved dependency；
- Gate 检查 claim 与 dependency 的一致性；
- 最终正确性由 golden、人工 review 和 answer verification 共同验证；
- Gate 不把单次 LLM 布尔值直接视为 `verified_correct`。

### 11.4 Admission Gate

Admission Gate 最终输出：

```json
{
  "gate_schema": "admission-gate/v0.3",
  "decision": "approved",
  "layers": {
    "structural": "pass",
    "provenance": "pass",
    "semantic": "pass",
    "admission": "approved"
  },
  "reasons": []
}
```

## 12. Admission 状态

| status | 条件 |
|---|---|
| approved | Structural/Provenance/Semantic 全通过，且 answer 满足自动标准 |
| candidate | 存在 fuzzy/ambiguous/missing/incomplete/低置信度，或需要人工 review |
| rejected | 存在结构/语义明确矛盾，或证据不成立 |

### 12.1 Composite 原子性

- composite 任一子题非 ready，整个 composite 不能 approved；
- 禁止部分子题 approved；
- candidate/reject 必须按整个 composite 返回。

## 13. Answer Verification

```json
{
  "source_located": true,
  "complete": true,
  "verified_correct": null
}
```

定义：

- `source_located`：Resolver/Compiler 找到答案来源；
- `complete`：按 question-type content_roles 和答案边界判定，source 内容完整，
  无截断；选项/多值/单元格/跨行答案必须全部闭合。
- `verified_correct`：答案内容已与权威答案或人工确认一致。

自动 approved 的答案必须同时满足：

- source_located=true；
- complete=true；
- verified_correct=true 或由人工/验证流程确认；
- 不允许 source_located=true 单独证明答案正确。

verified_correct 的权威来源规则：

- 教师版答案区是权威“来源”，不是自动“正确性”证明。
- 可以自动置 true 的输入只能是以下任一路径：
  1. Golden/人工审核：有 `verified_by=human` 或 `verified_by=golden` 且审核记录关联
     source_version_id；
  2. 严格自动权威：教师版答案区来源 + resolver exact/normalized + span/cell 唯一 +
     compiler complete=true + 无 PUA/替换符/未解析 LaTeX/截断 + 答案通过该题型
     allowed-answer grammar 校验。
- LLM 输出、旧 answer_extractor 子串回查、source_located=true 均不能直接置 true。
- 不满足上述条件时 `verified_correct=null`，Gate 只能给 candidate/review。

### 13.1 Allowed-Answer Grammar（Phase 5 前置 DoD）

严格自动 `verified_correct=true` 不得引用未定义的 grammar。Phase 5 开始前必须把
以下 grammar 固化到 DISPLAY_CONTRACT 或独立的 Answer Grammar 文档：

1. 每个 canonical_question_type 都有一份 role-aware grammar：
   - stem：required；
   - options：required_for_choice / not_applicable；
   - answer：按题型声明允许的 token 集合和规范化规则；
   - explanation：optional。
2. 首批必须覆盖：
   - single_choice：允许的选项标签集合等于该题 options 的实际 resolved labels，
     禁止混入选项正文；
   - multiple_choice：字母集合，canonical 排序去重，禁止连写/逗号/中文分隔歧义；
   - true_false：在 DISPLAY_CONTRACT 中明确 T/F 或 A/B 的唯一 canonical 映射；
   - fill_in/short_answer/writing：本阶段不开放“strict auto grammar”，
     verified_correct 只能由 human/golden 置 true；
   - table_cell/structured answer：按 4.34 cell hash 和 answer_structure 校验，
     不允许只匹配单元格子串。
3. Grammar 必须附 golden 正例/反例和测试，禁止用解析器实现代替文档评审。
4. 未覆盖题型不满足严格自动路径；该题只能 approved=false，进入
   candidate/human，除非 verified_by=human/golden。

Phase 5 开始的第一项任务必须是先补 DISPLAY_CONTRACT 的 true_false canonical 映射，
再验收 grammar；不允许只声明“存在 grammar”而无真实题型映射。

没有上述 grammar 文档时，严格自动 `verified_correct=true` 路径视为未实现。

Admission 状态映射：

- 新链 canonical：`approved` / `candidate` / `rejected`。
- DB question 持久化映射：`approved` -> questions approved；`candidate` ->
  question_candidates admission_status=candidate；`rejected` -> 删除候选并写审计。
- 旧 `review`/`reject`、旧 `approved/reviewing/rejected` 只作为 legacy 兼容，
  新链对外/内部对象一律使用 canonical admission_status。

## 14. 与 Annotation 的闭环

```text
Semantic Annotation
  -> Source Resolver
  -> Semantic Question IR
  -> Compiler
  -> Gate
  -> Candidate/Admission
```

任一阶段发现缺失时：

- 结构化错误直接标记 invalid/incomplete；
- 可重试的缺失回到 Annotation/Resolver 聚焦重试；
- 不可自动纠正的进入 candidate/review；
- 禁止用后处理规则补语义。

## 15. Golden 与验收

契约固化前至少验证：

1. 同一 source + 同一 Annotation 产生确定性 Resolver/IR。
2. Annotation 不含 line_refs，IR 不含未解析 dependency。
3. Composite 任一子题缺 span，整体不能 ready。
4. Material span 与子题 stem span 不重复。
5. fuzzy/ambiguous 不被自动 approved。
6. answer 的 source_located/complete/verified_correct 分离。
7. golden 覆盖独立题、共享材料、空位、共享选项池和答案表。
8. line_character/table_cell/fragment span 必须在 sealed source index 中可回放。

## 16. 本阶段实施顺序

1. 按本文件完成 Resolver/IR schema 实现。
2. 用最小 golden 验证 standalone 与 composite。
3. 再实现 Deterministic Compiler。
4. 最后实现 Gate 层。
5. 在 golden 达到自动标准前，不允许启动 0.5B 训练和业务 Admission 堆叠。

## 17. 下一步开发实现指引

### 17.1 处理单元

建议实现以下纯处理步骤，避免函数间隐式修改 Annotation：

```text
run_resolver(source_version, annotation)
  -> ResolverRunOutput

build_ir(resolver_run)
  -> SemanticQuestionIR

compile_ir(ir, source_version)
  -> CompiledQuestion / CompiledComposite

run_gate(compiled, source_version)
  -> GateDecision
```

约束：

- Resolver/IR/Compiler 不得修改 annotation。
- Resolver 输出必须带 `source_version_id`。
- IR 必须带 `annotation_run_id` 和 `resolver_run_id`。
- Compiler 不接收未解析的 question_label/marker。

### 17.2 禁止复用旧链语义猜测

新实现不得以兼容旧链为理由继续使用：

- `correct_anchors()` 的 nearest/fuzzy/marker-fallback 逻辑。
- `content_slicer()` 按行号补 stem、合并共享材料、拆/拼子题的逻辑。
- `quality_gate()` 把 confidence/issues 当成 semantic proof。
- `admission_gate.py` 的旧 R01-R18 作为新 semantic gate。

旧函数/测试可以保留为 legacy 回归，但新链不得 import 它们作为核心路径。

### 17.3 Resolver 输出状态

Resolver 结果应至少区分：

| 状态 | 语义 | 是否可进入 ready IR |
|---|---|---|
| resolved | 有唯一 resolved span/relation | 是 |
| incomplete | Annotation 缺少必要 claim/ref | 否 |
| ambiguous | 多个候选且无法确定 | 否 |
| missing | source 中找不到 reference | 否 |
| fuzzy | 只有近似候选，边界或语义不能唯一证明 | 否，只允许 review/candidate |
| invalid | schema/语义矛盾 | 否 |

不允许新增“nearest”作为自动可接受状态。旧 `anchor_status` 只属于 legacy。

### 17.4 IR 必须携带的内容

1. source_version_id 与 annotation/resolver run id。
2. 每个 question/composite 的 question identity 和 unit_type。
3. 每个 role 的 resolved span，不得只有未解析 label。
4. 每个 dependency 的 resolved target span。
5. blank/option/answer/image 的闭合映射。
6. composite 的 shared components 与子题关系。
7. semantic_status，只有 ready 可进入 Compiler。

### 17.5 Compiler 输出校验

- stem/options/shared_material/answer/explanation 必须来自 resolved span。
- `source_version_id`、line_refs、text_hash 必须可回放。
- composite shared material 只输出一次，子题不得复制材料。
- canonical question_type 必须由 Compiler 从 original type 映射，映射失败为
  incomplete，不能以 NULL 静默入库。
- 输出对象必须兼容 DISPLAY_CONTRACT，但不得反向修改 IR。

### 17.6 Gate 实现顺序

1. Structural Gate：schema、span 唯一、source version 存在。
2. Provenance Gate：正文/行号/text_hash 一致，无生成正文。
3. Semantic Gate：依赖完整、组合原子、blank/option/answer 闭合、材料不重复。
4. Admission Gate：只有前三层通过且 answer 达到自动标准才 approved。

### 17.7 回归防护测试

- `test_resolver_same_source_same_annotation_deterministic`
- `test_ambiguous_marker_not_resolved`
- `test_missing_span_makes_ir_incomplete`
- `test_composite_any_sub_incomplete_blocks_all`
- `test_material_span_not_inside_sub_stem`
- `test_compiler_no_generated_text`
- `test_answer_status_three_fields_independent`
- `test_gate_rejects_ir_without_ready_status`
- `test_old_anchor_slicer_not_imported_by_new_pipeline`
