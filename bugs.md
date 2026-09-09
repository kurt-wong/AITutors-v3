# AI Tutor V3 — 已知问题与修复记录

> **更新规范（参照 V2 `bugs.md`）**
> - 只记录 V3 开发中发现的缺陷；进度/验收/架构分别写 `Status.md` / `log.md` /
>   `Docs/V3_SPEC/`。
> - 新增按 ID 追加：编号从 **`BUG-V3-001`** 起（避免与 V2 的 `BUG-xxx` 混淆）。
> - **每条记录与状态变更均带当前时间戳（`YYYY-MM-DD HH:MM:SS`）**；Open → Resolved 等
>   状态变化在原条目下追加一行时间戳，不改写现象/根因历史。
> - 每条带：Status（Open / Resolved）/ 现象 / 根因 / 修复 / 验收条件。修复后标
>   `Resolved`，**保留历史**。

## Open Bugs

### BUG-V3-001 — 10 §1 `documents` 域归类与 §4 冲突
- Status: Open
- 登记：2026-09-05 20:31:32
- 现象：10 §1 A 域列表含 `documents`，但 schema 定义在 §4（B 域）。
- 根因：10 v1.2.1 引言归类与 schema 定义位置不一致。
- 处置：段 A 实现按 §4 归 B 域（models/source.py）；待 10 changelog/errata 澄清。
- 验收：实现无偏差；登记为 spec 待裁决项。
- **Resolved（2026-09-08）**：终裁 `documents` 归 B 域（§4 Schema 定义权威，§1 A 域清单删
  documents；B 域澄清为 Source Domain）。加规则「总览 vs 逐表定义冲突时以 Schema 定义为准」。

### BUG-V3-002 — `document_source_selection_events` 列冻结缺失
- Status: Open
- 登记：2026-09-05 20:31:32
- 现象：10 §4.5 只给语义（旧/新 version、操作人、reason、run_id），未冻结逐列。
- 根因：spec 字段级缺漏。
- 处置：段 A 按 01 v0.3 决策 5 补列（id/document_id/role/old_source_version_id/
  new_source_version_id/operated_by/reason/run_id/created_at）；待 10 errata。
- 验收：实现与该补列一致。
- **Resolved（2026-09-08）**：冻结 9 列（id/created_at/document_id/role/old_source_version_id/
  new_source_version_id/operated_by/reason/run_id）；run_id ≠ LE identity；无 UNIQUE。

### BUG-V3-003 — embedding 模型名跨文档不一致
- Status: Open
- 登记：2026-09-05 20:31:32
- 现象：50 §3 写 Qwen3-Embedding **0.6B**；ASSET_INVENTORY / DICTIONARY / V2 写
  `qwen3-embedding:4b`（dim 2560）。
- 根因：文档口径不一致。
- 处置：段 A config/.env.example 用 4b/2560；待段 C 前终裁。
- 验收：配置与最终裁决一致。
- **Resolved（2026-09-08）**：终裁 embedding = `qwen3-embedding:4b` / dim 2560；50 §3 措辞
  errata 为 4b/2560（原「0.6B」为离群值）。

### BUG-V3-004 — replay 入口措辞不一致（10 §9 vs 30 §2）
- Status: Open
- 登记：2026-09-05 20:31:32
- 现象：10 §9 `python -m v3 replay` vs 30 §2 `python -m app.worker run`。
- 根因：包名 v3/app 未统一（已由用户裁决包名 `app`）。
- 处置：段 A 全用 `app`；replay 实装（段 H）用 `python -m app.cli replay`；10 §9 措辞待
  errata。
- 验收：CLI 入口与包名裁决一致。
- **Resolved（2026-09-08）**：10 §9 措辞 errata 为 `python -m app.cli replay`（包名 `app`）；
  replay 工具本身按段 I 排期实现。

### BUG-V3-005 — canonical_json 浮点 precision 位数未冻结
- Status: Open
- 登记：2026-09-05 20:31:32
- 现象：30 §16 写「浮点按定长十进制格式化」，未冻结 precision 位数/格式化算法。
- 根因：spec 数字规范缺位数。
- 处置：段 A 用 `repr(float)` 作临时 deterministic representation（不代表冻结解释）；当前
  LE hash 身份输入不含 float，不阻塞。待 30 §16 终裁。
- 验收：终裁后 utility 版本递增 + 走 Rebuild。
- **Resolved（2026-09-09）**：终裁 float **不是**允许的 identity 输入类型——canonical identity
  序列化遇 float 必须 fail-fast（30 §16 canonical_json），杜绝浮点 precision 进入身份 hash。
  commit `a731e0d`。

### BUG-V3-006 — `budget` 列清单遗漏 reserved 数值列（30 §17 vs §11）
- Status: Open
- 登记：2026-09-05 21:18:44
- 现象：30 §11 明确预算三量「额度/已用量/预留量」，§17 `budget` 列清单只有 limit/used/
  reserved_at，无 reserved 数值列。
- 根因：spec 字段级缺漏。
- 处置：段 C 按冻结语义补 `budget.reserved NUMERIC` 列实现（reserve→settle 需预留量）；
  `limit`/`used`/`reserved` 单位与精度（token/调用/金额）未冻结 → 以调用方同单位数值实现，
  不自行设币种/换算。待 30 §17 errata 终裁。
- 验收：reserved 补列与 reserve/settle 语义一致；终裁后对齐。
- **Resolved（2026-09-08）**：冻结 `reserved NUMERIC NOT NULL DEFAULT 0`；单位=调用方同单位
  抽象标量（同一 scope 内同计量体系，DB 不存单位/币种、不跨单位换算）；精度=NUMERIC（禁 FLOAT/
  固定 scale）；保留五账户正交禁派生。

### BUG-V3-007 — `original_sha256` 与 `document_source_versions` 基数关系未冻结
- Status: Open
- 登记：2026-09-05 22:30:34
- 现象：段 B seal 幂等的 version identity 语义存在 spec 张力——30 §16「幂等由 source_version
  唯一（原始文件内容 hash）」与 40 §2「seal 幂等（原始文件 hash 唯一）」暗示一文件一 version；
  但 10 §4.2 `role` 枚举（native/ocr_ppsv3/canonical）+ §4.5 `document_active_sources` 复合
  PK `(document_id, role)` 明确支持一文档多 source_version；且 30 §16 LE 公式
  contract_domain 含 role/provider → 不同 role 得不同 logical_execution_hash。
- 根因：spec 未明确「一个 original_sha256 对应几个 sealed version」（document identity 与
  seal execution identity 关系未统一）。
- 处置：段 B 保守按 10 §3「唯一约束作用于 (stage,hash)」LE 幂等 + 10 §4.1 document 级
  `original_sha256` 复用实现；Gate B1 只断言「同文件+同 role/provider/contract → 恰 1
  version」；跨 role 版本基数留给 errata 终裁，不自行创造唯一性规则。
- 验收：errata 终裁后按最终语义对齐（若裁决一文件一 version，则需补 UNIQUE；若允许多
  role 多 version，则保持现状并确认幂等键）。
- **终裁（2026-09-07，用户 Final Ruling）**：`original_sha256` 定义 Source/Document Identity，
  **不定义全局唯一 Sealed Version**；同一 `original_sha256` 允许存在多个 sealed version；
  跨不同 frozen seal role/provider 的 version 合法共存、不视为 duplicate；同一
  `original_sha256 + frozen seal role/provider scope` 内 canonical sealed version 至多一个；
  **禁止 `UNIQUE(original_sha256)`**；不得为实现 H-1 擅自引入 Frozen Spec 未定义的
  identity 字段；改 DB constraint 前先核对 Document/Version schema 与 Frozen Spec，现有字段
  若不足以表达该作用域 → 登记新 Spec gap，不自行扩展 schema。→ BUG-V3-029（H-1）按此
  终裁设计 scoped uniqueness。
- **Clarification（2026-09-07）**：「禁止 `UNIQUE(original_sha256)`」作用域 = `document_source_versions`
  的 Seal 层全局唯一（禁）；`documents` 层的 `UNIQUE(original_sha256)` 放行（Source/Document Identity，
  一个原始文件一个主档）。Seal Version canonical uniqueness 由 Frozen LE Identity 表达
  `UNIQUE(logical_execution_stage, logical_execution_hash)`。
