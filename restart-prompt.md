# AI Tutor V3 — RESTART PROMPT

Version: v1.11
Status: 段 H 编码进行中 — Phase 7（H0-15 方案 B）实现 + commit 前第一性原理对抗审查（真 DB live 探针
L1–L5 5/5 PASS）+ 用户放行，已提交独立基线（P2-1 Closed）；下一实施步 = Phase 8 TaskExecutor
Date: 2026-09-07

## 0.0 当前结论（2026-09-07 20:02）

- **H 段推进定格**：A–G 七段 + Step 1–5 全 CLOSED（Step 5 基线 = commit `0917404`，含 Step 5 收口 +
  P-4②③ 转正）。**Phase 7（H0-15 方案 B — Annotation Artifact success-only failure policy）实现完成 +
  commit 前第一性原理对抗审查无 P0/P1 + 用户放行，已提交为独立基线并 push 至 origin**。P2-1（失败路径
  RepositoryError 遮蔽原始错误）**正式 Closed**——方案 B 使 annotate 失败不再落 invalid 行，遮蔽自然消解。
- **Phase 7 方案 B 交付**：`annotation/service.py` 删 3 条 failure-path `create_semantic_annotation(
  status="invalid")`（provider error / JSON parse error / forbidden-field）→ annotate 失败一律 0 artifact、
  不占 (stage,hash)，成功只写 `status="valid"`；三失败原样传播（provider 原异常 / parse `ValueError` /
  validation `ValueError`），service 不吞不遮蔽。repo/executor/gate 零改动——历史 invalid 残留防御
  （同 LE 残留阻挡 valid，须新 LE）原样保留。新增 `test_h_step7_failure_policy.py` 6 回归锁死 S7-1..S7-6。
  全量 pytest **261 passed ×2**（净 +6，可重入，无中间清理）。
- **commit 前对抗审查（mock 覆盖空洞实证填补）**：既有 Phase 7 测试全走 gateway mock 分支（无
  audit/budget 副作用 G4）→ plan 语义区分从未在 live 链路证据化。一次性探针
  `backend/tests/_audit_phase7_live.py`（不入 Git）live executor × service × 真 DB **L1–L5 全 PASS**：
  parse→audit completed + 0 artifact；provider→audit failed/network_error + 0 artifact + budget 释放；
  forbidden→audit completed + 0 artifact；同 session fail→success 同 LE 收敛恰 1 valid（audit=
  [failed,completed]，无悬挂）；success 后同 LE retry → find_existing 幂等命中、不重调 provider、audit/
  invocation 不增。
- **Phase 8 Required Handoff（两 Note，不阻塞 Phase 7，不改 Phase 7 代码）**：**H8-1** parse/validation
  失败详情现只经 service ValueError 传 caller，audit completed 行 error_type=None（append-only 不可补记）
  → Phase 8 TaskExecutor 须把下游失败写入 task failure 否则丢失；**H8-2** 冻结双层失败语义——
  `llm_call_audit` = Provider Invocation Runtime Truth，`task` = Logical Execution Outcome，即
  `LLM completed ≠ Logical task completed`，parse/forbidden 在 Runtime 层判 failed、audit 维持 completed。
- **deferred 登记（不重开）**：P2-1/P2-3 Closed；P2-2 陈旧探针不入历史；D1 crash-orphan reconciliation /
  D2 provider exception translation / D3 reclaim 仅 crash/orphan fallback / F-4 usage·token 事实源 +
  idempotency_key DB 唯一 = 延续 Step 4 登记（Phase 8/9 定夺）。BUG-V3-001..028 Open 不变（errata 终裁待）。
- **验证**：全量 **261 passed ×2**；真 DB 探针 cleanup 后无污染；git diff --check 干净；8 个 `_audit_*.py`
  探针全排除 Git 历史（留磁盘）。
- **下一步**：**Phase 8 TaskExecutor**（plan 末步，最后接编排）——承接 H8-1/H8-2（downstream failure →
  task failure persistence + audit/task 双层失败语义冻结）→ **Phase 9 配置常量随步补** → H 段最终收口。
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
