# EB-008 Revision-1 Verification Evidence

**Date**: 2026-09-15
**Verifier**: Claude / AITutors-V3
**Target**: `Docs/DECISIONS/88_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_REVISION1.md`
**Purpose**: 证明 Revision-1 是否真实解决 DSH Review-2 阻断项（RDQ-1/2/4）
**Constraint**: 不修改设计、不修改代码、不修改 schema、不修改 Frozen Spec、不增加新设计假设

---

## E1 RDQ-1 Cold Start Dependency

**DSH claim**: IR Boundary 存在 validation ledger 空状态无法启动的问题。

### Claim

Revision-1 通过定义事件产生时序解决冷启动：ValidationEvent 由 Gate（auto path）或 Human Review Projection（human path）在 IR Boundary 检查**之前**产生。Proof chain 无循环依赖。

### Evidence

| 来源 | 内容 |
|---|---|
| Frozen Spec `20 §8.2` L576-578 | 自动 approve 前置：「三层全过 + answer 达自动标准」——Gate evaluate 在 approve 之前 |
| Frozen Spec `75 §三 R4` L123 | 「只有 ValidationEvent 产生 Evidence Authority」——Authority 来自 Event，非相反 |
| `88 §D7` | IR Boundary 6 项必要条件，第 2 条：「每个 EvidenceReference 都有至少一个 ValidationEvent」——检查的是 Event 是否存在，不是 Event 是否被 IR 创建 |
| `88 §D3` | 人工路径：review_trail entry → 投影为 ValidationEvent——Event 由 review action 产生，非 IR 产生 |
| `promotion.py:153-155` | `record_validation_event` 对 `pending_review` 返回 `None`——pending_review 候选不产生 Event，因此 IR Boundary 对其 fail-closed（正确行为） |

### Proof Chain

```text
Source (sealed, immutable)
  ↓
Resolver → ResolvedSpan（定位，无 Authority）
  ↓
EvidenceReference（Proposal，R2: no authority）
  ↓
Gate evaluate() → gate_decision
  ├─ auto_approve → record_validation_event() → ValidationEvent(validated)
  ├─ rejected → record_validation_event() → ValidationEvent(rejected)
  └─ pending_review → None（无 Event）
  ↓
Authority Projection（从 Event chain 推导）
  ↓
IR Boundary check（检查 Event 是否存在且 validated）
  ↓
IR 构建（ready 状态）
  ↓
Admission Boundary check（检查 candidate identity + validity）
  ↓
物化 A 域
```

**循环依赖分析**：ValidationEvent 由 Gate 产生（在 IR 之前），IR Boundary 检查 Event 是否存在（在 IR 构建时）。Event 产生不依赖 IR，IR 构建依赖 Event。无循环。

**冷启动场景**：全新系统 → ledger 为空 → Gate 尚未运行 → 无 ValidationEvent → IR Boundary fail-closed → candidate 保持 pending_review。这是**正确行为**（fail-closed），不是启动失败。Gate 运行后 Event 被创建，后续 IR 构建可正常进行。

### Verdict

**PARTIALLY PROVEN**

设计层面无循环依赖，冷启动语义正确（fail-closed）。但存在实现缺口：FACT-018 确认 `is_evidence_validated` 在 `backend/app` 下零生产调用方——当前代码中 Gate 不产生 ValidationEvent。设计正确 ≠ 实现已存在。

---

## E2 Run Semantics

**针对**：candidate run_id / authority run_id / replay

### Claim

Revision-1 通过 run_id 绑定区分不同 run 的 Authority，防止跨 run authority transfer。

### Evidence

| 来源 | 内容 |
|---|---|
| `88 §D4` | AuthorityIdentity 四元组含 `run_id`（MUST） |
| `88 §D5` | ValidationEvent 增加 `run_id` 字段 |
| `88 §D8` | Admission Boundary 检查 `latest.run_id == current_run_id` |
| `88 §D6` | Replay = 从 DB 加载 events → 重算 projection → 确定性 |
| P3.2 N3 攻击向量 | cross-run evidence——run_id 绑定防御此攻击 |

### Candidate Identity 定义证据

Candidate identity = `Candidate.id`（UUID，DB 主键）。`Candidate.source_version_id` 绑定 SourceVersion。`Candidate.payload.ir_snapshot` 内含 units。

### Authority Identity 定义证据

Authority identity = `(source_version_id, candidate_id, run_id, claim_id)` 四元组（`88 §D4`）。run_id 标识产生该 Authority 的执行上下文。

### Replay 行为证明

**场景：同一 source，Run A → Run B replay**

