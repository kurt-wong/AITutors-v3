# Phase I-2C Resolver Robustness Validation

Date: 2026-09-09
Status: IN PROGRESS
Prerequisite: v3-phase-i2-closed

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

## 5. 执行顺序

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
