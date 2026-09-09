"""I-1-C — Prompt Contract 回归保护（不依赖真实模型，纯单测）。

I-0 真实根因：旧 prompt 只写「输出 semantic-metadata-annotation JSON」，从不把 Frozen
Annotation Contract 传给模型 → 真实 Qwen 输出栅栏 + schema 全盘漂移。本测试锁定 prompt
必须携带 contract（presence + strength 两层），防未来重构 prompt 时退化成「只说输出
JSON 却不喂 schema」。

Schema Source of Truth = Docs/V3_SPEC/20_Document_Pipeline.md（20 §4.1–4.5），非 test fixture。
"""

from app.domains.task.executor import build_annotation_prompt

_BODY = "1. 小明有 5 个苹果，又买了 3 个，一共有多少个苹果？"


def test_prompt_contains_required_fields() -> None:
    """Presence：prompt 必须包含顶层 + unit 字段名。"""
    prompt = build_annotation_prompt(_BODY)
    for field in (
        "document_metadata_claims",
        "sections",
        "semantic_units",
        "unit_id",
        "original_question_type",
        "content",
    ):
        assert field in prompt, f"prompt 缺少字段 {field}"


def test_prompt_enforces_json_only_no_fence() -> None:
    """Strength：JSON-only 约束 + 明确禁止 Markdown fence。"""
    prompt = build_annotation_prompt(_BODY)
    assert "只输出" in prompt  # JSON-only 约束
    assert "```json" in prompt  # 明确点名 fence 为禁止项（非仅「JSON」一词）


def test_prompt_contains_nested_schema_example() -> None:
    """Strength：一个完整 nested schema example（content.stem/options/answer 层级）。"""
    prompt = build_annotation_prompt(_BODY)
    for token in ('"content"', '"stem"', '"options"', '"answer"', '"role"'):
        assert token in prompt, f"prompt 的 schema example 缺少 {token}"


def test_prompt_interpolates_document_body() -> None:
    """正文注入：document 文本必须进入 prompt。"""
    prompt = build_annotation_prompt(_BODY)
    assert _BODY in prompt


def test_prompt_explanation_source_grounding() -> None:
    """独立 Prompt Contract 修复（不属 BUG-V3-038）：explanation 为 optional content role，
    仅当源中有【详解/解析】证据才声明；无证据必须省略字段，禁止凭空声明或占位。

    本测试只锁 prompt 文本契约（presence），不用字符串证明 LLM 服从——服从由
    live smoke / live probe 证明（无【详解】源 → Qwen 应省略 explanation → IR ready）。
    """
    prompt = build_annotation_prompt(_BODY)
    assert "explanation" in prompt
    assert "【详解】" in prompt  # source evidence 锚点
    assert "省略" in prompt  # omit when absent
    assert "凭空" in prompt  # do not invent
    assert "占位符" in prompt  # no placeholder for absent explanation
    # 只冻结 explanation 的 source grounding；不得顺手泛化到所有 optional 字段
    assert "【explanation 源证据约束】" in prompt
