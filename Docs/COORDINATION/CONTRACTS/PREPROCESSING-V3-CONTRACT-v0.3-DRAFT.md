# Preprocessing → Canonical V3 Consumer Contract v0.3

> **状态**：`CONTRACT FREEZE CANDIDATE` / **NOT FROZEN** / `AWAITING OWNER FREEZE ORDER`
> **NOT A MIGRATION AUTHORIZATION** / **NOT AN X3 ENTRY DECISION** / **NOT AN IMPLEMENTATION AUTHORIZATION**
>
> **本轮状态变更**：Owner Decisions **P01–P25 全部完成并已落版**（§1b）。其中 **P04 / P07 / P08 = CLOSED**。本文件由 `DRAFT` 升为 **CONTRACT FREEZE CANDIDATE**，供后续一致性检查与 Owner 冻结令使用。
>
> **权威顺序（binding）**：`Frozen Spec` > `Frozen Contract` > `Owner Decisions` > `v0.3 Contract` > `Implementation`。本文件**不得**覆盖 Frozen Spec / Frozen Contract（**P25**）。
>
> **定位**：AITutors-preprocessing → AITutors-v3 Consumer Boundary → Canonical V3 IR → V3 Semantic Enrichment → Gate → Admission → Persistence → Post-Admission Async Enrichment 的**架构合同**。
>
> **上游**：
> - `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`（Identity/Scope 冻结候选；**本文件不改写其冻结项**）
> - OD-2 Owner Closure（legacy vocabulary **boundary normalization**，非 QT→UT ontology mapping）
> - OD-1（`andonline/andalone_question` → migrate-as-UNKNOWN）
> - M1–M5 Consumer Identity Verification Design v1.1
> - Canonical Unit Type = `{standalone_unit, composite_unit}`
> - Canonical Question Type 闭集（见 §5，**不擅自增补**）
> - X2.7-INT-FULL-01 全量运行 + DSH 独立审查 + MIMO 本地独立验证
>
> **证据标签**：`OBSERVED` / `DERIVED` / `PROPOSED` / `OPEN` / `OWNER DECISION REQUIRED`
> **纪律**：`PROPOSED` ≠ 已实现；`DECISION` 在本文件中仅当引用上游已裁定项时使用。新设计一律标 `PROPOSED`。
>
> **本文件不做**：不修改 Frozen Spec / Frozen Contract / Canonical Ontology / DB schema / production code / corpus / migration / X3 状态。

**Security（逐字）**：Never hardcode API Keys/Passwords/Tokens/Secrets; Always use .env for configuration.

---

## 0. 术语规范与编号消歧（binding）

### 0.0.1 正式称谓

| 正式称谓 | 定义 | 禁止写法 |
|---|---|---|
| **Preprocessing** | = `kurt-wong/Aitutors-preprocessing`。负责 OCR / Markdown source preparation、document reslicing、question/unit boundary discovery、stem/options/answer/explanation region identification、material / sub-question structural recognition、printed number、question type discovery、unit type discovery、source line anchors、evidence / basis、provenance、source identity / SHA256、QC / disposition、flags / uncertainty，并生成供 AITutors-v3 消费的 Preprocessing Artifact | **禁止**把 Preprocessing 简写成 Producer |
| **Preprocessing Artifact** | AITutors-preprocessing 生成、供 AITutors-v3 Consumer Boundary 消费的数据产物 | 禁止写 Producer Artifact |
| **Current Preprocessing Artifact** | 当前版本 preprocessing 生成的产物 | — |
| **Legacy Preprocessing Artifact (V1 format)** | 旧版 Preprocessing Artifact 的**格式 / pipeline generation**；**V1 不是项目名** | **禁止**单独写 `V1 Artifact` |
| **AITutors-v3** | 当前 V3 系统 = Canonical V3 Consumer + Canonical V3 IR + V3 Semantic Enrichment + Gate + Admission + Persistence + Post-Admission Async Enrichment | 表格列名或已明确上下文方可缩写 `V3` |
| **AITutors-v3 Consumer Boundary** | `Preprocessing Artifact → Identity Verification → Interface Scope Verification → Deterministic Canonicalization → Evidence / Provenance Preservation → Canonical V3 IR` | 禁止写 "Producer Consumer" |
| **Canonical V3 IR** | AITutors-v3 消费并 canonicalize 后形成的规范 IR | — |
| **Producer** | **仅**作抽象架构角色（如 `Producer → Consumer`） | 实际项目描述必须写 `AITutors-preprocessing ↓ AITutors-v3 Consumer Boundary` |

### 0.0.2 编号消歧（三套编号，**不得混用**）

| 编号系 | 含义 | 位置 |
|---|---|---|
| **P1–P5** | 本文件 §1 **核心原则**编号 | §1 |
| **P01–P25** | **Owner Decisions** 编号（本文件 §1b 正式落版；源 = Owner Decision Package `OD-P01`–`OD-P25`） | §1b |
| **OD-V3-##** | Open Decisions / Gaps 登记号 | `PREPROCESSING-V3-OPEN-DECISIONS-v0.3-DRAFT.md` |

---

## 0.1 工作基线（不得重推翻）

### 0.1.1 Preprocessing 职责（`OBSERVED` + `DERIVED`）

Preprocessing 已承担主要 **Document Fact Discovery / Structural Recognition**：

- OCR / Markdown source
- document reslicing
- question / unit boundary discovery
- stem / options / answer / explanation region identification
- material / sub-question structural regions
- printed number
- rough question type
- unit type
- source line anchors
- evidence / basis
- provenance
- source identity / SHA256
- QC disposition
- flags / known uncertainty

