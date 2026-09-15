"""架构契约缺口证明（spec_gap）— **不进正常 CI gate**。

本目录存放「当前契约未闭环」的对抗性证明，按 Owner 2026-09-13 裁决分层：

  产品契约测试（F-3/F-5/F-6）→ 留在 tests/ 根，FAIL → 修复 → PASS
  架构审查测试（F-2）        → **已闭合**（EB-008 落地，见 test_eb008_evidence_authority.py）
  输入鲁棒性（F-4）          → 本目录，module 级 xfail，延后 preprocessing 阶段
  测试基础设施（F-1）        → 单独立项 TEST-INFRA-01

`testpaths = ["tests"]` 会递归收集子目录，**仅分目录不足以排除**，
故配 module 级 `pytestmark = pytest.mark.xfail`：`pytest -q` 记为 xfailed（非 failed）。

对应登记：bugs.md BUG-V3-049（F-4）。（BUG-V3-048 F-2 已由 EB-008 闭合。）
"""

import pathlib
import uuid

import pytest

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

pytestmark = pytest.mark.xfail(
    reason="架构契约缺口证明（非 CI gate）— 见 bugs.md BUG-V3-049",
    strict=False,
)

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000e")

_APP_ROOT = pathlib.Path(__file__).resolve().parents[2] / "app"


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
