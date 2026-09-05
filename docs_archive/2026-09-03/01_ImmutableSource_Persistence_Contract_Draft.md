# Immutable Source Persistence Contract Draft

Version: DRAFT-0.1
Status: 草案，供评审；未实施
Date: 2026-09-03
目的：定义文档入库语义管线中不可变源内容的持久化边界、对象模型、引用方式与
完整性约束，作为后续 DSD/Alembic/Repository 设计的前置契约。

## 1. 背景与目标

当前 `documents.native_markdown` 与 `documents.ocr_markdown` 只保存正文拼接文本，
行级结构、来源、bbox、raw_sources、selected_source、evidence、confidence 丢失；
`_save_l1_snapshot()` 也只保留少量字段。旧 L2 以 `line_id` 数组表达题目，下游无法
证明切片来自哪一份不可变源、由哪个版本解析、修正后是否仍可复现。

本契约要求：

1. 每个文档的原始解析结果和 canonical L1 一旦 seal 后不可修改。
2. 行级 source index 与正文一起持久化，保留足够 provenance。
3. 后续 Annotation、Resolver、IR、Compiler、Gate 只能引用已 seal source version，
   不能以新文本或内存中的可变 L1 作为事实源。
4. 任何重跑、重标、修正都产生新的 source version，而不是覆盖旧版本。

## 2. 术语

| 术语 | 含义 |
|---|---|
| Original artifact | 用户上传的原始 PDF/DOCX，保存于对象存储，`documents.object_key` 指向它 |
| Raw source | 单一提取器产生的 L1，如 native/ppsv3/docx，按行表达 |
| Canonical source | 多源裁决或主路径合并后用于下游的 L1 |
| Source version | 一次不可变持久化的 raw/canonical 完整结果，包含正文与行索引 |
| Source index | source version 下的行/图片索引，提供稳定 line_ref |
| line_ref | 单一 source version 内唯一的行引用，如 `P1L001`/`N1L001` |
| Active source | 当前文档解析结果采用的 source version，属于可变指针 |
| Run / attempt | 一次 pipeline 执行或一次人工重试批次 |
| Source span | 一行或多行组成的有序引用集合，下游语义对象使用它 |

## 3. 范围与非范围

范围：

- raw native L1、raw OCR/PP L1、raw DOCX L1、canonical L1 的持久化。
- line_ref、正文、页面、bbox、provider、raw_sources、证据字段。
- hash、完整性校验、seal、版本选择与迁移兼容。

非范围：

- LLM Semantic Metadata Annotation 的结构，见
  `02_SemanticMetadata_Annotation_Contract_Draft.md`。
- Source Resolver 的解析算法。
- Semantic Question IR 与 Compiler 的字段。
- Gate 的规则。
- 最终 `questions` / `question_instances` 表。

## 4. 持久化对象图

```text
documents
  └── original artifact (MinIO object)
        ├── raw native source
        ├── raw OCR/PP source
        └── raw DOCX source

canonical source
  ├── body_text
  ├── body_hash
  ├── source index (lines)
  ├── image index
  └── integrity_hash

document_active_sources
  └── role -> sealed source version id
```

同一文档可同时存在多个 raw source version 和多个 canonical source version。
“当前正文”只能是 `document_active_sources` 指向的版本，不能是散落历史记录。

## 5. Artifact 类型

建议使用 role/artifact_kind 表达，不用松散文件名字段：

| artifact_kind | role | 来源 | 是否 canonical |
|---|---|---|---|
| original_binary | original | 上传文件 | 否 |
| raw_l1 | native | PyMuPDF 文本层 | 否 |
| raw_l1 | ocr_ppsv3 | PP-StructureV3/PaddleOCR-VL | 否 |
| raw_l1 | docx | DOCX 原生结构 | 否 |
| canonical_l1 | canonical | 代码仲裁/主路径合并 | 是 |

若未来加入更多 OCR provider，按 `provider` 与 `role` 扩展，不修改历史 artifact。

## 6. Source version 持久化建议

以下表名与字段为设计建议，最终由 DSD + Alembic 评审后确定。

