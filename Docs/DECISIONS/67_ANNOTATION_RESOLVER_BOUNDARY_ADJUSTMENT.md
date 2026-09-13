# V3 Annotation/Resolver 边界调整方案

Status: Draft v2 — 对抗性审查后修订
Date: 2026-09-10
Predecessors: 65_PHASE_I5_SCOPE_FREEZE.md, 66_PHASE_I5_1_BOUNDARY_ANALYSIS.md

---

## 0. 核心约束

**本方案不改变 V3 的系统边界和数据流方向。** 不新增子系统，不删除已有模块，不修改 IRBuilder / Compiler / Gate / Admission 的任何逻辑。

但必须诚实说明：**Resolver 的内部职责发生根本性转变**——从"在源文本中搜索匹配结构位置"变为"验证外部声明的 Source 引用合法性"。这不是小改，是重写 `resolver.py` 的主体逻辑。之所以仍然可控，是因为 `ResolvedSpan`、`UnresolvedReference`、`ResolvedRun` 数据结构不变，下游消费方式不变。

V3 已验证的体系——Seal 不可变源、hash 完整性校验、IR 中间表示、Compiler 文本切片、Gate 门禁、Admission 入库——全部保持原样。

---

## 1. 问题诊断

### 1.1 当前管线

```
Source (Seal, 不可变)
  ↓
Annotation (LLM 输出语义标签，禁止携带行号)
  ↓
Resolver (代码用正则在源文本中搜索匹配)
  ↓
ResolvedSpan
  ↓
IRBuilder → Compiler → Gate → Admission
```

### 1.2 问题所在

Annotation 环节的 `FORBIDDEN_FIELDS` 禁止 payload 中出现 `line_refs`。这意味着 LLM 只能说"第 1 题有题干"，不能说"第 1 题的题干在第 7-8 行"。

Resolver 随后用正则（`is_question_start`、`option_tokens` 等）在源文本中搜索匹配。

**Phase I-4 已经证明**：layout evidence（font/size/bbox）对数学试卷的题号消歧率为 0%。Resolver 的正则搜索在简单测试用例上就全部失败（stem=ambiguous, options=incomplete, answer=missing）。

**根本原因**：Resolver 被要求用确定性规则解决一个本质上需要全文语义理解的问题。试卷格式天然存在学科差异、排版差异、OCR 噪声、答案表格式差异等无穷变体，正则无法穷尽。

### 1.3 已有证据

**硬实验证据**（V3 内部可控实验，可复现）：

| 证据 | 来源 |
|------|------|
| Layout evidence 对题号消歧率 0% | Phase I-4 实验 |
| Resolver 在简单用例上全部 UNRESOLVED | I-5-1 实测（Test 2） |
| `option_tokens()` 无法拆分同行多选项 | I-5-1 实测（Test 5） |
| 直接构造 ResolvedSpan → IRBuilder → Compiler 全链路可行 | I-5-1 实测（Tests 9/12/14） |

**参考性证据**（外部项目，未经 V3 管线验证）：

| 证据 | 来源 | 局限性 |
|------|------|--------|
| LLM 全文理解 + 结构标注可产出高质量 manifest | 预处理项目（319 units, 100% answer coverage） | 在**人工审核后**的文档上得到；预处理项目本身无严格文档和测试约束，不能直接作为 V3 生产依赖 |

预处理项目的价值是**证明了 LLM 结构理解这条路走得通**，不是**证明了具体实现可以直接复用**。

---

## 2. 设计原则

> **LLM 负责理解（这是什么、在哪里），代码负责验证（引用是否合法、能否进入下游）。**

这不是"让 LLM 写数据库"。V3 的核心原则——**LLM 不拥有事实写入权**——不变。LLM 产出的是结构声明（Structural Claim），代码负责校验声明的引用合法性，验证通过才转化为 `ResolvedSpan` 进入下游。

分工：

