# PREPROCESSING Integration Contract v0.2 — Freeze Candidate Review

> **角色**：Claude = **V3 Consumer Owner**（消费侧）。本文件是 **Contract v0.2 冻结候选评审**（Freeze Candidate Review）——把 Owner 已确认的六条原则落成可冻结候选，并解决其中两条本轮新裁项（命名方案 / bytes 交付能力冻结）。
> **性质**：评审报告 + 命名方案提案。**非实现 · 非数据动作 · 契约仍未冻结（DRAFT / NOT FROZEN）**。
> **上游**：`PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`（冻结候选，同批更新）；Consumer Alignment v3 @ `4e0dd34`；Owner Decision Record v1.4 §1quinquies（V3 `DEC-028` ≡ DSH `DEC-023`）；producer 侧 Interface Facts v2.1 + Producer Alignment v5 @ preprocessing `1657625`（+ DSH 并行未提交工作树）。
> **本轮登记**：V3 `DEC-029`（Freeze Candidate Review）。**跨仓**：本轮为 Owner 直接下达的评审令，DSH 侧对应登记待其 Producer Alignment v5 收口。
>
> **证据纪律**：每条款标 `DECISION` / `OBSERVED` / `PROPOSAL` / `REQUIREMENT` / `UNKNOWN`。**DECISION ≠ IMPLEMENTATION**。命名方案标 `PROPOSAL`（待 Owner 采纳 + DSH 双边确认），不是既成裁决。
>
> **⚠️ 后续裁决（DEC-030，2026-09-16 Finalization）**：本报告 §1 的命名提案 **`source_content_sha256` 已被 Owner 采纳**（Decision 1），全文词面收口已在 Contract v0.2 DRAFT 执行；§2 bytes 能力冻结获 Decision 2 确认；§3 状态边界获 Decision 3 确认。本文件保留为 DEC-029 评审轮的历史记录，**其中 PROPOSAL 标注以本条为准转为 DECISION**。
>
> **⚠️ 事实状态更新（DEC-033，2026-09-16 Freeze Finalization Audit）**：本文件表格中的「Step 1 / Step 2 = not started」等执行状态描述为 **DEC-029 评审时点的历史记录**，现已过时——**DSH 已执行 Step 1/2 并验证通过**（DSH `DEC-026`，commit `e70807b`；Freeze Evidence = `aad2237` C1-C9 VERIFIED；Producer 确认 = `67f564c` ALL PASS）。现行事实状态以 Contract v0.2 DRAFT §8/§9 为准（**READY FOR FREEZE / NOT FROZEN**；五项 V3 能力仍 NOT IMPLEMENTED）。本文件不改写历史表格，仅加本注记。

---

## §0 Owner 已确认原则（本轮输入，verbatim 要点）

Owner 下达六条确认原则，进入 Contract v0.2 Freeze Candidate Review：

1. **source identity**：`source_version_id = SHA256(raw bytes)`；`path(source_file)` 仅作 locator，**禁止参与 identity 判断**。
2. **双层权威**：Manifest = Source Identity Authority；IR = Semantic Consumption Authority；V3 消费语义来自 IR，但**身份验证独立于 IR**。
3. **16 份文件**：状态 = Identity Available + Semantic Pending；允许重新生成 IR；必须保证——source bytes hash 不变 / source identity 不变 / IR 版本可追踪 / 禁止覆盖历史事实。
4. **状态体系**：Semantic `ready/incomplete/unknown`；Decision `pending_review/approved/rejected`；**禁止合并**。
5. **`source_version_id` 命名问题**：提出最终命名方案，避免 Producer hash identity 与 V3 UUID FK 同名。
6. **source bytes 交付**：只冻结能力要求——**V3 必须能获得 raw bytes 并验证 hash**；**不冻结具体传输方案**。

**输出要求**：A. Contract v0.2 Freeze Candidate · B. 剩余未决问题列表 · C. Implementation Gap · D. 禁止修改任何代码和数据。

---

## §1 命名方案（原则 5 —— 本轮核心提案，`PROPOSAL`）

