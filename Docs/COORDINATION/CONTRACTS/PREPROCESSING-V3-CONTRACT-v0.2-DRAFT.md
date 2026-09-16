# Preprocessing Integration Contract v0.2 — DRAFT（Frozen Candidate）

> **状态**：**DRAFT（冻结候选 / Frozen Candidate）。NOT FROZEN。** 待 Owner 冻结令（五步序 Step 3，前置 = Step 1 接口快照 + Step 2 `source_version_id` 回填）。**v0.2 冻结范围 = 三件**（见 §0），其余暂缓。
> **定位**：AITutors-preprocessing（producer）→ AITutors-v3（consumer）的跨项目输出契约。**本版职责 = 冻结 V3 消费边界**。
> **上游**：v0.1 DRAFT @ `1fbaf5e`（本版取代其 §1/§2/§3 相关条款；未提及处继承 v0.1）；Owner B1/B2/B3（DEC-019 / DEC-020~022）+ DEC-B1 细化（ODR §1bis）+ CONTRACT-DECISION-FINALIZATION v1 四项（V3 `DEC-023`~`026` ≡ DSH `DEC-021-1`~`4`）+ **Interface Decision Finalization v1（ODR v1.3 §1quater；V3 `DEC-027` ≡ DSH `DEC-022`，Part 1–6 + 最终原则）**；V3 侧事实基线 + **Consumer Alignment v2**（同批）；producer 侧 = Interface Facts v2.1 + Readiness v3 + **Producer Alignment v4** @ preprocessing `22bf8b1`（含未提交工作树）。
> **本契约不做什么**：不定义 V3 内部实现（IR loader / 隔离通道 / hash 写入点归 V3 设计）；不替 DSH 决定生产侧实现（字段落点、清洗、守卫归 producer 域）；不修改任何代码 / adapter / 数据库 schema。
>
> **证据纪律**：每条款标 `DECISION`（Owner 裁决）/ `OBSERVED`（实测锚）/ `UNKNOWN`（无证据）/ `REQUIREMENT`（契约义务）。**DECISION ≠ 已实现**——实现状态见 §5.4 Implementation Status Table。
>
> **编号对照（跨仓，引用时必须双向标注）**：四项 FINALIZATION 裁决 V3 = `DEC-023`~`026` / DSH = `DEC-021-1`~`4`；本轮 Interface Decision Finalization v1 = V3 `DEC-027` / DSH `DEC-022`。**撞号累积 2 处**：DSH `DEC-021`≠V3 `DEC-021`(B2)；DSH `DEC-022`≠V3 `DEC-022`(B3)。见 Consumer Alignment v2 §1.1。**另：`source_version_id` 同名异义**（preprocessing sha256 hex vs V3 内部 UUID FK，§1.3 / OQ-20）。

---

## §0 v0.2 Frozen Candidate 冻结范围（`DECISION`，DEC-027 Part 6）

> Owner 裁定 v0.2 **只冻结三件**。本节是冻结范围的权威界定——**冻结仅及于此三件**，其余均为暂缓或支撑材料。

### 0.1 冻结内容（三件，binding）

| # | 冻结项 | 内容 |
|---|---|---|
| **① Identity** | `source_version_id = SHA256(original source bytes)` | 跨系统身份键 = 源文件原始字节 SHA-256；id 即 sha 值（§1.2/§2.1） |
| **② Scope** | Manifest **87** / IR **71** snapshot | Interface Scope = 87（字段口径）；IR 当前语义冻结面 = 71 ADMITTED（§1.6） |
| **③ Semantic Boundary** | `Unknown ≠ Ready`；Unknown 不得自动进入正式题库 | unknown semantic 保留事实态、不静默转换/fallback/skip、不 materialize（§3.2/§4） |

### 0.2 暂缓冻结（明确不属于 v0.2 interface contract）

数据库字段最终设计 · UI 展示 · 自动补全机制 · IR 扩产计划 · 图片恢复流程 · daemon 持续生产策略。

> 上述六类**不在本契约冻结范围**。本文件中涉及它们的内容仅为事实登记 / 开放项，**不构成 v0.2 承诺**。

### 0.3 语义边界的冻结口径（精确化，`DECISION` + `OBSERVED`）

冻结项 ③ 落字为**窄口径**：`Unknown ≠ Ready` + 三禁令 + 不 materialize。**四状态机词表（READY/INCOMPLETE/PENDING_REVIEW/REJECTED，DEC-025）是既定裁决，但不属 v0.2 冻结范围**——其 V3 表达层归属仍开口（语义层缺 `unknown` 取值 OQ-20 / unknown→PENDING_REVIEW 不可达 OQ-19）。冻结的是「Unknown 不等于 Ready、不得静默入题库」这条底线，不是完整状态机。

### 0.4 最终原则（Owner 原文，本契约自我约束）

> 文件身份由生产侧证明，系统侧验证。
> 文件内容由生产侧解释，系统侧裁决。
> 宁可缺少结构化数据，也不能制造未经确认的结构化数据。

---

## §0.5 生产与消费责任边界（`DECISION` + `REQUIREMENT`，DEC-027 Part 2）

**Owner 裁定**——固化原则：**Preprocessing 负责解释，V3 负责接受或拒绝解释。**

| 靠 | Producer（DSH） | Consumer（V3） |
|---|---|---|
| **Manifest** | 生成 Manifest / 计算 `source_version_id` / 保证字段正确 | **验证 Manifest / 重新计算 hash / 判断是否接受** |
| **IR** | OCR 后结构化 / LLM 语义解析 / 生成 IR | **验证 IR 是否符合契约 / Gate 判断是否进入正式题库 / 拒绝不符合的数据** |

**V3 侧义务现状（`OBSERVED`，全部未实现）**：验证 Manifest（无校验，`manifest_reader.py:52`）· 重算 hash（不读 producer sha，自算为 canonical_json 包裹非 raw bytes，`runner.py:71-73`）· 判断接受（无身份闸门，`identity_version` 0 命中）· 验证 IR / Gate / 拒收（零 IR 消费能力）。详见 Consumer Alignment v2 §2/§3。

**可执行前提（`UNKNOWN`，两侧同源）**：「V3 重算 hash」要求 source bytes 对 V3 可达；`source_file` 现为本机绝对路径跨机不可解析（OQ-12 / DSH G-4）。

---

## §1 Source Version

### 1.1 双层接口架构（`DECISION`）

正式生产接口 = **Manifest + IR 双层**：

| 层 | 角色 | 职责 |
|---|---|---|
| **Manifest** | **Source Identity Authority** | 承载源身份与标注事实；身份对账以本层为准 |
| **IR** | **Semantic Consumption Authority** | 承载结构解析 + provenance；语义消费以本层为准 |

两层必须通过明确 **`source_version_id`** 关联（`DECISION`）。

**语义消费方向（澄清）**：语义单元的消费流向 = **IR → V3**。这不改变 Manifest 的 Source Identity Authority 地位——身份对账面在 Manifest，语义消费面在 IR，二者经同一 `source_version_id` 对齐。两仓 DEC-019 / DEC-020 记录一致（preprocessing `b39b6da`；V3 `1243a7f`）。

**DEC-B1 细化（`DECISION`，ODR §1bis @ preprocessing `bbb5c70`）**：

> `source_version_id` 为双层**唯一关联键**；**V3 消费语义来自 IR，但 source 身份不依赖 IR 存在**。

生产侧保守义（DSH 解释，非裁决）：① manifest 的身份字段必须**自足**——任何一份入接口面的 manifest，其 `source_version_id` 可独立验证（当场重算 sha256(md 字节)），**不需要 IR 在场**；② IR 缺席（未扩产 / 拒收 / 未生成）**不使 manifest 身份失效**；③ 反向不成立：IR 的语义承载依赖 manifest 身份锚定。

