"""Gate F — Compiler：三 key + text_hash raw + canonical 直通 + 确定性 + 负向矩阵（20 §7）。"""

import copy
import hashlib
import uuid

import pytest

from app.core.hashing import sha256_hex
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000e")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000ae")


def mk(*texts):
    return tuple(SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
                 for i, t in enumerate(texts))


def _standalone_lines(answer_letter="A"):
    return mk("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
              "【答案】", f"1. {answer_letter}")


def _standalone_payload():
    return {"semantic_units": [{"unit_id": "Q1", "unit_type": "standalone_unit",
        "original_question_type": "single_choice",
        "content": {"stem": {"question_label": "1"},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {"answer_zone": "answer_table", "question_label": "1"}}}]}


def _compile(lines, payload):
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    lines_by_ref = {l.line_ref: l for l in lines}
    return Compiler(spans, lines_by_ref).compile(ir)


async def test_canonical_passthrough_and_text_hash_raw():
    snap = _compile(_standalone_lines(), _standalone_payload())
    assert len(snap.leaves) == 1
    leaf = snap.leaves[0]
    assert leaf.canonical_question_type == "single_choice"
    assert leaf.answer.verified_correct is None  # verified_correct 留 G
    assert leaf.answer.source_located and leaf.answer.complete
    # 2c/2d raw：等于 hashlib(compiled.text)，不等于 canonical identity hash
    assert leaf.stem.text_hash == hashlib.sha256(leaf.stem.text.encode()).hexdigest()
    assert leaf.stem.text_hash != sha256_hex({"text": leaf.stem.text})


async def test_answer_independence_fp1():
    snap_a = _compile(_standalone_lines("A"), _standalone_payload())
    snap_b = _compile(_standalone_lines("B"), _standalone_payload())
    assert snap_a.leaves[0].answer.text != snap_b.leaves[0].answer.text
    assert snap_a.leaves[0].dedup_key == snap_b.leaves[0].dedup_key  # Question ≠ Answer


async def test_occurrence_and_dedup_differ_fp3():
    lines = mk("1. 第一题", "A. 甲", "B. 乙", "2. 第二题", "A. 丙", "B. 丁",
               "【答案】", "1. A", "2. A")
    payload = {"semantic_units": [
        {"unit_id": "Q1", "unit_type": "standalone_unit",
         "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "1"}, "options": [{"label": "A"}, {"label": "B"}],
                     "answer": {"answer_zone": "answer_table", "question_label": "1"}}},
        {"unit_id": "Q2", "unit_type": "standalone_unit",
         "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "2"}, "options": [{"label": "A"}, {"label": "B"}],
                     "answer": {"answer_zone": "answer_table", "question_label": "2"}}},
    ]}
    snap = _compile(lines, payload)
    q1, q2 = snap.leaves[0], snap.leaves[1]
    assert q1.occurrence_key != q2.occurrence_key  # occurrence 是 document-local
    assert q1.dedup_key != q1.occurrence_key  # occurrence ≠ Question identity（不含 question_id）


async def test_occurrence_sensitive_to_stem_location_not_answer():
    # occurrence 是位置身份：题干文本变但行位不变 → occurrence 不变；行位变 → 变。
    a = _compile(_standalone_lines("A"), _standalone_payload()).leaves[0]
    b = _compile(_standalone_lines("B"), _standalone_payload()).leaves[0]
    assert a.occurrence_key == b.occurrence_key  # 仅 answer 变（位置同）→ occurrence 不变
    # 前置一行 → stem 落 P1L002 → occurrence 变
    shifted = mk("标题行", "1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
                 "【答案】", "1. A")
    s = _compile(shifted, _standalone_payload()).leaves[0]
    assert a.occurrence_key != s.occurrence_key  # stem 位置变 → occurrence 变


async def test_unknown_canonical_not_compiled_fp5():
    payload = copy.deepcopy(_standalone_payload())
    payload["semantic_units"][0]["original_question_type"] = "foo"
    snap = _compile(_standalone_lines(), payload)
    assert snap.leaves == ()


async def test_shared_material_compiled_once_fp2():
    def comp(material_line):
        lines = mk("材料开始", material_line, "材料结束",
                   "1. 第一问", "A. 甲", "B. 乙",
                   "【答案】", "1. A")
        payload = {"semantic_units": [
            {
                "unit_id": "U1-1", "unit_type": "composite_unit",
                "original_question_type": "single_choice",
                "shared_components": {
                    "material": {
                        "start_marker": {"kind": "instruction_marker",
                                         "granularity": "multi_line_pair", "text": "材料开始"},
                        "end_marker": {"kind": "instruction_marker",
                                       "granularity": "multi_line_pair", "text": "材料结束"},
                    }
                },
                "sub_questions": [
                    {"unit_id": "Q1", "unit_type": "standalone_unit", "question_label": "1",
                     "content": {
                        "stem": {"question_label": "1"},
                        "options": [{"label": "A"}, {"label": "B"}],
                        "answer": {"answer_zone": "answer_table", "question_label": "1"}}}
                ],
            }
        ]}
        return _compile(lines, payload)

    snap1 = comp("材料甲内容段落")
    snap2 = comp("材料乙内容完全不同")
    assert snap1.materials and snap2.materials
    assert snap1.materials[0].dedup_key != snap2.materials[0].dedup_key  # Material 变 → 独立 key 变
    assert snap1.leaves[0].dedup_key == snap2.leaves[0].dedup_key  # material 变不拆 Question
    assert "材料" not in snap1.leaves[0].stem.text  # material 只输出一次，不复制进子题


