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

---

## A 类 — 状态漂移（Gate / Phase 状态在文档间不一致）

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **A-01** | Gate C：`74` 仍 BLOCKED，`80` 已 CLOSED，无废止记录 | `74:5` `74:363` `74:537` vs `80:439`；C-1=`75`、C-2=`76`/`77` 已完成 | 🔴 | **SUPERSEDED** | `82 §3.1` 即废止记录；`74` 三处已加 supersede 标注 |
| **A-02** | `69 §8` 无日期路线图仍写「Errata Decision（Gate A-D 全部通过后）」 | `69:306` | 🔴 | **SUPERSEDED** | 已加 supersede 指针 |
| **A-03** | `81:11` 称「Gate B 系列 CLOSED」，过度陈述 `80` | `81:11` vs `80:421`（B1 CONDITIONAL）、`80:432`/`80:437`（DEFERRED） | 🔴 | **INCORPORATED** | 本轮自引入，已修正；聚合规则见 `90 §5 Rule 1` |
| **A-04** | `80` 内部：B2-B2 同时 CLOSED 与「Unknown 125 仍未清」 | `80:426`（CLOSED，99.8% = 1176/1178）vs `80:448` | 🟠 | **OPEN** | **歧义非错误**。合理读法：closed scope = 已测 1178 个 MC target，Unknown 125 在 scope 外，但 `80` **未写明**。待 triage 完成补 scope 声明 |
| **A-05** | `69` 带日期矩阵仍写 B2-B 为 BLOCKED / WAIT | `69:656`、`69:756` vs `80:426` 起 B2-B1~B5 已 CLOSED | 🟠 | **OPEN** | 历史快照，**建议保留原文**，以 `82 §3` 为准。（全仓**无**「B2-B = NEXT」表述） |
| **A-06** | `61` `Status: IN PROGRESS`，而 `Closure/PHASE_I3_CLOSURE.md` 已 CLOSED / Gate PASS | `61:4` vs `Closure/PHASE_I3_CLOSURE.md:4-5` | 🟠 | **OPEN** | **Phase I-3 关闭后 61 从未回写**。建议 61 加 supersede 标注 → Closure 记录 |
| **A-07** | `73:213` 声明 157 targets `UNRESOLVED / REVIEW REQUIRED`，而 Gate C 以 C-2「157 E2E」关闭 | `73:213-221`（NOT proven 全是**语义正确性**：correct / incorrect / auto-admitted / pass manual review）vs C-2 实际 = `test_c2_evidence_authority_e2e.py`（Semantic IR bypass 5 测 + Lifecycle 5 测 + 157 fail-closed 4 测） | 🔴 | **DECIDED** | **语义A 成立，非语义B**。C-2 证明**管线不变量**（invalid binding 不产生 validated evidence、IR bypass 阻断）；`73` 的 UNRESOLVED 是**语义裁决**——从来不是 Gate C 职责。二者正交，**Gate C CLOSED 成立**。已在 `73` 文首写入 **C-2 Evidence Scope Clarification**，**正文未改**（`73:202-204` 三项 RETRACTED 继续有效）。157 个的语义裁决仍属人工审未完成项 |
| **A-08** | `Status.md` 同时含已撤回与已修正的 Grammar 输入契约 | `Status.md:2309`（`必须是 Resolver 产出`——已撤回措辞，**未标记**）vs `Status.md:2423`（不变量版） | 🟠 | **OPEN** | **对立极性同主题**。2309 所在历史节未标 retracted |
| **A-09** | `Status.md` 顶层 Status 行 stale | 首个 Status 行 = `V3 Spec Baseline — Frozen（实现未开始）`，而 `backend/app` 已有完整实现 | 🟡 | **OPEN** | 正则取首个 Status 行；最新节在文件末尾。建议顶层 Status 改为指针 → `82 §3` |

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
| **C-01** | **`line_refs` 载体四方不一致** | L0 `20:117` FORBIDDEN_FIELDS 含 `line_refs`；`20:73` 硬边界 #2「不携带 resolved span / line_ref」；`67:114` 提议放进 annotation payload；`81 §5.1` 定在独立 manifest；`82 §5` 判 `PENDING` | 🔴 | **OPEN（BIND-1/2 已 PASS）** | 裁决见 `82 §5`：BIND-1 **PASS/FROZEN**；BIND-2 **PASS/FROZEN**（Owner 确认 2026-09-13）；BIND-3 方向 ACCEPTED / 契约 UNPROVEN。**manifest-only 仍 🟡 PROVISIONAL**，Carrier = PENDING。**单一剩余阻塞 = BIND-3**（manifest schema 冻结后完成契约验证） |
| **C-02** | `66 §7` `Bypasses: Annotation, Resolver` 与 `IRBuilder.build` 签名冲突 | `66 §7` vs `ir.py:87` `build(resolved_run, annotation_payload, ...)` 必需 annotation_payload；span_id `sp-{unit_id}.{role}` 由 annotation 反推 | 🔴 | **INCORPORATED** | 已修正为 `Bypasses: Resolver only`；`66 §7` 就地更正；裁决见 `81 §5.2` |

