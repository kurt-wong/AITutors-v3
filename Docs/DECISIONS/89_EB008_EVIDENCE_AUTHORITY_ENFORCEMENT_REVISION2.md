# EB-008 Evidence Authority Enforcement — L2 Design Revision-2

- **状态**: L2 Design Proposal（Revision-2）
- **关联**: 87号(Rev-0 superseded)、88号(Rev-1 superseded)、DEC-012、DEC-013
- **Owner Review**: 2026-09-15 EB-008 Owner Review — 三个 RDQ 阻断
- **前提**: Owner 裁决 Authority=Projection / ValidationEvent=Grant Event / Human Review→ValidationEvent→Authority / 两层 enforcement 方向保留；但 D-001 Option A（设计冻结先于实现）不接受，需先解决三个架构问题

---

## Revision-2 变更摘要

| RDQ | 问题 | Rev-2 回答 |
|---|---|---|
| RDQ-001 | Bootstrap Authority 循环依赖 | Authority 不是 IR 创建前提，是 IR Admission 前提；Gate 是 Authority Producer；首次 Authority 来自首次 Gate 运行 |
| RDQ-002 | Run Identity 冲突 | Candidate 属于 Run（many-to-one）；candidate_id 全局唯一；run_id 不需要；附 Run A/B replay 证明 |
| RDQ-003 | Human Issuer Contract | 四元组：issuer_type / issuer_identity / issuance_event / binding_scope；最小约束无 IAM |

---

## RDQ-001: Bootstrap Authority — 循环依赖如何打破

### OBSERVED: 当前 pipeline 时序

```
Document → compile → IR → Gate → gate_decision → Admission.approve()
```

来源: `gate/service.py:200-246`、`admission.py:62-114`

- Gate 在 IR 之后运行
- Admission 在 Gate 之后运行
- 当前 Admission 不检查 Authority（FACT-013）

### PROPOSED: Authority 检查点的正确位置

Rev-1 的 R5（"Semantic IR 只能引用 ValidatedEvidence"）如果被解读为 **IR 创建时检查 Authority**，则产生循环：

```
IR 创建需要 Authority → Authority 需要 Gate → Gate 需要 IR → 循环
```

**Rev-2 明确：R5 的检查点是 IR Admission，不是 IR Creation。**

修正后的时序：

```
Phase 1: IR 创建（无 Authority 要求）
  Document → compile → IR（provisional）
  
Phase 2: Gate 运行（Authority Producer）
  IR → Gate → gate_decision
  gate_decision → record_validation_event → ValidationEvent
  ValidationEvent → Authority Projection
  
Phase 3: IR Admission（Authority Consumer）
  Admission 检查 Authority 存在性 + Identity Match
  Authority 存在 → approve
  Authority 不存在 → fail-closed → pending_review
```

### 证明: 无循环依赖

**Gate 是 Authority Producer，不是 Consumer。**

| 阶段 | 输入 | 输出 | 是否需要 Authority |
|---|---|---|---|
| compile | Document | IR | 否 |
| Gate | IR | gate_decision | 否 |
| record_validation_event | gate_decision | ValidationEvent | 否 |
| Authority Projection | ValidationEvent | Authority | 否（纯推导） |
| Admission | Authority | approved/rejected | **是** |

首次 Authority 的产生机制：

1. 首个 Document 进入 pipeline
2. compile 产生 IR（不需要 Authority）
3. Gate 运行，产生 gate_decision
4. record_validation_event 创建 ValidationEvent
5. Authority 从 ValidationEvent 投影得出
6. Admission 检查 Authority → 存在 → approve

**冷启动 = fail-closed 正确行为**：如果 Gate 产生 pending_review（record_validation_event 返回 None），则 Authority 不存在，Admission fail-closed → pending_review → 人工审查路径。这不是循环依赖，是正确的拒绝语义。

### Bootstrap Protocol（冻结规则）

```
B1: IR 创建不需要 Authority。IR 是 provisional artifact。
B2: Gate 是唯一 Authority Producer（自动路径）。
B3: Human Review 是 Authority Producer（人工路径，通过 ValidationEvent）。
B4: Authority 检查点在 Admission Boundary，不在 IR Creation。
B5: 首次 Authority 来自首次 Gate 运行或首次 Human Review。
B6: Authority 不存在时 Admission fail-closed → pending_review。
```

---

## RDQ-002: Run Identity Model

### OBSERVED: 当前数据模型

