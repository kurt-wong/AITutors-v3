"""Gate E — Source Resolver 纯函数测试（段 E）。

覆盖 40 §2 段 E 出口闸：级联确定性；missing/ambiguous/fuzzy/incomplete 永不自动
（resolved ⇔ {exact, normalized, contextual}）；7 role 正反例；contextual 不自动准入；
text_hash raw；输入不可变；不可猜测矩阵；fixture golden。
"""

import copy
import hashlib
import uuid

from app.core.hashing import sha256_hex
from app.domains.resolver import RESOLVED_STATUSES
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import (
    SourceFigureView,
    SourceLineView,
)

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000e")


def mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def resolver(lines, figures=()):
    return SourceResolver(source_version_id=SVID, lines=lines, figures=figures)


def _q1_payload():
    return {
        "semantic_units": [
            {
                "unit_id": "Q1", "unit_type": "standalone_question",
                "question_number": "1",
                "content": {
                    "stem": {"question_label": "1"},
                    "options": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}],
                    "answer": {"answer_zone": "inline_answer", "question_label": "1"},
                },
            }
        ]
    }


def _run_refs(run):
    return {s.span_id: list(s.line_refs) for s in run.resolved_spans}


# ------------------------------------------------------------------ 确定性
async def test_determinism_same_input_same_output():
    lines = mk("1. 下列哪个是水果?", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子")
    payload = _q1_payload()
    r1 = resolver(lines).resolve(payload)
    r2 = resolver(lines).resolve(payload)
    assert [s.span_id for s in r1.resolved_spans] == [s.span_id for s in r2.resolved_spans]
    assert [s.line_refs for s in r1.resolved_spans] == [s.line_refs for s in r2.resolved_spans]
    assert [s.evidence for s in r1.resolved_spans] == [s.evidence for s in r2.resolved_spans]
    assert [s.text_hash for s in r1.resolved_spans] == [s.text_hash for s in r2.resolved_spans]


async def test_does_not_mutate_inputs():
    lines = mk("1. 题干", "A. 苹果", "B. 香蕉")
    payload = copy.deepcopy(_q1_payload())
    lines_before = copy.deepcopy(lines)
    resolver(lines).resolve(payload)
    assert lines == lines_before
    assert payload == copy.deepcopy(_q1_payload())


# ------------------------------------------------------------------ exact
async def test_standalone_exact_resolves_stem_and_options():
    lines = mk("1. 下列哪个是水果?", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子")
    run = resolver(lines).resolve(_q1_payload())
    refs = _run_refs(run)
    assert refs["sp-Q1.stem"] == ["P1L001"]
    assert refs["sp-Q1.option.A"] == ["P1L002"]
    assert refs["sp-Q1.option.B"] == ["P1L003"]
    assert refs["sp-Q1.option.C"] == ["P1L004"]
    assert refs["sp-Q1.option.D"] == ["P1L005"]
    assert all(s.resolution_status in RESOLVED_STATUSES for s in run.resolved_spans)
    assert not any(u.reference_id.startswith("Q1.stem") for u in run.unresolved_references)


async def test_stem_span_includes_body_until_first_option():
    lines = mk("1. 下面哪个是水果？", "水果是能吃的东西。", "A. 苹果", "B. 香蕉")
    payload = {
        "semantic_units": [
            {"unit_id": "Q1", "content": {"stem": {"question_label": "1"},
              "options": [{"label": "A"}, {"label": "B"}]}}
        ]
    }
    run = resolver(lines).resolve(payload)
    assert _run_refs(run)["sp-Q1.stem"] == ["P1L001", "P1L002"]


async def test_normalized_resolves_material_single_line():
    # 源行用全角字母Ｂ；marker 用半角 B → raw 不命中，full-width 折叠后唯一命中。
    lines = mk("答案是Ｂ，选它", "1. 题干", "A. 甲")
    payload = {
        "semantic_units": [
            {"unit_id": "U1", "unit_type": "composite_unit",
             "shared_components": {
                 "material": {
                     "start_marker": {"kind": "instruction_marker",
                                      "granularity": "single_line",
                                      "text": "答案是B"},
                     "end_marker": None,
                 }},
             "sub_questions": []}
        ]
    }
    run = resolver(lines).resolve(payload)
    span = next(s for s in run.resolved_spans if s.role == "material")
    assert span.line_refs == ("P1L001",)
    assert span.resolution_status == "normalized"


# ------------------------------------------------------------------ negative matrix
async def test_negative_missing():
    lines = mk("1. 题干", "A. 甲", "B. 乙")
    payload = {
        "semantic_units": [{"unit_id": "Q9", "content": {"stem": {"question_label": "9"},
                           "options": []}}]
    }
    run = resolver(lines).resolve(payload)
    u = next(u for u in run.unresolved_references if u.reference_id == "Q9.stem")
    assert u.resolution_status == "missing"
    assert all(s.span_id != "sp-Q9.stem" for s in run.resolved_spans)


async def test_negative_ambiguous_two_question_starts():
    lines = mk("1. 第一道", "1. 第二道重复", "A. 甲", "B. 乙")
    payload = {
        "semantic_units": [{"unit_id": "Q1", "content": {"stem": {"question_label": "1"},
                           "options": []}}]
    }
    run = resolver(lines).resolve(payload)
    u = next(u for u in run.unresolved_references if u.reference_id == "Q1.stem")
    assert u.resolution_status == "ambiguous"
    assert not any(s.span_id == "sp-Q1.stem" for s in run.resolved_spans)


async def test_negative_swap_order_no_hidden_first_match():
    # 两个「1.」行，交换顺序均不得自动选（无 list[0] fallback）。
    a = mk("1. 第一", "1. 第二", "A. 甲")
    b = mk("1. 第二", "1. 第一", "A. 甲")
    payload = {"semantic_units": [{"unit_id": "Q1", "content": {"stem": {"question_label": "1"},
               "options": []}}]}
    for lines in (a, b):
        run = resolver(lines).resolve(payload)
        assert not any(s.span_id == "sp-Q1.stem" for s in run.resolved_spans)
        assert any(u.reference_id == "Q1.stem" and u.resolution_status == "ambiguous"
                   for u in run.unresolved_references)


async def test_negative_fuzzy_not_auto_accepted():
    # 源行「阅读下 面短文」（OCR 拆空格）→ 仅 flatten 命中 → fuzzy，不 resolved。
    lines = mk("阅读下 面短文", "根据材料回答", "1. 题干", "A. 甲")
    payload = {
        "semantic_units": [
            {"unit_id": "U1", "shared_components": {
                "material": {"start_marker": {"kind": "instruction_marker",
                                              "granularity": "single_line",
                                              "text": "阅读下面短文"}}},
             "sub_questions": []}
        ]
    }
    run = resolver(lines).resolve(payload)
    assert not any(s.role == "material" for s in run.resolved_spans)
    assert any(u.reference_id.endswith("material") and u.resolution_status == "fuzzy"
               for u in run.unresolved_references)


async def test_negative_incomplete_stem_no_boundary():
    # 题号行后无选项、无下一题、无表头 → 无显式边界 → incomplete（不默认文档尾）。
    lines = mk("1. 只有一个孤零零的题干")
    payload = {"semantic_units": [{"unit_id": "Q1", "content": {"stem": {"question_label": "1"},
               "options": []}}]}
    run = resolver(lines).resolve(payload)
    u = next(u for u in run.unresolved_references if u.reference_id == "Q1.stem")
    assert u.resolution_status == "incomplete"
    assert not any(s.span_id == "sp-Q1.stem" for s in run.resolved_spans)


async def test_negative_option_duplicate_label_ambiguous():
    lines = mk("1. 题干", "A. 苹果", "A. 香蕉", "B. 西瓜")
    payload = {"semantic_units": [{"unit_id": "Q1", "content": {"stem": {"question_label": "1"},
               "options": [{"label": "A"}, {"label": "B"}]}}]}
    run = resolver(lines).resolve(payload)
    u = next(u for u in run.unresolved_references if u.reference_id == "Q1.option.A")
    assert u.resolution_status == "ambiguous"
    assert not any(s.span_id == "sp-Q1.option.A" for s in run.resolved_spans)


async def test_negative_material_pair_missing_end_incomplete():
    lines = mk("阅读下面短文", "文章甲", "1. 题干", "A. 甲")
    payload = {
        "semantic_units": [
            {"unit_id": "U1", "shared_components": {
                "material": {"start_marker": {"kind": "instruction_marker",
                                              "granularity": "multi_line_pair",
                                              "text": "阅读下面短文"}}},
             "sub_questions": []}
        ]
    }
    run = resolver(lines).resolve(payload)
    assert not any(s.role == "material" for s in run.resolved_spans)
    assert any(u.reference_id.endswith("material") and u.resolution_status == "incomplete"
               for u in run.unresolved_references)


# ------------------------------------------------------------------ contextual
async def test_contextual_does_not_auto_admit():
    # 两候选但需上下文收窄（此处不做自动窄化）→ 不 resolved；M1 安全：永不自动准入。
    lines = mk("根据材料回答第1题", "第一段材料", "根据材料回答第1题", "第二段材料",
               "1. 题干", "A. 甲")
    payload = {
        "semantic_units": [{"unit_id": "U1", "shared_components": {
            "material": {"start_marker": {"kind": "instruction_marker",
                                          "granularity": "single_line",
                                          "text": "根据材料回答第1题"}}},
            "sub_questions": []}]
    }
    run = resolver(lines).resolve(payload)
    assert not any(s.role == "material" for s in run.resolved_spans)
    assert any(u.reference_id.endswith("material") and u.resolution_status == "ambiguous"
               for u in run.unresolved_references)


# ------------------------------------------------------------------ answer/explanation
def _full_doc():
    return mk(
        "1. 下列哪项正确?", "A. 苹果", "B. 香蕉",
        "2. 下列哪项?", "A. 猫", "B. 狗",
        "【答案】", "1. A", "2. B",
        "【详解】", "1. 因为苹果", "2. 因为猫",
    )


def _two_question_payload():
    return {
        "semantic_units": [
            {"unit_id": "Q1", "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": "A"}, {"label": "B"}],
                "answer": {"answer_zone": "inline_answer", "question_label": "1"},
                "explanation": {"explanation_zone": "inline_explanation",
                                "question_label": "1"}}},
            {"unit_id": "Q2", "content": {
                "stem": {"question_label": "2"},
                "options": [{"label": "A"}, {"label": "B"}],
                "answer": {"answer_zone": "inline_answer", "question_label": "2"},
                "explanation": {"explanation_zone": "inline_explanation",
                                "question_label": "2"}}},
        ]
    }


