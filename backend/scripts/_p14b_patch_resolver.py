"""Patch Resolver label recognition — P1.4-B Rules B/C + Rule A trailing fallback."""
from pathlib import Path

# --- match_normalization._line_has_option_token ---
p1 = Path(r"D:\Project\AITutors-v3\backend\app\domains\resolver\match_normalization.py")
s = p1.read_text(encoding="utf-8")
old = '''def _line_has_option_token(normalized_line: str, label: str) -> bool:
    """选项形态匹配（M1 保守）：行首「A.」/「A、」/「(A)」等。禁匹配正文随机大写。

    分隔符含全角/半角逗号：normalize 会把 `，` 折成 `,`，两侧都要认
    （U44-46 `D，物种减少`）。
    """
    if re.match(rf"^{re.escape(label)}\\s*[.．、:，,)）]", normalized_line):
        return True
    if re.match(rf"^[（(]{re.escape(label)}[)）]", normalized_line):
        return True
    return False
'''
new = '''def _line_has_option_token(normalized_line: str, label: str) -> bool:
    """选项形态匹配（M1 保守）：行首「A.」/「A、」/「(A)」等。禁匹配正文随机大写。

    分隔符含全角/半角逗号：normalize 会把 `，` 折成 `,`，两侧都要认
    （U44-46 `D，物种减少`）。

    P1.4-B Rule B：digit-glued `2D.` — 行内/行首 `数字+标签+分隔`（数学 Q4）。
    P1.4-B Rule C：line-start `D 麦哲伦` — 标签+空白+CJK，无分隔符（历史 Q29）。
    仍禁：正文 `B 是 1945…`（后随 是/有/在 等散文连接词）。
    """
    if re.match(rf"^{re.escape(label)}\\s*[.．、:，,)）]", normalized_line):
        return True
    if re.match(rf"^[（(]{re.escape(label)}[)）]", normalized_line):
        return True
    # Rule B: digit-glued (normalize folds fullwidth; digits stay)
    if re.search(rf"(?<![A-Za-z0-9_])\\d{re.escape(label)}\\s*[.．、:，,)）]", normalized_line):
        return True
    # Rule C: line-start letter + space + CJK, not ordinary prose
    if re.match(rf"^{re.escape(label)}[ \\u00a0]+[\\u4e00-\\u9fff]", normalized_line):
        if not re.match(
            rf"^{re.escape(label)}[ \\u00a0]+(?:是|有|在|了|和|与|或|被|把|对|从|到|为|要|会|能|可|这|那|其|年|月|日)",
            normalized_line,
        ):
            return True
    return False
'''
if old not in s:
    print("match_norm old not found")
    i = s.find("def _line_has_option_token")
    print(s[i:i+500])
else:
    s = s.replace(old, new, 1)
    p1.write_text(s, encoding="utf-8")
    print("patched match_normalization._line_has_option_token")

# --- resolver._LABEL_RE / _label_offsets ---
p2 = Path(r"D:\Project\AITutors-v3\backend\app\domains\resolver\resolver.py")
s = p2.read_text(encoding="utf-8")
old = '''# 行内选项标签（bounded，防 "对A项" 误配随机大写；需标签+分隔符）。
# 全角逗号 `，`：真实卷 `C. 水土流失 D，物种减少`（U44-46）。格式兼容，非 heuristic。
_LABEL_RE = re.compile(r"(?<![\\w])([A-Ha-h])\\s*[.．、:，,)）]")


def _label_offsets(text: str, label: str) -> list[int]:
    return [
        m.start() for m in _LABEL_RE.finditer(text)
        if m.group(1).upper() == label.upper()
    ]
'''
new = '''# 行内选项标签（bounded，防 "对A项" 误配随机大写；需标签+分隔符）。
# 全角逗号 `，`：真实卷 `C. 水土流失 D，物种减少`（U44-46）。格式兼容，非 heuristic。
_LABEL_RE = re.compile(r"(?<![\\w])([A-Ha-h])\\s*[.．、:，,)）]")
# P1.4-B Rule B：digit-glued `2D.`（数学 Q4）。clean lookbehind `(?<![\\w])` 会因
# 前置 `2` 而漏检，故单独识别。NOT `2\\cos…`（字母后无分隔符）。
_LABEL_DIGIT_GLUE_RE = re.compile(r"(?<![A-Za-z0-9_])(\\d)([A-Ha-h])\\s*[.．、:，,)）]")
# P1.4-B Rule C：line-start `D 麦哲伦`（历史 Q29），缺分隔符。
_LABEL_SPACE_SEP_RE = re.compile(r"^(?:[ \\u00a0]*)([A-Ha-h])[ \\u00a0]{1,3}(?=[\\u4e00-\\u9fff])")
_LABEL_SPACE_SEP_PROSE = re.compile(
    r"^[ \\u00a0]*[A-Ha-h][ \\u00a0]+(?:是|有|在|了|和|与|或|被|把|对|从|到|为|要|会|能|可|这|那|其|年|月|日)"
)


def _label_offsets(text: str, label: str) -> list[int]:
    """Char offsets of option-label tokens for `label` in `text` (Rules A-C forms)."""
    offs: list[int] = []
    for m in _LABEL_RE.finditer(text):
        if m.group(1).upper() == label.upper():
            offs.append(m.start())
    for m in _LABEL_DIGIT_GLUE_RE.finditer(text):
        if m.group(2).upper() == label.upper():
            offs.append(m.start(2))
    if not _LABEL_SPACE_SEP_PROSE.search(text):
        for m in _LABEL_SPACE_SEP_RE.finditer(text):
            if m.group(1).upper() == label.upper():
                offs.append(m.start(1))
    return sorted(set(offs))
'''
if old not in s:
    print("resolver old not found")
    i = s.find("_LABEL_RE")
    print(s[i-80:i+400])
else:
    s = s.replace(old, new, 1)
    p2.write_text(s, encoding="utf-8")
    print("patched resolver._LABEL_RE / _label_offsets")
