"""Gate + Candidate + Admission domain constants.

UNIT_TYPES is the canonical Unit Type closed set (Owner D1 / 10 §5.2).
Single source of truth lives in compile (IR construction layer); gate re-exports
it so Gate boundary validation and IR construction cannot drift (F-M3-04 / M.3).
"""

from app.domains.compile import UNIT_TYPES

GATE_POLICY_VERSION = "admission-gate/v1"

# 10 §5.2 状态机值域（pending_review 唯一有出边；approved/rejected terminal）。
DECISION_STATUS = frozenset({"pending_review", "approved", "rejected"})

# HISTORICAL (T20-IMPLEMENT): type membership is no longer an admission gate.
# Owner R1/R2 — auto-publish is decided by source fidelity / ownership /
# answer_completeness / answer form, never by question-type whitelist.
# Kept as a frozen set only for audit scripts (gate_b044_coverage_measure)
# and BUG-044 regression tests. No runtime consumer in policy/admission.
STRICT_AUTO_TYPES = frozenset({"single_choice", "multiple_choice", "true_false"})

__all__ = [
    "UNIT_TYPES",
    "GATE_POLICY_VERSION",
    "DECISION_STATUS",
    "STRICT_AUTO_TYPES",
]
