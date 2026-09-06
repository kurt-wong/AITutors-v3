# H0 — Runtime Readiness Audit（A–G → H 边界审查）

Version: v0.1
Status: H0 Evidence Complete（正式审计资产；供 H Contract Audit 逐项引用）
Date: 2026-09-06
Baseline: commit `8a57a92`（A–G stable baseline，docs `8f10930`）

> 只读审计，零生产代码改动。逐项锚定 A–G 实现文件与 Frozen Spec（30 v1.1 / 40 v1.1 / 10 v1.2.1）。
> Findings 用 H0-N 编号；级 = R1（H 实现前必答）/ R2（H Contract Audit 裁决）/ ✅（已合规，供 H 参考）。

## Scope

评估 **H 段（Worker / Task / Claim / Recovery / Retry / budget / LLM live）** 引入前，A–G 已建能力与 30 Spec 契约之间的就绪度与缺口。只回答「接口/身份/幂等/Authority 边界」，不审查 A–G 内部正确性（已由各段关闭 + 二轮对抗审查覆盖）。

## Baseline

- V3 Core Pipeline A–G：Implementation Complete and Verified（用户裁决 2026-09-06）。
- 确定性主链闭环：Source Seal → Annotation → Resolver → IR/Compiler → Gate → Candidate → Admission → A 域物化。
- 运行域现状：仅 `llm_call_audit` + `budget` 已建（C 段）；`tasks` / `task_claims` 归 H，尚未建表。
- 权威：30 §2-§17（Process/Task/LE/Claim/Live/Retry/Recovery/Audit/Budget/崩溃/Task 幂等/§16 hash/§17 表契约）。

## Audit Method

- 逐项对照 Frozen Spec 原文（30 §3-§17、40 §7/§9/§10）与 A–G 实现（annotation / gate / admission / snapshot_repository / content_repository / runtime / ai 包）。
- 复用段 G 二轮跨提交审计实证（`_audit_g2.py` GA1/GA2：Replay 幂等、approve 原子回滚+重试）。
- 只读：不改 Spec、不改代码、不新增 BUG 编号。

## Evidence Sources

| 源 | 覆盖 |
|---|---|
| `app/domains/annotation/service.py` | ann stage LE、幂等短路、error/parse 无效行 |
| `app/domains/gate/service.py` | compile stage LE、run() 幂等编排、auto approve/reject |
| `app/domains/gate/admission.py` | approve 物化事务 / no-op 幂等（F1/F2 已修） |
| `app/repositories/snapshot_repository.py` | `UNIQUE(stage,hash)`、candidate 创建 |
| `app/models/runtime.py` | llm_call_audit / budget 表 |
| `app/repositories/runtime_repository.py` | audit append-only、budget reserve/settle/reclaim |
| `app/ai/gateway.py` `budget.py` `live_guard.py` `ocr/gateway.py` | external 闸骨架、五账户、live 前置 |
| `_audit_g2.py` GA1/GA2 | Replay 幂等 / approve 崩溃原子性实证 |
| 30 v1.1 §3-§17、40 v1.1 §7/§10 | Task/LE/Claim/Retry/Budget/崩溃/表契约/幂等红线 |

---

## Findings

### H0-1 — LE 键已含 `task_type`、不含 task_id/attempt/worker/时间 ✅
- Finding：`ann` 与 `compile` 两 stage 的 LE key 均带 `task_type`（默认 `document_ingest`），符合 30 §16「含 task_type 不含 task_id」与 40 §10 幂等红线。
- Evidence：annotation/service.py:45；gate/service.py:105-110,59。
- Spec Anchor：30 §16；40 §10。
- Classification：✅ 已合规。H 引用此模式，`task_type` 值域（document_ingest/re-annotate…）须保持业务语义，不得当 retry/force-rerun 绕过。

### H0-2 — `compile` LE 键域与 §16 公式不一致（BUG-V3-022 范畴） R2
- Finding：实现 `contract_domain=build_versions(8)`（含 annotation_schema_version / prompt_version / model_config_hash / source_version）；30 §16 定义 compile contract 仅 4 项（resolver / ir / compiler / gate）+ input=(annotation_id, payload hash)。已提交 candidate 的 hash 按实现 8 项域计算。
- Evidence：service.py:105-110（`_build_versions` 8 项）vs 30:369-377。
- Spec Anchor：30 §16；10 §9（Rebuild 语义）。
- Classification：R2（Contract Decision）。**H 不得隐式修改既有 compile LE hash**——任何对齐 = key 变化 = 新 candidate（10 §9 Rebuild）。处置三选一：A) Implementation wins → §16 errata；B) Spec wins → Rebuild + identity migration plan；C) 维持 M1 → BUG-V3-022 继续 deferred。须在 H Contract Audit 单独裁决。