> **基线结论**：V3 **不应**对 Preprocessing 已提供且具证据定位的结构事实做重复发现。

### 0.1.2 AITutors-v3 职责（`OBSERVED` + `DECISION`）

1. Preprocessing Artifact Consumer Boundary
2. Identity verification（M1–M5 + Interface Scope）
3. Evidence / Provenance preservation
4. Canonicalization
5. Canonical V3 IR
6. V3 semantic enrichment（difficulty / knowledge / skills 等）
7. Gate
8. Admission
9. Question / QuestionInstance / Material 持久化
10. **Post-Admission asynchronous semantic enrichment**（本版新增，`PROPOSED`）

### 0.1.3 目标生命周期（binding）

```text
ORIGINAL DOCUMENT
       │
       ▼
┌──────────────────────┐
│    PREPROCESSING     │  Fact Discovery / Structural Parsing
│                      │  Evidence / Provenance / Identity / QC / Flags
└──────────┬───────────┘
           │ Preprocessing Artifact
           ▼
┌──────────────────────┐
│  CONSUMER BOUNDARY   │  Identity Verify / Scope Verify
│                      │  Canonicalize / Preserve Evidence+Provenance
│                      │  Fail Closed
└──────────┬───────────┘
           ▼
     CANONICAL V3 IR
           │
           ▼
┌──────────────────────┐
│ V3 SEMANTIC WORK     │  Difficulty / Knowledge / Skills / ...
└──────────┬───────────┘
           ▼
         GATE
           ▼
       ADMISSION
           ▼
QUESTION / INSTANCE / MATERIAL PERSISTENCE
           │
           ▼
┌──────────────────────┐
│ POST-ADMISSION       │  Missing Explanation 等允许缺失语义
│ ASYNC ENRICHMENT     │  生成 → Validation → Persist
└──────────┬───────────┘
           ▼
    VALIDATED RESULT
```

一句话职责（`PROPOSED` 固化表述）：

> **Preprocessing discovers and evidences document facts; the Consumer Boundary preserves and canonicalizes those facts into V3's canonical IR without silent information loss or semantic mutation; V3 then performs its own semantic enrichment, Gate, Admission, persistence, and post-admission asynchronous enrichment.**

---

## 1. 核心原则（P1–P5）〔**原则编号** — 与 Owner Decisions **P01–P25** 是两套编号，**不得混用**，见 §0.0.2〕

### P1 — No Silent Information Loss（`PROPOSED`）

Consumer Boundary 不得静默丢失 Preprocessing Artifact 中具有业务意义的信息。

允许：canonicalization / normalization / representation change / evidence·provenance re-encoding。

必须能回答：**Preprocessing 每一个有业务意义的信息进入 V3 后去了哪里？**

每个 Preprocessing field 最终归类之一：

| 归类 | 含义 |
|---|---|
| `preserved` | 字段级原样保留 |
| `canonicalized` | 确定性映射到 canonical 值 |
| `converted_to_evidence` | 转为证据对象/串 |
| `converted_to_provenance` | 转为溯源对象 |
| `converted_to_v3_derived` | 作为 V3 派生语义的输入，产出新 authority |
| `retained_as_uncertainty` | 保留为 flag / UNKNOWN / INCOMPLETE |
| `explicitly_unsupported` | 显式登记为当前不支持 |
| `rejected` | fail-closed 拒绝该条目/字段 |

任何真正 `discard` 必须有明确理由；禁止 silent discard。  
逐字段矩阵见 `PREPROCESSING-V3-INFORMATION-PRESERVATION-MATRIX-v0.3-DRAFT.md`。

### P2 — No Silent Semantic Mutation（`PROPOSED`）

不得擅自改变 Preprocessing 已声明事实的语义。

反例（禁止）：

```text
Preprocessing unit_type = andalone_question
        ≠ 可静默变为 standalone_unit
        → 必须 UNKNOWN_UNIT_TYPE / fail closed（与 OD-1 / F-M3-04 一致）

Preprocessing answer = UNKNOWN
        ≠ 可被“看起来合理”的猜测覆盖
```

若 V3 自行推导，必须标识：

```text
Preprocessing fact
vs
V3-derived fact
```

二者不得混为同一 authority。

### P3 — Evidence Preservation（`PROPOSED`）

Preprocessing 提供的 `source line` / `source SHA` / `basis` / `basis_evidence` / `printed_provenance` / `provenance` / `flags` / `material references` / `answer evidence` **不得因 Canonicalization 消失**。

V3 IR 允许换表示，但必须保留可建立下链的能力：

```text
V3 fact
  → canonicalization
  → Preprocessing fact
  → evidence
  → source
```

### P4 — Fail Closed（`PROPOSED`，继承 v0.2 / M1–M5）

无法安全 canonicalize、无法验证 identity、无法解释 provenance、或存在明确 ambiguity 时：

> **不得猜测。**

应进入：`UNKNOWN` / `INCOMPLETE` / `FLAGGED` / `pending_review` / `reject|block`。

禁止用默认值把未知变成确定。

### P5 — Preprocessing Admission ≠ V3 Admission（`PROPOSED` 为正式 Contract 原则）

