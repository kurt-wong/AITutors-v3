# 82 — Contract Authority Reconciliation：规范权威层级与 Gate 状态权威

**Status**: **ACTIVE — Gate State Authority（本文档 §3 是唯一权威）**
**Date**: 2026-09-13
**触发**: 外部对抗性审查（2026-09-13）指出 Frozen Spec / Gate 裁决 / Phase 报告 /
Status 文档之间出现多个层级的规范性声明，且无废止关系记录。

> ⚠️ **降级为治理执行记录（2026-09-13，90 号生效）**
> 治理元规范已提升至 **`90 号`**（L0-META）。本文档 **§1 Authority Matrix**、
> **§2 CHANGE 分类**、**§9 Status Header**、**§11 读取顺序** **被 90 号吸收**，
> 此处保留为历史，**以 90 号为准**。
>
> 本文档**继续持有**且仍是唯一权威的部分：
> - **§3 Gate State Authority**（唯一；每次 Gate 状态变更须同 commit 更新）
> - §4 Conflict Register → **后继为 `84 号` Conflict Ledger**（全集）
> - §5 Binding Authority BIND-1/2/3（PENDING）
> - §10 Phase I-5 CURRENT BASELINE
>
> **最高规则（90 §2）**：L3/L4/L5 永远不得改变 L0/L1；L2 只能解释与裁决，
> 不得修改 L0。本文档是 **L2**，同样受此约束。

---

## 0. 为什么现在做 / 本轮明确不做什么

Errata Decision 的前置不是「再裁决一次 67」，而是**先把谁有权说什么理清楚**。
否则任何一份「最新报告」都能宣布一个 Gate 已关闭，而另一份历史报告仍写着 BLOCKED，
审计确定性会失效。

### 0.1 本轮**明确不做**（用户裁决 2026-09-13）

| 不做 | 原因 |
|---|---|
| 修改 `20_Document_Pipeline.md` | 权威层级未建立前，向 Frozen Spec 塞新约束会把未解决的架构冲突正式化 |
| 冻结 manifest-only 为规范事实 | 只是**候选架构方向**；BIND-1/2/3 未证明（§5） |
| 写 Errata Decision | 前置未满足 |
| 实现 Adapter | 81 §5.4 三项前置未满足 |
| 发布 67 号 Errata | CHANGE-4/5，Gate B 未 CLOSED（§3） |

### 0.2 本轮**做**的事

1. 建立文档分层与权威矩阵（§1）
2. 建立规范变更分类 CHANGE-0…5（§2）
3. 建立 Gate State Authority（§3，本文档为唯一权威）
4. 登记已核验的冲突（§4，含 `file:line` 证据）
5. 登记 Binding Authority 三个未决问题（§5，**不裁决**）
6. 修正本轮核出的事实性错误（§6）

---

## 1. 文档分层与权威矩阵

### 1.1 五层定义

| 层 | 性质 | 能做什么 | 不能做什么 |
|---|---|---|---|
| **A — Frozen Spec** | **Normative** | 定义契约；只能经 §2 正式变更流程修改 | 不得被 B/C/D/E 层改写或「事实上修订」 |
| **B — Decision Record** | **Normative（仅其裁决范围）** | 对具体问题作裁决 | **不得覆盖 A 层**；超出裁决范围即失效 |
| **C — Phase / Work Report** | **Informative** | 提供实验证据、分析 | **不得出现规范性语言**（「必须 / 禁止 / 契约」） |
| **D — Status / Restart** | **Informative** | 汇报当前状态 | **不得与 §3 矛盾**；矛盾即该文档 stale |
| **E — Experimental** | **非正式** | 方向性参考 | **不得单独支撑任何 PASS / CLOSED 声明** |

### 1.2 逐册归属

**A 层 — Frozen Spec（`Docs/V3_SPEC/`）**

| 分册 | 权威范围 | 版本 |
|---|---|---|
| `README.md` | 术语裁决、分册地图 | v1.1 Frozen |
| `00_Master_Spec.md` | 重建原则、系统边界、反模式红线 | v1.2 Frozen |
| `10_Data_Model.md` | DDL、实体关系、JSONB 边界、Admission 事务 | v1.2.2 Frozen |
| `20_Document_Pipeline.md` | **Schema Source of Truth**：制品分层、Annotation 契约、Resolver、IR、Compiler、Gate、Answer 三字段 | v1.2.1 Frozen |
| `30_Task_LLM_Safety.md` | 进程边界、Task 状态机、LLM 宪法 | v1.1 Frozen |
| `40_Development_Rules.md` | 开发顺序、复杂度预算、测试层级、DoD | v1.1 Frozen |
| `50_Migration_Assets.md` | V2→V3 迁移取舍、Golden Corpus | v1.1 Frozen |

**B 层 — Decision Record**

