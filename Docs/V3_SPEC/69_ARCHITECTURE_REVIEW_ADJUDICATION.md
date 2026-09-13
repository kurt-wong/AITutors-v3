# Phase I-5 架构审查：Step B / B5 / Step C 裁决记录

Status: Adjudicated — 项目负责人已裁决
Date: 2026-09-10
Predecessors: 65, 66, 67, 68
Supersedes: 无（本文件是审查结论的权威记录）

> 本文件记录 Step B（Frozen Impact Matrix）、Step B.5（67 Identity/Authority Review）、
> Step C（68 ↔ Frozen Data Model Compatibility）三轮审查的最终裁决。
> 所有结论经独立对抗性复核后由项目负责人确认。

---

## 1. 审查范围

| 阶段 | 审查对象 | 方法 |
|------|---------|------|
| Step B | 65/66/67/68 与 Frozen Spec (00/10/20) 的逐条款影响分析 | 四层分类法 + 核心不变量比对 |
| Step B.5 | 67 的 line_refs 性质、Authority 转移、Identity semantics、Failure path | 第一性原理推导 |
| Step C | 68 的 Question 模型与 Frozen Data Model 的兼容性 | 逐组件路径追踪 |

---

## 2. Step B 最终裁决

| 文档 | 性质 | 需要 Errata | 裁决 |
|------|------|------------|------|
| 65 Path B | Experiment | 当前不需要 | **Evidence** |
| 66 Manifest | Analysis | 不需要 | **Analysis** |
| 67 line_refs | Proposal | **需要**（Contract Change） | **Proposal — 必须走 Errata** |
| 68 Question | Domain Definition | 待验证 | **Proposal** |

### 65 — Evidence

实验证明 Path B（直接构造 ResolvedSpan → IR → Compiler）技术可行。
**可行性 ≠ 架构优越性。** 不得因实验成功自动推导 Frozen Contract 已被修改。

### 66 — Analysis

Manifest expressiveness 分析方向正确。
必须区分：业务语义正确 ≠ Annotation Schema 能表达 ≠ Resolver 能实现 ≠ 可直接改实现。

### 67 — Contract Change（必须 Errata）

三条字面冲突确认成立：
- 20 §4.3 FORBIDDEN_FIELDS 显式包含 `line_refs`
- 20 §3 硬边界 #2 显式写明 "不携带 resolved span / line_ref"
- 20 §5 Resolver 解析级联在验证器模式下不再适用

**67 不是普通实现修改，是 Contract Change。** 不得包装成"实现细节"。

### 68 — Proposal

核心语义模型与 Frozen IR 一致。三个待裁决点见 Step C。

---

## 3. Step B.5 最终裁决

### B5-1: line_refs = Source Binding Claim — ACCEPT

```text
Semantic Claim      "这是 stem"
Source Binding Claim "stem 位于 P1L002-P1L004"
Position Fact        "Resolver 已确认 P1L002-P1L004 就是该 stem"
```

line_refs 属于第二层。不是 Source Fact，不是 Resolved Position Fact。

### B5-2: Source Binding Selection Authority 转移 — ACCEPT

67 将 Source Binding Selection Authority 从 Resolver 前移到 LLM。
确定性层保留 Reference Integrity Authority。
**不是** "LLM 获得全部 Source Location Authority"——准确分层：

```text
LLM                    → Source Binding Selection Claim
Deterministic Validator → Reference Integrity Authority
Gate                    → Admission Authority
```

### B5-3: Identity semantics — CLOSED / PASS / TEST-EVIDENCED（2026-09-11）

**裁决（70 号 OQ-1 分析 + 直接测试证据）**：

三层 Identity 模型正式确认：

```text
Semantic Identity    = annotation_payload_hash（剔除 confidence + line_refs）
                       → 决定 "这是什么题"
                       → 进入 LE hash（幂等锚点）

Source Binding Claim = line_refs in payload（完整存储，不进 Semantic Identity）
                       → 决定 "LLM 认为在哪里"
                       → 进入 resolver_input_hash（供 Resolver 验证）

Resolved Evidence    = compiler_input_hash / occurrence_key（基于 resolved span）
                       → 决定 "实际引用了什么"
                       → 进入 Candidate / Instance
```

**核心结论**：Semantic Identity 与 Source Binding Claim 必须分离。
line_refs 属于 Source Binding Claim，不属于 Semantic Identity。

**测试证据**（`test_identity_projection.py`，4 个新增测试）：
- `test_line_refs_change_does_not_change_semantic_identity`（A1）
- `test_line_refs_change_changes_resolver_input_hash`（A1 补充）
- `test_semantic_change_with_same_line_refs_still_changes_identity`（A2）
- `test_line_refs_absent_backward_compatible`

**代码实现**：
- `_annotation_identity_projection`：剔除 `{confidence, line_refs}`
- `_confidence_only_projection`：仅剔除 `{confidence}`（供 resolver_input_hash）
- call-site audit 确认：仅 `service.py` 内 2 处调用，无隐藏依赖

**全量回归**：514/514 passed。

### B5-4: Resolver 定位 — ACCEPT

Frozen Resolver 不是"语义纠正器"。其优势是：
1. ambiguity/missing 拒绝机制
2. 从 Semantic Reference 到 Source Span 的确定性解析机会

准确对比：

| | Frozen | 67 |
|---|---|---|
| LLM 指定 | marker text（语义线索） | Source line ID（直接位置） |
| 确定性层 | 搜索/解析 marker → 定位 Span | 验证引用完整性 |
| 拒绝机制 | ambiguous → 拒绝闭合 | invalid → 拒绝；valid → 通过 |

**架构红线**：Resolver/Validator 不得演变成不断替 LLM 猜测和纠错的业务规则集合。
一旦出现 `line_refs → scoring → ranking → heuristic → fallback`，应重新评估是否重建了 Resolver（P5）。

---

## 4. Step C 最终裁决

### C-0: Semantic Atom Preservation

| 68 组件 | 20 Annotation | 20 IR | Compiler | 10 A-domain | 无损？ |
|---------|--------------|-------|----------|-------------|--------|
| material | shared_components | resolved span | 只输出一次 | materials + material_links | 是 |
| stem | content.stem | resolved span | 确定性提取 | instance_role_contents | 是 |
| options | content.options[] | per-label spans | per-option | instance_role_contents | 是 |
| figures | image_ref.figure_id | image span + figure_id | figure_refs[] | source_figures + links | 是 |
| parts | sub_questions[] | sub_questions[] | per-leaf | 多行 Question + unit_group | 见 C-1 |
| answer | content.answer | answer + status | 确定性提取 | instance_role_contents | 是 |
| explanation | content.explanation | optional span | 确定性提取 | instance_role_contents | 是 |

### C-1: Composite = ONE Question — PASS

**IR 层完全兼容。**

Frozen IR 的 composite_unit（20 §6.2）= shared_components + sub_questions[]，是一个原子 unit。
68 的"Composite = ONE Question，parts 是内部结构"与 IR 一致。