| 概念 | 含义 | 当前实例（`OBSERVED`） |
|---|---|---|
| **Preprocessing Admission** | Preprocessing 对自己发现的事实完成 QC/disposition | `ADMITTED=71` / `QC_FAIL=16` / `REJECTED_V1=1` |
| **V3 Consumer Validation** | identity / provenance / canonicalization / evidence consistency / completeness / supported vocabulary / structural safety | M1–M5 + Scope + adapters |
| **V3 Gate / Admission** | 是否允许 canonical Question 进入 V3 canonical persistence | `AdmissionCandidate` → `approve/reject` |

> **`Preprocessing ADMITTED` ≠ `V3 APPROVED`。**  
> 禁止将 71 ADMITTED 表述为 71 questions 已获 V3 Admission。

---

## 1b. Owner Decisions P01–P25（正式落版，`DECISION`）

> 本节是 `V3-CONTRACT-v0.3-OWNER-DECISION-PACKAGE.md` 中 `OD-P01`–`OD-P25` 的**正式裁决落版**。
> **Owner Decisions P01–P25: COMPLETE**。其中 **P04 = CLOSED**、**P07 = CLOSED**、**P08 = CLOSED**（不再把 P07 表述为 HOLD）。
> **落版 ≠ 实现授权**：本节只固化规则，**不授权** production code / schema / migration / corpus rerun / artifact rewrite。

### P01 — Legacy Preprocessing Artifact 不直接进入 AITutors-v3

> **Legacy Preprocessing Artifact (V1 format) 不迁移、不字段修补、不建立 AITutors-v3 compatibility path，不作为 AITutors-v3 的直接输入。**

对应 Original Source Document 必须保留。唯一进入路径：

```text
Original Source Document → Current AITutors-preprocessing
        → Current Preprocessing Artifact → AITutors-v3 Consumer Boundary
```

因此 `Legacy Preprocessing Artifact (V1 format)` ≠ `AITutors-v3 Input`。

### P02 — 所有历史非当前标准数据统一重新运行 AITutors-preprocessing

> **任何历史 Preprocessing Artifact，只要不符合当前 Preprocessing → AITutors-v3 Consumer Contract、Identity、QC 或其他当前准入要求，都不得通过字段修补、兼容转换、AITutors-v3 特判或人工 DB 修改进入 AITutors-v3。**

覆盖：Legacy Preprocessing Artifact (V1 format) · QC_FAIL artifact · REJECTED_V1 artifact · historical artifact · legacy artifact · pending_review 经人工处理后的 artifact。

```text
AITutors-v3 pending_review → Human Review → 重新运行 AITutors-preprocessing
        → AITutors-v3 Consumer Boundary → Gate → Admission
```

**禁止**直接人工修改 AITutors-v3 DB 后视为重新准入。

> **统一原则**：历史数据是否能够进入 AITutors-v3，**不取决于它过去由哪个 pipeline 生成**，而取决于它现在是否能够经过当前唯一标准的 Preprocessing → AITutors-v3 完整流程并通过准入。

### P03 — SHA256 是内容 Identity

```text
source_content_sha256 = Source Content Identity
```

**不是** stage identifier / pipeline identifier / migration identifier。AITutors-preprocessing **提供** Source Identity；AITutors-v3 **独立验证**。任何一方都不能通过修改 SHA256 改变 artifact 所处阶段。derived content 改变 → `new content → new SHA256 → provenance`，**不得**覆盖原始 Source Identity。

### P04 — Choice Question 必须具备 per-option structured evidence 〔CLOSED〕

**Owner Decision（binding）**：

> **如果 Canonical V3 IR 对 Choice Question 要求 per-option structure/evidence，则 AITutors-preprocessing 必须在当前 Preprocessing Contract 中正式产生 per-option structured information；AITutors-v3 不负责重新发现或猜测 option structure。**

**P04.1** 每个 option 至少必须能够表达：

```text
option
├── label
├── text
└── provenance
```

（如 `A` / `B` / `C` / `D` 及其对应文本和 Source provenance。）

**P04.2** Whole options region **仍然保留**：增加 `options[]`，**不得删除**已有 `options_lines`。两者并存：

```text
Whole Options Region  +  Per-Option Structured Evidence
```

**P04.3** provenance **不得硬编码成"一 option 一行"**。允许：

```text
line_range · char_span_in_line · table_cell · multiple source spans · other verifiable source provenance
```

核心要求：**每个 option 都必须能够可靠回溯到 Source，并且该 provenance 能被 AITutors-v3 验证。**

**P04.4** 无法可靠识别时**必须 fail closed**。不得猜测 option / label / text / provenance。必须显式表示 `unresolved` / `INCOMPLETE` / `QC_FAIL`（具体状态按最终 Contract 定义）。

**P04.5** 历史 Choice Artifact 的处理：当前历史 Preprocessing Artifact 中没有正式 per-option evidence 的数据——**不修补、不迁移、不由 AITutors-v3 Consumer 推导兼容**：

```text
Original Source Document → Current AITutors-preprocessing
        → Per-Option Structured Evidence → Current Preprocessing QC → AITutors-v3
```

**这不是一次性的 P04 workaround，而是 P01/P02 的统一历史数据原则。**

> **状态：CLOSED。** 本条**不授权实现 P04**（见 §20）。

### P05 — Composite Question 的整体性

> **Composite Question 是一个完整 Question/Unit；sub-question 是其内部结构。识别 sub-question 不意味着将其拆成独立 Question。**

AITutors-preprocessing 应负责识别：sub-question 数量 · 顺序 · source ranges · 可确定时的 answer / explanation / evidence correspondence。共享 material / context / premise dependency 必须保留。AITutors-v3 **不应**重新发现已由 AITutors-preprocessing 明确提供的结构事实。

