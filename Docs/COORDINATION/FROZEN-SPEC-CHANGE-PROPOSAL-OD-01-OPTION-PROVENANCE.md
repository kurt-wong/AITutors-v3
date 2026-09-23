# FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE

```text
Document ID:           OD-01-PROPOSAL-v4R
Title:                 OD-01 Frozen Spec Change Proposal — Option Provenance / Unified Provenance Model
Document Type:         Decision Record
Status:                PENDING
Authority Level:       L2-proposed
Purpose:               OD-01 option provenance 的 Current→Proposed 条款差异、缺口基线、三路径统一 provenance、可采纳 Frozen Text 与 Finding 映射
Normative:             NO
Derives From:          OD-01 · OD-01-A…J · OD-01R-01…10 · F-OD01-01…08 · F-OD01R-01…10 · F-OD01V3-01…12 · F-OD01V4-01…03 · F-OD01V4R-01…48 · P04 · L0 00/10/20/50（只读）· 90/91 §3.1 · 69 §5
May Change:            本 Proposal 文本；配套 CR-002 Candidate 引用一致性
Must Not Change:       L0 00–50 · L0-META 90/91 · Frozen Contract / P01–P25 · Gate/Admission/Question Core · Production · Preprocessing · Schema · Corpus · Migration
Related Records:       CONTRACT-CHANGE-RECORD-CR-002-OD-01.md · OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md · Docs/REPORTS/OD-01-PROPOSAL-V4-TARGETED-ADVERSARIAL-REVIEW.md（Historical Self Review）· Docs/REPORTS/OD-01V4R-FINAL-REMEDIATION-REPORT.md
Supersedes:            —
Superseded By:         —
Gate State Authority:  NO
Registration Level:    NOT REGISTERED
Current Version:       v4R（唯一 Current）
```

> **Status 字段**仅使用 `90 §4` / `91 §3.1` 冻结枚举值。本文件 `Status: PENDING`。
> **Finding Disposition 列不是 Status 字段**；处置词汇不声称属于 `91 §3.1`。
> Frozen Spec tree = `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`（UNCHANGED）。
> **Authority Level 取值仅限冻结枚举**（`90 §4:375` / `91 §5:167`：L0 | L0-META | L1 | L2 | L2-proposed | L3 | L4 | L5）。不得自创层级。Registration Level 单独描述注册状态。
> 核心方向不变：Artifact-first · Artifact-authoritative · Single provenance authority · No V3 rediscovery（Artifact 路径）· Fail closed。

**审查边界：** Self Review = 内部检查（Historical Self Review 文档）。DSH Review = 外部验证。OD-01-J 证据链只接受 DSH Review。

**Planning Category（非 Status）：** `Future Required Change` · `Future Consideration` — 仅规划分类，不是状态值。

**目录归层：** 本文件位于 `Docs/COORDINATION/`。该目录**不在** `90 §1.2` 目录模型内，属 **未归层**（`90:47`：未归层 = 不得引用为权威）。本文档自称为 Change Proposal / 决策记录草案，**不得**被引用为 L0/L1/L2 权威。

---

## 0. Finding → Fix Mapping — 唯一完整表

> 含 **F-OD01-01…08 · F-OD01R-01…10 · F-OD01V3-01…12 · F-OD01V4-01…03 · F-OD01V4R-01…48**。
> 历史 Finding 不删除、不重编号。Final ID 一问一号、无空号。
> `Problem` 列以 DSH 已提交基线报告的发现标题为准，不重释、不合并不降级。
> 历史空号 `OD-01F-09`/`OD-01F-10` 由连续三轮漏登的 `F-OD01V3-11`/`F-OD01V3-12` 填入（不重编号既有 Final ID）。
> 新问题自 **OD-01F-82** 起。`Finding Disposition` 列 ≠ Status 字段。

