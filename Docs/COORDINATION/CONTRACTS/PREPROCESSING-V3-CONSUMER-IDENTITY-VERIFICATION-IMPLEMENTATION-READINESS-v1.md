# PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-IMPLEMENTATION-READINESS-v1

> **性质**：Consumer Identity Verification Implementation Authorization 前置审查。**DESIGN REVIEW ONLY。ZERO CODE。**
> **基准**：Contract v0.2 FROZEN @ `f4941ff` · Design v1.1（同目录）
> **日期**：2026-09-16 · **状态**：DESIGN REVIEW ONLY / NOT IMPLEMENTED / WAITING OWNER IMPLEMENTATION AUTHORIZATION
>
> **本轮禁令（Owner 指令原文）**：ZERO CODE · ZERO DATA · ZERO SCHEMA · ZERO CONTRACT CHANGE
> **禁止修改**：Contract Artifact f4941ff · Producer manifest · source bytes · IR 数据 · schema · Gate/Admission 业务逻辑

---

## §0 审查概要

| # | 审查项 | Design v1.1 是否满足 | 处置 |
|---|---|---|---|
| 1 | Identity / Semantic 双轴完全正交 | ✅ 满足 | 确认 |
| 2 | Identity 来源唯一（raw bytes SHA256） | ✅ 满足 | 确认 |
| 3 | Duplicate identity 语义 | ⚠️ 需精化 | 本文件 §3 修正 |
| 4 | 模块职责边界 | ✅ 满足 | 确认 |
| 5 | 接口冻结 | ✅ 满足 | 确认 |

---

## §1 审查 1：Identity / Semantic 双轴完全正交

### 1.1 确认

Design v1.1 §1 定义了正交双轴模型：

| 轴 | 值 | 判定依据 | 下游作用 |
|---|---|---|---|
| **Identity State** | `VERIFIED` / `FAILED` | `computed_sha == manifest_sha` | 决定是否放行消费 |
| **Semantic State** | `AVAILABLE` / `PENDING` | `ir_sha == manifest_sha` | 决定语义层处理路径 |

**两轴独立判定，互不推导。**

### 1.2 禁止项确认

Design v1.1 §1.4 明确禁止：

- ❌ "identity pending" — 身份只有 VERIFIED / FAILED 两态
- ❌ 用 Semantic State 推导 Identity State
- ❌ 用 Identity State 推导 Semantic State

### 1.3 结论

```
PASS_WITH_SEMANTIC_PENDING 等混合状态已消除。
正交双轴模型满足实现要求。
✅ 审查通过
```

---

## §2 审查 2：Identity 来源唯一

### 2.1 确认

Design v1.1 §2 定义了唯一身份来源：

```
身份来源（唯一）：
    computed_source_sha256 = SHA256(raw bytes)
    身份判定 = (computed_source_sha256 == Manifest.source_content_sha256)
```

### 2.2 禁止项确认

Design v1.1 §2.4 明确禁止：

| 禁止项 | 原因 | 对应现状 |
|---|---|---|
| ❌ IR 作为身份来源 | 身份唯一来源 = raw bytes 重算 | v1 问题已修正 |
| ❌ IR sha 参与 Identity State 判定 | IR 一致性仅影响 Semantic State | v1 问题已修正 |
| ❌ path 作为身份来源 | path 仅 locator | — |
| ❌ `sha256_hex` 作为身份计算函数 | canonical_json wrap，V3 logical identity primitive | hashing.py:60-62 |
| ❌ text normalization hash | `read_text()` + `splitlines()` 导致 CRLF/trailing newline 漂移 | FACT-031：6/12 DIFFER |

### 2.3 结论

```
身份来源唯一 = SHA256(raw bytes)。
IR / canonical_json / text normalization hash 均排除。
✅ 审查通过
```

---

## §3 审查 3：Duplicate Identity 语义

### 3.1 问题

Design v1.1 F8 表述为「同一 sha 对应多个文件 → FAILED」。该表述**过于粗放**，未区分两种本质不同的场景。

### 3.2 Owner 精确语义

| 场景 | 定义 | 判定 | 说明 |
|---|---|---|---|
| **ALLOWED** | same content hash + different locator | **放行** | 多份内容完全相同的文件位于不同路径（合法副本） |
| **FORBIDDEN** | same identity key + conflicting content | **阻断** | 同一 identity key（source_content_sha256）被声明但指向不同内容 |

### 3.3 修正后的 F8

**原 F8**（v1.1，过于粗放）：

| F8 | duplicate identity | 同一 sha 对应多个文件 | M4+M5 | FAILED | FAIL-CLOSED |

**修正 F8**（Readiness v1）：

| # | 场景 | 触发条件 | 检测模块 | Identity State | Semantic State | 下游动作 |
|---|---|---|---|---|---|---|
| **F8a** | **same content, different locator** | 同一 sha 值出现在多个 manifest 中，指向不同 path | M4+M5 | `VERIFIED` | 逐份独立判定 | **允许**：各文件独立进入验证链 |
| **F8b** | **conflicting content for same identity** | 同一 path 声明了特定 sha，但实际 bytes 计算结果不同 | M2+M4 | `FAILED` | *(不判定)* | **FAIL-CLOSED**：阻断消费 |

### 3.4 设计依据

