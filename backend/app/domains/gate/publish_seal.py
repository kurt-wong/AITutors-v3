"""P0 publish seal: capability over a VERIFIED independent binding fact.

The seal is issued only by the authorized publish path after
`_publish_decision` accepts a BindingFact obtained from the trusted
registry (never from transport payload ownership). `create_role_content`
re-verifies the fact and the seal before any non-empty official answer
text is persisted.

The seal binds:
  fact.fact_id + fact.answer_text_hash + fact.ownership
  + official_text + span_id + publish

HMAC therefore proves the issuer signed THIS fact for THIS text — not
merely that some ownership string was signed. Forging ownership in the
transport cannot produce a seal that matches a foreign fact.

foreign ownership can never obtain a non-empty official seal.
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Mapping

from app.core.secrets import derive_domain_key

# Domain-separated key (P1-A). Distinct from binding-fact label.
_SEAL_KEY_LABEL = "aitutors/publish-seal/v1"


def _seal_key() -> bytes:
    return derive_domain_key(_SEAL_KEY_LABEL)


def _norm_own(ownership: str) -> str:
    own = (ownership or "unknown").strip().lower()
    if own == "foreign_question":
        return "foreign"
    if own in ("match", "foreign", "unknown"):
        return own
    return "unknown"


def _digest(
    *,
    fact_id: str,
    answer_text_hash: str,
    ownership: str,
    official_text: str,
    span_id: str,
    publish: str,
) -> str:
    msg = "|".join(
        [
            fact_id or "",
            answer_text_hash or "",
            ownership or "unknown",
            official_text or "",
            span_id or "",
            publish or "withheld_review",
        ]
    )
    return hmac.new(_seal_key(), msg.encode("utf-8"), hashlib.sha256).hexdigest()


def _fact_fields(fact) -> tuple[str, str, str, str]:
    """Extract (fact_id, answer_text_hash, ownership, span_id) from a fact."""
    if fact is None:
        return "", "", "unknown", ""
    if isinstance(fact, Mapping):
        return (
            str(fact.get("fact_id") or ""),
            str(fact.get("answer_text_hash") or ""),
            _norm_own(str(fact.get("ownership") or "unknown")),
            str(fact.get("span_id") or ""),
        )
    return (
        getattr(fact, "fact_id", "") or "",
        getattr(fact, "answer_text_hash", "") or "",
        _norm_own(getattr(fact, "ownership", "unknown") or "unknown"),
        getattr(fact, "span_id", "") or "",
    )


def issue_publish_seal(
    *,
    fact,
    official_text: str,
    publish: str,
) -> str:
    """Issue a seal ONLY for publishable official text of a trusted fact.

    `fact` must be a verified BindingFact (registry-backed). Returns ""
    when the combination is not publishable (foreign non-empty text,
    non-official non-empty text, or missing fact identity fields).
    """
    fact_id, ans_h, own, span_id = _fact_fields(fact)
    text = official_text or ""
    pub = (publish or "withheld_review").strip()

    if not fact_id or not ans_h:
        return ""
    if own == "foreign" and text:
        return ""
    if text and pub != "official":
        return ""
    return _digest(
        fact_id=fact_id,
        answer_text_hash=ans_h,
        ownership=own,
        official_text=text,
        span_id=span_id,
        publish=pub,
    )


def verify_publish_seal(
    *,
    fact,
    official_text: str,
    publish: str,
    seal: str,
) -> bool:
    """Verify seal against the verified binding fact.

    Forgery of publish=/ownership= in a transport payload is not enough:
    the seal only matches when fact_id + answer_text_hash + ownership +
    official_text + span_id + publish were all signed together.
    """
    if not seal:
        return False
    expected = issue_publish_seal(
        fact=fact,
        official_text=official_text,
        publish=publish,
    )
    return bool(expected) and hmac.compare_digest(expected, seal)