| Finding ID | Final ID | Problem（DSH 基准） | Fix Location | Verification Evidence | Finding Disposition |
|------------|----------|---------------------|--------------|----------------------|---------------------|
| F-OD01-01 | OD-01F-01 | Resolved Span 基线不完整 | Proposal §1 缺口基线 | 基线表含现有/缺口/延后/非目标 | REMEDIATED |
| F-OD01-02 | OD-01F-02 | 条款级 diff 不全 | Proposal §6–§7 | CI-1…12 + Appendix | REMEDIATED |
| F-OD01-03 | OD-01F-03 | 禁 rediscovery 与 §5.3 冲突 | CI-3 | CHANGE-5 取代文本 | REMEDIATED |
| F-OD01-04 | OD-01F-04 | provenance 权威链路未定义 | Proposal §4 · CI-5 | 单链路 + conflict signal | REMEDIATED |
| F-OD01-05 | OD-01F-05 | fail-closed 双字段歧义 | Proposal §2.2 · CI-6 | option_evidence_status 唯一 | REMEDIATED |
| F-OD01-06 | OD-01F-06 | image_region 缺口 | CI-12 | other 实例；非顶级 form | REMEDIATED |
| F-OD01-07 | OD-01F-07 | L0 修改路径未走治理 | CR-002 · §9 | Change Proposal Record 流程 | REMEDIATED |
| F-OD01-08 | OD-01F-08 | 引用 sp-*.option.* 错误 | CI-5 | 示例 `sp-Q1-A` | REMEDIATED |
| F-OD01V3-11 | OD-01F-09 | 逐字引用保真度下降：`10 §4` 引文为改写版且置于 fenced 代码块内 | CI-2 Current Rule | 标注 verbatim/summary；补齐「依据 01 v0.3 收敛。」等 | REGISTERED |
| F-OD01V3-12 | OD-01F-10 | 3 个文档被加入 UTF-8 BOM，属未声明的字节级改动 | 历史处置记录 | 本轮写入不经 BOM；字节改动仅限 COORDINATION/REPORTS | REGISTERED |
| F-OD01R-01 | OD-01F-11 | CR-002 不能仅凭自称成为正式 L1 | §9 · CR-002 §0 | 注册条件未满足 + Future registration path | REMEDIATED |
| F-OD01R-02 | OD-01F-12 | 治理 Header 不合规（含自创 L1-proposal） | 全文档 Header | 出生证明字段齐备 | REMEDIATED |
| F-OD01R-03 | OD-01F-13 | CHANGE 分类压低 | §8 | CHANGE-3/4/5 ACKNOWLEDGED | REMEDIATED |
| F-OD01R-04 | OD-01F-14 | 未覆盖多路径（只写 Artifact） | Proposal §4 | Native/Adapter/Artifact | REMEDIATED |
| F-OD01R-05 | OD-01F-15 | diff 影响面不全 | §7 | 含 10 §4 / 20 §6.2 / 50 / README §2 | REMEDIATED |
| F-OD01R-06 | OD-01F-16 | 定位方式一刀切 | Proposal §3 · CI-4 | 分型 locator | REMEDIATED |
| F-OD01R-07 | OD-01F-17 | 两个解析状态字段命名冲突 | Proposal §2.2 | span_resolution 唯一 | REMEDIATED |
| F-OD01R-08 | OD-01F-18 | fail-closed 与 degraded 关系不清 | Proposal §2.2 · §10 | 分层唯一承载；降级非本轮 | REMEDIATED |
| F-OD01R-09 | OD-01F-19 | 缺 Owner Decision / Finding Disposition 记录 | OWNER-DECISIONS | OD-01R / V4R 附录 | REMEDIATED |
| F-OD01R-10 | OD-01F-20 | 引用坐标错误（options_unresolved / sp-M1） | 历史处置 | sp-M1 = 20 §5.5 | REMEDIATED |
| F-OD01V3-01 | OD-01F-21 | 条款级 Proposed Frozen Text 全数消失 | Proposal §6 CI-1…12 | 每条含 Proposed Frozen Text | TEXT-CORRECTED |
| F-OD01V3-02 | OD-01F-22 | v2「完整现状基线」13 行表被删除 | Proposal §1 | 缺口基线表恢复 | TEXT-CORRECTED |
| F-OD01V3-03 | OD-01F-23 | `DONE` 作为状态值大面积使用（违反 91 §3.2） | 全文档 | 禁词扫描空；处置列≠Status | TEXT-CORRECTED |
| F-OD01V3-04 | OD-01F-24 | Governance Gap 混淆候选落位与正式注册 | §9 · CR-002 §0 | 候选≠已注册；条件未满足 | TEXT-CORRECTED |
| F-OD01V3-05 | OD-01F-25 | OD-01R-09「正式 Owner Decision」为 agent 自写且位于未归层目录，权威来源不可核验 | OWNER-DECISIONS · 本文件头 | 未归层声明；不引用为 L0/L1/L2 权威 | TEXT-CORRECTED |
| F-OD01V3-06 | OD-01F-26 | `degraded` 仍无合法层级/值域槽位 | §2.2 · §10 | 字段分层；降级=Future Consideration | REMEDIATED |
| F-OD01V3-07 | OD-01F-27 | 字段命名冲突以「删除该字段」规避，而非按冻结 vocabulary 命名 | Proposal §2.2 | span_resolution 唯一命名保留 | TEXT-CORRECTED |
| F-OD01V3-08 | OD-01F-28 | 新引入 `91 §3.1` 误引（×3） | 全文档 | Status 引用 90 §4 / 91 §3.1 枚举本体 | TEXT-CORRECTED |
| F-OD01V3-09 | OD-01F-29 | ID 空间三分且无映射表 | §0 | 本表唯一完整 | REMEDIATED |
| F-OD01V3-10 | OD-01F-30 | Authority Level 填写 L1 与 NOT REGISTERED 自相矛盾 | Header | Authority Level ≠ Registration Level | TEXT-CORRECTED |
| F-OD01V4-01 | OD-01F-31 | char offset 编码单位未钉死 | Proposal §3.3 · CI-4 | Unicode code point 已选定 | REMEDIATED |
| F-OD01V4-02 | OD-01F-32 | 50 任务书文件名不一致 | §7 | 注明实名 50_Migration_Assets.md | REMEDIATED |
| F-OD01V4-03 | OD-01F-33 | 四道门未过 | §8 | 全 PENDING | REMEDIATED |
| F-OD01V4R-01 | OD-01F-34 | 自审文件被当作独立对抗审查结论使用 | Historical Self Review | 边界声明；非 DSH 证据 | REMEDIATED |
| F-OD01V4R-02 | OD-01F-35 | 本轮唯一新增文档缺 90 §4 / 91 §5 强制 Header | 全文档 Header | 出生证明齐备 | REMEDIATED |
| F-OD01V4R-03 | OD-01F-36 | 禁用状态词修复不成立（COMPLETE / NEXT） | 全文档 | 禁词扫描空 | REMEDIATED |
| F-OD01V4R-04 | OD-01F-37 | CI-4 Proposed Text 内部自相矛盾（locator 冲突） | CI-4 | 分型规则；无无条件 line_ref | REMEDIATED |
| F-OD01V4R-05 | OD-01F-38 | 字段重命名未进入 change set（resolution 双名） | Proposal §2.2 · CI-4/6/9 | 仅 span_resolution；示例同步 | REMEDIATED |
| F-OD01V4R-06 | OD-01F-39 | 规范字段 Authority Level 被改名/替换 | Header | 仅用冻结枚举值 | TEXT-CORRECTED |
| F-OD01V4R-07 | OD-01F-40 | ID Mapping 表不完备且存在错配 | §0 | 本表；Problem=DSH 基准 | TEXT-CORRECTED |
| F-OD01V4R-08 | OD-01F-41 | 引入第 7 套命名空间，且 R-xx 语义在仓库内无定义 | §0 说明 | 不使用 R-xx 命名空间 | TEXT-CORRECTED |
| F-OD01V4R-09 | OD-01F-42 | Gap 结论两版并存；90:47 未归层后果仍未登记 | §9 · D1 · 头块 | 单向表述；未归层已登记 | TEXT-CORRECTED |
| F-OD01V4R-10 | OD-01F-43 | 新文档违反 90 §5 Rule 2（禁止词升级） | 全文档 | 禁词扫描；L3/L4 引用约束 | TEXT-CORRECTED |
| F-OD01V4R-11 | OD-01F-44 | 新增文档的 Path 字段指向另一个仓库 | 全文档 Path | 仅本仓路径 | TEXT-CORRECTED |
| F-OD01V4R-12 | OD-01F-45 | Current Rule 块保真度参差且未标注逐字/改写 | §6 各 CI | 每条标 verbatim/summary | TEXT-CORRECTED |
| F-OD01V4R-13 | OD-01F-46 | CI-12 与 CI-4 声明「同文」但实际不同文 | CI-4 + CI-12 + §6.3 合并文本 | 给出合并后 20 §5.5 全文 | TEXT-CORRECTED |
| F-OD01V4R-14 | OD-01F-47 | （HIGH）治理产物逐字节复制进入 AITutor-X 且从未 commit：跨仓副本；独立审查边界破坏风险 | 交付物归位 AITutors-v3；AITutor-X 无 COORDINATION 副本 | 本仓四件套；报告仓无治理副本 | REMEDIATED |
| F-OD01V4R-15 | OD-01F-48 | Finding→Fix 映射错配 3 行、缺失 4 项、空号 2 个 | §0 | 本表重建；09/10 已填 | TEXT-CORRECTED |
| F-OD01V4R-16 | OD-01F-49 | Gap 未修复却被映射到无关 Fix 并标 VERIFIED | §9 · CR-002 §0 | Gap 单向化；未归层登记 | TEXT-CORRECTED |
| F-OD01V4R-17 | OD-01F-50 | Purpose 字段从 Proposal/CR 头块消失 | 全文档 Header | Purpose 有；Derives From 拼写 | REMEDIATED |
| F-OD01V4R-18 | OD-01F-51 | Authority Level 值域被自创 | Header · §2.1 | 冻结枚举 + Future Required Change | TEXT-CORRECTED |
| F-OD01V4R-19 | OD-01F-52 | 状态词换词未归位；OD-01-H 引错章节 | 全文档 · §2.3 | Status 用冻结枚举；处置列分离 | TEXT-CORRECTED |
| F-OD01V4R-20 | OD-01F-53 | change set 要求 table_id 但 L0 无该实体且无生产者/不可满足 | CI-2 · §5 | 方案 B identity；生产来源前置；fail closed | REMEDIATED |
| F-OD01V4R-21 | OD-01F-54 | 5 个 CI 丢失 Current Rule | §6 CI-1…12 | 六段结构齐备 | REMEDIATED |
| F-OD01V4R-22 | OD-01F-55 | CI-4 的「逐字」并非逐字；字段名证据被移出 | CI-4 | verbatim/summary 分离标注 | REMEDIATED |
| F-OD01V4R-23 | OD-01F-56 | form 用语与 OD-01 绑定用语脱钩且无对照表 | §3.1 | line_range↔line 等 | REMEDIATED |
| F-OD01V4R-24 | OD-01F-57 | Self Review 头块围栏损坏且缺 5 个强制字段 | REPORTS Self Review | 出生证明齐备 | REMEDIATED |
| F-OD01V4R-25 | OD-01F-58 | 破引用与跨仓路径残留 | 全文档 | 仅本仓路径；引用可解析 | TEXT-CORRECTED |
| F-OD01V4R-26 | OD-01F-59 | 机械替换痕迹 `PENDING = Owner Review` | 全文档 | 无替换式状态描述 | TEXT-CORRECTED |
| F-OD01V4R-27 | OD-01F-60 | 头块字段名仍不规范；新增多个非规范字段 | 全文档 Header | Derives From；Supersedes=清单或— | TEXT-CORRECTED |
| F-OD01V4R-28 | OD-01F-61 | OWNER APPROVED RECORD 内拼写错误与同文件流程不一致 | D1 · 全文档 | APPROVED；v4R 唯一 Current | TEXT-CORRECTED |
| F-OD01V4R-29 | OD-01F-62 | 新引入非冻结分类词 Future * | §10 | Planning Category only | REMEDIATED |
| F-OD01V4R-30 | OD-01F-63 | 映射表偷换概念：-11…-14 四行 Problem 与 DSH 基准不符；HIGH 跨仓复制零登记 | §0 | 七行 Problem 已按基线恢复；-14 单独成行 | TEXT-CORRECTED |
| F-OD01V4R-31 | OD-01F-64 | -08/-09/-10 三行错配原样保留却宣告映射表 VERIFIED | §0 | 三行 Problem 已按基线恢复 | TEXT-CORRECTED |
| F-OD01V4R-32 | OD-01F-65 | OD-01F-09/10 空号；F-OD01V3-11/12 零命中 | §0 | 09/10 已填 V3-11/12 | TEXT-CORRECTED |
| F-OD01V4R-33 | OD-01F-66 | change set 遗漏 README.md §2 术语登记 target | §7 · §10 · CI 注记 | README §2 列入 Target；术语清单 | REMEDIATED |
| F-OD01V4R-34 | OD-01F-67 | CI-4 自称 form 与 granularity 正交却共用值名 | CI-4 | 维度定义 + 绑定规则；禁称正交 | REMEDIATED |
| F-OD01V4R-35 | OD-01F-68 | 无条件 line_ref 与 table_cell line_ref 可选并存 | CI-4 | 按 form 分型；删除无条件句 | REMEDIATED |
| F-OD01V4R-36 | OD-01F-69 | table_cell 强制条款无判定标准且含元陈述 | CI-2 方案 B | 可判定四元组；无元陈述 | REMEDIATED |
| F-OD01V4R-37 | OD-01F-70 | CI-4 与 CI-12 同改 20 §5.5 无合并文本 | §6.3 | 合并后全文 | REMEDIATED |
| F-OD01V4R-38 | OD-01F-71 | 20:317 JSON 示例未同步改写 | §6.3 合并文本 | 示例字段 span_resolution | REMEDIATED |
| F-OD01V4R-39 | OD-01F-72 | CR-002 Status 由合法 NOT RELEASED 改为枚举外 NOT REGISTERED | CR-002 Header | Status=NOT RELEASED | TEXT-CORRECTED |
| F-OD01V4R-40 | OD-01F-73 | Authority Level 值域仍自创；Self Review 层级不符 | 全文档 Header | 冻结枚举；Self Review=L3 | TEXT-CORRECTED |
| F-OD01V4R-41 | OD-01F-74 | 「状态词仅用 91 §3.1」为假陈述 | §2.3 | 声明已改为分层真陈述 | TEXT-CORRECTED |
| F-OD01V4R-42 | OD-01F-75 | D1 新附录缺 5 强制字段；Status/Authority 非枚举值 | D1 新附录 | 出生证明齐备；枚举值 | TEXT-CORRECTED |
| F-OD01V4R-43 | OD-01F-76 | Self Review 头块缺 4 字段；Status 语义错位；Derives From 非文档闭包 | Self Review Header | HISTORICAL；字段齐备 | TEXT-CORRECTED |
| F-OD01V4R-44 | OD-01F-77 | Self Review 历史正文被删除（108→45 行） | Self Review | 历史正文已恢复（git b6cb762） | BODY-RESTORED |
| F-OD01V4R-45 | OD-01F-78 | Gap 路径标题残留；未归层第四轮 0 命中 | D1 · 头块 | Gap 标题移除；未归层已登记 | TEXT-CORRECTED |
| F-OD01V4R-46 | OD-01F-79 | 非规范头字段持续增列；Supersedes 值格式错误 | 全文档 Header | Supersedes=清单或—；非规范字段移出 | TEXT-CORRECTED |
| F-OD01V4R-47 | OD-01F-80 | v3 系列 Problem 4 行不符与 2 行互换 | §0 | V3 Problem 已按基线恢复 | TEXT-CORRECTED |
| F-OD01V4R-48 | OD-01F-81 | D1 OD-01-J 流程块与同文件两版流程不一致 | D1 OD-01-J | 统一为 v4R → DSH 外部验证 | TEXT-CORRECTED |

