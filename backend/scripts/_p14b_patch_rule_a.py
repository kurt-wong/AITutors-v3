"""Add Rule A trailing-content fallback to Resolver._locate_options."""
from pathlib import Path

p = Path(r"D:\Project\AITutors-v3\backend\app\domains\resolver\resolver.py")
s = p.read_text(encoding="utf-8")

old = '''            # 无行首选项：尝试在前一个选项行（同物理行多选项）bounded inline。
            if cursor_ref is not None:
                line = self._idx.get(cursor_ref)
                offs = [o for o in _label_offsets(line.text, lab) if o >= cursor_end]
                if len(offs) == 1:
                    found[lab] = ("inline", cursor_ref, offs[0], offs[0] + len(lab))
                    cursor_end = offs[0] + len(lab)
                    continue
            found[lab] = ("incomplete",)
        return found
'''
new = '''            # 无行首选项：尝试在前一个选项行（同物理行多选项）bounded inline。
            if cursor_ref is not None:
                line = self._idx.get(cursor_ref)
                offs = [o for o in _label_offsets(line.text, lab) if o >= cursor_end]
                if len(offs) == 1:
                    found[lab] = ("inline", cursor_ref, offs[0], offs[0] + len(lab))
                    cursor_end = offs[0] + len(lab)
                    continue
            # P1.4-B Rule A: trailing unlabeled option content after last located
            # option (Chem Q23 `D．` dropped). Source-local only: content line
            # inside the option region, no label token, next sequential letter.
            trailing = self._trailing_unlabeled_option_line(
                labels, found, cursor_seq, region_upper
            )
            if trailing is not None:
                found[lab] = ("ok", trailing)
                cursor_seq = self._idx.seq_of(trailing)
                cursor_ref = trailing
                cursor_end = 0
                continue
            found[lab] = ("incomplete",)
        return found

    def _trailing_unlabeled_option_line(self, labels, found, cursor_seq, region_upper):
        """Rule A: first option-like content line after last located option with no label token.

        Only used for the next sequential missing letter. Never scans outside the
        option region (region_upper / cursor). Never uses answer evidence.
        """
        if not labels:
            return None
        # next expected letter among declared labels not yet found
        missing = [lab for lab in labels if lab not in found or found[lab][0] == "incomplete"]
        if not missing:
            return None
        want = missing[0]
        # sequential: want must be the next letter after the highest found label
        found_ok = [lab for lab in labels if lab in found and found[lab][0] in ("ok", "inline")]
        if found_ok:
            nxt = chr(ord(max(found_ok)) + 1)
            if want != nxt:
                return None
        else:
            if want != "A":
                return None
        for l in self._idx.lines:
            if l.seq <= cursor_seq:
                continue
            if region_upper is not None and l.seq >= region_upper:
                break
            text = l.text
            t = text.strip()
            if not t or len(t) < 4:
                continue
            if t.startswith("<") or t.startswith("#") or t.startswith("---"):
                continue
            if _LABEL_RE.search(text) or _LABEL_DIGIT_GLUE_RE.search(text):
                continue
            if _LABEL_SPACE_SEP_RE.search(text) and not _LABEL_SPACE_SEP_PROSE.search(text):
                continue
            if re.match(r"^\\d+\\s*[.．、\\\\]", t):
                continue
            return l.line_ref
        return None
'''
if old not in s:
    print("OLD not found")
    i = s.find("found[lab] = (\"incomplete\",)")
    print(repr(s[i-300:i+80]))
else:
    s = s.replace(old, new, 1)
    # ensure re is imported in resolver
    if "\nimport re\n" not in s and "\nimport re " not in s:
        # check
        if "import re" not in s:
            s = s.replace("from __future__ import annotations\n",
                          "from __future__ import annotations\n\nimport re\n", 1)
            print("added import re")
    p.write_text(s, encoding="utf-8")
    print("patched _locate_options Rule A fallback")
