"""X2.6 preprocessing ↔ V3/X Integration Boundary tests。

覆盖任务书 §15 要求的四类：

- Valid：standalone / composite / composite+sub / standalone+material /
  composite+shared material / figure 引用 / provenance 保留 / 顺序保留 /
  合法 canonical Question Type
- Invalid：缺失 Unit Type / 未知 Unit Type / legacy 值直入 canonical 结构 /
  畸形 composite / 断裂 material 引用 / 断裂 figure 引用 / 缺失身份·血缘 /
  不支持的 Producer 取值（legacy 噪声）
- Boundary：Producer 词表 ≠ canonical 词表；legacy 不得泄漏进 canonical runtime 结构
- End-to-end：preprocessing fixture → boundary adapter → V3 IR → Compiler → Gate

全部 fixture 为**合成数据**，不读生产语料。真实语料冒烟另由
`test_real_producer_activation.py` 承担。

Admission 落库（`create_admission_candidate`）需要 PostgreSQL 会话，不在本文件覆盖；
端到端止于 Gate policy/payload（纯函数），该限制在 TestEndToEnd 中显式登记，不模拟成功。
"""

from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domains.compile import CANONICAL_TYPES, UNIT_TYPES
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.payload import build as build_payload
from app.domains.gate.policy import evaluate
from scripts.preprocessing_consumer.annotation_adapter import (
    GAP_OPTION_LABEL_SPAN_UNAVAILABLE,
    GAP_STANDALONE_MATERIAL_NOT_CONSUMED,
    GAP_SUB_QUESTION_DECOMPOSITION,
    manifest_to_annotation_payload,
)
from scripts.preprocessing_consumer.boundary import (
    CODE_BROKEN_FIGURE_REFERENCE,
    CODE_BROKEN_MATERIAL_REFERENCE,
    CODE_MALFORMED_IDENTITY,
    CODE_MISSING_IDENTITY,
    CODE_MISSING_IDENTITY_VERSION,
    CODE_MISSING_UNIT_TYPE,
    CODE_OUT_OF_SCOPE_IDENTITY_VERSION,
    CODE_UNKNOWN_UNIT_TYPE,
    BoundaryViolation,
    normalize_interface_identity,
    normalize_unit_type,
    scan_figure_references,
    validate_figure_references,
    validate_material_references,
)
from scripts.preprocessing_consumer.manifest_reader import (
    Manifest,
    ManifestSection,
    ManifestUnit,
    load_manifest,
)
from scripts.preprocessing_consumer.resolved_span_adapter import (
    manifest_to_resolved_spans,
)
from scripts.preprocessing_consumer.runner_b2 import _build_resolved_run

SHA_OK = hashlib.sha256(b"synthetic source bytes").hexdigest()
LINE_COUNT = 40


# ═══════════════════════════════════════════════════════════════
# fixture helpers（合成数据）
# ═══════════════════════════════════════════════════════════════


def _unit(unit_id: str, unit_type: str, **kw) -> ManifestUnit:
    return ManifestUnit(
        unit_id=unit_id,
        unit_type=unit_type,
        question_numbers=tuple(kw.pop("question_numbers", (1,))),
        original_question_type=kw.pop("original_question_type", "short_answer"),
        **kw,
    )


def _manifest(units: list[ManifestUnit], **kw) -> Manifest:
    return Manifest(
        source_file=kw.pop("source_file", "D:/synthetic/source.md"),
        model=kw.pop("model", "synthetic-model"),
        prompt_version=kw.pop("prompt_version", "synthetic-v1"),
        validation_issues=kw.pop("validation_issues", ()),
        warnings=kw.pop("warnings", ()),
        units=tuple(units),
        source_content_sha256=kw.pop("source_content_sha256", SHA_OK),
        identity_version=kw.pop("identity_version", 2),
        sections=kw.pop("sections", ()),
    )


