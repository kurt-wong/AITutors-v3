# PREPROCESSING-V3-CONTRACT-BLOCKER-ANALYSIS

> **性质**：**非契约 · 非冻结文档 · 仅事实分析**。
> **目的**：Owner 裁决材料——供 Owner 就三个 blocker 逐项裁决，**不是 v0.2 草案**。
> **禁止事项（本文件遵守）**：未提出实现方案 · 未修改 Contract · 未修改 V3 · 未修改 preprocessing。
>
> **2026-09-16 状态更新**：Owner 已下达 B1/B2/B3 **架构裁决**（`DECISION`，见 `PREPROCESSING-V3-DECISION-ALIGNMENT-REPORT.md` §0）。三项 blocker 的**架构方向已定**；**实现均未开始**（`IMPLEMENTATION: not started`），落层/排期项仍 `UNKNOWN`。本文件下方「待 Owner 裁决问题」中已由 DECISION 回答的条目已标注；未回答条目仍开放。**DECISION ≠ IMPLEMENTATION。**
>
> **证据基线**：
> | 侧 | 基线 | 说明 |
> |---|---|---|
> | V3 代码 | `b5ddbe3` | 其后仅文档提交，代码未变 |
> | V3 文档 | `643ebd0` | Consumer Gap Map + 事实基线 |
> | preprocessing | `746e35c` | Owner 暂停令；Interface Facts v1 @ `17c55d8`；Reconciliation v0.2 @ `ad1abdd`；Closure Plan @ `4fdbb70`；DQE @ `4d78513` |
> | 被分析契约 | v0.1 @ `1fbaf5e` | 未改；v0.2 DRAFT 见 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`（NOT FROZEN） |
>
> **范围边界**：本文件只分析 **阻塞契约冻结的三项**。数据卫生项（figure recovery / flags registry / historical cleanup）已在 DSH Closure Plan v1 §1-B/§1-C 分类，**双方一致判定其不阻塞接口冻结**——不在此重复。相关 Owner 批准项见 Closure Plan §5。
>
> **更正登记（2026-09-16）**：本文件早期版本 CB-3「当前事实」含两处错误推断（candidate 层落 `composite_unit`、三层「静默分裂」）。经 DSH Reconciliation v0.2（`ad1abdd`）指出、我方逐行亲验确认后，**已据实更正**（见 CB-3）。权威更正落点：`PREPROCESSING-V3-CONSUMER-GAP-MAP.md` §0。

---

## CB-1 · source identity transport

### 当前事实

契约 §2 声明「V3 消费以 IR 为准，manifest 为回源凭据」；契约 §3.1 把 `source_sha256`（文件级 + 单元级 provenance）列为必须提供字段。

V3 实际状态与该声明不符：

- V3 全仓**无任何 IR 消费代码**（`Grep resolver_ir / resolver-ir / ir.json / source_sha256` @ `backend/` → **0 命中**）。
- V3 消费入口是 manifest JSON：`load_manifest`（`manifest_reader.py:44-75`），下游经 `annotation_adapter.py:97-115`（manifest → payload）与 `resolved_span_adapter.py:50-92`（manifest → ResolvedSpan）。
- `Manifest` dataclass **不含任何 sha 字段**（`manifest_reader.py:28-35`：仅 `source_file / model / prompt_version / validation_issues / warnings / units`）。
- 分层实测（DQE §4 @ `4d78513`；INTERFACE FACTS v1 §1 @ `17c55d8` 复扫）：IR 层 `source_sha256` **71/71 零漂移**；manifest 层 **0/166** 携带任何 sha 键。

**producer 侧输出面硬约束（INTERFACE FACTS v1 §0，本轮新固化）**：

- **没有任何单一输出面同时具备「全语料覆盖 + md sha 锚 + 持续产出」**——manifest 全覆盖（166 份）但零 sha；IR 有 sha + provenance 但只是 **88 条一次性样本工件**（71 条 ADMITTED 携 `ir` 对象，1,664 单元；自 R52 起未再生成，冻结永不回改）；OCR 清单（1,801 条）锚的是 **PDF 不是 md**。
- **identity 面分裂**：166 份 manifest 中 **identity v2 = 87 份 / v1 legacy = 79 份**。79 份 v1 在 C-IN-1 下必被拒收——**任何载体裁决的覆盖面以 87 份 v2 为上限**，79 份的处置是独立事实问题。
- IR 生成器在库且经 R52/R53 验证，但「全语料 IR」**当前不存在**；重新产出属数据生成动作 + 新工件面，按仓内纪律须 Owner 显式令（权限事实，非方案）。

**即：契约的 required 清单按 IR 层编写，V3 实际读 manifest 层，manifest 层没有 sha；且 producer 侧当前不存在可承载该 required 清单的运行面输出。**

### 证据位置

| 证据 | 位置 |
|---|---|
| 契约消费载体声明 | preprocessing `INTEGRATION/PREPROCESSING-INTEGRATION-CONTRACT.md:33` @ `1fbaf5e` |
| 契约 required 清单含 `source_sha256` | 同上 `:82`（§3.1） |
| V3 IR 消费 = 0 | `Grep` @ `backend/`，V3 @ `b5ddbe3` |
| V3 manifest 读取器 | `backend/scripts/preprocessing_consumer/manifest_reader.py:44-75` |
| Manifest 无 sha 字段 | `backend/scripts/preprocessing_consumer/manifest_reader.py:28-35` |
| 分层 sha 实测 | preprocessing `EVIDENCE/PREPROCESSING-DATA-QUALITY-REPORT.md` §4 @ `4d78513` |
| 五输出面清点 + 核心合取事实 + identity 87/79 | preprocessing `INTEGRATION/PREPROCESSING-PRODUCER-INTERFACE-FACTS.md` §0/§1 @ `17c55d8` |
| 传输层三断点 + 无双方 ack 的传输链 | preprocessing `INTEGRATION/PREPROCESSING-PRODUCER-FACT-RECONCILIATION-v0.2.md` §B1 @ `ad1abdd` |
| 完整审查 | V3 `CONTRACTS/PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW-v0.2.md` §A @ `938535d` |

### 影响范围

1. **契约 §3.1 required 承诺在 V3 消费路径上无数据可验证**——required 字段写在 V3 不读的载体上。
2. **契约 §4.2「`source_version_id` ↔ `source_sha256` 一一对应」无处落地**（该主张同时受 CB-2 制约）。
3. **CB-2 与 CB-3 均依赖本项**：CB-2 的对账需要先确定在哪个载体上比对；CB-3 的隔离执行面需要先确定消费载体。本项不裁，则另两项无统一落点。
4. 不影响已成立的部分：行锚机制（`[start,end]` → `P1L{line:03d}`）在 manifest 路径上已验证可用（Phase 0.3-B 527/548 = 96.2% coverage）——**阻塞的是 identity 对账，不是行定位**。

### 待 Owner 裁决问题

> **DECISION 已回答（2026-09-16）**：Q1-1 → **Manifest + IR 双层接口**（Manifest = Source Identity Authority，IR = Semantic Consumption Authority，经 `source_version_id` 关联）。其余问题状态如下。

- **Q1-1**：~~V3 消费载体裁定为哪一种？~~ **已裁决**：双层并行（`DECISION`，见 v0.2 DRAFT §1.1）。
- **Q1-2**：若裁定 manifest 为消费载体，契约 §3.1 中 IR 层独有字段（含 `source_sha256`）的 required 地位如何处置——**部分回答**：双层各有权威面，required 清单需按层拆分（v0.2 DRAFT §3.1/§5）；**具体字段归属表仍开放**。
- **Q1-3**：~~若裁定 IR 为消费载体，V3 侧 IR loader 的排期是否作为契约冻结前置条件？~~ **仍开放**（`UNKNOWN`）——v0.2 DRAFT §8-4 将排期归属列为冻结前提，须 Owner 另裁。
- **Q1-4**：契约 §2「V3 消费以 IR 为准」的措辞——**已由 v0.2 DRAFT §3.1 取代**（双层各有权威面，不再单层优先）。

**状态：DECIDED（架构）· IMPLEMENTATION: not started · 排期 UNKNOWN。**

---

## CB-2 · hash identity

### 当前事实

producer 侧 `source_sha256` 的定义 = 源 OCR markdown **原始文件字节** SHA-256（契约 §1.1）。契约 §1.2 规定 V3 义务：消费前独立重算 sha 与声明值比对，不一致 → 阻断（§3.3-3）。

V3 自算的两路 hash **均无法与之对上**：

| V3 路径 | 机制 | 结果 | 位置 |
|---|---|---|---|
| `file_sha = sha256_hex(body_text)` | 先 `canonical_json` 再 SHA-256（字符串被 JSON 引号包裹） | **永远 DIFFER** | `app/core/hashing.py:60-62`；`runner.py:73` |
| `body_hash = compute_body_hash(lines)` | `splitlines()` 规范化后 `\n` join 再 SHA-256 | 含 CRLF / 尾随换行的文件**漂移** | `source_loader.py:43-46`；`runner.py:72` |

v0.1 实测（12 份 ADMITTED 样本）：`file_sha` 路径 12/12 DIFFER；`body_hash` 路径 **6/12 DIFFER**（差异文件全部含 CRLF 或尾随换行）。

**producer 侧 hash 输出面（INTERFACE FACTS v1 §2，穷举复证）**：

- producer 输出面 hash 全集 = `source_sha256`(md 原始字节) / `source_sha256`(PDF 原始字节) / `corpus_sha256`(快照指纹)——**算法族唯一**（原始字节 SHA-256），无密钥、无版本化参数，任一方可用标准库独立重算。
- **`body_hash` / `line_hash` producer 零产出**（全仓 grep = 0）——「算法是否一致」在跨系统层面**无对象可比**；它们是 V3 内部字段。
- `norm_sha256` 归一化算法**已在 producer 仓内定义**（r64 NORM_ALGO：NFC + CRLF/CR→LF + per-line rstrip + whole strip），但**从未作为接口发布**——若口径裁决涉及文本规范化，生产侧事实是「算法定义存在、接口输出不存在」。

**即：根因不是映射表缺失，而是 hash 输入定义不一致**——原始字节 vs 规范化文本 vs canonical_json 包裹，三者互不相等；且 V3 内部 hash 在 producer 侧无对应物。

### 证据位置

| 证据 | 位置 |
|---|---|
| producer sha 定义 | 契约 `:14`（§1.1）@ `1fbaf5e` |
| V3 重算义务 | 契约 `:22`（§1.2）；`:101`（§3.3-3 阻断） |
| 一一对应主张 | 契约 `:115`（§4.2） |
| canonical_json 包裹 | `backend/app/core/hashing.py:60-62` |
| splitlines 规范化 | `backend/scripts/preprocessing_consumer/source_loader.py:27`（`load_source_lines`；勘误见 GAP-MAP §0 E-2）；join+hash 在 `:43-46` |
| consumer 写入点 | `backend/scripts/preprocessing_consumer/runner.py:71-73` |
| producer hash 输出面穷举 + 零产出确认 | preprocessing `INTEGRATION/PREPROCESSING-PRODUCER-INTERFACE-FACTS.md` §2/§4 @ `17c55d8` |
| producer 输入口径书面确认（原始字节） | preprocessing `INTEGRATION/PREPROCESSING-PRODUCER-FACT-RECONCILIATION-v0.2.md` §B1 @ `ad1abdd`（VERIFIED） |
| 12 样本实测 | V3 `CONTRACTS/PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW.md` §4.2（v0.1）@ b5ddbe3 基线 |
| 完整审查 | V3 `CONTRACTS/PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW-v0.2.md` §A.3 @ `938535d` |

### 影响范围

1. **契约 §1.2 的 V3 义务当前无法执行**——不是「尚未实现重算」，是「重算了也对不上」。
2. **§3.3-3「sha 不一致 → 阻断」当前不可用作闸门**——无一致口径则无法判定「不一致」。
3. **§4.3 authority 追溯依赖 sha 对账**（「任何对不上 sha/行号的既有 authority 必须失效」）——对账机制不成立则失效判定无依据。
4. 与 CB-1 的耦合：即便载体定了，若 hash 输入定义不统一，对账仍不成立。**两项独立成立，需分别裁决。**
5. 不影响 producer 侧自洽：IR 层 71/71 零漂移说明 producer 内部绑定完好——**问题在跨系统口径，不在任一侧内部**。

### 待 Owner 裁决问题

> **DECISION 已回答（2026-09-16）**：Q2-1 → **唯一 source identity = `SHA-256(raw bytes)`**；其他 hash 只能作内部校验。其余问题状态如下。

- **Q2-1**：~~跨系统对账 hash 的输入定义统一为什么？~~ **已裁决**：raw bytes SHA-256（`DECISION`，v0.2 DRAFT §2.1）。
- **Q2-2**：该定义由契约强制约定，还是双方各自实现后对账？——**部分回答**：契约强制约定（v0.2 DRAFT §2.1-2.3 为 REQUIREMENT）；**V3 侧现有两路 hash 与新定义的关系已明确**（不得作跨系统 identity，§2.2）；内部 hash 家族治理仍 `UNKNOWN`（OQ-7）。
- **Q2-3**：~~producer 侧计算输入口径是否需 DSH 先书面确认？~~ **已闭环**：DSH Reconciliation v0.2（`ad1abdd`）VERIFIED —— `source_sha256` 输入 = 源 md 原始文件字节。
- **Q2-4**：~~在口径统一前，契约 §3.3-3 的阻断条款如何表述？~~ **已回答**：口径已统一（§2.1）；阻断条款按 raw bytes 重述（v0.2 DRAFT §2.3/§4.4）；**可执行前提（载体）未满足**——依赖 B1 实现。

**状态：DECIDED（口径）· IMPLEMENTATION: not started（V3 写入/对账未按新口径实现）。**

---

## CB-3 · unit_type semantics

### 当前事实

**producer 侧**：非标准值恰 **1 例** `andalone_question`（DQE §1 全语料穷举：166 manifest × 4,609 单元 + IR 1,664 单元）。位置 = `Ocr-markdown\reslice-batch-C\合格考\化学\2020北京高中合格考化学（第一次）（教师版）(1).manifest.json`，unit `Q1`，属 identity v2 **可消费面**（非 legacy 边角）。producer 链零守卫：LLM 输出原样落盘（`write_outputs` 无值域校验）→ resolver 逐字复制（`resolver_reference.py:152`）——**生产侧今天没有任何一层检查 `unit_type`**。IR 忠实携带（零重塑；IR 单元值域 1,385 standalone / 278 composite / 1 andle——INTERFACE FACTS v1 §1 S3）。该 manifest 是 **R50_input_baseline 成员**（356 文件之一，pin sha `58058c4f…`）——Closure Plan §2 硬事实。

**噪声是类级现象，不是单点**（INTERFACE FACTS v1 §1，本轮新固化）：第 2 例 schema 噪声 = 游离键 `explanation_lines_note`（value = null；batch-C 理综哈尔滨三中 manifest，unit Q24）。两例均在 v2 可消费面内，均不在 v1 legacy 面。

**V3 侧（更正后事实形态）**：

`manifest_reader.py:52` 硬取 `u["unit_type"]`，**不校验闭集**。下游对未知值的实际行为 = **两层矛盾 + candidate 层零落库**：

| 层 | 实际行为 | 位置 |
|---|---|---|
| annotation 层 | `annotation_adapter.py:42` 把 payload 的 `unit_type` **硬编码重写**为 `"standalone_question"`——噪声在此被**静默洗白**，下游 payload 不含异常值，无任何信号 | `annotation_adapter.py:42`；`:101-104` |
| span 层 | 两轨均按**原始 manifest 值**分支（`== "standalone_question"`? 否 → composite 路径），产出 composite 式 spans；两轨都不产 `sp-Q1.stem` | `resolved_span_adapter.py:77-90`；`runner_b2.py:116-127` |
| candidate 层 | **零落库**——该单元 `semantic_status=incomplete`（stem 缺失）→ `runner_b2.py:232-239` skip+continue，**永不到达** `:252`。即便到达，IRBuilder 从洗白后 payload 取值（`ir.py:108`）会落 `standalone_unit`，**非** `composite_unit` | `runner_b2.py:232-239,252`；`ir.py:106-108` |

**矛盾 = annotation（standalone 编排）vs span（composite 解析）两层矛盾，不是三处。** 终态 = 无信号 `incomplete` → skip。记录在案的原因是 `"stem unresolved"` / `"options missing for choice type"`，**真实原因（unknown unit_type）在任何一层都不出现**——静默失败掩盖，比「静默当 standalone 吃」更隐蔽（消费方看到格式类错误，不会想到值域噪声）。

> **更正登记**：本文件早期版本曾写「candidate 层落 `composite_unit`、四处解释互相矛盾、静默分裂」——该结论**错误**，经 DSH Reconciliation v0.2（`ad1abdd` §B3）指出后我方逐行亲验确认更正成立。权威更正落点见 `PREPROCESSING-V3-CONSUMER-GAP-MAP.md` §0 E-1。**该更正不改变 CB-3 作为 blocker 的判定**：契约 §3.3-6 的隔离仍未实现。

**跨仓事实错误（已消解）**：

| 陈述 | 位置 | 处置状态 |
|---|---|---|
| 消费侧隔离「已生效，无需动作」 | DQE §1 选项 A @ `4d78513` | **DSH 已正式撤回**（Reconciliation v0.2 §B3 @ `ad1abdd`）——双方已对齐 |
| 「非闭集值 → PENDING 通道…fail-closed 生效中」 | Closure Plan §2 影响节 @ `4fdbb70` | 同上确认不准确——实际终态是 incomplete→skip，非 PENDING 通道隔离 |

### 证据位置

| 证据 | 位置 |
|---|---|
| 非标准值穷举 + 位置 | preprocessing `EVIDENCE/PREPROCESSING-DATA-QUALITY-REPORT.md` §1 @ `4d78513` |
| R50 基线成员身份 + snapshot 硬事实 | preprocessing `PREPROCESSING-CLOSURE-PLAN.md` §2 @ `4fdbb70` |
| 六层追踪 + 更正 + DQE 撤回 | preprocessing `INTEGRATION/PREPROCESSING-PRODUCER-FACT-RECONCILIATION-v0.2.md` §B3 @ `ad1abdd` |
| 噪声第 2 例 + producer 零守卫 + IR 值域 | preprocessing `INTEGRATION/PREPROCESSING-PRODUCER-INTERFACE-FACTS.md` §1/§3-B3 @ `17c55d8` |
| 契约隔离要求 | 契约 `:104`（§3.3-6）@ `1fbaf5e` |
| 无闭集校验 | `backend/scripts/preprocessing_consumer/manifest_reader.py:52` |
| annotation 洗白 | `annotation_adapter.py:42`；`:101-104` |
| span 层按原始值分支 | `resolved_span_adapter.py:77-90`；`runner_b2.py:116-127` |
| candidate 零落库（incomplete → skip） | `runner_b2.py:232-239`；`compile/ir.py:108,216-218` |
| 跨仓矛盾登记与消解 | V3 `state.yaml` FACT-032/033；handoff 007 B3 |
| 完整审查（含 v0.1 GAP-C2 勘误） | V3 `CONTRACTS/PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW-v0.2.md` §B @ `938535d`；更正落点 `CONSUMER-GAP-MAP.md` §0 |

### 影响范围

1. **契约 §3.3-6 的隔离要求未实现**——且更正后的真实终态比契约禁止的「静默当 standalone 吃」更隐蔽：静默失败掩盖，消费方看到的是格式类错误，不会想到值域噪声。
2. **数据完整性风险**：同一 unit 两层语义不一致——annotation（standalone 编排）vs span（composite 解析）；candidate 层无记录。当前损失面 = **恰 1 单元**（无扩散，unit_id 仍为 Q1），但**机制性风险与损失面规模无关**；且噪声是类级现象（第 2 例已出现）。
3. **跨仓事实错误已消解**：DSH 已撤回 DQE §1-A「已生效」与 Closure Plan §2「fail-closed 生效中」陈述（Reconciliation v0.2 §B3）。**v0.2 事实基线不再受污染**——该项从「跨仓争议」转为「双方已对齐的事实」。
4. 与 OD-1（Closure Plan §1-A / §5-1）耦合：**披露路线 vs 清洁路线**是 DSH 侧 Owner 待批项。但需注意——**在 V3 隔离面未实现之前，修复数据与否不改变 V3 当前零隔离的事实**。两项需分别裁决，不可互相替代。
5. 不影响其余 4,608 单元：canonical 二值本身分流正确。

### 待 Owner 裁决问题

> **DECISION 已回答（2026-09-16）**：unknown `unit_type` → **不自动转换 / 不静默 fallback / 不 materialize；处理方式 UNKNOWN/PENDING**。其余问题状态如下。

- **Q3-1**：~~unit_type 隔离的执行面在哪一层？~~ **部分回答**：处置语义已裁决（UNKNOWN/PENDING，v0.2 DRAFT §3.2/§4.1）；**落层设计仍 `UNKNOWN`**（B3-G2 / OQ-5——涉及冻结值域 BUG-V3-018 与 10 §5.2，须 Owner 另裁）。
- **Q3-2**：~~DSH 侧「已生效 / fail-closed 生效中」陈述如何处置？~~ **已闭环**：DSH Reconciliation v0.2（`ad1abdd` §B3）正式撤回两处陈述并确认 V3 四消费点零隔离信号。
- **Q3-3**：契约 §3.3-6 措辞是否需按 V3 实况调整——**已回答**：v0.2 DRAFT §3.2/§4.1/§4.2 将其升格为四条禁令 + 三处置禁止混淆（冻结候选措辞）。
- **Q3-4**：披露路线 vs 清洁路线（与 Closure Plan §5-1 同源）——**仍开放**；DECISION 不涉及数据清洗，该裁决**不能替代** Q3-1 落层裁定。

**状态：DECIDED（处置语义）· IMPLEMENTATION: not started（当前仍是静默 incomplete→skip）· 落层 UNKNOWN。**

---

## 三项关系与裁决顺序

```
CB-1 transport ──┬──→ CB-2 对账落点（载体未定则无处比对）
   （根因）      └──→ CB-3 隔离执行面（载体未定则无统一执行层）
