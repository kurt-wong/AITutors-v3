# Preprocessing Integration Contract v0.2 — DRAFT（Freeze Candidate，已收口 / Finalized）

> **状态**：**DRAFT（Freeze Candidate Finalized）。READY FOR FREEZE。NOT FROZEN。** **本轮 = Contract v0.2 Freeze Finalization Audit·Consumer 侧（V3 `DEC-033`）**：Task 1 冻结状态描述修正（Step 1/2 历史「未开始/未完成」表述 → 事实状态）· Task 2 Freeze Evidence 引用登记（§9）· Task 3 Freeze Object 明确化（§9.2，唯一冻结对象）· Task 4 关键词再验证（`source_version_id` / `source_content_sha256` / Semantic Unavailable / Semantic Pending / path / `source_file`）· Task 5 输出报告。**事实状态（DSH 已执行并验证，证据 = §9）**：**Step 1 接口快照 = DONE** · **Step 2 `source_content_sha256` 回填 ×87 = DONE** · **验证报告 = PASS**（71/71 Manifest hash = IR hash；87/87 == source bytes；C1-C9 最终复核 overall = VERIFIED）· **冻结条件（DEC-031 §六机械条件）= 已满足** → **READY FOR OWNER FREEZE**。**仍 NOT FROZEN**——冻结令属 Owner，尚未下达。**NOT IMPLEMENTED（V3 capability）**：五项消费端能力仍全部未实现（§5.6.1：Manifest identity verification / raw bytes acquisition / independent SHA256 verification / IR identity verification / identity gate）——契约冻结 = 裁决冻结，不是能力交付。**v0.2 冻结范围 = 六项冻结内容**（见 §0），其余暂缓；本轮**未扩展冻结范围**。
> **定位**：AITutors-preprocessing（producer）→ AITutors-v3（consumer）的跨项目输出契约。**本版职责 = 冻结 V3 消费边界**。
> **上游**：v0.1 DRAFT @ `1fbaf5e`；Owner B1/B2/B3（DEC-019/020~022）+ DEC-B1 细化（§1bis）+ CONTRACT-DECISION-FINALIZATION v1 四项（V3 `DEC-023`~`026` ≡ DSH `DEC-021-1`~`4`）+ Interface Decision Finalization v1（V3 `DEC-027` ≡ DSH `DEC-022`，Part 1–6）+ Interface Finalization Revision v1（ODR v1.4 §1quinquies；V3 `DEC-028` ≡ DSH `DEC-023`，Part 1–6）+ Freeze Candidate Review v1（V3 `DEC-029`：命名提案 + bytes 能力冻结 + 16 份四保证对齐）+ Freeze Candidate Finalization v1（V3 `DEC-030` ≡ DSH `DEC-025`：命名采纳 + 文字收口）+ **Owner Final Decision v1（V3 `DEC-031` ≡ DSH `DEC-026` 执行轮：四项原则终局确认 + Step 1/2 执行 + 机械冻结条件 + 五项延期）** + Contract v0.2 最终冻结收口 Consumer 侧（V3 `DEC-032`）+ **Freeze Finalization Audit（V3 `DEC-033`，本轮）**；producer 侧冻结收口 = DSH `DEC-027`（Freeze Evidence v1，commit `aad2237`）+ DSH `DEC-028`（Producer 最终确认，commit `67f564c`，含 F-1/F-2 两个 consumer 侧 WARNING——F-1 = 本契约缺证据工件引用与执行后状态注记，本轮 Task 1+2 修正；F-2 = 收口稿未提交，已由 V3 commit `c6e771c` 解决）。**producer 基线 commit = preprocessing `67f564c`**（Step 1/2/验证 = `e70807b`）。
> **本契约不做什么**：不定义 V3 内部实现；不替 DSH 决定生产侧实现；不修改任何代码 / adapter / 数据库 schema。
>
> **证据纪律**：每条款标 `DECISION` / `OBSERVED` / `UNKNOWN` / `REQUIREMENT`。**DECISION ≠ 已实现**——实现状态见 §5.4。接口键命名已裁（DEC-030）；`PROPOSAL` 类型本轮起不再使用（原提案已转 DECISION）。
>
> **编号对照（跨仓，引用时必须双向标注）**：四项 V3 `DEC-023`~`026` / DSH `DEC-021-1`~`4`；Finalization v1 = V3 `DEC-027` / DSH `DEC-022`；Revision v1 = V3 `DEC-028` / DSH `DEC-023`；Freeze Candidate Review = V3 `DEC-029`；Freeze Candidate Finalization = V3 `DEC-030` ≡ **DSH `DEC-025`（已登记）**；**Owner Final Decision v1 = V3 `DEC-031` ≡ DSH `DEC-026`（执行轮，已登记）**；冻结收口 Consumer 侧 = V3 `DEC-032`；Freeze Finalization Audit = V3 `DEC-033`（本轮）。**DSH 侧 producer 冻结收口** = DSH `DEC-027`（Freeze Evidence v1）+ DSH `DEC-028`（Producer 最终确认）。**撞号累积 3 处**：DSH `DEC-021`≠V3 `DEC-021`(B2)；DSH `DEC-022`≠V3 `DEC-022`(B3)；DSH `DEC-023`≠V3 `DEC-023`(Interface Scope)。见 Consumer Alignment v3 §1。**`source_version_id` 歧义已消除（DEC-030）**：跨系统接口键统一为 `source_content_sha256`（§1.2）；`source_version_id` 词面**专用化为 V3 内部 UUID FK**，不再表示跨系统身份键。**DEC-031 终局确认命名**：禁止任何系统以 path 作为唯一身份判断。

---

## §0 v0.2 Frozen Candidate 冻结范围（`DECISION`，DEC-027 Part 6 + DEC-028 Part 1–6 + DEC-029 + DEC-030 + DEC-031 终局确认）

> v0.2 冻结范围由 DEC-027 Part 6 的三件，经 DEC-028（Revision v1）扩为五项冻结原则，再经 DEC-029（Freeze Candidate Review）追加第⑥项 source bytes 能力冻结（Owner 原则 6：只冻能力、不冻传输），DEC-030（Finalization）确认接口键命名已采纳，**DEC-031（Owner Final Decision v1）对六项冻结内容终局确认**（Identity Authority / 双层职责 / 命名 / 16 份处理四项原则原文确认）。本节是冻结范围的权威界定——**冻结仅及于此六项**，其余均为暂缓或支撑材料。

### 0.1 冻结内容（六项，binding；接口键名 = `source_content_sha256`，DEC-030 已裁 + DEC-031 终局确认）

| # | 冻结项 | 内容 | 来源 |
|---|---|---|---|
| **① Identity** | 跨系统身份键 = `SHA256(original source bytes)`，**64 字符小写 hex**；**键名 = `source_content_sha256`** | 身份键 = 源文件原始字节 SHA-256；id 即 sha 值；身份由其唯一决定（§1.2/§2.1）；**内容 hash 决定身份，path 变化不得影响 identity，禁止任何系统使用 path 作为唯一身份判断（DEC-031 原文）**。`source_version_id` 词面专用化为 V3 内部 FK（§1.2a） | DEC-027 Part 6 + DEC-028 Part 1 + DEC-029 + DEC-030 Decision 1 + **DEC-031 原则 1 终局确认** |
| **② Scope** | Manifest **87** / IR **71** / **16 Semantic Pending** | Interface Scope = 87（不改 71）；71 = 当前 IR 语义消费；16 = 等待 semantic processing；禁「IR available = Interface available」（§1.6） | DEC-027 Part 6 + DEC-028 Part 4 |
| **③ Semantic Boundary** | `Unknown ≠ Ready`；Unknown 不入正式题库；unknown → reviewable record → pending_review | 语义层终局词表 `{ready,incomplete,unknown}` + 决策层 `{pending_review,approved,rejected}`，禁合并；禁 silent skip/convert/fallback（§3.2/§4） | DEC-027 Part 6 + DEC-028 Part 5/6 + DEC-030 Decision 3 确认 |
| **④ Path Non-Identity** | `source_file`/path = **locator**，非 identity | **Source identity belongs to content hash, not storage location.** 任何文档不得暗示 path 参与文件唯一/身份/版本/hash 判断；路径变化不得改身份键（§1.3） | DEC-028 Part 1/2 + DEC-030 Decision 1 + **DEC-031 原则 1 终局确认** |
| **⑤ Identity-only Recovery Rule** | 16 份 = Identity Available / **Semantic Pending**（可恢复） | 允许重生成 IR，四保证（bytes hash 不变 / identity 不变 / IR 版本可追踪 / 禁覆盖历史事实）；禁改原 source、禁新 identity、禁新 hash 替旧 hash（§1.6）。**DEC-031 终局确认 + 补充三禁**：不创建新 identity / 不修改历史 manifest / 不删除已有记录 | DEC-028 Part 3 + DEC-029 原则 3 + **DEC-031 原则 4 终局确认** |
| **⑥ Source Bytes Capability** | V3 **必须能获得 raw bytes 并重算身份键验证**（fail-closed）；**不冻结传输方案** | 能力 = binding（§2.3）：可得 bytes + 独立重算 SHA-256 比对 + 不一致即拒收 + 独立于 IR；传输 HOW（共享 FS/对象存储/IR 内嵌/相对路径）= 暂缓 | DEC-029 原则 6 + DEC-030 Decision 2 + **DEC-031 原则 2/3 终局确认** |

### 0.2 暂缓冻结（明确不属于 v0.2 interface contract）

数据库字段最终设计 · UI 展示 · 自动补全机制 · IR 扩产计划 · 图片恢复流程 · daemon 持续生产策略。

> 上述六类**不在本契约冻结范围**。本文件中涉及它们的内容仅为事实登记 / 开放项，**不构成 v0.2 承诺**。

**DEC-031 Owner 建议延期清单（非架构阻塞点，不阻塞冻结）**：

| 延期项 | 原因（Owner 原文） | 对应开放项 |
|---|---|---|
| legacy 79 份披露 | 不影响主链 | OQ-15 |
| 17 拒收记录 | 历史治理问题 | OQ-13 |
| OCR/PDF 扩展面 | 以后扩展 | OQ-10 |
| DEC 编号统一 | 文档管理问题 | 跨仓撞号 |
| bytes 传输方式 | 实现阶段再决定 | OQ-12″ |

### 0.3 语义边界的冻结口径（`DECISION`，DEC-028 Part 5/6 终局）

冻结项 ③ 落字：`Unknown ≠ Ready` + 三禁令（禁 silent skip/convert/fallback）+ 不 materialize + **unknown → reviewable record → pending_review workflow**。**两状态体系终局词表已裁**：语义层 `{ready, incomplete, unknown}` + 决策层 `{pending_review, approved, rejected}`，禁止合并（取代 DEC-025 四状态机的跨层合并记法）。**V3 侧表达仍未实现**——`SEMANTIC_STATUS` 冻结于 `{ready,incomplete}`（须解冻加 `unknown`，BUG-V3-018）；unknown→pending_review 在 V3 candidate-gated-on-ready 架构下无执行面。冻结的是词表 + 路由规则 + 底线，不是 V3 实现。

