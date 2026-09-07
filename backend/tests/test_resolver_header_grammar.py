"""H-3（BUG-V3-031）Header Grammar adversarial regression（纯函数，无 DB）。

冻结裁决（2026-09-07）：行首锚定 + 完整 token + 显式白名单；未命中一律正文。
完整 token 匹配，非 prefix substring。normalize 只消除格式差异（全角冒号 → 半角）。
"""

import pytest

from app.domains.resolver.match_normalization import (
    is_answer_header,
    is_explanation_header,
    normalize_text,
)


def _h(line: str) -> str:
    return normalize_text(line)


# ---------------------------------------------------------------- answer 正例
@pytest.mark.parametrize("line", [
    "答案",
    "答案：",
    "答案:",
    "参考答案",
    "参考答案：",
    "参考答案:",
    "【答案】",
    "【答案】1-5",
    " 答案：",   # 前导空白 normalize 后仍是 header
])
def test_answer_header_positive(line):
    assert is_answer_header(_h(line)), f"{line!r} 应为 Answer Header"


# ---------------------------------------------------------------- answer 负例
@pytest.mark.parametrize("line", [
    "请写出正确答案",
    "为什么这个答案错误",
    "本题答案如下",
    "答案可能是……",
    "参考答案如下",
    "参考答案见下文",
    "参考答案为 A",
    "试题答案",
    "答案与解析",
    "答案解析",
    "标准答案",
    "【答案】本题选择正确选项",
])
def test_answer_header_negative(line):
    assert not is_answer_header(_h(line)), f"{line!r} 不应为 Answer Header"


# ------------------------------------------------------------ explanation 正例
@pytest.mark.parametrize("line", [
    "详解",
    "详解：",
    "详解:",
    "解析",
    "解析：",
    "解析:",
    "解答",
    "解答：",
    "解答:",
    "【详解】",
    "【解析】",
    "【解答】",
    "【答案及解析】",
])
def test_explanation_header_positive(line):
    assert is_explanation_header(_h(line)), f"{line!r} 应为 Explanation Header"


# ------------------------------------------------------------ explanation 负例
@pytest.mark.parametrize("line", [
    "解析这个函数的定义域",
    "请解析下列图像",
    "为什么解析结果不同",
    "答案及解析如下",
])
def test_explanation_header_negative(line):
    assert not is_explanation_header(_h(line)), f"{line!r} 不应为 Explanation Header"


# ---------------------------------------------------------------- 端到端：不误判
def test_resolver_question_containing_answer_not_misjudged():
    """端到端（agent Finding 2 场景）：题干含「答案」不应误判为 answer header。

    修复前：`_answer_span` 把「请写出正确答案」当答案表头，answer 错指题干（exact）。
    修复后：题干含「答案」非 header → 无答案区 → answer missing（不产生错误 span）。
    """
    import uuid

    from app.domains.resolver.resolver import SourceResolver
    from app.domains.resolver.span import SourceLineView

    lines = tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(["1. 请写出正确答案", "2. 请写出正确答案"])
    )
    payload = {"semantic_units": [
        {"unit_id": "Q1", "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "1"},
                     "options": [{"label": "A"}, {"label": "B"}],
                     "answer": {"answer_zone": "answer_table", "question_number": "1"}}}]}
    run = SourceResolver(source_version_id=uuid.uuid4(), lines=lines).resolve(payload)
    answers = [s for s in run.resolved_spans if s.role == "answer"]
    assert answers == [], "题干含「答案」不应产生指向题干的 answer span（E 可以失败不能猜）"
