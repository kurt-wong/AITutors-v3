# AI Tutor Personal Edition — 数据库结构设计

Version: 4.6
Status: Phase 0 文档冻结基线；语义源/中间态表结构 planned
Date: 2026-09-04
Supersedes: DSD v4.5
Source of truth: `Docs/00_Requirements/REQUIREMENTS_AND_SOLUTION.md`

---

## 1. 目的

本文件定义项目数据库结构，是数据表和字段的唯一权威来源。

所有 Repository、Migration 和 Service 数据访问必须符合本文件。

---

## 2. 存储栈

允许：

- PostgreSQL 16
- pgvector
- MinIO 或 NAS 对象存储
- Redis

禁止：

- Qdrant
- Milvus
- Weaviate
- ChromaDB

---

## 3. 设计原则

### 3.1 Fact-Only

数据库只保存事实：

- 题目内容
- 答案
- 详解
- 元数据
- 来源和出现次数
- 错题记录
- 练习记录
- 掌握度

数据库禁止保存：

- Prompt
- 思维链
- 临时 LLM 输出
- Agent 对话

### 3.2 内容与元数据分离

题目内容字段：

- stem
- options
- answer
- explanation

元数据字段：

- subject
- grade
- year
- school
- question_type
- score
- difficulty
- knowledge_points
- occurrence_count

### 3.3 单学生

当前版本按单学生设计。

用户表预留 role，但业务默认只有一个管理员和一个学生账号。

### 3.4 知识树静态

知识树节点由管理员维护。

AI 只能把题目映射到已有节点，不能创建新节点。

### 3.5 真题与生成题

题目来源类型：

- document：来自原始文档的真题
- generated：AI 生成且审核通过的题
- student：学生 JPG 错题新建的题

---

## 4. 表结构

### 4.1 users

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| username | VARCHAR | 唯一 |
| password_hash | VARCHAR | 登录密码哈希 |
| role | VARCHAR | admin / student |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### 4.2 subjects

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| code | VARCHAR | 唯一编码 |
| name | VARCHAR | 学科名 |
| description | TEXT | |
| created_at | TIMESTAMPTZ | |

### 4.3 documents

保存原始 PDF/DOCX 文件和处理状态。

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| filename | VARCHAR | 原始文件名 |
| file_type | VARCHAR | pdf / docx |
| object_key | VARCHAR | 对象存储 key |
| subject | VARCHAR | 可选上传元数据 |
| grade | VARCHAR | 可选上传元数据 |
| year | INTEGER | 可选上传元数据 |
| school | VARCHAR | 可选上传元数据 |
| upload_status | VARCHAR | queued / processing / completed / failed |
| processing_status | VARCHAR | pending / parsing / annotating / reviewing / completed / failed |
| error_message | TEXT | |
| native_markdown | TEXT | 电子文本 PDF 的 L1 Native Markdown（P2 落地） |
| ocr_markdown | TEXT | 扫描件/OCR 路径的 L1 Markdown（P2 落地） |
| llm_annotated_markdown | TEXT | legacy：旧 L2 标注 JSON；Phase 0 后只读兼容镜像 |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

> Phase 0 冻结后：`native_markdown/ocr_markdown/llm_annotated_markdown` 只保留为
> legacy 只读兼容镜像。新链正文/行/表格 cell/fragment 证据写入
> `document_source_versions` 与 4.26/4.33-4.35，Annotation/Resolver/IR 按阶段写入
> 4.30-4.32 可审计表。

### 4.4 document_processing_logs

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK documents |
| stage | VARCHAR | |
| message | TEXT | |
| created_at | TIMESTAMPTZ | |

### 4.5 questions

核心题目表。

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| subject_id | UUID | FK subjects |
| grade | VARCHAR | 高一/高二/高三 |
| question_type_id | UUID | FK question_types |
| original_question_type | VARCHAR(50) | LLM 原始细粒度题型 code（cloze/grammar_fill/seven_to_five/essay/writing 等），可为空 |
| section_id | VARCHAR(100) | 来源卷面 section/共享材料区标识，可为空 |
| score | NUMERIC | 分值，可为空 |
| difficulty | INTEGER | 1-5 |
| stem | TEXT | 题干 |
| options | JSONB | 选项数组 |
| answer | TEXT | 标准答案 |
| answer_structure | JSONB | 结构化答案元数据（多答案/范围/扩展结构），可为空 |
| word_bank | JSONB | 选词填空题组共享词库，可为空 |
| explanation | TEXT | 详解 |
| source_type | VARCHAR | document / generated / student |
| source_document_name | VARCHAR | 来源文档名 |
| status | VARCHAR | approved / reviewing / rejected；新链只写 approved/rejected，reviewing 为 legacy 旧记录 |
| confidence | NUMERIC | 0-1 |
| occurrence_count | INTEGER | 缓存字段，由 Instance COUNT 驱动 |
| content_hash | VARCHAR(64) | SHA256（规范化题干+选项+题型），Step 5 已实现，可为 NULL（历史数据） |
| is_composite | BOOLEAN | 是否为综合题，默认 false |
| sub_questions | JSONB | 综合题子题元数据（可递归 sub_sub_questions） |
| review_reason | VARCHAR(200) | 审核原因分类 |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

说明：

