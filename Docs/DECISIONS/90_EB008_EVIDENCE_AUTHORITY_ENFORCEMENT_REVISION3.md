# EB-008 Evidence Authority Enforcement — Revision-3

- **Status**: L2 DESIGN PROPOSAL (awaiting DSH Review-4)
- **Supersedes**: 89号 (Revision-2)
- **Trigger**: Owner Decision-1~4 (frozen business rules)
- **Date**: 2026-09-15

---

## 0. 与 Revision-2 的差异

Revision-2 基于以下假设，Owner 已裁决推翻：

| Rev-2 假设 | Owner 裁决 | Rev-3 修正 |
|---|---|---|
| 每次 Run 创建新 Candidate | Decision-1: HASH 一致 = 同一 Entity | Candidate 创建基于 le_hash idempotent |
| Human Issuer 需要 IAM 或 prefix 约束 | Decision-2: 个人系统，用 Review Proof | 删除 IAM 讨论，改用 proof token |
| ValidationEvent 可 in-memory | Decision-3: 所有证据必须持久化 | Authority Ledger 落库 |
| IR Boundary 独立于 Admission Boundary | Decision-4: 先解释 IR，再对比方案 | 不预设结论，提交两方案分析 |

---

## 1. Owner 冻结业务规则

### Decision-1: Question Identity

HASH 一致 = 同一个 Question Entity。

- Run 是处理过程（Process），不是数据库实体
- Question/Candidate 是处理结果（Entity）
- 相同输入 HASH → 同一个 Entity（跨 Run 复用）
- 不同输入 HASH → 新 Entity

**删除**："每次 Run 创建新 Candidate" 及同类描述。

### Decision-2: Human Review Trust Model

系统定位：个人家庭内部 AI Tutor，非开放互联网 SaaS。

- 不要求 IAM 或密码学身份体系
- 审核页面完成后，系统自动生成 review proof token
- proof 与 review_result、candidate identity、reviewer action 绑定
- proof 持久化保存
- 存在合法 proof = 可信人工审核结果

### Decision-3: Evidence Persistence

所有关键证据必须持久化，禁止 "运行期间内存保存" 或 "实现阶段再决定"：

- 原始 PDF/DOCX → `documents` + object storage（已有）
- OCR Markdown → `document_source_versions.body_text` + `document_source_lines`（已有，sealed 禁 UPDATE）
- Annotation → `semantic_annotations.payload` JSONB（已有）
- Metadata → `admission_candidates.input_identity` + `build_versions`（已有）
- ValidationEvent → **新表 validation_events**（Rev-3 新增）
- Human Review Event → `admission_candidates.review_trail` JSONB（已有）+ `validation_events.review_proof`（Rev-3 新增）
- Authority Projection → **从 validation_events 确定性投影**（Rev-3 新增，非独立存储）

### Decision-4: IR Boundary

Owner 暂未裁决。Rev-3 提供 IR 解释 + 两方案对比（§7），供 Owner 决策。

---

## 2. RQ-001: HASH 相同重复运行时，Authority 如何保持一致？

### OBSERVED

从 `backend/app/domains/gate/service.py:214-216`：

```python
candidate = await self._snap.find_candidate_by_le_hash(
    logical_execution_stage=_STAGE, logical_execution_hash=le_hash
)
if candidate is None:
    candidate = await self._snap.create_admission_candidate(...)
```

- candidate 创建是 idempotent：le_hash 命中 → 复用；未命中 → 创建
- `logical_execution_hash` 输入：`{task_type, stage, contract_domain, input_domain}`
- input_domain 包含：`annotation_id, annotation_payload_hash, unit_id`
- 不含 attempt_id、run_id、时间戳

从 `backend/app/models/snapshot.py:46-48`：

```python
__table_args__ = (
    UniqueConstraint("logical_execution_stage", "logical_execution_hash"),
)
```

DB 层 UNIQUE 约束保证同一 le_hash 至多一个 candidate。

### INFERRED

相同输入 HASH 重复运行时：

1. Run A: le_hash_X → 创建 candidate_X → Gate 评估 → ValidationEvent → Authority
2. Run B（replay）: le_hash_X → **复用** candidate_X → 同一 candidate_id

