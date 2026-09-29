# G0 Authority Matrix

**Generated**: 2026-09-17 (G0 Governance Reset)
**Purpose**: Map every governance-relevant document to its Location, Git Status, Authority Level, and Evidence.

**Authority Levels** (per Consumer `Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md`):
- **L0**: Frozen Spec (normative)
- **L0-META**: Governance meta-spec
- **L1**: Contract Change Record
- **L2**: Decision Record (architecture adjudication)
- **L3**: Gate Report
- **L4**: Experiment Report
- **L5**: Status
- **None**: No governance authority
- **Unknown**: Authority not yet determined

**Location**: LOCAL (only in working tree) / REMOTE (only on GitHub) / BOTH (tracked + remote) / HISTORY (deleted from current, exists in git history)

**Git Status**: TRACKED / UNTRACKED / DELETED / MODIFIED

---

## A. Frozen Spec (L0) — Consumer Repo

| Document | Location | Git Status | Authority | Evidence |
|---|---|---|---|---|
| `Docs/V3_SPEC/00_Master_Spec.md` | BOTH | TRACKED | **L0** | Tracked at HEAD; authority_matrix.yaml confirms L0 active |
| `Docs/V3_SPEC/10_Data_Model.md` | BOTH | TRACKED | **L0** | Tracked; source of `DECISION_STATUS` freeze (§5.2) |
| `Docs/V3_SPEC/20_Document_Pipeline.md` | BOTH | TRACKED | **L0** | Tracked; source of `SEMANTIC_STATUS` freeze (§6.2, BUG-V3-018) |
| `Docs/V3_SPEC/30_Task_LLM_Safety.md` | BOTH | TRACKED | **L0** | Tracked |
| `Docs/V3_SPEC/40_Development_Rules.md` | BOTH | TRACKED | **L0** | Tracked |
| `Docs/V3_SPEC/50_Migration_Assets.md` | BOTH | TRACKED | **L0** | Tracked |
| `Docs/V3_SPEC/README.md` | BOTH | TRACKED | **L0** | Tracked; index volume |

## B. Governance Meta-Spec (L0-META) — Consumer Repo

| Document | Location | Git Status | Authority | Evidence |
|---|---|---|---|---|
| `Docs/V3_SPEC/90_DOCUMENT_GOVERNANCE.md` | BOTH | TRACKED | **L0-META** | Tracked; defines document authority levels |
| `Docs/V3_SPEC/91_PROJECT_TERMINOLOGY.md` | BOTH | TRACKED | **L0-META** | Tracked |

## C. Frozen Contract (Cross-Repo)

| Document | Location | Git Status | Authority | Evidence |
|---|---|---|---|---|
| `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` (at `f4941ff`) | BOTH | TRACKED | **L1 (FROZEN)** | sha256 `9c6b9063…7528` verified: `git show f4941ff:<path>` and current HEAD both produce identical hash. **This is THE freeze object.** |

## D. Untracked Consumer Documents (LOCAL ONLY — Primary Governance Risk)

All 9 files verified via `git log --all -- <path>`: **EMPTY for every file**. Never committed to any branch.

| Document | Location | Git Status | Authority | Evidence |
|---|---|---|---|---|
| `…IDENTITY-VERIFICATION-DESIGN-v1.md` | **LOCAL** | **UNTRACKED** | **Unknown** | Never in git. Superseded by v1.1 per DSH DEC-049. |
| `…IDENTITY-VERIFICATION-DESIGN-v1.1.md` | **LOCAL** | **UNTRACKED** | **Unknown** | Never in git. **Cited extensively by DSH Guardian DEC-035~049 as the source of D2/D3/D4 interface definitions.** Contains §4.7 "V3-side self-declared freeze". |
| `…IMPLEMENTATION-PLAN-v1.md` | **LOCAL** | **UNTRACKED** | **Unknown** | Never in git. Implementation plan for M1-M5. |
| `…IMPLEMENTATION-READINESS-v1.md` | **LOCAL** | **UNTRACKED** | **Unknown** | Never in git. Cited by DSH DEC-040 as "READINESS = IMPLEMENTATION READY". |
| `…IMPLEMENTATION-REPORT-PHASE1.md` | **LOCAL** | **UNTRACKED** | **Unknown** | Never in git. |
| `…IMPLEMENTATION-REPORT-PHASE2.md` | **LOCAL** | **UNTRACKED** | **Unknown** | Never in git. |
| `PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW.md` | **LOCAL** | **UNTRACKED** | **Unknown** | Never in git. Predecessor of tracked `…REVIEW-v0.2.md`. |
| `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT-SKELETON.md` | **LOCAL** | **UNTRACKED** | **Unknown** | Never in git. |
| `PREPROCESSING-V3-CONTRACT.md` | **LOCAL** | **UNTRACKED** | **Unknown** | Never in git. Predecessor of v0.2 DRAFT. |

(All paths relative to `Docs/COORDINATION/CONTRACTS/`)

**Governance Assessment**: These 9 documents are referenced extensively by DSH Guardian reviews (DEC-035 through DEC-049). Design v1.1 defines the D2/D3/D4 interface that DSH audited against. **None have entered git.** If the local working tree is lost, DSH audit references become dangling.

## E. Tracked Consumer Coordination Documents