### 6.1 document_source_versions

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK documents |
| run_id | UUID | 产生该 version 的 pipeline run/attempt |
| artifact_kind | VARCHAR | original_binary / raw_l1 / canonical_l1 |
| role | VARCHAR | native / ocr_ppsv3 / docx / canonical |
| provider | VARCHAR | native / ppsv3 / docx |
| body_text | TEXT | 确定性拼接的正文，不依赖下游展示 |
| body_hash | CHAR(64) | SHA256(body_text, normalized) |
| integrity_hash | CHAR(64) | SHA256(正文 + line index + provenance) |
| page_count | INTEGER | 有内容的页数 |
| line_count | INTEGER | line index 行数 |
| total_pages | INTEGER | 文档总页数 |
| text_coverage | NUMERIC | Native/OCR 覆盖率等 |
| source_meta | JSONB | 提取配置、页码范围、OCR 任务证据 |
| parent_version_id | UUID NULL | 同一文档修正/派生自哪个版本 |
| status | VARCHAR | draft / sealed / invalid |
| created_at | TIMESTAMPTZ | 创建时间 |

约束：

- `status=sealed` 后禁止任何 UPDATE。
- 同一 `document_id + role` 允许存在多个 sealed version，但每次 run 至少可独立重放。
- `body_text` 与 `line_count` 必须一致；不一致视为写入失败。

### 6.2 document_source_lines

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
- `seq` 必须从 1 开始、连续，且与行顺序一致。
- `line_ref` 只能引用本 version 的 index，不能引用其它 version。
- 对 canonical source，`line_ref` 保持现有 `P#L###` 规则，避免重写旧切片协议。
- 行 `text` 为 source 事实；展示规范化只能在编译/显示层发生，不得写回本表。

### 6.3 document_source_lines_image_refs

可并入 line 表或单独保存。每条配图引用至少保留：

| Field | Type | Note |
|---|---|---|
| image_id | VARCHAR | L1Image.image_id |
| source_version_id | UUID | 所属 source version |
| page_no | INTEGER | 必须存在 |
| bbox | JSONB | 必须存在 |
| placement | VARCHAR | stem / options / explanation / answer_area / standalone |
| source | VARCHAR | native / ppsv3 / ... |
| figure_id | VARCHAR | 文档级去重 ID |
| anchor_ref | JSONB NULL | 与正文 line_ref 的关系 |

### 6.4 document_active_sources

| Field | Type | Note |
|---|---|---|
| document_id | UUID | FK documents，PK |
| role | VARCHAR | raw_native / raw_ocr / canonical |
| source_version_id | UUID | 指向 sealed version |
| selected_at | TIMESTAMPTZ | |
| selection_reason | TEXT NULL | 人工/自动/回滚原因 |

说明：

- 只有该表可以随时间变化。
- 历史 sealed version 不因 active 指针变化而失效。
- `canonical` active version 一旦被 Annotation 使用，应在 annotation 记录其 id。

## 7. 不可变规则

### DSA-1 写后 seal

完成完整性检查后一次性写入 `source_version + line index` 并 seal。任何写入失败不得
留下可供下游读取的半成品。

### DSA-2 无原地修正

Repository/Service 不提供修改 sealed source 的 update 方法。修正必须创建新的
source version，并设置 `parent_version_id`。

### DSA-3 后处理纯函数

行拆分、公式规范化、表选项拆行等必须在 seal 前由纯函数产出新对象。已有 version
不得被后处理函数原地修改。如现有 `L1Document` 的 `lines` 字段被修改，应先复制为
新的 dataclass/artifact。

### DSA-4 正文可重算

`body_text` 必须能从 line index 按 `seq` 以 `\n` 确定性重建；读取时重算并比对
`body_hash`，不一致即拒绝使用并记录结构化错误。

### DSA-5 source index 只属于自身 version

所有 line_ref 都解析到同一 `source_version_id`。Annotation 不能混合不同 raw version
的 line_ref 作为 canonical 切片输入。

### DSA-6 原文证据不丢失

canonical line 保留 `raw_sources/selected_source/evidence/confidence`。即使该行最终
来源为 native 或 ppsv3，也不可在持久化时只保存拼接后的 text。

### DSA-7 图片不猜

图片索引必须带 page/bbox/placement/source/figure_id。缺失这些字段的行不得以“已定位
图片”身份参与 compiler/gate。

### DSA-8 最终内容可追溯

