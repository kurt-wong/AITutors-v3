# PREPROCESSING-V3 CONSUMER DECISION ALIGNMENT v2

> **状态**：**v2（2026-09-16，Interface Decision Finalization v1 回应轮）** · Authority = Owner 统一版指令（聊天原文照录于 preprocessing `PREPROCESSING-OWNER-DECISION-RECORD-v1.md` §1quater；ODR **v1.3**）。
> **角色**：Claude = **V3 Consumer Owner**。陈述 V3 消费面事实与义务，**不**做 preprocessing 审查者，**不**替 DSH 决定生产侧实现。
> **本轮纪律（Owner 令原文）**：不修改代码 / 不执行数据清洗 / 不执行数据迁移 / 不冻结数据库实现 / 不提前实现未裁事项。Contract 保持 **DRAFT / NOT FROZEN**。
> **编号沿革**：承接 `PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v1.md`（FINALIZATION v1 四项裁决轮，保留原文）。本文件为**维护中基线**（Owner Part 9 指定），取代 v1 作为 V3 消费侧对齐件。
> **Discipline**：`OBSERVED` / `DECISION` / `IMPLEMENTATION GAP` / `UNKNOWN` 四段；所有实现状态 = **not started**；无证据一律标 `UNKNOWN`；**DECISION ≠ IMPLEMENTATION**。
> **两侧唯一事实基线**：ODR v1.3（§1 + §1bis + §1ter + §1quater）· Interface Facts v2 · Readiness v3 · Consumer Gap Map（本仓）· **DSH Producer Alignment v4**（并行产出，本文件与其对读）。

---

## §0 Owner 裁决原文（Interface Decision Finalization v1，Part 1–6 + 最终原则）

> 照录 ODR §1quater。本文件不新增裁决；凡未载于此，均为未裁。

**Part 1 — 双层职责模型（正式采用）**

> **Manifest = Source Identity Authority；IR = Semantic Consumption Authority。**
> Manifest 回答「这个东西是谁？」（source identity / source version / raw bytes hash / 文件版本关系）；
> IR 回答「这个文件里面有什么？」（question structure / semantic annotation / knowledge information / unit information）。
> 禁止：用 Manifest 替代 IR 描述题目；用 IR 替代 Manifest 证明文件身份。

**Part 2 — 生产与消费责任边界**

> Manifest：Producer = Preprocessing（DSH）——生成 Manifest / 计算 `source_version_id` / 保证字段正确；Consumer = V3——**验证 Manifest / 重新计算 hash / 判断是否接受**。
> IR：Producer = Preprocessing——OCR 后结构化 / LLM 语义解析 / 生成 IR；Consumer = V3——**验证 IR 是否符合契约 / Gate 判断是否进入正式题库 / 拒绝不符合的数据**。
> 固化原则：**Preprocessing 负责解释，V3 负责接受或拒绝解释。**

**Part 3 — Scope 裁决**

> **Interface Scope = 87**（87 份文件具备接口身份）；**IR Consumption Scope = 71 ADMITTED**（71 份具备可消费语义结构）。二者允许不同。
> 禁止（为让数字一致）：强制生成 IR / 删除 identity 文件 / 修改历史数据。

**Part 4 — 16 份 Identity-only 文件**

> 「Manifest 有、IR 无」属正常状态，定义：**Identity Available / Semantic Unavailable**。
> 不得：自动补 IR / LLM 猜测生成 / 静默进入题库。后续是否重新生成 IR：**另行批准**。

**Part 5 — Semantic Unknown 处理原则**

> 对 `unit_type unknown` / `semantic unclear` / `annotation uncertain`：禁止 ①自动转换 ②静默 fallback ③静默 skip。必须保留事实状态，进入 **`UNKNOWN` 语义状态**。
> 注意：**不要合并现有 `semantic_status` 与 `decision_status` 两个状态体系**。本轮只确认：**UNKNOWN 属于语义层**。

**Part 6 — Contract v0.2 编写范围（Frozen Candidate 只冻结三件）**

