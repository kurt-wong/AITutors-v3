# Preprocessing Integration Contract v0.2 — DRAFT

> **状态**：**DRAFT（冻结候选）。NOT FROZEN。** 待 Owner 批准 + DSH（producer 侧）确认接口变更面后升 FROZEN。
> **定位**：AITutors-preprocessing（producer）→ AITutors-v3（consumer）的跨项目输出契约。**本版职责 = 冻结 V3 消费边界**。
> **上游**：v0.1 DRAFT @ `1fbaf5e`（本版取代其 §1/§2/§3 相关条款；未提及处继承 v0.1）；Owner B1/B2/B3 架构裁决（2026-09-16，见 `PREPROCESSING-V3-DECISION-ALIGNMENT-REPORT.md` §0）；V3 侧事实基线 @ `643ebd0`；producer 侧事实 @ `17c55d8`。
> **本契约不做什么**：不定义 V3 内部实现（IR loader / 隔离通道 / hash 写入点归 V3 设计）；不替 DSH 决定生产侧实现（字段落点、清洗、守卫归 producer 域）；不修改任何代码。
>
> **证据纪律**：每条款标 `DECISION`（Owner 裁决）/ `OBSERVED`（实测锚）/ `UNKNOWN`（无证据）/ `REQUIREMENT`（契约义务）。**DECISION ≠ 已实现**——本版所有 REQUIREMENT 均为冻结候选义务，实现状态见各条。

---

## §1 Source Version

### 1.1 双层接口架构（`DECISION`）

正式生产接口 = **Manifest + IR 双层**：

| 层 | 角色 | 职责 |
|---|---|---|
| **Manifest** | **Source Identity Authority** | 承载源身份与标注事实；身份对账以本层为准 |
| **IR** | **Semantic Consumption Authority** | 承载结构解析 + provenance；语义消费以本层为准 |

两层必须通过明确 **`source_version_id`** 关联（`DECISION`）。

**OBSERVED 现状（缺口登记，非本契约放宽）**：

- Manifest 层 0/166 携带任何 sha 键，无 `source_version_id` 字段（`manifest_reader.py:28-35`；INTERFACE FACTS v1 §1 S2 @ `17c55d8`）——Source Identity Authority 当前**无身份载体**。
- IR 层有 `source_sha256`（源 md 原始字节 SHA-256，71/71 零漂移），但无名为 `source_version_id` 的关联键（INTERFACE FACTS v1 §1 S3 @ `17c55d8`）。
- V3 当前只读 Manifest，IR 消费 = 0 命中（`Grep @ backend/`，V3 @ `b5ddbe3`）。
- **实现状态**：双层接口的字段落点属 producer 接口变更 + V3 新增消费能力，**均未开始**。

### 1.2 source_version_id 语义（`REQUIREMENT`）

- `source_version_id` = 跨系统源版本关联键。其**身份值** = 源 OCR markdown 文件的 `SHA-256(raw bytes)`（hex 小写 64 字符，见 §2.1）。
- Manifest 与 IR 的同源记录必须携带**同一** `source_version_id` 值。
- producer 侧承载字段的命名与位置：`UNKNOWN`（DSH 域，本契约不指定实现）。IR 现有 `source_sha256` 的值与 §2.1 定义一致（`OBSERVED`，`resolver_reference.py:249`），可作为该身份值；Manifest 侧当前缺失（`OBSERVED`，见 §1.1）。

### 1.3 V3 侧对应关系（`REQUIREMENT`）

- V3 内部 `source_version_id` 是 `document_source_versions` 主键 UUID（`models/source.py:44-57`；`evidence.py:44-46` FK），**不是**跨系统键——**禁止**将 V3 内部 UUID 与跨系统 `source_version_id` 混用。
- V3 必须以 §2.1 定义的 raw bytes sha 作为跨系统对账值；V3 内部 UUID ↔ 跨系统 sha 的绑定发生在 ingest，绑定关系可离线重建。
- **OBSERVED 缺口**：consumer 路径写入 `documents.original_sha256` 的值是 canonical_json 包裹 hash（`runner.py:73`；`hashing.py:60-62`），**不是** raw bytes sha——该绑定当前不成立。`IMPLEMENTATION: not started`。

### 1.4 Immutable（继承 v0.1 §1.2，`OBSERVED`）

