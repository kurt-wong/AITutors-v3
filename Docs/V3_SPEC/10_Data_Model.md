# AI Tutor V3 — 数据模型：全新库 schema、实体关系与 Admission 事务

Version: v1.2.2（Baseline—Frozen，2026-09-05；v1.2.1 锚点 errata；v1.2.2 BUG-011 Scope Freeze errata，source_figures 语义/唯一约束/IS-7 写入门）
Status: V3 收敛基线（10 分册）— 已落实 10 二轮审查 4 项冻结前修订 + v1.2.1 锚点 errata + v1.2.2 BUG-011 Scope Freeze errata，冻结（与 20/30/40/50 对齐）
Date: 2026-09-05
Supersedes: `Docs/V3_DATA_MODEL.md`（起草输入）;上位约束 `00_Master_Spec.md`（不可修改）;
字段权威参考 `docs_archive/2026-09-03/01_ImmutableSource_*_v0.3.md`、
`03_SourceResolver_SemanticIR_Gate_*_v0.3.md`

> 本分册只定义 **V3 内容数据域**的持久化 schema（Source、Annotation、Candidate、
> Admission 后的 Question/Material/Image/Knowledge）。任务生命周期、LLM 调用审计、
> Budget、进程与租约的 schema 见 `30_Task_LLM_Safety.md`；管线的阶段对象契约
> （Annotation manifest / Resolver / IR / Compiler / Gate 的 JSON schema）见
> `20_Document_Pipeline.md`。术语裁决以 `README.md` §2 为准。

---

## 1. 定位：本 schema 是"Source-derived 数据编译系统"的关系化载体

依据 `00 P7`：Question 不是黑盒结果，而是**可重放的编译结果**。本分册区分三类
不同性质的数据域，并**分库分层地落盘**，避免 V2 那种"一层拼一层"的表堆叠：

```text
A. 内容事实域（live relational，Admission 后成为唯一活数据）
   questions / question_instances / instance_role_contents /
   materials / material_links / unit_groups / instance_figure_links /
   knowledge_nodes / question_knowledge_links

B. 源域（Source Domain：含可变主档 documents + active 指针 + 不可变 sealed 内容）
   documents / document_source_versions / document_source_lines / source_figures /
   document_active_sources / document_source_selection_events

C. 管线快照域（immutable snapshot，LLM 依赖或确定性编译的审计留存）
   semantic_annotations / admission_candidates / admission_events
```

运行域（task/attempt/lease/audit/budget）不在本分册，见 30。

> **域归属裁决（BUG-V3-001 errata）**：当章节级 Domain 总览清单与逐表 Schema 定义冲突时，
> 以 **Canonical Schema Domain 定义**为准（§4/§5/§6 的逐表定义权威于本清单）。

### 1.0 V3 三大哲学边界（数据库 schema 的判据）

- **Source 是事实边界**：sealed 后不可变；一切 live 正文必须锚定它。
- **Candidate 是管线/业务边界**：C 域到 A 域的唯一通道。
- **Question 是 Admission 后的 canonical domain entity；Instance 是它在某 Source 中的
  一次 occurrence**。两者身份问题彻底分开（§6.1/6.2）。

### 1.1 四条不可违反的承载规则（防止"LLM→文本→特判→回填"回潮）

1. **LLM 输出永远是 C 域的 annotation manifest，不是任何 live 文本。**
   `semantic_annotations.payload` 中即使出现疑似正文，也只是 LLM 对 Source 的"引用
   建议/解释"，没有任何查询把它的字符串当作题干/选项/答案正文来源（20 P3）。
2. **任何 live 文本正文都必须是 Deterministic Compiler 从 resolved span 的确定性产物，
   且逐 role 带 `source_span` + `text_hash`（P3 provenance）。**
3. **稳定关系一律实体化为 FK 或 link 表，禁止用 JSONB 承载**（Question↔Instance↔Image
   ↔Material↔Composite↔Knowledge）。JSONB 只允许：动态 role 内容、provider 元数据、
   快照 payload、构建版本/输入身份（见 §7）。
4. **Candidate = 冻结边界**：管线世界（Source/Annotation/Resolver/IR/Compiler/Gate）
   只产 C 域证据与快照；A 域 live 行只能由 Admission Transaction 物化。任何 service
   绕过 Candidate→Admission 直接创建 Question/Instance/Material/Image 行，都是架构
   违规（代码评审红线）。

---

## 2. 与 00 的服从对照（每一张表必须支撑一个宪法原则，否则不建）

| 00 原则 | 本 schema 的落点 |
|---|---|
| P1 最小闭环 M1 | A+B+C 三域 + 30 运行域即闭环全部；不建外围表（无推荐/统计/生成） |
| P2 LLM 无 Admission Authority | C 域 annotation/candidate 是"证据+快照"；`decision_status` 只能由确定性 Gate Policy 或人工写 |
| P3 Source 唯一事实源 | 所有 live 正文行带 `source_span`；`source_figures` 图片不猜；无 provenance 不能进 approved |
| P4 副作用显式 | seal 事务、admission 事务是仅有的两个多行写入口；post-admission 派生为显式 Repository 步骤 |
| P5 稳定性由不变量保证 | §8 列出实体级不变量；禁止针对题号/学校/OCR 变体加列或加特判表 |
| P6 Idempotency | `logical_execution_stage` + `logical_execution_hash` 双列 = **阶段执行身份**（annotation stage / compile stage 各自独立），非跨派生实体传播的全局 run_id；admission 幂等 = 候选状态迁移（approved 写入与物化同事务）+ 唯一约束 |
| P7 Replayability | `build_versions`=用什么版本构建；`input_identity`=对什么输入构建，两者分离（§9） |

反 V2 模式自查（§10）：本 schema **没有**"LLM 产出最终文本 → 落库回填 → Gate 只看
字段非空"的路径；最终文本必经 Compiler+Gate+Admission，且每步落证据。

---