> 冻结内容：
> ① **Identity**：`source_version_id = SHA256(original source bytes)`；
> ② **Scope**：Manifest 87 / IR 71 snapshot；
> ③ **Semantic Boundary**：`Unknown ≠ Ready`；Unknown 不得自动进入正式题库。
> 暂缓冻结（不属于 v0.2 interface contract）：数据库字段最终设计 / UI 展示 / 自动补全机制 / IR 扩产计划 / 图片恢复流程 / daemon 持续生产策略。

**最终原则（Owner 原文）**

> 文件身份由生产侧证明，系统侧验证。
> 文件内容由生产侧解释，系统侧裁决。
> 宁可缺少结构化数据，也不能制造未经确认的结构化数据。

---

## §1 跨仓编号映射与命名碰撞（协调层，引用时必须双向标注）

### 1.1 DEC ID 撞号（累积，已第二处）

| 事项 | V3 侧 ID | DSH 侧 ID | 备注 |
|---|---|---|---|
| B1 双层传输 | `DEC-020` | `DEC-020`（ODR §1bis 记为 DEC-B1） | 一致 |
| B2 identity 算法 | `DEC-021` | — | **V3 DEC-021 = B2** |
| 四项 FINALIZATION 裁决 | `DEC-023`~`DEC-026` | `DEC-021-1`~`DEC-021-4` | **DSH DEC-021 ≠ V3 DEC-021** |
| B3 语义边界 | `DEC-022` | — | **V3 DEC-022 = B3** |
| **本轮 Interface Decision Finalization v1** | **`DEC-027`** | **`DEC-022`**（ODR §1quater） | **DSH DEC-022 ≠ V3 DEC-022** |

**撞号现状**：DSH 的 `DEC-021`/`DEC-022` 分别与 V3 的 `DEC-021`(B2)/`DEC-022`(B3) 同号异文。本轮不改任一侧历史编号（改会断引用链），改为**每处引用双向标注**。本令 V3 侧登记为 **`DEC-027` ≡ DSH `DEC-022`**。

**协调风险（`OBSERVED`，须 Owner 定约定）**：撞号已从 1 处增至 2 处，后续每轮都会新增。建议约定（本文件只登记不自裁）：V3 侧此后用 `V3-DEC-0NN` 前缀，或两仓各维护一张常驻映射表。属流程约定，非架构裁决。

### 1.2 `source_version_id` 同名异义（本轮新登记，比 DEC 撞号更危险）

契约的 `source_version_id` 与 V3 代码里到处出现的 `source_version_id` **不是同一个东西**：

| 概念 | 类型 | 语义 | 证据 |
|---|---|---|---|
| **preprocessing 契约 `source_version_id`** | sha256 hex（64 小写） | `SHA256(original source bytes)`，跨系统身份键，**id 即 sha 值** | DEC-027 Part 6；IR 侧 `ir.source_sha256` 71/71 同值 |
| **V3 内部 `source_version_id`** | `uuid.UUID` | `document_source_versions` 行主键 FK；Seal 层唯一性锚 `(logical_execution_stage, logical_execution_hash)`，**明令禁用 sha 作唯一** | `models/source.py:44-57`（`:50`「禁 UNIQUE(original_sha256)」）；`snapshot_repository.py:42-45` `session.get(DocumentSourceVersion, source_version_id)`；`runner_b2.py:158` `create_source_version(...).id` |

**危害**：契约若写「V3 消费 `source_version_id`」，极易被读成「V3 已具备」——**实为同名异类**（UUID vs sha256 hex）。当 manifest 未来补上 `source_version_id`（sha256 hex），V3 schema 里已有同名 UUID 列，**命名/类型直接冲突**。

**V3 内部第三概念（`OBSERVED`，勿与上两者混）**：`Document.original_sha256`（`String(64)` UNIQUE，`models/source.py:33,37`）——BUG-V3-007 文档身份，概念上对应「源内容 hash」，但当前实为 `canonical_json` 包裹的 joined-text（`runner.py:71-73` `file_sha = sha256_hex(body_text)`；`hashing.py:60-62` canonical wrap），**非 raw bytes**（DEC-021 要求 raw bytes，未改）。

→ **落 v0.2 时必须消歧**：跨系统键与 V3 内部 UUID 不得共用「`source_version_id`」一名而不加限定。列为 OQ-20。

---

## §2 V3 消费侧事实基线（Owner Part 7.1）