- **Resolved（2026-09-08）**：按终裁 + Clarification 闭合；Frozen Spec 30:389 / 40:55 已同步
  裁决后语义（documents `UNIQUE(original_sha256)` ≠ Seal 层全局 UNIQUE；Seal canonical uniqueness
  由 `UNIQUE(logical_execution_stage, logical_execution_hash)` 表达）。

### BUG-V3-008 — cloud OCR（PaddleOCR-VL）role/provider 值域未冻结（10 §4.2 vs OCR_PROVIDER_POLICY）
- Status: Open
- 登记：2026-09-05 23:07:10
- 现象：10 §4.2 `document_source_versions.role` 枚举 = native/ocr_ppsv3/docx/canonical、
  `provider` 枚举 = native/ppsv3/docx；而 OCR_PROVIDER_POLICY L1 主识别 = PPS/PVL 双模型，
  PaddleOCR-VL-1.6 非 PP-StructureV3。段 B cloud 路径落库实测 `role='ocr_ppsv3'` +
  `provider='paddleocr-vl'`（对抗探针 T7/P4 证实）——role 在冻结枚举内、provider 值不在
  冻结枚举。
- 根因：10 schema 冻结时只列 ppsv3，未冻结 PaddleOCR-VL（VL）对应的 role/provider 值域。
- 处置：段 B cloud 仅在 mock 路径落库 paddleocr-vl 作占位（真实 cloud transport 段 B 未
  接）；真实 live seal 的 role/provider 值待 10 errata 终裁（VL 是否新增 role/provider 枚举
  值，或归并 ocr_ppsv3/ppsv3）。
- 验收：errata 终裁后按最终值域对齐。
- **Resolved（2026-09-08）**：终裁新增独立 `provider='paddleocr-vl'` + `role='ocr_ppsvl'`
  （不归并 ppsv3/ocr_ppsv3）；封闭配对 `ocr_ppsvl ⟺ paddleocr-vl`。防 PPS/PVL 共享 provider
  导致 LE identity 碰撞。代码改动见 Commit C。

### BUG-V3-009 — `get_default_annotation` 最新排序依据未冻结（20 §4.7）
- Status: Open
- 登记：2026-09-06 00:08:31
- 现象：20 §4.7「消费该 source_version 上最新未 superseded 的 valid annotation」，但未定义
  「最新」的排序依据（created_at DESC / id DESC / 其他）。
- 根因：spec 使用「最新」自然语言而未冻结排序字段。
- 处置：段 D `get_default_annotation` 实现用 `created_at DESC` 作**实现冻结**（不声称 Frozen
  Spec 授权）；在代码注释标注「implementation choice for unresolved BUG-V3-009」。errata
  终裁后按最终排序对齐。
- 验收：errata 终裁后按最终语义对齐。
- **Resolved（2026-09-09）**：终裁 M1 **禁止 implicit/default annotation 选择**——所有消费
  annotation 的运行路径必须显式提供 `annotation_id`；不存在「默认最新 annotation」；
  `annotation_id` 缺失/未解析到 valid → fail-fast（RepositoryError），绝不自行查询「最新」。
  原「最新排序依据」命题被显式 id 语义消除。commit `3429671`。

### BUG-V3-010 — `json.loads` 失败时 invalid annotation payload 形态未冻结（10 §5.1）
- Status: Open
- 登记：2026-09-06 00:08:31
- 现象：10 §5.1 `payload JSONB NOT NULL`，但未定义 invalid annotation（LLM 输出非法 JSON）
  的 payload 内容。
- 根因：spec 未覆盖 parse 失败场景的 payload 形态。
- 处置：段 D 落库 `payload={"parse_error": str(exc)}`（NOT NULL 占位，非正文，不触发禁字段
  检查）；登记 bugs.md 待 errata。
- 验收：errata 终裁后按最终语义对齐。
- **Resolved（2026-09-08）**：Closed as Superseded——被 H Phase 7「H0-15 方案 B」覆盖（parse
  失败 → 0 artifact、直接 raise，不再落 invalid 行），本 BUG 的「invalid payload 形态」命题
  已不成立。

### BUG-V3-011 — 段 B seal 未接 figures；OCRFigure 缺 IS-7 字段（20 §4.4/§5.3 image）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：段 B `seal.py` 只 `append_line`，`OCRResult.figures` 未落 `source_figures`；
  `OCRFigure`（ai/ocr/result.py）缺 `placement/object_key/figure_id/figure_hash`，
  不满足 IS-7（10 §4.4「缺 page/bbox/placement/source 任一字段不得写入」）。
- 根因：段 B 骨架未接 figure seal；源料 figure 生产属 B 侧 backlog。
- 处置：段 E image policy 逻辑完整实现（IS-7 过滤 + 唯一→resolve/多→ambiguous/缺→missing），
  用合成 `SourceFigureView` fixture 测正向；生产 `source_figures` 恒空 → 真源路径恒
  ambiguous。补图须走新 source_version（parent_version_id），已 sealed version
  append-only 不回写。E 不反向修改已关闭 B。
- 验收：errata/B 侧 backlog 终裁后，seal 补齐字段计算 + `append_figure` + 计入
  `integrity_hash`。
- **终裁（2026-09-09，BUG-011 Scope Freeze / Errata）**：Frozen Spec 已同步（10 §4.4 / §6.6 /
  20 §5.3 / §7.2.5 / 两册 §12 变更记录）。4 项裁决 + 2 项语义修订：
  ① **placement（D-5）= A**：M1 恒 `standalone` = source-level placement 未定（**非**"图片
  天然独立"）；禁止 E 反向 UPDATE `source_figures`；`figure_refs[].role`（unit-level semantic
  role）与 `source_figures.placement`（source-level）**值域可相同、语义独立、不要求相等**。
  ② **figure_id（D-6）** = `FIG-{page_no}-{ordinal:02d}`；ordinal = canonical visual order
  `(page_no, bbox.top, bbox.left, bbox.bottom, bbox.right, figure_hash, extraction_ordinal)`；
  禁 DB ID/UUID/runtime ID/object_key/figure_hash。
  ③ **figure_hash（D-8）** = `SHA256(raw_image_bytes)`（非 resized/normalized/decoded/
  canonicalized）。
  ④ **object_key（D-7）** = `figure:{figure_hash}`（M1 logical deterministic key，不实现真实
  blob storage；object store lookup 找不到必须 fail-loud，不得据 key 存在断言图存在）。
  ⑤ **Native figures（D-9）= 是**：Native Source Seal（PyMuPDF）必须产 figures（page_no/bbox/
  raw bytes/source=native → figure_hash/figure_id/placement=standalone/object_key），不做
  semantic placement。
  ⑥ **UNIQUE(source_version_id, figure_id)** 立即补（DB 级 identity invariant，非仅应用层去重）。
  ⑦ **IS-7 重定义为完整写入门**（7 字段齐 + deterministic，任一缺失 → 不写 + fail-loud）。
- **执行拆分（顺序：Scope Freeze → Implementation → Contract Tests → Migration → Gate）**：
  BUG-011-A Figure Identity / BUG-011-B Native Figure Extraction / BUG-011-C Seal Figure
  Persistence（IS-7 校验 → append_figure）/ BUG-011-D Integrity Hash（figure_hashes 计入
  canonical 序）/ BUG-011-E DB UNIQUE + migration。
- **BUG-011-E2（记录，不本轮改代码）**：E `_image_span` IS-7 过滤只查 page/bbox/placement/
  source（4 字段），未查 object_key/figure_hash → 跨层 invariant drift（B 写入 7 字段 vs E
  消费 4 字段）。Spec 已区分写入门（10 §4.4 7 字段）与消费资格（20 §5.3 4 字段子集）；E 代码
  对齐留待后续统一处理，不在本轮扩大 BUG-011 范围。
