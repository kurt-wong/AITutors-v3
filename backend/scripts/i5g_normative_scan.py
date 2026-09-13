"""I-5-G: mechanical normative-language scan across the V3 doc tree.

Read-only. Classifies each doc by the 82 section 1.2 authority layer and counts
normative markers per file. Emits a table sorted by density within layer, plus
a Gate-status-line distribution for reconciliation against 82 section 3.

Not a pipeline measurement script: it reads Markdown only and touches no
application code, database, or test corpus.
"""
import collections
import os
import re

MARKERS = [
    r"\bmust\b", r"\bshall\b", r"\brequired\b",
    r"必须", r"不得", r"只能", r"唯一", r"权威", r"冻结",
    r"\bCLOSED\b", r"\bPASS\b", r"\bBLOCKED\b", r"\bDEFERRED\b",
    r"architecture", r"contract", r"invariant",
]
PAT = re.compile("|".join(MARKERS), re.IGNORECASE)


# 82 section 1.2 authority layers. B is an explicit allowlist: a number lands in
# B only by being a Decision Record. Everything else in the numbered phase-doc
# range is C unless it is one of the Frozen Spec volumes 00-50.
B_LAYER = re.compile(r"^(67|69|70|75|80|81|82)_")
C_LAYER = re.compile(r"^(6[0-6]|68|7[1-4]|7[6-9]|8[3-9])_")


def layer_of(name: str) -> str:
    if name == "README.md" or re.match(r"^(00|10|20|30|40|50)_", name):
        return "A-FrozenSpec"
    if B_LAYER.match(name):
        return "B-DecisionRecord"
    if C_LAYER.match(name):
        return "C-PhaseReport"
    if name in ("restart-prompt.md", "Status.md", "log.md"):
        return "D-Status"
    return "UNCATEGORISED"


def scan_file(path: str):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    hits = [i + 1 for i, ln in enumerate(lines) if PAT.search(ln)]
    return len(lines), len(hits), hits


def main():
    rows = []
    for root in ("Docs/V3_SPEC", "backend/Docs/V3_SPEC"):
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for fn in filenames:
                if not fn.endswith(".md"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ".").replace(os.sep, "/")
                nl, nh, hits = scan_file(full)
                rows.append((rel, layer_of(fn), nl, nh, hits))

    for extra in ("restart-prompt.md", "Status.md", "log.md"):
        if os.path.exists(extra):
            nl, nh, hits = scan_file(extra)
            rows.append((extra, layer_of(extra), nl, nh, hits))

    by_layer = collections.defaultdict(list)
    for rel, layer, nl, nh, hits in rows:
        dens = round(100.0 * nh / max(nl, 1), 1)
        by_layer[layer].append((rel, nl, nh, dens, hits))

    hdr = f"{'LAYER':<18} {'DOC':<56} {'LINES':>6} {'HITS':>5} {'DENS%':>7}"
    print(hdr)
    print("-" * len(hdr))
    for layer in sorted(by_layer):
        for rel, nl, nh, dens, _ in sorted(by_layer[layer], key=lambda x: -x[3]):
            print(f"{layer:<18} {rel:<56} {nl:>6} {nh:>5} {dens:>7}")
        print("-" * len(hdr))

    print("\n=== 分层合计 ===")
    for layer in sorted(by_layer):
        docs = by_layer[layer]
        print(
            f"{layer:<18} docs={len(docs):>3}  "
            f"lines={sum(d[1] for d in docs):>6}  "
            f"hits={sum(d[2] for d in docs):>5}"
        )

    print("\n=== C 层（Phase Report）密度 TOP —— 规范性语言嫌疑 ===")
    cdocs = sorted(by_layer.get("C-PhaseReport", []), key=lambda x: -x[3])[:8]
    for rel, nl, nh, dens, _ in cdocs:
        print(f"  {dens:>6}%  hits={nh:>4}  {rel}")

    print("\n=== Gate 状态行分布（供 82 §3 对账）===")
    gate_pat = re.compile(
        r"Gate\s+[A-D0-9][^\n]{0,80}\b(CLOSED|PASS|BLOCKED|DEFERRED|CONDITIONAL)\b",
        re.IGNORECASE,
    )
    for rel, layer, nl, nh, _ in rows:
        with open(rel, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        gl = [i + 1 for i, ln in enumerate(lines) if gate_pat.search(ln)]
        if gl:
            tail = " ..." if len(gl) > 12 else ""
            print(f"  [{layer}] {rel}: {len(gl)} 行  ->  {gl[:12]}{tail}")


if __name__ == "__main__":
    main()
