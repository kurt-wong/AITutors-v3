# FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE

```text
Document ID:           OD-01-PROPOSAL-v3
Title:                 OD-01 Frozen Spec Change Proposal — Option Provenance / Resolved Span
Document Type:         Decision Record（Frozen Spec Change Proposal 载体；非 Contract Change Record）
Authority Level:       L2
Status:                DRAFT
Normative:             NO（对 L0 尚未生效；不得被引用为 Frozen Spec）
Purpose:               承载 OD-01 option provenance 的条款级 explicit diff 与语义边界，供 CR-002 与 Owner Authorization 使用
Derives From:          OD-01（OWNER-DECISIONS）· OD-01R-01…10（同文件附录）· P04（Frozen Contract）· 00/10/20/50（L0，只读引用）· 90/91（L0-META）· 69 §5（四道门）
May Change:            本 Proposal 自身文本；配套 CR-002 候选文本的引用一致性
Must Not Change:       L0 00–50 正文 · L0-META 90/91 · Frozen Contract / P01–P25 · Gate/Admission/Question Core · 生产代码 · Schema · Corpus · Preprocessing
Supersedes:            OD-01 Proposal v2（2026-09-23）
Superseded By:         —
Gate State Authority:  NO（唯一 YES = 82 §3）
RE-FREEZE:             NOT DONE
OWNER AUTHORIZATION:   REQUIRED
```

> **NOT EFFECTIVE。尚未修改 Frozen Spec。**
> 当前生效 Frozen Spec = `Docs/V3_SPEC/**` @ tree `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`（unchanged）。
> **本文件不编辑 `Docs/V3_SPEC/**`。**
> **Proposal 必须服从 Frozen Governance（90/91）；不是 Proposal 定义治理规则。**
> 禁止使用自创层级（如 `L1-proposal`）或自创 Status。

**Related:** `OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md`（含 OD-01R-01…10）· `CONTRACT-CHANGE-RECORD-CR-002-OD-01.md`（L1 candidate / NOT RELEASED）· P04 · DSH review 与 F-OD01R 系列

---

## 0. R-01～R-10 处置状态

| ID | Owner Decision | 本文件落点 | Status |
|----|----------------|------------|--------|
| R-01 | ACCEPTED | §1 L1 落位判定（Governance Gap） | DONE — GAP RECORDED |
| R-02 | ACCEPTED | 文首出生证明 + 合法 Status/层级 | DONE |
| R-03 | ACCEPTED | §2 CHANGE-3/4/5 逐条 + 四道门 | DONE |
| R-04 | ACCEPTED | §3 Path A / Path B 双路径 | DONE |
| R-05 | ACCEPTED | §5 完整 explicit diff（含 10 §4、20 §6.2、50） | DONE |
| R-06 | ACCEPTED | §4 form 分型 locator | DONE |
| R-07 | ACCEPTED | §4 Provenance Resolution vs Option/Evidence Resolution | DONE |
| R-08 | ACCEPTED | §4 degraded ≠ fail-closed 后门 | DONE |
| R-09 | ACCEPTED | OWNER-DECISIONS 附录 OD-01R | DONE |
| R-10 | ACCEPTED | §6 引用坐标更正 | DONE |

---

## 1. R-01 — CR-002 正式 L1 落位判定

### 1.1 规则（只读，不修改）

| 来源 | 规则 |
|------|------|
| `90 §1` | L1 = Contract Change Record = 修改 L0 唯一入口；未走完流程不得生效 |
| `90 §1.2` | `Docs/V3_SPEC/` 允许「补 Change Record；新增 L1」；禁止「直接编辑；隐式改变」 |
| `90 §11` | L0 **实际修改后**登记 Change Audit（先例 CR-001） |
| `91 §5` | 出生证明字段强制（含 Derives From / May Change / Must Not Change） |
| `91 §3.1` | 合法 Status 含 `NOT RELEASED` |
| 先例 `67` | CHANGE-4/5 候选 = **NOT RELEASED**，**不是**已注册 L1 |

### 1.2 本轮约束冲突 → Governance Gap

