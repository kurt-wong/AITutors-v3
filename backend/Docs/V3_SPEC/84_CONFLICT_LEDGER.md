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
| A 状态漂移 | 7 | 3 | 0 |
| B 术语未定义 / 漂移 | 3 | 0 | 1 |
| C 架构边界冲突 | 1 | 1 | 0 |
| D 分层 / 归属 | 4 | 0 | 0 |
| E 误报 | — | — | 3 |
| **合计** | **15** | **4** | **3** |

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
| **A-07** | `73:213` 声明 157 targets `UNRESOLVED / REVIEW REQUIRED`，而 Gate C 以 C-2「157 E2E」关闭 | `73:213-216`（`NOT proven: All 157 are correct bindings`）vs `80:439` + commit `f5e2020` | 🔴 | **OPEN** | **A-01 同类**：C-1/C-2 完成于 09-13，`73` 作于 09-11，疑虑或已解决但**无文件声明 73 已关闭**。需确认 C-2 是否实质回应了 73 的质疑 |
| **A-08** | `Status.md` 同时含已撤回与已修正的 Grammar 输入契约 | `Status.md:2309`（`必须是 Resolver 产出`——已撤回措辞，**未标记**）vs `Status.md:2423`（不变量版） | 🟠 | **OPEN** | **对立极性同主题**。2309 所在历史节未标 retracted |
| **A-09** | `Status.md` 顶层 Status 行 stale | 首个 Status 行 = `V3 Spec Baseline — Frozen（实现未开始）`，而 `backend/app` 已有完整实现 | 🟡 | **OPEN** | 正则取首个 Status 行；最新节在文件末尾。建议顶层 Status 改为指针 → `82 §3` |

---

## B 类 — 术语未定义 / 术语漂移

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **B-01** | **`Evidence Contract` 零定义**，却被 ≥4 份文档当作约束依据 | 13 处使用：`74:165` `74:226` `74:241` `80:181` `81:221` `restart-prompt:99` 等；grep「Evidence Contract + (定义\|指的是\|即\|denotes)」**零命中** | 🔴 | **OPEN** | 多处写「preprocessing **必须满足** V3 Evidence Contract」——**用一个从未定义的术语立规**。违反 `90 §2 R6`。实际指向 `75 号`（C-1 设计冻结），但从未被显式等同 |
| **B-02** | 三个近义词只有一个有宪法地位 | `Validated Evidence` **10 处全在 L3 `74`**，L0/L2 零定义；`Verified Evidence` **全仓零使用**；L0 `20 §8.3` 用 `verified_correct` | 🔴 | **OPEN** | 用户 H-A 风险：`ValidatedEvidence = correct answer` 的误读温床。**建议**：冻结 `20 §8.3 verified_correct` 为唯一合法术语，`74` 的 `Validated Evidence` 判为非规范用语 |
| **B-03** | `ResolvedSpan` 100 处使用，检测器判零定义 | 用例分布于 `20`/`65`/`66`/`67`/`69`/`81` | 🟡 | **OPEN（疑误报）** | 实际由 L0 `20 §5.5` **字段表**定义，非散文定义句；检测器只匹配「定义/定为/冻结为」。**建议**：改进检测器识别表格定义，而非改文档 |
| **B-04** | `Binding Carrier` 10 处使用，零定义 | `82 §5` 引入 | 🟡 | **OPEN（故意）** | 已登记为 `PENDING`（BIND-1/2/3 未裁决）。**不是缺陷**，是未决标记 |

---

## C 类 — 架构边界冲突（同一约束的对立规定）

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **C-01** | **`line_refs` 载体四方不一致** | L0 `20:117` FORBIDDEN_FIELDS 含 `line_refs`；`20:73` 硬边界 #2「不携带 resolved span / line_ref」；`67:114` 提议放进 annotation payload；`81 §5.1` 定在独立 manifest；`82 §5` 判 `PENDING` | 🔴 | **OPEN** | **本轮最重的架构未决项**。四个层级给出四种答案。须经 **BIND-1/2/3**（`82 §5`）裁决后走 L1。**在裁决前，manifest-only 只是 🟡 PROVISIONAL** |
| **C-02** | `66 §7` `Bypasses: Annotation, Resolver` 与 `IRBuilder.build` 签名冲突 | `66 §7` vs `ir.py:87` `build(resolved_run, annotation_payload, ...)` 必需 annotation_payload；span_id `sp-{unit_id}.{role}` 由 annotation 反推 | 🔴 | **INCORPORATED** | 已修正为 `Bypasses: Resolver only`；`66 §7` 就地更正；裁决见 `81 §5.2` |

