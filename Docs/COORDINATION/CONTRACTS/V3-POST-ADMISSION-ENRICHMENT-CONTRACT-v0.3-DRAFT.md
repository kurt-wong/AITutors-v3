# AITutors-v3 Post-Admission Semantic Enrichment Contract v0.3

> **状态**：`CONTRACT FREEZE CANDIDATE` 配套 / **已同步 Owner Decisions P15–P19** / **NOT IMPLEMENTED** / **NOT AN IMPLEMENTATION AUTHORIZATION**
> **配套**：`PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` §8 / **§1b P15–P19**；`PREPROCESSING-V3-SEMANTIC-AUTHORITY-MATRIX-v0.3-DRAFT.md` §4
> **术语**：`Preprocessing` = `kurt-wong/Aitutors-preprocessing`；`AITutors-v3` = 当前 V3 系统；`Producer` **仅**作抽象架构角色（Contract §0）
> **证据标签**：`DECISION`（P15–P19 落版）/ `OBSERVED`（对照现状）/ `OPEN`
>
> **本轮同步（`DECISION`）**：**P15** 只允许生成缺失 detailed explanation · **P16** Generated explanation = AITutors-v3 Derived Enrichment · **P17** MIMO generate → DeepSeek validate · **P18** Enrichment failure 不回滚 Admission · **P19** 最多一次 retry，第二次 validation failure → `suspended`。
> **范围收窄**：P15 **排除**了原 §2 表中 `difficulty` / `knowledge_nodes` / `skills` 的 Post-Admission 补全——该三项属 **V3 Semantic Enrichment（Admission 前）**，见 Contract §6.1。

**Security（逐字）**：Never hardcode API Keys/Passwords/Tokens/Secrets; Always use .env for configuration.

---

## 1. 目标与边界

### 1.1 目标（`DECISION` **P15**）

在 Question **完成 Admission 并持久化之后**，对 **Gate/Admission 允许缺失** 的语义内容进行异步补全。

**`DECISION` P15 明确限定（binding）**：

> **只允许生成 Original Question 中缺失的 detailed explanation。**
> 已有 explanation：**不生成、不覆盖**。缺失 explanation：**允许异步生成**。

首要且**唯一**用例：**缺失 explanation 的题目**（含选择题详解）。

> **范围收窄说明**：P15 **不包含** `difficulty` / `knowledge_nodes` / `skills` 的 Post-Admission 补全。该三项属 **V3 Semantic Enrichment（Admission 前，Contract §6.1）**，不在本契约的 Post-Admission 范围内。

### 1.2 非目标

- 不替代 Preprocessing 原始 explanation（`explanation_preprocessing`）
- 不回滚/删除已 Admission 的 Question（**P18**）
- 不在本 Contract 内实现复杂 worker / 队列产品化
- 不修改 Frozen Spec / DB schema（schema 变更 = `OPEN` / implementation question，非本任务授权）

---

## 2. 允许缺失的字段（Allowed Missing）

| 字段 | Admission 时可缺？ | **Post-Admission** Enrichment 可补？ | 说明 |
|---|---|---|---|
| `explanation` | **是**（`DECISION` P15） | **是** | **P15 唯一允许项**；已有则不生成不覆盖 |
| `difficulty` | 是 | **否**（P15 排除） | 属 **V3 Semantic Enrichment**（Admission 前，Contract §6.1） |
| `knowledge_nodes` | 是 | **否**（P15 排除） | 同上 |
| `skills` | 是 | **否**（P15 排除） | 同上 |
| stem / options / answer / question_type（核心） | **否**（核心完整性） | 不适用 | 缺则不应走“可缺字段 enrichment”路径 |
| identity / provenance | **否** | 不适用 | M1–M5 失败不得靠 enrichment 洗白 |

> 若未来 Frozen Contract 将 explanation 升为 hard requirement，本表作废并以 Frozen 为准（`OPEN`，对齐 OD-V3-21）。

---

## 3. 生命周期（`DECISION` **P17 + P18 + P19**）

```text
Core Question
    → Gate
    → Admission
    → Persistence                    # Question / Instance / Material
    → Post-Admission Enrichment Job  # async
         → MIMO generate             # P17
         → DeepSeek validate         # P17
         → Persist enrichment result
    → Validated Result
```

### 3.1 与 Admission 解耦（`DECISION` **P18**）

