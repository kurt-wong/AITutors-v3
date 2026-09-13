# AI Tutor V3 — RESTART PROMPT

Version: v1.42
Status: **Gate B2-A 三项补强完成** —
Gate C CLOSED (Phase 1) + Gate B2-A three-task audit PASS；
下一步：Gate B2-B（结构化内容定位）
Date: 2026-09-13

## 0.0 当前结论（2026-09-13 Gate B2-A 三项补强完成）

- **Gate B2-A: PASS / TEST-EVIDENCED（stem-only, three-task audit）**。
  - Task A: 20 Legacy-only cases 全部为 pattern coverage gap，非验证错误。
  - Task B: 150 抽样中 96% 标准题号格式，验证结果可信。
  - Task C: Legacy 47.1% vs Path B 96.8%，+49.7pp，2.1x coverage。
- **Gate C CLOSED（Phase 1 Evidence Authority Boundary Closure）**。
- **Evidence Validity ≠ Semantic Correctness**。
- **下一步 = Gate B2-B**：结构化内容定位（option/answer table/fill-in/HTML table）。

- **A–G / H Phase 1–8 / Phase 9 / Errata 维持 FINAL CLOSED**。
- **Phase I-3 CLOSED**：Source Evidence Preservation Layer。
- **Phase I-4 CLOSED**：Valid Negative Result——layout evidence 消歧率 0%。
- **Phase I-5 进行中**：I-5-0 → I-5-1 → 盲测 → 68/69 号 → 对抗性审查 →
  P0 Closure Pack → Step 3 裁决 → **Gate A 关闭（本轮）**。
- **Gate A（Identity Closure）**：**PASS / TEST-EVIDENCED**。
  - 三层 Identity 模型：Semantic Identity / Source Binding Claim / Resolved Evidence。
  - 核心结论：line_refs 属于 Source Binding Claim，不属于 Semantic Identity。
  - `_annotation_identity_projection` 剔除 `{confidence, line_refs}`；
    `_confidence_only_projection` 仅剔除 `{confidence}`（供 resolver_input_hash）。
  - 4 个新增 A1/A2 测试 + call-site audit + 514/514 regression。
- **状态基线（2026-09-11）**：
  - Architecture Design: **PASS WITH RESERVATIONS**
  - Core Safety Model: **PASS**
  - Local Invariants: **PASS / TEST-EVIDENCED**（514/514）
  - Cross-Boundary Invariants: **PASS / TEST-EVIDENCED**
  - Admission Atomicity: **PASS**；Admission Concurrency: **PASS — 10/10**
  - Test Isolation: **PASS / TEST-EVIDENCED**
  - Resolver Algorithm Safety: **PASS**；Resolver Real-World Coverage: **FAIL — 16.7%**
  - Path B → IR/Compiler: **PROVEN — 21/21**；→ Gate/Admission: **NOT YET PROVEN**
  - 67 Contract Change: **CONDITIONALLY ACCEPTED**（Gate A PASS；Gate B CONDITIONAL；Errata BLOCKED BY Gate B/C）
  - OQ-1: **CLOSED**；OQ-2/OQ-3: **OPEN**
  - Full Production Pipeline: **NOT YET CLOSED**
- **Gate B1 修正后结果（2026-09-11，79 cases / 10343 role targets）**：
  - **旧 FAIL 裁决作废**：基于两个实验缺陷（读错源文件 + validator 过度严格）
  - Range Validity: **PASS**（100%）
  - Content Validity: **PASS WITH RESERVATIONS**（79.0%）
  - Role Validity: stem **97.3%** / explanation **96.7%** / option **51.8%** / answer **49.1%**
  - **Gate B1 = CONDITIONAL PASS / Corpus Substantially Valid**
  - 剩余问题：option region 语义（逐行拆分产生空 target）+ answer 共享答案表 contract
  - **Gate B2-A 允许开始**（stem + explanation）；B2-B BLOCKED BY contract 裁决
  - **禁止继续放宽 validator 提升数字**——那是 metric optimization
