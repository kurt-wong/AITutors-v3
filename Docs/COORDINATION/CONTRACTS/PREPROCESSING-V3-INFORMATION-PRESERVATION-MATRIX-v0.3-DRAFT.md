# Information Preservation Matrix v0.3

> **状态**：`CONTRACT FREEZE CANDIDATE` 配套 / **已同步 Owner Decisions P01–P25**
> **配套**：`PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` §P1 / §3 / §7 / **§16**
> **术语**：`Preprocessing` = `kurt-wong/Aitutors-preprocessing`；`AITutors-v3` = 当前 V3 系统；`Producer` **仅**作抽象架构角色（Contract §0）
> **字段来源**：live `*.manifest.json` + `resolver_ir.json` 实际键（非文档想象）
> **证据标签**：`OBSERVED`（字段存在/取值）/ `DERIVED`（归类）/ `DECISION`（P01–P25 落版）/ `OPEN`
>
> **本轮同步（Contract §16）**：新增 `options[]` / `option.label` / `option.text` / `option.provenance`；`options_lines` → **preserved**；`answer_table_unresolved` → **retained_as_uncertainty**；`flags` → **preserved / retained_as_uncertainty**（**P04 / P07 / P08**）。

## 列定义（12 问）

| 列 | 问题 |
|---|---|
| **PA** | Preprocessing 是否为 authority？ |
| **Keep** | V3 是否直接保留？ |
| **Canon** | 是否 canonicalize？ |
| **CanonRule** | canonicalization rule |
| **NeedEv** | 是否需要 evidence？ |
| **NeedProv** | 是否需要 provenance？ |
| **AllowUNK** | 是否允许 UNKNOWN？ |
| **GateUNK** | UNKNOWN 时 Gate 如何处理？ |
| **V3Derive** | 是否由 V3 再推导？ |
| **DeriveAuth** | 若推导，新 authority 是谁？ |
| **Loss** | 是否存在信息损失？ |
| **LossWhy** | 若有，为何允许？ |
| **NoMutation** | 如何验证无 silent semantic mutation？ |

P1 归类缩写：`pres` preserved · `canon` canonicalized · `ev` →evidence · `prov` →provenance · `v3d` →V3-derived · `unc` retained uncertainty · `unsup` explicitly unsupported · `rej` rejected

---

## A. Identity

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `source_file` | Preprocessing 提供 **locator only**（`DECISION` v0.2 ④） | 是（locator） | 否 | — | 否 | 是（作 locator 记录） | 否（缺失则无法装载） | BLOCK / not loaded | 否 | — | path 跨机不可解析（`OBSERVED`） | 允许：path 非 identity；identity 由 sha 决定 | 禁止用 path 做 identity 判定（代码级不变量） | `prov` |
| `source_content_sha256` | **Source Authority**（bytes）；Manifest 为声明 | 是（接口键） | 否 | 64 小写 hex 校验 | 是（M2 重算） | 是 | 否 | **BLOCK**（M1/M4 FAILED） | 否（V3 只验证不发明） | — | 无（可重算） | — | computed==manifest 才 VERIFIED | `pres` + `ev` |
| `identity_version` | Preprocessing 声明 | 是（Scope 判定输入） | 仅接受 `==2` | Interface Scope | 是 | 是 | 缺失→`MISSING_IDENTITY_VERSION` | **BLOCK** | 否 | — | v1 79 份被 Scope 拒 | 允许：接口面收缩；不 silent 升 v2 | 不得把 null/1 默认成 2 | `pres` / `rej`（出界） |
| `ir.source_sha256` / `provenance.source_version` | Preprocessing IR | 是（语义轴） | 否（与接口键同值映射） | 与 `source_content_sha256` 同值 | 是（M3） | 是 | IR 缺席→semantic PENDING | **BLOCK**（M5：VERIFIED+PENDING） | 否 | — | 无 | — | ir_sha!=manifest → PENDING 不 VERIFIED | `pres` |
| Manifest 整体 identity face | Preprocessing | 经 M1 | 否 | — | 是 | 是 | 否 | BLOCK | 否 | — | 无 | — | M1 fail-closed | `ev` |
| IR 整体 identity face | Preprocessing | 经 M3 | 否 | — | 是 | 是 | 缺 IR 可 PENDING | BLOCK | 否 | — | 无 | — | M4 语义轴独立 | `ev` |

---

