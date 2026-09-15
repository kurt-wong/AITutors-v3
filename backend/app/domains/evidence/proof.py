"""Review Proof 生成与验证（EB-008 /92号 §5.2，DEC-016 Decision-2；机制定义 Rev-3 §4）。

review_proof = SHA256(canonical_json({
    candidate_id, review_result, reviewer_id, reviewed_at, app_secret
}))

三项边界声明（92号 §2）：
1. proof 粒度 = candidate 级（绑定 candidate_id，不绑定 claim/unit 级）
2. proof 防数据库直接篡改（改 review_result / 重放 proof → 验证失败），
   不负责 API 身份认证
3. API 访问控制属于 Deployment Environment Boundary（外部职责）

APP_SECRET：.env 提供，≥32 字节；缺失或过短 → 生成/验证均 fail-closed 抛错
（fail-closed 而非 fail-open，92号 §5.3）。
"""

from __future__ import annotations

import hmac
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.core.hashing import sha256_hex
from app.repositories.base import RepositoryError

# 92号 §5.2：APP_SECRET 最小长度（32 字节）
MIN_APP_SECRET_BYTES = 32

# validator 前缀：human_review 事件的 validator 固定为 "human/<reviewer_id>"
HUMAN_VALIDATOR_PREFIX = "human/"


def require_app_secret() -> str:
    """读取并校验 APP_SECRET（fail-closed：缺失/过短抛错）。"""
    secret = settings.app_secret or ""
    if len(secret.encode("utf-8")) < MIN_APP_SECRET_BYTES:
        raise RepositoryError(
            f"APP_SECRET missing or shorter than {MIN_APP_SECRET_BYTES} bytes; "
            "review proof unavailable (EB-008 fail-closed)"
        )
    return secret


def _to_utc_iso(value: datetime) -> str:
    """datetime → 确定性 UTC ISO-8601（microseconds 固定，保证重算一致）。"""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def generate_review_proof(
    *,
    candidate_id: uuid.UUID,
    review_result: str,
    reviewer_id: str,
    reviewed_at: datetime,
    app_secret: str | None = None,
) -> str:
    """生成 candidate 级 review proof（SHA256 hex，64 chars）。

    review_result 取 ValidationEvent.validation_result 值域（validated/rejected）。
    app_secret 显式传入仅用于测试；生产路径用 require_app_secret()。
    """
    secret = app_secret if app_secret is not None else require_app_secret()
    return sha256_hex(
        {
            "candidate_id": str(candidate_id),
            "review_result": review_result,
            "reviewer_id": reviewer_id,
            "reviewed_at": _to_utc_iso(reviewed_at),
            "app_secret": secret,
        }
    )


def human_validator(reviewer_id: str) -> str:
    """human_review 事件的 validator 标识：'human/<reviewer_id>'（92号 §6）。"""
    return f"{HUMAN_VALIDATOR_PREFIX}{reviewer_id}"


def reviewer_from_validator(validator: str) -> str | None:
    """从 validator 反解 reviewer_id；非 human 前缀返回 None。"""
    if not validator.startswith(HUMAN_VALIDATOR_PREFIX):
        return None
    return validator[len(HUMAN_VALIDATOR_PREFIX):]


def verify_review_proof(record) -> bool:
    """从事件字段重算 proof 并恒时比较（92号 §5.2 验证模块）。

    record：ValidationEventRecord（ORM）或同字段对象。
    要求字段：candidate_id, validation_result, validator, validated_at, review_proof,
    validation_method。

    非 human_review / 无 proof / proof 不匹配 → False（fail-closed 由调用方执行）。
    APP_SECRET 缺失时抛 RepositoryError（配置错误，不静默降级为 False）。
    """
    if record.validation_method != "human_review" or not record.review_proof:
        return False
    reviewer_id = reviewer_from_validator(record.validator)
    if reviewer_id is None:
        return False
    expected = generate_review_proof(
        candidate_id=record.candidate_id,
        review_result=record.validation_result,
        reviewer_id=reviewer_id,
        reviewed_at=record.validated_at,
    )
    return hmac.compare_digest(expected, record.review_proof)
