# PREPROCESSING-V3 Consumer-side Decision Alignment Report

> **角色**：Claude = V3 Consumer Owner。对齐 Owner 已下达的 B1/B2/B3 架构裁决与 V3 消费侧现状。
> **性质**：决策对齐记录。**非实现 · 非冻结 · 不替 DSH 决定生产侧实现。**
> **三态纪律**：每条结论标 `DECISION`（Owner 架构选择）/ `OBSERVED`(有实测锚) / `UNKNOWN`（无证据，不推断）。**DECISION ≠ IMPLEMENTATION**——架构选择已下达，实现尚未发生。
>
> **2026-09-16 更新（并入 IF-v2 / Readiness）**：
> - **B1 双层架构保留**。曾有一条指令将 transport 写作「IR → V3，manifest 不作 source identity authority」，与两仓已入册的 DEC-019 / DEC-020 相反；经 Owner 确认**按双层理解**——Manifest = Source Identity Authority（身份对账面），IR = Semantic Consumption Authority（语义消费面），**语义消费方向 = IR → V3**。本报告 §1 据此维持。
> - **两张汇总表移入契约**：Decision Alignment Table = `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` §5.3；Implementation Status Table = 同文件 §5.4。本报告保留逐项细节与证据锚。
> - producer 侧事实基线升级为 Interface Facts v2 + B1-B3 Readiness @ preprocessing `b39b6da`。
>
> **证据基线**：
> | 侧 | 基线 |
> |---|---|
> | V3 代码 | `b5ddbe3`（其后仅文档提交，代码未变） |
> | V3 文档 | `1243a7f`（Decision Alignment + Contract v0.2 DRAFT 首版） |
> | preprocessing | `b39b6da`（IF-v2 + B1-B3 Readiness + Closure Plan v2 + DEC-019） |
> | 被对齐契约 | v0.1 @ `1fbaf5e`（未改）；v0.2 DRAFT 见同目录（NOT FROZEN） |
>
> **Owner 裁决来源**：DEC-019 @ preprocessing `b39b6da`（DSH 自记，authority = 用户裁定 2026-09-16 聊天原文）= DEC-020/021/022 @ V3 `1243a7f`，两仓内容一致。

---

## 0. Owner 裁决（逐字收录，`DECISION`）

### B1 Transport — `DECISION`

> 正式生产接口采用 **Manifest + IR 双层接口**。
> - Manifest = **Source Identity Authority**
> - IR = **Semantic Consumption Authority**
> - 两者必须通过明确 **`source_version_id`** 关联。

### B2 Identity — `DECISION`

> source identity 统一采用 **Original Source Bytes SHA-256**，即 `SHA-256(raw bytes)`。
> 其他 hash（canonical_json hash / body_hash / line_hash / integrity_hash）**只能作为内部完整性/一致性校验，不得替代 source identity**。

### B3 Semantic Boundary — `DECISION`

> unknown `unit_type`：**不得自动转换。不得静默 fallback。不得进入 Question materialization。**
> 处理方式：**UNKNOWN/PENDING**。

---

## 1. B1 Transport 对齐

### 1.1 DECISION 要求（见 §0 B1）

双层接口 + 显式 `source_version_id` 关联。

### 1.2 OBSERVED 现状

| 事实 | 证据 |
|---|---|
| V3 唯一消费载体 = manifest；IR 消费 = 0 命中 | `manifest_reader.py:44-75`；`Grep resolver_ir\|source_sha256 @ backend/` = 0（V3 @ `b5ddbe3`） |
| `Manifest` dataclass 无 sha、无 `source_version_id` 字段 | `manifest_reader.py:28-35`（仅 source_file/model/prompt_version/validation_issues/warnings/units） |
| manifest 层 0/166 携带任何 sha 键 | preprocessing INTERFACE FACTS v1 §1 S2 @ `17c55d8`；DQE §4 @ `4d78513` |
| IR 层有 `source_sha256`（源 md 原始字节 SHA-256），71/71 零漂移 | INTERFACE FACTS v1 §1 S3 @ `17c55d8`；`resolver_reference.py:249` |
| producer 侧无单一输出面同时具备全语料覆盖 + md sha 锚 + 持续产出 | INTERFACE FACTS v1 §0 合取事实 @ `17c55d8`（FACT-035） |
| identity 面分裂：v2 = 87 份 / v1 legacy = 79 份；覆盖面以 87 为上限 | INTERFACE FACTS v1 §1 S2 @ `17c55d8` |
| 两份 DRAFT 传输链互斥且均未 ack（v0.1 契约 §2 写 IR→V3；V3 侧需求稿写 manifest→V3） | Reconciliation v0.2 §B1 @ `ad1abdd` |

