# Question 结构定义与 Composite 判定规则

Status: Revised — 对抗性审查后修订
Date: 2026-09-10
Predecessors: 65_PHASE_I5_SCOPE_FREEZE.md, 66_PHASE_I5_1_BOUNDARY_ANALYSIS.md, 67_ANNOTATION_RESOLVER_BOUNDARY_ADJUSTMENT.md
Context: Step 0.5 盲测后，从 Question-first 第一性原理重新定义结构模型

---

## 1. 什么是完整 Question

本项目是以 Question 为核心的题库系统。预处理阶段需要识别的不是"文本片段"，而是**可以作为独立题库对象存在的完整 Question**。

### 1.1 定义

> **Question 是题库的最小完整使用单元。** 它包含完成理解、作答和后续教学所需要的全部组成部分。

### 1.2 组成结构

```
Question
├── 前置材料 / 共同条件（可选）
├── 题干（stem）
├── 选项（options，可选——选择题才有）
├── 配图 / 表格（可选）
├── 小问（sub-parts，可选——综合题才有）
├── 标准答案（answer）
└── 详解（explanation，可选）
```

### 1.3 完整性规则

| 组件 | 教师版要求 | 说明 |
|------|-----------|------|
| 标准答案 | **必须存在** | 缺失答案 = Question 不完整的重大异常 |
| 作答内容 | **必须存在** | 普通题表现为 stem；Composite 由 material + parts 共同构成 |
| 详解 | 可选 | 某些选择题无详解是合法的；后续可由 LLM 补充 |
| 选项 | 可选 | 填空题、解答题无选项 |
| 前置材料 | 可选 | 存在本身不决定 Composite；Composite 由 §2 判定规则决定 |
| 小问 | 可选 | 仅 Composite 有；是内部结构，非独立实体 |

### 1.4 关键约束

- **"缺少详解"不能作为 Question 不完整的依据。**
- **"缺少标准答案"是教师版 Question 完整性的重大异常。**
- Question 内部的"小问"是组成结构，**不是独立的 Question 实体**。

---

## 2. Composite Question 定义

### 2.1 核心原则

> **Composite Question 是一个 Question，不是 parent + child Question。**

不存在"父题"和"子题"这套实体关系。只存在一个完整 Question，其中可能包含若干小问。

正确模型：

```
一个完整 Question
├── 共同材料 / 前置条件
├── 小问 A
├── 小问 B
├── 小问 C
├── 答案
└── 详解
```

错误模型（不存在）：

```
父题 Question
├── 子题 Question 1
├── 子题 Question 2
└── 子题 Question 3
```

### 2.2 判定规则（OR 关系）

一组内容是否应作为 Composite Question，有两条独立的判定路径：

**规则 A：试卷显式规定**

试卷明确将若干小题组织为一个整体，例如：
- "阅读以下材料，解答1—3题"
- "回答下列问题"
- "结合材料，完成下列各小题"

即使每个小题单独也能解答，**仍然必须作为一个 Composite Question**。"能够独立解答"不能推翻试卷明确规定的 grouping。

**规则 B：Question 完整性规则**

试卷未显式规定，但实际结构中若干小题共同依赖相同的前置材料、条件、图表或上下文。离开这些前置内容后，单独的小题不能构成完整的题库对象。

共同依赖必须是 **Question-level 的实质性依赖**，不是文本邻近关系。通用说明、答题须知、整卷注意事项等与具体 Question 无实质依赖的上下文不构成 Composite 依据。

```
实验背景
实验装置
实验条件
实验数据表
      ↓
1. ...
2. ...
3. ...
```

此时应识别为一个 Composite Question。

**判定逻辑**：

```
试卷显式 grouping  OR  共同依赖结构  →  Composite Question
```

两条路径不互相覆盖，任一成立即为 Composite。

### 2.3 关键约束

- **"独立可解答"不是拆分 Composite 的充分条件。**
- Composite 内部的小问边界必须被显式表达，不能要求下游从行范围中自行推导。
- Composite 的答案可能是共享答案表（多道题共用一个表格），也可能是分别对应的独立答案。

---

## 3. stem / options 边界定义

### 3.1 stem 的定义

> **stem 是题干语义区域**——题目提出问题、给出条件的文本部分。

不包括选项。选项是独立的结构角色。

### 3.2 正确的结构分离

```
下列说法正确的是：          ← stem
A. xxx                     ← options
B. xxx                     ← options
C. xxx                     ← options
D. xxx                     ← options
```

```
stem_lines: [7, 8]
options_lines: [9, 12]
```

### 3.3 对盲测结果的修正解读

Step 0.5 Case C 中，ground truth 把整个题目区域（含选项）都算 stem，LLM 把选项分离出来。**LLM 的分离更符合 Question 结构语义。** ground truth 的定义不够精确。

---

## 4. 对 Step 0.5 盲测结果的重新审核

### 4.1 Case A（数学）：84/84 = 100%

全部字段精确匹配。无争议。

### 4.2 Case B（地理）：Composite grouping 错误

