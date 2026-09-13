"""Emit the docs_audit/ machine-readable governance artifacts.

Read-only with respect to all documentation. Writes only into docs_audit/:

  authority_matrix.yaml          - every doc -> L0..L5 with evidence
  contradiction_candidates.json  - machine form of the 84 conflict ledger
  frozen_terms.json              - term definition/use distribution
  scan_report.md                 - human-readable summary

Governed by Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md section 5.
Re-run after any doc change; diff the output to see governance drift.
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs_audit")

A_LAYER = {
    "00": "Docs/V3_SPEC/00_Master_Spec.md",
    "10": "Docs/V3_SPEC/10_Data_Model.md",
    "20": "Docs/V3_SPEC/20_Document_Pipeline.md",
    "30": "Docs/V3_SPEC/30_Task_LLM_Safety.md",
    "40": "Docs/V3_SPEC/40_Development_Rules.md",
    "50": "Docs/V3_SPEC/50_Migration_Assets.md",
}

# 90 section 1. L1 is an allowlist: a number becomes L1 only via a released
# Contract Change Record. L2/L3 are allowlists. Everything else in the numbered
# phase-doc range is L4 unless it is a formal closure record.
L1_ALLOW = set()  # no Contract Change Record has been released
# 84 is the Conflict Ledger and 71 (CORRECTED) is a Domain Contract adjudication:
# both record decisions, so both are L2 and live in Docs/DECISIONS.
L2_ALLOW = {"67", "69", "70", "71", "75", "80", "81", "82", "84", "90"}
L3_ALLOW = {"74", "83"}


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def rel(full):
    return os.path.relpath(full, ROOT).replace(os.sep, "/")


def level_of(path):
    base = os.path.basename(path)
    norm = path.replace("\\", "/")
    if path in A_LAYER.values() or base == "README.md":
        return "L0", "Frozen Spec volume", "YES", "active"
    if base in ("90_DOCUMENT_GOVERNANCE.md", "91_PROJECT_TERMINOLOGY.md"):
        return "L0-META", "governance meta-spec (90 section 1)", "YES", "active"
    # Archived / superseded copies are deprecated regardless of what else they
    # look like. This check MUST come before the numbered-allowlist and CLOSURE
    # branches: an archived "71_..._SUPERSEDED.md" would otherwise match L2_ALLOW
    # via "71", and an archived "PHASE_..._CLOSURE_SUPERSEDED.md" would match the
    # CLOSURE branch - both would then be reported as ACTIVE L2 authority, which
    # is exactly the duplicate-authority problem archiving is meant to remove.
    # Found by the residual audit (A-10) 2026-09-13; previously dead code.
    if "/ARCHIVE/" in norm or "_SUPERSEDED" in base:
        return "L4", "superseded, archived as audit evidence (90 section 2 R8)", "NO", "deprecated"
    m = re.match(r"^(\d+)_", base)
    if m:
        num = m.group(1)
        if num in L1_ALLOW:
            return "L1", "released Contract Change Record", "NO", "active"
        if num in L2_ALLOW:
            return "L2", "Architecture Decision Record (allowlist, 90 section 1)", "NO", "active"
        if num in L3_ALLOW:
            return "L3", "Gate / governance report (allowlist, 90 section 1)", "NO", "active"
        return "L4", "Experiment / phase report (default for numbered phase docs)", "NO", "active"
    # Closure records were moved to Docs/REPORTS in DG-2, so they are detected by
    # basename, not by a /Closure/ path segment. D-02 adjudicated 2026-09-13:
    # a formal phase closure record is a Decision Record (L2). It records a
    # decision about a phase, it does not define new architecture facts (90 R2).
    if "CLOSURE" in base.upper():
        return (
            "L2",
            "formal phase closure record - L2 (D-02 adjudicated 2026-09-13)",
            "NO",
            "active",
        )
    if base in ("restart-prompt.md", "Status.md", "log.md", "bugs.md"):
        return "L5", "Status / log / restart", "NO", "active"
    if "/REPORTS/" in norm:
        # Unnumbered report sitting in the reports tree defaults to L4 rather
        # than UNASSIGNED: its location already answers "what kind of doc".
        return "L4", "report placed in Docs/REPORTS (unnumbered, default L4)", "NO", "active"
    return (
        "UNASSIGNED",
        "not covered by 90 section 1 - may not be cited as authority",
        "NO",
        "active",
    )


# Directory model after DG-2 relocation (2026-09-13). L0 stays put; non-L0 is
# physically separated by layer. The four JSON corpora stay in
# backend/Docs/V3_SPEC because tests read them by path.
DOC_ROOTS = (
    "Docs/V3_SPEC",          # L0 Frozen Spec + L0-META governance meta-spec
    "Docs/DECISIONS",        # L2 Decision Records
    "Docs/REPORTS",          # L3/L4 Gate and Experiment Reports, Closure records
    "Docs/ARCHIVE",          # superseded / stale, kept as audit evidence
    "backend/Docs/V3_SPEC",  # legacy location; holds the frozen test corpora
)


def iter_docs():
    for root in DOC_ROOTS:
        base = os.path.join(ROOT, root)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for fn in sorted(filenames):
                if fn.endswith(".md"):
                    yield rel(os.path.join(dirpath, fn))
    for extra in ("restart-prompt.md", "Status.md", "log.md", "bugs.md"):
        if os.path.exists(os.path.join(ROOT, extra)):
            yield extra


STATUS_LINE = re.compile(
    r"^\s*(?:\*\*)?Status(?:\*\*)?\s*[:：]\s*(.+)$", re.IGNORECASE | re.MULTILINE
)
GATE_STATE = re.compile(
    r"Gate\s+([A-D][0-9A-B-]*)[^\n]{0,90}?\b"
    r"(CLOSED|PASS|BLOCKED|DEFERRED|CONDITIONAL|WAIT|NEXT|NOT CLOSED)\b",
    re.IGNORECASE,
)


def build_authority_matrix(docs):
    rows = []
    for d in docs:
        text = read(os.path.join(ROOT, d))
        level, reason, normative, lstatus = level_of(d)
        sm = STATUS_LINE.search(text)
        status = sm.group(1).strip()[:120] if sm else "(no Status field)"
        rows.append(
            {
                "path": d,
                "level": level,
                "classification_status": lstatus,
                "reason": reason,
                "status_field": status,
                "normative": normative,
                "gate_state_authority": (
                    "YES" if d.endswith("82_CONTRACT_AUTHORITY_RECONCILIATION.md") else "NO"
                ),
            }
        )
    return rows


def build_gate_matrix(docs):
    out = []
    for d in docs:
        text = read(os.path.join(ROOT, d))
        for i, ln in enumerate(text.splitlines(), 1):
            for m in GATE_STATE.finditer(ln):
                out.append(
                    {
                        "doc": d,
                        "line": i,
                        "gate": m.group(1),
                        "state": m.group(2).upper(),
                        "text": ln.strip()[:180],
                    }
                )
    return out


TERMS = [
    "ResolvedSpan", "ResolvedRun", "annotation_payload", "Source Binding Claim",
    "FORBIDDEN_FIELDS", "Validated Evidence", "Verified Evidence",
    "verified_correct", "Evidence Contract", "canonical_question_type",
    "STRICT_AUTO_TYPES", "structural_regions", "Binding Carrier", "line_refs",
]
# A definition is not always a prose "X means Y". Frozen Spec and Decision
# Records commonly define via tables, state-machine diagrams, JSON field lists
# and forbidden-field enumerations. 90 section 2 R6 requires the detector to
# recognise those, otherwise a table-defined term scores as undefined (B-03).
DEFINE_RX = re.compile(
    r"(定义|定为|冻结为|指的是|:=|denotes|is defined as"
    r"|唯一的?进入|唯一可进入|state:\s*\w+|唯一允许)"
)


def is_definition_line(line, term):
    if DEFINE_RX.search(line):
        return True
    if term in line and re.search(
        r"(state:\s*(?:trusted|immutable|untrusted|awaiting|terminal)"
        r"|唯一可进入|唯一允许进入|唯一进入)", line, re.IGNORECASE
    ):
        return True
    # Table row: | Term | ... | with a definitional-looking neighbour cell
    if line.strip().startswith("|") and term in line:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if any(c == term or c == f"`{term}`" for c in cells):
            return True
    return False


def build_terms(docs):
    out = {}
    for term in TERMS:
        defs, uses = [], []
        for d in docs:
            text = read(os.path.join(ROOT, d))
            for i, ln in enumerate(text.splitlines(), 1):
                if term in ln:
                    entry = {"doc": d, "line": i}
                    (defs if is_definition_line(ln, term) else uses).append(entry)
        if len(uses) >= 8 and len(defs) == 0:
            risk = "HIGH"
        elif len(uses) >= 3 and len(defs) == 0:
            risk = "MEDIUM"
        else:
            risk = "LOW"
        out[term] = {
            "definition_sites": len(defs),
            "use_sites": len(uses),
            "definitions": defs[:8],
            "uses_sample": uses[:12],
            "drift_risk": risk,
        }
    return out


# Hand-curated candidates, mirroring backend/Docs/V3_SPEC/84_CONFLICT_LEDGER.md.
# Kept explicit rather than auto-derived: a machine cannot judge polarity.
CANDIDATES = [
    {"id": "A-01", "type": "status_drift", "severity": "P0", "status": "SUPERSEDED",
     "summary": "doc 74 declared Gate C BLOCKED while doc 80 declared CLOSED, no supersession record",
     "evidence": ["74:5", "74:363", "74:537", "80:439"]},
    {"id": "A-02", "type": "status_drift", "severity": "P0", "status": "SUPERSEDED",
     "summary": "doc 69 section 8 undated roadmap still read 'Errata Decision after all of Gate A-D pass'",
     "evidence": ["69:306"]},
    {"id": "A-03", "type": "aggregation_error", "severity": "P0", "status": "INCORPORATED",
     "summary": "doc 81 claimed 'Gate B series CLOSED', overstating doc 80",
     "evidence": ["81:11", "80:421", "80:432", "80:437"]},
    {"id": "A-04", "type": "status_ambiguity", "severity": "P1", "status": "RESOLVED",
     "summary": "doc 80 records B2-B2 CLOSED while listing B2-B2 Unknown 125 triage as unresolved - RESOLVED 2026-09-13: scope declaration written into 80 section 4 B2-B2 line (closed scope = the 1178 measured MC targets; Unknown 125 is out of scope)",
     "evidence": ["80:426", "80:448"]},
    {"id": "A-05", "type": "stale_snapshot", "severity": "P1", "status": "RESOLVED",
     "summary": "doc 69 dated matrices still show B2-B as BLOCKED / WAIT - RESOLVED 2026-09-13: supersession banners added to all three 2026-09-11 dated Gate-state blocks; body text kept as history, 82 section 3 is the authority",
     "evidence": ["69:656", "69:756"]},
    {"id": "A-06", "type": "status_drift", "severity": "P1", "status": "RESOLVED",
     "summary": "doc 61 Status IN PROGRESS while PHASE_I3_CLOSURE records CLOSED - RESOLVED 2026-09-13: 61 header now reads HISTORICAL and points at the closure record",
     "evidence": ["61:4", "Docs/REPORTS/PHASE_I3_CLOSURE.md:4"]},
    {"id": "A-07", "type": "status_drift", "severity": "P0", "status": "DECIDED",
     "summary": "doc 73 declares 157 targets UNRESOLVED while Gate C closed on C-2 - DECIDED as orthogonal: C-2 proves pipeline invariant, not semantic truth",
     "evidence": ["73:213", "80:439", "backend/tests/test_c2_evidence_authority_e2e.py"]},
    {"id": "A-08", "type": "opposite_polarity", "severity": "P1", "status": "RESOLVED",
     "summary": "Status.md holds both retracted and corrected Grammar input contract, retracted one unmarked - RESOLVED 2026-09-13: retraction banner added to the 2026-09-13 section, pointing at 81 section 6.2 as the invariant form",
     "evidence": ["Status.md:2309", "Status.md:2423"]},
    {"id": "A-09", "type": "stale_header", "severity": "P2", "status": "RESOLVED",
     "summary": "Status.md top-level Status line still reads implementation not started - RESOLVED 2026-09-13: top-level Status is now a pointer to 82 section 3, it no longer self-describes",
     "evidence": ["Status.md"]},
    {"id": "A-10", "type": "provenance_missing", "severity": "P1", "status": "RESOLVED",
     "summary": "Phase I-2 Revision Closure existed twice with different content; the stale copy never entered the census and Status.md held two dead path pointers - RESOLVED 2026-09-13 (residual audit): all three Design Decisions already have carriers (D1/D3 in the governed closure section 4; D2 OCR-is-a-provider lives in L0 10_Data_Model section 4.2 role enum, higher authority). DELETE three-proof test failed (has historical value, has a live reference) so Disposition = ARCHIVE: git-mv to Docs/ARCHIVE/PHASE_I2_REVISION_CLOSURE_SUPERSEDED.md with a SUPERSEDED banner, empty Docs/V3_PHASE_STATUS/ removed, both Status.md historical sections got provenance banners. Body text unchanged everywhere. Method-validation case for the residual audit.",
     "evidence": ["Docs/ARCHIVE/PHASE_I2_REVISION_CLOSURE_SUPERSEDED.md",
                  "Docs/REPORTS/PHASE_I2_REVISION_CLOSURE.md",
                  "Docs/V3_SPEC/10_Data_Model.md:136",
                  "Docs/DECISIONS/84_CONFLICT_LEDGER.md"]},
    {"id": "B-01", "type": "term_name_drift", "severity": "P0", "status": "DECIDED",
     "summary": "'Evidence Contract' is an undeclared abbreviation of 'Evidence Promotion Contract' (doc 75); terminology note added to 75, no mass rename",
     "evidence": ["75", "74:226", "81:221"]},
    {"id": "B-02", "type": "term_drift", "severity": "P0", "status": "DECIDED",
     "summary": "Validated Evidence is L2-defined in doc 75 state machine, not L0; not promoted to L0; 90 R2/R9 freezes Validated Evidence != verified_correct and bans Verified Evidence",
     "evidence": ["75:42", "75:194", "20:637"]},
    {"id": "B-03", "type": "detector_limitation", "severity": "P2", "status": "MITIGATED",
     "summary": "detector missed table and state-machine definitions; fixed, all HIGH drift risks cleared",
     "evidence": ["20:288", "20:308"]},
    {"id": "C-01", "type": "boundary_conflict", "severity": "P0", "status": "OPEN_PAUSED",
     "summary": "line_refs carrier: BIND-1 PASS/FROZEN, BIND-2 PASS/FROZEN, BIND-3 direction ACCEPTED but contract UNPROVEN - C-01 OPEN/PAUSED 2026-09-13, paused on missing upstream production facts (82 section 5.3.1), not on an architecture error; Manifest Schema NOT FROZEN, Adapter NOT STARTED",
     "evidence": ["20:117", "20:73", "67:114", "81:5.1", "82:5"]},
    {"id": "C-02", "type": "boundary_conflict", "severity": "P0", "status": "INCORPORATED",
     "summary": "doc 66 section 7 'Bypasses: Annotation, Resolver' contradicted IRBuilder.build signature; corrected to Resolver only",
     "evidence": ["66:7", "backend/app/domains/compile/ir.py:87"]},
    {"id": "CA-001", "type": "l0_change_audit", "severity": "P0", "status": "CLOSED",
     "summary": "doc 40 section 5 gained a mandatory measurement-semantics rule in 0dd954d with no Change Record - CLOSED as (b): ratified CHANGE-2 via 90 section 11 CR-001, text retained, no L0 content change, procedural gap cured",
     "evidence": ["40", "0dd954d", "90:CR-001"]},
    {"id": "D-01", "type": "duplicate_number", "severity": "P0", "status": "CLOSED",
     "summary": "doc 71 existed twice with different content - CLOSED 2026-09-13 (DG-3): root copy judged stale, git-mv to Docs/ARCHIVE/71_..._SUPERSEDED.md with a SUPERSEDED block; backend CORRECTED copy moved to Docs/DECISIONS/71_... as L2. Neither copy deleted.",
     "evidence": ["Docs/ARCHIVE/71_B2B5_SUBJECTIVE_SUBQUESTION_ADJUDICATION_SUPERSEDED.md",
                  "Docs/DECISIONS/71_B2B5_SUBJECTIVE_SUBQUESTION_ADJUDICATION.md"]},
    {"id": "D-02", "type": "unassigned_layer", "severity": "P0", "status": "CLOSED",
     "summary": "5 docs inside V3_SPEC trees had no L-level - CLOSED 2026-09-13: 4x Closure records adjudicated L2 (KEEP, formal phase closure = Decision Record); gate_b2a_three_task_report already L4 via the Docs/REPORTS default (KEEP). No doc deleted or archived.",
     "evidence": ["Docs/REPORTS/PHASE_I3_CLOSURE.md:5", "Docs/REPORTS/gate_b2a_three_task_report.md"]},
    {"id": "D-03", "type": "mislayered", "severity": "P1", "status": "CLOSED",
     "summary": "3 mislayered docs - CLOSED 2026-09-13, all KEEP at L4 with explicit non-authority annotations: 63 no longer self-declares Frozen Constraint (promotion to L0 requires an L1 Change Record, 90 R1); 65 annotated as 69-typed Evidence with I-5 closed; 68 annotated as 69-typed Proposal. 65 NOT promoted to L2 - that would contradict 69 and duplicate rules already carried by 63 section 10.9/10.10 and 81 section 5.6.",
     "evidence": ["63:3", "65:95", "68"]},
    {"id": "D-04", "type": "l3_self_rule", "severity": "P1", "status": "CLOSED",
     "summary": "L3 doc 74 asserted six rules on V3 rather than citing L0/L1 - CLOSED 2026-09-13: all six sites rewritten from normative assertion to report finding plus a pointer at the L2 carrier in doc 75 (or 81 section 6.2 for the Grammar rule). Body content otherwise unchanged.",
     "evidence": ["74:224", "74:226", "74:283", "74:385", "74:395", "74:418"]},
    {"id": "D-05", "type": "concentration", "severity": "P1", "status": "CLOSED",
     "summary": "Gate-status lines concentrate in Status.md and doc 69 - CLOSED 2026-09-13: the control is already in force (90 section 4 Status Header rule + 82 section 3.3 declaration template, both with an explicit no-mandatory-backfill clause). Stock rows are not backfilled (Reconcile, don't rewrite); A-05 handled the three actively-stale blocks in 69.",
     "evidence": ["Status.md", "69", "90:4", "82:3.3"]},
    {"id": "E-01", "type": "false_positive", "severity": "none", "status": "FALSE_POSITIVE",
     "summary": "doc 81 mixed pipeline figure is two explicitly labelled branches, not an unlabelled mix",
     "evidence": ["81:208"]},
    {"id": "E-02", "type": "false_positive", "severity": "none", "status": "FALSE_POSITIVE",
     "summary": "doc 10 line 777 citing 20 section 12.1 is a changelog recording the fix TO 20 section 8.5, not a live citation",
     "evidence": ["10:777"]},
    {"id": "E-03", "type": "false_positive", "severity": "none", "status": "FALSE_POSITIVE",
     "summary": "no document says 'B2-B = NEXT'; residue is BLOCKED / WAIT only",
     "evidence": []},
]


# ---------------------------------------------------------------------------
# DG-1 Document Census (91 section 6). Per-document view, complementary to the
# per-conflict view in contradiction_candidates.json.
# ---------------------------------------------------------------------------

RULE_WORDS = re.compile(r"(必须|不得|禁止|只能|应当|shall|must(?:\s+not)?|MUST)", re.IGNORECASE)
L0_CITE = re.compile(r"\b(00|10|20|30|40|50)\s*§\s*[0-9]+")
# Label must be a whole token: "Gate Policy" must not yield "Gate P". The
# negative lookahead excludes a following lowercase letter, which is what made
# Gate State / Gate Report / Gate Policy register as phantom gates.
STAGE_NAMES = re.compile(
    r"\b(Phase|Step|Path|Gate)\s+([A-Z0-9](?:[A-Z0-9.\-]*[A-Z0-9])?)(?![a-z])"
)
BANNED_STATUS = re.compile(r"\b(COMPLETE|DONE|FINISHED|REVIEWED)\b")
# A line that *bans* a word is not a use of it. Without this, 91's own ban table
# flags itself.
BAN_CONTEXT = re.compile(r"(禁用|禁止|不得使用|banned|ban\b|forbid)", re.IGNORECASE)


def census(docs):
    """Per-document census. Problem classes follow 91 section 6 / the review."""
    rows = []
    stage_index = {}
    for d in docs:
        text = read(os.path.join(ROOT, d))
        lines = text.splitlines()
        level, reason, normative, lstatus = level_of(d)
        nlines = len(lines)

        # P1 overreach: normative tone in a layer that may not define rules
        rule_lines = [i + 1 for i, ln in enumerate(lines) if RULE_WORDS.search(ln)]
        cites_l0 = any(L0_CITE.search(ln) for ln in lines)
        overreach = []
        if level in ("L3", "L4"):
            # A rule line that does not cite L0 anywhere in the document is a
            # candidate overreach. Listed, not judged.
            if rule_lines and not cites_l0:
                overreach = rule_lines[:12]

        # P2 implicit L0 modification: phrases that retire an existing design
        implicit = []
        for i, ln in enumerate(lines, 1):
            if re.search(r"(不再适用|原设计|已被取代|no longer applies|superseded by the)", ln):
                if level not in ("L0", "L0-META", "L1"):
                    implicit.append(i)

        # P4 duplicate stage names
        for m in STAGE_NAMES.finditer(text):
            key = f"{m.group(1)} {m.group(2)}"
            stage_index.setdefault(key, []).append(d)

        banned = [
            i + 1
            for i, ln in enumerate(lines)
            if BANNED_STATUS.search(ln) and not BAN_CONTEXT.search(ln)
        ]

        rows.append(
            {
                "path": d,
                "level": level,
                "classification_status": lstatus,
                "lines": nlines,
                "normative_rule_lines": len(rule_lines),
                "cites_l0": cites_l0,
                "birth_certificate": any(
                    k in text for k in ("Document Type:", "Authority Level:", "Derives From:")
                ),
                "overreach_candidates": overreach,
                "implicit_l0_modification": implicit[:8],
                "banned_status_words": banned[:8],
            }
        )

    # P4 report: a stage name used in more than one document
    stage_dupes = {
        k: sorted(set(v))
        for k, v in stage_index.items()
        if len(set(v)) > 1 and len(k.split()[1]) <= 3
    }
    return rows, stage_dupes


def main():
    os.makedirs(OUT, exist_ok=True)
    docs = list(iter_docs())

    matrix = build_authority_matrix(docs)
    with open(os.path.join(OUT, "authority_matrix.yaml"), "w", encoding="utf-8") as fh:
        fh.write("# Generated by backend/scripts/i5g_emit_audit.py - do not hand-edit\n")
        fh.write("# Governed by Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md section 1\n")
        fh.write("# level: L0 Frozen Spec | L0-META governance meta-spec |\n")
        fh.write("#        L1 Contract Change Record | L2 Decision Record |\n")
        fh.write("#        L2-proposed (pending adjudication, NOT citable as authority) |\n")
        fh.write("#        L3 Gate Report | L4 Experiment Report | L5 Status | UNASSIGNED\n")
        fh.write("# classification_status: active | pending\n")
        fh.write("documents:\n")
        for r in sorted(matrix, key=lambda x: (x["level"], x["path"])):
            fh.write(f"  - path: {r['path']}\n")
            fh.write(f"    level: {r['level']}\n")
            fh.write(f"    classification_status: {r['classification_status']}\n")
            fh.write(f"    normative: {r['normative']}\n")
            fh.write(f"    gate_state_authority: {r['gate_state_authority']}\n")
            fh.write(f"    reason: {r['reason']}\n")
            fh.write(f"    status_field: \"{r['status_field']}\"\n")

    gates = build_gate_matrix(docs)
    with open(os.path.join(OUT, "contradiction_candidates.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "_generated_by": "backend/scripts/i5g_emit_audit.py",
                "_governed_by": "Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md",
                "_mirror_of": "backend/Docs/V3_SPEC/84_CONFLICT_LEDGER.md",
                "candidates": CANDIDATES,
                "gate_state_lines": gates,
            },
            fh, ensure_ascii=False, indent=2,
        )

    terms = build_terms(docs)
    with open(os.path.join(OUT, "frozen_terms.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "_generated_by": "backend/scripts/i5g_emit_audit.py",
                "_note": (
                    "drift_risk HIGH = many uses, zero prose definitions. "
                    "Field-table definitions (e.g. ResolvedSpan in 20 section 5.5) "
                    "are not detected; check B-03 before treating HIGH as a defect."
                ),
                "terms": terms,
            },
            fh, ensure_ascii=False, indent=2,
        )

    census_rows, stage_dupes = census(docs)
    with open(os.path.join(OUT, "document_census.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "_generated_by": "backend/scripts/i5g_emit_audit.py",
                "_governed_by": "Docs/V3_SPEC/91_PROJECT_TERMINOLOGY.md section 6 (DG-1)",
                "_problem_classes": {
                    "overreach_candidates": "L3/L4 document uses rule language but never cites L0",
                    "implicit_l0_modification": "non-L0 document retires an existing design",
                    "banned_status_words": "COMPLETE/DONE/FINISHED/REVIEWED per 91 section 3.2",
                    "duplicate_stage_names": "same Phase/Step/Path/Gate label across documents",
                },
                "documents": census_rows,
                "duplicate_stage_names": stage_dupes,
            },
            fh, ensure_ascii=False, indent=2,
        )

    by_level = {}
    for r in matrix:
        by_level.setdefault(r["level"], []).append(r["path"])
    # OPEN_PAUSED is still OPEN: it means "adjudication deferred for lack of
    # upstream facts", not "resolved". Counting only exact "OPEN" would print
    # "OPEN candidates: 0" while C-01 is still open, which reads as all-clear.
    open_c = [c for c in CANDIDATES if c["status"] in ("OPEN", "OPEN_PAUSED")]
    p0 = [c for c in open_c if c["severity"] == "P0"]

    with open(os.path.join(OUT, "scan_report.md"), "w", encoding="utf-8") as fh:
        fh.write("# docs_audit scan report\n\n")
        fh.write("Generated by `backend/scripts/i5g_emit_audit.py`. Governed by "
                 "`Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md`.\n\n")
        fh.write("## Layer census\n\n")
        fh.write("| Level | Docs |\n|---|---|\n")
        for lv in sorted(by_level):
            fh.write(f"| {lv} | {len(by_level[lv])} |\n")
        fh.write("\n## UNASSIGNED (may not be cited as authority)\n\n")
        for p in by_level.get("UNASSIGNED", []):
            fh.write(f"- `{p}`\n")
        if not by_level.get("UNASSIGNED"):
            fh.write("(none)\n")
        fh.write("\n## OPEN conflict candidates\n\n")
        fh.write(f"Total OPEN: {len(open_c)} (P0: {len(p0)})\n\n")
        fh.write("| ID | Sev | Type | Summary |\n|---|---|---|---|\n")
        for c in open_c:
            fh.write(f"| {c['id']} | {c['severity']} | {c['type']} | {c['summary']} |\n")
        fh.write("\n## High term-drift risk\n\n")
        for t, v in sorted(terms.items(), key=lambda kv: -kv[1]["use_sites"]):
            if v["drift_risk"] == "HIGH":
                fh.write(f"- `{t}`: {v['use_sites']} uses, "
                         f"{v['definition_sites']} definitions\n")
        fh.write("\n## Gate-state line concentration\n\n")
        conc = {}
        for g in gates:
            conc[g["doc"]] = conc.get(g["doc"], 0) + 1
        for d, n in sorted(conc.items(), key=lambda kv: -kv[1])[:10]:
            fh.write(f"- {n:>3}  `{d}`\n")

        # DG-1 census summary (91 section 6)
        with_bc = sum(1 for r in census_rows if r["birth_certificate"])
        over = [r for r in census_rows if r["overreach_candidates"]]
        impl = [r for r in census_rows if r["implicit_l0_modification"]]
        banned = [r for r in census_rows if r["banned_status_words"]]
        fh.write("\n## DG-1 Document Census\n\n")
        fh.write(f"Birth certificate present: {with_bc} / {len(census_rows)}\n")
        fh.write("(birth certificate = Document Type + Authority Level + Derives From, ")
        fh.write("per 91 section 5)\n\n")
        fh.write("### P1 overreach candidates (L3/L4 rule language, no L0 citation)\n\n")
        if over:
            for r in over:
                fh.write(f"- `{r['path']}` ({r['level']}): lines {r['overreach_candidates']}\n")
        else:
            fh.write("(none)\n")
        fh.write("\n### P2 implicit L0 modification\n\n")
        if impl:
            for r in impl:
                fh.write(f"- `{r['path']}` ({r['level']}): lines {r['implicit_l0_modification']}\n")
        else:
            fh.write("(none)\n")
        fh.write("\n### P3 banned status words (91 section 3.2)\n\n")
        if banned:
            for r in banned:
                fh.write(f"- `{r['path']}`: lines {r['banned_status_words']}\n")
        else:
            fh.write("(none)\n")
        fh.write("\n### P4 duplicate stage names (short labels only)\n\n")
        if stage_dupes:
            for k in sorted(stage_dupes)[:30]:
                fh.write(f"- `{k}` in {len(stage_dupes[k])} docs\n")
        else:
            fh.write("(none)\n")

    print(f"wrote {OUT}")
    print("  layers: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(by_level.items())))
    print(f"  OPEN candidates: {len(open_c)} (P0 {len(p0)})")
    print(f"  gate-state lines: {len(gates)}")
    print(f"  terms tracked: {len(terms)}")
    print(f"  census: birth_certificate {sum(1 for r in census_rows if r['birth_certificate'])}"
          f"/{len(census_rows)}; overreach {len(over)}; implicit_l0 {len(impl)};"
          f" banned_status {len(banned)}; dup_stage {len(stage_dupes)}")


if __name__ == "__main__":
    main()
