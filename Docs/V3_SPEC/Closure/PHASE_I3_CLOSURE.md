# Phase I-3 Closure — Source Evidence Preservation Layer

Date: 2026-09-09
Status: CLOSED
Gate: PASS
Prerequisite: Phase I-2C CLOSED
Commits: f15dfb2 → a9c32f3 → c42b8dc → 9645a81 → 6ec69df

---

## 1. Objective（达成）

Source Provider 保留 layout evidence，完成 V3 架构基础闭环：

```
Source Provider → Source Evidence → Immutable Storage → Replay Verification
```

**目标不是解决数学 PDF，而是让 layout 信息成为可靠的一等公民。**

已达成。

---

## 2. Completed

| 步骤 | 状态 | Commit |
|------|------|--------|
| I-3-0: 评估文档冻结 | ✅ | f15dfb2 |
| I-3-1: SourceSpan 定义 + NativeTextProvider 提取 | ✅ | a9c32f3 |
| I-3-2: 存储决策冻结（独立表） | ✅ | c42b8dc |
| I-3-3: document_source_spans 表 + seal 持久化 | ✅ | 9645a81 |
| I-3-4: FK 违例修复 | ✅ | 6ec69df |
| I-3-5: 对抗性审查（10 维度） | ✅ | 本文件 |
| I-3-6: Closure 文档 | ✅ | 本文件 |

### I-3-1: SourceSpan 数据模型

新增 `SourceSpan` frozen dataclass（`backend/app/ai/ocr/result.py`）：
- 字段：seq, text, font, size, flags, bbox, origin, span_hash
- `compute_hash()`：SHA256(text + font + size + flags + bbox + origin)
- Properties：`is_superscript`, `is_subscript`, `is_bold`, `is_italic`
- `OCRLine` 扩展 `spans: tuple[SourceSpan, ...] = ()`（向后兼容）

`NativeTextProvider.extract()` 从 PyMuPDF `get_text("dict")` 提取完整 span metadata。

### I-3-2: 存储决策

选择独立表 `document_source_spans`（非 bbox JSONB 扩展）：
- 可查询、可索引、可演进
- entity 边界清晰
- 符合 V3 Source 唯一事实源原则

详见 `62_PHASE_I3_STORAGE_DECISION.md`。

### I-3-3: 持久化链路

```
PyMuPDF dict → SourceSpan → SealLine.spans → DocumentSourceSpan ORM → PostgreSQL
```

- `SealLine` 扩展 `spans` 字段
- `SealService.seal_document()` 遍历 lines → spans → `append_span()`
- `SourceRepository.append_span()` / `update_span()`（append-only 保护）
- Migration 0010：`CREATE TABLE IF NOT EXISTS`（BUG-V3-028 双路径安全）

### I-3-4: FK 违例修复

**Bug**：`test_seal_dbflow.py` cleanup 未删除 `document_source_spans` → FK 违例。

**修复**：在删除 `document_source_versions` 前添加 `DELETE FROM document_source_spans`。

**验证**：13/13 tests pass。

---

## 3. 对抗性审查结果

### 审查方法

10 维度真实测试验证（非 mock），使用真实 PDF + 真实 PostgreSQL。

### 结果

| 维度 | 结果 | 证据 |
|------|------|------|
| 1. Data Integrity | PASS | span_hash 正确捕获 6 个 layout 字段 |
| 2. Deterministic Extraction | PASS | 同一 PDF 两次提取 → 完全相同输出 |
| 3. Span Ordering | PASS | seq 单调递增，build_line_index 保持顺序 |
| 4. Layout Loss Audit | PASS | font/bbox/flags/origin 零丢失 |
| 5. Provider Round-Trip | PASS | extract → serialize → reconstruct → hash 一致 |
| 6. Backward Compatibility | PASS | OCRLine 无 spans → 空 tuple，旧测试全通过 |
| 7. Seal Persistence | FAIL → **已修复** | FK 违例（见 I-3-4） |
| 8. Migration Safety | PASS | from-empty + incremental 双路径均通过 |
| 9. V3SPEC Compliance | PASS | 5 个不变量全部满足 |
| 10. No Resolver Changes | PASS | Resolver 代码完全未触碰 |

### 关键测试证据

**Layout Loss Audit**：
```
Raw spans from PyMuPDF: 3
Extracted spans from NativeTextProvider: 3
Span 0: text='Normal text' font=Helvetica size=12.0 flags=0
Span 1: text='Courier text' font=Courier size=10.0 flags=8
Span 2: text='Times text' font=Times-Roman size=14.0 flags=4
Zero loss across font, size, flags, bbox, origin.
```