### 2.1 Manifest 验证责任（V3 义务，`REQUIREMENT`）

**Owner 裁定（Part 2）**：V3 作为 Manifest Consumer = **验证 Manifest / 重新计算 hash / 判断是否接受**。

**OBSERVED 现状**：三项义务**全部未实现**。

| 义务 | 现状 | 证据 |
|---|---|---|
| 验证 Manifest | `load_manifest` 硬取字段，**无任何校验**（`unit_type` 硬取 `u["unit_type"]`，无闭集校验） | `manifest_reader.py:44-75`；`:52` |
| 重新计算 hash 对账 | **无**——V3 不读 preprocessing 的 sha；自算 `file_sha` 是 canonical_json 包裹 joined-text，非 raw bytes，**对不上** producer `source_sha256` | `runner.py:71-73`；`hashing.py:60-62`；`Grep source_sha256 @ preprocessing_consumer` = 0 |
| 判断是否接受 | **无身份闸门**——读到什么消费什么，不区分 87/79，不拒 sha 不符 | `Grep identity_version\|C-IN-1\|resolver_ir @ backend/**/*.py` = **0** |

**可执行前提（`OBSERVED`，与 DSH G-4 同源）**：「V3 重算 hash」成立的前提是 **source bytes 对 V3 可达**。manifest 当前 `source_file` = 本机绝对路径（`D:\Project\Papers\...`），跨机不可解析（IF-v2 §2.1）。交付形态（相对路径化 / 打包）未裁 → OQ-12。

**同算法可行性已实证（`OBSERVED`）**：生产侧 71/71 IR 的 `source_sha256` == 当前磁盘 md 原始字节 sha256，零漂移（IF-v2 §3.2）——证明「V3 用标准库当场重算对账」在算法上完全可行，缺的是载体字段 + V3 消费代码。

### 2.2 IR 消费责任（V3 义务，`REQUIREMENT`）

**Owner 裁定（Part 2）**：V3 作为 IR Consumer = **验证 IR 是否符合契约 / Gate 判断 / 拒绝不符合的数据**。语义消费方向 = **IR → V3**（DEC-020 / DEC-B1）。

**OBSERVED 现状**：V3 **零 IR 消费能力**。

- V3 当前唯一消费载体 = **manifest**；`Grep resolver_ir\|resolver-ir\|source_sha256 @ preprocessing_consumer` = **0**（FACT-030/038）。
- 语义事实（unit 结构 / span 行号）全部经 manifest → annotation/span adapter 进入 V3，**不经 IR**。
- 因此 V3 今天**违反**「IR = Semantic Consumption Authority」——它用身份层（manifest）承载语义消费。

**`IMPLEMENTATION GAP`**：V3 IR loader 是**新增消费能力**（当前不存在），且**在五步序（DEC-026）中无对应步骤**——V3 IR 消费实现排期 = `UNKNOWN`，不因本轮裁决而获得排期。

### 2.3 87 / 71 Scope 区别（`DECISION`，Part 3）

| 口径 | 值 | 含义 | V3 现状 |
|---|---|---|---|
| Interface Scope（Manifest） | **87**（字段口径 `identity_version=="2"`） | 具备接口身份的文件数 = 回填范围 | **无法识别**——`identity_version` 0 命中 |
| IR Consumption Scope | **71 ADMITTED**（1,664 单元） | 具备可消费语义结构 = 当前语义冻结面 | **零消费**（不读 IR） |
| 差额 | **16**（87−71） | Identity Available / Semantic Unavailable（Part 4 正常态） | 见 §4.3 |
| 历史资产 | 166 / v1 legacy 79 | 非接口（DEC-023/024） | v1 被送入会照常消费（无闸门） |

**三禁（Part 3，叠加生效）**：禁止为让数字一致而 ①强制生成 IR ②删除 identity 文件 ③修改历史数据。任何「补齐 16 份」的冲动动作均违反 Owner 裁决。

---

## §3 V3 当前实现检查（Owner Part 7.2 —— 只报告，不改码）

### 3.1 符合（`OBSERVED`）