sha 一经发布，对应文件字节冻结；任何内容变更必须产生新 sha = 新 source_version。保障机制：producer Input Integrity Gate + Audit Snapshot（INTERFACE FACTS v1 §1 S5 @ `17c55d8`）。

### 1.5 Version 关系（继承 v0.1 §1.3，`OBSERVED`）

producer 当前不产出 version→version 关系指针。跨版本 lineage 属开放项（§6 OQ-1）。V3 不得假设「旧版本权威可迁移到新版本」。

### 1.6 覆盖面边界（`OBSERVED`）

identity 面分裂：166 份 manifest 中 v2 = 87 份 / v1 legacy = 79 份（INTERFACE FACTS v1 §1 S2 @ `17c55d8`）。79 份 v1 在 C-IN-1 下拒收——**双层接口的可消费覆盖面以 87 份 v2 为上限**，直至 v1 处置另有裁决。

---

## §2 Hash Contract

### 2.1 唯一 source identity（`DECISION`）

**source identity 唯一定义 = `SHA-256(raw bytes)`**，即源 OCR markdown 文件**原始字节**的 SHA-256（hex 小写，64 字符）。

- producer 现有 `source_sha256` 的输入口径与此一致（`OBSERVED` VERIFIED：Reconciliation v0.2 §B1 @ `ad1abdd`；`resolver_reference.py:52-53,249`）。
- 任一方可用标准库独立重算，无需共享密钥或版本化算法参数（`OBSERVED`，INTERFACE FACTS v1 §2 @ `17c55d8`）。

### 2.2 禁止作跨系统 identity 的 hash（`DECISION` + `REQUIREMENT`）

以下 hash **只能作为内部完整性/一致性校验，不得替代 source identity，不得作为跨系统对账锚**：

| hash | 当前归属 | 证据 |
|---|---|---|
| canonical_json 包裹 hash（V3 `sha256_hex` 族，含 `file_sha`） | V3 内部 | `hashing.py:60-62`；`runner.py:71-73` |
| `body_hash` | V3 内部（producer 零产出） | `source_loader.py:43-46`；`line_index.py:70-72`；INTERFACE FACTS v1 §2/§4 |
| `line_hash` | V3 内部（producer 零产出） | `source_loader.py:38`；`line_index.py:75-90` |
| `integrity_hash` | V3 内部（consumer 路径退化 = body_hash） | `runner.py:93`；`line_index.py:93-108` |
| `norm_sha256` | producer 审计内部，从未作接口发布 | INTERFACE FACTS v1 §2 @ `17c55d8` |

**OBSERVED 现状**：上述 hash 当前本就无跨系统对应物（producer `body_hash`/`line_hash` 零产出，全仓 grep = 0）——本条款将其正式限定为内部用途，与现状不冲突。

**V3 仓内先例**（`OBSERVED`）：`compile/__init__.py:10` 已有「text_hash raw 绝不经 canonical JSON」规则，与本条款方向一致。

### 2.3 跨系统对账义务（`REQUIREMENT`）

- V3 消费前可独立重算源文件 raw bytes sha 与声明值比对；不一致 → 阻断（fail-closed，继承 v0.1 §3.3-3）。
- **可执行前提**（`OBSERVED`）：载体上有该字段 + 双方对「钉 raw bytes」一致。前者当前不成立（§1.1/§1.3 缺口）；后者已由 §2.1 DECISION 满足。
- **实现状态**：`IMPLEMENTATION: not started`（依赖 §1 双层接口落地）。

### 2.4 内部 hash 的地位（`REQUIREMENT`）

V3 内部 hash 家族（`body_hash`/`line_hash`/`integrity_hash`）的算法一致性属 V3 内部治理，**不在本契约跨系统承诺范围**。已登记的 V3 内部事实（同表 `line_hash` 双算法、consumer 路径 `integrity_hash` 退化）见 GAP-MAP L5/G-4 @ `643ebd0`。`UNKNOWN`：DECISION 未裁定该治理是否进行。

---

## §3 Semantic Annotation

### 3.1 载体分工（`DECISION`，取代 v0.1 §2 开头）

- **Manifest = Source Identity Authority**：标注事实层。V3 身份对账以本层 + §2.1 sha 为准。
- **IR = Semantic Consumption Authority**：结构解析 + provenance 层。V3 语义消费以本层为准。
- v0.1「V3 消费以 IR 为准，manifest 为回源凭据」的表述被本版**取代**：双层各有权威面，不再单层优先。