async def test_answer_row_located_in_answer_zone():
    run = resolver(_full_doc()).resolve(_two_question_payload())
    refs = _run_refs(run)
    assert refs["sp-Q1.answer"] == ["P1L008"]   # 【答案】后的 "1. A"
    assert refs["sp-Q2.answer"] == ["P1L009"]


async def test_explanation_row_located_under_header():
    run = resolver(_full_doc()).resolve(_two_question_payload())
    refs = _run_refs(run)
    assert refs["sp-Q1.explanation"] == ["P1L011"]
    assert refs["sp-Q2.explanation"] == ["P1L012"]


# ------------------------------------------------------------------ image / blank
def _figs(*figs):
    return tuple(SourceFigureView(*f) for f in figs)


async def test_image_unique_resolves():
    lines = mk("图1文字", "1. 看图片回答问题", "A. 甲", "B. 乙")
    figs = _figs(("fig1", 1, {"x0": 0, "y0": 0, "x1": 10, "y1": 10}, "inline",
                  "seal", "obj/fig1", "h" * 64))
    payload = {"semantic_units": [{"unit_id": "Q1", "content": {
        "stem": {"question_label": "1"}, "options": [{"label": "A"}],
        "image": {"image_ref": {"figure_id": "fig1"}}}}]}
    run = resolver(lines, figs).resolve(payload)
    assert any(s.role == "image" and s.resolution_status == "exact"
               for s in run.resolved_spans)