- year / school 已迁移到 question_instances（Phase 2A Step 1，2026-08-21）。
- content_hash 规范化/计算见 `app/domains/document/content_hash.py`（Step 5 已实现，20260821_0005 回填）。
- occurrence_count 为缓存字段，由 COUNT(question_instances) 驱动更新。

### 4.6 question_images

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| question_id | UUID | FK questions |
| image_key | VARCHAR | 对象存储 key |
| image_type | VARCHAR | diagram / question_image / formula_image |
| description | TEXT | |
| image_order | INTEGER | 排序 |
| page_no | INTEGER | 配图来源页码 |
| bbox | JSONB | 配图在来源页面上的坐标 |
| placement | VARCHAR | stem / options / answer / explanation / page_context |
| sub_question_qno | VARCHAR(100) | 答案图绑定的子题号，可为空 |
| source | VARCHAR | native / paddleocr / vl / manual |
| figure_id | VARCHAR | 同一物理图在文档级去重中的稳定标识 |
| created_at | TIMESTAMPTZ | |

说明：

- 物理图存储去重：同一 `figure_id` 在对象存储中只保留一份。
- 题-图关联允许多对多：共享材料题场景下，同一 `figure_id` 可通过多条 `question_images` 记录关联到多道题。
- 无显式证据的跨题广播必须抑制（详见 `V1_LESSONS.md` 3.4/3.26）。

### 4.7 question_instances

保存同一题在不同来源中的出现实例。

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| question_id | UUID | FK questions |
| document_id | UUID | FK documents，NOT NULL（Phase 2A Step 1 新增） |
| source_type | VARCHAR | document / generated / student |
| source_document_name | VARCHAR | 来源文档名（冗余保留，便于查询） |
| source_page | INTEGER | 来源页码，可为空 |
| source_question_number | VARCHAR | 来源原始题号，可为空 |
| year | INTEGER | 从 questions 迁移（Phase 2A Step 1） |
| school | VARCHAR | 从 questions 迁移（Phase 2A Step 1） |
| occurrence_no | INTEGER | 同一来源内出现序号 |
| source_version_id | UUID NULL | Phase 1 planned：本实例引用 sealed source version |
| annotation_run_id | UUID NULL | Phase 2 planned：本实例引用 semantic annotation run |
| resolver_run_id | UUID NULL | Phase 3 planned：本实例引用 resolver run |
| ir_snapshot_id | UUID NULL | Phase 3 planned：本实例引用 semantic IR snapshot |
| created_at | TIMESTAMPTZ | |

说明：

- document_id 为 Phase 2A Step 1 新增，NOT NULL，替代 source_document_name 作为精确关联。
- 唯一约束：`(document_id, source_question_number)` WHERE source_question_number IS NOT NULL。
- year / school 从 questions 表迁移而来（Phase 2A Step 1）。

### 4.8 question_knowledge

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| question_id | UUID | FK questions |
| knowledge_node_id | UUID | FK knowledge_nodes |
| confidence | NUMERIC | 0-1 |
| is_primary | BOOLEAN | 是否主知识点 |
| mapping_source | VARCHAR(20) | llm / rule / manual（Phase 2A Step 1 新增） |
| review_status | VARCHAR(20) | approved / pending / rejected，默认 approved（Phase 2A Step 1 新增） |
| created_at | TIMESTAMPTZ | |

### 4.9 knowledge_nodes

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| subject_id | UUID | FK subjects |
| parent_id | UUID | 可空 |
| code | VARCHAR | 唯一编码 |
| name | VARCHAR | 节点名 |
| level | INTEGER | 层级 |
| description | TEXT | |
| created_at | TIMESTAMPTZ | |

### 4.10 question_types

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| subject_id | UUID | FK subjects |
| parent_id | UUID | 可空 |
| code | VARCHAR | 唯一编码 |
| name | VARCHAR | 细粒度题型名 |
| sort_order | INTEGER | 排序 |
| created_at | TIMESTAMPTZ | |

### 4.11 question_embeddings

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| question_id | UUID | FK questions |
| embedding | vector(2560) | pgvector，qwen3-embedding:4b |
| embedding_provider | VARCHAR | Ollama |
| embedding_dimension | INTEGER | 固定 2560 |
| created_at | TIMESTAMPTZ | |

### 4.12 wrong_upload_tasks

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| task_id | UUID | FK background_tasks |
| user_id | UUID | FK users |
| image_key | VARCHAR | 学生 JPG key |
| detected_count | INTEGER | 切分题数 |
| created_at | TIMESTAMPTZ | |

### 4.13 wrong_upload_items

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| upload_id | UUID | FK wrong_upload_tasks |
| question_id | UUID | 可空，匹配或新建后关联 |
| content_snapshot | JSONB | 识别出的题目内容 |
| metadata_snapshot | JSONB | 识别出的元数据 |
| status | VARCHAR | pending_review / approved / rejected |
| review_comment | TEXT | |
| created_at | TIMESTAMPTZ | |

### 4.14 wrong_questions

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK users |
| question_id | UUID | FK questions |
| source_type | VARCHAR | practice / jpg_upload |
| error_type | VARCHAR | 可空 |
| wrong_count | INTEGER | 默认 1 |
| last_wrong_time | TIMESTAMPTZ | |
| mastery_status | VARCHAR | mastered / reviewing / not_mastered |
| review_count | INTEGER | 默认 0 |
| last_review_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