**映射表规则：** 不使用 `R-xx` 等附加命名空间。`Finding Disposition` 词汇表（非 Status）：`REMEDIATED` · `TEXT-CORRECTED` · `REGISTERED` · `BODY-RESTORED` · `PENDING`。

---

## 1. 缺口基线

| 形态 | 判定 | 依据 | OD-01 关系 |
|------|------|------|------------|
| line / line_character + offsets | 现有能力 | `20 §5.5` | form 术语见 §3.1 |
| Role spans / text_hash / 解析级联 | 现有能力 | `20` `10` | 保持 |
| options_lines | 现有义务 | P04.2 | 保持 |
| polymorphic option provenance | 真缺口 | — | 本 change set |
| multiple_source_spans / other | 真缺口 | — | 新增 |
| table_cell option 定位 | 延后+非目标 | `00 §5` `10 §4` `20 §5.5` | CHANGE-4 子集 |
| fragment / 完整 cell 索引 | 延后/非目标 | 同上 | 不解除 |
| image_region | 真缺口 | — | other 实例 |
| 降级质量标记 | 本轮不纳入 | — | Planning: Future Consideration |
| V3 无条件 option 边界发现 | 现有规定 | `20 §5.3` | CHANGE-5 删除/替换 |
| README §2 术语登记 | 前置条件 | `10:100-101` | 见 §10 |

