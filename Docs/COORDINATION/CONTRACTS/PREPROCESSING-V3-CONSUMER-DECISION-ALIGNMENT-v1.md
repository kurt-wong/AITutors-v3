# PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v1

> **角色**：Claude = **V3 Consumer Owner**。对 Owner 指令 `PREPROCESSING-V3-CONTRACT-DECISION-FINALIZATION v1` 的四项裁决做 **V3 消费侧**对齐检查。
> **性质**：Consumer side alignment report。**非实现 · 非冻结 · 不替 DSH 决定生产侧实现 · 不提出实现方案。**
> **本轮状态**：裁决入册 + Contract v0.2 起草准备。Contract 保持 **v0.2 DRAFT / NOT FROZEN**。
> **结构**：按 Owner 令输出 `OBSERVED` / `DECISION` / `IMPLEMENTATION GAP` / `UNKNOWN` 四段。**所有实现状态 = `not started`**，不得提前宣称完成。
>
> **与既有文档的关系**：本文件是 FINALIZATION 轮的 V3 侧对齐报告。B1/B2/B3 三项裁决的逐项细节与证据锚保留在 `PREPROCESSING-V3-DECISION-ALIGNMENT-REPORT.md`（未废止，本文件不重复其全部表格）。两张汇总表在契约 §5.3 / §5.4。
>
> **证据基线**：
> | 侧 | 基线 |
> |---|---|
> | V3 代码 | `b5ddbe3`（其后仅文档提交，代码未变） |
> | V3 文档 | 本文件所在提交 |
> | preprocessing | `bbb5c70`（DEC-B1 入册）+ 未提交工作树（ODR v1.2 §1ter / Readiness v3.2 / Gap List v1.2 / Dependency Map v2.2 / **Producer Decision Alignment v1**，DSH 并行产出中） |
> | Owner 裁决 | `PREPROCESSING-OWNER-DECISION-RECORD-v1.md`（v1.2，§1 + §1bis + §1ter） |
> | 生产侧事实 | Interface Facts v2 + Readiness v3 + Gap List + Dependency Map（同上基线） |
> | V3 侧事实 | Consumer Gap Map + Decision Alignment Report + Blocker Analysis（`643ebd0`~`7561062`） |
>
> **编号对照（跨仓，须一并引用）**：本轮四项裁决 DSH 侧记为 `DEC-021-1`~`DEC-021-4`（ODR §1ter）。V3 侧 `DEC-021` **已被 B2 Identity 占用**（`state.yaml` @ `1243a7f`），为避免撞号，V3 侧另编 `DEC-023`~`DEC-026`。**同一批裁决，两套编号**；引用任一侧时必须给出对照。

---

## 0. Owner 裁决（要点照录，`DECISION`）

### Decision 1 — Interface Scope

> Interface Scope = **v2 standard interface set**, Current size = **87 records**。
> - **166** = 全部历史资产规模，不等于正式接口；
> - **87** = 当前正式接口范围；
> - **71** = 当前已生成 IR 的 semantic consumption 面，不代表完整 interface。
>
> 正式定义：**Manifest interface scope: 87** / **IR semantic consumption current frozen scope: 71 ADMITTED records**

### Decision 2 — Legacy v1 Handling

> v1 legacy 数据：**status = historical asset, not part of v0.2 interface**。规模 = **79**。
> 禁止：自动迁移 / 自动补齐 / 自动重新生成 IR / 自动加入 87 接口。
> 未来如需处理：单独建立 **Legacy Migration Plan**，不得混入当前 Contract。

### Decision 3 — Semantic Boundary

> 系统必须明确区分：**READY / INCOMPLETE / PENDING_REVIEW / REJECTED**。
> - **READY**：semantic annotation 完整、unit_type 合法、可进入后续消费；
> - **INCOMPLETE**：输入不足（缺 stem、缺必要字段等）；
> - **PENDING_REVIEW**：系统无法安全判断（unknown unit_type、semantic ambiguity、多种解释均可能）；
> - **REJECTED**：明确违反接口要求。
>
> 强制规则：任何 unknown semantic **禁止 automatic conversion / silent fallback / silent skip**，必须进入 **PENDING_REVIEW 或 REJECTED**，由明确规则决定。

