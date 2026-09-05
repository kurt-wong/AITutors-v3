# Source Resolver + Semantic Question IR + Gate Contract Draft

Version: DRAFT-0.1
Status: 草案，供评审；未实施
Date: 2026-09-03
目的：补齐 Semantic Metadata Annotation 之后、Admission 之前的中间层契约，避免再次
回到“LLM line_id -> Content Slicer -> 字段非空 Gate”的旧管线。

## 1. 覆盖范围

本文件定义：

1. Source Resolver 的输入、解析状态、resolved span。
2. Semantic Question IR 的语义模型。
3. Structural / Provenance / Semantic / Admission Gate 的职责。
4. Answer Verification 与最终 admission 状态。

本文件不定义：

- Immutable Source 持久化细节，见
  `01_ImmutableSource_Persistence_Contract_Draft_v0.2.md`。
- LLM Semantic Annotation 输出细节，见
  `02_SemanticMetadata_Annotation_Contract_Draft_v0.2.md`。

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
| contextual | 结合 role/section/question 顺序唯一确定 | 条件通过后可 |
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

## 5. Role Resolution 规则

### 5.1 question_label

- Resolver 找到题号/子题号位置；
- stem 起点吸附到题号标记；
- stem 终点默认取该题最后一个内容行，并受下一题/下一 section 限制。

### 5.2 option_label

- Resolver 在 stem 之后按 A/B/C/D 顺序寻找选项标签；
- 每项从该标签到下一标签/下一题起点结束；
- 同题重复标签进入 ambiguous；
- 缺失标签进入 incomplete。

### 5.3 material

- 使用 `instruction_marker` 的 start/end 精确定位；
- 无显式 end 时，用下一 section/下一题目/section 题号范围推导；
- 推导仍不唯一时进入 ambiguous。

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
  "text_hash": "sha256",
  "resolution_status": "exact",
  "evidence": ["question_label=1", "next_boundary=Q2"]
}
```

约束：

- `start_line_ref` / `end_line_ref` 必须在 source version 中存在；
- `line_refs` 保持 source 顺序；
- `text_hash` 由程序按 source line text 计算；
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
  "ir_schema": "semantic-question-ir/v0.1",
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
  "question_type": "single_choice",
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
      "question_type": "single_choice",
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
      "independence_after_material": true,
      "semantic_status": "ready"
    }
  ],
  "semantic_status": "ready"
}
```

IR 不重复保存共享材料正文，只保存 shared_components 的 source span 和子题关系。

## 9. IR 完整性不变量

1. 每个 standalone question 的 stem/options/answer 必需 ref 都存在。
2. composite 的所有 sub_questions 都属于同一个 unit。
3. 每个 `material_dependency` 的 target 都能解析到同 unit 的 shared material。
4. blank/option/answer 映射闭合，不允许悬空引用。
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
- question 类型/编号可解释。

### 11.2 Provenance Gate

检查：

- 所有正文都能追溯到 Immutable Source；
- text_hash 与 source line 一致；
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
- `independence_after_material` 不是唯一证明；
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
  "gate_schema": "admission-gate/v0.1",
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
- `complete`：答案 source 内容完整，无截断；
- `verified_correct`：答案与权威来源/人工确认一致。

自动 approved 的答案必须同时满足：

- source_located=true；
- complete=true；
- verified_correct=true 或由人工/验证流程确认；
- 不允许 source_located=true 单独证明答案正确。

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

## 16. 本阶段实施顺序

1. 按本文件完成 Resolver/IR schema 实现。
2. 用最小 golden 验证 standalone 与 composite。
3. 再实现 Deterministic Compiler。
4. 最后实现 Gate 层。
5. 在 golden 达到自动标准前，不允许启动 0.5B 训练和业务 Admission 堆叠。