---

## D 类 — 分层 / 归属

| ID | 冲突 | 证据 | 级别 | 状态 | 备注 |
|---|---|---|---|---|---|
| **D-01** | **71 号同号双份且内容不同** | `Docs/V3_SPEC/71_…`（6914 B，Sep 12 21:33，「裁决记录」）vs `backend/Docs/V3_SPEC/71_…`（7783 B，23:05，「(CORRECTED)」）；`diff -q` = **DIFFERENT** | 🔴 | **OPEN** | **本轮最重的文档治理缺陷**。两个文件抢同一编号且无废止声明；**旧的那份在 L0 目录里**，路径直觉会当更权威。**建议**：root 版判 stale + supersede 指针 → backend CORRECTED 版；**不删除任一份** |
| **D-02** | 5 份文档在 V3_SPEC 树内但未归层（837 行） | `Closure/PHASE_I2C` `PHASE_I2_REVISION` `PHASE_I3` `PHASE_I4_CLOSURE.md`（均含 `Status: CLOSED`；`PHASE_I3_CLOSURE.md:5` 直接写 `Gate: PASS`）+ `gate_b2a_three_task_report.md` | 🔴 | **OPEN** | 未归层 = 不得引用为权威（`90 §1`）。**建议**：4×Closure → **L2**；`gate_b2a_…` → **L4** |
| **D-03** | 分层错误 3 份 | `63:3` `Status: Frozen Constraint`（L4 位置自封 L0 权限）；`65:95-106` 十二条禁令实为 scope freeze 契约；`68` 经 `69` 判为 Domain Definition Proposal | 🟠 | **OPEN** | `63` **升 L0 须走 L1**，不能靠改标签（`90 §2 R1`）。`65` 建议归 **L2**。`68` 保持 L4 但须注明 `69` 定性 |
| **D-04** | L3 `74` 对 V3 自立规范 6 处 | `74:224`（Native Path **必须**保证…）`74:226`（preprocessing **必须**满足…）`74:283`（answer span **不得**重叠）`74:385`（**唯一**允许进 IR）`74:395-396`（**禁止** CLAIMED/PROPOSED → IR）`74:418`（Validation **必须** append-only） | 🟠 | **OPEN** | 违反 `90 §2 R3`（L3 不得定义规则）。对照 `74:94`「这个结果**只能**证明」是**正确用法**——同文档两种用法并存，说明缺的是分类约束。大多已被 `75 号`（L2）承接，待逐条加指针 |
| **D-05** | Gate 状态行集中面：`Status.md` 45 行 / `69` 42 行 | 扫描统计 | 🟠 | **OPEN** | 聚合错误最大温床（A-03 即此类产物）。**建议**：新增行强制 `90 §4` + `82 §3.3` 模板；存量不回填 |

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

| 序 | ID | 为什么先 |
|---|---|---|
| 1 | **D-01**（71 号双份） | 阻塞 `90 §10` 第 10 项「无未登记 contradiction」；两文件抢同号 |
| 2 | **A-07**（73 的 157 targets UNRESOLVED vs Gate C 关闭） | 可能动摇 Gate C CLOSED 的证据基础 |
| 3 | **C-01**（`line_refs` 四方不一致） | 未来 preprocessing 架构的根；须走 BIND-1/2/3 |
| 4 | **B-01**（`Evidence Contract` 零定义却被用来立规） | 违反 `90 §2 R6`；影响面 ≥4 份文档 |
| 5 | **B-02**（三近义词一有宪法地位） | 用户 H-A 长期风险 |
| 6 | **D-02 / D-03**（未归层 5 份 + 分层错误 3 份） | 未归层 = 不得引用为权威 |
| 7 | **A-04 / A-06 / A-08 / A-09**（状态歧义与 stale） | 常规对账 |
| 8 | **D-04 / D-05**（L3 自立规范 + 状态行集中面） | 引用式改写，逐条 |

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
