# 87 — EB-008 Evidence Authority Enforcement：L2 Design Proposal

**Document Type**: L2 Design Proposal（非 Decision Record——待 DSH adversarial review + Owner 终裁后方可升 L2 Decision）
**Authority Level**: L2（设计提案，不产生规范效力）
**Status**: DRAFT — PENDING ADVERSARIAL REVIEW
**Normative**: NO
**Supersedes**: —
**Superseded By**: —
**Gate State Authority**: NO（唯一权威是 `82 §3`）

**Version**: 0.1.0-draft
**Date**: 2026-09-15
**Derives From**: `75_EVIDENCE_PROMOTION_CONTRACT.md` v1.1.0 · `20_Document_Pipeline.md §8.2/§8.3` · P3.2/EB-004 实验（FACT-012/013/014）
**May Change**: 本文档全部内容（draft 阶段）
**Must Not Change**: `20` Frozen Spec 任何字节 · `75` 五条冻结规则 R1–R5 · 生产代码 · Gate Policy

---

## 0. 裁决背景

**EB-008 Owner 裁决（2026-09-15）**：

1. **方向 B 确认**：Evidence Authority 是 Semantic IR 与 Knowledge Asset Admission 的**准入前置条件**，不接受降级为纯审计记录。
2. **Option C 暂不接受**：「human review = Evidence Authority / 更高 Authority」是 INFERRED/PROPOSED，不是 Frozen Fact。20 §8.2 允许 human review 进入 Admission **不自动等价于** 75 R4 所定义的 Evidence Authority。
3. **进入 L2 Design 阶段**，不进入 implementation。

**DEC-012（冻结）**：裁决前两侧不设计不实现、不改 Admission。

**本文档使命**：回答 D1–D10，为 Owner 终裁提供完整设计基础。完成后交 DSH adversarial review。

---

## 1. 已确认事实（OBSERVED）

| ID | 事实 | 证据 |
|---|---|---|
| FACT-012 | P3.2：4/4 attack vectors BYPASS Admission Boundary | `p32-enforcement-results.json` |
| FACT-013 | `AdmissionService.approve()` 仅检查 `gate_decision`，零 EvidencePromotion 引用 | `admission.py` 全文 grep |
| FACT-014 | `is_evidence_validated=False` 不阻断 Admission | P3.2 N2 实验 |
| FACT-015 | `VALID_VALIDATION_METHODS` 已包含 `"human_review"` | `evidence/models.py:158` |
| FACT-016 | `ValidationEvent.validator` 是 `str`，可承载 `"human/golden"` | `evidence/models.py:189` |
| FACT-017 | `EvidencePromotionService` 为 Phase 1 in-memory，零 DB 持久化 | `promotion.py:207` |
| FACT-018 | `is_evidence_validated` 在 `backend/app` 下零生产调用方 | 全仓 grep |
| FACT-019 | `record_validation_event` 对 `pending_review` 返回 `None`（不产生事件） | `promotion.py:153-155` |
| FACT-020 | 20 §8.2 双入口：auto（gate_decision=auto_approve）+ human（review_trail） | `20_Document_Pipeline.md:585-616` |

---

## 2. 设计问题 D1–D10

### D1：Evidence Authority 的统一抽象是什么？

**OBSERVED**：
- 75 §三 R4：「只有 ValidationEvent 产生 Evidence Authority」
- 75 §二 状态机：`VALIDATED EVIDENCE → state: trusted` 是进入 Semantic IR 的唯一合法状态
- 75 §4.5：`ValidatedEvidence` 是唯一可进入 IR 的证据状态
- 当前代码：`is_evidence_validated(claim_id)` 检查最新 ValidationEvent 是否为 `validated`

**INFERRED**：
- Evidence Authority 不是证据本体、不是引用、不是声明——它是 ValidationEvent 授予的**信任状态**
- 该状态绑定于：特定 claim × 特定 evidence reference × 特定 run context × 特定 SourceVersion
- 它有生命周期：未验证 → validated → invalidated（event sourcing，不可变历史）