| 分册 | 权威范围 | 状态 |
|---|---|---|
| `67_…BOUNDARY_ADJUSTMENT.md` | **NOT RELEASED** — 历史提案，CHANGE-4/5 候选 | 不得当作现行契约 |
| `69_ARCHITECTURE_REVIEW_ADJUDICATION.md` | Step 0–3 裁决、四道门定义、Authority 分层 | §8 路线图已被 §8 **supersede**（见 §4-C2） |
| `70_OQ1_IDENTITY_LAYERING.md` | Gate A 三层 Identity 裁决 | CLOSED |
| `75_EVIDENCE_PROMOTION_CONTRACT.md` | C-1 Evidence Promotion Contract 设计冻结 | REVIEWED |
| `80_B2B5_CLOSURE.md` | B2-B1~B5 裁决 + Evidence Admission Boundary（BUG-V3-044） | CLOSED，但见 §4-C3/C4 |
| `81_GATE_D_ADAPTER_BOUNDARY.md` | Adapter 边界契约 | CONTRACT CLOSED / IMPLEMENTATION NOT STARTED |
| **`82`（本文档）** | **文档权威层级 + Gate State Authority + 规范变更分类** | **ACTIVE** |

**C 层 — Phase / Work Report（Informative）**

`60`–`66`、`68`、`71`–`74`、`76`–`79`、`83`。
其中 `74` 的 Gate C 状态行已 stale（§4-C1）；`83` 是 I-5-G 全仓审计结果，
其 §6 六项待裁决未决前，G1–G6 均为**登记状态**。

> ⚠️ **待归层（83 号 G1/G3，未裁决）**：`Closure/PHASE_I2C|I2_REVISION|I3|I4_CLOSURE.md`
> 四份正式关闭记录（建议 **B**）、`gate_b2a_three_task_report.md`（建议 **C**）、
> `63`（自述 Frozen Constraint，**A 或 B 待裁决**）、`65`（scope freeze 契约，
> 建议 **B**）。在裁决前，**不得**按路径直觉把它们当 A 层用。

**D 层 — Status / Restart（Informative）**

`Status.md`、`restart-prompt.md`、`log.md`。**必须与 §3 一致**；不一致以 §3 为准。

**E 层 — Experimental（非正式）**

I-5-1 的 14 项实验（含「21/21 ready IR」）——**不可复现**（无脚本、无测试、git 历史
零提交），仅方向性参考。Path B harness 输出、`gate_b2b*_frozen_testset.json`
语料——是 C 层报告的输入，本身不构成契约。

### 1.3 尚不存在 / 存在也不得成为 A 层的

| 项 | 状态 |
|---|---|
| Manifest schema | **未冻结**——不得被引用为 V3 normative schema |
| V3 Annotation 对外契约 | **未冻结**——preprocessing 侧的前置 |
| Adapter 实现 | **NOT STARTED** |

### 1.4 维护规则（冻结）

1. **A 层只能经 §2 的正式变更流程修改**；任何 B/C/D 层文档不得改写 A 层语义。
2. **B 层裁决不得超出其声明的问题范围**；超出部分视为 C 层意见。
3. **C 层报告禁止使用规范性语言**。出现「必须 / 禁止 / 契约 / 冻结」即违规，
   应改写为「实验观察到 / 建议 / 待裁决」。
4. **D 层与 §3 矛盾时，以 §3 为准**，且 D 层须在下次更新时修正。
5. **E 层证据不得单独支撑 PASS / CLOSED**；必须有 B 层裁决引用并说明边界。

---

## 2. 规范变更分类（CHANGE-0…5）

Errata 不应只处理「放宽」。**新增强制 invariant 同样是正式变更。**

| 类别 | 定义 | 需要什么 | 例 |
|---|---|---|---|
| **CHANGE-0 Editorial** | typo、编号、格式 | 轻量修订记录 | 错别字、锚点 |
| **CHANGE-1 Clarification** | 措辞澄清，**规范语义零变化** | Change Record（简） | 同义改写 |
| **CHANGE-2 Normative Addition** | **新增**此前未规定的强制约束 | **Change Record + 评审**；不必走四道门 | E1（见 §4-C6） |
| **CHANGE-3 Normative Modification** | 改变既有规定的行为 | Change Record + 受影响层回归 | — |
| **CHANGE-4 Constraint Relaxation** | **放宽**既有约束 | **四道门 + Change Record** | — |
| **CHANGE-5 Constraint Removal** | **删除**既有约束 | **四道门 + Change Record** | 67 号（删 `FORBIDDEN_FIELDS` 的 `line_refs`，`20:117`） |

**判定规则**：拿不准时**往高里归**。归高了只是多走流程；归低了就是绕过治理。

**四道门（`69 §5`）仅适用于 CHANGE-4 / CHANGE-5**——它是为了守住「放宽安全边界」
而设的。CHANGE-2 不放宽任何东西，走四道门属过度程序，但**必须有 Change Record**，
否则会出现「Phase 文档偷偷给 Frozen Spec 加 invariant」。

`20` 已有 errata 先例（v1.2.1 BUG-011 Scope Freeze errata，2026-09-09），
Change Record 沿用该版本递增形式。

---

## 3. Gate State Authority（唯一权威）

> **本节是全部 Gate 状态的唯一现行权威。** 其他任何文档的 Gate 状态均为回声；
> 与本节矛盾即该文档 stale。**任何 Gate 状态变更必须在同一 commit 内更新本节。**

