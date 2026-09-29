"""Consumer Identity Verification — M5 Identity Gate。

设计依据：
- PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §4.6
- PREPROCESSING-V3-CONTRACT-v0.2 §5.6.1 (G-15)

Truth Table（Owner 指令，超越 Design v1.1 §4.6）：
┌──────────────────┬──────────────────┬───────┐
│ Identity State   │ Semantic State   │ Gate  │
├──────────────────┼──────────────────┼───────┤
│ VERIFIED         │ AVAILABLE        │ PASS  │
│ VERIFIED         │ PENDING          │ BLOCK │
│ VERIFIED         │ None             │ BLOCK │
│ FAILED           │ (any)            │ BLOCK │
│ INVALID          │ (any)            │ BLOCK │
└──────────────────┴──────────────────┴───────┘

核心不变量：VERIFIED + PENDING = BLOCK（最高优先级）。

纯函数边界（Design v1.1 §4.6 冻结）：
- 零 IO、零副作用、不抛异常。
- 对非法输入（None / 缺失属性 / 错误类型）fail-closed 返回 BLOCK。
- 值域白名单：identity ∈ {VERIFIED, FAILED}；semantic ∈ {AVAILABLE, PENDING}。
- str subclass 防御：所有 str 值先规范化为 plain str，再做白名单比对。
"""

from dataclasses import dataclass, field

IDENTITY_GATE_VERSION = "1.2.0"

GATE_PASS = "PASS"
GATE_BLOCK = "BLOCK"

# ─── reason codes（冻结）───
REASON_IDENTITY_VERIFIED_SEMANTIC_AVAILABLE = "identity_verified_semantic_available"
REASON_IDENTITY_VERIFICATION_FAILED = "identity_verification_failed"
REASON_SEMANTIC_PENDING = "semantic_pending"
REASON_SEMANTIC_ABSENT = "semantic_absent"
REASON_INVALID_STATE = "invalid_state"
REASON_MALFORMED_INPUT = "malformed_input"

# ─── 值域白名单（冻结）───
_VALID_IDENTITY_VALUES = ("VERIFIED", "FAILED")
_VALID_SEMANTIC_VALUES = ("AVAILABLE", "PENDING")


def _normalize_str(val) -> str | None:
    """将 str 或 str subclass 规范化为 plain str。

    防御 str subclass 自定义 __eq__ 绕过白名单检查。
    非 str 类型返回 None。
    """
    if not isinstance(val, str):
        return None
    # str(x) 对 plain str 返回自身；对 subclass 返回 plain str 副本
    return str(val)


@dataclass(frozen=True)
class IdentityGateDecision:
    gate: str                    # "PASS" | "BLOCK"
    identity_state: str          # "VERIFIED" | "FAILED" | "INVALID"
    semantic_state: str | None   # "AVAILABLE" | "PENDING" | "INVALID" | None
    reason: str
    mismatches: tuple[str, ...] = field(default_factory=tuple)


def evaluate_identity_gate(verification) -> IdentityGateDecision:
    """汇总 M4 验证结果，做出放行/阻断决策。

    冻结名（DESIGN-v1.1 §4.6）= `evaluate_identity`；本模块导出同名别名。

    输入: verification — M4 VerificationResult（或等价对象）
    输出: IdentityGateDecision(gate=..., identity_state=..., ...)

    行为（Design v1.1 §4.6 + Owner Truth Table）：
      - identity=FAILED → BLOCK
      - identity=VERIFIED + semantic=None → BLOCK (semantic_absent)
      - identity=VERIFIED + semantic=PENDING → BLOCK (semantic_pending)
      - identity=VERIFIED + semantic=AVAILABLE → PASS
      - 非法输入 → BLOCK (malformed_input / invalid_state)
      - 白名单外值 → BLOCK (invalid_state)

    不抛异常。对任何输入返回 IdentityGateDecision。
    """
    # ── 防御：verification 本体 ──
    if verification is None:
        return IdentityGateDecision(
            GATE_BLOCK, "INVALID", None, REASON_MALFORMED_INPUT, ()
        )

    identity = getattr(verification, "identity", None)
    if identity is None:
        return IdentityGateDecision(
            GATE_BLOCK, "INVALID", None, REASON_MALFORMED_INPUT, ()
        )

    identity_value = _normalize_str(getattr(identity, "value", None))
    if identity_value is None:
        return IdentityGateDecision(
            GATE_BLOCK, "INVALID", None, REASON_MALFORMED_INPUT, ()
        )

    # ── 值域白名单：identity ──
    if identity_value not in _VALID_IDENTITY_VALUES:
        mismatches = getattr(identity, "mismatches", ())
        if not isinstance(mismatches, (list, tuple)):
            mismatches = ()
        return IdentityGateDecision(
            GATE_BLOCK, "INVALID", None, REASON_INVALID_STATE, tuple(mismatches)
        )

    # ── FAILED → BLOCK ──
    if identity_value == "FAILED":
        mismatches = getattr(identity, "mismatches", ())
        if not isinstance(mismatches, (list, tuple)):
            mismatches = ()
        return IdentityGateDecision(
            GATE_BLOCK, "FAILED", None,
            REASON_IDENTITY_VERIFICATION_FAILED, tuple(mismatches),
        )

    # ── VERIFIED: 检查 semantic ──
    mismatches = getattr(identity, "mismatches", ())
    if not isinstance(mismatches, (list, tuple)):
        mismatches = ()
    mismatches = tuple(mismatches)

    semantic = getattr(verification, "semantic", None)
    if semantic is None:
        return IdentityGateDecision(
            GATE_BLOCK, "VERIFIED", None, REASON_SEMANTIC_ABSENT, mismatches
        )

    semantic_value = _normalize_str(getattr(semantic, "value", None))
    if semantic_value is None:
        return IdentityGateDecision(
            GATE_BLOCK, "VERIFIED", "INVALID", REASON_INVALID_STATE, mismatches
        )

    # ── 值域白名单：semantic ──
    if semantic_value not in _VALID_SEMANTIC_VALUES:
        return IdentityGateDecision(
            GATE_BLOCK, "VERIFIED", "INVALID", REASON_INVALID_STATE, mismatches
        )

    # ── PENDING → BLOCK（核心不变量）──
    if semantic_value == "PENDING":
        return IdentityGateDecision(
            GATE_BLOCK, "VERIFIED", "PENDING", REASON_SEMANTIC_PENDING, mismatches
        )

    # ── VERIFIED + AVAILABLE → PASS ──
    return IdentityGateDecision(
        GATE_PASS, "VERIFIED", "AVAILABLE",
        REASON_IDENTITY_VERIFIED_SEMANTIC_AVAILABLE, mismatches,
    )


# DESIGN-v1.1 §4.6 冻结接口名（interface reference only，D2=b）。
evaluate_identity = evaluate_identity_gate
