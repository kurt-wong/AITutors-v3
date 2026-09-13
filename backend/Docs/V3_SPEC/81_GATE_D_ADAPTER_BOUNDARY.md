# 81 — Gate D：Adapter Boundary 契约冻结

**Date**: 2026-09-13
**Status**: **Gate D — CONTRACT CLOSED / IMPLEMENTATION NOT STARTED**
**权威范围**: I-5-2 Adapter 的边界契约。本文档是 Gate D 的唯一权威裁决。

> **状态措辞说明**：`CLOSED` 在本项目其它 Gate 中表示「该 Gate 的要求已满足并有
> 测试证据」。Gate D 的要求是**契约裁决**，不是实现验收，故不用裸 `CLOSED`。
> `CONTRACT CLOSED` = 边界契约已冻结；`IMPLEMENTATION NOT STARTED` = `backend/app`
> 中无 Adapter 代码，且开工被 §5.4 三项前置阻塞。两者必须分开表述。
**前置**: Gate A PASS / Gate C CLOSED / BUG-V3-044 CLOSED / Gate B 见下
**Gate B 实际状态（依据 82 §3，2026-09-13）**:
- B1 **CONDITIONAL PASS**（option Role Validity 51.8% / answer 49.1%；Structural 未评估）
- B2-A **CLOSED — PASS**（stem-only）
- B2-B1 / B2-B2 / B2-B3-A/B / B2-B4-A/B / B2-B5 **CLOSED — PASS / SCOPE-BOUNDED**
- B2-B3-C / B2-B4-C **DEFERRED**（Domain / Material 依赖）
- **Gate B 整体 = NOT CLOSED**

> ⚠️ **更正（2026-09-13，82 号 §4-C3）**：本行此前写的是「Gate B 系列 CLOSED
> （80 号）」，**过度陈述了 80 号**。`80:421` 自己写 `B1 CONDITIONAL PASS`，
> `80:432`/`80:437` 写两项 DEFERRED。按 82 §3.2 聚合规则——**存在 CONDITIONAL
> 或 DEFERRED 子项时，父 Gate 不得记为 PASS 或 CLOSED**——Gate B 整体 NOT CLOSED。
> Gate D 是**契约裁决**，其成立不依赖 Gate B 整体关闭；但**发布 67 号等
> CHANGE-4/5 变更依赖**（见 82 §2）。

**出口标准（用户裁决 2026-09-13）**: **本轮只冻结契约，不要求实现**。

---

## 0. 为什么是现在

Gate D 此前被 `BLOCKED BY Grammar Contract`（80 号 §3）。BUG-V3-044 修复并通过
对抗性审查后，Grammar Contract 已冻结（80 号 §6/§7），阻塞解除。

Adapter 是 V3 与外部 preprocessing 项目之间的唯一接缝。**在接缝两侧的权责未冻结
之前写任何 Adapter 代码，都会把边界含糊固化进实现。** 因此本轮只做契约。

---

## 1. Gate D 的权威定义（69 号，不改写）

> I-5-2 Adapter 必须保持为 **Contract Translator**，不得引入：
> - 第二事实来源
> - 第二 Resolver
> - 隐式 fuzzy matching
> - 自主 Source 内容生成
> - 独立 semantic decision

本定义五条禁令**全部维持**，本文档不放宽任何一条。

---

## 2. 开题勘查事实

| 检查项 | 结果 |
|---|---|
| `backend/app` 中 adapter / preprocessing 模块 | **不存在** |
| manifest 解析代码 | **不存在** |
| I-5-1 的 14 项实验证据（66 §9 声称） | **全仓无脚本、无测试、`git log --all --diff-filter=A` 零提交** |
| 冻结的 manifest schema | **V3 Spec 中无**（manifest 属外部 preprocessing 项目） |

**因此 Gate D 不是代码审查，是契约裁决。** 而 I-5-1 的实验结论（含「21/21 ready
IR」）当前**不可复现**，不能作为 PASS 依据——本项目纪律要求每个结论有真实测试
证据，且度量脚本必须可审计（40 §5）。

---

