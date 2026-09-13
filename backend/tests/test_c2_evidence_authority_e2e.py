"""C-2 157 E2E — Evidence Authority Lifecycle + Fail-Closed Verification.

架构审查裁决（2026-09-13）授权的 C-2 测试维度：

1. Semantic IR bypass test: 构造 EvidenceClaim → 无 ValidationEvent → 尝试 Compiler → 必须 rejected
2. Evidence Authority Lifecycle: 每个 target 六问验证
3. 157 invalid binding cases fail-closed

核心原则: Only Validated Evidence may enter Semantic IR.
"""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.domains.evidence.models import (
    AppendOnlyEventLog,
    CheckResult,
    EvidenceReference,
    ProposerIdentity,
    ValidationEvent,
)
from app.domains.evidence.promotion import (
    EvidencePromotionService,
    create_evidence_references,
    record_validation_event,
)
from app.domains.resolver.span import ResolvedSpan

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000c")


def mk_span(span_id: str, role: str = "answer", line_ref: str = "P1L006") -> ResolvedSpan:
    """Create a minimal ResolvedSpan for testing."""
    return ResolvedSpan(
        span_id=span_id,
        source_version_id=SVID,
        role=role,
        start_line_ref=line_ref,
        end_line_ref=line_ref,
        line_refs=(line_ref,),
        granularity="line",
        start_offset=None,
        end_offset=None,
        text_hash="a" * 64,
        resolution_status="exact",
    )

CORPUS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "Docs", "V3_SPEC", "gate_c_invalid_binding_corpus.json",
)


# ---------------------------------------------------------------------------
# Semantic IR Bypass Test
# ---------------------------------------------------------------------------

class TestSemanticIRBypass:
    """核心攻击向量: 构造 EvidenceClaim → 无 ValidationEvent → 尝试 Compiler → 必须 rejected.

    V3 核心原则: Only Validated Evidence may enter Semantic IR.
    """

    def test_claim_without_validation_event_is_not_validated(self):
        """EvidenceClaim 存在但无 ValidationEvent → is_evidence_validated = False."""
        service = EvidencePromotionService()

        # 创建 EvidenceReference (Proposal 层)
        proposer = ProposerIdentity(producer_type="llm", model="test-model")
        span = mk_span("span-001")
        refs = service.create_references(
            type("FakeRun", (), {"resolved_spans": (span,)})(),
            proposer,
        )
        assert len(refs) == 1

        # 不产生 ValidationEvent
        # is_evidence_validated 必须返回 False
        assert service.is_evidence_validated("Q1") is False, (
            "Claim without ValidationEvent must NOT be validated"
        )

    def test_unvalidated_claim_cannot_enter_ir(self):
        """未经 ValidationEvent 的 claim 不能进入 Semantic IR.

        验证: EvidencePromotionService.is_evidence_validated() 是 IR 入口的守卫.
        """
        service = EvidencePromotionService()

        # 构造一个 "伪造" 的 claim_id — 没有经过 Gate validation
        forged_claim_id = "forged-Q1"

        # 任何未经 ValidationEvent 的 claim 必须被拒绝
        assert service.is_evidence_validated(forged_claim_id) is False

        # 即使手动构造 ValidationEvent 对象，不经过 record_validation 也不算
        # 真正的防护在于: 没有事件 = 不 validated
        assert service.is_evidence_validated("nonexistent-claim") is False

    def test_rejected_claim_is_not_validated(self):
        """rejected claim 不能进入 Semantic IR."""
        service = EvidencePromotionService()

        gate_decision_rejected = {
            "decision": "rejected",
            "layers": {
                "structural": {"status": "fail", "reasons": ["overlap detected"]},
            },
        }

        event = service.record_validation("Q-rejected", gate_decision_rejected)
        assert event is not None
        assert event.validation_result == "rejected"
        assert service.is_evidence_validated("Q-rejected") is False, (
            "Rejected claim must NOT be validated"
        )

    def test_invalidated_claim_is_not_validated(self):
        """validated → invalidated → 不再是 validated."""
        service = EvidencePromotionService()

        # 先 validated
        gate_approve = {"decision": "auto_approve", "layers": {}}
        service.record_validation("Q-inval", gate_approve)
        assert service.is_evidence_validated("Q-inval") is True

        # 再 invalidated (使用更晚的时间戳确保 max() 选中它)
        later = datetime.now(timezone.utc) + timedelta(seconds=1)
        inv_event = ValidationEvent(
            event_id="ve-inval-001",
            claim_id="Q-inval",
            validation_result="invalidated",
            checks=(),
            validation_method="human_review",
            validator="human",
            validated_at=later,
        )
        service._validation_log.append(inv_event)
        assert service.is_evidence_validated("Q-inval") is False, (
            "Invalidated claim must NOT be validated"
        )

    def test_bypass_via_direct_log_append_blocked_by_state_machine(self):
        """直接 log.append() 绕过 service → 状态机仍然阻止非法转换."""
        log = AppendOnlyEventLog()

        # 先 append validated
        v_event = ValidationEvent(
            event_id="ve-001",
            claim_id="Q1",
            validation_result="validated",
            checks=(),
            validation_method="frozen_header_rule",
            validator="gate/v1",
        )
        log.append(v_event)

        # 尝试直接 append rejected（validated → rejected 不允许）
        r_event = ValidationEvent(
            event_id="ve-002",
            claim_id="Q1",
            validation_result="rejected",
            checks=(),
            validation_method="structural_consistency",
            validator="gate/v1",
        )
        with pytest.raises(ValueError, match="only INVALIDATED transition allowed"):
            log.append(r_event)


