# Gate B2-B5 Closure — Subjective / Sub-question / Material

**Version**: 1.2.0
**Date**: 2026-09-13
**Status**: **B2-B5 CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED**；
**BUG-V3-044 CLOSED**（Evidence Admission Boundary 封闭，§6 实现 + §7 对抗性审查）
**前置**: Gate C CLOSED (Phase 1 Evidence Authority Boundary Closure)
**性质**: 裁决与对账文档。§6 为 BUG-V3-044 修复实现记录；§7 为对抗性审查记录。

---

## 0. 为什么现在关闭

文档 74 自定的路线是：

```text
Evidence Promotion Contract → 157 E2E → Gate C Closure → B2-B5 Closure → Gate D
```

前三项均已完成（docs 75–79 + Gate C Closure，2026-09-13）。B2-B5 的唯一阻塞项
Gate C 已关闭，故本轮出具 B2-B5 正式关闭裁决。

同时，本文档承担一项**对账职责**：B2-B1～B2-B4 与 B2-B5 的实验结果此前只写进了
69 号与 docs 71–74，**未进入 log.md / Status.md 基线矩阵 / restart-prompt**，
69 号的 Gate B 状态块至今仍写 `B2-B5: OPEN`。本轮一并回写。

---

## 1. 各阶段裁决

| Phase | 裁决 | 证据 |
|-------|------|------|
| **B2-B5-A** Classification | **CLOSED — PASS** | 706 targets 分类；对抗审查后修正为 `B2-B5-B-v2-corrected` |
| **B2-B5-B** Domain Expressiveness | **CLOSED — PASS / SCOPE-BOUNDED** | S1 281 / S2 79 / S3 69 可表示，合计 429 |
| **B2-B5-C** Invalid Binding Route | **CLOSED — PASS** | 157 targets → `pending_review`；11/11 integration tests；C-2 157 E2E |
| **B2-B5-D** E2E Projection Safety | **CLOSED — PASS** | 13 tests；S1/S2/S3 正向投影 + 负向安全 + 零 fallback |

### 1.1 B2-B5-A — 目标分类

冻结语料 `gate_b2b5_frozen_testset.json`，706 个主观/子题/材料类 answer targets：

| Category | 说明 | Count |
|----------|------|------:|
| S1 | Standalone + Subjective | 469 |
| S2 | Composite + Sub-question | 94 |
| S3 | Composite + Material + Subjective | 143 |
| | **Total** | **706** |

对抗审查后按 `Legal address ≠ legal evidence` 原则重分类：

| v3_status | Count |
|-----------|------:|
| deterministically_representable | 429 |
| invalid_binding_evidence | 267 |
| suspicious_content | 10 |

invalid_binding_evidence 细分：

| Reason | Count |
|--------|------:|
| EMPTY_REGION | 120 |
| WRONG_REGION | 56 |
| EXPLANATION_REGION | 49 |
| SEPARATOR_REGION | 27 |
| QUESTION_REGION | 15 |

### 1.2 B2-B5-B — Domain 表达力（scope-bounded）

**Claim**: Schema 可表达 S1/S2/S3 结构。
**证据**: 429 个 deterministically representable targets。
**边界（正式声明）**: 只证明**已审计结构在冻结语料上的表达力**。
**不证明**: IR 能投影这些结构 / Compiler 能编译它们 / Admission 能正确持久化——
这三项由 B2-B5-D 承担。

### 1.3 B2-B5-C — Invalid Binding 路由

文档 71 §0 的正式撤回成立并保留：

| 原始主张 | 撤回后正确理解 |
|----------|----------------|
| Resolver reject invalid evidence | Resolver 只验结构有效性 |
| Gate reject invalid evidence | Gate grammar 返回 `None` → `pending_review` |
| 157 targets 自动 rejected | 157 targets 走人工裁决路径 |

**三态决策模型（已验证）**: `True`→可自动；`False`→pending_review；
`None`（无法确定）→pending_review。**None ≠ False**。

**157 targets 的正式状态**: `UNRESOLVED / REVIEW REQUIRED`。
既未证明它们是正确 binding，也未证明是错误 binding；它们不被自动准入，
也不被自动否决，全部进入 `pending_review` 人工裁决。

此项由 Gate C 的 C-2 157 E2E 独立验证：157 个 invalid binding cases 经完整
pipeline 后全部 fail-closed（非 auto_approve）。

