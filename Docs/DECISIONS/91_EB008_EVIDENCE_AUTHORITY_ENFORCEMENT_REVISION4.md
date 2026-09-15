# EB-008 Evidence Authority Enforcement — Revision-4

- **Status**: L2 DESIGN PROPOSAL (awaiting Owner final adjudication)
- **Supersedes**: 90号 (Revision-3)
- **Trigger**: Owner Decision-4 adjudication — Option B adopted
- **Date**: 2026-09-15

---

## 0. 与 Revision-3 的差异

Revision-3 §7 提交 IR Boundary 两方案分析，未预设结论。Owner 已裁决：

> 采用 Option B：
> IR 可以先生成。
> 但：IR 不是可信知识资产。
> Authority 是进入 Question Knowledge Layer 的必要条件。

Revision-4 变更：

| # | 变更 | 位置 |
|---|---|---|
| 1 | 删除所有暗示 IR 必须先获得 Authority 的描述 | §2, §7 |
| 2 | 明确 IR = Intermediate Representation，职责与非职责 | §2 |
| 3 | 增加 Boundary 定义：IR Layer / Question Knowledge Layer | §3 |
| 4 | 明确未验证 IR 权限边界（可存在/调试/重编译，禁入 Question 实体） | §4 |
| 5 | 补充 Authority Projection 生命周期 | §5 |

**继承 Rev-3 不变**：Decision-1（幂等 Identity）、Decision-2（Review Proof）、Decision-3（Evidence Persistence）、RQ-001~005 回答、validation_events 表设计、INVALIDATED terminal 语义。

---

## 1. Owner 冻结业务规则（完整）

### Decision-1: Question Identity

HASH 一致 = 同一个 Question Entity。Run 是 Process，Question/Candidate 是 Entity。相同输入 HASH → 同一 Entity；不同输入 HASH → 新 Entity。（详细落实见 Rev-3 §2-§3，无变更）

### Decision-2: Human Review Trust Model

个人家庭内部 AI Tutor 系统，不要求 IAM。审核完成后系统自动生成 review proof token，与 review_result、candidate identity、reviewer action 绑定并持久化。存在合法 proof = 可信人工审核结果。（详细落实见 Rev-3 §4，无变更）

### Decision-3: Evidence Persistence

所有关键证据必须持久化：原始文件、OCR Markdown、Annotation、Metadata、ValidationEvent、Human Review Event、Authority Projection。禁止运行时内存保存，禁止实现阶段再决定。（详细落实见 Rev-3 §5，无变更）

### Decision-4: IR Boundary（本版裁决）

```
D4-1: 采用 Option B。IR 可以先生成，无 Authority 前置条件。
D4-2: IR 不是可信知识资产。
D4-3: Authority 是进入 Question Knowledge Layer 的必要条件。
```

---

## 2. IR 定义（修订）

### IR = Intermediate Representation（中间表示）

**职责**：

1. **结构化原始材料**：IRBuilder 把 ResolvedRun + annotation 装配成结构化 units（unit 树、content roles、span 引用）
2. **提供 Gate 输入**：Gate 评估的结构化对象（semantic_status、content 完整性）
3. **提供后续编译输入**：candidate.payload.ir_snapshot 冻结 IR，物化时作为 Question/Instance 构建源

**IR 本身不代表事实可信。**

IR 是什么：

| 属性 | 说明 |
|---|---|
| transient | 不独立持久化；冻结在 candidate.payload.ir_snapshot 中 |
| provisional | 允许未验证状态（semantic_status: ready / incomplete） |
| 可重新编译 | 输入变化（新 annotation / 新 source_version）→ 新 le_hash → 新 IR |
| 结构载体 | 只装配声明结构，不补猜语义（F 段原则） |

IR 不是什么：

| 非属性 | 说明 |
|---|---|
| 不是知识资产 | 不进入 Question Knowledge Layer |
| 不是 Authority 载体 | IR 构建与存在均无 Authority 检查 |
| 不是最终产物 | 最终产物是物化后的 Question / Instance / role_contents |
| 不是可信声明 | IR 内容的可信性由 ValidationEvent → Authority 表达，不由 IR 自身表达 |