### Decision 4 — Execution Ordering

> 所有数据动作必须遵循：
> **Step 1 Freeze interface snapshot → Step 2 Generate / backfill source_version_id → Step 3 Freeze Contract v0.2 → Step 4 Execute data hygiene → Step 5 Execute image recovery / historical cleanup**
>
> 原因：source identity 必须早于内容修改。身份冻结优先。

### 附带进入基线的前置裁决 — DEC-B1 细化（ODR §1bis，`DECISION`）

> source_version_id 作为双层**唯一关联键**；**V3 消费语义来自 IR，但 source 身份不依赖 IR 存在**。

该条对 V3 消费侧有直接后果（见 §1.3）。

---

## 1. 检查项 1 — V3 消费路径是否符合双层权威分工

### 1.1 OBSERVED（实测，V3 @ `b5ddbe3`）

| 事实 | 证据 |
|---|---|
| V3 唯一消费载体 = manifest；IR 消费代码 = **0 命中** | `manifest_reader.py:44-75`；`Grep resolver_ir\|source_sha256\|ir\.source @ backend/` = 0 |
| `Manifest` dataclass 无 sha、无 `source_version_id`、无 `identity_version` | `manifest_reader.py:28-35`（仅 `source_file/model/prompt_version/validation_issues/warnings/units`） |
| **`identity_version` 在 V3 全仓代码 0 命中** | `Grep identity_version @ backend/**/*.py` = 0 |
| **`C-IN-1` 在 V3 全仓代码 0 命中** | `Grep C-IN-1\|C_IN_1 @ backend/**/*.py` = 0 |
| V3 自算 hash 写入 `documents.original_sha256`，为 canonical_json 包裹值 | `runner.py:71-73`；`hashing.py:60-62` |
| producer 侧 C-IN-1 **已实现**（IR 生成时 `identity_version < 2` → `REJECTED_V1`） | IF-v2 §2.4；`resolver_reference.py`（producer 仓）；DSH Producer Alignment §A.5 |

### 1.2 判定

**两侧都不符合，且方向相反。**

| 双层权威 | 裁决要求 | V3 现状 | 判定 |
|---|---|---|---|
| **Manifest = Source Identity Authority** | 消费前以 manifest 身份对账 | manifest 载体上 0/166 携身份字段；V3 无任何身份校验代码 | **不符合**（authority 无承载 + V3 无校验） |
| **IR = Semantic Consumption Authority** | 语义消费以 IR 为准 | V3 的语义消费**全部来自 manifest**，IR 零消费 | **不符合**（消费的是身份层，不是语义层） |

**一句话现状**：V3 今天在用**身份层承载语义消费**，同时**没有任何身份锚**——双层裁决的两个半边，V3 侧一个都不满足。

### 1.3 DEC-B1「source 身份不依赖 IR 存在」的 V3 侧后果（`DECISION` → `IMPLEMENTATION GAP`）

该条对 V3 是**放宽**而非收紧：V3 的身份对账**不需要**先具备 IR 消费能力。因此：

- 身份绑定（把 raw bytes sha 写进 V3 侧对账字段）与 IR loader（语义消费路径）在 V3 侧是**两条独立工作线**，不是先后依赖；
- 当前两者**均未开始**；
- 反向不成立（ODR §1bis 明载）：IR 的语义承载依赖 manifest 身份锚定——所以 V3 若要走 IR 语义消费，仍需 manifest 侧先有 `source_version_id`。

`IMPLEMENTATION GAP`：

| # | 缺口 | 性质 | 状态 |
|---|---|---|---|
| V3-I1 | V3 具备 IR 语义消费路径 | V3 新增消费能力 | **not started** |
| V3-I2 | V3 以 raw bytes sha 做跨系统身份绑定（当前写入值为 canonical_json 包裹） | V3 消费侧绑定 | **not started** |
| V3-I3 | V3 消费前的身份对账闸门（重算比对，不一致 → 阻断） | V3 消费侧闸门，依赖 V3-I2 | **not started** |

