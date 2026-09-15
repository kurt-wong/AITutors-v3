# PREPROCESSING-V3-CONSUMER-GAP-MAP

> **角色**：Claude = **V3 Consumer Owner**（陈述 V3 自身消费面事实）。**不是** preprocessing 审查者。
> **性质**：V3 侧事实地图。**非契约 · 非冻结文档 · 不提出实现方案**。
> **目的**：为 Owner 裁决 B1/B2/B3 提供 V3 侧事实输入。
> **遵守**：未修改 EB-008 · 未冻结 contract · 未修改 V3/preprocessing 代码 · 未提实现方案。
>
> **证据基线**：
> | 侧 | 基线 |
> |---|---|
> | V3 代码 | `b5ddbe3`（其后仅文档提交，代码未变） |
> | preprocessing | `746e35c`（Owner 暂停令；Interface Facts v1 @ `17c55d8`；Reconciliation v0.2 @ `ad1abdd`） |
> | 被分析契约 | `INTEGRATION/PREPROCESSING-INTEGRATION-CONTRACT.md` @ `1fbaf5e`（未改） |
>
> **本轮关键输入**：DSH `INTEGRATION/PREPROCESSING-PRODUCER-FACT-RECONCILIATION-v0.2.md` @ `ad1abdd`（逐行亲读 V3 代码，**更正了我方两处结论**——经我亲验，两处更正均成立，见 §0）；DSH `INTEGRATION/PREPROCESSING-PRODUCER-INTERFACE-FACTS.md` v1 @ `17c55d8`（生产侧五输出面清点、identity 87/79 分裂、hash 零产出确认、schema 噪声第 2 例）。另：preprocessing 侧 Owner 已下暂停令（`746e35c`——数据清洗/schema/daemon/contract 全暂停，等 B1/B2/B3 裁决）。

---

## 0. 对既有 V3 文档的更正（亲验后确认）

DSH Reconciliation v0.2 指出我方 BLOCKER-ANALYSIS / Review v0.2 的两处错误。**我逐行复核，确认更正成立**，据实修正：

| # | 我方原结论 | 更正后事实 | 我的亲验 |
|---|---|---|---|
| **E-1** | CB-3：candidate 层落 `composite_unit`，「三处解释互相矛盾」 | candidate 层**零落库**——该单元 `semantic_status=incomplete` → `runner_b2.py:232-239` skip+continue，**永不到达** `:252`。即便到达，IRBuilder 从**洗白后** payload 取值（`ir.py:108`）会落 `standalone_unit`，非 `composite_unit` | ✅ 成立：`runner_b2.py:231-252`；`ir.py:106-108`；`annotation_adapter.py:42` |
| **E-2** | Review §A.3：`splitlines()` 规范化在 `compute_body_hash`（`source_loader.py:43-46`） | `splitlines()` 在 `load_source_lines`（`source_loader.py:27`）；`compute_body_hash` 本身只做 `"\n".join` + sha256。**6/12 DIFFER 结论不变** | ✅ 成立：`source_loader.py:24-46` |

**更正后的 CB-3 事实形态**（取代 BLOCKER-ANALYSIS §CB-3 的「当前事实」段）：

- **annotation 层**：`annotation_adapter.py:42` 把 payload 的 `unit_type` **硬编码重写**为 `"standalone_question"`——噪声在此被**静默洗白**，下游 payload 不含异常值，无任何信号。
- **span 层**：两轨均按**原始 manifest 值**分支（`== "standalone_question"`? 否 → composite 路径），产出 composite 式 spans。
- **矛盾** = annotation（standalone 编排）vs span（composite 解析）**两层矛盾**成立。
- **candidate 层**：无记录（incomplete → skip），**不是第三种解释**。
- **终态**：无信号的 `incomplete` → skip。记录在案的原因是 `"stem unresolved"` / `"options missing for choice type"`，**真实原因（unknown unit_type）在任何一层都不出现**——静默失败掩盖。