> 关闭残余 **OQ-8′**（`source_version_id` 同名异义：契约 sha 键 vs V3 内部 UUID FK 共用一名）。这是本轮唯一需要 Owner 采纳的实质决策。

### 1.1 冲突事实（`OBSERVED`，FACT-041 / GAP-MAP G-10）

| 概念 | 当前名 | 类型 | 语义 | 证据 |
|---|---|---|---|---|
| **契约/接口 `source_version_id`** | `source_version_id` | sha256 hex（64 小写） | `SHA256(raw bytes)` 跨系统身份键，id 即 sha 值 | 契约 §1.2；IR `ir.source_sha256` 71/71 同值 |
| **V3 内部 `source_version_id`** | `source_version_id` | `uuid.UUID` | `document_source_versions` 行主键 FK；Seal 层唯一性锚 `(logical_execution_stage, logical_execution_hash)`，**明令禁用 sha 作唯一**（`source.py:50`） | `models/source.py:44-57`；`snapshot_repository.py:42-45`；`runner_b2.py:158` |
| **V3 `Document.original_sha256`** | `original_sha256` | `String(64)` UNIQUE | BUG-V3-007 文档身份；概念对应「源内容 hash」，但当前写入 canonical_json 包裹 joined-text 非 raw bytes | `models/source.py:33,37`；`runner.py:71-73`；`hashing.py:60-62` |

**危险性**：契约 sha 键与 V3 代码到处出现的 UUID FK **同名、异义、异类型**。当 manifest 未来补上 sha256-hex 形态的身份键，V3 schema 已有同名 UUID 列——命名/类型直接冲突；且比 DEC 号撞号更危险，因为容易被误读为「V3 已经有 `source_version_id` 了」。

### 1.2 命名方案（`PROPOSAL`，待 Owner 采纳 + DSH 双边确认）

**核心思路**：V3 内部 UUID FK 是**代码列名**，本轮禁止改代码/改 schema，故不动它；**把跨系统接口键改名**，使其与 V3 内部列**词面永不同名**。接口键是契约词，改它 = 零代码 / 零数据 / 零 schema，纯契约措辞动作——最轻、最安全、且唯一能在不动 V3 代码的前提下消除冲突的路径。

**建议接口键名 = `source_content_sha256`**（跨系统唯一身份键 = `SHA256(source raw bytes)`，64 小写 hex）。

| 概念 | 旧名（冲突态） | **建议名** | 类型 | 跨接口？ | 说明 |
|---|---|---|---|---|---|
| **跨系统 source 内容身份键（接口键）** | `source_version_id`（契约/接口义） | **`source_content_sha256`** | 64 小写 hex sha256 | **是** | 唯一跨系统身份键 = `SHA256(raw bytes)`；身份由其唯一决定 |
| V3 内部 seal 版本 FK | `source_version_id`（V3 代码） | **不变** `source_version_id` | `uuid.UUID` | 否 | 指 `document_source_versions` 行；永不跨接口；契约引用时须显式标「V3 内部」 |
| V3 内部内容 hash 列 | `original_sha256` | **不变** `original_sha256` | `String(64)` UNIQUE | 否 | V3 侧将来存放 `source_content_sha256` 的列；当前值为 canonical_json 包裹（V3 实现缺口，非命名问题） |
| producer IR 文件级 sha | `source_sha256` | **不变**（producer 域） | sha256 hex | 映射 | 与接口键**同值**（md raw bytes）；字段名 producer 自定，本契约不改 producer 实现 |
| producer IR 单元级 provenance | `provenance.source_version` | **不变**（producer 域） | sha256 hex | 映射 | 与接口键**同值** |

### 1.3 选 `source_content_sha256` 的理由（`PROPOSAL`）

1. **类型自证**：名字带 `sha256`，读者不可能把它误读为 UUID FK——冲突在词面即被消除。
2. **语义自证**：`content` 直接呼应冻结原则「Source identity belongs to **content** hash, not storage location」，强化 path 非身份。
3. **字面即定义**：取值就是 `SHA256(source raw bytes)`，名实相符。
4. **零数据 / 零 schema 改动**：纯契约措辞；不动 V3 代码列、不动 producer 字段、不动任何库表。
5. **与 producer 现有字段干净映射**：producer IR 的 `source_sha256` / `provenance.source_version` 与接口键同值，仅需一条映射注记，producer 侧无需改名。

