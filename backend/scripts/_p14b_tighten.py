from pathlib import Path

# --- Producer: tighten DIGIT_GLUE and Rule A prose reject ---
p = Path(r"D:\Project\Papers\scripts\reslice_pipeline.py")
s = p.read_text(encoding="utf-8")

old_re = '''_OPT_DIGIT_GLUE_RE = re.compile(r"(?<![A-Za-z0-9_])(\\d)([A-Ha-h])\\s*[.．、:，。)）]")'''
new_re = '''# Uppercase + period-like separator only: `2D.` yes; `2a)` / `2\\cos` no.
_OPT_DIGIT_GLUE_RE = re.compile(r"(?<![A-Za-z0-9_])(\\d)([A-H])\\s*[.．、]")'''
if old_re not in s:
    print("digit glue re not found", s[s.find("_OPT_DIGIT_GLUE_RE"):s.find("_OPT_DIGIT_GLUE_RE")+120])
else:
    s = s.replace(old_re, new_re, 1)
    print("tightened DIGIT_GLUE")

# Rule A: skip prose lines entirely
old_a = '''        if not _looks_option_like_content(text):
            continue
        # content must not carry a clean/glue label token (those were pass 1-3)
        if _OPT_LABEL_RE.search(text) or _OPT_DIGIT_GLUE_RE.search(text):
            continue
        if _OPT_SPACE_SEP_RE.search(text) and not _SPACE_SEP_PROSE.search(text):
            continue'''
new_a = '''        if not _looks_option_like_content(text):
            continue
        # content must not carry a clean/glue label token (those were pass 1-3)
        if _OPT_LABEL_RE.search(text) or _OPT_DIGIT_GLUE_RE.search(text):
            continue
        # Rule C prose (`B 是 1945…`) is NOT option content — do not trailing-bind it
        if _SPACE_SEP_PROSE.search(text):
            continue
        if _OPT_SPACE_SEP_RE.search(text):
            continue'''
if old_a not in s:
    print("rule A block not found")
else:
    s = s.replace(old_a, new_a, 1)
    print("tightened Rule A prose reject")

p.write_text(s, encoding="utf-8")

# --- Resolver: same DIGIT_GLUE tighten ---
p2 = Path(r"D:\Project\AITutors-v3\backend\app\domains\resolver\resolver.py")
s = p2.read_text(encoding="utf-8")
old = '''_LABEL_DIGIT_GLUE_RE = re.compile(r"(?<![A-Za-z0-9_])(\\d)([A-Ha-h])\\s*[.．、:，,)）]")'''
new = '''_LABEL_DIGIT_GLUE_RE = re.compile(r"(?<![A-Za-z0-9_])(\\d)([A-H])\\s*[.．、]")'''
if old not in s:
    print("resolver glue not found")
else:
    s = s.replace(old, new, 1)
    p2.write_text(s, encoding="utf-8")
    print("tightened resolver DIGIT_GLUE")

# Resolver Rule A: skip prose
old = '''            if _LABEL_SPACE_SEP_RE.search(text) and not _LABEL_SPACE_SEP_PROSE.search(text):
                continue
            if re.match(r"^\\d+\\s*[.．、\\\\]", t):
                continue
            return l.line_ref'''
new = '''            if _LABEL_SPACE_SEP_PROSE.search(text):
                continue
            if _LABEL_SPACE_SEP_RE.search(text):
                continue
            if re.match(r"^\\d+\\s*[.．、\\\\]", t):
                continue
            return l.line_ref'''
if old not in s:
    print("resolver rule A not found")
else:
    s = s.replace(old, new, 1)
    p2.write_text(s, encoding="utf-8")
    print("tightened resolver Rule A")
