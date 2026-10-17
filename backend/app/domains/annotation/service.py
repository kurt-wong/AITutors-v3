"""AnnotationService（段 D，20 §4）：幂等写 + LLMExecutor mock 调用 + forbidden-field 校验。

边界：只负责 annotation payload 的 LLM 获取 → JSON 解析 → 校验 → 落库。不负责 prompt
构造（caller 提供）、不负责 Resolver/Compiler/Gate（段 E/F/G）、不直接修改已有 annotation
状态（supersede 由 caller 显式调 repository）。

Lock-3（H Phase 5）：Domain 不持有 LLMGateway/Provider 依赖，只经 LLMExecutor 发起模型执行。

H0-15 方案 B（H Phase 7）：LLM/provider/parse/schema 失败一律不创建 invalid artifact
（失败留 llm_call_audit + task 状态）；Annotation Artifact 只由成功路径写 status="valid"。
历史 invalid 行保留、不被本 service 复用或清洗（repo 层对历史残留的防御不变）。
"""

from __future__ import annotations

import json
import uuid

from app.ai.executor import LLMExecutor
from app.core.hashing import logical_execution_hash, sha256_hex
from app.domains.annotation import (
    ANNO_SCHEMA_VERSION,
    ANN_PROMPT_VERSION,
    validate_annotation_payload,
)
from app.models.snapshot import SemanticAnnotation
from app.repositories.snapshot_repository import SnapshotRepository

_STAGE = "ann"


def _payload_semantic_hash(payload: dict) -> str:
    """确定性 payload 语义哈希（P2-AID）。

    覆盖影响题目结果的确定性语义：semantic_units / document_metadata_claims / sections。
    剔除 semantic_units 各 unit 顶层的 confidence + line_refs（与
    gate/service._annotation_identity_projection 一致）。
    排除 producer_boundary（含 llm_unit_checks 等非确定性诊断）。
    """
    units = payload.get("semantic_units")
    projected_units = (
        [
            ({k: v for k, v in u.items() if k not in ("confidence", "line_refs")}
             if isinstance(u, dict) else u)
            for u in units
        ]
        if isinstance(units, list)
        else units
    )
    return sha256_hex({
        "semantic_units": projected_units,
        "document_metadata_claims": payload.get("document_metadata_claims"),
        "sections": payload.get("sections"),
    })