> 此更正**不改变** CB-3 作为 blocker 的判定：契约 §3.3-6 的隔离仍未实现；且 DSH 已正式撤回 DQE §1-A「已生效」陈述（Reconciliation v0.2 §B3 特别确认），FACT-033 的矛盾登记现已由 producer 侧确认并更正，**该项从「跨仓争议」转为「双方已对齐的事实」**。
>
> **BLOCKER-ANALYSIS 已同步更正**：其 §CB-3「当前事实」段的 candidate `composite_unit` 推断与三层「静默分裂」表述已在同批删除，替换为本节更正后形态。本节为更正的权威记录（含错误→更正的对照）。

---

## 1. V3 消费管线现状（自有事实，五层）

V3 从 preprocessing 产物到落库的实际路径。**每一层标明该层的事实来源**：`[V3自有]` = V3 内部机制 · `[Contract声明]` = 契约 v0.1 对该层的主张。

### L1 · 载体读取

| 事实 | 位置 | 来源 |
|---|---|---|
| 读取器 = `load_manifest`，读 manifest JSON | `manifest_reader.py:44-75` | `[V3自有]` |
| `Manifest` dataclass 字段：`source_file / model / prompt_version / validation_issues / warnings / units` + unit 级 15 字段 | `manifest_reader.py:28-35`；`:50-67` | `[V3自有]` |
| **无 sha 字段**（`source_sha256` / `body_hash` / `line_hash` 均不在 Manifest 内） | 同上 | `[V3自有]` |
| `unit_type` 硬取 `u["unit_type"]`，**无闭集校验** | `manifest_reader.py:52` | `[V3自有]` |
| V3 全仓 IR 消费 = **0 命中** | `Grep resolver_ir / resolver-ir / source_sha256` @ `backend/` | `[V3自有]` |
| ~~契约主张：V3 消费以 IR 为准~~ | 契约 `:33` | `[Contract声明]` — **与 V3 实况不符** |

### L2 · 适配转换

| 事实 | 位置 | 来源 |
|---|---|---|
| manifest → annotation payload（`unit_type` 硬编码重写为 canonical 值） | `annotation_adapter.py:97-115`；`:42` | `[V3自有]` |
| manifest → ResolvedSpan（行区间 → `P1L{line:03d}`，越界 → unresolved 显式记录） | `resolved_span_adapter.py:50-92`；`:30-47,63-75` | `[V3自有]` |
| span_id 约定 `sp-{unit_id}.{role}` | `resolved_span_adapter.py:35` | `[V3自有]` |
| options 不 fabricate per-label（诚实 incomplete） | `annotation_adapter.py:35-39` | `[V3自有]` |

### L3 · 编译

| 事实 | 位置 | 来源 |
|---|---|---|
| IRBuilder 从 payload 取 `unit_type`（默认 `standalone_question`） | `ir.py:108` | `[V3自有]` |
| figure_refs 延后（BUG-V3-020）；image/blank → `unsupported=True` → incomplete | `ir.py:145`；`:220-222` | `[V3自有]` |
| choice 型无 options → `"options missing for choice type"` → incomplete | `ir.py:216-218` | `[V3自有]` |
| composite 缺 material → invalid | `ir.py:230` | `[V3自有]` |

### L4 · 落库与闸门

| 事实 | 位置 | 来源 |
|---|---|---|
| Track B2：非 ready → skip（不产 candidate） | `runner_b2.py:232-239` | `[V3自有]` |
| Track B2：ready 才产 candidate，`unit_type` 从 IRNode 取值经三元式 | `runner_b2.py:252-256` | `[V3自有]` |
| Track A：`GateService.run` 用 V3 自有 `SourceResolver`（搜索式，**不消费 manifest 行号**） | `gate/service.py:156-158` | `[V3自有]` |
| Gate 对非 ready 同样跳过 | `gate/service.py:182-184` | `[V3自有]` |
| claim_id = IR root unit_id；AuthorityIdentity = (source_version_id, candidate_id, claim_id)，run_id 禁入 | `admission.py:531-538`；`evidence.py:28-29` | `[V3自有]`（EB-008，**本文件不涉其状态**） |

