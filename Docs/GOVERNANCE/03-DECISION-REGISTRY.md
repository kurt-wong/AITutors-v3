# G0 Decision Registry

**Generated**: 2026-09-17 (G0 Governance Reset)
**Purpose**: Reconcile all DEC-* identifiers across both repositories, detect collisions, and trace decision provenance.

**Search scope**: Current local working tree + git tracked files + git history + GitHub remote (all four verified).

---

## 1. Two Independent DEC Numbering Systems

The system has **two separate DEC numbering sequences** that overlap and collide:

| System | Repository | Range | Maintained by | Format |
|---|---|---|---|---|
| **V3 Consumer DEC** | AITutors-v3 | DEC-001 ~ DEC-036 | Claude (V3 agent) | `Docs/COORDINATION/CURRENT.md` + `state.yaml` |
| **DSH Producer DEC** | Aitutors-preprocessing | DEC-012 ~ DEC-049 | DSH (Producer agent) | `Docs/COORDINATION/log.md` + `CURRENT.md` + `state.yaml` |

**These are NOT the same decisions.** A DEC-021 on the Consumer side and a DEC-021 on the Producer side are completely different adjudications.

---

## 2. Confirmed Numbering Collisions

### Collision Group 1–3: DEC-021 / DEC-022 / DEC-023 (Documented)

| Number | V3 Consumer Meaning | DSH Producer Meaning | Documented? |
|---|---|---|---|
| DEC-021 | B2 Identity: SHA-256(raw bytes) | Interface Decision Finalization v1 (≡ V3 DEC-027) | YES — both CURRENT.md carry warning |
| DEC-022 | B3 Semantic Boundary: closed set | Interface Decision Finalization v1 (≡ V3 DEC-027) | YES |
| DEC-023 | Interface Scope = 87 | Interface Finalization Revision v1 (≡ V3 DEC-028) | YES |

### Collision Group 4: DEC-031 ~ DEC-036 (UNDOCUMENTED — found by this G0 audit)

| Number | V3 Consumer Meaning | DSH Producer Meaning | Documented? |
|---|---|---|---|
| DEC-031 | Owner Final Decision v1 (four principles) | Freeze Artifact remote recheck | **NO** |
| DEC-032 | Freeze pre-final registration | Frozen status final registration | **NO** |
| DEC-033 | Freeze Finalization Audit | Frozen Baseline Final Integrity | **NO** |
| DEC-034 | Freeze Object Final Alignment | Frozen Baseline Archive Final Check | **NO** |
| DEC-035 | Freeze remote reproducibility | Guardian Mode activation | **NO** |
| DEC-036 | Owner Freeze Order (FROZEN) | Guardian During Consumer Phase 1 | **NO** |

**Governance gap**: The V3 CURRENT.md documents collisions for DEC-021/022/023 but NOT for DEC-031~036. 6 additional collisions exist without documentation.

---

## 3. V3 Consumer Decision Map (DEC-001 ~ DEC-036)

| DEC | Title | Git Status | Notes |
|---|---|---|---|
| DEC-001~009 | Early architecture decisions | TRACKED | In CURRENT.md history |
| DEC-012 | Deferred items (N3~N6) | TRACKED | |
| DEC-013 | — | TRACKED | |
| DEC-016 | — | TRACKED | |
| DEC-020 | B1 Transport: Manifest + IR dual-layer | TRACKED | |
| DEC-021 | B2 Identity: SHA-256(raw bytes) | TRACKED | ⚠️ Collides with DSH DEC-021 |
| DEC-022 | B3 Semantic Boundary: closed set | TRACKED | ⚠️ Collides with DSH DEC-022 |
| DEC-023 | Interface Scope = 87 | TRACKED | ≡ DSH DEC-021-1; ⚠️ Collides with DSH DEC-023 |
| DEC-024 | Legacy v1 Handling | TRACKED | ≡ DSH DEC-021-2 |
| DEC-025 | Semantic Boundary four-state machine | TRACKED | ≡ DSH DEC-021-3 |
| DEC-026 | Execution Ordering five steps | TRACKED | ≡ DSH DEC-021-4 |
| DEC-027 | Interface Decision Finalization v1 | TRACKED | ≡ DSH DEC-022 |
| DEC-028 | Interface Finalization Revision v1 | TRACKED | ≡ DSH DEC-023 |
| DEC-029 | Freeze Candidate Review v1 | TRACKED | |
| DEC-030 | Freeze Candidate Finalization v1 | TRACKED | ≡ DSH DEC-025 |
| DEC-031 | Owner Final Decision v1 | TRACKED | ≡ DSH DEC-026; ⚠️ Undocumented collision |
| DEC-032 | Freeze pre-final registration | TRACKED | ⚠️ Undocumented collision |
| DEC-033 | Freeze Finalization Audit | TRACKED | ⚠️ Undocumented collision |
| DEC-034 | Freeze Object Final Alignment | TRACKED | ⚠️ Undocumented collision |
| DEC-035 | Freeze remote reproducibility | TRACKED | ⚠️ Undocumented collision |
| DEC-036 | **Owner Freeze Order — Contract v0.2 FROZEN** | TRACKED | **Latest V3 DEC**; ⚠️ Undocumented collision |

