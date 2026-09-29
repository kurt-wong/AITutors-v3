# PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1

> **Authority (OD-002, Owner 2026-09-29): WORKING REFERENCE only.**
> 本文件**不是**正式 Authority Source。Authority assignment **DEFERRED** 至 D2/D3/D4（OD-003）closure。
> 不得据此声称 interface authority 已锚定；实现引用本文件时须标 `working reference / authority pending`。
> 权威裁决载体：本注记 + `EB008-P1-IMPLEMENTATION-NOTES.md §10`；不新建 Decision 文件。
> **D2（Owner 2026-09-29）= (b) 仅 §4.2–§4.6 M1–M5 可作接口依据（Interface reference only）。**
> 授权：接口边界 / IO 契约 / 模块职责 / 实现检查依据。**不**含 schema·migration·business semantic authority、**不**改 Frozen Spec、**不**自动进入 LIMITED Implementation。
> **排除**：§1 Identity 双轴模型（pending authority）· §2 仅原则参考（无实现义务）· §3/§4.7/§5 reference only（§5 禁令仍有效）。


> **性质**：Consumer Identity Verification 实现前最终收口。**IMPLEMENTATION READY DESIGN。NOT IMPLEMENTED。**
> **基准**：Contract v0.2 FROZEN @ `f4941ff`（sha256 `9c6b9063…7528`）· Design v1（同目录，本文件取代其为实现基准）
> **日期**：2026-09-16 · **状态**：IMPLEMENTATION READY DESIGN / NOT IMPLEMENTED / WAITING OWNER IMPLEMENTATION AUTHORIZATION
>
> **本轮禁令（Owner 指令原文）**：ZERO CODE · ZERO DATA · ZERO SCHEMA · ZERO CONTRACT CHANGE

---

## §0 与 Design v1 的差异（收口清单）

| # | 收口项 | v1 状态 | v1.1 修正 |
|---|---|---|---|
| 1 | Identity 状态模型 | `PASS / PASS_WITH_SEMANTIC_PENDING / FAIL` 三值混合 | **拆分为正交双轴**：Identity State `{VERIFIED, FAILED}` × Semantic State `{AVAILABLE, PENDING}`；**禁止 "identity pending"** |
| 2 | Verifier 数据流 | 三方比对，IR 参与身份判定 | **身份来源唯一 = raw bytes 重算**；IR 仅做一致性校验，**禁止 IR 作为身份来源** |
| 3 | 异常矩阵 | 8 场景 | **扩展至 13 场景**（+unicode bytes / CRLF-LF / trailing newline / path swap attack / stale IR） |
| 4 | 接口稳定性 | 签名草案 | **冻结 M1-M5 输入/输出/异常/状态码**，实现阶段直接使用 |

---

## §1 Identity 状态模型（收口 1）

### 1.1 正交双轴模型

**Design v1 的问题**：`PASS_WITH_SEMANTIC_PENDING` 把身份验证结果和语义可用性混在一个枚举里，导致「identity pending」这种不存在的状态被隐式表达。

**v1.1 修正**：拆分为两个正交维度，各自独立取值，互不影响。