---

## 2. Authority / 字段 / 状态

### 2.1 Authority Level — 仅冻结枚举

| 对象 | Authority Level（冻结值） | 治理角色（非枚举） |
|------|---------------------------|--------------------|
| Owner Decision | **L2** | 决策记录 |
| Proposal | **L2-proposed** | 变更提案 |
| CR-002 | **L2-proposed** | 变更记录候选 |
| Self Review（Docs/REPORTS） | **L3** | 证据/报告 |

**Planning Category: Future Required Change** — 冻结枚举（`90 §4:375` / `91 §5:167`）**无法表达**「决策权 / 提案权 / 变更记录权」三分角色。本轮取最接近冻结值（上表）。在正式值域经 L1 流程确立前，**禁止自创层级**（`91 §5.1` 门槛 3）。

| 并行字段 | 值 | 含义 |
|----------|-----|------|
| **Registration Level** | NOT REGISTERED | **仅**注册状态跟踪 |

**禁止** `Authority Level = L1`（除非已正式注册）。**禁止** Authority Level 与 Registration 混用。

### 2.2 解析字段唯一命名（span_resolution）

| 层 | 唯一命名 | 值域 |
|----|----------|------|
| provenance/span 解析 | **span_resolution** | exact / normalized / contextual / fuzzy / ambiguous / missing / incomplete |
| option 证据 | option_evidence_status | resolved / unresolved / incomplete |
| answer 结论 | answer_status | source_located / complete / verified_correct |
| IR 完备 | semantic_status | ready / incomplete |

禁止 `resolution_status` 等双名。禁止 `options_unresolved` 作为字段名。

### 2.3 状态词 — 分层真陈述

| 场景 | 允许取值 | 依据 |
|------|----------|------|
| Header `Status` 字段 | 仅 `90 §4:376` / `91 §3.1` 枚举值（ACTIVE / SUPERSEDED / HISTORICAL / DRAFT / CLOSED / NOT RELEASED；及 91 §3.1 的 OPEN / PENDING / CONDITIONAL PASS / NOT STARTED / DEFERRED / RETRACTED） | 冻结枚举 |
| Finding Disposition 列（非 Status 字段） | REMEDIATED / TEXT-CORRECTED / REGISTERED / BODY-RESTORED / PENDING | 处置词汇；**不声称**属 `91 §3.1` |
| Owner Decision 历史表 Status 列 | 历史原文保留（不重写） | AGENTS：不重写历史决策语义 |
| 禁用词（新文档） | COMPLETE / DONE / FINISHED / NEXT / REVIEWED / APPROED | `91 §3.2` |

**不得**声称「状态词仅用 91 §3.1」覆盖处置列。不确定 → Header 填 `PENDING`。

---

## 3. 定位规则与 form 术语

### 3.1 Form 术语对应

| Producer / P04 / 调查用语 | L0 form 名 | 关系 |
|---------------------------|------------|------|
| `line_range` | **`line`** | 同一能力：行区间。Producer 用语 → L0 form 名映射；非两套坐标。 |
| `char_span_in_line` | **`line_character`** | 同一能力：行内字符区间 + offset。映射既有 `granularity: line_character`。 |
| `table_cell` | `table_cell` | 同名。 |
| `multiple_source_spans` | `multiple_source_spans` | 同名。 |
| `other` | `other` | 同名；`image_region` = `other` 的实例名（method）。 |

Change Set 统一采用 **L0 form 名**；Producer 用语仅作对照（对照表在 Proposal，不把 Producer 别名写入 L0 值域）。

### 3.2 Locator（按 form 分型）

| Form | 必需 | 可选 | 禁止 |
|------|------|------|------|
| line | line_ref（start/end） | — | 无定位标 resolved |
| line_character | line_ref + character offset | — | 缺 offset；伪造 |
| table_cell | table_cell identity 四元组（§5 / CI-2） | line_ref | 「完全无定位」 |
| multiple_source_spans | 多条 provenance entry（成员各带 form+locator） | — | 假连续；空列表 resolved |
| other | 显式 provenance 描述（method+locator+可验证回溯） | — | 不可验证 free-form；伪造 line_ref |

**无**「一切 form 必须 line_ref」无条件规则。**无**「table_cell 不需要任何定位」。

### 3.3 字符 offset

