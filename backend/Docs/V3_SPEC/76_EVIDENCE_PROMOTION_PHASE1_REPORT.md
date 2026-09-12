# Evidence Promotion Contract Phase 1 — 实现报告

**Version**: 1.0.0
**Date**: 2026-09-13
**Status**: COMPLETE — 全部测试通过
**Design**: 75_EVIDENCE_PROMOTION_CONTRACT.md v1.1.0 (架构审查通过)
**Commit**: d28f3b9 (pushed to origin/main)

---

## 一、执行摘要

Phase 1 按架构审查修正后的路径实现：**不污染 ResolvedSpan**，新增 EvidenceReference 桥接层。

| 指标 | 结果 |
|------|------|
| 新增文件 | 4 (3 模块 + 1 测试) |
| 修改文件 | 1 (gate/service.py) |
| 新增代码行 | 975 |
| 新增测试 | 46 |
| 全量测试 | 601 passed, 0 failed |
| 回归 | 无 |
| 冻结规则违反 | 0 |

---

## 二、实现内容

### 2.1 新模块 `app/domains/evidence/`

#### models.py — 三个 frozen dataclass

**ProposerIdentity** (Provenance 层):
```python
@dataclass(frozen=True)
class ProposerIdentity:
    producer_type: str   # "native_parser" | "ocr" | "llm" | "heuristic" | "human"
    model: str | None
    pipeline_version: str | None
```
- `__post_init__` 校验 producer_type 在合法值域内
- 无 trust_level 字段 — Provenance 与 Reliability 分离 (架构审查要求)

**EvidenceReference** (Proposal 层 / 桥接层):
```python
@dataclass(frozen=True)
class EvidenceReference:
    reference_id: str
    span_id: str                    # → ResolvedSpan
    proposed_role: str              # "answer" | "explanation" | ...
    proposer: ProposerIdentity
    source_version_id: UUID
    created_at: datetime
```
- `from_resolved_span()` classmethod: 从 ResolvedSpan 创建
- 无 validated/authority/trust 字段 — R2: Proposal 无证据授权

**ValidationEvent** (Validation 层):
```python
@dataclass(frozen=True)
class ValidationEvent:
    event_id: str
    claim_id: str
    validation_result: str          # "validated" | "rejected" | "invalidated"
    checks_passed: tuple[str, ...]
    checks_failed: tuple[str, ...]
    validation_method: str          # "frozen_header_rule" | "byte_proven" | ...
    validator: str                  # "gate/v1"
    validated_at: datetime
```
- `__post_init__` 校验 validation_result 和 validation_method 在合法值域内
- `is_validated` / `is_terminal` 属性
- Event sourcing: append-only, 不可变, INVALIDATED 可追加

#### promotion.py — 服务层

**create_evidence_references(resolved_run, proposer)** → `tuple[EvidenceReference, ...]`
- 从 ResolvedRun 的每个 ResolvedSpan 创建 EvidenceReference
- 纯函数, 无副作用

**record_validation_event(claim_id, gate_decision, validator)** → `ValidationEvent | None`
- auto_approve → ValidationEvent(result="validated")
- rejected → ValidationEvent(result="rejected")
- pending_review → None (验证未完成, 等待人工)

**EvidencePromotionService**:
- `create_references(resolved_run, proposer)` — 创建并存储 EvidenceReference
- `record_validation(claim_id, gate_decision)` — 记录 ValidationEvent (append-only)
- `validation_events` / `evidence_references` — 只读访问
- `get_events_for_claim(claim_id)` — 按 claim 查询
- `is_evidence_validated(claim_id)` — 最新 event 是否 validated (INVALIDATED 可覆盖)

### 2.2 GateService 集成

`app/domains/gate/service.py` 修改:

```python
# __init__ 新增
self._evidence = EvidencePromotionService()

# run() 中, Resolver 完成后
proposer = ProposerIdentity(producer_type="native_parser", pipeline_version=RESOLVER_VERSION)
self._evidence.create_references(resolved_run, proposer)

# run() 中, Gate evaluate() 后
self._evidence.record_validation(root.unit_id, gate)

# 新增 property
@property
def evidence_promotion(self) -> EvidencePromotionService: ...
```

**关键约束**: 纯增量, 不改变现有 pipeline 流程, 不改变公共 API 签名。

---

## 三、冻结规则验证