### 已删除的描述

Rev-3 §7 Option A（Authority → IR）中 "IRBuilder 检查每个 evidence reference 的 Authority == VALIDATED" 方案已被 Owner 否决。Rev-4 中**不存在任何要求 IR 先获得 Authority 的设计**。Option A 仅作为被否决方案记录于 §7 历史注记。

---

## 3. Boundary 定义

系统存在两个层级，信任要求不同：

### IR Layer

```
允许状态: provisional（含未验证 evidence reference）
Authority 要求: 无
消费者: Gate（评估输入）、开发调试、重新编译
持久化: transient（candidate.payload.ir_snapshot 冻结快照）
```

IR Layer 内，IR 可以自由存在与流转：构建、评估、失败、重试、重新编译。任何操作都不要求 Authority。

### Question Knowledge Layer

```
允许状态: Authority validated（唯一入口条件）
Authority 要求: Authority(candidate_id, claim_id) == VALIDATED
                human_review 路径额外要求 review_proof 验证通过
消费者: 下游学习系统、用户展示、知识检索
持久化: A 域表（questions / instances / role_contents / materials）
进入方式: Admission.approve() 唯一入口
```

### Boundary 语义

```
IR Layer                    Question Knowledge Layer
─────────────────────       ─────────────────────────
IR (provisional)
  │
  ▼
Gate 评估
  │
  ▼
ValidationEvent ──投影──► Authority
                              │
                              ▼
                        Admission Boundary
                        （Authority == VALIDATED?）
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                 通过                  拒绝
                    │                   │
                    ▼                   ▼
              物化 Question        fail-closed
              (Knowledge Layer)    → pending_review
                                   (停留 IR Layer)
```

**Authority 是跨越 Boundary 的通行证。** 无 Authority 的 IR 永远停留在 IR Layer，不产生 Knowledge Layer 实体。

---

## 4. 未验证 IR 权限边界

### 允许

| 操作 | 说明 |
|---|---|
| 存在 | IR 构建成功即存在，无 Authority 前置条件 |
| 调试 | 开发环境可查看 IR 结构、semantic_status、span 引用 |
| 重新编译 | 输入变化或修复后重新运行 compile → 新 IR |
| Gate 评估 | Gate 消费 IR 产出 gate_decision（ValidationEvent 的输入） |
| 失败重试 | Gate rejected / pending_review 后可修复输入重试 |

### 禁止

| 操作 | 说明 | 执行点 |
|---|---|---|
| 进入最终 Question 实体 | 物化需要 Authority VALIDATED | Admission.approve() |
| 被下游学习系统消费 | 下游只消费 Knowledge Layer 产物 | 系统边界 |
| 被当作知识资产引用 | IR 是中间表示，不是知识 | 使用约定 + Boundary enforcement |

### 执行机制

Admission.approve() 是唯一 enforcement 点：

```
approve() 入口检查：
1. query validation_events(candidate_id, claim_id)
2. 投影 Authority = latest.validation_result
3. Authority != "validated" → RepositoryError → fail-closed → pending_review
4. validation_method == "human_review" → 额外验证 review_proof
5. 全部通过 → 物化 A 域（进入 Knowledge Layer）
```

无 VALIDATED Authority 的 IR 对应的 candidate 永远停留在 pending_review，物化代码路径不可达。

---

## 5. Authority Projection 生命周期

### 5.1 投影定义

```
Authority(candidate_id, claim_id) = latest ValidationEvent.validation_result
```

- 无事件 → `none`（fail-closed）
- 最新事件 validated → `validated`
- 最新事件 rejected → `rejected`（terminal）
- 最新事件 invalidated → `invalidated`（terminal）

### 5.2 生命周期状态机

```
  [none] ──Gate auto_approve──► [VALIDATED] ──System invalidate──► [INVALIDATED]
    │                              │                                (terminal)
    │                              │
    ├──Gate rejected──────────► [REJECTED]
    │                              (terminal)
    │
    ├──Human approve(+proof)──► [VALIDATED]
    │
    └──Human reject───────────► [REJECTED]
                                   (terminal)

恢复路径（INVALIDATED 专用）:
  [INVALIDATED] ──新 evidence──► [新 Entity] ──Gate/Human──► [新 VALIDATED]
  （旧 claim 保持 INVALIDATED，新旧 Authority 独立）
```

