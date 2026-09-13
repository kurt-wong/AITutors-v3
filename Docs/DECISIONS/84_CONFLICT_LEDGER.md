# 84 — Conflict Ledger：争议点 / 交叉约束 / 潜在冲突台账

**Document Type**: Gate Report（台账，非裁决）
**Authority Level**: L3
**Status**: ACTIVE
**Normative**: NO
**Supersedes**: `82 §4`（Conflict Register）—— 本台账是其全集与后继
**Superseded By**: —
**Gate State Authority**: NO（唯一权威仍是 **82 §3**）

**Date**: 2026-09-13
**规则**：治理元规范 `90 号`。**本台账只登记，不裁决。**
**证据要求**：每条必须有 `file:line`；**未核验的指控不进台账**。
**机器可读对应物**：`docs_audit/contradiction_candidates.json`

**状态取值**：
`OPEN` 待裁决 · `DECIDED` 已裁决 · `SUPERSEDED` 已被他文废止 · `INCORPORATED` 已并入权威

---

## 0. 本轮汇总

| 类型 | OPEN | 已处置 | 误报 |
|---|---|---|---|
| A 状态漂移 | 6 | 4 | 0 |
| B 术语未定义 / 漂移 | 1 | 2 | 1 |
| C 架构边界冲突 | 1 | 1 | 0 |
| D 分层 / 归属 | 4 | 0 | 0 |
| E 误报 | — | — | 3 |
| F L0 修改审计 | **0** | **1** | 0 |
| **合计** | **11** | **8** | **3** |

### 2026-09-13 二次裁决（用户）

| ID | 裁决 |
|---|---|
| **A-07** | **DECIDED** — 语义A 成立，Gate C CLOSED 不动摇。已在 `73` 文首写入 **C-2 Evidence Scope Clarification**（proves / does not prove），**正文未改** |
| **B-01** | **DECIDED** — 名称漂移非概念缺失。已在 `75` 加 **Terminology** 节声明简称等同；**不全文替换**（diff 大、易误改 L0）；新文档一律用全称 |
| **B-02** | **DECIDED** — **不升 L0**。`Validated Evidence` 是证据生命周期**状态**（系统机制），不是基础原则。层级 L0 存原则 / L2 定机制合理。`90 §2 R9` 已冻结 `≠ verified_correct` + 禁用 `Verified Evidence` |

### 2026-09-13 三次裁决（用户）

| ID | 裁决 |
|---|---|
| **CA-001** | **CLOSED — (b)**：保留 `40 §5` 文本，**不回滚、不改 L0 内容**；认定 **CHANGE-2 Normative Addition**；补建 Change Record **`90 §11 CR-001`**，Review **ACCEPTED / EFFECTIVE**。四道门不需要。procedural gap 已 cure |

### 2026-09-13 四次裁决（用户）— C-01 / BIND-1/2/3

| 项 | 裁决 |
|---|---|
| **C-01 性质** | **真实 Contract Carrier Conflict**，但一阶问题不是「line_refs 放哪」，而是**谁拥有 binding claim、谁验证它、两条路径如何携带**。**整体仍 OPEN** |
| **BIND-1** | **PASS — ACCEPTED / FROZEN** — annotation semantic unit 与 binding unit 必须有确定性可验证 identity join；禁止 fuzzy matching / 文本相似度 / 重跑 Resolver 建立身份。**⚠️ PASS ≠ Adapter 可开工** |
| **BIND-2** | **PASS — ACCEPTED / FROZEN**（2026-09-13 Owner 确认）。九项代码+测试证据（`82 §5.2`）。`line_refs` 作为 Annotation **输入**禁止，作为 Resolver **输出**合法。`gate/service.py` 历史残留**不构成反证，登记即可** |
| **BIND-3** | 方向 **ACCEPTED**：Manifest role declarations = **External Claims**（非 Semantic Authority），且必须过 V3 自己的 contract validation。**契约验证 = UNPROVEN**，阻塞于 manifest schema 未冻结 |
| **收敛结论** | **Native Path 不需要 preprocessing 提供 `line_refs`**；preprocessing 的 Manifest **不需要**为兼容 Native 而把 `line_refs` 塞进 Annotation（`82 §5.2.1`）。C-01 从「四方概念冲突」收敛为**单一工程契约问题** |
| **分层原则** | 冻结：Annotation = semantic structure · Binding = source-reference claim · Identity Join = deterministic relation。**不预先决定载体位置** |
| **落笔约束** | 裁决写入既有 `82 §5`，**不新建 C-01 专题治理文档** |
| **未变** | manifest-only 未冻结 · 67 Errata 未发布 · Adapter 未开工 · L0 零改动 |

