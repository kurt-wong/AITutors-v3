# -*- coding: utf-8 -*-
"""GEO-SUBQ: deterministic composite sub-question expansion.

Owner ruling: proven structure only (题号→题干→A-D→答案表);
Q43 must stay rejected; no fake single-question over a multi-q range.
"""
from __future__ import annotations

from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)
from app.domains.source.subq_expand import (
    expand_composite_sub_questions,
    specs_to_payload_subs,
)


def _geo_lines() -> list[str]:
    """Minimal OCR-like fixture: Q1-2 composite + Q3-5 composite + broken Q43."""
    lines = [""] * 40
    # material + Q1-2 (U1-2)
    lines[8] = "材料：探测土星。据此完成1-2题。"
    lines[10] = "1\\. 与卡西尼号探测的天体系统级别相同的是"
    lines[12] = "A. 地月系 B. 太阳系 C. 银河系 D. 总星系"
    lines[14] = "2. 为推断是否存在生命，需要寻找的证据是"
    lines[16] = "A. 体积适当 B. 质量适中 C. 有大气层 D. 有液态水"
    # material + Q3-5 (U3-5)
    lines[18] = "太阳爆发了强烈耀斑。据此完成3-5题。"
    lines[20] = "3. 本次耀斑爆发时，伦敦正值"
    lines[22] = "A. 上午 B. 中午 C. 下午 D. 晚上"
    lines[24] = "4. 本次耀斑爆发对地球的影响有"
    lines[25] = "①为地球提供光热资源②干扰无线电短波通讯"
    lines[26] = "A.①②B.①④C.②③D.③④"
    lines[28] = "5. 太阳活动的主要标志还有"
    lines[30] = "A. 太阳黑子 B. 太阳风 C. 日冕 D. 日珥"
    # Q42-43 broken (Q43 options truncated — real OCR defect)
    lines[32] = "42. 对图中景物的合理解释是"
    lines[33] = "A. 大雁塔位于西安 B. 帆船靠风力 C. 椰子为海南特产 D. 骆驼适应干旱"
    lines[34] = "43\\. 推进一带一路建设有利于"
    lines[35] = "①我国产业结构升级②沿线国家经济合作"
    lines[36] = "A.①②③B.①②④C"  # OCR truncated — D missing
    # answer table
    lines[38] = (
        "<table><tr><td>题号</td><td>1</td><td>2</td><td>3</td>"
        "<td>4</td><td>5</td></tr><tr><td>答案</td>"
        "<td>A</td><td>D</td><td>B</td><td>D</td><td>A</td></tr></table>"
    )
    return lines


class TestGeoSubqExpand:
    def test_normal_expand_q1_q2(self):
        lines = _geo_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[1, 2],
            questions_range=(9, 17),
            answer_range=(39, 39),
            original_question_type="single_choice",
        )
        assert r.skipped == {}
        assert [s.question_number for s in r.sub_questions] == [1, 2]
        q1 = r.sub_questions[0]
        assert q1.stem_start == 11
        assert q1.option_labels == ("A", "B", "C", "D")
        assert q1.answer_lines == (39, 39)

    def test_normal_expand_q3_q5(self):
        lines = _geo_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[3, 4, 5],
            questions_range=(19, 31),
            answer_range=(39, 39),
            original_question_type="single_choice",
        )
        assert r.skipped == {}
        assert [s.question_number for s in r.sub_questions] == [3, 4, 5]
        # Q4 compact options still expose A-D labels in order
        assert r.sub_questions[1].option_labels == ("A", "B", "C", "D")

    def test_q43_truncated_options_rejected(self):
        """Q43 (A.①②③B.①②④C) — option boundary unresolved, must NOT expand."""
        lines = _geo_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[42, 43],
            questions_range=(33, 37),
            answer_range=(39, 39),
            original_question_type="single_choice",
        )
        assert 43 not in [s.question_number for s in r.sub_questions]
        assert 43 in r.skipped
        assert "option boundary unresolved" in r.skipped[43]
        # Q42 (clean) may still expand — Q43 must not fake-merge into it
        assert [s.question_number for s in r.sub_questions] == [42]

    def test_no_fake_single_question(self):
        """Multi-q range must never collapse into one big sub."""
        lines = _geo_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[1, 2],
            questions_range=(9, 17),
            answer_range=(39, 39),
            original_question_type="single_choice",
        )
        # exactly one sub per question number — never one sub covering both
        assert len(r.sub_questions) == 2
        for spec in r.sub_questions:
            # each sub ends before the next question starts
            assert spec.stem_end < 15 or spec.question_number == 2

    def test_missing_question_start_skipped(self):
        lines = _geo_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[1, 2, 9],
            questions_range=(9, 17),
            answer_range=(39, 39),
            original_question_type="single_choice",
        )
        assert 9 in r.skipped
        assert [s.question_number for s in r.sub_questions] == [1, 2]

    def test_short_answer_out_of_scope(self):
        lines = _geo_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[51],
            questions_range=(9, 17),
            answer_range=(39, 39),
            original_question_type="short_answer",
        )
        assert r.sub_questions == []
        assert r.unit_reason is not None

    def test_specs_to_payload_shape(self):
        lines = _geo_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[1, 2],
            questions_range=(9, 17),
            answer_range=(39, 39),
            original_question_type="single_choice",
        )
        subs = specs_to_payload_subs("U1-2", r.sub_questions,
                                    original_question_type="single_choice")
        assert len(subs) == 2
        s0 = subs[0]
        assert s0["unit_type"] == "standalone_unit"
        assert s0["question_number"] == "1"
        c = s0["content"]
        assert c["stem"]["question_label"] == "1"
        assert [o["label"] for o in c["options"]] == ["A", "B", "C", "D"]
        assert c["answer"]["answer_lines"] == [39, 39]
        assert s0["depends_on"][0]["target"] == "material"