## B. Unit / Question identity

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `unit_id` | Preprocessing | 是 | 否 | 原样 | 建议 | 是 | 否 | 缺 id → incomplete/rej | 可派生 span_id 前缀 | Canonical V3（派生名） | 无 | — | 禁止重编号冒充原 id | `pres` |
| `question_numbers` | Preprocessing（印刷/迁移主张） | 是 | 范围表示 `question_number_range` | 列表→字符串范围（可逆需保原列表） | 是（`basis`/`basis_evidence`） | 是 | 是（`unverified`） | pending_review / incomplete | 可拆 sub 派生 | V3 Derived（若拆题） | multi-q 小问不拆时子题粒度丢失（`OBSERVED`） | 允许：显式 `SUB_QUESTION_DECOMPOSITION_UNAVAILABLE`；非 silent | 原列表与 range 同时可回溯 | `pres`+`canon` |
| `printed_number` | Preprocessing Source Fact | 是 | 否 | — | 是 | 是 | 是 | UNKNOWN 不得当题号权威 | 否 | — | 596 `unknown`（`OBSERVED`） | 允许：诚实 UNKNOWN | 禁止用 `question_numbers` 冒充 printed | `pres`/`unc` |
| `section` | Preprocessing 展示元数据 | 是 | 否 | — | 建议 | 是 | 是 | 不单独 gate | 否 | — | 无 | — | — | `pres` |
| `section_ref` | Preprocessing | 是 | 否 | → `sections[].id` | 建议 | 是 | 是 | dangling → incomplete | 否 | — | 无 | — | 禁止重绑错误 section | `pres` |

---

## C. Structural content（行区间）

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `stem_lines` | Preprocessing | → IR content.stem + ResolvedSpan | representation | `[a,b]`→`line_refs` | 是 | 是 | 缺→incomplete | incomplete 不进 candidate（现势） | 否 | — | 无（71/71 锚定） | — | slice 只读不改写正文 | `prov`+`pres` |
| `options_lines` | Preprocessing（整块） | **是（preserved — P04.2 明令不得删除）** | representation | 同上 | 是 | 是 | 可缺 | choice 无 options → incomplete | 否（per-option 由 `options[]` 承载） | — | 无（Whole Options Region 与 `options[]` 并存） | — | 不得 fabricate A/B/C span | **`pres`** + `prov` |
| `options[]` | **Preprocessing structural fact**（`DECISION` P04.1） | 是 | 否（结构事实原样） | — | 是 | 是 | **否**（缺失 → fail closed） | choice 缺 per-option → `unresolved` / `INCOMPLETE` / `QC_FAIL` | **否**（AITutors-v3 不重新发现、不猜，P04） | — | 无 | — | 不得由 AITutors-v3 凭空创造或覆盖 Preprocessing fact | **`pres`** |
| `option.label` | **Preprocessing structural fact**（`DECISION` P04.1） | 是 | 否 | — | 是 | 是 | 否 | 同 `options[]` | 否 | — | 无 | — | **不得猜 label**（P04.4） | **`pres`** |
| `option.text` | **Preprocessing structural fact**（`DECISION` P04.1） | 是 | 否 | — | 是 | 是 | 否 | 同 `options[]` | 否 | — | 无 | — | **不得猜 text**（P04.4） | **`pres`** |
| `option.provenance` | Preprocessing evidence / provenance（`DECISION` P04.3） | 是 | representation | **多态**：`line_range` / `char_span_in_line` / `table_cell` / `multiple source spans` / other verifiable source provenance | 本身 | 本身 | 否 | 不可回溯 → fail closed | 否 | — | **禁止**硬编码"一 option 一行" | — | **不得猜 provenance**（P04.4）；须可被 AITutors-v3 验证 | **`ev`** + **`prov`** |
| `extra_lines` | Preprocessing | 是 | representation | 同上 | 是 | 是 | 可缺 | 通常不单独 gate | 否 | — | 弱语义 | 允许 | — | `prov` |
| `answer_lines` | Preprocessing | 是 | representation | 同上 | 是 | 是 | 可缺 | 缺 answer 视 QT 策略 | 答案表解析可派生 | V3 Derived（若再解析） | 答案表题号映射弱（502 unresolved） | 允许：flag 保留 | 不得猜答案内容覆盖 | `prov`+`unc` |
| `explanation_lines` | Preprocessing | 是 | representation | 同上 | 是 | 是 | **是**（允许缺失） | **不**因缺 explanation 拒核心入库（`PROPOSED` §8） | 可 Post-Admission 生成 | **V3 Derived**（generated） | 覆盖率 474/1664 | 允许：非 hard requirement | 生成物不得冒充 Preprocessing explanation | `prov` / `v3d` |
| `material_lines` | Preprocessing | 是 | representation | 同上 | 是 | 是 | 可缺 | composite 无 material 视规则 | 否 | — | 41 处与 questions 同区间 | 允许：flag/known fold；禁 silent 合并语义 | 原区间保留 | `prov` |
| `questions_lines` | Preprocessing | 是 | representation | 同上 | 是 | 是 | 可缺 | composite 需要 | 子题分解可派生 | V3 Derived | 同上 + multi-q 缺印刷号 54/148 | 同上 | 不得重切冒充原区间 | `prov` |
| `material_ref` | Preprocessing | 是 | 否 | → `materials` 键 | 是 | 是 | dangling→fail/incomplete | BLOCK 或 incomplete | 否 | — | 无（278/278 可解析） | — | 禁止改 ref 指向他物 | `pres` |