### 3.1 当前状态（2026-09-13）

| Gate | 状态 | 残留 / 边界 |
|---|---|---|
| **A** Identity Closure | **PASS / TEST-EVIDENCED** | A1/A2/A3 直接测试 + call-site audit；514/514 |
| **B1** Binding Integrity | **CONDITIONAL PASS** | Content 79.0%；Role：stem 97.3% / explanation 96.7% / **option 51.8%** / **answer 49.1%**；Structural **未评估**；Semantic **UNPROVEN** |
| **B2-A** Clean Roles | **CLOSED — PASS** | stem-only three-task audit；Legacy 47.1% vs Path B 96.8% |
| **B2-B1** | **CLOSED — PASS / SCOPE-BOUNDED** | 非 HTML option region 99.6%（1065/1069） |
| **B2-B2** | **CLOSED — PASS / SCOPE-BOUNDED** | MC answer 99.8%（1176/1178）；**closed scope = 已测 1178 个 MC target**，Unknown 125 在 scope 外（显式延期，§4-C4 **已 RESOLVED**） |
| **B2-B3-A** | **CLOSED** | 原 fill_in 70 → MC 误分类 36 / 真填空 34 |
| **B2-B3-B** | **CLOSED — PASS / DETERMINISTIC** | 34/34，fallback 0 |
| **B2-B3-C** | **DEFERRED** | Domain Contract 依赖 F2/F4/F9 |
| **B2-B4-A** | **CLOSED** | HTML 602 → Direct 507 / Excluded 95 |
| **B2-B4-B** | **CLOSED — PASS / DETERMINISTIC** | 507/507，fallback 0 |
| **B2-B4-C** | **DEFERRED** | Domain/Material 依赖 H4/H5/H6 |
| **B2-B5** | **CLOSED — PASS / SCOPE-BOUNDED** | S1/S2/S3 投影 13 tests |
| **B 整体** | **NOT CLOSED** | **聚合规则见 §3.2** |
| **C** | **CLOSED (Phase 1)** | C-1=`75`，C-2=`76`/`77`；**supersedes `74`**（§4-C1） |
| **D** | **CONTRACT CLOSED / IMPLEMENTATION NOT STARTED** | 契约冻结；`backend/app` 无代码；开工阻塞于 81 §5.4 |
| BUG-V3-044 | **CLOSED** | Evidence Admission Boundary；802 tests |

### 3.2 Gate 聚合规则（冻结）

> **子 Gate 的 PASS 不得自动聚合成父 Gate 的 PASS。**

```text
Gate B = NOT CLOSED
├── B1  CONDITIONAL PASS
├── B2-A PASS
├── B2-B1 PASS
├── B2-B2 PASS（scope-bounded；Unknown 125 未清）
├── B2-B3-A/B PASS
├── B2-B3-C DEFERRED
├── B2-B4-A/B PASS
├── B2-B4-C DEFERRED
└── B2-B5 PASS
```

**判定**：`69 §5` 对 Gate B 的要求是「完整、可重复、同口径的 Legacy vs Path B
对比实验」。存在 **CONDITIONAL PASS 子项**或 **DEFERRED 子项**时，父 Gate **不得**
记为 PASS 或 CLOSED。「大部分子项 PASS → 基本完成 → 可发布 Contract Change」是
**禁止的逻辑偷换**。

### 3.3 状态声明模板（供 B/C 层引用）

引用本节状态时**必须**写成：

> Gate X：状态（依据 82 §3，日期）

**禁止**只写「Gate X CLOSED」而不带范围限定与依据。

---

## 4. Conflict Register（已核验）

每条含 `file:line` 证据。**未核验的指控不进本表。**