| Document | Location | Git Status | Authority | Evidence |
|---|---|---|---|---|
| `…CONSUMER-DECISION-ALIGNMENT-v1.md` | BOTH | TRACKED | L3 | First consumer alignment |
| `…CONSUMER-DECISION-ALIGNMENT-v2.md` | BOTH | TRACKED | L3 | Owner ruling Part 5/6 |
| `…CONSUMER-DECISION-ALIGNMENT-v3.md` | BOTH | TRACKED | L3 | Final vocabulary ruling |
| `…CONSUMER-GAP-MAP.md` | BOTH | TRACKED | L3 | Gap analysis |
| `…CONTRACT-BLOCKER-ANALYSIS.md` | BOTH | TRACKED | L3 | |
| `…CONTRACT-CONSUMER-REVIEW-v0.2.md` | BOTH | TRACKED | L3 | "契约不可冻结" review |
| `…CONTRACT-v0.2-DRAFT.md` | BOTH | TRACKED | **L1 (FROZEN)** | THE freeze object |
| `…CONTRACT-v0.2-FREEZE-CANDIDATE-REVIEW.md` | BOTH | TRACKED | L3 | |
| `…DECISION-ALIGNMENT-REPORT.md` | BOTH | TRACKED | L3 | |
| `CURRENT.md` | BOTH | TRACKED | L5 | Current state mirror |
| `state.yaml` | BOTH | TRACKED | L5 | Machine-readable state |
| `log.md` | BOTH | TRACKED | L5 | Append-only ledger |

## F. Consumer Decision Records (L2)

All 16 files in `Docs/DECISIONS/` are TRACKED and on BOTH local and remote. Key entries:

| Document | Authority | Notes |
|---|---|---|
| `67_ANNOTATION_RESOLVER_BOUNDARY_ADJUSTMENT.md` | L2 | |
| `69_ARCHITECTURE_REVIEW_ADJUDICATION.md` | L2 | |
| `70_OQ1_IDENTITY_LAYERING.md` | L2 | |
| `71_B2B5_SUBJECTIVE_SUBQUESTION_ADJUDICATION.md` | L2 | Superseded by 80 |
| `75_EVIDENCE_PROMOTION_CONTRACT.md` | L2 | |
| `80_B2B5_CLOSURE.md` | L2 | |
| `81_GATE_D_ADAPTER_BOUNDARY.md` | L2 | |
| `82_CONTRACT_AUTHORITY_RECONCILIATION.md` | L2 | |
| `84_CONFLICT_LEDGER.md` | L2 | |
| `85_PREPROCESSING_CONSUMER_PHASE0.md` | L2 | |
| `87`–`92` (EB008 series) | L2 | Evidence Authority Enforcement Design→Final |

## G. Producer Integration Documents (Tracked)

All files in Producer `Docs/COORDINATION/INTEGRATION/` are TRACKED and on BOTH local and remote. ~30 documents.

| Document | Authority | Notes |
|---|---|---|
| `PREPROCESSING-INTEGRATION-CONTRACT.md` | L1 | Predecessor of frozen Contract v0.2 |
| `PREPROCESSING-D2-D3-D4-DECISION-BRIEF-v1.md` | L3 | DSH DEC-049 output |
| `PREPROCESSING-PHASE25-GUARDIAN-REVIEW-v1.md` | L3 | DSH DEC-048 output |
| `PREPROCESSING-CONSUMER-BOUNDARY-CLOSURE-REVIEW-v1.md` | L3 | DSH DEC-047 output |
| `PREPROCESSING-PRODUCER-GUARDIAN-PHASE2-CHECK-v1.md` | L3 | Multi-round |
| `PREPROCESSING-OWNER-DECISION-RECORD-v1.md` | L2 | Owner decisions |

## H. Producer Governance Files (Tracked)

| Document | Location | Git Status | Authority | Notes |
|---|---|---|---|---|
| `governance/rule_registry.md` | BOTH | TRACKED | L2 | C1-C15 + G-* taxonomy |
| `governance/risk_register.md` | BOTH | TRACKED | L2 | RISK-FUTURE-001 |
| `governance/phase_p2_charter.md` | BOTH | TRACKED | L2 | Phase P2 charter |

## I. Session/Status Files

| Document | Repo | Location | Git Status | Authority |
|---|---|---|---|---|
| `restart-prompt.md` (v1.67) | Consumer | BOTH | TRACKED | L5 |
| `Status.md` | Consumer | BOTH | TRACKED | L5 |
| `bugs.md` (~50 entries) | Consumer | BOTH | TRACKED | L5 |
| `log.md` | Consumer | BOTH | TRACKED | L5 |
| `CLAUDE.md` | Consumer | **HISTORY** | **DELETED** (`72af28d`) | None |
| `RS.MD` | Producer | LOCAL | UNTRACKED (by design, .gitignore) | None |
| `status.md` | Producer | BOTH | TRACKED | L5 |
| `bugs.md` (~34 entries) | Producer | BOTH | TRACKED | L5 |
| `log.md` (~460KB) | Producer | BOTH | TRACKED | L5 |

---

## Summary: Authority Gaps

### CRITICAL: 9 Untracked Governance Documents

Consumer `Docs/COORDINATION/CONTRACTS/` contains 9 documents that have NEVER entered git history. These include Design v1.1 (source of D2/D3/D4), Implementation Plan/Readiness/Reports (M1-M5 evidence), and Contract predecessors. **These exist only in a local working tree.**

### MODERATE: Cross-Repo DEC Numbering Collisions

3 confirmed collisions already documented:
- DSH `DEC-021` ≠ V3 `DEC-021` (B2 Identity)
- DSH `DEC-022` ≠ V3 `DEC-022` (B3 Semantic Boundary)
- DSH `DEC-023` ≠ V3 `DEC-023` (Interface Scope)

Additionally, V3 `DEC-031`–`DEC-036` and DSH `DEC-031`–`DEC-036` are different decisions sharing the same numbers.

### LOW: Deleted Authority Candidates

No important governance document was accidentally deleted. `CLAUDE.md` was intentionally removed (governance violation fix). Producer accidentally-committed files were intentionally removed.
