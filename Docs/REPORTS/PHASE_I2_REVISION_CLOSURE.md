# Phase I-2 Revision Closure

Authority Level: L2 — Decision Record（formal phase closure；D-02 归层 2026-09-13）
Document Type: Decision Record
Normative: NO（记录阶段裁决，不定义新架构事实 — 90 §2 R2）
Gate State Authority: NO（唯一权威 = 82 §3）

Date: 2026-09-09
Status: CLOSED WITH NOTES
Tag: v3-phase-i2-closed

---

## 1. Objective

验证真实文件进入系统后的闭环：

```
Import
  ↓
Document Created
  ↓
Task Queued
  ↓
Seal
  ↓
Source Quality Gate
  ↓
Annotation
  ↓
Review Console
```

---

## 2. Evidence

| 项目 | 结果 |
|---|---|
| PDF Import | PASS |
| SHA256 identity | PASS |
| Source sealing | PASS |
| Source quality detection | PASS |
| Review Console | PASS |
| API exposure | PASS |
| Frontend build | PASS |

---

## 3. Test Evidence

| 类别 | 结果 |
|---|---|
| 全量 pytest | 425 passed |
| Quality Gate 单元测试 | 15/15 passed |
| Import E2E 测试 | 4/4 passed |
| Frontend TypeScript | 0 errors |
| API endpoints | 200/404 correct |

---

## 4. Confirmed Architecture

SourceQualityGate 正式确立为架构层：

```
Import → Seal → SourceQualityGate → Annotation → Resolve → Compile → Gate → Admission
```

- 纯函数（无 IO，确定性）
- 位于 Seal 后、Annotation 前（fail-loud before LLM consumption）
- QualityReport 落 source_meta 供 Review Console 展示

---

## 5. Critical Correction

**PDF Encoding False Alarm (BUG-V3-040 Resolved)**

初始判断 "PyMuPDF 中文编码失败" 不存在。实际为 Windows 终端编码显示问题。
Native extraction 正确提取中文文本。

核心教训：不要相信观察层输出，要相信 Source Artifact。

---

## 6. PUA Fix (BUG-V3-042 Resolved)

`_is_non_printable()` 排除 Private Use Area（Co, U+F000-U+F8FF）。
数学 PDF 用 PUA 编码符号（≥, ≤, →, 向量箭头）是合法的。

- PUA alone ≠ quality failure
- Cc/Cn still detected
- replacement alone still invalid

---

## 7. Deferred Capability

Resolver semantic reconstruction is not complete.

Known limitation (BUG-V3-041 Deferred → Phase I-2C):

- Mathematical formula fragmentation
- Symbol ordering
- Multi-line equation reconstruction

**Not a Source layer defect.** Source remains immutable factual extraction.

---

## 8. Key Insight

Native extraction succeeded; semantic reconstruction remains incomplete.

这是 V3 架构设计成功的体现——Source ≠ Semantic 边界成立。

Source layer 保存提取的事实；Resolver/Compiler 负责语义重建。
失败原因从"系统未知错误"变为"明确的领域能力边界"。

---

## 9. Next Phase

**Phase I-2C Resolver Robustness Validation**

目标不是让数学题 100% 解析，而是验证 Resolver 是否遵守：

| 原则 | 验证 |
|---|---|
| 不猜 | 无法确定就 incomplete |
| 可追溯 | 每个 semantic span 有 source_span |
| 可复现 | 同 source 得同 IR |

重点测试：正常文本 PDF / 数学公式 PDF / 图片题 PDF / 混排 PDF / OCR fallback PDF。

---

## 10. Git Commits

| Hash | Type | Description |
|---|---|---|
| ee4d08f | docs | Phase I-2 Revision Closure document |
| 1c31fdf | fix | PUA false positive (BUG-V3-042) |
| 0ef64ab | test | PUA regression tests |
| cf9d4b4 | docs | Status update |
| (this) | docs | Freeze + tag v3-phase-i2-closed |
