# Immutable Source Persistence Contract Draft

Version: DRAFT-0.3
Status: 开发指引契约，供评审；未实施
Date: 2026-09-04
Supersedes: `01_ImmutableSource_Persistence_Contract_Draft_v0.2.md`
目的：定义文档入库语义管线中不可变源内容的持久化边界、对象模型、引用方式与
完整性约束。

## 0. v0.3 开发指引要点

本文件从“供讨论的契约草案”升级为“Immutable Source 落库与回放契约”。总纲见
`00_SemanticPipeline_Development_Guide_v0.3.md`。

v0.3 重点解决旧管线中以下问题：

1. 旧 `documents.native_markdown/ocr_markdown` 只保存拼接文本，行级证据不可审计。
2. 旧 `llm_annotated_markdown` 保存的 L2 行号没有可核验的 L1 source index 可回放。
3. 旧重跑会清理/覆盖未审核记录，无法证明新结果与旧结果使用了同一或不同 source。
4. 旧 `_save_l1_snapshot()` 只保存少量字段，raw_sources/evidence/confidence 会丢。

因此本文件要求：所有后续阶段只消费 sealed source version；任何无法重建 line
index 的旧正文只能作为 legacy 诊断，不能作为新 Resolver 的证据。

## 1. v0.2 修订依据

> 历史版本说明保留。v0.3 不推翻 v0.2 结论，只补充开发实现契约。

本轮核心结论：

> LLM 负责理解语义，程序负责确定事实。

本契约因此只负责“原始事实如何不可变保存、程序如何按证据定位”，不负责定义
LLM 输出格式。行号、line_ref、source span 是程序定位结果，不是 LLM 语义输出。

## 2. 背景

当前 `documents.native_markdown` 与 `documents.ocr_markdown` 只保存正文拼接文本，
行级结构、来源、bbox、raw_sources、selected_source、evidence、confidence 丢失；
`_save_l1_snapshot()` 也只保留少量字段。新语义管线需要：

1. 每个文档的解析结果和 canonical L1 一旦 seal 后不可修改。
2. 保留足够的正文、行索引和 provenance，供 Source Resolver 做确定性定位。
3. 后续 Resolver、IR、Compiler、Gate 只能引用已 seal source version。
4. 任何重跑、重标、修正都产生新的 source version，而不是覆盖旧版本。

## 3. 术语

| 术语 | 含义 |
|---|---|
| Original artifact | 用户上传的原始 PDF/DOCX，保存于对象存储 |
| Raw source | 单一提取器产生的 L1，如 native/ppsv3/docx |
| Canonical source | 多源裁决或主路径合并后用于下游的 L1 |
| Source version | 一次不可变持久化的完整 raw/canonical 结果 |
| Source index | source version 下用于程序定位的正文/行/图片索引 |
| line_ref | 单一 source version 内程序使用的稳定行引用 |
| Semantic reference | LLM 给出的 role/label/marker 引用；不是本契约的最终事实 |
| Resolved span | Source Resolver 输出的真实 source 范围 |
| Active source | 当前文档解析结果采用的 source version |

## 4. 关键边界

```text
LLM Semantic Metadata Annotation
  -> semantic labels + role/marker references
  -> 不使用 line_ref

Source Resolver
  -> 在 sealed source 中解析 semantic reference
  -> 输出 resolved span / line_ref

Semantic Question IR / Compiler / Gate
  -> 消费 resolved span
```

因此本契约中的 line_ref 是“程序定位后的证据”，不是“LLM 标注语言”。

## 5. 范围与非范围

范围：

- raw native L1、raw OCR/PP L1、raw DOCX L1、canonical L1 的持久化。
- source version、line_ref、正文、页面、bbox、provider、raw_sources、证据字段。
- hash、完整性校验、seal、版本选择与迁移兼容。

非范围：

- Semantic Metadata Annotation 的字段，见
  `02_SemanticMetadata_Annotation_Contract_Draft_v0.3.md`。
- Source Resolver 如何解析 semantic reference。
- Semantic Question IR 与 Compiler 的字段。
- Gate 与 Admission 规则。