```text
正式 L1「新增」唯一合法落位 = Docs/V3_SPEC/（90 §1.2）
本轮 Frozen Spec tree hash 必须保持 b3eeb3e9… 不变
向 Docs/V3_SPEC/ 新增文件 ⇒ tree hash 改变 ⇒ 违反本轮硬边界
既有目录模型内无第二正式 L1 registry
Docs/COORDINATION/ 不在 90 §1.2 目录模型内
禁止自创 L1 目录 / 禁止改 90/91 迁就 CR-002
```

### 1.3 判定（必须能明确回答）

> **问：按照 Frozen Document Governance，CR-002 当前是否已经是一个正式注册的 L1 Change Record？**
> **答：否。**

```text
CR-002 formal L1 status = NOT REGISTERED / L1 candidate / NOT RELEASED
GOVERNANCE GAP          = RECORDED（正式 L1 注册与 Frozen Spec tree hash 不变，本轮互斥）
禁止表述                = 「已注册 L1」「L1 已生效」「可据此改 L0」
对齐先例                = 67（CHANGE-4/5 候选，NOT RELEASED）
```

---

## 2. R-03 — 真实影响面与 CHANGE 分类（禁止压低）

判定规则（`90 §3`）：**拿不准往高里归。** 禁止「实际上不算删除/放宽」的自定义降级。

### 2.1 逐条：原 Rule → 新 Rule → 实际变化 → CHANGE → Gate

#### A. `00_Master_Spec.md` §5 非目标（table cell / fragment）

| 项 | 内容 |
|----|------|
| 原 Frozen Rule | 「文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20；待样本证明需要再加回）」= **M1 明确非目标/约束不做** |
| OD-01 新规则 | table_cell 在 **option provenance 子集**解除延后；`fragment` 与完整文档级表格索引**仍为非目标** |
| 实际变化 | **放宽既有非目标约束**（不是空白新增） |
| **CHANGE** | **CHANGE-4 — Constraint Relaxation** |
| 需要哪些 Gate | **四道门（69 §5）** + Change Record |
| 当前 Gate 状态 | Gate A/B/C/D 全部 **PENDING**（见 §7） |

#### B. `20_Document_Pipeline.md` §5.3 `option_label`

| 项 | 内容 |
|----|------|
| 原 Frozen Rule | 「option_label：按 A/B/C/D 顺序；每项到下一标签/下一题结束；重复标签 → ambiguous；缺标签 → incomplete」= **V3 无条件在 Resolver 侧发现 option 边界** |
| OD-01 新规则 | **Path B**：Producer Artifact = Option Segmentation Authority；V3 只验证/规范化/拒绝/fail closed；**禁止**从 `options_lines` rediscovery。**Path A**：无 Producer Artifact；由 Native Resolver 确定性 role resolution 产出边界（首次解析，不是对 Producer 证据的 rediscovery）。禁止形成两套语义标准 |
| 实际变化 | **删除/替换**既有「V3 无条件 option 边界发现」规则 |
| **CHANGE** | **CHANGE-5 — Constraint Removal**（删除既有无条件规则）**+ CHANGE-2**（新增 Producer authority / 禁 rediscovery）**+ CHANGE-3**（改为 path-aware 行为） |
| 需要哪些 Gate | **四道门（69 §5）** + Change Record + 受影响层回归 |
| 当前 Gate 状态 | Gate A/B/C/D 全部 **PENDING** |

#### C. `20_Document_Pipeline.md` §5.5（Resolved Span / granularity / 延后注）

| 项 | 内容 |
|----|------|
| 原 Frozen Rule | `granularity ∈ {line, line_character}`；「table_cell/fragment 延后，见 00 §5」；已有 `start_offset/end_offset` 服务「单行多选项」 |
| OD-01 新规则 | 增加 **provenance form 维度**；table_cell option 子集延后解除；fragment 仍延后；`char_span_in_line` 映射既有 `line_character`+offset |
| 实际变化 | 改延后注（放宽）+ 新增强制 form |
| **CHANGE** | **CHANGE-4**（延后放宽）+ **CHANGE-2**（form 维度）+ **CHANGE-3**（范围表述） |
| Gate | 四道门（并入 A/B）+ Change Record |

