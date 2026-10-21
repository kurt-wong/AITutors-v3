"""P0-R16 A8/B3 先红回归用例.

A8: 跨 Source Version 同名局部 span_id 不能互相污染.
B3: 区间/紧凑答案键必须正确绑定, 结构化证据不丢失.

设计原则:
- 不 skip, 缺参数即视为失败 (pre-R16 代码必须报错).
- B3 检查 BindingFact 结构化证据, 不只检查 candidate_text.
"""
from __future__ import annotations

import uuid

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.binding_fact import (
    derive_binding_fact,
    get_registry,
    register_trusted_binding_fact,
    resolve_trusted_binding_fact,
)
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID1 = uuid.UUID("00000000-0000-0000-0000-00000000f201")
SVID2 = uuid.UUID("00000000-0000-0000-0000-00000000f202")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-00000000a201")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


@pytest.fixture(autouse=True)
def _clean_registry():
    get_registry().clear()
    yield
    get_registry().clear()


class TestA8CrossSourceVersionIsolation:
    def test_a8_sv_isolation_required(self):
        """A8: registry 必须按 (SV, span_id) 建键.

        当前代码: derive_binding_fact 无 source_version_id, registry 按 span_id 建键.
        修复后: source_version_id 必需, registry 复合键.
        本测试在 pre-R16 代码上必须失败.
        """
        # 尝试调用带 source_version_id 的 derive_binding_fact
        try:
            f1 = derive_binding_fact(
                span_id="sp-Q1.answer", unit_id="Q1",
                question_number="1", source_lines=["1. A"], answer_text="A",
                source_version_id=str(SVID1),
            )
        except TypeError as e:
            pytest.fail(
                f"derive_binding_fact 缺少 source_version_id 参数 (F8 未修): {e}"
            )

        f2 = derive_binding_fact(
            span_id="sp-Q1.answer", unit_id="Q1",
            question_number="2", source_lines=["2. B"], answer_text="B",
            source_version_id=str(SVID2),
        )

        register_trusted_binding_fact(f1)
        register_trusted_binding_fact(f2)

        got1 = resolve_trusted_binding_fact(
            span_id="sp-Q1.answer", source_version_id=str(SVID1)
        )
        got2 = resolve_trusted_binding_fact(
            span_id="sp-Q1.answer", source_version_id=str(SVID2)
        )
        assert got1 is not None, "SV1 fact must be retrievable"
        assert got2 is not None, "SV2 fact must be retrievable"
        assert got1.fact_id != got2.fact_id, "SV1/SV2 facts must be distinct"
        assert got1.answer_text == "A", f"SV1 answer_text: {got1.answer_text}"
        assert got2.answer_text == "B", f"SV2 answer_text: {got2.answer_text}"

    def test_a8_foreign_not_upgraded_by_match(self):
        """A8 核心: SV1 foreign 不被 SV2 match 覆盖."""
        try:
            f_foreign = derive_binding_fact(
                span_id="sp-Q1.answer", unit_id="Q1",
                question_number="5", source_lines=["12. A"], answer_text="A",
                source_version_id=str(SVID1),
            )
            f_match = derive_binding_fact(
                span_id="sp-Q1.answer", unit_id="Q1",
                question_number="1", source_lines=["1. B"], answer_text="B",
                source_version_id=str(SVID2),
            )
        except TypeError as e:
            pytest.fail(f"derive_binding_fact 缺少 source_version_id: {e}")

        assert f_foreign.ownership == "foreign", f"foreign ownership: {f_foreign.ownership}"
        assert f_match.ownership == "match", f"match ownership: {f_match.ownership}"

        register_trusted_binding_fact(f_foreign)
        register_trusted_binding_fact(f_match)

        got1 = resolve_trusted_binding_fact(
            span_id="sp-Q1.answer", source_version_id=str(SVID1)
        )
        assert got1 is not None
        assert got1.ownership == "foreign", (
            f"A8 FAIL: SV1 fact must stay foreign, got {got1.ownership}"
        )

    def test_a8_empty_sv_rejected(self):
        """verify_binding_fact 必须对空 SV 直接失败."""
        try:
            f = derive_binding_fact(
                span_id="sp-Q1.answer", unit_id="Q1",
                question_number="1", source_lines=["1. A"], answer_text="A",
                source_version_id="",
            )
        except (TypeError, ValueError) as e:
            # 空 SV 被拒绝 — 这是正确行为
            return
        pytest.fail(f"空 source_version_id 应被拒绝, 但创建成功: {f.to_payload()}")


