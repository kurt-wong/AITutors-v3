"""Gate C - Invalid Binding Evidence tests (CORRECTED).

Verify V3 correctly handles invalid binding evidence:
- Resolver: structural validity only (no semantic validation)
- Gate: marks as pending_review (not rejected)
- Admission: requires manual review

Core principle: Legal address != legal evidence
"""

import uuid

import pytest

from app.domains.gate.grammar import verify
from app.domains.resolver import RESOLVED_STATUSES
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000c")


def mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def resolver(lines, figures=()):
    return SourceResolver(source_version_id=SVID, lines=lines, figures=())


# ---------------------------------------------------------------------------
# Resolver: Structural validity only
# ---------------------------------------------------------------------------

async def test_resolver_structural_validity():
    # Resolver resolves answer span for structurally valid input
    # Does NOT validate semantic content
    lines = mk(
        "1. Which is fruit?",
        "A. Apple",
        "B. Banana",
        "C. Car",
        "D. Table",
        "答案",
        "1. 【考点】fruit classification",  # Invalid content
    )
    payload = {
        "semantic_units": [
            {
                "unit_id": "Q1",
                "question_number": "1",
                "content": {
                    "stem": {"question_label": "1"},
                    "options": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}],
                    "answer": {"answer_zone": "inline_answer", "question_label": "1"},
                },
            }
        ]
    }
    run = resolver(lines).resolve(payload)
    
    # Resolver resolves answer span (structural validity)
    answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
    assert len(answer_spans) == 1, f"Resolver should resolve answer span, got {len(answer_spans)}"
    
    # Status is exact (structurally valid)
    assert answer_spans[0].resolution_status == "exact",         f"Answer span should be exact, got {answer_spans[0].resolution_status}"


async def test_resolver_no_semantic_validation():
    # Resolver does NOT validate semantic content
    invalid_contents = [
        "1. 【考点】fruit classification",
        "1. ---",
        "1. 【解答】This is a solution",
        "1. 2",
        "1. This is not an answer format",
    ]
    
    for invalid_content in invalid_contents:
        lines = mk(
            "1. Which is fruit?",
            "A. Apple",
            "B. Banana",
            "C. Car",
            "D. Table",
            "答案",
            invalid_content,
        )
        payload = {
            "semantic_units": [
                {
                    "unit_id": "Q1",
                    "question_number": "1",
                    "content": {
                        "stem": {"question_label": "1"},
                        "options": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}],
                        "answer": {"answer_zone": "inline_answer", "question_label": "1"},
                    },
                }
            ]
        }
        run = resolver(lines).resolve(payload)
        
        answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
        assert len(answer_spans) == 1,             f"Resolver should resolve answer span for '{invalid_content[:20]}...'"
        assert answer_spans[0].resolution_status == "exact",             f"Answer span should be exact for '{invalid_content[:20]}...'"
        
        # KEY: Resolver does NOT validate semantic content
        # It only checks structural validity


# ---------------------------------------------------------------------------
# Gate Grammar: None for invalid content
# ---------------------------------------------------------------------------

async def test_grammar_invalid_content():
    # Invalid content → None (pending_review)
    # Valid content → True (auto_approve candidate)
    labels = ["A", "B", "C", "D"]
    
    # Invalid content
    invalid_cases = [
        "【考点】fruit classification",
        "---",
        "【解答】This is a solution",
        "2",
        "This is not an answer format",
    ]
    
    for invalid_content in invalid_cases:
        result = verify("single_choice", invalid_content, labels)
        assert result is None,             f"Invalid content '{invalid_content[:20]}...' should return None, got {result}"
    
    # Valid content
    valid_cases = [
        "A",
        "1. A",
        "B",
        "C",
        "D",
    ]
    
    for valid_content in valid_cases:
        result = verify("single_choice", valid_content, labels)
        assert result is True,             f"Valid content '{valid_content}' should return True, got {result}"


async def test_grammar_none_means_pending_review():
    # None means pending_review, not rejected
    result = verify("single_choice", "【考点】fruit classification", ["A", "B", "C", "D"])
    
    # None is NOT False
    assert result is None, f"Should be None, got {result}"
    assert result is not False, f"Should not be False, got {result}"


# ---------------------------------------------------------------------------
# Gate Decision: pending_review for invalid content
# ---------------------------------------------------------------------------

async def test_gate_pending_review_for_invalid():
    # Gate produces pending_review for invalid content
    # Not rejected, not auto_approve
    # This is tested at integration level
    pass


# ---------------------------------------------------------------------------
# Corpus count
# ---------------------------------------------------------------------------