从 `snapshot.py:42-73`：

```python
class AdmissionCandidate(UUIDPrimaryKeyMixin, Base):
    source_version_id: Mapped[uuid.UUID]     # FK → document_source_versions
    annotation_id: Mapped[uuid.UUID]         # FK → semantic_annotations
    attempt_id: Mapped[uuid.UUID | None]     # 可选
    # 无 run_id 字段
```

- candidate_id = 主键（UUID，全局唯一）
- 无显式 Run 实体
- run_id 仅存在于 `DocumentSourceSelectionEvent`（source.py:190），是 source selection 事件的属性，不是 pipeline execution 的属性

### PROPOSED: Candidate-Run 关系定义

**Run 是 conceptual entity（一次 pipeline execution），不是 database entity。**

```
Run（概念）= 一次完整的 pipeline execution
  └── Candidate（数据库实体）= Run 中一个 Document 的处理单元
        └── claim_id = Candidate 内一个 IR unit 的标识
```

关系：Candidate 属于 Run（many-to-one）。每次 Run 创建新的 Candidate（新 UUID）。

### AuthorityIdentity 修正

Rev-1 提出：`(source_version_id, candidate_id, run_id, claim_id)`

**Rev-2 修正为：`(source_version_id, candidate_id, claim_id)`**

理由：candidate_id 是 UUID，全局唯一。每次 Run 创建新 Candidate，因此 candidate_id 已隐含 Run 信息。run_id 冗余。

### 证明: Run A approved + Run B replay 无错误复用

**场景**：Document D 在 Run A 中处理并 approved，然后 Run B 重放 Document D。

```
Run A:
  1. 创建 Candidate_X (UUID_A) for Document D
  2. Gate 运行 → gate_decision = auto_approve
  3. record_validation_event → ValidationEvent(event_A, claim_id, "validated")
  4. Authority_A = (sv_D, candidate_X, claim_id)
  5. Admission 检查 Authority_A → 存在 → approve

Run B (replay):
  1. 创建 Candidate_Y (UUID_B) for Document D  ← 新 Candidate，新 UUID
  2. Gate 运行 → gate_decision = ?
  3a. 如果 auto_approve → ValidationEvent(event_B, claim_id, "validated")
      Authority_B = (sv_D, candidate_Y, claim_id)
      Admission 检查 Authority_B → 存在 → approve
      Authority_A 和 Authority_B 是不同 Authority（不同 candidate_id）
      
  3b. 如果 pending_review → record_validation_event 返回 None
      Authority_B 不存在
      Admission 检查 Authority_B → 不存在 → fail-closed → pending_review
      Authority_A 不被 Run B 使用（不同 candidate_id）
```

**关键证明点**：

1. **Candidate 不跨 Run 复用**：每次 Run 创建新 Candidate（新 UUID），因此 candidate_X ≠ candidate_Y
2. **Authority 不跨 Run 转移**：Authority_A 绑定 candidate_X，Authority_B 绑定 candidate_Y，互不影响
3. **状态机无冲突**：Candidate_X 的 decision_status 和 Candidate_Y 的 decision_status 独立
4. **run_id 不需要**：candidate_id 已经唯一标识 (Run, Document) 对

### Run Identity Model（冻结规则）

```
I1: Run 是 conceptual entity，不是 database entity。
I2: Candidate 属于 Run（many-to-one）。每次 Run 创建新 Candidate。
I3: candidate_id 是 UUID，全局唯一，隐含 Run 信息。
I4: AuthorityIdentity = (source_version_id, candidate_id, claim_id)。
I5: run_id 不需要在 AuthorityIdentity 中。
I6: Authority 不跨 Candidate 转移（即使同一 Document）。
```

---

## RDQ-003: Human Issuer Contract

### OBSERVED: 当前数据模型

从 `models.py:165-203`：

```python
class ValidationEvent:
    validation_method: str  # enum: "frozen_header_rule" | "byte_proven" | "structural_consistency" | "human_review"
    validator: str          # e.g., "gate/v1"
```

- validation_method 已区分 system 和 human
- validator 是自由字符串

### PROPOSED: Issuer Contract 四元组

**不需要 IAM。用现有字段定义最小约束。**

#### 1. issuer_type（派生自 validation_method）

| validation_method | issuer_type |
|---|---|
| "frozen_header_rule" | system |
| "byte_proven" | system |
| "structural_consistency" | system |
| "human_review" | human |