### 0.4 最终原则（Owner 原文，本契约自我约束）

> 文件身份由生产侧证明，系统侧验证。
> 文件内容由生产侧解释，系统侧裁决。
> 宁可缺少结构化数据，也不能制造未经确认的结构化数据。

---

## §0.5 生产与消费责任边界（`DECISION` + `REQUIREMENT`，DEC-027 Part 2）

**Owner 裁定**——固化原则：**Preprocessing 负责解释，V3 负责接受或拒绝解释。**

| 靠 | Producer（DSH） | Consumer（V3） |
|---|---|---|
| **Manifest** | 生成 Manifest / 计算 `source_content_sha256` / 保证字段正确 | **验证 Manifest / 重新计算 hash / 判断是否接受** |
| **IR** | OCR 后结构化 / LLM 语义解析 / 生成 IR | **验证 IR 是否符合契约 / Gate 判断是否进入正式题库 / 拒绝不符合的数据** |

**V3 侧义务现状（`OBSERVED`，全部未实现）**：验证 Manifest（无校验，`manifest_reader.py:52`）· 重算 hash（不读 producer sha，自算为 canonical_json 包裹非 raw bytes，`runner.py:71-73`）· 判断接受（无身份闸门，`identity_version` 0 命中）· 验证 IR / Gate / 拒收（零 IR 消费能力）。详见 Consumer Alignment v2 §2/§3。

**可执行前提（`UNKNOWN`，两侧同源）**：「V3 重算 hash」要求 source bytes 对 V3 可达；`source_file` 现为本机绝对路径跨机不可解析（OQ-12 / DSH G-4）。

---

## §1 Source Version

### 1.1 双层接口架构（`DECISION`）

正式生产接口 = **Manifest + IR 双层**：

| 层 | 角色 | 职责 |
|---|---|---|
| **Manifest** | **Source Identity Authority** | 承载源身份与标注事实；身份对账以本层为准。**Manifest 回答：「这是哪个文件？」（DEC-031 原则 2）** |
| **IR** | **Semantic Consumption Authority** | 承载结构解析 + provenance；语义消费以本层为准。**IR 回答：「这个文件表达了什么？」（DEC-031 原则 2）** |

**DEC-031 原则 2 终局确认**：V3 消费方向 = **Manifest 验证身份，IR 提供语义。两者不得混淆。**

两层必须通过明确 **`source_content_sha256`** 关联（`DECISION`；DEC-B1 原文写作 `source_version_id`，DEC-030 词面收口后统一为新名）。

**语义消费方向（澄清）**：语义单元的消费流向 = **IR → V3**。这不改变 Manifest 的 Source Identity Authority 地位——身份对账面在 Manifest，语义消费面在 IR，二者经同一 `source_content_sha256` 对齐。两仓 DEC-019 / DEC-020 记录一致（preprocessing `b39b6da`；V3 `1243a7f`）。

**DEC-B1 细化（`DECISION`，ODR §1bis @ preprocessing `bbb5c70`；引用词面已按 DEC-030 收口）**：

> `source_content_sha256` 为双层**唯一关联键**；**V3 消费语义来自 IR，但 source 身份不依赖 IR 存在**。

生产侧保守义（DSH 解释，非裁决）：① manifest 的身份字段必须**自足**——任何一份入接口面的 manifest，其 `source_content_sha256` 可独立验证（当场重算 sha256(md 字节)），**不需要 IR 在场**；② IR 缺席（未扩产 / 拒收 / 未生成）**不使 manifest 身份失效**；③ 反向不成立：IR 的语义承载依赖 manifest 身份锚定。

**V3 消费侧后果（`REQUIREMENT`）**：V3 的身份对账路径**不得以 IR 存在为前提**；同时，V3 若要走 IR 语义消费，其前提仍是 manifest 侧先有 `source_content_sha256`。二者是**两条独立工作线**，不是先后依赖（当前两者均未开始，见 §5.4）。

**OBSERVED 现状（IF-v2 @ `b39b6da`，缺口登记，非本契约放宽）**：

- Manifest 层 **0/166** 携带任何 sha/hash 键，**0/166** 携带 `source_content_sha256`（IF-v2 探针以旧名 `source_version_id` 检索，词面收口不改 0 命中事实；工件 `producer_interface_probe_v2.json.p1b`）——Source Identity Authority 当前**零身份字段**，缺的是字段不是能力（算法在库：`resolver_reference.py:52-53`）。
- IR 层有 `source_sha256`（源 md 原始字节 SHA-256），**71/71 自洽**（`ir.source_sha256` == 单元 `provenance.source_version` == 当前磁盘 md 原始字节 sha256，裁决当日复验零漂移，IF-v2 §3.2）；与接口键 `source_content_sha256` **同值映射**，IR 侧无同名关联键。
- **双层当前唯一关联值 = `source_file` 绝对路径字符串值相等**（IF-v2 §2.1/§3.4）——路径关联，非 id 关联；且该路径为本机绝对路径（`D:\Project\Papers\...`），跨机不可解析（IF-v2 §2.1）。
- V3 当前只读 Manifest，IR 消费 = 0 命中（`Grep @ backend/`，V3 @ `b5ddbe3`）。
- **实现状态**：双层接口的字段落点属 producer 接口变更 + V3 新增消费能力，**均未开始**（§6 Implementation Status Table）。

### 1.2 source_content_sha256 定义（`DECISION`，DEC-028 Part 1 = DEC-SOURCE-IDENTITY + DEC-030 命名）

**`source_content_sha256` = `SHA-256(original source bytes)`**，即源 OCR markdown 文件**原始字节**的 SHA-256。**格式 = 64 字符小写 hex 字符串**（与 producer `ir.source_sha256` 71 份实证形态完全一致，零格式迁移）。**id 的取值就是该 sha 本身**，不是另立的编号。身份由 `source_content_sha256` **唯一决定**。

> **固化原则（`DECISION`，DEC-028 Part 1）**：**Source identity belongs to content hash, not storage location.**（文件身份属于内容哈希，不属于存储位置。）

- Manifest 与 IR 的同源记录必须携带**同一** `source_content_sha256` 值。
- IR 现有 `source_sha256`（文件级，`resolver_reference.py:249`）与单元级 `provenance.source_version`（`:167`）**语义上就是这个值**，实证 71/71 与当前磁盘字节一致（IF-v2 §3.2）——IR 侧**无需改算法**，只需与 Manifest 侧对齐字段名/关联语义。
- Manifest 侧当前 **0/166** 携带该字段（IF-v2 §2.2）；producer 表态可提供，但写入属数据变更，**须 Contract 冻结后按令执行**（Readiness §2.1 / IF-v2 §2.3）。
- producer 承载字段的命名与位置：`UNKNOWN`（DSH 域，本契约不指定实现）。
- **双语料注意（`OBSERVED`）**：OCR 清单的 `source_sha256` 钉的是 **PDF** 字节（IF-v2 §4.3，`r67_manifest_bootstrap.py:181`）——若 `source_content_sha256` 定义在 md 面，两者语义不同，**不可混用**。OCR 清单是否纳入本接口 = 开放项（§6 OQ-10）。

### 1.2a 接口键命名（`DECISION`，DEC-030 Decision 1，OQ-8′ 关闭）

> 本节由 DEC-029 的 `PROPOSAL` 经 **DEC-030 采纳转为 `DECISION`**。**全文词面收口已执行**：契约中跨系统身份键一律写 `source_content_sha256`；`source_version_id` 词面**专用化为 V3 内部 UUID FK**，不再表示跨系统身份键。

**裁决**：跨系统接口身份键名 = **`source_content_sha256`**（= `SHA256(source raw bytes)`，64 小写 hex）。V3 内部 UUID FK（`source_version_id`，指向 `document_source_versions` 行）**保持不变**——它是代码列名，本轮禁改代码/schema，故不动；接口键改名后二者**词面永不同名**，零代码/零数据/零 schema。

| 概念 | 旧名（冲突态） | **现名（已裁）** | 类型 | 跨接口？ |
|---|---|---|---|---|
| **跨系统身份键（接口键）** | `source_version_id`（接口义） | **`source_content_sha256`** | 64 小写 hex sha256 | **是** |
| V3 内部 seal 版本 FK | `source_version_id`（V3 代码） | 不变 `source_version_id`（**专用为 V3 内部词面**） | `uuid.UUID` | 否 |
| V3 内部内容 hash 列 | `original_sha256` | 不变 `original_sha256` | `String(64)` UNIQUE | 否（将来装接口键值） |
| producer IR 文件级 sha | `source_sha256` | 不变（producer 域） | sha256 hex | 映射（与接口键同值） |
| producer IR 单元级 provenance | `provenance.source_version` | 不变（producer 域） | sha256 hex | 映射（与接口键同值） |

**选 `source_content_sha256` 理由**：① 类型自证（带 `sha256`，不会被误读为 UUID FK）；② 语义自证（`content` 呼应「content hash, not storage location」）；③ 名实相符；④ 零数据/schema 改动；⑤ 与 producer 现有 `source_sha256`/`provenance.source_version` 干净映射（同值，producer 无需改名）。**落选备选**：`source_bytes_sha256`（等价）；`source_sha256`（不推荐，md/PDF 面易混，OQ-10）。

**后续动作**：Owner 已终局确认命名（DEC-031 原则 3）；DSH 已随 Step 1/2 按本名执行完毕（DSH `DEC-026`，commit `e70807b`：87/87 manifest 携 `source_content_sha256`）——**双边落地已构成**，不再需要单独的命名确认轮。

### 1.3 V3 侧对应关系（`REQUIREMENT`）——键名消歧后的对照

**背景（`OBSERVED`，历史）**：DEC-030 之前，契约 sha 键与 V3 内部 UUID FK 曾共用 `source_version_id` 词面——同名、异义、异类型（OQ-20/FACT-041）。**DEC-030 改名接口键后，词面冲突消除**；下表保留对照，防混用：

| 概念 | 类型 | 语义 | 证据 |
|---|---|---|---|
| **接口键 `source_content_sha256`** | sha256 hex（64 小写） | `SHA256(raw bytes)` 跨系统身份键，id 即 sha 值 | §1.2；IR 侧 `ir.source_sha256` 71/71 同值 |
| **V3 内部 `source_version_id`** | `uuid.UUID` | `document_source_versions` 行主键 FK；Seal 层唯一性锚 `(logical_execution_stage, logical_execution_hash)`，**明令禁用 sha 作唯一**（`source.py:50`）。**词面专用化为 V3 内部，不表示跨系统身份键** | `models/source.py:44-57`；`snapshot_repository.py:42-45`；`runner_b2.py:158` |
| **V3 `Document.original_sha256`** | `String(64)` UNIQUE | BUG-V3-007 文档身份；概念对应「源内容 hash」 | `models/source.py:33,37` |

- **禁止**将 V3 内部 UUID 与接口键 `source_content_sha256` 混用或互认——二者不可互认。词面冲突已由 DEC-030 消除；类型冲突仍在（UUID vs hex），消费代码须显式区分。
- V3 必须以 §1.2 定义的 raw bytes sha 作为跨系统对账值；V3 内部 UUID ↔ 跨系统 sha 的绑定发生在 ingest，绑定关系可离线重建。