**备选（供 Owner 参考，按优先级降序）**：
- `source_bytes_sha256` —— 同样成立；`bytes` vs `content` 只是措辞细微差，`content` 与冻结原则「content hash, not location」配对更好。
- `source_sha256` —— 与 producer IR 现有文件级字段同名，但**不推荐**：md 面 / PDF 面（OCR 清单钉 PDF 字节，OQ-10）两语料同名易混，且不自证「content 非 location」。

### 1.4 采纳后的动作（`REQUIREMENT`，本轮不执行）

- Owner 采纳 `source_content_sha256` → 契约全文接口键做一次干净词面替换（把仍以接口义出现的 `source_version_id` 统一改为 `source_content_sha256`；`source_version_id` 仅保留在「V3 内部 FK」语境）。
- DSH 双边确认接口键名（跨系统契约词，须两侧一致）。
- **本轮（评审）不做全文替换**——命名是提案，未采纳前全文改名属越权；本文件 + 契约以「提案 + 解释条款」落字，采纳后一次性词面收口。

---

## §2 source bytes 交付 —— 只冻能力，不冻传输（原则 6，`DECISION` + `REQUIREMENT`）

> 关闭残余 **OQ-12′**（source bytes 如何交付给 V3 重算 hash）。Owner 裁定：**只冻结能力要求，不冻结具体传输方案。**

### 2.1 冻结的能力要求（`REQUIREMENT`，binding）

**V3 必须能够获得每份 source 的 raw bytes，并能重算 `source_content_sha256` 与声明值比对验证身份。** 具体：

1. **可获得 raw bytes**：对 Interface Scope 内每份 source，V3 有办法取得其原始字节（不是 canonical_json 包裹、不是 splitlines 规范化后的文本）。
2. **可重算并验证**：V3 用标准库对 raw bytes 独立重算 `SHA-256`，与 producer 声明的 `source_content_sha256` 比对。
3. **fail-closed**：无法获得 bytes，或重算值 ≠ 声明值 → **阻断消费（拒收）**，不得静默放行（继承 v0.1 §3.3-3 / 契约 §2.3）。
4. **独立于 IR**：身份验证不以 IR 存在为前提（原则 2 / DEC-B1；身份对账面在 Manifest）。

### 2.2 不冻结 / 暂缓的传输方案（`UNKNOWN`，明确不属于 v0.2 承诺）

**HOW** bytes 达到 V3 —— 共享文件系统 / 对象存储 / IR 内嵌 / manifest 相对路径解析 / 其它 —— **属暂缓项**，v0.2 不冻结。理由：传输是实现/部署形态，随环境（Windows / NAS / Linux / Object Storage）变化，冻结它会把部署细节锁进接口契约。当前 `source_file` 为本机绝对路径、跨机不可解析（IF-v2 §2.1；`OBSERVED`），正说明传输形态未定——但这**不阻塞**能力冻结：能力是「必须能拿到 bytes 并验证」，与「怎么拿」解耦。

### 2.3 对 OQ-12′ 的处置

- **能力维度 = 已冻结**（本节 2.1），进 v0.2 承诺面。
- **传输维度 = 暂缓**（本节 2.2），不进 v0.2 承诺面，不构成冻结阻塞。
- 净效果：OQ-12′ 从「开放项」变为「能力已冻 / 传输暂缓」——**不再是冻结前提**。

---

## §3 六条原则 → 候选版符合性核验（A 的核验面）

> 逐条核验 Contract v0.2 候选是否已承载 Owner 六条原则。原则 1–4 前轮已入册；原则 5 = 本轮提案；原则 6 = 本轮冻结。