```
┌─────────────────────────────────────────────────────────────┐
│                    正交双轴状态模型                           │
│                                                             │
│  Identity State (身份轴)          Semantic State (语义轴)    │
│  ┌─────────────────────┐         ┌─────────────────────┐   │
│  │ VERIFIED            │         │ AVAILABLE           │   │
│  │   sha 匹配，身份确认 │         │   IR 存在且一致      │   │
│  │                     │         │                     │   │
│  │ FAILED              │         │ PENDING             │   │
│  │   sha 不匹配/缺失    │         │   IR 缺失/不一致     │   │
│  └─────────────────────┘         └─────────────────────┘   │
│                                                             │
│  两轴独立判定，互不依赖。                                     │
│  Identity State 决定是否放行消费。                            │
│  Semantic State 决定语义层处理路径。                          │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 状态定义

| 轴 | 值 | 触发条件 | 下游动作 |
|---|---|---|---|
| **Identity State** | `VERIFIED` | `computed_sha == manifest_sha` | 放行，进入 Gate/Admission |
| | `FAILED` | `computed_sha != manifest_sha` 或 `manifest_sha is None` | **阻断消费**，不创建 DB 记录 |
| **Semantic State** | `AVAILABLE` | `ir_sha is not None and ir_sha == manifest_sha` | 语义层正常消费 |
| | `PENDING` | `ir_sha is None` 或 `ir_sha != manifest_sha` | 语义层标记待处理（OQ-21） |

### 1.3 组合矩阵

| Identity State | Semantic State | 含义 | 下游动作 |
|---|---|---|---|
| `VERIFIED` | `AVAILABLE` | 身份确认 + 语义可用 | 进入 Gate/Admission，语义正常消费 |
| `VERIFIED` | `PENDING` | 身份确认 + 语义待处理（16 份 Semantic Pending） | 进入 Gate/Admission，语义层标记 PENDING |
| `FAILED` | *(任意)* | 身份验证失败 | **阻断消费**，不创建 DB 记录 |
| *(任意)* | `PENDING` | — | 不影响身份判定 |

### 1.4 禁止项

| 禁止 | 原因 |
|---|---|
| ❌ "identity pending" | 身份只有 VERIFIED / FAILED 两态，不存在 pending |
| ❌ 用 Semantic State 推导 Identity State | 两轴独立，IR 缺失不使身份失效（DEC-020 DEC-B1 细化） |
| ❌ 用 Identity State 推导 Semantic State | 身份确认不保证 IR 存在 |

---

## §2 Verifier 数据流（收口 2）

### 2.1 身份来源唯一性

**Design v1 的问题**：M4 的三方比对逻辑中，IR sha 参与了身份判定（`ir_manifest_mismatch` 导致 FAIL），隐式把 IR 当作身份来源之一。

**v1.1 修正**：**身份来源唯一 = raw bytes 重算**。IR 仅做一致性校验，不是身份来源。

```
身份来源（唯一）：
    computed_source_sha256 = SHA256(raw bytes)
    身份判定 = (computed_source_sha256 == Manifest.source_content_sha256)

一致性校验（非身份来源）：
    IR.source_sha256 == Manifest.source_content_sha256
    → 仅用于 Semantic State 判定，不影响 Identity State
```

### 2.2 数据流图

```
┌──────────────┐
│ Source File  │
│ (raw bytes)  │
└──────┬───────┘
       │ read_bytes()
       ▼
┌──────────────┐     ┌──────────────────────────────────────┐
│ SHA256(bytes)│────►│ Identity Verification                 │
│ = computed   │     │                                      │
│   _source_   │     │  computed_source_sha256              │
│   sha256     │     │       ==                             │
└──────────────┘     │  Manifest.source_content_sha256      │
                     │       ?                              │
┌──────────────┐     │  YES → Identity State = VERIFIED     │
│ Manifest     │────►│  NO  → Identity State = FAILED       │
│ .source_     │     └──────────────────────────────────────┘
│  content_    │
│  sha256      │     ┌──────────────────────────────────────┐
└──────────────┘     │ Semantic Consistency Check           │
                     │  (仅当 Identity State = VERIFIED)     │
┌──────────────┐     │                                      │
│ IR           │────►│  IR.source_sha256                    │
│ .source_     │     │       ==                             │
│  sha256      │     │  Manifest.source_content_sha256      │
└──────────────┘     │       ?                              │
                     │  YES → Semantic State = AVAILABLE    │
                     │  NO  → Semantic State = PENDING      │
                     │  IR 缺失 → Semantic State = PENDING  │
                     └──────────────────────────────────────┘
```

### 2.3 验证步骤（精确顺序）

```
Step 1: raw_bytes = read_bytes(source_path)
        computed_source_sha256 = SHA256(raw_bytes)

Step 2: manifest_sha = Manifest.source_content_sha256
        if manifest_sha is None:
            Identity State = FAILED
            STOP (阻断消费)

Step 3: if computed_source_sha256 != manifest_sha:
            Identity State = FAILED
            STOP (阻断消费)

Step 4: Identity State = VERIFIED
        (继续语义一致性检查)

Step 5: ir_sha = IR.source_sha256  (IR 不存在时 ir_sha = None)
        if ir_sha is None or ir_sha != manifest_sha:
            Semantic State = PENDING
        else:
            Semantic State = AVAILABLE

Step 6: 输出 IdentityGateResult(
            identity_state = VERIFIED,
            semantic_state = AVAILABLE | PENDING
        )
        → 进入既有 Gate/Admission 链