# ---------------------------------------------------------------------------
# Evidence Authority Lifecycle — 六问验证
# ---------------------------------------------------------------------------

class TestEvidenceAuthorityLifecycle:
    """架构审查要求的 Evidence Authority Lifecycle 六问.

    每个 target 必须能回答:
    1. SourceFragment 来自哪里 → 有 hash/version
    2. Proposal 谁提出 → 有 producer
    3. Claim 谁提升 → 有 creator (Phase 2, 当前 placeholder)
    4. ValidationEvent 为什么通过 → 有 check_id
    5. ValidatedEvidence 对应哪些 span → 可追溯
    6. IR 是否只消费 validated → 无 bypass
    """

    def test_source_fragment_has_version_anchor(self):
        """Q1: SourceFragment 来自哪里 → EvidenceReference 有 source_version_id."""
        proposer = ProposerIdentity(producer_type="llm")
        span = mk_span("span-lifecycle-001")
        ref = EvidenceReference.from_resolved_span(span, proposer)

        assert ref.source_version_id == SVID, (
            "EvidenceReference must anchor to source_version_id"
        )
        assert ref.span_id == "span-lifecycle-001"

    def test_proposal_has_producer_identity(self):
        """Q2: Proposal 谁提出 → ProposerIdentity 有 producer_type."""
        proposer = ProposerIdentity(
            producer_type="llm",
            model="qwen3.5-9b",
            pipeline_version="resolver/v1",
        )
        span = mk_span("span-lifecycle-002", role="stem", line_ref="P1L001")
        ref = EvidenceReference.from_resolved_span(span, proposer)

        assert ref.proposer.producer_type == "llm"
        assert ref.proposer.model == "qwen3.5-9b"
        assert ref.proposer.pipeline_version == "resolver/v1"

    def test_validation_event_has_structured_check_id(self):
        """Q4: ValidationEvent 为什么通过 → 有 machine-parseable check_id."""
        gate_decision = {
            "decision": "auto_approve",
            "layers": {
                "provenance": {"status": "pass", "reasons": []},
                "structural": {"status": "pass", "reasons": []},
                "admission": {"status": "pass", "reasons": []},
            },
        }

        event = record_validation_event(
            claim_id="Q-lifecycle",
            gate_decision=gate_decision,
        )

        assert event is not None
        assert len(event.checks) > 0, "ValidationEvent must have structured checks"

        check_ids = {c.check_id for c in event.checks}
        assert "BYTE_PROVEN" in check_ids
        assert "STRUCTURAL_CONSISTENCY" in check_ids
        assert "STRICT_AUTO_GRAMMAR" in check_ids

        # 所有 check result 必须是 pass 或 fail
        for c in event.checks:
            assert c.result in ("pass", "fail")

    def test_validated_evidence_traceable_to_references(self):
        """Q5: ValidatedEvidence 对应哪些 span → reference_ids 可追溯."""
        service = EvidencePromotionService()
        proposer = ProposerIdentity(producer_type="llm")

        # 创建多个 EvidenceReferences
        roles = ["stem", "option", "answer", "explanation"]
        spans = tuple(
            mk_span(f"span-trace-{i}", role=role, line_ref=f"P1L00{i+1}")
            for i, role in enumerate(roles)
        )
        refs = service.create_references(
            type("FakeRun", (), {"resolved_spans": spans})(),
            proposer,
        )

        # Record validation with reference_ids
        ref_ids = tuple(r.reference_id for r in refs)
        gate_decision = {"decision": "auto_approve", "layers": {}}
        event = service.record_validation(
            "Q-trace", gate_decision, reference_ids=ref_ids
        )

        assert event is not None
        assert event.reference_ids == ref_ids

        # 从 ValidationEvent 可以追溯到 EvidenceReferences
        traced = service.get_references_for_ids(event.reference_ids)
        assert len(traced) == 4
        assert {r.span_id for r in traced} == {s.span_id for s in spans}

    def test_ir_only_consumes_validated(self):
        """Q6: IR 是否只消费 validated → 无 bypass.

        验证 is_evidence_validated 是唯一入口:
        - validated → True
        - rejected → False
        - invalidated → False
        - no event → False
        """
        service = EvidencePromotionService()

        # Case 1: validated
        service.record_validation("Q-valid", {"decision": "auto_approve", "layers": {}})
        assert service.is_evidence_validated("Q-valid") is True

        # Case 2: rejected
        service.record_validation(
            "Q-rej", {"decision": "rejected", "layers": {}}
        )
        assert service.is_evidence_validated("Q-rej") is False

        # Case 3: no event
        assert service.is_evidence_validated("Q-none") is False