### 3.2 unit_type 值域与隔离（`DECISION` + `REQUIREMENT`）

**canonical 闭集** = `{standalone_question, composite_question}`（`OBSERVED`：v2 面 2,347 单元内恰此 2 值 + 噪声 1 例，INTERFACE FACTS v1 §1 @ `17c55d8`）。

**unknown `unit_type` 处理（`DECISION`）**：

- **不得自动转换**（禁止任何层将未知值改写为闭集内值）。
- **不得静默 fallback**（禁止按默认分支静默处理）。
- **不得进入 Question materialization**（不产 candidate / leaves）。
- **处理方式 = UNKNOWN/PENDING**（显式隔离态，须可见、可审计）。

**OBSERVED 现状（全部违反上述禁令，实现未开始）**：

| 层 | 当前行为 | 证据 |
|---|---|---|
| 读取 | 硬取 `u["unit_type"]`，无闭集校验 | `manifest_reader.py:52` |
| annotation | 硬编码重写为 `"standalone_question"`（自动转换 + 静默） | `annotation_adapter.py:42`；`:101-104` |
| span | 未知值按原始值走 composite 分支（静默 fallback） | `resolved_span_adapter.py:77-90`；`runner_b2.py:116-127` |
| 终态 | 静默 incomplete→skip；真实原因任何层不出现 | `runner_b2.py:232-239`；GAP-MAP §0 E-1 |

**符合度**：「不得进入 Question materialization」经由静默 skip 达成（Compiler 非 ready 不产 leaves，`compiler.py:72-73`）——**结果符合、路径不符合**（非显式 UNKNOWN/PENDING）。其余三条禁令均**违反**。

**UNKNOWN/PENDING 落点**（`UNKNOWN`）：V3 `SEMANTIC_STATUS` 冻结值域 = `{ready, incomplete}`（`compile/__init__.py:28-29`，BUG-V3-018）；`DECISION_STATUS` = `{pending_review, approved, rejected}`（`gate/__init__.py:10-11`），且 `pending_review` 当前仅 ready 单元可达（`runner_b2.py:231-264`）。UNKNOWN/PENDING 落在哪一层 = **实现设计项，未裁决，本契约不指定**。

### 3.3 噪声类级事实（`OBSERVED`）

schema 噪声不只 unit_type 一处：恰 1 例 `andalone_question` + 恰 1 例游离键 `explanation_lines_note`（value = null），均在 v2 可消费面内（INTERFACE FACTS v1 §1 @ `17c55d8`）。producer 链零值域守卫（`write_outputs` 原样落盘 → `resolver_reference.py:152` 逐字复制）。**producer 侧守卫属 DSH 域，本契约不指定。**

### 3.4 继承条款（v0.1 §2.1-2.4，`OBSERVED`）

单元级字段表、claim/span 绑定（行锚 `[start,end]`）、material ref 消费禁令、figure 行内相对路径引用——**继承 v0.1**，本版不改。`unit_id` 仍为 display alias，禁止作跨系统键（v0.1 §2.2；`evidence.py:28-29` AuthorityIdentity 用 claim_id 但经三元绑定）。

---

## §4 Failure Boundary

> V3 仓内自有原则：**三层状态不复用**——E ResolvedStatus ≠ IR.semantic_status ≠ gate_decision（`compile/__init__.py:9`）。本节与之一致：三种失败处置**各自独立，禁止混淆**。

### 4.1 三种处置（`REQUIREMENT`）

| 处置 | 语义 | 何时使用 | 终态性质 |
|---|---|---|---|
| **REJECT** | 终态拒绝，无自动路径 | producer `disposition ∈ REJECTED_*` / `qc_verdict = FAIL`；identity v1（C-IN-1）；sha 不一致（§2.3） | terminal（V3 `decision_status = rejected`，`gate/__init__.py:11`） |
| **PENDING** | 待裁决，显式隔离，可审计 | **unknown `unit_type`（§3.2 DECISION）**；schema 值域越界（v0.1 §3.3-7 basis 闭集，R50 裁定 surfaced as PENDING_REVIEW） | 有出边（V3 `pending_review` 通道；**当前仅 ready 单元可达**——缺口） |
| **INCOMPLETE** | 结构上不可 materialize，非拒绝非待裁决 | 必需 span 缺失 / choice 型无 options / composite 缺 material（`ir.py:216-230`） | 非 materialize（V3 `semantic_status = incomplete`，`compile/__init__.py:29`） |

