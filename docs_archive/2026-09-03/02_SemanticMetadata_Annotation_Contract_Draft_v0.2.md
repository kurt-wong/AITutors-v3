# Semantic Metadata Annotation Contract Draft

Version: DRAFT-0.2
Status: 草案，供评审；未实施
Date: 2026-09-03
Supersedes: `02_SemanticMetadata_Annotation_Contract_Draft.md` v0.1
目的：定义 LLM Semantic Metadata Annotator 的输出契约。

本版按“以 question 为核心、LLM 负责理解语义、程序负责确定事实”修订。

## 1. v0.2 修订要点

相对 v0.1：

1. 顶层不再叫 `admission_units`，改为 `semantic_units`；Admission 是后续 Gate 的结果。
2. LLM 不再输出 line_ref、行号、坐标或 final source span。
3. LLM 使用受控 semantic reference 指认源文本，不直接转录正文。
4. Annotation 不再把“答案正文”作为正常输出；答案由程序从答案来源切片。
5. 增加 Source Resolver 输入/输出边界和 Semantic IR 预期能力，防止旧
   `line_id -> slicer` 模型回潮。

## 2. 核心分工

```text
LLM Semantic Metadata Annotator
  1. 判断这是什么：question / composite / shared_material / stem / option /
     answer / blank / image / sub_question
  2. 判断谁依赖谁：Q11 -> M1
  3. 判断组合边界：连续题号不等于组合题
  4. 输出 semantic reference 指认源位置

Source Resolver
  1. Exact Match
  2. Normalized Match
  3. Context / Structural Match
  4. Fuzzy Match
  5. Ambiguity -> Retry / Candidate / Review

Semantic Question IR
  保存 resolved span + 题目树 + 依赖关系

Deterministic Compiler
  把 IR 编译成最终题目/综合题/子题

Semantic + Evidence Gate
  判断结构、来源、语义依赖和 admission 结果
```

## 3. LLM 允许做什么

LLM 允许：

- 判断题目类型、section、独立/组合结构；
- 判断共享材料、材料依赖；
- 判断哪个 sub_question 依赖哪个 material；
- 判断 blank、option、answer、image 的归属；
- 判断题目之间的语义依赖；
- 给出受控 semantic reference；
- 给出结构化 confidence；
- 给出 metadata 判断（subject/grade/year 等）。

LLM 禁止：

- 重写/转录 Markdown 正文；
- 输出 stem/material/options/answer/explanation 的完整文本；
- 输出最终行号、line_ref、offset、source span；
- 在 annotation 中生成“这是答案”的正文；
- 输出 CoT/解题过程；
- 替代 Source Resolver 或 Compiler 做定位和组装。

## 4. Semantic Reference

LLM 指认源位置时，不输出行号，也不直接转录正文内容，而是输出受控的
semantic reference：

```json
{
  "role": "shared_material",
  "label": "M1",
  "start_marker": {
    "kind": "instruction_marker",
    "text": "阅读下面短文"
  },
  "end_marker": {
    "kind": "instruction_marker",
    "text": "根据上述材料回答第11～13题"
  }
}
```

`M1` 是 annotation 内部 ID，不是最终数据库 ID。Source Resolver 使用该 reference
在 Immutable Source 中定位真实位置。

### 4.1 Reference 类型

| kind | 内容 | 示例 |
|---|---|---|
| question_label | 题号/子题号 | `1`、`11` |
| option_label | 选项字母 | `A` |
| blank_label | 空位标识 | `第1空` |
| instruction_marker | 源中出现的短指令/边界标记 | `阅读下面短文` |
| answer_zone | 答案来源区域类型 | `answer_table`、`inline_answer` |
| explanation_zone | 详解来源区域类型 | `inline_explanation` |

### 4.2 规则

1. `question_label` / `option_label` / `blank_label` 是结构角色，不携带正文内容。
2. `instruction_marker` 只允许用于材料/任务指令/明确边界，不允许抄题干、选项、
   答案或材料正文。
