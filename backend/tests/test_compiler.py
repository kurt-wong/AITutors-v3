"""Gate F — Compiler：三 key + text_hash raw + canonical 直通 + 确定性 + 负向矩阵（20 §7）。"""

import copy
import hashlib
import uuid

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
    return {"semantic_units": [{"unit_id": "Q1", "original_question_type": "single_choice",
        "content": {"stem": {"question_label": "1"},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {"answer_zone": "answer_table", "question_number": "1"}}}]}


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
        {"unit_id": "Q1", "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "1"}, "options": [{"label": "A"}, {"label": "B"}],
                     "answer": {"answer_zone": "answer_table", "question_number": "1"}}},
        {"unit_id": "Q2", "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "2"}, "options": [{"label": "A"}, {"label": "B"}],
                     "answer": {"answer_zone": "answer_table", "question_number": "2"}}},
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
                    {"unit_id": "Q1", "question_label": "1", "content": {
                        "stem": {"question_label": "1"},
                        "options": [{"label": "A"}, {"label": "B"}],
                        "answer": {"answer_zone": "answer_table", "question_number": "1"}}}
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