```

### 2.4 禁止项

| 禁止 | 原因 |
|---|---|
| ❌ IR 作为身份来源 | 身份唯一来源 = raw bytes 重算（DEC-031 原则 1） |
| ❌ IR sha 参与 Identity State 判定 | IR 一致性仅影响 Semantic State |
| ❌ path 作为身份来源 | path 仅 locator（DEC-031 原则 1 + §1.3） |
| ❌ `sha256_hex` 作为身份计算函数 | canonical_json wrap，用途不同（V3 logical identity primitive） |

---

## §3 异常矩阵 v2（收口 3）

### 3.1 完整异常矩阵（13 场景）

| # | 场景 | 触发条件 | 检测模块 | Identity State | Semantic State | 下游动作 |
|---|---|---|---|---|---|---|
| F1 | **bytes 不存在** | `source_path.exists() == False` | M2 | `FAILED` | *(不判定)* | **FAIL-CLOSED**：阻断消费 |
| F2 | **bytes hash mismatch** | `computed_sha != manifest_sha` | M4 | `FAILED` | *(不判定)* | **FAIL-CLOSED**：阻断消费 |
| F3 | **manifest hash 缺失** | `manifest_sha is None` | M4 | `FAILED` | *(不判定)* | **FAIL-CLOSED**：阻断消费 |
| F4 | **IR hash mismatch** | `ir_sha != manifest_sha` | M4 | `VERIFIED` | `PENDING` | 放行，语义层标记 PENDING |
| F5 | **IR 缺失** | `ir_path.exists() == False` | M3 | `VERIFIED` | `PENDING` | 放行，语义层标记 PENDING |
| F6 | **manifest 缺失** | `manifest_path.exists() == False` | M1 | `FAILED` | *(不判定)* | **FAIL-CLOSED**：阻断消费 |
| F7 | **path 指向错误文件** | path 存在但内容被替换 | M2+M4 | `FAILED` | *(不判定)* | **FAIL-CLOSED**：阻断消费 |
| F8 | **duplicate identity** | 同一 sha 对应多个文件 | M4+M5 | `FAILED` | *(不判定)* | **FAIL-CLOSED**：阻断消费 |
| **F9** | **unicode bytes** | 文件含 BOM / 多字节 UTF-8 字符 | M2 | *(不影响判定)* | *(不影响判定)* | raw bytes 保真读取，sha 与 producer 对齐 |
| **F10** | **CRLF/LF difference** | Windows CRLF vs Unix LF | M2 | *(不影响判定)* | *(不影响判定)* | raw bytes 保真读取，不做 splitlines 规范化 |
| **F11** | **trailing newline** | 文件末尾有/无换行符 | M2 | *(不影响判定)* | *(不影响判定)* | raw bytes 保真读取，不做 strip |
| **F12** | **path swap attack** | path 指向被恶意替换的文件 | M2+M4 | `FAILED` | *(不判定)* | **FAIL-CLOSED**：阻断消费（同 F7，攻击视角） |
| **F13** | **stale IR** | IR 存在但对应旧版本 source | M3+M4 | `VERIFIED` | `PENDING` | 放行，语义层标记 PENDING（IR sha 不匹配） |

### 3.2 新增场景详细说明

#### F9: Unicode bytes

```
触发: 文件含 BOM (EF BB BF) / 多字节 UTF-8 字符（中文/emoji/特殊符号）
检测: M2 read_bytes() 保真读取，不做编码转换
判定: 不影响 Identity State（sha 与 producer 对齐即可）
动作: 正常进入验证链
```

**设计约束**：`read_bytes()` 返回原始字节序列，不做 UTF-8 解码，不做 BOM 剥离。producer 的 `source_content_sha256` 基于相同原始字节计算，因此 sha 可对齐。

#### F10: CRLF/LF difference

```
触发: 文件使用 Windows CRLF (\r\n) 或 Unix LF (\n)
检测: M2 read_bytes() 保真读取，不做 splitlines() 规范化
判定: 不影响 Identity State（sha 与 producer 对齐即可）
动作: 正常进入验证链
```

**设计约束**：这是 Design v1 中 R1 风险的运行时验证。`read_text()` + `splitlines()` 会把 CRLF → LF，导致 sha 漂移（FACT-031：6/12 DIFFER）。`read_bytes()` 保真读取，sha 与 producer 一致。

#### F11: Trailing newline

```
触发: 文件末尾有/无换行符 (\n)
检测: M2 read_bytes() 保真读取，不做 strip()
判定: 不影响 Identity State（sha 与 producer 对齐即可）
动作: 正常进入验证链
```

**设计约束**：`read_text()` + `splitlines()` 会丢失 trailing newline，导致 sha 漂移。`read_bytes()` 保真读取，sha 与 producer 一致。

#### F12: Path swap attack

```
触发: path 指向被恶意替换的文件（内容不同，但 path 相同）
检测: M2 重算 sha ≠ M1 manifest sha → "computed_manifest_mismatch"
判定: Identity State = FAILED
动作: FAIL-CLOSED：阻断消费
```

**设计约束**：这是 F7 的攻击视角。path 是 locator，不是 identity。任何 path 层面的篡改（替换文件/软链接/挂载点）都会导致 bytes 变化 → sha 变化 → FAILED。这是 path 非身份原则（DEC-031 原则 1）的运行时防御。

#### F13: Stale IR

```
触发: IR 存在，但对应旧版本 source（source 已更新，IR 未重新生成）
检测: M3 提取 ir_sha ≠ M1 manifest_sha → Semantic State = PENDING
判定: Identity State = VERIFIED（身份来自 raw bytes，不受 IR 影响）
动作: 放行，语义层标记 PENDING
```

**设计约束**：stale IR 不影响身份验证（身份唯一来源 = raw bytes 重算）。语义层标记 PENDING，等待 IR 重新生成（OQ-21 / 16 份 Semantic Pending 的扩展场景）。

### 3.3 异常矩阵分类汇总

| 类别 | 场景 | Identity State | 说明 |
|---|---|---|---|
| **阻断类**（FAIL-CLOSED） | F1/F2/F3/F6/F7/F8/F12 | `FAILED` | 身份验证失败，阻断消费 |
| **放行+语义待处理** | F4/F5/F13 | `VERIFIED` | 身份确认，语义层标记 PENDING |
| **不影响判定**（保真读取） | F9/F10/F11 | *(正常)* | raw bytes 保真，sha 与 producer 对齐 |

---

## §4 接口稳定性冻结（收口 4）

### 4.1 冻结声明

以下 M1-M5 接口签名、输入/输出类型、异常定义、状态码**已冻结**。实现阶段**直接使用**，不得修改。任何修改须 Owner 另行下令。

### 4.2 M1: Manifest Reader

```
文件: backend/scripts/preprocessing_consumer/identity/manifest_identity_reader.py

