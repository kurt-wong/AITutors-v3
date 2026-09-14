Version: v1.61
Status: **Documentation Governance 稳定；转入代码与架构对抗性审查（Step 1 已冻结）** —
**C-01 = OPEN / PAUSED**（权威落点 `82 §5.3.1`）：暂停于**上游生产事实缺口**，**非架构错误**；
BIND-1 **PASS/FROZEN** · BIND-2 **PASS/FROZEN** · BIND-3 方向 ACCEPTED / 契约 UNPROVEN；
**84 台账 A 类 0 OPEN · D 类 0 OPEN**；
**本轮对抗性审查新增 6 项发现（`bugs.md` 045–050）**，Owner 四分类：
产品实现缺陷 **045/046/047 应修** · 架构契约未闭环 **048 不编码** ·
输入鲁棒性 **049 延后 preprocessing** · 测试基础设施 **050 单独立项**；
下一步 = **Step 2 修 045/046/047**（需 Owner 明示开工）——
**不是**设计 Manifest Schema，**不是**实现 Adapter
Date: 2026-09-13

## 0.0e 代码与架构对抗性审查 · Step 1 冻结（2026-09-13）

**本轮性质**：代码与架构对抗性审查，**非**文档治理。四维度摸底（重试分层 / Resolver 不猜 /
Sealed 不可变 / Evidence 权威边界）→ 对每个可证伪缺口**自己写测试实测**，不采信摸底报告结论。

### 已证伪（红线成立）

```text
HTTP retry × LLM retry 乘法  9 post / 3 Invocation / 1 Audit / budget 1-0  ✅ 红线成立
真实 400 端到端不重试         1 post / 1 invocation / 1 failed audit       ✅ 不重试
fallback 默认关闭哨兵         settings.provider_fallback_enabled is False  ✅ 已锁
FORBIDDEN_FIELDS list-in-list a[0][0].line_refs 正确检出                   ✅ 递归正常
UNIQUE 三元组 DB 层           重复插入抛 IntegrityError                     ✅ 有效
Resolver 不猜负向矩阵         现有 31 例充分覆盖，未发现新猜路径             ✅
```

### 六项发现（四分类，**不统一进修复列表**）

| ID | bugs.md | 类型 | 处置 |
|---|---|---|---|
| **F-2** | 048 | **架构契约未闭环（非 bug）** | 改 C-2 表述，**暂不编码** |
| **F-3** | 045 | 产品实现缺陷 HIGH | **修** |
| **F-5** | 046 | 产品实现缺陷 HIGH | **修**（查全部 annotation 入口） |
| **F-6** | 047 | 产品实现缺陷 MEDIUM | **修**，统一 SourceMutationGuard |
| **F-4** | 049 | 输入鲁棒性 | **延后 preprocessing** |
| **F-1** | 050 | 测试基础设施 | **单独立项 TEST-INFRA-01** |

**F-2 定性（Owner 修正我的过度表述）**：Evidence 事件记录 PASS · Promotion 服务 PASS ·
**作为准入条件 FAIL**。实际链路 `Annotation → Resolver → Gate → Admission`，缺
`Evidence Validation → ValidatedEvidence` 环节。
**待裁决架构问题**：Evidence 是 A) 审计记录 还是 B) 准入前置条件？代码选 A，Spec 更接近 B。

**F-4 机制纠正（我纠正摸底报告）**：空白 marker 不是因 `"" in l.text` 恒真 → ambiguous；
实际 `raw_hits` 用原始 query，`"   " in "   "` 恰 1 命中 → `exact`。**非「不猜」违规。**

### 测试四分层（已落地）

```text
tests/test_adversarial_retry_compounding.py      3 PASS    红线反证
tests/test_adversarial_evidence_boundary.py      1 FAIL    F-3 产品契约
tests/test_adversarial_seal_immutability.py      2 FAIL / 2 PASS   F-5·F-6 + 2 已证伪
tests/adversarial/spec_gap/…                     3 XFAIL   F-2×2 · F-4，不进 CI gate
```

`testpaths=["tests"]` 递归收集子目录，**仅分目录不足以排除**，故配 module 级
`pytestmark = xfail`：`pytest -q` 记 xfailed 不计 failed。

### Step 1 完成 · Step 2–4 未开工

**已做**：F-1~F-6 登记 `bugs.md` 045–050 · 测试四分层 · L5 同步。
**未做（等 Owner 明示）**：Step 2 修 045/046/047 · Step 3 只改 C-2 表述不编码 ·
Step 4 单独处理 TEST-INFRA-01。**未改任何产品代码。**

## 0.0d Residual Audit Phase-2：三个搜索目标跑完一轮（A-11，2026-09-13）

按 Owner 认可的三个目标做**定向检索**（**非全库关键词扫描**）：
孤立旧目录 · 失效 provenance · 双份 Closure/Report。

| 目标 | 结果 |
|---|---|
| **孤立旧目录** | `docs_archive/`（8 个日期子目录）**不是孤立**——L0 显式声明为归档落点（`00:396/404`、`50 §6`、`README:6`）；7 份起草输入**在声明落点内 7/7** |
| **双份 Closure/Report** | 受治理树内**无残留**（计数全为 1）；唯一多版本漂移已在 A-10 处置 |
| **失效 provenance** | **20 条，单一根因 = DG-2 迁移未回写入站引用** → **A-11 RESOLVED** |

### A-11 处置（分两类，不逐行改写历史表体）

1. **`69` 三处直接修正路径**（唯一属 **L2 现行文档**；`69:1146` 原把已迁址的 80 号称作
   「本块权威来源」）→ `Docs/DECISIONS/80_B2B5_CLOSURE.md`；
   `1007`/`1083` → `backend/Docs/V3_SPEC/gate_b2b*_frozen_testset.json`。**正文零改动。**
2. **`65` / `83` / `60` / `PHASE_I3_CLOSURE` / `PHASE_I4_CLOSURE` 各加一条 📌 路径 banner**，
   声明内含 `Docs/V3_SPEC/…` 是 DG-2 前路径并给出现行落点。**表体零改动**
   （83 是审计当时的快照，逐行改写 = 伪造审计记录）。

**排除项（不是断链）**：`Docs/reference/` 400+ 条 V2 内部引用（范围外）· `docs_archive/` 内 V2 互引 ·
L0 各册 `Supersedes: Docs/V3_*.md`（起草输入，落点已验）· `50 §6` 迁移映射表。

### 观察（未改，L0 禁改）

`10:7`/`20:8` 称 `docs_archive/2026-09-03/*_v0.3.md` 为「字段权威**参考**」；`20:7` 另称
`10_Data_Model.md` 为「字段**权威**」；`50:159` 限定「唯一遗留参考 · **不指导新实现**」。
措辞分层、**不冲突**。但 **`docs_archive/` 不在 scanner `SCAN_BASES` 内**，故
「L0 出站引用是否可解析」**无机器校验**——工具覆盖缺口，非文档缺陷。**未擅自扩大 scanner 范围。**

