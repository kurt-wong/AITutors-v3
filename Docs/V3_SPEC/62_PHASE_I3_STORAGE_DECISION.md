# Phase I-3 Storage Decision

Date: 2026-09-09
Status: FROZEN
Prerequisite: I-3-1 SourceSpan Model ✅

---

## Decision 1: 独立表 `document_source_spans`

**不采用** `DocumentSourceLine.bbox JSONB` 扩展。

| 方案 | 问题 |
|------|------|
| bbox JSONB 扩展 | 查询困难，无法索引 span |
| line 内嵌 spans JSON | entity 边界模糊 |
| **独立表** | 可查询、可演进、符合 V3 Source 唯一事实源 |

---

## Decision 2: Schema

```sql
document_source_spans
  id                UUID PK
  source_version_id UUID FK → document_source_versions
  line_ref          VARCHAR  -- 关联 document_source_lines.line_ref
  seq               INTEGER  -- span 在行内的顺序（0-based）
  text              TEXT
  font              VARCHAR NULL
  size              FLOAT NULL
  flags             INTEGER NULL
  bbox              JSONB NULL   -- {x0,y0,x1,y1}
  origin            JSONB NULL   -- {x,y} baseline
  span_hash         VARCHAR(64)  -- SHA256(text+font+size+flags+bbox+origin)
  created_at        TIMESTAMPTZ
```

### 字段说明

| 字段 | 原因 |
|------|------|
| `source_version_id` | Source identity |
| `line_ref` | Resolver 回溯（关联 document_source_lines） |
| `seq` | 原始阅读顺序（span ordering preservation） |
| `text` | 内容 |
| `font` | 字体 hint（数学字体检测） |
| `size` | 字号 hint（上下标检测） |
| `flags` | font flags bitmask（superscript/subscript/bold/italic） |
| `bbox` | 空间 evidence |
| `origin` | 基线 evidence（垂直偏移检测） |
| `span_hash` | integrity check（layout evidence identity） |
| `created_at` | 审计 |

### 不包含 `page_no`

已有 `document_source_lines.page_no`。Span 不重复存储，避免一致性问题。

---

## Decision 3: 索引

```sql
CREATE INDEX idx_source_spans_version_line 
  ON document_source_spans(source_version_id, line_ref, seq);
CREATE INDEX idx_source_spans_hash 
  ON document_source_spans(span_hash);
```

---

## Decision 4: Cardinality 评估

| 场景 | lines | spans/line | total spans |
|------|-------|------------|-------------|
| 简单文本 PDF | 2377 | ~1 | ~2400 |
| 复杂数学 PDF | 2377 | ~5-8 | ~12000-19000 |
| OCR-VL（未来） | 2000 | ~2 | ~4000 |

PostgreSQL 处理无压力。

**注意**：当前测试 PDF 是简单文本（~1 span/line），不能代表所有 PDF。
复杂 PDF 可能有更多 spans（不同 font/size/flags 的公式元素）。

---

## Decision 5: Span ordering preservation

**Gate Criteria 新增**：

```
Provider span order == Stored span order
```

Resolver 后续可能依赖 page coordinate ordering + span sequence。
如果 `a b c d` 保存成 `a c b d`，即使 metadata 全存在，也破坏 evidence。

---

## Decision 6: 不修改 Resolver

Phase I-2C 已证明：85 unresolved 是 evidence 不足，不是 Resolver bug。
现在补 SourceSpan 是正确路径。Resolver 升级（消费 SourceSpan[]）是下一阶段。