### 1.4 B2-B5-D — 端到端投影安全

| 测试族 | 结果 |
|--------|------|
| Positive Projection（S1/S2/S3） | PASS — 层级不 flatten、shared material 不重复 |
| Negative Projection（WRONG/EXPLANATION/SEPARATOR/QUESTION region） | PASS — 全部 pending_review |
| Safety Properties | PASS — 0 search fallback / 0 LLM fallback / 0 source mutation |
| Corpus 关系 | PASS — 157 ⊂ 267 ⊂ 706 |

---

## 2. B2-B5-D 立下的四条冻结架构原则（保留）

```text
Principle 1: Source Address is location metadata, not semantic authority.
Principle 2: Evidence Claim is an explicit promotion event.
Principle 3: Only Validated Evidence may enter Semantic IR.
Principle 4: No downstream module may infer evidence validity from successful resolution.
```

核心命题 `Legal address ≠ legal evidence` 成立为 V3 Frozen Architecture 原则。

---

## 3. 残余项：Evidence Admission Boundary 仍未封闭（本轮实测确认）

文档 74 §6.3 曾记录一个 latent weakness，并明确**只做了 documented，未修复**。
Gate C 的关闭条件里也只要求「documented」而非「fixed」，故 Gate C 关闭不受影响。
但**本轮必须诚实确认：该 weakness 至今仍然开放。**

### 3.1 实测证据

探针：`backend/scripts/gate_b/gate_b2b5_closure_probe.py`
输出：`backend/scripts/gate_b/gate_b2b5_closure_probe.txt`

真实 pipeline（Resolver → IR → Compiler → Gate policy）四例：

| Case | 答案区内容 | decision |
|------|-----------|----------|
| C0 baseline | `1. A` | auto_approve（正确） |
| **C1** | `1. 【解答】A` | **auto_approve** |
| **C2** | `1. 【考点】本题考查词义辨析。【解答】A` | **auto_approve** |
| C3 control | 答案 `1. A` + 详解区另有内容 | auto_approve（正确，region map 正常工作） |

C1/C2 中答案 span 合法地位于 **answer structural region 内**，因此
structural overlap 检查不触发；题型是 strict-auto，因此 grammar-None 不触发；
Evidence Promotion Phase 1 是 **additive-only**（其自身文档明确「不改既有 pipeline 流程」），
只追加 ValidationEvent 日志，不新增准入判定。三层防御全部未拦截。

### 3.2 Grammar 边界刻画

`verify()` 对 single_choice 的实际行为：

| 答案文本 | single_choice | multiple_choice | true_false |
|----------|:---:|:---:|:---:|
| `A` / `1. A` | True | True | None |
| `【解答】A` | True | True | None |
| `【考点】…【解答】A` | True | True | None |
| `不选A，应选B` | None | True | None |
| **`见解析A页`** | **True** | True | None |
| **`参见教材A册第三章`** | **True** | True | None |
| `对` | None | None | True |
| `【解答】对` | None | None | None |

根因：`_option_letters()` 抽取答案文本中**任意** ASCII 字母。single_choice 只要求
「恰好一个字母 ∈ labels」，因此任何**恰好含一个 ASCII 字母**的正文（`A页`、`A册`）
都会被判 True。true_false 因走白名单 token 而不受影响。

`_option_letters()` 本身行为符合其职责（doc 74 §2.2 的定性成立）：
缺陷不在函数，在于**「该输入已是合法 answer evidence」这一前提没有被任何 Contract 证明**。

### 3.3 影响面

- Admission 以 `text=原始 span 切片` 持久化，并置 `verified_correct=True`。
  即 `参见教材A册第三章` 会被当作「已验证正确答案」写入题库。
- 触达条件：strict-auto 题型 + 答案区该行**恰好只含一个 ASCII 字母**的正文。
- **不在 B2-B5 关闭条件内**：B2-B5 语料是主观/子题/材料类（全部非 strict-auto），
  49 个 EXPLANATION_REGION targets 经 grammar-None 已 fail-closed。
  本 weakness 影响的是另一 population（strict-auto），与 B2-B5 正交。

### 3.4 正式处置

**已裁决并已修复（2026-09-13，见 §6）。** 本节保留原始发现与候选问题供追溯。

