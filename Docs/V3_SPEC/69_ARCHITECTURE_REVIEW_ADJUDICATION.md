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

### B5-3: Identity semantics — OPEN（禁止提前关闭）

**不能直接从 P6 推导 "line_refs 必须/不必进入 identity hash"。**

P6 的 `logical_execution_key` 标识"要执行什么逻辑任务"，不是"执行产生了什么结果"。
`input_hash` 是输入侧身份，不是输出侧。

需要定义并分析以下 Identity 层之间的关系（1:1 / 1:N / N:1）：

```text
Task Identity
Logical Execution Identity
Annotation Identity
Binding Claim Identity
Resolved Result Identity
IR Identity
Compile Identity
Candidate Identity
```

核心问题：**同一 logical execution 下，如果 Source Binding Claim 不同，如何保证不产生两个不同的持久化结果？**

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
| OQ-1 | B5-3 Identity 分层：Annotation Identity / Binding Claim Identity / Logical Execution Identity 的关系 | Architecture | 67 的 Errata |
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

#### Gate A — Identity Closure

必须完成 B5-3 Identity Semantics 裁决，明确 Semantic Annotation Identity /
Source Binding Claim / Resolved Evidence 三者之间的身份关系及 hash / dedup 规则。

特别需要证明：
- A1: 不同 `line_refs` + same semantic annotation → 不无意义地制造不同 Annotation identity
- A2: 真正不同的 semantic content → different identity，不能因 line_refs 被剥离而错误合并
- A3: ResolvedSpan 的 Source identity 不得被 Annotation identity 覆盖

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
67 号：CONDITIONALLY ACCEPTED
Frozen Spec：UNCHANGED
Errata：BLOCKED BY OQ-1 + Gate B/C
Path B：VALIDATED EXPERIMENTAL PATH
```

### 七、裁决依据

- Step 0.5 盲测：Case A 100% / Case C 100% / Case B 94.7%（LLM 可产出高质量 line_refs）
- Phase I-4：layout evidence 消歧率 0%（旧 Resolver 结构性失效）
- I-5-1：21/21 ready IR（Path B 全链路技术可行）
- 69 号 B5-3：Identity semantics OPEN，禁止提前关闭
- 核心原则：不因旧 Spec 的 FORBIDDEN 就拒绝已被实验支持的架构方向；
  不因 Path B 21/21 成功就跳过 OQ-1
