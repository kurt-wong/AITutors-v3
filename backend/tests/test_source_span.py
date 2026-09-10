"""SourceSpan 单元测试（Phase I-3-1）。"""

from __future__ import annotations

import pytest

from app.ai.ocr.result import OCRLine, SourceSpan, _make_span


class TestSourceSpanImmutability:
    def test_frozen_dataclass(self):
        span = _make_span(0, "test", "Helvetica", 11.0, 0, None, None)
        with pytest.raises(AttributeError):
            span.text = "modified"

    def test_frozen_bbox(self):
        span = _make_span(0, "test", "Helvetica", 11.0, 0, {"x0": 0}, None)
        with pytest.raises(AttributeError):
            span.bbox = {"x0": 1}


class TestSourceSpanHash:
    def test_deterministic_hash(self):
        span1 = _make_span(0, "test", "Helvetica", 11.0, 0, {"x0": 0, "y0": 0, "x1": 10, "y1": 10}, (5.0, 10.0))
        span2 = _make_span(0, "test", "Helvetica", 11.0, 0, {"x0": 0, "y0": 0, "x1": 10, "y1": 10}, (5.0, 10.0))
        assert span1.span_hash == span2.span_hash

    def test_spatial_identity_different_bbox(self):
        """相同文本不同位置 → 不同 hash（layout evidence identity）。"""
        span1 = _make_span(0, "x", "Cambria", 12.0, 0, {"x0": 0, "y0": 0, "x1": 10, "y1": 10}, (5.0, 10.0))
        span2 = _make_span(0, "x", "Cambria", 12.0, 0, {"x0": 100, "y0": 100, "x1": 110, "y1": 110}, (105.0, 110.0))
        assert span1.span_hash != span2.span_hash

    def test_spatial_identity_different_origin(self):
        """相同文本不同 origin → 不同 hash。"""
        span1 = _make_span(0, "x", "Cambria", 12.0, 0, None, (5.0, 10.0))
        span2 = _make_span(0, "x", "Cambria", 12.0, 0, None, (105.0, 110.0))
        assert span1.span_hash != span2.span_hash

    def test_different_text_different_hash(self):
        span1 = _make_span(0, "a", "Helvetica", 11.0, 0, None, None)
        span2 = _make_span(0, "b", "Helvetica", 11.0, 0, None, None)
        assert span1.span_hash != span2.span_hash

    def test_different_font_different_hash(self):
        span1 = _make_span(0, "x", "Helvetica", 11.0, 0, None, None)
        span2 = _make_span(0, "x", "Arial", 11.0, 0, None, None)
        assert span1.span_hash != span2.span_hash

    def test_different_flags_different_hash(self):
        span1 = _make_span(0, "x", "Helvetica", 11.0, 0, None, None)
        span2 = _make_span(0, "x", "Helvetica", 11.0, 1, None, None)  # superscript
        assert span1.span_hash != span2.span_hash

    def test_hash_length_64(self):
        span = _make_span(0, "test", "Helvetica", 11.0, 0, None, None)
        assert len(span.span_hash) == 64

    def test_hash_is_hex(self):
        span = _make_span(0, "test", "Helvetica", 11.0, 0, None, None)
        int(span.span_hash, 16)  # 不抛异常 = 合法 hex


class TestSourceSpanFlags:
    def test_superscript_flag(self):
        span = _make_span(0, "2", "Cambria", 8.0, 1, None, None)
        assert span.is_superscript is True
        assert span.is_subscript is False

    def test_subscript_flag(self):
        span = _make_span(0, "2", "Cambria", 8.0, 2, None, None)
        assert span.is_superscript is False
        assert span.is_subscript is True

    def test_bold_flag(self):
        span = _make_span(0, "text", "Helvetica", 11.0, 32, None, None)
        assert span.is_bold is True

    def test_italic_flag(self):
        span = _make_span(0, "text", "Helvetica", 11.0, 4, None, None)
        assert span.is_italic is True

    def test_no_flags(self):
        span = _make_span(0, "text", "Helvetica", 11.0, 0, None, None)
        assert span.is_superscript is False
        assert span.is_subscript is False
        assert span.is_bold is False
        assert span.is_italic is False

    def test_none_flags(self):
        span = _make_span(0, "text", "Helvetica", 11.0, None, None, None)
        assert span.is_superscript is False


class TestSourceLineComposition:
    def test_line_text_equals_join_spans(self):
        spans = (
            _make_span(0, "Hello ", "Helvetica", 11.0, 0, None, None),
            _make_span(1, "World", "Helvetica", 11.0, 0, None, None),
        )
        line = OCRLine(text="Hello World", page_no=1, bbox=None, spans=spans)
        assert line.text == "".join(s.text for s in line.spans)

    def test_line_default_empty_spans(self):
        line = OCRLine(text="test", page_no=1)
        assert line.spans == ()

    def test_line_with_spans(self):
        spans = (_make_span(0, "x", "Helvetica", 11.0, 0, None, None),)
        line = OCRLine(text="x", page_no=1, bbox=None, spans=spans)
        assert len(line.spans) == 1
        assert line.spans[0].text == "x"
