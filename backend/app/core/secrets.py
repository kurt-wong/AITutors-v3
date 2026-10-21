"""Domain-separated signing keys derived from APP_SECRET (P1-A).

Replaces hardcoded HMAC constants in BindingFact / publish seal.
Fail-closed: missing or short APP_SECRET raises — never falls back to a
fixed key. Test env supplies APP_SECRET via conftest before app import.
"""

from __future__ import annotations

import hashlib
import hmac

from app.core.config import settings

# Same floor as EB-008 review proof (92号 §5.2).
MIN_APP_SECRET_BYTES = 32

_derived: dict[str, bytes] = {}


def require_app_secret() -> str:
    """Return APP_SECRET or raise (fail-closed)."""
    secret = settings.app_secret or ""
    if len(secret.encode("utf-8")) < MIN_APP_SECRET_BYTES:
        raise ValueError(
            f"APP_SECRET missing or shorter than {MIN_APP_SECRET_BYTES} bytes; "
            "signing key unavailable (fail-closed)"
        )
    return secret


def derive_domain_key(label: str) -> bytes:
    """HMAC-SHA256(APP_SECRET, label) — distinct labels ⇒ distinct keys."""
    if not label:
        raise ValueError("domain label is required for key derivation")
    key = _derived.get(label)
    if key is None:
        secret = require_app_secret()
        key = hmac.new(
            secret.encode("utf-8"),
            label.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        _derived[label] = key
    return key


def clear_derived_keys() -> None:
    """Test hook: drop cached keys after monkeypatching settings.app_secret."""
    _derived.clear()