class TestB3RangeCompactAnswers:
    def test_b3_range_answer_structured_evidence(self):
        """B3: `19-23 DABCA` 的 BindingFact 必须含结构化证据 (entry_nums 或 table_qn)."""
        lines = _mk(
            "19. What is A?", "A. a", "B. b", "C. c", "D. d",
            "答案", "19-23 DABCA",
        )
        payload = {
            "semantic_units": [
                {
                    "unit_id": f"Q{n}",
                    "unit_type": "standalone_unit",
                    "original_question_type": "single_choice",
                    "content": {
                        "stem": {"question_label": str(n)},
                        "options": [{"label": l} for l in "ABCD"],
                        "answer": {
                            "answer_zone": "answer_table",
                            "question_label": str(n),
                            "answer_lines": [7, 7],
                        },
                    },
                }
                for n in range(19, 24)
            ]
        }
        run = SourceResolver(source_version_id=SVID1, lines=lines).resolve(payload)

        # 检查每个子题的 binding fact
        found_facts = []
        for n in range(19, 24):
            fact = resolve_trusted_binding_fact(
                source_version_id=str(SVID1), span_id=f"sp-Q{n}.answer"
            )
            if fact is not None:
                found_facts.append((n, fact))

        # 至少有一个 fact 被注册
        assert found_facts, "B3 FAIL: 无 BindingFact 被注册"

        for n, fact in found_facts:
            # fact 必须有结构化证据 (entry_nums / table_qn / decode_loc)
            has_structured = bool(fact.entry_nums) or bool(fact.table_qn) or bool(fact.decode_loc)
            assert has_structured, (
                f"B3 FAIL: Q{n} fact 缺少结构化证据. "
                f"entry_nums={fact.entry_nums}, table_qn={fact.table_qn}, "
                f"decode_loc={fact.decode_loc}, evidence_kind={fact.evidence_kind}"
            )
            # ownership 必须是 match (正确绑定)
            assert fact.ownership == "match", (
                f"B3 FAIL: Q{n} ownership={fact.ownership}, 期望 match"
            )

    def test_b3_compact_fgdae_structured_evidence(self):
        """B3: `FGDAE` 的 BindingFact 必须含结构化证据."""
        lines = _mk(
            "1. What is X?", "A. a", "B. b", "C. c", "D. d",
            "E. e", "F. f", "G. g",
            "答案", "FGDAE",
        )
        payload = {
            "semantic_units": [
                {
                    "unit_id": f"Q{i}",
                    "unit_type": "standalone_unit",
                    "original_question_type": "seven_select_five",
                    "content": {
                        "stem": {"question_label": str(i)},
                        "options": [{"label": l} for l in "ABCDEFG"],
                        "answer": {
                            "answer_zone": "answer_table",
                            "question_label": str(i),
                            "answer_lines": [10, 10],
                        },
                    },
                }
                for i in range(1, 6)
            ]
        }
        run = SourceResolver(source_version_id=SVID1, lines=lines).resolve(payload)

        found_facts = []
        for i in range(1, 6):
            fact = resolve_trusted_binding_fact(
                source_version_id=str(SVID1), span_id=f"sp-Q{i}.answer"
            )
            if fact is not None:
                found_facts.append((i, fact))

        assert found_facts, "B3 FAIL: 紧凑答案键无 BindingFact 被注册"

        for i, fact in found_facts:
            has_structured = bool(fact.entry_nums) or bool(fact.table_qn) or bool(fact.decode_loc)
            assert has_structured, (
                f"B3 FAIL: Q{i} fact 缺少结构化证据. "
                f"entry_nums={fact.entry_nums}, table_qn={fact.table_qn}, "
                f"decode_loc={fact.decode_loc}, evidence_kind={fact.evidence_kind}"
            )

    def test_b3_range_answer_correct_slices(self):
        """B3: `19-23 DABCA` 每个子题答案文本正确."""
        lines = _mk(
            "19. What is A?", "A. a", "B. b", "C. c", "D. d",
            "答案", "19-23 DABCA",
        )
        payload = {
            "semantic_units": [
                {
                    "unit_id": f"Q{n}",
                    "unit_type": "standalone_unit",
                    "original_question_type": "single_choice",
                    "content": {
                        "stem": {"question_label": str(n)},
                        "options": [{"label": l} for l in "ABCD"],
                        "answer": {
                            "answer_zone": "answer_table",
                            "question_label": str(n),
                            "answer_lines": [7, 7],
                        },
                    },
                }
                for n in range(19, 24)
            ]
        }
        run = SourceResolver(source_version_id=SVID1, lines=lines).resolve(payload)
        ir = IRBuilder.build(run, payload, SVID1, ANN_ID)
        spans = {s.span_id: s for s in run.resolved_spans}
        compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)

        expected = {"19": "D", "20": "A", "21": "B", "22": "C", "23": "A"}
        checked = 0
        for leaf in compiled.leaves:
            qn = leaf.unit_id.replace("Q", "")
            if qn in expected and leaf.answer is not None:
                assert leaf.answer.candidate_text == expected[qn], (
                    f"B3 FAIL: Q{qn} 期望 {expected[qn]}, got {leaf.answer.candidate_text!r}"
                )
                checked += 1
        assert checked > 0, "B3 FAIL: 无子题 answer 被检查"
