# Information Preservation Matrix v0.3 — DRAFT

> **状态**：`DRAFT` / `NON-AUTHORITATIVE` / `NOT FROZEN`
> **配套**：`PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` §P1 / §3 / §7
> **字段来源**：live `*.manifest.json` + `resolver_ir.json` 实际键（非文档想象）
> **证据标签**：`OBSERVED`（字段存在/取值）/ `DERIVED`（归类）/ `PROPOSED`（消费规则）/ `OPEN` / `OWNER DECISION REQUIRED`

## 列定义（12 问）

| 列 | 问题 |
|---|---|
| **PA** | Producer 是否为 authority？ |
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
| `source_file` | Producer 提供 **locator only**（`DECISION` v0.2 ④） | 是（locator） | 否 | — | 否 | 是（作 locator 记录） | 否（缺失则无法装载） | BLOCK / not loaded | 否 | — | path 跨机不可解析（`OBSERVED`） | 允许：path 非 identity；identity 由 sha 决定 | 禁止用 path 做 identity 判定（代码级不变量） | `prov` |
| `source_content_sha256` | **Source Authority**（bytes）；Manifest 为声明 | 是（接口键） | 否 | 64 小写 hex 校验 | 是（M2 重算） | 是 | 否 | **BLOCK**（M1/M4 FAILED） | 否（V3 只验证不发明） | — | 无（可重算） | — | computed==manifest 才 VERIFIED | `pres` + `ev` |
| `identity_version` | Producer 声明 | 是（Scope 判定输入） | 仅接受 `==2` | Interface Scope | 是 | 是 | 缺失→`MISSING_IDENTITY_VERSION` | **BLOCK** | 否 | — | v1 79 份被 Scope 拒 | 允许：接口面收缩；不 silent 升 v2 | 不得把 null/1 默认成 2 | `pres` / `rej`（出界） |
| `ir.source_sha256` / `provenance.source_version` | Producer IR | 是（语义轴） | 否（与接口键同值映射） | 与 `source_content_sha256` 同值 | 是（M3） | 是 | IR 缺席→semantic PENDING | **BLOCK**（M5：VERIFIED+PENDING） | 否 | — | 无 | — | ir_sha!=manifest → PENDING 不 VERIFIED | `pres` |
| Manifest 整体 identity face | Producer | 经 M1 | 否 | — | 是 | 是 | 否 | BLOCK | 否 | — | 无 | — | M1 fail-closed | `ev` |
| IR 整体 identity face | Producer | 经 M3 | 否 | — | 是 | 是 | 缺 IR 可 PENDING | BLOCK | 否 | — | 无 | — | M4 语义轴独立 | `ev` |

---

## B. Unit / Question identity

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `unit_id` | Producer | 是 | 否 | 原样 | 建议 | 是 | 否 | 缺 id → incomplete/rej | 可派生 span_id 前缀 | Canonical V3（派生名） | 无 | — | 禁止重编号冒充原 id | `pres` |
| `question_numbers` | Producer（印刷/迁移主张） | 是 | 范围表示 `question_number_range` | 列表→字符串范围（可逆需保原列表） | 是（`basis`/`basis_evidence`） | 是 | 是（`unverified`） | pending_review / incomplete | 可拆 sub 派生 | V3 Derived（若拆题） | multi-q 小问不拆时子题粒度丢失（`OBSERVED`） | 允许：显式 `SUB_QUESTION_DECOMPOSITION_UNAVAILABLE`；非 silent | 原列表与 range 同时可回溯 | `pres`+`canon` |
| `printed_number` | Producer Source Fact | 是 | 否 | — | 是 | 是 | 是 | UNKNOWN 不得当题号权威 | 否 | — | 596 `unknown`（`OBSERVED`） | 允许：诚实 UNKNOWN | 禁止用 `question_numbers` 冒充 printed | `pres`/`unc` |
| `section` | Producer 展示元数据 | 是 | 否 | — | 建议 | 是 | 是 | 不单独 gate | 否 | — | 无 | — | — | `pres` |
| `section_ref` | Producer | 是 | 否 | → `sections[].id` | 建议 | 是 | 是 | dangling → incomplete | 否 | — | 无 | — | 禁止重绑错误 section | `pres` |

---