- **Contract Adjudication（2026-09-11 完成）**：
  - Q1 = A：`options_lines` 是 Options Region，逐行拆分是 harness bug
  - Q2 = B：共享答案表需 per-question evidence，Source region ≠ Question answer evidence
  - Q3 = B：`answer_lines` 保持单一 Source Region，行内多答案需 subspan/offset
  - Q4 = B：HTML table answer 绑定到 cell/row，整个 table 是上层 Region
  - **统一原则：Source Region 与 Question Evidence 必须分层**
  - Region Binding 基本成立；Structured Evidence Binding 需 manifest schema 增强
  - **不修改生产 V3**——先实验验证语义能否在真实 corpus 上稳定表达
- **Gate B2-A 结果（2026-09-11，79 cases / 2750 B1-clean targets）**：
  - **Gate B2-A = PASS / TEST-EVIDENCED**（结论范围仅限 stem）
  - Stem: Legacy 829/1870 (**44.3%**) vs Path B 1820/1870 (**97.3%**)
  - Agreement: Both OK 814 / Legacy only 15 / Path B only **1857** / Neither 64
  - **核心证明**：把"搜索问题"变成"验证问题"——Doc 67 的架构变化方向正确
  - Explanation: 0% 是 capability absence，不是 comparative failure，不纳入对比
  - **结论边界**：不证明 Path B 语义正确率 97.3%（需独立抽样验证）；
    不证明 Path B 在所有 Question Roles 上优于 Legacy
- **红线（不变）**：HTTP retry ≠ LLM retry ≠ fallback；先冻结 Spec 再改代码；
  Schema Source of Truth = 20_Document_Pipeline.md；Resolver 不猜；
  实验结果 ≠ 实施授权；提议修改 ≠ 违反 Frozen Spec。
- **下一步（按序执行）**：
  1. **Gate B2-B**：结构化内容定位（option/answer table/fill-in/HTML table）
  2. **Phase 2 Evidence Ledger**：等真实 pipeline 压力出现后再启动
  4. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决
  5. **Errata Decision**（Gate B/C/D 通过后）
  6. **I-5-2 Adapter**（Gate D 约束：Contract Translator，非 Semantic Resolver）
  7. **Path B Full Closure E2E**（含 Provenance Golden Test + Replay 验证）
- 重启后第一任务：读本文件 → Status.md 尾 → log.md 尾 → bugs.md →
  按上述 Step 顺序执行。

## 1. 用途

Codex/Claude 重启后先读本文件恢复上下文。本文件只承载稳定信息：项目目标、基线状态、
强制规则、文档地图、恢复流程；最新状态细节以 `Status.md` / `log.md` 为准。
**更新约定（规则二）**：`0.0` 节结论每次更新带当前时间戳，
在对应小节下记录最近更新时刻。

## 2. 项目目标

从 V2 继承业务需求并**全量重写**（V2 需求见 `Docs/00_Requirements/
REQUIREMENTS_AND_SOLUTION.md`）：批量上传教师版 PDF/DOCX → 自动提取题目/配图/答案/
详解/元数据；题库统计分析；AI 生成题（延后）；错题本；个性化练习。V3 目标 = 杜绝
V2 的「LLM→文本→特判→Gate→回填」模式，以 Source 为唯一事实源、stage-scoped 幂等、
Replay 可重建。

## 3. 强制规则（摘要，权威在六册）

- 单主链：不建第二条 pipeline；状态只经唯一入口（decision_status → approve()/reject()）。
- Live 是组合放行：LLM/cloud OCR 须 live mode + `--allow-live` + task + budget 同时成立。
- LE key = `{task_type, stage, contract_domain, input_domain}`（不含 task_id）。
- 预算五账户正交、禁父子树；Recovery ≠ Retry；Worker 崩溃不自动重跑。
- 实现顺序、测试层级、DoD、评审红线：`40`；资产/Golden：`50`。
- **H 段**：LLMExecutor 唯一入口、Domain 不依赖 Gateway、Attempt 不可恢复续跑、Runtime/Business
  Identity 隔离（详见 plan 文件）。
