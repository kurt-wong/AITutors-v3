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
    """_compile_input_domain 不含 annotation_id，含 source_version_id。"""

    def test_semantic_same_same_domain(self):
        import uuid as _uuid
        from app.domains.gate.service import GateService

        ann = type("Ann", (), {"payload": {
            "semantic_units": [{"unit_id": "Q1"}],
            "document_metadata_claims": {"subject": "物理"},
        }})()
        sv = _uuid.uuid4()
        d1 = GateService._compile_input_domain(ann, "Q1", sv)
        d2 = GateService._compile_input_domain(ann, "Q1", sv)
        assert d1 == d2

    def test_annotation_id_not_in_domain(self):
        import uuid as _uuid
        from app.domains.gate.service import GateService

        ann = type("Ann", (), {"payload": {
            "semantic_units": [{"unit_id": "Q1"}],
            "document_metadata_claims": {"subject": "物理"},
        }})()
        d = GateService._compile_input_domain(ann, "Q1", _uuid.uuid4())
        assert "annotation_id" not in d

    def test_source_version_in_domain(self):
        import uuid as _uuid
        from app.domains.gate.service import GateService

        ann = type("Ann", (), {"payload": {
            "semantic_units": [{"unit_id": "Q1"}],
        }})()
        sv = _uuid.uuid4()
        d = GateService._compile_input_domain(ann, "Q1", sv)
        assert d.get("source_version_id") == str(sv)

    def test_semantic_change_changes_domain(self):
        import uuid as _uuid
        from app.domains.gate.service import GateService

        ann1 = type("Ann", (), {"payload": {
            "semantic_units": [{"unit_id": "Q1", "content": {"stem": {"text": "A"}}}],
        }})()
        ann2 = type("Ann", (), {"payload": {
            "semantic_units": [{"unit_id": "Q1", "content": {"stem": {"text": "B"}}}],
        }})()
        sv = _uuid.uuid4()
        d1 = GateService._compile_input_domain(ann1, "Q1", sv)
        d2 = GateService._compile_input_domain(ann2, "Q1", sv)
        assert d1 != d2, "semantic change must produce different identity"

    def test_cross_source_version_different_domain(self):
        import uuid as _uuid
        from app.domains.gate.service import GateService

        ann = type("Ann", (), {"payload": {
            "semantic_units": [{"unit_id": "Q1"}],
        }})()
        sv1, sv2 = _uuid.uuid4(), _uuid.uuid4()
        d1 = GateService._compile_input_domain(ann, "Q1", sv1)
        d2 = GateService._compile_input_domain(ann, "Q1", sv2)
        assert d1 != d2, "different source_version must produce different identity"


