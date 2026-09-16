# PREPROCESSING-V3 CONSUMER DECISION ALIGNMENT v3

> **状态**：**v3（2026-09-16，Interface Finalization Revision v1 回应轮）** · Authority = Owner 统一版指令（照录 preprocessing `PREPROCESSING-OWNER-DECISION-RECORD-v1.md` **§1quinquies**；ODR **v1.4**）。
> **角色**：Claude = **V3 Consumer Owner**。陈述 V3 消费面事实与义务，不替 DSH 决定生产侧实现。
> **本轮纪律（Owner 令原文）**：仅更新决策记录 / 契约草案 / Gap 文档 / 台账；**禁改代码 · 禁改 schema · 禁改 preprocessing 数据 · 禁重生成 IR · 禁图片恢复 · 禁 daemon · 禁冻结 Contract v0.2**。全部 implementation = **not started**。
> **编号沿革**：承接 `PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v2.md`（Interface Decision Finalization v1 轮，保留原文）。本文件为**维护中基线**，取代 v2。本轮**改动了前轮表述**（16 份 Unavailable→Pending；语义层加 `unknown`；path 非身份原则），故独立成 v3 以保审计链。
> **Discipline**：`OBSERVED` / `DECISION` / `IMPLEMENTATION GAP` / `UNKNOWN`；**DECISION ≠ IMPLEMENTATION**。
> **两侧事实基线**：ODR v1.4（§1~§1quinquies）· Interface Facts v2.1 · Readiness v3 · Consumer Gap Map（本仓）· **DSH Producer Alignment v5**（并行产出，本文件与其对读）。

---

## §0 Owner 裁决原文（Interface Finalization Revision v1，Part 1–6）

> 照录 ODR §1quinquies。本文件不新增裁决。

**Part 1 — Source Identity 原则修正（DEC-SOURCE-IDENTITY，最高优先级）**

> `source_version_id = SHA256(original source bytes)`；**格式：64 字符小写 hex 字符串**。
> Identity 由 `source_version_id` **唯一决定**；Location 由 `source_file` / path / locator 表达。
> **强制禁止**：任何文档不得暗示 `source_file` / path / absolute path / directory 参与：文件唯一判断 / source identity 判断 / version 判断 / hash identity 判断。
> 固化原则：**Source identity belongs to content hash, not storage location.**（文件身份属于内容哈希，不属于存储位置。）

**Part 2 — source_file / path 处理规则**

> `source_file` **保留**，重新定义 = `locator information`，**不是** identity information。
> 文档要求：「source_file 用于识别 source」→「**source_file 用于辅助定位 source，source_version_id 用于跨系统唯一识别 source**」。
> 未来 Windows / NAS / Linux / Object Storage / Cloud 路径变化：**不得导致 `source_version_id` 变化**。

**Part 3 — Identity-only 16 份重新定义**

> 16 份**不是永久缺失**。状态 = **Identity Available / Semantic Pending**（取代上轮「Semantic Unavailable」）。
> 允许后续重新执行 preprocessing 生成 IR，但四约束：① source bytes 不许改 ② `source_version_id` 必须一致 ③ 新 IR 必须绑定 `source_version_id` ④ 生成后 IR 必须重过 identity verification + semantic validation。
> 禁止：改原 source / 重新 OCR 覆盖原 source / 生成新 identity / 用新 hash 替代旧 hash。

**Part 4 — Interface Scope 保持**

> `Interface Scope = 87`，**不改为 71**。表：87 = 正式身份接口范围；71 = 当前已有 IR 语义消费范围；16 = 等待 semantic processing。
> 禁止：将「IR available」等同于「Interface available」。

**Part 5 — Semantic Unknown 状态补充（两状态体系终局词表）**

> 两状态体系**分离，禁止合并**。
> **Semantic Status 最终词表：`ready` / `incomplete` / `unknown`**。
> **Decision Status 词表：`pending_review` / `approved` / `rejected`**。

**Part 6 — Unknown 处理（明确规则）**

> 任何 unknown semantic unit：禁 silent skip / automatic conversion / silent fallback；**必须产生 `reviewable record`，进入 `pending_review` workflow**。

---

## §1 跨仓编号映射（第三处撞号）

| 事项 | V3 侧 ID | DSH 侧 ID |
|---|---|---|
| 四项 FINALIZATION 裁决 | `DEC-023`~`026` | `DEC-021-1`~`4` |
| Interface Decision Finalization v1 | `DEC-027` | `DEC-022` |
| **本轮 Interface Finalization Revision v1** | **`DEC-028`** | **`DEC-023`** |

