# PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1

> **性质**：Consumer Identity Verification 实现设计冻结。**DESIGN ONLY。NOT IMPLEMENTED。**
> **基准**：Contract v0.2 FROZEN @ `f4941ff`（sha256 `9c6b9063…7528`）· Implementation Plan v1（同目录）
> **日期**：2026-09-16 · **状态**：DESIGN ONLY / NOT IMPLEMENTED / WAITING IMPLEMENTATION AUTHORIZATION
>
> **本轮禁令（Owner 指令原文）**：ZERO CODE · ZERO DATA · ZERO SCHEMA · ZERO CONTRACT CHANGE

---

## §0 范围与禁令

### 0.1 本轮做什么

- 模块设计（5 个模块：输入 / 输出 / 责任边界 / 禁止行为）
- 接口设计（5 个接口：签名 / 返回类型 / 异常约定）
- Failure Matrix（8 种失败场景，全部 fail-closed）
- Test Plan（Unit / Integration / Negative）

### 0.2 本轮不做什么

| 禁令 | 范围 |
|---|---|
| ZERO CODE | 不写任何 `.py` 文件 |
| ZERO DATA | 不修改任何 manifest / IR / source 数据 |
| ZERO SCHEMA | 不修改 `models/source.py` / `models/snapshot.py` / Alembic |
| ZERO CONTRACT CHANGE | 不修改 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` @ `f4941ff` |

### 0.3 与 Implementation Plan v1 的关系

Implementation Plan v1 = 实现路径提案（What & Why）。
本文件 = 设计冻结（How，精确到模块边界 / 接口签名 / 失败处理）。
**本文件取代 Implementation Plan v1 中 §3 的模糊描述，是实现阶段的唯一设计基准。**

---

## §1 模块设计

### 模块总览

```
┌─────────────────────────────────────────────────────────────┐
│                    Identity Verification Pipeline            │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Manifest     │    │  Raw Bytes   │    │  IR Identity │  │
│  │  Reader       │    │  Loader      │    │  Reader      │  │
│  │  (M1)         │    │  (M2)        │    │  (M3)        │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Identity Verifier (M4)                   │  │
│  │  compare(manifest_sha, recomputed_sha, ir_sha)        │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Identity Gate (M5)                       │  │
│  │  PASS / PASS_WITH_SEMANTIC_PENDING / FAIL             │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│              PASS ──────┼────── FAIL                        │
│                         │        │                          │
│                         ▼        ▼                          │
│              ┌──────────────┐  ┌──────────────┐            │
│              │ Gate/        │  │ Block +      │            │
│              │ Admission    │  │ Log + Skip   │            │
│              │ (existing)   │  │ (no DB write)│            │
│              └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

### M1: Manifest Reader

| 维度 | 内容 |
|---|---|
| **职责** | 从 manifest JSON 中提取 `source_content_sha256` 字段 |
| **输入** | `manifest_path: Path`（manifest JSON 文件路径） |
| **输出** | `ManifestIdentity` dataclass：`source_content_sha256: str \| None` |
| **责任边界** | 只读取，不验证，不比对。读取失败 → 抛 `ManifestReadError`。 |
| **禁止行为** | ❌ 不修改 manifest 文件 ❌ 不做 sha 比对 ❌ 不读取 source 文件 ❌ 不读取 IR 文件 |

**关键设计**：
- `source_content_sha256` 字段在 manifest JSON 中可能不存在（旧文件未回填）→ 返回 `None`
- 字段存在但为空字符串 → 视为 `None`
- 字段存在但格式非法（非 64 位小写 hex）→ 抛 `ManifestReadError`

---

### M2: Raw Bytes Loader

| 维度 | 内容 |
|---|---|
| **职责** | 获取 source 文件的原始字节 + 独立计算 SHA-256 |
| **输入** | `source_path: Path`（source .md 文件路径） |
| **输出** | `RawBytesIdentity` dataclass：`raw_bytes: bytes` · `sha256: str` |
| **责任边界** | 只读文件 + 计算 hash，不做比对，不读 manifest，不读 IR。 |
| **禁止行为** | ❌ 不用 `read_text()` ❌ 不做 `splitlines()` ❌ 不复用 `hashing.sha256_hex` ❌ 不修改 source 文件 |