**path 非身份（`DECISION` + `REQUIREMENT`，DEC-028 Part 1/2 = 冻结项 ④）**：

- `source_file` / path / absolute path / directory = **locator information**（辅助定位 source），**不是** identity information。**任何文档不得暗示 path 参与**：文件唯一判断 / source identity 判断 / version 判断 / hash identity 判断。
- 正确表述：「**`source_file` 用于辅助定位 source，`source_content_sha256` 用于跨系统唯一识别 source**」。
- **边界公式（`REQUIREMENT`，DEC-032 Task 3，Owner 原文入册）**：

  ```
  path → 找文件
  SHA256(bytes) → 证明文件身份
  ```

  **path 只能用于找到 bytes，绝不能用于证明 bytes 是哪个 source。** 这是下一阶段实现必须严格遵守的边界。
- 未来 Windows / NAS / Linux / Object Storage / Cloud 路径变化：**不得导致 `source_content_sha256` 变化**（身份 = 内容 hash，与存储位置无关）。
- **V3 现状（`OBSERVED`）**：V3 仅将 `source_file` 用作 `Path(manifest.source_file)` 加载源文件（`runner.py:241`；`runner_b2.py:320`；`runner_b3.py:184`），全仓**无任何以 path 做身份/版本/hash 判断**的代码——**符合**本原则。跨系统双层当前靠 path 值相等关联 = **不合规现状**（正是本原则要消除的）。
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

**87 的「表达」缺口（`OBSERVED` → 已消除 producer 侧一半）**：~~生产侧现状无任何文件级接口面清单工件~~ **Step 1 接口快照工件已发布（DSH `DEC-026`，commit `e70807b`）** = `data/interface_scope_snapshot_step1.json`（87 行：manifest 相对路径 + `source_file` + hash + R50/IR 关联；sha256 = `b4f14524473d97b86f5d6a2f8bb03ee794727652a68fa4df4b00d794de98ad99`，登记见 §9）。**V3 侧识别能力缺口不变**：`identity_version` **代码 0 命中**，**无法识别接口面**（Consumer Alignment §4.1 D1-G2）。V3 侧 `IMPLEMENTATION: not started`（消费能力 NOT IMPLEMENTED，§5.6.1）。

**Scope 三数字定义（`DECISION`，DEC-028 Part 4）**：

| 范围 | 含义 |
|---|---|
| **87** | 正式身份接口范围（Interface Scope，**不改 71**） |
| **71** | 当前已有 IR 语义消费范围 |
| **16** | 等待 semantic processing（Semantic Pending） |

**禁止**：将「IR available」等同于「Interface available」——接口身份以 87 为准，不以 IR 71 为准。

**16 份 Identity-only = Semantic Pending（`DECISION`，DEC-028 Part 3 + DEC-029 原则 3 + DEC-031 原则 4 终局确认，取代 DEC-027 Part 4 的「Semantic Unavailable」）**：接口面 87 中 **16 份**（87−71）无 IR 语义承载，**不是永久缺失，而是可恢复的 Semantic Pending**——**Identity Available / Semantic Pending**。**允许重新执行 preprocessing 生成 IR（DEC-031 明确授权）**，但**约束（不变量，须同时成立）**：① **source bytes hash 不变**（source bytes 不许改；`source_content_sha256` 必须保持一致）② **source identity 不变**（身份键必须一致；**不创建新的 identity**）③ **IR 版本可追踪**（新 IR 必须绑定身份键）④ **禁止覆盖历史事实**（生成后 IR 必须重过 identity verification + semantic validation；禁改原 source / 禁 re-OCR 覆盖 / 禁新 hash 替旧 hash）⑤ **不修改历史 manifest** ⑥ **不删除已有记录**（⑤⑥ = DEC-031 原则 4 补充）⑦ **保留新旧 IR 的血统关系**（DEC-032 Task 4，Owner 原文入册——新 IR 与既有 IR 记录之间的来源血统必须显式可追踪，不得断代）。V3 应完成身份对账、暂不语义消费、标记 pending（V3 无此分离/标记能力，Consumer Alignment v3 §3.1）。接口面是否设呈现字段 = 未裁（OQ-21 / DSH 同）。

**16 份处理设计登记（`REQUIREMENT`，DEC-032 Task 4——只登记实现要求，不实施）**：未来执行路径：

```
Semantic Pending
       ↓
preprocessing（重新执行）
       ↓
new IR
       ↓
same source_content_sha256
```

该路径的实现要求 = 上述七约束不变量全部成立；血统关系（约束 ⑦）要求新 IR 记录与该 `source_content_sha256` 下既有 IR 记录（若有）的来源关联可追踪。**本登记不是实施令**——16 份的重跑执行须 Owner 单独下令（属数据动作，不在 DEC-031 Step 1/2 授权范围内）。

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

### 2.3 跨系统对账义务 + source bytes 能力冻结（`REQUIREMENT`，DEC-029 原则 6）

**冻结的能力要求（binding，DEC-029 入册 + DEC-030 Decision 2 确认 + DEC-031 终局确认）**：**V3 必须能够获得每份 source 的 raw bytes，并能重算身份键（`source_content_sha256`，§1.2）与声明值比对验证。** 具体四条：

1. **可获得 raw bytes**——Interface Scope 内每份 source，V3 有办法取得其原始字节（不是 canonical_json 包裹、不是 splitlines 规范化文本）。
2. **可重算并验证**——V3 用标准库对 raw bytes 独立重算 SHA-256，与 producer 声明值比对。
3. **fail-closed**——无法获得 bytes 或重算值 ≠ 声明值 → **阻断消费（拒收）**，不得静默放行（继承 v0.1 §3.3-3）。
4. **独立于 IR**——身份验证不以 IR 存在为前提（§1.1 DEC-B1；身份对账面在 Manifest）。

**不冻结 / 暂缓（`UNKNOWN`，明确不属 v0.2 承诺）**：**HOW** bytes 达到 V3（共享 FS / 对象存储 / IR 内嵌 / manifest 相对路径解析 / 其它）= 暂缓项。传输是实现/部署形态，随环境变化，冻结它会把部署细节锁进接口契约。当前 `source_file` 为本机绝对路径、跨机不可解析（IF-v2 §2.1；`OBSERVED`）正说明传输形态未定——但**不阻塞**能力冻结：能力是「必须能拿到 bytes 并验证」，与「怎么拿」解耦。**OQ-12′ 处置**：能力维度已冻结（进承诺面）；传输维度暂缓（不进承诺面、不构成冻结阻塞）。**DEC-031 Owner 建议**：bytes 传输方式 = 实现阶段再决定，**非架构阻塞点**。

**下一阶段核心架构风险（`REQUIREMENT`，DEC-031 Owner 原文入册；DEC-032 延伸至 Gate/Admission）**：preprocessing 侧不再是 V3 最大架构风险；**V3 消费端必须真正实现验证链**——

```
source bytes
      ↓
独立计算 SHA256
      ↓
验证 Manifest.source_content_sha256
      ↓
验证 IR 的 source_content_sha256
      ↓
确认身份与语义来源一致
      ↓
Gate
      ↓
Admission
```

任何关键验证失败：**fail-closed**——不得继续向下游消费（DEC-032 Task 3 完整链）。此链为 §0.5 六项消费义务 + 本节四条能力要求的执行面；当前 V3 零实现（§5.4 / §5.6）。

- **可执行前提**（`OBSERVED`）：载体上有该字段 + 双方对「钉 raw bytes」一致。前者当前不成立（§1.1/§1.3 缺口）；后者已由 §2.1 DECISION 满足。
- **实现状态**：`IMPLEMENTATION: not started`（依赖 §1 双层接口落地 + bytes 传输形态定案）。

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

**两状态体系终局词表（`DECISION`，DEC-028 Part 5，取代 DEC-025 四状态机的跨层合并记法）**——禁止合并，各层词表：

| 层 | 词表 | 说明 |
|---|---|---|
| **Semantic Status**（语义层） | `ready` / `incomplete` / `unknown` | READY→ready（语义完整、unit_type 合法、可消费）；INCOMPLETE→incomplete（输入不足）；unknown = 语义不明/无法安全判断（DEC-028 增补） |
| **Decision Status**（决策层） | `pending_review` / `approved` / `rejected` | PENDING_REVIEW→pending_review（待人审）；approved（放行）；REJECTED→rejected（明确违反接口） |

**引用语义边界时以此两层词表为准**（取代 DEC-022/DEC-019 的 UNKNOWN/PENDING 泛称与 DEC-025 的四状态机合并记法）。

**unknown semantic 处理（`DECISION`，DEC-028 Part 6）**——三禁令 + 强制路由：

1. **禁止 automatic conversion**（不得将未知值改写为闭集内值）。
2. **禁止 silent fallback**（不得按默认分支处理未知值）。
3. **禁止 silent skip**（不得以 incomplete/skip 路径无声吞掉，真实原因必须显式可见）。
4. **不得进入 Question materialization**（不产 leaves）。
5. **强制路由（本轮明确）**：任何 unknown semantic unit **必须产生 `reviewable record`、进入 `pending_review` workflow**（不再表述为「PENDING_REVIEW 或 REJECTED 由规则决定」——去向已裁 = pending_review）。

> **`reviewable record` 载体形态 = `UNKNOWN`**（本轮未裁）。**pending_review → rejected 的判定准则 = `UNKNOWN`**（若独立于人审 workflow，见 OQ-16′）。

**V3 侧表达缺口（`OBSERVED`，本轮结构发现，Consumer Alignment §2）**：四个状态词在 V3 分布在**两个互相正交、各自冻结**的值域里——READY/INCOMPLETE 落 `SEMANTIC_STATUS`（`compile/__init__.py:28-29`，冻结 BUG-V3-018）；PENDING_REVIEW/REJECTED 落 `DECISION_STATUS`（`gate/__init__.py:10-11`，冻结 10 §5.2）。且 `decision_status` 只存在于 candidate，candidate 只由 **ready 单元**产生（`runner_b2.py:231-264`）——**非 ready 单元永远进不了 PENDING_REVIEW / REJECTED**。

**层归属与词表已终局（`DECISION`，DEC-027 Part 5 + DEC-028 Part 5/6；OQ-5 关闭）**：Owner 已裁**不合并**两状态体系（OQ-5 关闭）；本轮进一步裁**终局词表**——语义层 `{ready,incomplete,unknown}`（OQ-20 值集就此关闭）+ 决策层 `{pending_review,approved,rejected}`；并裁 **unknown → reviewable record → pending_review**（OQ-19 路由就此关闭）。

**V3 侧表达仍未实现（`OBSERVED`，规则已裁、实现 not started）**：