#### D. `20` §7.2 Compiler 提取 / §6.1 IR / §6.2 不变量 / §7.3 dedup / `10` §4/§6.3/§8 / `50` 表格行

见 §5 explicit diff；分类分别为 CHANGE-3 / CHANGE-2+1 / CHANGE-2+3 / CHANGE-1 / CHANGE-4+2 / CHANGE-2+3。

### 2.2 总体分类

```text
OVERALL = 含 CHANGE-4 + CHANGE-5（并含 CHANGE-3 / CHANGE-2 / CHANGE-1）
四道门  = REQUIRED（69 §5）—— 不得免除
Change Record = REQUIRED（CR-002；当前 L1 candidate / NOT RELEASED）
受影响层回归 = REQUIRED（re-freeze 后、实现授权后）
```

**禁止再出现：**「这些不是 CHANGE-4/5，所以不需要对应 Gate。」

---

## 3. R-04 — Path A / Path B 双路径（禁止两套语义标准）

`91 §1`：`Path A` = Native（Resolver search/resolve）；`Path B` = Adapter/Manifest（verify only）。
`90 §H-C`：`ResolvedRun` 必须是唯一消费入口。

```text
Path A（Native）
  Original Source
    → Seal
    → Annotation
    → Native Resolver（确定性 role resolution；首次解析）
    → ResolvedSpan / ResolvedRun
    → Canonical V3 IR
    → Gate / Admission

Path B（Artifact / Adapter）
  Original Source
    → AITutors-preprocessing
    → Preprocessing Artifact
         options[] = {label, text, provenance}   ← Option Segmentation Authority
         options_lines MUST KEEP
    → V3 Consumer Boundary（verification / normalization only）
    → ResolvedSpan / ResolvedRun
    → Canonical V3 IR
    → Gate / Admission
```

### 3.1 Option Segmentation Authority（分路径，不分裂 IR 语义）

| 路径 | Option Segmentation Authority | V3 允许 | V3 禁止 |
|------|-------------------------------|---------|---------|
| **Path B** | **Producer Artifact `options[]`** | 验证、一致性检查、拒绝不可靠证据、fail closed | **重新发现/猜测 option 边界**；从 `options_lines` 切 option；形成第二套 segmentation authority |
| **Path A** | **Native Resolver 确定性 role resolution**（含 option 边界；原 §5.3 族规则的 Path A 保留形态） | 确定性首次解析；同输入同输出 | 把 Path A 边界规则**冒充**为 Path B 的 rediscovery 许可；LLM 猜测边界 |

**澄清（对齐 F-OD01-03 且不破坏 Path A）：**

- 「V3 不重新发现 option 边界」的禁令，针对的是 **Path B 上对 Producer 已提供 segmentation 的 rediscovery**。
- Path A **没有** Producer Artifact，不存在「已提供再重发现」；Native Resolver 的确定性解析是该路径的 segmentation 来源，**不是**对 Producer 证据的覆盖或第二 semantic authority path（OD-04）。
- **禁止**用「V3 仍可自行推断、但通常相信 Producer」模糊措辞。

### 3.2 汇聚：Canonical V3 IR（唯一下游语义）

| 层 | 要求 |
|----|------|
| Native | 产出 ResolvedSpan/ResolvedRun |
| Adapter | 产出 ResolvedSpan/ResolvedRun（**不得**让下游改消费 annotation_payload） |
| ResolvedRun | **唯一消费入口**（`90 §H-C`） |
| Canonical V3 IR | 两路径必须 **语义等价、结构一致** |
| Gate / Admission | 只面对 Canonical IR 语义；不因路径分叉出现两套 Gate 语义 |

受影响层表必须覆盖：**Native · Adapter · ResolvedRun · Canonical IR**（见 §8）。

---

## 4. R-06 / R-07 / R-08 — Provenance ontology、双层 Resolution、degraded 与 fail-closed

### 4.1 Form 分型 Locator（R-06）— 不得编造 `line_ref`

