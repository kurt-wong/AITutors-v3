# 88 — EB-008 Evidence Authority Enforcement：L2 Design Revision-1

**Document Type**: L2 Design Proposal Revision-1（回应 DSH adversarial review FACT-025~028）
**Authority Level**: L2（设计提案，不产生规范效力）
**Status**: DRAFT — PENDING SECOND ADVERSARIAL REVIEW
**Normative**: NO
**Supersedes**: `87_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_DESIGN.md` v0.1.0（作为 Revision-0）
**Superseded By**: —
**Gate State Authority**: NO（唯一权威是 `82 §3`）

**Version**: 1.0.0-revision1
**Date**: 2026-09-15
**Derives From**: `87` v0.1.0 · DSH adversarial review FACT-025~028 · `75_EVIDENCE_PROMOTION_CONTRACT.md` v1.1.0 · `20_Document_Pipeline.md §8.2/§8.3`
**May Change**: 本文档全部内容（draft 阶段）
**Must Not Change**: `20` Frozen Spec 任何字节 · `75` 五条冻结规则 R1–R5 · 生产代码 · Gate Policy · schema（实现阶段另行设计）

**分工**：
- Claude：负责设计修订（不实现）
- DSH：负责攻击验证（不重新设计）
- Owner：最终 DEC-013 裁决

---

## 0. Revision-1 变更摘要

Revision-0（87号）经 DSH adversarial review 发现四个必须解决的问题：

| FACT | 问题 | Revision-1 回应 |
|---|---|---|
| FACT-025 | ValidationEvent claim_id 是 document-local unit_id，缺 candidate/source_version/run identity binding | D4 重新定义 identity tuple；D5 引入 candidate_id 直接绑定 |
| FACT-026 | ValidationEvent 生命周期与 review_trail 持久化不一致，restart/replay 后 Authority 语义不明确 | D6 重新定义 persistence/lifecycle，区分 Event（不可变事实）与 Projection（可重算视图） |
| FACT-027 | Human authority producer 缺明确 issuer contract | D3 重新定位 Human Review，给出 Frozen Spec / L2 依据 |
| FACT-028 | IR Boundary 与 Admission Boundary 可能共享同一 evaluate decision，存在重复检查风险 | D9 证明两层防御不同 failure mode，定义独立检查机制 |

---

## 1. 已确认事实（OBSERVED）

### 1.1 Revision-0 遗留事实

| ID | 事实 | 证据 |
|---|---|---|
| FACT-012 | P3.2：4/4 attack vectors BYPASS Admission Boundary | `p32-enforcement-results.json` |
| FACT-013 | `AdmissionService.approve()` 仅检查 `gate_decision`，零 EvidencePromotion 引用 | `admission.py` 全文 grep |
| FACT-014 | `is_evidence_validated=False` 不阻断 Admission | P3.2 N2 实验 |
| FACT-015 | `VALID_VALIDATION_METHODS` 已包含 `"human_review"` | `evidence/models.py:158` |
| FACT-016 | `ValidationEvent.validator` 是 `str`，可承载 `"human/golden"` | `evidence/models.py:189` |
| FACT-017 | `EvidencePromotionService` 为 Phase 1 in-memory，零 DB 持久化 | `promotion.py:207` |
| FACT-019 | `record_validation_event` 对 `pending_review` 返回 `None` | `promotion.py:153-155` |
| FACT-020 | 20 §8.2 双入口：auto + human | `20_Document_Pipeline.md:585-616` |

### 1.2 DSH Adversarial Review 新发现

| ID | 事实 | 证据 |
|---|---|---|
| FACT-025 | ValidationEvent.claim_id = document-local unit_id；无 candidate_id / source_version_id / run_id 字段 | `models.py:185` `claim_id: str` |
| FACT-026 | ValidationEvent 为 in-memory（FACT-017）；review_trail 持久化在 Candidate JSON 中；两者生命周期不同步 | `promotion.py:207` vs `snapshot_repository.py` |
| FACT-027 | Human path 只写 review_trail entry（`verified_by`, `confirmed_fields`），不产生 ValidationEvent；无 issuer contract 定义谁有权签发 human Authority | `admission.py:97-102` |
| FACT-028 | IR Boundary（D7）与 Admission Boundary（D8）在 Revision-0 中都调用 `is_evidence_validated()`——同一底层检查，非独立防御 | `87 §D7/§D8` |