### H0-3 — `attempt_id` 产生机制缺失（产物行全 NULL） R1
- Finding：`semantic_annotations.attempt_id` / `admission_candidates.attempt_id` 列可空就绪，但 `annotate()` / `run()` 签名无 attempt_id 参数，Repository create 不落列 → 现全部 NULL。F2 修复已让 A 域 instance 从 candidate 原样继承 attempt——链已铺到 A 域，只差「谁在 LE 首次实际执行时分配」。
- Evidence：annotation/service.py:98；gate/service.py:114-125；admission.py:303-306（F2 透传）。
- Spec Anchor：30 §4.1/§5（Attempt = LE 级实际尝试；claim_round ≠ attempt_id）；10 §3。
- Classification：R1。
- Disposition（倾向）：attempt_id 是 **Runtime Execution Provenance，不是 Domain Artifact Identity**。由 **Task Executor** 在真正启动一次 LE 实际尝试时分配，穿给 domain service → Repository 落列；domain/repository 不得自行生成。重试沿用 vs 新 attempt 依 §7。边界表（建议原样进 H Contract）：

  | 字段 | 身份层 | 决定者 |
  |---|---|---|
  | logical_execution_hash | 逻辑执行身份 | Deterministic stage（含 task_type） |
  | stage | 逻辑执行域 | Stage contract |
  | attempt_id | 实际执行尝试 | Runtime Executor |
  | task_id | Runtime 调度实体 | TaskService |
  | claim_round | Task 租约轮次 | Task Claim |

  硬不变量：**claim_round ≠ attempt_id**。

### H0-4 — `llm_call_audit` 无写入方（并入主题 3） R1
- Finding：audit 表已备 `logical_execution_stage/hash/attempt_id/task_id/document_id` + `idempotency_key`，但生产代码无 `create_audit` 调用。
- Evidence：models/runtime.py:23-28；runtime_repository.py:14（仅定义）。
- Spec Anchor：30 §10。
- Classification：R1（见 H0-9/10 唯一 executor）。

### H0-5 — Replay/New 语义已对 ✅
- Finding：同 LE 重跑 → find_existing 短路（ann 命中不重调 LLM）；compile 命中已 approved candidate → approve no-op，不二次物化。GA1（commit 后重放零新行）/ GA2（失败回滚+重试单事件）实证。
- Evidence：annotation/service.py:56；admission.py:75-76；_audit_g2 GA1/GA2。
- Spec Anchor：30 §13；§12 三机制（LE 幂等 + 事务原子 + 条件迁移）。
- Classification：✅ 已合规——§12「防双物化」三机制 A–G 已全落地。

### H0-6 — find→insert 幂等写非原子（并发缺口） R1
- Finding：ann/candidate 幂等写为「先 find 后 create」，无 `ON CONFLICT`。单进程安全；H 多 worker 并发同 LE → 双 find=None → 双 insert → 一方 IntegrityError。
- Evidence：snapshot_repository / annotation.service 幂等路径。
- Spec Anchor：30 §5（claim 原子）、§13（Task 级幂等）。
- Classification：R1。
- Disposition（倾向）：**IntegrityError ≠ 业务失败，属 idempotent success**。优先 `INSERT … ON CONFLICT DO NOTHING RETURNING`（无返回 → re-read existing）；ORM 不适用时 try/except IntegrityError + savepoint + re-read。不得让整个 Task 因「另一 worker 已成功创建」进 failed。

### H0-7 — bounded retry / 熔断未实现（仅 spec） R1
- Finding：§7 分层 bounded（Task/Pipeline/LLM Request/HTTP Retry、Provider Fallback explicit、熔断 `MAX_LLM_CALLS_PER_TASK`）与 §11 LE 跨 attempt 累计预算，均无实现常量。
- Evidence：30:158-183（表）；无对应 app 常量。
- Spec Anchor：30 §7/§11。
- Classification：R1（H 实现面，须 Contract 冻结非实现细节）。每层必须明确：retry → 同 LE？同 attempt？新 attempt？（与 H0-3 联合裁决）。

### H0-8 — claim_round 与 attempt 命名隔离 ✅
- Finding：task 级租约轮次（claim_round，§5）与 LE 级实际尝试（attempt_id，§4.1）已由 spec 明确区分；`task_claims` 归 H 建 append-only 表承载。
- Evidence：30 §4.1/§5/§17。
- Classification：✅ 规则清晰，H 遵循；不得把 task 重试当 LE 重试或反之。