**V3 消费侧后果（`REQUIREMENT`）**：V3 的身份对账路径**不得以 IR 存在为前提**；同时，V3 若要走 IR 语义消费，其前提仍是 manifest 侧先有 `source_version_id`。二者是**两条独立工作线**，不是先后依赖（当前两者均未开始，见 §5.4）。

**OBSERVED 现状（IF-v2 @ `b39b6da`，缺口登记，非本契约放宽）**：

- Manifest 层 **0/166** 携带任何 sha/hash 键，**0/166** 携带 `source_version_id`（IF-v2 §2.2，工件 `producer_interface_probe_v2.json.p1b`）——Source Identity Authority 当前**零身份字段**，缺的是字段不是能力（算法在库：`resolver_reference.py:52-53`）。
- IR 层有 `source_sha256`（源 md 原始字节 SHA-256），**71/71 自洽**（`ir.source_sha256` == 单元 `provenance.source_version` == 当前磁盘 md 原始字节 sha256，裁决当日复验零漂移，IF-v2 §3.2）；但无名为 `source_version_id` 的关联键。
- **双层当前唯一关联值 = `source_file` 绝对路径字符串值相等**（IF-v2 §2.1/§3.4）——路径关联，非 id 关联；且该路径为本机绝对路径（`D:\Project\Papers\...`），跨机不可解析（IF-v2 §2.1）。
- V3 当前只读 Manifest，IR 消费 = 0 命中（`Grep @ backend/`，V3 @ `b5ddbe3`）。
- **实现状态**：双层接口的字段落点属 producer 接口变更 + V3 新增消费能力，**均未开始**（§6 Implementation Status Table）。

### 1.2 source_version_id 定义（`DECISION` + `REQUIREMENT`）

**`source_version_id` = `SHA-256(original source bytes)`**，即源 OCR markdown 文件**原始字节**的 SHA-256（hex 小写 64 字符）。**id 的取值就是该 sha 本身**，不是另立的编号。

- Manifest 与 IR 的同源记录必须携带**同一** `source_version_id` 值。
- IR 现有 `source_sha256`（文件级，`resolver_reference.py:249`）与单元级 `provenance.source_version`（`:167`）**语义上就是这个值**，实证 71/71 与当前磁盘字节一致（IF-v2 §3.2）——IR 侧**无需改算法**，只需与 Manifest 侧对齐字段名/关联语义。
- Manifest 侧当前 **0/166** 携带该字段（IF-v2 §2.2）；producer 表态可提供，但写入属数据变更，**须 Contract 冻结后按令执行**（Readiness §2.1 / IF-v2 §2.3）。
- producer 承载字段的命名与位置：`UNKNOWN`（DSH 域，本契约不指定实现）。
- **双语料注意（`OBSERVED`）**：OCR 清单的 `source_sha256` 钉的是 **PDF** 字节（IF-v2 §4.3，`r67_manifest_bootstrap.py:181`）——若 `source_version_id` 定义在 md 面，两者语义不同，**不可混用**。OCR 清单是否纳入本接口 = 开放项（§7 OQ-10）。

### 1.3 V3 侧对应关系（`REQUIREMENT`）——`source_version_id` 同名异义警告

**契约键与 V3 内部键同名、异义、异类型（`OBSERVED`，本轮升格登记，OQ-20）**：

| 概念 | 类型 | 语义 | 证据 |
|---|---|---|---|
| **契约 `source_version_id`**（本节/§2.1） | sha256 hex（64 小写） | `SHA256(raw bytes)` 跨系统身份键，id 即 sha 值 | §1.2；IR 侧 `ir.source_sha256` 71/71 同值 |
| **V3 内部 `source_version_id`** | `uuid.UUID` | `document_source_versions` 行主键 FK；Seal 层唯一性锚 `(logical_execution_stage, logical_execution_hash)`，**明令禁用 sha 作唯一**（`source.py:50`） | `models/source.py:44-57`；`snapshot_repository.py:42-45`；`runner_b2.py:158` |
| **V3 `Document.original_sha256`** | `String(64)` UNIQUE | BUG-V3-007 文档身份；概念对应「源内容 hash」 | `models/source.py:33,37` |

- **禁止**将 V3 内部 UUID 与跨系统 `source_version_id` 混用——二者不可互认。当 manifest 未来补上 sha256-hex 形态的 `source_version_id`，V3 schema 已有同名 UUID 列，**命名/类型直接冲突**，v0.2 落字须消歧（OQ-20）。
- V3 必须以 §2.1 定义的 raw bytes sha 作为跨系统对账值；V3 内部 UUID ↔ 跨系统 sha 的绑定发生在 ingest，绑定关系可离线重建。
- **OBSERVED 缺口**：consumer 路径写入 `documents.original_sha256` 的值是 canonical_json 包裹 joined-text（`runner.py:71-73` `file_sha = sha256_hex(body_text)`；`hashing.py:60-62`），**不是** raw bytes sha——该绑定当前不成立。`IMPLEMENTATION: not started`。

### 1.4 Immutable（继承 v0.1 §1.2，`OBSERVED`）

sha 一经发布，对应文件字节冻结；任何内容变更必须产生新 sha = 新 source_version。保障机制：producer Input Integrity Gate + Audit Snapshot（INTERFACE FACTS v1 §1 S5 @ `17c55d8`）。

### 1.5 Version 关系（继承 v0.1 §1.3，`OBSERVED`）

producer 当前不产出 version→version 关系指针。跨版本 lineage 属开放项（§6 OQ-1）。V3 不得假设「旧版本权威可迁移到新版本」。

### 1.6 Interface Scope（`DECISION`，取代原「覆盖面与接口面口径」）

**Owner 裁定（DEC-023 ≡ DSH DEC-021-1，FINALIZATION v1 Decision 1）**：

> Interface Scope = **v2 standard interface set**, Current size = **87 records**。
> **Manifest interface scope: 87** / **IR semantic consumption current frozen scope: 71 ADMITTED records**。
> 166 = 全部历史资产规模，不等于正式接口；87 = 当前正式接口范围；71 = 当前已生成 IR 的 semantic consumption 面，不代表完整 interface。

**identity 面双口径（`OBSERVED`，IF-v2 §2.4）**——裁决采纳**字段口径**：

| 口径 | v2 面 | v1 面 | 判定依据 |
|---|---|---|---|
| **字段口径**（`identity_version == "2"`）← **接口面锚定此口径** | **87** | 79 | IR 生成器与 C-IN-1 实际判定口径 |
| 目录口径（reslice-batch-C / pac-annotated / resliced-pilot） | 88 | 78 | 目录位置 |

差 1 实例 = `resliced-pilot\高一\化学\2021北京三十一中…manifest.json`（位于 v2 目录但 `identity_version=null`，IR 中 disposition = `REJECTED_V1`）。

**接口面（`REQUIREMENT`，由上述 DECISION 落字）**：Manifest 作为 Source Identity Authority 的接口面 = **字段口径 87 份**，不是目录口径 88，更不是 166。

**IR 消费面（`DECISION` + `OBSERVED`，IF-v2 §3.1/§3.4）**：IR = 88 记录 / **71 ADMITTED**（1,664 单元）/ 17 拒收（16 QC_FAIL + 1 REJECTED_V1）。对字段口径 v2 面 87 的覆盖 = 71/87；对全语料 166 = 43.4%。IR 是 R52 **一次性冻结工件**，无持续产出机制。**IR 作为 Semantic Consumption Authority 的当前冻结面 = 71 份 ADMITTED**。扩产机制 **未裁**（OQ-11）。

**87 的「表达」缺口（`OBSERVED`，两侧一致）**：生产侧现状**无任何文件级接口面清单工件**——87 是探针口径（`identity_version=="2"` 字段过滤）算出的集合，不是已发布的接口 manifest（DSH Producer Alignment §A.3 / C.1）。V3 侧 `identity_version` **代码 0 命中**，**无法识别接口面**（Consumer Alignment §4.1 D1-G2）。`IMPLEMENTATION: not started`。

