# Cross-Agent Coordination — Current State

**Workstream**: EB-0.3B Evidence Resolution Boundary Discovery
**Status**: OPEN
**Last Updated**: 2026-09-15
**Canonical Ledger**: DSH repo (kurt-wong/Aitutors-preprocessing). This is V3 mirror.

---

## Agents

| Agent | Repo | Commit | Status |
|---|---|---|---|
| Claude (V3) | AITutors-v3 | (this commit) | attribution_persisted |
| DSH (Preprocessing) | Aitutors-preprocessing | 6f09e9d | interop_complete |

---

## Shared Facts

| ID | Statement | Source | Status |
|---|---|---|---|
| FACT-001 | 527/548 resolved (96.2% coverage) | V3 | observed |
| FACT-002 | 103/113 sampled correctness (91.2%) | V3 | observed |
| FACT-003 | 21 pending: 10 STRUCT + 9 CONTEXT + 1 LEX + 1 UNK | V3 | observed |
| FACT-004 | HTML options cross-corroborated (V3 13 + DSH 3) | Both | observed |
| FACT-005 | Production Resolver NO options_region concept | V3 | observed, DSH-verified |
| FACT-006 | 214/216 regions contain canonical markers | DSH | observed |
| FACT-007 | options_region sufficient minimal handoff | Both | observed |
| FACT-008 | region_upper=None reaches production | DSH | observed |
| FACT-009 | No options_region concept (DSH independent) | DSH | observed |
| FACT-010 | Claude-4 attribution persisted, SEMANTIC=0 | V3 | observed |
| FACT-011 | Q51 = region missing, not region wrong | DSH | observed |
| FACT-012 | P3.2: 4/4 attack vectors BYPASS Admission | V3 | observed |
| FACT-013 | approve() checks gate_decision only | V3 | observed |
| FACT-014 | is_evidence_validated=False does not block Admission | V3 | observed |
| FACT-025 | ValidationEvent claim_id lacks candidate/source_version/run binding | DSH | observed |
| FACT-026 | ValidationEvent lifecycle vs review_trail persistence inconsistent | DSH | observed |
| FACT-027 | Human authority producer lacks issuer contract | DSH | observed |
| FACT-028 | IR/Admission Boundary may share same evaluate decision | DSH | observed |

---

## Open Questions

| ID | Question | Status |
|---|---|---|
| EB-001 | HTML ownership | Blocked by P3.2 |
| EB-002 | options_region in production Resolver | Open (V3 adoption gap) |
| EB-003 | Missing punctuation contextual rule | Open |
| EB-004 | _locate_options() CONTRACT GAP | Open, confirmed |
| EB-005 | Formula FP structural exclusion | Open, INFERRED |
| EB-008 | Admission Evidence Authority enforcement | **Design Frozen** (92号 FINAL; DEC-016; implementation entry) |

---

## Frozen Decisions

- DEC-001: No Frozen Spec modification
- DEC-002: No Resolver heuristic modification
- DEC-003: No Producer Contract freeze
- DEC-004: No L2 Decision Record yet
- DEC-005: B class entry = P3.2
- DEC-006: Three metrics separate
- DEC-007: Phase 0.3-B = Boundary Discovery
- DEC-008: P3.2 uses experimental adapter path
- DEC-009: Raw HTML is intended Source representation
- DEC-012: Before EB-008 adjudication: no design, no implementation, Admission not modified
- DEC-016: EB-008 Owner business rules frozen (Decision-1~4: idempotent Identity, Review Proof, persistence, IR Boundary Option B) [renamed from DEC-013, cross-ledger conflict]

---

## Evidence Locations

| Evidence | Location |
|---|---|
| Phase 0.3-B results | `backend/scripts/preprocessing_consumer/consumer-report-b3.json` |
| Correctness sampling | `backend/scripts/preprocessing_consumer/correctness-sampling-report.json` |
| Claude-4 attribution | `backend/scripts/preprocessing_consumer/claude4-attribution.json` |
| Sampling analyzer | `backend/scripts/preprocessing_consumer/sampling_analyzer.py` |
| Resolver source | `backend/app/domains/resolver/resolver.py` |
| EB-008 L2 Design (Rev-0) | `Docs/DECISIONS/87_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_DESIGN.md` |
| EB-008 L2 Design (Rev-1) | `Docs/DECISIONS/88_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_REVISION1.md` |
| EB-008 L2 Design (Rev-2) | `Docs/DECISIONS/89_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_REVISION2.md` |
| EB-008 L2 Design (Rev-3) | `Docs/DECISIONS/90_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_REVISION3.md` |
| EB-008 L2 Design (Rev-4) | `Docs/DECISIONS/91_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_REVISION4.md` |
| EB-008 FINAL (implementation entry) | `Docs/DECISIONS/92_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_FINAL.md` |
| EB-008 Verification Evidence | `Docs/COORDINATION/EVIDENCE/EB008-CLAUDE-VERIFICATION.md` |
| P3.2 enforcement results | `backend/scripts/preprocessing_consumer/p32-enforcement-results.json` |
