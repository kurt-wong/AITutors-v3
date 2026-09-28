# Consumer Identity Verification Implementation Plan v1

> **性质**：前置设计审计 + 最小实现路径提案。**零业务代码，零 schema 变更，零 Contract 修改。**
> **基准**：Contract v0.2 FROZEN @ `f4941ff`（sha256 `9c6b9063…7528`）· V3 代码 @ `b5ddbe3` · GAP-MAP G-15
> **日期**：2026-09-16 · **状态**：AUDIT COMPLETE / AWAITING OWNER IMPLEMENTATION ORDER

---

## §0 范围与边界

本文件覆盖 Contract §5.6.1 五项 NOT IMPLEMENTED 能力的**实现前审计**与**最小实现路径**。

**严格遵守**：
- 不修改冻结对象 `f4941ff`
- 不修改 Contract 正文
- 不修改 schema（`models/source.py` / `models/snapshot.py` 不动）
- 不修改 source 数据
- 不实现 identity gate（本文件只设计，不落地）
- 不扩展 admission / semantic / 不重构 schema

**本文件是设计文档，不是实现令。** 实现须 Owner 单独下达。

---

## §1 Task 1 — V3 Consumer 入口现状审计

### 1.1 Source 获取方式

| 事实 | 位置 | 说明 |
|---|---|---|
| source 路径来自 manifest 的 `source_file` 字段 | `manifest_reader.py:69` | 绝对路径，machine-local |
| V3 用 `Path(manifest.source_file)` 加载源文件 | `runner.py:241` / `runner_b2.py:320` | 仅作 locator，未用于身份判断 |
| 跨机不可解析 | IF-v2 §2.1 | 本机绝对路径，换机器即失效 |

**结论**：Source 获取 = path locator only。**符合** DEC-031「path → 找文件」原则。但 bytes 本身未以原始字节形式获取（见 §1.3）。

### 1.2 Manifest 读取

| 事实 | 位置 | 说明 |
|---|---|---|
| `load_manifest()` 读 manifest JSON | `manifest_reader.py:44-75` | `json.loads(path.read_text())` |
| `Manifest` dataclass 字段 | `manifest_reader.py:28-35` | `source_file / model / prompt_version / validation_issues / warnings / units` |
| **无任何 sha 字段** | 同上 | `source_content_sha256` / `source_sha256` / `body_hash` 均不在 dataclass 内 |
| `unit_type` 硬取 `u["unit_type"]` | `manifest_reader.py:52` | 无闭集校验，无 sha 校验 |
| manifest JSON 内是否有 `source_content_sha256` | Step 2 回填后已有（87/87） | **V3 dataclass 未声明该字段 → 读取后被丢弃** |

**结论**：Manifest 读取 = 有入口，但 dataclass 缺 `source_content_sha256` 字段 → 回填的 sha 在 V3 侧**不可见**。

### 1.3 Raw bytes 获取

| 事实 | 位置 | 说明 |
|---|---|---|
| 源文件读取方式 = `source_path.read_text(encoding="utf-8")` | `source_loader.py:26` | **读文本，非原始字节** |
| 读入后 `splitlines()` 规范化 | `source_loader.py:27` | CRLF/CR → LF，trailing newline 丢失 |
| 再 `"\n".join(l.text)` 重组 | `source_loader.py:45` / `runner.py:71` | 重组后的文本 ≠ 原始字节 |

**结论**：Raw bytes = **NOT ACQUIRED**。V3 获取的是规范化后的文本，不是 `SHA256(original source bytes)` 所指的原始字节。这是 §5.6.1 第 2 项 NOT IMPLEMENTED 的直接证据。

### 1.4 Hash 计算位置