**撞号累积至 3 处（`OBSERVED`，协调风险升级）**：DSH `DEC-021`≠V3 `DEC-021`(B2)；DSH `DEC-022`≠V3 `DEC-022`(B3)；**DSH `DEC-023`≠V3 `DEC-023`(Interface Scope)**。本轮 V3 用 `DEC-028` ≡ DSH `DEC-023`。**三处撞号已使跨仓引用高风险**——强烈建议 Owner 立即定约定（如 V3 侧此后 `V3-DEC-0NN` 前缀，或两仓常驻映射表）。本文件只登记不自裁。

---

## §2 Source Identity / Path 非身份 — V3 消费逻辑检查（Owner Part 9 重点）

### 2.1 固化原则（`DECISION`，Part 1/2）

**Source identity belongs to content hash, not storage location.** 身份 = `source_version_id = SHA256(raw bytes)`（64 小写 hex，**本轮已裁格式**）；`source_file`/path = **locator only**，不参与任何身份/版本/hash 判断。

### 2.2 V3 现状（`OBSERVED`）——path 用法已符合，身份校验未实现

| 面 | V3 现状 | 证据 | 与新原则 |
|---|---|---|---|
| `source_file` 用途 | **仅作 locator**——`Path(manifest.source_file)` 加载源 .md，全仓**无任何以 path 做身份/版本/hash 判断**的代码 | `runner.py:241`；`runner_b2.py:320`；`runner_b3.py:184`；`manifest_reader.py:30,69` | **符合**（path 非身份，V3 本就没拿 path 当身份） |
| `source_version_id` 身份校验 | **未实现**——V3 消费面读不到 preprocessing 的 `source_version_id`（manifest 0/166 携带）；`identity_version`/`resolver_ir`/`C-IN-1` 全仓 0 命中 | `manifest_reader.py:28-35`；`Grep identity_version\|resolver_ir\|C-IN-1 @ backend/**/*.py = 0` | **缺口**（Part 9 要求未来必须依赖 `source_version_id`） |
| V3 自算 hash | `documents.original_sha256` = `canonical_json` 包裹 joined-text，**非 raw bytes** | `runner.py:71-73`；`hashing.py:60-62` | **缺口**（DEC-021 要求 raw bytes，未改） |

**净结论**：V3 **今天不违反** path 非身份原则（它没拿 path 当身份用）；但也**完全没有** `source_version_id` 身份校验能力。Part 9 要求的「未来消费逻辑必须依赖 `source_version_id`、不得依赖 path」= **not started**。

### 2.3 `source_version_id` 同名异义（承接 v2 §1.2，仍须消歧）

契约键 = sha256 hex；V3 内部 `source_version_id` = `uuid.UUID` FK（`models/source.py:44-57`，`:50` 禁 sha 作 Seal 唯一）。同名异类，v0.2 落字须消歧（OQ-20 残余，本轮 Part 1 格式已裁但命名消歧仍在）。

---

## §3 本轮改动的裁决与 V3 侧状态

### 3.1 16 份 Identity-only：Unavailable → **Pending**（`DECISION`，Part 3/4）

前轮（DEC-027 Part 4）定为「Identity Available / Semantic Unavailable 正常态」。**本轮改为 Semantic Pending（可恢复）**——不是永久缺失，允许后续重生成 IR（四约束）。关闭「正常态 = 终态」的读法。DSH 侧 G3 扩产由「机制未裁」推进为「允许 + 四约束已裁」。

**V3 侧后果**：V3 须能对这 16 份做身份对账、暂不语义消费、标记为 pending（非 unavailable）；未来 IR 补齐后重过验证。V3 当前无身份/语义分离消费能力，也无 pending 标记（`IMPLEMENTATION GAP`，V3-G6 承接）。接口面是否设呈现字段（OQ-21）本轮 Part 3/4 **未明确裁**——见 §6。

### 3.2 语义层终局词表：加 `unknown`（`DECISION`，Part 5）

前轮 OQ-20(b)「语义层是否加 `unknown` 取值」——**本轮已裁**：`SEMANTIC_STATUS` 最终 = `{ready, incomplete, unknown}`；`DECISION_STATUS` = `{pending_review, approved, rejected}`；禁止合并。这**取代** DEC-025 四状态机的跨层合并记法：READY→semantic.ready、INCOMPLETE→semantic.incomplete、PENDING_REVIEW→decision.pending_review、REJECTED→decision.rejected（+ decision.approved）。