### 4.15 practice_sessions

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK users |
| trigger_type | VARCHAR | manual / recommendation / admin |
| question_count | INTEGER | |
| status | VARCHAR | in_progress / completed / abandoned |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

### 4.16 practice_answers

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| session_id | UUID | FK practice_sessions |
| question_id | UUID | FK questions |
| question_snapshot | JSONB | 题目快照 |
| student_answer | TEXT | |
| is_correct | BOOLEAN | |
| duration_seconds | INTEGER | |
| knowledge_point_ids | JSONB | 关联知识点 |
| created_at | TIMESTAMPTZ | |

### 4.17 mastery_records

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK users |
| knowledge_node_id | UUID | FK knowledge_nodes |
| mastery_level | INTEGER | 0-2 |
| total_attempts | INTEGER | |
| correct_count | INTEGER | |
| recent_correct_rate | NUMERIC | 0-1 |
| updated_at | TIMESTAMPTZ | |

### 4.18 generation_jobs

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| task_id | UUID | FK background_tasks |
| task_type | VARCHAR | practice / paper |
| subject | VARCHAR | |
| grade | VARCHAR | |
| parameters | JSONB | 知识点、题型、难度、题量等 |
| ratio_snapshot | JSONB | 历史比例快照 |
| created_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |

### 4.19 generation_results

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| job_id | UUID | FK generation_jobs |
| question_id | UUID | FK questions |
| review_status | VARCHAR | pending / approved / rejected |
| review_comment | TEXT | |
| created_at | TIMESTAMPTZ | |

### 4.20 system_configs

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| config_key | VARCHAR | 唯一 |
| config_value | TEXT | |
| description | TEXT | |
| updated_at | TIMESTAMPTZ | |

---

### 4.21 background_tasks

统一后台任务表。文档解析、AI 生成、导出、错题识别等异步能力共用。

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| task_type | VARCHAR | document_parse / generation / export / wrong_question / embedding |
| status | VARCHAR | queued / running / succeeded / failed / review_required |
| progress | NUMERIC | 0-1 |
| current_stage | VARCHAR | 当前阶段 |
| error_detail | TEXT | 失败原因 |
| payload_json | JSONB | 任务入参 |
| result_json | JSONB | 任务结果摘要 |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### 4.22 domain_events

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| event_type | VARCHAR | QuestionCreated / QuestionReviewed 等 |
| entity_type | VARCHAR | question / wrong_question / practice_session |
| entity_id | UUID | |
| payload_json | JSONB | 事件数据 |
| created_at | TIMESTAMPTZ | |
| processed_at | TIMESTAMPTZ | 消费者处理时间，可为空 |

### 4.23 answer_extraction_retries

答案提取重试队列。答案提取失败时写入，支持 worker 自动重试和人工触发。

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK documents |
| task_id | UUID | FK background_tasks，可空 |
| error_detail | TEXT | 失败原因 |
| retry_count | INTEGER | 默认 0 |
| max_retries | INTEGER | 默认 3 |
| status | VARCHAR(20) | pending / retrying / succeeded / failed |
| last_retry_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

索引：`(status, created_at)`

### 4.24 question_candidates

保存 Semantic/Evidence Gate 判定为 `candidate` 的候选题目，供人工审核、批量统计和
离线回放。approved 写入 `questions`，不入本表；rejected 删除本表候选并写 Domain
Event/审计记录，不把 rejected 持久化到本表。

状态模型：

- `approved` -> `questions`（Question status=approved）
- `candidate` -> `question_candidates`（admission_status=candidate）
- `rejected` -> 删除候选，不留 `question_candidates` 行

现有 `gate_decision=review/reject` 列是 legacy 兼容字段；新链以
`admission_status` 为准，migration 后允许废弃 `gate_decision`。

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| subject_id | UUID | FK subjects，NOT NULL |
| grade | VARCHAR | 年级，可为空 |
| question_type_id | UUID | FK question_types，可为空 |
| score | NUMERIC(8,2) | 分值 |
| difficulty | INTEGER | 1-5 |
| stem | TEXT | 题干，NOT NULL |
| options | JSONB | 选项数组 |
| answer | TEXT | 标准答案 |
| answer_structure | JSONB | 结构化答案 |
| word_bank | JSONB | 共享词库 |
| explanation | TEXT | 详解 |
| source_type | VARCHAR(20) | document / generated / student，默认 document |
| source_document_name | VARCHAR(255) | 来源文档名 |
| confidence | NUMERIC(4,3) | 解析置信度 |
| content_hash | VARCHAR(64) | 规范化内容 SHA256 |
| is_composite | BOOLEAN | 是否综合题 |
| original_question_type | VARCHAR(50) | LLM 原始细粒度题型 |
| section_id | VARCHAR(100) | 卷面 section |
| sub_questions | JSONB | 综合题子题 |
| stem_line_ids | JSONB | 题干行号 |
| answer_line_ids | JSONB | 答案行号 |
| explanation_line_ids | JSONB | 详解行号 |
| shared_material_line_ids | JSONB | 共享材料行号 |
| shared_material_notes_line_ids | JSONB | 材料注释行号 |
| stem_region | JSONB | 题干区域 |
| answer_region | JSONB | 答案区域 |
| explanation_region | JSONB | 详解区域 |
| scoring_standard | TEXT | 评分标准 |
| shared_material | TEXT | 共享材料正文 |
| shared_material_notes | TEXT | 材料注释正文 |
| answer_images | JSONB | 答案图片元数据 |
| source_question_number | VARCHAR(50) | 来源题号 |
| source_page | INTEGER | 来源页码 |
| year | INTEGER | 来源年份 |
| school | VARCHAR(255) | 来源学校 |
| knowledge_points | JSONB | 知识点字符串列表 |
| question_images | JSONB | 候选题目配图元数据快照 |
| gate_decision | VARCHAR(20) | legacy：review / reject，只供旧记录迁移/审计；新链不再新建 |
| gate_reason | VARCHAR(200) | 未通过 rule/reason |
| gate_checks | JSONB | 完整 Gate 校验结果快照 |
| admission_version | VARCHAR(50) | Gate 规则版本，默认 1.0 |
| answer_provenance_json | JSONB | Gate 前 answer provenance |
| explanation_provenance_json | JSONB | Gate 前 explanation provenance |
| sub_qno_status | JSONB | 子题 qno 完整性状态 |
| document_id | UUID | FK documents，NOT NULL |
| source_version_id | UUID NULL | Phase 1 planned：候选来源 sealed source |
| annotation_run_id | UUID NULL | Phase 2 planned：候选来源 annotation run |
| resolver_run_id | UUID NULL | Phase 3 planned：候选来源 resolver run |
| ir_snapshot_id | UUID NULL | Phase 3 planned：候选来源 IR snapshot |
| admission_status | VARCHAR | Phase 5 canonical：本表行恒为 candidate；approved/rejected 不入本表 |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

