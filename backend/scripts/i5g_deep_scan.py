"""I-5-G deep scan: substantive conflicts against the constitution.

Read-only. Goes beyond the marker-density scan in i5g_normative_scan.py, which
only checked *where* normative language appears. This script checks *what* the
new documents assert against what the Frozen Spec (00/10/20/30/40/50) actually
says, plus cross-document constraint conflicts.

Sections emitted:
  1. Citation graph + dangling-section check
  2. A-layer citation claims (citing line beside the cited section text)
  3. Architecture diagram inventory (Native vs Path B vs mixed)
  4. Status-field inventory vs the 82 section 10 baseline
  5. Constraint inventory grouped by subject (opposite-polarity conflicts)
  6. Key-term definition/use map

Nothing is modified. Findings are evidence for human adjudication, not verdicts.
The Frozen Spec volumes are read only; no byte of 00/10/20/30/40/50 is written.
"""
import collections
import os
import re

A_LAYER = {
    "00": "Docs/V3_SPEC/00_Master_Spec.md",
    "10": "Docs/V3_SPEC/10_Data_Model.md",
    "20": "Docs/V3_SPEC/20_Document_Pipeline.md",
    "30": "Docs/V3_SPEC/30_Task_LLM_Safety.md",
    "40": "Docs/V3_SPEC/40_Development_Rules.md",
    "50": "Docs/V3_SPEC/50_Migration_Assets.md",
}
NEW_DOC_ROOTS = ("Docs/V3_SPEC", "backend/Docs/V3_SPEC")
STATUS_FILES = ("restart-prompt.md", "Status.md")

CITE = re.compile(
    r"\b(00|10|20|30|40|50|6[0-9]|7[0-9]|8[0-9])\s*§\s*([0-9]+(?:\.[0-9]+)*)"
)
HEADING = re.compile(r"^(#{2,4})\s*(?:§\s*)?([0-9]+(?:\.[0-9]+)*)\b", re.MULTILINE)
MUST = re.compile(
    r"(必须|不得|禁止|只能|应当|shall|must(?:\s+not)?|MUST(?:\s+NOT)?)",
    re.IGNORECASE,
)
STATUS_LINE = re.compile(
    r"^\s*(?:\*\*)?Status(?:\*\*)?\s*[:：]\s*(.+)$", re.IGNORECASE | re.MULTILINE
)
PIPE = re.compile(
    r"(SealedSource|Source|preprocessing|Annotation|Resolver|Adapter|ResolvedRun|"
    r"IRBuilder|Compiler|Gate|Admission)\s*(?:→|->|↓|-->)\s*"
    r"(SealedSource|Source|preprocessing|Annotation|Resolver|Adapter|ResolvedRun|"
    r"IRBuilder|Compiler|Gate|Admission)"
)


def iter_new_docs():
    for root in NEW_DOC_ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for fn in sorted(filenames):
                if fn.endswith(".md"):
                    full = os.path.join(dirpath, fn)
                    yield os.path.relpath(full, ".").replace(os.sep, "/")
    for extra in STATUS_FILES:
        if os.path.exists(extra):
            yield extra


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def sections_of(path):
    if not os.path.exists(path):
        return None
    text = read(path)
    return {m.group(2): m.start() for m in HEADING.finditer(text)}


def section_text(path, sec, limit=420):
    text = read(path)
    heads = [(m.group(2), m.start()) for m in HEADING.finditer(text)]
    start = None
    for num, pos in heads:
        if num == sec:
            start = pos
            break
    if start is None:
        return None
    end = len(text)
    for num, pos in heads:
        if pos > start:
            end = pos
            break
    body = text[start:end].strip().splitlines()
    out, total = [], 0
    for ln in body:
        if total + len(ln) > limit:
            out.append("    ...")
            break
        out.append("    " + ln)
        total += len(ln)
    return "\n".join(out)


def sec1_citations(docs):
    print("\n" + "=" * 100)
    print("1. Citation graph + dangling-section check")
    print("=" * 100)
    a_secs = {k: sections_of(v) for k, v in A_LAYER.items()}
    dangling, by_target = [], collections.Counter()
    for doc in docs:
        text = read(doc)
        for m in CITE.finditer(text):
            vol, sec = m.group(1), m.group(2)
            by_target[f"{vol} SS{sec}"] += 1
            if vol in A_LAYER:
                if a_secs[vol] is None:
                    dangling.append((doc, 0, vol, sec, "volume file missing"))
                elif sec not in a_secs[vol]:
                    ln = text[: m.start()].count("\n") + 1
                    dangling.append((doc, ln, vol, sec, "section number absent"))
    print("\nMost-cited A-layer sections (top 25):")
    for tgt, n in by_target.most_common(25):
        print(f"  {n:>4}  {tgt}")
    print(f"\nDangling citations into A layer: {len(dangling)}")
    for doc, ln, vol, sec, why in dangling[:40]:
        print(f"  {doc}:{ln}  ->  {vol} SS{sec}  [{why}]")


def sec2_a_claims(docs):
    print("\n" + "=" * 100)
    print("2. A-layer citation claims (citing line beside cited section text)")
    print("=" * 100)
    print("\nLeft: how a new doc describes what A layer says.")
    print("Right: what that A-layer section actually contains.")
    print("A mismatch is a substantive-conflict candidate. Listed, not judged.")
    print("A-layer volumes citing each other are skipped: that is intra-constitutional.\n")
    a_paths = set(A_LAYER.values())
    shown = 0
    for doc in docs:
        if doc in a_paths:
            continue
        text = read(doc)
        for m in CITE.finditer(text):
            vol, sec = m.group(1), m.group(2)
            if vol not in A_LAYER or shown >= 40:
                continue
            target = section_text(A_LAYER[vol], sec)
            if target is None:
                continue
            ln = text[: m.start()].count("\n") + 1
            citing = text.splitlines()[ln - 1].strip()
            if len(citing) > 220:
                citing = citing[:220] + " ..."
            print(f"--- {doc}:{ln}")
            print(f"  CITING : {citing}")
            print(f"  {vol} SS{sec} ACTUAL:")
            print(target)
            print()
            shown += 1