AuthorityIdentity = `(source_version_id, candidate_id, claim_id)`

由于 candidate_id 在 replay 时不变，AuthorityIdentity 不变，Authority 从 validation_events 表查询，结果一致。

### PROPOSED: Replay 语义

```
R1: Replay 时 find_candidate_by_le_hash 命中 → 复用既有 candidate_id。
R2: Replay 不改变 Authority 状态。
R3: 如果 candidate 已有 VALIDATED ValidationEvent → 跳过重复 append（idempotent no-op）。
R4: 如果 candidate 无 ValidationEvent（pending_review）→ Gate 重新评估，可能产生新 ValidationEvent。
R5: 如果 candidate 有 INVALIDATED/REJECTED → 终态，replay 不复活（需走 §6 恢复路径）。
```

**关键规则：Authority 状态只通过显式状态转换改变（VALIDATED→INVALIDATED，或新 Evidence→新 Entity→新 Authority），replay 是 no-op。**

### 验证

Authority 一致性由以下机制保证：

1. le_hash 确定性：相同输入 → 相同 hash（canonical_json + SHA-256，float 禁止，BUG-V3-005）
2. candidate 复用：find_by_le_hash 命中 → 同一 candidate_id
3. validation_events 持久化：Authority 从 DB 查询，非内存
4. 幂等 append：已 VALIDATED 的 claim，重复 VALIDATED 为 no-op

---

## 3. RQ-002: Candidate Identity 与 Run Identity 的关系

### OBSERVED

- `admission_candidates` 表无 run_id 字段（snapshot.py:42-73）
- candidate_id = UUIDPrimaryKeyMixin 主键
- `attempt_id` 存在但可 NULL（snapshot.py:73）
- `logical_execution_hash` 是 UNIQUE 约束的一部分（snapshot.py:46-48）

### INFERRED

| 概念 | 定义 | 身份标识 | 持久化 |
|---|---|---|---|
| Run | 处理过程（Process） | 无独立 ID（attempt_id 可选） | 不持久化为独立实体 |
| Candidate | 处理结果（Entity） | le_hash（逻辑）+ candidate_id（物理 UUID） | admission_candidates 表 |

关系：
- 一个 Run 处理 N 个 Candidate（一个 annotation 可能有多个 unit）
- 一个 Candidate 可被 M 个 Run 处理（replay）
- Candidate 与 Run 是 "曾被处理" 关系，不是 "归属" 关系

### PROPOSED: Identity Model

```
I1: Run 是 conceptual entity，不是 database entity。
I2: Candidate 是 database entity，身份由 le_hash 唯一确定。
I3: candidate_id 是存储层 UUID，True identity 是 le_hash。
I4: AuthorityIdentity = (source_version_id, candidate_id, claim_id)。
I5: run_id / attempt_id 不参与 AuthorityIdentity。
I6: Replay 时同一 le_hash → 同一 candidate_id → 同一 AuthorityIdentity。
I7: 不同输入 HASH → 不同 le_hash → 不同 candidate_id → 不同 AuthorityIdentity。
```

**跨 Run 复用是 by design（Decision-1），不是漏洞。** 相同输入 = 相同 Entity = 相同 Authority。

---

## 4. RQ-003: Human Review Proof 的最小可信机制

### OBSERVED

当前 `backend/app/domains/gate/admission.py:450-456`：

```python
def _has_human_approve(review_trail: list | None) -> bool:
    if not review_trail:
        return False
    for entry in review_trail:
        if entry.get("decision") == "approve" and entry.get("verified_by") in _HUMAN_SOURCES:
            return True
    return False
```

- 只检查 decision + verified_by，无 proof 验证
- review_trail 是 JSONB，可被直接修改
- 无 proof token 生成或验证逻辑

### INFERRED

Owner Decision-2 要求：审核完成后系统自动生成 proof，与 review_result、candidate identity、reviewer action 绑定，持久化。

### PROPOSED: Review Proof 机制

#### Proof 生成

```
review_proof = SHA256(
    canonical_json({
        "candidate_id": "<UUID>",
        "review_result": "approve" | "reject",
        "reviewer_id": "<string>",
        "reviewed_at": "<ISO 8601 UTC>",
        "app_secret": "<from .env>"
    })
)
```