- **Implementation Plan Review 裁决（2026-09-09）**：批准进入 Implementation，4 点 amendment +
  migration 事实核验：
  ① deterministic scope 收紧 —— `extraction_ordinal` 是 provider 在同一 source bytes 上的稳定
  extraction order，仅作 canonical sort key 完全相同时的最后 tie-breaker，非 identity 语义组成；
  invariant =「同一 sealed source version + 同一 provider extraction → deterministic figure_id」，
  不要求跨 provider 相同（figure_id version-scoped）。
  ② Native 提取失败语义 ——「无 image placement」= 合法空集 `figures=()`；「已发现 placement 但
  无法形成完整 figure」= seal failure（产不完整 OCRFigure → IS-7 fail-loud → version 不 sealed）；
  禁 `try/except: continue` 静默丢图。
  ③ bbox 校验收紧 —— 必须验证 `x0/y0/x1/y1` 四键存在且为合法有限数值；不接受 `{}`/`{"x0":1}`/
  `None`/`NaN`（不把「非空 dict」误当「有效 bbox」）。
  ④ migration 0001 事实核验 —— 确证情况 A：0001 用 `Base.metadata.create_all`（动态依赖活 ORM
  metadata），故 from-empty 由 0001 建出约束 → 0009 用 DO block IF NOT EXISTS 幂等模式（复刻 0007）。
  新增 3 条测试 invariant：figure_index 纯函数 `len(ids)==len(set(ids))`；`figure_hash ≠ figure_id`
  （同 hash 异 id 合法）；`object_key == f"figure:{figure_hash}"` 且不出现任何 fake blob infra。
  commit 命名：A=Identity / B=Extraction / C=Persistence+Integrity / E=DB Constraint。
- Status: **Implementation**（Scope Freeze CLOSED → Plan Review CLOSED（4 点 amendment + migration
  情况 A 核验）→ Implementation 进行中，2026-09-09）
- **Resolved / Closed（2026-09-09 05:55）**：BUG-V3-011 → Closed。5 个 atomic commits（docs
  Scope Freeze `5c9ecc9` → A Figure Identity `a8cd129` → B Native Extraction `dd26a6b` → C
  Persistence+Integrity `716875e` → E DB UNIQUE + migration 0009 `9da09db`）；全量 pytest
  **413 passed**；migration replay 双路径 PASS（from-empty 0001 create_all 建约束 +
  incremental 0008→0009 delta == {uq_source_figures_figure_id}）；origin/main == local main ==
  `9da09db`。**BUG-011-E2 保持 Open 独立记录**（E `_image_span` IS-7 消费 4 字段 vs B 写 7
  字段的跨层 drift；Spec 已区分写入门 10 §4.4 7 字段 / 消费资格 20 §5.3 4 字段子集，E 代码
  对齐留待后续统一处理，不随 BUG-011 关闭）。

### BUG-V3-012 — 跨行 ResolvedSpan `text_hash` 拼接规则未冻结（20 §5.5）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：20 §5.5 只写「text_hash 由程序按 span 实际内容计算」，未定义跨行 span 的拼接规则
  （`line1+"\n"+line2` vs 逐行分别 hash）。
- 根因：spec 字段语义未冻结。
- 处置：段 E 采用与段 B IS-4 一致的 `"\n".join(行文本)` 的 raw UTF-8 SHA256 作
  **implementation choice**（代码注释 + 测试标注，不冒充 Frozen 授权）。
- 验收：errata 终裁后按最终拼接规则对齐（升级即走 Rebuild）。
- **Resolved（2026-09-09）**：终裁跨行 text 拼接 = `"\n".join(line.text for line in
  span.line_refs)`（按 `line_refs` **声明顺序**，非行号重排）；拼接符固定单个 `\n`；每行 text
  原样 UTF-8，不 strip/trim/whitespace-normalize；单行 span = 该行 text 本身；`text_hash` 再对
  最终 `text.encode("utf-8")` 计算。commit `878fb10`（含跨行拼接 golden）。

### BUG-V3-013 — blank/image 的 annotation content JSON 形态未冻结（20 §4.5）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：20 §4.5 列 blank/option/answer/image 为 content role，但未给 blank/image 的
  JSON 形态样例（image_ref / blank_label 结构），实现需自行拟定 minimal shape。
- 根因：spec 未冻结这两类 reference 的入参结构。
- 处置：段 E reference 提取按 minimal shape（`content.image.image_ref.figure_id` /
  `content.blank[].blank_label+question_number`）识别，代码注释标注 BUG-V3-013，不冒充
  Frozen 契约；policy 逻辑按 §5.3 规则实现。待 errata 冻结形态。
- 验收：errata 冻结后按最终 shape 对齐。
- **Resolved（2026-09-09）**：终裁 blank/image minimal shape——blank = list（或单 dict），每项
  `blank_label`（必填，unit 内 blank identity）+ `question_label`（可选）；image =
  `{image_ref: {figure_id}}`（figure_id 可选 = `source_figures.figure_id`，version-scoped）；
  malformed shape（非 dict/list、缺 `blank_label`、`image_ref` 非 dict）→ fail-fast（ValueError）
  绝不 silent skip。commit `3bbcf53`。

### BUG-V3-014 — original→canonical 题型别名映射表未冻结（20 §7.2 / DISPLAY_CONTRACT §0.2）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：DISPLAY_CONTRACT §0.2 冻结 12 种 canonical_question_type；但 V2 题型树 code 别名
  → canonical 的映射表未冻结（"single-choice"/"单选题"/"choice_single" 等）。
- 根因：别名表属 V2 资产，V3 未迁。
- 处置：段 F 只做 canonical exact passthrough（原值 ∈ 12 种 → 直通；否则 None →
  incomplete）。禁实现 alias resolver。别名映射待 errata/50 资产清点。
- 验收：errata 冻结别名表后按最终映射实现。
- **Resolved（2026-09-09）**：终裁 canonical 映射 = **exact passthrough**——`original ∈ 12
  canonical → 原样`，否则 `None → incomplete`；**禁 alias resolver**（`single-choice`/`单选题`
  等别名不映射）。commit `ff64352`。

### BUG-V3-015 — LaTeX 符号等价清单未冻结（20 §7.3）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：20 §7.3「LaTeX 等价（数学环境内不换行语义）」未冻结符号等价清单
  （\frac ↔ a/b、\sqrt ↔ root、x^2 ↔ x² 等）。
- 根因：20 §7.3「具体清单随实现评审固化」。
- 处置：段 F identity_normalization 只做数学环境（$...$/\[...\]）内空白/换行折叠；
  不做符号语义等价（那会开始数学语义判断）。
- 验收：errata/评审固化符号等价清单后实现。
- **Resolved（2026-09-09）**：终裁 LaTeX normalization = **structural-only**——`$...$`/
  `\[...\]` 内 `\s+`→`""`（空白/换行折叠）；**不做符号/语义等价**（`\frac{1}{2}`≠`0.5`、
  `x^2`≠`x²`）；canonical identity ≠ mathematical equivalence。commit `a105bf8`。

### BUG-V3-016 — content_roles 的 per-canonical-type role spec 未集中冻结
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：20 §7.2.2「content_roles 按 canonical type 的 role spec 判定」；但 per-type role
  spec 无集中冻结——值域分散在 20 §6.1 standalone 示例（stem required / options
  required_for_choice / answer required / explanation optional）+ DISPLAY_CONTRACT §0.2
  选项要求列（required / 固定2 / not_applicable / 按题型）+ 20 §8.4。
- 根因：示例/要求列未升级为集中 role-spec 契约（F0 核实，不自行推导）。
- 处置：段 F 用最保守可确定实现——stem required / answer required / explanation optional
  通用；options 按 DISPLAY_CONTRACT §0.2「选项要求」映射 required_for_choice
  （single/multiple/true_false）/ not_applicable（fill_in/short_answer/essay）/
  按题型（composite 子结构由内容声明决定）。不扩展未冻结项。
- 验收：errata 集中冻结 role spec 后按最终映射对齐。
- **Resolved（2026-09-09）**：终裁 M1 Role Contract 表冻结（12 型 × 4 role 值域
  {required/required_for_choice/optional/not_applicable}）——options 列
  {single/multiple/true_false}→required_for_choice、其余 9 型→not_applicable；
  stem/answer/explanation 沿用 conservative default（answer=required 为 M1 数据完整性，非
  「无标准答案=not_applicable」）。commit `3cca050`。

### BUG-V3-017 — 2d compiled text_hash 的字节序列未冻结（10 §8 2d）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：10 §8 2d「compiled text_hash == 该 role 确定性编译结果的 hash」，未冻结「确定性
  编译结果」的序列化（compiled text 字符串？canonical JSON？）。
- 根因：spec 字段语义未冻结（防 canonical JSON 冒充 raw，重演 BUG-V3-005）。
- 处置：段 F 2d = 编译文本（compiled text 字符串）的 raw UTF-8 SHA256，非 canonical JSON；
  2c = source raw slice SHA256；两 hash ≠ sha256_hex（identity 键）。