def _lines(n: int = LINE_COUNT) -> list:
    from scripts.preprocessing_consumer.source_loader import SourceLine

    return [
        SourceLine(
            line_ref=f"P1L{i:03d}",
            seq=i - 1,
            page_no=1,
            line_no_in_page=i,
            text=f"synthetic line {i}",
            block_type="text",
            line_hash=hashlib.sha256(f"synthetic line {i}".encode()).hexdigest(),
        )
        for i in range(1, n + 1)
    ]


def _run_to_gate(manifest: Manifest, lines: list) -> dict:
    """preprocessing fixture → adapter → IR → Compiler → Gate（纯函数段）。"""
    payload = manifest_to_annotation_payload(manifest)
    sv_id = uuid.uuid4()
    resolved_run = _build_resolved_run(manifest, lines, sv_id)
    ir = IRBuilder.build(resolved_run, payload, sv_id, uuid.uuid4())
    line_map = {sl.line_ref: sl for sl in lines}
    span_map = {s.span_id: s for s in resolved_run.resolved_spans}
    compiled = Compiler(span_map, line_map).compile(ir)
    gates = []
    for root in ir.units:
        if root.semantic_status != "ready":
            gates.append({"unit_id": root.unit_id, "decision": None,
                          "semantic_status": root.semantic_status})
            continue
        decision = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=resolved_run)
        gates.append({"unit_id": root.unit_id, "decision": decision.get("decision"),
                      "semantic_status": root.semantic_status,
                      "payload_keys": sorted(build_payload(
                          root=root, ir=ir, compiled=compiled,
                          resolved_run=resolved_run).keys())})
    return {"payload": payload, "ir": ir, "compiled": compiled,
            "resolved_run": resolved_run, "gates": gates}


# ═══════════════════════════════════════════════════════════════
# A. Valid cases（任务书 §15）
# ═══════════════════════════════════════════════════════════════