> **不同 provenance 类型可以拥有不同 locator，但每一种都必须能够真实、可验证地指向 Original Source。**

| Form | Locator（必需） | 明确不要求 / 禁止 |
|------|-----------------|-------------------|
| `line_range` | `start_line` + `end_line`（1-based closed）→ 映射 source lines | — |
| `char_span_in_line` | `line` + `start_char` + `end_char`（编码单位 Owner 钉死）→ 映射既有 `line_character`+`start_offset/end_offset` | 不得另造第二字符坐标 |
| `table_cell` | **表格单元格身份**（`table` node / span + `row`/`col` 或 cell identity）+ **可回溯 raw** | **禁止**为满足旧字段编造 `line_ref`；禁止假连续行区间 |
| `multiple_source_spans` | `spans[]` = **有序 non-empty**；**每个成员 form 各带自己的 locator** | **禁止**压成一个假的连续 line range |
| `other` / `image_region` | `method` + figure/image **identity** + **可验证区域**（page / bbox / placement）+ 回溯信息 | **禁止**编造 `line_ref`；禁止不可验证 free-form |

**定位真实性规则：**

1. line 系 form：必须有合法 line/offset 定位。
2. 非 line 系 form：必须有该形态的原生 locator；**不得**为了通过「必须有 line_ref」的旧校验而伪造行号。
3. 任一 form 无法真实定位 → **不得**标 resolved。

### 4.2 双层 Resolution Status（R-07）— 不得共用一个 `resolution_status`

| 层 | 名称（治理语义） | 词汇来源 | 含义 |
|----|------------------|----------|------|
| **Provenance Resolution** | 附着在 **provenance / span 对象**上的解析状态 | **沿用** `20 §5.2` `ResolvedStatus`：`exact / normalized / contextual / fuzzy / ambiguous / missing / incomplete` | provenance **本身**是否被可靠解析/归一化 |
| **Option / Evidence Resolution** | 附着在 **option 证据整体**上的可用状态 | **不得**与上层共用同一字段名；在 L0 change set 中以**独立语义**表达（与 `20 §6.2` 三层隔离一致） | 整个 option 的证据是否达到可用状态 |

**对齐 `20 §6.2` 既有三层隔离（不得搅混）：**

```text
E  ResolvedStatus     = provenance/span 解析质量
F  semantic_status    = IR 完备性（ready / incomplete）
G  gate_decision / decision_status = 准入/裁决
```

**Schema 纪律（R-07）：**

- 本轮 **不修改生产 Schema**、不新增表/列。
- 若 Option/Evidence Resolution 需要 **Frozen Schema 新字段** → 属本 CR-002 的 L0 change set 成员，**STOP → Owner Authorization 后**才写入 L0/实现；不得本轮直接改 Data Model DDL。
- 禁止把 E 层状态搬运成 F/G（`20 §6.2` 已禁止）。

### 4.3 `degraded` 与 fail-closed（R-08）— `degraded` 不是后门

```text
可靠且可验证
  → normal resolved
      provenance ResolvedStatus ∈ {exact, normalized, contextual}（按 20 §5.2）

质量下降，但仍然能够可靠验证
  → degraded（显式降级声明；仍满足 form locator 真实性与可验证性）
  → 是否允许继续进入后续管线：必须由【显式规则】决定
  → 默认不得自动进入正常 Admission

无法可靠验证
  → unresolved / incomplete / QC_FAIL
  → fail closed
```

**强制原则：**

1. **任何无法可靠验证的 provenance，都不得因为标记为 degraded 而进入正常 Canonical provenance。**
2. **禁止**出现无规则依据的 `degraded → 继续正常 Admission`。
3. 图片化选项在 OCR/Markdown 层无法恢复文字时：必须 `degraded` / `unresolved` 声明，**不得伪造** option text（F-OD01-06 / R-08）。
4. 状态不得互相覆盖、互相绕过：