## 3. 命名与 ID 约定

- 主键统一 UUID v4（link 表可用复合键）。个人系统规模不引入自增整数 id。
- 表名小写下划线；布尔列用 `is_` / `has_`；枚举列以 `*_status` / `decision_status`
  命名；时间戳统一 `TIMESTAMPTZ`。
- 审计/快照类表写入后不再 UPDATE（append-only），删除只能由显式人工接口。
- 标准 provenance 列（凡 B/C 域及 A 域派生表尽量带）：
  - `logical_execution_stage VARCHAR NULL` + `logical_execution_hash CHAR(64) NULL`：
    **stage-scoped 执行身份，以 "stage 枚举 + hash" 双列存储（冻结；30 必须沿用，
    不得改回 "单列 prefix+hash" 以免超长）**。`stage` ∈ 枚举（seal / ann / compile
    …），`hash` = 该 stage 的 SHA256。只记录**产生本行的那一个 stage**：annotation
    stage → semantic_annotations；compile stage（resolver+ir+compiler+gate 整段）
    → admission_candidates。**不是跨派生实体传播的全局 run_id**；唯一约束作用于
    `(stage, hash)` 对。hash 的 canonical 序列化规则见 §9，精确公式见 30。
  - `attempt_id UUID NULL`：那次实际执行尝试。
  - `source_version_id UUID`：实际消费的 sealed 版本（**不允许**假定与 active 一致）。
  - `input_identity JSONB`：P7 输入身份（§9）。
- 枚举值与 JSON 内字段名以 `README.md` §2 与 20/30 schema 为准；**新增术语必须先
  登记 README §2 再在本 schema 使用**。

---

## 4. B 域：不可变源域（Source Version 持久化）

依据 01 v0.3 收敛。**M1 裁剪**：`document_source_tables / _cells / _fragments` 不建
（00 §5 non-goal：文档级 cell/fragment 字符粒度延后）；`source_figures` 保留（M1
必需）。

### 4.1 documents（文档主档）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| original_object_key | VARCHAR | 对象存储 key |
| original_sha256 | CHAR(64) | 原始文件 SHA256（01 v0.3 决策 4） |
| file_name / file_type / upload_meta | VARCHAR / VARCHAR / JSONB | 上传元数据 |
| processing_status | VARCHAR | `created / ingesting / sealed / failed`（定义见下） |

规则与不变量：

- `documents` 不保存任何"最终题目文本"作为唯一事实；正文唯一来源是 active sealed
  source。
- `processing_status` 只表示 **Source 内容生命周期摘要**（raw/canonical 是否已 seal、
  active 是否已选）。它**不是** pipeline/task 完成度，更**不是**"该文档全部题目已
  Admission"；真正的每文档任务进度来自 30 的 task 记录。

### 4.2 document_source_versions（一次不可变解析结果）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| document_id | UUID | FK documents |
| artifact_kind | VARCHAR | original_binary / raw_l1 / canonical_l1 |
| role | VARCHAR | native / ocr_ppsv3 / ocr_ppsvl / docx / canonical |
| provider | VARCHAR | native / ppsv3 / paddleocr-vl / docx |
| parent_version_id | UUID NULL | 修正/派生来源 |
| body_text | TEXT | seal 前由 line index 确定性重建 |
| body_hash | CHAR(64) | SHA256(normalized body_text) |
| integrity_hash | CHAR(64) | SHA256(正文 + line index + figures + provenance) |
| page_count / line_count / text_coverage | INTEGER/INTEGER/NUMERIC | version 属性，非文档全局事实 |
| source_meta | JSONB | 提取配置、page_range 与 reason、OCR 证据、`legacy` 标记 |
| status | VARCHAR | draft / sealed / invalid |
| logical_execution_key / attempt_id | 见 §3 | 产生该 version 的 stage 键 |

约束：

- `status=sealed` 后禁止任何 UPDATE（Repository 抛错，不静默忽略）。
- **role/provider 封闭配对（BUG-V3-008 errata）**：`ocr_ppsv3 ⟺ ppsv3`、`ocr_ppsvl ⟺
  paddleocr-vl`、`native ⟺ native`、`docx ⟺ docx`；`canonical` role 无 provider。禁止任意
  组合。`provider`/`role` 均进入 seal LE hash（contract_domain.parser），独立引擎必须独立
  身份，防 identity 漂移。
- `body_text` 必须能从 line index 按 `seq` 以 `\n` 确定性重建（IS-4），读取比对
  `body_hash`，不一致拒绝使用。
- 修改任意一行/一张图，`integrity_hash` 必须改变（回归测试）。
- 个人规模：正文存 PostgreSQL TEXT，不引入对象存储正文（01 v0.3 决策 3）。

### 4.3 document_source_lines（line index）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK |
| line_ref | VARCHAR | 如 `P1L001`；`(source_version_id, line_ref)` 唯一 |
| seq | INTEGER | version 内全局 1-based 连续 |
| page_no / line_no_in_page | INTEGER | 1-based |
| text | TEXT | 该行正文 |
| block_type | VARCHAR | text / formula / table / figure_placeholder |
| bbox | JSONB NULL | page bbox |
| raw_sources | JSONB | provider 文本、native_line_id 等（IS-6，不丢） |
| selected_source / evidence | VARCHAR / TEXT | 最终来源与理由 |
| confidence | NUMERIC | 行级可信度，不代替答案正确性 |
| line_hash | CHAR(64) | SHA256(text + raw_sources + evidence…) |

约束：`line_ref` 只作**程序定位与审计证据**，永不进 LLM Annotation（20）；line_ref
不跨 version（IS-5）。行内字符级定位由 span 的 `start_offset/end_offset` 表达，不为
inline 单独建行。

