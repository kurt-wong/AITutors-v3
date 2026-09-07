# AI Tutor V3 — RESTART PROMPT

Version: v1.12
Status: 段 H 编码进行中 — Phase 8（TaskExecutor + Worker CLI）实现 + 独立对抗审查（0 CRITICAL / 1 HIGH
/ 2 MEDIUM / 3 LOW 全修复或登记）收口，全量 267 passed；变更未 commit（Phase 8 独立提交点待用户放行）；
下一实施步 = commit Phase 8 → Phase 9 配置常量随步补
Date: 2026-09-07

## 0.0 当前结论（2026-09-07 20:49）

- **H 段推进定格**：A–G 七段 + Step 1–5 + Phase 7 全 CLOSED。**Phase 8（TaskExecutor + Worker CLI）
  实现完成 + 独立对抗审查（sonnet 只读，0 CRITICAL）+ 修复收口**；变更未 commit（待用户放行）。
- **Phase 8 交付**：`domains/task/executor.py` `TaskExecutor`（Worker 循环编排，只拥 Runtime
  Authority：run_once → claim_next 原子 claim → 逐 stage Seal/Annotation/Compile 各独立 session 事务 →
  complete/fail，stage 边界 `_heartbeat` 续租）；`worker/__init__.py` + `__main__.py`（run / run
  --allow-live / recover [--dry-run|--confirm] 默认 dry-run / retry <task_id>）；`TaskClaimRepository.
  finalize_claim`（受控 claim 终态：outcome/error_type/end + lease_snapshot 并入 error_detail）+
  `TaskRepository.next_queued_id`；`TaskService.claim_next` + complete/fail 写 claim 终态 + lease 从
  settings 读；`config.py` Phase 9 常量（worker_concurrency=1 / task_claim_lease_seconds=60 /
  http_retry_count=2 / provider_fallback_enabled=False）；`test_task_executor.py` 6 测试。
- **H8-1/H8-2 落地**：下游失败经 `_classify_error`（V3Error→error_type / ValueError→validation_error
  / 其它→system_error）+ `fail(error_type, error_detail)` 持久化到 task_claims（outcome=failed +
  error_type + lease_snapshot.error_detail）。audit（executor 终态化）与 task（本层判 failed）双层分离。
- **独立对抗审查（0 CRITICAL / 1 HIGH / 2 MEDIUM / 3 LOW）全修复或登记**：HIGH（Worker 从不续租 →
  stage 边界 `_heartbeat`）✅修复；MEDIUM（`except BaseException` 吞取消信号 → `except Exception`）✅
  修复；测试隔离（残留 queued 污染 next_queued_id → cleanup 前移）✅修复。
- **deferred 登记（不重开）**：**D1** claim_next「无 queued」与「claim 竞争失败」混为 None（M1 单
  worker 不触发，worker_concurrency>1 时区分）；**D2** config 三字段 M1 预留未接线（http_retry_count
  与 llm_request_retry_count 分层）；**D3** file_path 信任边界（未来 enqueue 校验）；**D4** finalize_claim
  缺行 no-op vs finalize_audit 缺行 raise 不对称 + recover 不写 claim 终态（观察项）；**D5** live 长
  LLM stage 内持续 heartbeat 未接（live smoke 后）。延续 D1/D2/D3/F-4（Step 4 登记，Phase 8/9 定夺）。
  BUG-V3-001..028 Open 不变（errata 终裁待）。
- **验证**：全量 pytest **267 passed ×2**（净 +6，可重入）；git diff --check 干净；Worker CLI
  `--help` smoke 通过；真 DB 探针（claim→running + heartbeat 续租 + run_once→succeeded）实证。
- **下一步**：commit Phase 8（独立基线）→ **Phase 9 配置常量随步补**（config 常量已补，剩余 HTTP
  retry/fallback 接线 + D 项定夺）→ H 段最终收口。
- 重启后第一任务：读本文件 → Status.md 尾 → log.md 尾 → 打开 plan 文件
  （`~/.claude/plans/giggly-enchanting-volcano.md`）恢复上下文 → 按当前 Step 继续 H 段实现
  （或等待用户新指令）。

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