### 验收

```text
layers: L0=7 · L0-META=2 · L2=13 · L3=2 · L4=17 · L5=4   （与 A-10 修正后一致）
UNASSIGNED = 0        OPEN candidates: 1 (P0 1) = C-01 OPEN/PAUSED
802 passed, 8 warnings in 40.54s
```

**没做**：未全库关键词扫描 · 未重建 birth certificate · 未重扫 DG-5 已关三类 ·
未动 `Docs/reference` · 未改 L0 00–50 / 90 / 91 · 未调整任何已有 authority level ·
未新建治理文档 · 未新建四类审计报告 · 未改 C-01 · 未动 Manifest Schema / Adapter。

**下一步**：三个搜索目标已跑完一轮。唯一剩余可选项 = 是否给 scanner 加
「L0 出站引用可解析性」检查（不把 `docs_archive/` 纳入 census，只验引用）。
**属新增 scanner 能力，等 Owner 明示，不自动做。**

## 0.0c Residual Audit 案例 1 + 机器源 ARCHIVE 分类缺陷修复（2026-09-13）

**性质**：Documentation **Residual** Audit（残余风险审计）的第一个完整案例，用于**验证方法**。
**不是**重跑 DG-5：DG-5 已关闭的三类（Duplicate Authority / Normative Leakage / State Drift）
**本轮不重扫**。本轮只处理 DG-5 未覆盖的 **Provenance Missing** 与 **Dead/Superseded**。

**范围**：仅 `Docs/{V3_SPEC,DECISIONS,REPORTS,ARCHIVE}` + L5 四文件。**排除 `Docs/reference`。**
未做全库关键词扫描。**未新建任何治理文档**，产出全部落进已有容器（`84` / `docs_audit/` / `Status.md` / `log.md`）。

### 案例：Phase I-2 Revision Closure 双份（`84` A-10 = RESOLVED）

```text
旧份 Docs/V3_PHASE_STATUS/Phase_I2_Revision_Closure.md   6363 B  未进 census（未治理）
权威 Docs/REPORTS/PHASE_I2_REVISION_CLOSURE.md           3339 B  L2（D-02 归层）
```

| 判定 | 结论 |
|---|---|
| 未迁移决策 | **无**——D1 位置 / D3 纯函数 → 权威份 §4；**D2「OCR 是 Provider 不是替代」→ L0 `10_Data_Model.md §4.2` role 枚举 + role/provider 封闭配对（更高权威）** |
| State Drift | 测试数字 421/11 vs **425/15**；新版含更多 commit → **425/15 为准** |
| Provenance | 旧份 `Supersedes: PHASE_I2_REVISION_REVIEW.md` 所指文件**全仓不存在**；`Status.md` 两个历史节各含一个失效路径指针 |
| DELETE 三证 | **三证不全**（有历史价值 ✗ · 有活引用 ✗）→ **不得 DELETE** |
| **Disposition** | **ARCHIVE** → `Docs/ARCHIVE/PHASE_I2_REVISION_CLOSURE_SUPERSEDED.md`（+ SUPERSEDED banner，**正文零改动**）；空目录 `Docs/V3_PHASE_STATUS/` 已移除 |

`Status.md` 两个 2026-09-09 历史节各加 provenance/路径 banner（**历史正文零改动**，
沿用 A-05 / A-08 的 banner-only 先例）；`84` 加 **A-10**（复用 A 类既有 ID 空间，
**未造新问题分类体系**）；`i5g_emit_audit.py` `CANDIDATES` 同步。

### 顺带发现并修复的机器源缺陷（重要）

复跑 scanner 发现 **两份归档件都被误判为 `L2 / active`**：`level_of()` 里 ARCHIVE 分支
排在编号 allowlist 与 CLOSURE 分支之后，**实际是死代码**——`71_…_SUPERSEDED` 命中
`L2_ALLOW` 的 `"71"`，`…_CLOSURE_SUPERSEDED` 命中 CLOSURE 分支。后果：`authority_matrix.yaml`
把**已归档的废止副本报告为现行 L2 权威**，正是归档本应消除的重复权威。

**修复**：ARCHIVE/`_SUPERSEDED` 判定提到 L0-META 之后、编号分支之前；删除下游重复分支。

```text
层计数：L2 14 → 13    L4 15 → 17    census 44 → 45    UNASSIGNED = 0
802 passed, 8 warnings in 43.41s
```

⚠️ **上一轮已提交的 `L2=14` 基线含一份误判为 active 的归档件。** 本轮据实修正，不粉饰。

### 边界

**做了**：provenance 补充 · supersede/archive 修复 · 机器源 ARCHIVE 分类缺陷修复。
**没做**：未重扫 DG-5 已关三类 · 未全库关键词扫描 · 未动 `Docs/reference` ·
未给全部文档建 birth certificate · 未新建四类审计报告（Inventory / Conflict Report /
Consolidation Proposal / Risk Assessment）· 未改 C-01 · 未动 Manifest Schema / Adapter ·
未改 L0 00–50 · 未改 90/91 · 未调整任何已有 authority level。

**方法已验证。是否继续审计其余残余同类项，等 Owner 明示；不自动扩大扫描范围。**

## 0.0b C-01 PAUSE + DG-5 收口（2026-09-13 Owner 五次裁决，权威落点 `82 §5.3.1` + `84 §五次裁决`）

**C-01 = OPEN / PAUSED。** 含义必须读准：

> **不是发现了新的架构错误，而是缺乏必要的上游事实，因此暂缓架构裁决。**

BIND-3 的契约验证暂停，因为 preprocessing **尚未形成可测量、可复现的生产级输出**
（Source fidelity / line stability / role coverage / manifest 完整性 / 失败分布
均未生产验证）。**trial 结果不能替代生产级事实。** 在不知道上游能稳定提供什么之前
冻结 Manifest Schema = **从 V3 内部模型反向规定上游**。

**明确否定的误读**：「BIND-3 UNPROVEN → 立即设计 Manifest Schema → C-01 CLOSED →
Adapter」**只是架构假设链，不是已由事实证明的工程路线。**

**BIND-1 / BIND-2 不因 PAUSE 改变**——它们是 V3 内部证据，不依赖 preprocessing。
**不重开讨论。**

**当前全部保持 Candidate，不冻结**：

```text
Manifest Schema · BIND-3 完整契约 · Path B 最终接口 · Adapter 输入/输出
· Adapter 是否 bypass Resolver · preprocessing evidence 可否直入 ResolvedRun
· material/figure Carrier · 两条路径最终 convergence point
```

`Manifest → Adapter → ResolvedRun` 目前**只能**是 **Candidate Architecture**。

**执行顺序（状态机，冻结）**：

