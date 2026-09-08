"""Gate B2（line_index 确定性）/B4（body 重建）/B5（integrity 敏感）纯函数 + hash 分层。

无 DB：同输入确定性 + raw/canonical hash 分层单元。DB 全链路在 test_seal_dbflow.py。
"""

import hashlib

import pytest

from app.ai.ocr.result import OCRLine
from app.core.hashing import sha256_hex
from app.domains.source.line_index import (
    build_line_index,
    compute_body_hash,
    compute_integrity_hash,
    compute_line_hash,
    rebuild_body_text,
    verify_body_rebuild,
)
from app.domains.source.seal import validate_seal_role_provider


def _ocr_lines():
    return (
        OCRLine(text="Alpha 1 first line", page_no=1, bbox={"x0": 0, "y0": 0, "x1": 1, "y1": 1}),
        OCRLine(text="Beta 2 second line", page_no=1, bbox=None),
        OCRLine(text="Gamma 3 third line", page_no=2, bbox={"x0": 0, "y0": 0, "x1": 1, "y1": 1}),
    )


def test_b2_line_index_deterministic_and_refs():
    a = build_line_index(_ocr_lines())
    b = build_line_index(_ocr_lines())
    assert a == b
    # line_ref = P{page}L{line_no:03d}；seq 跨页全局 1-based；页内 line_no 自增
    assert [(s.line_ref, s.seq, s.page_no, s.line_no_in_page) for s in a] == [
        ("P1L001", 1, 1, 1),
        ("P1L002", 2, 1, 2),
        ("P2L001", 3, 2, 1),
    ]
    assert [s.text for s in a] == ["Alpha 1 first line", "Beta 2 second line", "Gamma 3 third line"]


def test_b4_body_rebuild_roundtrip_and_verify():
    seal_lines = build_line_index(_ocr_lines())
    body = rebuild_body_text(seal_lines)
    assert body == "Alpha 1 first line\nBeta 2 second line\nGamma 3 third line"
    assert verify_body_rebuild(body, seal_lines)
    assert not verify_body_rebuild(body + " tampered", seal_lines)


def test_body_hash_is_raw_utf8_sha256_not_canonical():
    body = "abc"
    bh = compute_body_hash(body)
    assert bh == hashlib.sha256(b"abc").hexdigest()
    # raw 内容 hash 不得退化为 canonical（JSON 引号语义漂移）
    assert bh != sha256_hex(body)


def test_b5_integrity_hash_sensitive_to_any_change():
    base = {
        "body_hash": "b" * 64,
        "line_hashes": ["l1" * 32],
        "figure_hashes": [],
        "provenance": {"role": "native", "provider": "native"},
    }
    h = compute_integrity_hash(**base)
    assert compute_integrity_hash(**{**base, "line_hashes": ["l2" * 32]}) != h
    assert compute_integrity_hash(**{**base, "figure_hashes": ["f1" * 32]}) != h
    assert compute_integrity_hash(**{**base, "body_hash": "c" * 64}) != h


def test_line_hash_deterministic_and_sensitive():
    args = dict(
        text="t",
        raw_sources={"provider": "native"},
        selected_source="native",
        evidence="native text layer",
    )
    assert compute_line_hash(**args) == compute_line_hash(**args)
    assert compute_line_hash(**{**args, "text": "t2"}) != compute_line_hash(**args)
    assert compute_line_hash(**{**args, "evidence": "other"}) != compute_line_hash(**args)


# ---- BUG-V3-008（errata）：seal role/provider 封闭配对 fail-fast ----


def test_validate_seal_role_provider_accepts_closed_pairs():
    validate_seal_role_provider("native", "native")
    validate_seal_role_provider("ocr_ppsv3", "ppsv3")
    validate_seal_role_provider("ocr_ppsvl", "paddleocr-vl")
    validate_seal_role_provider("docx", "docx")


def test_validate_seal_role_provider_rejects_mismatched_pair():
    with pytest.raises(ValueError):
        validate_seal_role_provider("ocr_ppsv3", "paddleocr-vl")  # 归并会致 identity 漂移
    with pytest.raises(ValueError):
        validate_seal_role_provider("ocr_ppsvl", "ppsv3")


def test_validate_seal_role_provider_rejects_unknown_role():
    with pytest.raises(ValueError):
        validate_seal_role_provider("main", "native")  # 历史无效默认值
    with pytest.raises(ValueError):
        validate_seal_role_provider("canonical", "native")  # seal 阶段不产 canonical