### 4.4 source_figures（图片索引，Source-derived entity）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK |
| figure_id | VARCHAR | `FIG-{page_no}-{ordinal:02d}`（BUG-011 冻结，确定性生成；version 内唯一） |
| page_no | INTEGER | 必填 |
| bbox | JSONB | 必填 |
| placement | VARCHAR | source-level placement；M1 恒 `standalone`（值域 stem / options / explanation / answer_area / standalone） |
| source | VARCHAR | native / ppsv3 / … |
| object_key | VARCHAR | `figure:{figure_hash}`（M1 logical deterministic key，非已持久化 blob 声明） |
| figure_hash | CHAR(64) | `SHA256(raw_image_bytes)`（跨文档精确去重用） |

唯一约束：**`UNIQUE(source_version_id, figure_id)`**（identity invariant，DB 级兜底，非仅
应用层去重；BUG-011 冻结）。

**figure_id 生成规则（BUG-011 冻结，canonical visual order）**：`page_no` 1-based；`ordinal`
= 该 page 内 figure 的 canonical visual order（1-based），排序键 = `(page_no, bbox.top,
bbox.left, bbox.bottom, bbox.right, figure_hash, extraction_ordinal)`。**禁止** DB ID /
UUID / runtime ID / object storage key / figure_hash 作 figure_id。

**figure_hash（BUG-011 冻结）**：`SHA256(raw_image_bytes)`——identity 为 raw bytes 精确去重，
非 resized / normalized / decoded_pixels / canonicalized_image；视觉/语义相似属独立
similarity layer，不污染 Source Identity。

**object_key（BUG-011 冻结）**：`figure:{figure_hash}` 为 **logical deterministic key**，只
证明 deterministic identity/address 已生成、不证明对象存储已完成；M1 不实现真实 blob
storage，后续需读 image bytes 时 object store lookup 找不到必须 fail-loud（不得据 key 存在
即断言图存在）。

**placement 语义（BUG-011 冻结）**：`source_figures.placement` 是 **source-level
placement**——Source Seal 阶段无法确定 figure 对具体 Question Unit 的语义归属，故 M1 恒
`standalone`（= 源层未定语义归属，**非**"图片语义上独立于题干"）；semantic 归属由 A 域
`instance_figure_links.role` 表达（§6.6），禁止 E 反向 UPDATE `source_figures`。

领域边界（审查裁决）：**Source 不知道 Question**。本表**不设 `role_owner`/题号归属
字段**；"哪道题的 stem 用 FIG-3" 是 Question 侧的语义，由 A 域 `instance_figure_links`
（§6.6）表达。图片归属到 instance+role 后天然防整页广播。

**生产来源（BUG-011 冻结）**：Native Source Seal（PyMuPDF）**必须能产生 figures**——至少
`page_no` / `bbox` / raw image bytes / `source=native`，并据此确定性产生 `figure_hash` /
`figure_id` / `placement=standalone` / `object_key`；Native 阶段**不做 semantic placement**
（不产 stem/options 归属）。figure 不因 native 文本层提取而只对 cloud OCR provider 成立。

写入门（IS-7，BUG-011 冻结为完整写资格）：`figure_id`（deterministic）/ `page_no` / `bbox`
/ `placement` / `source` / `object_key`（deterministic logical key）/ `figure_hash`
（`SHA256(raw bytes)`）任一缺失或不满足确定性 → **不写 SourceFigure**、seal 不得假装 figure
成功、fail-loud；`figure_id` version 内去重由 `UNIQUE(source_version_id, figure_id)` 兜底。

### 4.5 document_active_sources 与选择事件

| Field | Type | Note |
|---|---|---|
| document_id | UUID | PK |
| role | VARCHAR | PK；native / ocr_ppsv3 / canonical |
| source_version_id | UUID | 只允许指向 `sealed` version |
| selected_at / selection_reason | TIMESTAMPTZ / TEXT | 自动/人工/回滚原因 |

`document_source_selection_events`（append-only，BUG-V3-002 errata 冻结逐列）：

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| created_at | TIMESTAMPTZ | NOT NULL |
| document_id | UUID | FK documents |
| role | VARCHAR | native / ocr_ppsv3 / ocr_ppsvl / canonical |
| old_source_version_id | UUID NULL | FK document_source_versions |
| new_source_version_id | UUID NULL | FK document_source_versions |
| operated_by | VARCHAR | NOT NULL |
| reason | TEXT NULL | |
| run_id | VARCHAR NULL | 运行/批次关联串，**非 LE identity**（非 logical_execution_stage/hash 组成部分） |

无 UNIQUE 约束（append-only 事件日志，同 document/role/old-new 在多时间/操作者/run 下多条合法）。

规则：active 指针可随重跑变化，旧 sealed version 永远可读；旧 annotation 永远按
其 `source_version_id` 回放。

---

## 5. C 域：管线快照域（Annotation / Candidate / Admission）

本域是"证据 + 可重放快照"，不是 live 业务数据；payload 写入后不再 UPDATE。

### 5.1 semantic_annotations（LLM 语义 claim 的唯一持久化）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| source_version_id | UUID | FK；Annotation 实际消费的 sealed 版本 |
| annotation_schema_version | VARCHAR | 如 `semantic-metadata/v0.3` |
| prompt_version / model_config_hash | VARCHAR / CHAR(64) | 见 30 |
| payload | JSONB | annotation manifest（语义 claim；**不含 line_ref/坐标/正文坐标**，schema 见 20） |
| status | VARCHAR | valid / invalid / superseded |
| logical_execution_stage / logical_execution_hash | VARCHAR / CHAR(64) | **Annotation Stage** 的执行身份；`(stage, hash)` **唯一**（§3） |
| attempt_id | UUID | 那次实际尝试 |

规则：

- payload 只含 Semantic Interpretation（00 P3），永不回写 Source。
- 该表使**重新编译无需重调 LLM**（换 Resolver/Compiler 重放时复用 annotation）。
- **本表的 key 只属 Annotation Stage**；后续 Resolver/IR/Compiler/Gate 的"编译执行"
  是另一个 logical execution，键写在 candidate（§5.2），不得继承本表键。