```text
DG-5 收口 ✅ → 治理体系稳定 ✅ → C-01 PAUSED ✅
      → preprocessing 独立收口（下一步）
      → 生产级真实输出 → 事实基线
      → 重开 C-01 / BIND-3（按 82 §5.3.1 的 12 项逐条取证）
      → 再裁决 Manifest Schema / Path B / Adapter / convergence point
```

**DG-5 本轮结果（逐项，非笼统「completed」）**：

| ID | 结果 |
|---|---|
| **A-04** | **CLOSED / RESOLVED** — `80 §4` Gate B2-B2 行补入 scope 声明；`82 §4-C4` 同步 RESOLVED |
| **A-05** | **CLOSED / RESOLVED** — `69` 三个 2026-09-11 带日期 Gate 块各加 supersession banner → `82 §3`；正文保留原文 |
| **A-06** | **CLOSED / RESOLVED** — `61` 头行 `IN PROGRESS` → `HISTORICAL`，指向 `PHASE_I3_CLOSURE.md` |
| **A-08** | **CLOSED / RESOLVED** — `Status.md` 历史节加 retraction banner；现行权威 = `81 §6.2` / `80 §6.6` |
| **A-09** | **CLOSED / RESOLVED** — `Status.md` 顶层 Status 改为指针 → `82 §3`，不再自述 |
| **D-02** | **CLOSED** — 4×Closure **KEEP → L2**；`gate_b2a_three_task_report` **KEEP → L4**（本已 active）。零删除零归档 |
| **D-03** | **CLOSED** — 三份全部 **KEEP → L4**，零提升：`63` 3 处自封 `Frozen Constraint` 改为「L4 非 L0 权威，升 L0 须走 L1」；`65` **不采纳**原「建议归 L2」（与 `69` 的 Evidence 定性矛盾，且会重复 `63 §10.9/§10.10` + `81 §5.6`）；`68` 加 `69` 的 Proposal 定性注 |
| **D-04** | **CLOSED** — `74` 六处自立规范全部改写为「report finding + 权威指针」，指向 `75 §三 R4/R5` · `75 §4.4` · `75 §4.5` · `75 §九` · `81 §5.4` · `82 §5.0` · `20 §5.5`；测量正文零改动 |
| **D-05** | **CLOSED** — 控制已就位（`90 §4` + `82 §3.3`，均含「存量不强制回填」），**无需改文档** |

**机器源同步**：`i5g_emit_audit.py` CLOSURE 分支 `L2-proposed`/`pending` → `L2`/`active`；
A-04/05/06/08/09、C-01、D-01～D-05 的 status/summary 全部回写；
**修正一处会误导的计数**——OPEN 计数原只匹配 `status == "OPEN"`，C-01 改为
`OPEN_PAUSED` 后会打印「OPEN candidates: 0」，现改为同时匹配两者。

**层计数**：`L0=7 · L0-META=2 · L2=14（原 10，+4 Closure）· L3=2 · L4=15 · L5=4`；
**UNASSIGNED = 0**（scan_report 明确写 `(none)`）。

**本轮未做**：未改 L0 00–50 · 未改 L0 文件名 · 未改 90/91 治理原则 ·
**未改写 82 的 BIND-1/2 裁决** · 未冻结 Manifest Schema · 未实现 Adapter ·
未改 preprocessing · 未因 C-01 新建治理文档 · 未做架构设计。

**下一步**：preprocessing 独立收口。**不因 DG-5 完成而推进 C-01。**

## 0.0a C-01 / BIND-1/2/3 裁决（2026-09-13，权威落点 `82 §5`）

**一阶问题重定性**：C-01 **不是**「line_refs 放 annotation 还是 manifest」的二选一。
真正的一阶问题是**谁拥有 binding claim · 谁验证它 · 两条路径如何携带**。

**分层原则（冻结，`82 §5.0`）**：
`Annotation = semantic structure` · `Binding = source-reference claim` ·
`Identity Join = deterministic relation`。**不预先决定载体位置。**

| BIND | 状态 | 要点 |
|---|---|---|
| **BIND-1** Identity Join | **PASS — ACCEPTED / FROZEN** | 确定性可验证 join；禁 fuzzy / 相似度 / 重跑 Resolver |
| **BIND-2** Native Carrier | **PASS — ACCEPTED / FROZEN** | `line_refs` 作为 Annotation **输入**禁止、作为 Resolver **输出**合法。九项证据 + **802 passed**。`gate/service.py` 历史残留不构成反证 |
| **BIND-3** External Carrier | 方向 ACCEPTED / 契约 **UNPROVEN** | Manifest role declarations = **External Claims**（非 Semantic Authority），须过 V3 contract validation。UNPROVEN 因 manifest schema 未冻结 |

**收敛结论（`82 §5.2.1`，本轮核心收益）**：
**Native Path 不需要 preprocessing 提供 `line_refs`**；preprocessing 的 Manifest
**不需要**为兼容 Native 而把 `line_refs` 塞进 Annotation。C-01 从「四方概念冲突」
收敛为**单一工程契约问题**。

**⚠️ BIND-2 PASS ≠ Adapter 可开工。** 开工前置仍为 `81 §5.4` 三项。

**本轮未做**：未新建文档 · 未改 L0 · 未改 67/81 正文 · 未冻结 manifest-only ·
未发布 67 Errata · 未实现 Adapter。

**下一步**：~~继续 DG-5 剩余项~~ → **已完成，见 `§0.0b`**（2026-09-13）。
C-01 已改判 **OPEN / PAUSED**（`82 §5.3.1`）。**不因 BIND-2 PASS 启动 Adapter，
也不因 DG-5 完成而推进 C-01。**

## 0.0 当前结论（2026-09-13 CA-001 CLOSED + 91 号词汇宪法 + DG 阶段）

- **✅ CA-001 → CLOSED（Owner 裁决 (b)，2026-09-13）。**
  `40 §5` 的测量语义规则**保留，不回滚、不改 L0 内容**；正式认定 **CHANGE-2
  Normative Addition**；补建 Change Record **`90 §11 CR-001`**，Review
  **ACCEPTED / EFFECTIVE**。四道门不需要。procedural gap（先改 L0 后补手续）
  **已 cure**。
  - **不新建文件**——CR 落在 `90 §11`（避免「为治理文档又建治理文档」）。
  - **关键区分**：Change Record 批准前「**文本已存在 ≠ CHANGE-2 已完成生效**」；
    CR-001 Accepted 起该条才具完整 L0 效力。provenance 链闭合：
    `40 §5 新增 → CA-001 → CR-001 → Review → Accepted`。
  - **不为流程洁癖把正确规则撤掉再重加一遍。**
- **当前阶段正式命名 = `Documentation Governance Stabilization`（DG）。**
  **不叫** `Gate E` / `Step X` / `Phase Y`——Gate 是验证门槛、Step 是执行顺序、
  Phase 是生命周期，三者都不是「治理工作包」的正确量词（`91 §6`）。
  - **DG-1** Document Census — 进行中（`docs_audit/document_census.json`）
  - **DG-2** 出生证明回填 — 未开始（当前 **3/44**）
  - **DG-3** 术语冻结 — 基础已立（`91 §1–§3`）
  - **DG-4** 状态统一 — 未开始
  - **DG-5** 冲突清零 — 未开始（含 **CA-001**）
