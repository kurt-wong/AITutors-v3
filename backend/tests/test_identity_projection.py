"""BUG-V3-039 — Diagnostic Metadata Leaks into Compile Identity 回归锁。

Frozen Spec（20 §4.5:172 confidence 示例 / §8.1:568 / P1-6:768）：confidence 是诊断
元数据（annotation_meta），不作 decision 触发。若 confidence 进入 annotation_payload_hash：
 ① 真实 LLM 输出 float confidence → BUG-V3-005 fail-fast → Task validation_error
    （I-1-D live smoke 实证：error_detail = "float forbidden in canonical identity input"）
 ② 即便规范化为 str，confidence 波动（0.98→0.97）也会改变 compile LE identity →
    artifact 复用/幂等被诊断噪声破坏

单一边界 = `gate.service._annotation_identity_projection`：仅剔除 unit 顶层 confidence。
BUG-V3-005 float 红线保持不动——其它 semantic float 仍 fail-fast（本文件反向锁）。
"""

import uuid
from types import SimpleNamespace

import pytest

from app.core.hashing import sha256_hex
from app.domains.compile.identity_normalization import identity_hash
from app.domains.gate.service import GateService, _annotation_identity_projection


def _unit(**over) -> dict:
    unit = {
        "unit_id": "Q1",
        "unit_type": "standalone_question",
        "question_number": "1",
        "section_id": "SEC-1",
        "original_question_type": "single_choice",
        "content": {
            "stem": {"role": "stem", "question_label": "1"},
            "options": [{"label": "A", "role": "option", "question_label": "1"}],
            "answer": {"role": "answer", "question_label": "1",
                       "answer_zone": "answer_table"},
        },
    }
    unit.update(over)
    return unit


def _payload(*units) -> dict:
    return {
        "document_metadata_claims": {"subject": "数学"},
        "sections": [],
        "semantic_units": list(units),
    }


def test_confidence_float_does_not_break_compile_identity() -> None:
    """confidence=0.98（float，真实 Qwen 输出形态）→ identity hash 不得触发 BUG-V3-005。"""
    p = _payload(_unit(confidence=0.98))
    assert len(sha256_hex(_annotation_identity_projection(p))) == 64

    ann = SimpleNamespace(payload=p)
    domain = GateService._compile_input_domain(uuid.uuid4(), ann, "Q1")
    assert len(domain["annotation_payload_hash"]) == 64

    # _input_identity 无 self 状态依赖，绕过 __init__（需 session）直接验证第三处 hash。
    ident = object.__new__(GateService)._input_identity(
        uuid.uuid4(), uuid.uuid4(), ann, SimpleNamespace(resolved_spans=[])
    )
    assert len(ident["annotation_payload_hash"]) == 64
    assert len(ident["resolver_input_hash"]) == 64


def test_confidence_change_does_not_change_compile_identity() -> None:
    """核心验收：confidence 0.98 → 0.97（诊断噪声）→ compile identity 必须不变。"""
    a = SimpleNamespace(payload=_payload(_unit(confidence=0.98)))
    b = SimpleNamespace(payload=_payload(_unit(confidence=0.97)))
    ann_id, unit_id = uuid.uuid4(), "Q1"
    da = GateService._compile_input_domain(ann_id, a, unit_id)
    db = GateService._compile_input_domain(ann_id, b, unit_id)
    assert da["annotation_payload_hash"] == db["annotation_payload_hash"]

    sv = uuid.uuid4()
    ia = object.__new__(GateService)._input_identity(
        sv, ann_id, a, SimpleNamespace(resolved_spans=[])
    )
    ib = object.__new__(GateService)._input_identity(
        sv, ann_id, b, SimpleNamespace(resolved_spans=[])
    )
    assert ia["annotation_payload_hash"] == ib["annotation_payload_hash"]
    assert ia["resolver_input_hash"] == ib["resolver_input_hash"]


