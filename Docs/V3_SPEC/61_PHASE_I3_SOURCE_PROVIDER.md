# Phase I-3 Source Provider Layer Evaluation

Date: 2026-09-09
Status: IN PROGRESS
Prerequisite: Phase I-2C CLOSED

---

## 1. 目标

**Source Provider 保留 layout evidence，而不是 Resolver 修复数学 PDF。**

Phase I-3 的核心价值不是"解决数学 PDF"，而是完成一次架构验证：

> 确认 Source Provider 是否已经拥有足够信息，只是在数据模型和传输链路中丢失。

---

## 2. Source Evidence Preservation Invariant

```
Provider extraction result is immutable evidence.

Any transformation after extraction MUST preserve:
- text
- ordering
- spatial metadata
- provider metadata

Transformation may add interpretation,
but MUST NOT rewrite source evidence.
```

未来链路：`SourceSpan → Resolver → Compiler → Question IR`。
如果 SourceSpan 被后处理修改，会破坏整个 V3 的审计链。

---

## 3. 研究发现

### 当前 extraction 流程

```
PDF bytes
  → NativeTextProvider.extract()
     → PyMuPDF page.get_text("dict")  ← 已返回丰富 layout 信息
        → iterate blocks → lines → spans
           → "".join(sp["text"] for sp in spans)  ← 只取 text，丢弃其余
     → OCRLine(text, page_no, bbox)
  → SealService → DocumentSourceLine
```

**信息损失位置**：`PyMuPDF → OCRLine` 这一跳，rich representation → flat text representation。

**目标流程（Phase I-3 后）**：

```
PDF bytes
  → NativeTextProvider.extract()
     → PyMuPDF page.get_text("dict")
        → iterate blocks → lines → spans
           → 提取 text + font + size + flags + bbox + origin
     → SourceLine(text, page_no, bbox, spans=SourceSpan[])
  → SealService → DocumentSourceLine + DocumentSourceSpan（或等价存储）
```

### 丢弃的 layout 信息

| 数据 | 当前状态 | 数学公式相关性 |
|------|----------|----------------|
| `span["font"]` | 丢弃 | 识别数学字体（Cambria Math/Symbol） |
| `span["size"]` | 丢弃 | 通过字号差异检测上下标 |
| `span["flags"]` | 丢弃 | **提供 superscript/subscript hint，可作为 evidence，不保证语义正确** |
| `span["bbox"]` | 丢弃 | Span 级定位（比 line bbox 更精细） |
| `span["origin"]` | 丢弃 | 基线位置，检测垂直偏移（上标/下标/根号/分式） |
| `line["wmode"]` | 丢弃 | 检测垂直文本 |

**注意**：flags 在 Word 导出公式 / MathType / LaTeX PDF / 图片公式中可靠性差异很大。
Phase I-3 的核心是"保存证据"，不是"识别公式"。

### Font flags bitmask

| Flag | Bit | 值 | 含义 |
|------|-----|-----|------|
| SUPSCRIPT | 0 | 1 | 上标 |
| SUBSCRIPT | 1 | 2 | 下标 |
| ITALIC | 2 | 4 | 斜体 |
| SERIFED | 3 | 8 | 衬线字体 |
| MONOSPACED | 4 | 16 | 等宽 |
| BOLD | 5 | 32 | 粗体 |

### PyMuPDF vs 备选库

| 特性 | PyMuPDF | pdfplumber | pdfminer.six |
|------|---------|------------|--------------|
| 速度 | 快（C-based） | 慢（纯 Python） | 最慢 |
| Font metadata | 丰富（name/size/flags/color） | 中等 | 中等 |
| Superscript 检测 | 直接 flag | 需推断 | 需推断 |
| 已在项目中 | ✅ | ❌ | ❌ |

**结论**：PyMuPDF 已提供最丰富 font metadata，无需换库。

---

## 4. 架构决策

### D-1: 命名泛化

**不使用** `OCRLine`/`OCRLineSpan`——隐含"OCR 输出"语义，污染 Source 唯一事实源原则。

**采用** `SourceLine`/`SourceSpan`——与 provider 无关：

```
Source
  +-- SourceLine
        +-- SourceSpan

NativeProvider → SourceLine
OCRProvider    → SourceLine（未来）
```

### D-2: 存储方案

**优先评估独立实体存储** `document_source_spans`，**最终 schema 在 I-3-1 根据 cardinality 和查询模式决定**。

候选 schema：

```sql
document_source_spans
  id
  source_version_id  -- FK
  line_ref           -- 关联 document_source_lines
  seq                -- span 在行内的顺序
  text
  font
  size
  flags
  bbox               -- JSONB
  origin             -- JSONB
  span_hash          -- SHA256(text + font + size + flags + bbox + origin)
```

**span_hash 设计说明**：
- 描述 **source evidence instance**（layout evidence identity）
- **不表示 semantic equality**——两个文本相同但位置不同的 span，hash 不同（正确行为）
- 不能用 `span_hash` 判断"内容是否相同"，那是 Resolver/Compiler 的职责

**Cardinality 评估**（I-3-1 确认）：

