"""BUG-V3-044 — AnswerTokenContract real-corpus coverage measurement.

回答一个问题：白名单收紧后，真实语料里 strict-auto 题型的答案文本
有多少仍能通过 grammar（保持 auto_approve 能力），有多少落到 pending_review？

对照旧实现（_option_letters 抽任意 ASCII 字母）与新实现（白名单），
输出通过率差异与失败样本，供裁决者判断是否需要扩展允许形态。

实验 Harness——不修改生产代码。
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
import uuid
from collections import Counter
from dataclasses import dataclass

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from app.domains.gate import STRICT_AUTO_TYPES
from app.domains.gate import grammar as g
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

CORPUS = "D:/Project/Papers/Ocr-markdown"

# 旧实现复刻：抽任意 ASCII 字母（BUG-V3-044 修复前行为）
_OLD_LETTER_RE = re.compile(r"[A-Za-z]")


def _old_letters(answer_text: str) -> tuple[str, ...]:
    cleaned = g._clean_answer(answer_text)
    return tuple(m.group(0).upper() for m in _OLD_LETTER_RE.finditer(cleaned))


def _old_verify(ctype: str, answer_text: str, labels) -> bool | None:
    if ctype not in STRICT_AUTO_TYPES:
        return None
    if ctype == "true_false":
        return g._verify_true_false(g._clean_answer(answer_text))
    letters = _old_letters(answer_text)
    if ctype == "single_choice":
        if len(letters) != 1:
            return None
        return True if letters[0] in labels else None
    if not letters:
        return None
    return True if set(letters) <= labels else None


@dataclass
class Sample:
    case_id: str
    unit_id: str
    ctype: str
    answer_text: str


def load_cases():
    cases = []
    for mp in sorted(glob.glob(f"{CORPUS}/**/*.manifest.json", recursive=True)):
        with open(mp, encoding="utf-8") as f:
            manifest = json.load(f)
        src = manifest.get("source_file", "")
        md = src if src and os.path.exists(src) else mp.replace(".manifest.json", ".md")
        if not os.path.exists(md):
            continue
        with open(md, encoding="utf-8") as f:
            md_lines = f.readlines()
        max_line = 0
        for u in manifest.get("units", []):
            for fn in ("stem_lines", "options_lines", "answer_lines", "explanation_lines"):
                val = u.get(fn)
                if val and isinstance(val, list) and len(val) == 2 and isinstance(val[1], int):
                    max_line = max(max_line, val[1])
        if max_line > len(md_lines):
            continue
        cases.append((os.path.basename(mp).replace(".manifest.json", ""), md_lines, manifest))
    return cases


def build_payload_and_lines(md_lines, manifest):
    """构造 Resolver 可用的 annotation payload + SourceLineView。"""
    units = []
    for mu in manifest.get("units", []):
        qn = mu.get("question_numbers", [None])[0]
        qn_str = str(qn) if qn is not None else ""
        if not qn_str:
            continue
        ctype = mu.get("original_question_type", "single_choice")
        content = {"stem": {"question_label": qn_str}}
        if mu.get("answer_lines"):
            content["answer"] = {"answer_zone": "answer_table", "question_label": qn_str}
        if mu.get("options_lines"):
            content["options"] = [{"label": lb} for lb in ("A", "B", "C", "D", "E", "F")]
        units.append({
            "unit_id": mu.get("unit_id", "?"),
            "original_question_type": ctype,
            "content": content,
        })
    if not units:
        return None, None
    payload = {"semantic_units": units}
    lines = tuple(
        SourceLineView(f"P1L{i + 1:03d}", t.rstrip("\n"), i + 1, 1, i + 1)
        for i, t in enumerate(md_lines)
    )
    return payload, lines


def main():
    cases = load_cases()
    print(f"corpus cases loaded: {len(cases)}")

    stats: Counter = Counter()
    by_ctype: dict[str, Counter] = {}
    regressions: list[Sample] = []
    new_only_pass = 0

    for case_id, md_lines, manifest in cases:
        payload, lines = build_payload_and_lines(md_lines, manifest)
        if not payload:
            continue
        try:
            run = SourceResolver(source_version_id=uuid.uuid4(), lines=lines).resolve(payload)
        except Exception:
            stats["resolver_error"] += 1
            continue

        ctype_by_unit = {u["unit_id"]: u["original_question_type"]
                         for u in payload["semantic_units"]}
        line_by_ref = {l.line_ref: l for l in lines}

        for span in run.resolved_spans:
            if span.role != "answer" or span.resolution_status not in ("exact", "normalized"):
                continue
            # span_id 形如 "sp-{unit_id}.answer"（reference.py:212）
            unit_id = span.span_id[3:].rsplit(".answer", 1)[0]
            ctype = ctype_by_unit.get(unit_id, "single_choice")
            if ctype not in STRICT_AUTO_TYPES:
                continue
            ref = span.line_refs[0] if span.line_refs else None
            text = line_by_ref[ref].text if ref and ref in line_by_ref else ""

            labels = tuple("ABCDEF")
            old_ok = _old_verify(ctype, text, labels) is True
            new_ok = g.verify(ctype, text, labels) is True

            stats["total"] += 1
            bc = by_ctype.setdefault(ctype, Counter())
            bc["total"] += 1
            if old_ok:
                stats["old_pass"] += 1
                bc["old_pass"] += 1
            if new_ok:
                stats["new_pass"] += 1
                bc["new_pass"] += 1
            if new_ok and not old_ok:
                new_only_pass += 1
            if old_ok and not new_ok:
                stats["regression"] += 1
                bc["regression"] += 1
                if len(regressions) < 40:
                    regressions.append(Sample(case_id, unit_id, ctype, text))

    total = max(stats["total"], 1)
    print("\n===== AnswerTokenContract coverage impact (strict-auto only) =====")
    print(f"total resolved answer spans : {stats['total']}")
    print(f"old (_option_letters) pass  : {stats['old_pass']}  ({stats['old_pass'] / total:.1%})")
    print(f"new (whitelist) pass        : {stats['new_pass']}  ({stats['new_pass'] / total:.1%})")
    print(f"regressions (old→pending)   : {stats['regression']}")
    print(f"new-only pass (unexpected)  : {new_only_pass}")

    print("\n----- by canonical type -----")
    for ctype, bc in sorted(by_ctype.items()):
        t = max(bc["total"], 1)
        print(f"  {ctype:16} total={bc['total']:5}  "
              f"old={bc['old_pass']:5} ({bc['old_pass'] / t:6.1%})  "
              f"new={bc['new_pass']:5} ({bc['new_pass'] / t:6.1%})  "
              f"regress={bc['regression']:5}")

    if regressions:
        print("\n----- regression samples (old True → new None) -----")
        for s in regressions:
            print(f"  [{s.ctype}] {s.answer_text!r}   ({s.case_id} / {s.unit_id})")
    else:
        print("\n*** No regressions on real corpus — whitelist costs nothing ***")


if __name__ == "__main__":
    main()