### 1.3 代码结构事实

| ID | 事实 | 证据 |
|---|---|---|
| FACT-021 | `EvidenceReference.source_version_id` 已存在（UUID） | `models.py:97` |
| FACT-022 | `EvidenceReference.reference_id = f"er-{span.span_id}"` | `models.py:112` |
| FACT-023 | `ValidationEvent.reference_ids: tuple[str, ...]` 指向 EvidenceReference | `models.py:190` |
| FACT-024 | `AppendOnlyEventLog` 已实现 event sourcing + 状态机 | `models.py:235-333` |

---

## 2. 设计问题 D1–D10（Revision-1）

### D1：Evidence Authority 的统一抽象

**OBSERVED**：
- 75 R4：「只有 ValidationEvent 产生 Evidence Authority」
- 75 §二 状态机：`VALIDATED EVIDENCE → state: trusted`
- 当前代码：`is_evidence_validated(claim_id)` 检查最新 ValidationEvent 是否为 `validated`
- Revision-0 问题：直接写「ValidationEvent = Authority」，混淆了事件与授权

**INFERRED**：
- ValidationEvent 是**不可变事实**（append-only event）
- Authority 是从事件链**推导出的当前状态**（可重算、可失效）
- 二者不是同一物：Event 是「曾经发生过验证」，Authority 是「此刻拥有授权」
- Event sourcing 模式中，Event 是 source of truth，State/Authority 是 projection

**PROPOSED**：

> **Evidence Authority 是一个 Projection（投影视图），不是 Event 本身，不是 mutable Domain State。**
>
> 它是从 ValidationEvent append-only log 确定性推导出的只读视图，回答：
> 「claim X 在当前时刻是否拥有进入 Semantic IR 和 Knowledge Asset Admission 的授权？」

Authority 的性质：

| 属性 | 值 | 原因 |
|---|---|---|
| 抽象类型 | **Projection** | 从 events 推导，非独立存储 |
| 可变性 | **不可变**（per event chain snapshot） | 任何变更 = 追加新 event → 重算 projection |
| 持久化 | **不直接持久化** | 从 DB 中的 events 重算（D6） |
| 确定性 | **是** | 同一 event chain → 同一 Authority state |

**DECISION CANDIDATE**: Authority = Projection（非 Event、非 Domain State）。

---

### D2：ValidationEvent 与 Authority 的关系

**OBSERVED**：
- 75 R4：「只有 ValidationEvent 产生 Evidence Authority」
- 75 §4.4：ValidationEvent 是「Event sourcing 模式 — 不是状态, 是事件」
- 75 §二 状态机：VALIDATED → INVALIDATED 是合法转换

**INFERRED**：
- ValidationEvent 是 Authority 的**唯一合法来源**（R4 冻结）
- 但 ValidationEvent ≠ Authority——Event 是「验证行为的记录」，Authority 是「验证结果的授权效果」
- 关系是因果：Event 产生 → Authority projection 更新

**PROPOSED**：

```text
ValidationEvent (append-only, immutable)
    │
    │  deterministic projection
    ▼
Evidence Authority (read-only view)
```

| 概念 | 定义 | 生命周期 |
|---|---|---|
| **ValidationEvent** | Authority Grant Event——记录「validator V 在时刻 T 对 claim C 做出了 validation_result R」的不可变事实 | append-only，永不修改 |
| **Evidence Authority** | 从 ValidationEvent chain 推导的当前授权状态 | 随 event chain 变化，可重算 |

Authority 推导规则：

```text
给定 claim_id C 的 event chain E(C) = [e1, e2, ..., en]（按 validated_at 排序）：

if E(C) 为空:
    Authority(C) = ABSENT
elif latest(E(C)).validation_result == "validated":
    Authority(C) = GRANTED（绑定于 latest event 的 identity tuple）
elif latest(E(C)).validation_result == "invalidated":
    Authority(C) = REVOKED
elif latest(E(C)).validation_result == "rejected":
    Authority(C) = DENIED
```

**DECISION CANDIDATE**: ValidationEvent 是 Authority Grant Event；Authority 是 projection。R4「只有 ValidationEvent 产生 Authority」的正确解读是「ValidationEvent 是 Authority 的唯一合法事件来源」，不是「ValidationEvent 就是 Authority」。

