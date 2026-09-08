"""OCR providers（段 B）。Native = 本地确定性（PyMuPDF 文本层）；Cloud = PaddleOCR-VL
external（只经 OCRGateway 调用）；Mock = 测试注入。

边界：Native 属本地确定性（30 §16 不强审计，SealService 直调）；Cloud 属 external
（30 §6 必须经 Gateway，业务层禁直调）。段 B 不接线 Cloud transport（不做 live 冒烟）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.ai.ocr.result import OCRFigure, OCRLine, OCRResult

if TYPE_CHECKING:
    import fitz


@runtime_checkable
class OCRProvider(Protocol):
    name: str

    async def extract(self, file_bytes: bytes) -> OCRResult: ...


def _bbox(seq: tuple[float, float, float, float] | None) -> dict | None:
    """fitz bbox (x0,y0,x1,y1) -> JSON 可存 dict；None 则不强造。"""
    if seq is None:
        return None
    return {"x0": seq[0], "y0": seq[1], "x1": seq[2], "y1": seq[3]}


class NativeTextProvider:
    """PyMuPDF 文本层提取 → 每页文本行。本地确定性，无 external side effect。"""

    name = "native"
    model = "pymupdf"

    async def extract(self, file_bytes: bytes) -> OCRResult:
        import fitz  # lazy：仅 native 路径加载，disabled/mock 不 import

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            lines: list[OCRLine] = []
            page_count = doc.page_count
            for pno in range(page_count):
                page = doc[pno]
                page_dict = page.get_text("dict")
                for block in page_dict.get("blocks", []):
                    if block.get("type", -1) != 0:  # 0 = text block
                        continue
                    for line in block.get("lines", []):
                        text = "".join(sp["text"] for sp in line.get("spans", [])).strip()
                        if not text:
                            continue
                        lines.append(
                            OCRLine(
                                text=text,
                                page_no=pno + 1,
                                bbox=_bbox(line.get("bbox")),
                            )
                        )
            figures = self._extract_figures(doc)
        finally:
            doc.close()
        return OCRResult(
            provider=self.name,
            model=self.model,
            pages=page_count,
            lines=tuple(lines),
            figures=tuple(figures),
            source_meta={"engine": self.name, "method": "text-layer"},
        )

    def _extract_figures(self, doc: "fitz.Document") -> list[OCRFigure]:
        """原生图片提取：已放置图（get_image_info）→ 图 bytes + page 定位。

        失败语义（BUG-011 amendment ②）：无 image placement = 合法空集；已发现 placement 但
        无法形成完整 figure（缺 bbox / xref 不可提取）→ 产不完整 OCRFigure（空 content/bbox），
        交由 seal IS-7 fail-loud，绝不 try/except continue 静默丢图。
        """
        figures: list[OCRFigure] = []
        for pno in range(doc.page_count):
            page = doc[pno]
            for info in page.get_image_info(xrefs=True):
                bbox = _bbox(info.get("bbox"))
                xref = info.get("xref")
                content = b""
                if xref is not None:
                    try:
                        content = doc.extract_image(xref)["image"]
                    except Exception:
                        content = b""  # 提取失败 → 不完整 figure（seal IS-7 fail-loud）
                figures.append(
                    OCRFigure(
                        page_no=pno + 1,
                        bbox=bbox or {},
                        source=self.name,
                        content=content,
                    )
                )
        return figures


class MockOCRProvider:
    """测试/流程 provider：返回注入的确定性 OCRResult，无 external side effect。"""

    name = "mock"

    def __init__(self, result: OCRResult) -> None:
        self._result = result

    async def extract(self, file_bytes: bytes) -> OCRResult:
        return self._result


class CloudOCRProvider:
    """PaddleOCR-VL-1.6 异步 API（external）。只经 OCRGateway 调用。

    段 B 只建结构：真实 submit→poll→download→parse 契约见
    `Docs/reference/PADDLEOCR_API.md` + `OCR_PROVIDER_POLICY.md`（错误码 401/10010/
    12001/12002）。transport 不接线（live 冒烟段 F 后），段 B 不发明异步网络细节。
    """

    name = "paddleocr-vl"

    def __init__(self, *, model: str, base_url: str, token: str | None) -> None:
        self.model = model
        self._base_url = base_url
        self._token = token

    async def extract(self, file_bytes: bytes) -> OCRResult:
        raise NotImplementedError(
            "PaddleOCR-VL transport 未接线（段 B 骨架：cloud OCR live 冒烟在段 F 后；"
            "契约见 Docs/reference/PADDLEOCR_API.md）"
        )

    @staticmethod
    def markdown_lines_to_ocr_lines(page_text: str, page_no: int) -> tuple[OCRLine, ...]:
        """页 markdown 文本按换行拆成版面行（无 bbox，block_type 由 seal 定 text）。"""
        return tuple(
            OCRLine(text=ln, page_no=page_no)
            for ln in page_text.split("\n")
            if ln.strip()
        )