class TestValidCases:
    def test_standalone_unit_normalizes_and_builds(self):
        """standalone unit：Producer legacy → canonical，IR 可构建。"""
        m = _manifest([_unit("Q1", "standalone_question",
                             stem_lines=(1, 2), answer_lines=(3, 3))])
        out = manifest_to_annotation_payload(m)
        assert out["semantic_units"][0]["unit_type"] == "standalone_unit"

        ir = IRBuilder.build(
            _build_resolved_run(m, _lines(), uuid.uuid4()), out, uuid.uuid4(), uuid.uuid4()
        )
        assert ir.units[0].unit_type == "standalone_unit"
        assert ir.units[0].semantic_status == "ready"

    def test_composite_unit_normalizes_and_builds(self):
        """composite unit → composite_unit + 单个子题（确定性结构翻译）。"""
        m = _manifest([_unit("U1", "composite_question",
                             question_numbers=(1, 2),
                             material_lines=(1, 3), questions_lines=(4, 8),
                             answer_lines=(9, 10))])
        out = manifest_to_annotation_payload(m)
        top = out["semantic_units"][0]
        assert top["unit_type"] == "composite_unit"
        assert top["question_number_range"] == "1-2"

        ir = IRBuilder.build(
            _build_resolved_run(m, _lines(), uuid.uuid4()), out, uuid.uuid4(), uuid.uuid4()
        )
        assert ir.units[0].unit_type == "composite_unit"

    def test_composite_with_sub_questions(self):
        """composite 子题存在且为 canonical（不泄漏 legacy 词表）。"""
        m = _manifest([_unit("U1", "composite_question",
                             material_lines=(1, 3), questions_lines=(4, 8),
                             answer_lines=(9, 10))])
        out = manifest_to_annotation_payload(m)
        subs = out["semantic_units"][0]["sub_questions"]
        assert len(subs) == 1
        assert subs[0]["unit_id"] == "U1.sub"
        assert subs[0]["unit_type"] == "standalone_unit"

    def test_standalone_with_material_is_preserved_not_denied(self):
        """standalone + material：领域事实保留，且**不得**记成「standalone 无 material」。

        CL-22 / OD-BLOCK-02 仍 OPEN（UQ-06：implementation authorized = NONE），
        故消费策略不变；但声明必须被显式登记，不得静默丢弃。
        """
        m = _manifest([_unit("Q1", "standalone_question",
                             stem_lines=(1, 2), answer_lines=(3, 3),
                             material_lines=(10, 12))])
        out = manifest_to_annotation_payload(m)
        codes = {g["code"] for g in out["producer_boundary"]["known_gaps"]}
        assert GAP_STANDALONE_MATERIAL_NOT_CONSUMED in codes

    def test_composite_with_shared_material(self):
        """composite shared material → shared_components.material + resolved span。"""
        m = _manifest([_unit("U1", "composite_question",
                             material_lines=(1, 3), questions_lines=(4, 8),
                             answer_lines=(9, 10))])
        out = manifest_to_annotation_payload(m)
        assert out["semantic_units"][0]["shared_components"] == {"material": {"role": "material"}}

        rr = _build_resolved_run(m, _lines(), uuid.uuid4())
        assert "sp-U1.material" in {s.span_id for s in rr.resolved_spans}

    def test_figure_image_references_are_scanned(self):
        """figure/image 引用：确定性发现（markdown + HTML），不解析、不恢复。"""
        text = "a\n![fig1](./img/a.png)\nb\n<img src=\"./img/b.png\">\nc\n![fig1](./img/a.png)\n"
        refs = scan_figure_references(text)
        assert refs == ("./img/a.png", "./img/b.png")  # 去重 + 首见顺序

    def test_provenance_preservation(self):
        """identity / provenance 在读取层完整保留（此前被丢弃）。"""
        m = Manifest(
            source_file="D:/synthetic/source.md", model="m", prompt_version="p",
            validation_issues=(), warnings=(), units=(_unit("Q1", "standalone_question"),),
            source_content_sha256=SHA_OK, identity_version=2,
            sections=(ManifestSection("S0", "title", 1, 1, 2, 1),),
        )
        assert m.source_content_sha256 == SHA_OK
        assert m.identity_version == 2
        assert len(m.sections) == 1
        assert m.sections[0].ordinal == 1

    def test_ordering_preservation(self):
        """单元顺序与 IR 顺序一致；归一化不重排。"""
        units = [
            _unit("Q3", "standalone_question", question_numbers=(3,),
                  stem_lines=(1, 1), answer_lines=(2, 2)),
            _unit("U1", "composite_question", question_numbers=(4, 5),
                  material_lines=(3, 4), questions_lines=(5, 6), answer_lines=(7, 7)),
            _unit("Q1", "standalone_question", question_numbers=(1,),
                  stem_lines=(8, 8), answer_lines=(9, 9)),
        ]
        m = _manifest(units)
        out = manifest_to_annotation_payload(m)
        assert [u["unit_id"] for u in out["semantic_units"]] == ["Q3", "U1", "Q1"]
        assert [n["unit_id"] for n in out["producer_boundary"]["unit_normalizations"]] == [
            "Q3", "U1", "Q1"]

        ir = IRBuilder.build(
            _build_resolved_run(m, _lines(), uuid.uuid4()), out, uuid.uuid4(), uuid.uuid4()
        )
        assert [n.unit_id for n in ir.units] == ["Q3", "U1", "Q1"]

    @pytest.mark.parametrize("qt", sorted(CANONICAL_TYPES))
    def test_valid_canonical_question_types_accepted(self, qt):
        """12 个 canonical Question Type 全部原样通过（QT⟂UT，无 QT→UT 映射）。"""
        out = manifest_to_annotation_payload(_manifest([
            _unit("Q1", "standalone_question", original_question_type=qt,
                  stem_lines=(1, 1), answer_lines=(2, 2)),
        ]))
        assert out["semantic_units"][0]["original_question_type"] == qt
        # 关键边界断言：QT 变化**不**改变 Unit Type
        assert out["semantic_units"][0]["unit_type"] == "standalone_unit"


# ═══════════════════════════════════════════════════════════════
# B. Invalid cases（任务书 §15）
# ═══════════════════════════════════════════════════════════════