最终题目对象或其 IR 必须携带 `source_version_id` 与对应的 line_ref 集合。若最终字段
缺少该引用，Gate 不得视为 evidence-complete。

## 8. Canonical 规则

- Canonical source 在合并多源后产生，合并策略可变化，但同一 version 必须记录
  `source_meta.policy_version`。
- 新 strategy 只影响后续 run，不重写历史 run。
- 被 scanner/OCR 过滤掉页面的版本应明确写 `page_range` 与 reason；不得用“无此页”
  静默替代原始完整文档。
- `text_coverage` 等统计是 version 属性，不是文档全局事实。

## 9. Hash 与完整性

建议：

```text
body_hash =
  SHA256("\n".join(line.text for line in lines ordered by seq))

integrity_hash =
  SHA256(canonical_json(lines fields + raw_sources + selected_source +
                        evidence + confidence + body_text))
```

`body_hash` 用于判断正文是否变化；`integrity_hash` 用于判断完整证据链是否变化。
读取 repository 时必须校验两个 hash。任何 mismatch 的 version 标记为 `invalid`，
禁止被 active pointer 使用。

## 10. Provenance 字段约束

`raw_sources` 使用稳定 key：

| key | 含义 |
|---|---|
| native | native line text |
| ppsv3 | PP/OCR line text |
| docx | DOCX 提取文本 |
| native_line_id | canonical 行在 native raw source 中的 line_ref |

`selected_source` 必须是 `source / raw_sources` 中可解释的 provider；`evidence` 记录
为何选择它；`confidence` 只描述该行可信度，不代替答案正确性。

## 11. 生命周期

```text
original file
  -> raw source creation
  -> raw source seal
  -> canonical merge/seal
  -> active source selected
  -> annotation reads active canonical source
  -> resolver/IR/compiler/gate read source version + annotation
```

若 Annotation、Resolver 或 Gate 需要新的 source view，先创建 derived annotation
artifact，不改 source version。

## 12. 重试语义

1. 每次 worker/人工重试生成新 `run_id`。
2. 成功阶段写入新的 raw/canonical sealed version。
3. 失败阶段只更新 document/task 状态，不 seal 半成品，不覆盖历史。
4. 若失败发生在对象存储写入之后、DB seal 之前，做孤儿 object 清理或记录待清理，
   但不得被 active pointer 使用。
5. 同一 `run_id` 的后续 annotation 必须记录实际使用的 `source_version_id`，不能假设
   与 document.active 一致。

## 13. 当前字段兼容

迁移期间：

- `documents.native_markdown` / `ocr_markdown` 保留为只读兼容镜像，不再作为新语义
  管线权威源。
- `answer_retry_worker` 等读取旧字段的代码应迁移为从 active sealed source 读取。
- 已入库历史文档可回填创建 legacy source version；无 raw_sources 的旧行标记
  `legacy=true`，只用于诊断，不进入新 semantic Gate 的 evidence-complete 路径。
- DSD §7 “L1/L2 不落库”的旧说明与本契约冲突，批准本契约时应同步修订 DSD。
- 任何表/字段变更必须走 Alembic migration。

## 14. 验收标准

契约固化前应验证：

1. 两次相同输入产生相同 sealed version hash。
2. 修改一行会改变 `integrity_hash`，且不会误改 `body_hash` 之外的表结构。
3. Repository 无法对 sealed source 执行 update/delete。
4. 重跑后旧 active source 仍可读取，旧 annotation 仍能按原 source_version_id 回放。
5. 缺失 raw_sources/evidence/bbox 的 source 不能被 semantic gate 判为全证据。
6. 文件正文、DB body_text、line index 三方一致性校验有明确失败态。

## 15. 待评审问题

1. source version 数量增长后的清理与保留策略：是否保留全部 run，还是只保留
   failed 诊断 + 最后 N 个成功 version。
2. raw line 是否也必须建 `document_source_lines`，还是可只存 raw body + 原始 JSONL。
3. `body_text` 是否存 DB，还是对象存储 + DB 存 line index；当前个人系统规模优先
   建议 DB TEXT/JSONB。
4. original PDF/DOCX 是否需要再增加文件级 SHA256；现有 object_key 是否足够。
5. active source 指针是否需要版本化，以便人工回滚审计。
6. 图片二进制是否作为 source version 的一部分原子提交，还是继续独立对象存储事务。