---

## D. Semantic metadata

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `unit_type` | Preprocessing legacy 主张 | original 保留 | **是（仅 OD-2 两条）** | 见 Contract §2.3 | 是（mapping event） | 是 | 非法值 | **UNKNOWN_UNIT_TYPE fail closed** | 否 | — | 无（必须双值可追溯） | — | 禁 QT→UT；禁 andalone→standalone | `canon`+`pres`(legacy) |
| `original_question_type` | Preprocessing 分类主张 | 是（verbatim） | 闭集内可映射 | 仅 Owner 授权 per-value | 建议 | 是 | 是 | UNKNOWN/incomplete；禁默认题型 | canonical QT 可派生 | Canonical V3 | `listening` 等未入闭集 | 允许：unsup/rej 显式 | 禁止“合理猜测”改题型 | `pres`/`canon`/`unc` |
| （其它 Preprocessing 语义标签） | Preprocessing | 视字段 | 仅授权映射 | — | 视情况 | 是 | 是 | fail closed | 可 | V3 Derived | — | — | 不得混 authority | `pres`/`v3d` |

---

## E. Evidence

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `answer_evidence` | Preprocessing（`DECISION` **P08**：不得静默丢失） | **是** / 转 EvidenceReference | 可 re-encode | 结构→证据对象 | 本身即 evidence | 是 | 是 | 无证据答案 → pending；**不自动改 Gate**（P14） | 否 | — | 历史 Artifact 可能整体缺失（`OBSERVED` prompt 版本差异） | 允许，**必须登记**（P08/P24） | **不得丢弃后假装无证据** | **`ev`** |
| `basis` | Preprocessing | 是 | 否 | 词表保留 | 是 | 是 | 是（`unverified`） | unknown 题号不得当权威 | 否 | — | 现 IR 已带 | — | 禁止 unverified→printed_as_is | `pres`/`unc` |
| `basis_evidence` | Preprocessing | 是 | 否 | 字符串+L 行号 | 本身即 evidence | 是 | 是（可空） | 空+unverified → UNKNOWN | 否 | — | 596 空 | 允许：诚实空 | 不得补造证据串 | `ev` |
| `source_lines`（provenance 内） | Preprocessing | 是 | representation | role→span | 是 | 本身 | 越界 → unresolved/rej | BLOCK/incomplete | 否 | — | 无 | — | 禁止改行号 | `prov` |
| `printed_provenance` | Preprocessing | 是 | 否 | 枚举保留 | 是 | 是 | 是（`unknown`） | UNKNOWN 不得当 printed 权威 | 否 | — | 596 unknown | 允许 | 禁止 unknown→source_line | `pres`/`unc` |

---

## F. Quality / uncertainty

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `flags` | Preprocessing | **必须保留（`DECISION` P08）** | 否 | 原样列表 | 是 | 是 | flags 本身即 uncertainty | **不自动进 Gate**（`DECISION` P14：须正式 Contract / Owner rule 才生效；**不得**自动变 reject 或 pending_review） | 可映射 review 队列 | Canonical V3 policy | 无 | — | **丢 flag = violation**；且不得未经规则自动改变 Gate | **`pres`** + **`unc`** |
| `qc_verdict` | Preprocessing QC | 是 | 否 | PASS/FAIL | 是 | 是 | FAIL | FAIL → 非 ADMITTED | 否 | — | 无 | — | 不得把 FAIL 读成 PASS | `pres` |
| `disposition` | Preprocessing | 是 | 否 | ADMITTED / REJECTED_QC_FAIL / REJECTED_V1 | 是 | 是 | 否 | 非 ADMITTED 不进语义消费面 | 否 | — | 无 | — | **ADMITTED ≠ V3 APPROVED** | `pres` |
| `answer_table_unresolved` | Preprocessing 解析/映射残留（`DECISION` **P07**） | 是 | 否 | 原样 flag | 本身 | 是 | 是 | **不自动进 Gate**（P08/P14） | **否**（AITutors-v3 不猜映射，P07） | — | 无（映射 unresolved ≠ 删除答案表信息，P07.4） | — | **不得**人为制造 Question→Answer 映射；**不得**简化为"答案表错误" | **`retained_as_uncertainty`** |
| `answer_number_mismatch` | Preprocessing 结构观察 flag | 是 | 否 | 原样 flag | 本身 | 是 | 是 | **不自动进 Gate**（P08/P14） | 否 | — | 无 | — | 不得静默重绑题号 | **`retained_as_uncertainty`** |
| `answers.unresolved` | Preprocessing 解析残留（`DECISION` P07.4） | **是（保留）** | 否 | 列表保留 | 是 | 是 | 是 | answer 不完整 → incomplete/flag；**不自动改 Gate** | 可再解析 | Preprocessing 重跑（P07），非 AITutors-v3 Derived 猜测 | 无 | — | **不得填假答案**；unresolved 必须显式保留 | **`unc`** |
| `confidence_state` | Preprocessing | 是 | 否 | 原样 | 建议 | 是 | 是 | 不单独决定 Gate | 否 | — | 无 | — | 不得抬升置信 | `pres` |
| `validation_issues` / `warnings` | Preprocessing `annotation_meta` | 是 | 否 | 原样 | 建议 | 是 | 是 | 可进 review | 否 | — | 无 | — | — | `pres`/`unc` |

