"""AnnotationService（段 D，20 §4）：幂等写 + LLMExecutor mock 调用 + forbidden-field 校验。

边界：只负责 annotation payload 的 LLM 获取 → JSON 解析 → 校验 → 落库。不负责 prompt
构造（caller 提供）、不负责 Resolver/Compiler/Gate（段 E/F/G）、不直接修改已有 annotation
状态（supersede 由 caller 显式调 repository）。

Lock-3（H Phase 5）：Domain 不持有 LLMGateway/Provider 依赖，只经 LLMExecutor 发起模型执行。
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

        BUG-V3-009：这里不涉及 get_default_annotation（caller 业务）。
        BUG-V3-010：json.loads 失败 → status="invalid" + payload={"parse_error":...} + raise。
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

        try:
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
        except Exception as exc:
            ann = await self._repo.create_semantic_annotation(
                source_version_id=source_version_id,
                annotation_schema_version=annotation_schema_version,
                prompt_version=prompt_version,
                model_config_hash=model_config_hash,
                payload={"provider_error": str(exc)},
                status="invalid",
                logical_execution_stage=_STAGE,
                logical_execution_hash=le_hash,
                attempt_id=attempt_id,
            )
            await self._repo.flush()
            raise

        try:
            payload = json.loads(response)
        except (json.JSONDecodeError, TypeError) as exc:
            # BUG-V3-010：parse error payload 形态未冻结；用 parse_error dict 占位（NOT NULL）
            ann = await self._repo.create_semantic_annotation(
                source_version_id=source_version_id,
                annotation_schema_version=annotation_schema_version,
                prompt_version=prompt_version,
                model_config_hash=model_config_hash,
                payload={"parse_error": str(exc)},
                status="invalid",
                logical_execution_stage=_STAGE,
                logical_execution_hash=le_hash,
                attempt_id=attempt_id,
            )
            await self._repo.flush()
            raise ValueError(f"LLM response not valid JSON: {exc}") from exc

        ok, violations = validate_annotation_payload(payload)
        status = "valid" if ok else "invalid"

        ann = await self._repo.create_semantic_annotation(
            source_version_id=source_version_id,
            annotation_schema_version=annotation_schema_version,
            prompt_version=prompt_version,
            model_config_hash=model_config_hash,
            payload=payload,
            status=status,
            logical_execution_stage=_STAGE,
            logical_execution_hash=le_hash,
            attempt_id=attempt_id,
        )
        await self._repo.flush()

        if not ok:
            raise ValueError(
                f"annotation payload contains forbidden fields: {violations}"
            )
        return ann
