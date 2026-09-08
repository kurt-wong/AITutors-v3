"""Native OCR provider 图提取（BUG-011-B）：无图=合法空集 / 有图=产 OCRFigure。

失败语义（amendment ②）：无 image placement → figures=()；已发现 placement 但无法完整提取
→ 产不完整 OCRFigure → seal IS-7 fail-loud。DB 全链路在 test_seal_dbflow.py。
"""

import hashlib

from app.ai.ocr.providers import NativeTextProvider


async def test_native_text_only_pdf_produces_no_figures(pdf_bytes):
    result = await NativeTextProvider().extract(pdf_bytes)
    assert result.figures == ()


async def test_native_pdf_with_image_produces_figure(pdf_bytes_with_figure):
    result = await NativeTextProvider().extract(pdf_bytes_with_figure)
    assert len(result.figures) == 1
    fig = result.figures[0]
    assert fig.page_no == 1
    assert fig.source == "native"
    assert fig.content  # 非空 raw bytes
    assert set(fig.bbox) == {"x0", "y0", "x1", "y1"}
    # bbox 与插入矩形 (72,200,172,300) 一致
    assert fig.bbox == {"x0": 72.0, "y0": 200.0, "x1": 172.0, "y1": 300.0}


async def test_native_figure_content_is_raw_extracted_bytes(pdf_bytes_with_figure):
    """figure.content = extract_image 的原始 bytes（非 resized/normalized），hash 稳定。"""
    import fitz

    result = await NativeTextProvider().extract(pdf_bytes_with_figure)
    fig = result.figures[0]

    doc = fitz.open(stream=pdf_bytes_with_figure, filetype="pdf")
    try:
        info = doc[0].get_image_info(xrefs=True)[0]
        raw = doc.extract_image(info["xref"])["image"]
    finally:
        doc.close()

    assert fig.content == raw
    assert hashlib.sha256(fig.content).hexdigest() == hashlib.sha256(raw).hexdigest()


async def test_native_figure_extraction_deterministic(pdf_bytes_with_figure):
    a = await NativeTextProvider().extract(pdf_bytes_with_figure)
    b = await NativeTextProvider().extract(pdf_bytes_with_figure)
    assert a.figures == b.figures
