# Phase I-2C Closure — Resolver Robustness Validation

Authority Level: L2 — Decision Record（formal phase closure；D-02 归层 2026-09-13）
Document Type: Decision Record
Normative: NO（记录阶段裁决，不定义新架构事实 — 90 §2 R2）
Gate State Authority: NO（唯一权威 = 82 §3）

Date: 2026-09-09
Status: CLOSED
Prerequisite: v3-phase-i2-closed
Commits: 5f8a3a8 → 1192108 → 8267bfd

---

## 1. Objective（达成）

验证 Resolver 在真实数学 PDF 上的行为，建立可观测性，确认失败模式归属。

**目标不是让数学题 100% 解析，而是让系统能够回答：这 85 个为什么 unresolved。**

已达成。

---

## 2. Completed

| 步骤 | 状态 | Commit |
|------|------|--------|
| I-2C-0: 诊断文档冻结 | ✅ | 5f8a3a8 |
| I-2C-1: BUG-V3-043 figures 修复 | ✅ | 5f8a3a8 |
| I-2C-2: Diagnostic Layer | ✅ | 5f8a3a8 + 1192108 |
| 真实 PDF 诊断数据采集 | ✅ | 8267bfd |

### I-2C-1: BUG-V3-043（Resolved）

`GateService.run()` 创建 `SourceResolver` 时未传 `figures` 参数 → 所有 image reference 恒返回 `ambiguous`。

修复：加载 `source_figures` 并转换为 `SourceFigureView` 传入 Resolver。
验证：52 passed（gate + resolver + dbflow），零回归。

### I-2C-2: Diagnostic Layer

新增 `backend/app/domains/resolver/diagnostic.py`：
- `MatchAttempt`: exact/normalized/fuzzy 尝试结果
- `CandidateLine`: 部分匹配候选行
- `UnresolvedDiagnostic`: 单个 unresolved 结构化诊断
- `DiagnosticReport`: 分类汇总

15 new tests, all passing. Pure functions, no IO, deterministic.

---

## 3. 诊断发现（核心结论）

### 数据

```
Source version: a40a31a7-3227-4493-9d73-d3c64bde187f
Lines: 2377 / Figures: 11
Annotation: 17 semantic units
Resolved: 17 / Unresolved: 85
Resolution rate: 16.7%
```

### 分类分布

```
marker_ambiguous: 85 (100%)
marker_not_found: 0
marker_fragmented: 0
grammar_mismatch: 0
```

### 按 Role

```
stem: 10
option: 68
answer: 7
```

### 根因

**题号和选项标签在数学 PDF 中出现太多次，Resolver 无法唯一确定。**

- `Q1.stem` marker `"1"` → 190 exact hits
- `Q1.option.A` marker `"A"` → 大量 hits（数学公式中的字母 A）
- `Q1.answer` marker `"1"` → 在答案区也出现多次

---

## 4. 架构判断

### Resolver 当前行为是正确的

Annotation 输出 `question_label: "1"`，Resolver 在 Source 中查找 `"1"`，发现 190 次出现，返回 `ambiguous`。

**这是正确的 fail-loud。** 如果 Resolver 返回第一个匹配，反而是错误——它没有足够证据证明这个 "1" 就是题号。

符合 V3 核心原则：**宁可拒绝确定，不允许错误定位。**

### 三种失败模式的责任归属

| 类型 | 含义 | 责任归属 |
|------|------|----------|
| `marker_not_found` | Source 中不存在目标文本 | Source/Annotation 问题 |
| `marker_ambiguous` | Source 中存在太多候选位置 | **Layout/Structure 问题** |
| `marker_wrong` | 找到了错误位置 | Resolver 问题 |

当前属于第二类。

### 不做 Resolver robustness 的原因

1. **多行匹配无法解决核心问题**：当前失败是 marker 出现 190 次，不是拆行。多行拼接不改变 candidate_count。
2. **fuzzy matching 会恶化系统**：Levenshtein/embedding similarity 会找到"最像"的，产生错误的 Admission candidate——这是 V3 最应避免的问题。

---

## 5. 真正缺失的能力

当前 pipeline：

```
PDF → PyMuPDF text extraction → flat lines
```

丢失了 PDF 最重要的信息：**Layout information**。

数学试卷真正需要：

```
文字内容 + 坐标 + 字体 + 块关系 + 阅读顺序
```

而不是 flat lines。

---

## 6. Decision

**Resolver robustness enhancement deferred.**

原因：失败不是由匹配算法不足导致，缺失的能力属于 Source Provider layout reconstruction。

**下一阶段：Phase I-3 Source Provider Layer Evaluation**

目标：评估 native PDF extraction、OCR layout extraction、hybrid provider 对数学试卷的结构恢复能力。

---

## 7. BUG 状态更新

| BUG | Status | 说明 |
|-----|--------|------|
| BUG-V3-041 (Mathematical Layout Fragmentation) | Deferred → Phase I-3 | 根因确认为 Source Provider layout 缺失 |
| BUG-V3-043 (GateService figures 注入缺失) | **Resolved** | 修复完成，52 passed |

---

## 8. Git 记录

| Commit | 说明 |
|--------|------|
| 5f8a3a8 | I-2C-0 + I-2C-1 + I-2C-2（文档 + figures 修复 + diagnostic layer） |
| 1192108 | marker extraction 修正 + 真实 PDF 诊断报告 |
| 8267bfd | 诊断发现文档更新 |