---

### D3：Human Review / Golden Review 定位

**OBSERVED**：
- 20 §8.2：human path 通过 `review_trail` entry（`verified_by: human|golden`）进入 `approve()`
- FACT-015：`VALID_VALIDATION_METHODS` 已包含 `"human_review"`（数据模型预留）
- FACT-027：当前 human path 只写 review_trail，不产生 ValidationEvent；无 issuer contract
- 75 §五 Trust Split：「Reliability 是 ValidationEvent 的属性 (怎么验证的)」——human_review 是 validation method，不是独立 authority channel
- Owner 裁决：「Human Review 不直接等价 Authority，而应通过统一机制产生 Authority」

**INFERRED**：
- 75 §4.4 的 `validation_method` 枚举已包含 `"human_review"`——数据模型设计初衷是 human review 产生 ValidationEvent
- 75 §五 Trust Split 将 human_review 定位为 reliability 维度（怎么验证的），不是独立 authority 类型
- 「人工可信」不是理由——理由是 human_review 是 ValidationEvent 的一种 validation_method，通过统一机制产生 Authority

**PROPOSED**：

**选择 B**：Human Review 产生 `ValidationEvent(validation_method="human_review")`，再由统一 projection 机制产生 Authority。

**Frozen Spec / L2 依据**：

| 依据 | 内容 | 来源 |
|---|---|---|
| 数据模型预留 | `VALID_VALIDATION_METHODS` 包含 `"human_review"` | `models.py:158`（75 §4.4 实现） |
| Trust Split | human_review 是 reliability 维度，不是独立 authority channel | 75 §五 |
| R4 统一性 | 「只有 ValidationEvent 产生 Authority」不排除 human review 产生 ValidationEvent | 75 R4 字面解读 |
| Owner 裁决 | 「Human Review 不直接等价 Authority，而应通过统一机制产生 Authority」 | EB-008 Owner 裁决 2026-09-15 |

**Issuer Contract（PROPOSED）**：

Human ValidationEvent 的签发需要明确 issuer contract：

```text
Human ValidationEvent 签发条件:
1. review_trail 中存在 {decision: approve, verified_by: human|golden, reviewer_id, confirmed_fields}
2. reviewer_id 必须是已认证的 reviewer（identity 来源待定义——OPEN QUESTION）
3. confirmed_fields 必须覆盖该 claim 的全部 content role
4. 签发动作本身是确定性的（从 review_trail entry 投影为 ValidationEvent），非人工直接创建 ValidationEvent
```

**关键区分**：
- review_trail entry = 人工决策的**审计记录**（谁在什么时候确认了什么）
- ValidationEvent = Authority Grant Event（统一机制产生的授权事件）
- 人工路径**同时产生两者**：review_trail（§8.2 合规）+ ValidationEvent（R4 合规）

**OPEN QUESTION OQ-1**: reviewer_id 的 identity 来源与认证机制（当前无 IAM 系统）。建议 Phase 1 接受任意非空字符串，Phase 2 引入认证。需 Owner 确认。

**DECISION CANDIDATE**: Human Review 选择 B——产生 ValidationEvent(validation_method="human_review")，通过统一 projection 产生 Authority。review_trail 是审计记录，不是 Authority。

---

### D4：Authority Identity Binding

**OBSERVED**：
- FACT-025：ValidationEvent 只有 `claim_id: str`（= document-local unit_id），无 candidate_id / source_version_id / run_id
- FACT-021：`EvidenceReference.source_version_id` 已存在
- `Candidate` 有 `source_version_id`、`id`（candidate_id）、`payload.ir_snapshot`
- Run context 当前隐式

**INFERRED**：
- Authority 必须 scoped 以防止 cross-run / cross-version / cross-candidate 污染
- P3.2 N3（cross-run evidence）/ N4（wrong SourceVersion）攻击面需要 identity binding 防御
- document_id 从 source_version_id 可推导（source_version → document），可能冗余

**PROPOSED**：

Authority Identity Tuple（必须绑定）：

```text
AuthorityIdentity = (
    source_version_id,   # 防止跨版本 authority transfer
    candidate_id,        # 防止跨 candidate authority transfer
    run_id,              # 防止跨 run contamination（P3.2 N3）
    claim_id,            # 标识被验证的 claim（unit 级）
)
```

