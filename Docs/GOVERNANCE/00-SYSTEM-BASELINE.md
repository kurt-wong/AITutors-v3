# G0 System Baseline — AITutors System

**Generated**: 2026-09-17 (G0 Governance Reset)
**Audit method**: Local working tree + git tracked tree + git history + GitHub remote, all four layers verified.

---

## System Architecture

```
AITutors System
├── Producer (D:\Project\Papers)
│   └── kurt-wong/Aitutors-preprocessing
│       └── Role: Source Evidence Producer (OCR → Manifest → IR)
│
├── Contract (frozen artifact, lives in both repos)
│   └── PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md
│       └── Freeze Object: commit f4941ff, sha256 9c6b9063…7528
│
└── Consumer (D:\Project\AITutors-v3)
    └── kurt-wong/AITutors-v3
        └── Role: Evidence Resolution + Semantic IR + Gate + Admission
```

---

## V3 Consumer Repository

| Field | Value |
|---|---|
| **Local path** | `D:\Project\AITutors-v3` |
| **Remote** | `kurt-wong/AITutors-v3` |
| **Branch** | `main` |
| **Local HEAD** | `cc12d79e9a22f6274100ea0bb61f92493ba88509` |
| **Remote HEAD (origin/main)** | `cc12d79e9a22f6274100ea0bb61f92493ba88509` |
| **Sync status** | **IN SYNC** — zero commits ahead/behind |
| **Working tree** | CLEAN (no modified, no deleted) |
| **Untracked files** | **9 files** (all in `Docs/COORDINATION/CONTRACTS/`) |
| **Tracked file count** | 457 |
| **Last commit** | `cc12d79` — feat: Phase 2.5 Consumer Data Activation & Interface Closure |

### Untracked files (never entered git history)

All 9 untracked files verified via `git log --all -- <path>`: **EMPTY for every file**. These documents have NEVER been committed to any branch. They exist only in the local working tree.

| File | Git Status | Authority |
|---|---|---|
| `PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.md` | UNTRACKED, never in history | UNKNOWN |
| `PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md` | UNTRACKED, never in history | UNKNOWN |
| `PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-IMPLEMENTATION-PLAN-v1.md` | UNTRACKED, never in history | UNKNOWN |
| `PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-IMPLEMENTATION-READINESS-v1.md` | UNTRACKED, never in history | UNKNOWN |
| `PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-IMPLEMENTATION-REPORT-PHASE1.md` | UNTRACKED, never in history | UNKNOWN |
| `PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-IMPLEMENTATION-REPORT-PHASE2.md` | UNTRACKED, never in history | UNKNOWN |
| `PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW.md` | UNTRACKED, never in history | UNKNOWN |
| `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT-SKELETON.md` | UNTRACKED, never in history | UNKNOWN |
| `PREPROCESSING-V3-CONTRACT.md` | UNTRACKED, never in history | UNKNOWN |

(All paths relative to `Docs/COORDINATION/CONTRACTS/`)

### Tracked key directories

| Directory | File Count | Purpose |
|---|---|---|
| `Docs/V3_SPEC/` | 9 | Frozen Spec (L0) |
| `Docs/DECISIONS/` | 16 | Architecture Decision Records (L2) |
| `Docs/COORDINATION/CONTRACTS/` | 9 tracked + 9 untracked | Cross-repo coordination |
| `Docs/COORDINATION/` | CURRENT.md, state.yaml, log.md | Governance state |
| `backend/app/` | ~40 Python modules | Application code |
| `backend/tests/` | ~80 test files | Test suite |
| `backend/alembic/` | 12 migration files | Schema migrations |
| `backend/scripts/` | ~30 scripts | Consumer tooling |
| `docs_archive/` | 8 subdirectories | Historical archives |
| `docs_audit/` | 5 files | Document governance audit |

### Identity verification modules (tracked, in git)

| Module | Lines | SHA256 (prefix) | Role |
|---|---|---|---|
| `backend/app/core/raw_bytes_identity.py` | 54 | `803c4ed8…` | M2 |
| `backend/app/core/manifest_identity.py` | 78 | `1ca33a45…` | M1 |
| `backend/app/core/ir_identity.py` | 171 | `f960b513…` | M3 |
| `backend/app/core/identity_verifier.py` | 120 | `1306105c…` | M4 |
| `backend/app/core/identity_gate.py` | 155 | `8a5d267e…` | M5 |

### Deleted files in git history

| File | Deleted in commit | Notes |
|---|---|---|
| `CLAUDE.md` | `72af28d` | Governance violation fix — replaced by `restart-prompt.md` v1.67 |
| `PHASE_I2C_DIAGNOSTIC_REPORT.json` | `9978c48` | Superseded working document |

---

## Preprocessing Producer Repository

| Field | Value |
|---|---|
| **Local path** | `D:\Project\Papers` |
| **Remote** | `kurt-wong/Aitutors-preprocessing` |
| **Branch** | `main` |
| **Local HEAD** | `2b92898f05f6541a5fc65c8300cb8a59a06c4928` |
| **Remote HEAD (origin/main)** | `2b92898f05f6541a5fc65c8300cb8a59a06c4928` |
| **Sync status** | **IN SYNC** — zero commits ahead/behind |
| **Working tree** | **CLEAN** — no modified, no deleted, no untracked |
| **Tracked file count** | 419 |
| **Last commit** | `2b92898` — DEC-049: D2/D3/D4 Decision Brief (Evidence First, No Self-Fix) |