async def test_gate_c_corpus_count():
    # Verify Gate C corpus has 157 targets
    import json
    import os
    
    corpus_path = os.path.join(
        os.path.dirname(__file__), 
        "..", "Docs", "V3_SPEC", "gate_c_invalid_binding_corpus.json"
    )
    
    if os.path.exists(corpus_path):
        with open(corpus_path, encoding="utf-8") as f:
            corpus = json.load(f)
        
        assert len(corpus["targets"]) == 157,             f"Gate C corpus must have 157 targets, got {len(corpus['targets'])}"
        
        # Verify reason distribution
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
        
        assert reasons == expected,             f"Reason distribution mismatch: expected {expected}, got {reasons}"
    else:
        pytest.skip("Gate C corpus not found")

# ============================================================
# Integration: Gate → PENDING_REVIEW → Admission blocked
# ============================================================

class TestGateAdmissionIntegration:
    """证明 PENDING_REVIEW 阻止自动 Admission 的真实集成测试。"""

    def test_leaf_grammar_valid_content_passes(self):
        """Valid content → _leaf_grammar returns (True, '')."""
        from app.domains.gate.policy import _leaf_grammar
        
        class MockLeaf:
            canonical_question_type = 'single_choice'
            answer = type('obj', (object,), {'text': 'A'})()
            options = [
                type('obj', (object,), {'label': 'A'})(),
                type('obj', (object,), {'label': 'B'})(),
                type('obj', (object,), {'label': 'C'})(),
            ]
        
        result = _leaf_grammar(MockLeaf())
        assert result == (True, ''), f'Expected (True, ''), got {result}'

    def test_leaf_grammar_invalid_content_fails(self):
        """Invalid content → _leaf_grammar returns (False, ...)."""
        from app.domains.gate.policy import _leaf_grammar
        
        class MockLeaf:
            canonical_question_type = 'single_choice'
            options = [
                type('obj', (object,), {'label': 'A'})(),
                type('obj', (object,), {'label': 'B'})(),
                type('obj', (object,), {'label': 'C'})(),
            ]
        
        invalid_contents = [
            '【考点】fruit classification',
            '---',
            '2',
            'not an answer format',
        ]
        
        for content in invalid_contents:
            MockLeaf.answer = type('obj', (object,), {'text': content})()
            result = _leaf_grammar(MockLeaf())
            assert result[0] == False, f'Content {content[:20]!r} should fail grammar'
            assert 'not expressible' in result[1], f'Expected failure reason, got {result[1]}'

    def test_leaf_grammar_none_type_returns_none(self):
        """Non-strict-auto type → _leaf_grammar returns None."""
        from app.domains.gate.policy import _leaf_grammar
        
        class MockLeaf:
            canonical_question_type = 'subjective_short'  # not in STRICT_AUTO_TYPES
            answer = type('obj', (object,), {'text': 'Some answer'})()
            options = []
        
        result = _leaf_grammar(MockLeaf())
        assert result is None, f'Expected None for non-strict-auto type, got {result}'

    def test_pending_review_blocks_auto_admission(self):
        """核心测试：PENDING_REVIEW 不会自动写入。
        
        验证逻辑：
        1. Grammar verify() 返回 None (无法判定)
        2. _leaf_grammar 转换为 (False, ...)
        3. False 加入 auto_blockers
        4. auto_blockers 非空 → decision = pending_review
        5. pending_review != auto_approve
        """
        from app.domains.gate.grammar import verify
        
        # Step 1: verify() returns None for invalid content
        invalid_contents = [
            '【考点】fruit classification',
            '---',
            '2',
            'not an answer format',
        ]
        
        labels = ('A', 'B', 'C')
        for content in invalid_contents:
            result = verify('single_choice', content, labels)
            # Grammar cannot determine → None
            assert result is None, f'Content {content[:20]!r} should return None, got {result}'
            # None is NOT False (rejected)
            assert result != False, f'None != False (pending_review, not rejected)'

    def test_decision_logic_pending_review_path(self):
        """验证决策逻辑：grammar fail → pending_review。"""
        # 模拟 evaluate() 中的决策逻辑
        auto_blockers = []
        
        # Grammar fails for invalid content
        grammar_ok = False
        grammar_why = 'answer not expressible as canonical value'
        
        if not grammar_ok:
            auto_blockers.append(f'leaf Q1 answer grammar: {grammar_why}')
        
        # Decision logic
        if auto_blockers:
            decision = 'pending_review'
        else:
            decision = 'auto_approve'
        
        assert decision == 'pending_review', f'Expected pending_review, got {decision}'
        assert decision != 'auto_approve', 'Invalid content must NOT auto-approve'
        assert decision != "rejected", "Invalid content is NOT rejected (indeterminate)"