| # | 项 | 证据 |
|---|---|---|
| C-1 | **内部 hash 不作跨系统 identity**——V3 的 `body_hash`/`line_hash`/`integrity_hash` producer 零产出，本就是内部字段；`compile/__init__.py:10` 已有「text_hash raw 绝不经 canonical JSON」规则，与 DEC-021 方向一致 | `compile/__init__.py:10`；FACT-036 |
| C-2 | **三层状态不复用**原则（E ResolvedStatus ≠ IR.semantic_status ≠ gate_decision）与「四者语义独立、禁混用」方向一致 | `compile/__init__.py:9` |
| C-3 | **不 materialize 非 ready 单元**——unknown unit_type 经静默 skip 不产 candidate / leaves，结果上满足「Unknown 不得进入正式题库」（**路径不符合**，见 3.2） | `runner_b2.py:232-239`；`compiler.py:72-73` |
| C-4 | **AuthorityIdentity 三元绑定** `(source_version_id, candidate_id, claim_id)`，run_id 禁入——claim 身份不经 `unit_id` 裸键 | `evidence.py:28-29`（EB-008 既有，本契约不改） |
| C-5 | **producer 侧 B2 已 READY**（raw bytes SHA-256 单算法、双语料、单点生产）——V3 侧对账的算法前提由 producer 满足 | IF-v2 §4.1；Readiness §4 |

### 3.2 不符合（`OBSERVED`，实现均未开始）

| # | Owner 裁决要求 | V3 现状 | 证据 |
|---|---|---|---|
| N-1 | Manifest = Source Identity Authority | **不符**——manifest 0/166 携身份字段；V3 零身份校验代码 | `manifest_reader.py:28-35`；`Grep identity_version = 0` |
| N-2 | IR = Semantic Consumption Authority | **不符**——V3 语义消费全来自 manifest，IR 消费 = 0 | `Grep resolver_ir\|source_sha256 @ consumer = 0` |
| N-3 | V3 验证 Manifest + 重算 hash + 判断接受（Part 2） | **三项全无**（§2.1 表） | 同 §2.1 |
| N-4 | V3 验证 IR 符合契约 + Gate + 拒收（Part 2） | **无 IR 消费能力**（§2.2） | 同 §2.2 |
| N-5 | 禁止 automatic conversion（unknown unit_type） | **违反**——`annotation_adapter.py:42` 硬编码重写为 `"standalone_question"`（静默洗白） | `annotation_adapter.py:42,101-104` |
| N-6 | 禁止 silent fallback | **违反**——span 层未知值走 `else` → composite 分支 | `resolved_span_adapter.py:77-90`；`runner_b2.py:116-127` |
| N-7 | 禁止 silent skip | **违反**——静默 incomplete→skip，真实原因任何层不出现 | `runner_b2.py:232-239`；GAP-MAP §0 E-1 |
| N-8 | UNKNOWN 属语义层（须可表达） | **不可表达**——`SEMANTIC_STATUS` 冻结 2 值 `{ready,incomplete}`，无 `unknown` 取值 | `compile/__init__.py:28-29`（BUG-V3-018） |
| N-9 | unknown semantic 强制路由进 PENDING_REVIEW/REJECTED | **不可达**——decision_status 仅 candidate 有，candidate 仅由 ready 产；非 ready 单元永进不了决策层 | `runner_b2.py:231-264`；`gate/__init__.py:10-11` |
| N-10 | 只消费 Interface Scope = 87 内 manifest | **无法识别接口面**，读到什么消费什么（含 v1 legacy 79） | `Grep identity_version = 0` |

### 3.3 需未来实现（`IMPLEMENTATION GAP`，全部 `not started`）

对应 Owner Part 2 的 V3 义务，实现能力清单：

| 能力 ID | 能力 | 依赖 | 排期 |
|---|---|---|---|
| **V3-I1** | IR 消费路径（loader + 契约校验 + Gate 拒收） | Part 6 冻结 + 五步序外的 V3 实现令 | `UNKNOWN`（五步序无此步骤） |
| **V3-I2** | 读取 manifest `source_version_id`（sha256 hex）并绑定到 V3 内部身份 | producer Step 2 回填 + OQ-8 字段名/格式 | `UNKNOWN` |
| **V3-I3** | raw bytes sha 重算对账闸门（写 `documents.original_sha256` 改 raw bytes） | V3-I2 + source bytes 可达（OQ-12） | `UNKNOWN` |
| **V3-S1** | 语义层 `unknown` 取值（`SEMANTIC_STATUS` 加第三值） | 解冻 BUG-V3-018（OQ-20） | `UNKNOWN` |
| **V3-S2** | unknown semantic → PENDING_REVIEW/REJECTED 可达通道 | V3-S1 + OQ-19 路由架构 + OQ-16 规则文本 | `UNKNOWN` |
| **V3-F1** | 接口面识别与过滤（只消费 87 内 manifest，拒 v1 legacy） | producer 接口面承载物（DSH C.1/G-3）+ identity 字段 | `UNKNOWN` |