class TestInvalidCases:
    def test_missing_unit_type(self):
        with pytest.raises(BoundaryViolation) as e:
            normalize_unit_type(None)
        assert e.value.code == CODE_MISSING_UNIT_TYPE

    def test_unknown_unit_type(self):
        with pytest.raises(BoundaryViolation) as e:
            normalize_unit_type("some_new_unit_kind")
        assert e.value.code == CODE_UNKNOWN_UNIT_TYPE

    def test_non_string_unit_type_rejected(self):
        with pytest.raises(BoundaryViolation) as e:
            normalize_unit_type(3)
        assert e.value.code == CODE_UNKNOWN_UNIT_TYPE

    @pytest.mark.parametrize("legacy", ["standalone_question", "composite_question"])
    def test_legacy_values_rejected_by_canonical_construction(self, legacy):
        """legacy 值**直入** canonical IR 构造必须被 F-M3-04 拒绝（不泄漏）。

        归一化是集成边界职责（OD-2）；canonical 构造层只接受 canonical 词表。
        """
        out = {
            "semantic_units": [{
                "unit_id": "Q1",
                "unit_type": legacy,           # 故意不归一化
                "question_number": "1",
                "original_question_type": "short_answer",
                "content": {
                    "stem": {"role": "stem", "question_label": "1"},
                    "answer": {"role": "answer", "question_label": "1",
                               "answer_zone": "answer_table"},
                },
            }]
        }
        with pytest.raises(ValueError, match="non-canonical unit_type"):
            IRBuilder.build(
                _build_resolved_run(_manifest([]), _lines(), uuid.uuid4()),
                out, uuid.uuid4(), uuid.uuid4(),
            )

    def test_legacy_noise_never_canonical(self):
        """DI-01 噪声 `andalone_question`：OD-1 裁定永不可 canonical → 显式失败。"""
        with pytest.raises(BoundaryViolation) as e:
            normalize_unit_type("andalone_question")
        assert e.value.code == CODE_UNKNOWN_UNIT_TYPE

    def test_malformed_composite_structure_is_explicit_not_ready(self):
        """畸形 composite（缺 material / 缺 questions 区间）→ 显式 incomplete，不静默成功。"""
        m = _manifest([_unit("U1", "composite_question")])  # 全部行区间缺失
        out = manifest_to_annotation_payload(m)
        ir = IRBuilder.build(
            _build_resolved_run(m, _lines(), uuid.uuid4()), out, uuid.uuid4(), uuid.uuid4()
        )
        assert ir.units[0].semantic_status == "incomplete"

    def test_broken_material_reference(self):
        """material 行区间越界 → 断链显式报告 + span 未解析。"""
        checks = validate_material_references({"material": (5, 999)}, LINE_COUNT)
        assert len(checks) == 1
        assert checks[0].code == CODE_BROKEN_MATERIAL_REFERENCE

        m = _manifest([_unit("U1", "composite_question",
                             material_lines=(5, 999), questions_lines=(1, 2),
                             answer_lines=(3, 3))])
        rr = _build_resolved_run(m, _lines(), uuid.uuid4())
        assert "sp-U1.material" not in {s.span_id for s in rr.resolved_spans}
        assert len(rr.unresolved_references) == 1
        assert rr.unresolved_references[0]["code"] == CODE_BROKEN_MATERIAL_REFERENCE

    def test_broken_figure_reference(self, tmp_path):
        src = tmp_path / "source.md"
        src.write_text("![gone](./img/missing.png)\n", encoding="utf-8")
        refs = scan_figure_references(src.read_text(encoding="utf-8"))
        checks = validate_figure_references(refs, src)
        assert len(checks) == 1
        assert checks[0].code == CODE_BROKEN_FIGURE_REFERENCE

    def test_missing_required_identity(self):
        with pytest.raises(BoundaryViolation) as e:
            normalize_interface_identity(None, 2)
        assert e.value.code == CODE_MISSING_IDENTITY

    def test_malformed_identity(self):
        with pytest.raises(BoundaryViolation) as e:
            normalize_interface_identity("NOT-A-SHA256", 2)
        assert e.value.code == CODE_MALFORMED_IDENTITY

    def test_uppercase_identity_rejected(self):
        """身份键必须 64 **小写** hex（Frozen Contract §1.2）。"""
        with pytest.raises(BoundaryViolation) as e:
            normalize_interface_identity(SHA_OK.upper(), 2)
        assert e.value.code == CODE_MALFORMED_IDENTITY

    def test_missing_identity_version(self):
        with pytest.raises(BoundaryViolation) as e:
            normalize_interface_identity(SHA_OK, None)
        assert e.value.code == CODE_MISSING_IDENTITY_VERSION

    def test_legacy_identity_v1_out_of_scope(self):
        """v1 legacy 不属 v0.2 接口（§1.7 C-IN-1 consumer 侧），不得静默消费。"""
        with pytest.raises(BoundaryViolation) as e:
            normalize_interface_identity(SHA_OK, 1)
        assert e.value.code == CODE_OUT_OF_SCOPE_IDENTITY_VERSION

    def test_unsupported_producer_value_fails_whole_manifest(self):
        """一份 manifest 含噪声值 → 整份边界违规，不产部分 payload、不 per-unit 洗白。"""
        m = _manifest([
            _unit("Q1", "standalone_question", stem_lines=(1, 1), answer_lines=(2, 2)),
            _unit("Q2", "andalone_question"),
        ])
        with pytest.raises(BoundaryViolation) as e:
            manifest_to_annotation_payload(m)
        assert e.value.code == CODE_UNKNOWN_UNIT_TYPE