async def test_image_multi_figure_ambiguous():
    lines = mk("1. 题干", "A. 甲")
    figs = _figs(("fig1", 1, {"x0": 0, "y0": 0, "x1": 1, "y1": 1}, "inline", "s", "o1", "h"),
                 ("fig2", 1, {"x0": 0, "y0": 0, "x1": 1, "y1": 1}, "inline", "s", "o2", "h"))
    payload = {"semantic_units": [{"unit_id": "Q1", "content": {
        "stem": {"question_label": "1"}, "options": [],
        "image": {"image_ref": {}}}}]}
    run = resolver(lines, figs).resolve(payload)
    assert not any(s.role == "image" for s in run.resolved_spans)
    assert any(u.role == "image" and u.resolution_status == "ambiguous"
               for u in run.unresolved_references)


async def test_image_no_is7_complete_ambiguous():
    lines = mk("1. 题干", "A. 甲")
    payload = {"semantic_units": [{"unit_id": "Q1", "content": {
        "stem": {"question_label": "1"}, "options": [],
        "image": {"image_ref": {"figure_id": "fig1"}}}}]}
    run = resolver(lines).resolve(payload)  # 无 figures
    assert not any(s.role == "image" for s in run.resolved_spans)
    assert any(u.role == "image" and u.resolution_status == "ambiguous"
               for u in run.unresolved_references)