| ID | 冲突 | 证据 | 级别 | 处置 |
|---|---|---|---|---|
| **C1** | Gate C：`74` 仍写 BLOCKED，`80` 已宣布 CLOSED，**无废止记录** | `74:5` / `74:363` / `74:537` = BLOCKED（C-1+C-2 未闭环）；`80:439` = CLOSED；C-1 实际完成=`75`，C-2=`76`/`77` | 🔴 P0 | **本节 §3.1 即废止记录**：C = CLOSED (Phase 1)，supersedes `74` 的 Gate C 状态行。`74` 保持原文（历史报告），其 Gate C 行视为 stale |
| **C2** | `69 §8` 无日期路线图仍写「Errata Decision（Gate A-D 全部通过后）」 | `69:306`（§8「下一步顺序」代码块，**无日期标注**，读起来像现行规范） | 🔴 P0 | `69 §8` 加 supersede 指针 → 本文档 §8。**不改写历史正文** |
| **C3** | `81` 声称「Gate B 系列 CLOSED」，但 `80` 自己写 B1 CONDITIONAL + 两项 DEFERRED | `81:11` vs `80:421`（B1 CONDITIONAL PASS）、`80:432`/`80:437`（B2-B3-C / B2-B4-C DEFERRED） | 🔴 P0 | **本轮已修正** `81:11`（§6）。属聚合规则 §3.2 的违反实例 |
| **C4** | `80` 内部：B2-B2 同时 CLOSED 与「Unknown 125 仍未清」 | `80:426`（CLOSED — PASS / SCOPE-BOUNDED，99.8% = 1176/1178）vs `80:448`（B2-B2 Unknown 125 triage → 仍未清） | 🟠 P1 | **RESOLVED（2026-09-13，84 A-04）**。歧义非错误：closed scope = 已测的 1178 个 MC target，Unknown 125 在 scope 外。**scope 声明已补入 `80 §4` Gate B2-B2 行**，不再「待 triage 完成后补」。Unknown 125 仍属显式延期项，与 closed scope 不冲突 |
| **C5** | `69` 带日期状态矩阵仍写 B2-B 为 BLOCKED / WAIT | `69:656`（`BLOCKED BY contract 裁决`）、`69:756`（`WAIT FOR MANIFEST CONTRACT UPDATE`）；而 `80:426` 起 B2-B1~B5 已 CLOSED | 🟠 P1 | 历史快照，**保留原文**。以 §3.1 为准。（注：全仓**无**「B2-B = NEXT」表述） |
| **C6** | E1 性质：写入 20 §8.4 是 **Normative Addition** 而非澄清 | `20:662-679`（§8.4 现文）对 `answer_text` 来源**沉默**；约束已冻结在 `80 §6.6` / `81 §6.2` / `grammar.py` docstring | 🟠 P1 | 按 §2 归 **CHANGE-2**。**本轮不写入 20**；待 Authority 层清理完成后走 Change Record |
| **C7** | 无 Authority Matrix / 无变更分类 | 全仓 grep「Authority Matrix / CHANGE-0 / Normative Addition」零命中 | 🔴 P0 | **本文档 §1/§2 即为建立** |

### 4.1 核验中未成立的指控

| 指控 | 核验结果 |
|---|---|
| 「Gate B2-B = NEXT」 | **不成立**。全仓无「NEXT」措辞。实际残留是 C5 所列的 BLOCKED / WAIT |

---

## 5. Binding Authority — BIND-1/2/3 裁决（BIND-1/2 已 FROZEN；BIND-3 **PAUSED**）

> **2026-09-13 Owner 裁决**：C-01 是**真实 Contract Carrier Conflict**，但一阶问题
> 不是「`line_refs` 放 annotation 还是 manifest」，而是**谁拥有 binding claim、
> 谁验证它、Native / Adapter 两条路径如何携带它**。
> **BIND-1 = PASS / FROZEN · BIND-2 = PASS / FROZEN · BIND-3 = UNPROVEN。**
>
> **2026-09-13 Owner 二次裁决 — C-01 = OPEN / PAUSED**：BIND-3 的契约验证**暂停**，
> **不是因为发现新的架构错误，而是缺乏必要的上游事实**——preprocessing 尚未形成
> 可测量、可复现的生产级输出（Source fidelity / line stability / role coverage /
> manifest 完整性 / 失败分布均未生产验证）。在不知道上游能稳定提供什么之前冻结
> Manifest Schema，等于**从 V3 内部模型反向规定上游**，违反「先事实 → 再契约 →
> 再架构裁决」。BIND-1/BIND-2 的冻结**不因此改变**（它们是 V3 内部证据，不依赖
> preprocessing）。详见 §5.3.1。

`line_refs` 的规范载体是什么，是比「放 annotation 还是放 manifest」更根本的问题。
`69 §9.三` 的三层 Identity 模型把 `line_refs` 定义为 **Source Binding Claim** 的组成
部分，但**没有任何 A 层文档规定该 Claim 的载体**。

```text
Semantic Identity      "这是什么？"        → identity hash
Source Binding Claim   "我认为它在哪里？"   → claim, not truth
Resolved Evidence      "代码验证后引用了什么" → 进入 IR/Compiler/Gate/Admission
```

**关键澄清（避免把载体与权威混为一谈）**：`line_refs` 出现在 annotation 中本身
**不自动违反** Source-as-Fact-Source。真正违反的是

```text
LLM line_refs → 直接相信 → ResolvedSpan     ← 违规
LLM line_refs → Resolver 验证 → ResolvedSpan ← 不违规
```

因此「manifest-only 更干净」**不等于「manifest-only 已被证明正确」**。

### 5.0 分层原则（冻结）

> **Annotation = semantic structure**
> **Binding = source-reference claim**
> **Identity Join = deterministic relation between the two**

**不预先决定** Binding 必须存在于 Annotation 或 Manifest 中——那是 BIND-2 / BIND-3
各自要证明的。本轮冻结的是**分层本身**：语义结构与来源引用是两个不同的层，
二者之间只允许确定性 identity join。

**不采用**「为消灭不一致而宣布 Annotation 必须重新包含 `line_refs`」——那会把
semantic annotation 与 source binding 重新耦合。**也不采用**「Annotation 永远
禁止携带任何 binding information」——那是过度约束，BIND-2 未证明前无权预先排除。

两条路径在 `ResolvedRun` 汇合（下游 IRBuilder / Compiler / Gate 完全一致）：

```text
                 ┌─ Native ──── Resolver ────┐
Annotation ──────┤                            ├── ResolvedRun
                 └─ Adapter / Manifest ──────┘
```

