# AI Tutor V3 — RESTART PROMPT

Version: v1.6
Status: 段 H 编码进行中 — Step 2 Task State Machine 完成 + F-2/F-1 最小修复收口（229 passed ×2）；Step 2 待 commit
Date: 2026-09-07

## 0.0 当前结论（2026-09-07 00:04）

- **H Step 2（Task State Machine）实现完成 + 第一性原理对抗审查（F-2/F-1）+ 最小修复 +
  收口（229 passed ×2，可重入）**。A–G 七段仍定格（`8a57a92`）。Step 2 交付：
  `app/repositories/runtime_repository.py` +TaskRepository/TaskClaimRepository（条件 UPDATE…
  RETURNING 原子 claim / heartbeat / terminal / retry / recover；task_claims append-only）；
  `app/domains/task/`（TaskService：tasks/task_claims 状态机唯一入口，**不 commit**，
  调用方持事务，claim 的 tasks 状态更新与 task_claims 证据原子同事务）；Lock-1
  （worker_id/lease_token 只进 lease_snapshot JSONB）。`tests/test_task_service.py` 17 测试。
- **对抗审查发现（真 DB 探针 `tests/_audit_h2_task.py` 实证）**：**F-2（CONFIRMED，最高）**
  ——heartbeat 只更 heartbeat_at、**不滑动 lease_expires_at**，recover 只看 lease 不看
  liveness → 持续健康心跳但运行超初始租约（默认 60s）的长任务会被误中断。**F-1（CONFIRMED，
  覆盖缺口）**——无真并发 claim 永久回归（实现已正确，P3 实证恰一胜 + 单证据）。
- **用户裁决（不改 Frozen Spec，只修实现语义）**：F-2 采纳——heartbeat = **滑动续租**
  （liveness renewal，**非 reclaim/recovery**）：`SET heartbeat_at=now(),
  lease_expires_at=now()+make_interval(secs=>:lease) WHERE id/worker_id/lease_token/
  status='running' AND lease_expires_at>now()`（DB now() 单一来源，应用层不回写旧 lease；
  **已过期 claim 的 heartbeat 拒** → 由 recover 接管，绝不靠心跳抢救失效 claim）。F-1 采纳
  ——P3 真并发转正。记录为实现/状态机语义缺陷，非 Spec 变更。
- **修复与回归（4 新测试）**：heartbeat 增 `lease_seconds` 参数 + 续租 + 过期拒。F2-1 lease
  跨事务严格后移；F2-2 持续心跳（间隔<lease、穿过原 lease 边界）不被 recover；F2-3 停止心跳
  超 lease → heartbeat 拒（LeaseConflict）+ recover interrupted；F-1 两 session
  `asyncio.gather` 并发 claim → 恰一 winner（claim_round=1）+ 恰一证据行 + status=running。
- **验证**：全量 pytest **229 passed ×2**（无中间清理，可重入）。探针 P1 lease 严格后移 /
  P2 心跳任务不中断（running）/ P3 过期拒 + 停止可回收（interrupted）/ P4 并发恰一胜单证据
  全部通过。
- **下一步**：commit Step 2（独立提交点，含本文件 + Status.md + log.md 收口）后，按 plan
  严格 Step 顺序进入 **Step 3**（Audit Lifecycle / Phase 3：`finalize_audit` exactly-once
  terminalization）。
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