**PROPOSED**：

> **Evidence Authority = ValidationEvent 授予的、绑定于 (claim_id, reference_ids, source_version_id, run_id) 四元组的信任状态。该状态是 Semantic IR 引用证据（R5）和 Admission 物化 Knowledge Asset 的必要前置条件。**

Authority 不是布尔值，不是 mutable field，是 append-only event chain 的推导结果。

**DECISION needed**: Owner 确认此抽象是否成立。

---

### D2：R4 ValidationEvent 与 human/golden review 的关系是什么？

**OBSERVED**：
- 75 R4：「只有 ValidationEvent 产生 Evidence Authority」
- 20 §8.2：human path 通过 `review_trail` entry（`verified_by: human|golden`）进入 `approve()`
- 当前代码：`review_trail` 和 `ValidationEvent` 是完全独立的机制，互不引用
- FACT-015：`VALID_VALIDATION_METHODS` 已包含 `"human_review"`（数据模型已预留）
- FACT-016：`ValidationEvent.validator` 是 `str`，可承载 `"human/golden"`
- Owner 裁决：「human review = Evidence Authority」是 INFERRED/PROPOSED，不是 Frozen Fact

**INFERRED**：
- 数据模型（`VALID_VALIDATION_METHODS` 包含 `"human_review"`）暗示设计初衷允许 human review 产生 ValidationEvent
- 但当前实现从未使用此路径——human review 只写 `review_trail`，不产生 ValidationEvent
- 75 R4 的字面含义「只有 ValidationEvent 产生 Authority」并不排除 human review 产生 ValidationEvent——它排除的是「绕过 ValidationEvent 直接设置 Authority」

**PROPOSED（三选项，待 Owner 裁决）**：

| 选项 | 方案 | 优点 | 风险 |
|---|---|---|---|
| **α** | Human review 产生 ValidationEvent（`validation_method="human_review"`, `validator="human/golden"`）。统一 Authority 于 R4 之下。 | 数据模型已预留；单一 Authority 概念；R5 enforcement 统一 | 改变 review_trail 的语义定位（从 Authority 来源降级为审计记录） |
| **β** | Evidence Authority 有两个产生者：ValidationEvent（machine）+ HumanAuthorityEvent（human）。R4 需修正为「Authority 由且仅由 ValidationEvent 或 HumanReviewEvent 产生」。 | 尊重 human/machine 本质差异 | 引入第二种 Authority 类型，增加复杂度；R4 修正需 L0 变更流程 |
| **γ** | Human review 不经过 R4，是独立 Authority 通道（Owner 已倾向不接受）。 | 最小改动 | 违反 R4 统一性；P3.2 N7/N8 攻击面仍存在 |

**DECISION needed**: Owner 选择 α / β / γ，或提出替代方案。

---

### D3：自动入口和人工入口分别如何获得 Authority？

**OBSERVED**：
- 自动路径：Gate evaluate → `gate_decision=auto_approve` → `record_validation_event()` 创建 `ValidationEvent(validated)`（FACT-019：`pending_review` 不产生事件）
- 人工路径：human review → `review_trail` entry → `approve()`（当前无 ValidationEvent 产生）

**INFERRED**：
- 自动路径已有 Authority 产生机制（ValidationEvent from Gate），只是未被 Admission 消费
- 人工路径当前无 Authority 产生机制（在 R4 框架下）

**PROPOSED（基于 D2 选项 α）**：

| 入口 | Authority 来源 | 机制 |
|---|---|---|
| 自动 | Gate 产生的 ValidationEvent | `record_validation_event(claim_id, gate_decision)` → `ValidationEvent(validated)` |
| 人工 | Human review 产生的 ValidationEvent | Human review action → 同时写 `review_trail`（§8.2 合规）+ 创建 `ValidationEvent(validation_method="human_review", validator="human/golden")`（R4 合规） |

两条路径最终都产生 ValidationEvent → 统一 Authority 概念 → R5 enforcement 一致。