### P06 — material 与 question range 可以重叠

```text
material_lines == questions_lines     本身不是错误
```

综合题可能存在 shared material / shared premise / shared context / embedded statement。如果 Question 本身完整清晰：

> **不得为了制造"不重叠区间"而强制重新切割。**

只有 overlap 导致 Question 不完整、material relation 错误、或 sub-question relation 丢失，才需要重新运行 AITutors-preprocessing。

### P07 — `answer_table_unresolved` 的最终处置 〔CLOSED〕

**定义（binding，禁止简化）**：

> **`answer_table_unresolved` = AITutors-preprocessing 无法可靠建立共享答案表中的 answer-table cell 与当前 Unit 的 question_numbers 之间的映射。**

**禁止**简化成"答案表错误"。

**Owner Decision（binding）**：这是 **AITutors-preprocessing 的解析/映射规则问题**。

> **历史 Preprocessing Artifact 中存在 `answer_table_unresolved` 的数据，不进行 artifact patch、不建立 AITutors-v3 compatibility workaround、不要求 AITutors-v3 猜测映射；修改 AITutors-preprocessing 当前规则后，从 Original Source Document 重新运行 preprocessing。**

```text
Original Source Document → Current AITutors-preprocessing → Answer-table mapping
        → Preprocessing QC → Current Preprocessing Artifact → AITutors-v3
```

**P07.3** 仍无法可靠映射时：`explicit unresolved` / `QC_FAIL`，**而不是** `guess`。**不得人为制造 Question → Answer 映射。**

**P07.4** Evidence Preservation：答案表原始信息仍应作为 evidence/provenance 保留。

```text
unresolved mapping ≠ delete answer-table information
                 = information retained + mapping unresolved explicitly
```

> **状态：CLOSED。** 本条**不授权实现 P07**（见 §20）。

### P08 — Evidence / Flags 保留 〔CLOSED〕

以下 Preprocessing information **不得静默丢失**：

```text
flags · basis · basis_evidence · answer_evidence
option structured evidence / option provenance
provenance · unresolved information
```

默认属于 **Preprocessing evidence / Preprocessing provenance / review signal**，**而不是**自动成为 AITutors-v3 Gate authority。

例如 `answer_table_unresolved` **不能**未经正式 Contract 规则授权而自动变成 `V3 Gate = reject`，**也不能**自动变成 `V3 Gate = pending_review`。

> **状态：CLOSED。** 与 P14 合并阅读。

### P09 — Legacy Unit Type 的唯一合法 canonicalization

Legacy Unit Type `standalone_question` / `composite_question`：**只有 Owner-authorized deterministic normalization 才能 canonicalize。** `andalone_question` **禁止**兼容映射，必须重新运行 AITutors-preprocessing。Canonical Unit Type 仍然只有 `standalone_unit` / `composite_unit`。

### P10 — Canonical Question Type 使用 Frozen 闭集

Canonical Question Type 使用现有 **Frozen canonical vocabulary**。Historical Preprocessing value 可作 provenance / history 保留，但**不能**作为 canonical runtime QT。**不得擅自扩展 canonical QT。**

### P11 — Question Type 与 Unit Type 是独立维度

```text
QT ⊥ UT
```

**不得**建立 global QT → UT mapping。

### P12 — 三层判定互不等同

```text
Preprocessing QC  ≠  AITutors-v3 Gate  ≠  AITutors-v3 Admission
```

### P13 — `pending_review` 后必须完整重跑

```text
AITutors-preprocessing → AITutors-v3 → Gate → Admission
```

### P14 — Preprocessing flags 不自动改变 AITutors-v3 Gate

Preprocessing flags **不自动**改变 AITutors-v3 Gate。必须存在明确的 Contract / Owner rule。

### P15 — Post-Admission Enrichment 只生成缺失的 detailed explanation

AITutors-v3 Admission 后：**只允许生成 Original Question 中缺失的 detailed explanation。** 已有 explanation **不生成、不覆盖**；缺失 explanation **允许异步生成**。

### P16 — Generated explanation 是 AITutors-v3 Derived Enrichment

```text
Generated explanation = AITutors-v3 Derived Enrichment
```

**不是** Source Authority，**不是** Preprocessing Authority。

### P17 — 生成/验证链

```text
MIMO  ↓ generate  ↓  DeepSeek  ↓ validate
```

### P18 — Enrichment failure 不回滚 Admission

```text
Enrichment failure → 不 rollback AITutors-v3 Admission
```

### P19 — 最多一次 retry

最多一次 retry。第二次 validation failure → `suspended`。**禁止无限 retry。**

### P20 — 正式 entrypoint 必经统一入口

所有正式 `AITutors-preprocessing ↓ AITutors-v3` entrypoint **必须**经过：

```text
AITutors-v3 Consumer Boundary  +  Interface Scope  +  M1–M5 Identity Verification
```

### P21 — Source Identity 的提供与独立验证

AITutors-preprocessing **提供** Source Identity；AITutors-v3 **独立验证**。

### P22 — AITutors-v3 独立计算/验证 Source SHA256

AITutors-v3 独立计算/验证 Source SHA256。Mismatch → **fail closed**。

### P23 — 两个 hash 保持独立

```text
source_content_sha256    与    derived_text_hash      保持独立
```

不得混用或合并。

### P24 — Preprocessing evidence/provenance 不得 silent discard