---

## G. Provenance

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `source_file`（prov） | Preprocessing | 是 | 否 | locator | 否 | 本身 | 否 | 同 A | 否 | — | 同 A | 同 A | path≠identity | `prov` |
| `source_version`（prov） | Preprocessing | 是 | 否 | = 接口 sha 同值 | 是 | 本身 | 否 | 同 A | 否 | — | 无 | — | 不得改 hash | `prov` |
| `source_lines` | 见 E | | | | | | | | | | | | | `prov` |
| `manifest_file` | Preprocessing | 是 | 否 | locator | 建议 | 本身 | 缺→M1 fail | BLOCK | 否 | — | 无 | — | — | `prov` |
| `extraction_method` | Preprocessing | 是 | 否 | 原样（如 `line_span_v1`） | 建议 | 本身 | 是 | 不单独 gate | 否 | — | 无 | — | 不得改 method 美化 | `pres` |
| `qc_verdict`（prov） | Preprocessing | 是 | 否 | 同 F | 是 | 本身 | 否 | 同 F | 否 | — | 无 | — | — | `pres` |

---

## H. 汇总：允许 loss / discard 的显式清单

| 项 | 归类 | 理由 | 状态 |
|---|---|---|---|
| path 可移植性 | `prov` + locator 降级 | identity 由 content hash 决定（v0.2 ④ / **P03**） | 允许 |
| **`options_lines`（Whole Options Region）** | **`pres`** | **P04.2 明令不得删除**，与 `options[]` 并存 | **preserved** |
| **`options[]` / `option.label` / `option.text`** | **`pres`**（Preprocessing structural fact） | **P04.1**：AITutors-v3 不重新发现、不猜 | **required（P04，实现未授权）** |
| **`option.provenance`** | **`ev` + `prov`** | **P04.3** 多态 provenance；禁止"一 option 一行"硬编码 | **required（P04，实现未授权）** |
| ~~options per-label~~ | ~~`unsup`~~ | **已被 P04 取代**：不再允许按 `unsup` 长期挂账 | **CLOSED（P04）** |
| sub-question 拆分 | 结构事实保留（**P05**） | Composite 保持整体 Question；sub-question 为内部结构，识别 ≠ 拆分 | **DECISION（P05）** |
| **`answer_table_unresolved`** | **`retained_as_uncertainty`** | **P07**：映射 unresolved ≠ 删除答案表信息（P07.4）；禁止猜测映射 | **CLOSED（P07）** |
| **`answer_number_mismatch`** | **`retained_as_uncertainty`** | 结构观察 flag，不静默重绑题号 | **DECISION（P08/P14）** |
| **`flags` / `basis` / `basis_evidence` / `answer_evidence`** | **`pres` + `unc` / `ev`** | **P08**：属 Preprocessing evidence / provenance / review signal，**非** Gate authority | **CLOSED（P08）** |
| 596 printed provenance unknown | `unc` | 诚实 UNKNOWN | 允许 |
| 真正 discard | 仅 §7.5 条件 | 默认禁止（**P24**：不得 silent discard） | 若需 discard 清单外字段 → **STOP + 记录 + 等 Owner**（P25） |

---

## I. 验证 “无 silent semantic mutation” 的检查点（`PROPOSED`）

1. 每个 canonical 值可回指 Preprocessing original + mapping event id。
2. UNKNOWN/`unverified`/`unresolved` 计数在转换前后可对账（允许 representation 变化，不允许归零且无解释）。
3. `andonline/andalone` 类非法值不得出现于 canonical 输出。
4. explanation：`producer_explanation` 与 `generated_explanation` 物理/逻辑分离。
5. answer：source answer 与 derived answer 分 authority。
6. Preservation Matrix 的 P1 归类与实现日志一致（未来 acceptance）。

*End of Information Preservation Matrix v0.3 — CONTRACT FREEZE CANDIDATE 配套（Owner Decisions P01–P25 已同步）.*