| # | Owner 原则 | 候选版落点 | 状态 |
|---|---|---|---|
| 1 | source identity = `SHA256(raw bytes)`；path 仅 locator，禁参与 identity | §1.2（64 hex 定义）+ §1.3（path 非身份）+ §2.1；冻结项 ①/④ | **已入册**（DEC-028 Part 1/2）；V3 仅用 path 作 locator = 符合（FACT-044） |
| 2 | Manifest = Identity Authority；IR = Semantic Authority；V3 语义来自 IR、身份验证独立 IR | §1.1 双层架构 + §3.1 载体分工 + DEC-B1 身份自足；冻结项 ①/③ 语境 | **已入册**；V3 两半边均不符（IR 零消费 + 零身份锚，FACT-038）= 实现缺口 |
| 3 | 16 份 = Identity Available + Semantic Pending；允许重生成 IR；四保证 | §1.6（Semantic Pending + 四约束）+ 冻结项 ⑤ | **已入册**（DEC-028 Part 3）；本轮按 Owner 四保证措辞对齐（§4.1） |
| 4 | Semantic `{ready,incomplete,unknown}` + Decision `{pending_review,approved,rejected}`；禁合并 | §3.2 两层终局词表 + 冻结项 ③ | **已入册**（DEC-028 Part 5/6）；V3 `SEMANTIC_STATUS` 冻结 2 值须解冻加 unknown = 实现缺口 |
| 5 | `source_version_id` 命名消歧 | §1 命名方案（本文件）+ 契约 §1.2a | **本轮提案** = `source_content_sha256`（待 Owner 采纳 + DSH 确认） |
| 6 | bytes 交付只冻能力、不冻传输 | §2 能力冻结（本文件）+ 契约 §2.3 | **本轮冻结** = 能力 binding；传输暂缓 |

**核验结论**：候选版已承载原则 1–4 + 6；原则 5 以提案形式落字，是唯一待 Owner 采纳项。**候选在命名采纳后即 freeze-ready**（仍受五步序 Step 1/2 数据前置约束，见 §7）。

---

## §4 原则 3 措辞对齐 —— 16 份四保证（`DECISION`，本轮微调）

Owner 原则 3 的「四保证」与 DEC-028 Part 3「四约束」同向，本轮按 Owner 措辞对齐为**不变量四保证**（regeneration 允许，但必须同时成立）：

| # | 保证（不变量） | 对应既有约束 |
|---|---|---|
| ① | **source bytes hash 不变** | 约束① source bytes 不许改 |
| ② | **source identity 不变** | 约束② `source_content_sha256`（原 `source_version_id`）必须一致 |
| ③ | **IR 版本可追踪** | 约束③ 新 IR 必须绑定 `source_content_sha256`（版本可追踪） |
| ④ | **禁止覆盖历史事实** | 约束④ 重过 identity verification + semantic validation；禁改原 source / 禁 re-OCR 覆盖 / 禁新 identity / 禁新 hash 替旧 |

**禁止不变**（DEC-028 Part 3 / 契约 §1.6）：改原 source / re-OCR 覆盖原 source / 生成新 identity / 用新 hash 替代旧 hash。16 份 = **Identity Available / Semantic Pending（可恢复）**，非永久缺失。

---

## §5 (B) 剩余未决问题列表

> 只列真正未裁 / 待采纳 / 待双边。已关闭项不列。

### 5.1 待 Owner 采纳（本轮提案）

| # | 项 | 状态 | 说明 |
|---|---|---|---|
| **OQ-8′** | 接口键命名 = `source_content_sha256` | **PROPOSED，待 Owner 采纳 + DSH 双边确认** | §1 命名方案；采纳后契约全文词面收口 |

### 5.2 待 Owner 裁决（真未决）

