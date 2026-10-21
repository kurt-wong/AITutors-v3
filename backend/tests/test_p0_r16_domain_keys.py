"""P1-A: domain-separated signing keys derived from APP_SECRET.

Proves:
- issue/verify works under the real test APP_SECRET (conftest)
- missing/short APP_SECRET fails closed (no fixed-key fallback)
- binding-fact and publish-seal domain labels produce different keys
- tampering with digest-covered fields fails verification
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.core import secrets as secrets_mod
from app.domains.gate.binding_fact import (
    derive_binding_fact,
    verify_binding_fact,
)
from app.domains.gate.publish_seal import (
    issue_publish_seal,
    verify_publish_seal,
)


@pytest.fixture(autouse=True)
def _reset_keys():
    secrets_mod.clear_derived_keys()
    yield
    secrets_mod.clear_derived_keys()


class TestDomainSeparatedKeys:
    def test_issue_and_verify_roundtrip(self):
        fact = derive_binding_fact(
            span_id="sp-1",
            source_version_id="00000000-0000-0000-0000-000000000001",
            unit_id="Q1",
            question_number="1",
            source_lines=["1. B"],
            answer_text="B",
        )
        assert verify_binding_fact(fact)
        seal = issue_publish_seal(fact=fact, official_text="B", publish="official")
        assert seal
        assert verify_publish_seal(
            fact=fact, official_text="B", publish="official", seal=seal
        )

    def test_domain_labels_yield_different_keys(self):
        k_fact = secrets_mod.derive_domain_key("aitutors/binding-fact/v1")
        k_seal = secrets_mod.derive_domain_key("aitutors/publish-seal/v1")
        assert k_fact != k_seal
        assert len(k_fact) == 32 and len(k_seal) == 32

    def test_same_label_is_stable(self):
        a = secrets_mod.derive_domain_key("aitutors/binding-fact/v1")
        b = secrets_mod.derive_domain_key("aitutors/binding-fact/v1")
        assert a == b

    def test_missing_app_secret_fails_closed(self, monkeypatch):
        monkeypatch.setattr(secrets_mod.settings, "app_secret", "")
        secrets_mod.clear_derived_keys()
        with pytest.raises(ValueError, match="APP_SECRET"):
            secrets_mod.derive_domain_key("aitutors/binding-fact/v1")

    def test_short_app_secret_fails_closed(self, monkeypatch):
        monkeypatch.setattr(secrets_mod.settings, "app_secret", "too-short")
        secrets_mod.clear_derived_keys()
        with pytest.raises(ValueError, match="APP_SECRET"):
            secrets_mod.derive_domain_key("aitutors/publish-seal/v1")

    def test_no_fixed_key_fallback_on_missing_secret(self, monkeypatch):
        """After a failed derive, a later call must still fail — no cache of a
        hardcoded fallback."""
        monkeypatch.setattr(secrets_mod.settings, "app_secret", "")
        secrets_mod.clear_derived_keys()
        with pytest.raises(ValueError):
            secrets_mod.derive_domain_key("aitutors/binding-fact/v1")
        with pytest.raises(ValueError):
            secrets_mod.derive_domain_key("aitutors/binding-fact/v1")

    def test_tampered_fact_id_fails_verify(self):
        fact = derive_binding_fact(
            span_id="sp-1",
            source_version_id="00000000-0000-0000-0000-000000000001",
            unit_id="Q1",
            question_number="1",
            source_lines=["1. B"],
            answer_text="B",
        )
        tampered = replace(fact, fact_id="0" * 64)
        assert not verify_binding_fact(tampered)

    def test_tampered_ownership_fails_verify(self):
        fact = derive_binding_fact(
            span_id="sp-1",
            source_version_id="00000000-0000-0000-0000-000000000001",
            unit_id="Q1",
            question_number="1",
            source_lines=["1. B"],
            answer_text="B",
        )
        # Keep fact_id from the original so only ownership is wrong; the
        # HMAC will not match AND re-classification will disagree.
        tampered = replace(fact, ownership="unknown")
        assert not verify_binding_fact(tampered)

    def test_foreign_still_cannot_seal_nonempty(self):
        foreign = derive_binding_fact(
            span_id="sp-2",
            source_version_id="00000000-0000-0000-0000-000000000001",
            unit_id="Q9",
            question_number="5",
            source_lines=["12. A"],
            answer_text="A",
        )
        assert foreign.ownership == "foreign"
        assert issue_publish_seal(
            fact=foreign, official_text="A", publish="official"
        ) == ""

    def test_tampered_seal_fails_verify(self):
        fact = derive_binding_fact(
            span_id="sp-1",
            source_version_id="00000000-0000-0000-0000-000000000001",
            unit_id="Q1",
            question_number="1",
            source_lines=["1. B"],
            answer_text="B",
        )
        seal = issue_publish_seal(fact=fact, official_text="B", publish="official")
        assert seal
        assert not verify_publish_seal(
            fact=fact, official_text="B", publish="official", seal="0" * 64
        )
        assert not verify_publish_seal(
            fact=fact, official_text="A", publish="official", seal=seal
        )