async def test_blank_requires_closure_incomplete():
    lines = mk("1. 填空 ____", "A. 甲")
    payload = {"semantic_units": [{"unit_id": "Q1", "content": {
        "stem": {"question_label": "1"}, "options": [],
        "blank": {"blank_label": "第1空", "question_label": "1"}}}]}
    run = resolver(lines).resolve(payload)
    # blank 无 sub_question/answer 闭合 → incomplete（段 F 之前不造闭合）。
    assert not any(s.role == "blank" for s in run.resolved_spans)
    assert any(u.role == "blank" and u.resolution_status == "incomplete"
               for u in run.unresolved_references)


# ------------------------------------------------------------------ text_hash raw
async def test_text_hash_is_raw_not_canonical():
    lines = mk("1. 题干", "A. 苹果")
    run = resolver(lines).resolve(_q1_payload())
    stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.stem")
    raw = hashlib.sha256(lines[0].text.encode("utf-8")).hexdigest()
    canonical = sha256_hex({"text": lines[0].text})
    assert stem.text_hash == raw
    assert stem.text_hash != canonical


async def test_fragment_offset_line_character():
    # material line_fragment 在行内精确命中 → line_character + 正确 offset。
    lines = mk("本题材料见下页【图】请仔细看", "1. 题干", "A. 甲")
    payload = {"semantic_units": [{"unit_id": "U1", "shared_components": {
        "material": {"start_marker": {"kind": "instruction_marker",
                                      "granularity": "line_fragment",
                                      "text": "【图】"}}},
        "sub_questions": []}]}
    run = resolver(lines).resolve(payload)
    frag = next(s for s in run.resolved_spans if s.granularity == "line_character")
    assert frag.line_refs == ("P1L001",)
    line = lines[0].text
    assert line[frag.start_offset:frag.end_offset] == "【图】"


