# Cross-Agent Coordination — Current State

**Workstream**: EB-0.3B Evidence Resolution Boundary Discovery
**Status**: OPEN — **Contract v0.2 = Freeze Candidate Finalized / READY FOR FREEZE / NOT FROZEN**（DEC-034 Freeze Object Final Alignment 完成；**禁止写成 Frozen**）· **Freeze Artifact（唯一冻结对象）= commit `f4941ff`** · document `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` · sha256 `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`（git show 实测 == 工作树）· **Freeze Registration = 本轮 DEC-034 账本 commit**（parent `f4941ff`；**不是冻结对象**）· `c6e771c` = DEC-032 历史登记轮（该 commit 处契约 sha `c8d89586…` ≠ artifact，**排除**）· **Step 1 DONE · Step 2 DONE · Verification PASS**（DSH `DEC-026`/`027`/`028`）· 机械冻结条件已满足 · **NOT IMPLEMENTED (V3 capability)** 五项不变 · 一致性检查通过 · 16 份设计已登记 · **V3 侧无剩余冻结前工作** · preprocessing @ `67f564c`
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
| **DEC-031** | **Owner Final Decision v1**: **原则1 Identity Authority 终局确认**（`source_content_sha256` = SHA256(original source bytes) 64 小写 hex；内容 hash 决定身份；path 仅 locator；path 变化不得影响 identity；**禁止任何系统用 path 做唯一身份判断**）· **原则2 双层职责终局确认**（Manifest 回答「这是哪个文件」/ IR 回答「这个文件表达了什么」；V3：Manifest 验证身份、IR 提供语义，不得混淆）· **原则3 命名终局确认**（跨系统 `source_content_sha256` / V3 内部 `source_version_id`；禁两概念同名）· **原则4 16 份处理终局确认**（Identity Available / Semantic Pending；**允许重跑 preprocessing 生成 IR**；约束：sha 保持一致 / 不建新 identity / 不改历史 manifest / 不删已有记录）· **执行授权**：DSH 执行 Step 1 快照（文件列表 + sha + R50 关联）+ Step 2 回填 87 + 逐份验证 Manifest hash = IR hash + 验证报告（87 清单/hash 一致性/IR 覆盖/16 pending）· **冻结条件机械化 = Step 2 完成并验证 → Contract v0.2 Freeze** · **OQ-18 关闭**（五步序优先显式确认）· 五项延期（OQ-15/OQ-13/OQ-10/DEC 编号/OQ-12″）非架构阻塞 · **V3 下一阶段核心风险 = 消费端验证链**（bytes→重算→验证 Manifest→验证 IR→fail-closed） |
| **DEC-032** | **Contract v0.2 Freeze 前最终登记**（Owner 指令，三任务）: **Task 1 状态登记完成**（state.yaml / CURRENT.md / log.md 同步记录 DEC-032 + FACT-049 + EB-009；状态必须 = **Freeze Candidate Finalized / READY FOR FREEZE / NOT FROZEN**，禁止写成 Frozen）· **Task 2 一致性检查通过**（现行定义唯一：`source_content_sha256` = 跨系统内容身份 / `source_version_id` = V3 内部 UUID / `source_file`/path = locator；「Semantic Unavailable」零权威现用，「Semantic Pending」唯一现用词）· **Task 3 提交登记 commit**（不改 V3 代码/schema/数据/IR）· Consumer 侧收口内容同批登记：五项 NOT IMPLEMENTED（契约 §5.6.1 / G-15）· 实现边界（§5.6.2：输入 Manifest+raw bytes+IR → 验证三项 → fail-closed → 成功进既有 Gate/Admission；path→找文件 / SHA256(bytes)→证明身份）· 验证链延伸 Gate→Admission（§2.3）· 16 份设计登记（§1.6 七约束含新旧 IR 血统关系） |
| **DEC-033** | **Contract v0.2 Freeze Finalization Audit·Consumer 侧**（Owner 指令，五任务）: **Task 1 冻结状态描述修正**——Step 1/2 历史「未开始/未完成」统一更新为事实状态 **Step 1 DONE / Step 2 DONE / Verification PASS / READY FOR FREEZE / NOT IMPLEMENTED (V3 capability)**（依据 = DSH `DEC-026`/`027`/`028`，commit `e70807b`/`aad2237`/`67f564c`；只改事实状态，不改架构定义）· **Task 2 Freeze Evidence 引用登记**（契约 §9.1：Step 1 snapshot artifact + Step 2 backfill report + Verification report + Final check evidence + commit hash 五类齐全，含各工件 sha256）· **Task 3 Freeze Object 明确化**（契约 §9.2：唯一冻结对象 = Contract v0.2 DRAFT；document sha256 = `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`；**Freeze Artifact commit = `f4941ff`〔DEC-034 澄清〕**；禁止多个 commit 均作为最终版本）· **Task 4 关键词再验证通过**（`source_version_id` 仅 V3 UUID/历史解释/禁止跨系统 identity；`source_content_sha256` 唯一跨系统身份键；Semantic Unavailable 仅废止记录；path/`source_file` 仅 locator）· **Task 5 报告输出** · 边界保持：Contract freeze ≠ implementation；Requirement ≠ existing capability · 零代码/零 schema/零数据/零 IR/不扩展冻结范围 |
| **DEC-034** | **Freeze Object Final Alignment**（Owner 指令，三任务）: **Task 1 定义统一**——区分 **Freeze Artifact**（= `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` 实际冻结内容版本；repository / commit / document / sha256）与 **Freeze Registration**（= DEC 登记 / 状态更新 / 日志提交；repository / commit / documents）；**禁止两个 commit 同时作为 Contract 冻结对象**；`c6e771c`（DEC-032 历史登记轮，该 commit 处契约 sha `c8d89586…` ≠ artifact）**排除** · **Task 2 Remote 可复现性**——确认 Freeze Artifact commit = remote reachable；未 push 则只 push 不改内容 · **Task 3 文档一致性扫描**——Contract / CURRENT / state.yaml / GAP MAP / log：无 multiple Freeze Object · 无 ambiguous frozen commit · 无 READY/FROZEN 混用 · **Task 4 报告输出** · **契约文档本轮不动**（改之会变更其 sha256，重现多 commit 歧义）· 冻结前不扩展设计范围——唯一待解决 = 冻结对象唯一化 + remote 可复现性 · 边界保持：Contract Freeze ≠ V3 Implementation；Requirement ≠ Existing Capability |

