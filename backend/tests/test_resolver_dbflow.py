"""Gate E — DB flow：seal lines/figures → 读 → Resolver 对接（段 E, E6/E7）。

用 Repository 直接建受控 sealed lines（native OCR 拆词不可控，故不依赖真实 PDF 内容），
验证 get_lines_by_version 确定性排序 + line_ref 对接 SourceResolver 端到端。
"""

import hashlib
import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.models.source import DocumentSourceLine
from app.repositories.source_repository import SourceRepository


async def _manual_seal(session, texts: list[str]):
    """Repository 直建 sealed version + 受控行（不经 OCR，保证 line 文本精确）。"""
    repo = SourceRepository(session)
    sha = uuid.uuid4().hex * 2  # 64-hex
    doc = await repo.create_document(
        original_object_key=f"raw:{sha}", original_sha256=sha,
        file_name="resolver_test.pdf", file_type="pdf",
        upload_meta={}, processing_status="ingesting",
    )
    await repo.flush()
    body = "\n".join(texts)
    ver = await repo.create_source_version(
        document_id=doc.id, artifact_kind="raw_l1", role="native", provider="native",
        body_text=body, body_hash=hashlib.sha256(body.encode()).hexdigest(),
        integrity_hash=hashlib.sha256(body.encode()).hexdigest(),
        page_count=1, line_count=len(texts), status="draft",
    )
    await repo.flush()
    for i, t in enumerate(texts):
        await repo.append_line(DocumentSourceLine(
            source_version_id=ver.id, line_ref=f"P1L{i + 1:03d}",
            seq=i + 1, page_no=1, line_no_in_page=i + 1,
            text=t, block_type="text", bbox=None,
            raw_sources={"provider": "native"}, selected_source="native",
            evidence="native text layer", line_hash="h" * 64,
        ))
    await repo.flush()
    await repo.seal_version(ver.id)
    await repo.set_document_status(doc.id, "sealed")
    await repo.flush()
    return ver.id


async def test_get_lines_ordered_by_seq(session):
    texts = ["1. 题干甲", "A. 苹果", "B. 香蕉", "2. 题干乙", "A. 猫", "B. 狗"]
    vid = await _manual_seal(session, texts)
    lines = await SourceRepository(session).get_lines_by_version(vid)
    assert [l.text for l in lines] == texts
    assert [l.line_ref for l in lines] == [f"P1L{i + 1:03d}" for i in range(6)]


async def test_resolver_end_to_end_dbflow(session):
    texts = ["1. 题干甲", "A. 苹果", "B. 香蕉", "2. 题干乙", "A. 猫", "B. 狗"]
    vid = await _manual_seal(session, texts)
    lines = await SourceRepository(session).get_lines_by_version(vid)
    views = tuple(
        SourceLineView(l.line_ref, l.text, l.seq, l.page_no, l.line_no_in_page)
        for l in lines
    )
    payload = {
        "semantic_units": [
            {"unit_id": "Q1", "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": "A"}, {"label": "B"}]}},
        ]
    }
    run = SourceResolver(source_version_id=vid, lines=views).resolve(payload)
    by_id = {s.span_id: s for s in run.resolved_spans}
    assert by_id["sp-Q1.stem"].line_refs == ("P1L001",)
    assert by_id["sp-Q1.option.A"].line_refs == ("P1L002",)
    assert by_id["sp-Q1.option.B"].line_refs == ("P1L003",)


async def test_get_figures_returns_empty_when_none(session):
    vid = await _manual_seal(session, ["1. 题干"])
    figs = await SourceRepository(session).get_figures_by_version(vid)
    assert figs == []
