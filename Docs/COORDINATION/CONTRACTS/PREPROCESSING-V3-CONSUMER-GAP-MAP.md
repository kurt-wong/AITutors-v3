# PREPROCESSING-V3-CONSUMER-GAP-MAP

> **角色**：Claude = **V3 Consumer Owner**（陈述 V3 自身消费面事实）。**不是** preprocessing 审查者。
> **性质**：V3 侧事实地图。**非契约 · 非冻结文档 · 不提出实现方案**。
> **目的**：为 Owner 裁决 B1/B2/B3 提供 V3 侧事实输入。
> **遵守**：未修改 EB-008 · 未冻结 contract · 未修改 V3/preprocessing 代码 · 未提实现方案。
>
> **2026-09-16 更新**：Owner 已下达 B1/B2/B3 **架构裁决**（`DECISION`，见 `PREPROCESSING-V3-DECISION-ALIGNMENT-REPORT.md` §0）。本文件的 Gap 登记随之更新：三项 blocker 的**架构方向已定，实现均未开始**（`IMPLEMENTATION: not started`）。**DECISION ≠ IMPLEMENTATION**——本文件仍只登记事实与缺口，不提案实现。
>
> **2026-09-16 第二轮更新（FINALIZATION v1 四项裁决后）**：Owner 追加裁决 Interface Scope（=87）/ Legacy v1（historical asset）/ 四状态机（READY·INCOMPLETE·PENDING_REVIEW·REJECTED）/ 五步执行序。V3 侧对齐报告 = `PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v1.md`（同批）。本文件据此新增 §0 E-3 精度更正与 G-6~G-9 四项 Gap，并更新 §3 裁决事实输入。**DECISION ≠ IMPLEMENTATION 不变。**
>
> **2026-09-16 第三轮更新（Interface Decision Finalization v1 后，ODR v1.3 §1quater）**：Owner 追加 Part 1–6 + 最终原则。V3 侧对齐 = `PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v2.md`（取代 v1）。关闭 OQ-5（不合并）+ OQ-14（正常态），新增 G-10~G-12。**DECISION ≠ IMPLEMENTATION 不变。**
>
> **2026-09-16 第四轮更新（Interface Finalization Revision v1 后，ODR v1.4 §1quinquies）**：Owner 修正/固化——source identity 64 hex + **path 非身份原则**（belongs to content hash, not storage location）· 16 份改 **Semantic Pending（可恢复）**· 语义层终局词表加 **`unknown`**（`{ready,incomplete,unknown}`）· **unknown → reviewable record → pending_review**。V3 侧对齐 = `PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v3.md`（取代 v2）。**关闭 OQ-8 格式 / OQ-12 身份维度 / OQ-19 路由 / OQ-20 值集**；16 份由 Unavailable 改 Pending。**DECISION ≠ IMPLEMENTATION 不变。**
>
> **证据基线**：
> | 侧 | 基线 |
> |---|---|
> | V3 代码 | `b5ddbe3`（其后仅文档提交，代码未变） |
> | preprocessing | `1657625`（Producer Alignment v4 入册）+ 未提交工作树（ODR **v1.4** §1quinquies / **Producer Alignment v5** / Interface Facts v2.1） |
> | 被分析契约 | v0.1 @ `1fbaf5e`（未改）；v0.2 DRAFT 见 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`（**Frozen Candidate**，DRAFT / NOT FROZEN，冻结范围 = 五项原则） |
>
> **本轮关键输入**：Owner Decision Record v1.2（§1 + §1bis DEC-B1 + §1ter 四项裁决）；DSH `PREPROCESSING-PRODUCER-DECISION-ALIGNMENT-v1.md`（并行产出）；DSH Readiness v3（三点交集定量、87/87 R50 成员资格）；V3 侧 Consumer Decision Alignment v1。前轮输入（IF-v2 / Reconciliation v0.2 / Owner B1-B3 裁决 / 暂停令 `746e35c`）继续有效。

---

## 0. 对既有 V3 文档的更正（亲验后确认）

DSH Reconciliation v0.2 指出我方 BLOCKER-ANALYSIS / Review v0.2 的两处错误。**我逐行复核，确认更正成立**，据实修正：

| # | 我方原结论 | 更正后事实 | 我的亲验 |
|---|---|---|---|
| **E-1** | CB-3：candidate 层落 `composite_unit`，「三处解释互相矛盾」 | candidate 层**零落库**——该单元 `semantic_status=incomplete` → `runner_b2.py:232-239` skip+continue，**永不到达** `:252`。即便到达，IRBuilder 从**洗白后** payload 取值（`ir.py:108`）会落 `standalone_unit`，非 `composite_unit` | ✅ 成立：`runner_b2.py:231-252`；`ir.py:106-108`；`annotation_adapter.py:42` |
| **E-2** | Review §A.3：`splitlines()` 规范化在 `compute_body_hash`（`source_loader.py:43-46`） | `splitlines()` 在 `load_source_lines`（`source_loader.py:27`）；`compute_body_hash` 本身只做 `"\n".join` + sha256。**6/12 DIFFER 结论不变** | ✅ 成立：`source_loader.py:24-46` |
| **E-3** | 本文件旧 §2.2 G-1 / §3 与 BLOCKER-ANALYSIS：「79 份 v1 在 C-IN-1 下必被拒收」 | **精度修正（本轮，非结论反转）**：C-IN-1 在 **producer/IR 面已实现**（`resolver_reference.py` 生成时拒收）；在 **V3 消费面未实现**——`identity_version` 与 `C-IN-1` 在 V3 全仓代码 **0 命中**。若 v1 manifest 被送入 V3，V3 **会照常消费** | ✅ 成立：`Grep identity_version\|C-IN-1 @ backend/**/*.py` = 0；`manifest_reader.py:28-35` dataclass 无该字段；producer 侧见 IF-v2 §2.4 |

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

**G-1 · 载体 Gap（对应 B1）— 架构已裁决，实现未开始**

> **DECISION（2026-09-16）**：Manifest + IR 双层接口；Manifest = Source Identity Authority，IR = Semantic Consumption Authority；经 `source_version_id` 关联。

V3 读 manifest，契约 required 清单按 IR 写。manifest 层 **0/166** 带 sha（DQE §4 + INTERFACE FACTS v1 §1 复扫一致）。故契约 §3.1 的 `source_sha256` required 承诺**在 V3 消费路径上无数据载体**。

DSH Reconciliation v0.2 B1 问题 4 补充事实：**不存在任何双方 ack 的传输链定义**——两份 DRAFT 互斥（preprocessing 契约 §2 写 `IR → V3`；V3 侧需求稿写 `manifest → V3`），且**无文档定义 `IR → manifest → V3`**（producer 链方向是 manifest → resolver → IR，IR 不回流 manifest）。**该互斥由 DECISION 的双层架构取代。**

INTERFACE FACTS v1 §0 核心合取事实（生产侧硬约束）：**没有任何单一输出面同时具备「全语料覆盖 + md sha 锚 + 持续产出」**——manifest 全覆盖但零 sha；IR 有 sha 但只是 88 条一次性冻结样本工件（71 条 ADMITTED 携 `ir` 对象）；OCR 清单锚 PDF 非 md。

**identity 面分裂（覆盖上限事实，已由 DEC-023 升格为接口面裁决）**：166 份 manifest 中 identity v2 = **87 份** / v1 legacy = **79 份**。**Interface Scope = 87（字段口径）**（DEC-023 ≡ DSH DEC-021-1）。79 份 v1 的处置已由 **DEC-024 裁定 = historical asset 隔离，四禁，迁移走独立 Legacy Migration Plan**——不再是独立事实问题。**但隔离的 V3 侧执行面 = 0**（§0 E-3）。

**实现缺口**（`IMPLEMENTATION: not started`）：B1-G1 Manifest 无 `source_version_id` 载体 · B1-G2 关联字段定义项 · B1-G3 V3 零 IR 消费能力 · B1-G4 V3 内部 UUID ≠ 跨系统键且 consumer 写入 canonical_json 包裹值。详见 Alignment Report §1.3。

**G-2 · hash 口径 Gap（对应 B2）— 架构已裁决，实现未开始**

> **DECISION（2026-09-16）**：唯一 source identity = `SHA-256(raw bytes)`；canonical_json hash / body_hash / line_hash / integrity_hash 只能作内部校验，不得替代 source identity。

- 跨系统锚 `source_sha256`：producer = 原始文件字节 SHA-256（`resolver_reference.py:52-53,249`，DSH Reconciliation B1-Q1 VERIFIED）——**与 DECISION 口径一致**；V3 自算两路均对不上（canonical_json 引号 / splitlines 规范化）。
- `body_hash` / `line_hash`：**producer 不产出**（INTERFACE FACTS v1 §2 穷举复证，全仓 grep = 0），「算法是否一致」在跨系统层面**无对象可比**——它们是 V3 内部字段，不是跨系统字段。**DECISION 将其正式限定为内部校验用途（与现状不冲突）。**
- producer 侧 `norm_sha256` 归一化算法已在仓内定义（r64 NORM_ALGO：NFC + CRLF/CR→LF + per-line rstrip + whole strip），但**从未作为接口发布**——DECISION 未涉及该 hash，`UNKNOWN`。
- 真实断点是复合的：G-1（锚在 V3 消费路径上无载体）+ 本项（V3 自算值算法与 producer 定义不同）。**两项独立成立；DECISION 统一了口径定义，载体与写入实现仍未开始。**

**实现缺口**（`IMPLEMENTATION: not started`）：B2-G1 consumer 写入 `documents.original_sha256` 为 canonical_json 包裹值，不符 raw bytes 定义 · B2-G3 对账闸门依赖载体（B1）。详见 Alignment Report §2.3。

**G-3 · 值域语义 Gap（对应 CB-3）— 架构已裁决，实现未开始**

> **DECISION（2026-09-16）**：unknown `unit_type` 不得自动转换 / 不得静默 fallback / 不得进入 Question materialization；处理方式 UNKNOWN/PENDING。

- 契约 §3.3-6 要求非闭集值隔离 → **未实现**；DECISION 升格为四条禁令。
- 实际终态 = 无信号 incomplete → skip，真实原因不可见（§0 E-1）——**违反 DECISION 的「不得自动转换」「不得静默 fallback」**；「不得进入 Question materialization」经静默路径达成（结果符合、路径不符合）。
- DSH 已撤回「已生效」陈述，**双方事实已对齐**。
- **噪声是类级现象，不是单点**（INTERFACE FACTS v1 §1）：恰 1 例 `andalone_question` 之外，另有第 2 例 schema 噪声 = 游离键 `explanation_lines_note`（value = null；batch-C unit Q24）。producer 链零值域守卫（`write_outputs` 原样落盘 → `resolver_reference.py:152` 逐字复制）——生产侧今天没有任何一层检查 `unit_type`。

**实现缺口**（`IMPLEMENTATION: not started`）：B3-G1 当前静默路径不满足 UNKNOWN/PENDING · B3-G2 落层设计 `UNKNOWN`（SEMANTIC_STATUS 冻结值域 `{ready,incomplete}` 无 pending 取值；pending_review 仅 ready 可达）。详见 Alignment Report §3.3-3.4。

**G-4 · V3 内部一致性 Gap（新登记，非 blocker）**

`line_hash` 同表两算法并存、`integrity_hash` consumer 路径退化。**属 V3 内部治理**，DSH 明确不在处置范围，**不阻塞契约冻结**——但登记在案：consumer 路径写入的数据与生产路径写入的数据在同两张表内语义不同。DSH 标 UNKNOWN 是否有意允许共存；本文件同样不提案，仅登记事实。

**G-5 · 消费范围 Gap（非 blocker）**

契约 §3.1 required 清单中，V3 零消费的字段见 §2.1 末行。这些字段是 producer 自证层，V3 重新推导（行/hash 见 L5）。**不影响冻结**，但 v0.2 措辞应如实标注 V3 当前消费范围。

**G-6 · 接口面识别 Gap（对应 DEC-023）— 架构已裁决，实现未开始**

> **DECISION（DEC-023 ≡ DSH DEC-021-1）**：Interface Scope = 87（字段口径）；IR 当前冻结面 = 71 ADMITTED。

V3 **无「接口面」概念**：`identity_version` 在 V3 全仓代码 **0 命中**（§0 E-3 同批实测）；`Manifest` dataclass 无该字段（`manifest_reader.py:28-35`）。V3 读到什么 manifest 就消费什么，**无法区分 87 与 79**。生产侧同样无文件级接口面清单工件（DSH §A.3/C.1）。

**实现缺口**（`IMPLEMENTATION: not started`）：D1-G1 生产侧承载物 · D1-G2 V3 侧识别与过滤能力。详见 Consumer Alignment v1 §4.1。

**G-7 · Legacy 隔离执行面 Gap（对应 DEC-024）— 架构已裁决，V3 侧零执行面**

> **DECISION（DEC-024 ≡ DSH DEC-021-2）**：v1 legacy 79 = historical asset，不入 v0.2 接口；四禁；迁移走独立 Legacy Migration Plan。

producer 侧 C-IN-1 **已实现**（IR 生成拒收）；**V3 侧 `identity_version` / `C-IN-1` 均 0 命中**——隔离由生产侧单边执行。若 v1 manifest 被送入 V3，V3 会照常消费（D2-G1）。

**实现缺口**（`IMPLEMENTATION: not started` / 部分 `UNKNOWN`）：V3 消费侧 identity 闸门是否需要 = **UNKNOWN**（Owner 未下达 V3 实现设计）；legacy 披露形态 = OQ-15。

**G-8 · 四状态机表达 Gap（对应 DEC-025）— 词表已裁，层归属未裁，实现未开始**

> **DECISION（DEC-025 ≡ DSH DEC-021-3）**：READY / INCOMPLETE / PENDING_REVIEW / REJECTED 四值；三禁令（禁 auto conversion / silent fallback / silent skip）；unknown semantic 强制路由进 PENDING_REVIEW 或 REJECTED。

**V3 侧结构发现（本轮）**：四个词分布在**两个互相正交、各自冻结**的值域里——READY/INCOMPLETE ∈ `SEMANTIC_STATUS`（`compile/__init__.py:28-29`，BUG-V3-018）；PENDING_REVIEW/REJECTED ∈ `DECISION_STATUS`（`gate/__init__.py:10-11`，10 §5.2）。且 `decision_status` 只存在于 candidate，candidate 只由 **ready 单元**产生（`runner_b2.py:231-264`）——**非 ready 单元永远进不了 PENDING_REVIEW / REJECTED**。

**后果**：裁决点名的四个状态个体都能表达，但**对 unknown semantic 单元不可联合可达**。三条禁令在 V3 全部违反（洗白 / composite fallback / 静默 skip，同一条链的三个切面）。

**实现缺口**（`IMPLEMENTATION: not started`）：D3-G1 三禁令零执行面 · D3-G2 可达通道不存在。**层归属已裁（DEC-027 Part 5）= 不合并两状态体系，UNKNOWN 属语义层**（OQ-5 关闭）；由此细化：语义层加 `unknown` 取值须解冻 BUG-V3-018（**OQ-20**）· unknown→PENDING_REVIEW 不可达（**OQ-19**）· 路由规则文本 = **UNKNOWN**（OQ-16）。

**G-9 · 语义覆盖悬崖（对应 DEC-023 副产物）— 新登记，须 v0.2 落字**

接口面 87 中有 **16 份**（87−71）**无 IR 语义承载**。双层裁决把语义消费从 manifest（87+ 面）移到 IR（71）——这 16 份在身份面内但**失去语义可消费性**。V3 今天**能**通过 manifest 消费它们的语义；双层落地后不能，除非 ① IR 扩产（未裁未排期）② 明确声明其语义面外地位 ③ 其他（本文件不预设）。

DSH 从生产侧记为 D.2；本文件从 V3 消费侧登记。~~**OQ-14**~~ → 先裁（DEC-027 Part 4）正常态，**本轮改（DEC-028 Part 3）= Identity Available / Semantic Pending（可恢复）**，允许重生成 IR 四约束。V3 侧仍缺身份/语义分离消费能力 + pending 标记（见 G-11）。

**G-10 · `source_version_id` 同名异义 Gap（本轮新登记，协调层）**

契约的 `source_version_id`（sha256 hex，`SHA256(raw bytes)`）与 V3 代码到处出现的 `source_version_id`（`uuid.UUID`，`document_source_versions` 行主键 FK）**同名、异义、异类型**。证据：`models/source.py:44-57`（`:50` 明令禁用 sha 作 Seal 唯一）· `snapshot_repository.py:42-45` `session.get(DocumentSourceVersion, source_version_id)` · `runner_b2.py:158` `create_source_version(...).id`。当 manifest 未来补 sha256-hex 形态的 `source_version_id`，V3 schema 已有同名 UUID 列，命名/类型冲突。契约措辞须消歧 → **OQ-20**。

**G-11 · Part 2 V3 六项消费义务 Gap（本轮新登记）**

Owner（DEC-027 Part 2）固化：V3 = 验证 Manifest / 重算 hash / 判断接受 + 验证 IR / Gate / 拒收。**六项全部未实现**——无校验（`manifest_reader.py:52`）、不读 producer sha（自算 canonical_json 包裹非 raw bytes，`runner.py:71-73`）、无身份闸门（`identity_version` 0 命中）、零 IR 消费能力。对应 Consumer Alignment v2 的 **V3-G1 / V3-G2**。可执行前提 = source bytes 对 V3 可达（OQ-12 / DSH G-4）。

**G-12 · 语义层 unknown 取值 + 决策可达性 Gap（OQ-5 细化；本轮值集与路由已裁，实现 not started）**

DEC-027 Part 5 裁不合并 + UNKNOWN 属语义层；**DEC-028 Part 5 裁终局词表 `{ready,incomplete,unknown}`（OQ-20 值集关闭）+ Part 6 裁 unknown → reviewable record → pending_review（OQ-19 路由关闭）**。V3 侧两项实现缺口：(a) `SEMANTIC_STATUS` 冻结 `{ready,incomplete}`（`compile/__init__.py:28-29`，BUG-V3-018），加 `unknown` 须**解冻**——值集已裁，实现 not started；(b) candidate 仅由 ready 产生（`runner_b2.py:231-264`），语义 `unknown` 单元在现架构下进不了 pending_review——「产生 reviewable record 进 pending_review workflow」机制 not started。`reviewable record` 载体形态 = UNKNOWN（OQ-16′）。

**G-13 · path 非身份原则核验（DEC-028 Part 1/2，本轮）**

固化原则 **Source identity belongs to content hash, not storage location**；`source_file`/path = locator only，任何文档不得暗示 path 参与身份/版本/hash 判断。**V3 现状符合**——仅将 `source_file` 用作 `Path(manifest.source_file)` 加载源文件（`runner.py:241`；`runner_b2.py:320`；`runner_b3.py:184`），全仓无任何以 path 做身份/版本/hash 判断的代码。**跨系统双层当前靠 path 值相等关联 = 不合规现状**（正是本原则要消除的）；升级为 `source_version_id` 关联 = not started（G-1/G-11）。残余未裁 = source bytes 如何交付给 V3 重算 hash（OQ-12′，传输方式非 path 形态）。

---

## 3. 供 Owner 裁决的 V3 侧事实输入

> **状态更新（2026-09-16）**：Owner 已下达 B1/B2/B3 架构裁决（`DECISION`，Alignment Report §0）。以下事实输入仍有效——它们是 DECISION 的对账基线；实现缺口见各 G 项与 Alignment Report §1.3/§2.3/§3.3。**架构已定 ≠ 实现已发生。**
>
> **状态更新（2026-09-16 第二轮）**：Owner 追加 FINALIZATION v1 四项裁决（DEC-023~026 ≡ DSH DEC-021-1~4）。V3 侧对齐全文见 `PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v1.md`。新增 Gap G-6~G-9 见 §2.2。以下 B1/B2/B3 分项事实输入继续有效。
>
> **状态更新（2026-09-16 第三轮）**：Owner 追加 Interface Decision Finalization v1（V3 `DEC-027` ≡ DSH `DEC-022`，Part 1–6）。V3 侧对齐全文见 `PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v2.md`（取代 v1）。新增 Gap G-10~G-12 见 §2.2；关闭 OQ-5 + OQ-14。
>
> **状态更新（2026-09-16 第四轮）**：Owner 追加 Interface Finalization Revision v1（V3 `DEC-028` ≡ DSH `DEC-023`，Part 1–6）。V3 侧对齐全文见 `PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v3.md`（取代 v2）。新增 Gap G-13；关闭 OQ-8 格式 / OQ-12 身份维度 / OQ-19 路由 / OQ-20 值集；16 份 Unavailable→Pending。

### Interface Finalization Revision v1 — V3 侧事实输入（一句话版，DEC-028 ≡ DSH DEC-023）

| 裁决 | V3 侧核心事实 | Gap |
|---|---|---|
| **Part 1** source identity 64 hex + content-hash-not-location | producer 算法在库；V3 自算 canonical_json 非 raw bytes；零身份校验 | G-1/G-2 |
| **Part 1/2** path = locator 非身份 | V3 仅用 path 作 locator（**符合**）；跨系统靠 path 关联（不合规） | G-13（OQ-12′ bytes 交付） |
| **Part 3** 16 份 = Semantic Pending（可恢复） | 改前轮 Unavailable；允许重生成 IR 四约束；V3 无分离/标记能力 | G-9/G-11（OQ-21 呈现） |
| **Part 4** Scope 保持 87（禁 IR=Interface） | V3 无法识别接口面、IR 零消费 | G-6 |
| **Part 5** 语义层终局词表加 `unknown` | V3 `SEMANTIC_STATUS` 冻结 2 值，须解冻加值 | G-12（OQ-20 值集已裁） |
| **Part 6** unknown → reviewable record → pending_review | V3 candidate-gated-on-ready，无执行面 | G-12（OQ-19 路由已裁） |

### Interface Decision Finalization v1 — V3 侧事实输入（一句话版，DEC-027 ≡ DSH DEC-022）

| 裁决 | V3 侧核心事实 | Gap |
|---|---|---|
| **Part 1** 双层职责 + 双禁 | V3 用身份层做语义消费、且无身份锚（两半边都不符） | G-1/G-2 |
| **Part 2** V3 六项消费义务 | 验证/重算/接受 + 验证 IR/Gate/拒收 —— **六项全未实现** | G-11 |
| **Part 3** Scope 三禁 | V3 无法识别接口面、IR 零消费 | G-6 |
| **Part 4** 16 份 Identity-only 正常态 | **关闭 OQ-14**；V3 无身份/语义分离消费能力 | G-9/G-11 |
| **Part 5** UNKNOWN 属语义层、不合并 | **关闭 OQ-5**；语义层缺 `unknown` 取值 + 非 ready 不可达决策层 | G-12（OQ-19/20） |
| **Part 6** v0.2 只冻结三件 | Identity/Scope/Semantic Boundary；六类暂缓 | 契约 §0 |

另：`source_version_id` **同名异义**（sha256 hex vs V3 UUID）→ **G-10 / OQ-20**。

### FINALIZATION 四项裁决 — V3 侧事实输入（一句话版）

| 裁决 | V3 侧核心事实 | Gap |
|---|---|---|
| **DEC-023** Interface Scope = 87 / IR 冻结面 71 | V3 `identity_version` 代码 0 命中，**无法识别接口面**；生产侧也无清单工件 | G-6 |
| **DEC-024** Legacy 79 = historical asset | producer C-IN-1 已实现；**V3 侧零执行面**，v1 被送入会照常消费 | G-7 |
| **DEC-025** 四状态机 | 四词分属**两个正交冻结层**，非 ready 单元**不可达** PENDING_REVIEW/REJECTED；三禁令全部违反 | G-8 |
| **DEC-026** 五步执行序 | 五步全是数据/契约动作，**零 V3 实现动作**——V3 实现排期无对应步骤，= UNKNOWN | §5.5 / Consumer Alignment §4.4 |

另：接口面 87 中 **16 份无 IR 语义承载** → 语义覆盖悬崖（**G-9 / OQ-14**）。

### B1（传输层）—— V3 侧事实

1. V3 当前**唯一**消费载体 = manifest（L1 全部证据）。
2. V3 **零** IR 消费代码，**无** IR loader 排期记录。
3. manifest 层无 sha（0/166，双方各自复扫一致）。
4. 两份 DRAFT 契约稿定义了互斥的传输链，**均未 ack**（DSH Reconciliation B1 问题 4）——**由 DECISION 双层架构取代**。
5. producer 侧不存在可承载 IR-required 清单的运行面输出（五输出面合取约束，G-1）；identity 面 87/79 分裂使任何裁决的覆盖面以 **87 份 v2** 为上限。
6. V3 侧若走 IR 载体，涉及的是**新增消费能力**（当前不存在）；若走 manifest 载体，涉及的是 required 清单归属调整。**DECISION = 双层并行，两者都涉及；实现排期 UNKNOWN。**

### B2（hash 口径）—— V3 侧事实

1. V3 现有 hash 家族四个值（`file_sha` / `body_hash` / `line_hash` / `integrity_hash`）**全部为 V3 内部字段**，producer 不产出对应物（0 命中，DSH 亲验 + 我方 Grep 确认）——**DECISION 已将其正式限定为内部校验**。
2. 跨系统对账当前**无任何可用字段**：`source_sha256` 在 V3 消费路径上无载体（G-1）；V3 自算值算法与 producer 定义不同（`hashing.py:60-62` / `source_loader.py:27,43-46`）。
3. producer 侧 `source_sha256` 输入口径 = 原始文件字节（DSH Reconciliation B1 问题 1，VERIFIED）——**与 DECISION 口径一致**。
4. 行号勘误已确认（§0 E-2），漂移结论不变。

### B3（unit_type）—— V3 侧事实

1. 事实形态已更正为 §0 的两层矛盾 + candidate 零落库 + 静默失败掩盖。
2. DSH 已撤回 DQE §1-A「已生效」与 Closure Plan §2「fail-closed 生效中」陈述，**跨仓争议已消解**，双方对「隔离未实现」一致。
3. 噪声是类级现象（第 2 例 `explanation_lines_note` 已出现），producer 链零值域守卫——loss 面当前恰 1 单元，但机制性风险与损失面规模无关。
4. 隔离执行面仍依赖 B1（载体未定则无统一执行层）——**DECISION 已定双层架构，执行面落点仍 UNKNOWN（B3-G2）**。
5. 披露 vs 清洁路线（Closure Plan §5-1）**不能替代**执行面裁定——修复数据不改变 V3 零隔离的现状。

---

## 4. 边界声明

**本文件做了**：V3 消费管线五层现状（每层标 V3自有 / Contract声明）；字段来源逐个分类；**十三类 Gap 登记（G-1~G-13）**，其中 G-1/G-2/G-3 并入 B1/B2/B3、G-6~G-9 并入 FINALIZATION 四项、G-10~G-12 并入 Interface Decision Finalization v1、**G-13 并入 Interface Finalization Revision v1（DEC-028）**（均 `DECISION` 采纳、实现未开始或 `UNKNOWN`）；对既有 V3 文档**三处**更正（§0 E-1/E-2/E-3）；三项 blocker + 三轮裁决的 V3 侧事实输入；producer 侧新事实并入。

**本文件没做（任务禁止项）**：未提出实现方案（G-4~G-9 仅登记，缺口仅列不预判形态）；**未把 DECISION 描述为已实现**（全部标 `IMPLEMENTATION: not started` 或 `UNKNOWN`）；**未修改 EB-008**（L4 仅描述现状，其状态不变）；未冻结 contract；未修改 V3/preprocessing 任何代码或数据；未执行任何数据动作。

**与 BLOCKER-ANALYSIS 的关系**：BLOCKER-ANALYSIS §CB-3 早期版本含已被更正的 candidate 层推断（E-1）——**该文件已同批更正**，两文件事实形态现已一致。本文件 §0 保留错误→更正的对照记录，作为该更正的权威落点；BLOCKER-ANALYSIS 的 CB-1/CB-2 事实、裁决问题、依赖关系持续有效，其 producer 侧输入已并入 INTERFACE FACTS v1 新事实；其「待 Owner 裁决问题」中已由 DECISION 回答的部分见该文件状态更新。

**与 v0.2 DRAFT 的关系**：`PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` 是本文件事实基线的契约化产出（冻结候选，NOT FROZEN）。本文件不冻结任何东西。

---

*CONSUMER-GAP-MAP — 2026-09-16（第四轮：Interface Finalization Revision v1 / DEC-028 并入，关闭 OQ-8 格式/OQ-12 身份维度/OQ-19 路由/OQ-20 值集，16 份改 Pending，新增 G-13 path 非身份核验），Claude（AITutors-v3 Consumer Owner）。V3 代码基线 `b5ddbe3` · preprocessing `1657625`（+ DSH 并行未提交工作树：ODR v1.4 / Producer Alignment v5）· v0.1 契约 `1fbaf5e`（未改）· v0.2 DRAFT 另文（**Frozen Candidate**，冻结范围 = 五项原则，DRAFT / NOT FROZEN）。非契约 / 非冻结 / 无实现方案。DECISION ≠ IMPLEMENTATION。*