3. `instruction_marker` 必须能在 Immutable Source 中精确出现；源中缺失或改动时，
   Resolver 返回 `missing`，不得猜测。
4. 禁止使用整段材料、整道题干、完整答案区作为 reference。
5. 跨页/整页文本不得作为 reference。
6. Resolver 不能通过 reference 的唯一性保证语义；多个候选位置进入歧义状态。

Source Resolver 的输入输出契约见
`03_SourceResolver_SemanticIR_Gate_Contract_Draft.md`。

## 5. 顶层 Annotation Manifest

```json
{
  "annotation_schema": "semantic-metadata-annotation/v0.2",
  "annotation_version": "llm-semantic-v1",
  "annotation_run_id": "uuid",
  "source_version_id": "uuid",
  "document_id": "uuid",
  "document_metadata": {
    "subject": null,
    "grade": null,
    "year": null,
    "school": null,
    "metadata_source": "filename_or_upload",
    "metadata_confidence": 0.0
  },
  "sections": [],
  "semantic_units": [],
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
| annotation_schema | 固定 schema 名，后续变化升版本 |
| source_version_id | 指向 sealed immutable source version |
| document_metadata | 只表示 metadata claim，不入库事实；上传/文件名优先 |
| sections | 卷面结构声明 |
| semantic_units | 以 question/composite 为中心的语义单元 |
| annotation_meta | 诊断元数据，不进入最终 Question 事实 |

### 5.1 LLM payload 与管线 envelope 分离

顶层 manifest 是管线保存格式，不应要求 LLM 输出全部字段。

LLM 只输出语义 payload：

```json
{
  "document_metadata_claims": {
    "subject": null,
    "grade": null,
    "year": null,
    "school": null
  },
  "sections": [],
  "semantic_units": []
}
```

以下字段只能由 pipeline 注入：

- `annotation_schema`
- `annotation_version`
- `annotation_run_id`
- `source_version_id`
- `document_id`
- `annotation_meta`
- `metadata_source` / `metadata_confidence` 的最终判定

这样 LLM 不需要生成或猜测程序 ID，也避免把坐标/版本信息混入 semantic payload。

## 6. Semantic Unit 是核心对象

不再以 line_id 为主，而以 question 语义对象为主。

### 6.1 standalone question

```json
{
  "unit_id": "Q1",
  "unit_type": "standalone_question",
  "question_number": "1",
  "section_id": "SEC-1",
  "original_question_type": "single_choice",
  "canonical_question_type": "single_choice",
  "content": {
    "stem": {
      "role": "stem",
      "question_label": "1"
    },
    "options": [
      {
        "label": "A",
        "role": "option",
        "question_label": "1"
      }
    ],
    "answer": {
      "role": "answer",
      "question_label": "1",
      "answer_zone": "answer_table"
    },
    "explanation": {
      "role": "explanation",
      "explanation_zone": "inline_explanation"
    }
  },
  "confidence": 0.98
}
```

说明：

- annotation 不写 `stem`/`option`/`answer` 正文。
- `answer` 只负责声明“该题答案在答案表/题后答案区”，不保存答案正文。
- Source Resolver 结合题号和 role 在源中确定边界，不需要 LLM 给出正文。

### 6.2 composite unit

```json
{
  "unit_id": "U11-13",
  "unit_type": "composite_unit",
  "question_number_range": "11-13",
  "section_id": "SEC-1",
  "shared_components": {
    "material": {
      "role": "shared_material",
      "label": "M1",
      "start_marker": {
        "kind": "instruction_marker",
        "text": "阅读下面短文"
      },
      "end_marker": {
        "kind": "instruction_marker",
        "text": "根据上述材料回答第11～13题"
      }
    },
    "word_bank": null,
    "shared_option_pool": null,
    "task_instruction": {
      "role": "task_instruction",
      "start_marker": {
        "kind": "instruction_marker",
        "text": "根据上述材料回答第11～13题"
      }
    }
  },
  "sub_questions": [
    {
      "question_id": "Q11",
      "question_number": "11",
      "canonical_question_type": "single_choice",
      "content": {
        "stem": {
          "role": "stem",
          "question_label": "11"
        },
        "options": [
          {
            "label": "A",
            "role": "option",
            "question_label": "11"
          }
        ],
        "answer": {
          "role": "answer",
          "question_label": "11",
          "answer_zone": "answer_table"
        }
      },
      "depends_on": [
        {
          "type": "material_dependency",
          "target": "M1",
          "required": true
        }
      ],
      "independence_after_material": true,
      "confidence": 0.97
    }
  ],
  "confidence": 0.95
}
```

说明：

- `composite_unit` 是“共享组件 + 多个依赖该组件的 sub_questions”的原子对象。
- `independence_after_material=true` 表示该子题结合材料后可独立作答，不是“脱离材料
  也能独立作答”。
- composite 的原子性是 IR/Gate 不变量，不由 LLM 输出。

## 7. 独立/组合判断

判断依据是语义依赖，不是连续题号：

```text
材料 M1
 ├── Q11
 ├── Q12
 └── Q13