| 字段 | 必须？ | 原因 |
|---|---|---|
| `source_version_id` | **MUST** | Authority 不得跨 SourceVersion 转移（P3.2 N4） |
| `candidate_id` | **MUST** | Authority 不得跨 Candidate 转移（FACT-025 核心问题） |
| `run_id` | **MUST** | Authority 不得跨 Run 转移（P3.2 N3） |
| `claim_id` | **MUST** | 标识被验证的具体 claim（unit 级粒度） |
| `document_id` | SHOULD | 从 source_version_id 可推导，但显式绑定可简化查询 |
| `evidence hash` | SHOULD | `reference_ids` 已链接 EvidenceReference，可间接追溯 |
| `content hash` | NICE | 用于 mutation detection（D6），非 identity 本身 |

**DECISION CANDIDATE**: AuthorityIdentity 四元组 = (source_version_id, candidate_id, run_id, claim_id)。document_id / evidence hash / content hash 为 SHOULD/NICE。

---

### D5：claim_id → candidate_id Identity Join

**OBSERVED**：
- FACT-025：ValidationEvent.claim_id = unit_id（document-local），无 candidate_id
- `Candidate.payload.ir_snapshot.units[].unit_id` 存在于 payload 中
- 当前无正式 join 定义

**INFERRED**：
- unit_id 是 document-local 的，不全局唯一
- 单靠 unit_id 无法确定性 join 到 candidate
- 需要在 ValidationEvent 中直接携带 candidate_id

**PROPOSED**：

**Join 来源**：ValidationEvent 直接携带 `candidate_id` 字段（schema 变更，实现阶段执行）。

```text
ValidationEvent {
    event_id: str
    claim_id: str              # unit_id（document-local）
    candidate_id: UUID         # 新增：直接绑定 candidate
    source_version_id: UUID    # 新增：直接绑定 source version
    run_id: UUID               # 新增：直接绑定 run
    validation_result: str
    validation_method: str
    validator: str
    reference_ids: tuple[str, ...]
    validated_at: datetime
}
```

**唯一性**：`(candidate_id, claim_id)` 二元组在 ValidationEvent log 中唯一标识一个 claim 的验证历史。

**不可伪造条件**：
- ValidationEvent 由 Gate（确定性函数）或 Human Review Projection（确定性投影）产生
- 任何模块不得手动创建 ValidationEvent（R4：「authority 不可手动设置」）
- candidate_id / source_version_id / run_id 由产生 ValidationEvent 的上下文自动填充，不由调用方传入

**Replay 行为**：
- 从 DB 加载全部 ValidationEvents
- 按 (candidate_id, claim_id) 分组
- 对每组取 latest event → 推导 Authority projection
- 结果与 replay 前一致（确定性）

**DECISION CANDIDATE**: ValidationEvent 增加 candidate_id / source_version_id / run_id 字段。Join = ValidationEvent.candidate_id == Candidate.id AND ValidationEvent.claim_id == unit_id ∈ Candidate.payload.ir_snapshot.units[]。

---

### D6：Authority Persistence / Lifecycle

**OBSERVED**：
- FACT-017：Phase 1 EvidencePromotion 为 in-memory
- FACT-026：ValidationEvent 与 review_trail 持久化不一致
- 75 §4.4：「只能追加 INVALIDATED event」
- FACT-024：`AppendOnlyEventLog` 已实现状态机

**INFERRED**：
- Authority 是 projection，不直接持久化——持久化的是 events
- Restart 后从 DB 加载 events → 重算 projection → Authority 恢复
- Source mutation（re-seal）应触发批量 INVALIDATED

**PROPOSED**：

**持久化**：ValidationEvent + EvidenceReference 写入 DB append-only 表。

**Restart**：从 DB 加载 events → 重建 AppendOnlyEventLog → 重算 Authority projection。无需独立 Authority 状态表。

**Replay**：确定性——同一 event chain → 同一 Authority state。

**Lifecycle 状态转换**：

| 事件 | Authority 状态变化 | 触发条件 |
|---|---|---|
| **CREATED** | ABSENT → GRANTED / DENIED | 首个 ValidationEvent（validated / rejected） |
| **VALIDATED** | — → GRANTED | ValidationEvent(validation_result="validated") |
| **INVALIDATED** | GRANTED → REVOKED | ValidationEvent(validation_result="invalidated") |
| **EXPIRED** | 不在当前设计中 | OPEN QUESTION OQ-2：是否需要 time-based expiration |