- **`91 号` = 项目词汇宪法（L0-META，与 90 同级互补）。**
  `90` 回答「谁说了算」，`91` 回答「这些词是什么意思」。**都不含业务语义。**
  - **实测发现 `Phase` 有 16 种形态、三套编号体系并存**：罗马 `I-2C`/`I-3`/`I-4`/`I-5`
    + 阿拉伯 `1`/`2`/`3`/`4`/`9` + 单字母 `R`/`B`。
  - **`Phase B` / `Step B` / `Path B` / `Gate B` 四个共存**——同一字母 B 在四个
    维度各指一件事。历史保留；**新文档禁止再用单字母命名 Phase/Step**。
  - **两套 Phase 体系须区分**：项目生命周期（`Phase I-n`，规范形态）vs Evidence
    Promotion 内部子阶段（`Phase 1` 44 处 / `Phase 2` 25 处，**建议新文档改称
    `EP-Stage n`**，待裁决）。
  - **`Path` 永久冻结为两条**：`Path A` = Native（search/resolve）；`Path B` =
    Adapter/Manifest（verify only）。
  - **状态词冻结集**（`91 §3.1`）：OPEN / PENDING / CONDITIONAL PASS / CLOSED
    （须带范围限定）/ NOT STARTED / DEFERRED / SUPERSEDED / RETRACTED / ACTIVE /
    HISTORICAL。**禁用** COMPLETE（现存量 6 份）/ DONE / FINISHED / NEXT /
    REVIEWED——**历史保留，新文档禁用**。
  - **`Contract` 一词有使用门槛**：只有满足 `90 §2 R7` 引用闭包的约束才能称
    Contract；L4 实验约定只能叫 `Experiment Convention`。
  - **新文档出生证明**（`91 §5`）：在 `90 §4` Status Header 基础上扩展
    `Purpose` / `Derives From`（R7 闭包的可机检落点）/ `May Change` /
    `Must Not Change`。**存量不强制回填。**
- **DG-1 Census 首轮结果**（候选生成器，非裁决器）：
  - 出生证明 **3/44**
  - P1 越权候选 **13 份**（L3/L4 使用规则语言但全文不引 L0）
  - P2 隐含修改 L0 **1 份**（`69:48`）
  - P3 禁用状态词 **11 份**
  - P4 重复阶段名 **47 组**
  - **须注意误报**：`Gate X`（来自 `82 §3.3` 模板文本）、`91` 自身的禁用词表
    等。census 是**候选**，须人工核。
- **检测器两处修正**：(1) `Gate Policy`/`Gate State`/`Gate Report` 曾被截成
  `Gate P`/`Gate S`/`Gate R` 幻影，已加 `(?![a-z])`；(2) 禁用词表不再自我标记
  （加 BAN_CONTEXT 排除「禁用/禁止」语境）。
- **CA-001 仍 OPEN，未裁决。** `40 §5` 被 `0dd954d` 新增 CHANGE-2 强制规则而无
  Change Record。选项 (a) 追认 / (b) 撤回重走 L1 / (c) 挂起。见 `90 §11`。
- **本轮未改任何 L0 内容；未裁决 CA-001 / D-01 / C-01 / D-02。**

- **🔴 CA-001 — L0 完整性问题，当前最高优先级。**
  `40_Development_Rules.md §5` 在 `0dd954d`（09-13 14:43）被新增一条**强制**规则
  （「测量语义必须复刻真实 pipeline…禁止用近似文本代替…度量脚本必须能指出它复刻
  哪一段 pipeline，并有测试锁死该复刻语义」），**无 Change Record**。
  - **分类 CHANGE-2 Normative Addition**——新增了「指出复刻哪一段」+「测试锁死」
    两项此前不存在的可验证要求，**不是** CHANGE-1 Clarification。
  - **时序缓解因素，非豁免**：发生在 90 生效前，当时 CHANGE 分类未建立，但
    `82 §2` 与「先冻结 Spec 再改代码」已存在。
  - **内容可辩护**（源自 BUG-V3-044 教训），**但缺 Change Record 是事实**。
  - **可选处置待裁决**：(a) 追认 / (b) 撤回重走 L1 / (c) 挂起。见 `90 §11`。
  - **审计范围**：`0dd954d` 后触及 L0 的提交**仅 40 一处**。更早的 L0 修改自带
    `errata` 标记，属 90 前既有惯例。
- **P0 三项已裁决（用户 2026-09-13）**：
  - **A-07 → DECIDED：语义A 成立，Gate C CLOSED 不动摇。**
    `72 §3` 157 = invalid/suspicious targets；`73:215-221` NOT proven **全是语义
    正确性**；C-2 实际 = `test_c2_evidence_authority_e2e.py`（IR bypass + Lifecycle
    + 157 fail-closed）——**证明管线不变量，非每个 binding 的语义正确性**。
    已在 `73` 文首写 **C-2 Evidence Scope Clarification**，**正文未改**。
  - **B-01 → DECIDED：名称漂移非概念缺失。** `75` 实际标题是「Evidence
    **Promotion** Contract」。已在 `75` 加 **Terminology** 节声明简称等同；
    **不全文替换**；新文档用全称。
  - **B-02 → DECIDED：不升 L0。我先前判「零定义」是错的**——`Validated Evidence`
    **有 L2 定义**（`75:42` 状态机 `state: trusted`、`75:194` `§4.5`）。它是证据
    生命周期**状态**（系统机制），非基础原则。`90 R9` 已冻结 `≠ verified_correct`。
- **90 号新增四条规则**：
  - **R7 引用闭包**：L2/L3/L4 的规范性结论必须存在向上闭包。
  - **R8 废止传播**：`supersede` 后不得作为引用来源；扫描器跳过；`docs_audit` 标
    `deprecated`。
  - **R9 Evidence 术语不可互换（永久）**：`Validated Evidence ≠ verified_correct`；
    `Verified Evidence` 永久禁用。
  - **R10 L2 不得创造新名词**：`Binding Carrier` / `External Claim` /
    `Semantic Authority` 三项 ⚠️ 未定义，进入代码前须走 Terminology Proposal。
- **检测器改进（R6 定义形态扩展）**：识别表格 / 状态机 `state:` / 「唯一可进入」。
  改进后 `Validated Evidence` defs 0→6、`ResolvedSpan` 0→3、`annotation_payload`
  0→1、`FORBIDDEN_FIELDS` 0→1——**所有 HIGH 漂移风险清零**，证实全是检测器局限。
- **Closure 归层改为 `L2-proposed` + `classification_status: pending`**——
  L2 本身也是治理事实，未经裁决不能成为事实。