| Hash 类型 | 计算位置 | 算法 | 与 producer `source_content_sha256` 的关系 |
|---|---|---|---|
| `file_sha`（写入 `Document.original_sha256`） | `runner.py:73` / `runner_b2.py:145` | `sha256_hex(body_text)` = canonical_json wrap → SHA-256 | **永远 DIFFER**（canonical_json 包裹 + 非 raw bytes） |
| `body_hash` | `source_loader.py:43-46` | SHA-256(joined text with `\n`) | **漂移**（splitlines 规范化，6/12 DIFFER 实测） |
| `line_hash`（per-line） | `source_loader.py:38` | SHA-256(line text) | 内部用途，非跨系统身份 |
| `sha256_hex` 工具函数 | `hashing.py:60-62` | `canonical_json(obj) → UTF-8 → SHA-256 → hex` | **设计用途 = V3 logical identity**，非 source content identity |

**结论**：V3 当前所有 hash 均**不是** `SHA256(raw bytes)`。`sha256_hex` 是 V3 logical identity primitive（canonical_json wrap），**不可直接用作跨系统身份键计算**。

### 1.5 IR 消费入口

| 事实 | 位置 | 说明 |
|---|---|---|
| V3 全仓 IR 消费 = **0 命中** | `Grep resolver_ir\|source_sha256\|ir.json @ backend/` | 无 IR reader |
| V3 自建 IR | `runner_b2.py:220` | `IRBuilder.build(resolved_run, payload, sv_id, ann.id)` — 从 manifest 构建，非读取 producer IR |
| producer IR 文件路径 | preprocessing 仓 `data/` 目录 | V3 无读取代码 |

**结论**：IR 消费 = **ZERO**。V3 自建 IR，不读 producer IR。§5.6.1 第 4 项 NOT IMPLEMENTED。

---

## §2 Task 2 — Implementation Gap Report

### A. Raw bytes acquisition

| 维度 | 内容 |
|---|---|
| **当前状态** | NOT IMPLEMENTED。`read_text()` → text → `splitlines()` → rejoin。获取的是规范化文本，非原始字节。 |
| **代码位置** | `source_loader.py:26`（read_text）· `runner.py:241` / `runner_b2.py:320`（path locator） |
| **与 §5.6.1 差距** | Contract 要求「获得 source 原始字节」；V3 当前获取的是 UTF-8 解码 + splitlines 规范化后的文本。CRLF 文件 / trailing newline 差异 → bytes 不同 → sha 不同。 |
| **风险** | **HIGH**。即使后续补上 sha 比对，若 bytes 获取方式不改，比对结果永远 DIFFER。这是验证链的**第一环**，不修则后续全链无效。 |

### B. SHA256 recompute

| 维度 | 内容 |
|---|---|
| **当前状态** | NOT IMPLEMENTED。V3 的 `sha256_hex(body_text)` = canonical_json wrap → SHA-256，非 raw bytes SHA-256。 |
| **代码位置** | `hashing.py:60-62`（sha256_hex）· `runner.py:73` / `runner_b2.py:145`（调用点） |
| **与 §5.6.1 差距** | Contract 要求「独立重算 SHA-256 并比对声明值」，算法 = `SHA256(original source bytes)` = `hashlib.sha256(raw_bytes).hexdigest()`。V3 当前算法 = `hashlib.sha256(canonical_json(joined_text).encode()).hexdigest()`。两者**永远不同**。 |
| **风险** | **CRITICAL**。算法不匹配 → 比对必然失败 → fail-closed 永远触发。需新增独立的 raw-bytes SHA-256 函数，**不复用** `sha256_hex`。 |

### C. Manifest identity verification

| 维度 | 内容 |
|---|---|
| **当前状态** | NOT IMPLEMENTED。Manifest dataclass 无 `source_content_sha256` 字段；`load_manifest()` 读取后该值被丢弃。 |
| **代码位置** | `manifest_reader.py:28-35`（dataclass）· `manifest_reader.py:44-75`（load_manifest） |
| **与 §5.6.1 差距** | Contract 要求「验证 Manifest 声明的 `source_content_sha256`」。V3 当前连读取都做不到（字段不在 dataclass），遑论验证。 |
| **风险** | **HIGH**。Manifest 可声明任意 sha；V3 无法识别 → 无法进入验证链。这是验证链的**第二环**。 |

