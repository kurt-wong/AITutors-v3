"""Source Seal 编排（段 B，40 §2）。SealService 负责确定性 seal 全流程。

边界铁律（P0）：SealService 只负责「要 OCR」+ 拿 OCRResult 后的确定性编排
（line index → hash → persist → seal）。它不操作 audit/budget、不 import 不直调
`CloudOCRProvider`；external OCR 的合法性/lifecycle 全在 OCRGateway。本地确定性
seal（native）30 §16 不强审计、不走 budget。

extractor 由调用方注入：native = `NativeTextProvider().extract`；cloud =
`OCRGateway(mode...).extract`（段 B 真实运行只走 native）。
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Awaitable, Callable

from app.ai.ocr.result import OCRResult
from app.core.hashing import logical_execution_hash
from app.domains.source.line_index import (
    SealLine,
    build_line_index,
    compute_body_hash,
    compute_integrity_hash,
    compute_line_hash,
    rebuild_body_text,
    verify_body_rebuild,
)
from app.models.source import DocumentSourceLine, DocumentSourceVersion
from app.repositories.source_repository import SourceRepository

SEAL_CONTRACT_VERSION = "seal/v1"

_STAGE = "seal"
_ARTIFACT_KIND = "raw_l1"  # OCR/native 第一层结构化文本（10 §4.2）

# BUG-V3-008（errata）：seal role/provider 封闭配对。独立引擎必须独立身份，防 LE identity 漂移。
_SEAL_ROLE_PROVIDERS = {
    "native": {"native"},
    "ocr_ppsv3": {"ppsv3"},
    "ocr_ppsvl": {"paddleocr-vl"},
    "docx": {"docx"},
}


def validate_seal_role_provider(role: str, provider: str) -> None:
    """校验 seal role/provider 封闭配对（BUG-V3-008 errata）；非法组合 fail-fast。"""
    allowed = _SEAL_ROLE_PROVIDERS.get(role)
    if allowed is None:
        raise ValueError(f"unknown seal role: {role!r}")
    if provider not in allowed:
        raise ValueError(
            f"seal role/provider mismatch: role={role!r} provider={provider!r}"
            f" (allowed: {sorted(allowed)})"
        )

Extractor = Callable[[bytes], Awaitable[OCRResult]]


class SealService:
    """一次确定性 seal：幂等 lookup → extract → line index → hash → persist → sealed。"""

    def __init__(self, session) -> None:
        self._repo = SourceRepository(session)

    async def seal_document(
        self,
        *,
        file_bytes: bytes,
        file_name: str,
        file_type: str,
        role: str,
        provider: str,
        extractor: Extractor,
    ) -> DocumentSourceVersion:
        """返回 sealed DocumentSourceVersion（幂等：同文件+同 role/provider/contract → 既有行）。

        role/provider 为 seal 执行契约的一部分（10 §4.2 role / §4.3 provider 语义），
        extractor 必须与 role/provider 一致（native 本地确定性 / cloud 经 OCRGateway）。
        """
        validate_seal_role_provider(role, provider)
        original_sha256 = hashlib.sha256(file_bytes).hexdigest()

        document = await self._repo.find_document_by_sha256(original_sha256)
        if document is None:
            document = await self._repo.create_document(
                original_object_key=f"raw:{original_sha256}",  # 确定性占位；对象存储延后
                original_sha256=original_sha256,
                file_name=file_name,
                file_type=file_type,
                upload_meta={},
                processing_status="ingesting",
            )
            await self._repo.flush()
        doc_id = document.id

        le_hash = logical_execution_hash(
            task_type="document_ingest",
            stage=_STAGE,
            contract_domain={
                "seal_contract_version": SEAL_CONTRACT_VERSION,
                "parser": {"provider": provider, "role": role},
            },
            input_domain={"original_sha256": original_sha256},
        )

        existing = await self._repo.find_sealed_version_by_le(
            document_id=doc_id, logical_execution_hash=le_hash
        )
        if existing is not None:
            return existing

        try:
            result = await extractor(file_bytes)
        except Exception:
            await self._repo.set_document_status(doc_id, "failed")
            await self._repo.flush()
            raise

        lines = build_line_index(result.lines)
        body_text = rebuild_body_text(lines)
        if not verify_body_rebuild(body_text, lines):
            raise ValueError("body_text is not deterministic from line index (IS-4)")
        body_hash = compute_body_hash(body_text)

        provenance = {"role": role, "provider": provider, "artifact_kind": _ARTIFACT_KIND}
        line_hashes: list[str] = []
        for sl in lines:
            line_hashes.append(self._line_hash(sl, provider))
        integrity_hash = compute_integrity_hash(
            body_hash=body_hash,
            line_hashes=line_hashes,
            figure_hashes=[],
            provenance=provenance,
        )

        version = await self._repo.create_source_version(
            document_id=doc_id,
            artifact_kind=_ARTIFACT_KIND,
            role=role,
            provider=provider,
            body_text=body_text,
            body_hash=body_hash,
            integrity_hash=integrity_hash,
            page_count=result.pages,
            line_count=len(lines),
            status="draft",
            source_meta=dict(result.source_meta),
            logical_execution_stage=_STAGE,
            logical_execution_hash=le_hash,
            attempt_id=None,
        )
        await self._repo.flush()
        # H-1 并发收敛：create_source_version ON CONFLICT re-read 返回 existing sealed →
        # 复用（跳过 append/seal），避免对已 sealed 行重复写。
        if version.status == "sealed":
            return version

        for sl in lines:
            await self._repo.append_line(self._to_source_line(version.id, sl, provider))
        await self._repo.flush()

        await self._repo.seal_version(version.id)
        await self._repo.set_document_status(doc_id, "sealed")
        await self._repo.flush()
        return version

    def _line_hash(self, sl: SealLine, provider: str) -> str:
        return compute_line_hash(
            text=sl.text,
            raw_sources={"provider": provider},
            selected_source=provider,
            evidence=f"{provider} text layer",
        )

    def _to_source_line(
        self, source_version_id: uuid.UUID, sl: SealLine, provider: str
    ) -> DocumentSourceLine:
        return DocumentSourceLine(
            source_version_id=source_version_id,
            line_ref=sl.line_ref,
            seq=sl.seq,
            page_no=sl.page_no,
            line_no_in_page=sl.line_no_in_page,
            text=sl.text,
            block_type=sl.block_type,
            bbox=sl.bbox,
            raw_sources={"provider": provider},
            selected_source=provider,
            evidence=f"{provider} text layer",
            line_hash=self._line_hash(sl, provider),
        )