class AnnotationService:
    def __init__(self, session, llm_executor: LLMExecutor) -> None:
        self._repo = SnapshotRepository(session)
        self._executor = llm_executor

    async def annotate(
        self,
        *,
        source_version_id: uuid.UUID,
        prompt: str,
        model_config_hash: str,
        task_type: str = "document_ingest",
        annotation_schema_version: str = ANNO_SCHEMA_VERSION,
        prompt_version: str = ANN_PROMPT_VERSION,
        attempt_id: uuid.UUID | None = None,
        task_id: uuid.UUID | None = None,
        document_id: uuid.UUID | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> SemanticAnnotation:
        """幂等 annotation 写入（20 §4.7）。同 LE hash 已有 valid/superseded → 返回既有行。

        H0-15 方案 B：executor / JSON parse / forbidden-field 失败一律不创建 artifact，原始异常
        直接传播（失败占位属 Runtime 层，不占 Annotation (stage,hash)；P2-1 遮蔽随之消解）。
        BUG-V3-009：这里不涉及 get_default_annotation（caller 业务）。
        BUG-V3-010：json.loads 失败 → raise ValueError（方案 B：不再落 invalid 行）。
        attempt_id/task_id/document_id/provider/model 为 Runtime context 透传（mock/disabled 由
        executor 忽略；live 由 executor 校验必需）。attempt_id 仅作 Artifact Runtime Provenance
        （Lock-5），不进 LE hash。
        """
        le_hash = logical_execution_hash(
            task_type=task_type,
            stage=_STAGE,
            contract_domain={
                "annotation_schema_version": annotation_schema_version,
                "prompt_version": prompt_version,
                "model_config_hash": model_config_hash,
            },
            input_domain={"source_version_id": str(source_version_id)},
        )

        existing = await self._repo.find_annotation_by_le_hash(
            logical_execution_stage=_STAGE, logical_execution_hash=le_hash
        )
        if existing is not None:
            return existing

        # 方案 B：executor/provider 失败 → 不落 invalid artifact，原始异常直接传播
        # （live 下 executor 已 finalize audit FAILED；mock 无 audit，测试以异常为准）
        response = await self._executor.complete(
            prompt,
            le_stage=_STAGE,
            le_hash=le_hash,
            attempt_id=attempt_id,
            task_id=task_id,
            document_id=document_id,
            provider=provider,
            model=model,
        )

        try:
            payload = json.loads(response)
        except (json.JSONDecodeError, TypeError) as exc:
            # FORMAL-E2E-ENABLEMENT-03 Issue-C: minimal parse evidence (debug only;
            # no raw user content / secrets stored — only sizes + error class)
            _n = len(response) if isinstance(response, str) else None
            _b = len(response.encode("utf-8")) if isinstance(response, str) else None
            raise ValueError(
                f"LLM response not valid JSON: {exc} "
                f"[parse_error_type={type(exc).__name__} "
                f"response_chars={_n} response_bytes={_b}]"
            ) from exc

        ok, violations = validate_annotation_payload(payload)
        if not ok:
            # 方案 B：forbidden payload → 不落 invalid artifact，raise ValueError
            raise ValueError(
                f"annotation payload contains forbidden fields: {violations}"
            )

        ann = await self._repo.create_semantic_annotation(
            source_version_id=source_version_id,
            annotation_schema_version=annotation_schema_version,
            prompt_version=prompt_version,
            model_config_hash=model_config_hash,
            payload=payload,
            status="valid",
            logical_execution_stage=_STAGE,
            logical_execution_hash=le_hash,
            attempt_id=attempt_id,
        )
        await self._repo.flush()
        return ann

    async def annotate_from_payload(
        self,
        *,
        source_version_id: uuid.UUID,
        payload: dict,
        model_config_hash: str,
        task_type: str = "document_ingest",
        annotation_schema_version: str = ANNO_SCHEMA_VERSION,
        prompt_version: str = ANN_PROMPT_VERSION,
        attempt_id: uuid.UUID | None = None,
        task_id: uuid.UUID | None = None,
        document_id: uuid.UUID | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> SemanticAnnotation:
        """Persist a pre-built annotation payload without LLM re-split (M2-R2).

        Used by the formal preprocessing path where Producer manifest units are
        the authoritative unit source. Same LE hash / validation / persist rules
        as annotate(); no LLM call is made.
        """
        # P2-AID: include deterministic payload semantics in identity so that
        # manifest metadata changes (e.g. subject null→物理) produce a new
        # annotation instead of silently reusing a stale one.
        payload_hash = _payload_semantic_hash(payload)
        le_hash = logical_execution_hash(
            task_type=task_type,
            stage=_STAGE,
            contract_domain={
                "annotation_schema_version": annotation_schema_version,
                "prompt_version": prompt_version,
                "model_config_hash": model_config_hash,
            },
            input_domain={
                "source_version_id": str(source_version_id),
                "payload_semantic_hash": payload_hash,
            },
        )
        existing = await self._repo.find_annotation_by_le_hash(
            logical_execution_stage=_STAGE, logical_execution_hash=le_hash
        )
        if existing is not None:
            return existing

        ok, violations = validate_annotation_payload(payload)
        if not ok:
            raise ValueError(
                f"annotation payload contains forbidden fields: {violations}"
            )

        ann = await self._repo.create_semantic_annotation(
            source_version_id=source_version_id,
            annotation_schema_version=annotation_schema_version,
            prompt_version=prompt_version,
            model_config_hash=model_config_hash,
            payload=payload,
            status="valid",
            logical_execution_stage=_STAGE,
            logical_execution_hash=le_hash,
            attempt_id=attempt_id,
        )
        await self._repo.flush()
        return ann