- **本轮未裁决**：CA-001 / D-01 / C-01 / D-02。**未改任何 L0 内容。**

- **`90 号` = 治理元规范（L0-META，最高）**。**不是业务 Spec**，不含任何
  annotation / resolver / gate / admission 业务语义。它规定「规范如何被管理」。
  - **L0–L5 等级**：L0 Frozen Spec（`00`–`50`）/ **L1 Contract Change Record
    （修改 L0 的唯一入口，当前为空）** / L2 Decision Record / L3 Gate Report /
    L4 Experiment Report / L5 Status。旧 A–E 五层的 C 已拆为 L3+L4。
  - **最高规则**：**L3/L4/L5 永远不得改变 L0/L1；L2 只能解释与裁决，不得修改 L0。**
  - 核心规则 R1–R6：L0 只能经 L1 改 / L2 不得产生新架构事实 / L3 只能证明状态且
    必须引用 82 §3 / L4 不得把实验结论升为事实 / L5 不得与 82 §3 矛盾 / 术语必须
    有冻结定义。
  - CHANGE-0…5 分类 + Status Header 规范 + 扫描规则 Rule 1–4 + 强制读取顺序
    （90 → 82 §3/§10 → L0 → L1/L2 → L3 → L4 → L5）。**禁止「grep 到什么读什么」。**
- **`82 号` 降级为治理执行记录（L2）**：§1/§2/§9/§11 被 90 吸收；**继续持有
  §3 Gate State Authority（唯一）** + §5 BIND-1/2/3 + §10 Phase Baseline。
- **`84 号` = Conflict Ledger（L3 台账）**，取代 82 §4。**15 项 OPEN / 4 项已处置 /
  3 项误报**。每条带 `file:line` 证据；**只登记，不裁决**。
- **`docs_audit/` 机器可读产物已生成**（`i5g_emit_audit.py`，只读扫描）：
  - `authority_matrix.yaml` — 全仓归层：**L0=7 / L0-META=1 / L2=11 / L3=3 /
    L4=16 / L5=4 / UNASSIGNED=1**
  - `contradiction_candidates.json` — 84 台账的机器形式 + 196 条 Gate 状态行
  - `frozen_terms.json` — 14 个关键术语的定义/使用分布
  - `scan_report.md` — 人读汇总
- **本轮新增核验发现**（并入 84）：
  - **A-07 🔴**：`73:213` 声明 157 targets `UNRESOLVED / REVIEW REQUIRED`
    （`NOT proven: All 157 are correct bindings`），而 Gate C 以 C-2「157 E2E」关闭。
    **A-01 同类**——C-1/C-2 完成于 09-13，`73` 作于 09-11，疑虑或已解决但
    **无文件声明 73 已关闭**。可能动摇 Gate C CLOSED 的证据基础。
  - **B-01 🔴**：**`Evidence Contract` 零定义却被 ≥4 份文档用来立规**（13 处使用，
    grep「Evidence Contract + (定义|指的是|即|denotes)」零命中）。违反 90 §2 R6。
    实际指向 `75 号`，但从未被显式等同。
  - **B-02 🔴**：三近义词仅一个有宪法地位——`Validated Evidence`（10 处，**全在
    L3 `74`**，L0/L2 零定义）/ `Verified Evidence`（全仓零使用）/ `verified_correct`
    （L0 `20 §8.3`）。用户 H-A 长期风险。
  - **A-06 🟠**：`61:4` `Status: IN PROGRESS`，而 `Closure/PHASE_I3_CLOSURE.md:4-5`
    已 CLOSED / Gate PASS——Phase I-3 关闭后 61 从未回写。
  - **A-08 🟠**：`Status.md:2309`（已撤回的 Grammar 契约「必须 Resolver 产出」，
    **未标记**）vs `Status.md:2423`（不变量版）——对立极性同主题。
- **核验中的两处误报已记录（84 E 类）**，防重复排查：
  - **E-01**：`81:208-211` 管线图被判 MIXED——**误报**，是两条**显式标注**的分支
    （`Native Resolver（search/resolve）` / `Path B Adapter（verify only）`）。
  - **E-02**：`10:777` 引用 `20 §12.1` 判悬空——**误报**，该行是 **changelog**，
    记录的是「从 20 §12.1 **改为** 20 §8.5」的旧值。
- **本轮明确不做**：**L0 六册零字节改动**；不发 67；不冻结 manifest-only；
  不写 Errata Decision；不实现 Adapter；不逐句改写历史报告；不删除 71 号任一份；
  **不对 84 台账任何条目作裁决**。

- **82 号 = Governance Root（ACTIVE）**：五层权威矩阵 / CHANGE-0…5 分类 /
  **Gate State Authority = 82 §3（唯一）** / 聚合规则冻结 / Phase I-5 CURRENT
  BASELINE（82 §10）/ Status Header 规范（82 §9）/ Agent 强制读取顺序（82 §11）。
- **83 号 = I-5-G 全仓审计（C 层）**：机械扫描 `backend/scripts/i5g_normative_scan.py`
  产出 6 项发现，**全部只登记、未处置**。
  - **G2 🔴 最重：71 号同号双份且内容不同。**
    `Docs/V3_SPEC/71_…`（6914 B，Sep 12 21:33，「裁决记录」）vs
    `backend/Docs/V3_SPEC/71_…`（7783 B，23:05，「(CORRECTED)」），`diff` 判 DIFFERENT。
    **旧的那份在 A 层目录里**，路径直觉会把它当更权威——实际是被 CORRECTED 的版本。
    比 C1 更糟：C1 是同一文档状态被两处误读，这是两个文件抢同一编号且无废止声明。
  - **G1 🔴 5 份文档在 V3_SPEC 树内但未分类**（837 行）：4× `Closure/PHASE_I*_CLOSURE.md`
    （正式关闭记录，建议 **B**）+ `gate_b2a_three_task_report.md`（建议 **C**）。
    `PHASE_I3_CLOSURE.md:5` 直接写 `Gate: PASS` 却不在 82 §3 表内，无法对账。
  - **G3 🟠 分层错误 3 份**：`63` 自述 `Status: Frozen Constraint`（**A 或 B 待裁决**，
    升 A 须 Change Record）；`65` 是 scope freeze 契约（`65:95-106` 十二条禁令，
    建议 **B**）；`68` 保持 C 但须注明 69 的定性。
  - **G4 🟠 C 层自立规范**：`74` 对 V3 立规（`224`/`226`/`283`/`385`/`395-396`/`418`）。
    对照 `74:94`「这个结果只能证明」是**正确用法**——同文档两种用法并存，
    说明缺的是分类约束而非写作能力。
  - **G5 🟠 Gate 状态行集中面**：`Status.md` **45 行** / `69` **42 行** 是聚合错误
    最大温床（C3 即此类产物）。新增行须用 82 §3.3 模板。
  - **G6 🟡** `restart-prompt` 密度 36.6% 全仓最高——不压缩，改由 82 §11 读取顺序约束。