**关键设计**：
- `read_bytes()` 直接读二进制，保真 CRLF / trailing newline
- `hashlib.sha256(raw_bytes).hexdigest()` — 独立函数，与 `hashing.sha256_hex` 并存
- 文件不存在 → 抛 `SourceBytesNotFoundError`
- 文件读取失败（权限 / IO 错误）→ 抛 `SourceBytesReadError`

---

### M3: IR Identity Reader

| 维度 | 内容 |
|---|---|
| **职责** | 从 producer IR 文件中提取 `source_sha256` 字段 |
| **输入** | `ir_path: Path`（producer IR JSON 文件路径） |
| **输出** | `IRIdentity` dataclass：`source_sha256: str \| None` |
| **责任边界** | 只读取，不验证，不比对。IR 不存在 → 返回 `None`（Semantic Pending）。 |
| **禁止行为** | ❌ 不修改 IR 文件 ❌ 不做 sha 比对 ❌ 不读取 source 文件 ❌ 不读取 manifest 文件 |

**关键设计**：
- IR 不存在 → 返回 `None`（16 份 Semantic Pending 的正常态，不是错误）
- IR 存在但无 `source_sha256` 字段 → 返回 `None`
- IR 存在但字段格式非法 → 抛 `IRReadError`
- **IR 不存在 ≠ FAIL** — 身份验证不依赖 IR 存在（DEC-020 DEC-B1 细化：source 身份自足）

---

### M4: Identity Verifier

| 维度 | 内容 |
|---|---|
| **职责** | 比对三方 sha：manifest 声明值 / 重算值 / IR 提取值 |
| **输入** | `manifest_sha: str \| None` · `recomputed_sha: str` · `ir_sha: str \| None` |
| **输出** | `VerificationResult` dataclass：`status: str` · `mismatch_detail: list[str]` |
| **责任边界** | 只做比对，不读文件，不写文件，不阻断流程。 |
| **禁止行为** | ❌ 不读文件 ❌ 不写文件 ❌ 不做 IO ❌ 不抛异常（结果通过返回值传递） |

**比对逻辑**：

```
verify(manifest_sha, recomputed_sha, ir_sha) → VerificationResult:
    mismatches = []

    # 1. manifest sha 缺失
    if manifest_sha is None:
        mismatches.append("manifest_sha_missing")

    # 2. manifest sha != recomputed sha
    if manifest_sha is not None and manifest_sha != recomputed_sha:
        mismatches.append("manifest_recomputed_mismatch")

    # 3. IR sha 存在但 != manifest sha
    if ir_sha is not None and manifest_sha is not None and ir_sha != manifest_sha:
        mismatches.append("ir_manifest_mismatch")

    # 4. IR sha 存在但 manifest sha 缺失（无法比对）
    if ir_sha is not None and manifest_sha is None:
        mismatches.append("ir_present_manifest_missing")

    status = "PASS" if not mismatches else "FAIL"
    return VerificationResult(status=status, mismatch_detail=mismatches)
```

---

### M5: Identity Gate

| 维度 | 内容 |
|---|---|
| **职责** | 汇总验证结果，做出放行/阻断决策 |
| **输入** | `verification: VerificationResult` · `ir_sha: str \| None` |
| **输出** | `IdentityGateDecision` dataclass：`decision: str` · `reason: str` · `mismatches: list[str]` |
| **责任边界** | 只做决策，不读文件，不写文件，不修改 DB。 |
| **禁止行为** | ❌ 不读文件 ❌ 不写 DB ❌ 不修改 Gate/Admission ❌ 不做静默 fallback |

**决策逻辑**：

```
evaluate(verification, ir_sha) → IdentityGateDecision:
    if verification.status == "FAIL":
        return IdentityGateDecision(
            decision="FAIL",
            reason="identity_verification_failed",
            mismatches=verification.mismatch_detail,
        )

    if ir_sha is None:
        return IdentityGateDecision(
            decision="PASS_WITH_SEMANTIC_PENDING",
            reason="identity_verified_ir_absent",
            mismatches=[],
        )

    return IdentityGateDecision(
        decision="PASS",
        reason="identity_verified",
        mismatches=[],
    )
```