### L5 · hash 家族（V3 自有三字段，producer 不产出）

DSH Reconciliation v0.2 B2 四列核对 + 我方亲验，确认这三个字段 **preprocessing 全仓 0 命中，纯 V3 内部产物**：

| 字段 | consumer 路径算法 | 生产 seal 路径算法 | 两路径是否同算法 |
|---|---|---|---|
| `body_hash` | `splitlines()` 取行（`source_loader.py:27`）→ `\n` join → raw SHA-256（`:43-46`） | body_text 按 seq `\n` join 重建 → raw SHA-256（`line_index.py:70-72`） | **是**（同为 raw UTF-8 SHA-256） |
| `line_hash` | **raw 单行** `sha256(text)`（`source_loader.py:38`） | **canonical 复合** `sha256_hex({text, raw_sources, selected_source, evidence})`（`line_index.py:75-90`） | **否——同一张表 `document_source_lines.line_hash` 两种语义并存** |
| `integrity_hash` | **退化** `= body_hash`（`runner.py:93`；`runner_b2.py:165`） | 复合 `sha256_hex({body_hash, line_hashes, figure_hashes, provenance})`（`line_index.py:93-108`） | **否——consumer 路径丢失 figure/provenance 敏感性** |

**亲验确认**：三行全部属实（`line_index.py:60-108` 逐行读）。`line_hash` 双算法与 `integrity_hash` 退化属 **V3 内部治理事实**，DSH 明确不在其处置范围（Reconciliation v0.2 B2 附带 OBSERVED，标 UNKNOWN：V3 是否有意允许两路径同库共存）。

**另**：`file_sha = sha256_hex(body_text)` 写入 `documents.original_sha256`（`runner.py:73`；`runner_b2.py:145`）——经 canonical_json 引号包裹（`hashing.py:60-62`），与 producer `source_sha256` 是两个函数族。

---

## 2. 字段来源分类（Gap Map 核心）

### 2.1 V3 实际消费的字段，逐个标来源

| 字段 | V3 消费点 | 来源 | 契约 v0.1 是否列为 required |
|---|---|---|---|
| `unit_id` | span_id / claim_id / payload 键 | preprocessing manifest | 契约 §2.1 标 **display alias，禁止作键**（V3 用作 claim_id 但被 AuthorityIdentity 三元绑定，见 `evidence.py:28-29`） |
| `unit_type` | L1 无校验 → L2 分流 | preprocessing manifest | §3.3-6 要求闭集隔离（**未实现**） |
| `question_numbers` | `_qn` → question_label | preprocessing manifest | §2.1 required |
| `original_question_type` | choice 判定前置过滤 | preprocessing manifest | §2.1 required |
| `stem/options/answer/explanation/material/questions_lines` | L2 行区间 → span | preprocessing manifest | §2.1 required（区域级） |
| `answer_evidence` | answer span 降级来源 | preprocessing manifest | §2.1 required |
| `source_file` | 源 md 路径 | preprocessing manifest | §2.1 required |
| `validation_issues` / `warnings` | Manifest 字段（读入） | preprocessing manifest | §2.1 manifest 级 |
| `body_hash` / `line_hash` / `integrity_hash` / `file_sha` | L5 全部 | **V3 自算** | 契约未定义（producer 不产出，0 命中） |
| `source_sha256` | **零消费** | producer IR 层 | §3.1 required（**但 V3 不读 IR**） |
| `printed_number` / `section` / `basis` / `qc_verdict` / `disposition` / `provenance 块` / `material_ref 字符串` / `answers 表` | **零消费**（`section` 读入后下游零用） | producer IR/manifest | §3.1 required（多为 IR 层字段） |

### 2.2 Gap 分类

**G-1 · 载体 Gap（对应 B1）**