### D. IR identity verification

| 维度 | 内容 |
|---|---|
| **当前状态** | NOT IMPLEMENTED。V3 零 IR 消费代码。自建 IR 不含 producer `source_sha256`。 |
| **代码位置** | 无（Grep 0 命中） |
| **与 §5.6.1 差距** | Contract 要求「验证 IR 的 `source_content_sha256`」。V3 当前不读 producer IR → 无法提取其 sha → 无法与 Manifest sha 比对。 |
| **风险** | **HIGH**。语义消费来源未验证 → 可能消费被篡改/不匹配的 IR。这是验证链的**第三环**。 |

### E. Identity gate

| 维度 | 内容 |
|---|---|
| **当前状态** | NOT IMPLEMENTED。V3 无身份闸门。任何 bytes/manifest/IR 不一致均静默通过。 |
| **代码位置** | 无（`identity_version` / `C-IN-1` 全仓 0 命中） |
| **与 §5.6.1 差距** | Contract 要求「身份闸门：不一致 → 拒收（fail-closed）」。V3 当前无此机制。 |
| **风险** | **CRITICAL**。无闸门 = 验证链形同虚设。即使 A-D 全部实现，无 fail-closed 闸门则验证结果不阻断消费。这是验证链的**终端环**。 |

### Gap 汇总矩阵

| # | 能力 | 状态 | 代码位置 | 差距性质 | 风险 |
|---|---|---|---|---|---|
| A | raw bytes acquisition | NOT IMPLEMENTED | `source_loader.py:26` | 获取方式错误（text ≠ bytes） | HIGH |
| B | SHA256 recompute | NOT IMPLEMENTED | `hashing.py:60-62` | 算法错误（canonical_json wrap ≠ raw SHA-256） | CRITICAL |
| C | Manifest identity verification | NOT IMPLEMENTED | `manifest_reader.py:28-35` | 字段缺失（dataclass 无 sha） | HIGH |
| D | IR identity verification | NOT IMPLEMENTED | 无 | 能力缺失（零 IR 消费） | HIGH |
| E | identity gate | NOT IMPLEMENTED | 无 | 能力缺失（无 fail-closed） | CRITICAL |

---

## §3 Task 3 — 最小实现路径（Consumer Identity Verification Implementation Plan v1）

### 3.1 设计原则

1. **只实现冻结要求**（Contract §5.6.1 五项）——不扩展 admission / semantic / 不重构 schema
2. **fail-closed 优先**——任何验证失败 → 阻断消费，不得继续向下游
3. **独立于现有 hash 家族**——新增 raw-bytes SHA-256 函数，不复用 `sha256_hex`（后者是 V3 logical identity primitive）
4. **最小侵入**——新增模块，不修改现有 Gate/Admission 逻辑
5. **path → 找文件；SHA256(bytes) → 证明身份**（Contract §5.6.2 binding）

### 3.2 实现顺序（依赖链：A → B → C → D → E）

```
Step 1: Raw bytes acquisition (A)
    ↓
Step 2: SHA256 recompute (B)
    ↓
Step 3: Manifest identity verification (C)
    ↓
Step 4: IR identity verification (D)
    ↓
Step 5: Identity gate (E)
    ↓
Step 6: Gate/Admission 入口对接（成功路径）
```

### 3.3 各 Step 最小设计

#### Step 1: Raw bytes acquisition

**目标**：获取 source 文件的原始字节（`bytes`，非 `str`）。

**设计**：
- 新增 `source_bytes_loader.py`（独立模块，不修改 `source_loader.py`）
- 函数签名：`def load_raw_bytes(source_path: Path) -> bytes`
- 实现：`source_path.read_bytes()` — 直接读二进制，不做 UTF-8 解码，不做 splitlines

**边界**：
- 不修改现有 `load_source_lines()`（其输出继续用于 V3 内部 line_hash / span 构建）
- raw bytes 仅用于身份验证，不替代现有文本管线