裁决结果：
- **采用 Q-A**（AnswerTokenContract 白名单）为主方案
- **Q-B 不采纳**——Evidence Contract 不扩大，留 Phase 2
- **Evidence Promotion Phase 1 不回退**
- **Gate D 延后**至 Grammar Contract 冻结后（准入规则未冻结时，Adapter 测试结果无意义）
- 题号前缀采用**剥离后白名单**：保留既有 `_LEAD_QN_RE` 剥离（20 §5.5 冻结切片规则），
  契约只校验剥后剩余部分，`1. A` 仍 approve

原始候选问题（已由上述裁决回答）：
- Q-A: strict-auto 的 answer 文本改为白名单 token 判定 → **采纳**
- Q-B: Evidence Claim 携带显式 `answer_form` 声明 → **留 Phase 2**
- Q-C: 降低 strict-auto 范围 → **不采纳**（破坏「可证明安全自动化」目标）

---

## 6. BUG-V3-044 修复实现（2026-09-13）

### 6.1 架构定位

修复属于**Semantic Answer Contract** 层，是 Gate C 已解决的两层之下的第三层：

```text
Source Binding Boundary        ✅ Gate B / B2-B 已解决
Evidence Authority Boundary    ✅ Gate C Phase 1 已解决
Semantic Answer Contract       ✅ 本轮（BUG-V3-044）封闭
Admission / Knowledge Layer
```

**不改变** Evidence Contract，**不回退** Evidence Promotion Phase 1。
数据流：

```text
ValidatedEvidence → QuestionType Contract → AnswerForm Validation
                  → Grammar.verify() → Admission
```

### 6.2 实现

`app/domains/gate/grammar.py`：

- 删除 `_option_letters()`（从任意正文抽 ASCII 字母，缺陷源头）
- 新增 `_SC_FORMS_RE`：单选五形态**全串锚定**白名单
- 新增 `_MC_TOKEN_RE`：多选「可选前缀 + 字母，仅既定分隔符」
- `true_false` 原有白名单 token 判定不变（实测本就不受污染影响）

单选允许形态：

| 形态 | 示例 |
|------|------|
| 裸字母 | `A` / `A、` |
| 括号字母 | `（A）` / `(A)` |
| 答案标记 | `【答案】D` |
| 分值前缀 | `（3分）D` / `(3分)D` |
| 字母 + 句号 | `D。` / `B.` / `A．` |

**全串锚定**是关键：任何尾巴一律拒。`（3分）D["莫问当年事"…]`、`【答案】D详见解析`、
`D。本句采用的是暗喻。` 全部 → None。

**`【答案】` 与解析类标记的原则区别**（非特判）：`【答案】` 是冻结的答案表头 token
（BUG-V3-031 grammar），`【答案】D` 直陈「答案是 D」；`【分析】`/`【解答】`/`【考点】`
之后是解释正文。二者语义不同，前者是答案 token 形态，后者是要挡的污染。

### 6.3 真实语料覆盖率实测（101 份）

初版白名单（仅裸字母/括号/顿号）在真实语料上造成可量化代价，据此做了二次扩展：

| 类别（旧 True → 新 None） | 数量 | 判定 |
|---|---:|---|
| `【答案】+字母` | 48 | ⚠️ 合法 → **扩展纳入** |
| `【分析】…` 解析类标记 | 48 | ✅ 修复收益 |
| 其他真实垃圾 | 35 | ✅ 修复收益 |
| `（N分）+字母` | 10 | ⚠️ 合法 → **扩展纳入** |
| `字母+句号` | 4 | ⚠️ 合法 → **扩展纳入** |

扩展后 single_choice 保持通过 **56 → 119**；剩余 82 个回归全部为真实垃圾
（解析正文 / 分值+字母+解析混合 / 同行多答案）。multiple_choice 剩余 139 个回归
同为垃圾（`（1）B；C；D；E （2）正丁烷…`、`A 区适合摆放蔬菜水果…` 等非 MC 答案）。

测量脚本：`backend/scripts/gate_b/gate_b044_coverage_measure.py`。

### 6.4 测试证据

新增（`tests/test_gate_grammar.py`）：

- `TestAnswerTokenContractPositive` — 正向：合法形态（含三种扩展）必须仍通过
- `TestAnswerTokenContractBoundaryAttacks` — 边界攻击：解析类标记、单字母正文、
  「合法 token + 额外正文」混合形态全部 None