索引：

- `(document_id)`
- `(gate_decision)`
- 部分唯一索引 `(document_id, content_hash)` WHERE `content_hash IS NOT NULL`
- `(document_id, admission_status)`（Phase 5 planned；candidate 行可建部分索引）

### 4.25 document_source_versions

语义管线 sealed source version。status=sealed 后禁止 UPDATE/DELETE。

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK documents，NOT NULL |
| run_id | UUID | 产生该 version 的 pipeline run/attempt |
| artifact_kind | VARCHAR | original_binary / raw_l1 / canonical_l1 |
| role | VARCHAR | native / ocr_ppsv3 / docx / canonical |
| provider | VARCHAR | native / ppsv3 / docx / manual |
| status | VARCHAR | draft / sealed / invalid |
| body_text | TEXT | 可由 line index 按 seq 确定性重建 |
| body_hash | CHAR(64) | SHA256(body_text) |
| integrity_hash | CHAR(64) | SHA256(body_text + line + image/table/cell/fragment index + provenance) |
| page_count | INTEGER | 有内容页数 |
| line_count | INTEGER | line index 行数 |
| total_pages | INTEGER | 文档总页数 |
| text_coverage | NUMERIC | Native/OCR 覆盖率 |
| source_meta | JSONB | 提取配置/OCR 证据/策略版本/original_sha256 |
| parent_version_id | UUID NULL | 修正/派生来源 |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

建议索引：

- `(document_id, artifact_kind, role, status)`
- `(document_id, created_at)`

### 4.26 document_source_lines

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK document_source_versions，NOT NULL |
| line_ref | VARCHAR | 如 P1L001 / N1L001，version 内唯一 |
| seq | INTEGER | version 内 1-based 连续 |
| page_no | INTEGER | 1-based |
| line_no_in_page | INTEGER | 页内序号 |
| text | TEXT | 行正文 |
| block_type | VARCHAR | text / formula / table / figure_placeholder |
| bbox | JSONB | page bbox，可空 |
| source | VARCHAR | 行来源 |
| raw_sources | JSONB | native/ppsv3/docx 文本与 native_line_id |
| selected_source | VARCHAR | canonical 最终来源 |
| evidence | TEXT | 选择依据 |
| confidence | NUMERIC | 行级置信度 |
| line_hash | CHAR(64) | SHA256(text + raw_sources + evidence) |
| created_at | TIMESTAMPTZ | |

唯一约束：

- `(source_version_id, line_ref)`
- `(source_version_id, seq)`

### 4.27 document_source_lines_image_refs

| Field | Type | Note |
|---|---|---|
| image_id | VARCHAR | L1Image.image_id |
| source_version_id | UUID | FK document_source_versions |
| line_refs | JSONB | 图片关联/上下文 line_refs |
| page_no | INTEGER | 必须存在 |
| bbox | JSONB | 必须存在 |
| placement | VARCHAR | stem / options / explanation / answer_area / standalone |
| source | VARCHAR | native / ppsv3 / docx |
| figure_id | VARCHAR | 文档级去重标识 |
| created_at | TIMESTAMPTZ | |

图片缺少 page_no/bbox/placement/source 任一字段时不得作为已定位图片。

### 4.28 document_active_sources

| Field | Type | Note |
|---|---|---|
| document_id | UUID | FK documents，PK |
| role | VARCHAR | native / ocr_ppsv3 / docx / canonical |
| source_version_id | UUID | FK document_source_versions，指向 sealed |
| selected_at | TIMESTAMPTZ | |
| selection_reason | TEXT | 自动/人工/回滚原因 |

### 4.29 document_source_selection_events