## 4. DSH Producer Decision Map (DEC-012 ~ DEC-049)

| DEC | Title | Git Status |
|---|---|---|
| DEC-012~020 | Early coordination decisions | TRACKED |
| DEC-021 | Interface Decision Finalization (= V3 DEC-027) | TRACKED |
| DEC-022 | Interface Decision Finalization v1 (= V3 DEC-027) | TRACKED |
| DEC-023 | Interface Finalization Revision v1 (= V3 DEC-028) | TRACKED |
| DEC-025 | Freeze Candidate Finalization (= V3 DEC-030) | TRACKED |
| DEC-026 | Owner Final Decision execution (= V3 DEC-031) | TRACKED |
| DEC-027 | Contract v0.2 Freeze Evidence + consistency | TRACKED |
| DEC-028 | Producer Freeze final confirmation | TRACKED |
| DEC-029 | Freeze Producer Final Audit | TRACKED |
| DEC-030 | Producer Final Freeze Object Verification | TRACKED |
| DEC-031 | Freeze Artifact remote recheck | TRACKED |
| DEC-032 | Frozen status final registration | TRACKED |
| DEC-033 | Frozen Baseline Final Integrity | TRACKED |
| DEC-034 | Frozen Baseline Archive Final Check | TRACKED |
| DEC-035 | Guardian Mode activation | TRACKED |
| DEC-036 | Guardian During Consumer Phase 1 | TRACKED |
| DEC-037 | Consumer Phase 2 pre-start baseline | TRACKED |
| DEC-038 | Guardian checkpoint round 2 | TRACKED |
| DEC-039 | Guardian During Phase 2-M3 | TRACKED |
| DEC-040 | Phase 2-M4 Guardian Check | TRACKED |
| DEC-041 | Adversarial review of DEC-040 | TRACKED |
| DEC-042 | Consumer M5 Boundary Guardian Review | TRACKED |
| DEC-043 | Adversarial review of DEC-042 | TRACKED |
| DEC-044 | Consumer Boundary Closure Review order | TRACKED |
| DEC-045 | DSH self adversarial audit | TRACKED |
| DEC-046 | Owner ruling on DEC-045 | TRACKED |
| DEC-047 | Consumer Boundary Closure Guardian Review | TRACKED |
| DEC-048 | Phase 2.5 Guardian Review | TRACKED |
| DEC-049 | D2/D3/D4 Decision Brief | TRACKED | **Latest DSH DEC** |

---

## 5. Cross-Repo Mapping (Bidirectional)

| Concept | V3 Consumer DEC | DSH Producer DEC |
|---|---|---|
| B1 Transport | DEC-020 | — |
| B2 Identity | DEC-021 | — |
| B3 Semantic Boundary | DEC-022 | — |
| Four interface decisions | DEC-023~026 | DEC-021-1~4 |
| Finalization v1 | DEC-027 | DEC-022 |
| Revision v1 | DEC-028 | DEC-023 |
| Freeze Candidate Finalization | DEC-030 | DEC-025 |
| Owner Final Decision | DEC-031 | DEC-026 |
| Freeze registration chain | DEC-032~036 | DEC-027~032 |
| Guardian review chain | — | DEC-033~049 |

---

## 6. OQ (Open Question) Registry

| OQ | Topic | Status |
|---|---|---|
| OQ-5 | Four-value vocabulary layering | CLOSED (DEC-027 Part 5) |
| OQ-6 | Legacy v1 handling | CLOSED (DEC-024) |
| OQ-8 | Naming/format | CLOSED (DEC-030) |
| OQ-10 | PDF face source_content_sha256 backfill | **DEFERRED** |
| OQ-11 | Current interface face | CLOSED |
| OQ-12″ | Transport HOW | **DEFERRED** |
| OQ-13 | — | **DEFERRED** |
| OQ-15 | — | **DEFERRED** |
| OQ-16 | PENDING_REVIEW→REJECTED routing rule | **UNKNOWN** |
| OQ-16′ | pending→rejected criteria + carrier | **OPEN** |
| OQ-17 | 1 existing non-standard unit_type | **OPEN** |
| OQ-18 | Five-step priority | CLOSED (DEC-031) |
| OQ-20 | Semantic `unknown` value set | CLOSED (DEC-028 Part 5) |
| OQ-21 | 16 units presentation mechanism | **OPEN** |

---

## 7. Decision Integrity Findings

### Finding 1: Undocumented DEC-031~036 collisions
6 additional collisions beyond the 3 documented ones. Both repos should flag these.

### Finding 2: No unified DEC numbering
DEC-031 recommended deferring unified DEC numbering. Unresolved. Dual numbering remains active.

### Finding 3: All decisions are git-tracked
Every DEC entry in both repos is in TRACKED git files. **No decision exists only in an untracked file.** This is positive.

### Finding 4: Design v1.1 authority unclear
DSH Guardian reviews (DEC-035~049) treat Consumer Design v1.1 as a key authority for D2/D3/D4. But Design v1.1 is **untracked and has never entered git**. Its authority level is **Unknown** — it is not L0 (not Frozen Spec), not L2 (not in Docs/DECISIONS/), not L1 (not the Contract). It appears to be a self-declared design document that DSH Guardian elevated to quasi-authority through citation.