### 4.2 禁止混淆（`REQUIREMENT`）

1. **unknown `unit_type` 不得报为 INCOMPLETE**——当前静默路径正是如此（真实原因被格式类错误掩盖，GAP-MAP §0 E-1）。必须走 PENDING。
2. **INCOMPLETE 不得转 REJECT**——结构缺失 ≠ 终态拒绝；incomplete 单元不产 leaves（`compiler.py:72-73`）但不判 rejected。
3. **PENDING 不得静默转 PASS 或 REJECT**——继承 v0.1 §3.3-8（C-FAIL-1）。
4. **REJECT 人工放行必须走显式 Admission 记录**——继承 v0.1 §3.3-2（C-FAIL-2）。

### 4.3 OBSERVED 现状与缺口

| 事实 | 证据 |
|---|---|
| IR `semantic_status` 冻结值域 `{ready, incomplete}`——无 PENDING 取值 | `compile/__init__.py:28-29` |
| Gate `decision_status` 冻结值域 `{pending_review, approved, rejected}` | `gate/__init__.py:10-11` |
| `pending_review` 仅 ready 单元可达；非 ready 在 `runner_b2.py:232-239` 被 skip，进不了 pending 通道 | `runner_b2.py:231-264` |
| unknown unit_type 当前终态 = 静默 incomplete→skip（§4.2-1 违反） | GAP-MAP §0 E-1 |
| Admission fail-closed 执行中（EB-008 P1）——本契约不改其逻辑 | `admission.py:213-223`；EB-008 状态另册 |

**缺口**：PENDING 处置对 unknown unit_type **无可达通道**（B3-G1/G2，Alignment Report §3.3）。`IMPLEMENTATION: not started`；落点设计 = `UNKNOWN`。

### 4.4 继承条款（v0.1 §3.1-3.3，`OBSERVED`/`REQUIREMENT`）

- 必须提供字段清单、允许为空清单、消费禁令（unresolved 答案槽位禁止静默默认）——继承 v0.1 §3.1-3.2。
- 必须阻断清单中 1/2/4/5/8 项继承；第 3 项（sha 不一致）按 §2.1 raw bytes 口径重述；第 6 项（unit_type 越界）按 §3.2/§4.1 升格为 **PENDING 处置要求**；第 7 项（basis 闭集）维持 PENDING_REVIEW。

---

## §5 V3 消费边界（本版冻结面）

> 本节是 v0.2 的**核心冻结候选**：V3 消费侧承诺与禁止。producer 侧实现归 DSH 域，不在本节。

### 5.1 V3 承诺（`REQUIREMENT`）

1. 跨系统 source identity 只认 `SHA-256(raw bytes)`（§2.1）；内部 hash 不作跨系统用（§2.2）。
2. 消费前可独立重算 sha 对账；不一致 → 阻断（§2.3）。
3. unknown `unit_type` 不自动转换、不静默 fallback、不 materialize；走 UNKNOWN/PENDING（§3.2）。
4. 三种失败处置不混淆（§4.2）。
5. `unit_id` 不作跨系统键；claim 身份经 AuthorityIdentity 三元绑定（`evidence.py:28-29`，EB-008 既有设计，本契约不改）。

### 5.2 V3 禁止（`REQUIREMENT`）

1. 禁止将 V3 内部 UUID 与跨系统 `source_version_id` 混用（§1.3）。
2. 禁止用 canonical_json / body_hash / line_hash / integrity_hash 替代 source identity（§2.2）。
3. 禁止 unknown unit_type 的任何自动映射或静默路径（§3.2/§4.2）。
4. 禁止 unresolved 答案槽位静默默认（继承 v0.1 §3.2 特别条款）。

### 5.3 实现状态总表（`DECISION ≠ IMPLEMENTATION`）

| 契约义务 | 当前状态 | 缺口 ID |
|---|---|---|
| Manifest 携带 `source_version_id` | 未实现（producer 接口变更） | B1-G1 |
| Manifest↔IR 显式关联 | 未实现（字段定义项） | B1-G2 |
| V3 具备 IR 消费路径 | 未实现（0 命中） | B1-G3 |
| V3 绑定跨系统 sha（raw bytes） | 未实现（canonical_json 包裹） | B1-G4 / B2-G1 |
| sha 对账闸门按 raw bytes 可执行 | 未实现（依赖上两项） | B2-G3 |
| unknown unit_type → UNKNOWN/PENDING | 未实现（静默 incomplete→skip） | B3-G1 |
| UNKNOWN/PENDING 落层设计 | **UNKNOWN**（未裁决） | B3-G2 |

