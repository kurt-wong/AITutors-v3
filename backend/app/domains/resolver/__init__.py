"""Source Resolver 域（段 E，20 §5）：Semantic Reference → Resolved Span/Relation。

纯确定性解析器（00 P2「位置解析 → Resolver」）：同输入同输出（Exact Replay 前提），
不落库、不调 LLM、不修改 annotation/sealed source、不从正文推导 reference。

核心安全边界（违反即停）：
    resolved ⇔ resolution_status ∈ {exact, normalized, contextual}
    status ∈ {fuzzy, ambiguous, missing, incomplete} ⇒ 无 ResolvedSpan

「E 可以失败，但不能猜」（00 §7 硬门槛 7）。
"""

# 20 §5.2 解析状态（7 态；incomplete 回 Annotation 聚焦重试，其余不 resolved 进
# pending_review 候选）。版本化供 build_versions（P7）。
RESOLVER_VERSION = "resolver/v1"

RESOLUTION_STATUS = frozenset(
    {"exact", "normalized", "contextual", "fuzzy", "ambiguous", "missing", "incomplete"}
)

# 可产生 ResolvedSpan 的状态（其余状态只产 unresolved_references）。
RESOLVED_STATUSES = frozenset({"exact", "normalized", "contextual"})

# span granularity（20 §5.5：line / line_character；M1 不做 table_cell/fragment）。
SPAN_GRANULARITIES = frozenset({"line", "line_character"})

# Semantic Reference kind（20 §4.4）。
REFERENCE_KINDS = frozenset(
    {
        "question_label",
        "option_label",
        "blank_label",
        "instruction_marker",
        "answer_zone",
        "explanation_zone",
        "image",
    }
)

# content role → 判定它是否 resolved 时「必须已具备唯一 span」的归属。仅诊断辅助。
CONTENT_ROLES = frozenset(
    {"stem", "option", "answer", "explanation", "material", "blank", "image"}
)
