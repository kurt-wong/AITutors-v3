# Semantic Metadata Annotation Contract Draft

Version: DRAFT-0.1
Status: 草案，供评审；未实施
Date: 2026-09-03
目的：定义 Immutable Source 之后、Source Resolver 之前的 LLM Semantic Metadata
Annotation 契约，使程序能稳定消费结构角色、题目关系、材料依赖、blank/option/answer
关系和置信度，而不是继续消费“孤立的 line_id 数组”。

## 1. 当前问题

旧 L2 的主要表达是：

- 整份文档一个题目列表；
- 每个题目若干 `*_line_ids` 字段；
- 通过后处理把零散行号合成为综合题；
- 人工 retry hint 补行号；
- Gate 只检查行号存在与字段非空。

该模型丢失三类关键语义：

1. 材料与子题之间的依赖关系没有被显式表达；
2. 题目树/Admission Unit 边界由后处理拼装，而不是由 LLM 明确声明；
3. blank、option、answer、explanation 之间只有平行列表，没有对象级链接。

## 2. 设计原则

### SM-1 Annotation 是 claim，不是事实

LLM 输出全部属于“对不可变源的解释”，不是入库事实。Annotation 必须先经
Source Resolver 和 Semantic Question IR，再由 Compiler 生成题目对象。

### SM-2 LLM 不生成正文

除本契约允许的短字面量外，LLM 不得输出 stem/material/options/answer/explanation
的完整文本、LaTeX、解题过程或改写正文。

### SM-3 最终位置由 Source Resolver 负责

Annotation 可以携带从 source index 中选择的候选 line_ref，但不得输出
`resolved_span`、`corrected_line_ids`、`final_line_ids` 等“已最终校正”字段。
Resolver 负责 Exact -> Normalized -> Context/Structural -> LLM disambiguation。

### SM-4 依赖必须显式

每个 Admission Unit 和子题都必须说明它依赖什么。禁止仅凭“同一 section”或“行号
重叠”推断依赖；没有依赖关系的题不得被强制合并。

### SM-5 综合题是原子单元

一份共享材料/指令/词库/共享选项区与依赖它的子题组成一个 Admission Unit。任一
子题结构或依赖不完整，该单元整体不能 approved。

### SM-6 不存思维链

Annotation 可存结构化 confidence 与 evidence 类型，不存 LLM 推理文本/CoT。

## 3. 输入视图

Annotation prompt 的输入是已 seal 的 canonical source 的只读视图：

```json
{
  "source_version_id": "6b1e...",
  "body_hash": "a3f1...",
  "pages": [
    {
      "page_no": 1,
      "lines": [
        {
          "line_ref": "P1L001",
          "text": "...",
          "block_type": "text"
        }
      ]
    }
  ],
  "document_metadata_input": {
    "filename": "...",
    "subject": null,
    "grade": null
  }
}
```

约束：

- 输入只包含 canonical source，不包含未仲裁 raw source 的混合行号。
- 行文本用于让 LLM 理解语义，但 LLM 的返回结果不应把行文本搬运回 JSON。
- source view 必须声明 hash 和 version，避免 annotation 记录错绑到另一版本。

## 4. 顶层 Annotation Manifest

建议顶层结构：

```json
{
  "annotation_schema": "semantic-metadata-annotation/v0.1",
  "annotation_version": "llm-semantic-v1",
  "annotation_run_id": "uuid",
  "source_version_id": "uuid",
  "document_id": "uuid",
  "document_metadata": {
    "subject": null,
    "grade": null,
    "year": null,
    "school": null,
    "metadata_confidence": 0.0
  },
  "sections": [],
  "admission_units": [],
  "annotation_meta": {
    "model": "...",
    "prompt_version": "...",
    "status": "complete",
    "warnings": []
  }
}
```

字段要求：