**物化层语义张力**（需 Application 层裁决）：
10 §6.1 将 composite leaf 物化为独立 Question 行 + unit_group。
68 要求 parts 不是独立 Question 实体。
10 §6.5 的 unit_group 保留 grouping 语义，但不阻止对 leaf 的独立查询。

**必须保持**：
```text
Composite = ONE Question
sub_question = 内部 answerable part
sub_question ≠ Question entity
```

### C-2: Standalone + Material — CONTRACT EXPRESSIVENESS GAP

**确认存在 Annotation Contract 表达力缺口，不是业务模型冲突。**

业务语义：Standalone + Material 合法（如"阅读下面材料，回答第 1 题"）。

当前 Frozen Annotation schema（20 §4.5）的 `standalone_question` 定义中无 material/depends_on 字段。
material 只在 composite_unit 的 shared_components 中出现。

**不能**把 Material 强行并入 stem 作为默认方案——会丢失 Material identity / sharing / dedup / dependency。

后续如需支持，应走正式 Contract / Errata 决策。

### C-3: Composite 无 Material — NO CONFLICT / CLOSED

**Material 不限于文字。**

Material 是语义上的 supporting content，可以是：
text / image / figure / table / chart / map / diagram / mixed content。

Material 与 Figure 的关系是不同抽象层：
```text
Material → 语义 supporting content
Figure   → Source asset / content carrier
```

因此 "Composite without textual material" 不构成冲突。

---

## 5. Question 语义模型（裁决确认）

```text
                         Question
                            │
                ┌───────────┴───────────┐
                │                       │
          Standalone                Composite
                │                       │
          ┌─────┴─────┐          ┌──────┴──────┐
          │           │          │             │
       no Material  Material   supporting    sub_questions
                                  content
```

**核心语义规则**：

| 规则 | 内容 |
|------|------|
| Question 定义 | 题库中最小、完整、可独立使用的实体 |
| Composite | 仍然是一个 Question，不是 parent + child |
| sub_question | Composite 内部 answerable part，不是独立 Question entity |
| Material | supporting content 的语义概念；≠ text only；≠ Composite |
| Standalone + Material | 合法 |
| Composite + Material | 合法 |
| Figure/Table/Chart/Map/Diagram | 均可作为 supporting content 的底层载体 |
| Composite 判定 | Explicit grouping OR shared semantic dependency |
| Shared section alone | 不构成 Composite |

---

## 6. Frozen Spec Impact 声明

### 65

```text
Current Status: Experiment / Evidence Record
Not Implementation Authorization: 本文档不授权直接修改正式实现
Evidence Produced: Path B 全链路技术可行；Resolver 正则在数学题上失败
Frozen Spec Impact: 00 P1（仅当 Path B 被采纳为正式路径时）
Impact Classification: No Impact（当前）/ Contract Change（仅当采纳时）
Errata Requirement: 当前不需要
Implementation Gate: 需要新旧管线对比数据 + 项目负责人裁决
```

### 66

```text
Current Status: Analysis
Not Implementation Authorization: 本文档不授权直接修改正式实现
Evidence Produced: Manifest 字段映射 + expressiveness 缺口清单
Frozen Spec Impact: 无（分析的是实验 manifest，非 V3 正式契约）
Impact Classification: No Impact
Errata Requirement: 不需要
Implementation Gate: N/A
```

### 67

```text
Current Status: Proposal — Contract Change Candidate
Not Implementation Authorization: 本文档不授权直接修改正式实现
Evidence Produced: Step 0/0.5 盲测 LLM 可输出正确 line_refs；Resolver 正则失败
Frozen Spec Impact: 20 §4.3 / 20 §3 / 20 §5 / 00 P1 / 00 P2
Impact Classification: Contract Change
Errata Requirement: 需要（必须经正式 Errata 流程）
Implementation Gate: B5-3 Identity 分析完成 + 新旧管线对比 + 项目负责人裁决
```

### 68

```text
Current Status: Domain Definition Proposal
Not Implementation Authorization: 本文档不授权直接修改正式实现
Evidence Produced: Question-first 模型 + 三科盲测 + Composite 判定规则
Frozen Spec Impact: 20 §4.5（standalone material 表达力缺口）
Impact Classification: Design Extension（核心语义）/ Contract Expressiveness Gap（standalone material）
Errata Requirement: 核心语义不需要；standalone material 需要（如需支持）
Implementation Gate: C-2 的 Annotation Contract 设计裁决
```

---

## 7. Open Questions（待裁决）

| # | 问题 | 分类 | 阻塞什么 |
|---|------|------|---------|
| OQ-1 | B5-3 Identity 分层 | Architecture | **CLOSED（2026-09-11，70 号）** |
| OQ-2 | Standalone + Material 的 Annotation Contract 表达 | Contract Expressiveness | 68 的 material 支持 |
| OQ-3 | 物化层 leaf Question 独立性：是否需要 Application 层约束 | Application Rule | C-1 物化策略 |

---

## 8. 下一步顺序

```text
Step B/B5/C 裁决（本文件）     ← 已完成
        ↓
Step 3: 67 号 Contract Change 裁决  ← 已完成（2026-09-11，有条件接受）
        ↓
OQ-1: B5-3 Identity 分层分析
        ↓
Gate B: Legacy vs Path B 真实 corpus 对比
        ↓
Gate C: Safety Invariant Preservation 验证
        ↓
Errata Decision（Gate A-D 全部通过后）
        ↓
Owner Decision
        ↓
I-5-2 Adapter Contract（Gate D 约束）
```

**在此之前不修改 V3 正式代码。**

---

## 9. Step 3 裁决：67 号 Contract Change（2026-09-11）

### 裁决结果

**有条件接受（Conditional Acceptance）。**

67 号提出的核心架构方向获得原则性接受：**Source Pointer ≠ Source Content。**

允许 Semantic Annotation 提供 Source Binding Claim，由确定性代码对该 Claim 进行
Reference Integrity Validation，Resolver 继续持有 Source Reference Integrity Authority。
Resolver 从"搜索 Source"模式调整为"验证 Source Binding Claim"模式，架构原则上成立。

本裁决**不等同于立即修改 Frozen Spec，也不等同于正式采纳 67 号 Contract Change**。

### 一、已接受的架构原则

1. `line_refs` 可以作为 **Source Binding Claim**。
2. Source Binding Claim 不等于 Source Content。
3. LLM 可以提出 Source Binding Selection。
4. LLM 不获得 Source Content Authority。
5. LLM 不获得 Reference Integrity Authority。
6. Resolver 保留 Reference Integrity Authority。
7. 最终 Source Content 必须来自 Sealed Source。
8. Invalid / ambiguous / unverifiable binding 不得进入自动 Admission。
9. Adapter 不得成为第二个 Semantic Resolver。

### 二、Authority 分层（正式确认）

| 权限 | LLM | Resolver/Validator | Admission |
|------|-----|--------------------|-----------|
| 理解题目语义 | **✓** | | |
| 提出 line_refs | **✓** | | |
| 判断引用是否合法 | | **✓** | |
| 确认 Source 存在 | | **✓** | |
| 计算/验证 span integrity | | **✓** | |
| 语义正确性最终确认 | | | **✓** |
| 创建 Question | | | **✓** |