**V3 侧后果**：V3 的 `SEMANTIC_STATUS` 冻结于 `{ready, incomplete}`（`compile/__init__.py:28-29`，BUG-V3-018），**要加 `unknown` 须解冻该冻结域**。值集已裁，**实现仍 not started**。

### 3.3 unknown → pending_review 路由（`DECISION`，Part 6）

前轮 OQ-19「unknown→PENDING_REVIEW 可达性」、OQ-16「PENDING_REVIEW→REJECTED 规则」——**本轮 Part 6 给出路由**：unknown semantic unit **必须产生 reviewable record、进入 pending_review workflow**（不再是「PENDING_REVIEW 或 REJECTED 由规则决定」）。即 unknown 的去向已裁 = pending_review。

**V3 侧后果**：V3 现架构 candidate 仅由 ready 单元产生（`runner_b2.py:231-264`），非 ready（含 unknown）单元进不了决策层——**「产生 reviewable record 进 pending_review workflow」在 V3 无执行面**。规则已裁，**机制 not started**。reviewable record 的载体形态 = 未裁（DSH 同）。

---

## §4 V3 实现状态（Part 9 明确登记）

**`V3 identity verification capability not implemented` = `not started`**（Owner Part 9 原文要求登记项）。

V3 侧相关能力全部 `not started`，且**均不在五步序（DEC-026）内**：

| 能力 | 状态 | 依赖 |
|---|---|---|
| 读取 manifest `source_version_id` + 绑定（V3-I2） | not started | producer 回填 + 字段名消歧 |
| raw bytes sha 重算对账（V3-I3） | not started | V3-I2 + source bytes 可达（**传输方式未裁**，§6） |
| 语义层 `unknown` 取值（V3-S1） | not started | 值集已裁（Part 5），**解冻 BUG-V3-018 未执行** |
| unknown → reviewable record → pending_review（V3-S2） | not started | 路由已裁（Part 6），**机制未实现** |
| IR 消费路径（V3-I1） | not started | — |
| 接口面识别 + 16 份 pending 标记（V3-F1） | not started | 呈现字段未裁（OQ-21） |

---

## §5 Decision Alignment Summary（Owner Part 10 格式：`| Decision | Current | Final Rule |`）

| Decision | Current | Final Rule |
|---|---|---|
| Source identity 定义 | producer 算法在库 71/71；V3 自算 canonical_json 非 raw bytes；V3 零身份校验 | **`source_version_id = SHA256(raw bytes)`，64 小写 hex**；身份由其唯一决定（Part 1） |
| Path / `source_file` 角色 | V3 仅用作 locator（符合）；跨系统双层当前靠 path 值相等关联（不合规现状） | **path = locator only，非 identity**；任何文档不得暗示 path 参与身份/版本/hash 判断（Part 1/2） |
| `source_version_id` 格式 | 前轮 PROPOSED 裸 hex | **已裁 = 64 字符小写 hex**（与 `ir.source_sha256` 71 份一致，零迁移）（Part 1） |
| Interface Scope | 87（DEC-023） | **保持 87**，不改 71；71 = 当前 IR 语义消费；16 = semantic pending；禁「IR available = Interface available」（Part 4） |
| 16 份 Identity-only 状态 | 前轮「Semantic Unavailable 正常态」 | **改 = Identity Available / Semantic Pending**（可恢复）；允许重生成 IR，四约束（Part 3） |
| IR 重生成 | 前轮「另行批准」 | **允许，但四约束**（bytes 不变 / id 一致 / 新 IR 绑 id / 重过验证）；禁改原 source、禁新 identity、禁新 hash 替旧 hash（Part 3） |
| Semantic Status 词表 | `SEMANTIC_STATUS = {ready, incomplete}`（冻结 BUG-V3-018） | **终局 = `{ready, incomplete, unknown}`**；须解冻加 `unknown`（Part 5） |
| Decision Status 词表 | `DECISION_STATUS = {pending_review, approved, rejected}` | **保持不变**（Part 5） |
| 两状态体系关系 | 前轮「不合并」 | **保持分离、禁止合并**；取代 DEC-025 四状态机合并记法（Part 5） |
| unknown semantic 路由 | 前轮 OQ-19 可达性未裁 | **必须产生 reviewable record、进 pending_review workflow**；禁 silent skip/convert/fallback（Part 6） |
| V3 身份校验能力 | 未实现 | **登记 = not started**；未来消费必须依赖 `source_version_id`，不得依赖 path（Part 9） |