- **语义层加 `unknown` 取值**：`SEMANTIC_STATUS` 冻结于 `{ready, incomplete}`（`compile/__init__.py:28-29`，BUG-V3-018），要加 `unknown` 须**解冻该冻结域**——值集已裁，实现未执行。
- **unknown → pending_review 可达性**：V3 的 candidate 只由 **ready** 单元产生（`runner_b2.py:231-264`），`decision_status` 只存在于 candidate——语义 `unknown`（非 ready）单元在 V3 现架构下**到不了 pending_review**。「产生 reviewable record 进 pending_review workflow」的 V3 机制 = `not started`。

**净效果**：OQ-5 / OQ-19 / OQ-20 值集均已裁决；剩余是 V3 实现（解冻 + reviewable record 机制）与 `reviewable record` 载体形态（UNKNOWN）。

**OBSERVED 现状（V3 侧，全部违反上述禁令，实现未开始）**：

| 层 | 当前行为 | 证据 |
|---|---|---|
| 读取 | 硬取 `u["unit_type"]`，无闭集校验 | `manifest_reader.py:52` |
| annotation | 硬编码重写为 `"standalone_question"`（**违反禁令 1**） | `annotation_adapter.py:42`；`:101-104` |
| span | 未知值按原始值走 composite 分支（**违反禁令 2**） | `resolved_span_adapter.py:77-90`；`runner_b2.py:116-127` |
| 终态 | 静默 incomplete→skip，真实原因任何层不出现（**违反禁令 3**） | `runner_b2.py:232-239`；GAP-MAP §0 E-1 |

**禁令 4 符合度**：经由静默 skip 达成（Compiler 非 ready 不产 leaves，`compiler.py:72-73`）——**结果符合、路径不符合**（非显式 PENDING_REVIEW）。

**OBSERVED 现状（producer 侧，IF-v2 §5）**：全语料恰 1 例非标值（`andalone_question`，manifest 面与 IR 面同文件同单元 Q1）；**producer 链零守卫**——该值原样进入 ADMITTED IR（`resolver_reference.py:152` 逐字复制，无转换，但也无隔离）。producer 侧现状 = 「没有静默转换，但也没有进 PENDING_REVIEW」——裁决的隔离语义今天**双侧均无执行面**。

**存量对账（`OBSERVED`，与 DSH §B.3 一致）**：该 1 例在 IR 中 `disposition = ADMITTED`。按本节两层词表口径，其 `unit_type` 非法，**不应是 READY**。其在本契约下的呈现态属存量处置面——**`UNKNOWN`**（OQ-17）。

**落点设计（`UNKNOWN`）**：层归属已裁（不合并，UNKNOWN 属语义层，OQ-5 关闭）。**仍未裁**：语义层 `unknown` 取值的引入（须解冻 BUG-V3-018，OQ-20）· unknown→PENDING_REVIEW 路由架构（OQ-19）· 两层状态载体字段名/落点（producer 侧 manifest vs IR vs 双侧，Readiness §6 / DSH C.4）。本契约不指定。

### 3.3 噪声类级事实（`OBSERVED`）

schema 噪声不只 unit_type 一处：恰 1 例 `andalone_question` + 恰 1 例游离键 `explanation_lines_note`（value = null），均在 v2 可消费面内（INTERFACE FACTS v1 §1 @ `17c55d8`）。producer 链零值域守卫（`write_outputs` 原样落盘 → `resolver_reference.py:152` 逐字复制）。**producer 侧守卫属 DSH 域，本契约不指定。**

### 3.4 继承条款（v0.1 §2.1-2.4，`OBSERVED`）

单元级字段表、claim/span 绑定（行锚 `[start,end]`）、material ref 消费禁令、figure 行内相对路径引用——**继承 v0.1**，本版不改。`unit_id` 仍为 display alias，禁止作跨系统键（v0.1 §2.2；`evidence.py:28-29` AuthorityIdentity 用 claim_id 但经三元绑定）。

---

## §4 Failure Boundary

> V3 仓内自有原则：**三层状态不复用**——E ResolvedStatus ≠ IR.semantic_status ≠ gate_decision（`compile/__init__.py:9`）。本节与之一致：三种失败处置**各自独立，禁止混淆**。

### 4.1 四种处置（`DECISION` + `REQUIREMENT`，与 §3.2 两层词表对齐）

| 处置 | Owner 定义 | 何时使用 | 终态性质 |
|---|---|---|---|
| **READY** | semantic annotation 完整、unit_type 合法、可进入后续消费 | 闭集内 unit_type + 必需字段齐备 | 可 materialize（V3 `semantic_status = ready`，`compile/__init__.py:28`） |
| **INCOMPLETE** | 输入不足 | 必需 span 缺失 / choice 型无 options / composite 缺 material（`ir.py:216-230`） | 非 materialize（V3 `semantic_status = incomplete`，`compile/__init__.py:29`） |
| **PENDING_REVIEW** | 系统无法安全判断 | **unknown `unit_type`（§3.2 DECISION）**；semantic ambiguity；schema 值域越界（v0.1 §3.3-7 basis 闭集） | 待裁决、显式隔离、可审计（V3 `decision_status = pending_review`，`gate/__init__.py:11`；**当前仅 ready 单元可达**——缺口） |
| **REJECTED** | 明确违反接口要求 | producer `disposition ∈ REJECTED_*` / `qc_verdict = FAIL`；identity v1（C-IN-1，**仅 producer 侧已实现**，见 §1.7）；sha 不一致（§2.3） | terminal，无自动路径（V3 `decision_status = rejected`，`gate/__init__.py:11`） |

> 本表承接 §3.2 的两层状态词表（语义层 ready/incomplete/unknown + 决策层 pending_review/approved/rejected；READY/INCOMPLETE/PENDING_REVIEW/REJECTED 为处置标签，分属两层，**禁合并**）。V3 侧两值分属两个正交冻结层、且非 ready 单元不可达决策层——见 §3.2「V3 侧表达缺口」。

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

1. 禁止将 V3 内部 UUID `source_version_id` 与接口键 `source_content_sha256` 混用或互认；禁止在任何文档/字段/代码中把 `source_version_id` 用作跨系统身份键（词面已专用化为 V3 内部 FK，DEC-030）。
2. 禁止用 canonical_json / body_hash / line_hash / integrity_hash 替代 source identity（§2.2）。
3. 禁止 unknown unit_type 的任何自动映射、静默 fallback 或静默 skip（§3.2/§4.2）。
4. 禁止合并 `semantic_status` 与 `decision_status` 两个状态体系（DEC-027 Part 5，OQ-5 已裁不合并）。
5. 禁止消费 Interface Scope 外的 manifest（含 v1 legacy 79）而不显式拒收（§1.6/§1.7）。
6. 禁止为对齐 87/71 数字而强制生成 IR、删除 identity 文件、或修改历史数据（DEC-027 Part 3 三禁）。
7. 禁止把 INCOMPLETE 报为 PENDING_REVIEW / REJECTED，或反向代用（§4.2-1/2）。
8. 禁止 unresolved 答案槽位静默默认（继承 v0.1 §3.2 特别条款）。

### 5.3 Decision Alignment Table（`DECISION` / `OBSERVED` / `UNKNOWN` 对照，DA-1~36）

> 每行 = 一项裁决要求。DA-1~12 = B1/B2/B3；DA-13~20 = FINALIZATION v1（DEC-023~026）；DA-21~26 = Interface Decision Finalization v1（DEC-027）；DA-27~31 = Interface Finalization Revision v1（DEC-028）；DA-32~33 = Freeze Candidate Review v1（DEC-029）；DA-34 = Freeze Candidate Finalization v1（DEC-030）；DA-35 = Owner Final Decision v1（DEC-031）；**DA-36 = Contract v0.2 最终冻结收口 Consumer 侧（DEC-032）**。

