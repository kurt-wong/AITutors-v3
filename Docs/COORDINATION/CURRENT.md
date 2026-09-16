# Cross-Agent Coordination — Current State

**Workstream**: EB-0.3B Evidence Resolution Boundary Discovery
**Status**: OPEN — Owner **B1/B2/B3 架构已裁决**（DEC-020/021/022 ≡ DSH DEC-019）· **B1 双层保留**（2026-09-16 确认）· Contract v0.2 DRAFT 已并入 IF-v2/Readiness 事实，含两张汇总表 · **NOT FROZEN** · preprocessing @ `b39b6da`（IF-v2 + Readiness 交付）
**Last Updated**: 2026-09-16
**Canonical Ledger**: DSH repo (kurt-wong/Aitutors-preprocessing). This is V3 mirror.

---

## Owner Decisions (2026-09-16, architecture only — implementation not started)

| ID | Decision |
|---|---|
| DEC-020 | **B1 Transport**: Manifest + IR 双层接口（**保留**，2026-09-16 确认）。Manifest = Source Identity Authority；IR = Semantic Consumption Authority；经 `source_version_id` 关联。**语义消费方向 = IR → V3** |
| DEC-021 | **B2 Identity**: 唯一 source identity = `SHA-256(raw bytes)`；`source_version_id` = 该 sha 值本身；canonical_json / body_hash / line_hash / integrity_hash / norm_sha256 只能作内部校验，不得替代 source identity |
| DEC-022 | **B3 Semantic Boundary**: unit_type 必须闭集；unknown 值 **禁止自动转换 / 禁止 fallback / 禁止静默 skip / 不得进入 Question materialization**；处理方式 UNKNOWN/PENDING_REVIEW |

**汇总表位置**：Decision Alignment Table = Contract v0.2 DRAFT §5.3；Implementation Status Table = 同文件 §5.4。

**开放冻结前提**（v0.2 DRAFT §8）：Owner 批准冻结候选 · DSH 确认接口变更面（OQ-8 字段命名 / OQ-12 `source_file` 形态 / 接口面 87）· OQ-5 UNKNOWN/PENDING_REVIEW 落层（涉冻结值域）· 排期归属 · OQ-11 IR 面 71 vs 扩产 + OQ-6 v1 面 79 份。

---

## Agents

| Agent | Repo | Commit | Status |
|---|---|---|---|
| Claude (V3) | AITutors-v3 | 1243a7f | v02_draft_updated_if_v2 |
| DSH (Preprocessing) | Aitutors-preprocessing | b39b6da | if_v2_readiness_delivered_pending_contract_v02 |

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
| FACT-030 | **B1 transport mismatch**: contract says V3 consumes IR; V3 reads manifest only (0 hits for `resolver_ir\|source_sha256` @ backend/) | V3 | observed, **blocks freeze** |
| FACT-031 | **B2 hash algorithm mismatch**（行号已勘误）: `sha256_hex` via canonical_json always DIFFER; splitlines 在 `load_source_lines`（`:27`）非 `compute_body_hash`，`body_hash` 漂移 6/12 结论不变 | V3 | observed_corrected, **架构已裁决 DEC-021** |
| FACT-032 | **B3 unit_type silent failure**（已更正）: 两层矛盾（annotation 洗白为 standalone vs span 按 composite 解析）+ candidate 零落库（incomplete→skip，永不到达 `:252`）；静默失败掩盖 | V3 | observed_corrected, **blocks freeze** |
| FACT-033 | DQE §1-A「已生效」+ Closure Plan §2「fail-closed 生效中」—— **DSH 已正式撤回**（Reconciliation v0.2 §B3 @ `ad1abdd`），双方对齐 | V3 | **resolved** |
| FACT-034 | Figure: 70,838 refs, 27,240 dangling (unrecovered `imgs/`); V3 `SourceFigure` field-level non-interoperable | Both | observed, not a blocker |
| FACT-035 | **B1 producer 合取约束**: 无单一输出面同时具备全语料覆盖+md sha 锚+持续产出；identity 面 87 v2 / 79 v1，覆盖面以 87 为上限 | Both | observed, **blocks freeze** |
| FACT-036 | **B2 producer hash 穷举**: 输出面仅原始字节 SHA-256 单族；`body_hash`/`line_hash` producer 零产出；`norm_sha256` 算法在仓内定义但从未作接口发布 | Both | observed |
| FACT-037 | **B1-B3 producer readiness (IF-v2)**: manifest 0/166 携 `source_version_id`；IR 71/71 sha 自洽但覆盖 43.4%；双层现有关联 = 绝对路径值相等；identity 面双口径 87/79 vs 88/78；B2 producer 侧已 READY 零动作；unit_type 双侧零守卫 | Both | observed |

---

## Open Questions

| ID | Question | Status |
|---|---|---|
| EB-001 | HTML ownership | Blocked by P3.2 |
| EB-002 | options_region in production Resolver | Open (V3 adoption gap) |
| EB-003 | Missing punctuation contextual rule | Open |
| EB-004 | _locate_options() CONTRACT GAP | Open, confirmed |
| EB-005 | Formula FP structural exclusion | Open, INFERRED |
| EB-008 | Admission Evidence Authority enforcement | **Implementation completed, external adversarial verification pending** (P1 local: 88aeae8 + notes b5ddbe3; External verification evidence unavailable in current repository state; NOT VERIFIED / NOT DSH approved / step-6 NOT released) |
| EB-009 | Integration Contract v0.1 freeze | **NOT FROZEN** — BLOCK B1 (transport) / B2 (hash) / B3 (unit_type)。根因 = B1；无实现决策。待 Owner 裁决传输层 |

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
| Preprocessing ↔ V3 Integration Contract (DRAFT v0.1) | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT.md` |
| EB-008 P1 Implementation Notes | `Docs/COORDINATION/EVIDENCE/EB008-P1-IMPLEMENTATION-NOTES.md` |
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
| Consumer Review v0.1 (baseline `1fbaf5e`) | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW.md` |
| **Consumer Review v0.2 (freeze verdict, DQE baseline `4d78513`)** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW-v0.2.md` |
| **Contract Blocker Analysis（Owner 裁决材料，非契约/非冻结；CB 三项已标 DECIDED 架构）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-BLOCKER-ANALYSIS.md` |
| **V3 Consumer Gap Map（V3 消费面事实 + 对 BLOCKER-ANALYSIS 两处更正 + DECISION 状态）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONSUMER-GAP-MAP.md` |
| **Decision Alignment Report（Owner 裁决对齐；DECISION/IMPLEMENTATION/UNKNOWN 三态）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-DECISION-ALIGNMENT-REPORT.md` |
| **Contract v0.2 DRAFT（冻结候选，NOT FROZEN）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` |
| Handoff 007 (B1/B2/B3 → DSH confirm; 含勘误横幅) | `Docs/COORDINATION/HANDOFFS/2026-09-16-Claude-to-DSH-007.md` |