```

- **CB-1 是根因**：不裁则 CB-2/CB-3 各自的裁决缺乏落点。
- **CB-2 与 CB-3 相互独立**：hash 口径与 unit_type 隔离无直接依赖，可在 CB-1 之后并行裁决。
- **2026-09-16 状态**：三项**架构均已裁决**（`DECISION`）。CB-1 → 双层接口；CB-2 → raw bytes 唯一 identity；CB-3 → UNKNOWN/PENDING 处置语义。**实现均未开始**；仍开放的落点/排期项：Q1-2 字段归属表、Q1-3 排期归属、OQ-5 落层设计、OQ-7 内部 hash 治理、OQ-8 producer 字段命名。本文件不预填实现方案。

---

## 边界声明

**本文件做了**：三个 blocker 的事实陈述 + 行级证据位置 + 影响范围 + 待 Owner 裁决问题（含 DECISION 回答状态标注）；CB-3 两处错误推断的删除与更正（candidate composite_unit / 三层分裂 → 两层矛盾 + candidate 零落库 + 静默失败掩盖）；producer 侧新事实并入（identity 87/79、五输出面合取约束、hash 零产出、噪声类级现象）；Q2-3 / Q3-2 确认请求闭环登记；跨仓事实错误消解登记；Owner 架构裁决状态同步（DECIDED 架构 / IMPLEMENTATION not started / 落层 UNKNOWN）。

**本文件没做（任务禁止项）**：未提出实现方案 · **未把 DECISION 描述为已实现** · 未修改 Contract（preprocessing 仓契约本体未动）· 未修改 V3（代码零改动）· 未修改 preprocessing · 未冻结任何文档 · 未代 Owner 填任何裁决结论。

**被取代物**：`CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT-SKELETON.md`（早期骨架）**不进入正式历史**，保留于工作区未提交。本文件与 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`（冻结候选）共同构成当前裁决/契约材料。

**EB-008 状态**：不因本文件变动。

---

*BLOCKER-ANALYSIS — 2026-09-16，Claude（AITutors-v3）。V3 代码基线 `b5ddbe3` · 文档 `643ebd0` · preprocessing `746e35c` · v0.1 `1fbaf5e`（未改）· v0.2 DRAFT 另文（NOT FROZEN）。非契约 / 非冻结文档 / 仅事实分析。DECISION ≠ IMPLEMENTATION。*