| # | 裁决要求（DECISION） | OBSERVED 现状 | UNKNOWN |
|---|---|---|---|
| DA-1 | Manifest = Source Identity Authority（双层之一） | manifest 0/166 携任何 sha/hash 键，0/166 携 `source_content_sha256`（IF-v2 探针旧名检索，0 命中事实不变）；缺字段非缺能力 | producer 承载字段命名/位置 |
| DA-2 | IR = Semantic Consumption Authority（双层之一）；语义消费方向 IR → V3 | IR 71/71 sha 自洽零漂移；覆盖 88 记录/71 ADMITTED/1,664 单元；R52 一次性冻结工件无持续产出（IF-v2 §3）；V3 IR 消费 = 0 命中 | IR 是否扩产、是否建持续产出机制 |
| DA-3 | 双层经 `source_content_sha256` 关联 | 当前唯一关联 = `source_file` 绝对路径字符串值相等（IF-v2 §3.4）；路径为本机绝对路径跨机不可解析 | `source_file` 是否改仓库相对路径 |
| DA-4 | `source_content_sha256` = `SHA-256(original source bytes)`（id 即 sha 值） | IR 侧 `source_sha256`/`provenance.source_version` 语义已符合（71/71）；Manifest 侧 0/166 | 回填范围 87 vs 166（Readiness §6） |
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
| DA-20 | 接口面 87 中 16 份无 IR 语义承载 | 双层落地后这 16 份在身份面内、语义面外；V3 今天能通过 manifest 消费它们 | ~~语义面地位~~ **已裁 = Identity Available / Semantic Pending（DEC-028 Part 3；DEC-027 Part 4 旧表述「Semantic Unavailable」已废止）**；接口面呈现字段未裁（OQ-21） |
| DA-21 | **Part 1** 双层职责模型正式采用 + 双禁（Manifest 不代 IR 描述题目 / IR 不代 Manifest 证身份）（DEC-027） | V3 两个半边都不符——用身份层做语义消费、且无身份锚（FACT-038） | IR loader / 身份锚实现排期（五步序无对应步骤） |
| DA-22 | **Part 2** V3 验证 Manifest / 重算 hash / 判断接受（DEC-027） | 三项全无：无校验（`manifest_reader.py:52`）、不读 producer sha、无身份闸门（`identity_version` 0 命中） | source bytes 交付形态（OQ-12 / DSH G-4） |
| DA-23 | **Part 2** V3 验证 IR 符合契约 / Gate / 拒收；原则「Preprocessing 解释，V3 裁决」（DEC-027） | V3 零 IR 消费能力，语义消费全来自 manifest | IR loader 排期（五步序无此步骤） |
| DA-24 | **Part 3** 87/71 二者允许不同 + 三禁（禁强制生成 IR / 禁删 identity 文件 / 禁改历史数据）（DEC-027） | V3 无法识别接口面；IR 零消费 | 接口面 87 承载物形态（DSH G-3） |
| DA-25 | **Part 4** 16 份 Identity-only = 正常态 + 三禁（DEC-027；旧表述「Semantic Unavailable」已由 DEC-028 Part 3 改为 **Semantic Pending**，本表不再使用旧词） | 这 16 份已在接口面，靠身份自足成立；V3 无身份/语义分离消费能力 | semantic availability 呈现字段（OQ-21 / DSH G-6） |
| DA-26 | **Part 5** 三禁令 + UNKNOWN 属语义层 + 不合并两状态体系（DEC-027） | V3 三禁全违反（洗白/fallback/静默 skip 一条链三切面）；`SEMANTIC_STATUS` 无 `unknown` 取值；非 ready 不可达决策层 | 语义层 unknown 取值引入（OQ-20）· 路由架构（OQ-19）· 载体字段名/落点 |
| DA-27 | **Source identity = `SHA256(raw bytes)`，64 小写 hex**；身份由其唯一决定；**Source identity belongs to content hash, not storage location**（DEC-028 Part 1） | producer 算法在库 71/71；V3 自算 canonical_json 非 raw bytes；V3 零身份校验 | 格式已裁；命名已裁 = `source_content_sha256`（DEC-030，OQ-8′ 关闭） |
| DA-28 | **path = locator only，非 identity**；任何文档不得暗示 path 参与身份/版本/hash 判断；路径变化不得改 `source_content_sha256`（DEC-028 Part 1/2） | V3 仅用 path 作 locator（**符合**）；跨系统双层当前靠 path 值相等关联（不合规现状） | bytes 传输方案（OQ-12″，暂缓） |
| DA-29 | **16 份 = Identity Available / Semantic Pending（可恢复）**；允许重生成 IR 四约束；禁改原 source/新 identity/新 hash（DEC-028 Part 3） | 前轮记「Semantic Unavailable 正常态」，本轮改 Pending；V3 无身份/语义分离 + 无 pending 标记 | 呈现机制（OQ-21） |
| DA-30 | **语义层终局词表 `{ready,incomplete,unknown}` + 决策层 `{pending_review,approved,rejected}`，禁合并**（DEC-028 Part 5） | V3 `SEMANTIC_STATUS` 冻结 `{ready,incomplete}`（须解冻加 unknown）；`DECISION_STATUS` 已符合 | 解冻 BUG-V3-018 = not started |
| DA-31 | **unknown semantic → reviewable record → pending_review workflow**；禁 silent skip/convert/fallback（DEC-028 Part 6） | V3 三禁全违反；unknown→pending_review 在 candidate-gated-on-ready 架构下无执行面 | reviewable record 载体（UNKNOWN）· pending→rejected 准则（OQ-16′） |
| DA-32 | **接口键命名 = `source_content_sha256`**（DEC-029 提案 → **DEC-030 Decision 1 采纳**）；V3 内部 UUID FK 不变，词面专用化 | 契约 sha 键与 V3 UUID FK 曾同名异义（FACT-041）；改接口键名消歧，零代码/schema | ~~Owner 采纳~~ **已采纳**；DSH 双边确认键名 = 待办 |
| DA-33 | **source bytes 能力冻结**：V3 必须能获得 raw bytes + 重算验证（fail-closed）+ 独立于 IR；**不冻结传输**（DEC-029 原则 6 + DEC-030 Decision 2 确认） | V3 自算为 canonical_json 包裹非 raw bytes（`runner.py:71-73`）；零身份校验；`source_file` 本机绝对路径跨机不可解析 | bytes 具体传输方案（暂缓，OQ-12″）· V3 重算能力实现（not started） |
| DA-34 | **Freeze Candidate Finalization（DEC-030）**：① 命名 `source_content_sha256` 采纳 + 全文词面收口 ② bytes 能力冻结确认 ③ 双状态体系终局确认（ready/incomplete/unknown + pending_review/approved/rejected，禁合并；unknown→reviewable record→pending_review，禁 silent skip/convert/fallback）④ 废止「Semantic Unavailable」旧表述 + 消除接口键歧义 | 契约文本已收口（DEC-030 轮）；V3/producer 实现面均未动（DECISION ≠ IMPLEMENTATION） | ~~DSH 双边确认键名~~ **已由 DEC-031 终局确认取代** · Step 1/2 数据前置 |
| DA-35 | **Owner Final Decision v1（DEC-031）**：① 四项原则终局确认（Identity Authority：`source_content_sha256` = SHA256(original source bytes) 64 小写 hex，path 仅 locator，禁任何系统用 path 做唯一身份判断 / 双层职责：Manifest=「哪个文件」IR=「表达什么」，不得混淆 / 命名：跨系统 `source_content_sha256`、V3 内部 `source_version_id`，禁同名 / 16 份：Identity Available Semantic Pending，允许重跑 preprocessing，不建新 identity、不改历史 manifest、不删已有记录）② **Step 1 + Step 2 执行授权**（DSH 任务：快照含文件列表+sha+R50 关联；回填后逐份验证 Manifest hash = IR hash）③ **冻结条件机械化** = Step 2 完成并验证后进入 Freeze ④ 五项延期（OQ-15/OQ-13/OQ-10/DEC 编号/OQ-12″）非架构阻塞 ⑤ V3 下一阶段核心风险 = 消费端验证链（bytes→重算→验证 Manifest→验证 IR→fail-closed） | 契约文本侧本轮合并完成；~~DSH 执行 Step 1/2 = not started（授权已下）~~ **DSH Step 1/2 已执行并验证 = DONE**（DSH `DEC-026`，commit `e70807b`；证据 = §9）；V3 验证链 = not started | ~~DSH Step 1 快照~~ **DONE** · ~~DSH Step 2 回填 + 验证报告~~ **DONE + PASS** · ~~OQ-10 md/PDF 分层（Step 2 内裁）~~ **已按 md 面口径执行完毕** |
| DA-36 | **Contract v0.2 最终冻结收口 Consumer 侧（DEC-032）**：① **Task 1 文本核验通过**——八项表达完整无歧义（`source_content_sha256` / SHA256(raw bytes) / path non-identity / 双层职责 / 87-71-16 / Semantic Pending / bytes verification / fail-closed）② **Task 2 Consumer Boundary 最终核验**——五项能力 NOT IMPLEMENTED 显式登记（§5.6.1：Manifest identity verification / raw bytes acquisition / independent SHA256 verification / IR identity verification / identity gate）③ **Task 3 实现边界建立**（§5.6.2）：输入 = Manifest + raw bytes + IR；验证 = Manifest identity + IR identity + source-content consistency；失败 = fail-closed；成功 = 进入既有 Gate/Admission；**path → 找文件，SHA256(bytes) → 证明文件身份**（§1.3 边界公式）④ **Task 4 16 份设计登记**（§1.6）：Semantic Pending → preprocessing → new IR → same `source_content_sha256`；约束 ⑦ 新增「保留新旧 IR 的血统关系」；验证链延伸至 Gate→Admission（§2.3） | 契约文本核验完成（八项均在位，无需修正）；五项 NOT IMPLEMENTED 与 §5.4 / FACT-043 一致；实现边界与 16 份设计 = REQUIREMENT 登记，零实现 | bytes 传输形态（OQ-12″）· 实现排期（UNKNOWN）· 16 份重跑执行令（须 Owner 单独下令） |
| DA-37 | **Contract v0.2 Freeze Finalization Audit·Consumer 侧（DEC-033）**：① **Task 1 冻结状态描述修正**——Step 1/2 历史「未开始/未完成」表述统一更新为事实状态 **Step 1 DONE / Step 2 DONE / Verification PASS / READY FOR FREEZE / NOT IMPLEMENTED (V3 capability)**（只改事实状态，不改架构定义）② **Task 2 Freeze Evidence 引用登记**（§9.1：Step 1 snapshot artifact / Step 2 backfill report / Verification report / Final check evidence / commit hash 五类齐全，未来任何人可从本契约找到冻结依据）③ **Task 3 Freeze Object 明确化**（§9.2：唯一冻结对象 = 本文件；document sha256 + commit 登记于 V3 state.yaml/CURRENT.md，外部登记避免自引用；禁止多个 commit 均作为最终版本）④ **Task 4 关键词再验证**——`source_content_sha256` = 唯一跨系统身份键；`source_version_id` = 仅 V3 UUID / 历史解释 / 禁止跨系统 identity；Semantic Unavailable = 仅废止记录；path/`source_file` = 仅 locator | 冻结条件（DEC-031 §六机械条件）= **已满足**（DSH `DEC-026`/`027`/`028`）；契约状态 = **READY FOR FREEZE / NOT FROZEN**；五项 V3 能力仍 **NOT IMPLEMENTED**；本轮零代码 / 零 schema / 零数据 / 零 IR / 不扩展冻结范围 | Owner Freeze 令（属 Owner）· V3 消费端验证链实现（下一阶段，排期 UNKNOWN） |

### 5.4 Implementation Status Table（`DECISION ≠ IMPLEMENTATION`）