**关键边界**：上述 6 项 V3 能力**全部不在五步序（DEC-026）内**。五步序是数据/契约动作，不含 V3 实现步骤——**V3 实现排期 = UNKNOWN，且不因本轮任何裁决而获得排期**。

---

## §4 语义边界层归属（Part 5 后果：OQ-5 关闭 + OQ-19 新登记）

### 4.1 OQ-5 核心已关闭（`DECISION`，Part 5）

v1 轮登记的 OQ-5 =「四状态机在 V3 的层归属：(a) 跨两层逻辑词表 vs (b) 并成单一状态机」。**Part 5 已裁**：

> 不要合并 `semantic_status` 与 `decision_status` 两个状态体系。本轮只确认：**UNKNOWN 属于语义层**。

→ **Owner 明确否定 (b) 单一状态机**（不要合并）。两个状态体系**并存不互斥**（与 DSH v4 §B.5 解读一致：四状态机 = 决策层词表；UNKNOWN = 语义层事实呈现；unknown semantic 在语义层呈现 UNKNOWN，在决策层按 DEC-025 路由 PENDING_REVIEW/REJECTED）。**OQ-5 的「逻辑词表 vs 单一枚举」问题已关闭 = 不合并。**

### 4.2 由此产生两项新的 V3 侧精确缺口

**（a）语义层缺 `unknown` 取值（`OBSERVED`，解冻需求）**

Owner 要求 UNKNOWN 属语义层。V3 的语义层 `SEMANTIC_STATUS` **冻结于 2 值** `{ready, incomplete}`（`compile/__init__.py:28-29`，BUG-V3-018），**无 `unknown` 取值**。要让「UNKNOWN 属语义层」在 V3 可表达，必须给 `SEMANTIC_STATUS` 加第三值 `unknown` → **须解冻 BUG-V3-018**。

这是 Part 5 的直接 V3 侧后果，且**比 v1 轮的 OQ-5 更具体**：不再是「哪一层」（已裁 = 语义层），而是「语义层当前值域不够，要解冻加值」。→ **OQ-20**。

**（b）语义 UNKNOWN → 决策 PENDING_REVIEW 的可达性（`OBSERVED`，新架构问题）**

Owner 模型：unknown semantic 在语义层呈现 UNKNOWN（事实保留），在决策层路由到 PENDING_REVIEW。但 V3 的管线是：**candidate 只由 ready 单元产生**（`runner_b2.py:231-264`），`decision_status` 只存在于 candidate（`gate/__init__.py:10-11`）。一个语义层为 `unknown`（非 ready）的单元 → **不会成为 candidate → 永远到不了 PENDING_REVIEW**。

即：即便加了语义层 `unknown` 取值（解决 (a)），**「unknown → PENDING_REVIEW」这条 Owner 指定的路由在 V3 现架构下仍不可达**，除非 ① 让非 ready 单元也能进入决策通道（解冻 candidate 产生闸门）② 路由发生在 V3 candidate 管线之外 ③ 其他（本文件不预设）。→ **OQ-19**，须 Owner/架构裁决。

### 4.3 16 份 Identity-only = 正常态（`DECISION`，Part 4；关闭 OQ-14）

v1 轮登记的 OQ-14「语义覆盖悬崖：16 份无 IR 承载成员的地位」——**Part 4 已裁**：

> 「Manifest 有、IR 无」属正常状态：**Identity Available / Semantic Unavailable**。不得自动补 IR / LLM 猜测生成 / 静默进入题库。是否重新生成 IR：另行批准。