- `TestAnswerTokenTypeIsolation` — 题型隔离：9 个非 strict-auto 题型恒 None 不受影响

反转 2 条原「记录缺陷」断言为「锁死修复」：

- `test_role_provenance.py::test_strict_auto_answer_token_contract_enforced`
- `test_b2b5_d_projection_safety.py::test_invalid_explanation_region_blocked`

回归：

```text
全量 pytest: 736 passed（修复前 660，+76 条测试），零失败
探针 C0/C3: auto_approve（正确，不变）
探针 C1/C2: auto_approve → pending_review（缺陷封闭）
```

### 6.5 显式不主张

1. 不主张所有 strict-auto 答案的语义正确性——grammar 只验格式可表达性（必要不充分）。
2. 不主张覆盖了全部真实答案形态——白名单按实测语料扩展，未见形态仍 fail-closed
   到 pending_review，不会错准入。
3. Q-B（Evidence Claim 显式 `answer_form`）留 Phase 2，本轮未做。

### 6.6 输入来源契约（实现层冻结，2026-09-13；Gate D §6.2 修订）

`Grammar.verify()` 的 `answer_text` 参数有**来源约束**，此前未显式声明，本轮补上：

> **AnswerTokenContract consumes the text slice of a `ResolvedSpan` in a**
> **`ResolvedRun` with `role=answer`. That span MUST have `granularity` as a**
> **character slice, `resolution_status ∈ {exact, normalized}`, and a**
> **`text_hash` matching the SealedSource text.**
> **It MUST NOT consume raw source / OCR text.**
> **Question-number prefixes are upstream boundary artifacts and SHALL NOT**
> **participate in answer-token validation.**

中文：

> AnswerTokenContract 的输入**必须**是某个 `ResolvedRun` 中 `role=answer` 的
> `ResolvedSpan` 所承载的文本切片，且该 span 满足：`granularity` 为字符切片、
> `resolution_status ∈ {exact, normalized}`、`text_hash` 与 SealedSource 原文
> 一致。**不得**消费裸 source / OCR 文本。题号前缀属上游边界产物，**不参与**
> 答案 token 合法性判断。

**为什么需要这条**：`verify()` 的签名只有 `answer_text: str`，类型上无法区分
「ResolvedSpan 的 char-span 切片」与「裸 OCR 原文」。契约此前只靠唯一生产调用方
（`policy.py::_leaf_grammar` 传 `leaf.answer.text`）自觉遵守，没有声明。

**Gate D 修订（2026-09-13，81 号 §3 发现 2 / §6）**：初版措辞写的是「必须
Resolver 产出」。该措辞有两处错误——(1) `ResolvedSpan` 无生产者字段
（`resolver/span.py:61-75`），「Resolver 产出」在数据上**不可验证**；
(2) Adapter 路径按设计绕过 Resolver，照字面执行会**非法排除整条 Manifest Path**。
根因是写了**机制**而非**不变量**。已改写为上表的不变量形式，生产者不作限定。

**为什么 20 §8.4 不需要 Errata**：冻结文本 20 §8.4 规定了「允许 token 集与
规范化」，但对 `answer_text` 的**来源完全沉默**——既未授权裸文本，也未要求
ResolvedSpan 切片。它是**未规定**，不是**规定错误**，故不属于 Contract Change，
不触发 `69 号` 的正式 Errata 四道门。Gate D 已过，Errata 现已 UNBLOCKED——
若日后需写入 20 §8.4 正文，可启动该流程，已挂入 §4 显式延期项。

**权威文档**：本节的完整版见 `81_GATE_D_ADAPTER_BOUNDARY.md` §6。

**顺带澄清（防过度承诺）**：grammar 只保证 **representation validity**（该答案
表示形式对该 canonical type 合法），**不保证 semantic correctness**（该答案语义上
正确）。两者分属不同层，不得混同：

| 层 | 能保证 |
|---|---|
| Resolver / Adapter | 找到哪里 |
| Evidence Authority | 证明来源 |
| Grammar | 表示形式合法 |
| Gate | 结构规则 |
| Semantic Model | 内容正确 |

---

## 7. BUG-V3-044 对抗性审查（2026-09-13）

**审查文件**：`backend/tests/test_bug044_adversarial_review.py`（62 项）
**纪律**：每个结论必须有真实测试证据；发现缺陷则让测试失败并如实报告，不自我合理化。