def _payload_stem_changed(**over) -> dict:
    u = _unit(**over)
    u["content"]["stem"]["question_label"] = "2"
    return _payload(u)


def test_semantic_change_still_changes_identity() -> None:
    """projection 不得吞掉语义：真正的 semantic field 变化仍必须改变 identity。"""
    a = SimpleNamespace(payload=_payload(_unit(confidence=0.98)))
    b = SimpleNamespace(payload=_payload_stem_changed(confidence=0.98))
    ann_id = uuid.uuid4()
    ha = GateService._compile_input_domain(ann_id, a, "Q1")["annotation_payload_hash"]
    hb = GateService._compile_input_domain(ann_id, b, "Q1")["annotation_payload_hash"]
    assert ha != hb


def test_other_float_still_fails_fast() -> None:
    """BUG-V3-005 红线不被放宽：confidence 之外的 float 仍 ValueError fail-fast。

    防止「confidence 不进 identity」错误演化成「identity hash 自动接受 float」。
    """
    p = _payload(_unit(confidence=0.98, stray_float=0.5))
    projected = _annotation_identity_projection(p)
    with pytest.raises(ValueError, match="float forbidden"):
        identity_hash(projected)
    with pytest.raises(ValueError, match="float forbidden"):
        sha256_hex(projected)


def test_confidence_absent_remains_backward_compatible() -> None:
    """既有 mock fixture 全部无 confidence → projection 为恒等变换，hash 行为不变。"""
    p = _payload(_unit())
    assert _annotation_identity_projection(p) == p
    assert sha256_hex(_annotation_identity_projection(p)) == sha256_hex(p)

    # 入参不得被 mutate（ORM payload 是共享状态）。
    p2 = _payload(_unit(confidence=0.98))
    _annotation_identity_projection(p2)
    assert p2["semantic_units"][0]["confidence"] == 0.98


def test_nested_confidence_is_not_silently_projected() -> None:
    """锁定 projection 精确边界：嵌套 confidence 不被剥离（Identity Projection Rule）。

    projection 只剔除 semantic_units[*].confidence（unit 顶层），不做递归剥离。
    嵌套 confidence=float → BUG-V3-005 fail-fast；嵌套 confidence=str → 参与 identity。
    此测试不是支持嵌套 confidence，而是防止未来误以为 confidence 应被全局删除。
    """
    # nested confidence=float → canonical_json fail-fast（BUG-V3-005 红线）
    p_float = _payload(_unit())
    p_float["semantic_units"][0]["content"]["stem"]["confidence"] = 0.99
    projected = _annotation_identity_projection(p_float)
    # projection 不剥嵌套 —— float 仍在 → hash 时 fail-fast
    assert projected["semantic_units"][0]["content"]["stem"]["confidence"] == 0.99
    with pytest.raises(ValueError, match="float forbidden"):
        sha256_hex(projected)

    # nested confidence=str → 参与 identity（不被剥离）
    p_str_a = _payload(_unit())
    p_str_a["semantic_units"][0]["content"]["stem"]["confidence"] = "high"
    p_str_b = _payload(_unit())
    p_str_b["semantic_units"][0]["content"]["stem"]["confidence"] = "low"
    ha = sha256_hex(_annotation_identity_projection(p_str_a))
    hb = sha256_hex(_annotation_identity_projection(p_str_b))
    assert ha != hb  # 不同 nested confidence → 不同 identity（诚实行为）

    # unit 顶层 confidence 仍被剥离（精确 boundary 不变）
    p_top = _payload(_unit(confidence=0.98))
    p_top["semantic_units"][0]["content"]["stem"]["confidence"] = "high"
    projected_top = _annotation_identity_projection(p_top)
    assert "confidence" not in projected_top["semantic_units"][0]  # top stripped
    assert projected_top["semantic_units"][0]["content"]["stem"]["confidence"] == "high"  # nested kept