**跨仓编号对照（引用任一侧必须双向标注）**：四项 V3 = `DEC-023~026` / DSH = `DEC-021-1~4`；Finalization v1 = V3 `DEC-027` / DSH `DEC-022`；Revision v1 = V3 `DEC-028` / DSH `DEC-023`；Freeze Candidate Review = V3 `DEC-029`；Freeze Candidate Finalization = V3 `DEC-030` ≡ **DSH `DEC-025`（已登记）**；Owner Final Decision v1 = V3 `DEC-031` ≡ **DSH `DEC-026`（执行轮，已登记）**；Freeze 前最终登记 = V3 `DEC-032`；**Freeze Finalization Audit = V3 `DEC-033`（本轮）**。**DSH 侧 producer 冻结收口 = DSH `DEC-027`（Freeze Evidence v1）+ DSH `DEC-028`（Producer 最终确认）**。**撞号累积 3 处**：DSH `DEC-021`≠V3 `DEC-021`(B2)；DSH `DEC-022`≠V3 `DEC-022`(B3)；DSH `DEC-023`≠V3 `DEC-023`(Interface Scope)。**`source_version_id` 字段撞名已由 DEC-030 消除**（接口键 = `source_content_sha256`；≠ DEC-record-ID 撞号）。**DEC 编号统一 = DEC-031 建议延期项**（文档管理问题，非架构阻塞）。

**汇总表位置**：Decision Alignment Table = Contract v0.2 DRAFT §5.3（**DA-1~36**）；Implementation Status Table = 同文件 §5.4；五步序 = §5.5；**Consumer Boundary 五项 NOT IMPLEMENTED + 实现边界 = §5.6**；冻结范围六项 = §0；责任边界 = §0.5；命名 = §1.2a（DECISION）；**path 边界公式 = §1.3**；bytes 能力 + 验证链（延伸 Gate→Admission）= §2.3；16 份七约束 + 设计登记 = §1.6；**Freeze 前执行步骤清单 = §8**。V3 消费侧对齐 = Consumer Alignment v3；DEC-029 评审报告 = Freeze Candidate Review（历史记录）。