**风险缓解**：CRLF/trailing-newline 差异 → raw bytes 保真 → sha 可与 producer 对齐。

#### Step 2: SHA256 recompute

**目标**：对 raw bytes 独立计算 SHA-256（64 位小写 hex）。

**设计**：
- 在 `source_bytes_loader.py` 中新增：`def compute_source_content_sha256(raw_bytes: bytes) -> str`
- 实现：`hashlib.sha256(raw_bytes).hexdigest()`
- **不复用** `hashing.sha256_hex`（后者 canonical_json wrap，用途不同）

**边界**：
- 不修改 `hashing.py`（其 `sha256_hex` 继续服务 V3 logical identity）
- 新函数与 `sha256_hex` 并存，语义不同，命名区分

#### Step 3: Manifest identity verification

**目标**：从 manifest JSON 中提取 `source_content_sha256`，与 Step 2 重算值比对。

**设计**：
- 修改 `manifest_reader.py`：`Manifest` dataclass 新增字段 `source_content_sha256: str | None = None`
- `load_manifest()` 中：`source_content_sha256=raw.get("source_content_sha256")`
- 新增验证函数：`def verify_manifest_identity(manifest: Manifest, recomputed_sha: str) -> bool`
- 比对：`manifest.source_content_sha256 == recomputed_sha`

**边界**：
- 不修改 manifest JSON 文件（Step 2 回填已由 DSH 完成）
- dataclass 新增字段 = 加法变更，不破坏现有调用方（默认 `None`）

**风险缓解**：若 manifest 无 `source_content_sha256`（未回填的旧文件）→ 返回 `None` → identity gate 判定 FAIL。

#### Step 4: IR identity verification

**目标**：读取 producer IR 文件，提取其 `source_sha256`，与 Manifest sha 比对。

**设计**：
- 新增 `ir_identity_reader.py`（独立模块）
- 函数签名：`def load_ir_identity(ir_path: Path) -> str | None`
- 实现：读取 IR JSON，提取 `source_sha256` 字段（producer IR 已有此字段，71/71 自洽）
- 比对：`ir_source_sha256 == manifest.source_content_sha256`

**边界**：
- 不修改 producer IR 文件
- 不修改 V3 自建 IR（`IRBuilder.build()` 不动）
- 仅读取 producer IR 的 `source_sha256` 字段做身份验证

**风险缓解**：16 份 Semantic Pending（无 IR）→ IR 不存在 → identity gate 对 IR 面标记 SKIP（身份可用，语义待处理），不阻断身份验证。

#### Step 5: Identity gate

**目标**：汇总 A-D 验证结果，fail-closed。

**设计**：
- 新增 `identity_gate.py`（独立模块）
- 函数签名：
  ```python
  def evaluate_identity(
      manifest_sha: str | None,      # Manifest 声明值
      recomputed_sha: str,           # Step 2 重算值
      ir_sha: str | None,            # Step 4 提取值（可为 None = Semantic Pending）
  ) -> IdentityGateResult
  ```
- 判定逻辑：
  - `manifest_sha is None` → **FAIL**（manifest 无 sha）
  - `manifest_sha != recomputed_sha` → **FAIL**（bytes 与 manifest 不一致）
  - `ir_sha is not None and ir_sha != manifest_sha` → **FAIL**（IR 与 manifest 不一致）
  - `ir_sha is None` → **PASS_WITH_SEMANTIC_PENDING**（身份验证通过，语义待处理）
  - 全部一致 → **PASS**

**边界**：
- 不修改现有 Gate/Admission 逻辑（`gate/` / `admission.py` 不动）
- identity gate 是**前置闸门**，在进入现有 Gate/Admission 之前执行
- FAIL → 阻断消费（不创建 Document/SourceVersion/Candidate）
- PASS → 放行，进入现有 Gate/Admission 链

#### Step 6: Gate/Admission 入口对接

**目标**：identity gate PASS 后，进入既有 V3 Gate/Admission 链。

