# -*- coding: utf-8 -*-
"""CORE-DELIVERY-04-A 验证：short_answer 复合题确定性适配（Q8/Q9 真实输入）。

只读真实 Preprocessing 产物 + 纯函数/隔离调用；不写任何数据库、不导入。
覆盖任务书五、验证要求 1–7。
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET", "cd04a-local-test-key-not-production-000")

BACKEND = Path(r"D:\Project\AITutors-v3\backend")
sys.path.insert(0, str(BACKEND))

import hashlib  # noqa: E402

import pytest  # noqa: E402

from app.domains.gate.admission import (  # noqa: E402
    _aggregate_composite_roles,
    _dedup_key,
    _occurrence_key,
    _publish_decision,
)
from app.domains.gate.binding_fact import derive_binding_fact  # noqa: E402
from app.domains.source.preprocessing_import import (  # noqa: E402
    PreprocessingImportError,
    PreprocessingImportService,
    load_package_from_dir,
    _sha256,
)
from app.domains.source.short_answer_composite import (  # noqa: E402
    build_adapter_unit_payload,
    build_clean_package_dir,
    expand_short_answer_composite,
)

MANIFEST = Path(r"D:\Project\Papers\tests\CORE_DELIVERY_QUESTION_QUALITY\run_20261102_143000\03_FIXED\input\高考真题\化学\2020全国I卷高考真题化学（教师版）(1).manifest.json")
DISPLAY_VIEW = MANIFEST.with_suffix("").with_suffix(".md")  # 03_FIXED 同 basename 展示视图
ORIGINAL_DOCX = Path(r"D:\Project\Papers\maintainess\DOCX\高三\化学\2020全国I卷高考真题化学（教师版）(1).docx")
ORIGINAL_PDF = Path(r"D:\Project\Papers\maintainess\PDF\2020全国I卷高考真题化学（教师版）(1).pdf")


@pytest.fixture(scope="module")
def pkg():
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    src_path = Path(str(man["source_file"]))
    src_lines = src_path.read_text(encoding="utf-8").splitlines()
    return {"man": man, "src_path": src_path, "src_lines": src_lines}


@pytest.fixture(scope="module")
def adapted(pkg):
    out = {}
    for u in pkg["man"]["units"]:
        if u["unit_id"] in ("Q8", "Q9"):
            out[u["unit_id"]] = build_adapter_unit_payload(
                u, pkg["src_lines"],
                image_assets=pkg["man"].get("image_assets") or [],
            )
    return out


# ── V1 输入包读取来自 Manifest 指定权威文件 ──────────────────────────
def test_v1_package_loads_authoritative_source(pkg, tmp_path):
    info = build_clean_package_dir(
        tmp_path / "pkg",
        manifest_path=MANIFEST,
        source_md_path=pkg["src_path"],
        original_path=ORIGINAL_DOCX,
    )
    package = load_package_from_dir(Path(info["package_dir"]))
    # 权威源文内容身份：包内 basename 槽 = Ocr-markdown 字节
    assert package.source_md == pkg["src_path"].read_bytes()
    assert _sha256(package.source_md) == pkg["man"]["source_content_sha256"]
    # 身份闸通过（纯校验，不写库）
    PreprocessingImportService._verify_package_identity(
        PreprocessingImportService.__new__(PreprocessingImportService), package
    )


def test_v1b_display_view_cannot_pass_identity(pkg, tmp_path):
    """组包误放 03_FIXED 展示视图 → hash 闸 fail-closed（basename 风险被挡）。"""
    d = tmp_path / "bad"
    d.mkdir()
    base = Path(str(pkg["man"]["source_file"])).name
    MANIFEST_NAME = MANIFEST.name
    (d / MANIFEST_NAME).write_bytes(MANIFEST.read_bytes())
    (d / base).write_bytes(DISPLAY_VIEW.read_bytes())  # 展示视图顶位
    (d / ORIGINAL_DOCX.name).write_bytes(ORIGINAL_DOCX.read_bytes())
    package = load_package_from_dir(d)
    with pytest.raises(PreprocessingImportError) as ei:
        PreprocessingImportService._verify_package_identity(
            PreprocessingImportService.__new__(PreprocessingImportService), package
        )
    assert "mismatch" in str(ei.value)


# ── V2 父 Question 一个、内部子问完整有序 ───────────────────────────
def test_v2_one_parent_with_ordered_subs(adapted):
    for uid, k in (("Q8", 6), ("Q9", 6)):
        a = adapted[uid]
        assert a["ok"], a["issues"]
        subs = a["ir_unit"]["sub_questions"]
        assert a["ir_unit"]["unit_type"] == "composite_unit"
        assert len(subs) == k
        assert [int(s["question_number"]) for s in subs] == list(range(1, k + 1))
        # 父级 stem 恰一条 + 子问 stem 有序且非空
        stems = [r for r in a["compiled_roles"] if r["role"] == "stem"]
        parent = [r for r in stems if r.get("label") is None]
        subs_stems = [r for r in stems if r.get("label") is not None]
        assert len(parent) == 1 and parent[0]["unit_id"] == uid
        assert len(subs_stems) == k and all(r["text"] for r in subs_stems)
        assert [r["label"] for r in subs_stems] == [str(i) for i in range(1, k + 1)]
        # 不拆分成多 Question：适配输出只有一个 ir_unit 根
        assert a["ir_unit"]["sub_questions"] and a["ir_unit"]["unit_id"] == uid


def test_v2b_aggregation_keeps_single_question_with_sub_rows(adapted):
    """喂 _aggregate_composite_roles（生产函数）：1 父 + 6 子，父级 stem 不被子问 1 顶替。"""
    a = adapted["Q8"]
    root = a["ir_unit"]
    units = [root] + root["sub_questions"]
    roles_by_unit: dict = {}
    for r in a["compiled_roles"]:
        roles_by_unit.setdefault(r["unit_id"], []).append(r)
    answers_by_unit = {x["unit_id"]: x for x in a["answer"]}
    spans = {s["span_id"]: s for s in a["resolved_spans"]}
    roles, stem_meta, ans_rows = _aggregate_composite_roles(
        root, units, roles_by_unit, answers_by_unit, spans, materials_by_unit={},
    )
    # B1：stem_meta 必须是父级共享 stem，不得是 Q8.sub1
    assert stem_meta is not None
    assert stem_meta["unit_id"] == "Q8"
    assert stem_meta["unit_id"] != "Q8.sub1"
    assert stem_meta["label"] is None
    # B1：父级 stem 文本含题头与指导语（Q8 [OCR]L108 + L120）
    assert "回答下列问题" in stem_meta["text"]
    assert "8" in stem_meta["text"]  # 题头 8\. (14分)
    # B1：父级 stem 恰一行（聚合输出中 label=None 的 stem 只有一条）
    parent_stems = [r for r in roles if r["role"] == "stem" and r.get("label") is None]
    assert len(parent_stems) == 1
    assert parent_stems[0]["unit_id"] == "Q8"
    # 6 个子问 stem 独立存在（label=1..6，归属子 unit_id），不是父级
    sub_stems = [r for r in roles if r["role"] == "stem" and r.get("label") is not None]
    assert [r["label"] for r in sub_stems] == list("123456")
    assert [r["unit_id"] for r in sub_stems] == [f"Q8.sub{i}" for i in range(1, 7)]
    # material 在聚合输出只出现一次
    assert len([r for r in roles if r["role"] == "material"]) == 1
    # 6 个子问答案（label=题号）
    assert len(ans_rows) == 6
    assert [x["label"] for x in ans_rows] == ["1", "2", "3", "4", "5", "6"]


def test_v2c_q9_parent_stem_has_instruction(adapted):
    """B1：Q9 父级 stem 含 [OCR]L141 指导语，unit 归属 Q9。"""
    a = adapted["Q9"]
    root = a["ir_unit"]
    roles_by_unit: dict = {}
    for r in a["compiled_roles"]:
        roles_by_unit.setdefault(r["unit_id"], []).append(r)
    roles, stem_meta, _ans = _aggregate_composite_roles(
        root, [root] + root["sub_questions"], roles_by_unit,
        {x["unit_id"]: x for x in a["answer"]},
        {s["span_id"]: s for s in a["resolved_spans"]}, materials_by_unit={},
    )
    assert stem_meta["unit_id"] == "Q9"
    assert "回答下列问题" in stem_meta["text"]
    assert len([r for r in roles if r["role"] == "stem" and r.get("label") is None]) == 1


# ── V3 子问答案与解析一一对应 ─────────────────────────────────────
# R1C-R2 已复核的空位序映射（独立期望值，非实现自证）
EXPECTED_SEG_MAP = {
    "Q8": {1: [1], 2: [2, 3], 3: [4, 5], 4: [6], 5: [7], 6: [8]},
    "Q9": {1: [1], 2: [2], 3: [3], 4: [4], 5: [5, 6, 7, 8], 6: [9]},
}


def test_v3_sub_answers_and_explanations_bound(pkg, adapted):
    from app.domains.source.short_answer_composite import split_entry_segments
    for uid in ("Q8", "Q9"):
        a = adapted[uid]
        ans = [r for r in a["compiled_roles"] if r["role"] == "answer"]
        expl = [r for r in a["compiled_roles"]
                if r["role"] == "explanation" and r["label"] is not None]
        assert len(ans) == 6 and len(expl) == 6
        assert [r["label"] for r in ans] == [r["label"] for r in expl] == list("123456")
        for r in expl:
            assert len(r["text"]) > 10
        # 段归属唯一性：逐子问拼接等式（期望映射来自 R1C-R2，非实现自证）
        val = next(u for u in pkg["man"]["units"] if u["unit_id"] == uid)["answer_evidence"]["value"]
        segs = split_entry_segments(val)
        by_label = {r["label"]: r["text"] for r in ans}
        rebuilt = []
        for n in range(1, 7):
            expected = " ".join(segs[i] for i in EXPECTED_SEG_MAP[uid][n])
            assert by_label[str(n)] == expected, f"{uid} sub{n} 归属错"
            rebuilt.append(expected)
        # 全局重建：每段恰好归属一次（无丢无重）
        assert " ".join(rebuilt) == " ".join(segs[i] for i in sorted(segs))


def test_v3b_q8_answer_mapping_rinta2_rule(pkg, adapted):
    """Q8：空位序映射与 R1C-R2 复核一致（段2,3→子问2；段4,5→子问3）。"""
    a = adapted["Q8"]
    by_label = {r["label"]: r["text"] for r in a["compiled_roles"] if r["role"] == "answer"}
    assert "Fe²⁺" in by_label["2"]
    assert "VO⁺+MnO₂+2H⁺=VO₂⁺+Mn²⁺+H₂O" in by_label["2"]  # (3) 电荷补正在位
    assert "Mn²⁺" in by_label["3"]
    assert "Fe(OH)₃" in by_label["4"]
    assert "NaAlO₂" in by_label["5"] and "Na[Al(OH)₄]" in by_label["5"]  # (7) 双表达
    assert "同离子效应" in by_label["6"]


def test_v3c_aggregation_carries_sub_explanations(adapted):
    """聚合输出含 6 条子问 explanation（label=题号）+ 1 条组级（label=None）。"""
    a = adapted["Q8"]
    root = a["ir_unit"]
    roles_by_unit: dict = {}
    for r in a["compiled_roles"]:
        roles_by_unit.setdefault(r["unit_id"], []).append(r)
    roles, _s, _ans = _aggregate_composite_roles(
        root, [root] + root["sub_questions"], roles_by_unit,
        {x["unit_id"]: x for x in a["answer"]},
        {s["span_id"]: s for s in a["resolved_spans"]}, materials_by_unit={},
    )
    expl = [r for r in roles if r["role"] == "explanation"]
    sub_expl = [r for r in expl if r.get("label") is not None]
    grp_expl = [r for r in expl if r.get("label") is None]
    assert [r["label"] for r in sub_expl] == list("123456")
    assert len(grp_expl) == 1
    # 子问解析同时在 sub content 自包含（契约）
    for sp in root["sub_questions"]:
        assert "explanation" in sp["content"] and sp["content"]["explanation"]["explanation_lines"]


# ── V4 图片资源及关联可追溯 ───────────────────────────────────────
def test_v4_figure_links_traceable(adapted):
    q8_lines = {l for fl in adapted["Q8"]["figure_links"] for l in [fl["line_no"]]}
    q9_lines = {l for fl in adapted["Q9"]["figure_links"] for l in [fl["line_no"]]}
    assert {112, 483} <= q8_lines      # 材料流程图 + extra 区图
    assert {138, 147, 533, 542} <= q9_lines
    for uid in ("Q8", "Q9"):
        for fl in adapted[uid]["figure_links"]:
            assert fl["figure_src"] and fl["resolved_from"]
            assert fl["role"] != "unassigned" or fl["line_no"] in (483, 533, 542)  # extra 区允许未归属角色
    # zone 区分正文图与 extra 重复图（防高估图片交付）
    q8_zone = {fl["line_no"]: fl["zone"] for fl in adapted["Q8"]["figure_links"]}
    q9_zone = {fl["line_no"]: fl["zone"] for fl in adapted["Q9"]["figure_links"]}
    assert q8_zone == {112: "main", 483: "extra_duplicate"}
    assert q9_zone == {138: "main", 147: "main", 533: "extra_duplicate", 542: "extra_duplicate"}


def test_v4b_inline_img_src_present(pkg, adapted):
    """真实展示链=正文内联 <img>；src 在材料行内且指向 _imgs 资产。"""
    mat = next(r for r in adapted["Q8"]["compiled_roles"] if r["role"] == "material")
    assert "<img" in mat["text"] and "_imgs/" in mat["text"]


# ── V5 Q9 展示说明数据传递路径 ────────────────────────────────────
def test_v5_display_note_channel(adapted, pkg):
    note = "原文如此；题目区作 0.110 mol·L⁻¹（题干区 0.110 / 答案解析区 0.10 为源 Word 母本自带差异）"
    a = build_adapter_unit_payload(
        next(u for u in pkg["man"]["units"] if u["unit_id"] == "Q9"),
        pkg["src_lines"],
        display_annotations=[{"key": "q9_concentration_original", "text": note}],
    )
    rows = [r for r in a["compiled_roles"] if r["role"] == "display_note"]
    assert len(rows) == 1 and rows[0]["text"] == note and rows[0]["label"] == "q9_concentration_original"
    # B2：display_note 不入证据链——不在 resolved_spans、无 line_refs、无伪 P1L 行号
    assert not any("display_note" in s["span_id"] for s in a["resolved_spans"])
    assert "line_refs" not in rows[0]
    assert not str(rows[0].get("span_id", "")).startswith("P1L")
    assert all("P1L000" not in str(s.get("line_refs")) for s in a["resolved_spans"])
    # 聚合透传（admission 最小扩展）
    root = a["ir_unit"]
    roles_by_unit: dict = {}
    for r in a["compiled_roles"]:
        roles_by_unit.setdefault(r["unit_id"], []).append(r)
    roles, _s, _ans = _aggregate_composite_roles(
        root, [root] + root["sub_questions"], roles_by_unit,
        {x["unit_id"]: x for x in a["answer"]},
        {s["span_id"]: s for s in a["resolved_spans"]}, materials_by_unit={},
    )
    assert any(r["role"] == "display_note" and r["text"] == note for r in roles)
    # 学生端可读性：display_note 不属于答案类 role（读出期只门控 answer/explanation）
    dn = next(r for r in roles if r["role"] == "display_note")
    assert dn["role"] not in ("answer", "explanation")


# ── V6 答案仍受 BindingFact 与 Admission 约束 ─────────────────────
def test_v6_binding_fact_per_sub(pkg, adapted):
    a = adapted["Q8"]
    src_lines = pkg["src_lines"]
    for ans in a["answer"]:
        lo, hi = int(ans["line_refs"][0][3:]), int(ans["line_refs"][-1][3:])
        fact = derive_binding_fact(
            span_id=ans["span_id"],
            source_version_id="00000000-0000-4000-8000-00000000cd04a",
            unit_id=ans["unit_id"],
            question_number=ans["question_number"],
            source_lines=src_lines[lo - 1:hi],
            answer_text=ans["text"],
            declared_value=ans["text"],
            evidence_kind="verbatim_declaration",
        )
        assert fact.span_id == ans["span_id"]
        assert fact.ownership in ("match", "local_proven", "unknown", "foreign")
        # 无授权 → 不发布（写入期非 official 文本恒空）
        official, publish, nonempty = _publish_decision(
            ownership=fact.ownership, candidate_text=ans["text"], grant="none",
            review_evidence=None, content_ok=True, source_ok=True)
        assert publish != "official" or fact.ownership in ("match", "local_proven")
        if fact.ownership in ("match", "local_proven"):
            # auto_gate 可发；human 无 review 证据 → withheld
            _, p_auto, _ = _publish_decision(
                ownership=fact.ownership, candidate_text=ans["text"], grant="auto_gate",
                review_evidence=None, content_ok=True, source_ok=True)
            assert p_auto == "official"
            _, p_human_nore, _ = _publish_decision(
                ownership=fact.ownership, candidate_text=ans["text"], grant="human",
                review_evidence=None, content_ok=True, source_ok=True)
            assert p_human_nore != "official"


# ── V6b 父 Question 身份/去重/occurrence 纯规划路径 ─────────────────
def test_v6b_planning_identity_uses_parent_stem(adapted):
    """B1：_dedup_key/_occurrence_key 以父级 stem 定身份（纯规划，无 DB）。"""
    out = {}
    for uid in ("Q8", "Q9"):
        a = adapted[uid]
        root = a["ir_unit"]
        roles_by_unit: dict = {}
        for r in a["compiled_roles"]:
            roles_by_unit.setdefault(r["unit_id"], []).append(r)
        roles, stem_meta, _ans = _aggregate_composite_roles(
            root, [root] + root["sub_questions"], roles_by_unit,
            {x["unit_id"]: x for x in a["answer"]},
            {s["span_id"]: s for s in a["resolved_spans"]}, materials_by_unit={},
        )
        span = {s["span_id"]: s for s in a["resolved_spans"]}[stem_meta["span_id"]]
        out[uid] = {
            "dedup": _dedup_key("short_answer", stem_meta, roles),
            "occ": _occurrence_key(uid, uid[1:], span),
        }
    # 不同父 Question → dedup/occurrence 不同
    assert out["Q8"]["dedup"] != out["Q9"]["dedup"]
    assert out["Q8"]["occ"] != out["Q9"]["occ"]
    # 父身份由父级 stem 决定：换成子问 1 stem 的 dedup 必须不同（旧 bug 形态）
    a8 = adapted["Q8"]
    root8 = a8["ir_unit"]
    roles_by_unit8: dict = {}
    for r in a8["compiled_roles"]:
        roles_by_unit8.setdefault(r["unit_id"], []).append(r)
    roles8, _stem8, _ = _aggregate_composite_roles(
        root8, [root8] + root8["sub_questions"], roles_by_unit8,
        {x["unit_id"]: x for x in a8["answer"]},
        {s["span_id"]: s for s in a8["resolved_spans"]}, materials_by_unit={},
    )
    sub1_stem = next(r for r in roles8 if r["role"] == "stem" and r.get("label") == "1")
    assert _dedup_key("short_answer", sub1_stem, roles8) != out["Q8"]["dedup"]


# ── V7 不确定/证据不足的答案不被错误发布 ──────────────────────────
def test_v7_no_mis_publish():
    # foreign 永不发布
    _, p, _ = _publish_decision(
        ownership="foreign", candidate_text="X", grant="human",
        review_evidence={"reviewer_id": "R", "confirmed_fields": ["content", "belongs_to"]},
        content_ok=True, source_ok=True)
    assert p != "official"
    # unknown 无 review → withheld
    _, p2, _ = _publish_decision(
        ownership="unknown", candidate_text="X", grant="human",
        review_evidence=None, content_ok=True, source_ok=True)
    assert p2 != "official"
    # unknown + 合格 review（含 belongs_to）→ 可发（既有门槛，不降级）
    official3, p3, _ = _publish_decision(
        ownership="unknown", candidate_text="X", grant="human",
        review_evidence={"reviewer_id": "R", "confirmed_fields": ["content", "belongs_to"]},
        content_ok=True, source_ok=True)
    assert p3 == "official" and official3 == "X"


# ── 结构计数不齐 fail-loud（S6）──────────────────────────────────
def test_s6_fail_loud_on_count_mismatch(pkg):
    u = next(x for x in pkg["man"]["units"] if x["unit_id"] == "Q8")
    bad = dict(u)
    bad["answer_evidence"] = dict(u["answer_evidence"])
    bad["answer_evidence"]["value"] = "(1)仅一段"
    res = expand_short_answer_composite(
        pkg["src_lines"], unit_id="Q8",
        questions_range=tuple(u["questions_lines"]),
        material_range=tuple(u["material_lines"]),
        answer_value=bad["answer_evidence"]["value"],
        answer_range=tuple(u["answer_lines"]),
        explanation_range=tuple(u["explanation_lines"]),
    )
    assert not res.ok and res.subs == []
    assert any("mismatch" in i for i in res.issues)