### 5.3 投影时机与一致性

| 项 | 定义 |
|---|---|
| 计算时机 | Admission Boundary 检查时 on-demand 计算 |
| 缓存策略 | Phase-1 无缓存；每次查询 validation_events（确定性、可审计） |
| 一致性 | 投影在同一 DB 事务内与 ledger 一致（approve 是单事务） |
| 可重建性 | Authority 状态完全由 validation_events 决定；丢失投影 = 重新查询 |

### 5.4 投影消费

| 消费者 | 消费方式 | 时机 |
|---|---|---|
| Admission Boundary | 查询 + 投影 + 比较 VALIDATED | approve() 入口 |
| 审计/调试 | 查询事件链 | 任意 |

IR Layer **不消费投影**（IR 构建与存在不要求 Authority）。

### 5.5 投影与各层关系

```
IR Layer:        不涉及投影（无 Authority 检查）
Gate:            生产事件（ValidationEvent），不读投影
Human Review:    生产事件（human_review + proof），不读投影
Admission:       读投影（enforcement），唯一消费点
Knowledge Layer: 投影通过后的产物（物化结果）
```

### 5.6 投影与 Evidence 变更

| 事件 | 投影变化 | 后续 |
|---|---|---|
| Gate auto_approve | none → validated | 可 approve |
| Gate rejected | none → rejected | terminal，不可 approve |
| Gate pending_review | none → none（无事件） | 等待人工 |
| Human approve (+proof) | none → validated | 可 approve |
| Human reject | none → rejected | terminal |
| Source 变更 | validated → invalidated | terminal；新 Entity 重建 |
| Replay（同输入） | 不变（幂等 no-op） | 投影稳定 |

---

## 6. Authority Model 完整定义（继承 Rev-3 §8）

### Authority Identity

```
AuthorityIdentity = (source_version_id, candidate_id, claim_id)
```

- source_version_id：版本锚定（FK → document_source_versions）
- candidate_id：Entity 标识（FK → admission_candidates，le_hash 唯一决定）
- claim_id：unit 标识（IR unit_id）

### Authority 生产路径

| 路径 | Producer | validation_method | validator | review_proof |
|---|---|---|---|---|
| 自动 | Gate | derived from gate layers | "gate/v1" | NULL |
| 人工 | Human Review | "human_review" | "human/<reviewer_id>" | SHA256 proof |
| 撤销 | System | derived | "system/v1" | NULL |

### Authority 消费点

| Layer / Boundary | 检查内容 | 失败行为 |
|---|---|---|
| IR Layer | （无检查） | N/A |
| Admission Boundary | Authority == VALIDATED；human_review 额外验证 review_proof | fail-closed → pending_review |

---

## 7. Enforcement 结构

### 单层 Enforcement：Admission Boundary

| Layer | Authority 检查 | 语义 |
|---|---|---|
| IR Layer | 无 | provisional 允许；IR 非知识资产 |
| Question Knowledge Layer | 必须（Admission Boundary） | Authority 是进入的必要条件 |

共享 failure source：Authority 不存在或 proof 无效 → Admission 拒绝 → fail-closed → pending_review（candidate 停留 IR Layer 侧，不产生 Knowledge Layer 实体）。

### 历史注记：被否决的 Option A

Rev-3 §7 曾分析 Option A（Authority → IR：IRBuilder 先检查 Authority）。Owner Decision-4 否决该方案。Option A 的问题：冷启动死锁（IR 需要 Authority，Authority 来自 Gate，Gate 需要 IR）。Rev-4 不采用 Option A 的任何设计元素。

---

## 8. Lifecycle 完整定义（继承 Rev-3 §11，补充投影）

```
ValidationEvent 状态机：
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

Boundary 流转：
  IR Layer（provisional）──Authority VALIDATED──► Knowledge Layer
  IR Layer（无/无效 Authority）──► 停留（pending_review）
```