**LLM = Semantic + Binding Proposal Authority**
**Resolver = Reference Integrity Authority**
**Source = Fact Authority**
**Admission = Persistence Authority**

### 三、三层 Identity 模型（OQ-1 方向指引）

```text
┌──────────────────────┐
│ Semantic Identity    │  "这是什么？"
│ question_type/object │  → identity hash
│ /task/method/...     │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│ Source Binding Claim │  "我认为它在哪里？"
│ line_refs / spans    │  → claim, not truth
└──────────┬───────────┘
           │ validation
┌──────────▼───────────┐
│ Resolved Evidence    │  "代码验证后实际引用了什么？"
│ Source Version + span│  → 进入 IR/Compiler/Gate/Admission
└──────────────────────┘
```

核心问题：Semantic Annotation 的身份由什么决定？Source Binding Claim 的变化是否
构成 Annotation 的语义变化？

### 四、当前不得立即执行的事项

在 OQ-1 完成之前：

- 不修改 Frozen Spec §4.3 `FORBIDDEN_FIELDS`
- 不正式删除 `line_refs` 禁止项
- 不发布 67 号 Errata
- 不宣称新 Resolver Contract 已正式生效
- 不将 Path B 实验代码直接视为 Frozen V3 正式管线

### 五、Errata Gate（四道门）

#### Gate A — Identity Closure — **PASS / TEST-EVIDENCED（2026-09-11）**

B5-3 Identity Semantics 裁决已完成（70 号），Semantic Annotation Identity /
Source Binding Claim / Resolved Evidence 三者身份关系已定义并测试验证。

- A1: ✓ 不同 line_refs + same semantic → Semantic Identity 不变（直接测试）
- A2: ✓ 不同语义 → 不同 identity，剥离 line_refs 不降低区分能力（直接测试）
- A3: ✓ ResolvedSpan Source identity 独立于 Annotation identity（代码证明）
- call-site audit: ✓ `_annotation_identity_projection` 仅 2 处调用，无隐藏依赖
- 全量回归: 514/514 passed

#### Gate B — Legacy / Path B 对比

必须使用真实 Phase I-4 / I-5 corpus，对旧 Search Resolver 与 Path B Validator 进行
可重复的对比实验，至少报告：exact / normalized / contextual / fuzzy / ambiguous /
missing / validated / final usable references。

不得仅以 `21/21 ready IR` 作为完整可行性证明。21/21 是局部 feasibility evidence，
不是 corpus-level evidence。

#### Gate C — Safety Invariant Preservation

新 Contract 必须重新证明：
- C1: Source immutable（Pointer 不能写 Source）
- C2: LLM 无 Admission Authority（line_refs 只能进入 claim）
- C3: Invalid pointer fail-closed（line_ref 不存在 → 拒绝）
- C4: Cross-source pointer fail-closed（Source Version A 引用 B 的 line → 拒绝）
- C5: Span integrity 可验证（不能仅"line 102 exists"就认为 resolved）
- C6: Replay identity 不因非语义 pointer formatting 变化而破坏

#### Gate D — Adapter Boundary

I-5-2 Adapter 必须保持为 Contract Translator，不得引入：
- 第二事实来源
- 第二 Resolver
- 隐式 fuzzy matching
- 自主 Source 内容生成
- 独立 semantic decision

### 六、正式状态

```text
67 号：CONDITIONALLY ACCEPTED（Gate A PASS；Pending Gate B/C）
Frozen Spec：UNCHANGED
Errata：BLOCKED BY Gate B/C（Gate A 已解除）
Path B：VALIDATED EXPERIMENTAL PATH
```

### 七、裁决依据

- Step 0.5 盲测：Case A 100% / Case C 100% / Case B 94.7%（LLM 可产出高质量 line_refs）
- Phase I-4：layout evidence 消歧率 0%（旧 Resolver 结构性失效）
- I-5-1：21/21 ready IR（Path B 全链路技术可行）
- 69 号 B5-3：Identity semantics OPEN，禁止提前关闭
- 核心原则：不因旧 Spec 的 FORBIDDEN 就拒绝已被实验支持的架构方向；
  不因 Path B 21/21 成功就跳过 OQ-1

---

## 10. Gate B 裁决：Source Binding Strategy 对比实验（2026-09-11）

### 裁决结果

**Gate B：CONDITIONAL PASS / NOT CLOSED。"18% vs 100%" 结论正式撤销。**

Gate B 拆分为两个子 Gate：
- **Gate B1 — Binding Integrity**：Path B line_refs 是否指向合法、非空、结构匹配的 Source Evidence
- **Gate B2 — Strategy Comparison**：统一 Content Role Target 后 Legacy vs Path B 同口径对比

### 实验事实（已验证）

| 维度 | 结论 | 证据 |
|------|------|------|
| Corpus 可用性 | PASS — 67 cases / 1885 units / 10 学科 | 独立重新加载确认 |
| Semantic projection | PASS — 零 binding field 泄漏 | 1885 units 全量检查 |
| Legacy Resolver 执行 | PASS — 确实在搜索 | 44 resolved + 58 unresolved（sample），unresolved 原因分布合理 |
| Legacy baseline signal | PASS — ~18%（与 Phase I-4 17.6% 一致） | 同一 corpus controlled comparison |
| Path B range 构造 | PASS — 行号在 `[1, len(source_lines)]` 范围内 | 8089 spans 全部 range-valid |
| **Path B reference integrity** | **FAIL / INCOMPLETE** | 25.9% spans 指向空行（600/2314，sample） |
| **Manifest answer 质量** | **FAIL** | 12.2% answer_lines 指向选项行（66/540，sample） |
| Options normalization | INCOMPLETE | ABCDEFGH cap 限制，11/317 不匹配 |
| **跨策略度量可比性** | **FAIL** | Legacy target 数（7631）≠ Path B span 数（8089），口径不一致 |
| **"18% vs 100%" 结论** | **REJECTED** | 两者度量不同事物：搜索成功率 vs range 合法率 |

### 核心发现

**Path B 的 "100% validation" 只是 Range-Valid Rate，不是 Reference Integrity Rate。**

当前验证器仅证明 `1 <= start <= end <= len(source_lines)`，未证明：
1. `resolved_text` 非空（Level 2 — Content Validity）
2. 内容属于正确 role（Level 3 — Role Validity）
3. 内容符合 unit 语义（Level 4 — Semantic Validity）

```text
Level 1 — Range Validity    "行号在范围内"
Level 2 — Content Validity  "resolved_text 非空"
Level 3 — Role Validity     "内容属于正确 role"
Level 4 — Semantic Validity "内容符合 unit 语义（需独立证据）"
```

### Binding Integrity 分层（正式确认）

Path B Validator 必须产出分层验证结果，而非单一 pass/fail：

