# Phase 0 变更范围与验收清单

Version: PHASE0-0.3
Status: Phase 0 冻结基线（有条件通过）；Phase 1 样本/Phase 5 grammar 为条件项
Date: 2026-09-04
目的：把“权威文档同步 + v0.3 契约修正 + golden/测试/性能验收”做成同一次 Phase 0
冻结交付，避免新会话只读 PIPELINE/DSD 后按旧链实施。

## 1. 权威文档变更范围表

| 文档/章节 | 动作 | 变更范围 | 兼容策略 |
|---|---|---|---|
| PIPELINE §0.0 | 新增 | 新链唯一入口与最高优先级声明；Annotation 禁 line_ref/corrected_line_ids/resolved_span | §0 高于旧正文 |
| PIPELINE §1.1 | 改 | 标为旧链 legacy 教训，LLM 输出行号/锚点校正不再是 active 路径 | 保留历史 |
| PIPELINE §3-4 | 改 | 标题/正文标 `[LEGACY]`；新增新链阶段映射 | 旧链只作诊断参考 |
| PIPELINE §4.4 | 废弃 | LLM stem_lines/options_lines/answer_lines/explanation_lines 的 active 描述改为已废弃路径 | 删除 active 引用 |
| PIPELINE §8-10 | 改 | 目标源码结构/表格/PP 主路径标记为 legacy，新链源码边界由 v0.3 契约指定 | 保留历史 |
| DSD §4.3 | 改 | documents 三列 native/ocr/llm 标 legacy 只读镜像；规划 source_version_id 等 provenance 字段 | 保留兼容 |
| DSD §7 | 替换 | 删除“L1/L2 不落库”；改为 sealed Source Version + Annotation/Resolver/IR 可审计落库 | 新表为未来 migration |
| DSD §4.25-4.35 新增 | 新增 | source version/line/image/active/selection/annotation/resolver/IR/table/cell/fragment 表 | 独立新表，未 migration |
| DSD questions/instances/candidates | 改 | 增加 provenance id 字段；candidate 状态模型统一，旧 gate_decision 标 legacy | 不破坏现有 API |
| DSD §8.4 | 改 | question_annotations 独立表从“暂不建”改为 Phase 1-2 计划 | 与旧 llm_annotated_markdown 并存 |
| DICTIONARY §4 | 改 | 新增语义管线术语；旧 Line-range/Anchor 概念标 legacy | 旧词可查但不可用于新链 |
| DICTIONARY §7 | 改 | 统一 admission_status 为 approved/candidate/rejected；列出到 DB 状态映射 | 旧枚举 legacy |
| ACS §5.1-5.3 | 改 | 本轮列明端点范围，不实现；approve/reject 必须带 source/annotation/resolver id | 保持兼容 |
| ACS parse-result/review | 改 | 增加 provenance 字段说明 | 不改变现有响应结构 |
| 00/02/03 v0.3 | 改 | 本清单第 3 节契约修正 | 保留 v0.2 历史 |
| PROJECT_STATUS/RESTART_PROMPT | 改 | 旧链历史冻结；恢复流程先读 v0.3 再读权威文档 | 快照归档 |
| rules.md | 改 | 新增文档入库语义管线 active 规则；V1 行号规则标 legacy | 旧规则仅供历史 |
| SAD.md | 改 | P8/制品分层/文档入库工作流改为 v0.3；旧 L1/L2 行号段标 legacy | 保留旧架构历史 |
| 01/03 | 改 | Source Index 增加 table/cell/fragment；Allowed-Answer Grammar 前置 DoD | 与 DSD planned 表一致 |

## 2. 已否决的 Phase 0 做法

- 先批准 v0.3、之后另开会话同步权威文档。
- 只改 `Docs/02_Architecture/PIPELINE.md` §0，不降级 §1.1/§3/§4.4/§8-10。
- 让权威 DSD 继续保留“L1/L2 不落库”。
- 让 DICTIONARY 继续用 Line-range/Anchor 作为新链工作语言。
- 用旧 verified=True、旧 answer_extractor 子串回查支撑新链 approved。

## 3. 最小 Golden 清单

下表为 Phase 1-6 的最小真实样本。所有文件必须存在于仓库或作为待补清单显式标出。

| 样本 | 覆盖场景 | 预期通过标准 |
|---|---|---|
| `test/pdf/2026北京东城高一（上）期末英语（教师版）.pdf` + `test/fixtures/l1_native_english_dongcheng_2026.json` + `test/annotations/golden/english_2026_dongcheng_real_golden.json` | 完形/语法填空/七选五/阅读表达/写作；材料与子题；答案表 | source seal 可回放；Annotation 无行号；IR ready；材料不复制；答案三字段分开；与 golden 内容一致 |
| `test/pdf/2026北京朝阳高一（上）期末数学（教师版）.pdf` + `test/fixtures/l1_native_math_2026.json` + `test/annotations/golden/math_2026_chaoyang_contract_golden.json` | 独立选择题、解答题、公式/LaTeX、多小题 | canonical_question_type 由 Compiler 产出；长题干/公式 span 不截断；无共享材料误并 |
| `test/pdf/2026北京八十中高一（上）期末化学（教师版）.pdf` + `test/fixtures/l1_native_chemistry_2026_bashi.json` + `test/annotations/golden/chemistry_2026_bashi_contract_golden.json` | 表格选项、化学式、答案表 | table_cell/line_character span 可回放；答案单元格完整；无 LLM 正文输出 |
| `test/pdf/2026北京朝阳高一（上）期末语文（教师版）.pdf` + `test/fixtures/l1_native_chinese_2026_chaoyang.json` + `test/annotations/golden/chinese_2026_chaoyang_contract_golden.json` | 文言文/注释/材料题/递归子问 | shared_material 唯一；材料与子题 span 不重叠；递归子题映射闭合 |
| `test/pdf/2026北京朝阳高一（上）期末物理（教师版）.pdf` + `test/fixtures/l1_native_physics_2026.json` + `test/annotations/golden/physics_2026_chaoyang_contract_golden.json` | 多小题、图题、解题过程/答案区 | image ref 完整；答案来源与解题过程分离；verified_correct 不来自 LLM |
| 待补充：真实 60 页以上 PDF | seal 性能验收 | 本清单第 5 节性能门槛 |