| 状态 | 层 | 能否当 resolved 用 | 能否进 ready IR | 能否单独进 Admission |
|------|----|--------------------|-----------------|----------------------|
| provenance ResolvedStatus exact/normalized/contextual | E | 是（在 Option 亦 resolved 时） | 依 F | 否（仍走 Gate） |
| degraded（显式） | E/证据质量 | 仅当显式规则允许 | 视显式规则；默认否 | **否（默认）** |
| Option/Evidence `unresolved` / `incomplete` | Option | 否 | 否 | 否 |
| `semantic_status=incomplete` | F | — | 否 | 否 |
| `QC_FAIL` | QC/Gate | 否 | 否 | 否 |

### 4.4 Fail-closed 承载（衔接 F-OD01-05，坐标见 §6）

- Path B 无/不可靠 `options[]` → Option fail closed（unresolved / incomplete / QC_FAIL）。
- Path A 解析失败 → 沿用 `20 §5.2` 非 ready 状态 → 不得 ready。
- **禁止**伪造 provenance；**禁止** 0-span 静默通过（resolved ⇒ form **1..n**）。
- **禁止**引入独立语义字段 `options_unresolved`（见 §6 坐标）。

---

## 5. R-05 — 完整条款级 Explicit Diff（非生效文本）

> 格式：Frozen Spec 原规则 → OD-01 变化 → 变化原因 → 变化后语义。
> **完整影响面**；不为凑数量加入无实际影响章节。正式采纳 = CR-002 + Owner Authorization + re-freeze change set。

### 5.1 `00_Master_Spec.md` §5（约 `:274-275`）— CHANGE-4

**原规则：**

```text
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20；待样本
  证明需要再加回）。
```

**OD-01 变化：** table_cell 的 **option provenance 子集**解除延后；`fragment` 与完整文档级表格索引仍非目标。

**原因：** 样本已证明 option table_cell 需要（P04 调查）；非目标本身带「待样本证明再加回」解除条件。

**变化后语义：** option provenance 可表达 `table_cell`；不得推出完整文档级 cell 索引；`fragment` 仍延后。

### 5.2 `00_Master_Spec.md` §5 — JSONB 隐式业务模型（**不改正文**）

**原规则：** 「用 JSONB 隐式承载整个业务模型」= 非目标。

**OD-01 变化：** **不修改该条**；在 `10 §6.3` 划界（§5.8）说明 form 扩展仅承载可验证 provenance 结构，不把业务模型塞进 JSONB。

**分类：** 无 L0 文本变化（引用约束）。

### 5.3 `10_Data_Model.md` §4（`:107-108`）— CHANGE-4（与 00 §5 联动）

**原规则：**

```text
M1 裁剪：document_source_tables / _cells / _fragments 不建
（00 §5 non-goal：文档级 cell/fragment 字符粒度延后）；source_figures 保留。
```

**OD-01 变化：** table_cell **option provenance 子集**不再完全落在「_cells 不建」的延后语义内——provenance 需能定位到可回溯 table cell/raw；`document_source_tables/_cells/_fragments` **整表索引**是否建表仍非本 CR 自动授权。

**原因：** F-OD01R-05 明确该行是 00 §5 的 schema 侧投影；不改则与 form=table_cell 矛盾。

**变化后语义：** option table_cell provenance 可验证定位被允许；**不**自动授权新建 `_cells` 表或 DB migration。

### 5.4 `20_Document_Pipeline.md` §5.3 `option_label`（约 `:280-281`）— **CHANGE-5**

**原规则：**

```text
- **option_label**：按 A/B/C/D 顺序；每项到下一标签/下一题结束；重复标签 →
  ambiguous；缺标签 → incomplete。
```

**OD-01 变化：** 删除「V3 无条件按 A/B/C/D 发现 option 边界」的普遍规则；改为：

- **Path B**：Producer Artifact `options[]` = Option Segmentation Authority；V3 验证/规范化/拒绝/fail closed；**禁止** rediscovery。
- **Path A**：Native Resolver 确定性 role resolution 产出 option 边界（首次解析）。
- label 重复/缺失 → 仍 ambiguous / incomplete（校验结果，非 rediscovery）。

**原因：** Owner R-03/F-OD01-03；原规则与「禁 V3 rediscovery」在 Path B 直接冲突。