**DECISION needed**: 确认此双路径 Authority 产生机制。

---

### D4：Authority 如何与 SourceVersion、Evidence/Claim、candidate、run 绑定？

**OBSERVED**：
- `EvidenceReference` 已有 `source_version_id`（`models.py:97`）
- `ValidationEvent` 已有 `claim_id` + `reference_ids`（`models.py:185-191`）
- `Candidate` 有 `source_version_id`、`annotation_id`、`payload.ir_snapshot`
- Run context 当前隐式（in-memory per GateService.run() call）

**INFERRED**：
- Authority 必须 scoped 以防止 cross-run / cross-version 污染（P3.2 N3/N4 攻击面）
- `source_version_id` 已在 EvidenceReference 中，可追溯
- `run_id` 当前缺失，需要引入

**PROPOSED**：

Authority 绑定四元组：

```text
Authority = (claim_id, reference_ids, source_version_id, run_id)
```

| 维度 | 来源 | 约束 |
|---|---|---|
| `claim_id` | ValidationEvent.claim_id | 必须是 candidate IR 中的 unit_id |
| `reference_ids` | ValidationEvent.reference_ids | 必须指向同一 ResolvedRun 产生的 EvidenceReference |
| `source_version_id` | EvidenceReference.source_version_id | 必须与 Candidate.source_version_id 一致 |
| `run_id` | 新增字段（ValidationEvent + EvidenceReference） | 必须与 Candidate 所属 run 一致 |

**DECISION needed**: 确认四元组绑定模型；确认 `run_id` 引入方式。

---

### D5：claim_id → candidate_id 的正式 identity join 如何成立？

**OBSERVED**：
- `ValidationEvent.claim_id` 当前设置为 `unit_id`（`promotion.py:173`）
- `Candidate.payload.ir_snapshot.units[].unit_id` 存在于 payload 中
- 当前无正式 join 定义

**INFERRED**：
- Join 必须确定性（BIND-1 原则：禁 fuzzy / 相似度 / 重跑 Resolver）
- `unit_id` 是天然桥梁

**PROPOSED**：

```text
join: ValidationEvent.claim_id == Candidate.payload.ir_snapshot.units[].unit_id
```

**Candidate Authority 判定**：Candidate 的全部 leaf unit（D8：composite parent 不物化行）都有 `validated` 状态的 ValidationEvent → Candidate 具备 Authority。

纯函数，无 fuzzy matching：

```python
def candidate_has_authority(candidate, promotion_service) -> bool:
    leaf_unit_ids = _leaf_units(candidate.payload["ir_snapshot"]["units"])
    return all(
        promotion_service.is_evidence_validated(uid)
        for uid in leaf_unit_ids
    )
```

**DECISION needed**: 确认 join 路径与 all-leaf-units 判定规则。

---

### D6：Authority 如何持久化、失效、replay，并处理 restart？

**OBSERVED**：
- FACT-017：Phase 1 EvidencePromotion 为 in-memory，零 DB 持久化
- 75 §4.4：「未来一定会遇到：OCR 模型升级 / source version 变化 / Resolver bug 修复 / 人工重新审核。届时不能修改历史，只能追加 INVALIDATED event」
- `AppendOnlyEventLog` 已实现 event sourcing + 状态机（`models.py:235-333`）

**INFERRED**：
- 生产环境 Authority 必须跨 restart 存活
- Authority 必须可失效（source re-seal、evidence 发现错误等）
- Replay 必须能从 events 重建状态

**PROPOSED**：

| 能力 | 方案 |
|---|---|
| **持久化** | `ValidationEvent` + `EvidenceReference` 写入 DB append-only 表（新 migration） |
| **失效** | 追加 `ValidationEvent(result="invalidated")`（状态机已支持：VALIDATED → INVALIDATED） |
| **Replay** | 读取全部 events → 重建 `AppendOnlyEventLog` → 确定性推导当前 Authority 状态 |
| **Restart** | Authority 状态在 DB 中，restart 后从 DB 加载，天然存活 |

