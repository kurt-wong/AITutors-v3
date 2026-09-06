"""Gate + Candidate + Admission 域（段 G，20 §8 / 10 §5.2-5.4）。

gate 判定只产 pass/fail + reasons（gate_decision），不修改 content、不做语义猜测；
decision_status 只经 approve()/reject() 唯一入口（P0-G-001，application-level
enforcement，不加 ORM event / DB trigger/RLS）。
"""

GATE_POLICY_VERSION = "admission-gate/v1"

# 10 §5.2 状态机值域（pending_review 唯一有出边；approved/rejected terminal）。
DECISION_STATUS = frozenset({"pending_review", "approved", "rejected"})

# 20 §8.4 + 用户裁决（2026-09-06）：strict-auto 只开放这三种基础题型 + composite 子题递归。
# fill_in/short_answer/essay/共享选项池（seven_to_five/vocabulary_fill 等）不开放。
STRICT_AUTO_TYPES = frozenset({"single_choice", "multiple_choice", "true_false"})

# unit_type 值域（10 §5.2）。
UNIT_TYPES = frozenset({"standalone_unit", "composite_unit"})