| 契约义务 | 侧 | IMPLEMENTATION STATUS | 缺口 ID / 依赖 |
|---|---|---|---|
| Manifest 携带 `source_content_sha256`（0/166 → 回填，范围 = 87） | producer | **DONE**（DSH `DEC-026`，commit `e70807b`：87/87 回填完成 + 逐份验证通过；键名/格式按 DEC-030/031、64 hex DEC-028；md 面口径 OQ-10 延期项按此执行；R50 配对再冻结 E2 已落地 = pre/post 双快照；Manifest hash = IR hash **71/71 PASS**） | B1-G1 / G1 / D4-G2 — producer 侧关闭 |
| 双层关联从路径升级为 `source_content_sha256` | producer | **producer 侧载体 DONE**（键已在 87/87 manifest；DSH `DEC-026`）；**关联机制使用 = not started**（V3 消费侧未读该键，跨系统仍靠 path 值相等关联） | B1-G2 / G2 — 载体关闭，消费侧使用 not started |
| `source_file` 绝对路径 → 仓库相对路径 | producer | **not started**（待 v0.2 裁决） | OQ-12 |
| IR 覆盖扩产（71 → 更广） | producer | **not started**（须 Owner 令；扩产 = 新数据生成） | G3 / OQ-11 |
| IR 持续产出机制 | producer | **not started**（须 Owner 令，是否要未定） | G4 |
| unit_type 值域守卫（生成链） | producer | **not started**（B3 语义须先落字） | G5 |
| 存量 1 例 unit_type 修复 | producer | **deferred**（Owner 令：接口冻结优先；且破坏 R50 基线，须配对再冻结） | Readiness §5 D1 |
| V3 具备 IR 消费路径 | V3 | **not started**（0 命中） | B1-G3 |
| V3 绑定跨系统 sha（raw bytes 写入 `documents.original_sha256`） | V3 | **not started**（当前为 canonical_json 包裹值） | B1-G4 / B2-G1 |
| sha 对账闸门按 raw bytes 可执行 | V3 | **not started**（依赖上两项） | B2-G3 |
| unknown unit_type → PENDING_REVIEW / REJECTED | 双侧 | **not started**（当前静默 incomplete→skip / 零守卫） | D3-G1/G2 / G5 |
| 语义层 `unknown` 取值引入 | V3 | **值集已裁 = `{ready,incomplete,unknown}`（DEC-028 Part 5）**；V3 加值 = **not started**（须解冻 BUG-V3-018） | OQ-20 |
| unknown → reviewable record → pending_review | V3 | **路由已裁（DEC-028 Part 6）**；V3 机制 = **not started**（candidate 仅由 ready 产，非 ready 不可达决策层） | OQ-16′（载体/pending→rejected） |
| PENDING_REVIEW → REJECTED 路由规则文本 | — | **UNKNOWN**（Decision 3 要求「由明确规则决定」，规则未给） | OQ-16 |
| 接口面 87 承载物（清单工件）发布供 V3 核验 | producer | **DONE**（DSH `DEC-026`：`data/interface_scope_snapshot_step1.json` 已发布，87 行，sha256 = `b4f14524…98ad99`，§9.1）；V3 核验能力 = not started | D1-G1 — producer 侧关闭；D1-G2（V3 识别）仍 not started |
| V3 识别并只消费接口面内 manifest | V3 | **not started**（`identity_version` 代码 0 命中） | D1-G2 |
| 16 份 Identity-only 处理 | V3 | **DECIDED = Identity Available / Semantic Pending（可恢复，DEC-028 Part 3）**；允许重生成 IR 四约束；V3 身份/语义分离 + pending 标记 = **not started** | OQ-21（呈现字段）/ Consumer Alignment v3 §3.1 |
| Step 1 接口快照载体形态 + R50 血统关系 | producer | **DONE**（DSH `DEC-026`：快照工件 + pre/post 配对双 audit 快照已落地；R50 保留历史基线、DRIFT = 恰 87 manifest 为预期行为，血统解释见 DSH Freeze Evidence v1 §3） | D4-G1 / DSH D.6 — 关闭 |
| `source_content_sha256` 在 producer 侧的承载字段命名/位置 + md vs PDF 分层 | producer | **DONE**（DSH `DEC-026`：87/87 manifest 尾部追加 `source_content_sha256` 键；md 面口径执行，PDF 面 = OQ-10 延期项未纳入） | D4-G2 — md 面关闭；OQ-10（PDF 面）延期 |
| v1 面 79 份处置 | producer | **DECIDED = historical asset 隔离**（DEC-024）；四禁；迁移走独立 Legacy Migration Plan | §1.7 / ~~OQ-6~~ **已关闭** |
| V3 消费侧 identity 版本闸门（与 producer C-IN-1 双边） | V3 | **UNKNOWN**（Owner 未下达 V3 实现设计） | D2-G1 |
| **V3 验证 Manifest + 重算 hash + 判断接受**（Part 2 三义务） | V3 | **not started**（无校验 / 不读 producer sha / 无身份闸门） | V3-G1 / Consumer Alignment v2 §2.1 |
| **V3 验证 IR 契约 + Gate + 拒收**（Part 2 三义务） | V3 | **not started**（零 IR 消费能力；语义消费仍来自 manifest） | V3-G2 / Consumer Alignment v2 §2.2 |
| V3 消费身份但不消费语义（16 份 Identity-only 分离消费） | V3 | **not started**（V3 无身份/语义分离能力） | V3-G6 |
| 接口键命名消歧（跨系统 sha vs V3 UUID） | 契约措辞 | **已裁 = `source_content_sha256`（DEC-030 采纳 + DEC-031 终局确认）**；全文词面收口已执行；`source_version_id` 专用化为 V3 内部 FK；DSH 随 Step 1/2 按本名执行即落地 | OQ-8′ 关闭 |
| source bytes 能力（可得 raw bytes + 重算验证 fail-closed + 独立 IR） | 双侧 | **能力已冻结（DEC-029 原则 6 + DEC-030 Decision 2 确认）**；V3 重算能力 = **not started**（自算 canonical_json 非 raw bytes）；传输方案 = **暂缓** | OQ-12″（传输）/ B2-G1 |
| **V3 identity verification capability**（Part 9 明确登记） | V3 | **not implemented = not started**；未来消费必须依赖 `source_content_sha256`（身份键），不得依赖 path | Consumer Alignment v3 §4 |

### 5.5 Execution Ordering（`DECISION`，DEC-026 ≡ DSH DEC-021-4）

**Owner 裁定（FINALIZATION v1 Decision 4）**——所有数据动作必须遵循：

```
Step 1  Freeze interface snapshot
   ↓
Step 2  Generate / backfill source_content_sha256
   ↓
Step 3  Freeze Contract v0.2
   ↓
Step 4  Execute data hygiene
   ↓
Step 5  Execute image recovery / historical cleanup
```

**裁决理由（原文）**：source identity 必须早于内容修改。任何图片恢复 / OCR 修复 / markdown 修改都可能导致 content change → hash change → `source_content_sha256` invalid。**身份冻结优先。**

**与交集定量的兼容性（`OBSERVED`，DSH Dependency Map v2.2 §4）**：五步序与实测交集零冲突——Step 2 回填的 87 份全部为 R50 基线成员（E2 硬约束，由 Step 1 快照承担配对角色，其与 R50 的血统关系 = 执行令细化）；Step 5 图片恢复在排除模式下（排除 2 份三重成员）与接口面零交集（1,394 份）。

**残留不一致（OQ-18，DEC-031 后关闭）**：DSH Dependency Map 边表 **E1** 曾写「`v0.2 冻结 → G1b 回填`（字段未定义不得回填，硬治理）」，方向与五步序（回填 → 冻结）相反。DEC-030 已消除其「字段未定义」关切（键名/算法/格式均已裁）；**DEC-031 Owner 授权 Step 1/2 执行并规定冻结条件 = Step 2 完成并验证后进入 Freeze，等于显式确认五步序优先（回填 → 冻结）**。E1 由 DSH 侧文档随 Step 1/2 执行更新对齐；OQ-18 **关闭**。

**V3 侧边界（`OBSERVED` + `UNKNOWN`，本轮明确登记）**：**五步序全部是数据 / 契约动作，不含任何 V3 实现动作。** V3 的 IR 消费能力（V3-I1）、身份绑定（V3-I2/I3）、四状态机通道（V3-S1）**在五步序中没有对应步骤**——**V3 侧实现排期 = UNKNOWN，且不因本裁决而获得排期**。本契约不提案为其插入步骤。

### 5.6 Consumer Boundary 最终核验 + 下一阶段实现边界（`OBSERVED` + `REQUIREMENT`，DEC-032 Task 2/3）

> 本节为 **Contract v0.2 最终冻结收口（Consumer 侧）** 的新增登记：Task 2 = V3 当前真实状态的显式核验（五项能力 NOT IMPLEMENTED）；Task 3 = 下一阶段实现边界。**本节不含任何实现方案，不写业务代码，不改 schema。**

#### 5.6.1 V3 Consumer 现状核验（`OBSERVED`，Task 2——五项全部 NOT IMPLEMENTED）

| # | 能力 | 状态 | 证据 |
|---|---|---|---|
| 1 | **Manifest identity verification**（验证 Manifest 声明的 `source_content_sha256`） | **NOT IMPLEMENTED** | `manifest_reader.py:52` 无校验；Manifest dataclass 无 sha 字段（`manifest_reader.py:28-35`） |
| 2 | **raw bytes acquisition**（获得 source 原始字节） | **NOT IMPLEMENTED** | `source_file` 为本机绝对路径跨机不可解析（IF-v2 §2.1）；无 bytes 获取机制 |
| 3 | **independent SHA256 verification**（独立重算 SHA-256 并比对声明值） | **NOT IMPLEMENTED** | V3 自算为 canonical_json 包裹 joined-text（`runner.py:71-73`；`hashing.py:60-62`），非 raw bytes |
| 4 | **IR identity verification**（验证 IR 的 `source_content_sha256`） | **NOT IMPLEMENTED** | V3 零 IR 消费能力（Grep `resolver_ir\|source_sha256` @ `backend/` = 0 命中） |
| 5 | **identity gate**（身份闸门：不一致 → 拒收） | **NOT IMPLEMENTED** | 无身份闸门；`identity_version` 代码 0 命中；fail-closed 无执行面 |

**这五项属于下一阶段，不是 V3 当前已有能力。** 本契约中任何 `REQUIREMENT`（§0.5 六义务 / §2.3 四条能力 / §5.1 七承诺）**均为义务面冻结候选，不得读作现状描述**——现状即上表五项 NOT IMPLEMENTED。既有 V3 Gate / Admission 链（EB-008 面，`admission.py` / `gate/`）不因本节变动，本契约不改其逻辑。

#### 5.6.2 Consumer Implementation Boundary（`REQUIREMENT`，Task 3——下一阶段实现边界）

**输入**：

```
Manifest + raw bytes + IR
```

**验证**：

```
Manifest identity    （重算 SHA256(bytes) == Manifest.source_content_sha256）
IR identity          （IR.source_content_sha256 == Manifest.source_content_sha256）
source-content consistency（身份与语义来源一致——同一 sha 锚定同一 bytes 与同一 IR）
```

**失败**：

```
fail-closed（任何关键验证失败 → 阻断消费，不得继续向下游）
```

**成功**：

```
进入既有 V3 Gate / Admission 链
```

**path 边界（binding，DEC-032 Task 3）**：

```
path → 找文件（locator only）
SHA256(bytes) → 证明文件身份（identity）
```

**path 只能用于找到 bytes，绝不能用于证明 bytes 是哪个 source。** 这是下一阶段实现必须严格遵守的边界（§1.3 边界公式同源；冻结项 ④ 继承）。

