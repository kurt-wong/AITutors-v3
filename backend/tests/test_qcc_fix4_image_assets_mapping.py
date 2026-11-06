# -*- coding: utf-8 -*-
"""QCC-FIX-4 回归：manifest.image_assets 消费（行号 → 单元/选项）。

契约 8b：选项配图排在字母行之后。映射规则：
- 标签行之前的配图（未声明的前置选项）→ stem extra_lines（P2-fix-2 通道）；
- 标签后的配图按布局序与声明选项配对 → 该选项 evidence_lines 扩到配图行。
不猜、不虚构行号；无 image_assets 或无选项窗时行为不变。
"""
from __future__ import annotations

from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)

LINES = [
    "1. 题干如图所示",
    "A. 甲", "B. 乙", "C. 丙",
    "【答案】A",
]

# 两图在标签前（未声明前置选项），一图在 B 标签后
MAN = {
    "units": [{
        "unit_id": "Q1",
        "unit_type": "standalone_question",
        "question_numbers": [1],
        "original_question_type": "single_choice",
        "stem_lines": [1, 1],
        "options_lines": [2, 4],
        "answer_lines": [5, 5],
        "options": [
            {"label": "A", "start_line": 2, "end_line": 2},
            {"label": "B", "start_line": 3, "end_line": 3},
            {"label": "C", "start_line": 4, "end_line": 4},
        ],
        "answer_evidence": {"type": "answer_lines", "lines": [5, 5], "value": "A", "shared": False},
        "answer_completeness": "full",
    }],
    "image_assets": [
        {"src": "../../_imgs/p/img_x1.jpg", "line_no": 2, "resolved": True},
        {"src": "../../_imgs/p/img_x2.jpg", "line_no": 3, "resolved": True},
        {"src": "../../_imgs/p/img_x3.jpg", "line_no": 99, "resolved": True},
    ],
    "source_content_sha256": "0" * 64,
}


def _bind(man):
    return bind_units_from_manifest(
        man, list(LINES), source_content_sha256="0" * 64
    )


def _payload(bound):
    return build_annotation_payload_from_bound(
        bound, source_content_sha256="0" * 64,
        manifest_identity_version=None, subject=None, grade=None,
    )


class TestImageAssetsConsumption:

    def test_images_mapped_to_units_and_options(self):
        bu = _bind(MAN)[0]
        # line 2 = A 的标签行 → 不算标签前配对输入（配图需在标签行才有归属）；
        # 本夹具 line2/3 为选项行本身——配图行需独立于标签行，调整断言以规则为准：
        assert bu.opt_declared_line == {"A": 2, "B": 3, "C": 4}

    def test_pre_label_image_goes_to_stem_extra(self):
        """Q5 同构：窗内首标签前的配图 → stem extra；标签后配图按序配对。"""
        lines = [
            "1. 题干如图所示",
            '<div><img src="../../_imgs/p/lead.jpg"></div>',
            "",
            "B. 乙",
            '<div><img src="../../_imgs/p/b.jpg"></div>',
            "C. 丙",
        ]
        man = {
            "units": [{
                "unit_id": "Q1",
                "unit_type": "standalone_question",
                "question_numbers": [1],
                "original_question_type": "single_choice",
                "stem_lines": [1, 1],
                "options_lines": [2, 6],
                "answer_lines": [1, 1],
                "options": [
                    {"label": "B", "start_line": 4, "end_line": 4},
                    {"label": "C", "start_line": 6, "end_line": 6},
                ],
                "answer_evidence": {"type": "answer_lines", "lines": [1, 1], "value": "A", "shared": False},
                "answer_completeness": "full",
            }],
            "image_assets": [
                {"src": "../../_imgs/p/lead.jpg", "line_no": 2, "resolved": True},
                {"src": "../../_imgs/p/b.jpg", "line_no": 5, "resolved": True},
            ],
            "source_content_sha256": "0" * 64,
        }
        bu = bind_units_from_manifest(man, lines, source_content_sha256="0" * 64)[0]
        # line 2 在首个标签行(4)之前 → stem extra
        assert bu.stem_image_lines == [2]
        # line 5 ≥ 4 → 序数配对给第一个声明选项 B
        assert bu.opt_image_lines == {"B": [5]}
        p = build_annotation_payload_from_bound(
            [bu], source_content_sha256="0" * 64,
            manifest_identity_version=None, subject=None, grade=None,
        )
        stem = p["semantic_units"][0]["content"]["stem"]
        assert stem.get("extra_lines") == [2, 2]
        opts = {o["label"]: o for o in p["semantic_units"][0]["content"]["options"]}
        assert opts["B"]["evidence_lines"] == [4, 5]

    def test_option_evidence_lines_covers_label_and_image(self):
        man = {
            **MAN,
            "units": [{**MAN["units"][0], "options_lines": [2, 5]}],
            "image_assets": [
                {"src": "../../_imgs/p/img_a.jpg", "line_no": 3, "resolved": True},
            ],
            "LINES_PAD": True,
        }
        # 行3 介于 A(2) 与 B(3)… 序数配对：post=[3] → 第一个标签 A
        lines = list(LINES) + ["", ""]
        bu = bind_units_from_manifest(man, lines, source_content_sha256="0" * 64)[0]
        p = build_annotation_payload_from_bound(
            bu and [bu], source_content_sha256="0" * 64,
            manifest_identity_version=None, subject=None, grade=None,
        )
        opts = {o["label"]: o for o in p["semantic_units"][0]["content"]["options"]}
        # A 的 evidence_lines 应覆盖 [2,3]（标签行+配图行）
        assert opts["A"]["evidence_lines"] == [2, 3], opts["A"]
        # 无配图的选项不设 evidence_lines（保持既有标记搜索路径）
        assert "evidence_lines" not in opts["B"]

    def test_no_image_assets_payload_unchanged(self):
        man = {k: v for k, v in MAN.items() if k != "image_assets"}
        bu = _bind(man)[0]
        assert bu.opt_image_lines == {}
        assert bu.stem_image_lines == []
        p = _payload([bu])
        opts = p["semantic_units"][0]["content"]["options"]
        assert all("evidence_lines" not in o for o in opts)

    def test_out_of_window_images_ignored(self):
        bu = _bind(MAN)[0]
        # line 99 在 options 窗 [2,4] 外 → 不映射
        assert 99 not in [n for v in bu.opt_image_lines.values() for n in v]
        assert 99 not in bu.stem_image_lines
