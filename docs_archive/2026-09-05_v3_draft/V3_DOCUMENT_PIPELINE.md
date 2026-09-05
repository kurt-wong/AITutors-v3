# AI Tutor V3 — 文档解析与题目编译管线

Version: 3.0
Date: 2026-09-05
Status: V3 核心管线基线

## 1. 设计目标

把教师版 PDF/DOCX 转换为可验证、可追溯的 Question IR，再由确定性代码编译为数据库实体。

核心原则：

> LLM 只描述 Source 的语义；Source Resolver 找到 Source；Compiler 组装题目；Gate 决定是否允许入库。

## 2. 制品分层

```text
L0 Source File
   ↓
L1 Source Artifacts
   ├─ native text
   ├─ OCR/layout
   ├─ image blocks
   ├─ table blocks
   └─ page geometry
   ↓
L2 Semantic Metadata
   ↓
Source Resolver Result
   ↓
Question IR
   ↓
Compiled Candidate
   ↓
Admission
```

所有制品版本化。L0/L1 不可变。

## 3. L1 Source Artifact

L1 不直接等于“最终题目文本”。它是对文档的可追溯解析表示。

每个 Source Unit 至少包含：

- artifact_id
- page_no
- source_type
- block_type
- raw_text
- normalized_text
- bbox（如有）
- order
- provenance
- extraction_confidence

PDF：

- Native 文本作为证据源。
- PP-StructureV3 作为版面/OCR/公式源。
- PyMuPDF 提供页面几何、图片对象、文本层辅助证据。

不同源冲突时保留冲突，不静默覆盖。

## 4. L2 Semantic Metadata

V3 推荐使用 JSON sidecar，不修改 L1。

LLM 输出：

- document metadata claims
- sections
- semantic units
- semantic components
- semantic relations
- short exact text anchors
- original question type
- answer/explanation zone claims
- optional difficulty/confidence

LLM 不输出：

- 最终题干
- 完整选项文本
- 最终数据库字段
- 字符坐标
- 最终 line_id
- canonical question type
- admission decision

## 5. Anchor

Anchor 表达：

> 我要在 Source 中找到哪一段内容？

推荐结构：

```json
{
  "start_text": "...",
  "end_text": "...",
  "context_text": "...",
  "granularity": "single_line|fragment"
}
```

Anchor 必须来自 Source。

Resolver 按以下顺序定位：

1. exact unique
2. normalized unique
3. context-assisted
4. controlled fuzzy
5. ambiguous / unresolved

只有唯一且证据充分时才生成 resolved span。

歧义不得自动选择第一匹配。

## 6. Semantic Unit

最小核心单位：

```text
standalone_question
composite_unit
shared_material
sub_question
```

关系单独表达，例如：

```text
question --depends_on--> shared_material
sub_question --belongs_to--> composite
composite --uses--> shared_material
```

不要把关系隐藏在 `section_id` 或数组位置中。

## 7. Composite 判定

必须满足语义依赖，而非仅仅共享 section。

典型 composite：

- 完形填空整篇材料 + 多个空
- 阅读理解文章 + 多个问题
- 七选五文章 + 多个空
- 同一实验材料 + 多个子问

非 composite：

- 同一 section 中恰好连续的独立选择题
- 同一图片被两个题分别使用但没有共同任务依赖

### 原则

> Shared material + task dependency → composite。
> Shared section alone → not composite。

## 8. Question IR

Question IR 是编译器输入，不直接等于 DB schema。

示例：

```json
{
  "unit_id": "u42",
  "kind": "composite",
  "question_number": "26-28",
  "question_type": "reading",
  "materials": ["m1"],
  "stem": ["span-1"],
  "sub_questions": [
    {
      "qno": "26",
      "stem": ["span-2"],
      "options": ["span-3"],
      "answer": {"source_zone": "answer_table", "anchor": "..."}
    }
  ]
}
```

IR 必须能够：

1. 从 Source 重建展示文本；
2. 表达独立题和 composite；
3. 表达共享材料；
4. 表达图片和答案来源；
5. 进入质量门禁；
6. 被 Candidate 完整保存。

## 9. Deterministic Compiler

Compiler 只做确定性操作：

- 根据 resolved span 提取文本；
- 合并材料；
- 去重相同 Source span；
- 组装选项；
- 组装子题；
- 生成 provenance；
- 计算 content hash；
- 生成 Question / Instance materialization plan。

Compiler 不做：

- 语义猜测；
- “看起来像题目”的自动判断；
- 无证据答案猜测；
- 自动修复 LLM 语义错误。

## 10. Answer / Explanation

答案来源优先级：

1. 教师版答案/解析区域
2. 文档中明确标记的答案/解析
3. LLM 仅用于判断归属或在明确允许的缺失场景下生成兜底

答案状态必须区分：

```text
source_located
complete
content_verified
```

只有满足项目定义的 admission 条件才可 approved。

## 11. Image

Image Entity 至少包含：

- image_id
- object_key
- page_no
- bbox
- placement
- source_artifact
- provenance
- figure_hash

无 page/bbox/provenance：

```text
→ missing_evidence
→ review
```

禁止整页兜底。

## 12. Quality Gate

Gate 至少检查：

### Source
- 所有内容都有 provenance
- span 可解析且唯一
- 无越界

### Structure
- 题号完整
- stem 完整
- options 完整
- composite/subquestion 结构一致
- shared material 不重复

### Answer
- 答案存在或明确标记 missing
- 答案与题目归属一致
- 不能因为“答案区出现过该词”就判定成功

### Image
- 图片归属有空间/语义证据

### Semantic
- standalone question 可以独立回答
- composite 子题依赖关系完整

Gate 输出：

```text
approve
review
reject
```

并附结构化 reason codes。

## 13. 单一生产主路径

V3 禁止长期存在：

```text
pipeline A
pipeline B
legacy pipeline
fallback pipeline
special subject pipeline
```

如果某个 Provider 失败，应该在对应能力层处理，而不是复制整条解析管线。

## 14. 解析失败原则

失败必须成为显式状态：

```text
ocr_unavailable
source_conflict
anchor_unresolved
semantic_ambiguous
answer_unverified
image_unresolved
quality_failed
```

任何失败都不能静默转换为“成功但内容不完整”。