| 职责 | 谁做 | 说明 |
|------|------|------|
| 识别结构（题干/选项/答案/材料） | LLM | 语义理解，全文上下文 |
| 定位行号（哪行到哪行） | LLM | 基于语义理解的定位 |
| 校验行号合法性 | 代码 | 越界、空区间、hash 一致性 |
| 校验同 unit 内角色冲突 | 代码 | 同一题的 stem/options/answer 不重叠 |
| 构建 IR / 编译 / 门禁 / 入库 | 代码 | 现有流程，不变 |

**代码验证的边界**：代码能验证"引用是否指向合法的 Source 位置"，**不能**验证"这个位置的内容是否真的是题干/答案"。语义正确性由 LLM 标注质量和 Admission 人工确认共同保证（详见 §4.1）。

---

## 3. 改动范围

### 3.1 需要改的

**性质说明**：Annotation 中的 `line_refs` 是 LLM 对 Source 的**结构声明**（Structural Claim），不是最终事实。经过 Resolver 验证后才成为 `ResolvedSpan`。这个边界必须清晰：LLM 产出声明，代码验证声明，验证通过才进入下游。

#### A. Annotation 输入格式

**当前**：Annotation 的输入是纯文本（无行号前缀）。LLM 看不到行号，所以无法输出行号。

**改为**：输入源文本时附加行号前缀：

```
L001: 一、单项选择题
L002: 1. 原子的核式结构学说，是卢瑟福根据以下哪个实验或现象提出来的
L003: A. 光电效应实验
L004: B. 氢原子光谱实验
...
```

行号前缀增加约 5-8% 的 token 消耗。这是让 LLM 能引用行号的必要成本。

**影响范围**：AnnotationService 的调用方（输入构造逻辑）。

#### B. Annotation payload 格式

**当前**：`FORBIDDEN_FIELDS` 禁止 `line_refs`、`resolved_span`、`final_line_ids`、`corrected_line_ids`。

**改为**：允许 `line_refs`。每个 semantic unit 可以携带行号范围。

示例（调整后）：
```json
{
  "semantic_units": [
    {"unit_id": "Q1", "role": "stem", "question_label": "1", "line_refs": ["P1L002", "P1L003"]},
    {"unit_id": "Q1", "role": "answer", "answer_zone": "answer_table", "line_refs": ["P2L031"]}
  ]
}
```

`FORBIDDEN_FIELDS` 中移除 `line_refs`。其他禁字段（`resolved_span`、`final_line_ids`、`corrected_line_ids`）保持不变——它们属于 Resolver 的输出，仍然不应该出现在 annotation 中。

**需要新增**：`line_refs` 字段的格式校验（必须是非空字符串列表，每个元素符合 `P{page}L{line:03d}` 格式）。当前 `validate_annotation_payload()` 只检查 FORBIDDEN_FIELDS，不检查字段格式。允许 `line_refs` 后需要增加格式校验，否则非法格式的行号会在 Resolver 才被发现。

**影响范围**：`backend/app/domains/annotation/__init__.py`（FORBIDDEN_FIELDS 常量 + 格式校验逻辑）。

#### C. Annotation prompt

**当前**：prompt 要求 LLM 输出语义标签，不给行号。

**改为**：prompt 要求 LLM 在输出语义标签的同时，给出每段内容对应的行号范围（使用输入中的 L 前缀行号）。

**影响范围**：AnnotationService 的调用方（prompt 构造逻辑）。

#### D. Resolver 职责

**当前**：Resolver 是搜索器——拿着 annotation 的语义标签，用正则在源文本中搜索匹配位置。

**改为**：Resolver 是校验器——拿着 annotation 中 LLM 给出的行号，校验其引用合法性。

校验内容：
1. 行号是否越界（超过源文件行数）
2. 同一 unit 内不同角色的 span 是否重叠（见下文）
3. 行号对应的文本 hash 是否与 Seal 时一致
4. span 是否为空