必须 `preserve` / `canonicalize` / `convert_to_evidence` / `convert_to_provenance` / `retained_as_uncertainty`，或显式记录 `unsupported` / `rejected`。

### P25 — v0.3 Contract 不得覆盖 Frozen Spec

发现 `v0.3 Contract ≠ Frozen Spec` 时：

```text
STOP → 记录 conflict → 等待 Owner authorization
```

**不得自行修改 Frozen Spec。**

---

## 1c. Historical Source Reprocessing Principle（binding，统一历史数据原则）

> **所有历史 Preprocessing Artifact 均不得被视为当前 AITutors-v3 的兼容输入标准。凡历史 Artifact 不满足当前 Preprocessing → AITutors-v3 Consumer Contract，必须保留 Original Source Document 及历史 provenance，并使用当前版本 AITutors-preprocessing 重新生成 Current Preprocessing Artifact。AITutors-v3 只消费满足当前 Contract、Identity、QC 与 Consumer Boundary 要求的当前产物。**

该原则**统一覆盖**：

```text
Legacy Preprocessing Artifact (V1 format)
QC_FAIL
REJECTED_V1
P04 historical choice artifacts（无正式 per-option evidence）
P07 answer_table_unresolved historical artifacts
pending_review after human review
other historical non-conforming artifacts
```

**禁止**的替代路径（全部）：

```text
artifact field patch
compatibility conversion
AITutors-v3 special-case / 特判
manual AITutors-v3 DB mutation 后视为重新准入
```

> 本原则是 **P01 / P02 / P04.5 / P07 / P13** 的统一上位表述，不新增独立义务，**也不授权任何历史重跑**（重跑执行须 Owner 另行下令）。

---

## 2. Consumer Boundary 职责

### 2.1 范围（`PROPOSED`）

```text
Preprocessing Artifact
  → Identity / Interface Scope 验证（M1–M5 AND Scope）
  → Deterministic canonicalization（仅已授权映射）
  → Evidence / Provenance 保真重编码
  → Canonical V3 IR 装配输入
```

**不做**：重复 OCR、重复题目发现、语义再分类（除非 V3-derived 且新 authority）、静默修复。

### 2.2 正式入口统一（`PROPOSED` + `OBSERVED` 缺口）

所有正式 Preprocessing→V3 entrypoint **必须** 经过：

```text
Interface Scope ∧ M1 → M2 → M3 → M4 → M5
```

任一拒绝 ⇒ 下游语义消费 **NOT REACHED**。

`OBSERVED` 缺口（X2.7 NEW-F1，记为 **historical/experimental runner alignment issue**）：

| 入口 | Scope | M1–M5 | 现状 |
|---|---|---|---|
| `scripts/preprocessing_consumer/runner.py` | 是 | **否** | 可进 production GateService → 不合规 |
| `scripts/preprocessing_consumer/runner_b2.py` | 是 | **是** | 合规 harness |

> 本 Contract **不**修改生产代码；对齐属后续 implementation authorization 范围。  
> `OWNER DECISION REQUIRED`：`runner.py` 删除 / 硬阻断 / 对齐 B2。

### 2.3 Canonicalization 只允许已授权映射（`DECISION` 上游 OD-2 + `PROPOSED` 本版固化）

| Preprocessing legacy | Canonical | Event | 状态 |
|---|---|---|---|
| `standalone_question` | `standalone_unit` | `X2.6-OD-2-MAP-STANDALONE-01` | AUTHORIZED |
| `composite_question` | `composite_unit` | `X2.6-OD-2-MAP-COMPOSITE-01` | AUTHORIZED |
| `andalone_question` | *(无)* | OD-1 | **PROHIBITED** → `UNKNOWN_UNIT_TYPE` fail closed |
| `standalone_unit` / `composite_unit` | 自身 | — | 幂等直通 |
| 其它任意值 | *(无)* | — | fail closed，禁止 fallback |

必须同时保留：`preprocessing_unit_type`（legacy evidence）+ `canonical_unit_type`（runtime 唯一）。

**禁止**：把 Question Type 推导为 Unit Type（QT ⊥ UT，Owner D1）。

---

## 3. Information Preservation（总则）

完整 12 问矩阵见配套文件。此处固化总则：

1. 每个 Preprocessing field 必须有 P1 归类。
2. 任何 `explicitly_unsupported` / `rejected` / `discard` 必须写明理由与回源路径。
3. representation change（如 line range → ResolvedSpan）**允许**，条件是 §P3 证据链可重建。
4. canonicalization **允许**，条件是 deterministic + 可追溯 original value。
5. information loss = 业务信息从 V3 representation **完全消失**。
6. semantic mutation = 把 UNKNOWN/不确定改成确定，或改写 Preprocessing 语义。**禁止。**

---

## 4. Unit Type Contract

### 4.1 Canonical 闭集（`DECISION` 上游，不扩）

```text
standalone_unit
composite_unit
```

### 4.2 归一化规则（`DECISION` OD-2 + `PROPOSED` 落点）

- 仅 §2.3 表中两条 legacy 翻译。
- 映射表 runtime authority **最终只能有一个**（见 §9 mapping_registry）。
- `andonline_question` 样本当前语料中写作 `andalone_question`（`OBSERVED` 1 条）：一律 `UNKNOWN_UNIT_TYPE`，整条 unit（乃至文档级 fail-loud，以实现为准）**不得** fallback。

### 4.3 与 F-M3-04

保持一致：`andalone_question` 类非法值 = fail closed + isolate，**不是** silent repair 目标。