**16 份 Identity-only = 正常态（`DECISION`，DEC-027 Part 4；关闭 OQ-14）**：接口面 87 中有 **16 份**（87−71）**无 IR 语义承载**。Owner 裁定此为**正常状态**——**Identity Available / Semantic Unavailable**：不得自动补 IR / LLM 猜测生成 / 静默进入题库；是否重新生成 IR = 另行批准。**不再是接口未声明空档**（v1 轮的「语义覆盖悬崖 OQ-14」就此关闭；DSH 侧同批关闭 D-2）。双层落地后这 16 份在身份面内、语义面外，V3 应完成身份对账但不进入语义消费（V3 无此分离能力，Consumer Alignment v2 §4.3）。接口面是否设 semantic availability 呈现字段 = 未裁（OQ-21 / DSH G-6）。

### 1.7 Legacy v1 Handling（`DECISION`，DEC-024 ≡ DSH DEC-021-2）

**Owner 裁定（FINALIZATION v1 Decision 2）**：

> v1 legacy 数据：**status = historical asset, not part of v0.2 interface**。规模 = **79**。
> 禁止：**自动迁移 / 自动补齐 / 自动重新生成 IR / 自动加入 87 接口**。
> 未来如需处理：单独建立 **Legacy Migration Plan**，**不得混入当前 Contract**。

**OBSERVED 现状**：

- producer 侧 C-IN-1（`identity_version < 2` → `REJECTED_V1`）**已实现**（IR 生成时拒收，`resolver_reference.py`）；79 份自 R52 后未被触碰，零自动迁移 / 零补齐 / 零 IR 重生成已发生（DSH §A.5）。
- **V3 侧 `identity_version` 与 `C-IN-1` 均代码 0 命中**——「v1 不入接口」目前由生产侧**单边**执行，消费侧无对应闸门。若一份 v1 legacy manifest 被送入 V3，V3 **会照常消费**（Consumer Alignment §4.2 D2-G1）。

**措辞精度（权威记录）**：既有 V3 文档（Gap Map / Blocker Analysis / 本文件旧 §1.6）写「79 份 v1 在 C-IN-1 下必被拒收」——该表述**对 producer/IR 面成立，对 V3 消费面不成立**。精确形态：C-IN-1 是 **producer 侧已实现、V3 侧未实现**的不变量。

**`REQUIREMENT`**：本契约的接口面不含 v1 legacy；其披露形态（仅规模 vs 路径清单）= 起草面开放项（OQ-15）。任何 legacy 迁移动作**不属本契约**，走独立 Legacy Migration Plan。

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
| `body_hash` | V3 内部（producer 零产出） | `source_loader.py:43-46`；`line_index.py:70-72`；IF-v2 §4.2（全语料探针 0 命中复验） |
| `line_hash` | V3 内部（producer 零产出） | `source_loader.py:38`；`line_index.py:75-90`；IF-v2 §4.2 |
| `integrity_hash` | V3 内部（consumer 路径退化 = body_hash） | `runner.py:93`；`line_index.py:93-108` |
| `norm_sha256` | producer 审计内部（NORM_ALGO = NFC + 换行归一 + rstrip + strip，`r64_data_inventory.py:61`），从未作接口发布 | IF-v2 §4.2 |
| `corpus_sha256` | producer 审计内部（集合级摘要，非单源身份） | IF-v2 §4.2；`audit_integrity.py:134` |

**OBSERVED 现状**：producer 输出面的 source identity 就是 raw bytes SHA-256，**无第二算法、无歧义**（IF-v2 §4.1：md `resolver_reference.py:52-53` + PDF `r67_manifest_bootstrap.py:181`，双语料单点生产）；`body_hash`/`line_hash`/`integrity_hash` producer 零产出。**B2 在 producer 侧已 READY，零动作**（Readiness §4）。本条款将上述 hash 正式限定为内部用途。

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

**canonical 闭集（`REQUIREMENT`）** = `{standalone_question, composite_question}`。**unit_type 必须闭集**——值域外任何值均属违规输入。

**四状态机词表（`DECISION`，DEC-025 ≡ DSH DEC-021-3，FINALIZATION v1 Decision 3）**——系统必须明确区分：

| 状态 | Owner 定义 |
|---|---|
| **READY** | semantic annotation 完整、unit_type 合法、可进入后续消费 |
| **INCOMPLETE** | 输入不足（缺 stem、缺必要字段等） |
| **PENDING_REVIEW** | 系统无法安全判断（unknown unit_type、semantic ambiguity、多种解释均可能） |
| **REJECTED** | 明确违反接口要求 |

**该四值词表取代 DEC-022 / DEC-019 的「UNKNOWN/PENDING」泛称。引用 B3 语义边界时以四值为准。**

**unknown `unit_type` 处理（`DECISION`）**——三条禁令 + 强制路由：

1. **禁止 automatic conversion**（不得将未知值改写为闭集内值）。
2. **禁止 silent fallback**（不得按默认分支处理未知值）。
3. **禁止 silent skip**（不得以 incomplete/skip 等路径无声吞掉未知值——真实原因必须显式可见）。
4. **不得进入 Question materialization**（不产 candidate / leaves）。

**强制路由（`DECISION`）**：任何 unknown semantic **必须进入 PENDING_REVIEW 或 REJECTED**，**由明确规则决定**。

> **规则文本本身未给（`UNKNOWN`，OQ-16）**——本契约只落「必须二选一 + 由明确规则决定」这一条，PENDING_REVIEW → REJECTED 的具体路由规则内容待 Owner。

**V3 侧表达缺口（`OBSERVED`，本轮结构发现，Consumer Alignment §2）**：四个状态词在 V3 分布在**两个互相正交、各自冻结**的值域里——READY/INCOMPLETE 落 `SEMANTIC_STATUS`（`compile/__init__.py:28-29`，冻结 BUG-V3-018）；PENDING_REVIEW/REJECTED 落 `DECISION_STATUS`（`gate/__init__.py:10-11`，冻结 10 §5.2）。且 `decision_status` 只存在于 candidate，candidate 只由 **ready 单元**产生（`runner_b2.py:231-264`）——**非 ready 单元永远进不了 PENDING_REVIEW / REJECTED**。

**Part 5 后果（`DECISION`，DEC-027 Part 5；关闭 OQ-5 核心）**：Owner 已裁——**不要合并 `semantic_status` 与 `decision_status` 两个状态体系**；**UNKNOWN 属于语义层**。故 v1 轮的 OQ-5「逻辑词表 (a) vs 单一状态机 (b)」**已关闭 = 不合并**（否定 (b)）。两体系并存不互斥（与 DSH v4 §B.5 一致：四状态机 = 决策层词表；UNKNOWN = 语义层事实呈现）。

**但 Part 5 打开两个更精确的 V3 侧缺口（`OBSERVED`，本契约不预设形态）**：

- **（a）语义层缺 `unknown` 取值 → OQ-20**：`SEMANTIC_STATUS` 冻结于 `{ready, incomplete}`（`compile/__init__.py:28-29`，BUG-V3-018），**无 `unknown` 取值**。要让「UNKNOWN 属语义层」可表达，须加第三值 `unknown` → **须解冻 BUG-V3-018**。
- **（b）语义 UNKNOWN → 决策 PENDING_REVIEW 不可达 → OQ-19**：Owner 指定 unknown semantic 在决策层路由 PENDING_REVIEW，但 V3 的 candidate 只由 **ready** 单元产生（`runner_b2.py:231-264`），`decision_status` 只存在于 candidate——一个语义 `unknown`（非 ready）单元**永到不了 PENDING_REVIEW**。须 Owner 裁路由架构（解冻 candidate 闸门 / 管线外路由 / 其他）。

**净效果**：关闭一个开放项（OQ-5），换来两个更具体的实现前置（OQ-19/OQ-20）。

**OBSERVED 现状（V3 侧，全部违反上述禁令，实现未开始）**：

