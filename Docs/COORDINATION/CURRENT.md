# Cross-Agent Coordination — Current State

**Workstream**: EB-0.3B Evidence Resolution Boundary Discovery
**Status**: OPEN — Owner **Contract v0.2 Freeze Candidate Finalization v1 已入册**（DEC-030）· **接口键命名 `source_content_sha256` 已采纳**（OQ-8′ 关闭；全文词面收口完成，`source_version_id` 专用化为 V3 内部 FK）· **bytes 能力冻结确认**（传输 OQ-12″ 仍暂缓）· **双状态体系终局确认** · **废止旧「Semantic Unavailable」表述** · Contract v0.2 = **Freeze Candidate Finalized**（六项冻结范围；DRAFT / NOT FROZEN；DA 表 34 行；OQ 1~21）· **等待 Owner Freeze 令（五步序 Step 3）** · preprocessing @ `1657625`（Producer Alignment v5 并行，待 DEC-030 键名双边确认）
**Last Updated**: 2026-09-16
**Canonical Ledger**: DSH repo (kurt-wong/Aitutors-preprocessing). This is V3 mirror.

---

## Owner Decisions (2026-09-16 — architecture only, implementation not started)

| ID | Decision |
|---|---|
| DEC-020 | **B1 Transport**: Manifest + IR 双层接口（**保留**，2026-09-16 确认）。Manifest = Source Identity Authority；IR = Semantic Consumption Authority；经 `source_version_id` 关联。**语义消费方向 = IR → V3**。**DEC-B1 细化**（preprocessing `bbb5c70`，ODR §1bis）：`source_version_id` 为唯一关联键；**source 身份不依赖 IR 存在**（身份自足，IR 缺席不使身份失效；反向不成立） |
| DEC-021 | **B2 Identity**: 唯一 source identity = `SHA-256(raw bytes)`；`source_version_id` = 该 sha 值本身；canonical_json / body_hash / line_hash / integrity_hash / norm_sha256 只能作内部校验，不得替代 source identity。⚠️ **与 DSH 侧 `DEC-021`（= 本轮四项裁决）同号异文**，引用须双向标注 |
| DEC-022 | **B3 Semantic Boundary**: unit_type 必须闭集；unknown 值禁止自动转换 / 禁止 fallback / 禁止静默 skip / 不得进入 Question materialization。**词表部分已被 DEC-025 取代**（UNKNOWN/PENDING 泛称 → 四值）。⚠️ **与 DSH 侧 `DEC-022`（= Interface Decision Finalization v1）同号异文**，引用须双向标注 |
| **DEC-023** | **Interface Scope**（≡ DSH DEC-021-1）: Interface Scope = **87**（v2 字段口径）；IR 当前冻结面 = **71 ADMITTED**。166 = 历史资产规模 ≠ 正式接口。回填范围 = 87 |
| **DEC-024** | **Legacy v1 Handling**（≡ DSH DEC-021-2）: v1 legacy **79** = historical asset，**不入 v0.2 接口**。四禁：自动迁移 / 自动补齐 / 自动重新生成 IR / 自动加入 87。未来走独立 **Legacy Migration Plan**，不得混入当前 Contract。**关闭 OQ-6** |
| **DEC-025** | **Semantic Boundary 四状态机**（≡ DSH DEC-021-3）: **READY / INCOMPLETE / PENDING_REVIEW / REJECTED**。三禁令（auto conversion / silent fallback / silent skip）。**层归属已裁（DEC-027 Part 5，OQ-5 关闭 = 不合并）**；**词表与路由已终局（DEC-028 Part 5/6）**：语义层 `{ready,incomplete,unknown}` + 决策层 `{pending_review,approved,rejected}`，unknown→reviewable record→pending_review |
| **DEC-026** | **Execution Ordering**（≡ DSH DEC-021-4）: 五步 **Step1 冻结接口快照 → Step2 回填 source_version_id → Step3 冻结 Contract v0.2 → Step4 数据治理 → Step5 图片恢复**。身份冻结优先。**契约冻结 = Step 3**，前置 = Step1+Step2。**五步零 V3 实现动作** → V3 实现排期 = UNKNOWN |
| **DEC-027** | **Interface Decision Finalization v1**（≡ DSH DEC-022，ODR v1.3 §1quater）: Part1 双层职责正式采用+双禁 · Part2 生产/消费责任边界（V3 六项消费义务） · Part3 Scope 87/71 三禁 · Part4 16 份正常态 · Part5 UNKNOWN 属语义层、不合并 · Part6 v0.2 只冻结三件。⚠️ **与 V3 `DEC-022`(B3) 同号异文** |
| **DEC-028** | **Interface Finalization Revision v1**（≡ DSH DEC-023，ODR v1.4 §1quinquies）: **Part1 source identity = SHA256(raw bytes) 64 小写 hex + 「Source identity belongs to content hash, not storage location」+ path 非身份（禁暗示 path 参与身份/版本/hash 判断）** · Part2 `source_file` = locator 非 identity，路径变化不改 id · **Part3 16 份改 Identity Available / Semantic Pending（可恢复），IR 重生成允许+四约束** · Part4 Scope 保持 87（禁 IR=Interface） · **Part5 语义层终局词表加 `unknown`（`{ready,incomplete,unknown}`）+ 决策层 `{pending_review,approved,rejected}`，禁合并** · **Part6 unknown → reviewable record → pending_review workflow**。⚠️ **与 V3 `DEC-023`(Interface Scope) 同号异文（第三处撞号）** |
| **DEC-029** | **Freeze Candidate Review v1**（Owner 六条原则）: **原则5 接口键命名提案 = `source_content_sha256`**（`PROPOSAL`；**已由 DEC-030 采纳**）· **原则6 source bytes 交付只冻能力、不冻传输**（能力 = V3 必须能得 raw bytes + 重算验证 fail-closed + 独立 IR = binding；传输 HOW = 暂缓 OQ-12″）· 原则3 16 份四保证对齐。契约冻结范围 = **六项**（+bytes 能力） |
| **DEC-030** | **Freeze Candidate Finalization v1**（Owner Final Decision）: **D1 接口键命名 `source_content_sha256` = SHA256(raw bytes) 已采纳**（path 禁参与 identity；V3 内部 `source_version_id` 保持内部含义 = uuid.UUID FK，非跨系统键；契约全文词面收口完成；OQ-8′ 关闭）· **D2 bytes 能力冻结确认**（取得 raw bytes + 独立 SHA256 + 比对 + fail-closed；不冻结传输方式）· **D3 双状态体系终局确认**（Semantic `ready/incomplete/unknown` + Decision `pending_review/approved/rejected`，禁合并；unknown 单元必须生成 reviewable record 进 pending_review；禁 silent skip/convert/fallback）· **D4 文字收口**（删旧「Semantic Unavailable」表述 · 消除 `source_version_id` 接口键歧义 · 补 bytes 能力要求 · 确认 87/71/16）。**契约文本侧收口完成，仍 NOT FROZEN，待 Owner Freeze 令** |