**DB Schema（PROPOSED）**：

```sql
CREATE TABLE validation_events (
    event_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    validation_result TEXT NOT NULL,  -- validated | rejected | invalidated
    validation_method TEXT NOT NULL,
    validator TEXT NOT NULL,
    checks JSONB NOT NULL,
    reference_ids TEXT[] NOT NULL,
    run_id UUID,                      -- D4 新增
    validated_at TIMESTAMPTZ NOT NULL
);
-- append-only: 无 UPDATE / DELETE

CREATE TABLE evidence_references (
    reference_id TEXT PRIMARY KEY,
    span_id TEXT NOT NULL,
    proposed_role TEXT NOT NULL,
    producer_type TEXT NOT NULL,
    model TEXT,
    source_version_id UUID NOT NULL,
    run_id UUID,                      -- D4 新增
    created_at TIMESTAMPTZ NOT NULL
);
-- append-only: 无 UPDATE / DELETE
```

**DECISION needed**: 确认持久化方案与 DB schema 方向。

---

### D7：Semantic IR 入口如何 enforce R5？

**OBSERVED**：
- 75 R5：「Semantic IR 只能引用 ValidatedEvidence，不允许越级引用任何前置层」
- 当前 `IRBuilder` 不检查 Evidence Authority
- IR 从 `ResolvedRun` + annotation 构建

**INFERRED**：
- R5 enforcement point 应在 IR 构建入口（或紧邻其前）
- 如果任何引用的 evidence 缺 Authority → IR 构建失败（fail-closed）

**PROPOSED**：

IR Boundary enforcement（第一层）：

```text
IRBuilder.build() 入口:
  1. 遍历 ResolvedRun.resolved_spans
  2. 对每个 span，检查其 EvidenceReference 是否有 validated ValidationEvent
  3. 任一 span 缺 Authority → raise EvidenceAuthorityError
  4. 全部通过 → 构建 IR（此时 IR 中的 evidence 均为 ValidatedEvidence）
```

Fail-closed 语义：缺 Authority ≠ 拒绝候选，而是 **IR 无法构建 ready 状态** → candidate 保持 `pending_review`。

**与两层 enforcement 的关系**：IR Boundary 是第一层（防止 unvalidated evidence 进入 IR），Admission Boundary 是第二层（防止 unvalidated candidate 进入物化）。两层独立生效，任一层拒绝即阻断。

**DECISION needed**: 确认 IR Boundary enforcement 位置与 fail-closed 语义。

---

### D8：Admission Boundary 如何 enforce Authority？

**OBSERVED**：
- P3.2 证明：Admission 当前不 enforce Authority（FACT-012/013/014）
- `approve()` 当前流程：lock → status check → gate_decision check → source check → `_materialize()` → event → transition

**INFERRED**：
- Enforcement 必须在 `_materialize()` 之前
- 必须 fail-closed

**PROPOSED**：

Admission Boundary enforcement（第二层）：

```text
approve() 流程（新增步骤 4.5）:
  1. lock candidate
  2. check decision_status == pending_review
  3. check gate_decision != rejected
  4. check source (auto/human)
  4.5. verify_evidence_authority(candidate)   ← 新增
  5. _materialize()
  6. create_admission_event
  7. transition to approved
```

`verify_evidence_authority` 检查：
- Candidate 的全部 leaf unit 有 validated ValidationEvent（D5 join）
- ValidationEvent 的 source_version_id 与 Candidate 一致（D4 binding）
- ValidationEvent 的 run_id 与 Candidate 一致（D4 binding）

失败 → raise `EvidenceAuthorityError` → 外层不 COMMIT → 整体 ROLLBACK → candidate 保持 `pending_review`。

**DECISION needed**: 确认 Admission Boundary enforcement 位置与语义。

---

### D9：Admission 物化事务中 check 的精确位置与 fail-closed/pending_review 语义

