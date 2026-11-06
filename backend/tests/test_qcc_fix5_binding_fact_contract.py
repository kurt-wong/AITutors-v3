# -*- coding: utf-8 -*-
"""QCC-FIX-5 回归：归属事实判定契约（Owner 2026-01 裁决）。

契约（依据 binding_fact._classify 自身文档 + Owner 裁决）：
- 声明绑定（answer_lines/answer_value 的**存在性**）只用于定位，**不构成归属证据**；
- 归属正结论只来自：题号条目/结构证据，或「声明值 + 源文内容一致性」的可验证绑定
  （dv 分支——derive 与 verify 以同一 declared_value 契约复算）；
- 事实不足 → unknown，不得凭声明升级 match；
- 真实冲突保留 foreign（不因本修复降级）；
- derive 与 verify 必须一致，但一致不等于正确（Q18 修复前曾一致地误判 foreign）。
"""
from __future__ import annotations

import pytest

from app.domains.gate.binding_fact import (
    derive_binding_fact,
    register_trusted_binding_fact,
    verify_binding_fact,
)

SV = "00000000-0000-0000-0000-0000000000f5"


def _derive(qn, lines, answer_text, declared_value="", decode_loc=""):
    """声明绑定只体现在 declared_value / 源行契约上——归属升级入口
    （declared_binding 参数）已从 derive 删除（QCC-FIX-5），参数消失即契约强制。"""
    return derive_binding_fact(
        span_id="sp-t", source_version_id=SV, unit_id=f"Q{qn}",
        question_number=qn, source_lines=list(lines), answer_text=answer_text,
        evidence_kind="", decode_loc=decode_loc,
        declared_value=declared_value,
    )


class TestDeclaredBindingIsNotOwnershipEvidence:
    """声明绑定参与定位，但没有独立归属证据 → unknown（A3.1）。"""

    def test_placeholder_declared_binding_yields_unknown(self):
        """值占位（源行=声明值本身）：不能凭声明升级 match（修复前 derive=match）。"""
        val = "醛基；(酚)羟基"
        fact = _derive("17", [val], val, declared_value=val, decode_loc="qn:17")
        assert fact.ownership == "unknown", (
            f"declared_binding alone must not upgrade to match, got {fact.ownership!r}"
        )

    def test_placeholder_fact_verifies_and_registers(self):
        """derive/verify 同契约 → 注册成功、不再 registration_failed（A3.2/A3.3）。"""
        val = "醛基；(酚)羟基"
        fact = _derive("17", [val], val, declared_value=val, decode_loc="qn:17")
        assert verify_binding_fact(fact) is True, "derive/verify must agree on the fact"
        reg = register_trusted_binding_fact(fact)
        assert reg.ownership == "unknown"

    def test_declared_presence_without_value_no_upgrade(self):
        """仅 declared_binding=True（无声明值、无条目证据）→ unknown。"""
        fact = _derive("17", ["某段无条目正文"], "某段无条目正文",
                       declared_value="", decode_loc="qn:17")
        assert fact.ownership == "unknown"


class TestVerifiedBindingUnchanged:
    """「声明值+源文内容一致性」可验证绑定仍是正结论来源（dv 分支，双侧同契约）。"""

    def test_content_verified_value_still_matches(self):
        """Q1 形态：【答案】B 行 + 声明值 B → match（derive==verify）。"""
        fact = _derive("1", ["【答案】B"], "B", declared_value="B", decode_loc="qn:1")
        assert fact.ownership == "match"
        assert verify_binding_fact(fact) is True
        register_trusted_binding_fact(fact)

    def test_conflicting_value_does_not_match(self):
        """声明值与源文矛盾 → 不升级为 match。"""
        fact = _derive("1", ["【答案】B"], "B", declared_value="Z", decode_loc="qn:1")
        assert fact.ownership != "match"


class TestRealForeignPreserved:
    """真实归属冲突仍判 foreign（A3.4）；Q18 数值碎片不误判（A3.5 / FIX-3）。"""

    def test_foreign_entry_still_foreign(self):
        """条目指向他题号（>10，非歧义带）→ foreign，且 derive==verify 一致。"""
        fact = _derive("18", ["15. A"], "A", decode_loc="qn:18")
        assert fact.ownership == "foreign"
        assert verify_binding_fact(fact) is True
        reg = register_trusted_binding_fact(fact)
        assert reg.ownership == "foreign"

    def test_decimal_fragments_not_foreign(self):
        """Q18 同构：值/正文含 63.39% / 0.1000 / 35.5 等数值 → 不得判 foreign。"""
        val = "有效氯63.39%，该样品为优质品；偏低"
        fact = _derive("18", [val], val, declared_value=val, decode_loc="qn:18")
        assert fact.ownership != "foreign", (
            "decimal fragments must not fabricate foreign attribution"
        )

    def test_subquestion_block_not_foreign(self):
        """(1)(2)(3) 小问编号 + 小数的解答块（Q18 块同构）→ 不判 foreign。"""
        blk = ["【答案】(1). A (2). B", "n=0.1000 mol × 0.02000 L", "（4）. 偏低"]
        fact = _derive("18", blk, "A B", decode_loc="qn:18")
        assert fact.ownership != "foreign"


class TestRegisterRejectsBadFacts:
    """注册仍拒绝被篡改的事实（安全边界不放宽）。"""

    def test_tampered_ownership_rejected(self):
        import dataclasses
        fact = _derive("1", ["【答案】B"], "B", declared_value="B", decode_loc="qn:1")
        forged = dataclasses.replace(fact, ownership="match" if fact.ownership != "match" else "unknown")
        with pytest.raises(ValueError):
            register_trusted_binding_fact(forged)

    def test_tampered_fact_id_rejected(self):
        import dataclasses
        fact = _derive("1", ["【答案】B"], "B", declared_value="B", decode_loc="qn:1")
        forged = dataclasses.replace(fact, fact_id="0" * 64)
        assert verify_binding_fact(forged) is False