**Source Mutation 处理**：
- SourceVersion re-seal → 所有绑定该 source_version_id 的 ValidationEvents 追加 INVALIDATED
- 机制：批量 append INVALIDATED events（非修改历史 events）

**Candidate / Payload Mutation 处理**：
- Candidate payload 是冻结的（immutable after creation）
- 如果 payload 可变（当前设计不允许），Authority 需要 invalidation
- 结论：candidate immutability 是 Authority 有效性的前提

**OPEN QUESTION OQ-2**: 是否需要 time-based Authority expiration（EXPIRED 状态）？当前设计不需要——Authority 由 event chain 决定，不因时间流逝而失效。需 Owner 确认。

**DECISION CANDIDATE**: Authority 不直接持久化，从 DB events 重算。Restart/replay 确定性。Source mutation → 批量 INVALIDATED。Candidate immutability 是 Authority 有效性前提。

---

### D7：IR Boundary

**OBSERVED**：
- 75 R5：「Semantic IR 只能引用 ValidatedEvidence」
- 当前 IRBuilder 不检查 Authority
- FACT-028：Revision-0 的 IR Boundary 与 Admission Boundary 共享同一 `is_evidence_validated()` 检查

**INFERRED**：
- IR Boundary 不是「检查 Authority」这么简单——它定义 IR 生成的必要条件
- IR 生成后 Authority 必须绑定到 IR，防止后续 replay 时 Authority 状态与 IR 不一致

**PROPOSED**：

**IR 生成的必要条件（IR Boundary Invariant）**：

```text
IR 可以生成 ready 状态的必要条件：

1. 每个 ResolvedSpan 都有对应的 EvidenceReference（Proposal layer 完整）
2. 每个 EvidenceReference 都有至少一个 ValidationEvent
3. 每个 ValidationEvent 的 latest 状态 = "validated"
4. 每个 ValidationEvent 的 source_version_id == ResolvedRun.source_version_id
5. 每个 ValidationEvent 的 run_id == 当前 run_id
6. 全部 ValidationEvent 的 claim_id 覆盖 IR 中全部 leaf unit
```

任一条件不满足 → IR 无法生成 ready 状态 → candidate 保持 pending_review。

**IR 生成后 Authority 绑定**：

```text
IR 生成时，记录 AuthoritySnapshot:
{
    ir_id: str,
    authority_projection_hash: str,  # 全部 ValidationEvent event_id 的确定性 hash
    source_version_id: UUID,
    run_id: UUID,
    generated_at: datetime
}
```

IR 引用 AuthoritySnapshot，而非实时查询 Authority projection。这确保：
- IR 生成时的 Authority 状态被冻结
- 后续 Authority 变化（INVALIDATED）不 retroactively 改变已生成的 IR
- 但 Admission Boundary 会重新检查当前 Authority（D8）

**DECISION CANDIDATE**: IR Boundary 定义 6 项必要条件 + AuthoritySnapshot 绑定。IR 生成后 Authority 状态被冻结为 snapshot。

---

### D8：Admission Boundary

**OBSERVED**：
- P3.2 证明：Admission 当前不 enforce Authority（FACT-012/013/014）
- `approve()` 当前流程：lock → status check → gate_decision check → source check → `_materialize()` → event → transition

**INFERRED**：
- Admission 需要验证的不只是 Authority existence——还需要 validity、identity match、freshness
- FACT-028 警告：如果 Admission 只是重复 IR Boundary 的检查，就不是 defense-in-depth

**PROPOSED**：

**Admission 必须验证的四项**：

| 检查项 | 必要？ | 内容 | 防御的 failure mode |
|---|---|---|---|
| **Existence** | **MUST** | 每个 leaf unit 有至少一个 ValidationEvent | 无验证记录的 candidate 被物化 |
| **Validity** | **MUST** | latest ValidationEvent = "validated" | 被 invalidated/rejected 的 evidence 被物化 |
| **Identity Match** | **MUST** | ValidationEvent.candidate_id == Candidate.id AND source_version_id 匹配 AND run_id 匹配 | 跨 candidate/version/run 的 authority transfer（P3.2 N3/N4） |
| **Freshness** | SHOULD | ValidationEvent.validated_at 在当前 run 的时间窗口内 | 过期 authority（OQ-3：时间窗口定义待定） |