---

## 5. Question Type Contract

### 5.1 Canonical Question Type 闭集（`DECISION` 上游；本文件**不新增**）

```text
single_choice
multiple_choice
true_false
fill_in
short_answer
essay
cloze
reading
grammar_fill
vocabulary_fill
seven_to_five
reading_expression
```

### 5.2 Preprocessing `original_question_type` 处理（`PROPOSED`）

| 项 | 规则 |
|---|---|
| Preprocessing value | Source Authority 的分类**主张**（非 Source 字节事实） |
| 进入 V3 | **verbatim 保留** + 可选 canonical 映射 |
| deterministic mapping | 仅当存在 Owner 授权 per-value rule |
| unsupported value | `explicitly_unsupported` / `rejected`（fail closed） |
| unknown / missing | `UNKNOWN`，禁止默认 `short_answer` 等 |
| validation state | `ready` / `incomplete` / `unknown`（语义层） |

### 5.3 当前缺口（`OBSERVED` + `OPEN`）

- runtime **尚无** QT closed-set enforcement（X2.7：verbatim 透传）。
- Gate `grammar None` → `auto_approve` 不可达（X2.7 NEW-F3）。
- 语料全量还出现过 `true_false` / `listening` 等；`listening` **不在** §5.1 闭集。

> 本文件 **不**通过猜测扩集或静默映射。缺口记入 Open Decisions。

---

## 6. V3 Semantic Enrichment 与 Authority 边界

### 6.1 划分（`PROPOSED`）

Preprocessing **不必**承担全部 Question Semantic Metadata；它提供 document facts / structural facts。V3 可在可靠事实之上派生：

- difficulty
- knowledge nodes
- skill / ability
- concept relationships
- 其他 V3-owned semantic metadata

### 6.2 示例（`PROPOSED`）

```text
Preprocessing:
  original_question_type = single_choice     → Preprocessing Authority（可 canonicalize）

V3:
  question_type = single_choice              → Canonical V3 Authority（canonicalized Preprocessing fact）
  difficulty = medium                        → V3 Derived Authority
  knowledge_nodes = [...]                    → V3 Derived Authority
  skills = [...]                             → V3 Derived Authority
```

**禁止**：把 V3-derived 反写成 Preprocessing authority。  
矩阵见 `PREPROCESSING-V3-SEMANTIC-AUTHORITY-MATRIX-v0.3-DRAFT.md`。

---

## 7. Information Fidelity and Loss Policy

### 7.1 允许的 representation change

例：`stem_lines=[120,122]` → `ResolvedSpan(line_refs=P1L120..P122, text_hash=…)`。  
条件：可回源、可验 hash、role 可识别。

### 7.2 canonicalization

例：`composite_question` → `composite_unit`。  
条件：deterministic、Owner-authorized、original 保留、禁止 QT→UT。

### 7.3 information loss（禁止 silent）

例：`answer_lines` / `basis_evidence` / `flags` / `provenance` 从 V3 representation **完全消失**。  
若发生，必须 `explicitly_unsupported` 或带理由的 `discard`（见 7.5）。

### 7.4 semantic mutation（禁止）

例：`UNKNOWN` → guessed value；`unverified` → `printed_as_is`；生成答案覆盖 source answer。

### 7.5 允许真正 discard 的条件（`PROPOSED`）

同时满足才可 `discard`：

1. 字段无业务意义（纯临时/缓存），**或** 已完整 `converted_to_evidence/provenance` 的冗余副本；
2. 写明理由与不可回源影响评估；
3. 不破坏 P3 证据链；
4. 在 Preservation Matrix 中将该字段标为 discard + reason。

**默认原则：No silent discard。**

---

## 8. Post-Admission Semantic Enrichment（`DECISION` **P15 / P16 / P17 / P18 / P19**）

> 本节四小节的规范内容已由 Owner Decisions **P15–P19** 正式裁决（§1b）。原文 `PROPOSED` 表述**升级为 `DECISION`**；实现状态仍为 **NOT AUTHORIZED**（§20）。

### 8.1 目标（`DECISION` **P15**）

Question **入库之后**，对**允许缺失**的语义内容进行异步后台补全。

当前明确用例：**缺失 explanation 的选择题**（及其它 Gate/Admission 允许缺失的字段）。

```text
Question
├── stem           present
├── options        present
├── answer         present
├── question_type  present
├── difficulty     present / optional
├── knowledge      present / optional
└── explanation    missing
```

不得仅因 explanation 缺失阻止核心 Question 入库——**前提是** Gate/Admission Contract 允许该字段缺失。

**`DECISION` P15 明确限定**：只允许生成 Original Question 中**缺失的 detailed explanation**。已有 explanation **不生成、不覆盖**。

### 8.2 生命周期（`DECISION` **P17 + P19**）

```text
Core Question → Admission → Persistence
        → Post-Admission Enrichment Job
        → MIMO generate → DeepSeek validate
        → Persist enrichment result
        （最多一次 retry；第二次 validation failure → suspended）
```

**`DECISION` P16**：Generated explanation = **AITutors-v3 Derived Enrichment**，**不是** Source Authority，**不是** Preprocessing Authority。

### 8.3 与 Admission 解耦（`DECISION` **P18**）

禁止设计成（除非未来 Frozen Contract 明确 explanation 为 hard requirement）：

```text
no explanation → Gate fail → Question cannot enter DB
```

应允许：

```text
Core Question → Admission → Persistence → Async enrichment
```

