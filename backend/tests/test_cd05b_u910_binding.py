# -*- coding: utf-8 -*-
"""05-B.1 回归：U9-10 逐子问 answer span 分离 → 双 match（真实缺陷覆盖）。

覆盖（Owner 05-B.1 ③）：
1. multi-q builder 两个 answer span 分离（各自「【答案】」行，不绑整窗）；
2. sub9 ownership=match；3. sub10 ownership=match；
4. 答案分别为 A / C；
5. 不影响其他 composite（multi-part 契约不变：答案无 declared_value 覆盖）；
6. 安全闸：ownership!=match → 阻断 review-ready。
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors_testsuite",
)
os.environ.setdefault("APP_SECRET", "test-app-secret-32-bytes-minimum!!")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domains.gate.binding_fact import derive_binding_fact  # noqa: E402
from app.domains.source.deterministic_importer import (  # noqa: E402
    build_unit_payload,
    check_review_ready,
)

# U9-10 形态夹具（与审计源文同构：共享材料+双题干选项+分离「【答案】」行）
SRC = [
    "海水晒盐后精制得到 NaCl，氯碱工业电解饱和 NaCl 溶液得到 Cl₂ 和 NaOH。",  # L1
    "",  # L2
    "9. 下列关于 Na、Mg、Cl、Br 元素及其化合物的说法正确的是",  # L3
    "",  # L4
    "A. NaOH 的碱性比 Mg(OH)₂ 的强",  # L5
    "",  # L6
    "B. Cl₂ 得到电子的能力比 Br₂ 的弱",  # L7
    "",  # L8
    "C. 原子半径 r：r(Br) > r(Cl)",  # L9
    "",  # L10
    "D. 原子的最外层电子数 n：n(Na) < n(Mg)",  # L11
    "",  # L12
    "10. 下列选项所示的物质间转化均能实现的是",  # L13
    "",  # L14
    "A. NaCl(aq) 电解 Cl₂(g)",  # L15
    "",  # L16
    "B. NaCl(aq) CO₂ NaHCO₃(s)",  # L17
    "",  # L18
    "C. NaBr(aq) Cl₂ Br₂(aq)",  # L19
    "",  # L20
    "D. Mg(OH)₂(s) HCl MgCl₂(ag)",  # L21
    "",  # L22
    "【答案】A",  # L23 → sub9
    "",  # L24
    "【解析】",  # L25
    "",  # L26
    "【详解】A. 同周期自左至右金属性减弱，故 A 正确；",  # L27
    "",  # L28
    "10.下列选项所示的物质间转化均能实现的是",  # L29
    "",  # L30
    "A. ……",  # L31
    "",  # L32
    "【答案】C",  # L33 → sub10
]

U910_UNIT = {
    "unit_id": "U9-10",
    "unit_type": "composite_question",
    "question_numbers": [9, 10],
    "printed_number": "9",
    "original_question_type": "single_choice",
    "questions_lines": [1, 22],
    "material_lines": [1, 1],
    "options_lines": [5, 21],
    "answer_lines": [23, 33],
    "explanation_lines": [25, 28],
    "answer_evidence": {"type": "answer_lines", "value": "9.A 10.C"},
    "answer_completeness": "unknown",
}

# Q16 形态夹具（multi-part 契约不变对照）
SRC16 = [
    "16. （12分）吸收工厂烟气中的 SO₂。",  # L1 material
    "",
    "（1）离子方程式为___。",  # L3
    "",
    "（2）原因是___。",  # L5
    "",
    "【答案】(1). 2NH3+SO2=NH4+ (2). 减小",  # L7
    "",
    "【解析】",
    "",
    "【分析】",
    "分析正文。",
    "【详解】(1) 详解一；",
    "",
    "(2) 详解二。",
]
Q16_UNIT = {
    "unit_id": "Q16",
    "unit_type": "composite_question",
    "question_numbers": [16],
    "printed_number": "16",
    "original_question_type": "fill_in",
    "questions_lines": [1, 5],
    "material_lines": [1, 1],
    "options_lines": None,
    "answer_lines": [7, 7],
    "explanation_lines": [9, 15],
    "answer_evidence": {"type": "answer_lines",
                        "value": "2NH3+SO2=NH4+；减小"},
    "answer_completeness": "unknown",
}


def _fact_for(ans, window, dv, loc, qn_unit=None):
    return derive_binding_fact(
        span_id=ans["span_id"], source_version_id="test-sv",
        unit_id=ans["unit_id"], question_number=ans["question_number"],
        source_lines=window, answer_text=ans["text"],
        evidence_kind="verbatim_declaration", decode_loc=loc,
        declared_value=dv,
    )


def test_u910_answer_spans_separated():
    r = build_unit_payload(U910_UNIT, SRC)
    assert r["ok"] and not r["hold"], r.get("hold_reasons")
    assert len(r["answer"]) == 2
    a9 = next(a for a in r["answer"] if a["question_number"] == "9")
    a10 = next(a for a in r["answer"] if a["question_number"] == "10")
    # 1) span 分离：各自「【答案】」行，不绑整窗
    assert a9["line_refs"] == ["P1L023"], a9["line_refs"]
    assert a10["line_refs"] == ["P1L033"], a10["line_refs"]
    assert a9["line_refs"] != a10["line_refs"]
    # 4) 答案 A / C
    assert a9["text"] == "A"
    assert a10["text"] == "C"


def test_u910_facts_both_match():
    r = build_unit_payload(U910_UNIT, SRC)
    a9 = next(a for a in r["answer"] if a["question_number"] == "9")
    a10 = next(a for a in r["answer"] if a["question_number"] == "10")
    w9 = [SRC[int(a9["line_refs"][0][3:]) - 1]]
    w10 = [SRC[int(a10["line_refs"][0][3:]) - 1]]
    f9 = _fact_for(a9, w9, a9["declared_value"], a9.get("decode_loc", ""))
    f10 = _fact_for(a10, w10, a10["declared_value"], a10.get("decode_loc", ""))
    # 2)/3) 双 match
    assert f9.ownership == "match", f9.ownership
    assert f10.ownership == "match", f10.ownership
    assert f9.unit_id == "U9-10.sub9" and f9.question_number == "9"
    assert f10.unit_id == "U9-10.sub10" and f10.question_number == "10"
    assert f9.answer_text_hash and f10.answer_text_hash
    # 6) 安全闸：match facts 放行
    assert check_review_ready([f9, f10]) == []


def test_safety_gate_blocks_non_match():
    r = build_unit_payload(U910_UNIT, SRC)
    a9 = next(a for a in r["answer"] if a["question_number"] == "9")
    # 整窗+完整值输入 → foreign（真实缺陷形态）
    bad = _fact_for(a9, SRC[22:33], "9.A 10.C", "")
    assert bad.ownership != "match", bad.ownership
    reasons = check_review_ready([bad])
    assert reasons and "ownership" in reasons[0]


def test_multi_part_contract_unchanged():
    # 5) multi-part 答案不带 declared_value 覆盖（04-B 契约路径不变）
    r = build_unit_payload(Q16_UNIT, SRC16)
    assert r["ok"] and not r["hold"], r.get("hold_reasons")
    assert len(r["answer"]) == 2
    for a in r["answer"]:
        assert "declared_value" not in a, a
        assert "decode_loc" not in a, a
    assert r["answer"][0]["text"].startswith("2NH3")
    assert r["answer"][1]["text"] == "减小"
