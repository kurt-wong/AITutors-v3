# -*- coding: utf-8 -*-
"""Task A — option label fullwidth-comma format compatibility (U44-46)."""
import uuid

from app.domains.resolver.resolver import SourceResolver, _label_offsets
from app.domains.resolver.match_normalization import _line_has_option_token, normalize_text
from app.domains.resolver.span import SourceLineView


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


class TestFullwidthCommaOptionLabel:
    def test_label_offsets_finds_D_after_fullwidth_comma(self):
        line = "C. 水土流失 D，物种减少"
        offs = _label_offsets(line, "D")
        assert len(offs) == 1
        assert line[offs[0]:offs[0] + 1] == "D"

    def test_line_has_option_token_fullwidth_comma(self):
        assert _line_has_option_token("D，物种减少", "D")
        assert _line_has_option_token(normalize_text("D，物种减少"), "D")

    def test_u44_pattern_q44_options_resolved(self):
        """U44-46 Q44: A/B on L3, C/D on L4 (D uses fullwidth comma)."""
        lines = _mk(
            "44. 该实验探究的环境问题是",           # L1
            "A. 全球变暖 B. 酸雨危害",             # L2
            "C. 水土流失 D，物种减少",             # L3
            "45. 甲装置实验条件不变",               # L4
            "A. 减小水量",                          # L5
        )
        payload = {
            "semantic_units": [{
                "unit_id": "U44-46",
                "unit_type": "composite_unit",
                "question_number": "44",
                "question_number_range": "44-46",
                "original_question_type": "single_choice",
                "shared_components": {"material": {"role": "material",
                                                   "start_marker": {"text": "44. 该实验探究的环境问题是"}}},
                "sub_questions": [{
                    "unit_id": "U44-46.sub",
                    "unit_type": "standalone_unit",
                    "question_number": "44",
                    "original_question_type": "single_choice",
                    "content": {
                        "stem": {"role": "stem", "question_label": "44"},
                        "options": [
                            {"role": "option", "label": "A"},
                            {"role": "option", "label": "B"},
                            {"role": "option", "label": "C"},
                            {"role": "option", "label": "D"},
                        ],
                        "answer": {"role": "answer", "question_label": "44",
                                   "answer_zone": "answer_table",
                                   "answer_lines": [1, 1]},
                    },
                }],
            }]
        }
        run = SourceResolver(source_version_id=uuid.uuid4(), lines=lines).resolve(payload)
        opts = {s.span_id.rsplit(".", 1)[-1]: s for s in run.resolved_spans if s.role == "option"}
        assert "D" in opts, f"D must resolve, got {list(opts)} unres={[u.reference_id for u in run.unresolved_references]}"
        # D must sit on the Q44 line (L3), not the Q45 line
        assert opts["D"].line_refs[0] == "P1L003"
        # Task A content span: after `D，` → content, not the label letter
        d_txt = lines[2].text[opts["D"].start_offset:opts["D"].end_offset]
        assert d_txt.strip() == "物种减少", d_txt
        assert "A" in opts and "B" in opts
        a_txt = lines[1].text[opts["A"].start_offset:opts["A"].end_offset]
        assert a_txt.strip() == "全球变暖", a_txt
        for lab in "ABC":
            assert lab in opts, f"{lab} must stay resolved"

    def test_existing_separators_still_work(self):
        for sep in (".", "．", "、", ":", ")", "）", "，"):
            assert _line_has_option_token(f"A{sep}xxx", "A"), sep
            assert _label_offsets(f"Z A{sep}xxx", "A"), sep