### 1.3 DECISION → IMPLEMENTATION 缺口

| # | 缺口 | 性质 | 状态 |
|---|---|---|---|
| B1-G1 | Manifest 侧无 `source_version_id` 字段（Source Identity Authority 载体缺身份键） | **producer 接口变更需求**——落点归 DSH/Owner，本报告不提案 | `IMPLEMENTATION: not started` |
| B1-G2 | IR 侧有 `source_sha256` 但无名为 `source_version_id` 的关联键；与 Manifest 的关联字段如何命名/取值 = 接口定义项 | producer 接口定义项 | `IMPLEMENTATION: not started` |
| B1-G3 | V3 侧零 IR 消费能力；IR 作为 Semantic Consumption Authority 要求 V3 具备 IR 读取路径 | **V3 新增消费能力**——排期归 Owner，本报告不提案 | `IMPLEMENTATION: not started` |
| B1-G4 | V3 `source_version_id` 是内部 UUID（`document_source_versions` 主键，`models/source.py:44-57`；`evidence.py:44-46` FK），**不是**跨系统键。跨系统身份需经 V3 侧字段承载 producer sha——当前 consumer 路径写入的 `documents.original_sha256` 是 canonical_json 包裹值（`runner.py:73`；`hashing.py:60-62`），**不是 raw bytes sha** | V3 消费侧绑定缺口 | `IMPLEMENTATION: not started` |
| B1-G5 | 79 份 identity v1 manifest 的处置（C-IN-1 现状 = 拒收）未因本裁决改变 | 事实边界，独立问题 | `OBSERVED`（非新缺口） |

### 1.4 UNKNOWN（无证据，不推断）

- producer 侧将用哪个字段名承载 `source_version_id`、其取值是 sha 本身还是独立 ID → **UNKNOWN**（DSH 域）。
- V3 侧 IR loader 的形态/排期 → **UNKNOWN**（Owner 未下达实现排期）。
- 双层接口下「全语料 IR」是否重新产出、何时产出 → **UNKNOWN**（属数据生成动作，须 Owner 显式令；暂停令 `746e35c` 仍生效）。

---

## 2. B2 Identity 对齐

### 2.1 DECISION 要求（见 §0 B2）

唯一 source identity = `SHA-256(raw bytes)`；其他 hash 仅内部校验，禁止作跨系统 identity。

### 2.2 OBSERVED 现状

| 事实 | 证据 |
|---|---|
| producer `source_sha256` 输入口径 = 源 md **原始文件字节**（与 DECISION 一致） | Reconciliation v0.2 §B1 @ `ad1abdd` VERIFIED；`resolver_reference.py:52-53,249` |
| producer 输出面 hash 全集 = 原始字节 SHA-256 单族（md/PDF 两种 source_sha256 + corpus_sha256）；`body_hash`/`line_hash` **零产出** | INTERFACE FACTS v1 §2/§4 @ `17c55d8`（FACT-036） |
| V3 `file_sha = sha256_hex(body_text)`：canonical_json 引号包裹 → 与 raw bytes sha **永远 DIFFER** | `hashing.py:60-62`；`runner.py:71-73`；v0.1 实测 12/12 DIFFER |
| V3 `body_hash`：splitlines 取行（`:27`）→ `\n` join → raw SHA-256 → 含 CRLF/尾随换行文件漂移 | `source_loader.py:27,43-46`（E-2 勘误后行号）；v0.1 实测 6/12 DIFFER |
| V3 `line_hash` 同表两算法并存（consumer raw 单行 vs 生产 canonical 复合） | `source_loader.py:38` vs `line_index.py:75-90`（GAP-MAP L5） |
| V3 `integrity_hash` consumer 路径退化为 `= body_hash` | `runner.py:93`；`runner_b2.py:165` |
| V3 编译域自有规则：`text_hash raw 绝不经 canonical JSON`（与 B2 方向一致的仓内先例） | `compile/__init__.py:10` |
| `documents.original_sha256` UNIQUE（Document Identity 字段，`models/source.py:30-37`） | 同上 |