### Key directories

| Directory | Purpose |
|---|---|
| `Ocr-markdown/` | OCR output corpus (source md files + manifests + IR) |
| `data/` | Audit artifacts, evidence snapshots, fix logs |
| `Docs/COORDINATION/INTEGRATION/` | 30+ cross-repo integration documents |
| `Docs/COORDINATION/` | CURRENT.md, state.yaml, log.md, PROTOCOL.md |
| `governance/` | rule_registry.md, risk_register.md, phase_p2_charter.md |
| `scripts/` | Producer tooling (~30+ scripts) |
| `tests/` | Test suite (~40 test files) |
| `reports/` | Review reports |
| `attacks/` | Adversarial attack suite |
| `original/` | Original source PDFs |

### Producer data artifacts (key evidence chain)

| Artifact | Purpose |
|---|---|
| `data/audit_snapshot_R50_input_baseline.json` | R50 input baseline (356 files) |
| `data/audit_snapshot_interface_scope_prebackfill.json` | Pre-backfill snapshot |
| `data/audit_snapshot_interface_scope_postbackfill.json` | Post-backfill snapshot |
| `data/freeze_evidence_final_check.json` | Freeze evidence final check |
| `data/resolver_ref_r52/resolver_ir.json` | Producer IR artifact |

### Deleted files in git history

| File | Deleted in commit | Notes |
|---|---|---|
| `RS.MD` | `7bda4d7` | Intentionally untracked by design (local resume prompt, .gitignore line 31) |
| `data/r54_f1/f1_report.json` | `7bda4d7` | Accidentally committed, intentionally removed |
| `data/resolver_ref_r52/resolver_ir.json` | `7bda4d7` | Same |
| `logs/ocr_child_err.log` | `7bda4d7` | Same |
| `logs/reslice_reslice-pac-annotated_log.txt` | `7bda4d7` | Same |

---

## Local vs Remote State

### Consumer (AITutors-v3)

| Check | Result |
|---|---|
| Local HEAD == origin/main | **YES** — `cc12d79` |
| Uncommitted changes | **NONE** |
| Untracked files | **9** (all `Docs/COORDINATION/CONTRACTS/`) |
| Deleted tracked files | **NONE** |
| Modified tracked files | **NONE** |

### Producer (Aitutors-preprocessing)

| Check | Result |
|---|---|
| Local HEAD == origin/main | **YES** — `2b92898` |
| Uncommitted changes | **NONE** |
| Untracked files | **NONE** |
| Deleted tracked files | **NONE** |
| Modified tracked files | **NONE** |

---

## Producer/Consumer Drift

| Dimension | Status |
|---|---|
| Contract v0.2 freeze object | **ALIGNED** — both sides reference `f4941ff` / `9c6b9063…7528` |
| Source identity key naming | **ALIGNED** — `source_content_sha256` per DEC-030/031 |
| Semantic vocabulary | **PAPER ALIGNED** — `{ready, incomplete, unknown}` per DEC-028 Part 5; V3 `SEMANTIC_STATUS` code still frozen at `{ready, incomplete}` (BUG-V3-018) |
| Decision vocabulary | **ALIGNED** — `{pending_review, approved, rejected}` per DEC-028 Part 5 |
| D2/D3/D4 status | **OPEN** — Decision Brief delivered (DSH DEC-049), awaiting Owner ruling |
| V3 identity verification | **IMPLEMENTED** — M1-M5 in tracked code at `cc12d79` |
| V3 identity_version gate | **NOT IMPLEMENTED** — `identity_version` = 0 hits in V3 codebase |
| Non-ready → pending_review channel | **NOT IMPLEMENTED** — runner_b2 silently skips non-ready units |

---

## Open Items Snapshot

| Item | Source | Status |
|---|---|---|
| D2 — V3 identity_version gate | Contract §5.4 | UNKNOWN (Owner not ordered) |
| D3 — Semantic boundary / four-state machine | Contract §5.4 | Not started (requires unfreeze BUG-V3-018) |
| D4 — Execution ordering V3 scheduling | Contract §5.4 | UNKNOWN (five steps contain zero V3 steps) |
| OQ-10 — PDF face source_content_sha256 backfill | DSH ledger | Deferred |
| OQ-16 — PENDING_REVIEW→REJECTED routing rule | Contract | UNKNOWN |
| OQ-21 — 16 units presentation mechanism | Contract | Open |
| D-048-1 — M5 `__str__` override residual bypass | DSH DEC-048 | WARNING |
| D-048-2 — M3 positional fallback | DSH DEC-048 | NOTE |
| BUG-V3-001 through BUG-V3-050 | Consumer bugs.md | ~34 Open / ~16 Resolved |

---

## Governance Note

This baseline is a snapshot as of 2026-09-17. The system governance currently depends on:
1. Two git repositories with in-sync remotes (VERIFIED this round)
2. A frozen Contract artifact (`f4941ff` / `9c6b9063…7528`) verified byte-identical across git history and working tree
3. **9 untracked Consumer documents that exist only in a local working tree** — these are the primary governance risk identified by this audit

The goal of this G0 baseline is to make system governance traceable through git history and remote repositories, not through local working directories, agent memory, or session context.