---

## D 类 — 分层 / 归属

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **D-01** | **71 号同号双份且内容不同** | 原 `Docs/V3_SPEC/71_…`（6914 B，Sep 12 21:33，「裁决记录」）vs 原 `backend/Docs/V3_SPEC/71_…`（7783 B，23:05，「(CORRECTED)」）；`diff -q` = **DIFFERENT** | 🔴 | **DECIDED** | **DG-3 处置（2026-09-13）**：root 版判 **stale**，`git mv` 至 `Docs/ARCHIVE/71_…_SUPERSEDED.md` 并加 SUPERSEDED 声明块（`90 §2 R8`：正文保留、不得作为引用来源、`docs_audit` 标 `deprecated`）；backend CORRECTED 版为**权威版**，移至 `Docs/DECISIONS/71_…` 并归 **L2**。**两份都未删除。** |
| **D-02** | 5 份文档在 V3_SPEC 树内但未归层（837 行） | `Closure/PHASE_I2C` `PHASE_I2_REVISION` `PHASE_I3` `PHASE_I4_CLOSURE.md`（均含 `Status: CLOSED`；`PHASE_I3_CLOSURE.md:5` 直接写 `Gate: PASS`）+ `gate_b2a_three_task_report.md` | 🔴 | **OPEN** | 未归层 = 不得引用为权威（`90 §1`）。**建议**：4×Closure → **L2**；`gate_b2a_…` → **L4** |
| **D-03** | 分层错误 3 份 | `63:3` `Status: Frozen Constraint`（L4 位置自封 L0 权限）；`65:95-106` 十二条禁令实为 scope freeze 契约；`68` 经 `69` 判为 Domain Definition Proposal | 🟠 | **OPEN** | `63` **升 L0 须走 L1**，不能靠改标签（`90 §2 R1`）。`65` 建议归 **L2**。`68` 保持 L4 但须注明 `69` 定性 |
| **D-04** | L3 `74` 对 V3 自立规范 6 处 | `74:224`（Native Path **必须**保证…）`74:226`（preprocessing **必须**满足…）`74:283`（answer span **不得**重叠）`74:385`（**唯一**允许进 IR）`74:395-396`（**禁止** CLAIMED/PROPOSED → IR）`74:418`（Validation **必须** append-only） | 🟠 | **OPEN** | 违反 `90 §2 R3`（L3 不得定义规则）。对照 `74:94`「这个结果**只能**证明」是**正确用法**——同文档两种用法并存，说明缺的是分类约束。大多已被 `75 号`（L2）承接，待逐条加指针 |
| **D-05** | Gate 状态行集中面：`Status.md` 45 行 / `69` 42 行 | 扫描统计 | 🟠 | **OPEN** | 聚合错误最大温床（A-03 即此类产物）。**建议**：新增行强制 `90 §4` + `82 §3.3` 模板；存量不回填 |

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

> **2026-09-13 三次裁决后**：A-07 / B-01 / B-02 / **CA-001** 已处置。剩余 OPEN 11 项。

| 序 | ID | 为什么先 |
|---|---|---|
| 1 | **D-01**（71 号双份） | 阻塞 `90 §10` 第 10 项「无未登记 contradiction」；两文件抢同号 |
| 2 | **C-01**（`line_refs` 四方不一致） | 未来 preprocessing 架构的根；须走 BIND-1/2/3 |
| 3 | **D-02 / D-03**（归层：Closure 4 份 + `63`/`65`/`68`） | 未归层 = 不得引用为权威；`63` 升 L0 须走 L1 |
| 4 | **A-04 / A-06 / A-08 / A-09**（状态歧义与 stale） | 常规对账 |
| 5 | **D-04 / D-05**（L3 自立规范 + 状态行集中面） | 引用式改写，逐条 |
| 6 | **B-03 / B-04**（检测器局限 / 故意 PENDING） | 非缺陷；B-03 已随检测器改进大幅缓解 |

---

## 3. 显式不主张

1. **不主张**本台账任何条目已裁决——除已标 `SUPERSEDED` / `INCORPORATED` 者。
2. **不主张**本台账穷尽全部冲突——只覆盖 `90 §5` 四条规则的机械可查部分 + 本轮人工核验项。
3. **不主张** E 类误报是缺陷——它们是**检测器局限**，记录以防重复排查。
4. **不主张** A 层可据本台账修改——修改 A 层须走 L1（`90 §2 R1`）。
5. **不主张**本台账削弱 `82 §3` 的 Gate State Authority——**82 §3 仍是唯一权威**。

---

## 4. 下一步

```text
本台账（84 号，15 项 OPEN）      ← 现在
        ↓
逐条裁决（§2 优先级顺序）
        ↓
docs_audit/ 四件产物复核
        ↓
90 §10 十项完成条件全绿
        ↓
I-5-BIND — Binding Authority Decision（C-01 的 BIND-1/2/3）
```

**不碰 L0、不发 67、不冻结 manifest-only、不实现 Adapter。**