### 2026-09-13 五次裁决（用户）— C-01 PAUSE + DG-5 收口

| 项 | 裁决 |
|---|---|
| **C-01 = OPEN / PAUSED** | **不是架构错误，是缺乏必要上游事实。** BIND-3 的契约验证**暂停**——preprocessing 尚未形成可测量、可复现的**生产级**输出（Source fidelity / line stability / role coverage / manifest 完整性 / 失败分布均未生产验证）。在不知道上游能稳定提供什么之前冻结 Manifest Schema = **从 V3 内部模型反向规定上游**。权威落点 `82 §5.3.1` |
| **误读明确否定** | 「BIND-3 UNPROVEN → 立即设计 Manifest Schema → C-01 CLOSED → Adapter」**不是**已由事实证明的工程路线，只是架构假设链。**不成立** |
| **BIND-1/2 不变** | 均为 V3 内部证据，**不依赖 preprocessing**，FROZEN 状态**不因 PAUSE 改变**。不重开讨论 |
| **当前不冻结** | Manifest Schema · BIND-3 完整契约 · Path B 最终接口 · Adapter 输入/输出 · Adapter 是否 bypass Resolver · preprocessing evidence 可否直入 ResolvedRun · material/figure Carrier · 两条路径最终 convergence point。`Manifest → Adapter → ResolvedRun` 目前**只能**是 Candidate Architecture |
| **执行顺序** | DG-5 收口 → 治理体系稳定 → C-01 暂停 → **preprocessing 独立收口** → 以真实生产输出建立事实基线 → 重开 C-01/BIND-3 → 再裁决 Manifest Schema / Adapter / Path B |
| **Adapter** | **NOT STARTED**，且**不因 BIND-1/2 PASS 而具备开工条件**。Adapter 职责必须由「V3 已有 contract + preprocessing 实际稳定输出」**两者共同**决定 |
| **DG-5 边界** | 只做：状态对账 / disposition / 归层 / 过时标记 / L3-L4 越权语言修正 / 引用修正 / audit 同步 / L5 同步。**不得**：改 L0 00–50 · 改 L0 文件名 · 改 90/91 治理原则 · 改写 82 的 BIND-1/2 裁决 · 冻结 Manifest Schema · 实现 Adapter · 改 preprocessing · 因 C-01 新建治理文档 · 顺手做架构设计 |

---