# ─── 数据类型（冻结）───

@dataclass(frozen=True)
class ManifestIdentity:
    source_content_sha256: str | None   # 64-char lowercase hex, or None if absent

# ─── 异常（冻结）───

class ManifestReadError(Exception):
    """Manifest 文件读取失败或字段格式非法。"""
    # 触发: 文件不存在 / JSON 解析失败 / sha 字段非 64 位小写 hex

# ─── 接口（冻结）───

def read_manifest_identity(manifest_path: Path) -> ManifestIdentity:
    """从 manifest JSON 中提取 source_content_sha256。

    输入: manifest_path: Path — manifest JSON 文件路径
    输出: ManifestIdentity(source_content_sha256=...)
    异常: ManifestReadError — 文件不存在 / JSON 解析失败 / sha 格式非法

    行为:
      - sha 字段不存在 → source_content_sha256 = None
      - sha 字段为空字符串 → source_content_sha256 = None
      - sha 字段非 64 位小写 hex → 抛 ManifestReadError
    """
```

### 4.3 M2: Raw Bytes Loader

```
文件: backend/scripts/preprocessing_consumer/identity/raw_bytes_loader.py

# ─── 数据类型（冻结）───

@dataclass(frozen=True)
class RawBytesIdentity:
    raw_bytes: bytes                    # 原始字节，保真 CRLF/BOM/trailing newline
    sha256: str                         # 64-char lowercase hex = SHA256(raw_bytes)

# ─── 异常（冻结）───

class SourceBytesNotFoundError(Exception):
    """Source 文件不存在。"""

class SourceBytesReadError(Exception):
    """Source 文件读取失败（权限 / IO 错误 / path 指向目录）。"""

# ─── 接口（冻结）───

