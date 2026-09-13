# Phase I-2 Revision Closure

> ⚠️ **SUPERSEDED — 已归档，不得作为引用来源（`90 §2 R8`，残余审计 A-10 2026-09-13）**
>
> 本文件是 Phase I-2 Revision Closure 的**早期快照份**。同主题曾存在两份且内容不同：
>
> | 份 | 时间 | 大小 | 测试数字 | 现状 |
> |---|---|---|---|---|
> | **本文件**（原 `Docs/V3_PHASE_STATUS/Phase_I2_Revision_Closure.md`） | Sep 10 00:30 | 6363 B | 421 passed · QG 11/11 | **STALE，已归档** |
> | `Docs/REPORTS/PHASE_I2_REVISION_CLOSURE.md` | 较晚冻结 | 3339 B | **425 passed · QG 15/15** | **权威版**（L2，D-02 归层） |
>
> 新版含更多 commit（`cf9d4b4` Status update + freeze commit），**425 / 15 为准**。
>
> **未迁移决策信息核查** —— 本文 §6 三个 Design Decision **均已有载体**：
>
> | Decision | 载体 | 权威层级 |
> |---|---|---|
> | D1 SourceQualityGate 位于 Seal 后 Annotation 前 | `Docs/REPORTS/PHASE_I2_REVISION_CLOSURE.md §4` | L2（压缩迁移） |
> | D2 OCR 是 Provider，不是替代 | **L0 `10_Data_Model.md` §4.2** role 枚举 `native / ocr_ppsv3 / ocr_ppsvl / docx / canonical` + role/provider 封闭配对；sealed 不可变 = `20 §3.1` | **L0（更高权威）** |
> | D3 Quality Gate 为纯函数（无 IO、确定性） | `Docs/REPORTS/PHASE_I2_REVISION_CLOSURE.md §4` | L2（压缩迁移） |
>
> **DELETE 三证检验**：无历史价值 **✗**（真实历史快照，含 Real-file E2E 明细与 math fragmentation 例子）· 无决策价值 ✓ · 无引用价值 **✗**（`Status.md` 历史节曾引用）→ **三证不全，不得 DELETE** → **Disposition = ARCHIVE**。
>
> **本文独有内容**（证据粒度，非决策）：Real-file E2E 明细（PDF 名 / 11 页 / 2377 行 / 11 figures / CJK 42% · replacement 0% · non-printable 7%）· math fragmentation 具体例子（`P1L014`–`P1L018` → `点(1/2, 2)`）· Closure Verification checklist · PDF 编码误报完整证据链。math fragmentation 已由 **Phase I-2C** 承接并 CLOSED（`Docs/REPORTS/PHASE_I2C_CLOSURE.md`）。
>
> **Provenance 断链**：本文下方 `Supersedes: PHASE_I2_REVISION_REVIEW.md` 所指文件**全仓不存在**，上游来源已断——这也是本文件被判定为孤立旧案卷的依据之一。
>
> **权威版**：`Docs/REPORTS/PHASE_I2_REVISION_CLOSURE.md`
>
> **本文件正文保留为审计证据**（不删除、不改写）；按 `90 §2 R8`：不得作为引用来源、不得进入新文档的引用搜索结果、`docs_audit/` 标 `deprecated`。

**Date**: 2026-09-09
**Status**: CLOSED
**Supersedes**: PHASE_I2_REVISION_REVIEW.md (adversarial review)

---

## 1. Scope

### Goal
Establish observable real-file E2E boundary for V3 pipeline with real PDF input.

### Included
- SourceQualityGate (post-seal, pre-annotation text quality detection)
- Source metadata persistence (quality report in source_meta)
- Review Console source inspection (source lines API + frontend)
- Native PDF extraction validation (PyMuPDF)
- Real-file E2E verification

### Excluded
- OCR production (Cloud OCR transport)
- Mathematical formula reconstruction
- Live LLM integration (already completed in Phase I-1)
- Resolver enhancement for math PDFs

---

## 2. Confirmed Architecture

```
Import
  ↓
Seal (immutable)
  ↓
SourceQualityGate ← NEW (Phase I-2 Revision)
  ↓
Annotation
  ↓
Resolver
  ↓
Compile
  ↓
Gate
  ↓
Admission
```

**SourceQualityGate is now a formal architecture layer.**

Rationale:
- Prevents corrupted source from entering annotation (saves LLM tokens)
- Fail-loud at source level, not downstream
- Quality report persisted for human review
- Aligns with V3 P3: Source is the single source of truth

---

## 3. Test Evidence

### Backend
```
Total pytest: 421 passed (baseline 417, net +4)
Quality Gate: 11/11 tests PASSED
Import E2E: 4/4 tests PASSED
```

### Frontend
```
TypeScript compile: 0 errors
```

### API Verification
```
GET /api/documents/{id}/source-quality → HTTP 200
GET /api/documents/{id}/source-lines → HTTP 200
GET /api/documents/{id}/source-quality (invalid id) → HTTP 404
```