## A 类 — 状态漂移（Gate / Phase 状态在文档间不一致）

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **A-01** | Gate C：`74` 仍 BLOCKED，`80` 已 CLOSED，无废止记录 | `74:5` `74:363` `74:537` vs `80:439`；C-1=`75`、C-2=`76`/`77` 已完成 | 🔴 | **SUPERSEDED** | `82 §3.1` 即废止记录；`74` 三处已加 supersede 标注 |
| **A-02** | `69 §8` 无日期路线图仍写「Errata Decision（Gate A-D 全部通过后）」 | `69:306` | 🔴 | **SUPERSEDED** | 已加 supersede 指针 |
| **A-03** | `81:11` 称「Gate B 系列 CLOSED」，过度陈述 `80` | `81:11` vs `80:421`（B1 CONDITIONAL）、`80:432`/`80:437`（DEFERRED） | 🔴 | **INCORPORATED** | 本轮自引入，已修正；聚合规则见 `90 §5 Rule 1` |
| **A-04** | `80` 内部：B2-B2 同时 CLOSED 与「Unknown 125 仍未清」 | `80:426`（CLOSED，99.8% = 1176/1178）vs `80:448` | 🟠 | **RESOLVED** | **歧义非错误**。closed scope = 已测 1178 个 MC target，Unknown 125 在 scope 外。**scope 声明已写入 `80 §4` Gate B2-B2 行**（2026-09-13）；`82 §4-C4` 同步 RESOLVED。**不再「待 triage 后补」**——Unknown 125 仍是显式延期项，与 closed scope 不冲突 |
| **A-05** | `69` 带日期矩阵仍写 B2-B 为 BLOCKED / WAIT | `69:656`、`69:756` vs `80:426` 起 B2-B1~B5 已 CLOSED | 🟠 | **RESOLVED** | 历史快照，**正文保留原文**（Reconcile, don't rewrite）。已在 **3 个** 2026-09-11 带日期 Gate 状态块（`627`/`645`/`756`）各加 supersession banner → `82 §3`。（全仓无「B2-B = NEXT」表述） |
| **A-06** | `61` `Status: IN PROGRESS`，而 `PHASE_I3_CLOSURE.md` 已 CLOSED / Gate PASS | `61:4` vs `PHASE_I3_CLOSURE.md:4-5` | 🟠 | **RESOLVED** | Phase I-3 关闭后 61 从未回写。**已改**：`61` 头行 → `Status: HISTORICAL`，指向 Closure 记录并声明本文件非当前状态权威 |
| **A-07** | `73:213` 声明 157 targets `UNRESOLVED / REVIEW REQUIRED`，而 Gate C 以 C-2「157 E2E」关闭 | `73:213-221`（NOT proven 全是**语义正确性**：correct / incorrect / auto-admitted / pass manual review）vs C-2 实际 = `test_c2_evidence_authority_e2e.py`（Semantic IR bypass 5 测 + Lifecycle 5 测 + 157 fail-closed 4 测） | 🔴 | **DECIDED** | **语义A 成立，非语义B**。C-2 证明**管线不变量**（invalid binding 不产生 validated evidence、IR bypass 阻断）；`73` 的 UNRESOLVED 是**语义裁决**——从来不是 Gate C 职责。二者正交，**Gate C CLOSED 成立**。已在 `73` 文首写入 **C-2 Evidence Scope Clarification**，**正文未改**（`73:202-204` 三项 RETRACTED 继续有效）。157 个的语义裁决仍属人工审未完成项 |
| **A-08** | `Status.md` 同时含已撤回与已修正的 Grammar 输入契约 | `Status.md:2309`（`必须是 Resolver 产出`——已撤回措辞，**未标记**）vs `Status.md:2423`（不变量版） | 🟠 | **RESOLVED** | **对立极性同主题**。已在 2309 所在历史节节首加 retraction banner：该措辞**已撤回**，现行权威 = `81 §6.2` / `80 §6.6`（生产者可以是 Resolver **或** Adapter）。正文保留为历史 |
| **A-09** | `Status.md` 顶层 Status 行 stale | 首个 Status 行 = `V3 Spec Baseline — Frozen（实现未开始）`，而 `backend/app` 已有完整实现 | 🟡 | **RESOLVED** | **顶层 Status 已改为指针 → `82 §3`**，不再自述。并注明「最新状态 = 文末最新一条」以保持该文件自身的流式追加约定 |
| **A-10** | Phase I-2 Revision Closure **存在两份且内容不同**；旧份未进 census（未治理），且 `Status.md` 两处历史节各含一个失效路径指针 | 旧份 `Docs/V3_PHASE_STATUS/Phase_I2_Revision_Closure.md`（6363 B，Sep 10，**421 passed · QG 11/11**，不在 census 44 份内）vs 权威份 `Docs/REPORTS/PHASE_I2_REVISION_CLOSURE.md`（3339 B，L2 D-02 归层，**425 passed · QG 15/15**）——**State Drift**：同日两份均自称 Closure，测试数字不一致；新版含更多 commit（`cf9d4b4` + freeze），**425/15 为准**。**Provenance Missing**：旧份 `Supersedes: PHASE_I2_REVISION_REVIEW.md` 所指文件**全仓不存在**；`Status.md` 历史节一处指旧路径、另一处指 DG-2 前的 `Docs/V3_SPEC/Closure/…`（该目录已不存在） | 🟠 | **RESOLVED** | **未迁移决策核查：三个 Design Decision 均已有载体**——D1 位置 / D3 纯函数 → 权威份 §4（压缩迁移）；**D2「OCR 是 Provider 不是替代」→ L0 `10_Data_Model.md §4.2` role 枚举 + role/provider 封闭配对，配合 `20 §3.1` sealed 不可变（更高权威，无需回收）**。**DELETE 三证检验：三证不全**（无历史价值 ✗ · 无决策价值 ✓ · 无引用价值 ✗）→ **不得 DELETE → Disposition = ARCHIVE**。已 `git mv` 至 `Docs/ARCHIVE/PHASE_I2_REVISION_CLOSURE_SUPERSEDED.md` 并加 SUPERSEDED banner（正文零改动），空目录 `Docs/V3_PHASE_STATUS/` 已移除；`Status.md` 两个 2026-09-09 历史节各加 provenance/路径 banner，**正文零改动**。**方法验证案例**——Residual Audit 流程在此跑通一次 |