- LLM 只写 annotation；任何 LLM 请求进 30 的 `llm_call_audit`。

### 5.2 admission_candidates（Gate 决策 + 完整可重放 admission 快照）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| unit_type | VARCHAR | standalone_unit / composite_unit |
| source_version_id | UUID | FK |
| annotation_id | UUID | FK semantic_annotations |
| decision_status | VARCHAR | pending_review / approved / rejected（README §2.4） |
| gate_decision | JSONB | 分层 gate 输出：structural/provenance/semantic/admission + reasons（20 §8.1） |
| build_versions | JSONB | 用什么版本构建（§9） |
| input_identity | JSONB | 对什么输入构建：source_version_id、annotation_id、annotation_payload_hash、resolver_input_hash、compiler_input_hash（§9） |
| payload | JSONB | **完整可重放编译快照**（§5.3） |
| review_trail | JSONB NULL | 人工 review 的 decision/意见/时间（append，不覆盖） |
| created_at / decided_at | TIMESTAMPTZ | |
| logical_execution_stage / logical_execution_hash | VARCHAR / CHAR(64) | **Compile Stage**（resolver→ir→compiler→gate 整段）的执行身份；`(stage, hash)` **唯一**；与 5.1 的 annotation 键不同 stage（§3） |
| attempt_id | UUID | 那次实际尝试 |

决策归属（P2）：`decision_status` 只能由确定性 Gate Policy 或人工 approve/reject
写入；**LLM 调用不写本列**。knowledge 是否硬门槛不由本表决定（§6.7）。

决策语义（冻结，P1-1）：`approved` 不是"我决定批准"，而是"**本 Candidate 已完成
Admission 物化**"。`pending_review →（approve 事务：物化 A 域 + 写 admission_event +
置 approved）→ approved` 在同一数据库事务内原子完成（状态机见 §5.4）。事务失败整体
rollback，Candidate 保持 `pending_review` 可再次 approve。M1 **不存在 "approved 但
未物化" 的中间态**。

**gate_decision 不可变 + 人工 reject 理由归属（冻结，BUG-V3-026 终裁，20 §8.2）**：
`gate_decision` 由 Gate 判定一次性写入，写后不可变；机器拒受理由写
`gate_decision.reasons`，人工拒受理由写 `review_trail.reasons`（append，不覆盖、不写回
`gate_decision`）——二者分属不同证据链，**不是同一物**。不可变性为 application-layer
enforcement（Repository `update_candidate_decision` 恒抛 `AppendOnlyViolation`；
`_transition_decision` 唯一合法 transition path），**不加 DB trigger / RLS**。

### 5.3 Candidate payload 的完整性契约

`payload` 不是"stem+answer"，必须能在不重跑 LLM 的情况下重建 Question/Instance/
Material/Image（V3_DATA_MODEL §9）。最小结构（逐字段归 20/Display）：

```text
payload
├── ir_snapshot          IR（units/sub_questions/relations/依赖闭合，resolved 状态）
├── resolved_spans[]     每个 content role 的 Resolved Source Span（line_ref/offset/text_hash）
├── compiled_roles[]     role → compiled text（Deterministic Compiler 产物）+ text_hash
├── answer[]             编译后答案 + answer_status 三字段（source_located/complete/verified_correct）
├── figure_refs[]        (unit_id, figure_id, role, order)（IS-7 齐全才可带；落库见 §6.6）
├── knowledge_links[]    （可选）建议的知识点映射，源自 annotation claim（§6.7）
├── evidence[]           gate 判定证据
└── display_hint         canonical_question_type / content_roles（DISPLAY_CONTRACT 兼容）
```

约束：

- 任一 role 缺 resolved span 且缺 compiled text，payload 视为不完整，不得进自动
  approved（P3 / IS-8）。
- `payload` 是快照承载，不是 live 关系；admission 后所有稳定关系落 A 域真实表
  （§6）。与 00 §5"禁用 JSONB 隐式承载业务模型"不冲突。

### 5.4 admission_events（Admission outcome / audit record）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| candidate_id | UUID | FK admission_candidates；**唯一**（同一候选至多一条物化记录） |
| materialized_at | TIMESTAMPTZ | |
| created_question_ids / created_instance_ids / … | UUID[] | 事务内新建行 id 汇总 |

语义（二轮审查裁决，P1-1 状态原子性）：

```text
Candidate：pending_review
            ├── reject   → rejected（terminal）
            └── approve → Admission Transaction（单事务）
                              ├─ lock candidate & validate decision_status=pending_review
                              ├─ 物化 A 域（Question 复用/新建 + Instance + role + Material/Image/unit）
                              ├─ INSERT admission_event（candidate_id 唯一）
                              ├─ decision_status → approved
                              └─ COMMIT
                                  └─ 任一步失败 → ROLLBACK，Candidate 保持 pending_review，可再次 approve