**边界性质**：本节登记的是**输入 / 验证 / 失败 / 成功**四面的边界约束，**不是实现方案**——载体形态（bytes 传输 OQ-12″）、落点设计（V3 哪一层执行验证）、排期（UNKNOWN，§5.5）均不在本节。实现启动须 Owner 单独下令。

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
| OQ-8 | producer 侧身份键承载字段命名 / 格式 / md vs PDF 分层 | **格式已裁（DEC-028 Part 1）= 64 字符小写 hex**；**命名 OQ-8′ 已关闭（DEC-030 Decision 1 + DEC-031 终局确认）= 接口键 `source_content_sha256`**（§1.2a）。producer 内部承载字段命名/位置 = DSH 域；md vs PDF 分层（OQ-10 承接，DEC-031 延期）仍开放 |
| OQ-9 | 全语料 IR 是否/何时重新产出 + 是否建持续产出机制 | 须 Owner 显式令（G3/G4；暂停令 `746e35c` 生效中） |
| OQ-10 | OCR 清单（钉 PDF 字节）是否纳入双层接口 | 未裁决（IF-v2 §4.3；语义与 md 面不同，不可混用）。**DEC-031 Owner 建议延期**（OCR/PDF 扩展面 = 以后扩展，非架构阻塞）；Step 2 回填按 md 面执行，md vs PDF 分层在 Step 2 内按此口径处理 |
| OQ-11 | IR 权威面承诺 | **部分已裁（DEC-023）**：当前冻结面 = 71 ADMITTED。**扩产机制仍未裁**（DEC-B1 已使其与身份面解耦，不阻塞冻结） |
| OQ-12 | `source_file` 形态 + source bytes 交付 | **身份维度已关闭（DEC-028 Part 1/2）= path 非身份**（locator only）。**能力维度已冻结（DEC-029 原则 6 + DEC-031 确认）= V3 必须能得 raw bytes + 重算验证 fail-closed + 独立 IR**（§2.3）。**传输维度暂缓（OQ-12″）**：bytes 如何达 V3 = 实现/部署形态，不进 v0.2 承诺、不阻塞冻结。**DEC-031 Owner 建议延期**（bytes 传输方式 = 实现阶段再决定，非架构阻塞） |
| OQ-13 | 17 份拒收记录（16 QC_FAIL + 1 REJECTED_V1）在接口中的地位（披露 vs 排除） | 未裁决（Readiness §2.3-4；生产侧无偏好）。**DEC-031 Owner 建议延期**（历史治理问题，非架构阻塞） |
| OQ-14 | 接口面 87 中 16 份无 IR 语义承载的地位 | **已裁（DEC-028 Part 3 + DEC-031 原则 4 终局确认）= Identity Available / Semantic Pending（可恢复）**；允许重生成 IR 约束（§1.6，DEC-031 补充三禁）。呈现机制 = OQ-21 |
| OQ-15 | legacy 79 的披露形态（v0.2 文字层：仅规模 vs 路径清单） | 未裁决（起草面）。**DEC-031 Owner 建议延期**（不影响主链，非架构阻塞） |
| OQ-16 | unknown semantic 的路由 + pending_review → rejected 判定 | **路由已裁（DEC-028 Part 6）= unknown → reviewable record → pending_review**。**残余 OQ-16′**：pending_review → rejected 的判定准则（若独立于人审 workflow）；`reviewable record` 载体形态未裁 |
| OQ-17 | 存量 1 例 `andalone_question` 在两层词表下的呈现态与处置原子性 | 未裁决（涉 R50 成员 manifest + IR 冻结工件；DSH D.3 同源） |
| OQ-18 | **E1 残留冲突**：DSH Dependency Map 边表 E1（契约冻结 → 回填）与 Decision 4 五步序（回填 → 契约冻结）方向相反 | ~~已收窄（DEC-030）~~ **已关闭（DEC-031）**：Owner 授权 Step 1/2 执行 + 规定冻结条件 = Step 2 验证通过后 Freeze，显式确认五步序优先（回填 → 冻结）；E1 由 DSH 随 Step 1/2 执行更新对齐（§5.5） |
| OQ-19 | 语义 UNKNOWN → 决策 PENDING_REVIEW 可达性 | **路由规则已裁（DEC-028 Part 6）= unknown → pending_review workflow**；V3 现架构 candidate-gated-on-ready 下**机制 not started**（实现缺口，非开放裁决） |
| OQ-20 | `source_version_id` 同名异义消歧 + 语义层 `unknown` 取值 | **值集已裁（DEC-028 Part 5）= `{ready,incomplete,unknown}`**（解冻 BUG-V3-018 加值 = not started）。**命名消歧 OQ-8′ 已关闭（DEC-030）= 接口键 `source_content_sha256`，词面冲突消除** |
| OQ-21 | 接口面是否设 semantic availability / pending 呈现字段 | **未裁决**（状态已裁 = Semantic Pending；呈现载体 = manifest 字段 vs V3 靠 IR 面有无推断，两侧横跨，DSH 同） |

---

## §7 与 v0.1 的差异

| 条款 | v0.1 @ `1fbaf5e` | v0.2 DRAFT |
|---|---|---|
| 消费载体 | 「V3 消费以 IR 为准」（`:33`） | **取代**：双层各有权威面 + 语义消费方向 IR → V3（§1.1/§3.1） |
| source identity | 隐含 sha = raw bytes，未禁其他 hash | **收紧**：显式唯一定义 + 禁止清单含 norm_sha256/corpus_sha256（§2.1/§2.2） |
| `source_content_sha256`（接口键） | §4.2 声称「一一对应」但无载体 | **升格**：id = sha 值本身 + 双层同值 REQUIREMENT + 0/166 缺口登记（§1.2）；DEC-030 定名 `source_content_sha256`（§1.2a） |
| unknown unit_type | §3.3-6「隔离（PENDING 通道）」 | **收紧**：闭集强制 + 四条禁令（含禁静默 skip）+ 落点 UNKNOWN（§3.2/§4.1） |
| Failure Boundary | 分散于 §3.3 各项 | **集中**：三处置定义 + 五条禁止混用（§4） |
| 接口面口径 | 未定 | **升格为 DECISION**：Interface Scope = 87（字段口径）/ IR 当前冻结面 = 71 ADMITTED（§1.6，DEC-023） |
| legacy v1 面 | 仅 C-IN-1 拒收条款 | **新增 DECISION 节**：historical asset + 四禁 + 独立 Legacy Migration Plan 通道（§1.7，DEC-024） |
| semantic 状态词表 | 「PENDING 通道」泛称 | **升格**：四值 READY/INCOMPLETE/PENDING_REVIEW/REJECTED + 三禁令 + 强制路由（§3.2/§4.1，DEC-025） |
| 执行序 | 无 | **新增**：五步序（身份冻结优先）+ V3 侧无对应步骤声明（§5.5，DEC-026） |
| 身份自足性 | 无 | **新增**：source 身份不依赖 IR 存在（§1.1 DEC-B1 细化） |
| 语义覆盖悬崖 | 无 | **已裁**：16 份 = Identity Available / Semantic Pending（可恢复）（§1.6 / OQ-14 关闭，DEC-028 Part 3 取代 DEC-027 Part 4 旧表述） |
| **责任边界** | 无 | **新增 §0.5**：Preprocessing 解释 / V3 接受或拒绝 + V3 六项消费义务（DEC-027 Part 2） |
| **冻结范围** | 无明确范围 | **新增 §0**：v0.2 只冻结三件（Identity / Scope / Semantic Boundary）+ 六类暂缓（DEC-027 Part 6） |
| UNKNOWN 语义层 | 无 | **新增**：UNKNOWN 属语义层、不合并两状态体系（§3.2，DEC-027 Part 5；OQ-5 关闭，OQ-19/20 新登记） |
| 接口键命名 | 仅「禁混用」 | **升格并消歧**：同名异义对照表（§1.3）→ DEC-030 采纳 `source_content_sha256`，词面收口（§1.2a），OQ-8′ 关闭 |
| hash 行号 | — | 按 E-2 勘误（splitlines @ `source_loader.py:27`） |

---

## §8 冻结前提 / Freeze 前执行步骤清单（状态：**全部完成，条件已满足**）

> **结构**：Decision 4 把 **Contract v0.2 冻结放在五步序的 Step 3**，其前置 = Step 1（接口快照冻结）+ Step 2（`source_content_sha256` 回填）。**DEC-031 后冻结条件机械化**：Step 2 完成并验证（逐份 Manifest hash = IR hash）→ 进入 Contract v0.2 Freeze。**DEC-033 事实更新**：DSH 已执行 Step 1/2 并出验证报告（DSH `DEC-026`，commit `e70807b`），最终复核 C1-C9 = VERIFIED（DSH `DEC-027`，commit `aad2237`），Producer 最终确认 ALL PASS（DSH `DEC-028`，commit `67f564c`）——**机械冻结条件已满足**。

**已完成（DEC-030 + DEC-031 + DEC-032，契约文本侧）**：

- ✅ 接口键命名 `source_content_sha256` 采纳 + 全文词面收口 + **Owner 终局确认**（OQ-8′ 关闭；DEC-030/031）。
- ✅ source bytes 能力冻结确认（§2.3；传输 OQ-12″ 暂缓，DEC-031 建议延期）。
- ✅ 双状态体系终局确认（§3.2/§0.3；DEC-030 Decision 3）。
- ✅ 废止旧「Semantic Unavailable」表述（DA-20/25、§7）；`source_version_id` 接口键歧义消除。
- ✅ 四项原则终局确认 + 16 份补充三禁（DEC-031 原则 1–4，§0.1/§1.1/§1.6）。
- ✅ **Step 1/2 执行授权下达**（DEC-031 §二）；OQ-18 关闭（五步序优先显式确认）。
- ✅ **Consumer 侧最终冻结收口（DEC-032）**：Task 1 文本核验通过（八项完整）· Task 2 五项 NOT IMPLEMENTED 显式登记（§5.6.1）· Task 3 实现边界建立（§5.6.2 + §1.3 边界公式）· Task 4 16 份设计登记（§1.6，约束 ⑦ 血统关系）· 验证链延伸至 Gate→Admission（§2.3）。

**Freeze 前执行步骤（DSH 任务）——事实状态（DEC-033 更新，证据 = §9）**：

1. **Step 1 接口快照执行**（producer）——**DONE**（DSH `DEC-026`，commit `e70807b`）：`data/interface_scope_snapshot_step1.json`（87 行：文件列表 + `source_content_sha256` + R50 关联）+ pre-backfill audit 快照（corpus `4ad3458b…`，177 files）。
2. **Step 2 执行：87 份 manifest 补齐 `source_content_sha256`**（producer）——**DONE**（同 commit）：`n_backfilled = 87 / n_already = 0`；仅追加一键、剥键重序列化 == R50 基线 87/87（零污染证明）；R50 配对再冻结 = pre/post 双快照落地；md 面口径（OQ-10 延期项）。
3. **Step 2 验证报告**（producer）——**DONE + PASS**（同 commit）：`PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md`——① 87 份文件列表 ✓ ② hash 一致性：Manifest hash = IR hash **71/71 PASS**、Manifest hash = source bytes **87/87 PASS**、零漂移双证 ✓ ③ IR 覆盖 **71 ADMITTED / 16 REJECTED_QC_FAIL** ✓ ④ 16 份 pending = Identity Available / Semantic Pending ✓。**最终复核**（DSH `DEC-027`）：`freeze_evidence_final_check.py` 从磁盘字节独立重导，C1–C9 **overall = VERIFIED**，零 BLOCKER。
4. **→ Contract v0.2 Freeze**（Step 3）——**机械条件已满足**（DEC-031 §六）。**当前状态 = READY FOR OWNER FREEZE / NOT FROZEN**——冻结令属 Owner，尚未下达；契约文本收口与状态登记 = Claude 侧义务（本文件 + §9，DEC-033）。

**非冻结前提（DEC-031 Owner 建议延期，非架构阻塞点）**：

- **OQ-15** legacy 79 披露形态 —— 不影响主链。
- **OQ-13** 17 拒收记录地位 —— 历史治理问题。
- **OQ-10** OCR/PDF 扩展面 —— 以后扩展（Step 2 已按 md 面口径执行完毕）。
- **跨仓 DEC 编号统一** —— 文档管理问题（撞号 3 处仍待 Owner 定约定，但不阻塞冻结）。
- **OQ-12″** bytes 传输方式 —— 实现阶段再决定。

**其余已关闭/不在范围（沿 DEC-030 轮登记）**：