---

## §6 Remaining UNKNOWN（Owner Part 10：只保留真正未裁，不重复已关闭）

> 已关闭不再列：~~OQ-5~~（不合并）· ~~OQ-6~~（legacy 隔离）· ~~OQ-8 格式~~（64 hex）· ~~OQ-11 当前面~~（=71）· ~~OQ-12 身份维度~~（path 非身份）· ~~OQ-14~~（Semantic Pending）· ~~OQ-19 路由~~（→pending_review）· ~~OQ-20 值集~~（`{ready,incomplete,unknown}`）。

| # | 真正未裁事项 | 归属 |
|---|---|---|
| OQ-8′ | `source_version_id` 承载字段**命名消歧**（跨系统 sha vs V3 内部 UUID 同名）——格式已裁，命名冲突未消 | 契约措辞（OQ-20 残余） |
| OQ-12′ | **source bytes 如何交付给 V3 重算 hash**（传输/获取方式，非 path 形态）——path 已收窄为 locator，残余是 bytes 本身的可达方式 | 两侧横跨（DSH G-4 残余） |
| OQ-16′ | **pending_review → rejected 的判定**（人审后何以转 rejected）——unknown→pending_review 已裁，pending 之后的转 rejected 准则若独立则未裁 | gate 域 / workflow |
| OQ-21 | 16 份 Semantic Pending 的**接口面呈现机制**（manifest 字段 vs V3 靠 IR 面有无推断）——状态已裁，呈现载体未裁 | 两侧横跨（DSH 同） |
| OQ-10 | OCR 清单（钉 PDF 字节）是否纳入双层接口 | 承接（未裁） |
| OQ-13 | 17 份拒收记录（16 QC_FAIL + 1 REJECTED_V1）在接口中的地位 | 承接（未裁） |
| OQ-15 | legacy 79 披露形态（仅规模 vs 路径清单） | 起草面 |
| OQ-17 | 存量 1 例 `andalone_question` 呈现态与处置原子性 | 承接（未裁，R50 成员） |
| OQ-18 | E1 残留冲突（Dependency Map 边表 vs DEC-026 五步序方向相反） | 承接（未裁，本轮未触及） |
| D-6/E2 | Step 1 接口快照与 R50 基线配对血统；2 份三重成员处置 | 执行令面 |

---

## §7 边界声明

**本文件做了**：Owner Interface Finalization Revision v1（Part 1–6）的 V3 消费侧对齐——source identity/path 非身份检查（§2，Part 9 重点：V3 现用 path 作 locator 已符合、身份校验 not started）· 本轮三处改动的 V3 状态（16 份 Pending / 语义层加 unknown / unknown→pending_review，§3）· V3 实现状态登记（§4）· Decision Alignment Summary（§5，Part 10 格式）· Remaining UNKNOWN 精简（§6，Part 10 格式）· 跨仓第三处撞号登记（§1）。

**本文件没做**：未改任何 V3 代码 / adapter / schema / EB-008 / admission；未改 preprocessing；未执行数据动作（重生成 IR / 回填 / 图片恢复 / daemon 均未启动）；**未冻结 Contract**；未把任何 DECISION 描述为已实现（全部 `not started`）；未替 DSH 决定生产侧实现。

**与 DSH Producer Alignment v5 的关系**：并行产出。DSH 陈述生产侧（G 项 + §1quinquies 保守义），本文件陈述消费侧（V3 能力）。三处横跨须 v0.2 一并落字：`source_version_id` 命名消歧（OQ-8′/OQ-20 残余）· source bytes 交付方式（OQ-12′）· 16 份呈现机制（OQ-21）。

---

*v3 · 2026-09-16 · Claude（AITutors-v3 Consumer Owner）。裁决基准 = ODR v1.4 §1quinquies；V3 代码基线 `b5ddbe3`（其后仅文档提交，代码未变）· preprocessing `1657625`（+ DSH 并行未提交工作树：ODR v1.4 §1quinquies / Producer Alignment v5）。Contract v0.2 同批更新四章节（DRAFT / NOT FROZEN）。如有文字冲突，以 Owner 原文为准。DECISION ≠ IMPLEMENTATION。*