使 **Question identity / core factual integrity** 与 **optional semantic enrichment** 解耦。

细节见 `V3-POST-ADMISSION-ENRICHMENT-CONTRACT-v0.3-DRAFT.md`。

---

## 9. mapping_registry 双权威风险

`OBSERVED`：

| 位置 | 角色 | Production 接线 |
|---|---|---|
| `app/domains/compile/mapping_registry.py` | Governance scaffold + OD 事件表 | **NOT IMPLEMENTED**（自述 P1–P13 OPEN） |
| `scripts/preprocessing_consumer/boundary.normalize_unit_type` | Runtime 归一化（OD-2 两条） | harness 已用 |

`PROPOSED` 约束：

> Canonical mapping **必须最终只有一个 runtime authority。**

当前未决：

```text
OWNER DECISION REQUIRED
  - wire mapping_registry 为唯一 runtime authority
  - 或明确 boundary.normalize_unit_type 为 runtime authority，并将 mapping_registry 降级为纯治理登记
```

本文件**不**删除、不擅自接线任一实现。

---

## 10. Resolver 关系（不删除）

### 10.1 Preprocessing Consumer Path（`PROPOSED`）

Preprocessing 已给精确 source line spans 时：

```text
Preprocessing line anchors → Consumer Boundary → ResolvedSpan
```

**跳过**：source marker search / semantic rediscovery。

### 10.2 Raw V3 LLM Path（`OBSERVED` 生产链）

```text
Source → Annotation → Resolver → ResolvedSpan
```

**仍然需要。**

### 10.3 定位（`PROPOSED` 固化）

> Resolver 是 V3 对 **非-preprocessed source** 的安全解析组件，而不是 Preprocessing facts 的重复发现器。  
> 其 fail-closed / “可失败不可猜” 语义继续有效。

---

## 11. M1–M5 保留

`OBSERVED` 职责：

| ID | 职责 |
|---|---|
| M1 | Manifest identity 声明读取 |
| M2 | raw bytes 身份计算 |
| M3 | IR identity 提取 |
| M4 | 三方一致性 + 正交双轴（identity / semantic） |
| M5 | Identity Gate（VERIFIED+PENDING=BLOCK） |

**不是** preprocessing 与 V3 的重复语义工作；而是 identity / integrity / authority binding / fail-closed。

`PROPOSED`：

> 所有正式 Preprocessing→V3 entrypoint 必须统一经过 Identity / Interface Scope boundary。

---

## 12. 当前真实不完整性（不得写成完美）

`OBSERVED`（X2.7 + MIMO 本地验证，可复算）：

| 事实 | 值 | 表达要求 |
|---|---|---|
| Interface Scope | 87（v2：`identity_version==2` + `source_content_sha256`） | ≠ 166 全量 |
| Preprocessing ADMITTED | 71 | ≠ V3 APPROVED |
| QC_FAIL / Semantic Pending | 16 | 可恢复条件见 v0.2 ⑤ |
| REJECTED_V1 | 1 | 历史 V1 |
| v1 manifests 缺 identity | 79 | PREPROCESSING identity GAP |
| `andalone_question` | 1 unit / 1 doc | fail closed |
| multi-q 子题分解 | 不完整 | PREPROCESSING GAP |
| option label spans | 仅整块 `options_lines` | PREPROCESSING granularity GAP |
| answer table | 502 `answer_table_unresolved` | flags 保留 |
| printed provenance unknown | 596 units | `unverified` / `unknown` |
| material/questions 同区间 | 41 composites | 结构折叠 |
| 71 SHA / 行锚点 | 71/71 通过 | structural 可靠 |
| structural vs semantic | structural ≫ semantic completeness | **必须分述** |

必须分别表达：

```text
identity correctness
structural correctness
semantic completeness
evidence closure
```

**禁止**：“71 ADMITTED = 71 questions 全部语义正确”。

---

## 13. Batch Artifact Distribution（只定义，不实现）

`OBSERVED` 现状：manifest（live）+ `resolver_ref_r52/resolver_ir.json`（一次性实验快照）+ v1/v2 face 分裂。

`PROPOSED` 未来正式 package 至少含：

- source identity（`source_content_sha256` + raw bytes 可达性）
- manifest
- semantic artifact / IR（若走语义消费）
- artifact version
- preprocessing version
- schema/contract version
- QC / disposition
- provenance
- checksum

**本任务不实现** distribution system。开放项见 Open Decisions。

---

## 14. Historical Source Reprocessing Principle 与 v0.2 的关系

**统一历史数据原则**见 **§1c**（binding；`DECISION` P01 / P02 / P04.5 / P07 / P13 的统一上位表述）。

| v0.2 冻结候选项 | v0.3 |
|---|---|
| ① Identity = `source_content_sha256` | **继承，不改写**（并由 **P03** 固化"内容 Identity"语义） |
| ② Scope = 87 / IR 71 / 16 pending | **继承** |
| ③ Unknown ≠ Ready；禁 silent skip/convert/fallback | **继承并写入 P4** |
| ④ Path = locator 非 identity | **继承** |
| ⑤ 16 件 Identity-only recovery | **继承**；历史非标数据统一重跑见 **P02 / §1c** |
| ⑥ Source bytes capability | **继承**（并由 **P21 / P22** 固化提供与独立验证义务） |

v0.3 **新增**：术语规范（§0）、核心原则 P1–P5、**Owner Decisions P01–P25 落版（§1b）**、**Historical Source Reprocessing Principle（§1c）**、Information Preservation、Semantic Authority、Post-Admission Enrichment（P15–P19）、QT contract、mapping 双权威、Runner 对齐缺口、真实不完整性披露、Artifact package 草案。