### 7.1 发现 1 — 真实缺陷：混合括号被接受（已修复）

`verify("single_choice", "（A)")` 曾返回 **True**，应为 None。

**根因**：正则写成 `[（(]([A-Za-z])[）)]`，`[）)]` 是字符类，开闭括号**各自独立匹配**，
故 `（A)` 与 `(A）` 混用括号都能通过。这超出用户裁决的允许形态（只授权 `（A）` 与 `(A)`）。

**修复**：拆为全角配对 `（A）` 与半角配对 `(A)` 两条独立分支；分值前缀同理。
拒绝已锁入 `test_gate_grammar.py` 契约测试。

**修复过程中自引入的第二个 bug（同轮捕获）**：`score_fw` 命名组只捕获数字
（`(?P<score_fw>\d+)`），字母在组外，会导致 `（3分）D` 正则匹配成功却返回 None。
已在测试前发现并修正为整段纳入命名组。

### 7.2 发现 2 — 此前覆盖率报告的方法学缺陷（已修正）

§6.3 报告的覆盖率数字基于**错误的测量语义**：用「行内全部剩余文本」而非 E 的
char-span 切片（本题号起点 → 下一题号起点，见 `resolver.py::_answer_span`）。

**修正后按 char-span 语义重扫 8166 条目**：

| 题型 | 保持通过 | 回归拒收 |
|---|---:|---:|
| single_choice | 552 | 261 |
| multiple_choice | 546 | 320 |
| true_false | 0（语料中未观测到） | 0 |

261 个 single_choice 回归细分：

| 类别 | 数量 | 占比 | 判定 |
|---|---:|---:|---|
| 真实垃圾（数学公式碎片 / 化学计量值 `6.4 g` / 夹带字母正文） | 205 | 78.5% | ✅ 修复收益 |
| 解析类【】标记（`【分析】…`） | 55 | 21.1% | ✅ 修复收益 |
| `A;`（字母+分号） | 1 | 0.4% | 离群点 |

`A;` 在 8166 条目中仅出现 **1 次**（0.01%），非系统性合法形态，是旧代码误抽字母的
离群点。**不扩展白名单**——fail-closed 到 pending_review 是正确处置。

multiple_choice 320 个回归经样例核对同为垃圾（`（1）B；C；D；E （2）正丁烷…`、
`A 区适合摆放蔬菜水果；B 区…` 等非 MC 答案内容）。

### 7.3 发现 3 — A2 测试断言过严（非生产缺陷）

`test_a2_multi_entry_line_char_span_stops_at_next_entry` 期望 `'1. A'`，
实际 `'1. A '`（尾随空格）。切片 `raw[start:nxt_start]` 天然含分隔空白，
`_clean_answer` 会 strip。**生产行为正确**，是测试字面量写错。
已改为断言真正属性：span 不含下一题号 + decision 正确。

### 7.4 通过项（均有测试证据）

| 维度 | 结论 | 证据 |
|------|------|------|
| A2 span 文本 | grammar 收到带题号前缀的 char-span，非裸 token | `test_a2_grammar_receives_qn_prefixed_span_not_bare_token` |
| A2 char-span 切片 | 同行多题时止于下一 qn 前 | `test_a2_multi_entry_line_char_span_stops_at_next_entry` |
| A3 绕过 | CJK 正文含单字母 / 零宽空格 / 标记后跟正文 → 全 None | `TestA3BypassAttempts`（15 项） |
| A5 multiple_choice | 常用形态保持；标记/分值前缀有效；尾巴拒绝 | `TestA5MultipleChoice`（5 项） |
| A6 true_false | 13 个 canonical token 保持；污染文本拒绝；不受 SC 白名单影响 | `TestA6TrueFalseInvariance` |
| A7 集成 | policy decision 跟随新 grammar；失败 → pending_review 非 terminal；其余层不误判 fail | `TestA7DownstreamIntegration`（4 项） |
| A8 无削弱 | 三态约定不变；STRICT_AUTO_TYPES 不变；`_option_letters` **真正删除** | `TestA8NoTestWeakening`（4 项） |
| A1 正则 | VERBOSE 模式未误伤；全角字母不接受；括号必须配对；全串锚定 | `TestA1RegexCorrectness`（6 项） |
| A4 测量 | char-span 语义下无「合法 token 被误拒」 | `test_a4_char_span_semantics_scan` |