Unicode code point；行内 0-based；start inclusive；end exclusive。已选定，不留待决。

---

## 4. 三路径统一 Provenance

```text
Native + Adapter + Artifact → Unified Provenance Model → Canonical V3 IR → Gate / Admission
```

- Artifact-first / Artifact-authoritative；Single provenance authority。
- No V3 rediscovery（Artifact 路径）。
- Fail closed。
- Artifact provenance 不替代 Native authority；消费层禁止第二 semantic authority。
- Path A（Native）：Native Resolver 确定性 first-resolution（非对 Producer 的 rediscovery）。
- Path Adapter：verify/translate only；ResolvedRun 唯一消费入口。

---

## 5. table_cell identity（方案 B）— 可判定结构

```text
table_cell identity = (source_version_id, table_id, row_index, column_index)
```

| 字段 | 含义 | 生产来源（唯一） |
|------|------|------------------|
| `source_version_id` | sealed Source Version 主键 | Source Version seal（`10 §4`，已存在） |
| `table_id` | 该 source version 内表格稳定标识 | **必须存在** — 见下 |
| `row_index` | 表内行索引，0-based | Producer/preprocessing 表格切分（Artifact `options[]` 携带；Path B） |
| `column_index` | 表内列索引，0-based | 同上 |

**可判定定位标准：** 四字段均有值，且 `source_version_id` / `row_index` / `column_index` 可在 sealed Source 与 Artifact `options[]` 中核对。

**table_id 生产来源规则：**

1. `table_id` 的生产来源**必须存在**（前置条件）。
2. 当前 Frozen Spec **未定义** `table_id` 生产来源（`10 §4` 无 `document_source_tables`；`00 §5` 完整表格索引为非目标）。
3. → **Planning Category: Future Required Change**：在 Frozen Spec 写入前，确立 `table_id` 唯一生产来源（Producer Artifact 字段或 `10 §4` 实体）并登记。写入 Spec 时的唯一来源 = 该已确立生产者。
4. **不得**假设生产来源已存在。**不得**在本轮创建 schema / 字段 / 实现。
5. 在生产来源确立前：`table_cell` **不得**标 `option_evidence_status=resolved`（fail closed → unresolved/incomplete + review）。

**禁止**将 table_id 的定义完全推迟到未决未来（该状态不可判定）。**禁止**元陈述进入 L0（不写「identity 形状与 Frozen Spec 对齐前不得声称…」类流程句）。本条不授权数据库 schema 变更。

---

## 6. Change Items（F-OD01V4R-21/22）

结构固定：**Current Rule → Problem → Proposed Frozen Text → Reason → Impact → Affected**。

### CI-1 `00_Master_Spec.md` §5 — CHANGE-4

**Current Rule**（verbatim）

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20；待样本
  证明需要再加回）。
```

**Problem：** option provenance 的 table_cell 子集与非目标冲突。  
**Proposed Frozen Text**

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20；待样本
  证明需要再加回）。
  例外子集（CHANGE-4）：option provenance 允许 table_cell 定位（identity 见 10 §4 /
  20 §5.5）。完整文档级 cell/fragment 索引与 fragment form 仍为非目标，不解除。
```

**Reason：** 样本证明需要。 **Impact：** 放宽约束。 **Affected：** `00 §5`。

### CI-2 `10_Data_Model.md` §4 — CHANGE-4

**Current Rule**（verbatim）

```text
依据 01 v0.3 收敛。**M1 裁剪**：`document_source_tables / _cells / _fragments` 不建
（00 §5 non-goal：文档级 cell/fragment 字符粒度延后）；`source_figures` 保留（M1
必需）。
```

**Problem：** 与 option table_cell 定位冲突；table_id 无生产者时不可满足。  
**Proposed Frozen Text**（方案 B；含 identity 结构与生产来源）

```text
依据 01 v0.3 收敛。**M1 裁剪**：`document_source_tables / _cells / _fragments` 不建
完整文档级索引（00 §5 non-goal：文档级 cell/fragment 字符粒度延后；fragment 不解除）。
`source_figures` 保留（M1 必需）。

option provenance 的 table_cell 使用下列 identity 结构定位：

  table_cell identity = (source_version_id, table_id, row_index, column_index)

字段含义：
  source_version_id  sealed Source Version 主键（生产来源：Source Version seal，10 §4）。
  table_id           该 source version 内表格的稳定标识（生产来源必须存在，见下）。
  row_index          表内行索引，0-based（生产来源：Producer 表格切分 / Artifact options[]）。
  column_index       表内列索引，0-based（同上）。

table_id 生产来源（前置条件）：
  table_id 的生产来源必须存在。当前 Frozen Spec 未定义 table_id 生产来源
  （本节不建 document_source_tables）。Future Required Change：在 Frozen Spec
  写入前确立 table_id 唯一生产来源并登记；写入 Spec 时的唯一来源 = 该已确立生产者。
  不得假设生产来源已存在。本条不授权数据库 schema 变更。

可判定标准：
  table_cell 定位可验证 ⇔ 四元组四字段均有值，且 source_version_id / row_index /
  column_index 可在 sealed Source 与 Artifact options[] 中核对。
  table_id 生产来源确立前，table_cell 不得标 option_evidence_status=resolved
  （fail closed → unresolved 或 incomplete，进入 review）。
```

**Reason：** 与 CI-1 一致；消除不可判定条款与元陈述。 **Impact：** CHANGE-4。 **Affected：** `10 §4`。

### CI-3 `20_Document_Pipeline.md` §5.3 — CHANGE-5

**Current Rule**（verbatim）

```text
- **option_label**：按 A/B/C/D 顺序；每项到下一标签/下一题结束；重复标签 →
  ambiguous；缺标签 → incomplete。
```

**Problem：** 与 Artifact 权威 / 禁 rediscovery 冲突。  
**Proposed Frozen Text**

```text
- **option segmentation / option_label**：
  Artifact 路径：Preprocessing Artifact options[] 是 option segmentation 权威来源。
  V3 仅 verification / normalization / consistency check，并可 fail closed。
  V3 不得重新发现 option 边界，不得从 options_lines 切分 option。
  Native 路径：Native Resolver 确定性 role resolution 产出 option 边界（首次解析）。
  两路径必须产出语义等价 option 结构；V3 消费层不得建立第二套 segmentation
  authority。label 重复 → ambiguous；缺 label → incomplete。
```