---

## 9. Issuer Contract（继承 Rev-3 §9，无变更）

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

## 10. validation_events 表（继承 Rev-3 §5，无变更）

```sql
CREATE TABLE validation_events (
    event_id UUID PRIMARY KEY,
    claim_id VARCHAR NOT NULL,
    candidate_id UUID NOT NULL REFERENCES admission_candidates(id),
    source_version_id UUID NOT NULL,
    validation_result VARCHAR NOT NULL,     -- 'validated' | 'rejected' | 'invalidated'
    checks JSONB NOT NULL,
    validation_method VARCHAR NOT NULL,     -- 'frozen_header_rule'|'byte_proven'|'structural_consistency'|'human_review'
    validator VARCHAR NOT NULL,             -- 'gate/v1' | 'human/<reviewer_id>' | 'system/v1'
    reference_ids JSONB,
    review_proof VARCHAR,                   -- human_review 事件的 proof token；其他 NULL
    validated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ve_claim_candidate ON validation_events(claim_id, candidate_id);
CREATE INDEX idx_ve_candidate ON validation_events(candidate_id);
```

Append-only：Repository 只暴露 INSERT；应用层状态机写入前检查；DB 触发器为后续加固项。

---

## 11. 未解决风险

| # | 风险 | 描述 | 缓解 |
|---|---|---|---|
| 1 | APP_SECRET 泄露 | .env 泄露 → 可伪造 review_proof | 运维责任（个人系统威胁模型，Decision-2 接受） |
| 2 | validation_events 无 DB 层 append-only | 应用层约束可被 DBA 绕过 | Phase-1 trade-off；后续加触发器 |
| 3 | IR 被误当作知识资产 | 使用方误将 IR 用于下游消费 | Boundary 定义明确（§3-§4）；enforcement 在 Admission；文档约束 |
| 4 | provisional IR 调试泄露 | 开发环境 IR 内容被误当作已验证数据 | IR transient 不独立持久化；只有物化产物是对外实体 |
| 5 | INVALIDATED 误触发 | 系统 bug 误 INVALIDATED → 同 claim 无法恢复 | 需新 Entity 重建；审计追溯原因 |
| 6 | pending_review 无事件落库 | Gate 判 pending_review 时 Authority=none | 符合 fail-closed；人工审核后补 VALIDATED 事件 |
| 7 | 单层 enforcement | 只有 Admission Boundary 检查 Authority | IR 非知识资产（Decision-4）；若未来 IR 出现新消费者需重新评估 |

---

## 12. Owner 终裁清单

Revision-4 供 Owner 终裁（DEC-013）：

1. **Decision-1 落实**：le_hash 幂等 Identity、replay 语义 R1-R5（Rev-3 §2-§3，无变更）
2. **Decision-2 落实**：Review Proof token、Trust Model 边界（Rev-3 §4，无变更）
3. **Decision-3 落实**：validation_events 持久化、Authority 投影（Rev-3 §5 + 本版 §5）
4. **Decision-4 落实**：IR 定义、Boundary 双层、未验证 IR 权限、投影生命周期（本版 §2-§5）
5. **风险列表**：§11 七项，是否可接受

终裁通过 → 升级为 L2 Decision Record → 进入实现阶段。

---

## 13. DSH Review-4 攻击目标（Decision-4 后更新）

- T1: le_hash idempotent 正确性（replay 语义 R1-R5）
- T2: Review Proof 机制有效性（伪造/重放/跨 candidate 攻击）
- T3: validation_events 持久化完整性（append-only、投影确定性）
- T4: **IR Boundary Option B 落实正确性**（本版 §2-§4：IR 非知识资产、Boundary enforcement、未验证 IR 禁入 Question 实体）
- T5: INVALIDATED terminal 语义正确性（恢复路径、审计完整性）
- T6: Admission Boundary enforcement 完整性（本版 §4：approve() 唯一 enforcement 点）
- T7（新增）: Authority Projection 生命周期完备性（本版 §5：状态机、时机、一致性、消费点）