**决策语义**：

| Decision | 含义 | 下游动作 |
|---|---|---|
| `PASS` | 身份验证通过，IR 存在且一致 | 进入既有 Gate/Admission 链 |
| `PASS_WITH_SEMANTIC_PENDING` | 身份验证通过，IR 不存在（Semantic Pending） | 进入既有 Gate/Admission 链（语义层另行处理） |
| `FAIL` | 身份验证失败 | **阻断消费**，不创建 Document/SourceVersion/Candidate，记录失败原因 |

---

## §2 接口设计

### 2.1 Manifest Reader 接口

```
文件: backend/scripts/preprocessing_consumer/identity/manifest_identity_reader.py

@dataclass(frozen=True)
class ManifestIdentity:
    source_content_sha256: str | None

class ManifestReadError(Exception):
    """Manifest 文件读取失败或字段格式非法。"""

def read_manifest_identity(manifest_path: Path) -> ManifestIdentity:
    """从 manifest JSON 中提取 source_content_sha256。

    Args:
        manifest_path: manifest JSON 文件路径

    Returns:
        ManifestIdentity(source_content_sha256=...)

    Raises:
        ManifestReadError: 文件不存在 / JSON 解析失败 / sha 字段格式非法
    """
```

**边界**：
- 不修改 manifest 文件（只读）
- 不修改 schema（纯 Python dataclass，非 ORM）
- 不修改 Producer 数据

---

### 2.2 Raw Bytes Loader 接口

```
文件: backend/scripts/preprocessing_consumer/identity/raw_bytes_loader.py

@dataclass(frozen=True)
class RawBytesIdentity:
    raw_bytes: bytes
    sha256: str  # 64-char lowercase hex

class SourceBytesNotFoundError(Exception):
    """Source 文件不存在。"""

class SourceBytesReadError(Exception):
    """Source 文件读取失败（权限 / IO 错误）。"""

def load_raw_bytes(source_path: Path) -> RawBytesIdentity:
    """读取 source 文件原始字节 + 计算 SHA-256。

    Args:
        source_path: source .md 文件路径

    Returns:
        RawBytesIdentity(raw_bytes=..., sha256=...)

    Raises:
        SourceBytesNotFoundError: 文件不存在
        SourceBytesReadError: 文件读取失败
    """
```

**边界**：
- 不修改 source 文件（只读）
- 不复用 `hashing.sha256_hex`（独立函数）
- 不修改 `source_loader.py`（现有文本管线不动）

---

### 2.3 IR Identity Reader 接口

```
文件: backend/scripts/preprocessing_consumer/identity/ir_identity_reader.py

@dataclass(frozen=True)
class IRIdentity:
    source_sha256: str | None

class IRReadError(Exception):
    """IR 文件存在但读取失败或字段格式非法。"""

def read_ir_identity(ir_path: Path) -> IRIdentity:
    """从 producer IR JSON 中提取 source_sha256。

    Args:
        ir_path: producer IR JSON 文件路径

    Returns:
        IRIdentity(source_sha256=...)  # IR 不存在时 source_sha256=None

    Raises:
        IRReadError: IR 文件存在但 JSON 解析失败或 sha 字段格式非法
    """
```

**边界**：
- 不修改 IR 文件（只读）
- 不修改 V3 自建 IR（`IRBuilder.build()` 不动）
- IR 不存在 → 返回 `None`，不抛异常（Semantic Pending 正常态）

---

### 2.4 Identity Verifier 接口

```
文件: backend/scripts/preprocessing_consumer/identity/identity_verifier.py

@dataclass(frozen=True)
class VerificationResult:
    status: str  # "PASS" | "FAIL"
    mismatch_detail: list[str]

def verify_identity(
    manifest_sha: str | None,
    recomputed_sha: str,
    ir_sha: str | None,
) -> VerificationResult:
    """比对三方 sha，返回验证结果。

    Args:
        manifest_sha: Manifest 声明的 source_content_sha256
        recomputed_sha: Raw Bytes Loader 重算的 SHA-256
        ir_sha: IR Identity Reader 提取的 source_sha256

    Returns:
        VerificationResult(status=..., mismatch_detail=[...])
    """
```

