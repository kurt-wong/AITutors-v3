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

### BUG-V3-002 — `document_source_selection_events` 列冻结缺失
- Status: Open
- 登记：2026-09-05 20:31:32
- 现象：10 §4.5 只给语义（旧/新 version、操作人、reason、run_id），未冻结逐列。
- 根因：spec 字段级缺漏。
- 处置：段 A 按 01 v0.3 决策 5 补列（id/document_id/role/old_source_version_id/
  new_source_version_id/operated_by/reason/run_id/created_at）；待 10 errata。
- 验收：实现与该补列一致。

### BUG-V3-003 — embedding 模型名跨文档不一致
- Status: Open
- 登记：2026-09-05 20:31:32
- 现象：50 §3 写 Qwen3-Embedding **0.6B**；ASSET_INVENTORY / DICTIONARY / V2 写
  `qwen3-embedding:4b`（dim 2560）。
- 根因：文档口径不一致。
- 处置：段 A config/.env.example 用 4b/2560；待段 C 前终裁。
- 验收：配置与最终裁决一致。

### BUG-V3-004 — replay 入口措辞不一致（10 §9 vs 30 §2）
- Status: Open
- 登记：2026-09-05 20:31:32
- 现象：10 §9 `python -m v3 replay` vs 30 §2 `python -m app.worker run`。
- 根因：包名 v3/app 未统一（已由用户裁决包名 `app`）。
- 处置：段 A 全用 `app`；replay 实装（段 H）用 `python -m app.cli replay`；10 §9 措辞待
  errata。
- 验收：CLI 入口与包名裁决一致。

### BUG-V3-005 — canonical_json 浮点 precision 位数未冻结
- Status: Open
- 登记：2026-09-05 20:31:32
- 现象：30 §16 写「浮点按定长十进制格式化」，未冻结 precision 位数/格式化算法。
- 根因：spec 数字规范缺位数。
- 处置：段 A 用 `repr(float)` 作临时 deterministic representation（不代表冻结解释）；当前
  LE hash 身份输入不含 float，不阻塞。待 30 §16 终裁。
- 验收：终裁后 utility 版本递增 + 走 Rebuild。

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

### BUG-V3-010 — `json.loads` 失败时 invalid annotation payload 形态未冻结（10 §5.1）
- Status: Open
- 登记：2026-09-06 00:08:31
- 现象：10 §5.1 `payload JSONB NOT NULL`，但未定义 invalid annotation（LLM 输出非法 JSON）
  的 payload 内容。
- 根因：spec 未覆盖 parse 失败场景的 payload 形态。
- 处置：段 D 落库 `payload={"parse_error": str(exc)}`（NOT NULL 占位，非正文，不触发禁字段
  检查）；登记 bugs.md 待 errata。
- 验收：errata 终裁后按最终语义对齐。

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

### BUG-V3-012 — 跨行 ResolvedSpan `text_hash` 拼接规则未冻结（20 §5.5）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：20 §5.5 只写「text_hash 由程序按 span 实际内容计算」，未定义跨行 span 的拼接规则
  （`line1+"\n"+line2` vs 逐行分别 hash）。
- 根因：spec 字段语义未冻结。
- 处置：段 E 采用与段 B IS-4 一致的 `"\n".join(行文本)` 的 raw UTF-8 SHA256 作
  **implementation choice**（代码注释 + 测试标注，不冒充 Frozen 授权）。
- 验收：errata 终裁后按最终拼接规则对齐（升级即走 Rebuild）。

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

### BUG-V3-014 — original→canonical 题型别名映射表未冻结（20 §7.2 / DISPLAY_CONTRACT §0.2）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：DISPLAY_CONTRACT §0.2 冻结 12 种 canonical_question_type；但 V2 题型树 code 别名
  → canonical 的映射表未冻结（"single-choice"/"单选题"/"choice_single" 等）。
- 根因：别名表属 V2 资产，V3 未迁。
- 处置：段 F 只做 canonical exact passthrough（原值 ∈ 12 种 → 直通；否则 None →
  incomplete）。禁实现 alias resolver。别名映射待 errata/50 资产清点。
- 验收：errata 冻结别名表后按最终映射实现。

### BUG-V3-015 — LaTeX 符号等价清单未冻结（20 §7.3）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：20 §7.3「LaTeX 等价（数学环境内不换行语义）」未冻结符号等价清单
  （\frac ↔ a/b、\sqrt ↔ root、x^2 ↔ x² 等）。
- 根因：20 §7.3「具体清单随实现评审固化」。
- 处置：段 F identity_normalization 只做数学环境（$...$/\[...\]）内空白/换行折叠；
  不做符号语义等价（那会开始数学语义判断）。
- 验收：errata/评审固化符号等价清单后实现。

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

### BUG-V3-017 — 2d compiled text_hash 的字节序列未冻结（10 §8 2d）
- Status: Open
- 登记：2026-09-06 09:09:16
- 现象：10 §8 2d「compiled text_hash == 该 role 确定性编译结果的 hash」，未冻结「确定性
  编译结果」的序列化（compiled text 字符串？canonical JSON？）。
- 根因：spec 字段语义未冻结（防 canonical JSON 冒充 raw，重演 BUG-V3-005）。
- 处置：段 F 2d = 编译文本（compiled text 字符串）的 raw UTF-8 SHA256，非 canonical JSON；
  2c = source raw slice SHA256；两 hash ≠ sha256_hex（identity 键）。
- 验收：errata 冻结序列化后对齐（升级即走 Rebuild）。

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

### BUG-V3-021 — Question/Material subject·grade 确定性来源未冻结（10 §6.1/§6.4 vs 20 §4.2）
- Status: Open
- 登记：2026-09-06 11:50:50
- 现象：10 §6.1/§6.4 subject/grade = 「源自 annotation claim 的确定性映射」；20 §4.2
  `document_metadata_claims` 只是 claim + 上传/文件名优先级（02 §15 未在 10/20 落地）。
- 根因：spec 未冻结 subject/grade 的确定性来源与优先级。
- 处置：段 G M1 保守从 annotation payload 的 `document_metadata_claims.subject/grade` 取；
  null/缺省 → NOT NULL 占位（空串）。不自行实现上传/文件名优先级。待 errata。
- 验收：errata 终裁后按最终来源/优先级对齐（升级即走 Rebuild）。

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

### BUG-V3-025 — `review_trail` JSON 结构未完全冻结（20 §8.2）
- Status: Open
- 登记：2026-09-06 11:50:50
- 现象：20 §8.2 给 review_trail 字段 `{decision, verified_by: human|golden, reviewer_id,
  confirmed_fields, time}`，但 time 格式 / confirmed_fields 内容未冻结。
- 根因：spec 字段细节未冻结。
- 处置：段 G M1 用最小结构（append 不覆盖；time = ISO-8601 UTC 字符串；confirmed_fields =
  该次确认的 role/answer 标识列表）。待 errata。
- 验收：errata 终裁后按最终结构对齐。

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

## Resolved Bugs

（暂无。）