**Reason：** 删除无条件 V3 发现规则。 **Impact：** CHANGE-5。 **Affected：** `20 §5.3` 及下游提取/IR。

### CI-4 `20_Document_Pipeline.md` §5.5 — CHANGE-4+2

**Current Rule**（**verbatim**，仅以下两行原文；示例 JSON 与 Resolved Relation 为 summary 参照）

```text
- `granularity` ∈ {line, line_character}（M1；table_cell/fragment 延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 必须能唯
  一定位"同行多题答案/单行多选项"场景。
```

**Problem：** 无 form 维度；form/granularity 同名却称正交；无条件 line_ref 与 table_cell 可选冲突；解析字段名待统一；offset 单位未写死；`20:317` 示例仍为 `resolution_status`。  
**Proposed Frozen Text**（增量；完整合并文本见 §6.3）

```text
- `granularity` ∈ {line, line_character}（M1；fragment 延后，见 00 §5）。
- 维度定义：`form` 描述 provenance 定位空间结构（用何种源结构定位）；
  `granularity` 描述 span 解析粒度（在该结构上解析到何种精度）。
  M1 允许相同名称 line / line_character：同一 M1 能力在两个维度上的对偶标签，
  不是两个独立概念。绑定规则（非正交，禁止声明正交）：
    form=line ⇒ granularity=line；
    form=line_character ⇒ granularity=line_character；
    form ∈ {table_cell, multiple_source_spans, other} ⇒ granularity 字段缺省。
  form ∈ {line, line_character, table_cell, multiple_source_spans, other}。
  Producer 用语映射（对照，不进入 L0 值域）：line_range → line；
  char_span_in_line → line_character。
- line_ref / locator 按 form 分型（本条取代一切无条件 line_ref 规则）：
    line → line_ref 必需，且必须存在于该 source_version；
    line_character → line_ref + character offset 必需；line_ref 必须存在于该
      source_version；start/end_offset 为 Unicode code point（行内 0-based，
      start inclusive，end exclusive），必须能唯一定位「同行多题答案/单行多选项」；
    table_cell → table_cell identity 四元组必需（10 §4）；line_ref 可选；
    multiple_source_spans → 多条 provenance entry 必需；
    other → 显式 provenance 描述（method+locator+可验证回溯）必需。
  禁止要求一切 form 具备 line_ref；禁止 table_cell 无任何定位；禁止伪造 line_ref。
- 解析字段唯一命名：span_resolution
  （值域 exact/normalized/contextual/fuzzy/ambiguous/missing/incomplete）。
  同节示例 JSON 中 resolution_status 同步替换为 span_resolution。
- option_evidence_status=resolved 时 form 为 1..n。
```

**Reason：** 消除正交/同名矛盾、无条件 line_ref、双名与示例不同步。 **Impact：** CHANGE-4+2。 **Affected：** `20 §5.5`；`10 §8`。

### CI-5 `20 §6.1` — CHANGE-2+1

**Current Rule**（summary）

```text
IR content.options[label].source_span 示例 span_id：sp-Q1-A。
```

**Problem：** 链路权威未写入。  
**Proposed Frozen Text**

```text
option source_span 表达统一 provenance 模型中的规范化结果。链路：
  path-specific provenance evidence → V3 verification / normalization
  → unified provenance → IR source_span。
Native / Adapter / Artifact 不得形成互相竞争的 semantic authority。
冲突保留 conflict signal，不得静默覆盖，进入 review 或 fail closed。
示例 span_id 以 sp-Q1-A 为准。
```

**Reason：** 单 authority。 **Impact：** CHANGE-2+1。 **Affected：** `20 §6.1`。

### CI-6 `20 §6.2` — CHANGE-2+3

**Current Rule**（summary）

```text
E ResolvedStatus ≠ IR.semantic_status ≠ gate_decision（三层状态不复用）。
```

**Problem：** 解析字段命名需唯一。  
**Proposed Frozen Text**

```text
解析字段唯一命名：span_resolution（provenance/span 解析层）。
option_evidence_status（option 证据层）≠ answer_status（answer 结论层）
≠ semantic_status（IR 完备层）。四者语义独立、禁混用、禁双名。
E ResolvedStatus ≠ IR.semantic_status ≠ gate_decision 保持。
```

**Reason：** 唯一命名。 **Impact：** CHANGE-2+3。 **Affected：** `20 §6.2`。

### CI-7 `20 §7.2` — CHANGE-3

**Current Rule**（summary）

```text
Compiler 从 line / line_character Resolved Span 提取。
```

**Problem：** 需覆盖 form 维度并保持禁 rediscovery。  
**Proposed Frozen Text**

```text
Compiler 从 Resolved Span 按 form 提取（line / line_character / table_cell /
multiple_source_spans / other）。不得重新发现 option 边界；不得从 options_lines
切分。无法可靠解析 → option_evidence_status=unresolved 或 incomplete，fail closed。
```

**Reason：** 对齐 form。 **Impact：** CHANGE-3。 **Affected：** `20 §7.2`。

### CI-8 `20 §7.3` — CHANGE-1

**Current Rule**（summary）

```text
dedup 组合键与 Exact Replay / Rebuild 不变量。
```

**Problem：** 防误改；组合不变。  
**Proposed Frozen Text**

```text
dedup 组合键与 Exact Replay / Rebuild 不变量保持不变。Resolved Span 增加 form
不改变既有 dedup 组合定义。
```

**Reason：** 防误改。 **Impact：** CHANGE-1。 **Affected：** `20 §7.3`。

### CI-9 `10 §6.3` — CHANGE-1+2

**Current Rule**（summary）

```text
JSONB invariant；option provenance 结构。
```

**Problem：** 需含 form / span_resolution。  
**Proposed Frozen Text**

```text
option provenance JSON 结构增加 form 与 span_resolution 字段（命名见 20 §6.2）。
JSONB invariant 与既有键保持；不引入双名。
```

**Reason：** 红线一致。 **Impact：** CHANGE-1+2。 **Affected：** `10 §6.3`。

### CI-10 `10 §8` — CHANGE-2

**Current Rule**（summary）

```text
line 系核验规则。
```

**Problem：** 需分型 locator。  
**Proposed Frozen Text**

```text
核验规则按 form 分型（见 20 §5.5 locator 表）。禁止「一切 provenance 必须
line_ref」。禁止为 table_cell / other 伪造 line_ref。
```

**Reason：** 分型。 **Impact：** CHANGE-2。 **Affected：** `10 §8`。