**禁止**（除非 Frozen 另有规定）：

```text
no explanation → Gate fail → Question cannot enter DB
```

**应允许**：

```text
Core Question → Admission → Persistence → Async enrichment
```

目的：**Question identity / core factual integrity** 与 **optional semantic enrichment** 解耦。

**`DECISION` P18（binding）**：

```text
Enrichment failure → 不 rollback AITutors-v3 Admission
```

### 3.2 状态机（含 **P19** `suspended`）

Enrichment item 状态（独立于 Question 有效性）：

```text
absent → queued → generated → validated → accepted
                ↘ failed
                ↘ rejected
                ↘ unavailable
                ↘ suspended          # P19：第二次 validation failure
```

Question 本身保持 `valid/persisted`，不因 enrichment 失败而变 invalid（**P18**）。

---

## 4. Generated Content Authority（`DECISION` **P16**）

| 项 | 规则 |
|---|---|
| `explanation_preprocessing`（Original Question 自带） | `authority = Preprocessing / Source`，保留 source provenance |
| `explanation_generated` | **`authority = AITutors-v3 Derived Enrichment`**（**P16**），`generation_method = LLM` |
| 覆盖 | **禁止**覆盖或伪装成 `explanation_preprocessing` |
| 并存 | 允许双槽；展示策略见 §8 `OPEN`（OD-V3-22） |

**`DECISION` P16（binding）**：Generated explanation 是 **AITutors-v3 Derived Enrichment**——**不是** Source Authority，**不是** Preprocessing Authority。

（字段名按 Contract §0 术语规范化：原 `explanation_producer` → `explanation_preprocessing`。）

必须可追踪：

```text
Question
  → generation job
  → generation model/config
  → generated content
  → validation
  → current state
```

---

## 5. Validation（生成物也必须验证；`DECISION` **P17**）

**`DECISION` P17（binding）** 生成/验证链：

```text
MIMO  ↓ generate  ↓  DeepSeek  ↓ validate
```

状态（不与 Question semantic_status 混用）：

```text
generated   # 已生成，未验证
validated   # 通过自动验证（DeepSeek，P17）
accepted    # 通过人工/策略接受
rejected    # 验证或审核拒绝
suspended   # P19：第二次 validation failure
```

规则：

1. 生成 ≠ 正确。
2. 优先复用既有 Evidence / ValidationEvent，**不得另造平行 authority**。
3. 自动验证最小集（实现可裁剪，规则清单 = `OPEN` / OD-V3-23）：非空、语言/长度策略、与 stem/options 无直接矛盾的启发式、禁止密钥/注入模式、可追溯 job id。
4. `accepted` 前不得对用户展示为“教材级详解”（展示策略 `OPEN` / OD-V3-22）。

---

## 6. 失败语义（`DECISION` **P18 + P19**）

若 LLM 生成失败：

```text
Question     = valid / persisted   # 不回滚、不删除（P18）
Explanation  = pending | failed | unavailable | suspended
```

**`DECISION` P18（binding）**：

```text
Enrichment failure → 不 rollback AITutors-v3 Admission
```

**`DECISION` P19（binding）**：

```text
最多一次 retry
第二次 validation failure → suspended
禁止无限 retry
```

允许后续：`regeneration` / `manual review`（`regeneration` 形态 = `OPEN` / OD-V3-24 残项）。

边界：

| 约束 | 值 | 依据 |
|---|---|---|
| 失败是否影响 Question 持久化 | **否** | **P18** |
| 失败是否自动删除生成半成品 | 禁止静默删除已审计记录；可标记 failed | **P24** |
| retry 次数上限 | **最多 1 次** | **P19** |
| 第二次 validation failure | **`suspended`**（终态，不再自动重试） | **P19** |
| 是否允许无限自动重试 | **禁止** | **P19** |
| budget / backoff 数值 | `OPEN`（需 budget / live_guard 约束；OD-V3-24 残项） | — |
| 人工介入 | 允许，走 review；`accepted` 需可审计 | — |

---

## 7. 与 Preprocessing / Gate / Resolver 的关系

| 组件 | 关系 |
|---|---|
| Preprocessing | 不负责 post-admission 生成；其 explanation 为 PRD |
| Consumer Boundary | 不负责生成；只保真 |
| Resolver | 不负责生成；preprocessed 路径可跳过搜索 |
| Gate | 只门禁 **admission 时已存在** 的核心完整性；**不**因 optional 缺失 fail（`PROPOSED`） |
| Admission | 只物化核心 Question；enrichment 挂后 |
| Enrichment | 只写派生槽 + validation 状态 |

