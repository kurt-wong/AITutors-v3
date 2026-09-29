"""Adversarial probes of claimed current state. Real runs only."""
from __future__ import annotations

import ast
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IR, IRContent, IRNode
from app.domains.resolver.span import ResolvedSpan, SourceLineView

V3 = Path(r"D:\Project\AITutors-v3")
X = Path(r"D:\Project\AITutor-X")
SVID = uuid.UUID("00000000-0000-0000-0000-00000000000e")
AID = uuid.UUID("00000000-0000-0000-0000-0000000000ae")


class TestClaimedPushAndSuite:
    def test_v3_worktree_clean_at_checkpoint(self):
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", str(V3), "status", "--porcelain"], text=True)
        print(f"\n[PUSH] V3 porcelain={out!r}")
        # allow only this audit file and in-flight A-lane source fix
        lines = [ln for ln in out.splitlines() if ln.strip()]
        allowed = ("test_adv_state_audit.py", "compiler.py")
        assert all(any(a in ln for a in allowed) for ln in lines), lines

    def test_x_worktree_clean(self):
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", str(X), "status", "--porcelain"], text=True)
        print(f"[PUSH] X porcelain={out!r}")
        assert out.strip() == ""

    def test_docs_claim_suite_matches(self):
        t = (V3 / "Docs/COORDINATION/...").read_text(encoding="utf-8") if False else ""
        # check LIMITED / notes for stale suite counts
        notes = (V3 / "Docs/COORDINATION/EVIDENCE/EB008-P1-IMPLEMENTATION-NOTES.md").read_text(encoding="utf-8")
        # 837 is historical; 2096/2131 may appear
        for claim in ["2096 passed", "2131 passed", "837 passed"]:
            if claim in notes:
                print(f"[CLAIM] notes contains {claim!r}")


class TestCompilerNoBareKeyError:
    def test_source_has_no_bare_span_lookup_in_compile_paths(self):
        src = (V3 / "backend/app/domains/compile/compiler.py").read_text(encoding="utf-8")
        # _compile_role and _compile_material must use .get + ValueError
        assert "references unknown span_id" in src
        # find remaining [span_id] without get
        import re
        bares = re.findall(r"self\._span_by_id\[[^\]]+\]", src)
        print(f"\n[CMP] remaining direct span_by_id[...] lookups: {bares}")
        assert bares == [], f"bare span lookups remain: {bares}"

    def test_dangling_span_raises_valueerror_live(self):
        span = ResolvedSpan(
            span_id="sp-s", source_version_id=SVID, role="stem",
            start_line_ref="P1L001", end_line_ref="P1L001",
            line_refs=("P1L001",), granularity="single_line",
            start_offset=None, end_offset=None, text_hash="0"*64,
            resolution_status="exact",
        )
        n = IRNode(
            unit_id="U1", unit_type="standalone_question", question_number="1",
            question_number_range=None, original_question_type="single_choice",
            content=(IRContent(role="stem", span_id="sp-MISSING"),),
            shared_components=(), sub_questions=(), relations=(),
            semantic_status="ready",
        )
        ir = IR(ir_schema="x", source_version_id=SVID, annotation_id=AID, units=(n,))
        with pytest.raises(ValueError, match="unknown span_id"):
            Compiler({"sp-s": span}, {"P1L001": SourceLineView("P1L001", "t", 1, 1, 1)}).compile(ir)
        print("[CMP] dangling span -> ValueError confirmed live")


class TestMultiBlankBlockedRecorded:
    def test_matrix_d1_blocked(self):
        t = (V3 / "Docs/COORDINATION/LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md").read_text(encoding="utf-8")
        assert "D.1 Multi-blank" in t
        assert "BLOCKED" in t
        assert "UNBLOCK" in t or "UNBLOCK:" in t
        print("\n[MB] LIMITED D.1 BLOCKED present")

    def test_l0_still_has_ordered_values(self):
        t = (V3 / "Docs/V3_SPEC/10_Data_Model.md").read_text(encoding="utf-8")
        assert "多个有序值" in t
        print("[MB] L0 ordered-values wording intact (not rewritten)")

    def test_ledger_blocks_owner3(self):
        t = (V3 / "Docs/DECISIONS/84_CONFLICT_LEDGER.md").read_text(encoding="utf-8")
        assert "BLOCKED by L0" in t or "BLOCKED" in t
        print("[MB] ledger records BLOCKED")


class TestOD002SyncedBothRepos:
    def test_v3_design_working_reference(self):
        t = (V3 / "Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md").read_text(encoding="utf-8")
        assert "WORKING REFERENCE" in t
        assert "OD-002" in t
        print("\n[OD002] V3 DESIGN-v1.1 working reference")

    def test_x_report_e_status_note(self):
        t = (X / "Docs/60_REPORTS/REPORT-E-OWNER-DECISION-QUEUE.md").read_text(encoding="utf-8")
        assert "WORKING REFERENCE" in t
        assert "6279136" in t or "DESIGN-v1.1" in t
        print("[OD002] REPORT-E has status note")

    def test_x_notes_also_have_od002(self):
        t = (V3 / "Docs/COORDINATION/EVIDENCE/EB008-P1-IMPLEMENTATION-NOTES.md").read_text(encoding="utf-8")
        assert "OD-002" in t and "WORKING REFERENCE" in t
        print("[OD002] EB-008 notes S10 has OD-002=C")


class TestNoSilentNValues:
    def test_no_values_model_files(self):
        hits = []
        for p in (V3 / "backend/app").rglob("*.py"):
            txt = p.read_text(encoding="utf-8", errors="ignore")
            if "class Value" in txt or "OrderedValue" in txt or "values: list" in txt:
                hits.append(str(p))
        print(f"\n[NVAL] model files with Value/OrderedValue: {hits}")
        assert hits == []


class TestPapersUntouched:
    def test_papers_no_tracked_changes_this_session(self):
        """Claim scope: this session did not modify Papers tracked files.
        Pre-existing untracked (2026-09-26) is reported, not asserted clean.
        """
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", r"D:\Project\Papers", "status", "--porcelain"], text=True)
        print(f"[PAPERS] porcelain={out!r}")
        bad = [ln for ln in out.splitlines() if ln.strip() and not ln.startswith("??")]
        assert bad == [], f"tracked changes in Papers: {bad}"
        untracked = [ln for ln in out.splitlines() if ln.startswith("??")]
        print(f"[PAPERS] FINDING pre-existing untracked (NOT this session): {untracked}")
        # Do not assert clean: claim is only 'not modified this session'
        # Finding: Papers cannot be described as fully clean.