**边界**：
- 纯函数，零 IO，零副作用
- 不抛异常（结果通过返回值传递）
- 不修改任何文件 / DB

---

### 2.5 Identity Gate 接口

```
文件: backend/scripts/preprocessing_consumer/identity/identity_gate.py

@dataclass(frozen=True)
class IdentityGateDecision:
    decision: str  # "PASS" | "PASS_WITH_SEMANTIC_PENDING" | "FAIL"
    reason: str
    mismatches: list[str]

def evaluate_identity(
    verification: VerificationResult,
    ir_sha: str | None,
) -> IdentityGateDecision:
    """汇总验证结果，做出放行/阻断决策。

    Args:
        verification: Identity Verifier 的输出
        ir_sha: IR Identity Reader 提取的 source_sha256

    Returns:
        IdentityGateDecision(decision=..., reason=..., mismatches=[...])
    """
```

**边界**：
- 纯函数，零 IO，零副作用
- 不修改 DB（阻断 = 不写入，不是删除）
- 不修改 Gate/Admission（前置闸门，不侵入现有链）

---

### 2.6 模块依赖关系

```
manifest_identity_reader.py  ──┐
                               ├──► identity_verifier.py ──► identity_gate.py
raw_bytes_loader.py          ──┤
                               │
ir_identity_reader.py        ──┘
```

- 四个底层模块（M1/M2/M3/M4）相互独立，可并行实现
- M5 依赖 M4 的输出
- 所有模块位于 `backend/scripts/preprocessing_consumer/identity/` 子目录
- 不修改任何现有文件（`manifest_reader.py` / `source_loader.py` / `hashing.py` / `runner_b2.py` 不动）

---

## §3 Failure Matrix

### 3.1 八种失败场景

| # | 场景 | 触发条件 | 检测模块 | 判定 | 下游动作 |
|---|---|---|---|---|---|
| F1 | **bytes 不存在** | `source_path` 指向的文件不存在 | M2 | `SourceBytesNotFoundError` | **FAIL-CLOSED**：阻断消费，不创建 DB 记录 |
| F2 | **bytes hash mismatch** | 重算 sha ≠ manifest 声明 sha | M4 | `manifest_recomputed_mismatch` | **FAIL-CLOSED**：阻断消费，不创建 DB 记录 |
| F3 | **manifest hash mismatch** | manifest sha 字段缺失或为空 | M4 | `manifest_sha_missing` | **FAIL-CLOSED**：阻断消费，不创建 DB 记录 |
| F4 | **IR hash mismatch** | IR sha ≠ manifest sha | M4 | `ir_manifest_mismatch` | **FAIL-CLOSED**：阻断消费，不创建 DB 记录 |
| F5 | **IR 缺失** | IR 文件不存在 | M3 | `ir_sha = None` | **NOT FAIL**：`PASS_WITH_SEMANTIC_PENDING`，身份验证通过 |
| F6 | **manifest 缺失** | manifest 文件不存在 | M1 | `ManifestReadError` | **FAIL-CLOSED**：阻断消费，不创建 DB 记录 |
| F7 | **path 指向错误文件** | path 存在但内容被替换 | M2+M4 | `manifest_recomputed_mismatch` | **FAIL-CLOSED**：阻断消费，不创建 DB 记录 |
| F8 | **duplicate identity** | 同一 sha 对应多个不同文件 | M4+M5 | `manifest_recomputed_mismatch` 或运行时检测 | **FAIL-CLOSED**：阻断消费，不创建 DB 记录 |

### 3.2 详细说明

#### F1: bytes 不存在

```
触发: source_path.exists() == False
检测: M2 load_raw_bytes() → SourceBytesNotFoundError
判定: FAIL
动作: 不创建 Document / SourceVersion / Candidate；记录 "source_bytes_not_found"
```

**Contract 依据**：§5.6.2「fail-closed（任何关键验证失败 → 阻断消费）」

#### F2: bytes hash mismatch

```
触发: hashlib.sha256(raw_bytes).hexdigest() != manifest.source_content_sha256
检测: M4 verify_identity() → "manifest_recomputed_mismatch"
判定: FAIL
动作: 不创建 Document / SourceVersion / Candidate；记录 "bytes_hash_mismatch"
```

