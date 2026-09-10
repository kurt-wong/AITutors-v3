# V3 Architecture Constraint: Source Evidence Complexity Boundary

Status: Frozen Constraint
Applies From: Phase I-3 Closure onward
Purpose: Prevent Source Evidence Layer over-expansion after layout preservation capability is established.

---

## 1. Core Principle

Source Layer 的职责：

> 保存 Provider 产生的不可逆事实证据（immutable evidence），而不是理解文档。

Source Layer 必须回答：

> "原始文档中存在什么？"

而不能回答：

> "这些内容意味着什么？"

---

## 2. Source Evidence Boundary

### Allowed: Evidence Preservation

以下类型允许进入 Source Layer：

| 类型 | 示例 | 原因 |
|------|------|------|
| 原始文本 | text | 信息不可恢复 |
| 空间信息 | bbox | 定位证据 |
| 页面信息 | page_no | 来源定位 |
| 顺序信息 | line/span seq | 重建依据 |
| Provider metadata | font/size/flags/origin | 原始证据 |
| hash identity | span_hash | 完整性验证 |

这些属于 `Raw Evidence`。

### Forbidden: Semantic Interpretation

以下内容禁止进入 Source Layer：

| 类型 | 示例 | 所属层 |
|------|------|--------|
| 题号识别 | question_no=1 | Resolver |
| 题目边界判断 | question span | Resolver |
| 公式含义 | x²+y²=1 表示圆 | Semantic |
| 知识点标签 | 二次函数 | Knowledge |
| 题型分类 | 选择题/证明题 | Compiler/Semantic |
| 相似关系 | Similarity/Families | Analysis |

原因：这些不是事实，而是系统推理结果。

---

## 3. Source Entity Expansion Constraint

任何新增 `SourceXXX` / `DocumentSourceXXX` / `LayoutXXX` 实体前，必须回答四项审查：

### Q1: Evidence or Interpretation？

它保存的是 `Evidence` 还是 `Interpretation`？

如果属于 Interpretation → **禁止进入 Source**。

### Q2: Irreversible Loss？

删除该实体后，是否存在信息不可逆丢失？

如果 `No` → 不应该新增。

### Q3: Real Failure Case？

是否存在真实失败案例证明需要？

要求：必须来自真实 PDF / 真实测试失败 / 真实数据分析。

**禁止** "未来可能需要" 作为新增理由。

### Q4: Other Layer Responsibility？

是否存在其他层负责？

如果 Resolver / Compiler / Semantic Layer 可以解决 → Source 不承担。

---

## 4. Phase I-3 后禁止事项

### 禁止继续扩展 Source 为 PDF Understanding Engine

除非重新进行架构评审，否则禁止加入：

```
LayoutGraph
SourceRegion
SourceBlock
FormulaNode
ReadingOrderGraph
SemanticLayoutTree
```

原因：这些已经从 `Evidence Preservation` 进入 `Document Understanding`，属于更高层能力。

---

## 5. Resolver Development Constraint

### SourceSpan 增加后，不允许直接修改 Resolver 规则

正确顺序：

```
Source Evidence
        ↓
Diagnostic Evaluation
        ↓
Evidence Utilization Analysis
        ↓
Resolver Change Proposal
```

禁止：

```
Resolver失败
    ↓
立即增加 Source 字段
```

---

## 6. Resolver Evidence Utilization Gate

在修改 Resolver 前，必须完成：

### Before（Baseline）

记录当前状态：

```
marker="1"
candidate count: 190
status: ambiguous
```

### After（Evidence-Aware）

使用 SourceSpan evidence：

```
marker="1"
candidate count: ?
status: ?
```

只有证明新增 evidence 能改善定位，才进入 Resolver 修改。

---

## 7. Complexity Budget

V3 后续阶段新增抽象必须满足：

### Required Justification

每个新增 entity / service / abstraction / metadata field 必须提交：

```
Problem: 真实失败案例
Current limitation: 当前设计无法表达什么
Why existing layer cannot solve: 为什么不能放其他层
Minimal solution: 最小新增设计
Cost: 数据库/API/测试复杂度增加
```

---

## 8. Current Phase I-3 Assessment

Phase I-3 当前实现：

```
PyMuPDF
    ↓
SourceSpan
    ↓
Immutable Evidence
```

符合架构原则。原因：它解决的是 `information loss`，不是 `semantic understanding`。

```
PASS
```

---

## 9. Future Direction Constraint

后续优先级：

**正确**：

```
Source Evidence → Resolver Evaluation → Compiler → Semantic Layer
```

**错误**：

```
Source
  +-- increasingly complex PDF intelligence engine
```

---

## 10. Final Architectural Rule

> **Source 保存事实，Resolver 使用证据，Compiler 生成结构，Semantic Layer 负责理解。任何层不得替代下一层。**

> **当系统失败时，优先判断"缺少哪一层能力"，而不是继续向已有层添加复杂度。**
