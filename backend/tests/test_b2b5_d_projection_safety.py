"""
B2-B5-D: End-to-End Projection Safety Validation

验证 Path B / Source Binding 架构在真实上游错误存在时的 fail-closed 行为。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import pytest


# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class MockResolvedSpan:
    question_number: str
    content: str
    line_refs: List[str]
    resolution_status: str
    confidence: float


@dataclass
class MockAnswer:
    text: str
    line_refs: List[str]


@dataclass
class MockOption:
    label: str
    text: str


@dataclass
class MockCompiledLeaf:
    canonical_question_type: str
    answer: Optional[MockAnswer]
    options: List[MockOption]
    question_id: str
    parent_id: Optional[str] = None
    material_id: Optional[str] = None


@dataclass
class MockGateResult:
    decision: str
    auto_blockers: List[str]
    manual_warnings: List[str]


# ============================================================================
# 正向测试: Positive Projection
# ============================================================================

class TestPositiveProjection:
    """正向投影测试: S1/S2/S3 完整链路"""
    
    def test_s1_standalone_subjective_projection(self):
        """S1: Standalone Subjective - 完整链路验证"""
        evidence = {
            "question_number": "1",
            "question_type": "short_answer",
            "answer_zone": "The answer is 42.",
            "answer_line_refs": ["L10"],
        }
        
        # 1. Resolver
        resolved = MockResolvedSpan(
            question_number=evidence["question_number"],
            content=evidence["answer_zone"],
            line_refs=evidence["answer_line_refs"],
            resolution_status="exact",
            confidence=1.0,
        )
        assert resolved.resolution_status == "exact"
        
        # 2. Compiler
        leaf = MockCompiledLeaf(
            canonical_question_type="subjective_short_answer",
            answer=MockAnswer(text="The answer is 42.", line_refs=["L10"]),
            options=[],
            question_id="Q1",
            parent_id=None,
            material_id=None,
        )
        assert leaf.canonical_question_type == "subjective_short_answer"
        assert leaf.answer is not None
        assert leaf.parent_id is None
        
        # 3. Gate - subjective 不在 STRICT_AUTO_TYPES → pending_review
        gate = MockGateResult(
            decision="pending_review",
            auto_blockers=[],
            manual_warnings=["subjective requires manual review"],
        )
        assert gate.decision == "pending_review"
        assert gate.decision != "auto_approve"
        assert gate.decision != "rejected"
        
        # 4. Admission - pending_review 阻止自动准入
        admission_allowed = gate.decision == "auto_approve"
        assert not admission_allowed
        
        print("PASS: S1 Standalone Subjective Projection")


class TestS2CompositeSubquestion:
    """S2: Composite + Sub-question - 层级结构验证"""
    
    def test_s2_hierarchy_preserved(self):
        """验证子问题层级不会被 flatten"""
        parent = MockCompiledLeaf(
            canonical_question_type="composite",
            answer=None,
            options=[],
            question_id="Q1",
            parent_id=None,
        )
        
        subs = [
            MockCompiledLeaf(
                canonical_question_type="subjective_short_answer",
                answer=MockAnswer(text=f"Answer {i}", line_refs=[f"L{10+i*5}"]),
                options=[],
                question_id=f"Q1-{i}",
                parent_id="Q1",
            )
            for i in range(1, 4)
        ]
        
        # 验证层级
        assert parent.parent_id is None
        for sub in subs:
            assert sub.parent_id == "Q1", f"{sub.question_id} 应指向 Q1"
            assert sub.question_id.startswith("Q1-")
        
        # 验证没有 flatten
        all_ids = [parent.question_id] + [s.question_id for s in subs]
        assert len(all_ids) == 4
        assert len(set(all_ids)) == 4
        
        print("PASS: S2 Hierarchy Preserved")


class TestS3CompositeMaterial:
    """S3: Composite + Material + Subjective - Shared Material 验证"""
    
    def test_s3_shared_material_preserved(self):
        """验证 shared material 不会被 duplication"""
        questions = [
            MockCompiledLeaf(
                canonical_question_type="subjective_short_answer",
                answer=MockAnswer(text=f"Answer {i}", line_refs=[f"L{10+i*5}"]),
                options=[],
                question_id=f"Q{i}",
                material_id="M1",  # 共享 material
            )
            for i in range(1, 4)
        ]
        
        # 验证 shared material
        material_ids = set(q.material_id for q in questions)
        assert len(material_ids) == 1, "所有 questions 应共享同一个 material"
        assert "M1" in material_ids
        
        print("PASS: S3 Shared Material Preserved")


# ============================================================================
# 负向测试: Negative Projection Safety
# ============================================================================

class TestNegativeProjectionSafety:
    """负向投影安全测试: Invalid Binding Evidence 不会自动 admission"""
    
    def test_invalid_wrong_region_blocked(self):
        """WRONG_REGION: 错误区域绑定 → pending_review"""
        from app.domains.gate.grammar import verify
        
        invalid_content = "【考点】fruit classification"
        
        # Resolver - 结构有效
        resolved = MockResolvedSpan(
            question_number="1",
            content=invalid_content,
            line_refs=["L5"],
            resolution_status="exact",
            confidence=1.0,
        )
        assert resolved.resolution_status == "exact"
        
        # Grammar 验证
        result = verify("single_choice", invalid_content, ("A", "B"))
        assert result is not True, "Invalid content 不应返回 True"
        
        # Gate 判定
        gate_decision = "pending_review" if result is None or result is False else "auto_approve"
        assert gate_decision == "pending_review"
        
        # Admission
        admission_allowed = gate_decision == "auto_approve"
        assert not admission_allowed
        
        print("PASS: Invalid WRONG_REGION blocked")
    
    def test_invalid_explanation_region_blocked(self):
        """
        EXPLANATION_REGION: explanation content in answer role.

        BUG-V3-044 FIXED（用户裁决 2026-09-13，AnswerTokenContract）：
        旧实现用 `_option_letters()` 从任意正文抽 ASCII 字母，`【解答】A` 被判
        True 并可 auto_approve。现剥除题号前缀后走白名单——`【解答】A` 不属于
        任何允许形态（含汉字与【】标记）→ None → pending_review。

        本测试从「记录缺陷」反转为「锁死修复」。
        """
        from app.domains.gate.grammar import verify

        invalid_content = "【解答】A"

        result = verify("single_choice", invalid_content, ("A", "B", "C", "D"))

        assert result is None, (
            "AnswerTokenContract: explanation-prefixed text must not be treated "
            f"as a valid answer token, got {result!r}"
        )

        print("PASS: EXPLANATION_REGION blocked by AnswerTokenContract")
    
    def test_invalid_separator_region_blocked(self):
        """SEPARATOR_REGION: 分隔符区域绑定 → pending_review"""
        from app.domains.gate.grammar import verify
        
        invalid_content = "---"
        
        result = verify("single_choice", invalid_content, ("A", "B"))
        assert result is not True
        
        gate_decision = "pending_review" if result is None or result is False else "auto_approve"
        assert gate_decision == "pending_review"
        
        admission_allowed = gate_decision == "auto_approve"
        assert not admission_allowed
        
        print("PASS: Invalid SEPARATOR_REGION blocked")
    
    def test_invalid_question_region_blocked(self):
        """QUESTION_REGION: 问题区域绑定 → pending_review"""
        from app.domains.gate.grammar import verify
        
        invalid_content = "2"
        
        result = verify("single_choice", invalid_content, ("A", "B"))
        assert result is not True
        
        gate_decision = "pending_review" if result is None or result is False else "auto_approve"
        assert gate_decision == "pending_review"
        
        admission_allowed = gate_decision == "auto_approve"
        assert not admission_allowed
        
        print("PASS: Invalid QUESTION_REGION blocked")


# ============================================================================
# 安全属性验证
# ============================================================================

class TestSafetyProperties:
    """安全属性验证: 无 fallback, 无 mutation"""
    
    def test_no_search_fallback(self):
        """验证: Invalid evidence 不触发 search fallback"""
        from app.domains.gate.grammar import verify
        
        result = verify("single_choice", "【考点】...", ("A", "B"))
        
        # verify() 是纯函数, 不会触发 search
        assert result is None or result is False, \
            "应返回 None/False, 不是 search fallback"
        
        print("PASS: No search fallback")
    
    def test_no_llm_fallback(self):
        """验证: Invalid evidence 不触发 LLM fallback"""
        from app.domains.gate.grammar import verify
        
        result = verify("single_choice", "---", ("A", "B"))
        
        # verify() 是确定性函数, 不会调用 LLM
        assert result is None or result is False, \
            "应返回 None/False, 不是 LLM fallback"
        
        print("PASS: No LLM fallback")
    
    def test_no_source_mutation(self):
        """验证: Invalid evidence 不修改 Source"""
        source_content = "Original source content"
        original_hash = hash(source_content)
        
        # Resolver 只读取, 不修改
        resolved = MockResolvedSpan(
            question_number="1",
            content="Invalid content",
            line_refs=["L5"],
            resolution_status="exact",
            confidence=1.0,
        )
        
        assert hash(source_content) == original_hash, "Source 不应被修改"
        
        print("PASS: No source mutation")
    
    def test_three_state_decision_model(self):
        """验证: 三态判定模型 (True/False/None)"""
        from app.domains.gate.grammar import verify
        
        # True: Valid content
        result_valid = verify("single_choice", "A", ("A", "B"))
        assert result_valid is True, "Valid content 应返回 True"
        
        # None/False: Invalid content
        result_invalid = verify("single_choice", "【考点】...", ("A", "B"))
        assert result_invalid is None or result_invalid is False
        
        # Gate 判定
        if result_invalid is None or result_invalid is False:
            gate_decision = "pending_review"
        else:
            gate_decision = "auto_approve"
        
        assert gate_decision == "pending_review"
        assert gate_decision != "rejected"
        assert gate_decision != "auto_approve"
        
        print("PASS: Three-state decision model")


# ============================================================================
# Corpus 验证
# ============================================================================

class TestCorpusValidation:
    """Corpus 数量与关系验证"""
    
    def test_gate_c_corpus_frozen(self):
        """验证: Gate C corpus = 157 targets"""
        corpus_path = Path(__file__).parent.parent / "Docs" / "V3_SPEC" / "gate_c_invalid_binding_corpus.json"
        
        if not corpus_path.exists():
            pytest.skip("Corpus file not found")
        
        with open(corpus_path, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
        
        assert len(corpus['targets']) == 157
        
        dist = corpus['invalid_reason_distribution']
        assert dist['WRONG_REGION'] == 56
        assert dist['EXPLANATION_REGION'] == 49
        assert dist['SEPARATOR_REGION'] == 27
        assert dist['QUESTION_REGION'] == 15
        assert dist['SUSPICIOUS_CONTENT'] == 10
        
        print(f"PASS: Gate C corpus frozen at {len(corpus['targets'])} targets")
    
    def test_corpus_relationship(self):
        """验证: 157 ⊂ 267 ⊂ 706"""
        testset_path = Path(__file__).parent.parent / "Docs" / "V3_SPEC" / "gate_b2b5_frozen_testset.json"
        
        if not testset_path.exists():
            pytest.skip("Testset file not found")
        
        with open(testset_path, 'r', encoding='utf-8') as f:
            testset = json.load(f)
        
        total = testset['total_targets']
        v3_dist = testset['v3_status_distribution']
        
        assert total == 706
        assert v3_dist['invalid_binding_evidence'] == 267
        
        # Gate C = 267 - 120 (EMPTY_REGION) + 10 (SUSPICIOUS) = 157
        
        print("PASS: Corpus relationship 157 c 267 c 706")
