"""Gate + Candidate + Admission domain constants.

UNIT_TYPES is the canonical Unit Type closed set (Owner D1 / 10 §5.2).
Single source of truth lives in compile (IR construction layer); gate re-exports
it so Gate boundary validation and IR construction cannot drift (F-M3-04 / M.3).
"""

from app.domains.compile import UNIT_TYPES

GATE_POLICY_VERSION = "admission-gate/v1"

# 10 §5.2 状态机值域（pending_review 唯一有出边；approved/rejected terminal）。
DECISION_STATUS = frozenset({"pending_review", "approved", "rejected"})

# 20 §8.4 + 用户裁决（2026-09-06）：strict-auto 只开放这三种基础题型 + composite 子题递归。
# fill_in/short_answer/essay/共享选项池（seven_to_five/vocabulary_fill 等）不开放。
STRICT_AUTO_TYPES = frozenset({"single_choice", "multiple_choice", "true_false"})

__all__ = [
    "UNIT_TYPES",
    "GATE_POLICY_VERSION",
    "DECISION_STATUS",
    "STRICT_AUTO_TYPES",
]