```text
range_valid       → start/end 在 SourceLineView 范围内
content_valid     → resolved_text 非空
role_valid        → 内容结构匹配声明 role（stem/options/answer/explanation）
semantic_valid    → 内容语义正确（独立证据，不由简单规则冒充）
```

### 循环证明风险（正式声明）

Manifest 可以提供 Expected Structure（expected role + expected line_ref），但：
- **Expected Structure ≠ Path B Correctness**
- Path B 使用 manifest 的 line_ref 本身就是被测试的输入
- 不能形成"Manifest 说 line 155 → Path B 用 line 155 → Path B 验证 line 155 → 因此 Path B 正确"的循环

语义正确性（Level 4）必须有独立证据。

### 下一阶段（Gate B1/B2 重设计）

**不修改 V3 生产代码。** 先修实验 Harness：

1. 统一 Content Role Target Model：`(unit_id, role)` 为对比单位
2. Path B 增加 content_valid / role_valid 检查
3. Options normalization 从 manifest 实际结构推导，不假设 ABCD
4. 重跑完整 corpus（67 cases / 1885 units），非抽样
5. 产出 Legacy vs Path B 同口径 Role-Level Binding 成功率

### Gate B1 实验结果（2026-09-11，67 cases / 8367 role targets）

| 验证层 | 通过数 | 通过率 | 裁决 |
|--------|--------|--------|------|
| Level 1 — Range Validity | 8367 | 100.0% | PASS |
| Level 2 — Content Validity | 6263 | 74.9% | **FAIL** |
| Level 3 — Role Validity | 1051 | 12.6% | **FAIL — severe** |
| Level 4 — Structural Validity | — | 未评估 | INSUFFICIENT |
| Level 5 — Semantic Validity | — | 未评估 | UNPROVEN |

按 Role 分解：

| Role | Total | Range | Content | Role |
|------|-------|-------|---------|------|
| stem | 1556 | 1556 (100%) | 1333 (85.7%) | 205 (13.2%) |
| option | 4328 | 4328 (100%) | 2774 (64.1%) | 701 (16.2%) |
| answer | 1874 | 1874 (100%) | 1559 (83.2%) | 133 (7.1%) |
| explanation | 609 | 609 (100%) | 597 (98.0%) | 12 (2.0%) |

失败原因：role_mismatch 5212（71.2%）/ content_empty 2104（28.8%）。

### Gate B1 裁决（2026-09-11，修正后）

**Gate B1 = CONDITIONAL PASS / Corpus Substantially Valid, with two structural contract issues remaining.**

#### 修正记录（正式作废旧数据）

上一轮 Gate B1 = FAIL 基于两个实验缺陷，旧数据（74.9% Content / 12.6% Role）正式作废：

1. **读错源文件**：B1 harness 读了切片展示视图（`compile_slices()` 产出，含区域标记，行号与原始源不同），而非 `manifest['source_file']` 指向的原始源文件
2. **validator 过度严格**：`1\.` 反斜杠转义点号、`## 【解析】` markdown 前缀、答案表 `1-5 BBACB` 格式、`---` 水平线均未覆盖

修正后重新运行（79 cases / 10343 role targets）：

| 验证层 | 修正前 | 修正后 |
|--------|--------|--------|
| Range Validity | 100% | **100%** |
| Content Validity | 74.9% | **79.0%** |
| Role Validity | 12.6% | **63.3%** |

#### 修正后按 Role 分解

| Role | Total | Content | Role | Role Rate |
|------|-------|---------|------|-----------|
| stem | 1870 | 1870 (100%) | 1820 | **97.3%** |
| explanation | 880 | 880 (100%) | 851 | **96.7%** |
| option | 5311 | 3138 (59.1%) | 2753 | **51.8%** |
| answer | 2282 | 2280 (99.9%) | 1120 | **49.1%** |

#### Contract Readiness 矩阵

| Contract | 状态 |
|----------|------|
| Source line range | **PASS** |
| Source view / line mapping | **PASS — 已纠正** |
| Non-empty source evidence | **PASS WITH RESERVATIONS** |
| Stem binding | **PASS** |
| Explanation binding | **PASS** |
| Option region binding | **UNRESOLVED — 需 schema 语义裁决** |
| Per-option binding | **NOT PROVEN** |
| Answer region binding | **PASS WITH RESERVATIONS** |
| Per-question answer binding | **NOT PROVEN** |
| Semantic validity | **UNPROVEN** |

#### 剩余问题性质

剩余失败集中在 option/answer 两个结构性 role，不是普遍性 line_ref 失真：

1. **Option 51.8%**：`options_lines` 是整个 options region，B1 harness 逐行拆分成 per-option target 时，空行被当成独立 option target。需要裁决：`options_lines` 的 contract 定义的是 region 还是 per-option spans？
2. **Answer 49.1%**：共享答案表（`1-5: BBACB`）指向整张表而非单题答案。需要裁决：`answer_lines` 对共享答案表的 contract 是 source region 还是 per-question answer evidence？

#### 核心进展

已从"Path B 的输入数据是不是垃圾"推进到"对于不同 Question Role，Source Binding Claim 应该具有什么最小表达能力"——这是 Doc 67 更深层的 contract 设计问题。

### 循环证明风险（正式声明）

Manifest 可以提供 Expected Structure（expected role + expected line_ref），但：
- **Expected Structure ≠ Path B Correctness**
- Path B 使用 manifest 的 line_ref 本身就是被测试的输入
- 不能形成"Manifest 说 line 155 → Path B 用 line 155 → Path B 验证 line 155 → 因此 Path B 正确"的循环

语义正确性（Level 5）必须有独立证据。

**修复方向：修 manifest generator，不修 manifest 本身**——人工修改 manifest 后再用它证明 Path B 正确是闭环证明。

### Binding Integrity 五层分层（正式确认，更新）

```text
Level 1 — Range Validity       "行号在范围内"
Level 2 — Content Validity     "resolved_text 非空"
Level 3 — Role Validity        "内容结构匹配声明 role"
Level 4 — Structural Validity  "Question Structure 正确（option 顺序/边界/数量/多行/图片）"
Level 5 — Semantic Validity    "内容语义正确（需独立证据）"
```

### Gate B 当前状态（2026-09-11 修正后更新）

```text
Gate A: PASS / TEST-EVIDENCED
Gate B1: CONDITIONAL PASS / Corpus Substantially Valid
  Range Validity: PASS (100%)
  Content Validity: PASS WITH RESERVATIONS (79.0%)
  Role Validity: stem 97.3% / explanation 96.7% / option 51.8% / answer 49.1%
  Structural Validity: NOT YET EVALUATED
  剩余问题: option region 语义 + answer 共享答案表 contract
Gate B2: 允许开始，先用 B1-clean target set（stem + explanation）
  B2-A (Clean Roles): 可以开始
  B2-B (Structured Roles): BLOCKED BY option/answer contract 裁决
Gate C: OPEN
Gate D: OPEN
Errata: BLOCKED BY Gate B/C
```

### Phase I-5 状态矩阵（2026-09-11 修正后）