```

若 Q11/Q12/Q13 都依赖 M1，输出一个 `composite_unit`。

```text
Q11 独立
Q12 独立
Q13 独立
```

即使连续出现，也必须输出三个 `standalone_question`。

## 8. 关系表达

LLM 需要表达关系，而不仅是并列对象：

```json
{
  "from": "Q11",
  "to": "M1",
  "type": "material_dependency",
  "required": true
}
```

关系类型：

| type | 含义 |
|---|---|
| contains | composite 包含 sub_question |
| material_dependency | 子题依赖共享材料 |
| word_bank_dependency | 子题依赖词库 |
| option_pool_dependency | 子题依赖共享选项区 |
| blank_mapping | blank 对应某 sub_question/answer |
| option_mapping | option label 与源文本对应 |
| image_reference | image 属于 material/stem/answer |
| scoring_standard_of | scoring_standard 属于 question/unit |

## 9. 内容关系必须显式

必须表达：

- 哪个 blank 属于哪个 sub_question；
- 哪个 option 属于哪个 sub_question；
- 哪个 answer 对应哪个 sub_question；
- 哪个 image 属于哪个 material 或题；
- 哪个 sub_question 依赖哪个 material。

示例：

```json
{
  "blank_mapping": {
    "B1": {
      "question_id": "Q11",
      "answer_role": "answer",
      "blank_label": "第1空",
      "question_label": "11"
    }
  }
}
```

## 10. 不允许的字段

Annotation JSON 不允许：

```json
{
  "line_refs": [],
  "corrected_line_ids": [],
  "resolved_span": {},
  "final_line_ids": [],
  "answer_text": "...",
  "stem_text": "...",
  "material_text": "..."
}
```

line/span 只存在于 Source Resolver 输出和 Semantic Question IR。

## 11. Source Resolver 边界

Source Resolver 接收：

- sealed source version；
- Semantic Annotation；
- semantic reference。

Source Resolver 输出：

- resolved source span；
- 每个 role 对应的 line_ref 范围；
- resolution status：exact / normalized / contextual / fuzzy / ambiguous；
- ambiguity 列表；
- 与 Annotation 中 relation 对应的 resolved relation。

解析顺序：

```text
Exact Match
  -> Normalized Match
  -> Context / Structural Match
  -> Fuzzy Match
  -> Ambiguity -> Retry / Candidate / Review