### 5.1 BIND-1 Identity Join — **ACCEPTED / FROZEN**

> **Annotation semantic unit 与 binding unit 必须存在确定性的、可验证的
> identity join；不得依赖 fuzzy matching、文本相似度或重新执行 Resolver
> 来建立身份关系。**

| | |
|---|---|
| 裁决 | **ACCEPT**（2026-09-13 Owner） |
| 含义 | **Binding Unit ≠ Semantic Unit**。二者可通过确定性 ID 关联，但不能因「ID 一样」就自动获得 Source authority |
| 若违反 | join 依赖顺序 / 题号 / 模糊匹配 / 文本相似度 → 重新引入 Resolver-like 问题，违反 `81 §5.6`「不得隐式 fuzzy matching」与核心不变量「只允许机械投影」 |
| 边界 | BIND-1 **只解决**「两个东西怎么确定性地对应起来」；**不解决**「Manifest 中声明的 span 是否真的对应 Source」——后者属 Evidence Authority / Resolver / Adapter validation 边界 |

**⚠️ BIND-1 ACCEPT ≠ Adapter 可开工。** 开工前置仍为 `81 §5.4` 三项，本节不放宽任何一项。

### 5.2 BIND-2 Native Carrier — **PASS / ACCEPTED / FROZEN**

> **Owner 裁决（2026-09-13）**：BIND-2 = **PASS**。依据达**契约证明**级别，
> 不需再为形式增加实验。

**问题**：Native Path 能否完全脱离 `annotation.line_refs`？

**裁决结论**：

> **Native Path 在当前 Frozen L0 下不依赖 `annotation.line_refs`，且 `line_refs`
> 的合法来源是 Resolver 输出，而不是 Annotation 输入。**

即明确区分：

```text
line_refs as INPUT    ❌ 禁止（20 §4.3 FORBIDDEN_FIELDS）
line_refs as OUTPUT   ✅ 合法（Resolver 产出 ResolvedSpan.line_refs）
```

**证据（2026-09-13，代码 + 测试，非架构推论）**：

| # | 证据 | 出处 |
|---|---|---|
| 1 | `FORBIDDEN_FIELDS` 含 `line_refs`，递归校验，任意 depth 出现 → 整体 invalid | `20 §4.3`；`annotation/__init__.py:9-21` |
| 2 | 硬边界：Annotation 只携带 claim 与 Semantic Reference，**不携带 resolved span / line_ref** | `20:73` |
| 3 | **Semantic Reference 是 L0 规定的位置指认机制**：`start_marker` / `end_marker`（kind + granularity + text），**不含行号** | `20 §4.4` |
| 4 | Resolver 消费 `annotation_payload`，读取 `t.start_marker` / `t.end_marker` | `resolver.py:264`、`468-469` |
| 5 | Resolver **产出** `ResolvedSpan.line_refs`（输出，非输入） | `resolver.py:150, 177, 206, 226` |
| 6 | payload 含 `line_refs` → 校验违规（测试锁死） | `test_annotation.py:54-57` |
| 7 | valid payload 不含任何 FORBIDDEN key（测试锁死） | `test_annotation.py:85-89` |
| 8 | 全部 resolver 测试以 `start_marker` / `end_marker` 为输入，断言 `span.line_refs` 为**输出** | `test_resolver.py` 全文件 |
| 9 | 全量回归 | **802 passed**（2026-09-13） |

**证明性质**：不是「我们认为 Native 应该不需要 line_refs」，而是
**当前 L0 + 当前实现 + 当前测试共同证明 Native 不接受 line_refs 作为 Annotation 输入。**

**已知残留（登记，不构成反证）**：`gate/service.py:82-98`
`_confidence_only_projection` 在 `resolver_input_hash` 中**保留** `line_refs`，
注释引 OQ-1 §6.2 规则 3「Resolver 需要知道 LLM 声称的位置才能验证」。该设计源自
OQ-1（70 号）对 67 号提案的**预期**。在现行 L0 下（FORBIDDEN_FIELDS 禁止
`line_refs` 进入 payload），该 projection 对 `line_refs` 是**不可达的防御性历史逻辑**。

- 它**不能**证明「Resolver requires `annotation.line_refs`」；**最多**证明
  「旧设计曾经考虑过 `annotation.line_refs`」——两个命题完全不同。
- **不得**援引该历史 / 防御性代码作为 BIND-2 反证。
- **不判为代码错误，也不要求现在删除**——那会把治理裁决扩大成新的代码清理任务。
  仅当 FORBIDDEN_FIELDS 被放宽（CHANGE-5，未发生）时它才会生效。

### 5.2.1 BIND-1 + BIND-2 的收敛结论（本轮 C-01 核心收益）

两个 PASS 合起来正式得到：

```text
Annotation
    │  semantic structure
    ▼
Resolver
    │  consumes semantic references
    ▼
ResolvedRun
    │  produces source binding
    ▼
line_refs
```

由此两条**正式成立**：

1. **Native Path 不需要 preprocessing 提供 `line_refs`。**
2. **preprocessing 的 Manifest 不需要为了兼容 Native Path 而把 `line_refs`
   强行塞进 Annotation。**