生成时机：审核页面提交时，后端在写入 review_trail 前计算。

Synthetic 示例：

```json
{
  "candidate_id": "00000000-0000-0000-0000-0000000000aa",
  "review_result": "approve",
  "reviewer_id": "owner",
  "reviewed_at": "2026-09-15T10:00:00Z",
  "app_secret": "<redacted>"
}
→ review_proof = "a3f8…64hex"
```

#### Proof 绑定字段

| 字段 | 作用 | 防御 |
|---|---|---|
| candidate_id | 绑定 Entity | 防止 proof 跨 candidate 重用 |
| review_result | 绑定决策 | 防止 approve proof 用于 reject |
| reviewer_id | 绑定操作者 | 审计追溯 |
| reviewed_at | 绑定时间 | 防止无限期重放旧 proof |
| app_secret | 绑定部署环境 | 防止 DB 直接修改伪造 |

#### Proof 验证

验证时机：Admission Boundary 检查 Authority 时。

```
验证步骤：
1. 从 validation_events 查询该 candidate/claim 的 human_review 事件
2. 提取 stored review_proof
3. 从事件字段重新计算 expected_proof（同上公式）
4. 比较 stored == expected
5. 不匹配 → Authority 无效 → fail-closed
```

#### 防数据库直接修改

攻击场景：直接修改 `admission_candidates.review_trail`，伪造 approve 记录。

防御：
1. proof 由后端 API 生成，DB 直接修改不会产生合法 proof（不知道 app_secret）
2. Admission Boundary 验证 proof → 不匹配 → 拒绝 approve
3. review_trail 是审计记录；Authority 判定以 validation_events.review_proof 为准

#### Phase-1 最小实现

```
P1: APP_SECRET 从 .env 读取（32 字节随机字符串，启动时校验非空）
P2: proof = SHA256(canonical_json({candidate_id, review_result, reviewer_id, reviewed_at, app_secret}))
P3: human approve 路径：生成 proof → INSERT validation_events(validation_result=validated,
    validation_method=human_review, validator="human/<reviewer_id>", review_proof=proof)
P4: Admission Boundary 验证 proof
P5: 无 proof 或 proof 不匹配 → Authority 无效 → fail-closed → pending_review
```

#### 信任边界（明确标记）

```
Trust Model: Deployment Environment Boundary

防御范围：
- 数据库直接修改（无 APP_SECRET → 无法伪造 proof）
- 跨 candidate proof 重用（candidate_id 绑定）
- 跨 result proof 重用（review_result 绑定）

不防御（Trade-off，Owner Decision-2 接受）：
- 攻击者获取 APP_SECRET（.env 泄露）→ 可伪造
- 攻击者获取 DB + .env 完全访问 → 超出威胁模型（个人系统）

Phase-1 不等价于 IAM。Authority from human_review 在 APP_SECRET 泄露场景下可被伪造。
个人系统威胁模型：部署环境是信任边界，.env 保护是运维责任。
```

---

## 5. RQ-004: ValidationEvent 如何永久保存

### OBSERVED

当前 `backend/app/domains/evidence/promotion.py:207-209`：

```python
def __init__(self) -> None:
    # Phase 1: in-memory append-only log. Phase 2: DB persistence.
    self._validation_log = AppendOnlyEventLog()
```

- in-memory，per-run 生命周期，run 结束后丢失
- **违反 Decision-3**（禁止 "运行期间内存保存"、禁止 "实现阶段再决定"）

### PROPOSED: validation_events 表

```sql
CREATE TABLE validation_events (
    event_id UUID PRIMARY KEY,
    claim_id VARCHAR NOT NULL,              -- unit_id，如 "u1.stem"
    candidate_id UUID NOT NULL REFERENCES admission_candidates(id),
    source_version_id UUID NOT NULL,
    validation_result VARCHAR NOT NULL,     -- 'validated' | 'rejected' | 'invalidated'
    checks JSONB NOT NULL,                  -- [{"check_id","result","detail"}, ...]
    validation_method VARCHAR NOT NULL,     -- 'frozen_header_rule'|'byte_proven'|'structural_consistency'|'human_review'
    validator VARCHAR NOT NULL,             -- 'gate/v1' | 'human/<reviewer_id>' | 'system/v1'
    reference_ids JSONB,                    -- ["er-sp-u1.stem", ...]
    review_proof VARCHAR,                   -- Decision-2: human_review 事件的 proof token；其他为 NULL
    validated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ve_claim_candidate ON validation_events(claim_id, candidate_id);
CREATE INDEX idx_ve_candidate ON validation_events(candidate_id);
```