- 验收：errata 冻结序列化后对齐（升级即走 Rebuild）。
- **Resolved（2026-09-09）**：终裁 2d compiled `text_hash = SHA256(text.encode("utf-8"))`
  （raw，**不含 source refs**）；非 canonical JSON。commit `95c1700`（D-2 Spec 终裁）。

### BUG-V3-018 — IR.semantic_status 合法值域未冻结（20 §6.2）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：20 §6.2 不变量 8 只给「semantic_status=ready 才可进入 Compiler；ready 之前任何
  状态都不得进自动准入」，未列 semantic_status 枚举（ready/incomplete/unresolved/…）。
- 根因：spec 用自然语言未冻结值域。
- 处置：段 F 用最小可确定集合 {ready, incomplete}（E 的 ResolvedStatus
  exact/normalized/contextual/fuzzy… 不搬运进 F；三层状态严格区分）。unit_id 缺省或任一
  内容 role 未 resolved → semantic_status=incomplete。待 errata 冻结枚举。
- 验收：errata 冻结后按最终值域对齐。
- **Resolved（2026-09-09）**：终裁 `semantic_status ∈ {ready, incomplete}`（仅此二值）；
  **三层状态严格隔离**——E ResolvedStatus ≠ F semantic_status ≠ G gate_decision/
  decision_status；E 的 ambiguous/missing/fuzzy/contextual 一律坍缩为 `incomplete`，不搬运进
  F；`ready` 仅表示「语义完整可进 Compiler/Gate」，不表示 auto_approve。commit `c6014f7`。

### BUG-V3-019 — options identity serialization order 未冻结（20 §7.3）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：20 §7.3「按 DISPLAY_CONTRACT 固定 role/order/label 序列化」，但 label 固定序未
  明确冻结（选项 A→B→C→D 排序未成文）。
- 根因：identity 规范化策略未冻结（与 BUG-V3-016 同族）。
- 处置：段 F Question dedup_key 的 options 按 **annotation 声明序**序列化（不 sort by
  label——「看起来合理」不授权 Compiler 改 identity）。探针证实同 stem options (A,B) vs
  (B,A) → 不同 dedup（false-split 风险登记，非 false-resolved）。
- 验收：errata 冻结 label 固定序后对齐（升级即走 Rebuild）。
- **Resolved（2026-09-09）**：终裁 options 按 **label UTF-8 字节字典序**（Unicode 码点序）
  排序，与源声明序无关；label 重复 → fail-fast；排序由 Compiler 唯一实现（Admission 复用同一
  纯函数）。commit `878fb10`。

### BUG-V3-020 — image/unsupported content role 在 F IR/Compiler 被静默丢弃
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：annotation 声明 image 且 E 成功 resolve，但 F IR/Compiler 不表示 image 亦不产
  figure_refs → 产出 ready 快照却无图引用（silent data loss）。真实探针：E image
  resolved=True，IR content roles 缺 image，snapshot 无 figures 通道。
- 根因：实现链缺口 + 跨层契约缺口——E image resolved span 不携带 figure_id（仅 evidence）；
  F 无 figure_refs 建模；20 §7.2.5 figure_refs / 20 §9 验收 #5 依赖跨层
  ResolvedSpan↔SourceFigure/IS-7 契约。
- 处置：M1 fail-loud——annotation 声明 F 未建模 content role（image/blank）→
  IR semantic_status=incomplete（绝不静默丢弃、不 guess figure_id、不扫正文、不造
  figure_refs、不转成其他语义 role）。完整 figure_refs/ownership 待跨层契约冻结后支持。
- 验收：errata/跨层契约冻结后实现 figure_refs；M1 保持 fail-loud。
- **Resolved（2026-09-09）**：终裁 figure_refs 跨层契约冻结（M1 只冻结不实现）——
  `figure_refs[] = {unit_id, figure_id, role, order}`；`unit_id` = figure 归属 unit（business
  provenance，非 runtime ID）；`figure_id` = `source_figures.figure_id`（version-scoped）；
  `role` = `source_figures.placement` 值域；`order` = role 内顺序；image ResolvedSpan 携带
  结构化 `figure_id`（text span = absent/null，禁伪造哨兵）。image 通道待 BUG-011 实现前 M1
  保持 fail-loud incomplete。commit `0b0a4d3`。

### BUG-V3-021 — Question/Material subject·grade 确定性来源未冻结（10 §6.1/§6.4 vs 20 §4.2）
- Status: Open
- 登记：2026-09-06 11:50:50
- 现象：10 §6.1/§6.4 subject/grade = 「源自 annotation claim 的确定性映射」；20 §4.2
  `document_metadata_claims` 只是 claim + 上传/文件名优先级（02 §15 未在 10/20 落地）。
- 根因：spec 未冻结 subject/grade 的确定性来源与优先级。
- 处置：段 G M1 保守从 annotation payload 的 `document_metadata_claims.subject/grade` 取；
  null/缺省 → NOT NULL 占位（空串）。不自行实现上传/文件名优先级。待 errata。
- 验收：errata 终裁后按最终来源/优先级对齐（升级即走 Rebuild）。
- **Resolved（2026-09-09）**：终裁 subject/grade = annotation claim **直接映射**；claim 缺失
  → `NULL` = unknown（**绝不用空串**）；删除 V2「上传/文件名优先级」链；Question identity 不含
  subject/grade，metadata 独立于 identity；同 dedup_key 复用：NULL→known 允许、known→same
  no-op、known→different fail-loud（RepositoryError）。commit `3429671` + migration 0008。

### BUG-V3-022 — `input_identity` 各 hash 的精确输入域未冻结（10 §9）
- Status: Open
- 登记：2026-09-06 11:50:50
- 现象：10 §9 只列 input_identity 字段名（source_version_id/annotation_id/
  annotation_payload_hash/resolver_input_hash/compiler_input_hash），未冻结
  resolver_input_hash / compiler_input_hash 的精确输入。
- 根因：spec 字段语义缺精确输入定义。
- 处置：段 G M1 用最小确定性输入——resolver_input_hash = sha256(canonical_json
  (annotation_payload + source_version_id))；compiler_input_hash = sha256(canonical_json
  (per-unit resolved_spans 摘要 + compiled 摘要))；代码标注 BUG-V3-022，不冒充 Frozen。待 errata。
- 验收：errata 终裁后按最终输入域对齐（升级即走 Rebuild）。
- **Resolved（2026-09-09）**：终裁 compile LE `input = annotation_id + annotation payload
  hash + unit_id`（unit_id 为多 top-level unit 区分）；`build_versions`/`input_identity`
  （存储列，完整记录）≠ `contract_domain`/`input_domain`（LE hash，只含决定执行身份的最小
  字段集），二者不可混用。commit `7cf21ba`。

### BUG-V3-023 — 复合/共享选项题型 per-type grammar 未冻结（20 §8.4）
- Status: Open
- 登记：2026-09-06 11:50:50
- 现象：20 §8.4 grammar「由题型子结构决定」，但 cloze/reading/grammar_fill/
  vocabulary_fill/seven_to_five/reading_expression 的 per-type grammar 未冻结（共享选项池
  如 seven_to_five/vocabulary_fill 属「非固定选项关系」，需语义理解）。
- 根因：spec 只冻结首批三种（single/multiple/true_false）grammar 语义。
- 处置：段 G strict-auto 只开放 single_choice/multiple_choice/true_false +
  composite 子题递归（子题 ∈ 三种才判）；共享选项池/未覆盖题型 → pending_review 人工
  （verified_by=human|golden）。待 errata。
- 验收：errata 冻结 per-type grammar 后按最终开放范围对齐。
- **Resolved（2026-09-09）**：终裁 `STRICT_AUTO_TYPES = {single_choice, multiple_choice,
  true_false}`；其余 9 型（fill_in/short_answer/**essay**/cloze/reading/grammar_fill/
  vocabulary_fill/seven_to_five/reading_expression）`grammar=None` → pending_review，**禁止
  编造各自 grammar**；composite 子题递归（子题 ∈ 开放集才 strict grammar，否则 composite
  不自动）。commit `9c1d43f`。

### BUG-V3-024 — Gate 四层逐条检查项未完全冻结（20 §8.1）
- Status: Open
- 登记：2026-09-06 11:50:50
- 现象：20 §8.1 四层给检查类别与关键不变量，但逐条检查项未全冻结——structural
  「granularity/offset 与 role 一致」细则、provenance「contextual 须附 evidence」的 evidence
  形态、semantic「子题 image 归属」= BUG-V3-020 延后。