def sec3_diagrams(docs):
    print("\n" + "=" * 100)
    print("3. Pipeline diagram inventory (Native / Path B / mixed)")
    print("=" * 100)
    print("\nRisk: architecture diagrams inside code blocks read as normative.")
    print("Highest risk is a MIXED diagram (Resolver AND Adapter/preprocessing")
    print("in one figure with no path label).\n")
    for doc in docs:
        text = read(doc)
        lines = text.splitlines()
        in_block, block, start = False, [], 0
        for i, ln in enumerate(lines, 1):
            if ln.strip().startswith("```"):
                if in_block:
                    body = "\n".join(block)
                    arrows = PIPE.findall(body)
                    if arrows:
                        nodes = set()
                        for a, b in arrows:
                            nodes.add(a)
                            nodes.add(b)
                        has_legacy = "Resolver" in nodes
                        has_pathb = "Adapter" in nodes or "preprocessing" in nodes
                        mixed = has_legacy and has_pathb
                        if mixed:
                            kind = "MIXED !"
                        elif has_pathb:
                            kind = "Path B"
                        else:
                            kind = "Native"
                        print(f"  [{kind:<8}] {doc}:{start}-{i}  nodes={sorted(nodes)}")
                    in_block, block, start = False, [], 0
                else:
                    in_block, block, start = True, [], i
            elif in_block:
                block.append(ln)


def sec4_status(docs):
    print("\n" + "=" * 100)
    print("4. Status-field inventory (against the 82 section 10 baseline)")
    print("=" * 100)
    print("\nEach new doc's self-declared Status. Anything contradicting 82 section 10")
    print("is a stale-D-layer or overreaching-B-layer candidate.\n")
    for doc in docs:
        text = read(doc)
        m = STATUS_LINE.search(text)
        if m:
            val = m.group(1).strip()
            if len(val) > 110:
                val = val[:110] + " ..."
            print(f"  {doc:<58} {val}")


SUBJECTS = [
    ("line_refs carrier", r"line_refs"),
    ("FORBIDDEN_FIELDS", r"FORBIDDEN_FIELDS"),
    ("Annotation bypass", r"[Bb]ypass"),
    ("Resolver duty", r"Resolver.{0,30}(搜索|校验|验证|search|verify)"),
    ("Adapter duty", r"Adapter"),
    ("preprocessing role", r"preprocessing"),
    ("Grammar input source", r"answer_text|Grammar\.verify"),
    ("strict-auto type set", r"STRICT_AUTO_TYPES|strict-auto"),
    ("Gate aggregation", r"聚合|父 Gate"),
    ("Evidence Contract", r"Evidence Contract"),
    ("Source as fact", r"[Ss]ource.{0,20}(事实|Fact)|Fact Authority|事实源"),
]


def sec5_constraints(docs):
    print("\n" + "=" * 100)
    print("5. Constraint inventory by subject (opposite-polarity conflicts)")
    print("=" * 100)
    print("\nSame subject carrying both 'must X' and 'must not X' is a conflict")
    print("candidate. Listed only.\n")
    for label, pat in SUBJECTS:
        rx = re.compile(pat)
        print(f"\n### subject: {label}")
        found = 0
        for doc in docs:
            text = read(doc)
            for i, ln in enumerate(text.splitlines(), 1):
                if rx.search(ln) and MUST.search(ln):
                    s = ln.strip()
                    if len(s) > 170:
                        s = s[:170] + " ..."
                    print(f"  {doc}:{i}")
                    print(f"      {s}")
                    found += 1
                    if found >= 14:
                        break
            if found >= 14:
                break
        if not found:
            print("  (no normative-tone hits)")


TERMS = [
    "ResolvedSpan", "ResolvedRun", "annotation_payload", "Source Binding Claim",
    "FORBIDDEN_FIELDS", "Validated Evidence", "Verified Evidence",
    "Evidence Contract", "canonical_question_type", "STRICT_AUTO_TYPES",
    "structural_regions", "Binding Carrier", "Mechanical Projection",
]


def sec6_terms(docs):
    print("\n" + "=" * 100)
    print("6. Key-term definition / use distribution")
    print("=" * 100)
    print("\n'definition site' = same line has 定义/定为/冻结为/指的是/:= ;")
    print("'use site' = every other occurrence. Heavy use with few definitions")
    print("is term-drift risk.\n")
    define_rx = re.compile(r"(定义|定为|冻结为|指的是|:=|denotes)")
    for term in TERMS:
        defs, uses = [], []
        for doc in docs:
            text = read(doc)
            for i, ln in enumerate(text.splitlines(), 1):
                if term in ln:
                    (defs if define_rx.search(ln) else uses).append(f"{doc}:{i}")
        print(f"  {term}")
        print(f"      define {len(defs):>3}  {defs[:4]}")
        print(f"      use    {len(uses):>3}  {uses[:6]}{' ...' if len(uses) > 6 else ''}")


def main():
    docs = list(iter_new_docs())
    print(f"Scanning {len(docs)} new docs + status files (A-layer volumes read-only)")
    sec1_citations(docs)
    sec2_a_claims(docs)
    sec3_diagrams(docs)
    sec4_status(docs)
    sec5_constraints(docs)
    sec6_terms(docs)


if __name__ == "__main__":
    main()