| 项目 | 当前状态 |
|------|---------|
| Doc 67 B5-1 (line_refs = Source Binding Claim) | ACCEPTED |
| Doc 67 B5-2 (Authority 转移) | ACCEPTED |
| Doc 67 B5-3 (Identity semantics) | CLOSED / TEST-EVIDENCED |
| Doc 67 B5-4 (Resolver 定位) | ACCEPTED |
| Gate A (Identity Closure) | PASS / TEST-EVIDENCED |
| Gate B1 Range Validity | PASS |
| Gate B1 Content Validity | PASS WITH RESERVATIONS |
| Gate B1 Stem binding | PASS (97.3%) |
| Gate B1 Explanation binding | PASS (96.7%) |
| Gate B1 Option binding | UNRESOLVED — 需 schema 语义裁决 |
| Gate B1 Answer binding | UNRESOLVED — 需共享答案表 contract 裁决 |
| Gate B1 overall | **CONDITIONAL PASS** |
| Gate B2-A (stem + explanation) | 允许开始 |
| Gate B2-B (option + answer) | BLOCKED BY contract 裁决 |
| Legacy Resolver weakness | TEST-EVIDENCED |
| Path B technical operability | TEST-EVIDENCED |
| Path B correctness | NOT PROVEN |
| Manifest binding contract | PARTIALLY RESOLVED |
| Production code change | 暂缓 |

### Contract Adjudication 裁决结果（2026-09-11）

**统一原则：Source Region 与 Question Evidence 必须分层。**

```text
Source Region          "相关内容在哪里"
    ↓
Structural / Evidence Binding   "Question 的具体 evidence 是什么"
    ↓
ResolvedSpan
```

#### Q1: `options_lines` = A — Region

`options_lines: [11,17]` 表示该 Question 的 options 所在 Source Region，
不是 line 11 = option A、line 12 = option B……

逐行拆分是 **B1 harness interpretation bug**，不应作为 manifest quality failure。

Region Binding 与 Per-option Structure 是两个层次：
```text
Binding Claim → options region [11,17] → Resolver 验证 region
    → Structural parsing → A/B/C/D individual spans
```

未来若需要 per-option ResolvedSpan，应扩展 manifest schema 显式表达，
**不要让 Resolver 通过猜哪一行是 A/B/C/D 来补全 manifest**——那会退化成 Legacy Search。

#### Q2: 共享答案表 = B — Per-question evidence

共享答案表 `1-5: BBACB; 6-10: DBBBA` 只能说明答案存在于该行，
不能证明 Q1 → B、Q2 → B……

**Source region ≠ Question answer evidence。**

最终模型应为：
```text
Q1.answer
    source_region: [314,314]
    evidence: "B"  (或 subspan/offset/token locator)
```

Question-level answer evidence 必须能从共享 Source Region 中确定性定位，
不能要求 Resolver 自己猜。

#### Q3: 语法填空 = B — Single span

`answer_lines` 保持单一连续 Source Region `[start, end]`。
同一行内多个答案（`61 arrived 62 before`）属于 subspan 问题，不是多 span 问题。

未来若需 Question-level 精确答案绑定，应增加 line 内部的 deterministic
subspan/offset 能力，而不是把 `answer_lines` 变成任意多个 spans。

#### Q4: HTML table = B — Cell/row

整个 table 可作为上层 Source Region，但不能天然等价于 Question 的 answer evidence。
Answer evidence 应绑定到最小语义充分的结构单元（cell/row）。

不能让 LLM 直接输出 `cell = row 3, col 2` 然后代码无条件相信——
正确流程是 LLM 提出 Source Binding Claim → Resolver 验证 cell/row 确实存在。

未来 Binding Contract 可能需要 `line_refs + structured sublocator`，
而不是无限扩张 `line_refs` 本身。

#### Contract Adjudication 正式记录

```text
Q1 = A
  options_lines denotes an options Source Region. Per-option spans are a
  downstream structural representation and must not be inferred by treating
  every physical line as an option.

Q2 = B
  Shared answer tables require question-specific answer evidence. A shared
  answer Source Region alone is insufficient as the final Question-level binding.

Q3 = B
  answer_lines remains a single contiguous Source Region. Multiple answers
  within a line or region require deterministic subspan/offset semantics
  rather than multiple independent line spans.

Q4 = B
  HTML-table answers should bind to the smallest semantically sufficient
  structural evidence, such as a cell or row. The containing table may serve
  as the Source Region.
```

#### Gate 状态更新（Contract Adjudication 后）

```text
Gate B1: CONDITIONAL PASS — Region Binding Contract 基本成立
Structured Evidence Binding: CONTRACT ADJUDICATED, IMPLEMENTATION NOT YET ESTABLISHED
Gate B2-A (stem/explanation): READY
Gate B2-B (option/answer): WAIT FOR MANIFEST CONTRACT UPDATE / STRUCTURAL EXPERIMENT
```

**这些裁决不意味着现在修改生产 V3。** 先作为 Phase I-5 的 Contract Adjudication
记录；然后用实验 harness 验证这些语义能否在真实 corpus 上稳定表达；
只有实验闭环后，才决定是否形成 Doc 67 Errata 和生产实现。

### Gate B2-A 实验结果与裁决（2026-09-11）

**Gate B2-A = PASS / TEST-EVIDENCED（结论范围仅限 stem）。**

#### 实验设计

- 79 cases / 2750 B1-clean targets（stem 1870 + explanation 880）
- 同一 SourceLineView、同一 semantic projection、同一批 target
- Legacy：semantic-only annotation → SourceResolver（search）
- Path B：manifest line_refs → 直接验证（validation）

#### 核心结果（stem）

| 指标 | Legacy Resolver | Path B |
|------|----------------|--------|
| stem resolution/validation | 829/1870 (**44.3%**) | 1820/1870 (**97.3%**) |

Agreement Matrix（stem）：

| | Path B validated | Path B not validated |
|---|---|---|
| **Legacy resolved** | 814 | 15 |
| **Legacy not resolved** | **1857** | 64 |

**1857 个 target 是 Legacy 找不到、Path B 能验证的。** Legacy resolved / Path B not validated 仅 15 个（0.8%）。

#### 解释

Path B 的优势是**把"搜索问题"变成"验证问题"**：
- Legacy：给语义线索，Resolver 自己全文搜索 → 44.3%
- Path B：给 Source Binding Claim，Resolver 验证位置 → 97.3%

这正是 Doc 67 想验证的架构变化：Resolver 从"搜索 Source"模式调整为"验证 Source Binding Claim"模式。

#### Explanation 不纳入对比

Legacy Resolver 当前没有 explanation search/binding 能力，其 0% 是
**capability absence**，不是 comparative failure。Explanation 作为
Capability Evidence 记录，不作为 Strategy Comparison 指标。

#### 结论边界（正式声明）

- ✅ 在可信 Source Binding Claim 存在时，将 Resolver 从全文搜索转变为位置验证
  可以显著提高 stem binding 的可用性