- 根因：spec 逐条检查未冻结。
- 处置：段 G 用最小可确定检查实现四层（structural：leaf 非空/span 可溯源/题型可解释；
  provenance：text_hash=source slice hash + role resolution_status ∈ {exact,normalized} 才自动、
  contextual 附 evidence、fuzzy/ambiguous/missing 不自动；semantic：composite 依赖完整 +
  闭合 + 材料不重复 + 状态与 IR 一致）；image 归属 M1 走 fail-loud（BUG-V3-020）。待 errata。
- 验收：errata 冻结逐条后按最终检查对齐。
- **Resolved（2026-09-09）**：终裁 Gate 四层逐条检查项冻结（Structural/Provenance/Semantic/
  Admission）；关键分界——`text_hash` 不一致 = byte-level evidence contradiction → `rejected`
  （terminal）；`resolution ∉ {exact, normalized}` = 不能 byte-proven → `pending_review`
  （review downgrade，非 terminal）。commit `b24b5a7`。

### BUG-V3-025 — `review_trail` JSON 结构未完全冻结（20 §8.2）
- Status: Open
- 登记：2026-09-06 11:50:50
- 现象：20 §8.2 给 review_trail 字段 `{decision, verified_by: human|golden, reviewer_id,
  confirmed_fields, time}`，但 time 格式 / confirmed_fields 内容未冻结。
- 根因：spec 字段细节未冻结。
- 处置：段 G M1 用最小结构（append 不覆盖；time = ISO-8601 UTC 字符串；confirmed_fields =
  该次确认的 role/answer 标识列表）。待 errata。
- 验收：errata 终裁后按最终结构对齐。
- **Resolved（2026-09-09）**：终裁 review_trail entry schema——公共字段 `{decision,
  verified_by, reviewer_id, time}`（time 由 `append_review_trail()` 统一注入 UTC ISO-8601，
  调用方不手填）；decision-specific payload 互不共存：approve→`+ confirmed_fields`、
  reject→`+ reasons`（禁止为对齐 schema 制造空字段）。commit `19d236b`。

### BUG-V3-026 — 人工 reject 理由归属 + gate_decision immutability 未冻结（10 §5.2 vs 20 §8.1/§8.2）
- Status: Open
- 登记：2026-09-06 11:50:50
- 现象：(a) 20 §8.2 只明确 Gate 判定的 rejected 写 `gate_decision.reasons`；人工 reject
  理由写 review_trail 还是 gate_decision.reasons 未逐字冻结；(b) gate_decision 语义上 Gate
  写一次、人工只 append review_trail，但未用「immutable」一词要求 DB enforce。
- 根因：spec 证据链归属两处未逐字冻结。
- 处置：段 G M1 人工 reject 理由只进 review_trail（actor=human, action=reject），
  gate_decision 保留原机器判断不覆盖；gate_decision 由 Gate 写入后不 UPDATE（应用层纪律，
  不自行加 DB trigger/RLS，P0-G-001）。待 errata。
- 验收：errata 终裁后按最终归属对齐。
- **Resolved（2026-09-09）**：终裁 `gate_decision` 由 Gate 一次性写入、写后**不可变**；机器
  拒受理由→`gate_decision.reasons`、人工拒受理由→`review_trail.reasons`（append，不覆盖不写
  回，二者不同证据链）；不可变性为 application-layer enforcement（Repository
  `update_candidate_decision` 恒抛 AppendOnlyViolation），**不升级 DB trigger/RLS**。commit
  `5f0d3d0`。

### BUG-V3-027 — Question `dedup_key` 无 DB UNIQUE 约束（10 §6.1）
- Status: Open
- 登记：2026-09-06 11:50:50
- 现象：10 §6.1 仅应用层 exact lookup（dedup 命中 REUSE / 未命中 INSERT）；Question
  `dedup_key` 未声明 DB UNIQUE。并发 approve 两 candidate 同 dedup_key 时，双事务
  「find→none→INSERT」可能产生重复 Question。
- 根因：spec 只冻结应用层去重语义，未给 Question.dedup_key DB 级唯一约束（Instance 的
  `UNIQUE(question_id, source_version_id, occurrence_key)` 已冻结、Question 未声明）。
- 处置：段 G 不自行加 UNIQUE（遵循 A–E 纪律，不擅自改 DB schema）；Instance 唯一由 DB
  constraint 兜底；重复 Question 风险登记待 errata 裁决是否补 UNIQUE。
- 验收：errata 终裁后按最终约束对齐。
- **Resolved（2026-09-08）**：终裁加**全局** `UNIQUE(dedup_key)`（非复合；dedup_key 不含
  source_version/subject/grade，Question 本就跨文档 canonical identity）+ migration 0007
  fail-loud 前置查重。代码改动见 Commit D。

### BUG-V3-028 — 历史 migration full-metadata bootstrap 使 from-empty replay 的 revision ownership 失效（0001/0003）
- Status: Open
- 登记：2026-09-06 23:39:54
- 现象：0001/0003 用 `Base.metadata.create_all(bind)`（全量 metadata）建表。H Step 1 后
  Task/TaskClaim 已注册进 Base.metadata → 在**全新空库**逐步 `upgrade 0001→0004` 实证
  （tests/_audit_h1_migration.py）：0001 一次性建出 24 表**含 tasks/task_claims**（以及
  budget/llm_call_audit），0002/0003/0004 均 `added=[]`。即「tasks/task_claims 由 0004 首次
  创建」只在 A–G 时代**增量库**成立；空库上创建者是 0001。
- 根因：早期 migration 用当前 models 的全量 metadata bootstrap，属「以当前模型为快照」；
  后加入的模型会被**较早 revision** 提前建出 → revision ownership 在 incremental vs
  from-empty 两库间不一致，迁移链不具历史保真，且未来新模型/新列会与「按其 revision 首次
  出现」的预期分叉。
- 处置：**B 语义（用户 2026-09-06 裁决）**——不修改 0001/0003/0004（A–G 冻结基线不动）；
  0004 保持 tables 限定的专责语义（增量库建表，空库可能 no-op）。已补双路径测试
  `test_migration_replay.py`：from-empty 终态 shape == ORM metadata；incremental
  0003→0004 delta == {tasks, task_claims}。Owner = A–G migration history；Resolution:
  deferred（若未来真处理 A 再按 A–G Reconciliation 重审迁移）。
- 验收：from-empty / incremental 双路径测试全绿；0004 专责语义不因空库 no-op 而误导。
- **Resolved（2026-09-08）**：按 B 语义裁决 + deferred 闭合；双路径测试已补；如未来处理 A
  再按 A–G Reconciliation 重审迁移。

### BUG-V3-029 — seal/document 并发幂等无 DB UNIQUE 兜底（H-1，HIGH）
- Status: Open（H Final Closure Blocker）
- 登记：2026-09-07 22:02
- 现象：`SealService.seal_document` 幂等为 read-then-create（`find_document_by_sha256`/
  `find_sealed_version_by_le` 查 None → create），无 DB UNIQUE 兜底。真 DB 并发 probe 实证：两并发
  seal 同文件同 role/provider → 2 document（应 1）；后续 `scalar_one_or_none` 抛 MultipleResultsFound。
- 根因：与 BUG-V3-007（`original_sha256` 与 version 基数未冻结）直接相关——document/version 唯一
  作用域未冻结，故段 B 未加 DB UNIQUE。
- 处置：先终裁 BUG-V3-007（document identity / version identity / 唯一作用域），再决定 DB
  uniqueness key + ON CONFLICT + re-read + 并发 probe。禁随意加 global UNIQUE、禁改 Question/LE/
  occurrence identity。
- **BUG-V3-007 已终裁（2026-09-07）**：唯一作用域 = `original_sha256 + seal role/provider`
  内至多一个 canonical sealed version；跨 role/provider 允许多 version；禁 `UNIQUE(original_sha256)`。
  H-1 修复方向 = 核对 Document/Version schema 现有字段能否表达该作用域（不足则登记 spec gap
  不自行扩展），再加 scoped DB uniqueness + ON CONFLICT + 并发 probe。