→ **OQ-14 关闭**：这 16 份**不再是接口的未声明空档，而是声明的正常状态**。DSH 侧同批关闭其 Dependency Map 决策点 D-2（Producer Alignment v4 §B.4）。

**V3 侧后果（`REQUIREMENT`）**：双层落地后，V3 必须能**消费身份而不消费语义**——即对这 16 份，V3 应完成身份对账（接受其 Manifest 身份）但**不进入语义消费**（无 IR 可消费），且**不得静默进入题库**。V3 当前无此区分能力（它要么整体消费 manifest、要么整体不消费），实现归 V3-F1 / V3-I1。**接口面是否需呈现字段**（如 semantic availability 标记）供 V3 Gate 直接读取 = 未裁（DSH G-6 同源）→ OQ-21。

---

## §5 Implementation Gap 表（Owner Part 7.4 指定格式）

> 格式：`| Decision | Current | Gap |`。全部 `not started`。与 DSH Producer Alignment v4 §C 对读（生产侧 G-1~G-7）。

| Decision | Current | Gap |
|---|---|---|
| **Part 2** V3 验证 Manifest + 重算 hash + 判断接受 | 三项全无：无校验、不读 producer sha、无身份闸门 | **V3-G1**：需 ①manifest 读取校验层 ②raw bytes sha 重算对账 ③接受/拒绝闸门。依赖 producer 回填字段（DSH G-1）+ source bytes 可达（DSH G-4 / OQ-12） |
| **Part 2** V3 验证 IR 符合契约 + Gate + 拒收 | V3 零 IR 消费能力 | **V3-G2**：需 IR loader + 契约校验 + Gate 拒收路径（V3-I1）。语义消费须从 manifest 迁到 IR。排期 `UNKNOWN`（五步序无此步骤） |
| **Part 6①** `source_version_id = SHA256(raw bytes)` | producer 算法在库且 71/71 实证；manifest 0/166 携字段；V3 零读取 | **V3-G3**：V3 侧读取 + 绑定能力（V3-I2）。**命名碰撞**：V3 内部已有同名 UUID 列，须消歧（OQ-20） |
| **Part 6①** raw bytes 对账写入 `documents.original_sha256` | 当前为 canonical_json 包裹 joined-text（非 raw bytes） | **V3-G4**：改写入算法为 raw bytes sha（DEC-021 既定方向，未实现） |
| **Part 6②** 只消费 Interface Scope = 87 | V3 无法识别接口面（`identity_version` 0 命中） | **V3-G5**：接口面识别与过滤（V3-F1）。依赖 producer 接口面承载物（DSH C.1/G-3） |
| **Part 6②** IR 71 snapshot 语义消费 | V3 零 IR 消费 | 同 V3-G2 |
| **Part 4** 16 份 Identity-only 正常态处理 | V3 无身份/语义分离消费能力 | **V3-G6**：能消费身份、不消费语义、不静默入题库。是否需接口面呈现字段未裁（OQ-21） |
| **Part 6③** `Unknown ≠ Ready`；Unknown 不入正式题库 | 结果上经静默 skip 达成（不 materialize），但路径不符合 | **V3-G7**：须改为显式语义 `unknown` 态（非静默 skip），结果符合升级为路径+结果双符合 |
| **Part 5** UNKNOWN 属语义层，可表达 | `SEMANTIC_STATUS` 冻结 `{ready,incomplete}`，无 `unknown` 取值 | **V3-G8**：语义层加第三值 `unknown`（V3-S1），**须解冻 BUG-V3-018**（OQ-20） |
| **Part 5** 禁 auto-conversion / silent fallback / silent skip | **三禁全违反**（洗白 / composite fallback / 静默 skip，同一条链三个切面） | **V3-G9**：需在读取→适配→编译整条链引入显式隔离态。修复点不在链任一端，而在整条链缺显式隔离 |
| **DEC-025** unknown semantic 路由 PENDING_REVIEW/REJECTED | 非 ready 单元不可达决策层 | **V3-G10**：需 unknown → 决策层可达通道（V3-S2）。**架构问题 OQ-19**：V3 gates candidate on ready，须 Owner 裁路由架构 |
| **Part 5/DEC-025** 不合并两状态体系 | V3 本就分两层（`compile`/`gate`），方向一致 | 无新增 gap——**符合**「不合并」。但两层各自值域需按上数行扩展 |

