"""Preprocessing text extractor: accepted Markdown → OCRResult for Seal.

Formal-path only. Does NOT re-extract from PDF. Fails closed if markdown
bytes are missing. Never falls back to NativeTextProvider.
"""

from __future__ import annotations

import hashlib

from app.ai.ocr.result import OCRLine, OCRResult


class PreprocessingTextExtractor:
    """Serve already-accepted preprocessing Markdown as Seal input.

    Identity contract:
    - Callers pass the ORIGINAL file bytes to SealService (PDF/DOCX) so
      `documents.original_sha256` stays the original-document identity.
    - This extractor only supplies the SOURCE text body and records
      `source_content_sha256` = SHA256(markdown raw bytes) in source_meta.
    """

    name = "preprocessing"
    model = "preprocessing-markdown"

    def __init__(self, source_md: bytes, *, manifest_meta: dict | None = None) -> None:
        if not source_md:
            raise ValueError("preprocessing source markdown is empty")
        self._source_md = source_md
        self._manifest_meta = dict(manifest_meta or {})
        self._source_content_sha256 = hashlib.sha256(source_md).hexdigest()

    @property
    def source_content_sha256(self) -> str:
        return self._source_content_sha256

    async def extract(self, file_bytes: bytes) -> OCRResult:
        # file_bytes is the ORIGINAL document (identity). Text comes from MD.
        del file_bytes
        text = self._source_md.decode("utf-8")
        raw_lines = text.splitlines()
        lines: list[OCRLine] = []
        # Preserve 1:1 raw markdown line numbering (including blank lines) so
        # Producer manifest stem_lines/answer_lines bind correctly (M2-R2).
        for i, raw in enumerate(raw_lines, start=1):
            content = raw.rstrip("\n")
            lines.append(OCRLine(text=content, page_no=1, bbox=None, spans=()))

        source_meta = {
            "source_mode": "preprocessing",
            "source_content_sha256": self._source_content_sha256,
            "preprocessing": self._manifest_meta,
        }
        return OCRResult(
            provider=self.name,
            model=self.model,
            pages=1,
            lines=tuple(lines),
            figures=(),
            source_meta=source_meta,
        )