append-only 选择事件，记录 active source 每次变化。

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK documents |
| role | VARCHAR | |
| old_source_version_id | UUID NULL | |
| new_source_version_id | UUID | |
| selected_by | VARCHAR | system / manual |
| reason | TEXT | |
| run_id | UUID NULL | |
| created_at | TIMESTAMPTZ | |

### 4.30 semantic_annotation_runs

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK documents |
| source_version_id | UUID | FK document_source_versions |
| annotation_schema | VARCHAR | semantic-metadata-annotation/v0.3 |
| annotation_version | VARCHAR | prompt/model 版本 |
| model | VARCHAR | LLM 模型标识 |
| status | VARCHAR | complete / incomplete / invalid / retry |
| payload_json | JSONB | LLM semantic payload；禁止 line_ref/resolved_span/正文 |
| envelope_json | JSONB | pipeline 注入 run/source/annotation_meta |
| error_json | JSONB | schema/解析错误快照，不含 prompt 全文 |
| created_at | TIMESTAMPTZ | |

不保存 CoT/prompt 全文；只保存结构化 payload 与错误摘要。

### 4.31 semantic_resolver_runs

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| annotation_run_id | UUID | FK semantic_annotation_runs |
| source_version_id | UUID | FK document_source_versions |
| resolver_version | VARCHAR | |
| status | VARCHAR | resolved / incomplete / ambiguous / missing / invalid |
| result_json | JSONB | resolved spans/relations/ambiguity candidates |
| error_json | JSONB | 错误/证据摘要 |
| created_at | TIMESTAMPTZ | |

### 4.32 semantic_ir_runs

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| resolver_run_id | UUID | FK semantic_resolver_runs |
| source_version_id | UUID | FK document_source_versions |
| annotation_run_id | UUID | FK semantic_annotation_runs |
| ir_schema | VARCHAR | semantic-question-ir/v0.3 |
| status | VARCHAR | draft / ready / incomplete / invalid |
| ir_json | JSONB | Semantic Question IR；无 resolved span 不得 ready |
| gate_snapshot_json | JSONB | 后续 Gate 输出快照，可空 |
| created_at | TIMESTAMPTZ | |

### 4.33 document_source_tables

支持表格结构可回放定位；`table_id` 是 Resolver `cell_ref` 的根对象。

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK document_source_versions |
| table_id | VARCHAR | version 内唯一，如 T1 |
| page_no | INTEGER | 必须存在 |
| bbox | JSONB NULL | 页内 bbox |
| row_count | INTEGER | 逻辑行数 |
| column_count | INTEGER | 逻辑列数 |
| table_hash | CHAR(64) | SHA256(cells + layout metadata) |
| created_at | TIMESTAMPTZ | |

唯一约束：`(source_version_id, table_id)`。

### 4.34 document_source_table_cells

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK document_source_versions |
| table_id | VARCHAR | FK document_source_tables.table_id |
| row_index | INTEGER | 0-based |
| column_index | INTEGER | 0-based |
| row_span | INTEGER | 默认 1 |
| column_span | INTEGER | 默认 1 |
| text | TEXT | 单元格正文 |
| line_refs | JSONB | 关联 source lines |
| raw_sources | JSONB | provider 证据 |
| selected_source | VARCHAR | 最终来源 |
| evidence | TEXT | 选择/合并证据 |
| confidence | NUMERIC | 单元格置信度 |
| cell_hash | CHAR(64) | SHA256(text + raw_sources + spans) |
| created_at | TIMESTAMPTZ | |

唯一约束：`(source_version_id, table_id, row_index, column_index)`。

### 4.35 document_source_fragments

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK document_source_versions |
| fragment_id | VARCHAR | version 内唯一 |
| kind | VARCHAR | inline_option / blank_fragment / answer_fragment / instruction_marker / text_fragment |
| line_ref | VARCHAR NULL | 关联 source line，可空 |
| start_offset | INTEGER NULL | line 内 0-based 字符起点 |
| end_offset | INTEGER NULL | line 内字符终点（exclusive） |
| text | TEXT | 精确 fragment 正文 |
| text_hash | CHAR(64) | SHA256(text + source refs) |
| source | VARCHAR | 来源 provider |
| evidence | TEXT | 生成证据 |
| created_at | TIMESTAMPTZ | |

唯一约束：`(source_version_id, fragment_id)`。

---

### 4.36 worker_instances

Worker 进程登记表。真实 LLM worker 启动时写入随机 token 的 SHA256，
每 30 秒更新 heartbeat；Supervisor 将 heartbeat 超时或已 stopped 的
worker 所持有的 running/retrying 工作释放为 interrupted/pending，
禁止 worker 自动 requeue stale running 任务。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | PK |
| worker_id | VARCHAR(100) | 唯一 worker 标识 |
| worker_type | VARCHAR(50) | document_parse / answer_retry |
| token_hash | VARCHAR(64) | caller token SHA256，明文不入库 |
| pid | INTEGER | 进程 ID |
| status | VARCHAR(20) | active / stopped |
| last_heartbeat_at | TIMESTAMPTZ | 最近心跳 |
| started_at | TIMESTAMPTZ | 启动时间 |
| stopped_at | TIMESTAMPTZ | 停止/清理时间 |

关联变更：`background_tasks.worker_id` 标记任务当前处理者；
`answer_extraction_retries.worker_id/claimed_at` 标记重试原子 claim。