- **扫描关键限定**：标记词命中 ≠ 违规。A 层**应该**高密度；「只能证明 / 本实验采用」
  是报告的正确写法。要找的是**在错误层级自立规则**。
- **I-5-G 完成条件对账（82 §10）**：10 项中 ✅3 / 🟠6 / 🔴1（G2 阻塞第 10 项）。
  **结论：I-5-G 未完成，不得进入 I-5-BIND。**
- **本轮明确不做**：不改 20；不发 67；不冻结 manifest-only；不写 Errata Decision；
  不实现 Adapter；不逐句改写历史报告（Reconcile, don't rewrite）；**不删除 71 号任一份**。

- **权威层级已建立（82 号，ACTIVE）**——本文档是外部对抗性审查后的产物。审查发现
  Frozen Spec / Gate 裁决 / Phase 报告 / Status 之间出现多个层级的规范性声明且无
  废止关系，故**暂缓任何对 20 的修改**，也**暂缓把 manifest-only 正式冻结**。
  - **五层权威矩阵**（82 §1）：A Frozen Spec（Normative）/ B Decision Record（仅其
    裁决范围）/ C Phase Report（Informative，**禁用规范性语言**）/ D Status
    （不得与 82 §3 矛盾）/ E Experimental（**不得单独支撑 PASS**）。
  - **规范变更分类 CHANGE-0…5**（82 §2）：四道门**仅适用** CHANGE-4 放宽 /
    CHANGE-5 删除。**新增强制 invariant = CHANGE-2**，需 Change Record 但不走四道门。
    拿不准时往高里归。
  - **Gate State Authority = 82 §3**（唯一权威）。任何 Gate 状态变更须同 commit 更新。
  - **聚合规则冻结**：存在 CONDITIONAL 或 DEFERRED 子项时，父 Gate **不得**记为
    PASS/CLOSED。「大部分子项 PASS → 可发布 Contract Change」是**禁止的逻辑偷换**。
- **Gate B 整体 = NOT CLOSED**（依据 82 §3）：B1 CONDITIONAL PASS（option Role
  Validity 51.8% / answer 49.1%；Structural 未评估）；B2-B3-C / B2-B4-C DEFERRED。
  **因此 67 号 Errata（CHANGE-5，删 `FORBIDDEN_FIELDS` 的 `line_refs`，`20:117`）
  不得发布。**
- **已核验冲突 7 条（82 §4，含 file:line）**，P0 四条：
  - **C1** `74:5/363/537` 仍写 Gate C BLOCKED，`80:439` 已 CLOSED，**无废止记录** →
    82 §3.1 即废止记录（C-1=`75`，C-2=`76`/`77` 确已完成）。
  - **C2** `69:306` 无日期路线图仍写「Errata Decision（Gate A-D 全部通过后）」→
    已加 supersede 指针，正文保留为历史。
  - **C3** `81:11` 曾称「Gate B 系列 CLOSED」，**过度陈述 80 号**（80:421 自己写
    B1 CONDITIONAL）→ **本轮已修正**。
  - **C7** 无 Authority Matrix / 无变更分类 → 82 §1/§2 即为建立。
  - P1 三条：C4（`80:426` B2-B2 CLOSED vs `80:448` Unknown 125 未清，**歧义非错误**，
    待 triage 补 scope 声明）/ C5（`69:656`/`69:756` 历史快照仍写 B2-B BLOCKED/WAIT；
    全仓**无**「NEXT」措辞）/ C6（E1 属 **CHANGE-2 Normative Addition**，非澄清）。
> ⚠️ **以下 Binding Carrier 段落已过时（2026-09-13）**——它记录的是 BIND-1/2/3
> **登记未裁决**时的历史状态。**现行权威见本文 `§0.0a` 与 `82 §5`**：
> BIND-1 = **PASS/FROZEN** · BIND-2 = **PASS/FROZEN** · BIND-3 = **UNPROVEN**
> （方向 ACCEPTED）。正文保留为历史，**不得按此段判断当前状态**。

- **Binding Carrier Decision = PENDING**（82 §5）——三个未决问题**登记未裁决**：
  - **BIND-1** Annotation semantic unit ↔ Manifest binding unit 是否存在**确定性
    identity join**？若依赖顺序/题号/模糊匹配 → 重新引入 Resolver-like 问题，
    违反 81 §5.6 与「只允许机械投影」。**本轮最值得新增的审查点。**
  - **BIND-2** Native Path 能否完全脱离 `annotation.line_refs`？
  - **BIND-3** Manifest 的 role declaration 是 **External Claim** 还是 V3
    **Semantic Authority**？（初步倾向 External Claim Producer，未裁决）
  - 候选状态：manifest-only = 🟡 PROVISIONAL ARCHITECTURAL PREFERENCE（须 BIND-1/2/3
    全 PASS 才可冻结）；annotation 内 = 🔴 不得继续推进；两者共存 = 🔴 REJECT。
  - **关键澄清**：`line_refs` 在 annotation 中**不自动违反** Source-as-Fact-Source。
    违规的是「LLM line_refs → 直接相信 → ResolvedSpan」；「→ Resolver 验证 →」不违规。
    **「更干净」≠「已证明正确」。**
- **Gate D: CONTRACT CLOSED / IMPLEMENTATION NOT STARTED**（权威：`81 号`）。
  - 状态措辞：Gate D 的要求是**契约裁决**，不是实现验收，故不用裸 `CLOSED`。
    `CONTRACT CLOSED` = 边界契约已冻结；`IMPLEMENTATION NOT STARTED` =
    `backend/app` 中无 Adapter 代码，且开工被 81 §5.4 三项前置阻塞。
  - 出口标准（用户裁决）：**本轮只冻结契约，不要求实现**。
  - 69 号五条禁令**全部维持**，未放宽任何一条。
  - **Bypasses 修正**：66 §7 原文「Bypasses: Annotation, Resolver」是**表述错误**。
    `IRBuilder.build()` 必需 `annotation_payload`，其 `semantic_units[]` /
    `unit_id` / `unit_type` / `content{}` 驱动全部语义结构，且 ResolvedSpan 的
    span_id 约定（`sp-{unit_id}.{role}`）由 annotation 反推——绕过 Annotation
    则连 span_id 都构造不出来。正确表述：**Bypasses: Resolver only**。
    「绕过 Resolver」= 绕过其 search/resolve **机制**（以验证替代搜索），
    **不是**绕过 Source Binding 本身。下游 IRBuilder / Compiler / Gate 两条路径
    完全一致。
  - **annotation 归属裁决**：preprocessing 产出 **V3 形制 annotation_payload**
    + line_refs manifest；V3 Adapter 只做机械 line_ref 展开与 hash 校验，不碰语义。
    **契约方向不可颠倒**：V3 首先冻结它**自己要消费**的 Annotation / Manifest
    契约，preprocessing 再**实现**它。不是 preprocessing 自行设计 annotation
    再由 V3 适配（74 号：preprocessing 必须满足 V3 Evidence Contract）。
  - **核心不变量（高于任一单项禁令）**：**Adapter 只允许机械投影，不允许提高
    信息量**。输出的信息量 ≤ 输入（manifest ∪ SealedSource 确定切片）。六条禁令
    都是它的具体化。判定原则：**指不出来源的输出 = 违规**。
  - Adapter 职责白名单（5 项）/ 禁令黑名单（6 条）/ V3 侧三项前置已冻结。
  - **显式不主张**：Adapter 未实现；I-5-1 的 14 项实验**不可复现**（无脚本、无测试、
    git 历史零提交），降级为方向性参考，**且不建议重做**；manifest schema 未冻结；
    Adapter 路径在前置满足前覆盖率接近零。
