# CR-005 — CONTRACT CHANGE RECORD：role=preprocessing 与 artifact_kind 映射

```text
Document ID:           CR-005
Title:                 CONTRACT CHANGE RECORD — role=preprocessing / artifact_kind mapping
Document Type:         Contract Change Record
Authority Level:       L1
Status:                ACTIVE
Normative:             YES（对 L0 / Frozen Spec 10 的最小生效授权与 provenance）
Purpose:               将 Owner 已批准的最小变更 incorporated 进 Frozen Spec 10：
                       (1) role 枚举补入 preprocessing；
                       (2) role=preprocessing → artifact_kind=canonical_l1；
                       (3) 其余 role 的 artifact_kind 维持 raw_l1，docx 语义本轮不改。
Owner Authorization:   B1-R2 一次性裁决表（2026-10-10）·「role=preprocessing 纳入 Spec 批准正式最小变更」
                       「artifact_kind：preprocessing → canonical_l1 固化为明确规则」
Derives From:          Frozen Spec 10 §4.2 · models/source.py · seal.py · test_identity_phase_a
May Change:            Spec 10 §4.2 role 枚举与 artifact_kind 映射说明 · 本 Change Record 自身
Must Not Change:       表结构 / UNIQUE 约束 · 哈希算法 · path 非身份原则 ·
                       role/provider 封闭配对（除新增 preprocessing≡preprocessing）·
                       docx / native / ocr_* 既有语义 · Schema migration · Admission 运行时
Supersedes:            —
Superseded By:         —
Gate State Authority:  NO
```

## 0. 变更分类

| 项 | 内容 |
|---|---|
| 变更类型 | 最小枚举扩展 + 映射固化 |
| 影响面 | Spec 文本；`validate_artifact_compatibility` / Seal 写入行为 |
| 不做的事 | 不重写 Spec；不改 docx；不迁移数据；不启动全仓审计 |

## 1. 变更内容

### 1.1 role 枚举（Spec 10 §4.2）

| 修改前 | 修改后 |
|---|---|
| `native / ocr_ppsv3 / ocr_ppsvl / docx / canonical` | `native / ocr_ppsv3 / ocr_ppsvl / docx / preprocessing / canonical` |

依据：`models/source.py` `_ROLE_PROVIDER_PAIRS` 已含 `preprocessing`，Seal/Repository 已支持；本变更使规范与实现一致，消除登记缺口。

### 1.2 role/provider 封闭配对

新增：`preprocessing ≡ preprocessing`。  
既有配对不变：`ocr_ppsv3 ≡ ppsv3`、`ocr_ppsvl ≡ paddleocr-vl`、`native ≡ native`、`docx ≡ docx`、`canonical` 无 provider。

### 1.3 artifact_kind 映射

| role | artifact_kind | 状态 |
|---|---|---|
| `preprocessing` | **`canonical_l1`** | 本变更固化 |
| `native` / `ocr_ppsv3` / `ocr_ppsvl` / `docx` | `raw_l1` | 不变 |
| `canonical`（非 Seal 路径） | `canonical_l1` | 不变 |

依据：`test_identity_phase_a` 已断言 `preprocessing/preprocessing/canonical_l1` 合法且可持久化；GAP-2 锁 runner 输出 `canonical_l1`。

## 2. 实现一致性要求

- role → artifact_kind 的映射必须有**单一权威实现**（不得 Seal 与 runner 各写各的）。
- `documents.original_sha256` **仅**原始 PDF/DOCX 字节 SHA-256（E-DA-38）。
- `source_content_sha256` = Markdown 原始字节 SHA-256，落 Source Version 层。

## 3. 回归要求

- `test_identity_phase_a`：preprocessing/canonical_l1 仍合法。
- seal 写入：preprocessing 路径 artifact_kind = canonical_l1；native 路径仍 raw_l1。
- 既有 native Source Version 数据不受影响。

## 4. Provenance

```text
Owner Decision:  B1-R2 一次性裁决（2026-10-10）
Applied by:      MIMO M1-A
Spec file:       Docs/V3_SPEC/10_Data_Model.md
Code authority:  app/models/source.py :: artifact_kind_for_role()
```

---

*CR-005 · 最小 Frozen Spec 变更 · 2026-10-10 · M1-A 授权实施*