Synthetic 示例行：

```
event_id          = 00000000-0000-0000-0000-000000000001
claim_id          = "u1.stem"
candidate_id      = 00000000-0000-0000-0000-0000000000aa
validation_result = "validated"
validation_method = "frozen_header_rule"
validator         = "gate/v1"
review_proof      = NULL
validated_at      = 2026-09-15T10:00:00Z
```

### PROPOSED: Authority Projection

Authority 不是独立存储，从 validation_events 确定性投影：

```python
def project_authority(candidate_id: UUID, claim_id: str) -> str:
    events = query_events(candidate_id, claim_id)  # ORDER BY validated_at, event_id
    if not events:
        return "none"
    return events[-1].validation_result
```

投影规则：
- 无事件 → Authority = none（fail-closed）
- 最新事件 = validated → validated
- 最新事件 = rejected → rejected（terminal）
- 最新事件 = invalidated → invalidated（terminal，见 §6）

### PROPOSED: Append-Only 执行

应用层约束：
- validation_events 只 INSERT，Repository 不暴露 UPDATE/DELETE
- AppendOnlyEventLog 状态机在写入前检查（现有 models.py:268-304 逻辑保留，改为写 DB 前调用）

DB 层约束（Phase-1 标记为 trade-off，后续加固）：
- 触发器阻止 UPDATE/DELETE

---

## 6. RQ-005: INVALIDATED 后如何恢复

### OBSERVED

当前状态机 `backend/app/domains/evidence/models.py:232`：

```python
_TERMINAL_STATES = frozenset({"rejected", "invalidated"})
```

`models.py:293-297`：terminal 状态后 append 新事件 → ValueError。

INVALIDATED 语义：source 变更、OCR 升级、bug 修复 → 既有 evidence 链失效。

### PROPOSED: 恢复路径

**INVALIDATED 是 terminal。恢复 = 新 Entity → 新 Authority。**

```
L1: INVALIDATED 是 terminal，该 claim_id 不再接受新 ValidationEvent。
L2: 恢复路径：新 evidence → 新 annotation → 新 annotation_payload_hash →
    新 le_hash → 新 candidate → 新 claim_id → 新 ValidationEvent 链。
L3: 新旧 Authority 独立。旧 Authority 保持 INVALIDATED（审计追溯），新 Authority 从零开始。
L4: 无 Authority resurrection。不支持 INVALIDATED → VALIDATED 转换。
```

#### 恢复流程示例

```
初始状态：
- source_version_SV1 → annotation_A → le_hash_X → candidate_X
- Gate 评估 → VALIDATED → Authority(candidate_X) = validated

Source 变更（OCR 修复）：
- 系统对 candidate_X 追加 ValidationEvent(invalidated, validator="system/v1")
- Authority(candidate_X) = invalidated（terminal）

新 Pipeline 运行：
- source_version_SV2 → annotation_B → le_hash_Y → candidate_Y（新 Entity）
- Gate 评估 → VALIDATED → Authority(candidate_Y) = validated
- 与 candidate_X 的 Authority 独立
```

#### 为什么 INVALIDATED 是 terminal

1. **审计完整性**：旧 Authority 保持 invalidated，可追溯撤销原因
2. **防止误恢复**：INVALIDATED 通常因为 evidence 根本性问题，不应在同 claim 上"修复"
3. **新 Entity 更干净**：新 annotation → 新 le_hash → 新 candidate，Authority 链从零开始
4. **符合 Decision-1**：不同输入 HASH → 新 Entity，与恢复路径一致

#### 新 Evidence 如何产生新 Authority

新 evidence 意味着输入变化（source_version 或 annotation 变更）→ annotation_payload_hash 变化 → le_hash 变化 → 新 candidate → 新 claim_id → Gate 评估 → 新 ValidationEvent → 新 Authority。