| 层 | 当前行为 | 证据 |
|---|---|---|
| 读取 | 硬取 `u["unit_type"]`，无闭集校验 | `manifest_reader.py:52` |
| annotation | 硬编码重写为 `"standalone_question"`（**违反禁令 1**） | `annotation_adapter.py:42`；`:101-104` |
| span | 未知值按原始值走 composite 分支（**违反禁令 2**） | `resolved_span_adapter.py:77-90`；`runner_b2.py:116-127` |
| 终态 | 静默 incomplete→skip，真实原因任何层不出现（**违反禁令 3**） | `runner_b2.py:232-239`；GAP-MAP §0 E-1 |

**禁令 4 符合度**：经由静默 skip 达成（Compiler 非 ready 不产 leaves，`compiler.py:72-73`）——**结果符合、路径不符合**（非显式 PENDING_REVIEW）。

**OBSERVED 现状（producer 侧，IF-v2 §5）**：全语料恰 1 例非标值（`andalone_question`，manifest 面与 IR 面同文件同单元 Q1）；**producer 链零守卫**——该值原样进入 ADMITTED IR（`resolver_reference.py:152` 逐字复制，无转换，但也无隔离）。producer 侧现状 = 「没有静默转换，但也没有进 PENDING_REVIEW」——裁决的隔离语义今天**双侧均无执行面**。

**存量对账（`OBSERVED`，与 DSH §B.3 一致）**：该 1 例在 IR 中 `disposition = ADMITTED`。按本节四状态机口径，其 `unit_type` 非法，**不应是 READY**。其在本契约下的呈现态属存量处置面——**`UNKNOWN`**（OQ-17）。

**落点设计（`UNKNOWN`）**：层归属已裁（不合并，UNKNOWN 属语义层，OQ-5 关闭）。**仍未裁**：语义层 `unknown` 取值的引入（须解冻 BUG-V3-018，OQ-20）· unknown→PENDING_REVIEW 路由架构（OQ-19）· 两层状态载体字段名/落点（producer 侧 manifest vs IR vs 双侧，Readiness §6 / DSH C.4）。本契约不指定。

### 3.3 噪声类级事实（`OBSERVED`）

schema 噪声不只 unit_type 一处：恰 1 例 `andalone_question` + 恰 1 例游离键 `explanation_lines_note`（value = null），均在 v2 可消费面内（INTERFACE FACTS v1 §1 @ `17c55d8`）。producer 链零值域守卫（`write_outputs` 原样落盘 → `resolver_reference.py:152` 逐字复制）。**producer 侧守卫属 DSH 域，本契约不指定。**

### 3.4 继承条款（v0.1 §2.1-2.4，`OBSERVED`）

单元级字段表、claim/span 绑定（行锚 `[start,end]`）、material ref 消费禁令、figure 行内相对路径引用——**继承 v0.1**，本版不改。`unit_id` 仍为 display alias，禁止作跨系统键（v0.1 §2.2；`evidence.py:28-29` AuthorityIdentity 用 claim_id 但经三元绑定）。

---

## §4 Failure Boundary

> V3 仓内自有原则：**三层状态不复用**——E ResolvedStatus ≠ IR.semantic_status ≠ gate_decision（`compile/__init__.py:9`）。本节与之一致：三种失败处置**各自独立，禁止混淆**。

### 4.1 四种处置（`DECISION` + `REQUIREMENT`，与 §3.2 四状态机对齐）

| 处置 | Owner 定义 | 何时使用 | 终态性质 |
|---|---|---|---|
| **READY** | semantic annotation 完整、unit_type 合法、可进入后续消费 | 闭集内 unit_type + 必需字段齐备 | 可 materialize（V3 `semantic_status = ready`，`compile/__init__.py:28`） |
| **INCOMPLETE** | 输入不足 | 必需 span 缺失 / choice 型无 options / composite 缺 material（`ir.py:216-230`） | 非 materialize（V3 `semantic_status = incomplete`，`compile/__init__.py:29`） |
| **PENDING_REVIEW** | 系统无法安全判断 | **unknown `unit_type`（§3.2 DECISION）**；semantic ambiguity；schema 值域越界（v0.1 §3.3-7 basis 闭集） | 待裁决、显式隔离、可审计（V3 `decision_status = pending_review`，`gate/__init__.py:11`；**当前仅 ready 单元可达**——缺口） |
| **REJECTED** | 明确违反接口要求 | producer `disposition ∈ REJECTED_*` / `qc_verdict = FAIL`；identity v1（C-IN-1，**仅 producer 侧已实现**，见 §1.7）；sha 不一致（§2.3） | terminal，无自动路径（V3 `decision_status = rejected`，`gate/__init__.py:11`） |

> 本表承接 §3.2 的四状态机词表。V3 侧四值分属两个正交冻结层、且非 ready 单元不可达决策层——见 §3.2「V3 侧表达缺口」。

### 4.2 禁止混用（`REQUIREMENT`）

**四者语义独立，禁止任何互相转换或代用。** 具体：

1. **unknown `unit_type` 不得报为 INCOMPLETE**——当前静默路径正是如此（真实原因被格式类错误掩盖，GAP-MAP §0 E-1）。必须走 PENDING_REVIEW 或 REJECTED。
2. **INCOMPLETE 不得转 REJECTED / PENDING_REVIEW**——结构缺失 ≠ 终态拒绝 ≠ 待裁决；incomplete 单元不产 leaves（`compiler.py:72-73`）但不判 rejected。
3. **PENDING_REVIEW 不得静默转 READY 或 REJECTED**——继承 v0.1 §3.3-8（C-FAIL-1）。
4. **REJECTED 人工放行必须走显式 Admission 记录**——继承 v0.1 §3.3-2（C-FAIL-2）。
5. **任何处置不得静默丢弃**——READY 之外的三者都必须留痕（可审计），禁止无记录的 skip。
6. **READY 不得在 unit_type 非法时被赋予**——存量 1 例 `andalone_question` 现为 ADMITTED，按本条属违规现状（OQ-17）。

### 4.3 OBSERVED 现状与缺口

| 事实 | 证据 |
|---|---|
| IR `semantic_status` 冻结值域 `{ready, incomplete}`——无 PENDING 取值 | `compile/__init__.py:28-29` |
| Gate `decision_status` 冻结值域 `{pending_review, approved, rejected}` | `gate/__init__.py:10-11` |
| `pending_review` 仅 ready 单元可达；非 ready 在 `runner_b2.py:232-239` 被 skip，进不了 pending 通道 | `runner_b2.py:231-264` |
| unknown unit_type 当前终态 = 静默 incomplete→skip（§4.2-1 违反） | GAP-MAP §0 E-1 |
| Admission fail-closed 执行中（EB-008 P1）——本契约不改其逻辑 | `admission.py:213-223`；EB-008 状态另册 |

**缺口**：PENDING_REVIEW 处置对 unknown `unit_type` **无可达通道**（D3-G1/G2；Consumer Alignment §2 结构发现：非 ready 单元不可达决策层）。`IMPLEMENTATION: not started`；落层设计 = `UNKNOWN`（OQ-5）。

### 4.4 继承条款（v0.1 §3.1-3.3，`OBSERVED`/`REQUIREMENT`）

- 必须提供字段清单、允许为空清单、消费禁令（unresolved 答案槽位禁止静默默认）——继承 v0.1 §3.1-3.2。
- 必须阻断清单中 1/2/4/5/8 项继承；第 3 项（sha 不一致）按 §2.1 raw bytes 口径重述；第 6 项（unit_type 越界）按 §3.2/§4.1 升格为 **PENDING 处置要求**；第 7 项（basis 闭集）维持 PENDING_REVIEW。

---

## §5 V3 消费边界（本版冻结面）

> 本节是 v0.2 的**核心冻结候选**：V3 消费侧承诺与禁止。producer 侧实现归 DSH 域，不在本节。

### 5.1 V3 承诺（`REQUIREMENT`）