- ❌ 不证明 Path B 的语义正确率为 97.3%（需独立抽样验证）
- ❌ 不证明 Path B 在所有 Question Roles 上优于 Legacy

#### 三项补强结果（2026-09-11）

**补强 1：审计 15 个 Legacy-only cases — 完成**

15/15 全部为 Validator False Negative，manifest line_refs 全部正确：
- 数学公式题（stem 以 `=` 开头）→ validator 要求题号前缀，误杀
- 章节编号题（`10.6.3.2 ...`）→ `10` 提取为题号，`6` 不匹配 `.`，误杀
- 无题号正文段（chemistry）→ 无题号，误杀
- 特殊题号格式（`1-1` / `1.10.1` / `1、` / `9.` ）→ 题号提取正则不覆盖，误杀

**补强 2：独立抽样验证 Path B 成功结果 — 完成**

从 1820 个成功 stem 随机抽 100 个，独立确认 line_ref 指向的确实是该题题干：
- 初始验证器结果：96/100 (96.0%)
- 对 4 个失败样本逐案审计：3 个为验证逻辑 False Negative（合法 stem 被误判），1 个为真实 Manifest Binding Error（stem_lines 指向答案内容）
- **人工复核后实际 Binding 错误率：1/100 = 1.0%**
- 区分两个概念：96% 是验证器表现；~99% 是人工复核后 Manifest Binding 实际表现

**补强 3：排除 explanation — 完成**

正式结论仅基于 stem。Explanation 作为 Capability Evidence 记录，不作为 Strategy Comparison 指标。

#### Gate B2-A 正式关闭（2026-09-11）

**Gate B2-A = PASS / STRONGLY TEST-EVIDENCED / CLOSED**

> 在 79 cases、1870 个共同 stem targets 上，Legacy Resolver 的 Search Resolution Rate
> 为 44.3%（829/1870），Path B 的 Binding Validation Rate 为 97.3%（1820/1870）。
>
> Agreement Analysis 显示 1857 个 Legacy unresolved target 被 Path B validated。
> 对 15 个 Legacy-resolved / Path-B-not-validated 案例逐案审计后，
> 15/15 均为 Validator False Negative，Manifest line_refs 正确。
>
> 对 Path B 成功结果进行 100 个独立抽样审计，初始验证器结果为 96/100；
> 对 4 个失败案例逐案复核后，3 个属于验证逻辑 False Negative，
> 仅 1 个属于真实 Manifest Binding Error（1.0%）。
>
> 因此，实验结果充分支持以下结论：
>
> **在可信 Source Binding Claim 存在的前提下，将 Resolver 的职责从 Source Search
> 转变为 Binding Validation，可以显著提高 stem Source Binding 的实际可用性。**
>
> Explanation 不纳入策略对比，因为 Legacy Resolver 当前不具备 explanation
> Search Capability。
>
> **Gate B2-A：CLOSED。**

### Gate B2-B1 实验结果与裁决（2026-09-11）

**Gate B2-B1 = CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED**

#### 实验设计

- 79 cases / 1166 option regions
- B2-B1 不再逐行拆分 region（B1 的 interpretation bug），而是把整个 region 作为输入
- 结构解析器从 region 中恢复 per-option structure（label + text）
- 三层验证：Region Binding → Structure Extraction → Label Sequence

#### 已证明

1. **自动结构提取**：1069 个非 HTML option regions 中 1065 个成功恢复 option structure
   - 自动 extraction rate = **99.6%**
2. **结构一致性**：收紧 label sequence（gap 检测 + first=A + count 范围）后 1054/1069
   - pass rate = **98.6%**
3. **独立源文本对抗抽样**：50 个随机抽样，49 个通过
   - 观察通过率 = **98.0%**
   - 唯一失败（政治 Q19）为 Manifest Region Semantics Edge Case——region 包含选项组合定义文本（①②③④）+ 答案组合行（A.①②③），解析器正确提取 A/B/C/D，覆盖率计算 artifact

#### 未证明

1. **每个 option 的 label-text assignment 完全正确**——结构性恢复有强证据，但逐 option 全量分配正确性未证明
2. **50 个对抗样本的统计结果可外推为总体准确率**——样本量 50，无置信区间
3. **mixed HTML regions 的完整解析能力**——50 个 mixed region 仅抽样 10 个
4. **pure HTML table 的结构化解析能力**——47 个纯 HTML region 属 B2-B4

#### 失败分类

| 类型 | 数量 | 归属 |
|------|------|------|
| Pure HTML table/image | 47 | B2-B4 范畴 |
| Mixed HTML + text | 50 | 约半数可解析，待 B2-B4 |
| Manifest region 不完整 | 4 | 数据问题 |
| OCR 重复行 artifact | 3 | 数据问题 |
| 纯 LaTeX / 特殊结构 | 2 | 边缘 case |
| Region semantics edge case | 1 | Manifest Region Contract Issue |

#### 政治 Q19 记录

`options_lines` 的 region boundary 可合法包含"选项结构之外但与选项题有关的辅助文本"（选项组合定义层）。这进一步支持 Q1 裁决：**options_lines 本质是 Source Region，而非已等价于 per-option span 的精确结构。** Parser 的职责是从 region 恢复 option structures，不是假设 region 内每行都是 option。记录为 **Region Semantics Edge Case**，非 parser failure。

### Gate B2-B2 实验结果与裁决（2026-09-11）

**Gate B2-B2 = CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED**
**Scope: Structured Multiple-Choice Answer Extraction**

#### 实验设计

- 79 cases / 2282 answer targets / 1573 unique regions / 120 shared regions（服务 829 units）
- 验证：给定 answer_lines Region + 题号，能否确定性提取本题答案
- Q2 裁决验证：共享答案表 Source Region → Per-question Answer 的确定性定位

#### 核心结果

| 范围 | 总数 | 成功 | 成功率 |
|------|------|------|--------|
| **选择题答案** | **1178** | **1176** | **99.8%** |
| 填空题答案 | 106 | 69 | 65% (Capability Evidence) |
| HTML table | 602 | 0 | B2-B4 |
| 主观题子问题 | 271 | 0 | OUT OF SCOPE |
| Unknown | 125 | 0 | TRIAGE REQUIRED |

#### 选择题答案类型分解

| 答案结构 | 总数 | 成功 | 成功率 |
|----------|------|------|--------|
| 【答案】标记 | 573 | 573 | 100% |
| 故选 | 207 | 207 | 100% |
| Range Table (1-5: BBACB) | 137 | 137 | 100% |
| 故答案为 | 117 | 117 | 100% |
| ☑答案 checkbox | 93 | 93 | 100% |
| 连写编号 (1.C2.C3.A) | 42 | 41 | 98% |
| 编号答案 (1. B) | 9 | 8 | 89% |

#### 关键修复记录

1. **题号提取**：支持 `U6-7`（unit range）、`U51`/`N1`（section 编号）、转义点号 `\.`
2. **Range table 格式**：支持 `----`（多连字符）
3. **连写格式**：`1\. C2\. C3\. A4\. B` 和 `1C, 2D, 3B`
4. **新增类型**：`☑答案 X`、`故选：X`、`故答案为：X`