## C. Structural content（行区间）

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `stem_lines` | Producer | → IR content.stem + ResolvedSpan | representation | `[a,b]`→`line_refs` | 是 | 是 | 缺→incomplete | incomplete 不进 candidate（现势） | 否 | — | 无（71/71 锚定） | — | slice 只读不改写正文 | `prov`+`pres` |
| `options_lines` | Producer（整块） | 是（整块 span） | representation | 同上 | 是 | 是 | 可缺 | choice 无 options → incomplete | 需 per-label 才完整 | — | **per-label 缺失**（`OBSERVED` adapter GAP） | 允许：显式 `OPTION_LABEL_SPAN_UNAVAILABLE` | 不得 fabricate A/B/C span | `prov`+`unsup`(label) |
| `extra_lines` | Producer | 是 | representation | 同上 | 是 | 是 | 可缺 | 通常不单独 gate | 否 | — | 弱语义 | 允许 | — | `prov` |
| `answer_lines` | Producer | 是 | representation | 同上 | 是 | 是 | 可缺 | 缺 answer 视 QT 策略 | 答案表解析可派生 | V3 Derived（若再解析） | 答案表题号映射弱（502 unresolved） | 允许：flag 保留 | 不得猜答案内容覆盖 | `prov`+`unc` |
| `explanation_lines` | Producer | 是 | representation | 同上 | 是 | 是 | **是**（允许缺失） | **不**因缺 explanation 拒核心入库（`PROPOSED` §8） | 可 Post-Admission 生成 | **V3 Derived**（generated） | 覆盖率 474/1664 | 允许：非 hard requirement | 生成物不得冒充 Producer explanation | `prov` / `v3d` |
| `material_lines` | Producer | 是 | representation | 同上 | 是 | 是 | 可缺 | composite 无 material 视规则 | 否 | — | 41 处与 questions 同区间 | 允许：flag/known fold；禁 silent 合并语义 | 原区间保留 | `prov` |
| `questions_lines` | Producer | 是 | representation | 同上 | 是 | 是 | 可缺 | composite 需要 | 子题分解可派生 | V3 Derived | 同上 + multi-q 缺印刷号 54/148 | 同上 | 不得重切冒充原区间 | `prov` |
| `material_ref` | Producer | 是 | 否 | → `materials` 键 | 是 | 是 | dangling→fail/incomplete | BLOCK 或 incomplete | 否 | — | 无（278/278 可解析） | — | 禁止改 ref 指向他物 | `pres` |

---

## D. Semantic metadata

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `unit_type` | Producer legacy 主张 | original 保留 | **是（仅 OD-2 两条）** | 见 Contract §2.3 | 是（mapping event） | 是 | 非法值 | **UNKNOWN_UNIT_TYPE fail closed** | 否 | — | 无（必须双值可追溯） | — | 禁 QT→UT；禁 andalone→standalone | `canon`+`pres`(legacy) |
| `original_question_type` | Producer 分类主张 | 是（verbatim） | 闭集内可映射 | 仅 Owner 授权 per-value | 建议 | 是 | 是 | UNKNOWN/incomplete；禁默认题型 | canonical QT 可派生 | Canonical V3 | `listening` 等未入闭集 | 允许：unsup/rej 显式 | 禁止“合理猜测”改题型 | `pres`/`canon`/`unc` |
| （其它 Producer 语义标签） | Producer | 视字段 | 仅授权映射 | — | 视情况 | 是 | 是 | fail closed | 可 | V3 Derived | — | — | 不得混 authority | `pres`/`v3d` |

---

## E. Evidence

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `answer_evidence` | Producer | 是 / 转 EvidenceReference | 可 re-encode | 结构→证据对象 | 本身即 evidence | 是 | 是 | 无证据答案 → pending | 否 | — | V3 annotation 契约未 1:1（`OBSERVED` CONSUMER GAP） | 允许暂 unsup，**必须登记** | 不得丢弃后假装无证据 | `ev`/`unsup` |
| `basis` | Producer | 是 | 否 | 词表保留 | 是 | 是 | 是（`unverified`） | unknown 题号不得当权威 | 否 | — | 现 IR 已带 | — | 禁止 unverified→printed_as_is | `pres`/`unc` |
| `basis_evidence` | Producer | 是 | 否 | 字符串+L 行号 | 本身即 evidence | 是 | 是（可空） | 空+unverified → UNKNOWN | 否 | — | 596 空 | 允许：诚实空 | 不得补造证据串 | `ev` |
| `source_lines`（provenance 内） | Producer | 是 | representation | role→span | 是 | 本身 | 越界 → unresolved/rej | BLOCK/incomplete | 否 | — | 无 | — | 禁止改行号 | `prov` |
| `printed_provenance` | Producer | 是 | 否 | 枚举保留 | 是 | 是 | 是（`unknown`） | UNKNOWN 不得当 printed 权威 | 否 | — | 596 unknown | 允许 | 禁止 unknown→source_line | `pres`/`unc` |