## 4. 测试迁移策略

### Phase 1

- 保留现有全部后端 pytest，作为旧链回归和兼容回归。
- 新链 Phase 1 source repository 测试独立放
  `backend/tests/semantic_pipeline/source/`。
- 不删除旧测试，不把旧测试 import 到新链核心模块。

### Phase 2

- 旧 L2/slicer/gate 相关测试仍可运行，但标记/归档为 legacy：
  - 文件级：不在本次改目录；Phase 2 实施时新建
    `backend/tests/legacy/document_pipeline/` 并移动相关测试，或使用 marker
    `@pytest.mark.legacy_document_pipeline`。
  - 新链 Annotation/Resolver/IR/Compiler/Gate 测试放
    `backend/tests/semantic_pipeline/`。
- 禁止新链代码从旧 `line_annotator/anchor_corrector/content_slicer/quality_gate/
  admission_gate` import 作为核心路径。

### Phase 6

- 仅在新链 golden 通过且旧链不再作为 active 后才允许清理/归档旧测试。
- 清理必须写入 LOG，并保留旧测试存档目录或快照。

## 5. Seal 性能验收

目标：用真实长文档验证 hash、事务与内存，不让 Phase 1 在“短文档能过，60 页 OOM/超时”
后才被发现。

当前 `test/pdf/` 没有 60 页以上真实教师版 PDF，因此必须补充一份；若暂时无法补充，
Phase 1 DoD 只能部分满足，不得进入 Phase 2。

最低门槛：

| 指标 | 门槛 |
|---|---|
| 文档 | 真实教师版 PDF，≥60 页，含文字层或可 OCR 页 |
| 确定性 | 同一 source 两次 seal 的 body_hash/integrity_hash 完全一致 |
| 时长 | body_text 重建 + body_hash + integrity_hash ≤ 30s；事务整体 ≤ 60s（本地开发机） |
| 内存 | seal 过程不 OOM，峰值 RSS 需记录；后续按实际机器设置告警阈值 |
| 事务 | 中途失败不留半成品；回滚后可重试 |
| 日志 | 记录 line_count/page_count/hash 耗时/峰值内存 |

### 5.1 Allowed-Answer Grammar 前置 DoD

严格自动 `verified_correct=true` 是 Phase 5 能力，不是 Phase 0 隐藏条件；但 Phase 5
DoD 必须先交付：

- DISPLAY_CONTRACT 或独立 Answer Grammar 文档定义 canonical_question_type →
  content_roles → allowed answer grammar。
- 首批 grammar 覆盖 single_choice、multiple_choice、true_false；
  fill_in/short_answer/writing 在本阶段不开放 strict auto verified_correct。
- Phase 5 第一项是补 DISPLAY_CONTRACT 的 true_false T/F 或 A/B canonical 映射，
  不能只声明 grammar 存在。
- grammar 必须附 golden 正例/反例，并由评审确认；没有 grammar 的题型不得走严格
  自动 approved。

## 6. 评审口径记录

本文件先落实用户最终意见中的六组必改项及四项额外交付物。

如果“Claude 12 项”以独立清单存在，应追加到本文件或作为评审附件入库；当前仓库
未找到该清单文件，因此无法声称已逐项核对。用户列出的阻塞项全部纳入：

- Phase 0 文档冻结必须与权威文档同步完成。
- 旧链语言不得继续作为 active 指引。
- 源/Annotation/Resolver/IR 持久化结构必须在 DSD 落定。
- 契约内部行内粒度、递归、role 必填、状态、marker、verified_correct 需明确。
- 状态文件必须把旧链历史冻结。
- 需要输出变更范围表、golden 清单、测试迁移策略、seal 性能验收。

## 7. 综合审核阻塞项追踪（追加到本文件）

| 阻塞 | 结论 | 修复位置 | 状态 |
|---|---|---|---|
| rules.md/RESTART 恢复入口仍含旧行号规则 | 标 legacy，新增 Semantic Annotation active 规则 | rules.md、RESTART_PROMPT.md | 已修 |
| SAD 仍整体是旧行号架构 | P8/制品分层/工作流/治理改为 v0.3 | SAD.md | 已修 |
| source index 不支持 table_cell/fragment | 01/DSD 新增 tables/cells/fragments，纳入 integrity hash | 01 v0.3、DSD 4.33-4.35 | 已修 |
| question_candidates 新旧状态混写 | approved→questions、candidate→candidates、rejected 删除/审计 | DSD 4.24、DICTIONARY §7、ACS | 已修 |
| verified_correct 自动路径缺 allowed-answer grammar | 定义为 Phase 5 前置 DoD，首批题型范围明确 | 03 §13.1、04 §5.1 | 已修 |
| 60 页 seal 样本缺失 | 不阻塞 Phase 0，但 Phase 1 DoD 不完整 | 04 §5 | 待补样本 |
| Claude 12 项独立清单未入库 | 需要文件路径后追加逐条核对 | 04 §6/§7 | 待提供 |
