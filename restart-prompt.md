# AI Tutor V3 — RESTART PROMPT

Version: v1.7
Status: 段 H 编码进行中 — Step 3 Audit Lifecycle 完成 + F-1/F-2 分层收口（234 passed ×2）；Step 3 待 commit
Date: 2026-09-07

## 0.0 当前结论（2026-09-07 00:36）

- **H Step 3（Audit Lifecycle / Phase 3）实现完成 + Baseline 对抗审查 + 收口（234 passed ×2，
  可重入）**。A–G 七段仍定格（`8a57a92`）。Step 2（Task 状态机）已 CLOSED（commit be9df51）。
  Step 3 交付：`LlmCallAuditRepository.finalize_audit` = STARTED→terminal（completed/failed/
  unknown）exactly-once 原子 primitive（runtime_repository.py）。
- **对抗审查核心分离**：两不变量不同——A「不重复写 terminal audit」（finalize 条件 UPDATE，Phase
  3）≠ B「不重复执行/不重复建账」（request_id 复用 Phase 4 + attempt 贯通 Phase 5 + (stage,hash)
  ON CONFLICT Phase 6）。**finalize no-op ≠ 整体 exactly-once**。
- **裁决**：F-1 采纳——finalize 缺行 **raise AuditNotFoundError**（缺行≠已终态 no-op，不得被 0 行
  掩盖）；存在且 started→恰一迁移；存在且已终态→no-op 不改写；并发败者 reread 确认 terminal。
  F-2 分层采纳——Phase 3 只供 STARTED→UNKNOWN **primitive**；「何时判 orphan」归 Phase 4 且**绑
  task lease / worker liveness（Task=liveness authority，Audit=execution record），禁按 audit
  年龄判死**（防重蹈 Step 2 F-2）。F-3（idempotency_key 缺请求序）/F-4（usage/settle 事实源）
  carry-forward → Phase 4/5 定夺。
- **验证**：test_audit.py 3→8（三向终态化 / 二次 no-op 不改写 / 缺行 raise / 非法 status raise /
  双 session 并发恰一迁移）；全量 **234 passed ×2**。零越界（无 reconciliation/task lease/executor/
  budget/attempt/schema 扩展）。
- **下一步**：commit Step 3（独立基线，含本文件 + Status.md + log.md 收口）→ plan **Step 4
  LLMExecutor 唯一执行入口**（Phase 4）——先 Baseline/对抗审查再编码：① 真单入口（禁 Domain→
  Gateway/Provider 旁路）；② mock/disabled/live 同径；③ retry 计数点 = Provider Invocation Port
  （Lock-4/Note-1，actual invocations 非 attempt 数）；④ reserve→audit STARTED 同事务(Lock-6)→
  invocation→terminal→settle 接线；⑤ Attempt·LE 分离（Attempt 是运行历史非业务身份）；F-3 request
  identity 由 M1 真实请求模型定夺，不预加 request_seq。
- 重启后第一任务：读本文件 → Status.md 尾 → log.md 尾 → 打开 plan 文件
  （`~/.claude/plans/giggly-enchanting-volcano.md`）恢复上下文 → 按当前 Step 继续 H 段
  实现（或等待用户新指令）。

## 0. 当前工作状态（2026-09-06 20:34:06）

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
- **当前要执行**：按 Step 1–7 开始 H 段编码（Step 1 = Runtime Schema）。每步独立测试；触碰
  已关闭 D/G 段必须最小化 + 真实 DB 回归。
- **当前不要执行**：不重开 A–G 已关闭段（不回头修 BUG-V3-001..027）；不改 Frozen Spec 正文
  （除非 changelog/errata）；不改 compile hash（H0-2 维持 M1）；不加 Question global UNIQUE
  （BUG-V3-027 保持 Open）；不实现 Similarity / occurrence analytics / answer-evidence schema。
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