### 2.3 DECISION → IMPLEMENTATION 缺口

| # | 缺口 | 性质 | 状态 |
|---|---|---|---|
| B2-G1 | consumer 路径写入 `documents.original_sha256` 的值是 canonical_json 包裹 hash，**不符合** DECISION 的 raw bytes 定义 | V3 消费侧 | `IMPLEMENTATION: not started` |
| B2-G2 | V3 自算 `body_hash`/`line_hash`/`integrity_hash` 按 DECISION **不得**作跨系统 identity——当前它们本就未作跨系统用（producer 零对应物），DECISION 将其正式限定为内部校验 | 边界澄清（现状与 DECISION 不冲突） | `OBSERVED`（无实现缺口，契约措辞项） |
| B2-G3 | 跨系统对账闸门（v0.1 契约 §3.3-3「sha 不一致 → 阻断」）在 raw bytes 口径下可执行的前提：载体上有该字段 + 双方独立重算。载体缺口见 B1-G1/B1-G4 | 依赖 B1 | `IMPLEMENTATION: not started` |
| B2-G4 | `norm_sha256`（r64 NORM_ALGO）算法在 producer 仓内定义但从未作接口发布；DECISION 未涉及该 hash → 若未来需要文本规范化对账，属**新增接口产出** | 开放项 | `UNKNOWN`（DECISION 未覆盖） |

### 2.4 UNKNOWN

- V3 侧现有 `body_hash`/`line_hash` 双算法共存（G-4）是否在 DECISION 下需要治理、如何治理 → **UNKNOWN**（DECISION 只限定「不得作跨系统 identity」，未裁定 V3 内部一致性治理）。
- raw bytes sha 在 V3 侧的写入点/校验点排期 → **UNKNOWN**（Owner 未下达实现排期）。

---

## 3. B3 Semantic Boundary 对齐

### 3.1 DECISION 要求（见 §0 B3）

unknown `unit_type`：不得自动转换 / 不得静默 fallback / 不得进入 Question materialization；处理方式 UNKNOWN/PENDING。

### 3.2 OBSERVED 现状

| 事实 | 证据 |
|---|---|
| `manifest_reader.py:52` 硬取 `u["unit_type"]`，无闭集校验 | 同上（V3 @ `b5ddbe3`） |
| annotation 层把 payload `unit_type` 硬编码重写为 `"standalone_question"`——噪声静默洗白 | `annotation_adapter.py:42`；`:101-104` |
| span 层按原始 manifest 值分支（未知 → composite 路径） | `resolved_span_adapter.py:77-90`；`runner_b2.py:116-127` |
| candidate 层零落库：incomplete → `runner_b2.py:232-239` skip+continue，永不到达 `:252` | 同上 |
| 终态 = 静默 incomplete→skip；真实原因（unknown unit_type）在任何一层都不出现 | GAP-MAP §0 E-1；Reconciliation v0.2 §B3 @ `ad1abdd` |
| IR `semantic_status` 冻结值域 = `{ready, incomplete}`（BUG-V3-018）——**无 unknown/pending 值** | `compile/__init__.py:28-29` |
| Gate `decision_status` 冻结值域 = `{pending_review, approved, rejected}`（10 §5.2） | `gate/__init__.py:10-11` |
| `pending_review` 通道当前**仅对 ready 单元可达**（ready 才 evaluate → create candidate）；非 ready 单元在 `runner_b2.py:232-239` 被 skip，**进不了 pending_review** | `runner_b2.py:231-264`；`snapshot_repository.py:118-129` |
| V3 candidate `unit_type` 冻结值域 = `{standalone_unit, composite_unit}` | `gate/__init__.py:17-18`；`runner_b2.py:252` |
| 噪声是类级现象：恰 1 例 `andalone_question` + 第 2 例 schema 噪声 `explanation_lines_note`；producer 链零值域守卫 | INTERFACE FACTS v1 §1/§3-B3 @ `17c55d8` |
| DSH 已撤回 DQE §1-A「已生效」与 Closure Plan §2「fail-closed 生效中」陈述 | Reconciliation v0.2 §B3 @ `ad1abdd`（FACT-033 resolved） |