# ═══════════════════════════════════════════════════════════════
# C. Boundary cases（任务书 §15）
# ═══════════════════════════════════════════════════════════════


class TestBoundaryCases:
    def test_producer_vocabulary_is_not_canonical_vocabulary(self):
        """显式验证：Producer 词表 ≠ V3/X canonical 词表。"""
        producer_vocab = {"standalone_question", "composite_question"}
        assert producer_vocab.isdisjoint(set(UNIT_TYPES))
        assert set(UNIT_TYPES) == {"standalone_unit", "composite_unit"}

    def test_legacy_cannot_leak_into_canonical_runtime_structures(self):
        """legacy 值不得出现在 canonical runtime 结构（semantic_units → IRNode）。"""
        m = _manifest([
            _unit("Q1", "standalone_question", stem_lines=(1, 1), answer_lines=(2, 2)),
            _unit("U1", "composite_question",
                  material_lines=(3, 4), questions_lines=(5, 6), answer_lines=(7, 7)),
        ])
        out = manifest_to_annotation_payload(m)

        # canonical runtime 输入面
        for u in out["semantic_units"]:
            assert u["unit_type"] in UNIT_TYPES
            for sub in u.get("sub_questions", []):
                assert sub["unit_type"] in UNIT_TYPES

        # canonical runtime 输出面
        ir = IRBuilder.build(
            _build_resolved_run(m, _lines(), uuid.uuid4()), out, uuid.uuid4(), uuid.uuid4()
        )
        for node in ir.units:
            assert node.unit_type in UNIT_TYPES
            for sub in node.sub_questions:
                assert sub.unit_type in UNIT_TYPES

        # 深度序列化也不得泄漏（防止值藏在嵌套结构里）
        dumped = json.dumps(
            {"units": [vars(n) for n in ir.units]}, default=str, ensure_ascii=False
        )
        assert "standalone_question" not in dumped
        assert "composite_question" not in dumped

    def test_legacy_value_preserved_only_as_evidence_outside_runtime(self):
        """UQ-01 Decision 7：保留 legacy 值，但只作为 runtime 结构**之外**的 evidence。"""
        out = manifest_to_annotation_payload(_manifest([
            _unit("Q1", "standalone_question", stem_lines=(1, 1), answer_lines=(2, 2)),
        ]))
        norm = out["producer_boundary"]["unit_normalizations"][0]
        assert norm["producer_unit_type"] == "standalone_question"   # preserved
        assert norm["canonical_unit_type"] == "standalone_unit"
        assert norm["normalization_event_id"] == "X2.6-OD-2-MAP-STANDALONE-01"
        assert norm["already_canonical"] is False

    def test_normalization_event_ids_are_distinct_and_bound(self):
        """OD-2 §2：两个 event ID 不可混用、不可复用。"""
        a = normalize_unit_type("standalone_question")
        b = normalize_unit_type("composite_question")
        assert a.normalization_event_id == "X2.6-OD-2-MAP-STANDALONE-01"
        assert b.normalization_event_id == "X2.6-OD-2-MAP-COMPOSITE-01"
        assert a.normalization_event_id != b.normalization_event_id
        assert a.canonical_unit_type == "standalone_unit"
        assert b.canonical_unit_type == "composite_unit"

    def test_already_canonical_is_idempotent_passthrough(self):
        """canonical 值幂等直通：不改写、不绑 event ID。"""
        for v in sorted(UNIT_TYPES):
            n = normalize_unit_type(v)
            assert n.canonical_unit_type == v
            assert n.already_canonical is True
            assert n.normalization_event_id is None

    def test_no_question_type_to_unit_type_mapping(self):
        """QT 变化不改变 UT：显式证明不存在 QT→UT 映射。"""
        seen = set()
        for qt in sorted(CANONICAL_TYPES):
            out = manifest_to_annotation_payload(_manifest([
                _unit("Q1", "standalone_question", original_question_type=qt,
                      stem_lines=(1, 1), answer_lines=(2, 2)),
            ]))
            seen.add(out["semantic_units"][0]["unit_type"])
        assert seen == {"standalone_unit"}

    def test_sub_question_decomposition_gap_is_explicit(self):
        """Producer 不拆子题：1:1 结构翻译必须显式登记 gap，不得假装已拆分。"""
        out = manifest_to_annotation_payload(_manifest([
            _unit("U1", "composite_question",
                  material_lines=(1, 2), questions_lines=(3, 5), answer_lines=(6, 6)),
        ]))
        codes = {g["code"] for g in out["producer_boundary"]["known_gaps"]}
        assert GAP_SUB_QUESTION_DECOMPOSITION in codes