**OBSERVED**：
- 当前 `approve()` 是物化事务：lock → 校验 → 物化 → event → transition，同一 DB 事务原子完成
- 任一步失败 → 异常上抛 → 调用方不 COMMIT → 整体 ROLLBACK → candidate 保持 `pending_review`

**INFERRED**：
- Authority check 失败的语义应与现有失败模式一致：ROLLBACK + pending_review
- Authority check 失败 ≠ rejected（rejected 是 structural/semantic contradiction 的 terminal 状态）

**PROPOSED**：

| 场景 | 行为 | candidate 终态 |
|---|---|---|
| Authority check 通过 | 继续 `_materialize()` | `approved` |
| Authority check 失败（无 ValidationEvent） | raise `EvidenceAuthorityError` | `pending_review`（ROLLBACK） |
| Authority check 失败（ValidationEvent 被 invalidated） | raise `EvidenceAuthorityError` | `pending_review`（ROLLBACK） |
| Authority check 失败（source_version 不匹配） | raise `EvidenceAuthorityError` | `pending_review`（ROLLBACK） |

**不做的事**：
- 不 transition 到 `rejected`（Authority 缺失 ≠ 语义矛盾）
- 不静默跳过（fail-closed）
- 不修改 `gate_decision`（不可变，20 §8.2 冻结）

**与 §8.2 双入口的兼容性**：Authority check 在 source check 之后、`_materialize()` 之前。两条路径（auto/human）都经过此 check。check 的输入是 ValidationEvent（D2/D3 统一后的 Authority 来源），不是 `review_trail` 或 `gate_decision`。

**DECISION needed**: 确认 check 位置、fail-closed 语义、与 rejected 的区分。

---

### D10：如何保证 20 §8.2 双入口不被破坏？

**OBSERVED**：
- 20 §8.2：两个合法入口（auto + human）
- 两条路径汇入同一 Admission Transaction
- 20 §8.2 冻结：「无任一入口的候选永久 pending_review，不得静默消失」

**INFERRED**：
- Authority check 增加的是**前置条件**，不是移除路径
- 两条路径都仍然合法，只是都需要满足 Authority 要求

**PROPOSED**：

| §8.2 要求 | Authority enforcement 后 |
|---|---|
| 自动路径存在 | ✅ 保持。gate_decision=auto_approve → Gate 产生 ValidationEvent → Authority 已具备 |
| 人工路径存在 | ✅ 保持。Human review → review_trail + ValidationEvent → Authority 已具备 |
| 汇入同一 Admission Transaction | ✅ 保持。Authority check 在事务内，失败 ROLLBACK |
| 无入口的候选永久 pending_review | ✅ 保持。缺 Authority 的候选也保持 pending_review |

**§8.2 文本不需要修改**：Authority 是新增前置条件，不改变现有前置条件的语义。

**唯一变化**：人工路径现在需要**同时**产生 `review_trail` entry（§8.2 合规）和 `ValidationEvent`（R4 合规）。这是 D2 选项 α 的直接推论。

**DECISION needed**: 确认 §8.2 兼容性分析。

---

## 3. 架构总览（PROPOSED）

```text
SourceVersion (sealed)
    ↓
Resolver → ResolvedSpan
    ↓
EvidenceReference (Proposal layer, R2: no authority)
    ↓
EvidenceClaim (promotion request, R3: not truth assertion)
    ↓
┌─────────────────────────────────────────────────────┐
│  ValidationEvent (R4: only source of Authority)      │
│  ┌──────────────┐    ┌──────────────────────┐       │
│  │ Gate (auto)   │    │ Human Review          │       │
│  │ → validated   │    │ → human_review        │       │
│  └──────────────┘    └──────────────────────┘       │
└─────────────────────────────────────────────────────┘
    ↓
ValidatedEvidence (state: trusted)
    ↓
┌──────────────────┐    ┌──────────────────────────┐
│ IR Boundary (R5)  │    │ Admission Boundary        │
│ IRBuilder checks  │    │ approve() checks          │
│ Authority before  │    │ Authority before          │
│ IR construction   │    │ _materialize()            │
└──────────────────┘    └──────────────────────────┘
    ↓                         ↓
Semantic IR              Knowledge Asset (A domain)
```

