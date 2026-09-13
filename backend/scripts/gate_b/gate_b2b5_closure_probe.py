"""B2-B5 Closure: latent Evidence Admission Boundary verification (doc 74 §6.3).

Question: does a strict-auto (single_choice) answer span that sits INSIDE the
answer structural region, but whose content carries an explanation-like prefix
plus an option letter, still reach auto_approve?

Defense layers expected to fire:
  L1 grammar-None          — only for non-strict-auto types (does NOT apply here)
  L2 structural overlap    — only fires when answer span falls into
                             explanation/question region (does NOT apply: the
                             span is legitimately inside the answer region)
  L3 Evidence Promotion    — Phase 1 is additive-only event logging; it does not
                             add a new admission predicate

If the result is auto_approve, the latent weakness is still OPEN and must be
recorded honestly in the B2-B5 Closure verdict rather than papered over.
"""

from __future__ import annotations

import os
import sys
import uuid

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate import grammar as gate_grammar
from app.domains.gate.policy import evaluate
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f2")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a2")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(ctype="single_choice"):
    return {
        "semantic_units": [
            {
                "unit_id": "Q1",
                "original_question_type": ctype,
                "content": {
                    "stem": {"question_label": "1"},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": "1",
                    },
                },
            }
        ]
    }


def _run(lines, payload, root_unit_id="Q1"):
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    lines_by_ref = {l.line_ref: l for l in lines}
    compiled = Compiler(spans, lines_by_ref).compile(ir)
    root = next(u for u in ir.units if u.unit_id == root_unit_id)
    return root, ir, compiled, run


def _describe(tag, d, run, compiled):
    regions = [(r.role, r.line_refs) for r in run.structural_regions]
    print(f"\n===== {tag} =====")
    print(f"decision        : {d['decision']}")
    print(f"structural      : {d['layers']['structural']['status']}")
    print(f"provenance      : {d['layers']['provenance']['status']}")
    print(f"provenance auto : {d['layers']['provenance'].get('auto_allowed')}")
    print(f"semantic        : {d['layers']['semantic']['status']}")
    print(f"regions         : {regions}")
    print(f"reasons         : {d['reasons']}")
    return d


def case_baseline_clean():
    """Control: answer region holds a plain letter."""
    lines = _mk(
        "1. which fruit",
        "A. apple", "B. banana", "C. car", "D. table",
        "答案",
        "1. A",
    )
    return _run(lines, _payload())


def case_explanation_prefix_in_answer_region():
    """Attack: explanation-like prefix + option letter inside the ANSWER region."""
    lines = _mk(
        "1. which fruit",
        "A. apple", "B. banana", "C. car", "D. table",
        "答案",
        "1. 【解答】A",
    )
    return _run(lines, _payload())


def case_rich_explanation_prefix_in_answer_region():
    """Attack variant: longer explanation prose + option letter in ANSWER region."""
    lines = _mk(
        "1. which fruit",
        "A. apple", "B. banana", "C. car", "D. table",
        "答案",
        "1. 【考点】本题考查词义辨析。【解答】A",
    )
    return _run(lines, _payload())


def case_explanation_header_present_control():
    """Control: explanation content sits under a real 详解 header (region map fires)."""
    lines = _mk(
        "1. which fruit",
        "A. apple", "B. banana", "C. car", "D. table",
        "答案",
        "1. A",
        "详解",
        "1. 【解答】A",
    )
    return _run(lines, _payload())


GRAMMAR_BOUNDARY = [
    ("clean", "A"),
    ("qn prefix", "1. A"),
    ("solution bracket", "【解答】A"),
    ("kao dian + jie da", "【考点】本题考查词义辨析。【解答】A"),
    ("argues against A, picks B", "1. 【解答】不选A，应选B"),
    ("single wrong letter", "1. 见解析A页"),
    ("letter in prose only", "1. 参见教材A册第三章"),
    ("true_false clean", "对"),
    ("true_false bracket", "【解答】对"),
]


def grammar_boundary_report():
    print("\n\n===== GRAMMAR BOUNDARY (single/multiple/true_false) =====")
    rows = []
    for tag, text in GRAMMAR_BOUNDARY:
        sc = gate_grammar.verify("single_choice", text, ("A", "B", "C", "D"))
        mc = gate_grammar.verify("multiple_choice", text, ("A", "B", "C", "D"))
        tf = gate_grammar.verify("true_false", text, ())
        rows.append({"case": tag, "text": text, "single_choice": sc,
                     "multiple_choice": mc, "true_false": tf})
        print(f"  {tag:28} sc={sc!s:5} mc={mc!s:5} tf={tf!s:5}  {text!r}")
    return rows


def main():
    print("doc 74 §6.3 latent Evidence Admission Boundary — decisive probe")
    grammar_boundary_report()
    print("\ngrammar sanity:")
    print("  verify(sc, 'A')            ->", gate_grammar.verify("single_choice", "A", ("A", "B")))
    print("  verify(sc, '【解答】A')    ->", gate_grammar.verify("single_choice", "【解答】A", ("A", "B")))
    print("  verify(sc, '【考点】...A') ->", gate_grammar.verify(
        "single_choice", "【考点】本题考查词义辨析。【解答】A", ("A", "B")))

    results = {}
    for tag, fn in [
        ("C0 baseline clean '1. A'", case_baseline_clean),
        ("C1 '1. 【解答】A' in answer region", case_explanation_prefix_in_answer_region),
        ("C2 rich '【考点】...【解答】A' in answer region", case_rich_explanation_prefix_in_answer_region),
        ("C3 explanation under real 详解 header", case_explanation_header_present_control),
    ]:
        root, ir, compiled, run = fn()
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        results[tag] = _describe(tag, d, run, compiled)

    print("\n\n===== VERDICT =====")
    for tag, d in results.items():
        print(f"  {d['decision']:>15}  <- {tag}")

    weak = [
        tag for tag, d in results.items()
        if d["decision"] == "auto_approve" and ("【解答】" in tag or "【考点】" in tag)
    ]
    if weak:
        print("\n*** LATENT WEAKNESS STILL OPEN ***")
        print("   These explanation-prefixed answer spans reached auto_approve:")
        for t in weak:
            print(f"     - {t}")
    else:
        print("\n*** No explanation-prefixed answer span reached auto_approve ***")


if __name__ == "__main__":
    main()