# ═══════════════════════════════════════════════════════════════
# D. End-to-end（任务书 §15/§16）
# ═══════════════════════════════════════════════════════════════


class TestEndToEnd:
    def test_end_to_end_fixture_to_gate(self):
        """preprocessing fixture → adapter → V3 IR → Compiler → Gate（真实结构，非 mock）。

        覆盖 standalone（ready）+ composite（结构完整）+ 一个 malformed unit（incomplete）。
        Admission 落库不在本测试范围——`create_admission_candidate` 需要 PostgreSQL
        会话；该限制如实登记，不模拟成功（任务书 §16 No Fake End-to-End）。
        """
        units = [
            # standalone：stem + answer 齐备 → ready
            _unit("Q1", "standalone_question", question_numbers=(1,),
                  original_question_type="short_answer",
                  stem_lines=(1, 2), answer_lines=(3, 4)),
            # composite：material + questions + answer 齐备
            _unit("U1", "composite_question", question_numbers=(2, 3),
                  original_question_type="short_answer",
                  material_lines=(5, 6), questions_lines=(7, 9), answer_lines=(10, 11)),
            # malformed：行区间全缺 → incomplete（显式，不静默）
            _unit("Q9", "standalone_question", question_numbers=(9,),
                  original_question_type="short_answer"),
        ]
        out = _run_to_gate(_manifest(units), _lines())

        ir = out["ir"]
        assert [n.unit_id for n in ir.units] == ["Q1", "U1", "Q9"]
        assert all(n.unit_type in UNIT_TYPES for n in ir.units)

        by_id = {g["unit_id"]: g for g in out["gates"]}
        assert by_id["Q1"]["semantic_status"] == "ready"
        assert by_id["Q1"]["decision"] is not None
        assert by_id["U1"]["semantic_status"] == "ready"
        assert by_id["Q9"]["semantic_status"] == "incomplete"
        assert by_id["Q9"]["decision"] is None  # 非 ready 不进 Gate

        # 编译产物真实存在
        assert len(out["compiled"].leaves) >= 1

    def test_end_to_end_is_deterministic(self):
        """同一 fixture 两次执行结果一致（边界归一化是纯函数）。"""
        units = [_unit("Q1", "standalone_question",
                       stem_lines=(1, 2), answer_lines=(3, 4))]
        a = manifest_to_annotation_payload(_manifest(units))
        b = manifest_to_annotation_payload(_manifest(units))
        assert json.dumps(a, sort_keys=True, ensure_ascii=False) == \
            json.dumps(b, sort_keys=True, ensure_ascii=False)

    def test_end_to_end_fails_closed_on_noise_before_any_semantic_work(self):
        """噪声 unit_type 在进入任何语义消费前即被边界拒绝（fail-closed 顺序保证）。"""
        m = _manifest([
            _unit("Q2", "not_a_real_type"),
        ])
        with pytest.raises(BoundaryViolation):
            manifest_to_annotation_payload(m)

    def test_manifest_round_trip_preserves_identity_fields(self, tmp_path):
        """JSON 往返后 identity / provenance 仍完整（读取层 verbatim 保留）。"""
        raw = {
            "source_file": "D:/synthetic/source.md",
            "model": "synthetic-model",
            "identity_version": 2,
            "source_content_sha256": SHA_OK,
            "annotation_meta": {"prompt_version": "synthetic-v1",
                                "validation_issues": [], "warnings": []},
            "units": [{
                "unit_id": "Q1", "unit_type": "standalone_question",
                "question_numbers": [1], "original_question_type": "short_answer",
                "stem_lines": [1, 2], "answer_lines": [3, 4],
                "section_ref": "S1", "printed_provenance": "unknown",
                "basis": "unverified", "basis_evidence": "",
            }],
            "sections": [{"id": "S1", "title": "part one", "ordinal": 1,
                          "start_line": 1, "end_line": 4, "occurrence": 1}],
        }
        p = tmp_path / "synthetic.manifest.json"
        p.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

        m = load_manifest(p)
        assert m.source_content_sha256 == SHA_OK
        assert m.identity_version == 2
        assert len(m.sections) == 1 and m.sections[0].title == "part one"
        assert m.units[0].section_ref == "S1"
        assert m.units[0].basis == "unverified"

        # 身份可判定 + 词表可归一化 → 完整通过边界
        ident = normalize_interface_identity(m.source_content_sha256, m.identity_version)
        assert ident.identity_version == "2"
        assert normalize_unit_type(m.units[0].unit_type).canonical_unit_type == "standalone_unit"

    def test_resolved_span_adapter_agrees_with_runner_span_builder(self):
        """两条 span 构造路径对同一 fixture 产出一致的 span_id 集合（防跨路径漂移）。"""
        m = _manifest([
            _unit("Q1", "standalone_question", stem_lines=(1, 2), answer_lines=(3, 4)),
            _unit("U1", "composite_question",
                  material_lines=(5, 6), questions_lines=(7, 9), answer_lines=(10, 11)),
        ])
        lines = _lines()
        sv = uuid.uuid4()
        resolved, unresolved = manifest_to_resolved_spans(m, lines, sv)
        rr = _build_resolved_run(m, lines, sv)
        assert {s["span_id"] for s in resolved} == {s.span_id for s in rr.resolved_spans}
        assert unresolved == [] and rr.unresolved_references == ()

    def test_choice_type_gap_is_explicit_not_fabricated(self):
        """choice 题缺 per-label option span → 显式 gap + 不 fabricate 选项声明。"""
        out = manifest_to_annotation_payload(_manifest([
            _unit("Q1", "standalone_question", original_question_type="single_choice",
                  stem_lines=(1, 2), options_lines=(3, 6), answer_lines=(7, 8)),
        ]))
        codes = {g["code"] for g in out["producer_boundary"]["known_gaps"]}
        assert GAP_OPTION_LABEL_SPAN_UNAVAILABLE in codes
        assert "options" not in out["semantic_units"][0]["content"]