LLM 输出 34 units，ground truth 19 units。

**这不是粒度差异，是结构识别错误。** 试卷将共享材料的题目组织为 Composite Question，LLM 将其拆分为独立 unit，违反了 Composite 判定规则 A。

需要评估的指标：
1. LLM 是否正确识别了每个小问？→ 需要单独验证
2. LLM 是否正确识别了小问属于同一个 Composite？→ **失败**
3. LLM 是否正确识别了共同材料？→ 需要单独验证
4. LLM 是否正确关联了答案和详解？→ explanation 19/19 = 100%

### 4.3 Case C（物理）：stem/options 边界 + 共享答案表

- answer_lines 24/24 = 100%：共享答案表的 Question-level association 完全正确
- explanation 24/24 = 100%
- options 20/20 = 100%
- stem 19/24 = 79.2%：5 个 partial 是 ground truth 的 stem 定义不够精确导致的，**LLM 的分离更正确**

---

## 5. 对 Manifest Expressiveness 的影响

### 5.1 Composite 内部小问边界

当前 manifest 的 composite unit：

```json
{
  "unit_id": "U1-2",
  "unit_type": "composite_question",
  "material_lines": [17, 18],
  "questions_lines": [17, 25],
  "stem_lines": null,
  "answer_lines": [525, 525]
}
```

`questions_lines=[17,25]` 是一个整体范围，没有表达内部小问的边界。如果下游需要知道"第 1 小问在哪里、第 2 小问在哪里"，manifest 必须提供这个信息。

**需要增强**：manifest 应表达 composite 内部每个小问的结构位置。

### 5.2 共享答案表的 Question-level association

当前 manifest：

```json
Q1: "answer_lines": [472, 472]
Q2: "answer_lines": [472, 472]
...
Q8: "answer_lines": [472, 472]
```

8 道题指向同一行，但没有表达"Q1 的答案是表格中的哪个值"。

盲测证明 LLM 能正确建立这种关联。但 manifest 没有保存这个关联结果。

**需要增强**：manifest 应保存 Question-specific answer reference（指向 Source 中的具体位置/结构入口），而不是复制 answer value/text。Source 是唯一事实来源，Manifest 只表达引用关系。

### 5.3 stem/options 边界

当前 manifest 的 `stem_lines` 包含整个题目区域（含选项），`options_lines` 单独标出选项范围。这两个字段有重叠。

按 §3 的定义，stem 和 options 应该是**不重叠的区域**。

---

## 6. Step 3 重新审核结果（2026-09-10）

在 prompt 中加入 Composite 判定规则后，重新运行地理盲测：

### 6.1 Composite grouping 修正

| 指标 | 修正前（无规则） | 修正后（有规则） |
|------|----------------|----------------|
| LLM units | 34（拆分 composite） | **19（与 GT 一致）** |
| answer_lines | 14/19 = 73.7% | **18/19 = 94.7%** |
| explanation_lines | 19/19 = 100% | **19/19 = 100%** |
| material_lines | 未比较 | 1/19 = 5.3% |

**结论：在当前地理 case 上，Composite grouping 对 Prompt Contract 具有明显响应性（34→19 units）。普遍可靠性需要更多学科样本验证。**

### 6.2 material_lines 边界问题

LLM 倾向于只识别材料的**起始行**，不覆盖**完整材料范围**：

| Unit | LLM | GT | 差异 |
|------|-----|-----|------|
| U8-10 | [105,105] | [105,142] | LLM 只取首行，GT 取全部 38 行 |
| U11-12 | [145,145] | [145,172] | 同上 |
| U19-21 | [251,251] | [251,284] | 同上 |

当前结果显示 LLM 倾向于只输出材料起始位置。一个合理假设是 Material Span Contract 尚未明确要求完整覆盖，但需要下一轮 Prompt Contract 验证确认。可能原因包括：prompt 未定义、LLM 无法判断 material end、图片/表格导致边界困难、GT 本身定义不够严格。

### 6.3 解答题 composite 识别

GT 中 Q31-34 是 composite（有材料+小问），LLM 标成了 standalone。原因：prompt 中的 composite 示例只提到了选择题场景，没有覆盖解答题的"材料+小问"模式。

### 6.4 核心发现

1. **Composite grouping 对 Prompt Contract 具有明显响应性**（单一地理 case，普遍性待验证）
2. **material 范围可能需要在 prompt 中明确"覆盖完整材料区域"**（原因待确认）
3. **解答题的 composite 模式需要在 prompt 中补充示例**
4. **answer/explanation 的跨区域关联表现良好**（三个学科：数学 100%/100%、物理 100%/100%、地理 94.7%/100%）

---

## 7. 下一步

- **Step 4**：检查 manifest expressiveness——manifest 是否表达了构成完整 Question 所需的全部结构关系（composite 小问边界、共享答案表的 question-level association、material 完整范围）
- **Step 5**：设计 I-5-2 Adapter Contract

在此之前不修改 V3 正式代码。