**变化后语义：** 见 §3.1；无两套 IR 语义标准。

### 5.5 `20_Document_Pipeline.md` §5.5 Resolved Span + granularity（约 `:308-324`）— CHANGE-4 + CHANGE-2

**原规则：**

```text
- `granularity` ∈ {line, line_character}（M1；table_cell/fragment 延后，见 00 §5）。
- line_ref 必须存在于该 source_version；line_character 的 start/end_offset 必须能唯
  一定位"同行多题答案/单行多选项"场景。
```

（Resolved Relation 示例 `sp-M1` 亦在本节，见 §6。）

**OD-01 变化：** 增加 provenance form 维度；table_cell option 子集延后解除；fragment 仍延后；form locator 分型（§4.1）；resolved ⇒ form 1..n。

**原因：** F-OD01-01/02/05/06；R-06。

**变化后语义：** granularity 与 form 正交；非 line form 不得伪造 line_ref。

### 5.6 `20_Document_Pipeline.md` §6.1 IR option `source_span`（约 `:365-369`）— CHANGE-2 + CHANGE-1

**原规则示例：** `options: {"A": {"source_span": {"span_id": "sp-Q1-A"}, "status": "resolved"}}`（示例 key 为 `sp-Q1-A`，**不是** `sp-<unit>.option.<label>`）。

**OD-01 变化：** 增加单链路权威语义：`options[].provenance`（输入证据）→ V3 verification/normalization → Frozen Resolved Span → IR `source_span`；冲突保留 conflict signal，不得静默覆盖。

**原因：** F-OD01-04 / R-04；OD-04 对齐。

**变化后语义：** IR source_span = Canonical 表达；非第二 authority。

### 5.7 `20_Document_Pipeline.md` §6.2 IR 完整性不变量（全节，尤 status 隔离）— CHANGE-2 + CHANGE-3

**原规则（摘）：** 8 条不变量；`semantic_status ∈ {ready, incomplete}`；**三层状态严格隔离** E ResolvedStatus ≠ F semantic_status ≠ G gate/decision。

**OD-01 变化：** 新 form / option 证据必须纳入不变量 4（blank/option/answer 映射闭合）与状态隔离：Provenance Resolution（E）≠ Option/Evidence Resolution ≠ F/G；degraded 不得直接写成 `ready` 或 auto Admission。

**原因：** R-07/R-08；F-OD01R-05 点名本节。

**变化后语义：** 状态层更严；禁止跨层搬运。

### 5.8 `20_Document_Pipeline.md` §7.2 步 1（约 `:454`）— CHANGE-3

**原规则：** 逐 content role 从 resolved span（line / line_character）确定性提取。

**OD-01 变化：** 提取源扩展到 OD-01 form 所定位 source slice；option leaf label/text 的 authority 分路径（§3.1）；禁止 Path B rediscovery。

**原因：** 新 form 后提取规则必须一致。

### 5.9 `20_Document_Pipeline.md` §7.3 Question `dedup_key`（约 `:523`）— CHANGE-1

**原规则：** type + own stem + own options（label order；label 重复 fail-fast）+ 排除列表。

**OD-01 变化：** **组合与 identity 语义不变**；仅澄清 own options 输入在 Path B 来自 verified Producer `options[]`，在 Path A 来自 Native 解析结果。

**原因：** 来源变更需声明；OD-01 不改 Question Core。

### 5.10 `10_Data_Model.md` §6.3 `source_span` JSONB — CHANGE-1 + CHANGE-2

**原规则：** JSONB 非 FK；应用层 provenance invariant（§8 2a–2d）。

**OD-01 变化：** 划界 JSONB 只承载可验证 provenance 结构扩展；对齐 `00 §5` JSONB 非目标；**不**自动授权 DDL。

### 5.11 `10_Data_Model.md` §8 不变量 2b/2c — CHANGE-2

**原规则：** line_ref（及 offset）∈ source lines；text_hash == slice hash。

**OD-01 变化：** 非 line form 的 locator 必须解析到可验证 source 实体/切片；**不得**伪造 line_ref；2c 按 form locator 切片 hash。