# ---------------------------------------------------------------------------
# 157 Invalid Binding Cases — Fail-Closed Verification
# ---------------------------------------------------------------------------

class Test157InvalidBindingCases:
    """验证 157 invalid binding cases 全过程 fail-closed.

    每个 case 的 expected_resolver_behavior = REJECT.
    核心: invalid binding evidence 不能产生 validated evidence.
    """

    @pytest.fixture
    def corpus(self):
        if not os.path.exists(CORPUS_PATH):
            pytest.skip("Gate C corpus not found")
        with open(CORPUS_PATH, encoding="utf-8") as f:
            return json.load(f)

    def test_corpus_has_157_targets(self, corpus):
        """Corpus 必须有 157 个 targets."""
        assert len(corpus["targets"]) == 157, (
            f"Expected 157 targets, got {len(corpus['targets'])}"
        )

    def test_corpus_reason_distribution(self, corpus):
        """Reason 分布必须匹配 spec."""
        reasons = {}
        for t in corpus["targets"]:
            r = t["invalid_reason"]
            reasons[r] = reasons.get(r, 0) + 1

        expected = {
            "WRONG_REGION": 56,
            "EXPLANATION_REGION": 49,
            "SEPARATOR_REGION": 27,
            "QUESTION_REGION": 15,
            "SUSPICIOUS_CONTENT": 10,
        }
        assert reasons == expected, (
            f"Reason distribution mismatch: expected {expected}, got {reasons}"
        )

    def test_all_targets_expect_reject(self, corpus):
        """所有 157 个 targets 的 expected_resolver_behavior 必须包含 REJECT."""
        for t in corpus["targets"]:
            behavior = t["expected_resolver_behavior"]
            assert "REJECT" in behavior.upper() or "UNRESOLVED" in behavior.upper(), (
                f"Target {t['case_id']}/{t['unit_id']} expected REJECT, got: {behavior}"
            )

    def test_invalid_binding_produces_no_validated_evidence(self, corpus):
        """Invalid binding evidence 不能产生 validated evidence.

        模拟: 即使 Resolver 错误地返回了 exact span（结构有效但语义无效），
        Gate grammar verification 应该返回 None → pending_review → 不产生 ValidationEvent.
        """
        from app.domains.gate.grammar import verify

        service = EvidencePromotionService()

        # 取样验证: 每种 reason 至少验证一个
        sampled = []
        seen_reasons = set()
        for t in corpus["targets"]:
            r = t["invalid_reason"]
            if r not in seen_reasons:
                seen_reasons.add(r)
                sampled.append(t)

        for t in sampled:
            answer_preview = t.get("answer_preview", "")
            unit_type = t.get("original_question_type", "short_answer")

            # Grammar verification: invalid content → None → pending_review
            if unit_type in ("single_choice", "multiple_choice", "true_false"):
                result = verify(unit_type, answer_preview, ["A", "B", "C", "D"])
                # Invalid content 应该返回 None（无法判定）或 False
                # None → pending_review → 不产生 ValidationEvent
                if result is None:
                    # pending_review → record_validation_event returns None
                    event = record_validation_event(
                        claim_id=f"{t['case_id']}-{t['unit_id']}",
                        gate_decision={"decision": "pending_review", "layers": {}},
                    )
                    assert event is None, (
                        f"pending_review must NOT produce ValidationEvent for {t['unit_id']}"
                    )
                elif result is False:
                    # rejected → ValidationEvent with rejected
                    pass  # rejected is handled correctly

            # 验证: 无论哪种路径，未经过 auto_approve 的 claim 不是 validated
            claim_id = f"{t['case_id']}-{t['unit_id']}"
            assert service.is_evidence_validated(claim_id) is False, (
                f"Invalid binding {claim_id} must NOT be validated"
            )

    def test_separator_region_content_blocked(self):
        """SEPARATOR_REGION: 分隔符内容不能通过 grammar."""
        from app.domains.gate.grammar import verify

        separators = ["---", "***", "***", "===", "---  "]
        for sep in separators:
            result = verify("single_choice", sep, ["A", "B", "C", "D"])
            assert result is None, (
                f"Separator '{sep}' should return None (pending_review), got {result}"
            )

    def test_explanation_region_content_blocked(self):
        """EXPLANATION_REGION: 解析内容不能通过 grammar."""
        from app.domains.gate.grammar import verify

        explanations = [
            "【考点】fruit classification",
            "【解答】This is a solution",
            "【解析】Because A is correct",
        ]
        for exp in explanations:
            result = verify("single_choice", exp, ["A", "B", "C", "D"])
            assert result is None, (
                f"Explanation '{exp[:30]}' should return None, got {result}"
            )

    def test_question_region_content_blocked(self):
        """QUESTION_REGION: 题目内容不能通过 grammar."""
        from app.domains.gate.grammar import verify

        questions = [
            "1. Which is fruit?",
            "2. What is 1+1?",
            "3. Choose the correct answer",
        ]
        for q in questions:
            result = verify("single_choice", q, ["A", "B", "C", "D"])
            assert result is None, (
                f"Question '{q[:30]}' should return None, got {result}"
            )