**Contract 依据**：§5.6.2「Manifest identity（重算 SHA256(bytes) == Manifest.source_content_sha256）」

#### F3: manifest hash mismatch

```
触发: manifest.source_content_sha256 is None 或 ""
检测: M4 verify_identity() → "manifest_sha_missing"
判定: FAIL
动作: 不创建 Document / SourceVersion / Candidate；记录 "manifest_sha_missing"
```

**Contract 依据**：§5.6.1 第 1 项「Manifest identity verification」

#### F4: IR hash mismatch

```
触发: ir.source_sha256 != manifest.source_content_sha256
检测: M4 verify_identity() → "ir_manifest_mismatch"
判定: FAIL
动作: 不创建 Document / SourceVersion / Candidate；记录 "ir_hash_mismatch"
```

**Contract 依据**：§5.6.2「IR identity（IR.source_content_sha256 == Manifest.source_content_sha256）」

#### F5: IR 缺失

```
触发: ir_path.exists() == False
检测: M3 read_ir_identity() → IRIdentity(source_sha256=None)
判定: PASS_WITH_SEMANTIC_PENDING（不是 FAIL）
动作: 继续进入 Gate/Admission；语义层另行处理（OQ-21）
```

**Contract 依据**：§0.1 冻结项②「16 Semantic Pending」；DEC-020 DEC-B1 细化「source 身份不依赖 IR 存在」

#### F6: manifest 缺失

```
触发: manifest_path.exists() == False
检测: M1 read_manifest_identity() → ManifestReadError
判定: FAIL
动作: 不创建 Document / SourceVersion / Candidate；记录 "manifest_not_found"
```

**Contract 依据**：§5.6.1 第 1 项「Manifest identity verification」

#### F7: path 指向错误文件

```
触发: path 存在，但文件内容被替换（篡改 / 误覆盖）
检测: M2 重算 sha ≠ M1 manifest sha → "manifest_recomputed_mismatch"
判定: FAIL
动作: 不创建 Document / SourceVersion / Candidate；记录 "path_content_mismatch"
```

**Contract 依据**：§1.3「path → 找文件；SHA256(bytes) → 证明文件身份」；DEC-031 原则 1「禁止任何系统用 path 做唯一身份判断」

#### F8: duplicate identity

```
触发: 同一 source_content_sha256 对应多个不同文件（理论上不可能，因 sha256 抗碰撞）
检测: M4 运行时比对 + 上游 Step 1 snapshot 的 87 文件清单去重
判定: FAIL（若检测到）
动作: 不创建 Document / SourceVersion / Candidate；记录 "duplicate_identity"
```

**Contract 依据**：§1.2「身份由 source_content_sha256 唯一决定」

### 3.3 Fail-Closed 原则总结

| 原则 | 说明 |
|---|---|
| **所有身份验证失败 → FAIL** | F1/F2/F3/F4/F6/F7/F8 全部阻断消费 |
| **IR 缺失 ≠ 身份验证失败** | F5 是 Semantic Pending 正常态，不阻断身份验证 |
| **阻断 = 不写入 DB** | 不创建 Document / SourceVersion / Candidate / Annotation |
| **阻断 ≠ 删除** | 不删除任何已有数据 |
| **阻断 ≠ 抛异常** | 异常在模块内部捕获，转换为 FAIL 决策传递给调用方 |

---

## §4 Test Plan

### 4.1 Unit Tests

#### T-U1: sha256 raw bytes 计算正确性

```
class TestComputeSourceContentSha256:
    def test_empty_bytes(self):
        """空字节 → e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"""

    def test_ascii_text(self):
        """ASCII 文本 → 已知 sha256"""

    def test_utf8_chinese(self):
        """UTF-8 中文 → 已知 sha256"""

    def test_crlf_preserved(self):
        """CRLF 字节序列 → sha256 与 LF 不同（验证不 splitlines）"""

    def test_trailing_newline_preserved(self):
        """trailing newline → sha256 与无 newline 不同（验证不 strip）"""

    def test_matches_producer_sha256sum(self):
        """与 `sha256sum file.md` 输出一致（跨工具对齐）"""
```

**覆盖目标**：算法正确性 + 与 producer 对齐 + CRLF/newline 保真