| 场景 | lines | spans/line | total spans |
|------|-------|------------|-------------|
| 普通文本 PDF（100 页） | 5000 | 5 | 25000 |
| 数学试卷（11 页） | 2377 | ~8 | ~19000 |
| OCR-VL（未来） | 2000 | ~2 | 4000 |

规模可接受。索引设计在 I-3-1 确认。

---

## 5. Non-Goals（不做）

- 不接入 CloudOCRProvider（PaddleOCR-VL transport 未接线，独立工作）
- 不切换到 pdfplumber/其他库
- 不实现完整 layout analysis（column detection/line merging/reading order）
- 不实现数学公式 LaTeX 重建
- 不修改 Resolver matching algorithm
- 不为单个 PDF 添加特殊规则
- **不保证 Phase I-3 后 unresolved 数量下降**
- **不进行目录重构**（不移动 `app/ai/ocr/` 文件）

---

## 6. 成功标准

Phase I-3 的成功标准是：

| 指标 | 目标 | 说明 |
|------|------|------|
| Span metadata preservation rate | 100% | PDF span count == stored span count |
| Deterministic extraction | ✅ | 同一 PDF 两次 extract() 输出 canonical identical |
| **Provider round-trip preservation** | ✅ | extract → serialize → reconstruct → canonical comparison 全字段一致 |
| Layout loss audit | font/bbox/flag/origin loss = 0 | Seal 前后对比 |
| 向后兼容 | 现有测试零回归 | OCRLine 扩展不影响现有代码 |

**Provider round-trip preservation** 详细验证：

```
NativeTextProvider.extract()
        ↓
SourceSpan serialization (JSON)
        ↓
SourceSpan reconstruction (from DB)
        ↓
canonical comparison:
  text equal
  font equal
  flags equal
  bbox normalized equal
  origin normalized equal
```

不仅数量一致，还要字段级一致——否则 `PyMuPDF dict → JSON → DB` 过程中仍可能丢精度。

**不是**：85 unresolved → 10 unresolved。

---

## 7. 验证指标详细定义

### 7.1 信息完整率

```
PDF span count == stored span count
```

目标：100%。这一阶段不是理解，是保存。

### 7.2 可重放性

同一 PDF：

```
extract() → extract()
```

输出：canonical identical。

否则后续 resolver evidence 会不稳定。

### 7.3 Layout loss audit

```
Seal 前: PyMuPDF dict spans
  ↓
Seal 后: DocumentSourceSpan（或等价存储）

统计:
  font loss = 0
  bbox loss = 0
  flag loss = 0
  origin loss = 0
```

---

## 8. 实测问题

### 第一层：数据可靠性

**Q1**: PyMuPDF span metadata 是否完整保存？
**Q2**: 同一 PDF 重建是否一致？

### 第二层：数学 PDF 表现

**Q3**: flags 是否能识别上标/下标/希腊字符？
**Q4**: font 是否区分普通文本/数学符号？

### 第三层：Resolver 价值

**Q5**: 增加 span evidence 后，marker_ambiguous 是否下降？

---

## 9. 预期结果

### 可以解决

✅ 题号定位辅助——font size + bbox 位置 + header 区域，可以减少 "1 出现 190 次" 的问题。

### 不能解决

❌ 完整数学公式恢复——`x²+y²=1` 被拆成 `x` `2` `+` `y` `2` `=` `1`，需要 layout reconstruction / formula parser / OCR-VL，不是 Resolver 职责。

---

## 10. I-3 Gate Criteria

Phase I-3 PASS requires:

1. Existing Phase I-2 tests pass（零回归）
2. SourceSpan extraction deterministic（可重放）
3. Layout metadata preserved（font/bbox/flag/origin loss = 0）
4. Provider round-trip preservation（serialize → reconstruct → canonical identical）
5. No Resolver code changes
6. No provider-specific special case

---

## 11. 执行步骤

| 步骤 | 内容 | 状态 |
|------|------|------|
| I-3-0 | 冻结评估文档（本文件） | ✅ |
| I-3-1 | 定义 SourceLine/SourceSpan + 评估存储方案（cardinality/index） | ⏳ |
| I-3-2 | NativeTextProvider 提取 span metadata | ⏳ |
| I-3-3 | 存储 layout metadata（表或 JSONB，I-3-1 决定） | ⏳ |
| I-3-4 | 测试 + 全量回归 + layout loss audit + round-trip | ⏳ |
| I-3-5 | 真实 PDF E2E 验证（三层问题） | ⏳ |
| I-3-6 | 评估结论 + Closure 文档 | ⏳ |

---

## 12. 关键文件清单

**修改**
- `backend/app/ai/ocr/result.py`（新增 SourceSpan，现有 OCRLine 类型语义迁移）
- `backend/app/ai/ocr/providers.py`（NativeTextProvider 提取 span metadata）
- `backend/app/domains/source/line_index.py`（SealLine 传递 layout metadata）

**新建**
- `backend/tests/test_source_span.py`（SourceSpan 测试）

**待定（I-3-1 决定）**
- `backend/app/models/source.py` + migration（如果需要独立表）

**不修改**
- Resolver（本阶段只提供数据，不改 matching algorithm）
- CloudOCRProvider（transport 未接线，独立工作）
- 目录结构（不移动 `app/ai/ocr/` 文件）