---

## B 类 — 术语未定义 / 术语漂移

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **B-01** | **`Evidence Contract` 名称漂移**：19 处使用简称 vs 15 处全称，二者从未显式等同 | 全称 `Evidence Promotion Contract` 15 处 / 7 份文档；简称 `Evidence Contract` 19 处 / 7 份文档；`74` 同时用两种（4× 全称 + 5× 简称）。**概念本身有完整定义**（`75 §二` 状态机 + 5 条禁止转换 + `§4.5`「唯一可进入 IR」） | 🔴 | **DECIDED** | **是名称漂移，不是概念缺失**——我先前判「零定义」过严。处置：在 `75` 加 **Terminology** 节声明「Evidence Contract 是 Evidence Promotion Contract 的非正式简称，二者同一契约」。**不全文替换**（diff 巨大、历史污染、易误改 L0）。**新文档一律用全称**；既有文档不动 |
| **B-02** | `Validated Evidence` / `Verified Evidence` / `verified_correct` 三近义词 | `Validated Evidence` **有 L2 定义**：`75:42` 状态机 `state: trusted`、`75:194` `§4.5（唯一可进入 IR）`、`75:280` `§6.4`、`75:298` `§6.5`。`Verified Evidence` **全仓零使用**。`verified_correct` = L0 `20 §8.3` | 🔴 | **DECIDED** | **我先前判「L0/L2 零定义」是错的**——检测器漏了状态机图与小节标题形态。改进后 defs=6、risk HIGH→LOW。**残留真实问题**：`Validated Evidence` 是 **L2 定义不在 L0**，且无显式 `≠` 声明。裁决：**不升 L0**（它是证据生命周期**状态**=系统机制，非基础原则；同类 `ResolvedSpan`/`Admission Candidate`）。`90 §2 R9` 已冻结 `≠ verified_correct` + 永久禁用 `Verified Evidence`；术语表落在 `75` Terminology 节 |
| **B-03** | `ResolvedSpan` 100 处使用，检测器判零定义 | 用例分布于 `20`/`65`/`66`/`67`/`69`/`81` | 🟡 | **OPEN（疑误报）** | 实际由 L0 `20 §5.5` **字段表**定义，非散文定义句；检测器只匹配「定义/定为/冻结为」。**建议**：改进检测器识别表格定义，而非改文档 |
| **B-04** | `Binding Carrier` 10 处使用，零定义 | `82 §5` 引入 | 🟡 | **OPEN（故意）** | 已登记为 `PENDING`（BIND-1/2/3 未裁决）。**不是缺陷**，是未决标记 |

---