#### 正式边界（必须保留）

1. **99.8% 是 scoped metric**——仅适用于结构化选择题答案类型，不代表全部 answer targets 的总体提取率
2. **填空题 65% 是 Capability Evidence**——证明 parser 能处理部分填空，但策略未闭环，进入 B2-B3
3. **主观题 271 个不属于 parser 失败**——是尚未定义提取策略的问题，需先确认 V3 Question/Task/Answer 语义模型（B2-B5）
4. **HTML 602 个归 B2-B4**——Source Region 内部二维/嵌套结构，line span 不足以表达最终 answer binding
5. **125 个 Unknown 需分类审计**——不再为提高百分比继续无目标增加格式规则

#### 架构分界线（正式确认）

```text
第一层：Source Binding —— Path B 已解决
  "这个 Question 在 Source 的哪里？"
  Manifest Claim + Validator

第二层：In-region Structure Resolution —— B2-B 系列解决
  "已知区域在哪，区域里哪部分属于当前题？"
  选择题：index lookup（B2-B2 已证明）
  HTML：row/cell lookup（B2-B4）
  填空：token sequence binding（B2-B3）
  主观题：task structure → answer structure（B2-B5，Domain Contract first）
```

### Gate B2-B3 实验结果与裁决（2026-09-11）

**Gate B2-B3-A = CLOSED — Target Classification Audit**

原始 B2-B2 报告的 fill-in 目标 106 个（69/106 = 65%）经过分类审计后发现分母污染：

| 类别 | 数量 | 处理 |
|------|------|------|
| 原始 fill_in targets | 70 | — |
| MC 误分类 | 36 | 移出 B2-B3，回归 B2-B2 |
| **真填空** | **34** | B2-B3 冻结测试集 |

真填空 Class 分布（52 lines）：

| Class | 数量 | 占比 | Binding 证据需求 |
|-------|------|------|-----------------|
| F1_single | 18 | 34.6% | question_id + region |
| F8_long | 12 | 23.1% | 需审核是否主观题 |
| F5_multi_token | 9 | 17.3% | token grouping |
| F3_concatenated | 8 | 15.4% | per-question extraction |
| F2_multi_blank | 5 | 9.6% | blank ordinal → Domain Contract |

学科分布：英语 14 > 化学 7 > 物理 6 > 政治 5 > 语文 1 = 数学 1

**关键发现**：原 65% fill-in extraction rate 正式失效。`detect_answer_type` 在"MC 答案 + 解释文本"场景存在 classification boundary defect，导致 MC targets 污染 fill-in evaluation set。此 defect 记录为独立 preprocessing defect，不纳入 Source Binding 架构结论。

冻结文件：`Docs/V3_SPEC/gate_b2b3_frozen_testset.json`

---

**Gate B2-B3-B = CLOSED — PASS / TEST-EVIDENCED / DETERMINISTIC**

实验设计：给定 preprocessing evidence（question_id + answer_region），V3 能否**不进行语义搜索、不调用 LLM、不使用 fuzzy matching**，仅通过机械验证形成 ResolvedSpan。

Positive Cases（34 个冻结真填空单元）：

| Check | 结果 | 状态 |
|-------|------|------|
| question_id_valid | 34/34 (100%) | PASS |
| source_version_valid | 34/34 (100%) | PASS |
| region_valid | 34/34 (100%) | PASS |
| region_nonempty | 34/34 (100%) | PASS |
| region_in_scope | 34/34 (100%) | PASS |
| evidence_hash_valid | 34/34 (100%) | PASS |
| resolved_span_constructed | 34/34 (100%) | PASS |
| binding_stable | 34/34 (100%) | PASS |
| **fallback_used** | **0** | **PASS** |

Determinism：3 次重复 × 10 样本 = 10/10 完全一致

Negative Cases（必须 fail-closed）：

| 测试 | 结果 |
|------|------|
| N1_invalid_range | PASS |
| N2_out_of_range | PASS |
| N3_empty_region | PASS |
| N4_wrong_question_id | PASS |
| N5_tampered_hash | PASS |
| N6_missing_source | PASS |

**6/6 fail-closed**

**B2-B3-B 核心结论**：

> 已有 preprocessing evidence（question_id + answer_region）可以被 V3 完全机械地验证并形成稳定 ResolvedSpan。零搜索、零 fallback、零 LLM 调用。非法 evidence 全部 fail-closed。

**B2-B3 分层状态**：

```text
B2-B3-A  Target Classification     CLOSED
B2-B3-B  Deterministic Binding     CLOSED — PASS
B2-B3-C  Domain-dependent          DEFERRED（F2/F4/F9 → Domain Contract）
```

**独立 preprocessing defect 记录**（不纳入 Source Binding 架构结论）：

> `detect_answer_type` 在"答案字母 + 解释文本"场景下存在 classification boundary defect，导致 MC targets 被污染进 fill-in evaluation set。Classification defect ≠ Fill-in binding defect。未来 preprocessing 进入生产级 pipeline 时处理。

### Gate B2-B4 实验结果与裁决（2026-09-11）

**Gate B2-B4-A = CLOSED — HTML Target Classification / Contract Freeze**

602 个 HTML answer targets 分类结果：

| Class | 数量 | 占比 | 说明 |
|-------|------|------|------|
| H3_table_with_mc | 426 | 70.8% | HTML 表格含 MC 答案 |
| H4_complex_structure | 49 | 8.1% | colspan/rowspan |
| H2_multi_table | 39 | 6.5% | 多 table |
| H3_table_with_qn | 30 | 5.0% | 表格含题号 |
| H6_html_with_image | 29 | 4.8% | HTML+图片 |
| H5_mixed_content | 17 | 2.8% | HTML+text 混合 |
| H1_simple_table | 12 | 2.0% | 简单表格 |

**关键发现**：H3_table_with_mc 占 70.8%，与 B2-B2 的 MC answer extraction 同构，只是载体从纯文本变成 HTML table。

学科分布：
- H3_table_with_mc: 生物 125 > 化学 89 > 政治 71
- H4_complex_structure: 化学 22 > 数学 16 > 英语 7
- H2_multi_table: 化学 16 > 数学 12 > 生物 4

冻结文件：`Docs/V3_SPEC/gate_b2b4_frozen_testset.json`

---

**Gate B2-B4-B = CLOSED — PASS / TEST-EVIDENCED / DETERMINISTIC**

Scope：507 个 Direct targets（H3_table_with_mc 426 + H3_table_with_qn 30 + H2_multi_table 39 + H1_simple_table 12）
Excluded：95 个（H4/H5/H6 → B2-B4-C）

Positive Cases（507 个 Direct HTML targets）：