| Field | Requirement |
|---|---|
| annotation_schema | 固定 schema 名；后续变化升版本 |
| annotation_version | prompt/model 版本，用于 A/B 与回放 |
| annotation_run_id | 一次 annotation run 的唯一 ID |
| source_version_id | 必须指向 sealed immutable source version |
| document_id | 冗余保存，便于恢复与归属校验 |
| sections | 卷面结构声明；不是题目事实 |
| admission_units | 可 admission 的独立题或综合题单元 |
| annotation_meta | 诊断元数据，不进入最终 Question 事实 |

## 5. Source Reference

Annotation 中的引用统一为 candidate ref：

```json
{
  "role": "material",
  "line_refs": ["P1L003", "P1L004", "P1L005"],
  "confidence": 0.99,
  "reason_basis": "shared_material_start_end"
}
```

允许 role 至少包括：

| role | 含义 |
|---|---|
| section_header | 卷面 section 标题/题组标题 |
| task_instruction | 任务说明、评分范围说明、要求 |
| material | 需共享的材料/文章/情境/数据/图表说明 |
| material_note | 文言注释等附属材料 |
| word_bank | 词库/选项池等共享资源 |
| stem | 独立题题干，或综合题子题自身题干 |
| blank | 题干中的空位/作答点 |
| option | 单个选项，按 label 分组 |
| shared_option_pool | A-G 等被多子题共享的选项区 |
| answer | 答案来源区域/答案项 |
| explanation | 详解/解题过程来源区域 |
| scoring_standard | 评分标准来源区域 |
| image | 图片锚点/配图引用 |

约束：

- 所有 `line_refs` 必须在 annotation 声明的 `source_version_id` 中有效。
- `role` 决定下游 Compiler 如何消费；同一条 line 不能既作为 material 又作为子题
  stem 的内容来源，但可作为 dependency 目标被引用。
- `confidence` 表示 LLM 对该 role 归属/边界的置信度，不是程序验证结果。

## 6. Section Annotation

Section 用于卷面结构，不直接表示题目：

```json
{
  "id": "SEC-1",
  "label": "一、单项选择",
  "question_number_range": "1-10",
  "header_ref": {
    "role": "section_header",
    "line_refs": ["P1L001"],
    "confidence": 0.99
  },
  "order": 1
}
```

Section 不承载“是否共享材料”的判断；材料归属与依赖只在 Admission Unit 中表达。

## 7. Admission Unit Annotation

Admission Unit 是最小可审核/可入库单元：

- 独立题：`mode=independent`；
- 综合题：`mode=composite`，父容器 + 依赖同一资源的子题。

```json
{
  "unit_id": "AU-1",
  "mode": "composite",
  "question_number": "1-10",
  "section_id": "SEC-1",
  "original_question_type": "cloze",
  "canonical_question_type": "single_choice",
  "container_roles": {
    "stem": {
      "role": "stem",
      "line_refs": ["P1L002"],
      "confidence": 0.99
    },
    "material": {
      "role": "material",
      "line_refs": ["P1L003", "P1L004", "P1L005"],
      "confidence": 0.99
    },
    "word_bank": null,
    "shared_option_pool": null
  },
  "sub_questions": [
    {
      "unit_id": "AU-1.Q1",
      "qno": "1",
      "question_type": "single_choice",
      "roles": {
        "stem": {
          "role": "stem",
          "line_refs": ["P1L006"],
          "confidence": 0.99
        },
        "options": {
          "A": {"line_refs": ["P1L007"], "confidence": 1.0},
          "B": {"line_refs": ["P1L008"], "confidence": 1.0},
          "C": {"line_refs": ["P1L009"], "confidence": 1.0},
          "D": {"line_refs": ["P1L010"], "confidence": 1.0}
        },
        "answer": {
          "literal": "C",
          "literal_kind": "option_letter",
          "line_refs": ["P9L005"],
          "confidence": 0.98
        },
        "explanation": {
          "line_refs": [],
          "confidence": 0.0
        }
      },
      "dependencies": [
        {
          "type": "requires_material",
          "target": "AU-1.MATERIAL",
          "required": true,
          "confidence": 1.0
        }
      ]
    }
  ]
}
```