## C 类 — 架构边界冲突（同一约束的对立规定）

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **C-01** | **`line_refs` 载体四方不一致** | L0 `20:117` FORBIDDEN_FIELDS 含 `line_refs`；`20:73` 硬边界 #2「不携带 resolved span / line_ref」；`67:114` 提议放进 annotation payload；`81 §5.1` 定在独立 manifest；`82 §5` 判 `PENDING` | 🔴 | **OPEN / PAUSED** | BIND-1 **PASS/FROZEN**；BIND-2 **PASS/FROZEN**；BIND-3 方向 ACCEPTED / 契约 **UNPROVEN**。**PAUSED（2026-09-13 Owner 五次裁决）**：暂停于**上游生产事实缺口**，非架构错误。**不**意味着「应立即继续设计 Manifest Schema」。manifest-only 仍 🟡 PROVISIONAL，Carrier = PENDING。权威落点 `82 §5.3.1`。**重开条件 = preprocessing 收口并形成可复现的生产级输出** |
| **C-02** | `66 §7` `Bypasses: Annotation, Resolver` 与 `IRBuilder.build` 签名冲突 | `66 §7` vs `ir.py:87` `build(resolved_run, annotation_payload, ...)` 必需 annotation_payload；span_id `sp-{unit_id}.{role}` 由 annotation 反推 | 🔴 | **INCORPORATED** | 已修正为 `Bypasses: Resolver only`；`66 §7` 就地更正；裁决见 `81 §5.2` |

---

## D 类 — 分层 / 归属

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **D-01** | **71 号同号双份且内容不同** | 原 `Docs/V3_SPEC/71_…`（6914 B，Sep 12 21:33，「裁决记录」）vs 原 `backend/Docs/V3_SPEC/71_…`（7783 B，23:05，「(CORRECTED)」）；`diff -q` = **DIFFERENT** | 🔴 | **DECIDED** | **DG-3 处置（2026-09-13）**：root 版判 **stale**，`git mv` 至 `Docs/ARCHIVE/71_…_SUPERSEDED.md` 并加 SUPERSEDED 声明块（`90 §2 R8`：正文保留、不得作为引用来源、`docs_audit` 标 `deprecated`）；backend CORRECTED 版为**权威版**，移至 `Docs/DECISIONS/71_…` 并归 **L2**。**两份都未删除。** |
| **D-02** | 5 份文档在 V3_SPEC 树内但未归层（837 行） | `PHASE_I2C_CLOSURE` `PHASE_I2_REVISION_CLOSURE` `PHASE_I3_CLOSURE` `PHASE_I4_CLOSURE.md`（均含 `Status: CLOSED`；`PHASE_I3_CLOSURE.md:5` 直接写 `Gate: PASS`）+ `gate_b2a_three_task_report.md` | 🔴 | **CLOSED** | **Disposition = KEEP，无一删除/归档。** 4×Closure → **L2**（formal phase closure = Decision Record：记录阶段裁决，不定义新架构事实 — `90 §2 R2`）。`gate_b2a_three_task_report` → **L4**（经 `Docs/REPORTS` 默认规则，本已 active）。四份 Closure 已各加 `Authority Level: L2` 头块；`PHASE_I3_CLOSURE` 另加澄清：`Gate: PASS` 指**阶段出口**，非项目级 Gate。机器源 `i5g_emit_audit.py` CLOSURE 分支由 `L2-proposed`/`pending` → `L2`/`active` |
| **D-03** | 分层错误 3 份 | `63:3` `Status: Frozen Constraint`（L4 位置自封 L0 权限）；`65:95-106` 十二条禁令实为 scope freeze 契约；`68` 经 `69` 判为 Domain Definition Proposal | 🟠 | **CLOSED** | **Disposition = 三份全部 KEEP → L4，零提升、零删除。** ① **63**：3 处 `Status: Frozen Constraint` 全改——文首加 `Authority Level: L4 / Normative: NO` + 声明「**升 L0 必须走 L1**（`90 §2 R1`），不能靠改标签」；`§10`/`§10.9` 两处改 `L4 Experiment Constraint（非 L0 权威）`。② **65**：**不采纳原「建议归 L2」**——`69 §2` 已定性为 **Evidence**、`69 §65` 写明 `Experiment / Evidence Record`，升 L2 会与 69 矛盾且重复 `63 §10.9/§10.10` 与 `81 §5.6` 已承载的约束（造成第二来源）。已加 HISTORICAL + 定性注。③ **68**：加 `69` 定性注 = **Proposal**，非 Domain Contract、非 L0 权威；「Adjudicated」仅指完成兼容性审查 |
| **D-04** | L3 `74` 对 V3 自立规范 6 处 | `74:224`（Native Path **必须**保证…）`74:226`（preprocessing **必须**满足…）`74:283`（answer span **不得**重叠）`74:385`（**唯一**允许进 IR）`74:395-396`（**禁止** CLAIMED/PROPOSED → IR）`74:418`（Validation **必须** append-only） | 🟠 | **CLOSED** | 违反 `90 §2 R3`（L3 不得定义规则）。对照 `74:94`「这个结果**只能**证明」是**正确用法**。**6 处已全部改写为「report finding + 权威指针」**，正文测量内容零改动：`224`/`226` → 指 `81 §5.4` + `82 §5.0`；`283` → 指 `75 §九`（`role_region_consistency`）+ `20 §5.5`；`385`/`395-396` → 指 `75 §三 R5` + `75 §4.5` + `75 §二·禁止转换`；`418` → 指 `75 §4.4` + `75 §三 R4` |
| **D-05** | Gate 状态行集中面：`Status.md` 45 行 / `69` 42 行 | 扫描统计 | 🟠 | **CLOSED** | **控制已就位，无需改文档。** `90 §4`（Status Header 规范，强制）+ `82 §3.3`（状态声明模板，供 B/C 层引用）均已冻结，且两者都写明「**存量文档不强制回填**（Reconcile, don't rewrite）」。存量不回填；`69` 中**实际已 stale** 的三个块由 A-05 处理完毕。新增行强制走模板 |