### 5.12 `50_Migration_Assets.md`（约 `:51` 表格行）— CHANGE-2 + CHANGE-3

**原规则：** 「图像/表格 bbox 定位能力 | 保留思想，重写 | source_figures（page/bbox/placement/source，IS-7）+ role 归属…」

**OD-01 变化：** option provenance 的 `table_cell` / `image_region`（`other` 实例）与该资产能力对齐；image_region 必须 figure identity + region，禁止伪造 line_ref。

**原因：** R-05/R-06；F-OD01R-05 点名 `50:51`。

### 5.13 全树检索后：确认无额外「直接受影响」业务条款

已检索 `Docs/V3_SPEC/**`：`ResolvedSpan` / `option` / `granularity` / `provenance` / `table` / `fragment` / `line_ref` / `options_lines` / `dedup_key` / `ResolvedRun`。

| 候选 | 是否纳入 diff | 理由 |
|------|---------------|------|
| `30_Task_LLM_Safety.md` | 否 | 无 option provenance / Resolved Span ontology 条款 |
| `40_Development_Rules.md` | 否 | 无直接相关强制条款（CR-001 测量条款不涉及） |
| `90` / `91` | 流程义务 | 不改规则；仅遵守 + 未来 §11 登记义务 |
| `README` 术语 | 否 | 不改 Question/Unit 词汇 |

**不修改（非目标）：** Gate 四层语义 · Admission · Question Core · QT→UT · P01–P25 · OD-02…G-02 · 历史重处理 · Migration policy · X3 · `fragment` 延后本身。

---

## 6. R-10 — 引用 / 坐标更正

### 6.1 `options_unresolved` 的准确 L0 coordinate

| 问题 | 更正 |
|------|------|
| 错误写法 | 「废止 `options_unresolved`」（无坐标，且暗示 L0 存在该字段） |
| **事实** | **`options_unresolved` 从未进入 L0 Frozen Spec**（tree `b3eeb3e9…` 无此字段） |
| Proposal 层出处 | D4 §4.2 logical shape；Proposal v2 §3.4/§4.2（**非 L0**） |
| 「废止」准确含义 | **不得引入 L0**；不得作为独立语义 fail-closed 载体 |
| **L0 真实 fail-closed / 状态坐标** | `20 §5.2` ResolvedStatus（`incomplete`/`ambiguous`/`missing` 等）· `20 §6.2` `semantic_status=incomplete` · `20 §6.2` 三层隔离 · Contract P04.4（`unresolved`/`INCOMPLETE`/`QC_FAIL`）· `10 §8` 不变量 |

### 6.2 `sp-M1` 章节坐标

| 错误 | 更正 |
|------|------|
| `sp-M1` = `20 §6.1` 示例 | **错误** |
| **正确** | **`sp-M1` = `20 §5.5` Resolved Relation 示例**（`20:336` 附近） |
| `20 §6.1` 示例 key | `sp-Q1-stem` / `sp-Q1-A` / `sp-Q1-answer`（`20:367-369`） |
| 代码构造 `sp-{unit_id}.option.{label}` | `backend/.../ir.py` `_content_span_id` — **代码，非 Spec** |

### 6.3 全文检索

已检索本 Proposal 与 CR-002：无其他 `sp-*.option.*` 冒充 Spec 示例；无其他把 `sp-M1` 写入 §6.1 的句子。

---

## 7. 四道门 Evidence / Status（R-03 + 硬性证据规则）

> 依据：`69 §5` Errata Gate（四道门）。**Status 只按证据填写。禁止**因 Proposal 写完 / Owner 同意 OD-01 / DSH 无阻塞 / 设计合理而标 PASS。