Migration：`20260905_0001_add_worker_safety_tables.py`。

## 5. 关系

```text
documents
├── document_processing_logs
├── document_source_versions
│   ├── document_source_lines
│   ├── document_source_lines_image_refs
│   ├── document_source_tables
│   ├── document_source_table_cells
│   ├── document_source_fragments
│   └── document_source_selection_events
├── document_active_sources
├── semantic_annotation_runs
├── semantic_resolver_runs
├── semantic_ir_snapshots
└── question_candidates

question_candidates
├── subjects
├── question_types
└── documents

document_source_versions → documents
document_source_lines → document_source_versions
document_source_lines_image_refs → document_source_versions
document_source_tables → document_source_versions
document_source_table_cells → document_source_versions / document_source_tables
document_source_fragments → document_source_versions
document_active_sources → documents / document_source_versions
document_source_selection_events → documents / document_source_versions
semantic_annotation_runs → documents / document_source_versions
semantic_resolver_runs → semantic_annotation_runs / document_source_versions
semantic_ir_snapshots → semantic_resolver_runs / document_source_versions / semantic_annotation_runs

questions
├── question_images
├── question_instances
├── question_knowledge
└── question_embeddings

knowledge_nodes
└── question_knowledge

question_types
└── questions

wrong_upload_tasks
└── wrong_upload_items

wrong_questions → questions

practice_sessions
└── practice_answers → questions

mastery_records → knowledge_nodes

generation_jobs
└── generation_results → questions

background_tasks
├── wrong_upload_tasks
└── generation_jobs

domain_events
└── 事件实体：question / wrong_question / practice_session
```

---

## 6. 索引建议

普通索引：

- questions(subject_id, grade, year)
- questions(question_type_id)
- questions(status, confidence)
- questions(source_type)
- question_knowledge(question_id, knowledge_node_id)
- question_instances(question_id, year)
- question_images(question_id, source, page_no)
- question_candidates(document_id)
- question_candidates(gate_decision)（legacy；migration 后可选移除）
- question_candidates(document_id, content_hash)（部分唯一，content_hash 非空）
- document_source_versions(document_id, artifact_kind, role, status)（Phase 1 planned）
- document_source_versions(document_id, created_at)（Phase 1 planned）
- document_source_lines(source_version_id, line_ref)（唯一，Phase 1 planned）
- document_source_lines(source_version_id, seq)（唯一，Phase 1 planned）
- document_source_tables(source_version_id, table_id)（唯一，Phase 1 planned）
- document_source_table_cells(source_version_id, table_id, row_index, column_index)
  （唯一，Phase 1 planned）
- document_source_fragments(source_version_id, fragment_id)（唯一，Phase 1 planned）
- semantic_annotation_runs(document_id, source_version_id, created_at)（Phase 2 planned）
- semantic_resolver_runs(annotation_run_id)（Phase 3 planned）
- semantic_ir_snapshots(resolver_run_id)（Phase 3 planned）
- wrong_questions(user_id, status)
- practice_answers(session_id, question_id)
- mastery_records(user_id, knowledge_node_id)
- background_tasks(task_type, status)
- domain_events(event_type, created_at)

向量索引：
- 当前 embedding 为 2560 维，超过 pgvector HNSW 索引 2000 维上限，初始阶段不建向量索引。
- 家庭题库规模下先使用暴力余弦检索；后续如需向量索引，先做降维或更换不超过 2000 维的模型。

---

## 7. L1/L2 与语义中间态落库说明

> 本节约束取代旧“L1/L2 不落库”结论。Phase 0 文档冻结后，L1/L2 不再是“只存在于
> 内存、不落库”的中间态；源证据和中间结果按可审计性落库，但只有最终事实进入
> questions/question_instances 业务查询。

规则：

1. raw/canonical L1 作为 sealed Source Version 落库，正文、行、图片、表格、
   表格单元格、fragment、provenance 必须可回放。
2. L1 原文不可修改；修正/重跑创建新 source version。
3. 旧 L2 的 line_id/anchors 只属于 legacy `documents.llm_annotated_markdown`。
4. Semantic Annotation、Resolver Run、Semantic IR 分别写入
   `semantic_annotation_runs/semantic_resolver_runs/semantic_ir_snapshots`。
5. 只有 Compiler 输出 + Gate 通过的内容写入 questions；questions 必须能通过
   question_instances/source_version_id 回溯证据。
6. `documents.native_markdown/ocr_markdown/llm_annotated_markdown` 保留为 legacy
   只读镜像，新链不再写入。

---

## 8. Phase 2A Schema（已实施）与未来 Family/Similarity 计划

> §8.1-8.3 描述的 Phase 2A schema 变更**已全部实施**（migration
> `20260821_0003`、`20260821_0005`、`20260827_0001`，2026-08-21/27 执行，
> `alembic current` 确认在 head）。当前 DB 即本节结构。
> §8.4/8.5 的 Family/Similarity 部分为**未来计划**，Phase 2D 之前不建。
> 代码审计（2026-08-21）补充：Phase 2A 还包含审核写回 DB、Worker 失败语义
> 修正、L2 完整持久化三项代码修复，详见 PLAN §7.1 和 ROADMAP P4A。

### 8.1 questions 表变更（已实施）

