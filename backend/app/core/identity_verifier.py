"""Consumer Identity Verification — M4 Identity Verifier。

设计依据：
- PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §4.5
- PREPROCESSING-V3-CONTRACT-v0.2 §5.6.1 (G-15)

身份语义：
- Raw bytes SHA256 是唯一身份事实来源（DEC-031 原则 1）。
- Manifest 是身份声明；IR 是语义一致性证据。
- M4 不改变三者的权威等级。

判定规则（冻结）：
- Identity State: computed vs manifest。IR 禁止参与。
- Semantic State: ir vs manifest。独立于 Identity State。
- identity=FAILED 时 semantic=None（不判定语义）。

纯函数边界：
- 零 IO、零文件读取、零数据库访问、零副作用、不抛异常。
"""

from dataclasses import dataclass, field

IDENTITY_VERIFIER_VERSION = "1.0.0"

# ─── 冻结常量 ───

IDENTITY_VERIFIED = "VERIFIED"
IDENTITY_FAILED = "FAILED"

SEMANTIC_AVAILABLE = "AVAILABLE"
SEMANTIC_PENDING = "PENDING"

# mismatches reason codes
REASON_MANIFEST_SHA_MISSING = "manifest_sha_missing"
REASON_COMPUTED_MANIFEST_MISMATCH = "computed_manifest_mismatch"

# semantic reason codes
REASON_IR_ABSENT = "ir_absent"
REASON_IR_MANIFEST_MISMATCH = "ir_manifest_mismatch"


# ─── 数据类型（冻结）───


@dataclass(frozen=True)
class IdentityState:
    """Identity State — 身份轴，仅两值。"""

    value: str  # "VERIFIED" | "FAILED"
    mismatches: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SemanticState:
    """Semantic State — 语义轴，仅两值。"""

    value: str  # "AVAILABLE" | "PENDING"
    reason: str | None = None  # PENDING 时的原因，AVAILABLE 时为 None


@dataclass(frozen=True)
class VerificationResult:
    """M4 输出 — 正交双轴验证结果。"""

    identity: IdentityState
    semantic: SemanticState | None  # identity=FAILED 时为 None


# ─── 接口（冻结）───


def verify_identity(
    computed_sha: str,
    manifest_sha: str | None = None,
    ir_sha: str | None = None,
) -> VerificationResult:
    """比对三方 sha，返回正交双轴状态。

    输入:
      computed_sha: str — SHA256(raw bytes)，64-char lowercase hex（来自 M2）
      manifest_sha: str | None — Manifest 声明值（来自 M1）
      ir_sha: str | None — IR 提取值（来自 M3，None = IR 缺失）

    输出: VerificationResult(identity=..., semantic=...)

    判定规则:
      Identity State:
        manifest_sha is None → FAILED (manifest_sha_missing)
        computed != manifest → FAILED (computed_manifest_mismatch)
        computed == manifest → VERIFIED

      Semantic State (仅当 identity=VERIFIED):
        ir_sha is None       → PENDING (ir_absent)
        ir_sha != manifest   → PENDING (ir_manifest_mismatch)
        ir_sha == manifest   → AVAILABLE
    """
    # Step 1: Identity State 判定
    if manifest_sha is None:
        return VerificationResult(
            identity=IdentityState(IDENTITY_FAILED, (REASON_MANIFEST_SHA_MISSING,)),
            semantic=None,
        )

    if computed_sha != manifest_sha:
        return VerificationResult(
            identity=IdentityState(IDENTITY_FAILED, (REASON_COMPUTED_MANIFEST_MISMATCH,)),
            semantic=None,
        )

    identity = IdentityState(IDENTITY_VERIFIED, ())

    # Step 2: Semantic State 判定（仅当 identity=VERIFIED）
    if ir_sha is None:
        semantic = SemanticState(SEMANTIC_PENDING, REASON_IR_ABSENT)
    elif ir_sha != manifest_sha:
        semantic = SemanticState(SEMANTIC_PENDING, REASON_IR_MANIFEST_MISMATCH)
    else:
        semantic = SemanticState(SEMANTIC_AVAILABLE, None)

    return VerificationResult(identity=identity, semantic=semantic)