V3 读 manifest，契约 required 清单按 IR 写。manifest 层 **0/166** 带 sha（DQE §4 + INTERFACE FACTS v1 §1 复扫一致）。故契约 §3.1 的 `source_sha256` required 承诺**在 V3 消费路径上无数据载体**。

DSH Reconciliation v0.2 B1 问题 4 补充事实：**不存在任何双方 ack 的传输链定义**——两份 DRAFT 互斥（preprocessing 契约 §2 写 `IR → V3`；V3 侧需求稿写 `manifest → V3`），且**无文档定义 `IR → manifest → V3`**（producer 链方向是 manifest → resolver → IR，IR 不回流 manifest）。

INTERFACE FACTS v1 §0 核心合取事实（生产侧硬约束）：**没有任何单一输出面同时具备「全语料覆盖 + md sha 锚 + 持续产出」**——manifest 全覆盖但零 sha；IR 有 sha 但只是 88 条一次性冻结样本工件（71 条 ADMITTED 携 `ir` 对象）；OCR 清单锚 PDF 非 md。

**identity 面分裂（覆盖上限事实）**：166 份 manifest 中 identity v2 = **87 份** / v1 legacy = **79 份**。79 份 v1 在 C-IN-1 下必被拒收——**任何载体裁决的可消费覆盖面以 87 份为上限**，79 份处置是独立事实问题（INTERFACE FACTS v1 §1 S2）。

**G-2 · hash 口径 Gap（对应 B2）**

- 跨系统锚 `source_sha256`：producer = 原始文件字节 SHA-256（`resolver_reference.py:52-53,249`，DSH Reconciliation B1-Q1 VERIFIED）；V3 自算两路均对不上（canonical_json 引号 / splitlines 规范化）。
- `body_hash` / `line_hash`：**producer 不产出**（INTERFACE FACTS v1 §2 穷举复证，全仓 grep = 0），「算法是否一致」在跨系统层面**无对象可比**——它们是 V3 内部字段，不是跨系统字段。
- producer 侧 `norm_sha256` 归一化算法已在仓内定义（r64 NORM_ALGO：NFC + CRLF/CR→LF + per-line rstrip + whole strip），但**从未作为接口发布**——若裁决涉及文本规范化，生产侧事实是「算法定义存在、接口输出不存在」。
- 真实断点是复合的：G-1（锚在 V3 消费路径上无载体）+ 本项（V3 自算值算法与 producer 定义不同）。**两项独立成立。**

**G-3 · 值域语义 Gap（对应 CB-3，更正后形态）**

- 契约 §3.3-6 要求非闭集值隔离 → **未实现**。
- 实际终态 = 无信号 incomplete → skip，真实原因不可见（§0 E-1）。
- DSH 已撤回「已生效」陈述，**双方事实已对齐**。
- **噪声是类级现象，不是单点**（INTERFACE FACTS v1 §1）：恰 1 例 `andalone_question` 之外，另有第 2 例 schema 噪声 = 游离键 `explanation_lines_note`（value = null；batch-C unit Q24）。producer 链零值域守卫（`write_outputs` 原样落盘 → `resolver_reference.py:152` 逐字复制）——生产侧今天没有任何一层检查 `unit_type`。

**G-4 · V3 内部一致性 Gap（新登记，非 blocker）**

`line_hash` 同表两算法并存、`integrity_hash` consumer 路径退化。**属 V3 内部治理**，DSH 明确不在处置范围，**不阻塞契约冻结**——但登记在案：consumer 路径写入的数据与生产路径写入的数据在同两张表内语义不同。DSH 标 UNKNOWN 是否有意允许共存；本文件同样不提案，仅登记事实。

**G-5 · 消费范围 Gap（非 blocker）**

契约 §3.1 required 清单中，V3 零消费的字段见 §2.1 末行。这些字段是 producer 自证层，V3 重新推导（行/hash 见 L5）。**不影响冻结**，但 v0.2 措辞应如实标注 V3 当前消费范围。

---

## 3. 供 Owner 裁决的 V3 侧事实输入

### B1（传输层）—— V3 侧事实

