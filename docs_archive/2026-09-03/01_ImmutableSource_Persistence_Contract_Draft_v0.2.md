# Immutable Source Persistence Contract Draft

Version: DRAFT-0.2
Status: 草案，供评审；未实施
Date: 2026-09-03
Supersedes: `01_ImmutableSource_Persistence_Contract_Draft.md` v0.1
目的：定义文档入库语义管线中不可变源内容的持久化边界、对象模型、引用方式与
完整性约束。

## 1. v0.2 修订依据

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
  `02_SemanticMetadata_Annotation_Contract_Draft_v0.2.md`。
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
  ├── source index (lines/images)
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

## 8. Source version 持久化建议

表名与字段为设计建议，最终由 DSD + Alembic 评审后确定。

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

## 9. 不可变规则

### IS-1 写后 seal

完成完整性检查后一次性写入 source version + line index 并 seal。失败不得留下可供
下游读取的半成品。

### IS-2 无原地修正

不提供修改 sealed source 的 update 方法。修正必须创建新的 source version。

### IS-3 后处理纯函数

行拆分、规范化、表选项拆行等必须在 seal 前由纯函数产出新对象。已有 version 不得
被原地修改。

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
                        evidence + confidence + body_text))
```

`body_hash` 用于判断正文是否变化；`integrity_hash` 用于判断完整证据链是否变化。
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
- DSD §7 “L1/L2 不落库”的旧说明与本契约冲突，批准时应同步修订 DSD。
- 任何表/字段变更必须走 Alembic migration。

## 17. 验收标准

1. 两次相同输入产生相同 sealed version hash。
2. 修改一行会改变 `integrity_hash`。
3. Repository 无法对 sealed source 执行 update/delete。
4. 重跑后旧 active source 仍可读取，旧 annotation 仍可按原 source_version_id 回放。
5. 缺失 raw_sources/evidence/bbox 的 source 不能作为全证据。
6. line_ref 只出现在程序 resolved 结果中，不出现在 LLM Semantic Annotation JSON。

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