```

禁止模糊匹配后静默接受错误结果。多位置命中或边界无法确定时，进入歧义状态。

## 12. Semantic Question IR 预期能力

虽然 Semantic IR 契约单独设计，但 Annotation 契约必须满足以下可编译性：

1. 每个 semantic unit 都能编译成 question/composite 对象。
2. 每个 dependency 都能解析到同一个 unit 内的 material。
3. 每个 sub_question 都有 stem/answer 对应关系。
4. blank/option/answer 能建立闭合映射。
5. 不存在悬空 `depends_on`。
6. 独立题不存在必需 material_dependency。

Annotation 如果不能满足这些可编译性，Source Resolver/IR 阶段应返回 incomplete，
而不是用后处理猜补。

## 13. Confidence 与 Evidence

Annotation 的 confidence 只代表 LLM 对语义判断的置信度，不代表程序验证。

```json
{
  "confidence": 0.97,
  "reasoning_basis": "dependency_from_shared_material"
}
```

约束：

- 不存 CoT；
- 不存“我觉得像”等自由文本；
- evidence 由 Resolver/Compiler/Gate 产生。

## 14. Answer Verification 分离

Annotation 不写最终 `verified=True`。程序必须分别记录：

```json
{
  "answer_status": {
    "source_located": false,
    "complete": false,
    "verified_correct": null
  }
}
```

语义：

- `source_located`：找到答案来源；
- `complete`：答案完整；
- `verified_correct`：答案与权威答案/人工确认一致。

“找到答案来源”不等于“答案完整”，也不等于“答案正确”。

## 15. 元数据优先级

metadata 字段按本项目规则：

1. 上传表单/文件名/文档路径优先；
2. LLM 只填空或高置信度覆盖；
3. `None` 不得写成字符串 `"None"`；
4. 知识树为空时不得静默跳过 knowledge_point 映射。

## 16. 校验规则

### 16.1 Annotation 自身

- 必须包含 `source_version_id` 与 `semantic_units`。
- LLM payload 不含 source_version_id/document_id/annotation_run_id/annotation_meta。
- 不允许出现 line_refs/corrected_line_ids/resolved_span。
- question_label/option_label/blank_label 不携带正文。
- instruction_marker 只能引用短边界/任务指令，禁止整段原文复制。
- unit_id 唯一，dependency 目标存在。

### 16.2 独立/组合

- standalone question 无必需 material_dependency；
- composite unit 有至少一个共享组件；
- sub_question 若需材料，必须显式 depends_on；
- 不允许连续题号自动组合，Annotation 是唯一组合声明来源。

### 16.3 原子性

- composite unit 中任一 sub_question 不完整，整体 incomplete；
- 不允许只把可解析子题单独 approved；
- 共享材料只存一次，不复制到每个 sub_question stem。

## 17. 与旧 L2 的迁移

新 Annotation 不与旧 L2 混用：

- 旧 `llm_annotated_markdown` 保留为 legacy；
- 新 annotation 使用 `annotation_schema=semantic-metadata-annotation/v0.2`；
- Source Resolver 输出 resolved span；
- Compiler 输出兼容 DISPLAY_CONTRACT 的 question/composite；
- 新旧结果可并行跑 golden 对比。

## 18. 验收标准

1. LLM Annotation JSON 不含 line_refs/resolved_span/正文文本。
2. 综合题结构来自 Annotation，不来自代码按题号合并。
3. 去掉一个 dependency 后 IR 显式 incomplete。
4. 材料 reference 被替换/消失后 Resolver 返回 ambiguous/missing，不能静默接受。
5. 答案正文不在 Annotation 中出现。
6. 同一 source + 同一 prompt 可重复回放。

## 19. 已定实施决策

1. `instruction_marker` 的生成规则直接进入 prompt 和 schema 校验；源中缺失时标记
   `missing`，不得静默使用模糊文本。
2. metadata（subject/grade/year/school/difficulty/score/knowledge_points）并入本
   Annotation，但只作为 claim，仍遵守上传/文件名优先级，且不直接写入最终事实表。
3. Semantic IR 的 resolved span、relation 与 Gate 结构由
   `03_SourceResolver_SemanticIR_Gate_Contract_Draft.md` 定义，本文件不再留下空白。
4. 0.5B Structure Annotator 第一阶段只训练 semantic role/dependency/label，不训练
   开放文本 marker 生成；instruction_marker 在主 LLM 阶段生成，且必须由 Resolver
   做精确/规范化校验。达不到自动 admission 标准时进入 review，不启动训练堆叠。