---

### 4.2 Integration Tests

#### T-I1: Manifest verification 集成

```
class TestManifestIdentityVerification:
    def test_manifest_with_valid_sha(self):
        """manifest 有 sha + bytes 匹配 → PASS"""

    def test_manifest_with_wrong_sha(self):
        """manifest 有 sha + bytes 不匹配 → FAIL (manifest_recomputed_mismatch)"""

    def test_manifest_without_sha(self):
        """manifest 无 sha 字段 → FAIL (manifest_sha_missing)"""

    def test_manifest_empty_sha(self):
        """manifest sha 为空字符串 → FAIL (manifest_sha_missing)"""
```

#### T-I2: IR verification 集成

```
class TestIRIdentityVerification:
    def test_ir_with_matching_sha(self):
        """IR sha == manifest sha → PASS"""

    def test_ir_with_wrong_sha(self):
        """IR sha != manifest sha → FAIL (ir_manifest_mismatch)"""

    def test_ir_absent(self):
        """IR 不存在 → PASS_WITH_SEMANTIC_PENDING"""

    def test_ir_without_sha_field(self):
        """IR 存在但无 sha 字段 → PASS_WITH_SEMANTIC_PENDING"""
```

---

### 4.3 Negative Tests

#### T-N1: 篡改 bytes

```
class TestTamperedBytes:
    def test_append_byte(self):
        """在 source 文件末尾追加 1 字节 → FAIL (manifest_recomputed_mismatch)"""

    def test_modify_middle_byte(self):
        """修改文件中间 1 字节 → FAIL (manifest_recomputed_mismatch)"""

    def test_crlf_to_lf(self):
        """CRLF → LF 转换 → FAIL (manifest_recomputed_mismatch)"""

    def test_add_trailing_newline(self):
        """追加 trailing newline → FAIL (manifest_recomputed_mismatch)"""
```

**验证目标**：任何 bytes 变化 → sha 变化 → FAIL

#### T-N2: 篡改 manifest

```
class TestTamperedManifest:
    def test_modify_sha_to_wrong_value(self):
        """修改 manifest sha 为错误值 → FAIL (manifest_recomputed_mismatch)"""

    def test_remove_sha_field(self):
        """删除 manifest sha 字段 → FAIL (manifest_sha_missing)"""

    def test_set_sha_to_empty(self):
        """manifest sha 设为空字符串 → FAIL (manifest_sha_missing)"""

    def test_set_sha_to_invalid_format(self):
        """manifest sha 设为非法格式（非 64 hex）→ ManifestReadError → FAIL"""
```

**验证目标**：manifest 篡改 → 被检测 → FAIL

#### T-N3: 篡改 IR

```
class TestTamperedIR:
    def test_modify_ir_sha(self):
        """修改 IR sha 为错误值 → FAIL (ir_manifest_mismatch)"""

    def test_replace_ir_with_different_file(self):
        """替换 IR 为不同文件的 IR → FAIL (ir_manifest_mismatch)"""

    def test_delete_ir(self):
        """删除 IR 文件 → PASS_WITH_SEMANTIC_PENDING（不是 FAIL）"""
```

**验证目标**：IR 篡改 → 被检测 → FAIL；IR 缺失 → Semantic Pending

#### T-N4: path 替换

```
class TestPathReplacement:
    def test_path_points_to_different_file(self):
        """path 指向不同文件（内容不同）→ FAIL (manifest_recomputed_mismatch)"""

    def test_path_points_to_empty_file(self):
        """path 指向空文件 → FAIL (manifest_recomputed_mismatch)"""

    def test_path_points_to_directory(self):
        """path 指向目录 → SourceBytesReadError → FAIL"""
```

**验证目标**：path 指向错误文件 → sha 不匹配 → FAIL（path 非身份原则的运行时验证）

---

### 4.4 Test Coverage Matrix

