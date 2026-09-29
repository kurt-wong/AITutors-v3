# G0 Claim Registry

**Generated**: 2026-09-17 (G0 Governance Reset)
**Purpose**: Trace key governance claims to their actual source evidence. Each claim verified against local file, git tracked state, git history, and remote — not accepted from agent reports alone.

---

## C-001: Contract v0.2 is FROZEN

| Field | Value |
|---|---|
| **Claim** | "Contract v0.2 = FROZEN (DEC-036, Owner Freeze order 2026-09-16)" |
| **Claim Source** | Consumer CURRENT.md, restart-prompt.md v1.67 |
| **Repository** | Both |
| **Path** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` |
| **Commit** | `f4941ff` (freeze artifact) |
| **Local/Remote** | BOTH |
| **Authority** | L1 (FROZEN) |
| **Evidence** | `git show f4941ff:<path> \| sha256sum` = `9c6b9063…7528` == registered value. Current HEAD tracked version identical. Size = 92,197 bytes. `git merge-base --is-ancestor f4941ff origin/main` = TRUE. |
| **Result** | **VERIFIED** |

## C-002: Design v1.1 is the source of D2/D3/D4 interface definitions

| Field | Value |
|---|---|
| **Claim** | "Design v1.1 §4.7 contains V3-side self-declared freeze defining D2/D3/D4" |
| **Claim Source** | DSH DEC-049 (Producer log.md) |
| **Repository** | Consumer |
| **Path** | `…/PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md` |
| **Commit** | **NONE — never committed** |
| **Local/Remote** | **LOCAL ONLY** |
| **Authority** | **Unknown** |
| **Evidence** | `git log --all -- <path>` = EMPTY. File exists in local working tree only. DSH Guardian DEC-035~049 cite it extensively. Zero git traceability. |
| **Result** | **VERIFIED as governance risk** — cited as authority but no git history |

## C-003: V3 has zero identity_version checking

| Field | Value |
|---|---|
| **Claim** | "identity_version 在 V3 全仓代码 0 命中" |
| **Claim Source** | Consumer Decision Alignment v1 §1.1 |
| **Path** | `backend/**/*.py` |
| **Commit** | `cc12d79` |
| **Local/Remote** | BOTH |
| **Evidence** | `Grep identity_version @ backend/**/*.py` = 0 hits. M1 reads `source_content_sha256` but not `identity_version`. |
| **Result** | **VERIFIED** |

## C-004: SEMANTIC_STATUS frozen at {ready, incomplete}

| Field | Value |
|---|---|
| **Claim** | "SEMANTIC_STATUS = frozenset({'ready', 'incomplete'}) — BUG-V3-018 frozen" |
| **Claim Source** | Frozen Spec 20 §6.2; compile/__init__.py:29 |
| **Path** | `backend/app/domains/compile/__init__.py` |
| **Commit** | `cc12d79` |
| **Local/Remote** | BOTH |
| **Authority** | L0 (Frozen Spec) + code |
| **Evidence** | `compile/__init__.py:29` = `frozenset({"ready", "incomplete"})`. DEC-028 Part 5 ordered adding `unknown` but code unchanged. |
| **Result** | **VERIFIED** — code still frozen at 2 values despite DEC-028 Part 5 |

## C-005: Non-ready units are silently skipped

| Field | Value |
|---|---|
| **Claim** | "非 ready 单元在 runner_b2.py 被 skip，无通道进入 pending_review" |
| **Claim Source** | Consumer Decision Alignment v1 §2.2 |
| **Path** | `backend/scripts/preprocessing_consumer/runner_b2.py` |
| **Commit** | `cc12d79` |
| **Local/Remote** | BOTH |
| **Evidence** | Lines 322-329: `semantic_status != "ready"` → `skip_count += 1`, `status="skipped"`, `continue` |
| **Result** | **VERIFIED** |

## C-006: Both repos are in sync with remote

| Field | Value |
|---|---|
| **Claim** | "Local HEAD == origin/main for both repos" |
| **Claim Source** | This G0 audit |
| **Commit** | Consumer: `cc12d79`; Producer: `2b92898` |
| **Local/Remote** | BOTH |
| **Evidence** | `git fetch` then `git rev-parse HEAD` vs `origin/main` — identical for both. Zero ahead/behind. |
| **Result** | **VERIFIED** |

## C-007: 9 untracked Consumer documents have never entered git

| Field | Value |
|---|---|
| **Claim** | "9 docs in CONTRACTS/ are untracked with zero git history" |
| **Claim Source** | This G0 audit |
| **Path** | `Docs/COORDINATION/CONTRACTS/` (9 files) |
| **Commit** | N/A |
| **Local/Remote** | **LOCAL ONLY** |
| **Authority** | **Unknown** |
| **Evidence** | Each file: `git log --all -- <path>` = EMPTY. `git ls-files --others --exclude-standard` confirms. |
| **Result** | **VERIFIED** |

## C-008: Producer working tree is completely clean

| Field | Value |
|---|---|
| **Claim** | "Producer: zero untracked, zero modified, zero deleted" |
| **Commit** | `2b92898` |
| **Evidence** | `git status --short` = empty. All `--others`/`--deleted`/`--modified` = empty. |
| **Result** | **VERIFIED** |

## C-009: DSH DEC-049 Decision Brief exists and is tracked

| Field | Value |
|---|---|
| **Claim** | "D2/D3/D4 Decision Brief delivered with 13-point evidence structure" |
| **Path** | Producer `Docs/COORDINATION/INTEGRATION/PREPROCESSING-D2-D3-D4-DECISION-BRIEF-v1.md` |
| **Commit** | `2b92898` |
| **Local/Remote** | BOTH |
| **Authority** | L3 (report) |
| **Evidence** | File tracked at HEAD. Producer log.md DEC-049 entry describes full evidence structure. |
| **Result** | **VERIFIED** |

## C-010: Frozen Spec volumes are all tracked and on remote

| Field | Value |
|---|---|
| **Claim** | "V3_SPEC 9 volumes are L0, tracked and on remote" |
| **Path** | `Docs/V3_SPEC/` |
| **Commit** | `cc12d79` |
| **Local/Remote** | BOTH |
| **Authority** | L0 |
| **Evidence** | `git ls-files Docs/V3_SPEC/` = 9 files, all at HEAD, all on origin/main. |
| **Result** | **VERIFIED** |

## C-011: CLAUDE.md was intentionally deleted

| Field | Value |
|---|---|
| **Claim** | "CLAUDE.md dropped as governance violation fix" |
| **Path** | `CLAUDE.md` |
| **Commit** | `72af28d` (deletion) |
| **Local/Remote** | HISTORY |
| **Authority** | None |
| **Evidence** | `git log --all -- CLAUDE.md`: created `2a723a6`, deleted `72af28d`. Message: "fix governance violation — drop CLAUDE.md". |
| **Result** | **VERIFIED** — intentional, not accidental |

## C-012: DEC numbering collisions

| Field | Value |
|---|---|
| **Claim** | "3 documented collisions (DEC-021/022/023)" |
| **Claim Source** | Consumer CURRENT.md |
| **Evidence** | Consumer CURRENT.md: "撞号累积 3 处". **This G0 audit found 6 MORE**: DEC-031~036 also collide undocumented. |
| **Result** | **VERIFIED (3 documented) + 6 NEW undocumented found** |

---

## Summary

| Result | Count |
|---|---|
| **VERIFIED** | 12 |
| **REFUTED** | 0 |
| **UNVERIFIABLE** | 0 |

### Key Governance Risks

1. **9 untracked documents with zero git traceability** — Design v1.1 cited as authority by DSH Guardian but no git history
2. **6 undocumented DEC numbering collisions** — DEC-031~036
3. **DEC-028 Part 5 not implemented** — `unknown` ordered but SEMANTIC_STATUS still frozen at 2 values
4. **D2/D3/D4 remain OPEN** — Decision Brief delivered, awaiting Owner ruling