```

- **`approved` 状态写入、A 域物化、`admission_event` 插入属于同一数据库事务**
  （P1-1）；不存在 "approved 但未物化" 的中间态。
- 本表是 **admission outcome / audit + materialization result index**，不是幂等机制
  本身。真正防止重复物化 = approve 状态机 + 事务原子性 + Question 去重复用 /
  Instance occurrence 唯一（§6.1/6.2）+ `candidate_id` 唯一。
- 重复 approve 已 approved 的 candidate：状态机拦截为 no-op，返回既有结果。

---

## 6. A 域：内容事实域（Admission 的物化目标，live relational）

A 域 live 行只能经 Repository 创建；**内容原子组（Question/Instance/role/Material/
Image/unit）只在 Admission Transaction 内创建**；post-admission 的可选派生（知识映射
§6.7）以独立 Repository 步骤追加，不得回改已提交的内容行。

### 6.1 questions（canonical 题目本体 = leaf）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| subject / grade | VARCHAR NULL / VARCHAR NULL | Derived（annotation claim 直接映射；claim 缺失 → NULL = unknown，非空串，BUG-V3-021 终裁） |
| canonical_question_type | VARCHAR | single_choice / multiple_choice / true_false / fill_in / short_answer / writing…（DISPLAY_CONTRACT） |
| dedup_key | CHAR(64) | canonical 精确去重（§6.8） |
| created_at | TIMESTAMPTZ | |

身份与生命周期：

- **Question = 跨文档 canonical identity**；**不设 `status` 生命周期列**——一行
  Question 存在本身即意味已通过 Admission。若未来需要 deprecated/superseded，作为
  显式生命周期功能设计，**不得复用/混淆 `Candidate.decision_status`**。
- composite 的"叶子题"与 standalone 一样是 Question；composite 作为展示单元由
  unit_groups + material_links 表达（§6.4/6.5），Question 表不存复制文本。

**Admission 去重行为（审查裁决，冻结）**——Admission Transaction 内按 `dedup_key`
查表：

```text
candidate(unit) 进入物化
  → question dedup lookup（按 dedup_key，exact）
      ├─ 无 exact 命中 → INSERT 新 Question（新 canonical identity）
      └─ exact 命中   → REUSE 该 Question（不重建、不改写），仅为其 INSERT 新 Instance
```

- 近义 / 模糊命中 → **不自动合并**，列入人工确认候选（00 §5：semantic merge 延后）。
- **DB 唯一性（BUG-V3-027 errata）**：`questions.dedup_key` 加**全局** `UNIQUE(dedup_key)`
  （非复合；dedup_key 不含 source_version/subject/grade/document，Question 本就是跨文档
  canonical identity）。`create_question` 用 `INSERT ... ON CONFLICT DO NOTHING` + re-read
  收敛；并发 approve 同 dedup_key → 恰 1 Question、多个 Instance。存量重复 → migration
  fail-loud（不静默 merge/删行）。

**subject/grade metadata 收敛（BUG-V3-021 终裁）**：Question identity（dedup_key）不含
subject/grade；metadata 是独立于 identity 的层次。同 dedup_key 复用既有 Question 时：
`NULL → known` 允许（补写）；`known → same` 允许（no-op）；`known → different` → fail-loud
（RepositoryError，禁止静默覆盖）。unknown 用 `NULL` 表示，**绝不用空串 `""`**。
- **dedup 命中永远不使 candidate 变成 rejected**：去重只影响"复用还是新建"，不否定
  题目本身有效。
- `dedup_key` 基于 **20 定义的 Compiler canonical output** 计算（空格/换行/LaTeX/
  Unicode/全半角等规范化规则归 20 的 normalization contract）；**Admission 层不做
  任何 normalize/fuzzy/特判**，禁止在物化时临时 `remove_space/if latex/…`——防止 V2
  fuzzy matching 从物化路径塞回（P1-2）。

### 6.2 question_instances（一次 Source occurrence）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| question_id | UUID | FK questions |
| document_id | UUID | FK documents |
| source_version_id | UUID | FK；出现所在 sealed 版本 |
| unit_group_id | UUID NULL | 若属于 composite/展示单元（§6.5） |
| occurrence_key | CHAR(64) | **occurrence 身份**：同一 Question 在同一 Source 中的同一次出现（构造见 20，如 unit/question_number/resolved stem span 的确定性组合） |
| question_number / question_number_range | VARCHAR | 题号 / 如 `11-13` |
| page_no | INTEGER | 出现页 |
| instance_order | INTEGER | 文档内展示顺序 |
| created_at | TIMESTAMPTZ | |
| logical_execution_stage/hash + attempt_id | 见 §3 | 由产生它的 admission 带出 |

约束与区分（审查裁决）：

- **Question 去重回答"是不是同一道题"；Instance 唯一回答"是不是同一次出现"。** 两
  个问题彻底分开。
- 唯一约束：`UNIQUE(question_id, source_version_id, occurrence_key)`。
- 同一 question 在多文档/多出现处各有一 instance；同文档内同一题只应有一 instance
  （intra-doc 重复被 occurrence_key 拦截）。

### 6.3 instance_role_contents（逐 role 编译内容 + 逐 role provenance）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| instance_id | UUID | FK |
| role | VARCHAR | stem / options / answer / explanation（content_role，README §2.2） |
| label | VARCHAR NULL | 仅 options 用，如 `A` |
| role_index | INTEGER | options/多值顺序 |
| text | TEXT | **Compiler 从 resolved span 的确定性正文** |
| text_hash | CHAR(64) | SHA256(text.encode("utf-8"))（raw，不含 source refs，BUG-V3-017 终裁） |
| source_span | JSONB | 该 role 的 Resolved Span（见下方 provenance 约束） |
| answer_status | JSONB NULL | 仅 role=answer：`{source_located, complete, verified_correct}` 三字段独立（20） |

约束：

- `(instance_id, role, label, role_index)` 唯一。
- `text` 绝不来自 LLM 输出。
- **`source_span` 是 JSONB，不是 FK——PostgreSQL 无法强制它的引用与 hash 真实性。**
  它是**应用层 provenance invariant**，由 Resolver/Compiler/Gate 验证（§8 不变量
  2a-2d）；实现者不得假设"有 span JSON = 数据库已保证 provenance"。

### 6.4 materials + material_links（共享材料只存一次）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| subject / grade | VARCHAR NULL | 同上 Derived（claim 缺失 → NULL，BUG-V3-021 终裁） |
| source_version_id | UUID | **Scope**（见下） |
| text | TEXT | material 编译正文（一次） |
| text_hash | CHAR(64) | |
| source_span | JSONB | material 的 resolved span |
| dedup_key | CHAR(64) NULL | 材料精确去重线索 |

material_links：

| Field | Type | Note |
|---|---|---|
| instance_id | UUID | FK（消费该材料的子题 instance） |
| material_id | UUID | FK materials |
| role | VARCHAR | material_required / word_bank |
| order | INTEGER | 组内顺序 |

Source-scoped 规则（审查裁决）：**Material 是 Source-scoped entity，M1 不做跨
Source Version 的自动共享**。另一文档出现相同材料 → 各自成行、`dedup_key` 相同，
只作**精确去重候选**，不自动跨 Source canonicalize（避免悄悄长成全库材料统一/内容
复用系统，00 §5 semantic merge 延后原则一致）。

约束：material 正文不复制进任何子题 stem；子题经 material_links 引用
（README §2.2 / 00 P1）。material_links 的 instance 与 material 应同属一个
source_version（IS-5）。

### 6.5 unit_groups + members（presentation / grouping 单元）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| unit_type | VARCHAR | standalone_unit / composite_unit（**展示/分组标签**） |
| document_id / source_version_id | UUID | |
| question_number_range | VARCHAR | 如 `11-13` |
| shared_material_id | UUID NULL | composite 主材料（可空：共享选项池等） |

unit_group_members：

| Field | Type | Note |
|---|---|---|
| unit_group_id | UUID | FK |
| instance_id | UUID | FK question_instances |
| member_order | INTEGER | 展示顺序 |
| role_in_group | VARCHAR | child / 说明 |

边界声明（审查裁决）：**unit_group 只表达 presentation/grouping identity，不决定
Question 的语义独立性。** standalone vs composite 的语义由 20 的 Semantic Question
IR 判定；本表不承担"这些题共享解题语义"的语义断言（防 V2 Composite bug 回潮）。
standalone 也可记单 member 的 unit_group，使展示读取模型统一。

### 6.6 instance_figure_links（Instance 对 Source 图的归属）

| Field | Type | Note |
|---|---|---|
| instance_id | UUID | FK question_instances |
| source_figure_id | UUID | FK source_figures（B 域） |
| role | VARCHAR | stem / options / explanation / answer_area… |
| order | INTEGER | 图在 role 内顺序 |

page_no/bbox/figure_hash 从 `source_figures` 读取，**A 域不复制**（避免重复存储与
漂移）。唯一约束：`(instance_id, source_figure_id, role, order)`。

```text
source_figures (B 域，图属于哪个 Source)
      ↑  instance_figure_links
      │