- ~~OQ-8 命名/格式~~ —— 已裁（DEC-028 Part 1 + DEC-030/031）。
- ~~OQ-12 身份维度~~ —— 已裁 = path 非身份；~~OQ-12′ bytes 能力~~ —— 已冻结（§2.3）。
- ~~OQ-5 / OQ-19 / OQ-20 值集~~ —— 已裁：不合并 + 终局词表 + unknown→pending_review。V3 实现 = not started，不阻塞契约冻结。
- ~~OQ-14~~ —— 已裁 = Semantic Pending（DEC-028 Part 3 + DEC-031 确认）。
- ~~OQ-18~~ —— **已关闭（DEC-031）** = 五步序优先。
- ~~OQ-6~~ —— 已由 DEC-024 关闭（historical asset 隔离）。
- ~~OQ-11 当前面~~ —— 已裁 = 71 ADMITTED；扩产解耦且暂缓。
- ~~排期归属~~ —— 已由 DEC-026 裁定（数据动作五步序）。
- **OQ-21**（16 份呈现机制）与 **OQ-17**（存量 1 例）**未裁但不列入 DEC-031 冻结条件**——DEC-031 §六冻结条件仅 = Step 2 完成并验证（**已满足**）；此二项按未裁开放项继续跟踪，不阻塞冻结。
- V3 侧实现（IR 消费 / 身份绑定 / 语义 unknown 取值 / reviewable record 机制 / 验证链）—— **不在五步序内**，不构成冻结前置；实现排期 = UNKNOWN（§5.5 / Consumer Alignment v3 §4）。**DEC-031 已指明：V3 消费端验证链 = 下一阶段核心架构风险**（§2.3）。

---

## §9 Freeze Evidence 引用 + Freeze Object（`DEC-033` Task 2/3；未来任何人可从本契约找到冻结依据）

### 9.1 冻结证据定位（Freeze Evidence Registry）

**权威链**（Contract 条文 → Step 1 快照 → Step 2 回填 → 验证报告 → 最终复核）：

```text
Contract v0.2 条文（本文件；FC-1~FC-5 渊源 = DSH FREEZE-CANDIDATE-FINAL-v1 @ ff04f47）
   ↓
Step 1 interface snapshot — DSH commit e70807b
   data/interface_scope_snapshot_step1.json
   sha256 = b4f14524473d97b86f5d6a2f8bb03ee794727652a68fa4df4b00d794de98ad99
   + audit data/audit_snapshot_interface_scope_prebackfill.json
     sha256 = b11874c472a9fad3051f58c5fc46367dc8d7fc3e5ad961b266edfa55c142dd9c
     corpus_sha256 = 4ad3458ba11752d53b5885eb727e9da6ee5726b8eac2a5f0b0d81ca22fd19160（177 files）
   ↓
Step 2 backfill — DSH commit e70807b
   data/interface_scope_step2_backfill_report.json
   sha256 = d430cc2f6ebdf6553464f9751ade4b02eac6423f0509222a96c4c4666fb6eec1
   + audit data/audit_snapshot_interface_scope_postbackfill.json
     sha256 = 2cb980c7ca421f5a2c3615053cd3308d5ad1aa078083928724af88d4663a4096
     corpus_sha256 = 24af8f566e8e2356c29aa99e6b185c5f6f8eaf2df983bd4b6b0669684c240a10（177 files, verify ok）
   ↓
Verification Report — DSH commit e70807b
   Docs/COORDINATION/INTEGRATION/PREPROCESSING-STEP1-STEP2-VERIFICATION-REPORT-v1.md
   四项验证 PASS（87 清单 / 71-71 hash 一致 / IR 覆盖 71+16 / 16 pending）
   ↓
Final Check — DSH commit aad2237（DEC-027）
   data/freeze_evidence_final_check.json
   sha256 = a707738e5ceae7008eef7a7744d38b7b7ca1c052d936b49e0b31e59f1c5a5c33
   C1-C9 overall = VERIFIED（从磁盘字节独立重导，不信先前报告结论）
   Docs/COORDINATION/INTEGRATION/PREPROCESSING-CONTRACT-v0.2-FREEZE-EVIDENCE-v1.md（证据总账）
   ↓
Producer Final Confirmation — DSH commit 67f564c（DEC-028）
   七项文本要素 ALL PASS + 证据链 CONFIRMED complete + 五项 V3 能力 NOT IMPLEMENTED 记录
   Docs/COORDINATION/INTEGRATION/PREPROCESSING-CONTRACT-FREEZE-PRODUCER-CONFIRMATION-v1.md
```

**commit hash 汇总**（producer 域 = preprocessing 仓）：

| 环节 | commit | 内容 |
|---|---|---|
| Step 1 + Step 2 + Verification Report | `e70807b`（DSH `DEC-026`） | 快照 + 回填 ×87 + 验证报告 v1 |
| Freeze Evidence + Final Check（C1-C9 VERIFIED） | `aad2237`（DSH `DEC-027`） | 证据总账 + 独立复核 |
| Producer Final Confirmation（ALL PASS） | `67f564c`（DSH `DEC-028`） | 七要素核验 + F-1/F-2 WARNING 登记 |
| Contract 条文 FC 基线 | `ff04f47`（DSH `DEC-025`） | FREEZE-CANDIDATE-FINAL-v1（FC-1~FC-5） |

**脚本**（确定性、可复跑）：`scripts/interface_scope_step1_snapshot.py`（回填后重跑 fail-closed = 正确行为）/ `scripts/interface_scope_step2_backfill.py`（幂等可重入）/ `scripts/freeze_evidence_final_check.py`（只读复核）。

**R50 血统冻结解释**（防误读）：R50_input_baseline（356 files）为历史基线；回填后其 87 份 manifest 成员 DRIFT = **预期行为**，非数据事故；接口面完整性基线的现行承接者 = pre/post 配对双快照；未来审计对 R50 跑 verify 应预期 drift == 恰 87、missing 0。

### 9.2 Freeze Object（唯一冻结对象，`DEC-033` Task 3）

```text
Contract Freeze Candidate Artifact:
  repository:  kurt-wong/AITutors-v3（V3 = Consumer Owner 侧契约维护方；
               canonical ledger = DSH repo kurt-wong/Aitutors-preprocessing）
  document:    Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md
  sha256:      <见下方登记值；内容身份，随最终文本一次性确定>
  commit:      本文件最终文本所在 V3 commit（唯一）——其 hash 与 document sha256
               同步登记于 Docs/COORDINATION/state.yaml（agents.v3.commit + EB-009）
               与 Docs/COORDINATION/CURRENT.md（Evidence Locations）
  status:      READY FOR FREEZE / NOT FROZEN（待 Owner Freeze 令）
```

**唯一性纪律**：唯一冻结对象 = **上列单一 document**，其内容身份 = **单一 sha256**；**禁止多个 commit 均作为最终版本**。commit hash 与 document sha256 的登记放在**本文件之外**（state.yaml / CURRENT.md / log.md），以避免自引用（文件无法内嵌自身 sha256）。冻结后任何文本变更 = 新 document sha256 = 不再是本冻结对象。

**边界（保持）**：**Contract freeze ≠ implementation**——本冻结 = 裁决/契约文本冻结，不代表 V3 已具备任何验证能力（§5.6.1 五项 NOT IMPLEMENTED 不变）；**Requirement ≠ existing capability**——契约 REQUIREMENT 是下一阶段实现义务，不是现状描述。

---

## 边界声明

**本文件做了**：Owner B1/B2/B3 裁决的契约化（§1-4）+ DEC-B1 细化（§1.1）+ FINALIZATION v1 四项（§1.6/§1.7/§3.2+§4.1/§5.5）+ Interface Decision Finalization v1（DEC-027）+ Interface Finalization Revision v1（DEC-028：source identity 64hex + path 非身份 + 16 份 Semantic Pending + 语义层终局词表加 unknown + unknown→pending_review）+ Freeze Candidate Review v1（DEC-029：命名提案 + bytes 能力冻结 + 16 份四保证）+ Freeze Candidate Finalization v1（DEC-030：命名采纳 + 词面收口 + bytes/双状态确认 + 废止「Semantic Unavailable」）+ Owner Final Decision v1（DEC-031：四项原则终局确认 §0.1/§1.1/§1.6/§1.2a + Step 1/2 执行授权 §5.4/§8 + 机械冻结条件 §8 + 五项延期 §0.2/§6 + V3 下一阶段核心风险 = 消费端验证链 §2.3）+ Contract v0.2 最终冻结收口 Consumer 侧（DEC-032：Task 1 文本核验 · Task 2 五项 NOT IMPLEMENTED §5.6.1 · Task 3 实现边界 §5.6.2 + §1.3 · Task 4 16 份设计 §1.6 · 验证链 Gate→Admission §2.3）+ **Freeze Finalization Audit（DEC-033，本轮）**：**Task 1 冻结状态描述修正**（Step 1/2 历史「未开始」→ DONE / PASS，§8 + §5.4 + 状态头）· **Task 2 Freeze Evidence 引用登记**（§9.1，五类证据齐全）· **Task 3 Freeze Object 明确化**（§9.2，唯一冻结对象）· **Task 4 关键词再验证** · DA-1~37 · Implementation Status Table（§5.4）· v0.1 差异对照（§7）· 开放项 OQ-1~21 与冻结前提更新（§6/§8/§9）。每条款标 DECISION/OBSERVED/UNKNOWN/REQUIREMENT。

**本文件没做**：未把 DECISION 描述为已实现（§5.4 全表 `not started` / `DONE`（producer 侧）/ `deferred` / `UNKNOWN`；**§5.6.1 五项 NOT IMPLEMENTED 显式登记不变**）；未把契约描述为已冻结（DRAFT / **READY FOR FREEZE / NOT FROZEN**——机械冻结条件已满足，冻结令属 Owner 尚未下达）；未修改 V3 代码 / adapter / 数据库 schema / EB-008 / admission 逻辑；未修改 preprocessing；未执行任何数据动作（五步序中 Step 4 卫生 / Step 5 图片恢复未启动；16 份重跑 = 仅设计登记，未实施）；**未扩展冻结范围**（仍 = §0 六项）；**未把 §5.6 实现边界读作实现方案或排期承诺**（边界 ≠ 设计 ≠ 排期）；**未把 §9.2 Freeze Object 读作已冻结**（READY ≠ FROZEN）。

**EB-008 状态**：不因本文件变动。AuthorityIdentity 三元绑定（`evidence.py:28-29`）为既有冻结设计，本契约仅引用不改。

---

*v0.2 DRAFT（Freeze Candidate Finalized / READY FOR FREEZE / NOT FROZEN）— 2026-09-16，Claude（AITutors-v3 Consumer Owner）。本轮 = Contract v0.2 Freeze Finalization Audit·Consumer 侧（V3 `DEC-033`）：Task 1 状态修正（Step 1 DONE / Step 2 DONE / Verification PASS）· Task 2 Freeze Evidence 引用（§9.1）· Task 3 Freeze Object（§9.2）· Task 4 关键词再验证。上轮 = DEC-032 冻结收口登记；上上轮 = Owner Final Decision v1（DEC-031）。DA-1~37。V3 代码 `b5ddbe3`（其后仅文档提交，代码未变）· preprocessing `67f564c`（Step 1/2/验证 = `e70807b`；证据总账 = `aad2237`）· v0.1 `1fbaf5e`（未改）。**冻结范围 = §0 六项（未扩展）；状态 READY FOR FREEZE / NOT FROZEN——机械冻结条件已满足，待 Owner Freeze 令**。五项 V3 能力 NOT IMPLEMENTED 不变。DECISION ≠ IMPLEMENTATION。*