| Gate | Requirement（69 §5） | Evidence（本轮实况） | Status |
|------|----------------------|----------------------|--------|
| **Gate A — Identity Closure** | Identity 语义闭合；跨层 identity 不被 provenance form 破坏 | **无** OD-01 form 级 identity 测试；未跑全量回归 | **PENDING** |
| **Gate B — Legacy / Path B 对比** | 真实 corpus 上旧解析 vs Path B 可重复对比（exact/normalized/…/usable） | **无** option provenance form 语料对比；P04 调查 ≠ Gate B 对比实验 | **PENDING** |
| **Gate C — Safety Invariant Preservation** | C1 Source immutable · C2 LLM 无 Admission Authority · C3/C4 invalid/cross-source fail-closed · C5 span integrity · C6 replay identity | **未**就新 form 重新证明 C1–C6 | **PENDING** |
| **Gate D — Adapter Boundary** | Adapter = Contract Translator；禁第二事实来源 / 第二 Resolver / fuzzy / 自主生成 / 独立 semantic decision | 原则与 Path B「禁 rediscovery」一致，但**无**正式 evidence package | **PENDING** |

```text
Gate A: PENDING
Gate B: PENDING
Gate C: PENDING
Gate D: PENDING
四道门整体: NOT SATISFIED — CHANGE-4/5 不得发布 / 不得 re-freeze
```

---

## 8. 受影响层（R-04 覆盖 Native / Adapter / ResolvedRun / Canonical IR）

| Layer | 受影响 | 说明 |
|-------|--------|------|
| L0 `00` §5 | YES（CHANGE-4） | §5.1 |
| L0 `10` §4/§6.3/§8 | YES | §5.3/5.10/5.11 |
| L0 `20` §5.3/§5.5/§6.1/§6.2/§7.2/§7.3 | YES | §5.4–5.9 |
| L0 `50` 表格定位行 | YES | §5.12 |
| **Native（Path A）** | YES | segmentation 来源；ResolvedRun 产出 |
| **Adapter（Path B）** | YES | verify-only；禁 rediscovery |
| **ResolvedRun** | YES | 唯一消费入口保持 |
| **Canonical IR** | YES | 双路径汇聚；语义等价 |
| Gate 四层 **语义** | **NO** | 禁止改 |
| Admission 语义 | **NO** | 禁止改 |
| Question Core / vocabulary | **NO** | 禁止改 |
| DB Schema / 代码 / Preprocessing / Corpus | **NO** | 本轮禁改 |

**回归范围（登记；本轮不执行）：** form 全集 · 分型 locator 真实性（禁伪造 line_ref）· Path A/Path B 等价 IR · 禁 Path B rediscovery 负向 · dual resolution status 隔离 · degraded 不绕过 fail-closed · conflict signal · text_hash/2c · no double consumption · options_lines 保留 · dedup 组合不变。

---

## 9. Owner Approval（修订后；与 CR-002 一致）

```text
[ ] 1. 确认 R-01 判定：CR-002 = L1 candidate / NOT RELEASED；Governance Gap 已登记
[ ] 2. 批准 CHANGE-4（00 §5 / 10 §4 table_cell 子集放宽）范围
[ ] 3. 批准 CHANGE-5（20 §5.3 无条件 V3 option 边界规则删除/替换）+ Path A/B 语义
[ ] 4. 批准 form 分型 locator（禁止伪造 line_ref）
[ ] 5. 批准双层 Resolution（Provenance vs Option/Evidence）命名与 Schema 纪律
[ ] 6. 批准 degraded / fail-closed 关系（degraded 非后门）
[ ] 7. 钉死 char offset 编码单位；table_cell identity 形态；legacy 无 form 读取规则
[ ] 8. 确认 Gate A–D 全部 PENDING；四道门未过前不得 re-freeze
[ ] 9. 明确正式 L1 注册的合法路径（解除 Governance Gap）或书面接受 candidate 状态
[ ] 10. Freeze Order 仍 NOT ISSUED
```

```text
OD-01 as Frozen Spec = NOT EFFECTIVE
CR-002               = L1 candidate / NOT RELEASED / NOT REGISTERED
Re-freeze            = NOT EXECUTED
Phase 1              = NOT ENTERED
```

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` |
| Version | **v3**（R-01…R-10 reconciled） |
| Document Type | Decision Record（Proposal 载体） |
| Authority Level | **L2**（非 L0；非自创 L1-proposal） |
| Status | **DRAFT** |
| Effective Frozen Spec | UNCHANGED (`b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`) |