---

## §6 开放项

| # | 开放项 | 状态 |
|---|---|---|
| OQ-1 | source_version supersede/lineage 指针 | 未建（继承 v0.1） |
| OQ-2 | `unit_type` 值域闭集化 producer 侧守卫 | 未实施（DSH 域；DECISION 是消费侧边界） |
| OQ-3 | 图片资产交付形态 | 继承 v0.1（当前仅行内相对路径；27,240 悬空已量化，FACT-034） |
| OQ-4 | basis 值域校验 producer 侧落地 | 未实施（期间 V3 自检，v0.1 §3.3-7） |
| OQ-5 | UNKNOWN/PENDING 在 V3 哪一层落地（IR 域扩展 / Gate 通道 / 其他） | **未裁决**（B3-G2；涉及冻结值域 BUG-V3-018 / 10 §5.2，须 Owner） |
| OQ-6 | 79 份 identity v1 manifest 的处置 | 未裁决（覆盖面以 87 v2 为上限） |
| OQ-7 | V3 内部 hash 家族治理（line_hash 双算法 / integrity_hash 退化） | 未裁决（G-4；DECISION 只限定不作跨系统 identity） |
| OQ-8 | producer 侧 `source_version_id` 承载字段命名/位置 | DSH 域（§1.2） |
| OQ-9 | 全语料 IR 是否/何时重新产出 | 须 Owner 显式令（暂停令 `746e35c` 生效中） |

---

## §7 与 v0.1 的差异

| 条款 | v0.1 @ `1fbaf5e` | v0.2 DRAFT |
|---|---|---|
| 消费载体 | 「V3 消费以 IR 为准」（`:33`） | **取代**：双层各有权威面（§1.1/§3.1） |
| source identity | 隐含 sha = raw bytes，未禁其他 hash | **收紧**：显式唯一定义 + 禁止清单（§2.1/§2.2） |
| `source_version_id` 关联 | §4.2 声称「一一对应」但无载体 | **升格为 REQUIREMENT** + 缺口登记（§1.2/§1.3） |
| unknown unit_type | §3.3-6「隔离（PENDING 通道）」 | **收紧**：四条禁令 + PENDING 落点 UNKNOWN（§3.2/§4.1） |
| Failure Boundary | 分散于 §3.3 各项 | **集中**：三处置定义 + 禁止混淆（§4） |
| hash 行号 | — | 按 E-2 勘误（splitlines @ `source_loader.py:27`） |

---

## §8 冻结前提（本版不满足即不冻结）

1. Owner 批准本 DRAFT 作为冻结候选。
2. DSH 确认 producer 侧接口变更面（§1.1 Manifest 身份载体、§1.2 字段命名）——**本契约不替其决定**。
3. OQ-5（UNKNOWN/PENDING 落层）有裁决。
4. §5.3 实现状态表中「V3 承诺」项的排期归属明确（实现是否为冻结前置、还是契约先冻结实现后补 = Owner 裁决）。

---

## 边界声明

**本文件做了**：Owner B1/B2/B3 裁决的契约化（§1-4）；V3 消费边界冻结候选面（§5）；v0.1 差异对照（§7）；开放项与冻结前提（§6/§8）。每条款标 DECISION/OBSERVED/UNKNOWN/REQUIREMENT。

**本文件没做**：未把 DECISION 描述为已实现（§5.3 全表 `IMPLEMENTATION: not started` 或 `UNKNOWN`）；未替 DSH 决定生产侧实现；未修改 preprocessing / V3 业务代码 / EB-008 / admission 逻辑；未冻结本契约（DRAFT）。

**EB-008 状态**：不因本文件变动。AuthorityIdentity 三元绑定（`evidence.py:28-29`）为既有冻结设计，本契约仅引用不改。

---

*v0.2 DRAFT — 2026-09-16，Claude（AITutors-v3 Consumer Owner）。V3 代码 `b5ddbe3` · preprocessing `746e35c` · v0.1 @ `1fbaf5e`。冻结候选，NOT FROZEN。*