---

## 8. Persistence Semantics（`DECISION` **P15 / P16**）

逻辑槽（**不指定物理 schema**；schema 变更 = `OPEN` / OD-V3-25，非本任务授权）：

```text
Question
  core: stem, options, answer, question_type, identity, provenance, ...
  slots:
    explanation_preprocessing  : optional, PRD/SRC   ← Original Question 自带
    explanation_generated      : optional, AITutors-v3 Derived Enrichment
                                 + generation provenance + validation_state + retry_count
  enrichment_jobs[]            : append-only 可审计
```

**`DECISION` P15 范围收窄**：Post-Admission **仅** `explanation_*` 双槽。
~~`difficulty_generated` / `knowledge_generated` / `skills_generated`~~ **不在 Post-Admission 范围**——该三项属 V3 Semantic Enrichment（Admission 前，Contract §6.1）。

原则：

1. 不覆盖 PRD 槽（**P15**：已有 explanation 不生成不覆盖）。
2. jobs 可追溯（**P17**：MIMO generate → DeepSeek validate 链路可追踪）。
3. 当前展示哪一槽 = `OPEN`（OD-V3-22）。
4. 与 Question dedup / identity **正交**：enrichment 不得改变 question identity hash 的语义成分（若 identity hash 排除 generated 字段，须显式记录——`OPEN` / OD-V3-26）。

---

## 9. Retry / Regeneration 边界（`DECISION` **P19**）

| 项 | Contract 边界 | 依据 / 实现 |
|---|---|---|
| retry | **最多 1 次** | **P19** |
| 第二次 validation failure | **`suspended`**（终态） | **P19** |
| 无限自动重试 | **禁止** | **P19** |
| regeneration | 允许（新 job，不覆盖旧 accepted，除非显式 supersede 策略） | `OPEN`（OD-V3-24 残项） |
| supersede | 须 append 新版本 + 标记 | `OPEN` |
| budget / backoff / rate limit | 必须受 AITutors-v3 live_guard / budget 约束 | `OBSERVED` 已有模块，接线 `OPEN`（OD-V3-24 残项） |

---

## 10. 明确禁止

1. `no explanation → 拒绝入库`（在未 Frozen 为 hard requirement 前）
2. 生成物冒充 Preprocessing / Source（**P16**）
3. 生成失败导致回滚 Question（**P18**）
4. 无 validation 直接 accepted（**P17**）
5. 平行于 ValidationEvent 的第二套证据权威
6. 用 enrichment 洗白 identity/provenance 失败
7. **生成已有 explanation / 覆盖 `explanation_preprocessing`**（**P15**）
8. **超过 1 次 retry 或无限重试**（**P19**）
9. **Post-Admission 补 `difficulty` / `knowledge_nodes` / `skills`**（**P15** 范围外；属 Admission 前 V3 Semantic Enrichment）

---

## 11. Open（**实现问题**，非 Owner Decision 欠账）

> **Owner Decisions P15–P19: COMPLETE**（已落版于 Contract §1b 与本文件）。下表**均为 implementation / 依赖未来 Frozen 项**，**未**伪装成 Owner Decision。

| 项 | 状态 | 对齐 |
|---|---|---|
| explanation 是否永远 optional | `OPEN`（依赖未来 Frozen） | OD-V3-21 |
| 展示 Preprocessing vs generated 优先级 | `OPEN`（P16 已裁 authority 归属） | OD-V3-22 |
| validation 自动规则清单 | `OPEN`（P17 已裁 MIMO→DeepSeek 链） | OD-V3-23 |
| retry 的 budget / backoff 数值 | `OPEN`（**P19 已裁：最多 1 次、二次失败 `suspended`**） | OD-V3-24 |
| schema 扩展（jobs 表等） | `OPEN`（DB schema 明令本任务禁改） | OD-V3-25 |
| identity hash 是否排除 generated | `OPEN`（对齐现有 identity projection） | OD-V3-26 |

*End of AITutors-v3 Post-Admission Semantic Enrichment Contract v0.3 — CONTRACT FREEZE CANDIDATE 配套（Owner Decisions P15–P19 已同步）.*