第 2 条是本轮 C-01 的核心收益：preprocessing 侧的契约设计**解除了一项本不存在的
兼容性负担**。C-01 因此从「四方概念冲突」收敛为一个具体的工程契约问题——
**仅剩 BIND-3 的 manifest schema 冻结**。

### 5.3 BIND-3 External Carrier — 方向 ACCEPTED，契约验证 UNPROVEN

**问题**：Manifest 中的 role declaration 是 External Claim 还是 V3 Semantic Authority？

**裁决方向（2026-09-13 Owner）**：

> **Manifest role declarations = External Claims**，不是 Semantic Authority。
> **External Claim 可以被 Adapter / Binding layer 转换为 V3 所需结构，但必须经过
> V3 自己的 contract validation；不能直接绕过 V3 的 semantic / evidence gates。**

**禁止**：

```text
Manifest → "V3 已经相信它" → IR        ← 违规（产生第二个 Semantic Authority）
```

**要求**：

```text
Manifest → External Claims → Adapter（validate / translate）→ V3 contract → ResolvedRun
```

**支撑证据（既有，本轮未新增）**：

| # | 证据 | 出处 |
|---|---|---|
| 1 | `annotation_payload` 驱动 IRBuilder 全部语义结构；`Bypasses: Annotation` 结构上不可能 | `81` 发现 1；`ir.py:87` |
| 2 | `Bypasses: Resolver only` | `81 §5.2` |
| 3 | V3 先冻结消费契约，preprocessing 再实现（方向不可颠倒） | `81 §5.4` |
| 4 | Adapter 白名单仅五项机械操作 | `81 §5.5` |
| 5 | 核心不变量「Adapter 只允许机械投影，不允许提高信息量」+「指不出来源的输出 = 违规」 | `81 §5.6` |
| 6 | ResolvedSpan 生产者不变量：Resolver 与 Adapter 产出同构，下游不区分 | `81 §6.2` |

**UNPROVEN 部分**：「必须经过 V3 自己的 contract validation」目前**无可指向的
契约**——manifest schema **未冻结**（§1.3），因此 External Claim 的验证内容
（哪些字段、哪些校验、何种 fail-closed）**尚不存在规范**。这不是裁决缺口，是
**前置依赖未就绪**：manifest schema 冻结属 `81 §5.4` 前置 2。

**结论**：BIND-3 方向 **ACCEPTED**；**契约级验证 = UNPROVEN**。

#### 5.3.1 为什么 PAUSE 而不是继续设计（2026-09-13 Owner 二次裁决）

BIND-3 的 UNPROVEN **此前被误读成「需要立即继续设计 Manifest Schema」**。这两个
含义完全不同，本轮明确区分：

| | 含义 | 当前 |
|---|---|---|
| ❌ 误读 | 「BIND-3 尚未完成 → 应立即继续设计」 | **不成立** |
| ✅ 裁决 | 「BIND-3 缺必要上游事实 → **暂缓**架构裁决」 | **PAUSED** |

**缺失的是上游生产事实，不是 V3 内部推理。** 以下均**尚未**在生产级 corpus 上验证：

| # | 待验证事实 |
|---|---|
| 1 | 最终 Source Markdown 的 fidelity |
| 2 | deterministic repair 后文本质量 |
| 3 | line structure 的稳定性 |
| 4 | LLM reslice 对真实数据的稳定性 |
| 5 | unit / question / material / stem / options / answer / explanation / extra 实际覆盖率 |
| 6 | composite question 的实际表达能力 |
| 7 | figure / material 的引用与关联质量 |
| 8 | answer region 是否始终覆盖评分依据 |
| 9 | explanation region 是否稳定覆盖解析过程 |
| 10 | 题号 / unit identity 与 source line 的长期稳定对应 |
| 11 | 真实大规模 corpus 上的失败类型与失败比例 |
| 12 | Manifest 在真实数据上的完整性、可追溯性与 fail-closed 行为 |

preprocessing 的 **trial 结果不能替代生产级事实**。

**因此当前显式不冻结**（全部保持 Candidate）：

```text
Manifest Schema · BIND-3 完整契约 · Path B 最终接口 · Adapter 输入/输出
· Adapter 是否 bypass Resolver · preprocessing evidence 是否可直入 ResolvedRun
· material / figure 的 Carrier 方式 · 两条路径的最终 convergence point
```

`Manifest → Adapter → ResolvedRun` 目前**只能**是 **Candidate Architecture**，
**不得**作为 Frozen Architecture 引用。

**正确顺序（冻结）**：

```text
Preprocessing 实际生产输出 → 发现它真实能提供什么 → 识别哪些是 External Claims
  → 与 V3 Frozen Contract 对照 → 确定真正缺失的边界
  → 决定是否需要 Adapter → 决定 Adapter 做什么
```

禁止倒置为「V3 内部希望得到什么 → 反推 preprocessing 必须提供什么 → 设计 Adapter
把它转换出来」。

**重开条件**：preprocessing 收口并形成可复现的生产级输出后，按 §5.3.1 表 12 项
逐条取证，再重开 C-01 / BIND-3。