### 7.1 independent

独立题必须满足：

- 自身 roles 覆盖完成题目所需语义；
- 没有指向其他 Admission Unit 或共享 material 的 required dependency；
- 若有条件/短文/公式背景，它们应属于该题自身 stem/options/image 的可切片范围，
  而不是放到共享 material；
- 不得因为 section 相同而被并入 composite。

### 7.2 composite

综合题容器必须满足：

- 父容器至少提供 material/word_bank/shared_option_pool/task_instruction 中的一种；
- 每个子题都显式列出自己需要哪些资源；
- 任一子题缺少必要 dependency 或对应 answer source，整个 unit 不 approved；
- 容器不得持有答案/详解/选项这些只属于子题的 role；
- material 引用只存一次，子题不得把整段 material 复制到 stem。

## 8. 关系模型

Annotation 中关系是对象到对象的边：

| type | 方向语义 |
|---|---|
| contains | Admission Unit 包含子题 |
| requires_material | 子题依赖父容器材料 |
| requires_word_bank | 子题依赖词库 |
| uses_option_pool | 子题使用共享选项区 |
| blank_answered_by | blank 对应某个 answer/sub-question |
| option_labeled | 选项与 label 的绑定 |
| answer_source | answer literal/内容来自 source role |
| explanation_source | explanation 来自 source role |
| image_anchor | role 与图片引用绑定 |
| scoring_of | scoring_standard 属于 unit/sub-question |

关系字段：

```json
{
  "type": "requires_material",
  "from": "AU-1.Q1",
  "to": "AU-1.MATERIAL",
  "required": true,
  "confidence": 1.0
}
```

规则：

- `from`/`to` 都必须存在于同一 annotation 内。
- `requires_*` 只能指向同一 composite unit 内的资源或同一 section 中显式声明的
  共享资源，不能引用其它文档/其它 unit 的内部内容。
- 关系是语义声明，不是最终 DB FK；最终 FK/引用由 Resolver/IR/Compiler 决定。

## 9. Blank / Option / Answer 映射

对空位题必须给出对象级映射，而不是只有 `stem_line_ids`：

```json
{
  "blank_id": "B1",
  "qno": "11",
  "blank_ref": {"line_refs": ["P2L001"], "confidence": 0.99},
  "belongs_to_stem": {"line_refs": ["P2L001", "P2L002"], "confidence": 0.99},
  "answer_target": {
    "role": "answer",
    "line_refs": ["P9L010"],
    "literal": "racing",
    "literal_kind": "short_answer",
    "confidence": 0.99
  }
}
```

对共享选项池（如七选五）：

- `shared_option_pool` 保存 A-G 来源；
- 每个子题 `option` 只绑定自己的空位和所需字母；
- `extra_options` 声明多余选项数量；
- 子题不得复制 A-G 全文到 `stem`。

## 10. 允许的短字面量

LLM 只能输出以下类型字面量：

| literal_kind | 示例 |
|---|---|
| question_number | `1-10` |
| qno | `11` |
| section_id | `SEC-1` |
| original_question_type | `cloze` |
| option_label | `A` |
| short_answer | `C`、`racing`、`24.00` |
| score | `1.5` |
| difficulty | `3` |
| knowledge_point | `动词时态` |

禁止：

- 题干原文、选项全文、材料全文；
- 答案/详解的整段生成文本；
- 解题过程；
- 公式 LaTeX 抄写；
- 人工给 Gate 写的“自证合格”文本。

## 11. 完整性声明

每个 unit/sub-question 可以有结构化 completeness claim：

```json
{
  "semantic_status": "complete",
  "answer_status": {
    "source_located": true,
    "complete": false,
    "verified_correct": null
  }
}
```

约束：

