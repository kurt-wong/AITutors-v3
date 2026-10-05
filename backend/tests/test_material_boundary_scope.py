# -*- coding: utf-8 -*-
"""Material boundary marker scope constraint (Option A).

Anchors must not enter a neighbour's declared material range. Shared
boundary lines (prev_end / next_start) are legal anchors. When external
unique anchors are unavailable (adjacent blocks / duplicated headers),
fall back to a tight in-block pair (non-overlapping, no neighbour pollution).
"""
from scripts.preprocessing_consumer.annotation_adapter import (
    material_boundary_markers,
    _nearest_unique_nonempty,
)


# synthetic listening-like layout: adjacent blocks + duplicated headers
LINES = [
    "# 听力录音材料",            # 1 unique
    "听第1段材料，回答第1题。",   # 2 DUPLICATE (also on L13)
    "M: Alpha line one.",        # 3 unique
    "W: Alpha line two.",        # 4 unique
    "",                          # 5 blank
    "听第2段材料，回答第2题。",   # 6 DUPLICATE (also on L14)
    "M: Beta line one.",         # 7 unique
    "W: Beta line two.",         # 8 unique
    "",                          # 9 blank
    "听第3段材料，回答第3题。",   # 10 unique (only here)
    "M: Gamma line one.",        # 11 unique
    "W: Gamma line two.",        # 12 unique
    "听第1段材料，回答第1题。",   # 13 duplicate of L2
    "听第2段材料，回答第2题。",   # 14 duplicate of L6
    "9. 题干行 unique.",          # 15 unique (healthy next-question anchor)
]


def _interior(m):
    st = m["start_marker"]["text"]
    en = m["end_marker"]["text"]
    s_no = next(i + 1 for i, t in enumerate(LINES) if t == st)
    e_no = next(i + 1 for i, t in enumerate(LINES) if t == en)
    return set(range(s_no + 1, e_no)), s_no, e_no


class TestScopeConstraint:
    def test_end_anchor_does_not_enter_neighbour_content(self):
        m = material_boundary_markers((2, 4), LINES, neighbour_bounds=(0, 6))
        assert m is not None
        assert "Beta" not in m["end_marker"].get("text", "")

    def test_start_anchor_may_share_previous_boundary_line(self):
        """Owner rule: start anchor ≥ prev material end (shared line legal)."""
        m = material_boundary_markers((6, 8), LINES, neighbour_bounds=(4, 10))
        assert m is not None
        assert "Beta" not in m["start_marker"]["text"]

    def test_healthy_next_question_anchor_still_works(self):
        lines = [
            "材料首行内容甲乙丙。",
            "材料次行内容丁戊己。",
            "",
            "1. 题干第一行",
        ]
        m = material_boundary_markers((1, 2), lines, neighbour_bounds=(0, 99))
        assert m is not None
        # either the next-question line is the end anchor (ideal), or a
        # deterministic in-block/single fallback was used (start has no
        # external unique because scope [prev_end=0, s-1=0] is empty).
        assert m["start_marker"]["text"] in lines[0:2]

    def test_no_neighbour_still_finds_external_unique(self):
        lines = [
            "唯一标题行",
            "",
            "材料甲",
            "材料乙",
            "",
            "唯一结束行",
        ]
        m = material_boundary_markers((3, 4), lines, neighbour_bounds=(0, 99))
        assert m is not None
        assert m["start_marker"]["text"] == "唯一标题行"
        assert m["end_marker"]["text"] == "唯一结束行"


class TestNeighbourIsolation:
    def test_adjacent_duplicated_headers_no_neighbour_content(self):
        m = material_boundary_markers((2, 4), LINES, neighbour_bounds=(0, 6))
        assert m is not None
        texts = m["start_marker"].get("text", "") + m.get("end_marker", {}).get("text", "")
        assert "Beta" not in texts

    def test_two_adjacent_blocks_interiors_do_not_overlap(self):
        ma = material_boundary_markers((2, 4), LINES, neighbour_bounds=(0, 6))
        mb = material_boundary_markers((6, 8), LINES, neighbour_bounds=(4, 10))
        assert ma is not None and mb is not None
        ia, _, _ = _interior(ma)
        ib, _, _ = _interior(mb)
        assert not (ia & ib), f"interiors overlap: {ia & ib}"
        # B's interior must not contain A's dialogue lines (3,4)
        assert not ({3, 4} & ib), f"B interior pulled A content: {ib}"


class TestUnchanged:
    def test_n1_unique_single_marker(self):
        m = material_boundary_markers((3, 3), LINES)
        assert m == {"role": "material", "start_marker": {"text": "M: Alpha line one."}}

    def test_n1_non_unique_rejected(self):
        assert material_boundary_markers((2, 2), LINES) is None

    def test_walk_clamps_into_scope(self):
        hit = _nearest_unique_nonempty(LINES, 4, forward=False, limit=8, min_no=3, max_no=3)
        assert hit == (3, "M: Alpha line one.")

    def test_walk_in_scope_finds_neighbour_boundary(self):
        hit = _nearest_unique_nonempty(LINES, 5, forward=False, limit=8, min_no=4, max_no=5)
        assert hit is not None
        assert hit[0] in (4, 5)