### 1.4 UNKNOWN

- V3 侧 IR loader 的形态与排期 → **UNKNOWN**（Owner 未下达 V3 实现排期；Decision 4 只排数据动作，见 §4.4）。
- raw bytes sha 在 V3 侧的写入点 / 校验点 → **UNKNOWN**（同上）。

---

## 2. 检查项 2 — V3 是否能表达 READY / INCOMPLETE / PENDING_REVIEW / REJECTED

**这是本轮 V3 侧最重要的结构发现。**

### 2.1 OBSERVED（实测）

V3 仓内**自有原则**：**三层状态不复用**——E ResolvedStatus ≠ IR.semantic_status ≠ gate_decision（`compile/__init__.py:9`）。四个状态词分布在**两个互相正交、各自冻结**的值域里：

| Owner 状态词 | V3 落点 | 冻结值域 | 出处 |
|---|---|---|---|
| **READY** | `IR.semantic_status = "ready"` | `SEMANTIC_STATUS = frozenset({"ready","incomplete"})` | `compile/__init__.py:28-29`（BUG-V3-018 终裁冻结） |
| **INCOMPLETE** | `IR.semantic_status = "incomplete"` | 同上 | 同上 |
| **PENDING_REVIEW** | `candidate.decision_status = "pending_review"` | `DECISION_STATUS = frozenset({"pending_review","approved","rejected"})` | `gate/__init__.py:10-11`（10 §5.2 冻结） |
| **REJECTED** | `candidate.decision_status = "rejected"` | 同上 | 同上 |

**关键可达性事实**：

| 事实 | 证据 |
|---|---|
| `decision_status` 只存在于 **candidate**；candidate 只由 **ready 单元**产生 | `runner_b2.py:231-264`（非 ready 在 `:232-239` skip，到不了 `:252`）；`snapshot_repository.py:118-129` |
| 因此 `pending_review` / `rejected` **仅从 ready 单元可达** | 同上 |
| 非 ready 单元（含 unknown unit_type 终态）**永远进不了** decision 层 | 同上 |
| Compiler 对非 ready 不产 leaves | `compiler.py:72-73` |

### 2.2 结构判定

**Owner 的四个状态词读起来像一个线性状态机；V3 实现的是两个刻意不复用的正交层。**

```
Owner 词表（一维）:   READY ── INCOMPLETE ── PENDING_REVIEW ── REJECTED

V3 实现（二维）:
    语义层 SEMANTIC_STATUS   { ready , incomplete }     ← 冻结 BUG-V3-018
                              │
                              │ 仅 ready 可下沉
                              ▼
    决策层 DECISION_STATUS   { pending_review , approved , rejected }  ← 冻结 10 §5.2
```

**后果**：Decision 3 要处理的正是「unknown semantic → 必须进 PENDING_REVIEW 或 REJECTED」。但一个 unknown `unit_type` 单元在 V3 里是**语义上 not-ready**，按现状只能落 `semantic_status = incomplete`，而 `incomplete` **没有通往 `pending_review` / `rejected` 的边**。

**即：裁决点名的四个状态，个体都能表达，但对裁决关心的那类单元不可联合可达。**这正是 OQ-5 的实质，且 Decision 3 **没有解决层归属问题**——它只给了目标词，没给落在哪一层。

### 2.3 UNKNOWN（须 Owner，本报告不提案）

**Decision 3 的四值是 (a) 一个跨两层的逻辑词表（映射到现有两个冻结值域即可），还是 (b) 一个要求并成单一状态机的指令（须解冻 BUG-V3-018 与 10 §5.2 两个冻结域）？**

两种读法的 V3 后果截然不同：

| 读法 | 含义 | V3 代价 |
|---|---|---|
| (a) 逻辑词表 | READY/INCOMPLETE 归语义层，PENDING_REVIEW/REJECTED 归决策层；需新增「非 ready 也可进入决策层」的显式通道 | 须扩一条通道；是否动冻结值域待定 |
| (b) 单一状态机 | 四值并成一个枚举 | **须解冻两个已冻结域**（BUG-V3-018 + 10 §5.2），属最高级别变更 |

