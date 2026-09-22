# Preprocessing → Canonical V3 Consumer Contract v0.3 — DRAFT

> **状态**：`DRAFT` / `NON-AUTHORITATIVE` / `NOT FROZEN` / `NOT A MIGRATION AUTHORIZATION` / `NOT AN X3 ENTRY DECISION`
>
> **定位**：Producer（AITutors-preprocessing）→ Canonical Consumer Boundary → Canonical V3 IR → V3 Semantic Enrichment → Gate → Admission → Persistence → Post-Admission Async Enrichment 的**架构合同草案**。
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

## 0. 工作基线（不得重推翻）

### 0.1 Preprocessing 职责（`OBSERVED` + `DERIVED`）

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

> **基线结论**：V3 **不应**对 Producer 已提供且具证据定位的结构事实做重复发现。

### 0.2 V3 职责（`OBSERVED` + `PROPOSED`）

1. Producer Artifact Consumer Boundary
2. Identity verification（M1–M5 + Interface Scope）
3. Evidence / Provenance preservation
4. Canonicalization
5. Canonical V3 IR
6. V3 semantic enrichment（difficulty / knowledge / skills 等）
7. Gate
8. Admission
9. Question / QuestionInstance / Material 持久化
10. **Post-Admission asynchronous semantic enrichment**（本版新增，`PROPOSED`）

### 0.3 目标生命周期（`PROPOSED`）

```text
ORIGINAL DOCUMENT
       │
       ▼
┌──────────────────────┐
│    PREPROCESSING     │  Fact Discovery / Structural Parsing
│                      │  Evidence / Provenance / Identity / QC / Flags
└──────────┬───────────┘
           │ Producer Artifact
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

## 1. 核心原则（P1–P5）

### P1 — No Silent Information Loss（`PROPOSED`）

Consumer Boundary 不得静默丢失 Producer Artifact 中具有业务意义的信息。

允许：canonicalization / normalization / representation change / evidence·provenance re-encoding。

必须能回答：**Producer 每一个有业务意义的信息进入 V3 后去了哪里？**

每个 Producer field 最终归类之一：

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

不得擅自改变 Producer 已声明事实的语义。

反例（禁止）：

```text
Producer unit_type = andalone_question
        ≠ 可静默变为 standalone_unit
        → 必须 UNKNOWN_UNIT_TYPE / fail closed（与 OD-1 / F-M3-04 一致）

Producer answer = UNKNOWN
        ≠ 可被“看起来合理”的猜测覆盖
```

若 V3 自行推导，必须标识：

```text
Producer fact
vs
V3-derived fact
```

二者不得混为同一 authority。

### P3 — Evidence Preservation（`PROPOSED`）

Producer 提供的 `source line` / `source SHA` / `basis` / `basis_evidence` / `printed_provenance` / `provenance` / `flags` / `material references` / `answer evidence` **不得因 Canonicalization 消失**。

V3 IR 允许换表示，但必须保留可建立下链的能力：

```text
V3 fact
  → canonicalization
  → producer fact
  → evidence
  → source
```

### P4 — Fail Closed（`PROPOSED`，继承 v0.2 / M1–M5）

无法安全 canonicalize、无法验证 identity、无法解释 provenance、或存在明确 ambiguity 时：

> **不得猜测。**

应进入：`UNKNOWN` / `INCOMPLETE` / `FLAGGED` / `pending_review` / `reject|block`。

禁止用默认值把未知变成确定。

### P5 — Producer Admission ≠ V3 Admission（`PROPOSED` 为正式 Contract 原则）

| 概念 | 含义 | 当前实例（`OBSERVED`） |
|---|---|---|
| **Producer Admission** | Producer 对自己发现的事实完成 QC/disposition | `ADMITTED=71` / `QC_FAIL=16` / `REJECTED_V1=1` |
| **V3 Consumer Validation** | identity / provenance / canonicalization / evidence consistency / completeness / supported vocabulary / structural safety | M1–M5 + Scope + adapters |
| **V3 Gate / Admission** | 是否允许 canonical Question 进入 V3 canonical persistence | `AdmissionCandidate` → `approve/reject` |

> **`Producer ADMITTED` ≠ `V3 APPROVED`。**  
> 禁止将 71 ADMITTED 表述为 71 questions 已获 V3 Admission。

---

## 2. Consumer Boundary 职责

### 2.1 范围（`PROPOSED`）

```text
Producer Artifact
  → Identity / Interface Scope 验证（M1–M5 AND Scope）
  → Deterministic canonicalization（仅已授权映射）
  → Evidence / Provenance 保真重编码
  → Canonical V3 IR 装配输入
