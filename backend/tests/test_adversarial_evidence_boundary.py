"""对抗性审查 — Evidence 边界产品契约测试（H-ADV-EVIDENCE）。

按 Owner 2026-09-13 四分类裁决，本文件**只保留产品契约测试**：

  F-3（no_cross_version 缺失）→ 留在此处，FAIL → 修复 → PASS，进正常 CI gate。

已迁出到 `tests/adversarial/spec_gap/`（module 级 xfail，不进 CI gate）：
  F-2  Evidence Authority Enforcement 未闭环（架构决策未决，非 bug）
  F-4  退化空白 marker → 自信 exact（输入鲁棒性，延后 preprocessing）

对应登记：bugs.md BUG-V3-045（F-3）、BUG-V3-048（F-2）、BUG-V3-049（F-4）。
"""

import uuid

import pytest

from app.core.hashing import sha256_hex
from app.domains.gate.service import GateService
from app.models.source import DocumentSourceLine
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

SINGLE_LINES = (
    "一、单选题（每小题4分，共32分）",
    "1. 已知弧长为5π的弧所对的圆心角为150°，则该弧所在圆的半径为",
    "A. 3",
    "B. 4",
    "C. 5",
    "D. 6",
)


def _single_units():
    return [
        {
            "unit_id": "Q1",
            "unit_type": "standalone_question",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}],
                "answer": {"answer_zone": "inline_answer", "question_label": "1"},
            },
        }
    ]


async def _seed_two_versions(session, texts_a, texts_b):
    """同一 document 下造两个 sealed source version，annotation 绑在 A 上。"""
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="x.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()

    async def _mk_sv(texts):
        sv = await src.create_source_version(
            document_id=doc.id, artifact_kind="raw_l1", role="native", provider="native",
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
        await src.seal_version(sv.id)
        await session.flush()
        return sv

    sv_a = await _mk_sv(texts_a)
    sv_b = await _mk_sv(texts_b)
    ann = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv_a.id,  # ← 绑在 A
        annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1", model_config_hash=sha256_hex("m"),
        payload={"semantic_units": _single_units(),
                 "document_metadata_claims": {"subject": "数学", "grade": "三年级"}},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv_a, sv_b, ann


# ---------------------------------------------------------------------------
# F-3 / BUG-V3-045：GateService.run 的 no_cross_version 校验
# ---------------------------------------------------------------------------


async def test_gate_run_rejects_annotation_from_different_source_version(session) -> None:
    """75 §六.4 no_cross_version：annotation 绑定的 source_version 必须与传入的一致。

    Owner 裁决（2026-09-13）：**确认 HIGH 产品实现缺陷，应修。**
    `annotation.status == valid` 只证明 annotation 有效，
    **没有证明它对当前 source 有效**。Source Version 是 V3 最核心不变量之一，
    不能跨版本解释。

    构造：同 document 下两个 sealed version（A、B 内容不同），annotation 绑 A，
    用 B 的 id 调 GateService.run。按契约应拒绝。若放行，resolver 会用 B 的行
    去解释为 A 设计的 payload —— provenance 错配。
    """
    texts_a = list(SINGLE_LINES)
    # B：同结构、不同数值——题号仍可解析，故若无校验就可能"成功"产出 candidate
    texts_b = [t.replace("5π", "9π").replace("150°", "120°") for t in texts_a]

    sv_a, sv_b, ann = await _seed_two_versions(session, texts_a, texts_b)
    assert ann.source_version_id == sv_a.id
    assert sv_b.id != sv_a.id

    with pytest.raises(Exception) as ei:
        await GateService(session).run(source_version_id=sv_b.id, annotation_id=ann.id)

    msg = str(ei.value).lower()
    assert "source_version" in msg or "cross" in msg, (
        f"跨 source_version 调用应被明确拒绝并指出 source_version 不一致；"
        f"实际异常 = {type(ei.value).__name__}: {ei.value}。（F-3，75 §六.4 no_cross_version）"
    )
