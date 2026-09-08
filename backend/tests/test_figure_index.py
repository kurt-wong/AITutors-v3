"""Gate（figure identity 确定性 / IS-7 写入门 / raw hash 分层）纯函数 + hash 分层。

无 DB：canonical visual order → figure_id 确定性；IS-7 fail-loud；figure_hash raw SHA256。
DB 全链路在 test_seal_dbflow.py。
"""

import hashlib

import pytest

from app.ai.ocr.result import OCRFigure
from app.core.hashing import sha256_hex
from app.domains.source.figure_index import (
    build_figure_index,
    compute_figure_hash,
)


def _fig(page_no, bbox, content=b"img-bytes", source="native"):
    return OCRFigure(page_no=page_no, bbox=bbox, source=source, content=content)


def _bbox(x0=0, y0=0, x1=100, y1=50):
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


# ---- figure_id / canonical visual order ----


def test_single_page_single_figure_gets_fig_1_01():
    sf = build_figure_index((_fig(1, _bbox()),))[0]
    assert sf.figure_id == "FIG-1-01"
    assert sf.page_no == 1


def test_single_page_multiple_figures_canonical_visual_order():
    # 视觉序 = (page, top, left, bottom, right, hash, extraction_ordinal)
    # 下三图 top 递增 → ordinal 按 top 排序，与输入顺序无关
    bottom = _fig(1, _bbox(y0=200), content=b"bottom")
    top = _fig(1, _bbox(y0=0), content=b"top")
    mid = _fig(1, _bbox(y0=100), content=b"mid")
    sfs = build_figure_index((bottom, top, mid))
    assert [s.figure_id for s in sfs] == ["FIG-1-01", "FIG-1-02", "FIG-1-03"]
    assert [s.content for s in sfs] == [b"top", b"mid", b"bottom"]


def test_same_page_top_then_left_tie_break():
    # top 相同 → left 决定顺序
    right = _fig(1, _bbox(x0=200), content=b"right")
    left = _fig(1, _bbox(x0=0), content=b"left")
    sfs = build_figure_index((right, left))
    assert [s.figure_id for s in sfs] == ["FIG-1-01", "FIG-1-02"]
    assert [s.content for s in sfs] == [b"left", b"right"]


def test_multi_page_page_scoped_ordinal():
    p2 = _fig(2, _bbox(), content=b"page2")
    p1b = _fig(1, _bbox(y0=100), content=b"page1b")
    p1a = _fig(1, _bbox(y0=0), content=b"page1a")
    sfs = build_figure_index((p2, p1b, p1a))
    assert [s.figure_id for s in sfs] == ["FIG-1-01", "FIG-1-02", "FIG-2-01"]


def test_figure_index_no_collision():
    # 纯函数 invariant：canonical 排序后 figure_id 全局唯一
    figs = tuple(
        _fig(p, _bbox(x0=i * 10, y0=i * 10), content=bytes([i]))
        for i in range(1, 30)
        for p in (1, 2, 3)
    )
    ids = [s.figure_id for s in build_figure_index(figs)]
    assert len(ids) == len(set(ids))


def test_figure_order_change_does_not_change_identity():
    # 同一 source bytes 上 provider extraction order 变化 → canonical 后 identity 不变
    a = _fig(1, _bbox(y0=0), content=b"a")
    b = _fig(1, _bbox(y0=100), content=b"b")
    fwd = build_figure_index((a, b))
    rev = build_figure_index((b, a))
    assert [(s.figure_id, s.content) for s in fwd] == [
        (s.figure_id, s.content) for s in rev
    ]


def test_extraction_ordinal_is_last_tie_breaker_only():
    # 完全相同的 (page,bbox,hash) → 仅 extraction_ordinal 区分 → 稳定序仍是 provider 序
    dup1 = _fig(1, _bbox(), content=b"same")
    dup2 = _fig(1, _bbox(), content=b"same")
    sfs = build_figure_index((dup1, dup2))
    assert [s.figure_id for s in sfs] == ["FIG-1-01", "FIG-1-02"]
    # 交换输入顺序 → 由于 (page,bbox,hash) 全同，ordinal 由 extraction_ordinal 定 → 跟随输入序
    sfs2 = build_figure_index((dup2, dup1))
    assert [s.content for s in sfs] == [s.content for s in sfs2]
    assert sfs[0].figure_hash == sfs[1].figure_hash


# ---- figure_hash ----


def test_same_image_twice_two_figures_same_hash():
    raw = b"same-image-content"
    f1 = _fig(1, _bbox(y0=0), content=raw)
    f2 = _fig(1, _bbox(y0=100), content=raw)
    sfs = build_figure_index((f1, f2))
    assert len(sfs) == 2
    assert sfs[0].figure_hash == sfs[1].figure_hash
    assert sfs[0].figure_id != sfs[1].figure_id


def test_different_images_different_hash():
    sfs = build_figure_index((_fig(1, _bbox(y0=0), content=b"a"), _fig(1, _bbox(y0=100), content=b"b")))
    assert sfs[0].figure_hash != sfs[1].figure_hash


def test_figure_hash_is_raw_sha256_not_canonical():
    raw = b"raw-image-bytes"
    h = compute_figure_hash(raw)
    assert h == hashlib.sha256(raw).hexdigest()
    # canonical sha256_hex 仅接受 JSON 类型（bytes 被拒，BUG-V3-005）→ figure_hash 只能走 raw
    with pytest.raises(ValueError):
        sha256_hex(raw)


def test_figure_hash_is_not_figure_id():
    sf = build_figure_index((_fig(1, _bbox()),))[0]
    assert sf.figure_hash != sf.figure_id
    assert sf.object_key == f"figure:{sf.figure_hash}"
    assert sf.object_key != sf.figure_id


def test_figure_content_change_changes_hash():
    a = compute_figure_hash(b"a")
    b = compute_figure_hash(b"b")
    assert a != b


# ---- IS-7 写入门：无 figure 合法 / 不完整 figure fail-loud ----


def test_no_figures_is_legal_empty_set():
    assert build_figure_index(()) == ()


@pytest.mark.parametrize(
    "bbox",
    [
        {},  # 空 dict
        {"x0": 1},  # 缺键
        {"x0": None, "y0": 0, "x1": 1, "y1": 1},  # None 值
        {"x0": float("nan"), "y0": 0, "x1": 1, "y1": 1},  # NaN
        {"x0": float("inf"), "y0": 0, "x1": 1, "y1": 1},  # inf
        {"x0": "1", "y0": 0, "x1": 1, "y1": 1},  # 字符串非数值
    ],
)
def test_is7_fail_loud_on_invalid_bbox(bbox):
    with pytest.raises(ValueError):
        build_figure_index((_fig(1, bbox),))


def test_is7_fail_loud_on_empty_source():
    with pytest.raises(ValueError):
        build_figure_index((_fig(1, _bbox(), source=""),))


def test_is7_fail_loud_on_empty_content():
    with pytest.raises(ValueError):
        build_figure_index((_fig(1, _bbox(), content=b""),))


def test_is7_fail_loud_on_illegal_page_no():
    with pytest.raises(ValueError):
        build_figure_index((_fig(0, _bbox()),))


def test_is7_fail_loud_rejects_partial_write():
    # 一好一坏：坏 figure 使整个 build 失败（无部分成功）
    good = _fig(1, _bbox(y0=0), content=b"good")
    bad = _fig(1, _bbox({"x0": 1}), content=b"bad")
    with pytest.raises(ValueError):
        build_figure_index((good, bad))