### 5.4 当前候选状态（更新）

| 候选 | 状态 |
|---|---|
| `line_refs` = manifest-only | 🟡 **PROVISIONAL ARCHITECTURAL PREFERENCE**（BIND-1/2 均 PASS；BIND-3 契约验证 UNPROVEN → **仍不可冻结**）。**阻塞原因已改判：非「待设计」，而是「待上游生产事实」（§5.3.1）** |
| `line_refs` = annotation 内 | 🔴 **REJECT as Native Path 规范输入**（BIND-2 已 PASS 证明 Native 不接受它作为输入；Resolver 产出它作为**输出**则合法）。不预先排除未来载体变更——那需独立 CHANGE + 四道门 |
| 两者共存 | 🔴 **REJECT**（产生「哪个权威」歧义，削弱单一来源保证） |

**`Binding Carrier Decision` 仍 = `PENDING`。** manifest-only **未冻结**。
**67 号 Errata 未发布。Adapter 未开工。**
**C-01 = OPEN / PAUSED**——暂停于上游事实缺口，**不**暂停于架构错误。

---

## 6. 本轮修正的事实性错误

| 文件 | 修正 | 依据 |
|---|---|---|
| `81:11` | 「Gate B 系列 CLOSED（80 号）」→ 精确列出 B1 CONDITIONAL PASS / B2-A~B5 各自状态 / 两项 DEFERRED / **Gate B 整体 NOT CLOSED** | §3.2 聚合规则；`80:421`/`80:432`/`80:437` |
| `69 §8` | 加 supersede 指针 → 本文档 §8 | §4-C2 |
| `74` | **不改写正文**（历史报告）；其 Gate C 状态行由 §3.1 废止 | §4-C1 |
| `restart-prompt` 下一步 | 「Errata Decision」→「Contract Authority Reconciliation → Binding Decision」 | §0.1 |

**未做**：不修改 `20`；不冻结 manifest-only；不写 Errata Decision；不实现 Adapter。

---

## 7. 显式不主张

1. **不主张** Binding Carrier 已定——BIND-1 / BIND-2 均 PASS/FROZEN，BIND-3 方向
   ACCEPTED 但契约验证 UNPROVEN；Carrier 仍 PENDING。**不主张** manifest-only 已冻结。
   **C-01 = OPEN / PAUSED**（§5.3.1）：暂停于**上游生产事实缺口**，不是架构错误，
   也**不**意味着「应立即继续设计 Manifest Schema」。
2. **不主张** Gate B 已关闭——整体 NOT CLOSED（§3.1）。
3. **不主张** E1 可以写进 20——它是 CHANGE-2，需 Change Record（§2 / §4-C6）。
4. **不主张** 本文档可修改 A 层语义——本文档只建立权威层级，不改任何 Frozen 契约。
5. **不主张** C 层报告的历史正文已全部去规范性化——C1/C2/C5 只登记与废止，
   未逐句改写历史报告。
6. **不主张** BIND-1 ACCEPT 等于 Adapter 可开工——开工前置仍为 `81 §5.4` 三项。

---

## 8. 下一步（权威顺序）

```text
Contract Authority Reconciliation（本文档）  ← 现在
        ↓
Gate State 维持于 82 §3（每次状态变更同 commit 更新）
        ↓
Binding Authority Decision（BIND-1 / BIND-2 / BIND-3）
        ↓
V3 Annotation Contract 冻结（V3 拥有，preprocessing 实现）
        ↓
Manifest Contract 冻结
        ↓
Change Records（E1=CHANGE-2；67=CHANGE-4/5 → REJECT/WITHDRAW）
        ↓
Errata Decision
        ↓
最小 Adapter + 对抗性测试 → 真实 corpus E2E → Path B Full Closure
```

**不得倒序。** 在 Authority 层与 Binding Carrier 未定前修改 20 或实现 Adapter，
都会让实现反过来定义契约——重蹈 V2「代码先行、契约后补」。

非 Path B 侧（不阻塞于上表）：OQ-3 → OQ-2 → B2-B2 Unknown 125 triage（补 C4 scope
声明）→ Phase 2 Evidence Ledger。

---

## 9. Status Header 规范（83 号起强制）

**每份新文档必须以如下块开头**，使 Agent 无需猜测权威层级：

```text
Document Type:  <Frozen Spec | Decision Record | Governance Record |
                 Phase Report | Status | Experimental>
Authority Level: <A | B | C | D | E>
Status:         <ACTIVE | SUPERSEDED | HISTORICAL | DRAFT | CLOSED>
Normative:      <YES | NO>
Supersedes:     <doc list 或 —>
Superseded By:  <doc 或 —>
Gate State Authority: <YES | NO>     # 仅 YES 时可定义 Gate 状态；现行唯一为 82 §3
```

**81 号 / 82 号 回填示例**

| | 81 | 82 |
|---|---|---|
| Document Type | Decision Record | Governance / Authority Record |
| Authority Level | B | B（**治理根**） |
| Status | ACTIVE | ACTIVE |
| Normative | NO（裁决范围内的契约描述，**不是 Frozen Spec**） | NO（治理规则，不改 A 层语义） |
| Gate State Authority | NO | **YES** |