def load_raw_bytes(source_path: Path) -> RawBytesIdentity:
    """读取 source 文件原始字节 + 计算 SHA-256。

    输入: source_path: Path — source .md 文件路径
    输出: RawBytesIdentity(raw_bytes=..., sha256=...)
    异常: SourceBytesNotFoundError — 文件不存在
          SourceBytesReadError — 文件读取失败

    行为:
      - 使用 read_bytes()，保真 CRLF/BOM/trailing newline/unicode
      - sha256 = hashlib.sha256(raw_bytes).hexdigest()
      - 禁止使用 read_text() / splitlines() / strip()
      - 禁止复用 hashing.sha256_hex（canonical_json wrap，用途不同）
    """
```

### 4.4 M3: IR Identity Reader

```
文件: backend/scripts/preprocessing_consumer/identity/ir_identity_reader.py

# ─── 数据类型（冻结）───

@dataclass(frozen=True)
class IRIdentity:
    source_sha256: str | None           # 64-char lowercase hex, or None if IR absent

# ─── 异常（冻结）───

class IRReadError(Exception):
    """IR 文件存在但读取失败或字段格式非法。"""

# ─── 接口（冻结）───

def read_ir_identity(ir_path: Path) -> IRIdentity:
    """从 producer IR JSON 中提取 source_sha256。

    输入: ir_path: Path — producer IR JSON 文件路径
    输出: IRIdentity(source_sha256=...)  # IR 不存在时 source_sha256=None
    异常: IRReadError — IR 文件存在但 JSON 解析失败或 sha 字段格式非法

    行为:
      - IR 不存在 → source_sha256 = None（Semantic Pending 正常态，不抛异常）
      - IR 存在但无 source_sha256 字段 → source_sha256 = None
      - IR 存在但 sha 字段非 64 位小写 hex → 抛 IRReadError
      - IR 仅用于 Semantic State 判定，不参与 Identity State 判定
    """
```

### 4.5 M4: Identity Verifier

```
文件: backend/scripts/preprocessing_consumer/identity/identity_verifier.py

# ─── 数据类型（冻结）───

@dataclass(frozen=True)
class IdentityState:
    """Identity State — 身份轴，仅两值。"""
    value: str                          # "VERIFIED" | "FAILED"
    mismatches: list[str]               # 失败原因列表，VERIFIED 时为空

@dataclass(frozen=True)
class SemanticState:
    """Semantic State — 语义轴，仅两值。"""
    value: str                          # "AVAILABLE" | "PENDING"
    reason: str | None                  # PENDING 时的原因，AVAILABLE 时为 None

@dataclass(frozen=True)
class VerificationResult:
    identity: IdentityState
    semantic: SemanticState | None      # identity=FAILED 时为 None（不判定语义）

# ─── 异常（冻结）───
# 无。M4 是纯函数，零 IO，零副作用，不抛异常。

# ─── 接口（冻结）───

def verify_identity(
    computed_sha: str,                  # SHA256(raw bytes)，来自 M2
    manifest_sha: str | None,           # Manifest.source_content_sha256，来自 M1
    ir_sha: str | None,                 # IR.source_sha256，来自 M3
) -> VerificationResult:
    """比对三方 sha，返回正交双轴状态。

    输入:
      computed_sha: str — SHA256(raw bytes)，64-char lowercase hex
      manifest_sha: str | None — Manifest 声明值
      ir_sha: str | None — IR 提取值（None = IR 缺失）

    输出: VerificationResult(identity=..., semantic=...)

    行为:
      # Step 1: Identity State 判定
      if manifest_sha is None:
          identity = IdentityState("FAILED", ["manifest_sha_missing"])
          return VerificationResult(identity, None)

      if computed_sha != manifest_sha:
          identity = IdentityState("FAILED", ["computed_manifest_mismatch"])
          return VerificationResult(identity, None)

      identity = IdentityState("VERIFIED", [])

      # Step 2: Semantic State 判定（仅当 identity=VERIFIED）
      if ir_sha is None:
          semantic = SemanticState("PENDING", "ir_absent")
      elif ir_sha != manifest_sha:
          semantic = SemanticState("PENDING", "ir_manifest_mismatch")
      else:
          semantic = SemanticState("AVAILABLE", None)

      return VerificationResult(identity, semantic)
    """
```

### 4.6 M5: Identity Gate

```
文件: backend/scripts/preprocessing_consumer/identity/identity_gate.py