**关于重叠检测**：只检查**同一 unit 内不同角色的重叠**——同一道题的 stem、options、answer 不应该指向重叠的行号范围。跨 unit 的重叠不做检查（composite 共享材料、共享答案表等合法场景需要跨 unit 重叠，区分合法/非法重叠需要语义理解，不属于 Validator 的职责）。跨 unit 的冲突由 Gate 和 Admission 环节处理。

**影响范围**：`backend/app/domains/resolver/resolver.py` 主体重写。`ResolvedSpan`、`UnresolvedReference`、`ResolvedRun` 数据结构不变。`reference.py` 的 `extract_targets()` 需要适配新 payload 格式（读取 `line_refs` 字段）。

### 3.2 不需要改的

| 模块 | 状态 |
|------|------|
| Seal（DocumentSourceVersion / DocumentSourceLine） | **不变** |
| IRBuilder | **不变** — 已验证能消费直接构造的 ResolvedSpan |
| Compiler | **不变** — 已验证能从 ResolvedSpan 切出正确文本 |
| Gate | **不变** — 校验逻辑不依赖 Resolver 的实现方式 |
| Admission | **不变** |
| 数据库 schema（表结构） | **不变** |

### 3.3 契约影响确认清单

实施前**必须**确认以下契约变化的影响：

| 确认项 | 说明 | 风险 |
|--------|------|------|
| Annotation hash 规则 | payload 新增 `line_refs` 字段后，hash 计算是否包含该字段？ | **高**：LLM 输出的行号可能有非确定性（两次调用行号微调），如果 hash 包含 line_refs，会破坏 annotation 幂等性 |
| Annotation identity projection | identity 投影是否包含 `line_refs`？ | **高**：同上，影响去重和幂等 |
| `line_refs` 格式校验 | 需要新增格式校验逻辑 | 中 |
| `extract_targets()` 适配 | 读取新 payload 格式 | 低 |
| 现有测试 | 哪些旧测试假设"annotation 无位置"，哪些 invariant 必须保留 | 中 |

**关于 hash/identity 的建议方案**：`line_refs` 参与 payload 的完整存储，但**不参与** identity hash 计算。identity 仍然基于语义标签（unit_id、role、question_label 等）。这样同一文档的重复标注（行号可能微调）仍然幂等，而行号变化通过 Resolver 验证来捕获。

---

## 4. 风险控制

### 4.1 代码验证的边界

必须明确区分两类验证：

**引用有效性（Reference Validity）**——代码可以确定性验证：
- 行号是否存在、是否越界
- hash 是否与 Seal 一致
- span 是否为空
- 同 unit 内角色是否重叠

**语义正确性（Semantic Correctness）**——代码**无法**验证：
- 这行内容是不是真的是题干？
- 这个答案是不是真的属于 Q1？
- 这段材料是不是真的属于 Q1-Q3？

LLM 可能把选项误标成题干——行号合法、hash 一致、文本非空，Resolver 全部通过。Gate 检查的是"stem 非空、answer 存在"——这是结构完整性，不是语义正确性。如果 LLM 标错了角色但内容非空，Gate 也不会拒绝。

**语义正确性由且仅由以下环节保证**：
- LLM 标注质量（prompt 设计 + 模型能力）
- Admission 环节的人工确认

**不要期望 Gate 或 Resolver 能捕获语义错误。** 它们能捕获的是引用非法、结构不完整、数据不一致——不是"内容标错了角色"。

### 4.2 人工审核在哪里？

Admission 前的 Gate 环节不变。通过 Gate 的数据进入 Admission，Admission 中保留人工确认步骤。**人工确认是语义正确性的最终防线。**

### 4.3 防线清单