1. V3 当前**唯一**消费载体 = manifest（L1 全部证据）。
2. V3 **零** IR 消费代码，**无** IR loader 排期记录。
3. manifest 层无 sha（0/166，双方各自复扫一致）。
4. 两份 DRAFT 契约稿定义了互斥的传输链，**均未 ack**（DSH Reconciliation B1 问题 4）。
5. producer 侧不存在可承载 IR-required 清单的运行面输出（五输出面合取约束，G-1）；identity 面 87/79 分裂使任何裁决的覆盖面以 **87 份 v2** 为上限。
6. V3 侧若走 IR 载体，涉及的是**新增消费能力**（当前不存在）；若走 manifest 载体，涉及的是 required 清单归属调整。**两者都是裁决后果，本文件不预判。**

### B2（hash 口径）—— V3 侧事实

1. V3 现有 hash 家族四个值（`file_sha` / `body_hash` / `line_hash` / `integrity_hash`）**全部为 V3 内部字段**，producer 不产出对应物（0 命中，DSH 亲验 + 我方 Grep 确认）。
2. 跨系统对账当前**无任何可用字段**：`source_sha256` 在 V3 消费路径上无载体（G-1）；V3 自算值算法与 producer 定义不同（`hashing.py:60-62` / `source_loader.py:27,43-46`）。
3. producer 侧 `source_sha256` 输入口径 = 原始文件字节（DSH Reconciliation B1 问题 1，VERIFIED）——handoff 007 B2 的确认请求**已获答复**。
4. 行号勘误已确认（§0 E-2），漂移结论不变。

### B3（unit_type）—— V3 侧事实

1. 事实形态已更正为 §0 的两层矛盾 + candidate 零落库 + 静默失败掩盖。
2. DSH 已撤回 DQE §1-A「已生效」与 Closure Plan §2「fail-closed 生效中」陈述，**跨仓争议已消解**，双方对「隔离未实现」一致。
3. 噪声是类级现象（第 2 例 `explanation_lines_note` 已出现），producer 链零值域守卫——loss 面当前恰 1 单元，但机制性风险与损失面规模无关。
4. 隔离执行面仍依赖 B1（载体未定则无统一执行层）。
5. 披露 vs 清洁路线（Closure Plan §5-1）**不能替代**执行面裁定——修复数据不改变 V3 零隔离的现状。

---

## 4. 边界声明

**本文件做了**：V3 消费管线五层现状（每层标 V3自有 / Contract声明）；字段来源逐个分类；五类 Gap 登记（G-1~G-5）；对既有 V3 文档两处错误的更正（§0，亲验确认，权威落点）；三项 blocker 的 V3 侧事实输入；producer 侧新事实并入（identity 87/79、五输出面合取约束、hash 零产出、norm_sha256 内部定义、噪声类级现象、Owner 暂停令）。

**本文件没做（任务禁止项）**：未提出实现方案（G-4/G-5 仅登记，B1/B2/B3 仅列事实不预判）；**未修改 EB-008**（L4 仅描述现状，其状态不变）；未冻结 contract；未修改 V3/preprocessing 任何代码或数据。

**与 BLOCKER-ANALYSIS 的关系**：BLOCKER-ANALYSIS §CB-3 早期版本含已被更正的 candidate 层推断（E-1）——**该文件已同批更正**，两文件事实形态现已一致。本文件 §0 保留错误→更正的对照记录，作为该更正的权威落点；BLOCKER-ANALYSIS 的 CB-1/CB-2 事实、裁决问题、依赖关系持续有效，其 producer 侧输入已并入 INTERFACE FACTS v1 新事实。

---

*CONSUMER-GAP-MAP — 2026-09-16，Claude（AITutors-v3 Consumer Owner）。V3 代码基线 `b5ddbe3` · preprocessing `746e35c`（Interface Facts v1 @ `17c55d8` / Reconciliation v0.2 @ `ad1abdd`）· 契约 `1fbaf5e`（未改）。非契约 / 非冻结 / 无实现方案。*