**设计**：
- 在 `runner_b2.py` 的 `_create_source_records()` 调用之前，插入 identity gate
- identity gate PASS → 继续现有流程
- identity gate FAIL → skip + 记录失败原因（不创建任何 DB 记录）

**边界**：
- 不修改 Gate/Admission 内部逻辑
- 不扩展 admission 职责
- 不修改 schema

### 3.4 不做的事（明确排除）

| 排除项 | 原因 |
|---|---|
| 修改 `hashing.py` | `sha256_hex` 是 V3 logical identity primitive，用途不同，不可混用 |
| 修改 `source_loader.py` | 现有文本管线继续服务 V3 内部 line_hash / span 构建 |
| 修改 Gate/Admission 逻辑 | identity gate 是前置闸门，不侵入现有链 |
| 修改 schema | Contract 冻结范围不含 schema 变更 |
| 实现 bytes 传输方案 | OQ-12″ 暂缓，实现阶段再决定 |
| 扩展 semantic 层 | 本阶段只做 identity verification，不做 semantic 处理 |
| 解决 16 份 Semantic Pending | OQ-21 开放项，非本阶段职责 |

### 3.5 实现前置条件

| 条件 | 状态 | 说明 |
|---|---|---|
| Contract v0.2 FROZEN | ✅ 已满足 | DEC-036 |
| Step 1/2 回填完成 | ✅ 已满足 | DSH DEC-026，87/87 |
| Owner 实现令 | ❌ 未下达 | **本文件不构成实现授权** |
| bytes 传输方案（OQ-12″） | ❌ 未裁决 | 实现阶段再决定 |

---

## §4 风险登记

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| R1 | raw bytes 获取方式不改 → sha 比对永远 DIFFER | 验证链第一环失效 | Step 1 必须用 `read_bytes()`，不可用 `read_text()` |
| R2 | `sha256_hex` 被误用作跨系统身份键计算 | 算法不匹配 → 比对永远 FAIL | 新增独立函数，命名区分，代码注释明确语义 |
| R3 | Manifest dataclass 新增字段破坏现有调用方 | 运行时错误 | 字段默认 `None`，加法变更，向后兼容 |
| R4 | 16 份 Semantic Pending（无 IR）被误判为 FAIL | 阻断身份验证 | identity gate 对 IR 面标记 SKIP，不阻断身份验证 |
| R5 | identity gate 位置不当 → 侵入现有 Gate/Admission | 违反最小侵入原则 | identity gate 是前置闸门，在现有链之前执行 |

---

## §5 输出物清单

| 物件 | 性质 | 状态 |
|---|---|---|
| 本文件 | 设计审计 + 实现路径 | ✅ 产出 |
| `source_bytes_loader.py` | 新增模块 | ❌ 未实现（待 Owner 令） |
| `ir_identity_reader.py` | 新增模块 | ❌ 未实现（待 Owner 令） |
| `identity_gate.py` | 新增模块 | ❌ 未实现（待 Owner 令） |
| `manifest_reader.py` 修改 | dataclass 新增字段 | ❌ 未实现（待 Owner 令） |
| `runner_b2.py` 修改 | 插入 identity gate 调用 | ❌ 未实现（待 Owner 令） |

---

## §6 结论

V3 Consumer Identity Verification 五项能力**全部 NOT IMPLEMENTED**。当前消费管线：

```
manifest (无 sha) → read_text (非 raw bytes) → sha256_hex (canonical_json wrap) → 自建 IR (零 producer IR 消费) → Gate/Admission (无身份闸门)
```

目标消费管线（§5.6.2）：

```
Manifest + raw bytes + IR → 验证 Manifest identity → 验证 IR identity → 验证 source-content consistency → fail-closed → 进入既有 Gate/Admission
```

**最小实现路径** = 6 个 Step，按依赖链 A→B→C→D→E→Gate 对接。新增 3 个独立模块 + 2 处修改，不触碰现有 Gate/Admission/schema/hash 家族。

**本文件是设计文档，不是实现令。实现须 Owner 单独下达。**