## 6. 持久化对象图

```text
documents
  └── original artifact (MinIO object)
        ├── raw native source
        ├── raw OCR/PP source
        └── raw DOCX source

canonical source
  ├── body_text
  ├── body_hash
  ├── source index
  │   ├── lines
  │   ├── images
  │   ├── tables
  │   ├── table cells
  │   └── fragments
  └── integrity_hash

document_active_sources
  └── role -> sealed source version id
```

同一文档可同时存在多个 sealed source version。“当前正文”只能通过
`document_active_sources` 指向的版本取得。

## 7. Artifact 类型

| artifact_kind | role | 来源 | 是否 canonical |
|---|---|---|---|
| original_binary | original | 上传文件 | 否 |
| raw_l1 | native | PyMuPDF 文本层 | 否 |
| raw_l1 | ocr_ppsv3 | PP-StructureV3/PaddleOCR-VL | 否 |
| raw_l1 | docx | DOCX 原生结构 | 否 |
| canonical_l1 | canonical | 代码仲裁/主路径合并 | 是 |

## 8. Source version 持久化结构

表名与字段已同步到 DSD §7/§4.25-4.35（Phase 1-3 planned）。在 Alembic migration
评审通过前不创建表，也不得自行改名。

### 8.1 document_source_versions

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK documents |
| run_id | UUID | 产生该 version 的 pipeline run/attempt |
| artifact_kind | VARCHAR | original_binary / raw_l1 / canonical_l1 |
| role | VARCHAR | native / ocr_ppsv3 / docx / canonical |
| provider | VARCHAR | native / ppsv3 / docx |
| body_text | TEXT | 确定性拼接的正文 |
| body_hash | CHAR(64) | SHA256(body_text, normalized) |
| integrity_hash | CHAR(64) | SHA256(正文 + source index + provenance) |
| page_count | INTEGER | 有内容的页数 |
| line_count | INTEGER | line index 行数 |
| total_pages | INTEGER | 文档总页数 |
| text_coverage | NUMERIC | Native/OCR 覆盖率 |
| source_meta | JSONB | 提取配置、页码范围、OCR 任务证据 |
| parent_version_id | UUID NULL | 修正/派生来源 |
| status | VARCHAR | draft / sealed / invalid |
| created_at | TIMESTAMPTZ | 创建时间 |

约束：

- `status=sealed` 后禁止任何 UPDATE。
- `body_text` 与 line index 必须一致；不一致视为写入失败。

### 8.2 document_source_lines

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK document_source_versions |
| line_ref | VARCHAR | 如 `P1L001` |
| seq | INTEGER | 全局顺序，1-based |
| page_no | INTEGER | 1-based |
| line_no_in_page | INTEGER | 页内顺序 |
| text | TEXT | 该行正文 |
| block_type | VARCHAR | text / formula / table / figure_placeholder |
| bbox | JSONB NULL | page bbox |
| source | VARCHAR | line 的选定来源 |
| raw_sources | JSONB | provider 文本、native_line_id 等 |
| selected_source | VARCHAR | 最终来源 |
| evidence | TEXT | 选定证据 |
| confidence | NUMERIC | 行级置信度 |
| line_hash | CHAR(64) | SHA256(text + raw_sources + evidence 等) |

约束：

- `source_version_id + line_ref` 唯一。
- `seq` 从 1 开始、连续。
- 同一 source version 内，line_ref 只能引用本 version 的 index。
- line_ref 只作为程序定位和审计证据，不作为 LLM 输出的语义引用。

### 8.3 document_source_lines_image_refs

| Field | Type | Note |
|---|---|---|
| image_id | VARCHAR | L1Image.image_id |
| source_version_id | UUID | 所属 source version |
| page_no | INTEGER | 必须存在 |
| bbox | JSONB | 必须存在 |
| placement | VARCHAR | stem / options / explanation / answer_area / standalone |
| source | VARCHAR | native / ppsv3 / ... |
| figure_id | VARCHAR | 文档级去重 ID |

### 8.4 document_active_sources