同一 candidate 不会出现"新 evidence"：evidence 绑定 source_version + annotation，两者不变则 le_hash 不变，replay 不产生新 Authority（R2）。

---

## 7. RQ-006: IR 的真实职责 + IR Boundary 两方案分析

### OBSERVED: IR 是什么

从 `backend/app/domains/compile/ir.py:1-2`：

```
Semantic Question IR（段 F）。transient；span 只存 id，不复制正文。
```

IR 的实际职责：

1. **装配**：IRBuilder 把 ResolvedRun + annotation 装配成结构化 units
2. **验证**：validate_ir 校验 20 §6.2 不变量，产出 semantic_status（ready/incomplete）
3. **输入 Gate**：Gate 评估 IR → gate_decision
4. **冻结**：IR 存入 candidate.payload.ir_snapshot（物化时使用）

IR **不是**：
- 独立持久化实体（transient，冻结在 candidate payload 中）
- Authority 边界（当前无 Authority 检查）
- 物化边界（物化在 Admission.approve()）

### 为什么 Authority 可能影响 IR

75号 Evidence Promotion Contract R5：Semantic IR can only reference ValidatedEvidence。

即 IR 中的 evidence reference 应指向已 VALIDATED 的 evidence。

问题：Authority 由 Gate 产生（ValidationEvent），Gate 又以 IR 为输入 → 若 IR 要求 Authority 先存在 → **循环依赖**。

### 两方案对比

#### Option A: Authority → IR

流程：Authority → IR → Gate → Admission

IRBuilder 检查每个 evidence reference 的 Authority == VALIDATED；无 Authority → IR 不能构建。

**优点**：
- IR 本身保证只包含已验证 evidence
- 最强边界：IR 是 Authority 的 gatekeeper

**缺点**：
- **冷启动死锁**：首次运行无 Authority → IR 无法构建 → Gate 无法运行 → 无法产生 Authority
- 需要外部 Authority bootstrap（人工预验证或首次运行绕过）
- 增加 pipeline 复杂度

#### Option B: IR → Gate → Authority → Admission

流程：IR（provisional）→ Gate → Authority → Admission Boundary

IRBuilder 不检查 Authority（IR 是 provisional assembly）；Gate 评估 IR → ValidationEvent → Authority；Admission Boundary 检查 Authority == VALIDATED 才物化。

**优点**：
- 无循环依赖：IR 是 Gate 的输入，Gate 是 Authority 的 Producer
- 冷启动正常：首次运行 IR 无 Authority → Gate 评估 → 产生 Authority
- Authority 检查在物化边界（Admission），是最终防线

**缺点**：
- IR 可包含未验证 evidence（provisional 状态）
- 如果 IR 被 Admission 之外的系统直接消费，可能绕过 Authority 检查

### 分析（非裁决）

**Option B 与当前系统结构一致**，理由：

1. IR 是 transient，不独立持久化，只冻结在 candidate.payload.ir_snapshot
2. IR 只流向 Admission（当前代码无其他消费者）
3. Gate 需要 IR 作为输入，Authority 由 Gate 产生 — 这是 pipeline 的自然顺序
4. Admission 是物化边界（产生 A 域行），Authority 检查在此处是最终防线

Option A 的适用场景：IR 被多个下游系统消费（非只有 Admission），需要 IR 自身保证 Authority。若未来出现此场景，需重新评估。

**此节供 Owner Decision-4 裁决，Rev-3 不预设结论。**

### PROPOSED: Option B 设计（若 Owner 接受）

```
IB1: IR 是 provisional assembly，不检查 Authority。
IB2: Gate 是 Authority Producer（自动路径：auto_approve → VALIDATED）。
IB3: Human Review 是 Authority Producer（人工路径：review proof → VALIDATED）。
IB4: Admission Boundary 是 Authority Consumer：Authority == VALIDATED + proof 验证才物化。
IB5: Authority 不存在或非 VALIDATED → fail-closed → pending_review（不 reject）。
IB6: IR 不持久化为独立实体，冻结在 candidate.payload.ir_snapshot。
```

---

## 8. Authority Model 最终定义

### Authority Identity

```
AuthorityIdentity = (source_version_id, candidate_id, claim_id)
```