**本报告不预设是哪一种，也不提案。**这是 OQ-5 的 Owner 裁决内容。

### 2.4 IMPLEMENTATION GAP

| # | 缺口 | 状态 |
|---|---|---|
| V3-S1 | unknown semantic → PENDING_REVIEW / REJECTED 的可达通道（当前不存在） | **not started** |
| V3-S2 | 该通道落在哪一层（语义层扩展 / 决策层新入口 / 单一状态机） | **UNKNOWN**（须 Owner，涉冻结域） |
| V3-S3 | PENDING_REVIEW → REJECTED 的路由规则文本（Decision 3 要求「由明确规则决定」，规则本身未给） | **UNKNOWN** |

---

## 3. 检查项 3 — V3 代码中的 silent skip / fallback / semantic conversion

按 Owner 令，三项分别登记 `OBSERVED` / `NOT IMPLEMENTED` / `IMPLEMENTATION GAP`。

### 3.1 semantic conversion

| 标记 | 内容 |
|---|---|
| **OBSERVED** | `annotation_adapter.py:42` 把 payload 的 `unit_type` **硬编码重写**为 `"standalone_question"`；`:101-104` 以重写后的值分支。噪声（如 `andalone_question`）在此被静默洗白，下游 payload **不含异常值、无任何信号**。读取端 `manifest_reader.py:52` 硬取 `u["unit_type"]`，**无闭集校验**。 |
| **NOT IMPLEMENTED** | Decision 3「禁止 automatic conversion」。该禁令在 V3 代码中**零执行面**——没有任何一层检查值域，也没有任何一层拒绝改写。 |
| **IMPLEMENTATION GAP** | 读取端闭集校验 + 值域外显式路由（取代改写）。目标态 = PENDING_REVIEW 或 REJECTED。落层 = **UNKNOWN**（OQ-5，SEMANTIC_STATUS 无 pending 取值）。**not started**。 |

### 3.2 fallback

| 标记 | 内容 |
|---|---|
| **OBSERVED** | `resolved_span_adapter.py:77-90`：`if unit.unit_type == "standalone_question": … else: …`——**未知值落入 else，走 composite 分支**，产出 material/questions 式 spans。`runner_b2.py:116-127` 同构分支。 |
| **NOT IMPLEMENTED** | Decision 3「禁止 silent fallback」。该 else 分支就是静默 fallback 的定义形态。 |
| **IMPLEMENTATION GAP** | 同 3.1。**额外性质**：对一个非 composite 单元产出 composite 式 spans，不只是路由错误，而是**语义伪造**——它制造了源数据里不存在的结构解释。**not started**。 |

### 3.3 silent skip

| 标记 | 内容 |
|---|---|
| **OBSERVED** | `runner_b2.py:232-239`：`if root.semantic_status != "ready": skip_count += 1; … reason="not_ready"; continue`。`gate/service.py:182-184` 同类跳过。**真实原因（unknown unit_type）在任何一层都不出现**——记录在案的原因是 `"stem unresolved"` / `"options missing for choice type"` 等格式类错误（GAP-MAP §0 E-1 亲验更正后的形态）。 |
| **NOT IMPLEMENTED** | Decision 3「禁止 silent skip」。同时：非 ready 单元**无 PENDING_REVIEW 通路**（§2.1），所以「必须进入 PENDING_REVIEW 或 REJECTED」在现状下对这类单元**不可能满足**。 |
| **IMPLEMENTATION GAP** | 需要一条**带真实原因、可见、可审计**的隔离通道。该通道的落层触碰冻结值域（BUG-V3-018），见 §2.3。**not started**；落层 **UNKNOWN**。 |

### 3.4 三项的共同事实

三条禁令在 V3 侧**全部违反**，且**违反方式是同一条路径的三个切面**：

```
读取无校验 (manifest_reader.py:52)
   → annotation 洗白 (annotation_adapter.py:42)      [semantic conversion]
   → span 按原始值走 else (resolved_span_adapter.py:77-90)  [fallback]
   → 无信号 incomplete → skip (runner_b2.py:232-239)  [silent skip]
```