**Part 2 六项消费义务（DEC-027 Part 2，本版新增）**：

1. **验证 Manifest**（读取校验：字段完整 + `unit_type` 闭集）· **重新计算 hash**（raw bytes sha 对账）· **判断是否接受**（不一致 → 拒收）。
2. **验证 IR 符合契约** · **Gate 判断是否进入正式题库** · **拒绝不符合的数据**。

**既有承诺（承接 B1/B2/B3 + FINALIZATION）**：

3. 跨系统 source identity 只认 `SHA-256(raw bytes)`（§2.1）；内部 hash 不作跨系统用（§2.2）；**对账不以 IR 存在为前提**（§1.1 DEC-B1）。
4. unknown `unit_type` 不自动转换、不静默 fallback、不静默 skip、不 materialize；UNKNOWN 属语义层、保留事实态（§3.2，DEC-027 Part 5）。
5. `Unknown ≠ Ready`；Unknown 不得自动进入正式题库（§0 冻结项 ③）。
6. 只消费 **Interface Scope = 87** 内的 manifest（§1.6）；v1 legacy 79 不入接口（§1.7）；16 份 Identity-only 完成身份对账但不语义消费（§1.6 / DEC-027 Part 4）。
7. `unit_id` 不作跨系统键；claim 身份经 AuthorityIdentity 三元绑定（`evidence.py:28-29`，EB-008 既有设计，本契约不改）。

> **实现状态**：上述 1-7 **全部未实现**（§5.4 / Consumer Alignment v2 §5）。本节是冻结候选的**义务面**，不是现状描述。

### 5.2 V3 禁止（`REQUIREMENT`）

1. 禁止将 V3 内部 UUID `source_version_id` 与跨系统 sha `source_version_id` 混用或互认（§1.3，同名异义，OQ-20）。
2. 禁止用 canonical_json / body_hash / line_hash / integrity_hash 替代 source identity（§2.2）。
3. 禁止 unknown unit_type 的任何自动映射、静默 fallback 或静默 skip（§3.2/§4.2）。
4. 禁止合并 `semantic_status` 与 `decision_status` 两个状态体系（DEC-027 Part 5，OQ-5 已裁不合并）。
5. 禁止消费 Interface Scope 外的 manifest（含 v1 legacy 79）而不显式拒收（§1.6/§1.7）。
6. 禁止为对齐 87/71 数字而强制生成 IR、删除 identity 文件、或修改历史数据（DEC-027 Part 3 三禁）。
7. 禁止把 INCOMPLETE 报为 PENDING_REVIEW / REJECTED，或反向代用（§4.2-1/2）。
8. 禁止 unresolved 答案槽位静默默认（继承 v0.1 §3.2 特别条款）。

### 5.3 Decision Alignment Table（`DECISION` / `OBSERVED` / `UNKNOWN` 对照，DA-1~26）

> 每行 = 一项裁决要求。**DECISION** = Owner 架构选择 · **OBSERVED** = 实测现状 · **UNKNOWN** = 无证据不推断。DA-1~12 = B1/B2/B3；DA-13~20 = FINALIZATION v1 四项（DEC-023~026）；DA-21~26 = Interface Decision Finalization v1（DEC-027）。

| # | 裁决要求（DECISION） | OBSERVED 现状 | UNKNOWN |
|---|---|---|---|
| DA-1 | Manifest = Source Identity Authority（双层之一） | manifest 0/166 携任何 sha/hash 键，0/166 携 `source_version_id`（IF-v2 §2.2）；缺字段非缺能力 | producer 承载字段命名/位置 |
| DA-2 | IR = Semantic Consumption Authority（双层之一）；语义消费方向 IR → V3 | IR 71/71 sha 自洽零漂移；覆盖 88 记录/71 ADMITTED/1,664 单元；R52 一次性冻结工件无持续产出（IF-v2 §3）；V3 IR 消费 = 0 命中 | IR 是否扩产、是否建持续产出机制 |
| DA-3 | 双层经 `source_version_id` 关联 | 当前唯一关联 = `source_file` 绝对路径字符串值相等（IF-v2 §3.4）；路径为本机绝对路径跨机不可解析 | `source_file` 是否改仓库相对路径 |
| DA-4 | `source_version_id` = `SHA-256(original source bytes)`（id 即 sha 值） | IR 侧 `source_sha256`/`provenance.source_version` 语义已符合（71/71）；Manifest 侧 0/166 | 回填范围 87 vs 166（Readiness §6） |
| DA-5 | `body_hash`/`line_hash`/`integrity_hash`/`norm_sha256` 禁作跨系统 identity | producer 零产出（前三者）/ 仅审计内部（norm_sha256）；B2 producer 侧已 READY 零动作（Readiness §4） | V3 内部 hash 家族治理（line_hash 双算法 / integrity_hash 退化）是否进行 |
| DA-6 | unit_type 必须闭集 `{standalone_question, composite_question}` | v2 面 2,347 单元内恰 2 canonical 值 + 噪声 1 例；V3 `manifest_reader.py:52` 无闭集校验 | — |
| DA-7 | unknown unit_type 禁止自动转换 | `annotation_adapter.py:42` 硬编码重写 → **违反** | — |
| DA-8 | unknown unit_type 禁止 fallback | span 层未知值走 composite 分支 → **违反** | — |
| DA-9 | unknown unit_type 禁止静默 skip | 终态静默 incomplete→skip，真实原因任何层不出现 → **违反** | — |
| DA-10 | unknown unit_type 不得进入 Question materialization | skip 不产 candidate；Compiler 非 ready 不产 leaves → **结果符合**（经静默路径，路径不符合） | — |
| DA-11 | unknown unit_type 处理 = UNKNOWN/PENDING_REVIEW | 双侧均无执行面：V3 非 ready 进不了 `pending_review`；producer 链零守卫，值原样入 ADMITTED IR | 落点设计（V3 哪一层 / producer manifest vs IR 字段） |
| DA-12 | Failure boundary：REJECT / PENDING_REVIEW / INCOMPLETE 三者独立，禁止混用 | V3 仓内自有「三层状态不复用」原则（`compile/__init__.py:9`）方向一致；但 unknown→INCOMPLETE 混用当前存在（DA-9） | — |
| DA-13 | **Interface Scope = 87（字段口径）；IR 当前冻结面 = 71 ADMITTED**（DEC-023） | 字段口径 87 / 目录口径 88（差 1 混入件已 REJECTED_V1）/ 全语料 166；IR 消费面 = 71 ADMITTED；**两侧均无「接口面」承载物**：生产侧无清单工件，V3 侧 `identity_version` 代码 0 命中 | 87 的承载物形态；V3 如何识别接口面 |
| DA-14 | v1 legacy 79 = historical asset，不入 v0.2 接口；四禁；未来走独立 Legacy Migration Plan（DEC-024） | producer 侧 C-IN-1 已实现（IR 生成拒收）；**V3 侧 `identity_version`/`C-IN-1` 均 0 命中**——隔离由生产侧单边执行 | V3 是否需消费侧 identity 闸门；legacy 披露形态 |
| DA-15 | 四状态机词表 READY/INCOMPLETE/PENDING_REVIEW/REJECTED，取代 UNKNOWN/PENDING 泛称（DEC-025） | 四词分属**两个正交冻结层**：READY/INCOMPLETE ∈ `SEMANTIC_STATUS`（BUG-V3-018）；PENDING_REVIEW/REJECTED ∈ `DECISION_STATUS`（10 §5.2） | ~~逻辑词表 vs 单一状态机~~ **已裁不合并（OQ-5 关闭）**；语义层加 `unknown` 取值须解冻 BUG-V3-018（**OQ-20**） |
| DA-16 | unknown semantic 必须进 PENDING_REVIEW 或 REJECTED | 非 ready 单元**不可达**决策层（candidate 仅由 ready 产生，`runner_b2.py:231-264`）——裁决目标态对该类单元**当前不可满足** | 路由架构（**OQ-19**：语义 UNKNOWN→决策 PENDING_REVIEW 如何可达） |
| DA-17 | PENDING_REVIEW → REJECTED 路由「由明确规则决定」 | 规则文本**未给** | 规则内容（OQ-16） |
| DA-18 | 五步执行序：快照冻结 → 回填 → 契约冻结 → 数据治理 → 图片恢复（DEC-026） | 与交集定量零冲突（DSH Dependency Map v2.2 §4）；**五步均为数据/契约动作，零 V3 实现动作** | Step 1 快照载体与 R50 血统；V3 实现排期无对应步骤 |
| DA-19 | source identity 必须早于内容修改（身份冻结优先） | 87/87 接口面 manifest 均为 R50 成员 → 回填必致 R50 DRIFT，须配对再冻结（E2） | Step 1 快照如何承担配对角色 |
| DA-20 | 接口面 87 中 16 份无 IR 语义承载 | 双层落地后这 16 份在身份面内、语义面外；V3 今天能通过 manifest 消费它们 | ~~语义面地位~~ **已裁 = Identity Available / Semantic Unavailable 正常态（OQ-14 关闭）**；接口面呈现字段未裁（OQ-21） |
| DA-21 | **Part 1** 双层职责模型正式采用 + 双禁（Manifest 不代 IR 描述题目 / IR 不代 Manifest 证身份）（DEC-027） | V3 两个半边都不符——用身份层做语义消费、且无身份锚（FACT-038） | IR loader / 身份锚实现排期（五步序无对应步骤） |
| DA-22 | **Part 2** V3 验证 Manifest / 重算 hash / 判断接受（DEC-027） | 三项全无：无校验（`manifest_reader.py:52`）、不读 producer sha、无身份闸门（`identity_version` 0 命中） | source bytes 交付形态（OQ-12 / DSH G-4） |
| DA-23 | **Part 2** V3 验证 IR 符合契约 / Gate / 拒收；原则「Preprocessing 解释，V3 裁决」（DEC-027） | V3 零 IR 消费能力，语义消费全来自 manifest | IR loader 排期（五步序无此步骤） |
| DA-24 | **Part 3** 87/71 二者允许不同 + 三禁（禁强制生成 IR / 禁删 identity 文件 / 禁改历史数据）（DEC-027） | V3 无法识别接口面；IR 零消费 | 接口面 87 承载物形态（DSH G-3） |
| DA-25 | **Part 4** 16 份 Identity-only = 正常态（Identity Available / Semantic Unavailable）+ 三禁（DEC-027） | 这 16 份已在接口面，靠身份自足成立；V3 无身份/语义分离消费能力 | semantic availability 呈现字段（OQ-21 / DSH G-6） |
| DA-26 | **Part 5** 三禁令 + UNKNOWN 属语义层 + 不合并两状态体系（DEC-027） | V3 三禁全违反（洗白/fallback/静默 skip 一条链三切面）；`SEMANTIC_STATUS` 无 `unknown` 取值；非 ready 不可达决策层 | 语义层 unknown 取值引入（OQ-20）· 路由架构（OQ-19）· 载体字段名/落点 |