---

## F 类 — L0 修改审计（90 §11 Change Audit Record）

**任何对 L0 的修改都必须在此登记。** 权威版见 `90 §11`。

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **CA-001** | `40 §5` 被新增一条**强制**规则，**无 Change Record** | `0dd954d`（2026-09-13 14:43）新增：「测量语义**必须**复刻真实 pipeline…**禁止**用近似文本代替…度量脚本**必须**能指出它复刻哪一段 pipeline，并有测试锁死该复刻语义」 | 🔴 | **CLOSED** | **Owner 裁决 (b)（2026-09-13）**：保留 `40 §5` 现有文本，**不回滚、不改 L0 内容**；正式认定为 **CHANGE-2 Normative Addition**，补建 Change Record **`90 §11 CR-001`**，Review **ACCEPTED / EFFECTIVE**。四道门不需要。流程缺陷（先改 L0 后补手续）属 **procedural gap，已 cure**。**区分**：Change Record 批准前「文本已存在 ≠ CHANGE-2 已生效」；CR-001 Accepted 起该条具有完整 L0 效力 |

**审计范围**：`0dd954d` 之后触及 L0 的提交仅 `40` 一处。更早的 L0 修改
（`10`/`20` 于 09-08/09-09，`30`/`50` 于 09-08）在提交信息中已自带
`errata` / `Scope Freeze errata` / `spec-only, A-Guarded` 标记，属 90 之前的
既有变更惯例，不在本轮审计范围。

---

## E 类 — 已核验为误报（记录以防重复排查）

| ID | 表面冲突 | 核验结果 | 状态 |
|---|---|---|---|
| **E-01** | `81:208-211` 管线图同时含 `Resolver` 与 `Adapter`/`preprocessing`，被判 MIXED | **误报**。该图是**两条显式分支**（`Native Resolver（search/resolve）` / `Path B Adapter（verify only）`），均有路径标签，正是「双轨汇聚」的正确画法。检测器不识别分支标签 | **误报** |
| **E-02** | `10:777` 引用 `20 §12.1`，而 20 无 §12.1 → 悬空引用 | **误报**。该行是 **changelog**：`出处 "20 §12.1" → "20 §8.5"（20 §12 是变更记录）`——记录的是**已修正**的旧值。检测器把 changelog 里的旧值当成活引用 | **误报** |
| **E-03** | 「Gate B2-B = NEXT」 | **不成立**。全仓无「NEXT」措辞；实际残留是 A-05 的 BLOCKED / WAIT | **误报** |

---

## 1. 交叉约束图（`line_refs`，C-01 展开）