| Field | Type | Note |
|---|---|---|
| document_id | UUID | FK documents，PK |
| role | VARCHAR | native / ocr_ppsv3 / canonical |
| source_version_id | UUID | 指向 sealed version |
| selected_at | TIMESTAMPTZ | |
| selection_reason | TEXT NULL | 自动/人工/回滚原因 |

### 8.5 document_source_tables

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK document_source_versions |
| table_id | VARCHAR | version 内唯一，如 T1 |
| page_no | INTEGER | 必须存在 |
| bbox | JSONB NULL | 表格页内 bbox |
| row_count | INTEGER | 行数 |
| column_count | INTEGER | 列数 |
| table_hash | CHAR(64) | SHA256(cells + layout metadata) |
| created_at | TIMESTAMPTZ | |

约束：`source_version_id + table_id` 唯一。

### 8.6 document_source_table_cells

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK document_source_versions |
| table_id | VARCHAR | FK document_source_tables.table_id |
| row_index | INTEGER | 0-based 表格逻辑行 |
| column_index | INTEGER | 0-based 表格逻辑列 |
| row_span | INTEGER | 默认 1 |
| column_span | INTEGER | 默认 1 |
| text | TEXT | 单元格正文 |
| line_refs | JSONB | 单元格在 source line index 中的关联行 |
| raw_sources | JSONB | provider/canonical 证据 |
| selected_source | VARCHAR | 最终来源 |
| evidence | TEXT | 选择/合并证据 |
| confidence | NUMERIC | 单元格置信度 |
| cell_hash | CHAR(64) | SHA256(text + raw_sources + spans) |
| created_at | TIMESTAMPTZ | |

约束：

- `source_version_id + table_id + row_index + column_index` 唯一。
- 每个 Resolver `cell_ref` 必须能按 `{table_id,row,column}` 唯一回放。
- 单元格文本不能只由整行拼接重建；有合并单元格时必须保留 span。

### 8.7 document_source_fragments

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK document_source_versions |
| fragment_id | VARCHAR | version 内唯一，如 F-opt-A1 |
| kind | VARCHAR | inline_option / blank_fragment / answer_fragment / instruction_marker / text_fragment |
| line_ref | VARCHAR | 关联 source line，可空（如表单内 fragment） |
| start_offset | INTEGER NULL | line 内 0-based 字符起点 |
| end_offset | INTEGER NULL | line 内字符终点（exclusive） |
| text | TEXT | 精确 fragment 正文 |
| text_hash | CHAR(64) | SHA256(text + source refs) |
| source | VARCHAR | 来源 provider |
| evidence | TEXT | 如何从 line/table cell 生成 |
| created_at | TIMESTAMPTZ | |

约束：

- `source_version_id + fragment_id` 唯一。
- 同一 source version 内，fragment 不允许跨 version 引用。
- Resolver 的 `fragment_ref`/`line_character` 只能引用已 seal index。
- 单行多选项、同行多题答案必须落到独立 fragment，不允许只靠 Resolver 猜测字符范围。

## 9. 不可变规则

### IS-1 写后 seal

完成完整性检查后一次性写入 source version + line index 并 seal。失败不得留下可供
下游读取的半成品。

### IS-2 无原地修正

不提供修改 sealed source 的 update 方法。修正必须创建新的 source version。

### IS-3 后处理纯函数

行拆分、规范化、表格 cell 拆分、fragment 生成等必须在 seal 前由纯函数产出新对象。
已有 version 不得被原地修改；Resolver 不得在 seal 后创建新的 cell/fragment 并回写。

### IS-4 正文可重算

`body_text` 必须能从 line index 按 `seq` 以 `\n` 确定性重建；读取时重算并比对
`body_hash`，不一致即拒绝使用。

### IS-5 line_ref 不跨 version

所有 line_ref 都解析到同一 `source_version_id`。Resolver 不能混合不同 raw version
的 line_ref 作为 canonical resolved span。

### IS-6 provenance 不丢失

canonical line 保留 `raw_sources/selected_source/evidence/confidence`。即使最终来源
为 native 或 ppsv3，也不可只保存拼接后的 text。