**两层 enforcement**：
- **IR Boundary**（D7）：防止 unvalidated evidence 进入 Semantic IR
- **Admission Boundary**（D8）：防止 unvalidated candidate 进入物化

两层独立生效，任一层拒绝即阻断。

---

## 4. 与现有 Spec 的兼容性分析

| Spec 条款 | 兼容性 | 说明 |
|---|---|---|
| 20 §8.2 双入口 | ✅ | 两条路径都保持，Authority 是新增前置 |
| 20 §8.2 物化事务 | ✅ | Authority check 在事务内，失败 ROLLBACK |
| 20 §8.2 gate_decision 不可变 | ✅ | Authority check 不修改 gate_decision |
| 20 §8.3 verified_correct | ✅ | verified_correct 语义不变（答案正确性），Authority 是证据信任状态 |
| 75 R1–R3 | ✅ | 不涉及 |
| 75 R4 | ✅ | 统一 Authority 于 ValidationEvent（D2 选项 α） |
| 75 R5 | ✅ | IR Boundary enforcement 闭合 R5 |
| 75 状态机 | ✅ | VALIDATED → INVALIDATED 已支持 |
| 10 §5.4 物化事务 | ✅ | Authority check 是事务内新增步骤 |

---

## 5. 待裁决事项汇总

| D# | 裁决点 | Owner 选项 |
|---|---|---|
| D1 | Evidence Authority 统一抽象 | 确认 / 修正 |
| D2 | R4 ValidationEvent 与 human review 关系 | **α / β / γ / 替代** |
| D3 | 双路径 Authority 产生机制 | 确认 / 修正 |
| D4 | Authority 四元组绑定 + run_id 引入 | 确认 / 修正 |
| D5 | claim_id → candidate_id join | 确认 / 修正 |
| D6 | 持久化方案 + DB schema | 确认 / 修正 |
| D7 | IR Boundary enforcement | 确认 / 修正 |
| D8 | Admission Boundary enforcement | 确认 / 修正 |
| D9 | check 位置 + fail-closed 语义 | 确认 / 修正 |
| D10 | §8.2 兼容性 | 确认 / 修正 |

---

## 6. 明确不主张

- 本文档**不是** L2 Decision Record（待 adversarial review + Owner 终裁）
- **不修改**任何生产代码
- **不修改**任何 Frozen Spec
- **不实现** workaround
- **不假设** D2 选项 α 是唯一正确答案——三选项均列出，待 Owner 裁决
- **不假设** `is_evidence_validated=True` 是最终方案——它是 Phase 1 的 in-memory 实现，生产方案需 DB 持久化（D6）

---

## 7. 下一步

1. **DSH adversarial review**：对本文档 D1–D10 逐项审查
2. **Owner 终裁**：基于 adversarial review 结果裁决 D1–D10
3. **升 L2 Decision Record**：裁决通过后正式升格
4. **Implementation**：L2 Decision 生效后方可进入编码

---

## 附录 A：证据文件索引

| 文件 | 内容 |
|---|---|
| `backend/scripts/preprocessing_consumer/p32-enforcement-results.json` | P3.2 实验结果 |
| `backend/scripts/preprocessing_consumer/p32_scope.md` | P3.2 实验 scope |
| `backend/app/domains/gate/admission.py` | AdmissionService 当前实现 |
| `backend/app/domains/evidence/promotion.py` | EvidencePromotionService Phase 1 |
| `backend/app/domains/evidence/models.py` | ValidationEvent / EvidenceReference 数据模型 |
| `Docs/DECISIONS/75_EVIDENCE_PROMOTION_CONTRACT.md` | Evidence Promotion Contract（R1–R5） |
| `Docs/V3_SPEC/20_Document_Pipeline.md §8.2/§8.3` | 双入口 + verified_correct |