- 验收：同 source 并发恰一合法 identity；replay 不产生重复 document/version。
- **Resolved（2026-09-07 Batch 2）**：`documents.UNIQUE(original_sha256)` +
  `document_source_versions.UNIQUE(logical_execution_stage, logical_execution_hash)`（migration
  0006，DO 块 IF NOT EXISTS 双路径安全）；`create_document`/`create_source_version` 改
  `pg_insert ON CONFLICT DO NOTHING` + re-read；`SealService` 并发收敛（re-read sealed → 复用，
  跳过 append/seal）。测试 `test_h_seal_concurrency` 2 项（并发 seal 恰 1 doc + 1 version +
  跨 role 多 version 合法）。

### BUG-V3-030 — 非 dict 合法 JSON 落 valid artifact（H-2，HIGH）
- Status: Open（H Final Closure Blocker）
- 登记：2026-09-07 22:02
- 现象：`validate_annotation_payload` 只做递归禁字段检查，不校验顶层类型；`json.loads("[]")`→`[]`
  → validate 返回 `(True, [])` → `create_semantic_annotation(status="valid")`。真 DB probe 实证：
  `[]` → `status=valid payload=[]`。下游 `payload.get()` 抛 AttributeError，违反 H0-15 方案 B。
- 根因：annotation 校验只查「禁字段」不查「顶层结构」，隐式假设 LLM 输出必为 dict。
- 处置：validator 第一层加 `isinstance(payload, dict)`，非 dict 走方案 B 失败路径（0 artifact）。
  禁自动 JSON repair / LLM 自我纠错 / 大型 schema framework。
- 验收：`[]`/`null`/`"string"`/`123` 全部不进 valid annotation（真 DB probe）。
- **Resolved（2026-09-07 Batch 1）**：`validate_annotation_payload` 顶层加
  `isinstance(payload, dict)`，非 dict 走方案 B 失败路径。测试
  `test_s7_non_dict_json_rejected` 锁死。

### BUG-V3-031 — Resolver 表头判定用非锚定子串误判区界（H-3，HIGH）
- Status: Open（H Final Closure Blocker）
- 登记：2026-09-07 22:02
- 现象：`_qzone_end`/`_answer_span`/`_region_end`/`_explanation_span` 以 `"答案" in norm` 等非锚定
  子串判定 section 区界。题干含「答案」误判——纯函数复现：`"1. 请写出正确答案"` 被当答案表头，
  answer 错指题干行（`exact`），违反「E 可以失败但不能猜」。
- 根因：区界判定用 V2「文本特判」子串匹配，未用冻结的 section-header grammar。
- 处置：先冻结最小 Header Grammar（明确哪些 token 形态是 header：`【答案】`/`答案：` 等），满足
  grammar 才成 boundary，仅含词继续作正文。加 adversarial cases（「请写出正确答案」等）。
- 验收：题干含「答案/解析/详解」不被误判 header；真实 header 仍正确切分。
- **Resolved（2026-09-07 Batch 1）**：冻结 Header Grammar（`is_answer_header`/
  `is_explanation_header`，行首锚定 + 完整 token + 显式白名单），替换 Resolver 6 处
  substring 判定。测试 `test_resolver_header_grammar.py` 39 项锁死。

### BUG-V3-032 — composite shared material contextual 绕过 Gate（H-4，HIGH）
- Status: Open（H Final Closure Blocker）
- 登记：2026-09-07 22:02
- 现象：`GateService` provenance 层只遍历 leaf 的 `_role_spans`，不检查 shared material 的
  `resolution_status`。纯函数复现：材料 `contextual` + 子题 `exact` → `auto_approve`，违反
  「任一 role 为 contextual 不得自动准入」。
- 根因：provenance 白名单漏了 material（leaf 严格、material 缺失）。
- 处置：provenance 统一评估所有物化 role（stem/option/answer/explanation/material），任一
  resolution ∉ {exact,normalized} → auto_allowed=False。加真 DB probe：child=exact + material=
  contextual → NOT auto_approve；material=exact → 保持原行为。
- 验收：contextual 材料不得 auto approve；exact 材料不受影响。
- **Resolved（2026-09-07 Batch 1）**：`policy.evaluate` provenance 层把 shared material
  纳入 resolution 白名单。测试 `test_composite_material_contextual_not_auto` 锁死。

### BUG-V3-033 — HTTP retry 是否计 Provider Invocation（Phase 9 spec gap）
- Status: Frozen for implementation（用户 Phase 9-0 终裁，2026-09-07）
- 现象：`MAX_LLM_CALLS_PER_TASK` 按「真实 Provider Invocation」计数（Lock-4），而 30 §7 说
  HTTP retry「不影响业务语义」——HTTP retry（同一次 provider 调用的传输层重发）是否计新
  invocation，Frozen Spec 未冻结。
- 终裁：**不计新的 Provider Invocation**。一次逻辑 Provider Invocation 可含 N 次 HTTP transport
  attempt；HTTP retry 属同一次 invocation 的传输层重试。HTTP retry 不得产生新 audit invocation、
  不得独立 reserve budget。计数：invocation=1、HTTP attempts=N、MAX_LLM_CALLS=1。
- 验收：Phase 9-2 HTTP retry 实现时，HTTP retry 不增 invocation / audit / budget。

### BUG-V3-034 — HTTP status → error_type 映射（Phase 9 spec gap）
- Status: Frozen for implementation（用户 Phase 9-0 终裁，2026-09-07）
- 现象：40 §6 给 error_type 8 分类，30 §6/§7 未给 HTTP→error_type 映射表。
- 终裁：**transport exception**（httpx ConnectError/ConnectTimeout/ReadTimeout/WriteTimeout/
  NetworkError）→ `LLMNetworkError`（可重试）；**HTTP response error** → `LLMProviderError`。
  状态码：408/429/5xx → ProviderError + retryable；4xx 其他 → ProviderError + non-retryable。
  边界：不得把「provider returned HTTP 500」与「client cannot connect」混为同一 failure
  provenance（前者 ProviderError、后者 NetworkError）。
- 验收：Phase 9-3 异常翻译按此映射；adversarial test 锁定 transport vs HTTP response 分层。
- **对抗审查补充 B-2（2026-09-08）**：冻结的 translation 只覆盖 transport + HTTP status 两类；
  遗漏第三类「HTTP 200 + malformed body」（非 JSON / choices 缺失·空 / message·content 缺失·
  null）→ 已修复：翻译为 `LLMProviderError(retryable=False)`（用户裁决保守分类：HTTP 200 属
  contract violation 非 transient），防裸 IndexError/KeyError/JSONDecodeError 泄漏 + audit
  error_type 误分类 'unknown'。commit `312d1f7`。

### BUG-V3-035 — fallback 触发条件 + provider 列表（Phase 9 spec gap）
- Status: Frozen for implementation（用户 Phase 9-0 终裁，2026-09-07）
- 现象：30 §7 说 fallback explicit（默认关闭）+ 必须审计/预算 + model_config_hash 变 → 新 LE，
  但触发条件 + provider 列表未冻结。
- 终裁：fallback 默认关闭；触发 = primary retryable provider/network failure 且 primary retry
  exhausted 且 fallback enabled 且存在显式 fallback provider；**禁止**触发 = CancelledError /
  parse / validation / forbidden / system / lease / budget / task failure。fallback provider 列表
  必须显式、有限、有序，禁自动发现/随机/动态推断。fallback identity = 新 provider/config →
  新 model_config_hash → 新 LE（X≠Y）。fallback budget：每 fallback invocation 单独计 invocation/
  budget（HTTP retry 不增、fallback 增）。
- 验收：Phase 9-3 fallback 按此语义；X≠Y LE + invocation 计数正确。
- **对抗审查补充 B-1（2026-09-08）**：fallback 未注册 provider 名在 multi-provider 模式下曾
  静默回退 `_live_provider`（primary）→ identity 漂移（audit 记 fallback 名、实际调 primary）
  → 已修复：multi-provider 模式名未命中 → None（fail-closed→GatewayDenied），single-provider
  模式才回退默认（向后兼容）。commit `1e435a9`。

