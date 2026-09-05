"""Audit 工具：idempotency_key（30 §10——同一 LE+attempt 同一逻辑请求的稳定键，请求前生成、重试沿用）。"""

import uuid

from app.core.hashing import sha256_hex


def build_idempotency_key(
    *,
    logical_execution_stage: str,
    logical_execution_hash: str,
    attempt_id: uuid.UUID | None,
    provider: str,
    model: str,
    stage: str,
) -> str:
    """provider/model/stage 参与键（不同 provider 的 external call 身份不同）；attempt 参与区分。"""
    payload = {
        "logical_execution_stage": logical_execution_stage,
        "logical_execution_hash": logical_execution_hash,
        "attempt_id": str(attempt_id) if attempt_id else None,
        "provider": provider,
        "model": model,
        "stage": stage,
    }
    return sha256_hex(payload)
