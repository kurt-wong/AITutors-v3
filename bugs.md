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

## Resolved Bugs

（暂无。）