### IS-7 图片不猜

图片索引必须带 page/bbox/placement/source/figure_id。缺失这些字段的图片不得以
“已定位图片”身份参与 compiler/gate。

### IS-8 最终内容可追溯

最终题目对象或 Semantic IR 必须携带 `source_version_id` 与 resolved source span。
若缺少该证据，Gate 不得视为 evidence-complete。

## 10. Semantic reference 的持久化边界

Semantic reference 属于 Annotation，不写入本 source contract。原因：

- reference 是 LLM 对源文本的“引用建议”；
- reference 可能模糊或偏移；
- 只有 Source Resolver 的 resolved span 才是程序事实。

如需加速 Resolver，可在 Source Index 上提供只读检索视图，但不得把 LLM 建议的
reference 当作不可变源正文的一部分。

## 11. Canonical 规则

- Canonical source 在合并多源后产生，同一 version 必须记录
  `source_meta.policy_version`。
- 新策略只影响后续 run，不重写历史 run。
- 被过滤的页面应明确写 page_range 与 reason。
- `text_coverage` 等统计是 version 属性，不是文档全局事实。

## 12. Hash 与完整性

建议：

```text
body_hash =
  SHA256("\n".join(line.text for line in lines ordered by seq))

integrity_hash =
  SHA256(canonical_json(lines fields + raw_sources + selected_source +
                        evidence + confidence + images + tables + table_cells +
                        fragments + body_text))
```

`body_hash` 用于判断正文是否变化；`integrity_hash` 用于判断完整证据链是否变化，
必须覆盖 source index 中的 lines/images/tables/table_cells/fragments。
任何 mismatch 的 version 标记为 `invalid`，禁止被 active pointer 使用。

## 13. Provenance 字段约束

`raw_sources` 使用稳定 key：

| key | 含义 |
|---|---|
| native | native line text |
| ppsv3 | PP/OCR line text |
| docx | DOCX 提取文本 |
| native_line_id | canonical 行在 native raw source 中的 line_ref |

`selected_source` 必须是可解释 provider；`evidence` 记录为何选择它；`confidence`
只描述该行可信度，不代替答案正确性。

## 14. 生命周期

```text
original file
  -> raw source creation
  -> raw source seal
  -> canonical merge/seal
  -> active source selected
  -> semantic annotation on canonical source
  -> Source Resolver maps semantic reference to line_ref/span
  -> IR / compiler / gate
```

## 15. 重试语义

1. 每次 worker/人工重试生成新 `run_id`。
2. 成功阶段写入新的 sealed version。
3. 失败阶段只更新 document/task 状态，不 seal 半成品。
4. 对象存储写入后、DB seal 前失败时，做孤儿 object 清理或记录待清理。
5. Annotation 必须记录实际使用的 `source_version_id`，不能假设与 active 一致。

## 16. 当前字段兼容

迁移期间：

- `documents.native_markdown` / `ocr_markdown` 保留为只读兼容镜像。
- 读取旧字段的代码应迁移为从 active sealed source 读取。
- 历史文档可回填 legacy source version；无 raw_sources 的旧行只用于诊断。
- DSD §7 已同步修订：L1/L2 不再标“不落库”，raw/canonical source 与
  Annotation/Resolver/IR 中间结果按可审计性落库。
- 任何表/字段变更必须走 Alembic migration。

## 17. 验收标准

1. 两次相同输入产生相同 sealed version hash。
2. 修改一行会改变 `integrity_hash`。
3. Repository 无法对 sealed source 执行 update/delete。
4. 重跑后旧 active source 仍可读取，旧 annotation 仍可按原 source_version_id 回放。
5. 缺失 raw_sources/evidence/bbox 的 source 不能作为全证据。
6. line_ref 只出现在程序 resolved 结果中，不出现在 LLM Semantic Annotation JSON。
7. Resolver 使用的 table_id/row/column、fragment_id、start/end offset 必须能通过
   sealed source index 精确回放。
8. 修改任一 table cell/fragment 文本会改变 integrity_hash。