### BUG-V3-036 — Negative retry configuration bypasses execution and can return None
- Status: Open（Phase 9 Closure Reopened / Corrective Patch Pending）
- 登记：2026-09-08
- 现象：`config.py` 的 `llm_request_retry_count` / `http_retry_count` 无 `ge=0` 约束，且
  `LLMExecutor.__init__` / `HTTPLLMProvider.__init__` 不校验构造参数。`LLM_REQUEST_RETRY_COUNT=-1`
  时 executor `range(self._retry_count + 1)` = `range(0)` 零次迭代 → 0 次 Provider Invocation，
  却仍 `finalize_audit(failed, error_type='unknown')` + `settle(actual=0)` + `return None`（违反
  `-> str`）；`HTTP_RETRY_COUNT=-1` 时 `raise LLMNetworkError("LLM transport failed: None")`，
  实际零 HTTP 请求。缺陷链：负值 → 0 迭代 → 执行管线照跑 → audit/budget 语义失真 → None 静默返回。
- 根因：runtime safety config 未 fail-fast——无 Settings 约束、无构造层校验，非法负值穿透进
  有副作用的执行路径，制造「0 真实调用却产生 failed/unknown audit + None 返回」的失真 Runtime
  Truth（违反 V3 Runtime Truth 不变式）。
- 处置：最小双保险——① `config.py` 两 retry 字段加 `Field(ge=0)`（env / Settings 路径 fail-fast）；
  ② `LLMExecutor.__init__` / `HTTPLLMProvider.__init__` 加 `if < 0: raise ValueError`（构造路径
  fail-fast，因构造参数绕过 pydantic）。不捆绑 `max_llm_calls_per_task` / `task_claim_lease_seconds`
  / `worker_concurrency`（单独 errata 硬化）。保留 `retry_count=0` 合法语义（attempts = 1 +
  retry_count）。
- 验收：负 retry 两路径被拒（Settings ValidationError / 构造 ValueError）；0 真实调用 → 0 audit /
  0 budget / 0 provider invocation / 0 None-return；`retry_count=0` → 恰 1 invocation；
  `http_retry_count=0` → 恰 1 attempt。
- **Resolved（2026-09-08）**：`config.py` 两 retry 字段加 `Field(ge=0)`；`LLMExecutor.__init__` /
  `HTTPLLMProvider.__init__` 加 `if < 0: raise ValueError` 构造 fail-fast。+6 test（2 Settings
  validation + 2 构造 fail-fast + 2 retry=0 边界）；全量 350 passed。commit `7ace837`。

### BUG-V3-037 — Live Long-Running Stage Lease Loss（Annotation 阶段持续 Heartbeat）
- Status: Open
- 登记：2026-09-09 13:49:47
- 现象：I-1-D live smoke 实证——真实 Ollama 数据面闭环成功（`audit provider=ollama/
  model=qwen3.5:4b/status=completed`、`budget settled used=1`、`annotation valid=1`），但
  `TaskExecutor._process` 只在 stage 边界续租（`_heartbeat` 三处），annotation stage 内一次
  真实 LLM 网络调用（~300s cold-load）期间无 heartbeat。`task_claim_lease_seconds=60` < 300s →
  lease 在 LLM 调用中途过期 → 调用返回后边界 `_heartbeat` 抛 `LeaseConflict`（`lease_expires_at
  > now()` 条件不满足）→ `_fail_task` 亦 `LeaseConflict` → 打日志 `"lease already lost"` → Task
  卡 `running` 交 recover 置 `interrupted`。下游 Candidate/Gate/Question/Instance=0 为级联失败
  （compile 未跑到），非独立缺陷。
- 根因：`long-running external await exceeds Task Lease without lease renewal`——runtime
  ownership layer 缺「长阻塞 stage 内持续续租」能力（`executor.py` 旧注释早已点名「持续
  heartbeat 属 Phase 9+/live smoke」的 deferred 项）。
- 处置：方案 2（用户裁决，不延长 lease）——新增 `TaskExecutor._lease_heartbeat`
  （`@asynccontextmanager` 后台 renew loop，周期 = `resolved_lease_seconds/4`，严格 < lease），
  `_process` 用 `async with` 包裹 `_annotation_stage` 调用。只做 liveness renewal（复用
  `_heartbeat`，独立 session + commit，DB now() 单源），不改 Attempt/Gateway/Provider/Budget/
  Prompt/Annotation Schema。异常语义（R5）：`LeaseConflict`（lease 真丢失）→ 停循环 + 边界
  fail-loud；其它 `Exception`（瞬时 DB 故障）→ 下一 tick 重试；`CancelledError` → 静默退出。
  `finally` 保证 loop cancel + await，无 orphan。不 cancel 在途 LLM 调用（避免与 BUG-V3-035
  fallback/cancellation 契约交叉）。Compile stage（M1 确定性无 LLM）暂不接入；Cloud OCR 待 I-2。
- 验收：① targeted（test_task_executor.py 18 passed）+ full regression 全绿；② live smoke
  12 层 Hard Gate 全 PASS（Task succeeded + Candidate/Gate/Question/Instance 由 lease 存活而
  跑通 + audit provider=ollama + budget settled + replay 零重复）；③ 新增 5 测试：长 annotation
  保持 lease（lease=1s + LLM 2.5s → succeeded）、lease 被 recover 接管 → 精确 interrupted、
  LLM 异常 → failed 且 heartbeat 清理、CancelledError 传播、`_lease_heartbeat` context 退出后
  loop done()（无 orphan）。
- **Implemented（2026-09-09 14:58）**：lease 修复完成并验证——`_lease_heartbeat` 原语已实装
  （`executor.py`），targeted（test_task_executor.py）18 passed + 全量 pytest **426 passed**
  （零回归）；live smoke 核心层 PASS（Task succeeded / outcome=succeeded / audit ollama
  completed / budget settled / annotation valid / replay 零重复），Task 不再卡 running。**但
  验收②「12 层 Hard Gate 全 PASS」未达成**：Candidate/Gate/Question/Instance 仍 = 0，根因非
  lease，而是 BUG-V3-038（Resolver 字段漂移）+ smoke fixture `[Answer]` 英文表头，级联阻断
  compile。lease 缺陷本体已关闭，全链路验收由 BUG-V3-038 承接。

### BUG-V3-038 — Resolver answer/explanation 字段漂移（question_number vs question_label）
- Status: Resolved
- 登记：2026-09-09 14:58
- 现象：live smoke 修复 lease 后 Task 成功跑到 compile，但 Candidate/Question/Instance = 0。
  定位：真实 Qwen 输出的 answer 用 `question_label`（符合 Frozen Schema + I-0-1 prompt），但
  Resolver `_answer_target` / `_explanation_target`（`reference.py`）读的是
  `answer["question_number"]` → 读到 None → answer 判 `incomplete`（"answer needs
  question_number"）→ 无 candidate。stem/options 的 `_stem_target` / `_option_target` 正确读
  `question_label`，唯 answer/explanation 错。
- 根因：跨层契约漂移。Frozen Schema（20 §4.5 line 169 + line 204-205「术语统一用
  question_label，不用 question_number」）规定 content 角色（stem/options/answer/explanation）
  用 `question_label`；`question_number` 只属 unit 顶层字段。Resolver 对 answer/explanation
  误读了顶层字段名。
- 佐证：mock fixture（`_single_units()` 等）也用 `question_number`，与 Resolver bug 一致，故
  mock 测试「碰巧」通过——正是「Schema Source of Truth ≠ test fixture」要防的漂移。
- 处置（用户裁决 2026-09-09）：① Resolver `_answer_target` / `_explanation_target` 改读
  `question_label`，**禁止 alias fallback**（不写 `data.get("question_label") or
  data.get("question_number")`）；`ResolveTarget.question_number` 数据类字段名保留（E 域内部
  表示，重命名超范围）。② 9 个 mock fixture 文件 content-role 字段迁移
  （`test_gate_service` / `test_ir` / `test_resolver` / `test_compiler` / `test_gate_policy` /
  `test_gate_payload` / `test_admission` / `test_reference_shape` /
  `test_resolver_header_grammar`）；unit 顶层 `question_number` 合法保留。③ 新增 strict
  contract 回归锁 `test_frozen_contract_question_label_only_answer_explanation`：payload 仅带
  `question_label`、全文无 `question_number` → Resolver 必须完整解析 stem/answer/explanation。
  ④ `resolver.py:486` 诊断文案 `"answer needs question_number"` → `"answer needs
  question_label"`。
- 验收（2026-09-09 18:09 全部达成）：targeted（resolver/ir/compiler/gate/admission 等）
  154 passed；全量 pytest **433 passed**；live smoke 12 层 Hard Gate **全 PASS**
  （Task succeeded + Candidate + Gate approved + Question=1 + Instance=1 + audit ollama
  completed + budget settled + replay 零重复）——答案 span 由 incomplete 恢复 exact。