**既有文档不强制回填**（Reconcile, don't rewrite）；下次实质性修订时补上。

---

## 10. Phase I-5 CURRENT BASELINE（2026-09-13 冻结）

> **本表优先于任何 Phase Report。** 与本表冲突的文档一律 stale。

╔════════════════════════════════════════════════════════════╗
║              PHASE I-5 CURRENT BASELINE                    ║
╠════════════════════════════════════════════════════════════╣
║ Scope Freeze (I-5-0)         CLOSED                        ║
║ I-5-1 Feasibility            HISTORICAL / NON-REPRODUCIBLE ║
║ Gate A                       PASS / TEST-EVIDENCED         ║
║ Gate B                       NOT CLOSED                    ║
║ Gate C                       CLOSED — Phase 1              ║
║ Gate D                       CONTRACT CLOSED               ║
║ Adapter implementation       NOT STARTED                   ║
║ Binding Carrier              PENDING — C-01 OPEN / PAUSED  ║
║ BIND-1 Identity Join         PASS — ACCEPTED / FROZEN      ║
║ BIND-2 Native Carrier        PASS — ACCEPTED / FROZEN      ║
║ BIND-3 External Carrier      方向 ACCEPTED / 契约 UNPROVEN ║
║                              （PAUSED — 待上游生产事实）   ║
║ Errata 67                    NOT RELEASED (CHANGE-5)       ║
║ E1 (Grammar → 20 §8.4)       PENDING — CHANGE-2            ║
║ E2 (Adapter 边界 → 20 §3)    DEFERRED                      ║
║ V3 Annotation Contract       NOT FROZEN                    ║
║ Manifest Contract            NOT FROZEN                    ║
║ Document Governance (I-5-G)  收口（8/10 全绿，2 项部分）   ║
║ 下一步                       preprocessing 独立收口        ║
║                              （不进 I-5-BIND — 见 §10）    ║
╚════════════════════════════════════════════════════════════╝

**I-5-G 完成条件（10 项，全部满足才进入 I-5-BIND）**：

1. Authority Matrix 建立 ✅（§1）
2. Gate State Authority 建立 ✅（§3）
3. Supersession 关系清理 ✅ — C1/C2/C3 已处理；D-01（71 号双份）CLOSED；
   A-01/A-02/A-05 的废止记录与 supersession banner 均已就位（2026-09-13 DG-5）
4. 所有 ACTIVE 文档 authority/status 明确 ✅ — **UNASSIGNED = 0**；
   D-02 归层（4×Closure → L2）+ D-03 去自封（63/65/68）已完成。
   （`90 §4` Status Header **存量不强制回填**，增量补齐）
5. 所有 normative-looking phase/report 文档完成分类 — **部分完成**：分层归属已全部
   明确（同第 4 项）；`74` 的 6 处自立规范已改引用式（D-04）。**残留**：census 的
   P1 overreach 候选（10 份 L4）——按 `91 §6.1` 扫描器是**候选生成器不是裁决器**，
   待逐条人工裁决，非已确认违规
6. Gate 状态不存在冲突 ✅ — A-04（B2-B2 scope）与 A-05（69 三个 stale 块）已处理；
   全部 Gate 状态经 §3 唯一权威收口（2026-09-13 DG-5）
7. Frozen Spec 不被后续报告隐式修改 ✅（§1.4 规则 1）
8. CHANGE-0…5 覆盖所有现有 Contract Change 候选 — **进行中**（E1=CHANGE-2 已归类；
   67=CHANGE-4/5 REJECT；其余候选待 Authority 层清理完成后走 Change Record）
9. `67 / 69 / 74 / 80 / 81 / 82` 关系可解释 ✅（§1.2 + §4）
10. 全仓不存在**未分类的** normative contradiction ✅ — 84 台账 A 类 0 OPEN ·
    D 类 0 OPEN；剩余 3 项**均已分类**：C-01 = OPEN/**PAUSED**（§5.3.1）、
    B-03 = 检测器局限（非缺陷）、B-04 = 故意 PENDING（非缺陷）

> ⚠️ **I-5-G 全绿 ≠ 可以进入 I-5-BIND。** 2026-09-13 Owner 五次裁决改变了顺序：
> I-5-G 收口后**不进入 I-5-BIND**，而是 **C-01 PAUSED → preprocessing 独立收口 →
> 以生产级真实输出重开 C-01/BIND-3**，之后才谈 I-5-BIND。见 §5.3.1 与 `84 §4`。
> **治理完成不是架构开工的授权。**

---

## 11. Agent 读取顺序（强制）

为防上下文污染——把旧结论、新结论、实验结论与用户最新要求「综合理解」后
自行创造一个不存在的 Contract（C3 即此类产物）——Agent 读取顺序强制为：

```text
1. 82 号（Authority + Gate State + Baseline）
2. Frozen Spec 00–50
3. 相关 Decision Record
4. 82 §3 当前 Gate 状态
5. Experimental 证据
6. 历史文档
```

**禁止**「grep 到什么读什么」。