question_instance  (A 域，谁用它、当什么 role)
```

命名说明（二轮裁决，P1-3）：本表 FK 是 `instance_id`（非 question_id）——同一
Question 的不同 Instance 可能各配不同图，某次出现甚至无图。故命名
`instance_figure_links` 而非 `question_image_links`，避免误读为 canonical Question
拥有图。它链接的是 `question_instance ↕ source_figure`。

candidate payload 的 `figure_refs[]`（§5.3）经 Admission 落成这些行；缺 page/bbox/
placement/source 的图不得成为关联（IS-7）。

**Admission mapping（D-6 Figure Contract 冻结，M1 只冻结不实现）**：
`figure_refs[] → instance_figure_links` 的映射为：由 `(source_version_id, figure_id)`
在 `source_figures` 内唯一反查 `source_figure_id`，再写 `(instance_id, source_figure_id,
role, order)`；`figure_id` 是 version-scoped 字符串 join key（非 UUID），不改动既有
SourceFigure identity 模型。**段 B 未接 seal figures（BUG-011）前 `source_figures` 恒空**
→ image reference 恒 ambiguous → F image `unsupported → incomplete`（fail-loud）、
`figure_refs[]` 恒空——**本映射为契约定义，非当前已实现的 figure 通道**。

**placement ≠ role 语义区分（BUG-011 冻结）**：`source_figures.placement`（source-level
placement，M1 恒 `standalone`）与 `figure_refs[].role`（unit-level semantic role）**值域可
相同但语义层级不同、不要求值相等**——`figure_refs[].role` 可为 `stem/options/...`，而
`source_figures.placement` 在 M1 恒 `standalone`；semantic 归属只由本表 `role` 列承载，
禁止 E 反向 UPDATE `source_figures`（sealed source 不可变）。

### 6.7 knowledge_nodes + question_knowledge_links（可选派生映射）

| Field | Type | Note |
|---|---|---|
| id | UUID | PK |
| tree_version | VARCHAR | 知识树版本（seed 来自 50；自动扩展延后） |
| parent_id | UUID NULL | |
| subject / code / name | VARCHAR | 稳定 code + 名称 |
| source | VARCHAR | seed / derived |

question_knowledge_links：

| Field | Type | Note |
|---|---|---|
| question_id | UUID | FK |
| knowledge_node_id | UUID | FK |
| mapped_by | VARCHAR | deterministic / human（M1 不用 annotation_claim 直写 approved 链接） |
| mapped_from_claim | JSONB NULL | 若源自 annotation claim 的引用 |

**是否 hard gate——跨分册契约（审查裁决）**：

- **M1 默认：Knowledge 是 optional derived mapping，不是 Admission 硬依赖。**
  题目内容原子性 = Question content complete + Instance complete + Material complete +
  Image provenance complete + Answer valid；与 knowledge 分类成功与否**解耦**。
- knowledge mapping failure **不得破坏 Question 内容原子性、不得使 approved 回滚**。
- 若 20/00 未来明确 "Knowledge is admission-required"，20/00 必须显式写出；届时 10
  再给 candidate 加对应不变量。**10 不在本版本单方拍板。**

### 6.8 Hash / Dedup 规则

- `dedup_key`（questions / materials）只做**确定性精确去重**；语义相似不是 hash。
- 去重链：`exact hash → 明确相似候选 → 人工/独立语义判断`（00 §5 无自动 merge）。
- Question：exact 命中 = 复用 canonical + 新建 Instance（§6.1）；Materials：exact
  命中只作候选，不跨 Source 自动共享（§6.4）。
- 同一 Question 多 occurrence 由 instance 层承载（§6.2），不由复制文本表达。

---

## 7. JSONB 使用边界

允许（变量面 / 快照面，非关系面）：

- annotation manifest、gate decision、candidate payload（快照承载，§5.3）；
- `build_versions`、`input_identity`（构建身份，§9）；
- provider 元数据 / source_meta / review_trail / role 的动态 `answer_status` /
  dynamic display_hint。

禁止（稳定关系不得入 JSONB）：

- Question↔Instance、Instance↔role 正文、Instance↔Material、Composite↔child、
  Instance↔Figure(Source 图)、Question↔Knowledge——全部实体化 FK/link（§6）。

判断句：**能数清个数的稳定关系必须能 join；只有逐题可变长、可变的动态面才允许
JSONB。**

---

## 8. 实体级不变量（P5 + provenance 真实性）

1. sealed source 行：无 UPDATE/DELETE；body_hash 可重建（IS-4）。
2. 每个 live 正文行非空且带 `source_span` + `text_hash`（IS-8）。因 `source_span`
   是 JSONB 而非 FK，以下**应用层 provenance invariant 必须由 Resolver/Compiler/
   Gate 验证**，不假设数据库保证：
   - 2a `source_span.source_version_id ==` 该行所在表的 `source_version_id`；
   - 2b `source_span.line_ref`（及 offset）∈ `document_source_lines(source_version_id)`
     且行内 slice 存在；
   - 2c resolved `text_hash ==` 该 source line/slice 的实际 hash；
   - 2d compiled `text_hash ==` 该 role 确定性编译结果的 hash（no generated prose）。
3. composite：任一子题 unresolved/incomplete → 整个 composite 不是 ready（20 §8.5）；
   material 正文不在任何子题 stem span 内（不重复）。
4. `decision_status` ∈ {pending_review, approved, rejected}；无对象即状态混写。
5. approved 的 answer 行必须 `source_located=true` 且 `complete=true` 且
   `verified_correct=true`（或 human/golden 置 true），三字段独立（20）。
6. 同一 candidate 至多一次物化（§5.4）；重复 approve 为 no-op。
7. 图片与 Instance+role 的关联（`instance_figure_links`）必须指向已通过 IS-7 的
   source figure（§6.6）；**Source 侧不设题号归属字段**（§4.4）。
8. `unit_group.unit_type` 是展示标签，不是语义 composite 断言（§6.5）。
9. `documents.processing_status` 只表达 Source 内容生命周期，不表达 admission/task
   进度（§4.1）。
10. **禁止**因单题号/单学校/单 OCR 变体新增列或特判表；某差异看似必须特判，先质疑
    model/role 表达力（00 P5 红线）。

---

## 9. Replay 与版本（P7 落点）

分离两个概念（审查裁决）：

- `build_versions` = **用什么版本构建**：

```json
{
  "source_version": "<uuid>",
  "annotation_schema_version": "semantic-metadata/v0.3",
  "prompt_version": "semantic-annotation/v3",
  "model_config_hash": "<sha256>",
  "resolver_version": "resolver/v1",
  "ir_schema_version": "semantic-question-ir/v0.3",
  "compiler_version": "compiler/v1",
  "gate_policy_version": "admission-gate/v1"
}
```

- `input_identity` = **对什么输入构建**（Exact Replay 的输入身份，Candidate 上）：

```json
{
  "source_version_id": "<uuid>",
  "annotation_id": "<uuid>",
  "annotation_payload_hash": "<sha256>",
  "resolver_input_hash": "<sha256>",
  "compiler_input_hash": "<sha256>"
}
```

- **Exact Replay**：相同 `input_identity` + 相同 `build_versions` → 重放
  resolver→ir→compiler→gate 得到确定性等价候选；由候选 compile-stage key 唯一性 +
  编译纯函数保证。
- **canonical 序列化（二轮裁决）**：`input_identity` 中的各 hash 与
  `logical_execution_hash` 必须基于 **canonicalized、确定性序列化** 后计算（JSON 键序
  稳定），统一序列化规则由 30 / 公共 hashing utility 定义，防 "同对象不同键序 → 不同
  hash" 漂移。
- **Rebuild**：换 resolver/compiler/gate 版本（改 `build_versions`）→ 新 compile
  logical execution、新 key、新 candidate；不覆盖旧 candidate。这是版本演进正常机制。
- 旧 annotation 永远按 `source_version_id` + 自身版本回放（01 §17 验收 4）。
- 工具：`python -m app.cli replay <candidate_id>`（只读确定性重放比对）。

---

## 10. 反 V2 模式逐条自查（本 schema 的护栏落点）

| V2 反模式 | 本 schema 的阻止点 |
|---|---|
| LLM → 最终题干文本落库 | 唯一正文来源 = B 域 line + A 域 role `text`（Compiler 产物）；annotation.payload 只是 claim |
| 行号/line_id 当最终事实 | line_ref 只在 Resolved Span（C 域）出现；live 文本锚定 span，不存裸行号文本 |
| content_slicer 按行号拼 stem/材料 | 无 slicer 表/字段；role 边界由 Resolved Span 闭合，逐 role 落 A 域 |
| Gate 只查字段非空 + 文本相似 | 无"字段非空即可"存储位；gate 依据来自 §5.3 结构化证据 + §8 不变量 |
| 答案"在原文出现"=正确 | answer_status 三字段独立，approved 强制 verified_correct 路径（20） |
| recover stale → queued 自动重跑 | 属 30；candidate/annotation 阶段键 + 状态机防重复物化 |
| JSONB sub_questions 吸收关系 | sub/child/material/image/knowledge 全部实体化（§6） |
| Composite 当成语义合并块 | unit_group 只表达展示（§6.5）；语义 composite 归 20 IR |
| 服务直接写 Question | §1.1 规则 4：A 域只能经 Candidate→Admission 物化，违者=架构违规 |
| 单题号特判 + 兼容第二管线 | §8 不变量 10；A/B/C 三域一套表，无 legacy 分支列 |

---

## 11. 迁移与演进规则

1. 所有 schema 变更走 Alembic migration：`Model + Migration + Test + 文档`。
2. 禁止手工 `ALTER TABLE` 作正常流程；禁止给 sealed 表做覆盖历史式 backfill。
3. V3 全新库：**不迁移 V2 任何列/镜像**（00 §1 第四类只继承资产与样本，不继承库）。
4. A 域新增实体必须回答它支撑哪条 P1-P7；若只为某 pipeline 方便而建 → 不建（P5）。
5. 版本演进用 Rebuild（新 compile logical execution + 新 candidate），不改旧行。

---

## 12. 变更记录

### 2026-09-05（v1.0）

- 建立 10 分册：收敛 `V3_DATA_MODEL`（起草）+ v0.3 01/03（字段权威）；A/B/C 三域
  分层；M1 裁剪 table_cells/fragments；Candidate 快照完整性契约；Admission 原子
  物化；P6 幂等键、P7 version set 落地。

### 2026-09-05（v1.1，10 审查 8 项修订 + 3 项最小方案）

- P0-1 `logical_execution_key` 明确为**阶段执行身份**：annotation stage（5.1）与
  compile stage（5.2）各自独立，非跨派生实体传播的全局 run_id（§3）。
- P0-2 Question dedup 命中行为冻结：exact 命中 → **复用 canonical Question + 新建
  Instance**；近义 → 人工确认候选；dedup 永不使 candidate rejected（§6.1）。
- P0-3 `source_span` 明示为**应用层 provenance invariant 而非 FK**，四条子不变量
  2a-2d 写入 §8，由 Resolver/Compiler/Gate 验证。
- P0-4 Instance 增加 `occurrence_key` + `UNIQUE(question_id, source_version_id,
  occurrence_key)`；明确"Question 去重=是不是同一题 / Instance 唯一=是不是同一次
  出现"分离（§6.2）。
- P1-1 Knowledge 标注为**跨分册契约**：M1 默认 optional derived、不阻断内容原子性；
  是否 hard gate 待 20/00 显式决策（§6.7）。
- P1-2 删除 `source_figures.role_owner`（Source 不知道 Question）；归属改由 A 域
  `instance_figure_links` 表达（§4.4）。
- P1-3 补全 `instance_figure_links` schema（instance_id + source_figure_id + role +
  order；page/bbox/hash 从 B 域读，A 域不复制）（§6.6）。
- P1-4 P7 分离 `build_versions`（用什么版本）与 `input_identity`（对什么输入）
  （§5.2、§9）。
- 最小方案：`questions`/`materials` 不设生命周期 `status` 列（存在即 admitted，与
  `decision_status` 区分）；`documents.processing_status` 限定为 Source 内容生命周期
  摘要（§4.1 不变量）；`admission_events` 定位为 outcome/audit，幂等措辞改为
  候选状态迁移+事务+唯一约束（§5.4）。
- 补强：§1.0 三大哲学边界（Source=事实 / Candidate=管线·业务 / Question=canonical +
  Instance=occurrence）；§1.1 规则 4 Candidate=冻结边界；§6.5 unit_group 只表达
  presentation（防 V2 Composite 回潮）。

### 2026-09-05（v1.2，10 二轮审查 4 项冻结前修订）

- P1-1 Admission 状态原子性：`approved` 状态写入、A 域物化、`admission_event` 插入
  在同一数据库事务；事务失败整体 rollback，Candidate 保持 pending_review 可再次
  approve；M1 无 "approved 但未物化" 中间态（§5.2 决策语义、§5.4 状态机、§8 不变量 6）。
- P1-2 `dedup_key` 生成责任归 20：基于 Compiler canonical output 计算；Admission 层
  不做 normalize/fuzzy/特判（§6.1、§6.8）。
- P1-3 `question_image_links` → `instance_figure_links`：FK 实为 instance_id，避免误读
  为 canonical Question 拥有图（§6.6 及全文引用）。
- P1-4 `logical_execution_key` 改 **stage 枚举 + hash CHAR(64) 双列**（冻结；30 必须
  沿用，不得回退单列 prefix+hash）；§9 增 canonical 确定性序列化规则（键序稳定，由
  30/公共 hashing utility 定义）。

### 2026-09-05（v1.2.1，锚点 errata）

- 仅修正两处指向 20 的**节号引用**（无 schema/字段/语义变更）：
  - §5.2 `gate_decision` 分层输出出处 "20 §11" → **"20 §8.1"**（四层 Gate 定义处；
    20 §11 是词汇红线，原引用无法解析）；
  - §8 不变量 3 composite 原子性出处 "20 §12.1" → **"20 §8.5"**（20 §12 是变更记录）。
- 触发：20 v1.1 审查 P1-3 发现 10 冻结文件含 v0.3 时代遗留节号；errata 限引用修正，
  20 §8.1/§8.5 为 Gate 分层与 Composite 原子性的实际所在节。

### 2026-09-09（v1.2.2，BUG-011 Scope Freeze errata）

- §4.4 `source_figures` 四字段语义 + 唯一约束冻结（BUG-011 终裁）：`figure_id` =
  `FIG-{page_no}-{ordinal:02d}`（canonical visual order，排序键 page_no→bbox.top→bbox.left→
  bbox.bottom→bbox.right→figure_hash→extraction_ordinal）；`placement` M1 恒 `standalone`
  （source-level placement 未定，非"图片天然独立"）；`figure_hash` = `SHA256(raw_image_bytes)`；
  `object_key` = `figure:{figure_hash}`（M1 logical deterministic key，非已持久化 blob）；
  加 `UNIQUE(source_version_id, figure_id)`；IS-7 重定义为完整 7 字段写资格（任一缺失或不
  满足确定性 → 不写 + fail-loud）。
- §4.4 增 figure 生产来源：Native Source Seal（PyMuPDF）必须产 figures（不做 semantic
  placement）。
- §6.6 增 placement ≠ role 语义区分（source-level vs unit-level，值域可同、语义独立、
  不要求相等；禁止 E 反向 UPDATE `source_figures`）。
