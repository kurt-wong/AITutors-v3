"""段 A Repository create 方法真实 DB 往返全链路（flush 到 PostgreSQL，回滚隔离）。

补 coverage 缺口：create_role_content / create_material / create_unit_group /
append_figure / create_semantic_annotation / create_admission_candidate(flush) 等
create 方法此前未在真实 DB 上往返执行。
"""

from app.models.content import (
    InstanceFigureLink,
    KnowledgeNode,
    MaterialLink,
    QuestionKnowledgeLink,
    UnitGroupMember,
)
from app.models.source import DocumentSourceLine, SourceFigure
from app.repositories.content_repository import ContentRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

_SHA = "a" * 64


async def test_repository_create_db_roundtrip(session) -> None:
    """A 域/B 域/C 域 create 全链路真实写入 DB（含 FK 依赖链），rollback 隔离。"""
    sr = SourceRepository(session)
    cr = ContentRepository(session)
    snap = SnapshotRepository(session)

    # --- B 域 ---
    doc = await sr.create_document(
        original_object_key="obj/k.pdf", original_sha256=_SHA, file_name="p.pdf",
        file_type="pdf", upload_meta={}, processing_status="created",
    )
    await sr.flush()  # doc.id 由 client default 于 flush 赋值
    version = await sr.create_source_version(
        document_id=doc.id, artifact_kind="canonical_l1", role="canonical",
        provider="", body_text="", body_hash=_SHA, integrity_hash=_SHA,
        page_count=1, line_count=1, status="draft",
    )
    await sr.flush()  # version.id 落位后再建 line/figure
    line = DocumentSourceLine(source_version_id=version.id, line_ref="P1L001", seq=1,
                              page_no=1, line_no_in_page=1, text="x", block_type="text",
                              line_hash=_SHA)
    await sr.append_line(line)
    figure = SourceFigure(source_version_id=version.id, figure_id="FIG-1",
                          page_no=1, bbox={}, placement="stem", source="native",
                          object_key="obj/f.png", figure_hash=_SHA)
    await sr.append_figure(figure)
    await sr.flush()
    await sr.seal_version(version.id)
    await sr.flush()
    assert line.id and figure.id

    # --- A 域 ---
    question = await cr.create_question(subject="数学", grade="高一",
                                        canonical_question_type="single_choice",
                                        dedup_key=_SHA)
    await cr.flush()
    instance = await cr.create_instance(question_id=question.id, document_id=doc.id,
                                        source_version_id=version.id, occurrence_key=_SHA,
                                        page_no=1, instance_order=1, question_number="1",
                                        question_number_range="1")
    await cr.flush()
    role = await cr.create_role_content(instance_id=instance.id, role="stem",
                                        role_index=0, text="stem text", text_hash=_SHA,
                                        source_span={"ref": "P1L001"})
    material = await cr.create_material(subject="数学", grade="高一",
                                        source_version_id=version.id, text="shared",
                                        text_hash=_SHA, source_span={"ref": "P1L001"})
    unit_group = await cr.create_unit_group(unit_type="composite_unit",
                                            document_id=doc.id,
                                            source_version_id=version.id,
                                            question_number_range="1")
    await cr.flush()  # role/material/unit_group 落 id
    await sr.add(UnitGroupMember(unit_group_id=unit_group.id, instance_id=instance.id,
                                 member_order=1, role_in_group="child"))
    await sr.add(MaterialLink(instance_id=instance.id, material_id=material.id,
                              role="material_required", order=1))
    await sr.add(InstanceFigureLink(instance_id=instance.id, source_figure_id=figure.id,
                                    role="stem", order=1))
    await sr.flush()
    node = KnowledgeNode(tree_version="t1", subject="数学", code="KN1", name="node1",
                         source="seed")
    await sr.add(node)
    await sr.flush()  # node.id
    await sr.add(QuestionKnowledgeLink(question_id=question.id, knowledge_node_id=node.id,
                                       mapped_by="deterministic"))
    await sr.flush()
    assert instance.id and role.id and material.id and unit_group.id and node.id

    # --- C 域 ---
    ann = await snap.create_semantic_annotation(
        source_version_id=version.id, annotation_schema_version="v1", payload={},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=_SHA, prompt_version="p1", model_config_hash=_SHA,
    )
    await session.flush()  # ann.id 落位后再建 candidate
    candidate = await snap.create_admission_candidate(
        unit_type="standalone_unit", source_version_id=version.id, annotation_id=ann.id,
        build_versions={}, input_identity={}, payload={},
        logical_execution_stage="compile", logical_execution_hash=_SHA,
    )
    await session.flush()
    assert ann.id and candidate.id
    assert candidate.decision_status == "pending_review"
