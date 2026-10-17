"""P2-CANDIDATE-DEDUP — Annotation 重跑不再无信息量复制 Candidate。

场景：
A. 同一输入重复运行 → 不新增等价 Candidate
B. 仅 subject/grade claims 变化 → Question 复用，不复制 Candidate，元数据到达 Question
C. Gate 判定实质变化 → 不错误复用旧判定
D. pending_review 保持 pending_review
E. 旧 Annotation / Question / Instance / role_contents 不被破坏
F. 真实判定差异不被静默吞掉
"""
import uuid

import pytest

from app.core.hashing import sha256_hex
from app.domains.gate.service import _candidate_semantic_projection


class TestCandidateSemanticProjection:
    """_candidate_semantic_projection 的确定性。"""

    def _payload(self, subject=None, stem="题干内容", unit_id="Q1"):
        return {
            "document_metadata_claims": {"subject": subject, "grade": "高一"},
            "sections": [],
            "semantic_units": [
                {"unit_id": unit_id, "unit_type": "standalone_unit",
                 "content": {"stem": {"text": stem}}}
            ],
            "producer_boundary": {"llm_unit_checks": []},
        }

    def test_subject_change_same_hash(self):
        """B: subject 变化不影响判定依据 → 同 hash。"""
        a = sha256_hex(_candidate_semantic_projection(self._payload(subject=None)))
        b = sha256_hex(_candidate_semantic_projection(self._payload(subject="物理")))
        assert a == b

    def test_stem_change_different_hash(self):
        """C: 题干变化 → 不同 hash → 新 Candidate。"""
        a = sha256_hex(_candidate_semantic_projection(self._payload(stem="A")))
        b = sha256_hex(_candidate_semantic_projection(self._payload(stem="B")))
        assert a != b

    def test_unit_id_different_hash(self):
        """unit_id 区分多 unit。"""
        a = sha256_hex(_candidate_semantic_projection(self._payload(unit_id="Q1")))
        b = sha256_hex(_candidate_semantic_projection(self._payload(unit_id="Q2")))
        assert a != b

    def test_producer_boundary_excluded(self):
        """producer_boundary（含 llm_unit_checks）不进判定依据。"""
        p1 = self._payload()
        p2 = self._payload()
        p2["producer_boundary"]["llm_unit_checks"] = [{"check": "new"}]
        a = sha256_hex(_candidate_semantic_projection(p1))
        b = sha256_hex(_candidate_semantic_projection(p2))
        assert a == b

    def test_sections_excluded(self):
        """sections 不进判定依据。"""
        p1 = self._payload()
        p2 = self._payload()
        p2["sections"] = [{"id": "S1"}]
        a = sha256_hex(_candidate_semantic_projection(p1))
        b = sha256_hex(_candidate_semantic_projection(p2))
        assert a == b

    def test_confidence_line_refs_excluded(self):
        """confidence / line_refs 不进判定依据。"""
        p1 = self._payload()
        p2 = self._payload()
        p2["semantic_units"][0]["confidence"] = 0.9
        p2["semantic_units"][0]["line_refs"] = ["P1L001"]
        a = sha256_hex(_candidate_semantic_projection(p1))
        b = sha256_hex(_candidate_semantic_projection(p2))
        assert a == b


class TestCompileInputDomain:
    """_compile_input_domain 不含 annotation_id。"""

    def test_annotation_id_not_in_domain(self):
        import uuid as _uuid
        from app.domains.gate.service import GateService

        ann = type("Ann", (), {"payload": {
            "semantic_units": [{"unit_id": "Q1"}],
            "document_metadata_claims": {"subject": "物理"},
        }})()
        id1 = _uuid.uuid4()
        id2 = _uuid.uuid4()
        d1 = GateService._compile_input_domain(id1, ann, "Q1")
        d2 = GateService._compile_input_domain(id2, ann, "Q1")
        assert d1 == d2, "annotation_id must not affect candidate identity"
        assert "annotation_id" not in d1

    def test_semantic_change_changes_domain(self):
        from app.domains.gate.service import GateService

        ann1 = type("Ann", (), {"payload": {
            "semantic_units": [{"unit_id": "Q1", "content": {"stem": {"text": "A"}}}],
        }})()
        ann2 = type("Ann", (), {"payload": {
            "semantic_units": [{"unit_id": "Q1", "content": {"stem": {"text": "B"}}}],
        }})()
        d1 = GateService._compile_input_domain(uuid.uuid4(), ann1, "Q1")
        d2 = GateService._compile_input_domain(uuid.uuid4(), ann2, "Q1")
        assert d1 != d2, "semantic change must produce different identity"
