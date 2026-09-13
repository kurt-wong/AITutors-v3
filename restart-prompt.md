# AI Tutor V3 — RESTART PROMPT

Version: v1.39
Status: **Evidence Promotion Phase 1 Hardened + HIGH Fix** —
AppendOnlyEventLog (__slots__ + name mangling + state machine in append())；
全量 640 passed；Gate B2-A 仍 pending 三项补强
Date: 2026-09-13

## 0.0 当前结论（2026-09-13 Phase 1 Hardening 关闭）

- **Evidence Promotion Contract Phase 1 Hardened**：
  - AppendOnlyEventLog: `__slots__` + name mangling (`__events`) + state machine in `append()`
  - GateService: per-run isolation + reference_ids linking + ProposerIdentity=llm
  - CheckResult 结构化检查替代叙述性字符串
  - validation_method 从 gate layers 推导
- **HIGH 严重性缺陷（第二轮）已修复**：
  - HIGH-1: `log._events = ()` → AttributeError（__slots__ + name mangling）
  - HIGH-2: 直接 `log.append()` → ValueError（状态机在 ledger 层）
- **全量测试：640 passed**
- **下一步**：C-2 157 E2E → Gate C Closure
- Gate B2-A 仍 pending 三项补强（审计 15 个 Legacy-only case + 独立抽样 + 排除 explanation）

## 0.1 上一轮结论（2026-09-11 Gate A 关闭）

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
  1. **B2-A 三项补强**：
     a. 审计 15 个 Legacy-success / Path-B-failure cases（逐个分类）
     b. 独立抽样验证 Path B 成功结果（1820 个中抽 100-200 个）
     c. 正式报告中把 explanation 从 comparative metric 中排除
  2. **Gate B2-B**：结构化内容定位（option/answer table/fill-in/HTML table）
  3. **Gate C**：Safety Invariant Preservation 验证
  4. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决
  5. **Errata Decision**（Gate B/C/D 通过后）
  6. **I-5-2 Adapter**（Gate D 约束：Contract Translator，非 Semantic Resolver）
  7. **Path B Full Closure E2E**（含 Provenance Golden Test + Replay 验证）
- 重启后第一任务：读本文件 → Status.md 尾 → log.md 尾 → bugs.md →
  按上述 Step 顺序执行。

## 0. 当前工作状态（2026-09-08 14:01）

- **已完成（A–G 七段关闭）**：`Docs/V3_SPEC/` 六册 + README 冻结；段 A（config/DB 19 表/
  Repository/hashing）、段 C（Gateway/audit/budget external 闸）、段 B（Source Seal + OCR）、
  段 D（Annotation）、段 E（Source Resolver）、段 F（IR + Compiler）、段 G（Gate + Admission
  + Grammar）全部关闭。完整 pytest 201 passed ×2。
- **段 G 已关闭（实现要点）**：Gate 四层 gate_decision + 冻结可重放 payload + AdmissionService
  物化事务唯一入口 + GateService LE 幂等编排 + auto approve/reject。二轮对抗审查 F1/F2 修复
  （commit 8a57a92）：F1 unit_groups.unit_type 从 candidate（A 域值）；F2 instance LE provenance
  从 candidate 原样继承。
- **H0/H 进展（本轮）**：
  - H0 Runtime Readiness Audit 落盘（commit 8032af3）；R1 五项（attempt_id 缺失 / 并发幂等写
    / retry 熔断 / Execution Wrapper / tasks·task_claims）+ R2 两项（compile 指纹口径 /
    invalid annotation 归属）。
  - H Contract Reconciliation 五条裁决：① H0-2 维持 M1；② H0-15 方案 B；③ H0-3 attempt 由
    Task Executor 分配；④ H0-6 ON CONFLICT 幂等写；⑤ H0-7 LE→Attempt→bounded retry。
  - H Implementation Plan Final 冻结（6 Locks + 4 Notes + 3 Clarifications + Step 1–7）。
- **BUG 登记状态**：BUG-V3-001..020 Open（A–F 遗留）；BUG-V3-021..027 已写入 bugs.md（G 相关）。
  F1/F2 与 G 对抗 4 项为已修复实现 bug，不入 bugs.md 编号。
- **当前要执行**：待用户裁决下一 Phase 范围（新的功能 / Bug 阶段）；BUG-011-E2 延续为独立记录
  （后续统一处理）。
- **当前不要执行**：不重复执行 D-1 至 D-6；不重新施工 BUG-011（已 Closed）；不把
  `_audit_*.py` 混入 main（已归档 `_audit_archive/`）；不实现 Similarity / occurrence
  analytics / answer-evidence schema；不自行开启新 Phase（待用户裁决）。
- **关键文件**：
  - `~/.claude/plans/giggly-enchanting-volcano.md` — H 实施计划（唯一实施指令，含全部 Lock/Note/Clarification）
  - `Docs/reference/H0_RUNTIME_READINESS_AUDIT.md` — H0 审计资产
  - `Docs/V3_SPEC/30_Task_LLM_Safety.md` — H 运行时契约（Task 状态机/claim/retry/audit/budget）
  - `Docs/V3_SPEC/10_Data_Model.md` — A/B/C 域数据（Question/Instance/dedup/occurrence）
  - `Docs/V3_SPEC/40_Development_Rules.md` — A-I 顺序与出口闸
- 详细状态见 `Status.md` 与 `log.md`。

## 1. 用途

Codex/Claude 重启后先读本文件恢复上下文。本文件只承载稳定信息：项目目标、基线状态、
强制规则、文档地图、恢复流程；最新状态细节以 `Status.md` / `log.md` 为准。
**更新约定（规则二）**：`0.0/0` 节结论每次更新带当前时间戳（`YYYY-MM-DD HH:MM:SS`），
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
