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
| **B2-B2** | **CLOSED — PASS / SCOPE-BOUNDED** | MC answer 99.8%（1176/1178）；**但 Unknown 125 triage 未清**（§4-C4） |
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
| **C4** | `80` 内部：B2-B2 同时 CLOSED 与「Unknown 125 仍未清」 | `80:426`（CLOSED — PASS / SCOPE-BOUNDED，99.8% = 1176/1178）vs `80:448`（B2-B2 Unknown 125 triage → 仍未清） | 🟠 P1 | **登记为歧义**，不判为错误。合理读法是「closed scope = 已测的 1178 个 MC target，Unknown 125 在 scope 外」，但 `80` **未写明**。待 B2-B2 triage 完成后补 scope 声明 |
| **C5** | `69` 带日期状态矩阵仍写 B2-B 为 BLOCKED / WAIT | `69:656`（`BLOCKED BY contract 裁决`）、`69:756`（`WAIT FOR MANIFEST CONTRACT UPDATE`）；而 `80:426` 起 B2-B1~B5 已 CLOSED | 🟠 P1 | 历史快照，**保留原文**。以 §3.1 为准。（注：全仓**无**「B2-B = NEXT」表述） |
| **C6** | E1 性质：写入 20 §8.4 是 **Normative Addition** 而非澄清 | `20:662-679`（§8.4 现文）对 `answer_text` 来源**沉默**；约束已冻结在 `80 §6.6` / `81 §6.2` / `grammar.py` docstring | 🟠 P1 | 按 §2 归 **CHANGE-2**。**本轮不写入 20**；待 Authority 层清理完成后走 Change Record |
| **C7** | 无 Authority Matrix / 无变更分类 | 全仓 grep「Authority Matrix / CHANGE-0 / Normative Addition」零命中 | 🔴 P0 | **本文档 §1/§2 即为建立** |

### 4.1 核验中未成立的指控

| 指控 | 核验结果 |
|---|---|
| 「Gate B2-B = NEXT」 | **不成立**。全仓无「NEXT」措辞。实际残留是 C5 所列的 BLOCKED / WAIT |

---

## 5. Binding Authority — 三个未决问题（**登记，不裁决**）

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

| ID | 未决问题 | 为何必须先答 |
|---|---|---|
| **BIND-1** | Annotation 的 semantic unit 与 Manifest 的 binding unit 之间，是否存在**确定性 identity join**？ | 若 join 依赖顺序 / 题号 / 模糊匹配 / 文本相似度，则**重新引入 Resolver-like 问题**，直接违反 81 §5.6「不得隐式 fuzzy matching」与核心不变量「只允许机械投影」。**这是本轮最值得新增的审查点** |
| **BIND-2** | Native Path 能否完全脱离 `annotation.line_refs`？ | 若 Native Path 仍需 annotation 携带位置信息，则 manifest-only 不能成为**唯一**载体，`20:117` 的 `FORBIDDEN_FIELDS` 也不能整体维持 |
| **BIND-3** | Manifest 中的 role declaration（stem/options/answer/explanation）只是 **External Claim**，还是 V3 **Semantic Authority**？ | 若是后者，等于把「V3 可以接受 preprocessing 的结果」偷换成「V3 相信 preprocessing 的语义判断」，违反 `00` 的 Source-as-Fact-Source。**初步倾向：External Claim Producer**，但未裁决 |

### 5.1 当前候选状态

| 候选 | 状态 |
|---|---|
| `line_refs` = manifest-only | 🟡 **PROVISIONAL ARCHITECTURAL PREFERENCE**（须 BIND-1/2/3 全 PASS 才可冻结） |
| `line_refs` = annotation 内 | 🔴 **不得作为新规范继续推进**（与 81 §5.1 冲突；若采纳需先裁决） |
| 两者共存 | 🔴 **REJECT**（产生「哪个权威」歧义，削弱单一来源保证） |

**在 BIND-1/2/3 裁决前，`Binding Carrier Decision = PENDING`。**

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

1. **不主张** BIND-1/2/3 已解决——只登记，未裁决。
2. **不主张** manifest-only 正确——只是候选方向。
3. **不主张** Gate B 已关闭——整体 NOT CLOSED（§3.1）。
4. **不主张** E1 可以写进 20——它是 CHANGE-2，需 Change Record（§2 / §4-C6）。
5. **不主张** 本文档可修改 A 层语义——本文档只建立权威层级，不改任何 Frozen 契约。
6. **不主张** C 层报告的历史正文已全部去规范性化——C1/C2/C5 只登记与废止，
   未逐句改写历史报告。

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
║ Scope Freeze (I-5-0)          CLOSED                       ║
║ I-5-1 Feasibility             HISTORICAL / NON-REPRODUCIBLE║
║ Gate A                        PASS / TEST-EVIDENCED        ║
║ Gate B                        NOT CLOSED                   ║
║ Gate C                        CLOSED — Phase 1             ║
║ Gate D                        CONTRACT CLOSED              ║
║ Adapter implementation        NOT STARTED                  ║
║ Binding Carrier               PENDING (BIND-1/2/3)         ║
║ Errata 67                     NOT RELEASED (CHANGE-5)      ║
║ E1 (Grammar → 20 §8.4)        PENDING — CHANGE-2           ║
║ E2 (Adapter 边界 → 20 §3)      DEFERRED                     ║
║ V3 Annotation Contract        NOT FROZEN                   ║
║ Manifest Contract             NOT FROZEN                   ║
║ Document Governance (I-5-G)   ← CURRENT WORK               ║
╚════════════════════════════════════════════════════════════╝

**I-5-G 完成条件（10 项，全部满足才进入 I-5-BIND）**：

1. Authority Matrix 建立 ✅（§1）
2. Gate State Authority 建立 ✅（§3）
3. Supersession 关系清理 — **进行中**（C1/C2/C3 已处理；G3 的 71 号双份待裁决）
4. 所有 ACTIVE 文档 authority/status 明确 — **进行中**（§9 规范已立，存量待回填）
5. 所有 normative-looking phase/report 文档完成分类 — **进行中**（83 号审计）
6. Gate 状态不存在冲突 — **进行中**（以 §3 对账中）
7. Frozen Spec 不被后续报告隐式修改 ✅（§1.4 规则 1）
8. CHANGE-0…5 覆盖所有现有 Contract Change 候选 — **进行中**
9. `67 / 69 / 74 / 80 / 81 / 82` 关系可解释 ✅（§1.2 + §4）
10. 全仓不存在未分类的 normative contradiction — **进行中**（83 号）

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