- **Resolved（2026-09-09 18:09:30）**：生产契约 bug 本体关闭。smoke fixture 中文表头 +
  【详解】区属 harness correction（独立 commit），不计入本 BUG 根因。
- 关联（非独立编号）：smoke fixture 第二阻塞——`_SMOKE_LINES` 用英文 `[Answer]`，但 frozen
  `is_answer_header`（BUG-V3-031）只认中文（`答案`/`参考答案`/`【答案】`）。harness 修复 =
  改 `【答案】` + `_make_pdf` 加 `fontname="china-s"`（PyMuPDF 中文渲染）。非生产 bug。第三
  阻塞——模型声明 `explanation` 而源无【详解】区 → Resolver fail-loud 判 missing（行为正确）
  → IR incomplete。harness 修复 = `_SMOKE_LINES` 补【详解】区（用户裁决 A）；同时 prompt
  新增 explanation 源证据约束（用户裁决 B，独立 Prompt Contract 修复，不计入本 BUG）。

### BUG-V3-039 — Diagnostic Metadata Leaks into Compile Identity
- Status: Resolved
- 登记：2026-09-09 18:09:30
- 现象：BUG-V3-038 修复 + smoke fixture 补【详解】后，live smoke 仍 Task failed：
  `error_type=validation_error`，
  `error_detail=float forbidden in canonical identity input (BUG-V3-005)`。真实 Qwen 输出
  unit 顶层 `confidence: 0.98`（float）→ `gate/service.py` 的 `sha256_hex(ann.payload)` 三处
  （`_compile_input_domain` :190、`_input_identity` :206/:208）→ `hashing.canonical_json` →
  `_reject_float` fail-fast → compile stage 抛 ValueError → Task failed，Candidate/Gate/
  Question/Instance 全 0。
- 根因：诊断元数据泄漏进 Compile identity 边界。Frozen Spec（20 §4.5:172 confidence 示例 /
  §8.1:568 / P1-6:768）明确 confidence 是诊断元数据（annotation_meta），**不作 decision
  触发**——因此不应进入 canonical identity。两层危害：① 真实 float 直接击穿 BUG-V3-005
  fail-fast；② 即便规范化为 str，confidence 波动（0.98→0.97）也会改变
  `annotation_payload_hash` → compile LE identity 漂移 → artifact 复用/幂等被诊断噪声破坏。
- 佐证：`backend/tests` 全目录零 `confidence` 字段（Grep 确认）——mock fixture 与真实模型
  输出再次不一致，与 BUG-V3-038 同类的 cross-layer drift，这次落在 identity 层。prompt 示例
  本身写着 `"confidence": 0.98`，是模型照抄来源（已连续两次暴露「示例塑形小模型输出」模式：
  explanation 凭空声明 + confidence float）。
- 处置（用户裁决 2026-09-09，修法 C1）：① 建立**单一** identity projection 边界
  `gate/service.py::_annotation_identity_projection`——仅剔除 `semantic_units[]` 各 unit 顶层
  `confidence` 一个键，其余字段原样保留；不删 unknown fields、不过滤其它 float（BUG-V3-005
  红线不动）；不 mutate 入参。三处 hash 输入全部复用同一 helper，避免「hash A 排除、hash B
  忘排」。② prompt 示例删除 `"confidence": 0.98`（减噪，**不**新增「禁止输出 confidence」
  规则——架构正确性不依赖 prompt 保证数据完美；若模型仍输出 confidence，identity 层已隔离）。
  ③ 不在三处分别 `pop()`；不引入 annotation_meta 重构（未来 schema evolution 另议）。
- 验收（2026-09-09 18:09 全部达成）：新增 5 类回归锁
  （`tests/test_identity_projection.py`）——`confidence_float_does_not_break_compile_identity`
  / `confidence_change_does_not_change_compile_identity`（核心：0.98→0.97 identity 不变）/
  `semantic_change_still_changes_identity` / `other_float_still_fails_fast`（BUG-V3-005 反向
  锁，防「confidence 不进 identity」演化成「identity 自动接受 float」）/
  `confidence_absent_remains_backward_compatible`。targeted 59 passed；全量 **433 passed**；
  live smoke 12 层 Hard Gate **全 PASS**。
- **Resolved（2026-09-09 18:09:30）**：Phase I live data plane 四层阻断全部关闭（I-0-1
  prompt contract → BUG-V3-037 lease → BUG-V3-038 field drift → BUG-V3-039 identity
  leakage）。
- Review scope 提示（非本 BUG 施工范围）：Post-Implementation Gate Review 应专项检查所有
  identity-bearing production path 是否存在「测试 fixture 未覆盖、真实模型可能生成」的字段。
- **Identity Projection Rule（Post-Implementation Gate Review 契约固化，2026-09-09）**：
  ```
  _annotation_identity_projection 仅剔除: semantic_units[*].confidence（unit 顶层）
  不做递归 confidence 剥离。
  不做 unknown-field 剥离。
  不做通用 float 归一化。
  嵌套 confidence=float → BUG-V3-005 fail-fast（红线不动）。
  嵌套 confidence=str  → 参与 identity（精确 boundary 的诚实行为）。
  其余字段按 canonical_json 原规则处理。
  ```
  反向锁：`test_nested_confidence_is_not_silently_projected`
  （`tests/test_identity_projection.py`）。

### BUG-V3-040 — PDF Encoding False Alarm (Windows Terminal Display Issue)
- Status: Resolved
- 登记：2026-09-09 20:30:00
- 现象：Phase I-2 E2E 初始判断 "PyMuPDF 中文编码失败"，显示中文乱码。
- 根因：**Windows 终端编码显示问题**，非 PDF/PuMuPDF 编码失败。文本写入文件（显式 UTF-8）
  后验证完全正常：
  ```
  第1页/共11页
  2026 北京北师大实验中学高一（下）阶段测试一
  一、单选题（每小题4 分，共32 分）
  1. 已知弧长为5π 的弧所对的圆心角为150...
  ```
- 影响：无。Native extraction 正确提取中文文本。
- 修复：无需代码修复。文档修正认知——"不要相信观察层输出，要相信 Source Artifact"。
- **Resolved（2026-09-09 20:30:00）**：经文件写入验证，中文文本完全正常。终端乱码为 Windows
  编码显示问题。

### BUG-V3-041 — Mathematical Layout Fragmentation (Resolver Bottleneck)
- Status: Open / Deferred
- 登记：2026-09-09 20:30:00
- 现象：数学 PDF 中公式/表达式被 native extraction 拆散到多行，Resolver 无法建立语义 span。
- 示例：
  ```
  P1L014: '2. 已知角的终边经过点1'   # 期望：点(1/2, 2)
  P1L015: '1'
  P1L016: ','
  P1L017: '2'
  P1L018: '2'
  ```
- 根因：PDF extraction 输出的是 text stream + font mapping + layout objects，数学公式被
  物理拆分。这是 Mathematical Document Understanding 问题，非 OCR 问题。
- 影响：Resolver 成为 Phase I-2 瓶颈（17 resolved / 85 unresolved）。
- 处置：Phase I-2C Resolver Robustness Validation 专项处理。不做自动修复（错误修复比失败
  更危险）。
- 验收：Resolver 能正确处理布局碎片，或诚实报告 ambiguous/incomplete。

### BUG-V3-042 — PUA False Positive in Source Quality Gate
- Status: Open
- 登记：2026-09-09 20:30:00
- 现象：`_is_non_printable()` 将 Private Use Area（U+F000-U+F8FF, category "Co"）归类为
  不可打印。数学 PDF 用 PUA 编码符号（≥, ≤, →, 向量箭头）。
- 风险：数学密集 PDF 的 PUA 比例 > 10% 时，会被错误标记为 `invalid`，阻断 pipeline。
- 当前状态：本 PDF PUA 7% < 10% 阈值，未触发。
- 修复：修改 invalid 判定条件为 **AND** 逻辑：
  ```python
  if non_printable_ratio > _MAX_NON_PRINTABLE_RATIO and replacement_ratio > 0.01:
      status = "invalid"
  ```
  PUA 单独存在 ≠ quality failure。需 combined with replacement chars 才判 invalid。
- 验收：PUA 20% + replacement 0% → degraded（非 invalid）；PUA 20% + replacement 2% → invalid。

## Resolved Bugs

（暂无。）