# ─── 数据类型（冻结）───

@dataclass(frozen=True)
class IdentityGateDecision:
    identity_state: str                 # "VERIFIED" | "FAILED"
    semantic_state: str | None          # "AVAILABLE" | "PENDING" | None (identity=FAILED 时)
    reason: str                         # 人类可读的决策原因
    mismatches: list[str]               # 失败原因列表

# ─── 异常（冻结）───
# 无。M5 是纯函数，零 IO，零副作用，不抛异常。

# ─── 接口（冻结）───

def evaluate_identity(
    verification: VerificationResult,   # 来自 M4
) -> IdentityGateDecision:
    """汇总验证结果，做出放行/阻断决策。

    输入: verification: VerificationResult — M4 的输出
    输出: IdentityGateDecision(identity_state=..., semantic_state=..., reason=..., mismatches=[...])

    行为:
      if verification.identity.value == "FAILED":
          return IdentityGateDecision(
              identity_state="FAILED",
              semantic_state=None,
              reason="identity_verification_failed",
              mismatches=verification.identity.mismatches,
          )

      return IdentityGateDecision(
          identity_state="VERIFIED",
          semantic_state=verification.semantic.value,
          reason="identity_verified",
          mismatches=[],
      )

    下游动作:
      - identity_state="FAILED" → 阻断消费，不创建 Document/SourceVersion/Candidate
      - identity_state="VERIFIED" → 进入既有 Gate/Admission 链
        - semantic_state="AVAILABLE" → 语义层正常消费
        - semantic_state="PENDING" → 语义层标记 PENDING（OQ-21）
    """
```

### 4.7 接口冻结确认

| 模块 | 输入类型 | 输出类型 | 异常 | 状态码 |
|---|---|---|---|---|
| M1 | `Path` | `ManifestIdentity` | `ManifestReadError` | — |
| M2 | `Path` | `RawBytesIdentity` | `SourceBytesNotFoundError` / `SourceBytesReadError` | — |
| M3 | `Path` | `IRIdentity` | `IRReadError` | — |
| M4 | `str` / `str\|None` / `str\|None` | `VerificationResult` | 无 | `VERIFIED`/`FAILED` × `AVAILABLE`/`PENDING` |
| M5 | `VerificationResult` | `IdentityGateDecision` | 无 | 同上 |

**冻结状态**：以上签名、类型、异常、状态码**已冻结**。实现阶段直接使用，不得修改。任何修改须 Owner 另行下令。

---

## §5 设计冻结声明

### 5.1 收口完成清单

| # | 收口项 | 状态 |
|---|---|---|
| 1 | Identity 状态模型（正交双轴，禁止 "identity pending"） | ✅ 完成 |
| 2 | Verifier 数据流（身份来源唯一 = raw bytes，禁止 IR 作为身份来源） | ✅ 完成 |
| 3 | 异常矩阵 v2（13 场景，含 unicode/CRLF/newline/path swap/stale IR） | ✅ 完成 |
| 4 | 接口稳定性冻结（M1-M5 输入/输出/异常/状态码） | ✅ 完成 |

### 5.2 模块清单（冻结）

| 模块 | 文件 | 状态 |
|---|---|---|
| M1: Manifest Reader | `identity/manifest_identity_reader.py` | IMPLEMENTATION READY |
| M2: Raw Bytes Loader | `identity/raw_bytes_loader.py` | IMPLEMENTATION READY |
| M3: IR Identity Reader | `identity/ir_identity_reader.py` | IMPLEMENTATION READY |
| M4: Identity Verifier | `identity/identity_verifier.py` | IMPLEMENTATION READY |
| M5: Identity Gate | `identity/identity_gate.py` | IMPLEMENTATION READY |

### 5.3 异常矩阵清单（13 场景）

| 类别 | 场景 | 数量 |
|---|---|---|
| 阻断类（FAIL-CLOSED） | F1/F2/F3/F6/F7/F8/F12 | 7 |
| 放行+语义待处理 | F4/F5/F13 | 3 |
| 不影响判定（保真读取） | F9/F10/F11 | 3 |

### 5.4 状态

```
IMPLEMENTATION READY DESIGN
NOT IMPLEMENTED
WAITING OWNER IMPLEMENTATION AUTHORIZATION
```

**本文件是设计收口，不是实现令。实现须 Owner 单独下达。**