**Admission Boundary Invariant**：

```text
approve() 步骤 4.5（新增）:

verify_admission_authority(candidate):
    leaf_units = _leaf_units(candidate.payload.ir_snapshot.units)
    for unit_id in leaf_units:
        events = db.load_validation_events(candidate.id, unit_id)
        if not events:
            raise EvidenceAuthorityError("no ValidationEvent for unit")
        latest = max(events, key=lambda e: e.validated_at)
        if latest.validation_result != "validated":
            raise EvidenceAuthorityError("latest event not validated")
        if latest.candidate_id != candidate.id:
            raise EvidenceAuthorityError("candidate_id mismatch")
        if latest.source_version_id != candidate.source_version_id:
            raise EvidenceAuthorityError("source_version mismatch")
        if latest.run_id != current_run_id:
            raise EvidenceAuthorityError("run_id mismatch")
    return True  # all checks passed
```

**Fail-closed 语义**：任何检查失败 → raise → ROLLBACK → candidate 保持 pending_review。

**DECISION CANDIDATE**: Admission 验证 Existence + Validity + Identity Match（MUST）+ Freshness（SHOULD）。检查逻辑独立于 IR Boundary。

---

### D9：两层 Enforcement 的差异

**OBSERVED**：
- FACT-028：Revision-0 中 IR Boundary 和 Admission Boundary 都调用 `is_evidence_validated()`——同一底层检查
- 这意味着绕过一层 = 绕过两层（不是 defense-in-depth）

**INFERRED**：
- Defense-in-depth 要求两层**独立**——使用不同的检查机制，防御不同的 failure mode
- IR Boundary 防御的是「unvalidated evidence 进入 IR」（数据质量问题）
- Admission Boundary 防御的是「unvalidated candidate 被物化」（不可逆动作问题）

**PROPOSED**：

| 维度 | IR Boundary | Admission Boundary |
|---|---|---|
| **检查时机** | IR 构建时（compile 阶段） | approve() 物化前（admission 阶段） |
| **检查对象** | ResolvedSpan → EvidenceReference → ValidationEvent | Candidate → leaf units → ValidationEvent |
| **检查内容** | 6 项必要条件（D7） | 4 项检查（D8） |
| **失败语义** | IR 无法生成 ready 状态 | ROLLBACK + pending_review |
| **防御的 failure mode** | unvalidated evidence 污染 Semantic IR | unvalidated candidate 被物化为 Knowledge Asset |
| **独立性** | 检查 EvidenceReference → ValidationEvent 链 | 检查 Candidate → ValidationEvent 直接绑定 |

**关键区别**：
- IR Boundary 检查的是 **evidence 层**（每个 ResolvedSpan 是否有 validated Authority）
- Admission Boundary 检查的是 **candidate 层**（整个 Candidate 的全部 leaf unit 是否有 validated Authority + identity match）

**为什么不是重复检查**：
1. IR Boundary 在 compile 阶段，Admission Boundary 在 admission 阶段——时间上分离
2. IR Boundary 检查 evidence 链完整性，Admission Boundary 检查 candidate identity match——内容上不同
3. 如果 IR Boundary 被绕过（e.g., 手动构造 IR），Admission Boundary 仍能拦截
4. 如果 Admission Boundary 被绕过（e.g., 直接调用 _materialize()），IR Boundary 已在更早阶段阻断

**DECISION CANDIDATE**: 两层 enforcement 防御不同 failure mode，使用独立检查机制。IR Boundary 检查 evidence 链，Admission Boundary 检查 candidate identity + validity。

---

### D10：双入口兼容

**OBSERVED**：
- 20 §8.2：两个合法入口（auto + human）
- 两条路径汇入同一 Admission Transaction
- 20 §8.2 冻结：「无任一入口的候选永久 pending_review，不得静默消失」

**INFERRED**：
- Authority enforcement 增加的是前置条件，不是移除路径
- 两条路径的差异在于「谁产生 ValidationEvent」，不在于「Authority 如何被检查」

**PROPOSED**：