**开放冻结前提**（v0.2 DRAFT §8/§9，按 DEC-026 五步序 + DEC-031/032/033）——**契约文本侧已收口**（DEC-030/031/032/033）；**一致性检查通过**（DEC-032 Task 2 + DEC-033 Task 4 再验证）；**Step 1 = DONE · Step 2 = DONE · Verification = PASS**（DSH `DEC-026`，commit `e70807b`；Freeze Evidence = `aad2237` C1-C9 VERIFIED；Producer 确认 = `67f564c` ALL PASS）→ **机械冻结条件（DEC-031 §六）已满足**。**Freeze Evidence 五类证据已登记**（契约 §9.1：Step 1 snapshot artifact / Step 2 backfill report / Verification report / Final check evidence / commit hash）；**Freeze Object 唯一冻结对象已明确**（契约 §9.2 + 下方 Evidence Locations）。**当前状态 = READY FOR OWNER FREEZE / NOT FROZEN**——按 Owner DEC-033 建议流程，下一步 = **DSH 最终确认 → Owner Freeze 令 → Contract v0.2 Frozen → 进入 V3 Consumer Identity Verification 实现阶段**。**已不再阻塞**：~~Step 1/2 执行~~（**DONE + PASS**）· ~~OQ-18~~（**DEC-031 关闭**）· ~~DSH 键名双边确认~~（已随 Step 1/2 落地）· ~~OQ-15/OQ-13/OQ-10/DEC 编号/OQ-12″ 传输~~（**DEC-031 建议延期，非架构阻塞**）· ~~OQ-8 命名/格式~~/~~OQ-12 身份~~/~~OQ-12′ 能力~~/~~OQ-5/19/20 值集~~/~~OQ-14~~/~~OQ-6~~/~~OQ-11 当前面~~/~~排期归属~~。**开放但不在冻结条件内**：OQ-21（16 份呈现机制）、OQ-17（存量 1 例）、OQ-16′（pending→rejected 准则 + 载体）。**V3 实现无五步对应步骤，排期 UNKNOWN**；**DEC-031 指明 V3 下一阶段核心架构风险 = 消费端验证链**（边界已登记 §5.6.2，五项 NOT IMPLEMENTED §5.6.1）。**当前不应再讨论**（已裁决完毕）：path 是否 identity · `source_version_id` 命名 · 16 份是否重跑 · hash 是否唯一。

---

## Agents