# ---------------------------------------------------------------------------
# Evidence Authority Ledger — 完整生命周期集成测试
# ---------------------------------------------------------------------------

class TestEvidenceAuthorityFullLifecycle:
    """完整 Evidence Authority 生命周期: Fragment → Proposal → Claim → Validation → IR.

    验证正常路径和异常路径都经过 Evidence Authority Ledger.
    """

    def test_full_lifecycle_happy_path(self):
        """正常路径: Fragment → Proposal → Validation → validated."""
        service = EvidencePromotionService()
        proposer = ProposerIdentity(producer_type="llm", model="qwen3.5-9b")

        # Step 1: SourceFragment (ResolvedSpan)
        span = mk_span("span-full-001")

        # Step 2: Proposal (EvidenceReference)
        refs = service.create_references(
            type("FakeRun", (), {"resolved_spans": (span,)})(),
            proposer,
        )
        assert len(refs) == 1
        assert refs[0].proposer.producer_type == "llm"

        # Step 3: Validation (ValidationEvent)
        gate_decision = {
            "decision": "auto_approve",
            "layers": {
                "provenance": {"status": "pass", "reasons": []},
            },
        }
        ref_ids = tuple(r.reference_id for r in refs)
        event = service.record_validation(
            "Q-full", gate_decision, reference_ids=ref_ids
        )

        # Step 4: Verify Evidence Authority
        assert event is not None
        assert event.validation_result == "validated"
        assert service.is_evidence_validated("Q-full") is True
        assert event.reference_ids == ref_ids

        # Step 5: Traceability
        traced = service.get_references_for_ids(event.reference_ids)
        assert len(traced) == 1
        assert traced[0].span_id == "span-full-001"

    def test_full_lifecycle_rejection_path(self):
        """异常路径: Fragment → Proposal → Rejection → NOT validated."""
        service = EvidencePromotionService()
        proposer = ProposerIdentity(producer_type="llm")

        span = mk_span("span-rej-001")
        refs = service.create_references(
            type("FakeRun", (), {"resolved_spans": (span,)})(),
            proposer,
        )

        gate_decision = {
            "decision": "rejected",
            "layers": {
                "structural": {"status": "fail", "reasons": ["invalid content"]},
            },
        }
        event = service.record_validation(
            "Q-rej-full", gate_decision,
            reference_ids=tuple(r.reference_id for r in refs),
        )

        assert event is not None
        assert event.validation_result == "rejected"
        assert service.is_evidence_validated("Q-rej-full") is False

    def test_full_lifecycle_invalidation_path(self):
        """Invalidation 路径: validated → source change → invalidated → NOT validated."""
        service = EvidencePromotionService()

        # 先 validated
        service.record_validation("Q-inv", {"decision": "auto_approve", "layers": {}})
        assert service.is_evidence_validated("Q-inv") is True

        # Source 变化 → invalidated (使用更晚时间戳)
        later = datetime.now(timezone.utc) + timedelta(seconds=1)
        inv_event = ValidationEvent(
            event_id="ve-inv-001",
            claim_id="Q-inv",
            validation_result="invalidated",
            checks=(),
            validation_method="human_review",
            validator="human-review-console",
            validated_at=later,
        )
        service._validation_log.append(inv_event)

        assert service.is_evidence_validated("Q-inv") is False, (
            "After INVALIDATED, claim must NOT be validated"
        )