# ------------------------------------------------------------------ prefix collision (FAIL-1)
async def test_prefix_collision_answer_explanation_not_cross():
    """qn=1 不得误吞 10/11/12 的答案/详解（题号 token equality，禁 prefix substring）。"""
    lines = mk(
        "1. 第一题题干", "A. 甲",
        "10. 第十题题干", "A. 乙",
        "11. 第十一题题干", "A. 丙",
        "12. 第十二题题干", "A. 丁",
        "【答案】", "1. A", "10. B", "11. C", "12. D",
        "【详解】", "1. 因为甲", "10. 因为乙", "11. 因为丙", "12. 因为丁",
    )
    # 只问 Q1：answer/explanation 必须各自唯一指向自身行，不得吞 10/11/12。
    payload = {"semantic_units": [{"unit_id": "Q1", "content": {
        "stem": {"question_label": "1"}, "options": [{"label": "A"}],
        "answer": {"answer_zone": "answer_table", "question_label": "1"},
        "explanation": {"explanation_zone": "inline_explanation", "question_label": "1"}}}]}
    run = resolver(lines).resolve(payload)
    a = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.answer")
    e = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.explanation")
    # 答案表 "1. A" 在 P1L010（【答案】在 P1L009）
    assert a.start_line_ref == "P1L010" and a.start_offset == 0
    # 详解 "1. 因为甲" 在 P1L015；不得含 10/11/12 的详解行
    assert e.line_refs == ("P1L015",)
    # 反向：Q10/Q11/Q12 的 explanation 不得被 Q1 吞（无多余 unresolved 或错配）
    assert not any(u.reference_id == "Q1.explanation" for u in run.unresolved_references)


# ------------------------------------------------------------------ contextual (FAIL-2)
async def test_contextual_resolves_by_zone_exclusion():
    """material marker 双命中，其中一处在题目区一处在详解区 → 确定性区界排除 → contextual。"""
    lines = mk(
        "阅读下面材料", "1. 题干", "A. 甲", "B. 乙",
        "【详解】", "阅读下面材料请参考本题详解",
    )
    payload = {"semantic_units": [{"unit_id": "U1", "unit_type": "composite_unit",
        "shared_components": {"material": {"start_marker": {
            "kind": "instruction_marker", "granularity": "single_line",
            "text": "阅读下面材料"}}},
        "sub_questions": []}]}
    run = resolver(lines).resolve(payload)
    mats = [s for s in run.resolved_spans if s.role == "material"]
    assert len(mats) == 1
    m = mats[0]
    assert m.resolution_status == "contextual"
    assert m.line_refs == ("P1L001",)
    assert any("excluded" in e for e in m.evidence)  # 候选集快照（收窄步骤入 evidence）


async def test_contextual_initial_gt1_final_eq1_invariant():
    """contextual 成立的前提：候选数 >1（两处命中），收窄后 final==1。"""
    lines = mk(
        "阅读下面材料", "1. 题干", "A. 甲",
        "【详解】", "阅读下面材料见解析",
    )
    # 两处 raw 命中
    from app.domains.resolver.resolver import _LineIndex
    idx = _LineIndex(lines)
    assert len(idx.raw_hits("阅读下面材料")) == 2
    payload = {"semantic_units": [{"unit_id": "U1", "unit_type": "composite_unit",
        "shared_components": {"material": {"start_marker": {
            "kind": "instruction_marker", "granularity": "single_line",
            "text": "阅读下面材料"}}},
        "sub_questions": []}]}
    m = next(s for s in resolver(lines).resolve(payload).resolved_spans if s.role == "material")
    assert m.resolution_status == "contextual"
    assert m.line_refs == ("P1L001",)


async def test_exact_unique_is_not_contextual():
    """exact 唯一命中必须标 exact，不得混标 contextual（防 provenance 污染）。"""
    lines = mk("阅读下面材料", "1. 题干", "A. 甲")
    payload = {"semantic_units": [{"unit_id": "U1", "unit_type": "composite_unit",
        "shared_components": {"material": {"start_marker": {
            "kind": "instruction_marker", "granularity": "single_line",
            "text": "阅读下面材料"}}},
        "sub_questions": []}]}
    m = next(s for s in resolver(lines).resolve(payload).resolved_spans if s.role == "material")
    assert m.resolution_status == "exact"