### 3.3 DECISION → IMPLEMENTATION 缺口

| # | 缺口 | 性质 | 状态 |
|---|---|---|---|
| B3-G1 | 当前终态 = 静默 incomplete→skip，**既非 UNKNOWN 也非 PENDING**——不满足 DECISION 的「处理方式 UNKNOWN/PENDING」 | V3 消费侧 | `IMPLEMENTATION: not started` |
| B3-G2 | `SEMANTIC_STATUS` 冻结值域 `{ready, incomplete}` 无 unknown/pending 取值；`UNIT_TYPES` 冻结值域 `{standalone_unit, composite_unit}` 同样无。DECISION 要求的 UNKNOWN/PENDING 落在哪一层（IR 层扩展 / Gate 层新通道 / 其他）= **实现设计项，未裁决** | 设计项 | `UNKNOWN`（本报告不提案） |
| B3-G3 | 「不得进入 Question materialization」：当前 skip 路径本就不产 candidate/leaves（`compiler.py:72-73` 非 ready 不编译）——**该禁止项与现状不冲突**；缺口在「静默」而非「误 materialize」 | 边界澄清 | `OBSERVED`（部分已满足，见 §3.4） |
| B3-G4 | producer 侧值域守卫未实施（排期③）；DECISION 是消费侧边界，不改变 producer 现状 | producer 域 | `OBSERVED`（非 V3 缺口） |

### 3.4 DECISION 与现状的符合度（逐条）

| DECISION 禁令 | 现状 | 判定 |
|---|---|---|
| 不得自动转换 | annotation 层**已自动转换**（`annotation_adapter.py:42` 硬编码重写） | **违反** — 缺口 B3-G1 |
| 不得静默 fallback | span 层静默走 composite 路径；终态静默 incomplete→skip | **违反** — 缺口 B3-G1 |
| 不得进入 Question materialization | skip 路径不产 candidate；Compiler 非 ready 不产 leaves | **符合**（但经由静默路径达成，非显式 UNKNOWN/PENDING） |
| 处理方式 UNKNOWN/PENDING | 无 UNKNOWN/PENDING 通道可达（非 ready 进不了 pending_review） | **未实现** — 缺口 B3-G1/G2 |

---

## 4. 本轮 FACT 修正

| FACT | 修正 | 证据 |
|---|---|---|
| FACT-031 | `compute_body_hash uses splitlines (source_loader.py:43-46)` → **勘误**：splitlines 在 `load_source_lines`（`source_loader.py:27`）；`compute_body_hash`（`:43-46`）只做 join+SHA-256。漂移 6/12 结论不变 | GAP-MAP §0 E-2；Reconciliation v0.2 §B3 特别确认 4 @ `ad1abdd` |
| FACT-030/032/033 | 已在 `643ebd0` 更正（B1 措辞、B3 candidate 零落库/两层矛盾、B3 跨仓争议 resolved）——本轮复核无新增错误 | `643ebd0` |
| 新 DEC 登记 | Owner B1/B2/B3 架构裁决 → state.yaml `decisions` DEC-020/021/022 | 本报告 §0 |

---

## 5. 边界声明

**本文件做了**：Owner 三项裁决逐字收录（§0）；每项的 V3 侧 OBSERVED 现状 + DECISION→IMPLEMENTATION 缺口 + UNKNOWN 分列（§1-3）；B3 禁令逐条符合度判定（§3.4）；FACT-031 行号勘误（§4）。

**本文件没做**：未把任何 DECISION 描述为已实现（全部缺口标 `IMPLEMENTATION: not started` 或 `UNKNOWN`）；未提出实现方案（B1-G3/B3-G2 明确标设计项/排期项不提案）；未替 DSH 决定生产侧实现（B1-G1/G2 标 producer 接口变更需求，落点归 DSH/Owner）；未修改 preprocessing / V3 业务代码 / EB-008 / admission 逻辑；未冻结契约（v0.2 DRAFT 另文，见 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`）。

**EB-008 状态**：不因本文件变动。

---

*Decision Alignment Report — 2026-09-16，Claude（AITutors-v3 Consumer Owner）。V3 代码 `b5ddbe3` · 文档 `643ebd0` · preprocessing `746e35c`。DECISION ≠ IMPLEMENTATION。*