| # | 项 | 说明 |
|---|---|---|
| **OQ-16′** | `pending_review → rejected` 判定准则 + `reviewable record` 载体形态 | unknown 路由已裁进 pending_review，但 reviewable record 用什么承载、何时判 rejected 未给 |
| **OQ-21** | 16 份 Semantic Pending 的呈现机制 | manifest 字段 vs V3 靠 IR 面有无推断；两侧横跨（DSH 同） |
| **OQ-15** | legacy 79 的披露形态 | v0.2 文字层：仅规模 vs 路径清单 |
| **OQ-10** | OCR 清单（钉 PDF 字节）是否纳入双层接口 | 语义与 md 面不同，不可混用；影响 md vs PDF 分层 |
| **OQ-13** | 17 份拒收记录（16 QC_FAIL + 1 REJECTED_V1）在接口中的地位 | 披露 vs 排除 |
| **OQ-17** | 存量 1 例 `andalone_question` 在两层词表下的呈现态与处置原子性 | 涉 R50 成员 manifest + IR 冻结工件（DSH D.3 同源） |
| **OQ-18** | E1 残留冲突：DSH Dependency Map 边表 E1（契约冻结→回填）与 DEC-026 五步序（回填→契约冻结）方向相反 | 须 Owner 在 Step 1 执行令或 v0.2 起草令一并裁 |
| **D-6 / E2** | Step 1 接口快照载体形态 + 与 R50 血统/配对再冻结 | 数据动作执行令细化，非契约文本 |

### 5.3 协调层（跨仓，须 Owner 约定）

| # | 项 | 说明 |
|---|---|---|
| **跨仓 DEC ID 撞号** | 累积 **3 处**：DSH `DEC-021`≠V3 `DEC-021`(B2)；DSH `DEC-022`≠V3 `DEC-022`(B3)；DSH `DEC-023`≠V3 `DEC-023`(Interface Scope) | 每轮新增撞号风险递增；须 Owner 定跨仓编号约定（本命名方案不解决 DEC 号撞号，只解决字段名撞名——两者是不同冲突） |

### 5.4 传输维度（暂缓，非冻结阻塞）

| # | 项 | 说明 |
|---|---|---|
| **OQ-12″** | source bytes 具体传输方案 | 能力已冻结（§2）；传输暂缓（共享 FS / 对象存储 / IR 内嵌 / 相对路径解析等），属实现/部署形态 |

---

## §6 (C) Implementation Gap（`DECISION ≠ IMPLEMENTATION`）

> 全部实现状态 = `not started` / `deferred` / `UNKNOWN`。本轮零代码、零数据动作。

### 6.1 V3 消费侧缺口

| 义务 / 能力 | 状态 | 缺口 ID |
|---|---|---|
| 验证 Manifest（字段完整 + `unit_type` 闭集） | **not started**（`manifest_reader.py:52` 硬取无校验） | V3-G1 |
| 重算 raw bytes sha 对账（= `source_content_sha256`） | **not started**（自算为 canonical_json 包裹 joined-text，`runner.py:71-73`；非 raw bytes） | B2-G1 |
| 判断接受 / 身份闸门（fail-closed） | **not started**（`identity_version` 0 命中） | V3-G1 / D2-G1 |
| 验证 IR 契约 + Gate + 拒收 | **not started**（零 IR 消费能力，语义消费全来自 manifest） | V3-G2 / B1-G3 |
| **身份验证能力（依赖 `source_content_sha256`，不依赖 path）** | **not implemented = not started**（本轮明确登记；V3 现仅用 path 作 locator = 符合 path 非身份，但无身份键校验） | Consumer Alignment v3 §4 / FACT-044 |
| 语义层加 `unknown` 取值 | **值集已裁** `{ready,incomplete,unknown}`；V3 加值 = **not started**（须解冻 `SEMANTIC_STATUS` / BUG-V3-018） | OQ-20 / G-12 |
| unknown → reviewable record → pending_review | **路由已裁**；V3 机制 = **not started**（candidate-gated-on-ready，`runner_b2.py:231-264`，非 ready 不可达决策层） | OQ-16′ / G-12 |
| 16 份身份/语义分离消费 + pending 标记 | **not started**（无分离/标记能力） | G-9 / G-11 |
| 只消费 Interface Scope 87 内 manifest | **not started**（无法识别接口面，`identity_version` 0 命中） | G-6 / D1-G2 |
| 内部 hash 家族治理（`line_hash` 双算法 / `integrity_hash` 退化） | **UNKNOWN**（是否进行未裁；DECISION 只限定其不作跨系统 identity） | OQ-7 / G-4 |

