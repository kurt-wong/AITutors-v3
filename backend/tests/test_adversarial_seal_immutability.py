"""对抗性审查 — Sealed 不可变 + FORBIDDEN_FIELDS + UNIQUE（H-ADV-SEAL）。

针对第四份摸底报告声称的可证伪缺口，**不采信报告结论，逐条实测**：

  S-GAP-1 (HIGH 声称)：draft source_version 能否被 annotation 引用？
                        （10 §4.5「只允许指向 sealed version」）
  S-GAP-2 (MEDIUM 声称)：sealed version 能否被 append_line 直接注入行？
                        （10 §4.2「sealed 后禁任何 UPDATE」「sealed 行无 UPDATE/DELETE」）
  S-GAP-3 (MEDIUM 声称)：UNIQUE(question_id, source_version_id, occurrence_key)
                        是否真在 DB 层拒绝重复插入？
  S-GAP-6 (LOW 声称)：FORBIDDEN_FIELDS 对 list-in-list 嵌套是否递归命中？
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.hashing import sha256_hex
from app.domains.annotation import validate_annotation_payload
from app.models.content import Question, QuestionInstance
from app.models.source import DocumentSourceLine
from app.repositories.source_repository import SourceRepository
from app.repositories.snapshot_repository import SnapshotRepository


async def _mk_doc_and_version(session, *, status: str, texts=("1. 题干", "A. 甲")):
    """造 document + 指定 status 的 source version + 行。"""
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="d.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    sv = await src.create_source_version(
        document_id=doc.id, artifact_kind="pdf", role="native", provider="native",
        body_text="\n".join(texts), body_hash=sha256_hex(list(texts)),
        integrity_hash=sha256_hex(list(texts)), page_count=1, line_count=len(texts),
        status="draft",
    )
    await session.flush()
    for i, t in enumerate(texts):
        await src.append_line(DocumentSourceLine(
            source_version_id=sv.id, line_ref=f"P1L{i + 1:03d}", seq=i + 1,
            page_no=1, line_no_in_page=i + 1, text=t, block_type="text",
            line_hash=sha256_hex(t),
        ))
    await session.flush()
    if status == "sealed":
        await src.seal_version(sv.id)
        await session.flush()
    return doc, sv


# ---------------------------------------------------------------------------
# S-GAP-1：draft source_version 不得被 annotation 引用
# ---------------------------------------------------------------------------


async def test_annotation_cannot_reference_draft_source_version(session) -> None:
    """10 §4.5：`source_version_id` **只允许指向 sealed version**。

    构造 draft version，直接经 SnapshotRepository 建 annotation。
    按契约应拒绝。若放行，下游 Resolver/Gate 会消费一个仍可被改写的 source。
    """
    _doc, sv = await _mk_doc_and_version(session, status="draft")
    assert sv.status == "draft", f"前提：version 应为 draft，实为 {sv.status}"

    with pytest.raises(Exception) as ei:
        await SnapshotRepository(session).create_semantic_annotation(
            source_version_id=sv.id,
            annotation_schema_version="semantic-metadata-annotation/v0.3",
            prompt_version="semantic-annotation/v1",
            model_config_hash=sha256_hex("m"),
            payload={"semantic_units": []},
            status="valid",
            logical_execution_stage="ann",
            logical_execution_hash=sha256_hex(str(uuid.uuid4())),
        )

    msg = str(ei.value).lower()
    assert "seal" in msg or "status" in msg or "draft" in msg, (
        f"引用 draft source_version 应被拒绝并指出未 seal；"
        f"实际异常 = {type(ei.value).__name__}: {ei.value}。（S-GAP-1，10 §4.5）"
    )


# ---------------------------------------------------------------------------
# S-GAP-2：sealed version 不得被 append_line 注入行
# ---------------------------------------------------------------------------


async def test_append_line_on_sealed_version_is_rejected(session) -> None:
    """10 §4.2 / §8 不变量 1：sealed 后禁任何变更；sealed 行无 UPDATE/DELETE。

    `update_line()` 明确抛 AppendOnlyViolation，但 `append_line()` 是
    `await self.add(line)`，无 sealed 守卫。SealService 靠 early-return 规避，
    但**直接调 repository 的路径绕过它**。
    """
    _doc, sv = await _mk_doc_and_version(session, status="sealed")
    assert sv.status == "sealed"

    with pytest.raises(Exception) as ei:
        await SourceRepository(session).append_line(DocumentSourceLine(
            source_version_id=sv.id, line_ref="P99L001", seq=99,
            page_no=1, line_no_in_page=99, text="injected", block_type="text",
            line_hash=sha256_hex("injected"),
        ))
        await session.flush()

    msg = str(ei.value).lower()
    assert "seal" in msg or "append" in msg or "immutable" in msg, (
        f"向 sealed version 追加行应被拒绝；实际异常 = {type(ei.value).__name__}: {ei.value}。"
        f"若未抛错，sealed 源可被静默注入额外行，破坏 00 P3「seal 即不可变」。（S-GAP-2）"
    )


# ---------------------------------------------------------------------------
# S-GAP-3：UNIQUE(question_id, source_version_id, occurrence_key) DB 层拒绝
# ---------------------------------------------------------------------------


async def test_question_instances_unique_triple_rejects_duplicate(session) -> None:
    """10 §6.2：`UNIQUE(question_id, source_version_id, occurrence_key)`。

    schema 存在性已由 test_models_schema 的 pg_constraint 内省验证，但**从未真正插入重复行**。
    若约束配置有误（列错、未建），插入会静默成功。
    """
    doc, sv = await _mk_doc_and_version(session, status="sealed", texts=("x",))
    q = Question(
        canonical_question_type="single_choice",
        dedup_key=sha256_hex(str(uuid.uuid4())),
        subject="数学", grade="三年级",
    )
    session.add(q)
    await session.flush()

    def _inst():
        return QuestionInstance(
            question_id=q.id, document_id=doc.id, source_version_id=sv.id,
            occurrence_key="k1", question_number="1", question_number_range="1",
            page_no=1, instance_order=1,
        )

    session.add(_inst())
    await session.flush()

    session.add(_inst())   # ← 重复三元组
    with pytest.raises(IntegrityError):
        await session.flush()


# ---------------------------------------------------------------------------
# S-GAP-6：FORBIDDEN_FIELDS 对 list-in-list 递归
# ---------------------------------------------------------------------------


def test_forbidden_field_inside_list_in_list_is_detected() -> None:
    """20 §4.3：禁字段「任意深度出现即整体判 invalid」。

    现有测试覆盖了 dict-in-list（`items[0].answer_text`）与
    dict-in-list-in-dict（`sections[0].semantic_units[0].stem_text`），
    **未覆盖 list 嵌 list**。`_walk` 声称递归 list 时带下标。
    """
    payload = {"a": [[{"line_refs": ["P1L001"]}]]}
    ok, violations = validate_annotation_payload(payload)
    assert ok is False, "list-in-list 内的 line_refs 必须被检出（20 §4.3 任意深度）"
    assert any(v.endswith("line_refs") for v in violations), (
        f"violation 路径应以 line_refs 结尾；实为 {violations}"
    )
    assert "a[0][0].line_refs" in violations, (
        f"路径应可定位到 a[0][0].line_refs；实为 {violations}"
    )