```text
Run A:
  Gate evaluate → ValidationEvent(run_id=A, validated)
  Authority projection: GRANTED (bound to run_id=A)
  IR 构建 → Admission → 物化

Run B (replay, 同一 source):
  Gate evaluate → ValidationEvent(run_id=B, validated)  ← 新 Event，新 run_id
  Authority projection: GRANTED (bound to run_id=B)
  IR 构建 → Admission 检查 run_id match
```

**关键行为**：
- Run A 的 ValidationEvent(run_id=A) 不授予 Run B 的 candidate Authority
- Run B 需要自己的 ValidationEvent(run_id=B)
- Admission Boundary 的 `run_id match` 检查防止跨 run authority transfer
- Replay（投影重算）：从 DB 加载 events → 重算 → 同一 event chain → 同一 Authority state（确定性）

**两种 "replay" 语义的区分**：

| 语义 | 含义 | 行为 |
|---|---|---|
| **Projection replay** | 从 DB events 重算 Authority | 确定性，同一 events → 同一 Authority |
| **Pipeline re-run** | 重新执行 Gate → 新 ValidationEvent | 新 run_id，独立 Authority |

### Verdict

**PROVEN**（设计层面）

run_id 绑定正确区分不同 run 的 Authority。Projection replay 确定性。Pipeline re-run 产生独立 Authority。无跨 run 泄漏。

---

## E3 Human Authority Producer

**针对 RDQ-4**：Human Review → ValidationEvent → Authority 完整证据链

### Claim

Revision-1 定义 Human Review 通过确定性投影产生 ValidationEvent，再由统一 projection 机制产生 Authority。

### Evidence

| 来源 | 内容 |
|---|---|
| `88 §D3` | 选择 B：Human Review 产生 ValidationEvent(validation_method="human_review") |
| `models.py:157-162` | `VALID_VALIDATION_METHODS` 包含 `"human_review"`（数据模型预留） |
| `models.py:189` | `ValidationEvent.validator` 是 `str`，可承载 `"human/{reviewer_id}"` |
| `75 §五 Trust Split` | human_review 是 reliability 维度（怎么验证的），不是独立 authority channel |
| `20 §8.2` L589-595 | 人工路径：review_trail entry → approve() |

### 完整证据链

```text
Human Reviewer 执行 review
  ↓
review_trail entry 写入（20 §8.2 冻结 schema）:
  {decision: approve, verified_by: human|golden, reviewer_id, confirmed_fields, time}
  ↓
确定性投影（project_validation_event）:
  ValidationEvent(
    validation_result="validated",
    validation_method="human_review",
    validator="human/{reviewer_id}",
    candidate_id=<from context>,
    source_version_id=<from context>,
    run_id=<from context>,
    claim_id=<unit_id>,
    reference_ids=<from EvidenceReference>
  )
  ↓
Authority Projection: GRANTED
```

### 逐项证明

| 问题 | 回答 | 证据 |
|---|---|---|
| **issuer 是谁** | Human Review Projection 机制（确定性代码），非人工直接创建 ValidationEvent | `88 §D3` issuer contract 第 4 条 |
| **issuer identity 如何存在** | `reviewer_id` 来自 review_trail entry（20 §8.2 冻结 schema） | `20 §8.2` L590 |
| **review entry 如何绑定** | review_trail entry 的 `confirmed_fields` 覆盖该 claim 的全部 content role | `88 §D3` issuer contract 第 3 条 |
| **event 如何生成** | 确定性投影：从 review_trail entry 字段映射到 ValidationEvent 字段 | `88 §D3` issuer contract 第 4 条 |
| **authority 如何产生** | ValidationEvent → Authority projection（统一机制，与 auto path 相同） | `88 §D1/D2` |

### 未解决部分

| 问题 | 状态 |
|---|---|
| reviewer_id 的 identity 来源与认证机制 | **UNRESOLVED**（OQ-1：当前无 IAM 系统） |
| 投影触发时机（何时执行 project_validation_event） | **UNRESOLVED**（设计未指定：review_trail 写入时？approve() 时？） |

### Verdict

**PARTIALLY PROVEN**

证据链结构完整：review_trail → 投影 → ValidationEvent → Authority。issuer contract 定义了 4 项签发条件。但 reviewer_id 认证机制（OQ-1）和投影触发时机未解决。

---

## E4 Identity Binding

**Claim**：AuthorityIdentity 四元组不是声明，每个字段有来源、唯一性、生命周期、校验位置。

### 逐字段证明