## 3. 发现（均有代码证据）

### 发现 1 — `Bypasses: Annotation` 与 `IRBuilder.build` 签名直接冲突 🔴

66 §7 声称 Adapter 路径绕过 Annotation。实际代码：

```python
# backend/app/domains/compile/ir.py:87
def build(
    resolved_run: ResolvedRun,
    annotation_payload: dict,        # ← 必需
    source_version_id: uuid.UUID,
    annotation_id: uuid.UUID,
) -> IR:
```

`annotation_payload` 驱动**全部语义结构**：`semantic_units[]` 决定题目列表、
`unit_id` 决定 span_id 命名、`unit_type` 决定 standalone/composite、`content{}`
决定存在哪些 role、`shared_components`/`sub_questions` 决定材料与子题。
全量测试中的调用均为双参齐传。

更关键的是 span_id 约定（`ir.py:64-76`）：

```python
f"sp-{unit_id}.stem" / f"sp-{unit_id}.answer" / f"sp-{unit_id}.option.{label}"
```

**ResolvedSpan 的身份由 annotation 的 unit_id 与 role 反推。** Adapter 若不知道
annotation，连 span_id 都构造不出来，IRBuilder 更找不到该 span。

**结论**：`Bypasses: Annotation` 在当前 IRBuilder 下**结构上不可能**。
已按裁决修正为 `Bypasses: Resolver only`（§5）。

### 发现 2 — Grammar 输入来源契约过窄（本轮早前自引入，已修正）🔴

本轮早前冻结的措辞是「`answer_text` **必须**是 Resolver 产出的标准化 answer
span」。两个事实使该措辞站不住：

1. **`ResolvedSpan` 无生产者字段**（`resolver/span.py:61-75`：只有 span_id /
   source_version_id / role / line_refs / offsets / text_hash /
   resolution_status / evidence）。「Resolver 产出」**在数据上不可验证**。
2. Adapter 路径按设计绕过 Resolver。照该措辞字面执行，**整条 Adapter 路径非法**。

**根因**：写的是**机制**（谁产出），不是**不变量**（该 span 具备哪些性质）。
正确不变量见 §6。已修正 `grammar.py` 三处 docstring 与 80 号 §6.6。

### 发现 3 — I-5-1 实验证据不可复现 🟠

66 §9 报告 14 项测试，含关键结论「IRBuilder with direct ResolvedSpans →
21/21 ready」。全仓搜索：`backend/scripts/` 无脚本、`backend/tests/` 无测试、
git 历史对 `*i5*` / `*adapter*` 零提交。

**处置**：I-5-1 结论降级为**方向性参考**，不作为 Gate D PASS 依据。
复现实验列入延期项（§8）。

### 发现 4 — 66 §10 的结论本身说明 Adapter 无法自洽 🟠

66 §9 测试 5/11 失败后，66 §10 写道：

> `option_tokens()` is insufficient; **Adapter needs own parser**
> Option spans must be split by character offset

但 66 §7 明令 Adapter 禁止「any content parsing or structural inference」。

**为了让 Adapter 工作而给它加 parser，恰好违反它自己的禁令。** 66 §10 把两个
gap（`answer_text` 缺失、options 未预切）判给 preprocessing 是正确的——但那意味着
**Adapter 在 manifest 增强之前覆盖率接近零**，而现在 manifest 既未增强、schema
也未冻结。

---

## 4. 用户裁决（2026-09-13）

| 问题 | 裁决 |
|---|---|
| Adapter 路径的 `annotation_payload` 从哪里来？ | **preprocessing 产出 V3 形制 annotation** |
| Gate D 的出口标准？ | **本轮只冻结契约，不要求实现** |

**裁决含义**：preprocessing 负责语义结构识别并产出**符合 V3 annotation schema**
的 payload + line_refs manifest；V3 Adapter 只做机械的 line_ref 展开与 hash 校验，
**不碰任何语义**。方向性与 74 号一致——「preprocessing 必须满足 V3 Evidence
Contract，而不是反过来 V3 按照 preprocessing 的 contract 设计」。

---

## 5. 冻结的 Adapter Contract