## 18. 已定实施决策

1. 在个人系统规模下，raw source 与 canonical source 都写入同一 line index；不再
   区分“只有 canonical 才落库”。历史 raw body 必须能重建，否则 provenance 审计不完整。
2. 所有 sealed source version 默认保留，不做静默清理；后续若确需归档，必须由人工
   显式执行并记录归档原因。
3. `body_text` 存 PostgreSQL TEXT；line index 存 PostgreSQL JSONB/relation。个人系统
   规模不引入对象存储存正文。
4. original PDF/DOCX 增加原始文件 SHA256；存于 original source version 的
   `source_meta.original_sha256`。
5. active source 指针允许随重跑变化；每次选择写入 append-only
   `document_source_selection_events`，包含旧/新 version、操作人、原因和 run_id。
6. Source Resolver 首版不做持久化 semantic reference 倒排索引；在 sealed body_text 上按
   normalized text 检索。文档规模达到索引收益之前，不增加新存储组件。

## 19. 下一步开发实现指引

### 19.1 Repository 边界

建议以 Repository 作为 sealed source 的唯一写入口，禁止 worker/processor 直接
UPDATE/INSERT source 表。方法边界如下：

| Method | 行为 | 是否可更新 sealed |
|---|---|---|
| `create_source_version(document, artifact_kind, role, meta)` | 创建 draft version | 否 |
| `replace_source_index(version_id, lines, images)` | seal 前纯替换 draft index | 否 |
| `seal_source_version(version_id, body_hash, integrity_hash)` | 校验后 seal | 不允许再写 |
| `get_sealed_source(version_id)` | 只读取回 source + index | 否 |
| `set_active_source(document_id, role, version_id, reason, run_id)` | 写 active pointer + selection event | 否 |
| `list_source_versions(document_id, artifact_kind, role)` | 审计查询 | 否 |

约束：

- `replace_source_index` 只允许 status=draft。
- `seal_source_version` 必须在同一事务内完成完整性校验与状态更新。
- sealed 行不能执行 UPDATE/DELETE；ORM 层应抛错而不是静默忽略。
- 删除 source version 需要显式人工接口和归档理由，普通代码不提供删除。

### 19.2 Seal 事务顺序

```text
1. 纯函数产出 L1 objects（raw/canonical），不修改内存原始对象
2. 计算 seq/line_ref/page_no/line_no_in_page/line_hash
3. 由 line index 重建 body_text，计算 body_hash
4. 计算含 raw_sources/selected_source/evidence/confidence 的 integrity_hash
5. 单事务写入 source version + line index + image refs
6. 校验成功后 seal
7. 记录 active source / selection event
8. 事务失败时整体回滚，不留半成品
```

### 19.3 Image 写入门

- image ref 缺少 page_no、bbox、placement、source 任一字段时不得写入。
- `figure_id` 必须在 source version 内去重。
- 同一 image 可以出现在多个 line refs 的上下文中，但必须带明确 role owner；
  禁止整页图片和跨题广播。

### 19.4 旧字段兼容与回填

1. `documents.native_markdown/ocr_markdown/llm_annotated_markdown` 保留字段，
   新代码停止写入，只作为 legacy 镜像。
2. 历史文档回填时创建 `legacy_source_version`；无法提供 raw_sources 的行只能在
   `source_meta.legacy=true` 下存在。
3. 回填不得修改旧 question 的 line_id，只能建立 source version 到 question
   line_id 的可追溯映射。
4. DSD §7 已修订；后续任何再改回“L1/L2 不落库”的提议都必须重新走评审。

### 19.5 回归防护测试

实现时应覆盖：

- 两次相同输入 seal 后 body_hash/integrity_hash 相同。
- 修改一行文本后 integrity_hash 改变。
- sealed version 的 update/delete 被 Repository 拒绝。
- active pointer 切换后旧 version 仍可读取。
- 重跑不会覆盖旧 sealed source。
- line index 无法按 seq 重建 body_text 时 seal 失败。
- legacy markdown 只读镜像不会被新链误作证据。
