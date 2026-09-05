# AI Tutor V3 — 数据模型设计原则

Version: 3.0
Date: 2026-09-05
Status: V3 数据设计基线

## 1. 设计目标

V3 数据模型必须优先表达业务事实，而不是迎合某次解析管线的中间变量。

核心实体：

```text
Document
  └─ SourceArtifact
       └─ SemanticAnnotation
            └─ QuestionCandidate
                 ├─ Question
                 ├─ QuestionInstance
                 ├─ QuestionImage
                 └─ QuestionKnowledge
```

Task / LLM Audit 与 Question 数据生命周期独立。

## 2. Document

保存：

- 原始文件对象 key
- 文件名
- 文件类型
- 上传元数据
- processing status
- artifact versions

不保存不可追溯的“最终题目文本”作为唯一事实源。

## 3. SourceArtifact

表示某份文档的解析制品。

建议：

- artifact_id
- document_id
- artifact_type
- version
- source_provider
- content/location
- checksum
- created_at

L0/L1 artifact 不可变。

## 4. SemanticAnnotation

保存 LLM 对 Source 的结构判断。

必须记录：

- annotation_id
- document_id
- model/provider
- prompt_version
- schema_version
- source_artifact_version
- raw_json
- status
- created_at

SemanticAnnotation 与 Question 分开，允许重新编译而不重新调用 LLM。

## 5. Question

代表去重后的“题目本体”。

核心字段：

- id
- subject
- grade
- question_type
- stem/material structure
- options
- answer
- explanation
- source_type
- status
- content_hash
- quality metadata

如果 composite 关系稳定，优先考虑独立的 Composite / SubQuestion / Material 表，而不是无限扩张 JSONB。

## 6. QuestionInstance

表示 Question 在具体来源中的一次出现。

至少：

- id
- question_id
- document_id
- source_question_number
- source_page
- source_metadata
- occurrence information

同一道 Question 可以有多个 Instance。

## 7. Material

共享材料是独立事实，不是复制进每个子题的字符串。

至少：

- material_id
- source spans
- text projection
- type
- provenance

Question/SubQuestion 通过关系引用 Material。

## 8. Image

Image 是 Source-derived entity，不是 Question 的一个简单字符串字段。

建议：

- image_id
- figure_hash
- object_key
- source_artifact_id
- page_no
- bbox
- placement
- provenance

题目关联使用关系表。

## 9. Candidate

Candidate 必须是 admission snapshot。

它必须能够在不重新运行 LLM 的情况下重建：

- Question
- Instance
- Images
- Materials
- SubQuestions
- Knowledge mappings
- quality/admission evidence

因此 Candidate 不能只保存一个 `stem` + `answer`。

## 10. Admission Transaction

批准 Candidate 必须在一个事务中完成：

```text
Candidate
  ↓
validate snapshot
  ↓
find/create Question
  ↓
create QuestionInstance
  ↓
create Material relations
  ↓
create Image relations
  ↓
create Knowledge relations
  ↓
mark Candidate admitted
  ↓
COMMIT
```

任一关键步骤失败，整个 admission rollback。

不能出现：

```text
Question 已创建
Instance 没创建
Image 丢失
Knowledge 丢失
Candidate 仍显示 approved
```

## 11. JSONB 使用边界

允许：

- 真正动态的 answer_structure
- Provider-specific metadata
- 可版本化的 raw annotation
- 未来扩展字段

不允许用 JSONB 隐藏稳定关系：

- Question ↔ Instance
- Question ↔ Image
- Question ↔ Knowledge
- Composite ↔ SubQuestion
- Question ↔ Material

## 12. Hash / Dedup

content_hash 只用于确定性精确去重。

语义相似不是 hash。

V3 第一版建议：

```text
exact hash
   ↓
明确相似候选
   ↓
人工/独立语义判断
```

不要在首次入库就引入复杂自动 merge。

## 13. Migration

所有 schema 变化必须：

```text
Model
+ Migration
+ Test
+ Documentation
```

禁止手工 ALTER TABLE 作为正常开发流程。