| 测试类型 | 覆盖模块 | 覆盖场景 | 数量 |
|---|---|---|---|
| Unit | M2 (sha256 计算) | 算法正确性 / CRLF / newline | 6 |
| Integration | M1+M2+M4 (Manifest verification) | sha 匹配 / 不匹配 / 缺失 | 4 |
| Integration | M3+M4 (IR verification) | sha 匹配 / 不匹配 / 缺失 | 4 |
| Negative | M2+M4 (篡改 bytes) | 追加 / 修改 / CRLF / newline | 4 |
| Negative | M1+M4 (篡改 manifest) | 修改 / 删除 / 空值 / 非法格式 | 4 |
| Negative | M3+M4 (篡改 IR) | 修改 / 替换 / 删除 | 3 |
| Negative | M2+M4 (path 替换) | 不同文件 / 空文件 / 目录 | 3 |
| **合计** | | | **28** |

---

## §5 禁止事项确认

### 5.1 本轮禁令（Owner 指令原文）

| 禁令 | 状态 |
|---|---|
| **ZERO CODE** | ✅ 确认：本轮未写任何 `.py` 文件 |
| **ZERO DATA** | ✅ 确认：本轮未修改任何 manifest / IR / source 数据 |
| **ZERO SCHEMA** | ✅ 确认：本轮未修改 `models/source.py` / `models/snapshot.py` / Alembic |
| **ZERO CONTRACT CHANGE** | ✅ 确认：本轮未修改 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` @ `f4941ff` |

### 5.2 实现阶段禁令（继承 Contract v0.2）

| 禁令 | 来源 |
|---|---|
| 不修改冻结对象 `f4941ff` | DEC-036 |
| 不修改 `hashing.py`（`sha256_hex` 是 V3 logical identity primitive） | 设计原则 |
| 不修改 `source_loader.py`（现有文本管线不动） | 设计原则 |
| 不修改 Gate/Admission 逻辑（identity gate 是前置闸门） | 设计原则 |
| 不扩展 admission 职责 | Owner 指令 |
| 不扩展 semantic 层 | Owner 指令 |
| 不重构 schema | Owner 指令 |
| 不实现 bytes 传输方案（OQ-12″ 暂缓） | DEC-031 延期项 |

---

## §6 设计冻结声明

### 6.1 模块清单

| 模块 | 文件 | 状态 |
|---|---|---|
| M1: Manifest Reader | `identity/manifest_identity_reader.py` | DESIGN ONLY |
| M2: Raw Bytes Loader | `identity/raw_bytes_loader.py` | DESIGN ONLY |
| M3: IR Identity Reader | `identity/ir_identity_reader.py` | DESIGN ONLY |
| M4: Identity Verifier | `identity/identity_verifier.py` | DESIGN ONLY |
| M5: Identity Gate | `identity/identity_gate.py` | DESIGN ONLY |

### 6.2 接口清单

| 接口 | 函数签名 | 返回类型 |
|---|---|---|
| Manifest Reader | `read_manifest_identity(manifest_path: Path)` | `ManifestIdentity` |
| Raw Bytes Loader | `load_raw_bytes(source_path: Path)` | `RawBytesIdentity` |
| IR Identity Reader | `read_ir_identity(ir_path: Path)` | `IRIdentity` |
| Identity Verifier | `verify_identity(manifest_sha, recomputed_sha, ir_sha)` | `VerificationResult` |
| Identity Gate | `evaluate_identity(verification, ir_sha)` | `IdentityGateDecision` |

### 6.3 Failure Matrix 清单

| # | 场景 | 判定 |
|---|---|---|
| F1 | bytes 不存在 | FAIL-CLOSED |
| F2 | bytes hash mismatch | FAIL-CLOSED |
| F3 | manifest hash mismatch | FAIL-CLOSED |
| F4 | IR hash mismatch | FAIL-CLOSED |
| F5 | IR 缺失 | PASS_WITH_SEMANTIC_PENDING |
| F6 | manifest 缺失 | FAIL-CLOSED |
| F7 | path 指向错误文件 | FAIL-CLOSED |
| F8 | duplicate identity | FAIL-CLOSED |

### 6.4 Test Plan 清单

| 类型 | 数量 |
|---|---|
| Unit | 6 |
| Integration | 8 |
| Negative | 14 |
| **合计** | **28** |

### 6.5 状态

```
DESIGN ONLY
NOT IMPLEMENTED
WAITING IMPLEMENTATION AUTHORIZATION
```

**本文件是设计冻结，不是实现令。实现须 Owner 单独下达。**