### H0-9/10 — Gateway 是 Permission Gate，非 Execution Boundary；无 audit/budget 接线 R1
- Finding：`LLMGateway._live` 只做四前置放行判定（allow_live / task_context / budget_ok(bool) / live_provider），不写 audit、不 reserve/settle budget、不生成 idempotency_key。`annotate()` 是 `Gateway.complete()` 唯一生产调用者——若 mode=live 会直调 live provider 而无 audit/budget 包裹；cloud OCR（ocr/gateway.py:4-5 自认）同构同缺口。现因 disabled/mock 未暴露。
- Evidence：ai/gateway.py:42-55；annotation/service.py:63；ai/ocr/gateway.py:4-5；runtime_repository 无 reserve/settle 调用方。
- Spec Anchor：30 §6（唯一调用链）、§10（每次真实请求一条 audit）、§11（五账户 reserve/settle）、§16（cloud OCR 同闸）。
- Classification：R1 — **H 第一优先级 Runtime Architecture Issue**。
- Disposition（倾向）：H 新增组件核心不是 Worker/Celery，而是 **Task Executor / Execution Authority Layer**。唯一 **LLM Execution Wrapper**：

  ```text
  Task Executor
    → Resolve LE / Allocate attempt / Build idempotency_key
    → Budget reserve（五账户单事务）
    → Audit STARTED
    → Gateway.complete()
        ├ Success → Audit COMPLETED → Budget settle(actual)
        ├ Failure → Audit FAILED → Budget settle/release
        └ Process death → Audit UNKNOWN（started 无 end）
  ```

  Authority 清单：Attempt / Retry / LLM Call / Budget / Audit / Failure Classification。
  **Domain Service 永不拥有完整 LLM 调用生命周期**——只表达「我需要一次模型调用」。否则 Annotation/OCR Cloud/knowledge resolver 各自实现 budget+audit+retry，C 段统一闸失效。idempotency_key 由 executor 在请求前生成（canonical(LE, attempt, 请求序)），重试沿用；与 provider 层幂等键不同（30 §10）。

### H0-11 — budget 基础设施已备且对齐 ✅
- Finding：`five_account_refs` 五账户正交；le 账户 `(stage,hash)` scope 与 budget 表 `UNIQUE(account_dim, scope_id, stage)` 吻合；reserve/settle 条件 UPDATE、`reclaim_expired` 均实现。无生产调用方。
- Evidence：ai/budget.py:62-70；runtime_repository.py:76-110；models/runtime.py:53-59。
- Spec Anchor：30 §11/§17。
- Classification：✅ 骨架齐。H executor 是唯一调用方；LE 跨 attempt 累计语义由同 scope 自然满足。

### H0-12 — `tasks`/`task_claims` 域未实现 R1
- Finding：两表未建（30 §17 列与不变量已冻结）；`python -m app.worker` 不存在。
- Evidence：models/runtime.py:1（docstring 明确归 H）；40:61。
- Spec Anchor：30 §2（Process Boundary）、§3（Task 状态机）、§5、§17。
- Classification：R1 — Task 域应视为 H 独立子系统，非「queue 表」。
- Disposition：TaskService 显式接口 `enqueue / claim(原子, claim_round+1, RETURNING) / heartbeat / complete / fail / retry / recover`；状态迁移唯一入口；无自动 stale→queued；failed/interrupted 无自动出口（§3）。**Task Claim 是独立 Runtime Evidence**：`task.status=running` ≠「Worker 永远拥有任务」——Task Business Lifecycle 与 Worker Lease/Claim Lifecycle 分离。claim 原子 = `UPDATE … SET status='running', claim_round=claim_round+1 … WHERE status='queued' RETURNING`（或 FOR UPDATE SKIP LOCKED）；heartbeat/completion 校验四元组（task_id+worker_id+lease_token+status=running）；旧 worker 诈尸不得改写 recovery 接管后的状态（写带 lease_token 条件）。

### H0-13 — §12 崩溃语义现成立 ✅
- Finding：approve 单事务（物化+event+approved 原子）→ commit 后崩溃 → rerun 命中 approved candidate → approve no-op → 任务可推进。GA2 实证。
- Evidence：admission.py + GA2；_audit_g2。
- Spec Anchor：30 §12。
- Classification：✅。Worker 采用 **Artifact-first recovery**（查 stage 产物是否就绪 → 复用/执行），非 execution-memory recovery（不维护 step_1_done 之类）。