### CI-11 `50_Migration_Assets.md` bbox 行 — CHANGE-2+3

**Current Rule**（summary）

```text
图像/表格 bbox 定位能力：source_figures + role 归属。
```

**Problem：** option table/image provenance 需对齐。  
**Proposed Frozen Text**

```text
| 图像/表格 bbox 定位能力 | 保留思想，重写 | source_figures（page/bbox/placement/source，IS-7）+ role 归属；option provenance 的 table_cell 使用 table_cell identity 四元组定位，other(method=image_region) 使用 figure/region 身份；line_ref 可选，不得伪造 |
```

**Reason：** 对齐。 **Impact：** CHANGE-2+3。 **Affected：** `50_Migration_Assets.md`。

### CI-12 other / image_region — CHANGE-2

**Current Rule**（summary）

```text
无开放 other form；无 image_region 正式承载；20 §5.5 无 image_region 段落。
```

**Problem：** 图片化选项无法用 line 表达；与 CI-4 同改 20 §5.5 需合并归属。  
**Proposed Frozen Text**（增量；完整合并文本见 §6.3）

```text
form=other 的实例 image_region 使用 method=image_region，并必须携带 figure/image
身份、可验证区域（page/bbox/placement 或等价 region）、可独立回溯信息。
image_region 不是顶级 provenance form。无法可靠确定时 option_evidence_status=
unresolved 或 incomplete 并进入 review / fail closed；不得伪造 option text。
fragment 不纳入 form 枚举。不引入降级质量标记（Planning Category: Future Consideration）。
```

**Reason：** 覆盖真实语料形态。 **Impact：** CHANGE-2。 **Affected：** `20 §5.5`（与 CI-4 合并，见 §6.3）。

### CI-README `README.md` §2 — 术语登记前置（F-OD01V4R-33）

**Current Rule**（verbatim，`10:100-101`）

```text
- 枚举值与 JSON 内字段名以 `README.md` §2 与 20/30 schema 为准；**新增术语必须先
  登记 README §2 再在本 schema 使用**。
```

**Problem：** 新术语未登记 README §2 即写入 change set，违反 L0 自身前置规则。  
**Proposed Frozen Text**（写入 README §2 术语表的条目；本任务**不修改** README.md 本体）

```text
| span_resolution | provenance/span 解析状态唯一字段名 | resolution_status（废止双名） | 值域 exact/normalized/contextual/fuzzy/ambiguous/missing/incomplete |
| option_evidence_status | option 证据层状态 | — | resolved / unresolved / incomplete |
| form | provenance 定位空间结构 | Producer: line_range / char_span_in_line | line / line_character / table_cell / multiple_source_spans / other |
| line | form：行区间 | line_range | 与 granularity=line 对偶标签 |
| line_character | form：行内字符区间 | char_span_in_line | 与 granularity=line_character 对偶标签 |
| table_cell | form：表格 cell | 同名 | identity=(source_version_id, table_id, row_index, column_index) |
| multiple_source_spans | form：多源 span | 同名 | 多条 provenance entry |
| other | form：其他 | image_region 为实例 method | 非顶级实例名不进 form 枚举 |
| table_cell identity | table_cell 定位四元组 | — | 见 10 §4 / 20 §5.5 |
```

**迁移顺序（Future Required Change 执行序）：** 先 `README.md §2` 术语登记 → 再 `20` / `10` 条款。  
**Reason：** `10:100-101` + `90 §2 R6`。 **Impact：** CHANGE-2（术语层）。 **Affected：** `README.md §2`（本任务仅登记 Future Required Change，不改文件）。

---

## 6.3 合并后目标文本：`20 §5.5`（CI-4 + CI-12）

> **迁移者须整节替换/合并使用下文。** 不得只复制增量片段自行拼接。
> 含改写后 JSON 示例（`span_resolution`）。Current Rule 对照见 CI-4 / CI-12。

**合并后 Proposed Frozen Text（完整目标）**

```text
### 5.5 Resolved Span 输出

```json
{
  "span_id": "sp-Q1-stem", "source_version_id": "<uuid>",
  "start_line_ref": "P1L001", "end_line_ref": "P1L002",
  "line_refs": ["P1L001", "P1L002"],
  "form": "line",
  "granularity": "line",
  "start_offset": null, "end_offset": null,
  "text_hash": "<sha256>", "span_resolution": "exact",
  "evidence": ["question_label=1", "next_boundary=Q2"]
}
```

- `granularity` ∈ {line, line_character}（M1；fragment 延后，见 00 §5）。
- 维度定义：`form` 描述 provenance 定位空间结构（用何种源结构定位）；
  `granularity` 描述 span 解析粒度（在该结构上解析到何种精度）。
  M1 允许相同名称 line / line_character：同一 M1 能力在两个维度上的对偶标签，
  不是两个独立概念。绑定规则（非正交，禁止声明正交）：
    form=line ⇒ granularity=line；
    form=line_character ⇒ granularity=line_character；
    form ∈ {table_cell, multiple_source_spans, other} ⇒ granularity 字段缺省。
  form ∈ {line, line_character, table_cell, multiple_source_spans, other}。
  Producer 用语映射（对照，不进入 L0 值域）：line_range → line；
  char_span_in_line → line_character。
- line_ref / locator 按 form 分型（本条取代一切无条件 line_ref 规则）：
    line → line_ref 必需，且必须存在于该 source_version；
    line_character → line_ref + character offset 必需；line_ref 必须存在于该
      source_version；start/end_offset 为 Unicode code point（行内 0-based，
      start inclusive，end exclusive），必须能唯一定位「同行多题答案/单行多选项」；
    table_cell → table_cell identity 四元组必需（(source_version_id, table_id,
      row_index, column_index)，见 10 §4）；line_ref 可选；
    multiple_source_spans → 多条 provenance entry 必需（成员各带 form+locator）；
    other → 显式 provenance 描述（method+locator+可验证回溯）必需。
  禁止要求一切 form 具备 line_ref；禁止 table_cell 无任何定位；禁止伪造 line_ref。
- form=other 的实例 image_region 使用 method=image_region，并必须携带 figure/image
  身份、可验证区域（page/bbox/placement 或等价 region）、可独立回溯信息。
  image_region 不是顶级 provenance form。无法可靠确定时 option_evidence_status=
  unresolved 或 incomplete 并进入 review / fail closed；不得伪造 option text。
  fragment 不纳入 form 枚举。不引入降级质量标记（Planning Category: Future Consideration）。
- 解析字段唯一命名：span_resolution
  （值域 exact/normalized/contextual/fuzzy/ambiguous/missing/incomplete）。
  本节示例 JSON 已使用 span_resolution；禁止 resolution_status 双名。
- option_evidence_status=resolved 时 form 为 1..n。
- `text_hash` 由程序按该 span 实际内容计算；同一 source version 内 span 可重放。
- **Annotation 不得包含本结构**（只在 Resolver 及之后出现）。
- **`figure_id` 结构化字段（D-6 Figure Contract 冻结）**：`image` ResolvedSpan 额外携带
  结构化 `figure_id`（= `source_figures.figure_id`）；**仅 image span 有意义**——text span
  `figure_id` = absent/null，不得伪造或填充 `""`/`"unknown"` 等字符串哨兵。figure_id 在
  跨层传递中**不得仅依赖非结构化 `evidence` 字符串重新解析**（structured field →
  structured field，BUG-020 根因修复原则）。

Resolved Relation：

```json
{"from": "Q11", "to": "M1", "type": "material_dependency", "resolved_target_span": {"span_id": "sp-M1"}, "status": "resolved"}
```

关系必须全部 resolved，IR 才可 ready。
```