### Real-File E2E
```
PDF: 2026北京北师大实验中学高一（下）阶段测试一数学（教师版）.pdf
Pages: 11
Lines extracted: 2377
Figures: 11
Quality status: valid (CJK ratio 42%, replacement 0%, non-printable 7%)
```

---

## 4. Critical Correction: PDF Encoding False Alarm

### Previous (Incorrect) Assumption
"PyMuPDF Chinese encoding failure → needs OCR fallback"

### Actual Finding
```
PDF → PyMuPDF extraction → Text is CORRECT
                              ↓
                    Windows terminal display corruption
                              ↓
                    Mistaken for PDF encoding failure
```

### Evidence
Text extracted from PDF (written to file with explicit UTF-8):
```
第1页/共11页
2026 北京北师大实验中学高一（下）阶段测试一
一、单选题（每小题4 分，共32 分）
1. 已知弧长为5π 的弧所对的圆心角为150...
```

**Conclusion**: Native extraction is correct. The "乱码" was Windows console encoding issue.

### Impact
- No OCR needed for text-layer PDFs
- Quality Gate correctly identifies valid text
- Real bottleneck is Resolver math formula fragmentation (not encoding)

---

## 5. Known Limitations

### Deferred to Phase I-2C (Resolver Robustness)

| Issue | Status | Priority |
|-------|--------|----------|
| Mathematical formula structure recovery | Deferred | P1 |
| LaTeX token extraction | Deferred | P1 |
| Layout-aware (block-based) Resolver | Deferred | P1 |
| OCR provider (scanned PDF support) | Deferred | P2 |
| Cloud OCR transport | Deferred | P2 |

### Example: Math Formula Fragmentation
```
Source lines (fragmented):
P1L014: '2. 已知角的终边经过点1'
P1L015: '1'
P1L016: ','
P1L017: '2'
P1L018: '2'

Expected (semantic):
点(1/2, 2)
```

This is **mathematical document understanding**, not OCR problem.

---

## 6. Design Decisions

### Decision 1: SourceQualityGate Position
**Decision**: Between Seal and Annotation.

**Reason**:
- Fail-loud before LLM consumption
- Prevents wasted annotation attempts
- Quality report available for human review before annotation

### Decision 2: OCR is Provider, Not Replacement
**Decision**: OCR is an alternative source provider, not a fix for native extraction.

**Reason**:
- V3 P3: Source is single source of truth
- OCR output is a different source_version (role=ocr_*)
- Never modify sealed source (SPEC 20 §3.1)

### Decision 3: Quality Gate Pure Function
**Decision**: `SourceQualityGate.evaluate()` is pure (no IO, deterministic).

**Reason**:
- Testable in isolation
- Idempotent (same input = same output)
- No hidden state

---

## 7. PUA False Positive Bug (P0 Fix)

### Issue
`_is_non_printable()` treats Private Use Area (U+F000-U+F8FF, category "Co") as non-printable.

### Reality
Math PDFs use PUA for symbols (≥, ≤, →, vector arrows).

### Current Status
Not triggered in this PDF (PUA 7% < 10% threshold).

### Risk
Math-heavy PDFs with PUA > 10% would be incorrectly marked `invalid`.

### Fix (Applied)
Change invalid condition to require BOTH:
```python
if non_printable_ratio > _MAX_NON_PRINTABLE_RATIO and replacement_ratio > 0.01:
    status = "invalid"
```

PUA alone is not quality failure. Combined with replacement chars indicates corruption.

---

## 8. Next Phase: I-2C Resolver Robustness

### Goal
Not "improve recognition rate", but establish reliable transformation:
```
Source Evidence → Resolved Span → Semantic Question IR
```

### Scope (Phase I-2C)
1. Resolver debug view (frontend)
2. Line/block relationship modeling
3. Formula fragment detection
4. Ambiguous status display

### Out of Scope
- OCR integration
- LLM auto-repair
- LaTeX reconstruction
- Full math formula parsing

---

## 9. Git Commit History

### Commit 1: Documentation Freeze (`ee4d08f`)
```
docs: freeze Phase I-2 Revision conclusions

- Add Phase_I2_Revision_Closure.md
- Update Status.md (Phase I-2 Revision CLOSED)
- Update bugs.md (BUG-V3-040/041/042)
```

### Commit 2: PUA Fix (`1c31fdf`)
```
fix: exclude mathematical PUA symbols from source quality failure

PUA alone ≠ quality failure. Exclude Co (Private Use Area) from
non-printable count. Prevents false-positive rejection of math PDFs.
```

### Commit 3: Quality Gate Tests (`0ef64ab`)
```
test: add source quality regression coverage for PUA handling

- PUA 20% alone → valid
- PUA + replacement → invalid
- replacement > 5% alone → invalid
- Realistic math PDF scenario → valid
```

---

## 10. Closure Verification

- [x] All tests pass (421 passed)
- [x] Frontend compiles (0 TypeScript errors)
- [x] API endpoints verified (200/404)
- [x] Real-file E2E completed
- [x] Documentation frozen
- [x] PUA bug fixed
- [x] Architecture decisions recorded

**Phase I-2 Revision: CLOSED**