### 7.5 审查后回归

```text
全量 pytest: 802 passed（审查前 736，+66 项），零失败
探针 C0/C3: auto_approve（正确，不变）
探针 C1/C2: pending_review（缺陷保持封闭）
```

---

## 4. Gate B 系列最终状态

```text
Gate A            : PASS / TEST-EVIDENCED
Gate B1           : CONDITIONAL PASS — Region Binding Contract 基本成立
Gate B2-A         : CLOSED — PASS / TEST-EVIDENCED（stem-only, three-task audit）
                    Stem: Legacy 47.1% vs Path B 96.8%（补强后 stem-only 口径）
Gate B2-B1        : CLOSED — PASS / SCOPE-BOUNDED
                    非 HTML option region 结构提取 99.6% (1065/1069)；对抗抽样 98.0% (49/50)
Gate B2-B2        : CLOSED — PASS / SCOPE-BOUNDED
                    MC answer extraction 99.8% (1176/1178)
Gate B2-B3-A      : CLOSED — Target Classification Audit
                    原 fill_in 70 → MC 误分类 36，真填空 34
Gate B2-B3-B      : CLOSED — PASS / DETERMINISTIC
                    34/34 resolved，fallback 0，determinism 10/10，negative 6/6 fail-closed
Gate B2-B3-C      : DEFERRED — Domain Contract dependency (F2/F4/F9)
Gate B2-B4-A      : CLOSED — HTML Target Classification
                    602 → Direct 507 / Excluded 95
Gate B2-B4-B      : CLOSED — PASS / DETERMINISTIC
                    507/507 resolved，fallback 0，determinism 10/10，negative 7/7 fail-closed
Gate B2-B4-C      : DEFERRED — Domain/Material dependency (H4/H5/H6)
Gate B2-B5        : CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED
Gate C            : CLOSED (Phase 1 Evidence Authority Boundary Closure)
Gate D            : CONTRACT CLOSED / IMPLEMENTATION NOT STARTED（81 号，2026-09-13）
Adapter 实现       : NOT STARTED（阻塞于 81 §5.4 三项前置）
Errata            : UNBLOCKED（Gate D 已过；Decision 项见 81 §9.1）
```

**显式延期项（不视为失败，不视为已完成）**：
- B2-B3-C（F2 multi-blank / F4 / F9）→ Domain Contract
- B2-B4-C（H4 colspan/rowspan / H5 mixed / H6 html+image）→ Domain/Material
- B2-B2 Unknown 125 triage → 仍未清
- Q-B Evidence Claim 显式 `answer_form` → Phase 2
- **Grammar 输入来源契约写入 20 §8.4 正文** → 正式 Errata（当前冻结在实现层，
  §6.6 / 81 号 §6；20 §8.4 对该点沉默而非写错，Errata 现已 UNBLOCKED）
- **Adapter 实现** → 阻塞于 81 号 §5.4 三项前置（V3 annotation schema 对外发布 /
  manifest schema 冻结 / SealedSource 版本绑定）

---

## 5. 结论

**Gate B2-B5: CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED**

已证明：
1. V3 Schema 能表达 S1/S2/S3 主观/子题/材料结构（scope-bounded）。
2. invalid binding evidence 全部进入 `pending_review`，不被自动准入也不被自动否决。
3. S1/S2/S3 可完成端到端投影，且零 search / LLM fallback / source mutation。
4. `Legal address ≠ legal evidence` 成立为冻结架构原则。
5. **Evidence Admission Boundary 已封闭**（§6，BUG-V3-044）——strict-auto 不再把
   解析正文误提升为 `verified_correct`。

未证明 / 显式不主张：
1. 不主张 429 个 representable targets 的语义正确性。
2. 不主张 157 个 invalid targets 的最终人工裁决结果。
3. 不主张 grammar 通过即语义正确——它只验格式可表达性（必要不充分）。

---

**下一步**: **Errata Decision**（不进入 Adapter 实现）→ V3 Annotation Contract
冻结 → Manifest Contract 冻结 → OQ-3 → OQ-2 → B2-B2 Unknown 125 triage →
Phase 2 Evidence Ledger → Path B Full Closure E2E → Adapter 实现（最后，
阻塞于 81 §5.4 三项前置，依赖链不可倒序）。