| 变更 | 类型 | 说明 |
|---|---|---|
| 新增 content_hash | VARCHAR(64) | 规范化文本 SHA256，用于 exact dedup。覆盖题干+选项+题型。答案/详解冲突进审核不静默覆盖。 |
| 移除 year | — | 已移到 question_instances。Question 只保留内容事实。 |
| 移除 school | — | 已移到 question_instances。 |
| occurrence_count | — | 派生值：COUNT(question_instances)。保留为缓存字段但由 Instance 驱动更新。 |

### 8.2 question_instances 表变更（已实施）

| 变更 | 类型 | 说明 |
|---|---|---|
| 新增 document_id | UUID FK documents | 替代 source_document_name 文本字段（NOT NULL）。 |
| 唯一约束 | — | 部分唯一索引 ix_question_instances_doc_qno：(document_id, source_question_number)（两者均非 NULL 时唯一）。 |

### 8.3 question_knowledge 表变更（已实施）

| 变更 | 类型 | 说明 |
|---|---|---|
| 新增 mapping_source | VARCHAR | llm / rule / manual，记录映射来源。 |
| 新增 review_status | VARCHAR | approved / pending / rejected，低置信度映射进审核。 |

综合题（is_composite=true）子题级知识点映射已承载：父题 `questions.sub_questions`
JSONB 字段关联（Phase 2A 实现时决定并落地）。

### 8.4 暂不建的表（未来计划）

以下表在 Phase 2D 之前不建：

| 表 | 推迟原因 |
|---|---|
| question_families | Family 定义未确定，建表会锁死模型 |
| question_similarity | Similarity 引擎未实现 |
| question_annotations（独立表） | 旧名不采用；新链使用 `semantic_annotation_runs`（Phase 2 planned） |

### 8.5 设计原则（已实施 vs 未来）

已实施：

| 原则 | 说明 |
|---|---|
| Annotation ≠ 事实 | LLM 输出的标注都带 source/confidence/version；新链落 semantic_annotation_runs |
| Structure Signature 存 L2 JSON | legacy；新链结构信息进入 Semantic IR/Compiler，不写回旧 L2 |

未来（Family/Similarity 引擎落地时生效）：

| 原则 | 说明 |
|---|---|
| Primary Family 唯一归属 | 每道题只有一个 Primary Family，用于统计报表 |
| Family Membership N:M | 一道题可以属于多个 Family，用于检索/分析 |
| Knowledge Point ≠ Family | 同知识点不同任务属于不同 Family |

---

### 8.6 旧数据回填与行号映射迁移策略（Phase 0 文档冻结，未实施）

1. 新链只处理新跑文档；历史文档默认继续以旧 questions/question_instances 查询。
2. `documents.native_markdown/ocr_markdown/llm_annotated_markdown` 不删除，标记为
   legacy 只读镜像。
3. 历史文档重跑时创建新 source version，并只清理未被人工审核的新链/旧链候选；
   已 approved/reviewed 的历史记录保留。
4. 旧 question 行号映射：
   - 历史 question 若只有 line_id、没有可回放的 source index，不允许伪造 raw_sources。
   - 重跑并 seal 后，通过 question_instances.source_version_id 指向新版本；
     旧 question 保留 legacy 状态和旧 line_id。
   - 如需审计旧行号，增加 `legacy_line_ref` 快照字段，不与新 Resolver line_ref
     混用。
5. 回填脚本必须是幂等 one-shot 工具并写入 LOG；禁止塞进生产 worker。

---

## 9. 一致性要求

DSD 必须与以下文档保持一致：

- PRD.md
- SAD.md
- ACS.md
- MIS.md
- PIPELINE.md

冲突时：

- 产品范围以 REQUIREMENTS_AND_SOLUTION.md 为准。
- 数据库结构以本文件为准。

---

## 10. 变更记录

### 2026-08-11

- `documents.processing_status` 枚举补充 `failed`，与后台任务失败状态一致。

### 2026-08-11 07:07:42

- 固化 V1 教训：`documents` 增加 L1 Native/OCR Markdown 字段。
- `question_images` 增加 `page_no/bbox/placement/source/figure_id`，用于无猜图、文档级去重和来源可追溯。

### 2026-08-11

- 版本升至 4.5：`question_images` 多对多语义说明（物理图存储去重 + 题图关联多对多 + 无证据广播抑制）。
- 新增 L1/L2 中间态说明（不落库，详见 T3_IMPLEMENTATION.md）。

### 2026-08-21

- 新增 §8 Phase 2A 设计冻结：questions 移除 year/school、新增 content_hash、occurrence_count 改派生；question_instances 新增 document_id FK（NOT NULL）+ 部分唯一索引（WHERE source_question_number IS NOT NULL）；question_knowledge 新增 mapping_source/review_status。
- 明确暂不建 question_families、question_similarity、独立 question_annotations 表。
- 冻结设计原则：Primary Family 唯一归属、KP ≠ Family、Annotation ≠ 事实、Structure Signature 存 L2 JSON。

### 2026-08-21

#### Phase 2A Step 1 实施