class TestMaterialConvergence:
    """P2-MATERIAL-METADATA: Candidate 复用时 Material subject/grade 收敛。"""

    async def _reannotate_composite(self, session, sv, claims):
        from app.repositories.snapshot_repository import SnapshotRepository
        from tests.test_gate_service import _composite_units
        return await SnapshotRepository(session).create_semantic_annotation(
            source_version_id=sv.id,
            annotation_schema_version="semantic-metadata-annotation/v0.3",
            prompt_version="semantic-annotation/v1",
            model_config_hash=sha256_hex(str(uuid.uuid4())),
            payload={"semantic_units": _composite_units(), "document_metadata_claims": claims},
            status="valid", logical_execution_stage="ann",
            logical_execution_hash=sha256_hex(str(uuid.uuid4())),
        )

    async def test_question_and_material_converge(self, session):
        """A: Candidate 复用时，Question 与关联 Material 的 subject/grade 均收敛。"""
        from tests.test_gate_service import _seed, COMPOSITE_LINES, _composite_units
        from app.domains.gate.service import GateService
        from app.models.content import Question, Material
        from sqlalchemy import select

        sv, ann = await _seed(
            session, texts=COMPOSITE_LINES,
            units=_composite_units(),
            claims={},
        )
        svc = GateService(session)
        await svc.run(source_version_id=sv.id, annotation_id=ann.id)
        await session.flush()

        q = (await session.execute(select(Question))).scalars().first()
        assert q.subject is None
        mats = (await session.execute(select(Material))).scalars().all()
        assert len(mats) > 0, "composite should have materials"
        for m in mats:
            assert m.subject is None

        ann2 = await self._reannotate_composite(session, sv, {"subject": "生物", "grade": "高一"})
        await svc.run(source_version_id=sv.id, annotation_id=ann2.id)
        await session.flush()

        q = (await session.execute(select(Question))).scalars().first()
        assert q.subject == "生物"
        assert q.grade == "高一"
        mats = (await session.execute(select(Material))).scalars().all()
        for m in mats:
            assert m.subject == "生物", f"Material {m.id} subject not converged"
            assert m.grade == "高一"

    async def test_no_material_link_normal_flow(self, session):
        """B: 不存在 Material 关联时，原流程正常。"""
        from tests.test_gate_service import _seed, _reannotate
        from app.domains.gate.service import GateService
        from app.models.content import Question
        from sqlalchemy import select

        sv, ann = await _seed(session, claims={})
        svc = GateService(session)
        await svc.run(source_version_id=sv.id, annotation_id=ann.id)
        await session.flush()

        ann2 = await _reannotate(session, sv, {"subject": "数学", "grade": "三年级"})
        await svc.run(source_version_id=sv.id, annotation_id=ann2.id)
        await session.flush()

        q = (await session.execute(select(Question))).scalars().first()
        assert q.subject == "数学"

    async def test_material_conflict_fails_loud(self, session):
        """C: 已有非空 Material subject 与新来源冲突 → RepositoryError，不静默覆盖。"""
        from tests.test_gate_service import _seed, COMPOSITE_LINES, _composite_units
        from app.domains.gate.service import GateService
        from app.repositories.base import RepositoryError
        import pytest

        sv, ann = await _seed(
            session, texts=COMPOSITE_LINES,
            units=_composite_units(),
            claims={"subject": "物理", "grade": "高一"},
        )
        svc = GateService(session)
        await svc.run(source_version_id=sv.id, annotation_id=ann.id)
        await session.flush()

        ann2 = await self._reannotate_composite(session, sv, {"subject": "化学", "grade": "高一"})
        with pytest.raises(RepositoryError):
            await svc.run(source_version_id=sv.id, annotation_id=ann2.id)

    async def test_no_dup_on_rerun(self, session):
        """D: 重跑不复制 Candidate/Question/Instance，不修改 Material 正文。"""
        from tests.test_gate_service import _seed, _count, COMPOSITE_LINES, _composite_units
        from app.domains.gate.service import GateService
        from app.models.content import Question, QuestionInstance, Material
        from app.models.snapshot import AdmissionCandidate
        from sqlalchemy import select

        sv, ann = await _seed(
            session, texts=COMPOSITE_LINES,
            units=_composite_units(),
            claims={},
        )
        svc = GateService(session)
        await svc.run(source_version_id=sv.id, annotation_id=ann.id)
        await session.flush()
        q1 = await _count(session, Question)
        i1 = await _count(session, QuestionInstance)
        c1 = await _count(session, AdmissionCandidate)
        m1 = sorted(m.text for m in (await session.execute(select(Material))).scalars().all())

        ann2 = await self._reannotate_composite(session, sv, {"subject": "生物", "grade": "高一"})
        await svc.run(source_version_id=sv.id, annotation_id=ann2.id)
        await session.flush()
        assert await _count(session, Question) == q1
        assert await _count(session, QuestionInstance) == i1
        assert await _count(session, AdmissionCandidate) == c1
        m2 = sorted(m.text for m in (await session.execute(select(Material))).scalars().all())
        assert m1 == m2, "Material text must not change"

    async def test_cross_source_version_isolation(self, session):
        """E: 两份不同 source_version 即使语义相同，也不共用 Candidate。"""
        from tests.test_gate_service import _seed
        from app.domains.gate.service import GateService

        sv1, ann1 = await _seed(session)
        sv2, ann2 = await _seed(session)

        svc = GateService(session)
        c1, _ = await svc.run(source_version_id=sv1.id, annotation_id=ann1.id)
        await session.flush()
        c2, _ = await svc.run(source_version_id=sv2.id, annotation_id=ann2.id)
        await session.flush()

        assert c1[0].id != c2[0].id, "different source_version must not share Candidate"
        assert c1[0].source_version_id != c2[0].source_version_id