修复点不在这条链的任一端，而在**整条链缺少一个显式隔离态**。这与 §2 的结构发现是同一件事。

---

## 4. 逐裁决对齐

### 4.1 Decision 1 — Interface Scope = 87 / IR frozen scope = 71

**OBSERVED**

- v2 接口面（字段口径 `identity_version=="2"`）= **87**；目录口径 88（差 1 = resliced-pilot 三十一中混入件，producer 侧已 `REJECTED_V1`）；全语料 166；IR ADMITTED = **71**（1,664 单元，sha 71/71 零漂移）。（IF-v2 §2.4/§3；Readiness v3 §A.1）
- **V3 侧无「接口面」概念**：`identity_version` 代码 0 命中（§1.1）。V3 读到什么 manifest 就消费什么，**无法区分 87 与 79**。
- **87 的「表达」在生产侧也是缺口**：DSH Producer Alignment §A.3——现状**无任何文件级接口面清单工件**，87 是探针口径算出的集合，不是已发布的接口 manifest。

**DECISION**（照录，不展开）

Manifest interface scope = 87；IR semantic consumption current frozen scope = 71 ADMITTED。166 = 历史资产规模 ≠ 正式接口。

**IMPLEMENTATION GAP**（全部 `not started`）

| # | 缺口 | 侧 |
|---|---|---|
| D1-G1 | 接口面 87 的承载物（清单工件 / 口径声明）如何发布供 V3 核验 | producer（DSH C.1） |
| D1-G2 | V3 如何识别并只消费接口面内的 manifest（当前无此能力） | **V3** |
| D1-G3 | `source_version_id` 如何覆盖 87（回填机制 + 此后新文件的持续携带） | producer（DSH C.3） |
| D1-G4 | IR 后续扩展机制未定义（Decision 1 只裁「当前面」） | producer（DSH C.3 / D.6） |

**UNKNOWN**

- **语义覆盖悬崖（V3 侧新登记）**：双层裁决把语义消费从 manifest（87+ 面）移到 IR（**71**）。接口面内有 **16 份**（87−71）**无 IR 语义承载**。V3 今天**能**通过 manifest 消费这 16 份的语义；双层落地后，按「IR = Semantic Consumption Authority」它们**失去语义可消费性**，除非 ①IR 扩产（G3，未裁未排期）②V3 保留 manifest 语义兜底（**与 IR = Semantic Consumption Authority 冲突**）③明确声明其在语义面外但仍在身份面内。DSH 从生产侧记为 D.2（「16 份接口面内无 IR 成员的消费语义」）；**本报告从 V3 消费侧登记为独立缺口，须在 v0.2 落字**。

### 4.2 Decision 2 — Legacy v1 = 79，historical asset

**OBSERVED**

- 79 份 `identity_version` 缺失；producer 侧 C-IN-1 **已实现**（IR 生成时拒收，`resolver_reference.py`）。79 份自 R52 后未被触碰，零自动迁移 / 零补齐 / 零 IR 重生成已发生。（DSH §A.5）
- **V3 侧 C-IN-1 与 `identity_version` 均 0 命中**（§1.1）。**「v1 不入接口」目前由生产侧单边执行，消费侧无对应闸门。**

**DECISION**（照录）

historical asset，not part of v0.2 interface；四禁；未来走独立 Legacy Migration Plan，不得混入当前 Contract。

**IMPLEMENTATION GAP**

| # | 缺口 | 侧 | 状态 |
|---|---|---|---|
| D2-G1 | V3 侧无 identity 版本校验——若一份 v1 legacy manifest 被送入 V3，V3 **会照常消费** | **V3** | **not started** |
| D2-G2 | legacy 隔离的披露形态（v0.2 文字层：仅规模？路径清单？） | producer（DSH C.6） | 随 v0.2 起草 |