| §8.2 要求 | Authority enforcement 后 | 验证 |
|---|---|---|
| 自动路径存在 | ✅ Gate 产生 ValidationEvent(validated) → Authority GRANTED | D3 |
| 人工路径存在 | ✅ Human Review 产生 ValidationEvent(human_review) → Authority GRANTED | D3 |
| 汇入同一 Admission Transaction | ✅ Authority check 在事务内，失败 ROLLBACK | D8 |
| 无入口的候选永久 pending_review | ✅ 缺 Authority 的候选保持 pending_review | D8 fail-closed |

**统一机制**：

```text
自动路径:
  Gate.evaluate() → gate_decision=auto_approve
    → record_validation_event(claim_id, gate_decision)
    → ValidationEvent(validated, validator="gate/v1")
    → Authority projection: GRANTED

人工路径:
  Human review → review_trail entry (§8.2 audit)
    → project_validation_event(review_trail_entry)
    → ValidationEvent(validated, validator="human/{reviewer_id}", method="human_review")
    → Authority projection: GRANTED

两条路径汇入:
  approve() → verify_admission_authority(candidate) → _materialize()
```

**§8.2 文本不需要修改**：Authority 是新增前置条件。人工路径现在同时产生 review_trail（§8.2 合规）和 ValidationEvent（R4 合规），这是 D3 选项 B 的直接推论。

**DECISION CANDIDATE**: 双入口保持统一。差异在 ValidationEvent 产生者（Gate vs Human Review Projection），不在 Authority 检查机制。

---

## 3. 架构总览（Revision-1 PROPOSED）

```text
SourceVersion (sealed)
    ↓
Resolver → ResolvedSpan
    ↓
EvidenceReference (Proposal layer, R2: no authority)
    │  source_version_id ✅
    ↓
EvidenceClaim (promotion request, R3: not truth assertion)
    ↓
┌─────────────────────────────────────────────────────────────┐
│  ValidationEvent (Authority Grant Event, R4)                 │
│  Identity: (source_version_id, candidate_id, run_id, claim_id)│
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────────┐   │
│  │ Gate (auto)        │    │ Human Review Projection       │   │
│  │ → validated        │    │ → validated                   │   │
│  │ validator=gate/v1  │    │ validator=human/{reviewer_id} │   │
│  │ method=frozen_rule │    │ method=human_review           │   │
│  └──────────────────┘    └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
    │
    │  deterministic projection (D1/D2)
    ▼
Evidence Authority (read-only view)
    │
    ├──→ IR Boundary (D7): 6 necessary conditions + AuthoritySnapshot
    │         ↓
    │    Semantic IR (sealed with AuthoritySnapshot)
    │
    └──→ Admission Boundary (D8): Existence + Validity + Identity Match
              ↓
         Knowledge Asset (A domain)
```

---

## 4. 与现有 Spec 的兼容性分析

| Spec 条款 | 兼容性 | 说明 |
|---|---|---|
| 20 §8.2 双入口 | ✅ | 两条路径都保持，Authority 是新增前置 |
| 20 §8.2 物化事务 | ✅ | Authority check 在事务内，失败 ROLLBACK |
| 20 §8.2 gate_decision 不可变 | ✅ | Authority check 不修改 gate_decision |
| 20 §8.3 verified_correct | ✅ | verified_correct 语义不变，Authority 是证据信任状态 |
| 75 R1–R3 | ✅ | 不涉及 |
| 75 R4 | ✅ | ValidationEvent 是 Authority 唯一事件来源（projection 解读） |
| 75 R5 | ✅ | IR Boundary enforcement 闭合 R5 |
| 75 §4.4 validation_method | ✅ | "human_review" 已在枚举中（FACT-015） |
| 75 §五 Trust Split | ✅ | human_review 是 reliability 维度，不是独立 authority channel |
| 75 状态机 | ✅ | VALIDATED → INVALIDATED 已支持 |
| 10 §5.4 物化事务 | ✅ | Authority check 是事务内新增步骤 |

---

## 5. 待裁决事项汇总