async def test_compile_deterministic_and_immutable():
    lines = _standalone_lines()
    payload = _standalone_payload()
    lines_before = copy.deepcopy(lines)
    payload_before = copy.deepcopy(payload)
    s1 = _compile(lines, payload)
    s2 = _compile(lines, payload)
    assert s1 == s2
    assert s1.leaves[0].dedup_key == s2.leaves[0].dedup_key
    assert s1.leaves[0].occurrence_key == s2.leaves[0].occurrence_key
    assert lines == lines_before and payload == payload_before


def test_question_dedup_key_declaration_order_invariant():
    """BUG-V3-019：同一语义选项集不同声明序 → 同一 dedup_key（选项按 canonical label order）。

    注：不走 resolver 全链路——resolver 的选项定位按源行序前进（cursor），乱序声明会
    incomplete；此处直接测 Compiler._question_dedup_key 对声明序的不敏感性。
    """
    from app.domains.compile.snapshot import CompiledRole

    stem = CompiledRole(role="stem", span_id="s0", line_refs=(),
                        text="1. 下列哪个是水果", text_hash="0" * 64, label=None)
    texts = {"A": "A. 苹果", "B": "B. 香蕉", "C": "C. 汽车", "D": "D. 桌子"}

    def opts(order):
        return tuple(
            CompiledRole(role="option", span_id=f"o{l}", line_refs=(),
                         text=texts[l], text_hash="0" * 64, label=l)
            for l in order
        )

    compiler = Compiler({}, {})
    a = compiler._question_dedup_key("single_choice", stem, opts("ABCD"))
    b = compiler._question_dedup_key("single_choice", stem, opts("BDAC"))
    assert a == b


def test_canonical_options_input_sorts_and_rejects_dupes():
    """BUG-V3-019：canonical_options_input 按 label 排序 + label 重复 fail-fast。"""
    from app.domains.compile.identity_normalization import canonical_options_input
    out = canonical_options_input(
        [("B", "香蕉"), ("D", "桌子"), ("A", "苹果"), ("C", "汽车")]
    )
    assert [o["label"] for o in out] == ["A", "B", "C", "D"]
    assert out == [
        {"label": "A", "text": "苹果"},
        {"label": "B", "text": "香蕉"},
        {"label": "C", "text": "汽车"},
        {"label": "D", "text": "桌子"},
    ]
    with pytest.raises(ValueError):
        canonical_options_input([("A", "苹果"), ("A", "香蕉")])


def test_slice_span_multiline_join_golden():
    """BUG-V3-012：跨行 text 单个 \\n 按声明顺序拼接，不 strip 首尾空白；单行=该行本身。"""
    from app.domains.compile.compiler import _slice_span
    from app.domains.resolver.span import ResolvedSpan, SourceLineView
    line_by_ref = {
        "P1L001": SourceLineView("P1L001", " 材料开始 ", 1, 1, 1),
        "P1L002": SourceLineView("P1L002", " 材料甲内容段落 ", 2, 1, 2),
        "P1L003": SourceLineView("P1L003", "材料结束", 3, 1, 3),
    }

    def _span(refs, granularity="multi_line_pair"):
        return ResolvedSpan(
            span_id="sp-1", source_version_id=SVID, role="material",
            start_line_ref=refs[0], end_line_ref=refs[-1],
            line_refs=tuple(refs), granularity=granularity,
            start_offset=None, end_offset=None, text_hash="0" * 64,
            resolution_status="exact",
        )

    # 声明顺序 + 单个 \n + 不 strip
    assert _slice_span(_span(["P1L001", "P1L002", "P1L003"]), line_by_ref) == \
        " 材料开始 \n 材料甲内容段落 \n材料结束"
    # 声明顺序反序 → 结果反序（不按行号重排）
    assert _slice_span(_span(["P1L003", "P1L001"]), line_by_ref) == "材料结束\n 材料开始 "
    # 单行 = 该行 text 本身
    assert _slice_span(_span(["P1L001"], "single_line"), line_by_ref) == " 材料开始 "


def test_math_env_whitespace_folded_structural_only():
    """BUG-V3-015：数学环境内空白/换行折叠（structural）；符号/语义等价不做。"""
    from app.domains.compile.identity_normalization import normalize_identity
    # 正例：数学环境内空白/换行折叠 → 同一 identity
    assert normalize_identity("$x^2 + 1$") == normalize_identity("$x^2+1$")
    assert normalize_identity("$x^2 +\n 1$") == normalize_identity("$x^2+1$")
    # 反例：canonical identity ≠ mathematical equivalence（不做符号/语义等价）
    assert normalize_identity(r"\frac{1}{2}") != normalize_identity("0.5")
    assert normalize_identity(r"\sqrt{x^2}") != normalize_identity("|x|")
    assert normalize_identity("x^2") != normalize_identity("x²")