---

## §6 逐裁决四段登记（OBSERVED / DECISION / IMPLEMENTATION GAP / UNKNOWN）

### Part 1 — 双层职责模型
- **DECISION**：Manifest = Source Identity Authority；IR = Semantic Consumption Authority；双禁（Manifest 不代 IR 描述题目 / IR 不代 Manifest 证身份）。
- **OBSERVED**：V3 两个半边都不符——用身份层（manifest）承载语义消费（违 IR 权威），且无身份锚（违 Manifest 权威）。**净效果：用身份层做语义，且没有身份**（FACT-038）。
- **IMPLEMENTATION GAP**：V3-G2（IR 消费）+ V3-G3/G4（身份锚）。均 `not started`。
- **UNKNOWN**：IR loader 与身份绑定的实现排期（五步序无对应步骤）。

### Part 2 — 生产/消费责任边界
- **DECISION**：DSH 生成/计算/保证；V3 验证/重算/接受或拒绝。原则「Preprocessing 解释，V3 裁决」。
- **OBSERVED**：V3 侧 6 项义务（验证 Manifest / 重算 hash / 判断接受 / 验证 IR / Gate / 拒收）**全部未实现**（§3.2 N-3/N-4）。同算法对账生产侧 71/71 已实证可行。
- **IMPLEMENTATION GAP**：V3-G1（Manifest 三项）+ V3-G2（IR 三项）。
- **UNKNOWN**：source bytes 对 V3 的交付形态（OQ-12，与 DSH G-4 同源）。

### Part 3 — Scope（87 / 71）
- **DECISION**：Interface Scope = 87；IR Consumption Scope = 71 ADMITTED；二者允许不同；三禁（禁强制生成 IR / 禁删 identity 文件 / 禁改历史数据）。
- **OBSERVED**：V3 无法识别接口面（`identity_version` 0 命中），IR 零消费。字段口径 87 / 目录口径 88 / 全语料 166 / v1 legacy 79。
- **IMPLEMENTATION GAP**：V3-G5（接口面识别过滤）。
- **UNKNOWN**：接口面 87 的承载物形态（DSH G-3 / C.1，与五步序 Step 1 同题）。

### Part 4 — 16 份 Identity-only = 正常态
- **DECISION**：Identity Available / Semantic Unavailable 属正常；三禁（禁自动补 IR / 禁 LLM 猜测 / 禁静默入题库）；重生成 IR = 另行批准。**关闭 OQ-14 + DSH D-2**。
- **OBSERVED**：这 16 份已在接口面内，靠身份自足成立（DEC-B1「身份不依赖 IR」一致）。V3 无身份/语义分离消费能力。
- **IMPLEMENTATION GAP**：V3-G6。
- **UNKNOWN**：接口面是否设 semantic availability 呈现字段（OQ-21 / DSH G-6）。

### Part 5 — Semantic Unknown 处理
- **DECISION**：三禁令；保留事实状态进 `UNKNOWN` 语义状态；**不合并两状态体系**；UNKNOWN 属语义层。**关闭 OQ-5（不合并）**。
- **OBSERVED**：V3 三禁全违反（洗白/fallback/静默 skip，一条链三切面）；`SEMANTIC_STATUS` 无 `unknown` 取值（冻结 2 值）；非 ready 不可达决策层。
- **IMPLEMENTATION GAP**：V3-G8（语义层加 unknown，须解冻 BUG-V3-018）+ V3-G9（整链显式隔离）+ V3-G10（决策可达通道）。
- **UNKNOWN**：语义 UNKNOWN → 决策 PENDING_REVIEW 的路由架构（**OQ-19**）；PENDING_REVIEW → REJECTED 规则文本（OQ-16）；语义/决策两层载体（字段名/落点）。

### Part 6 — Contract v0.2 冻结范围
- **DECISION**：v0.2 只冻结三件（Identity / Scope / Semantic Boundary）；六类暂缓（DB 字段设计 / UI / 自动补全 / IR 扩产 / 图片恢复 / daemon 策略）。
- **OBSERVED**：V3 侧对三件的实现全部 `not started`；六类暂缓项 V3 均未涉及（不属本契约）。
- **IMPLEMENTATION GAP**：三件各有 V3 侧缺口（V3-G3/G4 = Identity；V3-G5 + IR 消费 = Scope；V3-G7/G8/G9/G10 = Semantic Boundary）。
- **UNKNOWN**：`source_version_id` 格式细节（裸 hex DSH 建议，PROPOSED 未裁）；三件的字段落点。

