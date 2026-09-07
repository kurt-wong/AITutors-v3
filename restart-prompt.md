# AI Tutor V3 — RESTART PROMPT

Version: v1.10
Status: 段 H 编码进行中 — Step 5 attempt_id 贯通 + Lock-3 依赖倒置 + Phase 6 幂等写 完成 + 两轮对抗审查无 P0/P1（commit 前真 DB 探针 6/6 PASS，256 passed ×2）；Step 5 待 commit
Date: 2026-09-07

## 0.0 当前结论（2026-09-07 15:40）

- **H Step 5（attempt_id 贯通 + AnnotationService 依赖倒置 Lock-3 + Phase 6 并发幂等写）实现完成 +
  两轮对抗审查均无 P0/P1（14:05 sonnet 只读 R-A~R-G；15:40 commit 前第一性原理真 DB 探针审查）**。
  A–G 七段 + Step 1–4 仍定格（bf888a8 为当前基线，Step 4 已 CLOSED）。Step 5 交付：Lock-3 倒置
  （`AnnotationService` 只持 `LLMExecutor`，删 annotation Domain→Gateway 直连旁路，domains/repositories
  零 gateway 导入扫描确认）；attempt_id 贯通 annotate→gate→candidate 全链（Lock-5 仅 Artifact Runtime
  Provenance 不进 LE hash；`executor.complete` 身份参数放宽默认 None + `_complete_live` fail-closed 补
  task_id/document_id/provider/model 校验）；Phase 6 并发幂等写 `pg_insert ON CONFLICT DO NOTHING` 锚
  `UNIQUE(stage,hash)`（valid/superseded 冲突 → 幂等返回既有；invalid 残留阻挡 valid 写 →
  RepositoryError 显式化；candidate 冲突 → re-read 既有）。新增 test_h_step5_attempt_provenance 5
  回归；既有 D/G 语义经 executor 注入保持（test_annotation_dbflow `_svc` helper / test_repositories
  候选测试补真实 FK 父行）。
- **commit 前第一性原理对抗审查（2026-09-07 15:40，真 PostgreSQL 探针）**：
  `backend/tests/_audit_step5_adversarial.py`（untracked 一次性，不入 Git）6 探针全 PASS ×3，
  **无 P0/P1**。P-1/P-2 Phase 6 真并发败者（annotation/candidate）B 阻塞于 A 未提交行
  （`not b_task.done()` 防假绿）→ A commit 后 ON CONFLICT no-op + re-read 恰单行、胜者 attempt 保留；
  P-3 FK 不被 DO NOTHING 吞仍抛 IntegrityError；P-4 服务层端到端 invalid 残留阻挡 + 失败 attempt 落库
  + P2-1 遮蔽签名 DB 实证（P-4②③ 转正为永久回归
  test_service_invalid_residue_blocks_valid_and_masks_second_failure）；P-5 Lock-3 import-only 零
  gateway/provider；P-6 parse/forbidden 失败分支 attempt 落库。R-A~R-G 结论保持（14:05）。
- **deferred 登记（不重开；2 P2）**：P2-1 annotate 失败路径 invalid-over-invalid 时 RepositoryError
  遮蔽原始错误 → **owner = Phase 7 方案 B**（触碰同一 D 失败路径、届时 annotate 失败改不落 invalid 行，
  遮蔽自然消解）；P2-2 未跟踪 `_audit_d.py` 旧签名直连 Gateway（不入 Git 历史，一次性探针惯例）；
  P2-3 服务层二次失败错误类型缺口**已随 P-4②③ 转正关闭**。D1 crash-orphan reconciliation / D2 provider
  exception translation / D3 reclaim 仅 crash/orphan fallback / F-4 usage·token 事实源 + idempotency_key
  DB 唯一 = 延续 Step 4 登记（Phase 8/9 定夺）。
- **验证**：定向 D/G/runtime 34 ×2；全量 **256 passed ×2**（净 +1：P-4②③ 转正，可重入）；git diff
  --check 干净。变更未 commit（Step 5 独立提交点待用户放行；放行范围含 6 生产文件 +
  test_h_step5_attempt_provenance + Status.md/log.md/restart-prompt 收口；全部 `_audit_*.py` 探针排除
  Git 历史外）。
- **下一步**：commit Step 5（独立基线，含本文件 v1.10 + Status.md + log.md 收口 + P2 登记）→
  **Phase 7（H0-15 方案 B）** annotate 失败路径不落 invalid 行（失败留 audit+task 证据）→
  **Phase 8 TaskExecutor**（plan 末步，最后接编排）→ Phase 9 配置常量随步补。
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