| 防线 | 检查什么 | 能捕获什么 | 不能捕获什么 |
|------|---------|-----------|------------|
| `validate_annotation_payload()` | FORBIDDEN_FIELDS + `line_refs` 格式 | 格式非法的 payload | 语义错误 |
| Resolver | 行号越界、hash 一致、同 unit 重叠、空 span | 非法引用 | 语义错误 |
| Gate | stem 非空、answer 存在、角色完整 | 结构不完整 | 语义错误 |
| Admission | 人工确认 | 语义错误 | — |

### 4.4 `resolution_status = "exact"` 的语义说明

`"exact"` 在本方案中的含义是：**LLM 提出的 Source 引用已经过 Resolver 的引用有效性验证（行号存在、hash 一致、范围合法），不是指 Resolver 通过文本搜索发现该位置。**

下游代码（IRBuilder、Compiler）不区分 Resolver 发现的 span 和 Annotation 提供的 span——它们消费的是同一个 `ResolvedSpan` 数据结构，校验逻辑相同。

### 4.5 Annotation 的上下文要求

LLM 进行结构标注时，**必须获得足以完成当前结构判断的上下文**。不能简单地把文档切块后让 LLM 独立理解每个块——很多结构关系天然跨区域（题目在前面、答案表在后面、综合题材料和子题的关系、跨页题目等）。

当前阶段：小文档（如试卷）可以一次送入 LLM 全文理解。

大文档（数百 KB）的分段策略属于后续优化，不在本次范围内。但实施时不能默认"全文理解"自动成立——必须确认 LLM 实际获得的上下文范围是否足够。

### 4.6 回退方案

新旧管线通过配置开关共存，不直接替换：

- **旧管线**（Resolver 搜索模式）：保留现有代码路径，作为回退选项
- **新管线**（Annotation 行号 + Resolver 校验模式）：新增代码路径

用同一批文档分别走新旧管线，比较 resolved rate 和编译质量。数据说话，不预设结论。

---

## 5. 与 Phase I-5 的关系

Phase I-5 实验验证的是：**预处理项目的 manifest 输出能否作为 V3 的合法输入。**

本方案验证的是：**V3 自己的 Annotation 环节能否直接输出带行号的结构标注。**

两者共享同一个架构判断（LLM 理解 + 代码验证），但实施路径不同：

| | Phase I-5 (预处理项目) | 本方案 (V3 内部) |
|---|---|---|
| 结构信息来源 | 外部预处理项目的 manifest | V3 自己的 Annotation 环节 |
| 行号来源 | manifest 的 line 范围 | LLM 在 annotation 中直接输出 |
| 适用场景 | 已有预处理结果的文档 | 所有新文档 |
| 依赖 | 预处理项目（非正式） | 无外部依赖 |

两者可以并行推进，互不阻塞。

---

## 6. 实施建议

### 第一步：修改 Annotation 输入格式 + FORBIDDEN_FIELDS + 格式校验

输入附加行号前缀，允许 `line_refs`，新增格式校验。3 个文件。

### 第二步：修改 Annotation prompt

要求 LLM 输出带行号的结构标注。

### 第三步：改写 Resolver 为 Validator

保留模块位置和数据结构，重写内部逻辑。新旧代码路径通过配置开关共存。

### 第四步：端到端测试

用 I-5-1 已有的测试数据验证全链路：
Seal → Annotation (LLM 输出行号) → Resolver (校验) → IRBuilder → Compiler → Gate

### 第五步：与旧管线对比

用同一批文档分别走新旧管线，比较 resolved rate 和编译质量。根据数据决定是否切换默认路径。

---

## 7. 一句话总结

**V3 的结构信息由语义生产者（LLM）提供；Resolver 不再负责从 Source 猜测结构，而负责将结构声明解析为对 Sealed Source 的有效引用，并执行引用合法性验证。语义正确性不由 Resolver 证明，由 LLM 标注质量和 Admission 人工确认共同保证。下游的 IRBuilder、Compiler、Gate、Admission 全部不变。**