### 5.1 数据流

```text
SealedSource (DocumentSourceVersion + DocumentSourceLine[])
        │
        ▼
  preprocessing（外部项目，可选上游）
        │
        ├── annotation_payload   ← V3 形制（schema 见 §5.4）
        └── manifest.json        ← line_refs + 结构声明
        │
        ▼
     Adapter（V3 侧，纯机械）
        │
        ▼
   ResolvedRun（含 ResolvedSpan[]）
        │
        ▼
   IRBuilder.build(resolved_run, annotation_payload, ...)
        │
        ▼
   Compiler → Gate → Admission
```

### 5.2 Bypasses

> **Bypasses: Resolver only.**
> **Does NOT bypass Annotation — Annotation 的语义工作由 preprocessing 承担，
> 产出 V3 形制 payload。**

**「绕过 Resolver」的准确含义**：绕过的是 Legacy Resolver 的 **search / resolve
机制**（正则搜索 Source、模糊匹配、消歧），**不是绕过 Source Binding 本身**。
Adapter 以「验证」替代「搜索」——manifest 直接给出 line_ref，Adapter 只做
精确校验。这是 Doc 67 的核心架构变化：**把搜索问题变成验证问题。**

```text
                    ┌─ Native Resolver（search/resolve）─┐
Annotation ─────────┤                                      ├── ResolvedRun
                    └─ Path B Adapter（verify only）──────┘
                                                            │
                                                            ▼
                                                      same IRBuilder
                                                            ▼
                                                      same Compiler → Gate → Admission
```

**Adapter 可以改变「如何得到 `ResolvedSpan`」，不能改变「`ResolvedSpan` 之后
系统如何理解题目」。** 下游 IRBuilder / Compiler / Gate 对两条路径完全一致。

66 §7 原文「Bypasses: Annotation, Resolver」为**表述错误**，已在 66 号就地更正。

### 5.3 V3 Native Path 不受影响

```text
preprocessing 缺席时：Source → Annotation → Resolver → IRBuilder → …（现状，不变）
preprocessing 在场时：Source → preprocessing → Adapter → IRBuilder → …
```

两条路径**同构于 `ResolvedRun`**，下游 IRBuilder / Compiler / Gate 完全一致。
V3 Native Path **必须独立成立**（74 号），Adapter 路径是可选加速，不是替代。

### 5.4 V3 先冻结消费契约，preprocessing 再实现（方向不可颠倒）

**契约方向（冻结）**：V3 首先冻结它**自己要消费**的 Annotation / Manifest 契约；
preprocessing 必须**实现**该契约。**不是** preprocessing 自行设计 annotation，
再由 V3 Adapter 去适配——后者会把 preprocessing 变成事实上的 schema 制定者，
违反 74 号「preprocessing 必须满足 V3 Evidence Contract，而不是 V3 为
preprocessing 定制」。

```text
V3 Annotation Contract（V3 冻结，V3 拥有）
        ↓
preprocessing 必须满足
        ↓
annotation_payload + manifest
        ↓
Adapter（V3 侧，纯机械）
        ↓
ResolvedRun → IRBuilder → …
```

在下列条件全部满足之前，Adapter **不得开工**：

1. **V3 annotation schema 冻结并对外发布**——**由 V3 定义并冻结**，preprocessing
   照它产出 payload。这是 Errata 链条上的独立一项，不是 Adapter 实现的副产品。
2. **manifest schema 冻结**，至少含：
   - `answer_text`：每题抽取后的答案值（66 §10 gap 1）
   - per-option span（行范围或字符偏移），非单一 `options_lines`（gap 2）
   - `line_refs` 与 SealedSource 版本绑定
3. **SealedSource 版本绑定机制**：manifest 必须声明它指向哪个
   `source_version_id`，跨版本引用 fail-closed。

### 5.5 Adapter 职责（白名单，仅此五项）

1. `line_ref` 展开 → line_refs 元组
2. `text_hash` 计算（与 Resolver 同一算法）
3. 范围校验（line bounds / offset 合法性）
4. `ResolvedSpan` 构造（span_id 遵循 `sp-{unit_id}.{role}[.{label}]` 约定）
5. 结构一致性检查（空 stem / 缺 answer / span 重叠 → fail-closed）

