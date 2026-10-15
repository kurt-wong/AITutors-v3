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


class TestImageOptionExpansion:
    """V3-IMG-OPTION-001 — image-only options must still expose A–D labels.

    GEO Q8 real shape: `A.` plain line, then `<div>B.</div>` wrappers, each
    label followed by `<div><img …/></div>` body. Labels live inside HTML
    layout; images are the option text. Structure must expand; no guessing.
    """

    def _geo_q8_lines(self) -> list[str]:
        lines = [""] * 30
        # shared material + Q7 (text options) + Q8 (image options) + Q9
        lines[5] = "北京时间2017年8月20日14时，热带风暴生成。据此完成下面小题。"
        lines[7] = "7. 生成时，东京正值（）"
        lines[9] = "A. 凌晨 B. 正午 C. 下午 D. 傍晚"
        lines[11] = "8. 图中表示天气系统的是（）"
        lines[13] = "A."
        lines[15] = "---"
        lines[17] = '<div style="text-align: center;"><img src="a.jpg" alt="Image" /></div>'
        lines[19] = '<div style="text-align: center;">B.</div>'
        lines[21] = '<div style="text-align: center;"><img src="b.jpg" alt="Image" /></div>'
        lines[23] = '<div style="text-align: center;">C.</div>'
        lines[25] = '<div style="text-align: center;"><img src="c.jpg" alt="Image" /></div>'
        lines[27] = '<div style="text-align: center;">D.</div>'
        lines[28] = '<div style="text-align: center;"><img src="d.jpg" alt="Image" /></div>'
        # answer table
        lines[29] = (
            "<table><tr><td>题号</td><td>7</td><td>8</td><td>9</td></tr>"
            "<tr><td>答案</td><td>C</td><td>C</td><td>A</td></tr></table>"
        )
        return lines

    def test_html_wrapped_labels_detected(self):
        lines = self._geo_q8_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[8],
            questions_range=(11, 28),
            answer_range=(30, 30),
            original_question_type="single_choice",
        )
        assert r.skipped == {}
        assert [s.question_number for s in r.sub_questions] == [8]
        assert r.sub_questions[0].option_labels == ("A", "B", "C", "D")

    def test_mixed_plain_and_html_labels_in_composite(self):
        """Q7 text options + Q8 image options in one composite — both expand."""
        lines = self._geo_q8_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[7, 8],
            questions_range=(7, 28),
            answer_range=(30, 30),
            original_question_type="single_choice",
        )
        assert r.skipped == {}
        assert [s.question_number for s in r.sub_questions] == [7, 8]
        assert r.sub_questions[1].option_labels == ("A", "B", "C", "D")

    def test_truncated_image_labels_still_rejected(self):
        """Missing D label (image body only) stays fail-closed."""
        lines = self._geo_q8_lines()
        # wipe the D label wrapper, leave only its image
        lines[27] = ""
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[8],
            questions_range=(11, 28),
            answer_range=(30, 30),
            original_question_type="single_choice",
        )
        assert 8 not in [s.question_number for s in r.sub_questions]
        assert 8 in r.skipped
        assert "option boundary unresolved" in r.skipped[8]

    def test_payload_carries_image_option_labels(self):
        lines = self._geo_q8_lines()
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[8],
            questions_range=(11, 28),
            answer_range=(30, 30),
            original_question_type="single_choice",
        )
        subs = specs_to_payload_subs(
            "U7-9", r.sub_questions, original_question_type="single_choice"
        )
        assert len(subs) == 1
        opts = subs[0]["content"]["options"]
        assert [o["label"] for o in opts] == ["A", "B", "C", "D"]