- questions 表：移除 year/school 列，新增 content_hash VARCHAR(64)。
- question_instances 表：新增 document_id UUID FK documents（nullable），部分唯一索引 ix_question_instances_doc_qno（WHERE document_id IS NOT NULL AND source_question_number IS NOT NULL）。
- question_knowledge 表：新增 mapping_source VARCHAR(20)、review_status VARCHAR(20) DEFAULT 'approved'。
- 索引变更：ix_questions_subject_grade_year → ix_questions_subject_grade（移除 year），新增 ix_questions_content_hash。
- Alembic migration：20260821_0003_phase2a_data_foundation.py。
- 版本升至 4.6。

### 2026-08-27（P0 文档状态修正）

- **§8 状态漂移修正**：标题/引言去掉「待实现/当前 DB 仍为旧结构」表述，改为
  「已实施 + 未来计划」；§8.1-8.3 标注已实施（migration 20260821_0003/0005、
  20260827_0001，`alembic current` 在 head）；§8.5 拆分为「已实施原则」与
  「未来 Family/Similarity 原则」。
- §4.5 两处过时说明同步修正：content_hash「当前可为 NULL」→「Step 5 已实现，
  可为 NULL（历史数据）」；「本步只加列」→「Step 5 已实现，20260821_0005 回填」。


### 2026-08-28 23:50:00

- 新增 questions.original_question_type VARCHAR(50)：保留 LLM 原始细粒度题型（cloze/grammar_fill/seven_to_five/essay/writing 等）。
- 新增 questions.section_id VARCHAR(100)：保留卷面 section/共享材料区标识。
- Alembic migration：20260828_0001_add_question_original_type_section.py。


### 2026-08-29 00:05:00

- questions.sub_questions JSONB 支持递归 sub_sub_questions，用于化学综合题 ⅠⅡⅢⅣ / ①②③④ 等多层子问。
- P0-3 实现：L2QuestionAnnotation/L2SubQuestion 递归结构、line_annotator 解析、content_slicer 切片、ingestion 序列化、前端递归渲染。


### 2026-08-29 00:15:00

- questions 新增 answer_structure JSONB：保存结构化答案（可包含 accepted_answers/range 等），原始答案仍保留在 answer TEXT。
- Alembic migration：20260829_0001_add_question_answer_structure.py。


### 2026-08-29 00:35:00

- questions 新增 word_bank JSONB：词库独立存储，单题与多题词库路径均支持。
- Alembic migration：20260829_0002_add_question_word_bank.py。
- P0-1 统计补强：入库优先使用 original_question_type 建立细粒度 question_type_id。

### 2026-08-29 12:30:00

- P0-2：essay/writing 作为原始细粒度 code 入库，question_type_id 可创建 essay/writing；无 schema 变更。
- P1-3：填空位标记增加普通数字上下文保护，英语正文数字误标风险收敛。
- P1-4：七选五 A-G 标签完整性进入锚点校验，缺失时 retry。
- P2-2：前端展示层增强，不涉及数据 schema。

### 2026-08-29 15:30:00

- P1-2：question_images 新增 sub_question_qno VARCHAR(100)，用于答案图子题粒度绑定；Alembic migration 20260829_0003。
- P0-5：化学式文本标准化，无 schema 变更。

### 2026-09-03 23:15:44

- 新增 `4.24 question_candidates`：Admission Gate review/reject 候选题目持久化表。
- 同步 `question_candidates` 与 subjects/question_types/documents 关系及索引。
- 该表已由 Admission Gate/Ingestion 代码使用；本次仅补齐 DSD 文档缺口。

### 2026-09-03 23:57:03

- Phase 0 文档冻结：删除“L1/L2 不落库”旧结论，改为 sealed Source Version 与
  Annotation/Resolver/IR 按阶段可审计落库。
- `documents.native_markdown/ocr_markdown/llm_annotated_markdown` 标记 legacy
  只读兼容镜像。
- 新增 Phase 1-3 planned 表结构：
  `document_source_versions`、`document_source_lines`、
  `document_source_lines_image_refs`、`document_active_sources`、
  `document_source_selection_events`、`semantic_annotation_runs`、
  `semantic_resolver_runs`、`semantic_ir_snapshots`。
- question_instances/question_candidates 增加 planned provenance 字段与
  admission_status 说明。
- 新增 §8.6 旧数据回填与行号映射迁移策略；本轮未创建 Alembic migration，
  所有 planned 表以 `####` 标注，避免与当前代码 metadata 混淆。

### 2026-09-04 00:16:28

- 新增 4.33 document_source_tables、4.34 document_source_table_cells、
  4.35 document_source_fragments，补足 table_cell/fragment 可回放 source index。
- integrity_hash 明确定义覆盖 body/lines/images/tables/cells/fragments。
- 统一 question_candidates 状态模型：approved→questions、candidate→本表、
  rejected→删除候选并审计；gate_decision 标 legacy，admission_status 只存
  candidate。
- questions.status 新链口径为 approved/rejected；legacy reviewing 仅旧记录。
- 本轮仍未创建 Alembic migration。


### 2026-09-05 09:48:44

- 新增 `4.36 worker_instances`：worker 登记、token hash、heartbeat、状态。
- `background_tasks.worker_id` 与 `answer_extraction_retries.worker_id/claimed_at`
  记录任务/重试原子 claim 归属。
- Supervisor 将失效 worker 持有的 document task 标记 interrupted（人工 retry），
  answer retry 重置 pending；不自动 requeue。
- 文档对应 Alembic migration：`20260905_0001_add_worker_safety_tables.py`。