**措辞更正（本轮，非错误更正而是精度修正）**：既有 V3 文档（Gap Map / Blocker Analysis / v0.2 DRAFT §1.6）写「79 份 v1 在 C-IN-1 下必被拒收」——该表述**对 producer/IR 面成立**，**对 V3 消费面不成立**（V3 无此检查）。精确形态：C-IN-1 是 **producer 侧已实现、V3 侧未实现**的不变量。本条为更正的权威记录。

**UNKNOWN**

- V3 是否需要消费侧 identity 闸门（与 producer C-IN-1 构成双边）→ **UNKNOWN**（属 V3 实现设计，Owner 未下达）。

### 4.3 Decision 3 — 四状态机

**OBSERVED**：见 §2 全节（两层结构 + 可达性事实）与 §3 全节（三条禁令的代码切面）。

**DECISION**（照录）

四值词表 + 三条禁令 + unknown semantic 必须进 PENDING_REVIEW 或 REJECTED，路由由明确规则决定。

**补充事实（与 DSH 对账一致，DSH §B.3）**：存量恰 1 例 `andalone_question` 在 IR 中 `disposition = ADMITTED`。按 Decision 3 口径，该单元 `unit_type` 非法，**四状态机下不应是 READY**。其在 v0.2 下的呈现态属存量处置面——**未裁**（DSH D.3；V3 侧 OQ-5 同源）。

**IMPLEMENTATION GAP**

| # | 缺口 | 侧 | 状态 |
|---|---|---|---|
| D3-G1 | 三条禁令在 V3 零执行面（§3） | **V3** | **not started** |
| D3-G2 | unknown semantic → PENDING_REVIEW / REJECTED 的可达通道 | **V3** | **not started** |
| D3-G3 | 落层设计（读法 (a) 词表 vs (b) 单一状态机） | — | **UNKNOWN**（须 Owner，涉冻结域） |
| D3-G4 | PENDING_REVIEW → REJECTED 路由规则文本 | — | **UNKNOWN** |
| D3-G5 | producer 侧值域守卫 + 标记载体 | producer（DSH C.4） | **not started** |

**引用纪律**：本裁决的四值词表**取代** DEC-022 / DEC-019 的「UNKNOWN/PENDING」泛称。引用 B3 语义边界时以四值为准。

### 4.4 Decision 4 — 五步执行序

**OBSERVED**

- 五步序本身与交集定量**零冲突**（DSH Dependency Map v2.2 §4）：Step 2 回填的 87 份全部为 R50 成员（E2 硬约束，由 Step 1 快照承担配对角色）；Step 5 图片恢复在排除模式下与接口面零交集（1,394 份，2 份三重成员单独裁决）。
- **五步序全部是数据 / 契约动作，不含任何 V3 实现动作。**

**DECISION**（照录）

五步；身份冻结优先。

**IMPLEMENTATION GAP**

| # | 缺口 | 侧 | 状态 |
|---|---|---|---|
| D4-G1 | Step 1 接口快照的载体形态与 R50 血统关系（新基线工件？audit_id 规则？） | producer（DSH D.6 / C.1） | **not started**，需 Step 1 执行令 |
| D4-G2 | Step 2 回填范围已裁 87；字段名 / 格式（裸 hex vs 前缀）、md 面 vs PDF 面分层声明**未裁** | producer（DSH C.2） | **not started** |

**UNKNOWN（V3 侧，本轮明确登记）**

**Decision 4 不排 V3 实现。** 五步是数据动作序列；V3 的 IR 消费能力（V3-I1）、身份绑定（V3-I2/I3）、四状态机通道（V3-S1）**在五步序中没有对应步骤**。

→ **V3 侧实现排期 = UNKNOWN，且不因 Decision 4 而获得排期。** 本报告不提案为其插入步骤。

---

## 5. 跨侧观察（V3 ↔ DSH，登记不裁决）

本轮同时读到 DSH 并行产出的 Producer Decision Alignment v1 及其配套增量。以下三处需要两侧共同看见，**本报告只登记，不裁决、不提案**。

### 5.1 跨仓 DEC 编号冲突（须两侧一并引用对照）