| 规则 | 实现方式 | 测试覆盖 |
|------|----------|----------|
| R1: SourceFragment 无 semantic role | ResolvedSpan schema 不变 (12 字段, 无 proposer/trust/validated) | `test_resolved_span_not_polluted` |
| R2: Proposal 无 evidence authority | EvidenceReference 无 validated/authority/trust 字段 | `test_no_evidence_authority_field`, `test_r2_proposal_no_authority` |
| R3: Claim 是 request 不是 assertion | Phase 2 (EvidenceReference.proposed_role 是提议, 不是声明) | `test_proposed_role_from_span` |
| R4: 只有 Validation 产生 authority | `is_evidence_validated()` 只查 ValidationEvent 链 | `test_r4_only_validation_produces_authority` |
| R5: IR 只引用 ValidatedEvidence | Phase 2 enforcement | — |
| 禁止 4: Fragment → IR | EvidenceReference 是桥接, 不是 IR 输入 | `test_evidence_reference_is_bridge` |

---

## 四、信任拆分验证

架构审查要求: Provenance (谁产生) 与 Reliability (怎么验证) 分离。

| 维度 | 载体 | 字段 | 测试 |
|------|------|------|------|
| Provenance | ProposerIdentity | producer_type, model, pipeline_version | `test_valid_producer_types`, `test_llm_is_low_provenance` |
| Reliability | ValidationEvent | validation_method, validator | `test_valid_results`, `test_invalid_method_raises` |

验证: ProposerIdentity 无 trust_level 字段 (`test_llm_is_low_provenance`)。
验证: ValidationEvent.validation_method 只接受确定性方法 (`test_invalid_method_raises`)。

---

## 五、测试覆盖

### 5.1 新增测试 (46)

| 测试类 | 数量 | 覆盖 |
|--------|------|------|
| TestProposerIdentity | 5 | 合法/非法 producer_type, frozen, LLM 低信任 |
| TestEvidenceReference | 4 | from_resolved_span, frozen, 无 authority, proposed_role |
| TestValidationEvent | 7 | 合法/非法 result/method, frozen, is_validated, is_terminal |
| TestCreateEvidenceReferences | 4 | 空 run, 单 span, 多 span, proposer 保留 |
| TestRecordValidationEvent | 7 | auto_approve→validated, rejected→rejected, pending→None, 默认值 |
| TestEvidencePromotionService | 9 | 创建/记录/append-only/查询/is_validated/INVALIDATED 覆盖 |
| TestFrozenRules | 5 | R1/R2/R4, ResolvedSpan 不污染, 桥接验证 |
| TestGateIntegration | 4 | 完整流程 validated/rejected/pending, 多 claim 独立 |

### 5.2 回归测试

| 范围 | 结果 |
|------|------|
| test_evidence_promotion.py | 46 passed |
| test_gate_service.py + policy + payload + grammar | 全部 passed |
| test_role_provenance.py | 全部 passed |
| test_b2b5_d_projection_safety.py | 全部 passed |
| **全量 tests/** | **601 passed, 0 failed** |

---

## 六、与 Contract 的映射

| Contract 层 | Phase 1 实现 | 状态 |
|-------------|-------------|------|
| SourceFragment | ResolvedSpan (不改) | DONE |
| EvidenceProposal | EvidenceReference | DONE |
| EvidenceClaim | — (Phase 2) | DEFERRED |
| ValidationEvent | ValidationEvent + EvidencePromotionService | DONE |
| ValidatedEvidence | is_evidence_validated() 查询 | DONE (轻量) |

---

## 七、Phase 2 前置条件

Phase 1 完成后, Phase 2 可以开始:

- [x] EvidenceReference dataclass (桥接层)
- [x] ProposerIdentity dataclass (Provenance)
- [x] ValidationEvent dataclass (append-only)
- [x] EvidencePromotionService (服务层)
- [x] GateService 集成 (增量)
- [x] 全量测试通过 (601)
- [ ] ValidationEvent DB 持久化 (Phase 2)
- [ ] EvidenceProposal / EvidenceClaim 显式 dataclass (Phase 2)
- [ ] 状态机 enforcement (Phase 2)
- [ ] INVALIDATED 完整支持 (Phase 2)

---

## 八、文件清单

| 文件 | 操作 | 行数 |
|------|------|------|
| `app/domains/evidence/__init__.py` | NEW | 32 |
| `app/domains/evidence/models.py` | NEW | 163 |
| `app/domains/evidence/promotion.py` | NEW | 175 |
| `app/domains/gate/service.py` | MODIFIED | +25 |
| `tests/test_evidence_promotion.py` | NEW | 580 |

---

**报告状态**: COMPLETE
**下一步**: Phase 2 — DB 持久化 + 状态机 enforcement + EvidenceClaim