### 5.6 Adapter 禁令（黑名单，69 号五条 + 66 §7 具体化）

**核心不变量（Gate D 最高优先级，高于下方任一单项）**：

> **Adapter 只允许机械投影，不允许提高信息量。**

即：输出的信息量 ≤ 输入（manifest 字段 ∪ SealedSource 确定切片）之和。
Adapter 是最容易发生「为了让测试通过而偷偷加一点智能」的组件——一旦出现
`if not found: fuzzy_match(...)` / `if answer_lines_missing: parse_text(...)` /
`if options_not_split: regex_split(...)` 这类代码，Adapter 就不再是 Translator。
下方六条禁令都是这条不变量的具体化。

| 禁令 | 具体化 |
|---|---|
| 第二事实来源 | Adapter 不得引入 SealedSource 之外的任何文本源 |
| 第二 Resolver | 不得搜索 Source；只验证 manifest 给出的 line_ref |
| 隐式 fuzzy matching | 不得做任何近似匹配；line_ref 精确不存在 → fail-closed |
| 自主 Source 内容生成 | 不得生成、补全、改写任何正文 |
| 独立 semantic decision | 不得判定题型 / 切分选项 / 抽取答案 / 推导子题 |
| 内容解析 / 结构推断 | 不得用正则解释文本（66 §7 明令，含 option 切分） |

**判定原则**：Adapter 的每一个输出字段，都必须能指出它来自 manifest 的哪个
字段或 SealedSource 的哪个确定切片。**指不出来源的输出 = 违规。**

---

## 6. ResolvedSpan 生产者不变量（修正 Grammar 输入契约）

### 6.1 为什么需要

§3 发现 2：早前措辞「必须 Resolver 产出」既不可验证，又与 Adapter 路径冲突。

### 6.2 冻结不变量

> `Grammar.verify()` 的 `answer_text` **必须**是某个 `ResolvedRun` 中
> `role=answer` 的 `ResolvedSpan` 所承载的文本切片，且该 span 满足：
>
> 1. `granularity` 为字符切片；
> 2. `resolution_status ∈ {exact, normalized}`；
> 3. `text_hash` 与 SealedSource 原文一致（20 §8.1 Provenance 层已校验）。
>
> **生产者可以是 Resolver（Native Path）或 Adapter（Manifest Path）。
> 二者产出的 `ResolvedSpan` 在 20 §5.5 下同构，Grammar 不区分、也不需要区分。**

**禁止**传入裸 source / OCR 文本。题号前缀属上游边界产物（Resolver 的
`_answer_span` 切片规则或 Adapter 的等价切片），由 `_clean_answer()` 剥除，
不参与答案 token 合法性判断。

### 6.3 明确决定不做的事

**不给 `ResolvedSpan` 加生产者字段。** 不变量 §6.2 不需要它即可验证；加字段
会扩大 20 §5.5 的公开面，违反 YAGNI。若日后 Replay 需要区分路径来源，
届时再走 Errata——已挂入 §8 延期项。

### 6.4 分层职责（不变）

| 层 | 能保证 |
|---|---|
| Resolver / Adapter | 找到哪里（产出 ResolvedSpan） |
| Evidence Authority | 证明来源（text_hash / line_refs） |
| Grammar | **表示形式合法** |
| Gate | 结构规则 |
| Semantic Model | 内容正确 |

grammar 保证 representation validity，**不保证** semantic correctness。

---

## 7. Gate D 显式不主张

1. **不主张 Adapter 已实现**——本轮只冻结契约，`backend/app` 中无 Adapter 代码。
2. **不主张 I-5-1 的 14 项实验结论成立**——证据不可复现（§3 发现 3），降级为
   方向性参考。
3. **不主张 manifest schema 已冻结**——它属外部 preprocessing 项目，V3 侧只冻结
   「manifest 必须提供哪些字段」（§5.4），不冻结其内部形态。