| 裁决 | DSH 侧 | V3 侧 |
|---|---|---|
| B1 双层（细化） | `DEC-019`（总纲）/ `DEC-020`（DEC-B1 分项） | `DEC-020` |
| B2 identity | `DEC-019`（总纲）内 | **`DEC-021`** |
| B3 semantic boundary | `DEC-019`（总纲）内 | **`DEC-022`** |
| 本轮四项（D1~D4） | **`DEC-021-1`~`DEC-021-4`** | **`DEC-023`~`DEC-026`** |

**冲突点**：DSH 的 `DEC-021` = 本轮四项；V3 的 `DEC-021` = B2 identity。**同号异文。**

处置：本轮不改任一侧已入册编号（改历史编号会破坏引用链），改为**登记对照表**并要求引用时双向标注。建议后续由 Owner 一次性统一编号规则。

### 5.2 E1 硬约束与 Decision 4 的方向相反（残留不一致）

DSH `PREPROCESSING-EXECUTION-DEPENDENCY-MAP.md` v2.2 已把 §4 执行序改为 Owner 五步（Step 2 回填 → Step 3 契约冻结），**但边表 E1 未改**：

> `E1 | v0.2 冻结 → G1b | 字段未定义不得回填 | 硬(治理)`

**E1 的方向与 Decision 4 相反**（E1：契约冻结 → 回填；D4：回填 → 契约冻结）。

**可能的调和（登记，不裁决）**：`source_version_id` 的**语义**已由 DEC-021/B2 裁定（= `SHA-256(raw bytes)`，id 即 sha 值），不依赖契约文档冻结。因此 E1 在「算法语义」上已被满足。E1 的**残留效力**只在字段**名 / 格式**上——而那两项 DSH 已标未裁（C.2 / A1）。若 Step 2 以临时名/格式回填而 Step 3 契约后来改名，会产生二次回填。

→ 该残留冲突**须 Owner 在 Step 1 执行令或 v0.2 起草令中一并裁**，否则两侧文档会长期并存两个相反方向的「硬约束」。

### 5.3 语义覆盖悬崖（16 份）

见 §4.1 UNKNOWN。生产侧记为 DSH D.2，消费侧记为本报告 §4.1。**同一事实，两个视角，须在 v0.2 落字时合并处理**，否则会出现「身份面含 87 / 语义面只有 71」但接口未声明中间 16 份地位的空档。

---

## 6. 边界声明

**本文件做了**：Owner 四项裁决要点照录（§0）+ DEC-B1 细化并入基线；三项检查逐项完成（§1 双层符合性 / §2 四状态机可表达性 / §3 三条禁令的代码切面登记）；逐裁决 OBSERVED / DECISION / IMPLEMENTATION GAP / UNKNOWN 四段对齐（§4）；跨侧三处观察登记（§5）；既有文档一处措辞精度修正的权威记录（§4.2 C-IN-1）。

**本文件没做**：未把任何 DECISION 描述为已实现（全部 `not started` / `UNKNOWN`）；未提出实现方案（V3-I1~3 / V3-S1~3 / D1-G2 / D2-G1 均只列缺口不预判形态）；未替 DSH 决定生产侧实现（producer 侧缺口只引不重写）；未修改 preprocessing；未修改 V3 业务代码 / adapter / 数据库 schema / 测试逻辑 / EB-008 / admission 逻辑；未执行任何 migration / cleanup / 数据写入；**未冻结 Contract**。

**与 Contract v0.2 DRAFT 的关系**：本文件是其事实输入之一。本轮已同步更新 `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`（§1.6 升格 DECISION + Decision 2 披露 + §3.2 四值词表 + §4.1 READY + §5.5 五步序 + §5.3/§5.4 增行 + §6 OQ 状态变更 + §8 重写）。契约仍为 **DRAFT / NOT FROZEN**。

**EB-008 状态**：不因本文件变动。

---

*Consumer Decision Alignment v1 — 2026-09-16，Claude（AITutors-v3 Consumer Owner）。V3 代码 `b5ddbe3` · preprocessing `bbb5c70`（+ DSH 并行未提交工作树）· Owner Decision Record v1.2。DECISION ≠ IMPLEMENTATION。*