---

## F. Quality / uncertainty

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `flags` | Producer | **必须保留** | 否 | 原样列表 | 是 | 是 | flags 本身即 uncertainty | 现势：**未进 Gate 策略**（CONSUMER GAP） | 可映射 review 队列 | Canonical V3 policy | **当前消费缺口** | 不允许 silent 丢 flag | 丢 flag = violation | `unc` |
| `qc_verdict` | Producer QC | 是 | 否 | PASS/FAIL | 是 | 是 | FAIL | FAIL → 非 ADMITTED | 否 | — | 无 | — | 不得把 FAIL 读成 PASS | `pres` |
| `disposition` | Producer | 是 | 否 | ADMITTED / REJECTED_QC_FAIL / REJECTED_V1 | 是 | 是 | 否 | 非 ADMITTED 不进语义消费面 | 否 | — | 无 | — | **ADMITTED ≠ V3 APPROVED** | `pres` |
| `answers.unresolved` | Producer 解析残留 | 是 | 否 | 列表保留 | 是 | 是 | 是 | answer 不完整 → incomplete/flag | 可再解析 | V3 Derived | 502 级 flag | 允许 | 不得填假答案 | `unc` |
| `confidence_state` | Producer | 是 | 否 | 原样 | 建议 | 是 | 是 | 不单独决定 Gate | 否 | — | 无 | — | 不得抬升置信 | `pres` |
| `validation_issues` / `warnings` | Producer `annotation_meta` | 是 | 否 | 原样 | 建议 | 是 | 是 | 可进 review | 否 | — | 无 | — | — | `pres`/`unc` |

---

## G. Provenance

| Field | PA | Keep | Canon | CanonRule | NeedEv | NeedProv | AllowUNK | GateUNK | V3Derive | DeriveAuth | Loss | LossWhy | NoMutation | P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `source_file`（prov） | Producer | 是 | 否 | locator | 否 | 本身 | 否 | 同 A | 否 | — | 同 A | 同 A | path≠identity | `prov` |
| `source_version`（prov） | Producer | 是 | 否 | = 接口 sha 同值 | 是 | 本身 | 否 | 同 A | 否 | — | 无 | — | 不得改 hash | `prov` |
| `source_lines` | 见 E | | | | | | | | | | | | | `prov` |
| `manifest_file` | Producer | 是 | 否 | locator | 建议 | 本身 | 缺→M1 fail | BLOCK | 否 | — | 无 | — | — | `prov` |
| `extraction_method` | Producer | 是 | 否 | 原样（如 `line_span_v1`） | 建议 | 本身 | 是 | 不单独 gate | 否 | — | 无 | — | 不得改 method 美化 | `pres` |
| `qc_verdict`（prov） | Producer | 是 | 否 | 同 F | 是 | 本身 | 否 | 同 F | 否 | — | 无 | — | — | `pres` |

---

## H. 汇总：允许 loss / discard 的显式清单

| 项 | 归类 | 理由 | 状态 |
|---|---|---|---|
| path 可移植性 | `prov` + locator 降级 | identity 由 content hash 决定（v0.2 ④） | 允许 |
| options per-label | `unsup` | Producer 未提供粒度；禁止 fabricate | 允许但必须登记 GAP |
| sub-question 拆分 | `unsup` → 单 sub 结构翻译 | 显式 `SUB_QUESTION_DECOMPOSITION_UNAVAILABLE` | 允许但必须登记 |
| answer 表未解析单元 | `unc` | flag 保留，不猜 | 允许 |
| 596 printed provenance unknown | `unc` | 诚实 UNKNOWN | 允许 |
| 真正 discard | 仅 §7.5 条件 | 默认禁止 | `OWNER DECISION REQUIRED` 若需 discard 清单外字段 |

---

## I. 验证 “无 silent semantic mutation” 的检查点（`PROPOSED`）

1. 每个 canonical 值可回指 Producer original + mapping event id。
2. UNKNOWN/`unverified`/`unresolved` 计数在转换前后可对账（允许 representation 变化，不允许归零且无解释）。
3. `andonline/andalone` 类非法值不得出现于 canonical 输出。
4. explanation：`producer_explanation` 与 `generated_explanation` 物理/逻辑分离。
5. answer：source answer 与 derived answer 分 authority。
6. Preservation Matrix 的 P1 归类与实现日志一致（未来 acceptance）。

*End of Information Preservation Matrix v0.3 DRAFT.*