| D# | 裁决点 | Owner 选项 | 状态 |
|---|---|---|---|
| D1 | Authority = Projection（非 Event、非 Domain State） | 确认 / 修正 | DECISION CANDIDATE |
| D2 | ValidationEvent 是 Authority Grant Event；Authority 是 projection | 确认 / 修正 | DECISION CANDIDATE |
| D3 | Human Review 选择 B（产生 ValidationEvent）+ issuer contract | 确认 / 修正 | DECISION CANDIDATE |
| D4 | AuthorityIdentity 四元组 = (source_version_id, candidate_id, run_id, claim_id) | 确认 / 修正 | DECISION CANDIDATE |
| D5 | ValidationEvent 增加 candidate_id / source_version_id / run_id 字段 | 确认 / 修正 | DECISION CANDIDATE |
| D6 | Authority 从 DB events 重算；source mutation → 批量 INVALIDATED | 确认 / 修正 | DECISION CANDIDATE |
| D7 | IR Boundary 6 项必要条件 + AuthoritySnapshot | 确认 / 修正 | DECISION CANDIDATE |
| D8 | Admission 验证 Existence + Validity + Identity Match + Freshness | 确认 / 修正 | DECISION CANDIDATE |
| D9 | 两层 enforcement 防御不同 failure mode，独立检查机制 | 确认 / 修正 | DECISION CANDIDATE |
| D10 | 双入口统一，差异在 ValidationEvent 产生者 | 确认 / 修正 | DECISION CANDIDATE |

### OPEN QUESTION

| ID | 问题 | 影响 |
|---|---|---|
| OQ-1 | reviewer_id 的 identity 来源与认证机制（当前无 IAM） | D3 issuer contract |
| OQ-2 | 是否需要 time-based Authority expiration（EXPIRED 状态） | D6 lifecycle |
| OQ-3 | Freshness 检查的具体时间窗口定义 | D8 Admission check |

---

## 6. 需要 DSH 攻击的问题

| 攻击目标 | 攻击向量 | 预期防御 |
|---|---|---|
| D4 identity binding | 构造 candidate_id 不匹配的 ValidationEvent | Admission Boundary Identity Match 检查 |
| D5 join 唯一性 | 构造重复 (candidate_id, claim_id) 的 ValidationEvent | DB UNIQUE 约束 + 状态机 |
| D6 replay 确定性 | 修改 DB 中的 ValidationEvent 后 replay | append-only 表 + 无 UPDATE/DELETE |
| D7 AuthoritySnapshot | IR 生成后 INVALIDATED，检查 IR 是否受影响 | AuthoritySnapshot 冻结 + Admission Boundary 重新检查 |
| D9 独立性 | 绕过 IR Boundary 后尝试 Admission | Admission Boundary 独立检查 |
| D3 human path | 构造无效 review_trail entry 尝试产生 ValidationEvent | issuer contract 验证 |

---

## 7. 明确不主张

- 本文档**不是** L2 Decision Record（待 DSH 二次 adversarial review + Owner DEC-013 终裁）
- **不修改**任何生产代码
- **不修改**任何 Frozen Spec
- **不修改** schema（D5 的 schema 变更是设计提案，实现阶段执行）
- **不实现** workaround
- **不提交** migration

---

## 8. 下一步

1. **DSH 二次 adversarial review**：对 Revision-1 的 D1–D10 逐项攻击
2. **Owner DEC-013 终裁**：基于二次 review 结果裁决
3. **升 L2 Decision Record**：DEC-013 通过后正式升格
4. **Implementation**：L2 Decision 生效后方可进入编码

---

## 附录 A：Revision-0 → Revision-1 变更对照

| D# | Revision-0 | Revision-1 | 变更原因 |
|---|---|---|---|
| D1 | ValidationEvent = Authority | Authority = Projection | 混淆事件与授权 |
| D2 | 未区分 Event 与 Authority | ValidationEvent = Grant Event；Authority = projection | FACT-026 |
| D3 | 选项 α/β/γ 列出 | 选择 B + issuer contract | FACT-027 + Owner 方向 |
| D4 | 四元组（无 candidate_id） | 四元组（含 candidate_id） | FACT-025 |
| D5 | unit_id join | candidate_id 直接绑定 | FACT-025 |
| D6 | 简述持久化 | 详细 lifecycle + source mutation 处理 | FACT-026 |
| D7 | 「检查 Authority」 | 6 项必要条件 + AuthoritySnapshot | FACT-028 |
| D8 | 「检查 Authority」 | 4 项检查（Existence/Validity/Identity/Freshness） | FACT-028 |
| D9 | 未证明独立性 | 证明两层防御不同 failure mode | FACT-028 |
| D10 | 兼容性表格 | 统一机制 + 路径图 | 深化 |