### 6.2 producer 侧缺口（DSH 域，本契约不替其决定）

| 义务 | 状态 | 缺口 ID |
|---|---|---|
| Manifest 携带 `source_content_sha256`（0/166 → 回填 87） | **not started**（五步序 Step 2；须 Step 1 快照 + 命名/格式裁决 + R50 配对再冻结 E2） | B1-G1 / D4-G2 |
| 双层关联从 path 升级为 `source_content_sha256` | **not started** | B1-G2 / G2 |
| 接口面 87 清单工件发布 | **not started**（87 是探针口径算出，非已发布清单） | D1-G1 / DSH C.1 |
| IR 覆盖扩产（71 → 更广） | **not started**（须 Owner 令；新数据生成） | G3 / OQ-11 |
| unit_type 值域守卫（生成链） | **not started** | G5 |
| Step 1 接口快照载体形态 + R50 血统 | **not started**（需 Step 1 执行令） | D4-G1 / D-6 |
| source bytes 传输形态交付 | **暂缓**（能力已冻，传输未裁，§2.2） | OQ-12″ |

### 6.3 五步序边界（`OBSERVED`）

五步序（DEC-026）**全是数据 / 契约动作，零 V3 实现动作**——V3 的 IR 消费 / 身份绑定 / 语义 unknown / reviewable-record 机制在五步序中无对应步骤，**V3 实现排期 = UNKNOWN，不因本评审获得排期**。本评审不提案为其插入步骤。

---

## §7 (D) 边界声明 + 冻结还差什么

**本文件做了**：Owner 六条原则的候选符合性核验（§3）；**接口键命名方案提案** `source_content_sha256`（§1，原则 5，待采纳）；**source bytes 交付只冻能力、不冻传输**（§2，原则 6）；16 份四保证措辞对齐（§4，原则 3）；剩余未决列表（§5 = B）；Implementation Gap（§6 = C）。

**本文件没做（任务禁止项 = D）**：未修改任何代码 · 未修改数据库 schema · 未修改 preprocessing 数据 · 未执行 IR 重生成 · 未执行图片恢复 · 未执行 daemon · **未冻结契约（仍 DRAFT / NOT FROZEN）** · 未把命名提案描述为已裁决（标 `PROPOSAL`）· 未把任何 DECISION 描述为已实现（全部 `not started` / `deferred` / `UNKNOWN`）。

**冻结还差（候选 → 可冻结的剩余条件）**：
1. **Owner 采纳命名方案** `source_content_sha256`（§1）+ 契约全文词面收口 + DSH 双边确认接口键名。
2. **五步序 Step 1** 接口快照冻结 + R50 血统（数据动作，D-6/E2）。
3. **五步序 Step 2** `source_content_sha256` 回填 87 + R50 配对再冻结（数据动作，E2；命名采纳后按新名回填）。
4. **OQ-18**（E1 残留冲突）裁决。
5. 同期落字：OQ-15（legacy 披露）· OQ-21（16 份呈现）。
6. **Owner 冻结令**（五步序 Step 3）。

> 原则 6 的能力冻结（§2）**已满足**，不再阻塞；OQ-12′ 传输维度**暂缓**，不阻塞；OQ-8′ 命名**从开放项变为待采纳提案**——是当前离冻结最近的一步。

**EB-008**：不因本文件变动；AuthorityIdentity 三元绑定为既有冻结设计，本契约仅引用不改。

---

*CONTRACT-v0.2-FREEZE-CANDIDATE-REVIEW — 2026-09-16，Claude（AITutors-v3 Consumer Owner）。V3 代码 `b5ddbe3`（其后仅文档提交，代码未变）· preprocessing `1657625`（+ DSH 并行未提交：ODR v1.4 / Producer Alignment v5 / Interface Facts v2.1）· 契约候选 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`（同批更新，**仍 DRAFT / NOT FROZEN**）· 本轮登记 V3 `DEC-029`。命名 = `PROPOSAL`（`source_content_sha256`，待采纳）；bytes 能力 = 冻结 / 传输 = 暂缓。零代码 · 零数据。DECISION ≠ IMPLEMENTATION。*