class TestCompositeTypeGate:
    """E2E-009R1: cloze + selection-type reading enter expansion; others stay out."""

    def _reading_lines(self) -> list[str]:
        # Q1-2 selection reading (A-D), answer table at end
        lines = [""] * 20
        lines[2] = "1. What will the speakers do?"
        lines[4] = "A. Go to a concert. B. Do some homework. C. Play some music. D. Stay home"
        lines[6] = "2. Where does the conversation take place?"
        lines[8] = "A. In a hotel B. At airport C. In a shop D. At school"
        lines[18] = (
            "<table><tr><td>题号</td><td>1</td><td>2</td></tr>"
            "<tr><td>答案</td><td>A</td><td>C</td></tr></table>"
        )
        return lines

    def _cloze_lines(self) -> list[str]:
        # number + A-D on one line (EN 2018 listening-style cloze options)
        lines = [""] * 12
        lines[2] = "26. A. happiest B. shortest C. weakest D. youngest"
        lines[4] = "27. A. reached B. held C. waved D. crossed"
        lines[10] = (
            "<table><tr><td>题号</td><td>26</td><td>27</td></tr>"
            "<tr><td>答案</td><td>A</td><td>B</td></tr></table>"
        )
        return lines

    def test_reading_with_declared_options_enters_scope(self):
        r = expand_composite_sub_questions(
            self._reading_lines(),
            question_numbers=[1, 2],
            questions_range=(3, 9),
            answer_range=(19, 19),
            original_question_type="reading",
            has_declared_options=True,
        )
        assert r.unit_reason is None
        assert [s.question_number for s in r.sub_questions] == [1, 2]

    def test_reading_without_options_stays_out_of_scope(self):
        r = expand_composite_sub_questions(
            self._reading_lines(),
            question_numbers=[1, 2],
            questions_range=(3, 9),
            answer_range=(19, 19),
            original_question_type="reading",
            has_declared_options=False,
        )
        assert r.unit_reason is not None
        assert "not in scope" in r.unit_reason
        assert r.sub_questions == []

    def test_open_text_types_enter_scope_without_ad(self):
        """Owner 2026-10: fill_in / reading_expression / essay 入库不因无选项受阻。"""
        lines = [""] * 12
        lines[2] = "21. Gladys"
        lines[4] = "22. 808-7754"
        lines[10] = "21. Gladys 22. 808-7754"
        for t in ("fill_in", "reading_expression", "essay"):
            r = expand_composite_sub_questions(
                lines,
                question_numbers=[21, 22],
                questions_range=(3, 5),
                answer_range=(11, 11),
                original_question_type=t,
                has_declared_options=False,
            )
            assert r.unit_reason is None, t
            assert [s.question_number for s in r.sub_questions] == [21, 22]
            for s in r.sub_questions:
                assert s.option_labels == ()  # no forced A-D

    def test_unknown_type_stays_out_of_scope(self):
        r = expand_composite_sub_questions(
            self._reading_lines(),
            question_numbers=[1],
            questions_range=(3, 5),
            answer_range=(19, 19),
            original_question_type="short_answer",
            has_declared_options=True,
        )
        assert r.unit_reason is not None
        assert "not in scope" in r.unit_reason

    def test_cloze_number_plus_options_line_expands(self):
        r = expand_composite_sub_questions(
            self._cloze_lines(),
            question_numbers=[26, 27],
            questions_range=(3, 5),
            answer_range=(11, 11),
            original_question_type="cloze",
        )
        assert r.unit_reason is None
        assert [s.question_number for s in r.sub_questions] == [26, 27]
        # each sub keeps A-D option integrity
        for s in r.sub_questions:
            assert s.option_labels == ("A", "B", "C", "D")

    def test_cloze_missing_option_label_fails_closed(self):
        lines = self._cloze_lines()
        lines[4] = "27. A. reached B. held C. waved"  # D missing
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[26, 27],
            questions_range=(3, 5),
            answer_range=(11, 11),
            original_question_type="cloze",
        )
        assert 26 in [s.question_number for s in r.sub_questions]
        assert 27 in r.skipped
        assert "option boundary unresolved" in r.skipped[27]

    def test_no_duplicate_or_cross_capture(self):
        r = expand_composite_sub_questions(
            self._reading_lines(),
            question_numbers=[1, 2, 1, 2],
            questions_range=(3, 9),
            answer_range=(19, 19),
            original_question_type="reading",
            has_declared_options=True,
        )
        nums = [s.question_number for s in r.sub_questions]
        assert nums == [1, 2]
