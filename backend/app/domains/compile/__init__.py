"""Semantic Question IR + Deterministic Compiler 域（段 F，20 §6/§7）。

compile stage 的确定性收口：把段 E 的 ResolvedRun + annotation 装配成 IR（transient），
校验 20 §6.2 不变量 1-8，再编译成 CompiledSnapshot（10 §5.3 payload 结构，transient）。

边界（执行闸）：
- F 只装配不补语义：无 options reference 不从正文找；无 dependency 不自动挂载；
  无 answer span 不猜答案。Annotation 声明什么，E 解析什么，F 只装配什么。
- 三层状态不复用：E ResolvedStatus ≠ IR.semantic_status（F）≠ gate_decision（G）。
- text_hash raw（2c/2d）绝不经 canonical JSON；identity normalization 只用于三 key，
  不用于展示/compiled text。
"""

# 版本（build_versions 用，改规则即走 Rebuild）。
COMPILER_VERSION = "compiler/v1"
IR_SCHEMA_VERSION = "semantic-question-ir/v0.3"
IDENTITY_NORM_VERSION = "identity-norm/v1"

# DISPLAY_CONTRACT §0.2 12 种 canonical_question_type（直通，禁别名 resolver）。
CANONICAL_TYPES = frozenset(
    {
        "single_choice", "multiple_choice", "true_false", "fill_in", "short_answer",
        "essay", "cloze", "reading", "grammar_fill", "vocabulary_fill",
        "seven_to_five", "reading_expression",
    }
)

# Owner D1 / 10 §5.2 canonical Unit Type closed set.
# Question Type ⟂ Unit Type（正交；无 canonical QT→UT mapping）。
# IR construction + Gate boundary 共用此值域（F-M3-04 / M.3）。
UNIT_TYPES = frozenset({"standalone_unit", "composite_unit"})

# 20 §6.2 IR.semantic_status 值域（BUG-V3-018 终裁 → X2.6 M.2 解冻）。
# M.2 (X2.6-OD-D9-01 + IMPL-AUTH-01): 增加 "unknown" — semantic state / IR expression，
# 不等于 UNKNOWN migration。旧 IR 无 unknown 值时 ready/incomplete 逻辑不变。
# unknown 不进 compiler leaves；unknown 不进 production mapping / migration。
SEMANTIC_STATUS = frozenset({"ready", "incomplete", "unknown"})

# content role 必需性值域（20 §6.1 示例 + DISPLAY_CONTRACT §0.2；per-type 未集中冻结
# → BUG-V3-016 保守映射）。
ROLE_REQUIREMENT = frozenset(
    {"required", "required_for_choice", "optional", "not_applicable"}
)

# options=required 的 canonical 题型（DISPLAY_CONTRACT §0.2 选项要求 required / 固定 2）。
_CHOICE_TYPES = frozenset({"single_choice", "multiple_choice", "true_false"})


def map_canonical_type(original: str) -> str | None:
    """20 §7.2.2 canonical 映射：canonical exact passthrough；未知 → None（→incomplete）。

    禁实现 alias resolver（BUG-V3-014）："single-choice"/"单选题" 等不映射。
    """
    if original in CANONICAL_TYPES:
        return original
    return None


def content_roles_for(canonical_type: str | None) -> dict[str, str]:
    """content role 必需性（保守可确定，BUG-V3-016；stem/answer required、explanation
    optional 通用；options 按 DISPLAY_CONTRACT 选项要求）。"""
    roles: dict[str, str] = {"stem": "required", "answer": "required", "explanation": "optional"}
    if canonical_type is None:
        return roles
    roles["options"] = (
        "required_for_choice" if canonical_type in _CHOICE_TYPES else "not_applicable"
    )
    return roles