---

## §7 跨侧观察（只登记，不裁决）

1. **DEC 撞号累积至 2 处**（§1.1）：DSH DEC-021/022 ≠ V3 DEC-021/022。本轮 V3 用 DEC-027 ≡ DSH DEC-022。**须 Owner 定跨仓编号约定**，否则每轮新增。
2. **`source_version_id` 同名异义**（§1.2，本轮新登记，比 DEC 撞号更危险）：preprocessing sha256 hex vs V3 UUID FK，类型语义均不同。契约措辞必须消歧（OQ-20）。
3. **OQ-5 关闭的两面性**（§4）：Part 5 关闭了「合并 vs 不合并」（= 不合并），但**打开了两个更具体的 V3 缺口**——语义层缺 `unknown` 取值（须解冻 BUG-V3-018，OQ-20）、unknown→PENDING_REVIEW 不可达（OQ-19）。关闭一个开放项，换来两个更精确的实现前置。
4. **E1 残留冲突未因本轮消解**（承接 v1 §5.2 / OQ-18）：DSH Dependency Map 边表 E1 仍写「契约冻结 → 回填」，方向与 DEC-026 五步序（回填 → 契约冻结）相反。本轮 Interface Decision Finalization v1 未触及该冲突，**仍须 Owner 裁**。
5. **两侧 Gap 表互补**：V3 侧 V3-G1~G10（消费能力）+ DSH 侧 G-1~G-7（生产载体）。Part 2 的「V3 重算 hash」义务**横跨两侧**——DSH G-4（source bytes 可达）是 V3-G1 的前置。

---

## §8 边界声明

**本文件做了**：Owner Interface Decision Finalization v1（Part 1–6 + 最终原则）的 V3 消费侧对齐——事实基线（§2，Part 7.1）· V3 实现检查符合/不符合/需未来实现（§3，Part 7.2）· 语义层归属后果 OQ-5 关闭 + OQ-19/OQ-20 新登记 + OQ-14 关闭（§4）· Implementation Gap 表 `| Decision | Current | Gap |`（§5，Part 7.4）· 逐裁决四段（§6）· 跨仓 DEC 撞号与 `source_version_id` 同名异义登记（§1/§7）。每条带 commit hash + 文件路径 + 行级证据。

**本文件没做**：未修改任何 V3 代码 / adapter / 数据库 schema / EB-008 / admission 逻辑；未修改 preprocessing；未执行任何数据动作（清洗 / 迁移 / IR 重生成 / 图片恢复均未启动）；未冻结任何契约；**未把任何 DECISION 描述为已实现**（全部 `not started` / `UNKNOWN`）；未替 DSH 决定生产侧实现；未提案任何未裁事项的形态（OQ-19/20/21 仅登记）。

**与 DSH Producer Alignment v4 的关系**：并行产出，事实互不覆盖——DSH 陈述生产侧（G-1~G-7），本文件陈述消费侧（V3-G1~G-10）。两侧共同引用 ODR v1.3 为唯一裁决来源；`source_version_id` 可达性（DSH G-4 ↔ V3-G1）、接口面承载物（DSH G-3 ↔ V3-G5）、semantic availability 呈现字段（DSH G-6 ↔ OQ-21）三处**横跨两侧，须 v0.2 一并落字**。

---

*v2 · 2026-09-16 · Claude（AITutors-v3 Consumer Owner）。裁决基准 = ODR v1.3 §1quater；V3 代码基线 `b5ddbe3`（其后仅文档提交，代码未变）· preprocessing `22bf8b1`（+ DSH 并行未提交工作树：ODR v1.3 / Producer Alignment v4 / Interface Facts v2.1）。Contract v0.2 同批升 Frozen Candidate（DRAFT / NOT FROZEN）。如有文字冲突，以 Owner 原文为准。DECISION ≠ IMPLEMENTATION。*