4. **不主张 Adapter 路径能覆盖真实语料**——66 §10 已判定当前 manifest 表达力不足，
   在 §5.4 三项前置满足之前覆盖率接近零。
5. **不主张 preprocessing 可以强制启用**——它是可选上游，缺席时 Native Path 照常。

---

## 8. 延期项（不视为失败，不视为已完成）

| 项 | 阻塞 |
|---|---|
| 复现 I-5-1 的 14 项实验为可提交脚本 | 真实 manifest 数据 + preprocessing 配合 |
| V3 annotation schema 冻结并对外发布 | 需独立裁决（preprocessing 的前置） |
| manifest schema 冻结 | 属 preprocessing 项目 |
| 最小 Mechanical Adapter 实现 + 测试 | §5.4 三项前置全部满足 |
| `ResolvedSpan` 生产者字段（若 Replay 需要） | 正式 Errata |
| Grammar 输入来源契约写入 20 §8.4 正文 | 正式 Errata（80 §4 已挂） |

---

## 9. Gate D 最终状态

```text
Gate A            : PASS / TEST-EVIDENCED
Gate B1           : CONDITIONAL PASS
Gate B2-A         : CLOSED — PASS / TEST-EVIDENCED
Gate B2-B1~B2-B5  : CLOSED（B2-B3-C / B2-B4-C DEFERRED）
Gate C            : CLOSED (Phase 1)
BUG-V3-044        : CLOSED（含对抗性审查）
Gate D            : **CONTRACT CLOSED / IMPLEMENTATION NOT STARTED**（本文档）
Errata            : UNBLOCKED（Gate D 已过；Decision 项见 §9.1）
Adapter 实现       : NOT STARTED（阻塞于 §5.4 三项前置）
```

### 9.1 下一步（已被 82 号 supersede，2026-09-13）

> ⚠️ 本节原写「Gate D 后先进入 Errata Decision」。**该顺序已作废**——外部对抗性
> 审查发现文档权威层级漂移（P0），已建 `82 号` Contract Authority Reconciliation。
> **Errata Decision 暂缓**；`20` 不改；manifest-only 不冻结。权威顺序见 **82 §8**。

```text
Contract Authority Reconciliation（82 号）  ← 已建，ACTIVE
      ↓
Binding Authority Decision（BIND-1 优先；82 §5）
      ↓
V3 Annotation Contract 冻结（V3 拥有，preprocessing 实现）
      ↓
Manifest Contract 冻结
      ↓
Change Records（E1 = CHANGE-2；67 = CHANGE-4/5 → REJECT，Gate B NOT CLOSED）
      ↓
Errata Decision
      ↓
Adapter → ResolvedRun 机械映射定义
      ↓
最小 Adapter 实现 → 对抗性测试 → 真实 preprocessing corpus E2E
      ↓
Path B Full Closure
```

**不得倒序**：Authority 层与 Binding Carrier 未定前改 20 或写 Adapter，会让实现
反过来定义契约，重新制造 V2 式「代码先行、契约后补」。

### 已证明

1. 69 号五条禁令全部维持，未放宽任何一条。
2. `Bypasses: Annotation` 与 `IRBuilder.build` 的冲突已定位并修正为
   `Bypasses: Resolver only`。
3. Grammar 输入契约已由「机制」改写为「不变量」，与 Adapter 路径兼容。
4. Adapter 职责/禁令/前置条件已冻结为可执行的白名单与黑名单。

### 未证明

见 §7。另见 82 §5：**BIND-1/2/3 未裁决**，Binding Carrier = PENDING。

---

**下一步**（权威顺序见 **82 §8**）: Binding Authority Decision（BIND-1 优先）→
V3 Annotation Contract 冻结 → Manifest Contract 冻结 → Change Records →
Errata Decision → 最小 Adapter + 对抗性测试 → 真实 corpus E2E → Path B Full Closure。
非 Path B 侧：OQ-3 → OQ-2 → B2-B2 Unknown 125 triage → Phase 2 Evidence Ledger。

**Gate 状态权威 = 82 §3。** 本文件 §9 状态块为回声。
