# Phase I-2C Resolver Robustness Validation

Date: 2026-09-09
Status: **CLOSED**
Prerequisite: v3-phase-i2-closed
Closure: `Docs/V3_SPEC/Closure/PHASE_I2C_CLOSURE.md`

---

## 1. 目标

验证 Resolver 在真实数学 PDF 上的行为，建立可观测性，为后续改进提供数据基础。

**不是**让数学题 100% 解析，而是让系统能够回答：

> 这 85 个为什么 unresolved。

---

## 2. 已确认事实

1. Resolver 当前采用单行 marker resolution（`_locate()` 期望连续子串）
2. Resolver 不负责数学公式重建（职责边界）
3. Figures 必须作为 Resolver 输入（BUG-V3-043）
4. Unresolved 必须可诊断（当前无 logging/debug）

---

## 3. 当前发现

### BUG-V3-043 — GateService figures 注入缺失

- **Severity**: P0
- **Status**: Resolved（2026-09-09）
- **现象**: `GateService.run()` 创建 `SourceResolver` 时未传 `figures` 参数
- **影响**: 所有 image reference 恒返回 `ambiguous`，图片题无法进入 Compile
- **修复**: 加载 `source_figures` 并转换为 `SourceFigureView` 传入 Resolver
- **验证**: 52 passed（gate + resolver + dbflow），零回归

### Resolver 架构诊断

| 组件 | 说明 |
|------|------|
| 匹配级联 | exact → normalized → contextual → fuzzy → ambiguous → missing |
| 输入 | `SourceLineView[]` + `SourceFigureView[]` |
| 输出 | `ResolvedRun`（resolved_spans + unresolved_references） |
| 诊断 | `evidence` 字段存在但无结构化输出 |
| Logging | 零（无 logger/debug/print） |

### 失败模式分析（待数据采集）

| 类型 | 可能原因 | 解决方向 |
|------|----------|----------|
| 图片引用缺失 | figures 未注入 | BUG-V3-043（已修复） |
| 标题定位失败 | grammar 不匹配 | Header Grammar 扩展 |
| 数学公式拆行 | PDF layout fragmentation | Source Provider Layer（非 Resolver） |
| Marker 不存在 | LLM 输出与 Source 不符 | Annotation Contract |
| 多义匹配 | 文本重复 | Zone exclusion / contextual |

---

## 4. 不做事项（Non-Goals）

本阶段**不实现**：

- OCR fallback
- LLM-assisted resolver
- Formula reconstruction
- Semantic matching
- Vector search
- Source schema 修改
- Resolver 职责扩展
- 为单个 PDF 添加特殊规则

---

## 5. 真实 PDF 诊断数据（2026-09-09）

### 数据来源

- PDF：2026北京北师大实验中学高一（下）阶段测试一数学（教师版）
- Source version：`a40a31a7-3227-4493-9d73-d3c64bde187f`
- Lines：2377 / Figures：11
- Annotation：17 semantic units

### 诊断结果

| 指标 | 值 |
|------|-----|
| Resolved spans | 17 |
| Unresolved refs | 85 |
| Resolution rate | 17/102 = 16.7% |

### Unresolved 分类分布

| 分类 | 数量 | 占比 |
|------|------|------|
| `marker_ambiguous` | 85 | 100% |
| `marker_not_found` | 0 | 0% |
| `marker_fragmented` | 0 | 0% |
| `grammar_mismatch` | 0 | 0% |

### 按 Role 分布

| Role | 数量 | 说明 |
|------|------|------|
| stem | 10 | 题干定位失败 |
| option | 68 | 选项定位失败（主要） |
| answer | 7 | 答案定位失败 |

### 根因分析

**所有 85 个 unresolved 都是 `marker_ambiguous`**——marker 文本在源文本中出现太多次，无法唯一确定。

典型案例：
- `Q1.stem` marker `"1"` → 190 exact hits（题号 "1" 在数学 PDF 中出现 190 次）
- `Q1.option.A` marker `"A"` → 大量 hits（数学公式中的字母 A）
- `Q1.answer` marker `"1"` → 在答案区也出现多次

**这不是"找不到"，而是"无法唯一确定"**——Resolver 的单行 marker resolution 设计边界。

### 结论

Resolver 在数学 PDF 上的失败模式是 **marker ambiguity**，不是 **marker missing**。

这意味着：
1. Source 层提取正确（2377 lines，CJK 正常）
2. Annotation 层输出正确（17 units，question_label/label 正确）
3. Resolver 层的单行 marker 匹配无法处理数学 PDF 中大量重复的题号和选项标签

**这是架构设计边界，不是 bug。** 数学 PDF 的 layout reconstruction 属于 Source Provider Layer 职责，不属于 Resolver。

---

## 6. 执行顺序

```
I-2C-0: 文档冻结（本文件）
        ↓
I-2C-1: 修复 figures 注入缺陷（BUG-V3-043）✅
        ↓
I-2C-2: Resolver Diagnostic Layer（P0）
        ↓
真实 PDF E2E 数据采集
        ↓
I-2C-3: Resolver Robustness 改进（P1，基于数据决策）
        ↓
I-2C Closure
```

---

## 6. Phase I-2C 核心原则

| 原则 | 验证 |
|------|------|
| 不猜 | 无法确定就 incomplete |
| 可追溯 | 每个 semantic span 有 source_span |
| 可复现 | 同 source 得同 IR |

---

## 7. 诊断数据结构（I-2C-2 设计）

目标：每个 unresolved reference 有结构化诊断，回答"为什么失败"。

```json
{
  "reference_id": "ref-001",
  "role": "stem",
  "marker": "sinα=1/2",
  "status": "unresolved",
  "attempts": [
    {"method": "exact", "result": "not_found"},
    {"method": "normalized", "result": "not_found"},
    {"method": "fuzzy", "result": "low_score"}
  ],
  "candidate_lines": ["P1L014: sin", "P1L015: α", "P1L016: =", "P1L017: 1/2"]
}
```

---

## 8. 验收条件

1. BUG-V3-043 修复后，image reference 在有 figures 时能正确 resolve
2. Resolver 有结构化诊断输出，能分类 unresolved 原因
3. 真实 PDF E2E 能采集到 unresolved 分布数据
4. 基于数据决定是否进入 I-2C-3

---

## 9. Git 记录

| 步骤 | Commit | 说明 |
|------|--------|------|
| I-2C-0 | (this) | 诊断文档冻结 |
| I-2C-1 | (next) | BUG-V3-043 figures 修复 |
| I-2C-2 | (pending) | Diagnostic Layer |