- `source_located` 只能表示 annotation 声称找到了答案来源；
- `complete` 只能表示该 role/span 范围完整；
- `verified_correct` 不进入 annotation 默认字段；由答案匹配、人工或独立验证写入；
- 三者必须分离，不允许 Gate 把“行号非空”同时解释为“来源存在 + 完整 + 正确”。

## 12. 版本与持久化建议

Semantic Annotation 应作为新的 annotation artifact 保存，不能覆盖 Immutable
Source：

```text
annotation_manifest
  ├── document_id
  ├── source_version_id
  ├── annotation_run_id
  ├── annotation_version
  └── sealed annotation JSON
```

建议：

- 每个 annotation run 独立存储；同一 source version 可多次标注。
- 当前用于入股的 annotation 由 active annotation pointer/status 表达。
- 旧 `documents.llm_annotated_markdown` 保留为 legacy L2；新语义 annotation 使用
  `annotation_schema` 区分，避免 parser 混用。
- 若 Annotation 结构变化，`annotation_schema` 升版，不原地改写旧记录。

## 13. 校验规则

### 13.1 schema 校验

- 顶层包含 `annotation_schema`、`source_version_id`、`admission_units`。
- 所有 line_ref 属于声明 source version。
- unit_id 唯一；question_number 在同一 section 可解释。

### 13.2 graph 校验

- 无重复/冲突 `from`-`to` 关系。
- 无 cycle。
- 每个子题只能属于一个 Admission Unit。
- independent unit 不能有 required external dependency。
- composite unit 必须整体通过 compiler/gate，禁止子题单独入库。

### 13.3 语义完整性校验

- 有答案 role 的题必须有可解析 answer source ref，或明确 answer 来自人工/LLM
  fallback 且被 Gate 分类，不能静默接受空。
- 共享材料在 parent 只表达一次；sub-question stem 不能重复引用整段 material。
- 选项与空位关系必须闭合：每个选择式子题有 label、refs，每个引用存在。

## 14. 与旧 L2 的迁移

本 contract 不是简单扩展 `L2QuestionAnnotation` 字段，而是要求新的语义 manifest。
迁移路径建议：

1. 新 pipeline 输出 `semantic_metadata_annotation/v0.1`；
2. Source Resolver 把它解析为 Semantic Question IR；
3. Compiler 生成兼容 DISPLAY_CONTRACT 的题目/综合题结构；
4. 旧 line_id annotation 只用于诊断对比，不再作为 admission 输入；
5. 对同一份样本并行跑旧/新 annotation，做字段级 golden 对比，验证不丢材料/答案。

## 15. 验收标准

1. 给定同一 sealed source 与同一 prompt，两次标注可对比、可回放。
2. 禁止字段无正文复制：对全量 annotation JSON 做 text overlap 检查，超过允许
   literal 的行/span 直接 fail。
3. 综合题材料不重复：material role 的 line_refs 不出现在子题 stem role。
4. 缺失依赖关系的子题在 IR/Gate 可见为 incomplete，而不是被后处理猜测合并。
5. 去掉某个 dependency 或 line_ref 后，Semantic Question IR 必然出现 dangling/缺失。
6. Annotation 不含 `corrected_line_ids`/`resolved_span`；这些只出现在 Resolver 输出。

## 16. 待评审问题

1. 是否允许 LLM 直接输出 source index 的 line_refs，还是应输出抽象
   source-marker 后由 Resolver 解析；本草案倾向允许候选 line_refs，但禁止 final
   resolved 字段。
2. answer literal 的边界：哪些客观短答案允许直接输出，哪些必须完全由 Source
   Resolver 从答案区切片。
3. metadata（subject/grade/year/school/knowledge_points）是并入本 manifest，还是
   由单独 metadata annotation 输出。
4. `semantic_status` 是否需要 enum 和 fallback，还是只允许 complete/partial。
5. Section 与 Admission Unit 的层级是否足够表达“一题多问、任务式大题、写作选项”。