| 字段 | 来源 | 唯一性 | 生命周期 | 校验位置 |
|---|---|---|---|---|
| `source_version_id` | `EvidenceReference.source_version_id`（`models.py:97`，UUID） | DB 主键，全局唯一 | source sealed 后不可变 | Admission Boundary: `latest.source_version_id == candidate.source_version_id`（`88 §D8`） |
| `candidate_id` | **新增字段**（`88 §D5`，当前代码不存在——FACT-025） | Candidate.id（UUID，DB 主键） | candidate 创建后不可变（payload frozen） | Admission Boundary: `latest.candidate_id == candidate.id`（`88 §D8`） |
| `run_id` | **新增字段**（`88 §D5`，当前代码不存在） | run 执行上下文唯一 | run 完成后不可变 | Admission Boundary: `latest.run_id == current_run_id`（`88 §D8`） |
| `claim_id` | `ValidationEvent.claim_id`（`models.py:185`，= unit_id） | candidate 内唯一 | IR 构建后不可变 | Admission Boundary: `claim_id ∈ candidate.payload.ir_snapshot.units[]`（`88 §D5`） |

### 诚实评估

| 字段 | 当前代码状态 |
|---|---|
| `source_version_id` | ✅ 已存在（EvidenceReference） |
| `candidate_id` | ❌ 不存在（FACT-025：ValidationEvent 无此字段） |
| `run_id` | ❌ 不存在（FACT-025） |
| `claim_id` | ✅ 已存在（但仅 unit_id，无 candidate 绑定） |

### Verdict

**PARTIALLY PROVEN**

设计定义了完整的 identity binding。但 4 个字段中 2 个（candidate_id, run_id）在当前代码中不存在。binding 是设计提案，不是当前事实。

---

## E5 claim_id → candidate_id Join

**Claim**：正式 join 规则可区分不同 candidate 的同名 claim。

### Join 规则

```text
join: ValidationEvent.candidate_id == Candidate.id
  AND ValidationEvent.claim_id ∈ Candidate.payload.ir_snapshot.units[].unit_id
```

### 两个 Candidate 的区分

```text
Candidate A (id=uuid-a):
  payload.ir_snapshot.units = [Q1, Q2, Q3]

Candidate B (id=uuid-b):
  payload.ir_snapshot.units = [Q1, Q4, Q5]

ValidationEvent(event_1):
  candidate_id = uuid-a
  claim_id = "Q1"
  → 属于 Candidate A 的 Q1

ValidationEvent(event_2):
  candidate_id = uuid-b
  claim_id = "Q1"
  → 属于 Candidate B 的 Q1
```

**区分机制**：`candidate_id` 字段。同名 `claim_id="Q1"` 在不同 candidate 下通过 `candidate_id` 区分。

### 不可伪造条件

- `candidate_id` 由产生 ValidationEvent 的上下文自动填充（Gate / Human Review Projection），不由调用方传入（`88 §D5`）
- R4：「authority 不可手动设置」——任何模块不得手动创建 ValidationEvent

### Verdict

**PARTIALLY PROVEN**

Join 规则设计正确，可区分不同 candidate 的同名 claim。但 `candidate_id` 字段当前不存在于代码中（FACT-025）。

---

## E6 Authority Lifecycle

**Claim**：Created → Valid → Invalidated 每步有明确触发条件。

### 状态转换证明

| 转换 | 触发条件 | 证据 |
|---|---|---|
| **ABSENT → GRANTED** | 首个 ValidationEvent(validation_result="validated") 被 append | `88 §D6` lifecycle 表；`promotion.py:170`：`decision == "auto_approve"` → `"validated"` |
| **ABSENT → DENIED** | 首个 ValidationEvent(validation_result="rejected") 被 append | `promotion.py:170`：`decision == "rejected"` → `"rejected"` |
| **GRANTED → REVOKED** | ValidationEvent(validation_result="invalidated") 被 append | `88 §D6`；`models.py:154`：`VALID_VALIDATION_RESULTS` 含 `"invalidated"` |

### 状态机 enforcement（已实现）

`AppendOnlyEventLog._check_state_transition`（`models.py:268-304`）：

```text
- REJECTED 是 terminal：不允许后续 event
- INVALIDATED 要求 prior VALIDATED
- VALIDATED → 只允许 INVALIDATED
```

**FACT-024 确认**：此状态机已实现且不可绕过（enforcement 在 ledger 层，非 service 层）。

### Verdict

**PROVEN**

状态转换有明确触发条件。状态机已在代码中实现（FACT-024）。

---

## E7 IR Boundary / Admission Boundary

**Claim**：两层防御不同 failure mode，非重复检查。

### IR Boundary 防御什么