```text
L0 20:117   FORBIDDEN_FIELDS ← 含 "line_refs"        【禁止出现在 annotation】
L0 20:73    硬边界 #2        ← "不携带 resolved span / line_ref"
                ↓
L4 67:114   提议移除 line_refs 出 FORBIDDEN_FIELDS    【CHANGE-5 候选，NOT RELEASED】
L4 67:179   建议 line_refs 不参与 identity hash
                ↓
L2 69 §9.三 三层 Identity：line_refs ∈ Source Binding Claim（claim, not truth）
L2 69 §9.五 四道门 Gate D：Adapter 不得成为第二个 Semantic Resolver
                ↓
L2 81 §5.1  line_refs 载体 = 独立 manifest.json        【与 67 对立】
L2 81 §5.2  Bypasses: Resolver only（search/resolve 机制，非 Source Binding）
L2 81 §5.6  核心不变量：只允许机械投影，不允许提高信息量
                ↓
L2 82 §5    Binding Carrier = PENDING（BIND-1/2/3 未裁决）
L2 82 §5.1  manifest-only = 🟡 PROVISIONAL ARCHITECTURAL PREFERENCE
                ↓
L0-META 90 §6 H-B   BIND-1：semantic_unit.id ←确定性 join→ binding.unit_id
                    不得依赖顺序/题号/fuzzy/stem 相似度
```

**结论**：`line_refs` 的规范载体在四个层级上有四种答案，**且无一份 L1 Contract Change Record**。
在 BIND-1/2/3 裁决并走完 L1 之前，**任何一方都不得被当作事实**。

---

## 2. 待裁决优先级（建议，非裁决）

> **2026-09-13 五次裁决后**：A 类 **0 OPEN** · D 类 **0 OPEN** · E 类全为误报。
> **剩余 3 项，其中 2 项已判非缺陷：**
>
> | ID | 状态 | 性质 |
> |---|---|---|
> | **C-01** | **OPEN / PAUSED** | 唯一真实阻塞项，但**暂停于上游事实缺口**（`82 §5.3.1`），不是待办设计任务 |
> | **B-03** | OPEN（疑误报） | 检测器局限：`ResolvedSpan` 由 `20 §5.5` **字段表**定义，散文定义句匹配不到。**非缺陷**，应改检测器 |
> | **B-04** | OPEN（故意） | `Binding Carrier` 本就应为 `PENDING`。**非缺陷**，是未决标记 |
>
> **因此当前没有「应立即推进的架构设计项」。** 下一步不是继续整理文档或设计
> Manifest Schema，而是 **preprocessing 独立收口**（§4）。

---

## 3. 显式不主张

1. **不主张**本台账任何条目已裁决——除已标 `SUPERSEDED` / `INCORPORATED` /
   `RESOLVED` / `CLOSED` / `DECIDED` / `FALSE_POSITIVE` 者。
2. **不主张**本台账穷尽全部冲突——只覆盖 `90 §5` 四条规则的机械可查部分 + 本轮人工核验项。
3. **不主张** E 类误报是缺陷——它们是**检测器局限**，记录以防重复排查。
4. **不主张** A 层可据本台账修改——修改 A 层须走 L1（`90 §2 R1`）。
5. **不主张**本台账削弱 `82 §3` 的 Gate State Authority——**82 §3 仍是唯一权威**。

---

## 4. 下一步

```text
DG-5 收口（本轮）                        ← 现在
        ↓
治理体系稳定（A 类 0 OPEN · D 类 0 OPEN）
        ↓
C-01 PAUSED —— 不继续架构推演
        ↓
preprocessing 独立收口（AITutors-preprocessing 自身）
        ↓
生产级真实输出 → 事实基线
        ↓
重开 C-01 / BIND-3（按 82 §5.3.1 的 12 项逐条取证）
        ↓
再裁决：Manifest Schema · Path B · Adapter · Resolver 是否 bypass
        · ResolvedRun 是否为 convergence point · material/figure Carrier
```

**当前没有应立即推进的架构设计项。** B-03 / B-04 已判非缺陷；C-01 PAUSED。
「继续整理文档」或「先设计 Manifest Schema」**都不是**下一步。

**不碰 L0、不发 67、不冻结 manifest-only、不实现 Adapter。**