**插入/合并位置：** 整节替换现行 `20 §5.5`（自 `### 5.5 Resolved Span 输出` 至 Resolved Relation 段结束）。CI-4 与 CI-12 不得再各给一份互不衔接的增量。

---

## 7. Explicit Diff Appendix

| File | Section | Current | Proposed | Reason | Impact | Gate Required |
|------|---------|---------|----------|--------|--------|---------------|
| `README.md` | §2 术语表 | 无 span_resolution / option_evidence_status / form | 登记新术语（先于 20/10） | `10:100-101` | CHANGE-2 | 前置 |
| `00_Master_Spec.md` | §5 | table/fragment 非目标 | option table_cell 子集解除 | 样本 | CHANGE-4 | 四道门 |
| `10_Data_Model.md` | §4 | `_cells` 等不建 | option cell 定位允许；identity 四元组；table_id 生产来源前置 | 一致 | CHANGE-4 | 四道门 |
| `10_Data_Model.md` | §6.3 | JSONB invariant | + form / span_resolution | 红线 | CHANGE-1+2 | PENDING |
| `10_Data_Model.md` | §8 | line 系核验 | 分型 locator | F-37 | CHANGE-2 | 联动 |
| `20_Document_Pipeline.md` | §5.3 | V3 无条件发现 | 分路径；禁 rediscovery | F-03 | CHANGE-5 | 四道门 |
| `20_Document_Pipeline.md` | §5.5 | line 系；resolution_status | + form；span_resolution；code point；image_region；合并全文 | F-37/38/43 | CHANGE-4+2 | 四道门 |
| `20_Document_Pipeline.md` | §6.1 | sp-Q1-A | + 单链路 | F-04 | CHANGE-2+1 | PENDING |
| `20_Document_Pipeline.md` | §6.2 | E≠F≠G | + 命名唯一 | F-17 | CHANGE-2+3 | PENDING |
| `20_Document_Pipeline.md` | §7.2 | line 系提取 | + form；禁 rediscovery | 一致 | CHANGE-3 | PENDING |
| `20_Document_Pipeline.md` | §7.3 | dedup 组合 | 组合不变 | 防误改 | CHANGE-1 | PENDING |
| `50_Migration_Assets.md` | bbox 行 | figures | + cell/image 对齐 | 对齐 | CHANGE-2+3 | PENDING |

---

## 8. CHANGE 与 Gate

```text
CHANGE-3: ACKNOWLEDGED
CHANGE-4: ACKNOWLEDGED — four-gate required
CHANGE-5: ACKNOWLEDGED — four-gate required
```

| Gate | Finding Disposition |
|------|---------------------|
| A | PENDING |
| B | PENDING |
| C | PENDING |
| D | PENDING |

---

## 9. CR-002 注册（单向表述）

```text
CR-002 = Change Proposal Record
Status: NOT RELEASED（90 §4 / 91 §3.1 枚举内）
L1: NOT REGISTERED AS L1（正文短语；非 Status 字段值）
Registration Level: NOT REGISTERED
Location: Docs/COORDINATION/（本仓；未归层，90:47）
```

**原因：** 尚未满足正式注册条件（下列四条未齐）。  
**不是**「没有 L1 落点」。**保留** Future registration path。**禁止**第二 registry。  
`Docs/COORDINATION/` 为 **未归层** 目录（不在 `90 §1.2` 模型内）；未归层文档**不得引用为权威**（`90:47`）。

Formal L1 registration requires（Planning Category: Future Required Change）:

1. Owner approval  
2. Gate completion  
3. Frozen Spec commit  
4. 90/91 governance registration  

---

## 10. Planning Category（非 Status）

| 词 | 性质 | 用途 |
|----|------|------|
| **Future Required Change** | Planning Category | 将来必须做的变更项 |
| **Future Consideration** | Planning Category | 将来可选考虑 |

**不是 Status。** 不得填入 Status 字段。

| 项 | Category |
|----|----------|
| 正式 L1 写入治理登记点 | Future Required Change |
| CA-002 登记 | Future Required Change |
| table_id 生产来源确立 + table_cell identity 与 Frozen Spec 对齐 | Future Required Change |
| **README.md §2 登记 span_resolution / option_evidence_status / form（及 L0 form 名）** | Future Required Change |
| Authority Level 决策/提案/变更记录角色值域（冻结枚举无法表达三分） | Future Required Change |
| 降级质量标记 | Future Consideration |

**README.md §2（不修改本体；仅记录未来同步位置）：** 须登记 `span_resolution`、`option_evidence_status`、`form`（及 `line` / `line_character` / `table_cell` / `multiple_source_spans` / `other`）。迁移顺序：先 README §2，后 20/10。

---

## 11. 非目标

Gate/Admission/Question Core/词汇/QT→UT/P01–P25/OD-02…G-02/历史重处理/Migration/X3/fragment 延后/降级态/schema/代码/Corpus/Preprocessing/re-freeze/Phase 1/修改 README.md 本体（本轮）。

---

**Document control**（非 Header 规范字段）

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` |
| Current Version | v4R |
| Content Predecessor | Proposal v4（同路径 git 历史；非 Supersedes 文档清单项） |
| Authority Level | L2-proposed |
| Registration Level | NOT REGISTERED |
| Status | PENDING |