v0.3 **不**扩大 v0.2 冻结范围，**不**宣布冻结（冻结令属 Owner）。

---

## 15. 配套交付物

| 交付物 | 文件 | 本轮状态 |
|---|---|---|
| A. Consumer Contract（本文件） | `PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` | **`CONTRACT FREEZE CANDIDATE`** |
| B. Information Preservation Matrix | `PREPROCESSING-V3-INFORMATION-PRESERVATION-MATRIX-v0.3-DRAFT.md` | **已同步 P04 / P07 / P08** |
| C. Semantic Authority Matrix | `PREPROCESSING-V3-SEMANTIC-AUTHORITY-MATRIX-v0.3-DRAFT.md` | **已同步 P16 / §17** |
| D. Post-Admission Enrichment Contract | `V3-POST-ADMISSION-ENRICHMENT-CONTRACT-v0.3-DRAFT.md` | **已同步 P15–P19** |
| E. Open Decisions / Gaps | `PREPROCESSING-V3-OPEN-DECISIONS-v0.3-DRAFT.md` | **`OWNER DECISION STATUS: COMPLETE`** |
| F. Owner Decision Package | `V3-CONTRACT-v0.3-OWNER-DECISION-PACKAGE.md` | **治理历史证据**；已加状态说明，**未删除历史记录** |

---

## 16. Information Preservation 同步点（binding，`DECISION` P04 / P07 / P08）

| 字段 | 归类 |
|---|---|
| `options_lines` | **`preserved`**（Whole Options Region 保留，**P04.2 不得删除**） |
| `options[]` | **Preprocessing structural fact**（**P04.1**） |
| `option.label` | **Preprocessing structural fact**（**P04.1**） |
| `option.text` | **Preprocessing structural fact**（**P04.1**） |
| `option.provenance` | **evidence / provenance**（**P04.3**；多态，禁止"一 option 一行"硬编码） |
| `answer_table_unresolved` | **`retained_as_uncertainty`**（**P07.4**） |
| `answer_number_mismatch` | **`retained_as_uncertainty`** |
| `flags` | **`preserved` / `retained_as_uncertainty`**（**P08**） |
| `basis` / `basis_evidence` | `preserved` / evidence（**P08**） |
| `answer_evidence` | evidence（**P08**） |

---

## 17. Semantic Authority 同步点（binding，`DECISION` P16）

以下属于 **Preprocessing-discovered structural / evidence facts**：

```text
option label
option text
option provenance
answer-table mapping
```

AITutors-v3 可以 canonicalize，但**不得凭空重新创造或覆盖与 Preprocessing fact 冲突的事实**。

Generated explanation 属于 **AITutors-v3 Derived Enrichment**，**不是** Source Authority，**不是** Preprocessing Authority（**P16**）。

---

## 18. 执行确认（本任务）

- AITutors-v3 production code = **unchanged**
- AITutors-preprocessing production code = **unchanged**
- Frozen Spec / Frozen Contract = **unchanged**
- Canonical Ontology / QT set / UT set = **unchanged**
- DB schema / migration / X3 = **unchanged**
- preprocessing corpus / artifacts = **unchanged**
- **P04 / P07 / Post-Admission Enrichment 实现 = NOT AUTHORIZED**
- **历史 corpus 重跑 = NOT AUTHORIZED**（P02 / P04 / P07 写入的是**规则**，不是执行令）

---

## 19. 一致性检查（Frozen Spec vs Frozen Contract vs Owner Decisions vs v0.3）

```text
发现 v0.3 Contract ≠ Frozen Spec
  → STOP
  → 记录 conflict
  → 等待 Owner authorization
  → 不得自行修改 Frozen Spec（P25）
```

本轮一致性检查执行结果（`OBSERVED`，2026-09-23）：

| 检查对 | 结果 |
|---|---|
| Frozen Spec（`Docs/V3_SPEC/**`）vs v0.3 Contract | **NO CONFLICT** — Frozen Spec 未被本任务改动（`git diff` 为空）；v0.3 未改写任何 Frozen 条款 |
| Frozen Contract（`PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` 冻结六项）vs v0.3 | **NO CONFLICT** — §15 逐项「继承，不改写」 |
| Owner Decisions P01–P25 vs v0.3 Contract | **ALIGNED** — §1b 25/25 落版；P04 / P07 / P08 = CLOSED |
| Owner Decisions P01–P25 vs Information Preservation Matrix | **ALIGNED** — §16 同步点已入表 |
| Owner Decisions P01–P25 vs Semantic Authority Matrix | **ALIGNED** — §17 同步点已入表 |
| Owner Decisions P15–P19 vs Post-Admission Enrichment Contract | **ALIGNED** — 已同步；并按 **P15 收窄**范围（排除 difficulty / knowledge_nodes / skills） |
| Owner Decisions vs Open Decisions 登记 | **ALIGNED** — `OWNER DECISION STATUS: COMPLETE`；17 项 `OPEN` 明确标为 implementation question |

**未触发 STOP**：本轮未发现 `v0.3 Contract ≠ Frozen Spec` 类冲突，因此无需 record conflict / 等待 Owner authorization。若后续发现此类冲突，严格执行 **P25**。

*End of Preprocessing → Canonical V3 Consumer Contract v0.3 — CONTRACT FREEZE CANDIDATE.*
