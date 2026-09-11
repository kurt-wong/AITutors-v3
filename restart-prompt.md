# AI Tutor V3 — RESTART PROMPT

Version: v1.30
Status: **全代码库对抗性审查完成** — 架构 PASS WITH RESERVATIONS；
核心安全模型 PASS；Resolver 覆盖率 FAIL（16.7%，由 Phase I-5 Path B 解决）；
下一步 = Step 1 修测试隔离 → Step 2 补 Admission 测试 → Step 3 裁决 67 号
Date: 2026-09-10

## 0.0 当前结论（2026-09-10 对抗性审查收敛）

- **A–G / H Phase 1–8 / Phase 9 / Errata 维持 FINAL CLOSED**。
- **Phase I-3 CLOSED**：Source Evidence Preservation Layer。
- **Phase I-4 CLOSED**：Valid Negative Result——layout evidence 消歧率 0%。
- **Phase I-5 进行中**：I-5-0 → I-5-1 → Step 0/0.5 盲测 → 68 号 → Step B/B5/Step C 裁决（69 号）
  → **全代码库对抗性审查完成（本轮）**。
- **对抗性审查最终状态基线**：
  - Architecture Design: **PASS WITH RESERVATIONS**
  - Core Safety Model: **PASS**
  - Local Invariants: **PASS / TEST-EVIDENCED**（508 测试，506 通过）
  - Cross-Boundary Invariants: **PARTIAL**（Admission 原子性/并发测试缺失）
  - Resolver Algorithm Safety: **PASS**（不猜、确定性、fail-safe）
  - Resolver Real-World Coverage: **FAIL**（16.7%——由 Phase I-5 Path B 解决，非加强 Resolver）
  - Phase I-5 Path B → IR/Compiler: **PROVEN**（21/21 ready IR）
  - Phase I-5 Full Closure: **NOT YET PROVEN**（Gate/Admission 未验证）
  - Manifest Expressiveness: **2 GAPS**（answer_text、options 预拆分）
  - 67 Contract Change: **OPEN / P0 DECISION**（Source Pointer ≠ Source Content）
  - OQ-2/OQ-3: **OPEN / P0 DECISION**
  - Test Isolation: **FAIL**（.env 泄漏 + DB state 泄漏）
  - Full Production Pipeline: **NOT YET CLOSED**
- **审查发现的真实问题（需修复）**：
  - P0: test_config `.env` 泄漏；test_h_seal_concurrency DB 隔离失败
  - P0: Admission 失败原子性测试缺失；并发 Approval 测试缺失
  - P1: Domain→Infrastructure 依赖（目录归位即可）；policy.py 重复 span 检查不完整
  - P1: test_db_tables_exact_19 命名不一致（实际 20 表）
  - OPEN: Figure placement 不进 integrity_hash（需先回 Frozen Spec 定义语义）
- **红线（不变）**：HTTP retry ≠ LLM retry ≠ fallback；先冻结 Spec 再改代码；
  Schema Source of Truth = 20_Document_Pipeline.md；Resolver 不猜；
  实验结果 ≠ 实施授权；提议修改 ≠ 违反 Frozen Spec。
- **下一步（按序执行）**：
  1. **Step 1**：修测试隔离（.env + DB）→ 508/508 干净基线
  2. **Step 2**：补 Admission 失败原子性 + 并发 Approval 测试
  3. **Step 3**：裁决 67 号 Contract Change（Source Pointer ≠ Source Content）
  4. **Step 4**：裁决 OQ-3（leaf Materialization）→ OQ-2（Standalone+Material Annotation）
  5. **Step 5**：补 Manifest Contract（answer_text + options）
  6. **Step 6**：设计 I-5-2 Adapter（Translator + Validator，非第二个 Resolver）
  7. **Step 7**：Path B Full Closure E2E（含 Provenance Golden Test）
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