**issuer_type 不是独立字段**，从 validation_method 确定性派生。

#### 2. issuer_identity（validator 字段约束）

| issuer_type | validator 约束 |
|---|---|
| system | 非空；必须匹配已注册 system_id 模式（如 "gate/v1"） |
| human | 非空；**不得**匹配 system_id 模式（防止冒充） |

**最小约束（无 IAM）**：

```
H1: validator 非空
H2: validation_method = "human_review" 时，validator 不得以 "gate/" 开头
H3: validation_method ≠ "human_review" 时，validator 必须以 "gate/" 开头
```

这防止：
- Human 冒充 System（H2）
- System 冒充 Human（H3）

不要求验证 validator 是否为真实用户（那是 IAM 的事）。

#### 3. issuance_event（ValidationEvent 本身）

| 字段 | 作用 |
|---|---|
| event_id | 唯一标识 issuance |
| validated_at | issuance 时间戳 |
| checks | issuance 时的检查结果 |

issuance_event 不需要额外字段——ValidationEvent 本身就是 issuance 记录。

#### 4. authority_binding_scope（AuthorityIdentity）

Authority 绑定到 `(source_version_id, candidate_id, claim_id)`。

- source_version_id：哪个文档版本
- candidate_id：哪个 Candidate（隐含哪个 Run）
- claim_id：哪个 claim

Authority 不跨 Candidate 转移（即使同一 Document）。

### Issuer Contract（冻结规则）

```
C1: issuer_type 从 validation_method 确定性派生，不是独立字段。
C2: validator 非空（H1）。
C3: human_review 的 validator 不得以 "gate/" 开头（H2）。
C4: 非 human_review 的 validator 必须以 "gate/" 开头（H3）。
C5: ValidationEvent 本身就是 issuance_event。
C6: Authority 绑定 scope = (source_version_id, candidate_id, claim_id)。
C7: 不要求 IAM；validator 真实性由后续 Phase 验证。
```

---

## AuthorityIdentity 最终定义（Revision-2）

```
AuthorityIdentity = (source_version_id, candidate_id, claim_id)
```

| 字段 | 来源 | 作用 |
|---|---|---|
| source_version_id | AdmissionCandidate.source_version_id | 哪个文档版本 |
| candidate_id | AdmissionCandidate.id (UUID) | 哪个 Candidate（隐含 Run） |
| claim_id | ValidationEvent.claim_id | 哪个 claim |

**run_id 从 AuthorityIdentity 中移除**（RDQ-002 证明冗余）。

---

## 与 Revision-1 的差异

| 维度 | Revision-1 | Revision-2 | 变更原因 |
|---|---|---|---|
| AuthorityIdentity | (sv_id, candidate_id, run_id, claim_id) | (sv_id, candidate_id, claim_id) | RDQ-002: run_id 冗余 |
| Bootstrap | 未明确 | Bootstrap Protocol B1-B6 | RDQ-001: 循环依赖 |
| Issuer Contract | 未定义 | Issuer Contract C1-C7 | RDQ-003: 最小约束 |
| R5 检查点 | IR Boundary（模糊） | IR Admission（明确） | RDQ-001: 消除循环 |

---

## 对 DSH Review-2 阻断项的回答状态

| 阻断项 | Rev-1 状态 | Rev-2 状态 | 证据 |
|---|---|---|---|
| RDQ-001 Bootstrap | 未解决 | **已解决** | Bootstrap Protocol B1-B6 + 时序证明 |
| RDQ-002 Run Identity | 未解决 | **已解决** | Run Identity Model I1-I6 + replay 证明 |
| RDQ-003 Issuer Contract | 未解决 | **已解决** | Issuer Contract C1-C7 |

---

## 未解决项（继承自 Rev-1）

| 项 | 严重度 | 状态 |
|---|---|---|
| FACT-018: Gate 不产生 ValidationEvent | BLOCKER（实现） | 设计已定，实现后补 |
| FACT-025: candidate_id/run_id 字段缺失 | BLOCKER（实现） | candidate_id 已存在（主键）；run_id 不再需要 |
| OQ-2: time-based expiration | NOTE | 当前设计不需要 |
| OQ-3: Freshness 窗口 | NOTE | 当前设计不需要 |
| AuthoritySnapshot 机制 | WARNING | 设计已定，实现后补 |
| Projection trigger timing | WARNING | Gate 运行后立即投影（设计已定） |