**跨仓编号对照（引用任一侧必须双向标注）**：四项 V3 = `DEC-023~026` / DSH = `DEC-021-1~4`；Finalization v1 = V3 `DEC-027` / DSH `DEC-022`；Revision v1 = V3 `DEC-028` / DSH `DEC-023`；Freeze Candidate Review = V3 `DEC-029`；**Freeze Candidate Finalization = V3 `DEC-030`**（DSH 侧待登记）。**撞号累积 3 处**：DSH `DEC-021`≠V3 `DEC-021`(B2)；DSH `DEC-022`≠V3 `DEC-022`(B3)；DSH `DEC-023`≠V3 `DEC-023`(Interface Scope)。**`source_version_id` 字段撞名已由 DEC-030 消除**（接口键 = `source_content_sha256`；≠ DEC-record-ID 撞号，后者仍需 Owner 定跨仓编号约定）。**建议 Owner 立即定跨仓编号约定**。

**汇总表位置**：Decision Alignment Table = Contract v0.2 DRAFT §5.3（DA-1~34）；Implementation Status Table = 同文件 §5.4；五步序 = §5.5；冻结范围六项 = §0；责任边界 = §0.5；命名 = §1.2a（DECISION）；bytes 能力 = §2.3；**Freeze 前执行步骤清单 = §8**。V3 消费侧对齐 = Consumer Alignment v3；DEC-029 评审报告 = Freeze Candidate Review（历史记录）。

**开放冻结前提**（v0.2 DRAFT §8，按 DEC-026 五步序 + DEC-030）——**契约文本侧已收口**（命名采纳 + 词面收口 + 废止 Semantic Unavailable + bytes 能力 + 87/71/16）。**Freeze 前剩余（按序）**：Step 1 快照 · Step 2 回填（键名 `source_content_sha256` 已裁，按此回填；OQ-10 md/PDF 分层仍开放）· OQ-18 次序对齐（已收窄为纯次序之争）· DSH 键名双边确认 · OQ-15 legacy 披露 · OQ-21 16 份呈现机制 · **Owner Freeze 令（Step 3）**。**已不再阻塞**：~~OQ-8 命名~~（DEC-030 已裁）· ~~OQ-8 格式~~（64 hex）· ~~OQ-12 身份维度~~（path 非身份）· ~~OQ-12′ bytes 能力~~（→冻结；传输 OQ-12″ 暂缓）· ~~OQ-5/OQ-19/OQ-20 值集~~ · ~~OQ-14~~（Semantic Pending）· ~~OQ-6~~/~~OQ-11 当前面~~/~~排期归属~~。**V3 实现无五步对应步骤，排期 UNKNOWN**。

