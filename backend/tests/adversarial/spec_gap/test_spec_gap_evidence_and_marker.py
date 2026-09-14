"""架构契约缺口证明（spec_gap）— **不进正常 CI gate**。

本目录存放「当前契约未闭环」的对抗性证明，按 Owner 2026-09-13 裁决分层：

  产品契约测试（F-3/F-5/F-6）→ 留在 tests/ 根，FAIL → 修复 → PASS
  架构审查测试（F-2）        → 本目录，module 级 xfail
  输入鲁棒性（F-4）          → 本目录，module 级 xfail，延后 preprocessing 阶段
  测试基础设施（F-1）        → 单独立项 TEST-INFRA-01

`testpaths = ["tests"]` 会递归收集子目录，**仅分目录不足以排除**，
故配 module 级 `pytestmark = pytest.mark.xfail`：`pytest -q` 记为 xfailed（非 failed），
缺口仍被登记，且若日后有人实现 enforcement 会 XPASS —— 那本身就是信号。

对应登记：bugs.md BUG-V3-048（F-2）、BUG-V3-049（F-4）。
"""

import pathlib
import uuid

import pytest

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

pytestmark = pytest.mark.xfail(
    reason="架构契约缺口证明（非 CI gate）— 见 bugs.md BUG-V3-048 / BUG-V3-049",
    strict=False,
)

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000e")

_APP_ROOT = pathlib.Path(__file__).resolve().parents[2] / "app"


# ---------------------------------------------------------------------------
# F-2 / BUG-V3-048：Evidence Authority Enforcement 未闭环
# ---------------------------------------------------------------------------


def test_admission_module_has_zero_evidence_promotion_reference() -> None:
    """75 §三 R4/R5 契约缺口证明。

    契约：「只有 ValidationEvent 产生 Evidence Authority」+「Semantic IR 只能引用
    ValidatedEvidence」。若 admission 的 approve 路径从不查询 evidence ledger，
    则 authority boundary 是**叙述**而非**执行**。

    Owner 裁决（2026-09-13）：这**不是 bug，是架构决策未决**——Evidence 当前是
    A) 审计记录 还是 B) 准入前置条件？代码选了 A，Spec 更接近 B。
    故本测试不进 CI gate，只作为缺口证明长期保留，待架构裁决后决定去留。
    """
    source = (_APP_ROOT / "domains" / "gate" / "admission.py").read_text(encoding="utf-8")
    hits = [n for n in ("EvidencePromotion", "is_evidence_validated", "ValidationEvent")
            if n in source]
    assert hits, (
        "AdmissionService 完全不引用 EvidencePromotionService / ValidationEvent / "
        "is_evidence_validated。75 §三 R4/R5 在 admission 路径上未被执行；"
        "门控 admission 的是 gate_decision，evidence ledger 是并行审计记录。（F-2）"
    )


def test_is_evidence_validated_has_no_production_caller() -> None:
    """`is_evidence_validated` 在 backend/app 下除定义外零生产调用方（F-2 第二证据）。"""
    callers = []
    for p in _APP_ROOT.rglob("*.py"):
        for i, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
            if "is_evidence_validated" not in line:
                continue
            s = line.strip()
            if s.startswith("def ") or s in ("is_evidence_validated,", "is_evidence_validated") \
                    or s.startswith(("#", "-", '"', "'")):
                continue
            if "is_evidence_validated(" in s or ".is_evidence_validated" in s:
                callers.append(f"{p.name}:{i}: {s[:90]}")
    assert callers, (
        "`is_evidence_validated` 在 backend/app 内**零生产调用方**"
        "（仅 promotion.py 的定义与 evidence/__init__.py 的导出）。"
        "evidence authority 从未被任何生产代码查询。（F-2）"
    )


# ---------------------------------------------------------------------------
# F-4 / BUG-V3-049：退化空白 marker → 自信 exact
# ---------------------------------------------------------------------------


def _mk(*texts: str):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def test_whitespace_only_marker_yields_confident_exact() -> None:
    """退化输入鲁棒性：纯空白 marker text 拿到自信 `exact`。

    实测行为：`raw_hits` 用**原始** query（非规范化后），`"   " in "   "` 为真且
    恰 1 命中 → `exact`，指向那行纯空白。

    **不构成「不猜」违规**——是字面子串匹配如设计工作。
    违反的是「有效引用必须具有语义意义」。

    Owner 裁决（2026-09-13）：降级为输入质量问题，**延后到 preprocessing 阶段**——
    C-01 正在等 marker 质量 / source fidelity / role coverage 的生产事实，
    现在修这里可能是假问题。
    """
    lines = _mk("   ", "1. 题干", "A. 甲")
    payload = {
        "semantic_units": [
            {
                "unit_id": "U1",
                "shared_components": {
                    "material": {
                        "start_marker": {
                            "kind": "instruction_marker",
                            "granularity": "single_line",
                            "text": "   ",
                        }
                    }
                },
                "sub_questions": [],
            }
        ]
    }
    run = SourceResolver(source_version_id=SVID, lines=lines, figures=()).resolve(payload)
    mats = [s for s in run.resolved_spans if s.role == "material"]
    assert not mats or all(s.resolution_status != "exact" for s in mats), (
        f"退化纯空白 marker 不应拿到自信 exact；实际 = "
        f"{[(s.resolution_status, s.line_refs) for s in mats]}。（F-4）"
    )