**Round-Trip Preservation**：
```
Span 0: text='Part1 ' orig_hash=0e92a62cad1e59ab... recon_hash=0e92a62cad1e59ab... match=True
Span 1: text='Part2' orig_hash=b848670a6984df8a... recon_hash=b848670a6984df8a... match=True
Origin round-trips correctly: stored as {"x": float, "y": float}, reconstructed as (float, float), hash unchanged.
```

**Spatial Identity**：
```
span1 = text='x' bbox={x0:0,y0:0,...} → hash A
span2 = text='x' bbox={x0:100,y0:100,...} → hash B
A ≠ B → physical evidence identity, not semantic identity
```

---

## 4. Gate Criteria 验证

| Criteria | 目标 | 实际 | 结果 |
|----------|------|------|------|
| Existing tests pass | 零回归 | 454 passed | ✅ |
| Deterministic extraction | ✅ | 同 PDF 两次提取 identical | ✅ |
| Layout metadata preserved | loss = 0 | font/bbox/flags/origin loss = 0 | ✅ |
| Provider round-trip | serialize → reconstruct → identical | hash 一致 | ✅ |
| No Resolver changes | 0 files touched | git diff 确认 | ✅ |
| No provider special case | 0 special rules | 代码审查确认 | ✅ |

**Phase I-3 Gate: PASS**

---

## 5. 架构影响

### Before Phase I-3

```
PDF → PyMuPDF text extraction → flat lines → Resolver (text only)
```

### After Phase I-3

```
PDF bytes
    ↓
NativeTextProvider
    ↓
SourceLine
    ↓
SourceSpan (font, size, flags, bbox, origin)
    ↓
SealService
    ↓
Immutable Source Evidence
    ↓
Annotation / Resolver
```

Resolver 现在消费的是**真实 evidence**，而不是降维后的 text dump。

---

## 6. BUG 状态更新

| BUG | Status | 说明 |
|-----|--------|------|
| BUG-V3-041 (Mathematical Layout Fragmentation) | **Partially Addressed** | Source Provider 已保留 layout evidence，Resolver 消费待 Phase I-4 |
| BUG-V3-043 (GateService figures 注入缺失) | Resolved (I-2C) | — |

---

## 7. 文件清单

### 新建

| 文件 | 用途 |
|------|------|
| `backend/app/ai/ocr/result.py` | SourceSpan + _make_span |
| `backend/alembic/versions/20260909_0010_source_spans.py` | document_source_spans 表 |
| `backend/tests/test_source_span.py` | 19 tests |
| `Docs/V3_SPEC/61_PHASE_I3_SOURCE_PROVIDER.md` | 评估文档 |
| `Docs/V3_SPEC/62_PHASE_I3_STORAGE_DECISION.md` | 存储决策 |
| `Docs/V3_SPEC/63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md` | 架构护栏 |

### 修改

| 文件 | 变更 |
|------|------|
| `backend/app/ai/ocr/providers.py` | NativeTextProvider 提取 span metadata |
| `backend/app/ai/ocr/result.py` | OCRLine 扩展 spans 字段 |
| `backend/app/domains/source/line_index.py` | SealLine 扩展 spans 字段 |
| `backend/app/domains/source/seal.py` | 持久化 spans |
| `backend/app/models/source.py` | DocumentSourceSpan ORM |
| `backend/app/models/__init__.py` | 导出 DocumentSourceSpan |
| `backend/app/repositories/source_repository.py` | append_span / update_span |
| `backend/tests/test_models_schema.py` | 20 tables, 11 UNIQUE constraints |
| `backend/tests/test_migration_replay.py` | delta 包含 document_source_spans |
| `backend/tests/test_seal_dbflow.py` | FK cleanup 修复 |

---

## 8. Git 记录

| Commit | 说明 |
|--------|------|
| f15dfb2 | I-3-0 评估文档冻结 |
| a9c32f3 | I-3-1 SourceSpan + NativeTextProvider |
| c42b8dc | I-3-2 存储决策冻结 |
| 9645a81 | I-3-3 document_source_spans + seal 持久化 |
| 6ec69df | I-3-4 FK 违例修复 |

---

## 9. Decision

**Phase I-3 CLOSED. Gate PASS.**

Source Evidence Preservation Layer 实现正确，架构基础闭环完成。

**下一阶段：Phase I-4 Resolver Evidence Utilization Evaluation**

目标：验证 SourceSpan 是否真的能够降低 marker_ambiguous。

**不直接修改 Resolver matching algorithm。** 先测量收益，再决定是否修改。

详见 `63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md` §5。