| 维度 | 内容 |
|---|---|
| **Failure mode** | unvalidated evidence 进入 Semantic IR（数据质量问题） |
| **检查对象** | ResolvedSpan → EvidenceReference → ValidationEvent（evidence 链） |
| **检查内容** | 6 项必要条件（`88 §D7`）：EvidenceReference 存在、ValidationEvent 存在、latest=validated、source_version 匹配、run_id 匹配、claim_id 覆盖全部 leaf unit |
| **检查时机** | IR 构建时（compile 阶段） |
| **失败语义** | IR 无法生成 ready 状态 → candidate 保持 pending_review |

### Admission Boundary 防御什么

| 维度 | 内容 |
|---|---|
| **Failure mode** | unvalidated candidate 被物化为 Knowledge Asset（不可逆动作问题） |
| **检查对象** | Candidate → leaf units → ValidationEvent（candidate identity 链） |
| **检查内容** | 4 项检查（`88 §D8`）：Existence、Validity、Identity Match（candidate_id + source_version_id + run_id）、Freshness |
| **检查时机** | approve() 物化前（admission 阶段） |
| **失败语义** | ROLLBACK + pending_review |

### 为什么不是重复检查

| 区别维度 | IR Boundary | Admission Boundary |
|---|---|---|
| 检查阶段 | compile（IR 构建） | admission（approve()） |
| 检查粒度 | evidence 级（每个 ResolvedSpan） | candidate 级（整个 Candidate 的 leaf units） |
| 检查内容 | evidence 链完整性 | candidate identity match |
| 防御目标 | 数据质量（IR 内容正确） | 不可逆动作（物化正确） |

**独立性证明**：
1. 如果 IR Boundary 被绕过（手动构造 IR），Admission Boundary 的 candidate identity check 仍能拦截
2. 如果 Admission Boundary 被绕过（直接调用 _materialize()），IR Boundary 已在更早阶段阻断
3. 两层使用不同检查逻辑（evidence 链 vs candidate identity），非同一 `evaluate()` 调用

### Verdict

**PROVEN**（设计层面）

两层防御不同 failure mode，检查内容和时机不同，具备独立性。

---

## E8 Remaining Open Risks

主动列出仍未证明的问题：

| # | 问题 | 状态 | 影响 |
|---|---|---|---|
| 1 | **实现缺口**：FACT-018 确认 `is_evidence_validated` 零生产调用方。Gate 当前不产生 ValidationEvent。 | UNPROVEN | 设计正确但未实现。冷启动问题在实现后才真正解决。 |
| 2 | **OQ-1**：reviewer_id identity 来源与认证机制（当前无 IAM）。 | UNRESOLVED | Human Authority 的 issuer identity 未闭合。 |
| 3 | **OQ-2**：time-based Authority expiration（EXPIRED 状态）。 | UNRESOLVED | 当前设计不需要，但未明确排除。 |
| 4 | **OQ-3**：Freshness 检查的具体时间窗口定义。 | UNRESOLVED | Admission Boundary 的 Freshness 检查无具体阈值。 |
| 5 | **投影触发时机**：Human Review Projection 何时执行（review_trail 写入时？approve() 时？）。 | UNRESOLVED | E3 证据链的触发点未定义。 |
| 6 | **candidate_id / run_id 字段不存在**：FACT-025 确认当前 ValidationEvent 无此字段。 | UNPROVEN | E4/E5 的 identity binding 是设计提案，非当前事实。 |
| 7 | **AuthoritySnapshot 机制未定义**：`88 §D7` 提出 AuthoritySnapshot，但未定义其存储、查询、失效机制。 | UNRESOLVED | IR 生成后的 Authority 冻结机制不完整。 |

---

## 汇总

| 项 | Verdict | 核心理由 |
|---|---|---|
| E1 Cold Start | **PARTIALLY PROVEN** | 设计无循环依赖，但实现缺口存在（FACT-018） |
| E2 Run Semantics | **PROVEN** | run_id 绑定正确，replay 确定性 |
| E3 Human Authority | **PARTIALLY PROVEN** | 证据链完整，但 OQ-1 和触发时机未解决 |
| E4 Identity Binding | **PARTIALLY PROVEN** | 设计完整，但 2/4 字段不存在于代码 |
| E5 Join | **PARTIALLY PROVEN** | 规则正确，但 candidate_id 不存在 |
| E6 Lifecycle | **PROVEN** | 状态机已实现（FACT-024） |
| E7 Two-layer | **PROVEN** | 不同 failure mode，独立检查 |
| E8 Open Risks | — | 7 项未解决 |
