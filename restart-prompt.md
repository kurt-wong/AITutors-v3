# AI Tutor V3 — RESTART PROMPT

Version: v1.14
Status: 段 H 编码进行中 — Phase 8 已提交（4c3e35f）；V3 全量对抗审查 4 HIGH 全关闭（H Batch 1/2 完成，
310 passed）；剩余 Runtime blockers（Batch 3）；下一实施步 = commit Batch 2 → Batch 3（H Runtime）
Date: 2026-09-07

## 0.0 当前结论（2026-09-07 22:xx）

- **H 段推进定格**：A–G 七段 + Step 1–5 + Phase 7 + **Phase 8（4c3e35f）** 全 CLOSED。**V3 全量
  第一性原理对抗审查**确认核心不变量成立 + 4 HIGH 实现缺陷。**4 HIGH 全关闭**（Batch 1 = H-2/H-3/
  H-4，Batch 2 = H-1）。用户裁决：A–G 继续 CLOSED，H Phase 1-8 substantially complete 但 FINAL
  CLOSURE BLOCKED（剩 Runtime blockers），Phase 9 PAUSED。
- **H-1（BUG-V3-029 Resolved，Batch 2）**：documents.UNIQUE(original_sha256) +
  document_source_versions.UNIQUE(logical_execution_stage, logical_execution_hash)（migration 0006）；
  create_document/create_source_version 改 ON CONFLICT DO NOTHING + re-read；SealService 并发收敛。
  测试 test_h_seal_concurrency（并发恰 1 doc + 1 version + 跨 role 多 version 合法）。
- **BUG-V3-007 终裁 + Clarification**：documents.UNIQUE(original_sha256) 放行（Source/Document
  Identity）；document_source_versions.UNIQUE(stage,hash) 放行（Seal LE Identity）；禁
  document_source_versions.UNIQUE(original_sha256)（Seal 层全局唯一）。
- **当前状态**：H-1/H-2/H-3/H-4 全 Resolved（4 HIGH 关闭）；Runtime blockers（ai/executor.py
  `except BaseException` / complete-fail lease ownership / audit-settle rollback / model_config_hash
  漂移）属 Batch 3；Phase 9 NOT STARTED。
- **下一步**：commit Batch 2（`fix(runtime): H-1 seal concurrent idempotency`）→ Batch 3 = H
  Runtime correctness（BaseException / lease ownership / audit-settle / model_config_hash）。
- 重启后第一任务：读本文件 → Status.md 尾 → log.md 尾 → bugs.md（BUG-V3-007 终裁 + 029..032）→
  按当前 Batch 继续（Batch 2 待 commit / Batch 3 待开始）。

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