### 5.4 Implementation Status Table（`DECISION ≠ IMPLEMENTATION`）

| 契约义务 | 侧 | IMPLEMENTATION STATUS | 缺口 ID / 依赖 |
|---|---|---|---|
| Manifest 携带 `source_version_id`（0/166 → 回填，范围 = 87） | producer | **not started**（五步序 **Step 2**；前置 = Step 1 快照 + 字段名/格式裁决 OQ-8；须配对 R50 再冻结 E2） | B1-G1 / G1 / D4-G2 |
| 双层关联从路径升级为 `source_version_id` | producer | **not started**（同 G1） | B1-G2 / G2 |
| `source_file` 绝对路径 → 仓库相对路径 | producer | **not started**（待 v0.2 裁决） | OQ-12 |
| IR 覆盖扩产（71 → 更广） | producer | **not started**（须 Owner 令；扩产 = 新数据生成） | G3 / OQ-11 |
| IR 持续产出机制 | producer | **not started**（须 Owner 令，是否要未定） | G4 |
| unit_type 值域守卫（生成链） | producer | **not started**（B3 语义须先落字） | G5 |
| 存量 1 例 unit_type 修复 | producer | **deferred**（Owner 令：接口冻结优先；且破坏 R50 基线，须配对再冻结） | Readiness §5 D1 |
| V3 具备 IR 消费路径 | V3 | **not started**（0 命中） | B1-G3 |
| V3 绑定跨系统 sha（raw bytes 写入 `documents.original_sha256`） | V3 | **not started**（当前为 canonical_json 包裹值） | B1-G4 / B2-G1 |
| sha 对账闸门按 raw bytes 可执行 | V3 | **not started**（依赖上两项） | B2-G3 |
| unknown unit_type → PENDING_REVIEW / REJECTED | 双侧 | **not started**（当前静默 incomplete→skip / 零守卫） | D3-G1/G2 / G5 |
| 四状态机层归属 | — | **DECIDED = 不合并两状态体系**（DEC-027 Part 5，OQ-5 关闭）；语义层 `unknown` 取值引入 = **not started**（须解冻 BUG-V3-018） | OQ-20 |
| 语义 UNKNOWN → 决策 PENDING_REVIEW 可达通道 | V3 | **not started**；架构未裁（candidate 仅由 ready 产，非 ready 不可达决策层） | OQ-19 |
| PENDING_REVIEW → REJECTED 路由规则文本 | — | **UNKNOWN**（Decision 3 要求「由明确规则决定」，规则未给） | OQ-16 |
| 接口面 87 承载物（清单工件）发布供 V3 核验 | producer | **not started** | D1-G1 / DSH C.1 |
| V3 识别并只消费接口面内 manifest | V3 | **not started**（`identity_version` 代码 0 命中） | D1-G2 |
| 16 份 Identity-only 处理 | V3 | **DECIDED = Identity Available / Semantic Unavailable 正常态**（DEC-027 Part 4，OQ-14 关闭）；V3 身份/语义分离消费能力 = **not started** | OQ-21（呈现字段）/ Consumer Alignment v2 §4.3 |
| Step 1 接口快照载体形态 + R50 血统关系 | producer | **not started**（需 Step 1 执行令） | D4-G1 / DSH D.6 |
| `source_version_id` 字段名 / 格式 / md vs PDF 分层 | producer | **not started**（**未裁**，回填范围已裁 87） | D4-G2 / OQ-8 |
| v1 面 79 份处置 | producer | **DECIDED = historical asset 隔离**（DEC-024）；四禁；迁移走独立 Legacy Migration Plan | §1.7 / ~~OQ-6~~ **已关闭** |
| V3 消费侧 identity 版本闸门（与 producer C-IN-1 双边） | V3 | **UNKNOWN**（Owner 未下达 V3 实现设计） | D2-G1 |
| **V3 验证 Manifest + 重算 hash + 判断接受**（Part 2 三义务） | V3 | **not started**（无校验 / 不读 producer sha / 无身份闸门） | V3-G1 / Consumer Alignment v2 §2.1 |
| **V3 验证 IR 契约 + Gate + 拒收**（Part 2 三义务） | V3 | **not started**（零 IR 消费能力；语义消费仍来自 manifest） | V3-G2 / Consumer Alignment v2 §2.2 |
| V3 消费身份但不消费语义（16 份 Identity-only 分离消费） | V3 | **not started**（V3 无身份/语义分离能力） | V3-G6 |
| `source_version_id` 同名异义消歧（跨系统 sha vs V3 UUID） | 契约措辞 | **not started**（须 v0.2 落字） | OQ-20 |

### 5.5 Execution Ordering（`DECISION`，DEC-026 ≡ DSH DEC-021-4）

**Owner 裁定（FINALIZATION v1 Decision 4）**——所有数据动作必须遵循：

