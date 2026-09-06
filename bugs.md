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

## Resolved Bugs

（暂无。）