```
F8a: same content hash + different locator → ALLOWED
  理由: 身份属于内容（DEC-031 原则 1），同一内容的多份副本是合法的。
        path 仅 locator，不同 path 不改变身份判定。
        例: docs/a.md 和 backup/a.md 内容完全相同 → sha 相同 → 两份独立放行。

F8b: same identity key + conflicting content → FORBIDDEN
  理由: Manifest 声明的 sha 与实际 bytes 不一致 = 身份伪造或篡改。
        这就是 F2 (bytes hash mismatch) 的具体表现，在此标记为独立场景。
        例: manifest 声明 sha=X，但文件实际 sha=Y → FAILED，阻断消费。
```

### 3.5 结论

```
Duplicate identity 语义已精化。
ALLOWED: same content hash + different locator（合法副本）。
FORBIDDEN: same identity key + conflicting content（篡改/伪造）。
✅ 审查通过（修正后）
```

---

## §4 审查 4：模块职责边界

### 4.1 确认

Design v1.1 §4 冻结了 M1-M5 完整接口，每模块职责单一：

| 模块 | 职责 | 输入 | 输出 | 不做的事 |
|---|---|---|---|---|
| **M1** Manifest Reader | 只读取 manifest identity | `Path` | `ManifestIdentity` | 不读 source bytes，不读 IR |
| **M2** Raw Bytes Loader | 只负责 bytes + raw SHA256 | `Path` | `RawBytesIdentity` | 不读 manifest，不做文本规范化 |
| **M3** IR Reader | 只负责 IR identity metadata | `Path` | `IRIdentity` | 不参与身份判定 |
| **M4** Identity Verifier | 只比较 identity | 三方 sha | `VerificationResult` | 零 IO，零副作用，纯函数 |
| **M5** Consumer Identity Gate | 只执行 fail-closed decision | `VerificationResult` | `IdentityGateDecision` | 零 IO，零副作用，纯函数 |

### 4.2 职责边界审计

| 检查项 | 结果 |
|---|---|
| M1 不做 source 读取 | ✅ 仅解析 manifest JSON |
| M2 不做文本规范化 | ✅ `read_bytes()` 保真读取，禁止 `read_text()/splitlines()/strip()` |
| M3 不参与 Identity State | ✅ 仅用于 Semantic State 判定 |
| M4 零 IO | ✅ 纯函数，输入为三方 sha 字符串 |
| M5 零 IO | ✅ 纯函数，输入为 VerificationResult |

### 4.3 结论

```
M1-M5 各模块职责单一，边界清晰。
无越权操作，无隐式依赖。
✅ 审查通过
```

---

## §5 审查 5：接口冻结确认

### 5.1 确认

Design v1.1 §4 已冻结 M1-M5 接口签名、数据类型、异常定义、状态码。本审查逐项确认：

| 模块 | 数据类型 | 异常 | 状态码 |
|---|---|---|---|
| M1 | `ManifestIdentity(source_content_sha256: str\|None)` | `ManifestReadError` | — |
| M2 | `RawBytesIdentity(raw_bytes: bytes, sha256: str)` | `SourceBytesNotFoundError` / `SourceBytesReadError` | — |
| M3 | `IRIdentity(source_sha256: str\|None)` | `IRReadError` | — |
| M4 | `VerificationResult(identity: IdentityState, semantic: SemanticState\|None)` | 无 | `VERIFIED`/`FAILED` × `AVAILABLE`/`PENDING` |
| M5 | `IdentityGateDecision(identity_state: str, semantic_state: str\|None, reason: str, mismatches: list[str])` | 无 | 同上 |

### 5.2 结论

```
M1-M5 接口签名、数据类型、异常定义、状态码已冻结。
实现阶段直接使用，不得修改。
✅ 审查通过
```

---

## §6 审查总结

### 6.1 四项 Owner 要求审查结果

| # | Owner 要求 | Design v1.1 | Readiness 修正 | 最终状态 |
|---|---|---|---|---|
| 1 | 双轴完全正交，禁止混合状态 | ✅ | — | **确认** |
| 2 | Identity 来源唯一 = raw bytes SHA256 | ✅ | — | **确认** |
| 3 | Duplicate identity 语义 | ⚠️ F8 过粗 | F8 拆分为 F8a/F8b | **修正后确认** |
| 4 | 模块职责边界 | ✅ | — | **确认** |

### 6.2 实现链确认

Owner 要求的实现链：

```
raw bytes
    ↓ SHA256(raw bytes)
Manifest verification
    ↓ IR consistency check
Consumer Identity Gate
    ↓ existing Gate/Admission
```

Design v1.1 §2.3 的验证步骤精确匹配此链。✅

### 6.3 三层边界确认

| 边界 | 定义 | 状态 |
|---|---|---|
| Requirement ≠ Capability | 有需求 ≠ 已实现 | ✅ 五能力仍 NOT IMPLEMENTED |
| Design ≠ Implementation | 设计冻结 ≠ 实现授权 | ✅ 本文件明确声明 |
| Consumer ≠ Producer | 身份验证是 Consumer 职责 | ✅ M1-M5 全部在 Consumer 侧 |

### 6.4 最终状态

```
IMPLEMENTATION READINESS: CONFIRMED
Design v1.1: APPROVED (with F8 refinement)
NOT IMPLEMENTED
WAITING OWNER IMPLEMENTATION AUTHORIZATION
```

**本文件是实现前置审查，不是实现令。实现须 Owner 单独下达。**