```

**不做**：重复 OCR、重复题目发现、语义再分类（除非 V3-derived 且新 authority）、静默修复。

### 2.2 正式入口统一（`PROPOSED` + `OBSERVED` 缺口）

所有正式 Producer→V3 entrypoint **必须** 经过：

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

| Producer legacy | Canonical | Event | 状态 |
|---|---|---|---|
| `standalone_question` | `standalone_unit` | `X2.6-OD-2-MAP-STANDALONE-01` | AUTHORIZED |
| `composite_question` | `composite_unit` | `X2.6-OD-2-MAP-COMPOSITE-01` | AUTHORIZED |
| `andalone_question` | *(无)* | OD-1 | **PROHIBITED** → `UNKNOWN_UNIT_TYPE` fail closed |
| `standalone_unit` / `composite_unit` | 自身 | — | 幂等直通 |
| 其它任意值 | *(无)* | — | fail closed，禁止 fallback |

必须同时保留：`producer_unit_type`（legacy evidence）+ `canonical_unit_type`（runtime 唯一）。

**禁止**：把 Question Type 推导为 Unit Type（QT ⊥ UT，Owner D1）。

---

## 3. Information Preservation（总则）

完整 12 问矩阵见配套文件。此处固化总则：

1. 每个 Producer field 必须有 P1 归类。
2. 任何 `explicitly_unsupported` / `rejected` / `discard` 必须写明理由与回源路径。
3. representation change（如 line range → ResolvedSpan）**允许**，条件是 §P3 证据链可重建。
4. canonicalization **允许**，条件是 deterministic + 可追溯 original value。
5. information loss = 业务信息从 V3 representation **完全消失**。
6. semantic mutation = 把 UNKNOWN/不确定改成确定，或改写 Producer 语义。**禁止。**

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

### 5.2 Producer `original_question_type` 处理（`PROPOSED`）

| 项 | 规则 |
|---|---|
| Producer value | Source Authority 的分类**主张**（非 Source 字节事实） |
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
Producer:
  original_question_type = single_choice     → Producer Authority（可 canonicalize）

V3:
  question_type = single_choice              → Canonical V3 Authority（canonicalized Producer fact）
  difficulty = medium                        → V3 Derived Authority
  knowledge_nodes = [...]                    → V3 Derived Authority
  skills = [...]                             → V3 Derived Authority
```

**禁止**：把 V3-derived 反写成 Producer authority。  
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

## 8. Post-Admission Semantic Enrichment（本版新增）

### 8.1 目标（`PROPOSED`）

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

### 8.2 生命周期（`PROPOSED`）

```text
Core Question → Admission → Persistence
        → Post-Admission Enrichment Job
        → LLM Generation
        → Validation
        → Persist enrichment result
```

### 8.3 与 Admission 解耦（`PROPOSED`）

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

Producer 已给精确 source line spans 时：

```text
Producer line anchors → Consumer Boundary → ResolvedSpan
```

**跳过**：source marker search / semantic rediscovery。

### 10.2 Raw V3 LLM Path（`OBSERVED` 生产链）

```text
Source → Annotation → Resolver → ResolvedSpan
```

**仍然需要。**

### 10.3 定位（`PROPOSED` 固化）

> Resolver 是 V3 对 **非-preprocessed source** 的安全解析组件，而不是 Producer facts 的重复发现器。  
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

> 所有正式 Producer→V3 entrypoint 必须统一经过 Identity / Interface Scope boundary。

---

## 12. 当前真实不完整性（不得写成完美）

`OBSERVED`（X2.7 + MIMO 本地验证，可复算）：

| 事实 | 值 | 表达要求 |
|---|---|---|
| Interface Scope | 87（v2：`identity_version==2` + `source_content_sha256`） | ≠ 166 全量 |
| Producer ADMITTED | 71 | ≠ V3 APPROVED |
| QC_FAIL / Semantic Pending | 16 | 可恢复条件见 v0.2 ⑤ |
| REJECTED_V1 | 1 | 历史 V1 |
| v1 manifests 缺 identity | 79 | PRODUCER identity GAP |
| `andalone_question` | 1 unit / 1 doc | fail closed |
| multi-q 子题分解 | 不完整 | PRODUCER GAP |
| option label spans | 仅整块 `options_lines` | PRODUCER granularity GAP |
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
- producer version
- schema/contract version
- QC / disposition
- provenance
- checksum

**本任务不实现** distribution system。开放项见 Open Decisions。

---

## 14. 与 v0.2 的关系

| v0.2 冻结候选项 | v0.3 |
|---|---|
| ① Identity = `source_content_sha256` | **继承，不改写** |
| ② Scope = 87 / IR 71 / 16 pending | **继承** |
| ③ Unknown ≠ Ready；禁 silent skip/convert/fallback | **继承并写入 P4** |
| ④ Path = locator 非 identity | **继承** |
| ⑤ 16 件 Identity-only recovery | **继承** |
| ⑥ Source bytes capability | **继承** |

v0.3 **新增**：P1–P5、Information Preservation、Semantic Authority、Post-Admission Enrichment、QT contract、mapping 双权威、Runner 对齐缺口、真实不完整性披露、Artifact package 草案。

v0.3 **不**扩大 v0.2 冻结范围，**不**宣布冻结。

---

## 15. 配套交付物

| 交付物 | 文件 | 状态 |
|---|---|---|
| A. Consumer Contract Draft | 本文件 `PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` | `DRAFT` |
| B. Information Preservation Matrix | `PREPROCESSING-V3-INFORMATION-PRESERVATION-MATRIX-v0.3-DRAFT.md` | `DRAFT` |
| C. Semantic Authority Matrix | `PREPROCESSING-V3-SEMANTIC-AUTHORITY-MATRIX-v0.3-DRAFT.md` | `DRAFT` |
| D. Post-Admission Enrichment Contract | `V3-POST-ADMISSION-ENRICHMENT-CONTRACT-v0.3-DRAFT.md` | `DRAFT` |
| E. Open Decisions / Gaps | `PREPROCESSING-V3-OPEN-DECISIONS-v0.3-DRAFT.md` | `DRAFT` |

---

## 16. 执行确认（本任务）

- production code = **unchanged**
- Frozen Spec / Frozen Contract = **unchanged**
- Canonical Ontology / QT set / UT set = **unchanged**
- DB schema / migration / X3 = **unchanged**
- preprocessing corpus / artifacts = **unchanged**

*End of Consumer Contract v0.3 DRAFT.*