- **Grammar 输入来源契约已修订（81 号 §6.2 不变量版）**：
  - 原措辞「必须 Resolver 产出」**两处错误**：(1) `ResolvedSpan` 无生产者字段，
    「Resolver 产出」在数据上不可验证；(2) 与 Adapter 路径冲突，会非法排除整条
    Manifest Path。根因是写了**机制**而非**不变量**。
  - 正确不变量：`answer_text` 必须是 `ResolvedRun` 中 `role=answer` 的
    `ResolvedSpan` 文本切片，且 `granularity` 为字符切片、
    `resolution_status ∈ {exact, normalized}`、`text_hash` 与 SealedSource 一致。
    **生产者可以是 Resolver 或 Adapter**，本模块不区分。
  - 明确不给 `ResolvedSpan` 加生产者字段（YAGNI；若 Replay 需要再走 Errata）。
- **Errata: UNBLOCKED**（Gate D 已过）。待议两项：Grammar 输入来源契约写入
  20 §8.4 正文；`ResolvedSpan` 生产者字段。

- **BUG-V3-044: Resolved + 对抗性审查通过**（80 号 §6 实现 / §7 审查）。
  - 裁决：Q-A 白名单为主；Evidence Contract **不扩大**；Evidence Promotion
    Phase 1 **不回退**；Gate D 延后至 Grammar Contract 冻结（现已冻结，阻塞解除）。
  - 题号前缀：**剥离后白名单**（20 §5.5 切片规则不动，`1. A` 仍 approve）。
  - 语料实测扩展：`【答案】D` / `（3分）D` / `D。` 三种**全串锚定**形态。
  - 全量 pytest **802 passed**；探针 C1/C2 由 auto_approve → pending_review。
- **对抗性审查发现（80 号 §7）**：
  - **真实缺陷已修**：混合括号 `（A)` 曾被接受（正则字符类 `[）)]` 允许开闭不配对）。
    已拆为全角/半角配对分支。修复过程中自引入的 `score_fw` 命名组截断 bug 同轮捕获。
  - **方法学缺陷已修**：此前覆盖率数字基于「行内剩余文本」而非 E 的 char-span 切片。
    修正后 8166 条目：single_choice 552 保持 / 261 回归（205 垃圾 + 55 解析标记
    + **1 离群点 `A;`**，不扩展白名单）；multiple_choice 546 / 320。
- **架构分层（当前完整视图）**：
  ```text
  Source Binding Boundary        ✅ Gate B / B2-B
  Evidence Authority Boundary    ✅ Gate C Phase 1
  Semantic Answer Contract       ✅ BUG-V3-044（含对抗性审查）
  Admission / Knowledge Layer
  ```
- **Gate B2-B5: CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED**
  （权威：`backend/Docs/V3_SPEC/80_B2B5_CLOSURE.md` v1.2.0）。
- **Gate B 全系列关闭或显式延期**：B1 CONDITIONAL PASS / B2-A PASS /
  B2-B1～B2-B5 CLOSED / B2-B3-C 与 B2-B4-C DEFERRED（Domain Contract）。
- **Gate B2-A: PASS / TEST-EVIDENCED（stem-only, three-task audit）**。
  - Task A: 20 Legacy-only cases 全部为 pattern coverage gap，非验证错误。
  - Task B: 150 抽样中 96% 标准题号格式，验证结果可信。
  - Task C: Legacy 47.1% vs Path B 96.8%，+49.7pp，2.1x coverage。
- **Gate C CLOSED（Phase 1 Evidence Authority Boundary Closure）**。
- **Evidence Validity ≠ Semantic Correctness**；**Legal address ≠ legal evidence**。

- **A–G / H Phase 1–8 / Phase 9 / Errata 维持 FINAL CLOSED**。
- **Phase I-3 CLOSED**：Source Evidence Preservation Layer。
- **Phase I-4 CLOSED**：Valid Negative Result——layout evidence 消歧率 0%。
- **Phase I-5 进行中**：I-5-0 → I-5-1 → 盲测 → 68/69 号 → 对抗性审查 →
  P0 Closure Pack → Step 3 裁决 → Gate A → Gate B/C → B2-B5 → BUG-V3-044 →
  **BUG-V3-044 对抗性审查（本轮）**。
- **Gate A（Identity Closure）**：**PASS / TEST-EVIDENCED**。
  - 三层 Identity 模型：Semantic Identity / Source Binding Claim / Resolved Evidence。
  - 核心结论：line_refs 属于 Source Binding Claim，不属于 Semantic Identity。
  - `_annotation_identity_projection` 剔除 `{confidence, line_refs}`；
    `_confidence_only_projection` 仅剔除 `{confidence}`（供 resolver_input_hash）。
- **状态基线（2026-09-13 对账后）**：
  - Architecture Design: **PASS WITH RESERVATIONS**
  - Core Safety Model: **PASS**
  - Local Invariants: **PASS / TEST-EVIDENCED**（802/802）
  - Cross-Boundary Invariants: **PASS / TEST-EVIDENCED**
  - Admission Atomicity: **PASS**；Admission Concurrency: **PASS — 10/10**
  - Test Isolation: **PASS / TEST-EVIDENCED**
  - Resolver Algorithm Safety: **PASS**；Resolver Real-World Coverage: **FAIL — 16.7%**
    （Legacy 搜索口径；Path B 验证口径下 stem 96.8%）
  - Path B → IR/Compiler: **PROVEN — 21/21**；→ Gate/Admission: **NOT YET PROVEN**
  - 67 Contract Change: **CONDITIONALLY ACCEPTED**（Gate A/B/C 通过；Errata BLOCKED BY Gate D）
  - OQ-1: **CLOSED**；OQ-2/OQ-3: **OPEN**
  - Full Production Pipeline: **NOT YET CLOSED**