- source_version_id：版本锚定（FK → document_source_versions）
- candidate_id：Entity 标识（FK → admission_candidates，le_hash 唯一决定）
- claim_id：unit 标识（IR unit_id）

### Authority 状态

```
Authority(candidate_id, claim_id) = latest ValidationEvent.validation_result
```

- 无事件 → none（fail-closed）
- validated → 有效
- rejected → 终态拒绝
- invalidated → 终态撤销

### Authority 生产路径

| 路径 | Producer | validation_method | validator | review_proof |
|---|---|---|---|---|
| 自动 | Gate | derived from gate layers | "gate/v1" | NULL |
| 人工 | Human Review | "human_review" | "human/<reviewer_id>" | SHA256 proof |
| 撤销 | System | derived | "system/v1" | NULL |

### Authority 消费点

| Boundary | 检查内容 | 失败行为 |
|---|---|---|
| Admission Boundary | Authority == VALIDATED；human_review 额外验证 review_proof | fail-closed → pending_review |

---

## 9. Issuer Contract 最终定义

```
C1: issuer_type 从 validation_method 确定性派生。
C2: validator 非空（H1）。
C3: human_review → validator 以 "human/" 开头 + review_proof 非空（H2）。
C4: 非 human_review → validator 以 "gate/" 或 "system/" 开头 + review_proof 为 NULL（H3）。
C5: ValidationEvent 本身就是 issuance_event（append-only）。
C6: Authority 绑定 scope = (source_version_id, candidate_id, claim_id)。
C7: 不要求 IAM；validator 真实性由 review_proof 保证（human_review）或确定性派生（gate/system）。
```

---

## 10. Enforcement 结构

### Defense-in-depth with shared failure source（不使用 "Proven independent"）

| Boundary | 防御的攻击 | 检查时机 | 检查对象 |
|---|---|---|---|
| Admission Boundary | Candidate 无合法 Authority 被 approve | approve() 入口 | Authority == VALIDATED + review_proof 验证 |

共享 failure source：Authority 不存在或 proof 无效 → Admission 拒绝 → fail-closed → pending_review。

当前设计一层 enforcement（Admission Boundary）。若 Owner Decision-4 选择 Option A，增加 IR Boundary 形成两层。

---

## 11. Lifecycle 最终定义

```
状态机：
  (无事件) → VALIDATED
  (无事件) → REJECTED
  VALIDATED → INVALIDATED
  INVALIDATED → terminal（不可恢复）
  REJECTED → terminal（不可恢复）

恢复路径：
  INVALIDATED → 新 evidence → 新 annotation → 新 le_hash →
  新 candidate → 新 claim_id → 新 VALIDATED

Authority 投影：
  Authority = latest ValidationEvent.validation_result
  无事件 → none（fail-closed）
```

---

## 12. 未解决风险

| 风险 | 描述 | 缓解 |
|---|---|---|
| APP_SECRET 泄露 | .env 泄露 → 可伪造 review_proof | 运维责任（个人系统威胁模型接受，Decision-2） |
| validation_events 无 DB 层 append-only | 应用层约束可被 DBA 绕过 | Phase-1 trade-off；后续加触发器 |
| IR 暂无 Authority 检查 | Option B：IR 可包含未验证 evidence | Admission Boundary 是最终防线；IR 当前只流向 Admission |
| INVALIDATED 误触发 | 系统 bug 误 INVALIDATED → 同 claim 无法恢复 | 需新 annotation 重建（新 Entity）；审计追溯原因 |
| pending_review 无 ValidationEvent | Gate 判 pending_review 时无事件落库，Authority=none | 符合 fail-closed；人工审核后补 VALIDATED 事件 |

---

## 13. DSH Review-4 攻击目标

- T1: le_hash idempotent 正确性（Decision-1 落地；replay 语义 R1-R5）
- T2: Review Proof 机制有效性（Decision-2 落地；伪造/重放/跨 candidate 攻击）
- T3: validation_events 持久化完整性（Decision-3 落地；append-only、投影确定性）
- T4: IR Boundary 方案分析正确性（Decision-4；冷启动、循环依赖、消费方范围）
- T5: INVALIDATED terminal 语义正确性（RQ-005；恢复路径、审计完整性）
- T6: Admission Boundary enforcement 完整性（fail-closed、proof 验证时序）