---

## Agents

| Agent | Repo | Commit | Status |
|---|---|---|---|
| Claude (V3) | AITutors-v3 | 5dc86aa | freeze_candidate_finalization_v1_naming_adopted_text_finalized |
| DSH (Preprocessing) | Aitutors-preprocessing | 1657625 | odr_v14_producer_alignment_v5_parallel_pending_dec030_keyname_bilateral_confirm |

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
| FACT-038 | **V3 双层权威双半边均不符合**: Manifest 身份对账未达成（0/166 载体 + V3 零身份校验代码，`identity_version`/`C-IN-1` 全仓 0 命中）；IR 语义消费未达成（V3 语义全来自 manifest，IR 零消费）。**净效果 = 用身份层承载语义消费，且无身份锚**。C-IN-1 仅 producer 侧已实现（IR 生成拒收），V3 消费面无对应闸门 | V3 | observed |
| FACT-039 | **四状态机结构性表达缺口（本轮 V3 侧核心发现）**: READY/INCOMPLETE ∈ `SEMANTIC_STATUS`（冻结 BUG-V3-018）；PENDING_REVIEW/REJECTED ∈ `DECISION_STATUS`（冻结 10 §5.2）——**两个正交冻结层**。`decision_status` 只存在于 candidate，candidate 只由 ready 单元产生 → **非 ready 单元永远进不了 PENDING_REVIEW/REJECTED**。四状态个体可表达，但对 unknown semantic **不可联合可达**。四值是逻辑词表还是单一状态机（须解冻两个域）= **未裁，OQ-5**。三禁令在 V3 全部违反，且是同一条链的三个切面 | V3 | observed |
| FACT-040 | **语义覆盖悬崖（跨侧）**: 接口面 87 中 **16 份**（87−71）无 IR 语义承载。**已裁（DEC-027 Part 4）= Identity Available / Semantic Unavailable 正常态**，关闭 OQ-14 + DSH D-2；V3 仍无身份/语义分离消费能力 | Both | **resolved (DEC-027 Part 4)** |
| FACT-041 | **`source_version_id` 同名异义（跨边界新登记）**: 契约键 = sha256 hex（`SHA256(raw bytes)`）；V3 代码键 = `uuid.UUID` FK（`document_source_versions` 行主键，Seal 唯一锚 `(stage,LE-hash)`，`source.py:50` 明令禁 sha 唯一）。同名、异义、异类型；V3 另有第三概念 `Document.original_sha256`（现为 canonical_json 包裹 joined-text 非 raw bytes）。须 v0.2 消歧（OQ-20） | V3 | observed |
| FACT-042 | **OQ-5 关闭 + OQ-14 关闭（DEC-027 Part 5/4）**: Part5 裁不合并两状态体系、UNKNOWN 属语义层 → 关闭 OQ-5（非单一状态机）；但打开两项更精确 V3 缺口——语义层缺 `unknown` 取值须解冻 BUG-V3-018（OQ-20）、candidate 仅由 ready 产致 unknown→PENDING_REVIEW 不可达（OQ-19）。Part4 裁 16 份正常态 → 关闭 OQ-14。**关闭一个开放项换来两个更精确实现前置** | Both | observed |
| FACT-043 | **Part 2 V3 六项消费义务全未实现（DEC-027）**: V3 = 验证 Manifest + 重算 hash + 判断接受 + 验证 IR + Gate + 拒收。六项全无——无校验（`manifest_reader.py:52`）、不读 producer sha（自算 canonical_json 包裹，`runner.py:71-73`）、无身份闸门（`identity_version` 0 命中）、零 IR 消费。同算法对账生产侧 71/71 已实证可行。可执行前提 = source bytes 可达（OQ-12） | Both | observed |
| FACT-044 | **path 非身份原则 V3 侧核验（DEC-028 Part 1/2）**: V3 仅将 `source_file` 用作 `Path(manifest.source_file)` 加载源文件（`runner.py:241`/`runner_b2.py:320`/`runner_b3.py:184`），全仓**无任何以 path 做身份/版本/hash 判断**的代码 → **符合**「Source identity belongs to content hash, not storage location」。跨系统双层当前靠 path 值相等关联 = 不合规现状；升级 `source_version_id` 关联 = not started。残余 = bytes 如何交付 V3 重算（OQ-12′） | V3 | observed |
| FACT-045 | **语义层终局词表 + 路由已裁（DEC-028 Part 5/6）**: `SEMANTIC_STATUS` 终局 = `{ready,incomplete,unknown}`（加 unknown，取代四状态机合并记法）+ `DECISION_STATUS` = `{pending_review,approved,rejected}`，禁合并；unknown → reviewable record → pending_review（关闭 OQ-19 路由 + OQ-20 值集）。V3 现状：`SEMANTIC_STATUS` 冻结 `{ready,incomplete}` 须解冻加值（not started）；unknown→pending_review 在 candidate-gated-on-ready 架构下无执行面（not started）；reviewable record 载体 = UNKNOWN | Both | observed |
| FACT-046 | **Freeze Candidate Review 两决策（DEC-029 原则5/6）**: (a) 接口键命名提案 = `source_content_sha256`（PROPOSAL；**已由 DEC-030 采纳，见 FACT-047**）。(b) source bytes 交付只冻能力（V3 必须能得 raw bytes + 重算验证 fail-closed + 独立 IR = binding）、传输暂缓（OQ-12″）。零 V3 实现、零数据 | Both | observed |
| FACT-047 | **Freeze Candidate Finalization（DEC-030）**: (a) 接口键命名 `source_content_sha256` **已采纳**（=SHA256(raw bytes) 64 hex；V3 内部 `source_version_id` = uuid.UUID FK 专用化为内部词面；契约全文词面收口完成，52 处新名；OQ-8′ 关闭）。(b) bytes 能力冻结确认。(c) 双状态体系终局确认（禁合并；unknown→reviewable record→pending_review；禁 silent skip/convert/fallback）。(d) 废止旧「Semantic Unavailable」表述；87/71/16 确认。契约 = Freeze Candidate Finalized，仍 NOT FROZEN。零代码、零数据 | V3 | observed |

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
| EB-009 | Integration Contract v0.2 freeze readiness | **Freeze Candidate Finalized / NOT FROZEN**（DEC-030）— 冻结范围 = **六项**（DEC-029 + DEC-030）。**命名 `source_content_sha256` 已采纳**（OQ-8′ 关闭，词面收口完成）· **bytes 能力冻结确认**。**契约文本侧已收口**。冻结 = 五步序 Step 3。**Freeze 前剩余（按序）** = Step1 快照 · Step2 回填（新名）+ OQ-10 · OQ-18 次序对齐 · DSH 键名确认 · OQ-15 · OQ-21 · **Owner Freeze 令**。**已不再阻塞**：~~OQ-8 命名/格式~~/~~OQ-12 身份~~/~~OQ-12′ 能力~~/~~OQ-5/19/20 值集~~/~~OQ-14~~/~~OQ-6~~/~~OQ-11 当前面~~/~~排期归属~~。**V3 identity verification = not implemented（not started）；V3 用 path 作 locator 已符合 path 非身份；V3 实现无五步对应步骤，排期 UNKNOWN** |

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
| **Decision Alignment Report（B1/B2/B3 逐项；DECISION/IMPLEMENTATION/UNKNOWN 三态）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-DECISION-ALIGNMENT-REPORT.md` |
| **Consumer Decision Alignment v1（FINALIZATION 四项裁决 V3 侧对齐；已被 v2 取代，保留审计）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v1.md` |
| **Consumer Alignment v2（Interface Decision Finalization v1 V3 侧对齐；已被 v3 取代，保留审计）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v2.md` |
| **Consumer Alignment v3（Interface Finalization Revision v1 V3 侧对齐；取代 v2；Part 10 格式 Decision Alignment Summary + Remaining UNKNOWN）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v3.md` |
| **Contract v0.2 DRAFT（Freeze Candidate Finalized，DRAFT / NOT FROZEN；§0 冻结范围六项 + §0.5 责任边界 + §1.2/§1.2a 接口键命名 `source_content_sha256`（DECISION）+ §2.3 bytes 能力 + §8 Freeze 前执行步骤清单；DA-1~34）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` |
| **Contract v0.2 Freeze Candidate Review（DEC-029 历史记录；命名提案已由 DEC-030 采纳）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-FREEZE-CANDIDATE-REVIEW.md` |
| Handoff 007 (B1/B2/B3 → DSH confirm; 含勘误横幅) | `Docs/COORDINATION/HANDOFFS/2026-09-16-Claude-to-DSH-007.md` |