- **Gate B1 修正后结果（2026-09-11，79 cases / 10343 role targets）**：
  - Range Validity **PASS**（100%）；Content Validity **PASS WITH RESERVATIONS**（79.0%）
  - Role Validity: stem **97.3%** / explanation **96.7%** / option **51.8%** / answer **49.1%**
  - **Gate B1 = CONDITIONAL PASS / Corpus Substantially Valid**
  - **禁止继续放宽 validator 提升数字**——那是 metric optimization
- **Contract Adjudication（2026-09-11）**：Q1=A region / Q2=B per-question evidence /
  Q3=B single span / Q4=B cell-row；**统一原则：Source Region 与 Question Evidence 必须分层**。
- **Gate B2-B 系列结果（2026-09-11/12 完成，09-13 回写）**：
  - B2-B1 option region：非 HTML 结构提取 **99.6%**（1065/1069），对抗抽样 98.0%
  - B2-B2 MC answer：extraction **99.8%**（1176/1178）；Unknown 125 **仍未清**
  - B2-B3 fill-in：原 65% 因分母污染**正式失效**；真填空 34/34 deterministic PASS
  - B2-B4 HTML：507/507 Direct targets deterministic PASS，零 HTML 解析、零 fallback
  - B2-B5 主观/子题/材料：CLOSED（706 targets / 429 representable / 157 pending_review）
  - 四条冻结原则：Address≠Authority / Claim=Promotion / Validated-only / No-inference
- **红线（不变）**：HTTP retry ≠ LLM retry ≠ fallback；先冻结 Spec 再改代码；
  Schema Source of Truth = 20_Document_Pipeline.md；Resolver 不猜；
  实验结果 ≠ 实施授权；提议修改 ≠ 违反 Frozen Spec。
- **下一步（Documentation Governance Stabilization，按序；DG 全绿前不得进入
  Binding Authority Decision，更不得实现 Adapter）**：
  1. **裁决 D-01**（71 号双份不同内容）——阻塞 `90 §10` 第 10 项。建议 root 版
     判 stale + supersede 指针 → backend CORRECTED 版；**不删除任一份**。
  2. **裁决 `91 §1.2` 的 `EP-Stage` 改称**（Evidence Promotion 内部的 `Phase 1`
     44 处 / `Phase 2` 25 处是否改称，避免与项目生命周期 `Phase I-n` 混淆）。
  3. **裁决 C-01**（`line_refs`，须走 BIND-1/2/3）→ **D-02 / D-03**（归层）。
  4. **DG-1 收尾**：人工核 `docs_audit/document_census.json` 四类候选，排除误报
     （如 `Gate X` 来自 `82 §3.3` 模板）。**扫描器是候选生成器，不是裁决器**
     （`91 §6.1`）。
  5. **DG-2 出生证明回填**（`91 §5`，当前 3/44）。
  6. **DG-4 状态统一**（`91 §3.1` 冻结集）→ **DG-5 冲突清零**（`84` OPEN 归零）。
  7. **重跑 `i5g_emit_audit.py`** 复核；`90 §10` 全绿 → Current Baseline declared。
  8. **I-5-BIND — Binding Authority Decision**（BIND-1 优先；`82 §5`）。
  9. 之后才依次：V3 Annotation Contract → Manifest Contract → Change Records
     （E1=CHANGE-2；67=CHANGE-4/5 REJECT）→ Errata Decision → 最小 Adapter。
  - **L0 修改强制登记于 `90 §11`，否则违规。**（CR-001 是首例，已 ACCEPTED）
  - **文档创建门槛（`91 §5.1`，DG 根因）**：新建任何文档前必须答四项——
    为什么现有文档承载不了 / 出生证明齐备 / 权威归属明确 / `May Change` +
    `Must Not Change`（至少含 L0）。**DG 期间冻结新建治理文档。**
  - **每次 Gate 状态变更必须同 commit 更新 `82 §3`。**
  - **Agent 读取顺序强制（90 §7）**：90 → 91 → 82 §3/§10 → L0 00–50 → L1/L2 →
    L3 → L4 → L5。**禁止「grep 到什么读什么」。**
  - **权威链**：`90`（谁说了算）+ `91`（词是什么意思）→ `82 §3`（Gate State
    Authority，唯一）→ `84`（Conflict Ledger）→ `docs_audit/`（机器可读）。
- 重启后第一任务：读本文件 → Status.md 尾 → log.md 尾 → bugs.md →
  按上述 Step 顺序执行。
- **对账教训（2026-09-13）**：B2-B1～B2-B5 的实验结果曾只写进 69 号与 docs 71–74，
  长期未回写 log.md / Status.md / restart-prompt，导致重启时误判「B2-B 未开始」。
  **实验关闭后必须同步回写四者**，否则状态文件会撒谎。
- **契约扩展教训（2026-09-13）**：白名单/校验类契约不能只按推理设计——初版
  AnswerTokenContract 按裁决字面实现后，在真实语料上误伤 62 个合法条目
  （`【答案】D` 等）。**收紧前必须在真实语料上量化覆盖率影响**，
  再据数据决定是否扩展允许形态。
- **测量语义教训（2026-09-13 对抗性审查）**：覆盖率测量必须复刻**真实 pipeline 的
  数据语义**（E 的 char-span 切片到下一 qn 前），而非「行内剩余文本」这类近似。
  错误语义会同时高估回归与低估收益。**测量脚本本身也要接受对抗性审查。**

## 1. 用途

Codex/Claude 重启后先读本文件恢复上下文。本文件只承载稳定信息：项目目标、基线状态、
强制规则、文档地图、恢复流程；最新状态细节以 `Status.md` / `log.md` 为准。
**更新约定（规则二）**：`0.0` 节结论每次更新带当前时间戳，
在对应小节下记录最近更新时刻。

## 2. 项目目标

从 V2 继承业务需求并**全量重写**（V2 需求见 `Docs/00_Requirements/
REQUIREMENTS_AND_SOLUTION.md`）：批量上传教师版 PDF/DOCX → 自动提取题目/配图/答案/
详解/元数据；题库统计分析；AI 生成题（延后）；错题本；个性化练习。V3 目标 = 杜绝
V2 的「LLM→文本→特判→Gate→回填」模式，以 Source 为唯一事实源、stage-scoped 幂等、
Replay 可重建。

## 3. 强制规则（摘要，权威在六册）

- 单主链：不建第二条 pipeline；状态只经唯一入口（decision_status → approve()/reject()）。
- Live 是组合放行：LLM/cloud OCR 须 live mode + `--allow-live` + task + budget 同时成立。
- LE key = `{task_type, stage, contract_domain, input_domain}`（不含 task_id）。
- 预算五账户正交、禁父子树；Recovery ≠ Retry；Worker 崩溃不自动重跑。
- 实现顺序、测试层级、DoD、评审红线：`40`；资产/Golden：`50`。
- **H 段**：LLMExecutor 唯一入口、Domain 不依赖 Gateway、Attempt 不可恢复续跑、Runtime/Business
  Identity 隔离（详见 plan 文件）。