```
Step 1  Freeze interface snapshot
   ↓
Step 2  Generate / backfill source_version_id
   ↓
Step 3  Freeze Contract v0.2
   ↓
Step 4  Execute data hygiene
   ↓
Step 5  Execute image recovery / historical cleanup
```

**裁决理由（原文）**：source identity 必须早于内容修改。任何图片恢复 / OCR 修复 / markdown 修改都可能导致 content change → hash change → `source_version_id` invalid。**身份冻结优先。**

**与交集定量的兼容性（`OBSERVED`，DSH Dependency Map v2.2 §4）**：五步序与实测交集零冲突——Step 2 回填的 87 份全部为 R50 基线成员（E2 硬约束，由 Step 1 快照承担配对角色，其与 R50 的血统关系 = 执行令细化）；Step 5 图片恢复在排除模式下（排除 2 份三重成员）与接口面零交集（1,394 份）。

**残留不一致（`OBSERVED`，须 Owner 裁，Consumer Alignment §5.2）**：DSH Dependency Map 边表 **E1** 仍写「`v0.2 冻结 → G1b 回填`（字段未定义不得回填，硬治理）」——**方向与本节相反**。可能的调和：`source_version_id` 的**算法语义**已由 DEC-021/B2 裁定（= `SHA-256(raw bytes)`，id 即 sha 值），不依赖契约文档冻结；E1 的残留效力只在字段**名 / 格式**上（DSH C.2，未裁）。若 Step 2 以临时名/格式回填而 Step 3 契约后来改名，会产生二次回填。→ **须 Owner 在 Step 1 执行令或 v0.2 起草令中一并裁**（OQ-18）。

**V3 侧边界（`OBSERVED` + `UNKNOWN`，本轮明确登记）**：**五步序全部是数据 / 契约动作，不含任何 V3 实现动作。** V3 的 IR 消费能力（V3-I1）、身份绑定（V3-I2/I3）、四状态机通道（V3-S1）**在五步序中没有对应步骤**——**V3 侧实现排期 = UNKNOWN，且不因本裁决而获得排期**。本契约不提案为其插入步骤。

---

## §6 开放项

| # | 开放项 | 状态 |
|---|---|---|
| OQ-1 | source_version supersede/lineage 指针 | 未建（继承 v0.1） |
| OQ-2 | `unit_type` 值域闭集化 producer 侧守卫 | 未实施（DSH 域；G5，须 B3 语义先落字） |
| OQ-3 | 图片资产交付形态 | 继承 v0.1（当前仅行内相对路径；27,240 悬空已量化，FACT-034；恢复动作 D2 暂缓） |
| OQ-4 | basis 值域校验 producer 侧落地 | 未实施（期间 V3 自检，v0.1 §3.3-7） |
| OQ-5 | 四状态机在 V3 的层归属：(a) 跨两层逻辑词表 vs (b) 并成单一状态机 + producer 侧落点 | ~~未裁决~~ **核心已关闭（DEC-027 Part 5）= 不合并两状态体系**；由此细化为 OQ-19（可达性）+ OQ-20（语义层 unknown 取值） |
| OQ-6 | v1 面 79 份处置 | ~~未裁决~~ **已关闭（DEC-024 / §1.7）= historical asset 隔离，四禁，迁移走独立 Legacy Migration Plan** |
| OQ-7 | V3 内部 hash 家族治理（line_hash 双算法 / integrity_hash 退化） | 未裁决（G-4；DECISION 只限定不作跨系统 identity） |
| OQ-8 | producer 侧 `source_version_id` 承载字段命名 / 格式（裸 hex vs 前缀）/ md 面 vs PDF 面分层声明 | **未裁**（DSH 域；回填范围已裁 87，字段细节未裁；与 OQ-18 相关） |
| OQ-9 | 全语料 IR 是否/何时重新产出 + 是否建持续产出机制 | 须 Owner 显式令（G3/G4；暂停令 `746e35c` 生效中） |
| OQ-10 | OCR 清单（钉 PDF 字节）是否纳入双层接口 | 未裁决（IF-v2 §4.3；语义与 md 面不同，不可混用） |
| OQ-11 | IR 权威面承诺 | **部分已裁（DEC-023）**：当前冻结面 = 71 ADMITTED。**扩产机制仍未裁**（DEC-B1 已使其与身份面解耦，不阻塞冻结） |
| OQ-12 | `source_file` 绝对路径 → 仓库相对路径 | 未裁决（跨机解析；Readiness §2.2-2） |
| OQ-13 | 17 份拒收记录（16 QC_FAIL + 1 REJECTED_V1）在接口中的地位（披露 vs 排除） | 未裁决（Readiness §2.3-4；生产侧无偏好） |
| OQ-14 | **语义覆盖悬崖**：接口面 87 中 16 份无 IR 语义承载的地位 | ~~未裁决~~ **已关闭（DEC-027 Part 4）= Identity Available / Semantic Unavailable 正常态**（§1.6）；呈现字段细化为 OQ-21 |
| OQ-15 | legacy 79 的披露形态（v0.2 文字层：仅规模 vs 路径清单） | 未裁决（起草面） |
| OQ-16 | PENDING_REVIEW → REJECTED 的路由规则文本内容 | **未裁决**（Decision 3 要求「由明确规则决定」，规则本身未给） |
| OQ-17 | 存量 1 例 `andalone_question` 在四状态机下的呈现态与处置原子性 | 未裁决（涉 R50 成员 manifest + IR 冻结工件；DSH D.3 同源） |
| OQ-18 | **E1 残留冲突**：DSH Dependency Map 边表 E1（契约冻结 → 回填）与 Decision 4 五步序（回填 → 契约冻结）方向相反 | **未裁决**（本轮 Interface Decision Finalization v1 未触及；仍须 Owner 在 Step 1 执行令或 v0.2 起草令中一并裁） |
| OQ-19 | **语义 UNKNOWN → 决策 PENDING_REVIEW 可达性**：V3 candidate 仅由 ready 单元产生，非 ready（含语义 unknown）永到不了决策层——Owner 指定的路由在 V3 现架构下不可达 | **未裁决**（DEC-027 Part 5 关闭 OQ-5 后新登记；须 Owner 裁路由架构：解冻 candidate 闸门 / 管线外路由 / 其他） |
| OQ-20 | **`source_version_id` 同名异义消歧 + 语义层 `unknown` 取值引入**：(a) 跨系统 sha 键与 V3 内部 UUID 列共用一名（类型语义均不同）；(b) `SEMANTIC_STATUS` 加第三值 `unknown` 须解冻 BUG-V3-018 | **未裁决**（DEC-027 Part 5/6 后新登记；(a) 契约措辞消歧须 v0.2 落字；(b) 涉冻结值域解冻） |
| OQ-21 | **接口面是否设 semantic availability 呈现字段**：供 V3 Gate 直接读取「此 16 份 Identity Available / Semantic Unavailable」，而非 V3 自行靠 IR 面有无判断 | **未裁决**（DEC-027 Part 4 后新登记；DSH G-6 同源，横跨两侧须 v0.2 一并落字） |

---

## §7 与 v0.1 的差异

