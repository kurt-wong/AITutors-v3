"""Interface Scope identity rules — sole production authority.

Migrated from scripts/preprocessing_consumer/boundary.py (B1-R2-BOUNDARY-AND-DB-ISOLATION-03)
so the formal import path no longer depends on experimental scripts/.

Semantics frozen by Contract v0.2 §1.2 / §1.6 / §1.7 and boundary normalization:
- source_content_sha256 = SHA-256(source raw bytes), 64 lowercase hex
- identity_version ∈ {2, "2"} (same fact; all other values rejected)
- path is locator only, never identity
- No silent repair, no default, no coercion of malformed shapes

This module is the ONLY rule definition. Callers must not copy the sets/codes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Cross-system identity key format (Frozen Contract §1.2).
_SHA256_LOWER_HEX = re.compile(r"^[0-9a-f]{64}$")

# Interface Scope identity_version field criterion (Frozen Contract §1.6).
# corpus has both int 2 and str "2"; both express the same fact.
_INTERFACE_IDENTITY_VERSIONS = frozenset({2, "2"})

# JSON scalar shapes allowed past the type gate (F-RBC-01).
# bool is allowed through to membership (True == 1 != 2 → still rejected).
# float keeps historical 2.0 semantics (F-RBC-05) — membership still applies.
_IDENTITY_VERSION_ACCEPTED_TYPES: tuple[type, ...] = (bool, int, float, str)

# Stable boundary error codes (do not rename; tests and runners key on these).
CODE_MISSING_IDENTITY = "MISSING_IDENTITY"
CODE_MALFORMED_IDENTITY = "MALFORMED_IDENTITY"
CODE_MISSING_IDENTITY_VERSION = "MISSING_IDENTITY_VERSION"
CODE_MALFORMED_IDENTITY_VERSION = "MALFORMED_IDENTITY_VERSION"
CODE_OUT_OF_SCOPE_IDENTITY_VERSION = "OUT_OF_SCOPE_IDENTITY_VERSION"

__all__ = [
    "CODE_MISSING_IDENTITY",
    "CODE_MALFORMED_IDENTITY",
    "CODE_MISSING_IDENTITY_VERSION",
    "CODE_MALFORMED_IDENTITY_VERSION",
    "CODE_OUT_OF_SCOPE_IDENTITY_VERSION",
    "BoundaryViolation",
    "NormalizedIdentity",
    "InterfaceScopeDecision",
    "normalize_interface_identity",
    "enforce_interface_scope",
]


class BoundaryViolation(Exception):
    """Producer input cannot be deterministically normalized at the boundary."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class NormalizedIdentity:
    """Normalized cross-system identity fact (read-only; does not rewrite Producer value)."""

    source_content_sha256: str
    identity_version: str
    already_canonical: bool


@dataclass(frozen=True)
class InterfaceScopeDecision:
    """Uniform decision shape for every runtime entry point."""

    accepted: bool
    code: str | None
    reason: str
    identity: NormalizedIdentity | None


def normalize_interface_identity(
    source_content_sha256: object,
    identity_version: object,
) -> NormalizedIdentity:
    """Validate and normalize cross-system identity (Contract §1.2 / §1.6 / §1.7).

    Fail-closed. No default. No coercion. No silent repair.
    """
    if source_content_sha256 is None:
        raise BoundaryViolation(
            CODE_MISSING_IDENTITY,
            "Manifest does not declare source_content_sha256; cross-system identity "
            "cannot be established (path must never be used as identity).",
        )
    if not isinstance(source_content_sha256, str) or not _SHA256_LOWER_HEX.match(
        source_content_sha256
    ):
        raise BoundaryViolation(
            CODE_MALFORMED_IDENTITY,
            f"source_content_sha256 must be 64 lowercase hex chars "
            f"(SHA-256 of raw source bytes), got {source_content_sha256!r}.",
        )

    if identity_version is None:
        raise BoundaryViolation(
            CODE_MISSING_IDENTITY_VERSION,
            "Manifest does not declare identity_version; Interface Scope membership "
            "cannot be established (Frozen Contract §1.6).",
        )
    # Type gate before membership (F-RBC-01): unhashable shapes must not TypeError.
    if not isinstance(identity_version, _IDENTITY_VERSION_ACCEPTED_TYPES):
        raise BoundaryViolation(
            CODE_MALFORMED_IDENTITY_VERSION,
            f"identity_version must be a JSON scalar (bool/int/float/str), got "
            f"{type(identity_version).__name__} value {identity_version!r}; no "
            f"coercion is permitted (list/dict/set are rejected as malformed — "
            f"never stringified, never defaulted to 2).",
        )
    if identity_version not in _INTERFACE_IDENTITY_VERSIONS:
        raise BoundaryViolation(
            CODE_OUT_OF_SCOPE_IDENTITY_VERSION,
            f"identity_version {identity_version!r} is outside the Interface Scope "
            f"field criterion (identity_version == 2). v1 legacy assets are not part "
            f"of the interface (Frozen Contract §1.7) and are not silently consumed.",
        )

    return NormalizedIdentity(
        source_content_sha256=source_content_sha256,
        identity_version="2",
        already_canonical=isinstance(identity_version, str) and identity_version == "2",
    )


def enforce_interface_scope(
    source_content_sha256: object,
    identity_version: object,
) -> InterfaceScopeDecision:
    """Sole runtime entry for Interface Boundary enforcement (F-INT-01 / F-INT-08).

    100% delegates to normalize_interface_identity. Never raises; folds
    BoundaryViolation into a decision shape for uniform runner/entry handling.
    """
    try:
        identity = normalize_interface_identity(source_content_sha256, identity_version)
    except BoundaryViolation as exc:
        return InterfaceScopeDecision(
            accepted=False,
            code=exc.code,
            reason=f"interface_scope_rejected: {exc.code}: {exc.message}",
            identity=None,
        )
    return InterfaceScopeDecision(
        accepted=True,
        code=None,
        reason="interface_scope_accepted: identity_version==2",
        identity=identity,
    )