### H0-14 — decision_status 与 task.status 维度分离 ✅
- Finding：approve/reject 唯一入口无旁路（P0-G-001/002 探针）；Gate 只产判定不物化；Worker 不直写 decision_status。Task 状态是另一维度。
- Evidence：snapshot_repository（update_candidate_decision → AppendOnlyViolation）；30 §12。
- Classification：✅ 已合规。H TaskService 不得以 task 状态覆盖/替代业务状态机。

### H0-15 — invalid annotation 持久化语义待裁决 R2
- Finding：`annotate()` 在 `complete` 抛错 / JSON parse 失败时，先 `create` invalid 行（payload 含 provider_error / parse_error）再 raise，同事务 flush；是否 commit 由调用方定。Worker 引入后需明确失败产物是否留在 artifact 域。
- Evidence：annotation/service.py:62-93。
- Spec Anchor：30 §10（failed/unknown 审计归因）；§12（每 stage 产物单事务）。
- Classification：R2（不能从代码推导，须语义裁决）。
- Disposition（倾向，待 H Contract Audit 终裁）：**方案 B**——执行失败记录属 Runtime Audit / Task Failure，**不属于 Stage Artifact**；Semantic Annotation 只保存可被 Stage Contract 视为实际产物的行。否则 artifact 域混入 failed execution record，污染 Replay / find_existing 短路 / Stage 幂等（invalid 行易成错误命中源）。除非 Frozen Spec 已明确 invalid annotation 是合法 Stage Artifact，否则不扩大该语义。

---

## R1 — Must Resolve Before H Implementation

1. **H0-3**：attempt_id 分配职责（Task Executor）+ `annotate()`/`run()`/Repository 穿参落列。
2. **H0-6**：ann/candidate 幂等写并发化 → idempotent success。
3. **H0-7**：retry 分层 bounded + 熔断常量（Contract 冻结，非实现细节）。
4. **H0-9/10**：唯一 LLM Execution Wrapper（audit + budget + idempotency_key + unknown 归因）。
5. **H0-12**：tasks/task_claims 建表 + TaskService + claim 原子/lease 校验。

## R2 — H Contract Audit Decisions

1. **H0-2**：compile LE 键域 —— errata / Rebuild+identity migration / M1 维持（三选一；不隐式改 hash）。
2. **H0-15**：invalid annotation 归属 —— 默认方案 B（Runtime Audit/Task，非 Stage Artifact）。

## R3 — Observations

- cloud OCR/embedding 若 M1 纳入（30 §16 P1-3 跨册裁决）：与 LLM 同 executor 闸，不另起炉灶。
- 本地确定性 seal 不强审计（00 P4）；seal 重跑由 source_version 原始内容 hash 幂等，不构成 H 阻断；仅 cloud 路径需闸。

## H0 Final Disposition

A–G = **Runtime-ready foundation（确定性业务数据管线 ready）**，非 Runtime 本身 ready。防双物化三机制、Replay/New 语义、budget 骨架均已实证就绪；运行域 Authority（attempt/audit/budget/retry/task）未收口——**H 真正的交付是 Execution Authority Layer，Worker 技术是第二问题**。本审计列 R1 五项为 Implementation Blocker、R2 两项为 Contract Decision，其余以 Carry-Forward Constraints 进入 H。

## Carry-Forward Constraints

1. Worker 不直写 `decision_status`（唯一入口 approve()/reject()，30 §12/20 §8.2）。
2. Task Status 不替代 Candidate Decision Status（两维度分离）。
3. `claim_round` 不替代 `attempt_id`（task 租约轮次 vs LE 实际尝试）。
4. `attempt_id` 由 Runtime Executor 分配（Runtime Execution Provenance，非 Domain Artifact Identity）；domain/repository 不自行生成。
5. Domain Service 不绕 Gateway（唯一调用链 30 §6）。
6. Gateway Runtime 调用必须绑定 Audit + Budget（真实 reserve/settle，非构造期 bool）。
7. 同 LE 并发创建必须收敛为 Idempotent Success（IntegrityError ≠ 业务失败）。
8. H 不隐式修改既有 compile LE identity（H0-2 三选一先裁决，10 §9 Rebuild 语义）。
9. `task_type` 不得作为 retry / force-rerun 绕过手段（40 §10）。
10. Crash Recovery 依赖 Artifact Readiness（每 stage 产物幂等复用），不依赖 Worker Memory（30 §12/§13）。