| 条款 | v0.1 @ `1fbaf5e` | v0.2 DRAFT |
|---|---|---|
| 消费载体 | 「V3 消费以 IR 为准」（`:33`） | **取代**：双层各有权威面 + 语义消费方向 IR → V3（§1.1/§3.1） |
| source identity | 隐含 sha = raw bytes，未禁其他 hash | **收紧**：显式唯一定义 + 禁止清单含 norm_sha256/corpus_sha256（§2.1/§2.2） |
| `source_version_id` | §4.2 声称「一一对应」但无载体 | **升格**：id = sha 值本身 + 双层同值 REQUIREMENT + 0/166 缺口登记（§1.2） |
| unknown unit_type | §3.3-6「隔离（PENDING 通道）」 | **收紧**：闭集强制 + 四条禁令（含禁静默 skip）+ 落点 UNKNOWN（§3.2/§4.1） |
| Failure Boundary | 分散于 §3.3 各项 | **集中**：三处置定义 + 五条禁止混用（§4） |
| 接口面口径 | 未定 | **升格为 DECISION**：Interface Scope = 87（字段口径）/ IR 当前冻结面 = 71 ADMITTED（§1.6，DEC-023） |
| legacy v1 面 | 仅 C-IN-1 拒收条款 | **新增 DECISION 节**：historical asset + 四禁 + 独立 Legacy Migration Plan 通道（§1.7，DEC-024） |
| semantic 状态词表 | 「PENDING 通道」泛称 | **升格**：四值 READY/INCOMPLETE/PENDING_REVIEW/REJECTED + 三禁令 + 强制路由（§3.2/§4.1，DEC-025） |
| 执行序 | 无 | **新增**：五步序（身份冻结优先）+ V3 侧无对应步骤声明（§5.5，DEC-026） |
| 身份自足性 | 无 | **新增**：source 身份不依赖 IR 存在（§1.1 DEC-B1 细化） |
| 语义覆盖悬崖 | 无 | ~~新增~~ **已裁**：16 份 = Identity Available / Semantic Unavailable 正常态（§1.6 / OQ-14 关闭，DEC-027 Part 4） |
| **责任边界** | 无 | **新增 §0.5**：Preprocessing 解释 / V3 接受或拒绝 + V3 六项消费义务（DEC-027 Part 2） |
| **冻结范围** | 无明确范围 | **新增 §0**：v0.2 只冻结三件（Identity / Scope / Semantic Boundary）+ 六类暂缓（DEC-027 Part 6） |
| UNKNOWN 语义层 | 无 | **新增**：UNKNOWN 属语义层、不合并两状态体系（§3.2，DEC-027 Part 5；OQ-5 关闭，OQ-19/20 新登记） |
| `source_version_id` 命名 | 仅「禁混用」 | **升格**：同名异义消歧警告 + 类型对照表（§1.3，OQ-20） |
| hash 行号 | — | 按 E-2 勘误（splitlines @ `source_loader.py:27`） |

---

## §8 冻结前提（本版不满足即不冻结）

> **结构变更（本轮，由 DEC-026 决定）**：Decision 4 把 **Contract v0.2 冻结放在五步序的 Step 3**，其前置 = Step 1（接口快照冻结）+ Step 2（`source_version_id` 回填）。因此冻结前提不再是「先冻结、实现后补」，而是**数据身份动作先行、契约冻结收口**。原「排期归属未裁」开放项**已由 DEC-026 关闭**（数据动作排期已裁）；V3 侧实现排期仍无对应步骤（§5.5）。

**冻结前置（Step 1 / Step 2 必须先完成）**：

1. **Step 1 接口快照冻结完成**——快照载体形态与 R50 血统关系有执行令（OQ / D4-G1；DSH D.6）。
2. **Step 2 `source_version_id` 回填完成**——范围 = 87（已裁）；字段名 / 格式 / md 面 vs PDF 面分层**须先裁**（OQ-8 / D4-G2）；回填与 R50 再冻结配对原子执行（E2）。
3. **OQ-18（E1 残留冲突）有裁决**——两侧文档不得长期并存两个相反方向的「硬约束」。

**冻结同期须落字（v0.2 正文内容）**：

4. Owner 批准本 DRAFT 作为冻结候选；冻结**范围 = §0 三件**（Identity / Scope / Semantic Boundary），六类暂缓项明确排除。
5. DSH 确认 producer 侧接口变更面（§1.1 Manifest 身份载体、OQ-8 字段命名、OQ-12 `source_file` 形态）——**本契约不替其决定**。
6. **OQ-20**（`source_version_id` 同名异义消歧：跨系统 sha 键 vs V3 内部 UUID 列共用一名）落字——否则冻结项 ① 的措辞有歧义。
7. **OQ-16**（PENDING_REVIEW → REJECTED 路由规则文本）有裁决。
8. **OQ-15**（legacy 79 披露形态）落字。
9. **OQ-21**（接口面是否设 semantic availability 呈现字段）有裁决——与 DSH G-6 同题，横跨两侧。

**不构成 v0.2 冻结前提（已关闭或不在范围）**：

- ~~OQ-5（四状态机层归属）~~ —— **已由 DEC-027 Part 5 关闭 = 不合并**；细化项 OQ-19/OQ-20 是**实现前置**，其中 OQ-20 落字见上 item 6，OQ-19 架构属 V3 实现设计、不阻塞契约冻结（§0.3 已明确四状态机不属 v0.2 冻结范围）。
- ~~OQ-14（16 份语义覆盖悬崖）~~ —— **已由 DEC-027 Part 4 关闭 = Identity Available / Semantic Unavailable 正常态**（§1.6）。
- ~~OQ-6（v1 面 79 份处置）~~ —— **已由 DEC-024 关闭**（historical asset 隔离）。
- ~~OQ-11（IR 权威面 71 vs 扩产）~~ —— **当前面已由 DEC-023 裁定 = 71 ADMITTED**；扩产机制未裁，但 DEC-B1 已使其与身份面解耦，**不阻塞冻结**（且 IR 扩产计划属 Part 6 暂缓项）。
- ~~排期归属~~ —— **已由 DEC-026 裁定**（数据动作五步序）。
- V3 侧实现（IR 消费能力 / 身份绑定 / 语义层 unknown 取值 / 决策可达通道）—— **不在五步序内**，不构成冻结前置；其实现排期 = UNKNOWN（§5.5 / Consumer Alignment v2 §3.3）。

---

## 边界声明

**本文件做了**：Owner B1/B2/B3 裁决的契约化（§1-4）+ DEC-B1 细化（§1.1）+ FINALIZATION v1 四项（§1.6/§1.7/§3.2+§4.1/§5.5）+ **Interface Decision Finalization v1 契约化（DEC-027 ≡ DSH DEC-022）**：新增 **§0 冻结范围（三件 + 六类暂缓）**、**§0.5 生产/消费责任边界（Part 2）**、§1.3 `source_version_id` 同名异义消歧、§1.6 16 份正常态（Part 4，OQ-14 关闭）、§3.2 UNKNOWN 语义层 + 不合并（Part 5，OQ-5 关闭，OQ-19/20 新登记）；V3 消费边界义务面（§5.1-5.2，含 Part 2 六项）；**Decision Alignment Table（§5.3，DA-1~26）** 与 **Implementation Status Table（§5.4）**；v0.1 差异对照（§7）；开放项 OQ-1~21 与冻结前提按 DEC-026 五步序 + DEC-027 Part 6 三件范围重写（§6/§8）。每条款标 DECISION/OBSERVED/UNKNOWN/REQUIREMENT。

**本文件没做**：未把 DECISION 描述为已实现（§5.4 全表 `not started` / `deferred` / `UNKNOWN`）；未替 DSH 决定生产侧实现；未修改 V3 代码 / adapter / 数据库 schema / EB-008 / admission 逻辑；未修改 preprocessing；未执行任何数据动作（Step 1~5 均未启动）；**未冻结本契约（DRAFT）**。

**EB-008 状态**：不因本文件变动。AuthorityIdentity 三元绑定（`evidence.py:28-29`）为既有冻结设计，本契约仅引用不改。

---

*v0.2 DRAFT（Frozen Candidate）— 2026-09-16，Claude（AITutors-v3 Consumer Owner）。V3 代码 `b5ddbe3`（其后仅文档提交，代码未变）· preprocessing `22bf8b1`（+ DSH 并行未提交工作树：ODR v1.3 / Producer Alignment v4 / Interface Facts v2.1）· Owner Decision Record **v1.3**（§1quater）· v0.1 `1fbaf5e`（未改）。**冻结范围 = §0 三件；状态 DRAFT / NOT FROZEN**。DECISION ≠ IMPLEMENTATION。*