class TestBindingIntegration:
    def _manifest(self, units):
        return {
            "units": units,
            "identity_version": 2,
            "source_content_sha256": "b" * 64,
        }

    def test_multi_q_composite_emits_real_subs(self):
        lines = _geo_lines()
        unit = {
            "unit_id": "U1-2",
            "unit_type": "composite_question",
            "question_numbers": [1, 2],
            "original_question_type": "single_choice",
            "material_lines": [9, 9],
            "questions_lines": [9, 17],
            "answer_lines": [39, 39],
        }
        bound = bind_units_from_manifest(
            self._manifest([unit]), lines, source_content_sha256="b" * 64
        )
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="b" * 64, manifest_identity_version=2
        )
        su = payload["semantic_units"][0]
        assert su["unit_type"] == "composite_unit"
        assert len(su["sub_questions"]) == 2
        assert [s["question_number"] for s in su["sub_questions"]] == ["1", "2"]
        # NOT the old fake: one sub carrying the whole multi-q stem
        assert all(s["unit_type"] == "standalone_unit" for s in su["sub_questions"])

    def test_broken_q43_unit_yields_partial_then_safe(self):
        lines = _geo_lines()
        unit = {
            "unit_id": "U42-43",
            "unit_type": "composite_question",
            "question_numbers": [42, 43],
            "original_question_type": "single_choice",
            "material_lines": [32, 32],
            "questions_lines": [33, 37],
            "answer_lines": [39, 39],
        }
        bound = bind_units_from_manifest(
            self._manifest([unit]), lines, source_content_sha256="b" * 64
        )
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="b" * 64, manifest_identity_version=2
        )
        su = payload["semantic_units"][0]
        subs = su["sub_questions"]
        assert [s["question_number"] for s in subs] == ["42"]
        # Q43 must not appear as accepted structure
        assert all(s["question_number"] != "43" for s in subs)

    def test_unexpandable_multi_q_keeps_empty_subs(self):
        """No question starts found → sub_questions=[] (safe reject), not fake."""
        lines = ["x"] * 10
        unit = {
            "unit_id": "U1-2",
            "unit_type": "composite_question",
            "question_numbers": [1, 2],
            "original_question_type": "single_choice",
            "material_lines": [1, 1],
            "questions_lines": [1, 5],
            "answer_lines": [8, 8],
        }
        bound = bind_units_from_manifest(
            self._manifest([unit]), lines, source_content_sha256="b" * 64
        )
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="b" * 64, manifest_identity_version=2
        )
        su = payload["semantic_units"][0]
        assert su["sub_questions"] == []
        assert su["group_evidence"]["structure"] == "undetermined_sub_questions"