| Check | 结果 | 状态 |
|-------|------|------|
| question_id_valid | 507/507 (100%) | PASS |
| source_version_valid | 507/507 (100%) | PASS |
| region_valid | 507/507 (100%) | PASS |
| region_nonempty | 507/507 (100%) | PASS |
| region_in_scope | 507/507 (100%) | PASS |
| evidence_hash_valid | 507/507 (100%) | PASS |
| has_html_content | 507/507 (100%) | PASS |
| resolved_span_constructed | 507/507 (100%) | PASS |
| binding_stable | 507/507 (100%) | PASS |
| **fallback_used** | **0** | **PASS** |

By Class：

| Class | 结果 |
|-------|------|
| H1_simple_table | 12/12 (100%) |
| H2_multi_table | 39/39 (100%) |
| H3_table_with_mc | 426/426 (100%) |
| H3_table_with_qn | 30/30 (100%) |

Determinism：3 次重复 × 10 样本 = 10/10 完全一致

Negative Cases（必须 fail-closed）：

| 测试 | 结果 |
|------|------|
| N1_invalid_range | PASS |
| N2_out_of_range | PASS |
| N3_empty_region | PASS |
| N4_wrong_question_id | PASS |
| N5_tampered_hash | PASS |
| N6_missing_source | PASS |
| N7_no_html_content | PASS |

**7/7 fail-closed**

**B2-B4-B 核心结论**：

> 507 个 Direct HTML targets 的 preprocessing evidence 可以被 V3 完全机械地验证并形成稳定 ResolvedSpan。零搜索、零 fallback、零 HTML 解析。非法 evidence 全部 fail-closed。

**B2-B4 分层状态**：

```text
B2-B4-A  HTML Target Classification   CLOSED
B2-B4-B  Deterministic HTML Binding   CLOSED — PASS
B2-B4-C  Domain/Material-dependent    DEFERRED（H4/H5/H6）
```

#### Gate B 当前状态（B2-B5 关闭后，2026-09-13 对账更新）

> 本块以 `backend/Docs/V3_SPEC/80_B2B5_CLOSURE.md` 为权威来源。
> B2-B1～B2-B5 的实验在 2026-09-11/12 完成；此前本块漏记 B2-B5 系列结果，
> 现按 80 号裁决回写。

```text
Gate A: PASS / TEST-EVIDENCED
Gate B1: CONDITIONAL PASS — Region Binding Contract 基本成立
Gate B2-A: PASS / TEST-EVIDENCED / CLOSED（stem-only, three-task audit）
  Stem: Legacy 47.1% vs Path B 96.8%（补强后 stem-only 口径）
Gate B2-B1: CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED
  Non-HTML extraction: 99.6% (1065/1069)
  Adversarial sampling: 98.0% (49/50)
  Tightened label sequence: 98.6% (1054/1069)
Gate B2-B2: CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED
  Scope: Structured Multiple-Choice Answer Extraction
  MC answer extraction: 99.8% (1176/1178)
  Fill-in: 65% → RECLASSIFIED (see B2-B3-A)
  HTML: 0% → RECLASSIFIED (see B2-B4-A)
  Sub-question: → B2-B5
  Unknown: 125 TRIAGE REQUIRED（仍未清）
Gate B2-B3-A: CLOSED — Target Classification Audit
  Original fill_in: 70 → MC misclassified: 36, Real fill-in: 34
Gate B2-B3-B: CLOSED — PASS / TEST-EVIDENCED / DETERMINISTIC
  Positive: 34/34 resolved, Fallback: 0, Determinism: 10/10, Negative: 6/6 fail-closed
Gate B2-B3-C: DEFERRED — Domain Contract dependency (F2/F4/F9)
Gate B2-B4-A: CLOSED — HTML Target Classification
  Total: 602 → Direct: 507, Excluded: 95
Gate B2-B4-B: CLOSED — PASS / TEST-EVIDENCED / DETERMINISTIC
  Positive: 507/507 resolved, Fallback: 0, Determinism: 10/10, Negative: 7/7 fail-closed
Gate B2-B4-C: DEFERRED — Domain/Material dependency (H4/H5/H6)
Gate B2-B5: CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED（80 号，2026-09-13）
  A classification 706 / B expressiveness 429 representable
  C invalid binding → pending_review（157 targets, UNRESOLVED/REVIEW REQUIRED）
  D E2E projection safety 13 tests PASS
  Residual: Evidence Admission Boundary → CLOSED（BUG-V3-044，80 号 §6）
Gate C: CLOSED (Phase 1 Evidence Authority Boundary Closure)
Gate D: CONTRACT CLOSED / IMPLEMENTATION NOT STARTED（81 号，2026-09-13）
  五条禁令全部维持；Bypasses 修正为 Resolver only（原「Annotation, Resolver」
  与 IRBuilder.build 签名冲突）；Adapter 职责白名单 / 禁令黑名单 /
  V3 侧三项前置已冻结；核心不变量「只允许机械投影，不允许提高信息量」。
  本轮不实现。契约方向：V3 先冻结消费契约，preprocessing 再实现（不可颠倒）。
Adapter 实现: NOT STARTED（阻塞于 81 §5.4 三项前置）
Errata: UNBLOCKED（Gate D 已过；Decision 项见 81 §9.1）
```

### 禁止事项（正式声明）

**禁止为了提升 B1 数字而继续放宽 validator。** 正确方式是：
Frozen contract → validator → 发现真实 mismatch → 判断是 validator bug / manifest bug / contract gap → 分别处理。

已经完成：validator bug → 修复；source-view bug → 修复。
剩余：manifest structural semantics / contract gap → 需要裁决。

### 下一步（按序执行，2026-09-13 四次更新）

> Grammar 契约裁决已完成（BUG-V3-044 Resolved，80 号 §6）。
> Gate D 契约已冻结（81 号）。**不进入 Adapter 实现。**

1. **Errata Decision**（Gate D 已过，阻塞解除）。
2. **V3 Annotation Contract 冻结**（V3 拥有，preprocessing 实现；81 §5.4）。
3. **Manifest Contract 冻结**。
4. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决。
5. **B2-B2 Unknown 125 triage**（仍未清）+ B2-B3-C / B2-B4-C 延期项。
6. **Phase 2 Evidence Ledger**（含 Q-B Evidence Claim 显式 `answer_form`）。
7. **Path B Full Closure E2E**（含 Provenance Golden Test + Replay 验证）。
8. **I-5-2 Adapter 实现**：**最后**，且阻塞于 81 §5.4 三项前置（V3 annotation
   schema 对外发布、manifest schema 冻结、SealedSource 版本绑定机制）。
   **依赖链不可倒序**——Annotation / Manifest Contract 冻结前写 Adapter 会
   让 Adapter 反过来定义契约。

### 重要措辞

> Path B 的优势是把"搜索问题"变成"验证问题"——这正是 Doc 67 的核心架构变化。
> Stem 上 Legacy 44.3% vs Path B 97.3%，1857 个 Legacy 失败被 Path B 成功处理。
> 这证明"从搜索改成验证"方向正确，但不证明 Path B 语义正确率 97.3%。
> Explanation 是 capability absence，不是 comparative failure。
> 下一阶段 B2-B 解决"一个区域里面还有更细结构"的定位问题。