# ------------------------------------------------------------------ material overlap (FAIL-3)
async def test_material_overlap_with_stem_rejected():
    """material span 若含子题 stem/option 行 → material 不得 resolved（E source-span invariant）。"""
    lines = mk("材料开始", "材料内容", "1. 这是子题题干", "A. 子题选项", "材料结束")
    payload = {"semantic_units": [{"unit_id": "U1-1", "unit_type": "composite_unit",
        "shared_components": {"material": {
            "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                             "text": "材料开始"},
            "end_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                           "text": "材料结束"}}},
        "sub_questions": [{"unit_id": "Q1", "content": {
            "stem": {"question_label": "1"}, "options": [{"label": "A"}]}}]}]}
    run = resolver(lines).resolve(payload)
    assert not any(s.role == "material" for s in run.resolved_spans)
    assert any(u.reference_id == "U1-1.material" and u.resolution_status == "incomplete"
               and any("overlaps" in e for e in u.evidence)
               for u in run.unresolved_references)


# ------------------------------------------------------------------ inline 同行 (FAIL-4)
async def test_option_shared_line_line_character():
    """单行多选项 'A. 苹果 B. 香蕉' → B 以 line_character 定位（有界 label，非 first-match）。"""
    lines = mk("1. 哪个是水果", "A. 苹果  B. 香蕉")
    payload = {"semantic_units": [{"unit_id": "Q1", "content": {
        "stem": {"question_label": "1"}, "options": [{"label": "A"}, {"label": "B"}]}}]}
    run = resolver(lines).resolve(payload)
    b = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.option.B")
    assert b.granularity == "line_character"
    assert b.line_refs == ("P1L002",)
    assert lines[1].text[b.start_offset:b.end_offset] == "B"
    assert not any(u.reference_id == "Q1.option.B" for u in run.unresolved_references)


async def test_answer_shared_line_multi_qn():
    """同行多题答案 '1. A  2. B' → qn1/qn2 各自 line_character（不互相吞）。"""
    lines = mk("1. 第一题", "A. 甲", "2. 第二题", "A. 乙", "【答案】", "1. A  2. B")
    payload = {"semantic_units": [
        {"unit_id": "Q1", "content": {"stem": {"question_label": "1"},
          "options": [], "answer": {"answer_zone": "answer_table", "question_label": "1"}}},
        {"unit_id": "Q2", "content": {"stem": {"question_label": "2"},
          "options": [], "answer": {"answer_zone": "answer_table", "question_label": "2"}}}]}
    run = resolver(lines).resolve(payload)
    a1 = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.answer")
    a2 = next(s for s in run.resolved_spans if s.span_id == "sp-Q2.answer")
    assert a1.line_refs == ("P1L006",) and a1.granularity == "line_character"
    assert a2.line_refs == ("P1L006",) and a2.granularity == "line_character"
    # qn1 切片不得含 qn2 内容；qn2 切片含 "2. B"
    assert "2" not in lines[5].text[a1.start_offset:a1.end_offset]
    assert lines[5].text[a2.start_offset:a2.end_offset].startswith("2")


# ------------------------------------------------------------------ fixture golden
async def test_fixture_golden_composite_full_resolution():
    """段内 fixture golden：固定输入 → 固定预期解析率（正反例齐备）。"""
    lines = mk(
        "阅读下面短文回答问题", "文章内容甲", "文章内容乙", "根据材料回答第1～2题",
        "1. 下列哪项正确?", "A. 苹果", "B. 香蕉",
        "2. 下列哪项?", "A. 猫", "B. 狗",
        "【答案】", "1. A", "2. B",
        "【详解】", "1. 因为苹果", "2. 因为猫",
    )
    payload = {
        "semantic_units": [
            {"unit_id": "U1-2", "unit_type": "composite_unit", "question_number_range": "1-2",
             "shared_components": {
                 "material": {
                     "start_marker": {"kind": "instruction_marker",
                                      "granularity": "multi_line_pair",
                                      "text": "阅读下面短文回答问题"},
                     "end_marker": {"kind": "instruction_marker",
                                    "granularity": "multi_line_pair",
                                    "text": "根据材料回答第1～2题"}}},
             "sub_questions": [
                 {"unit_id": "Q1", "question_label": "1", "content": {
                     "stem": {"question_label": "1"},
                     "options": [{"label": "A"}, {"label": "B"}],
                     "answer": {"answer_zone": "answer_table", "question_label": "1"},
                     "explanation": {"explanation_zone": "inline_explanation",
                                     "question_label": "1"}},
                  "depends_on": [{"type": "material_dependency", "target": "material"}]},
                 {"unit_id": "Q2", "question_label": "2", "content": {
                     "stem": {"question_label": "2"},
                     "options": [{"label": "A"}, {"label": "B"}],
                     "answer": {"answer_zone": "answer_table", "question_label": "2"},
                     "explanation": {"explanation_zone": "inline_explanation",
                                     "question_label": "2"}},
                  "depends_on": [{"type": "material_dependency", "target": "material"}]},
             ],
            }
        ]
    }
    run = resolver(lines).resolve(payload)
    refs = _run_refs(run)
    # 预期 resolved span 全集（material 内文排他 marker）
    assert refs["sp-U1-2.material"] == ["P1L002", "P1L003"]
    assert refs["sp-Q1.stem"] == ["P1L005"]
    assert refs["sp-Q1.option.A"] == ["P1L006"]
    assert refs["sp-Q1.option.B"] == ["P1L007"]
    assert refs["sp-Q1.answer"] == ["P1L012"]
    assert refs["sp-Q1.explanation"] == ["P1L015"]
    assert refs["sp-Q2.stem"] == ["P1L008"]
    assert refs["sp-Q2.answer"] == ["P1L013"]
    # material_dependency 全部 resolved
    assert len(run.resolved_relations) == 3
    assert all(r.status == "resolved" for r in run.resolved_relations)
    assert not run.unresolved_relations
    # 解析率对照：全部 reference 均 resolved（无 unresolved 泄漏）
    assert not run.unresolved_references


async def test_fixture_golden_repeats_consistent():
    lines = mk("1. 题干", "A. 苹果", "B. 香蕉")
    p = _q1_payload()
    g1 = resolver(lines).resolve(p)
    g2 = resolver(lines).resolve(p)
    assert g1 == g2  # ResolvedRun frozen 等值（确定性 golden）


# ------------------------------------------------------------------ BUG-V3-038 contract lock
async def test_frozen_contract_question_label_only_answer_explanation():
    """BUG-V3-038 regression lock：严格 Frozen Schema（20 §4.5）payload——content role 的
    answer/explanation 只带 question_label，全文不存在 question_number——Resolver 必须
    完整解析 stem/answer/explanation。若 Resolver 再漂回读 question_number，本测试即失败
    （answer/explanation 会因 qn=None 判 incomplete）。"""
    lines = mk(
        "1. 下列哪个是水果?", "A. 苹果", "B. 香蕉",
        "【答案】", "1. A",
        "【详解】", "1. 因为苹果是水果",
    )
    payload = {"semantic_units": [
        {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_number": "1",  # unit 顶层合法字段（20 §4.5:164）
         "content": {
             "stem": {"role": "stem", "question_label": "1"},
             "options": [{"label": "A", "role": "option", "question_label": "1"},
                         {"label": "B", "role": "option", "question_label": "1"}],
             "answer": {"role": "answer", "question_label": "1",
                        "answer_zone": "answer_table"},
             "explanation": {"role": "explanation", "question_label": "1",
                             "explanation_zone": "inline_explanation"},
         }},
    ]}
    run = resolver(lines).resolve(payload)
    refs = _run_refs(run)
    assert refs["sp-Q1.stem"] == ["P1L001"]
    assert refs["sp-Q1.answer"] == ["P1L005"]
    assert refs["sp-Q1.explanation"] == ["P1L007"]
    assert not any(u.reference_id.startswith("Q1.") for u in run.unresolved_references)