| Agent | Repo | Commit | Status |
|---|---|---|---|
| Claude (V3) | AITutors-v3 | f4941ff | freeze_object_final_alignment_complete_freeze_artifact_f4941ff_ready_for_owner_freeze_not_frozen |
| DSH (Preprocessing) | Aitutors-preprocessing | 67f564c | step1_step2_done_verification_pass_producer_ready_for_owner_freeze_dec028 |

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
| FACT-040 | **语义覆盖悬崖（跨侧）**: 接口面 87 中 **16 份**（87−71）无 IR 语义承载。~~已裁（DEC-027 Part 4）= Identity Available / Semantic Unavailable 正常态~~（**该表述已废止**——DEC-028 Part 3 改为 **Identity Available / Semantic Pending**，DEC-031 原则 4 终局确认；OQ-14 关闭 + DSH D-2）；V3 仍无身份/语义分离消费能力 | Both | **resolved (DEC-027 Part 4 → DEC-028 Part 3 修订)** |
| FACT-041 | **`source_version_id` 同名异义（跨边界新登记）**: 契约键 = sha256 hex（`SHA256(raw bytes)`）；V3 代码键 = `uuid.UUID` FK（`document_source_versions` 行主键，Seal 唯一锚 `(stage,LE-hash)`，`source.py:50` 明令禁 sha 唯一）。同名、异义、异类型；V3 另有第三概念 `Document.original_sha256`（现为 canonical_json 包裹 joined-text 非 raw bytes）。须 v0.2 消歧（OQ-20） | V3 | observed |
| FACT-042 | **OQ-5 关闭 + OQ-14 关闭（DEC-027 Part 5/4）**: Part5 裁不合并两状态体系、UNKNOWN 属语义层 → 关闭 OQ-5（非单一状态机）；但打开两项更精确 V3 缺口——语义层缺 `unknown` 取值须解冻 BUG-V3-018（OQ-20）、candidate 仅由 ready 产致 unknown→PENDING_REVIEW 不可达（OQ-19）。Part4 裁 16 份正常态 → 关闭 OQ-14。**关闭一个开放项换来两个更精确实现前置** | Both | observed |
| FACT-043 | **Part 2 V3 六项消费义务全未实现（DEC-027）**: V3 = 验证 Manifest + 重算 hash + 判断接受 + 验证 IR + Gate + 拒收。六项全无——无校验（`manifest_reader.py:52`）、不读 producer sha（自算 canonical_json 包裹，`runner.py:71-73`）、无身份闸门（`identity_version` 0 命中）、零 IR 消费。同算法对账生产侧 71/71 已实证可行。可执行前提 = source bytes 可达（OQ-12） | Both | observed |
| FACT-044 | **path 非身份原则 V3 侧核验（DEC-028 Part 1/2）**: V3 仅将 `source_file` 用作 `Path(manifest.source_file)` 加载源文件（`runner.py:241`/`runner_b2.py:320`/`runner_b3.py:184`），全仓**无任何以 path 做身份/版本/hash 判断**的代码 → **符合**「Source identity belongs to content hash, not storage location」。跨系统双层当前靠 path 值相等关联 = 不合规现状；升级 `source_version_id` 关联 = not started。残余 = bytes 如何交付 V3 重算（OQ-12′） | V3 | observed |
| FACT-045 | **语义层终局词表 + 路由已裁（DEC-028 Part 5/6）**: `SEMANTIC_STATUS` 终局 = `{ready,incomplete,unknown}`（加 unknown，取代四状态机合并记法）+ `DECISION_STATUS` = `{pending_review,approved,rejected}`，禁合并；unknown → reviewable record → pending_review（关闭 OQ-19 路由 + OQ-20 值集）。V3 现状：`SEMANTIC_STATUS` 冻结 `{ready,incomplete}` 须解冻加值（not started）；unknown→pending_review 在 candidate-gated-on-ready 架构下无执行面（not started）；reviewable record 载体 = UNKNOWN | Both | observed |
| FACT-046 | **Freeze Candidate Review 两决策（DEC-029 原则5/6）**: (a) 接口键命名提案 = `source_content_sha256`（PROPOSAL；**已由 DEC-030 采纳，见 FACT-047**）。(b) source bytes 交付只冻能力（V3 必须能得 raw bytes + 重算验证 fail-closed + 独立 IR = binding）、传输暂缓（OQ-12″）。零 V3 实现、零数据 | Both | observed |
| FACT-047 | **Freeze Candidate Finalization（DEC-030）**: (a) 接口键命名 `source_content_sha256` **已采纳**（=SHA256(raw bytes) 64 hex；V3 内部 `source_version_id` = uuid.UUID FK 专用化为内部词面；契约全文词面收口完成，52 处新名；OQ-8′ 关闭）。(b) bytes 能力冻结确认。(c) 双状态体系终局确认（禁合并；unknown→reviewable record→pending_review；禁 silent skip/convert/fallback）。(d) 废止旧「Semantic Unavailable」表述；87/71/16 确认。契约 = Freeze Candidate Finalized，仍 NOT FROZEN。零代码、零数据 | V3 | observed |
| FACT-048 | **Owner Final Decision v1（DEC-031）**: (a) 四项原则终局确认（Identity Authority：`source_content_sha256` = SHA256(original source bytes) 64 小写 hex、path 仅 locator、禁任何系统用 path 做唯一身份判断；双层职责：Manifest=「哪个文件」/ IR=「表达什么」；命名终局；16 份 Identity Available / Semantic Pending + 允许重跑 preprocessing + 补充三禁）。(b) **Step 1 快照 + Step 2 回填执行授权（DSH）**：快照记录文件列表+sha+R50 关联；回填后逐份验证 Manifest hash = IR hash；验证报告含 87 清单/hash 一致性/IR 覆盖/16 pending。(c) **冻结条件机械化** = Step 2 完成并验证 → Freeze；OQ-18 关闭。(d) 五项延期（OQ-15/13/10/DEC 编号/OQ-12″）非架构阻塞。(e) V3 下一阶段核心风险 = 消费端验证链（bytes→重算→验证 Manifest→验证 IR→fail-closed）。契约文本本轮合并；仍 NOT FROZEN | Owner | observed |
| FACT-049 | **Contract v0.2 Freeze 前最终登记（DEC-032）**: (a) **一致性检查通过**——`source_content_sha256` = 唯一跨系统内容身份键（60 处）；`source_version_id` 残留全部为历史注记/消歧表/内部 UUID 定义/禁止条款（零处作跨系统键）；`source_file`/path = locator only；「Semantic Unavailable」零权威现用（残留全部为已废止注记）；「Semantic Pending」唯一现用词。(b) **五项能力 NOT IMPLEMENTED 显式登记**（契约 §5.6.1 / G-15）：Manifest identity verification / raw bytes acquisition / independent SHA256 verification / IR identity verification / identity gate。(c) **实现边界登记**（§5.6.2）：输入 Manifest+raw bytes+IR → 验证三项 → fail-closed → 成功进既有 Gate/Admission；path→找文件 / SHA256(bytes)→证明身份。(d) **16 份设计登记**（§1.6 七约束含新旧 IR 血统关系）。(e) Contract 状态 = **Freeze Candidate Finalized / READY FOR FREEZE / NOT FROZEN** | V3 | observed |
| FACT-050 | **Freeze Finalization Audit（DEC-033）**: (a) **DSH Step 1/2 事实核实 = DONE + PASS**——Step 1 snapshot（`data/interface_scope_snapshot_step1.json`，sha256 `b4f14524…98ad99`，87 行）+ Step 2 回填（`n_backfilled=87`，`data/interface_scope_step2_backfill_report.json`，sha256 `d430cc2f…6eec1`）+ Verification Report（71/71 Manifest hash = IR hash；87/87 == source bytes）+ Final Check（`data/freeze_evidence_final_check.json`，sha256 `a707738e…5c33`，C1-C9 overall = VERIFIED）；DSH commits = `e70807b` / `aad2237` / `67f564c`。(b) **冻结条件（DEC-031 §六机械条件）= 已满足**。(c) **Freeze Evidence 五类证据登记入契约 §9.1**（snapshot artifact / backfill report / verification report / final check / commit hash）。(d) **Freeze Object 唯一冻结对象明确**（契约 §9.2）：repository = AITutors-v3 · document = `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` · **sha256 = `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`** · commit = **`f4941ff`**〔DEC-034 澄清：= Freeze Artifact commit，唯一冻结对象；DEC-033 原「本登记 commit（前驱基线 `c6e771c`）」表述歧义，已取代〕· status = READY FOR FREEZE / NOT FROZEN。(e) **关键词再验证通过**（Task 4 四类定义唯一）。(f) DSH F-1（契约缺证据引用 + 状态注记过时）本轮修正；F-2（收口稿未提交）已由 `c6e771c` 解决。(g) 零代码/零 schema/零数据/零 IR/不扩展冻结范围 | V3 | observed |
| FACT-051 | **Freeze Object Final Alignment（DEC-034）**: (a) **Freeze Artifact 唯一化并验证**——commit = **`f4941ff`**，document = `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`，sha256 = `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`（`git show f4941ff:<path> \| sha256sum` == 工作树 == 登记值）。(b) **Freeze Registration 区分**——= DEC 登记/状态更新/日志提交 commit（本轮 DEC-034 账本 commit，parent = `f4941ff`；documents = state.yaml / CURRENT.md / log.md / GAP MAP）；**registration commit 不是冻结对象**。(c) **歧义消除**——`c6e771c` 处契约 sha = `c8d895863a4a07d1d262febe959f6cb2508a2058deeb001aae2c1c1175fe1032`（≠ artifact）→ 非冻结对象；旧「this/本 registration commit」表述全部取代。(d) 契约文档本轮**未改**（改之变更 sha256）。(e) READY/FROZEN 用词扫描通过。(f) 零代码/零 schema/零数据/零 IR/不扩展设计范围 | V3 | observed |

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
| EB-009 | Integration Contract v0.2 freeze readiness | **Freeze Candidate Finalized / READY FOR FREEZE / NOT FROZEN**（DEC-034 Freeze Object Final Alignment 完成）— 冻结范围 = **六项**（未扩展）。**Step 1 DONE · Step 2 DONE · Verification PASS** → 机械冻结条件已满足。**Freeze Artifact（唯一冻结对象）= commit `f4941ff`** · document `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` · sha256 `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528`；**Freeze Registration = DEC-034 账本 commit**（parent `f4941ff`，非冻结对象）；`c6e771c` 排除（契约 sha 不同）。Freeze Evidence 五类已登记（§9.1）。**NOT IMPLEMENTED (V3 capability)** 五项不变（§5.6.1 / G-15）。**开放但不在冻结条件内**：OQ-21 · OQ-17 · OQ-16′。**下一步** = DSH 最终确认 → Owner Freeze 令 → Contract v0.2 Frozen → V3 Consumer Identity Verification 实现阶段 |

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
| **Contract v0.2 DRAFT（Freeze Candidate Finalized，READY FOR FREEZE / NOT FROZEN；§0 冻结范围六项 + §0.5 责任边界 + §1.2/§1.2a 接口键命名 `source_content_sha256`（DECISION）+ §1.3 path 边界公式 + §1.6 16 份七约束与设计登记 + §2.3 bytes 能力与验证链（延伸 Gate→Admission）+ §5.6 Consumer Boundary 五项 NOT IMPLEMENTED + 实现边界 + §8 Freeze 前执行步骤（全部 DONE）+ §9 Freeze Evidence 引用 + Freeze Object；DA-1~37；DEC-031/032/033 并入）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` |
| **Freeze Artifact（唯一 Contract 冻结对象，DEC-034）**: repository = `kurt-wong/AITutors-v3` · commit = **`f4941ff`** · document = `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` · sha256 = `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528` · status = READY FOR FREEZE / NOT FROZEN · **禁止多个 commit 均作为最终版本**；`c6e771c` 处契约 sha = `c8d89586…` ≠ artifact → 排除 | 见契约 §9.2 + 本表 + state.yaml FACT-051 / EB-009 |
| **Freeze Registration（DEC 登记 / 状态更新 / 日志提交，非冻结对象）**: repository = `kurt-wong/AITutors-v3` · commit = **本轮 DEC-034 commit**（parent = `f4941ff`）· documents = `state.yaml` · `CURRENT.md` · `log.md` · `PREPROCESSING-V3-CONSUMER-GAP-MAP.md` | 本表 + log.md DEC-034 轮次 |
| **Freeze Evidence（DSH 侧，DEC-026/027/028）**: Step 1 snapshot `data/interface_scope_snapshot_step1.json`（sha256 `b4f14524…98ad99`）· Step 2 report `data/interface_scope_step2_backfill_report.json`（sha256 `d430cc2f…6eec1`）· Verification Report `PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md` · Final Check `data/freeze_evidence_final_check.json`（sha256 `a707738e…5c33`，C1-C9 VERIFIED）· 证据总账 `PREPROCESSING-CONTRACT-v0.2-FREEZE-EVIDENCE-v1.md` · Producer 确认 `PREPROCESSING-CONTRACT-FREEZE-PRODUCER-CONFIRMATION-v1.md`；commits = `e70807b` / `aad2237` / `67f564c`（preprocessing 仓 Docs/COORDINATION/INTEGRATION/） | preprocessing repo @ `67f564c`；全文登记 = 契约 §9.1 |
| **Coordination log（轮次日志，DEC-032 起建档）** | `Docs/COORDINATION/log.md` |
| **Contract v0.2 Freeze Candidate Review（DEC-029 历史记录；命名提案已由 DEC-030 采纳、DEC-031 终局确认）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-FREEZE-CANDIDATE-REVIEW.md` |
| Handoff 007 (B1/B2/B3 → DSH confirm; 含勘误横幅) | `Docs/COORDINATION/HANDOFFS/2026-09-16-Claude-to-DSH-007.md` |
