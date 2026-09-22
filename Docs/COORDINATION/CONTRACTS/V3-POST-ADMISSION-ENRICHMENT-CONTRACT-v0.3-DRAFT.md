# V3 Post-Admission Semantic Enrichment Contract v0.3 — DRAFT

> **状态**：`DRAFT` / `NON-AUTHORITATIVE` / `NOT FROZEN` / `NOT IMPLEMENTED`
> **配套**：`PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` §8；`PREPROCESSING-V3-SEMANTIC-AUTHORITY-MATRIX-v0.3-DRAFT.md` §4
> **证据标签**：`PROPOSED`（本文件主体）/ `OBSERVED`（对照现状）/ `OPEN` / `OWNER DECISION REQUIRED`

**Security（逐字）**：Never hardcode API Keys/Passwords/Tokens/Secrets; Always use .env for configuration.

---

## 1. 目标与边界

### 1.1 目标（`PROPOSED`）

在 Question **完成 Admission 并持久化之后**，对 **Gate/Admission 允许缺失** 的语义内容进行异步补全。

首要用例：**缺失 explanation 的题目**（含选择题详解）。

### 1.2 非目标

- 不替代 Producer 原始 explanation
- 不回滚/删除已 Admission 的 Question
- 不在本 Contract 内实现复杂 worker / 队列产品化
- 不修改 Frozen Spec / DB schema（若需 schema 扩展 → `OWNER DECISION REQUIRED`）

---

## 2. 允许缺失的字段（Allowed Missing）

| 字段 | Admission 时可缺？ | Enrichment 可补？ | 说明 |
|---|---|---|---|
| `explanation` | **是**（`PROPOSED`） | **是** | 首要用例 |
| `difficulty` | 是 | 是 | V3D |
| `knowledge_nodes` | 是 | 是 | V3D |
| `skills` | 是 | 是 | V3D |
| stem / options / answer / question_type（核心） | **否**（核心完整性） | 不适用 | 缺则不应走“可缺字段 enrichment”路径 |
| identity / provenance | **否** | 不适用 | M1–M5 失败不得靠 enrichment 洗白 |

> 若未来 Frozen Contract 将 explanation 升为 hard requirement，本表作废并以 Frozen 为准（`OPEN`）。

---

## 3. 生命周期

```text
Core Question
    → Gate
    → Admission
    → Persistence                    # Question / Instance / Material
    → Post-Admission Enrichment Job  # async
         → (optional) LLM generation
         → Validation
         → Persist enrichment result
    → Validated Result
```

### 3.1 与 Admission 解耦（`PROPOSED`）

**禁止**（除非 Frozen 另有规定）：

```text
no explanation → Gate fail → Question cannot enter DB
```

**应允许**：

```text
Core Question → Admission → Persistence → Async enrichment
```

目的：**Question identity / core factual integrity** 与 **optional semantic enrichment** 解耦。

### 3.2 状态机（`PROPOSED`）

Enrichment item 状态（独立于 Question 有效性）：

```text
absent → queued → generated → validated → accepted
                ↘ failed
                ↘ rejected
                ↘ unavailable
```

Question 本身保持 `valid/persisted`，不因 enrichment 失败而变 invalid。

---

## 4. Generated Content Authority

| 项 | 规则 |
|---|---|
| Producer explanation | `authority = Producer/Source`，保留 source provenance |
| V3 generated explanation | `authority = V3`，`generation_method = LLM` |
| 覆盖 | **禁止**覆盖或伪装成 source explanation |
| 并存 | 允许双槽；展示策略见 §8 `OPEN` |

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

## 5. Validation（生成物也必须验证）

状态（`PROPOSED`，不与 Question semantic_status 混用）：

```text
generated   # 已生成，未验证
validated   # 通过自动验证
accepted    # 通过人工/策略接受
rejected    # 验证或审核拒绝
```

规则：

1. 生成 ≠ 正确。
2. 优先复用既有 Evidence / ValidationEvent，**不得另造平行 authority**（`PROPOSED`）。
3. 自动验证最小集（`PROPOSED`，实现可裁剪）：非空、语言/长度策略、与 stem/options 无直接矛盾的启发式、禁止密钥/注入模式、可追溯 job id。
4. `accepted` 前不得对用户展示为“教材级详解”（展示策略 `OPEN`）。

---

## 6. 失败语义

若 LLM 生成失败：

```text
Question     = valid / persisted   # 不回滚、不删除
Explanation  = pending | failed | unavailable
```

允许后续：`retry` / `regeneration` / `manual review`。

**不在本 Contract 实现**复杂 retry 策略；仅定边界：

| 约束 | 值 |
|---|---|
| 失败是否影响 Question 持久化 | **否** |
| 失败是否自动删除生成半成品 | 禁止静默删除已审计记录；可标记 failed |
| 是否允许无限自动重试 | `OPEN`（需 budget / live_guard 约束） |
| 人工介入 | 允许，走 review；`accepted` 需可审计 |

---

## 7. 与 Producer / Gate / Resolver 的关系

| 组件 | 关系 |
|---|---|
| Preprocessing | 不负责 post-admission 生成；其 explanation 为 PRD |
| Consumer Boundary | 不负责生成；只保真 |
| Resolver | 不负责生成；preprocessed 路径可跳过搜索 |
| Gate | 只门禁 **admission 时已存在** 的核心完整性；**不**因 optional 缺失 fail（`PROPOSED`） |
| Admission | 只物化核心 Question；enrichment 挂后 |
| Enrichment | 只写派生槽 + validation 状态 |

---

## 8. Persistence Semantics（`PROPOSED`）

逻辑槽（不指定物理 schema；schema 变更 `OWNER DECISION REQUIRED`）：

```text
Question
  core: stem, options, answer, question_type, identity, provenance, ...
  slots:
    explanation_producer   : optional, PRD/SRC
    explanation_generated  : optional, V3D + generation provenance + validation_state
    difficulty_generated   : optional, V3D
    knowledge_generated    : optional, V3D
    skills_generated       : optional, V3D
  enrichment_jobs[]        : append-only 可审计
```

原则：

1. 不覆盖 PRD 槽。
2. jobs 可追溯。
3. 当前展示哪一槽 = `OPEN`（策略/产品决定）。
4. 与 Question dedup / identity **正交**：enrichment 不得改变 question identity hash 的语义成分（若 identity hash 排除 generated 字段，须显式记录——`OPEN` 对齐 OQ-1/identity projection 现有设计）。

---

## 9. Retry / Regeneration 边界

| 项 | Contract 边界 | 实现 |
|---|---|---|
| retry | 允许 | 未规定算法 |
| regeneration | 允许（新 job，不覆盖旧 accepted，除非显式 supersede 策略） | `OPEN` |
| supersede | 须 append 新版本 + 标记 | `OPEN` |
| budget / rate limit | 必须受 V3 live_guard / budget 约束 | `OBSERVED` 已有 budget/live_guard 模块，接线 `OPEN` |

---

## 10. 明确禁止

1. `no explanation → 拒绝入库`（在未 Frozen 为 hard requirement 前）
2. 生成物冒充 Producer/Source
3. 生成失败导致回滚 Question
4. 无 validation 直接 accepted
5. 平行于 ValidationEvent 的第二套证据权威
6. 用 enrichment 洗白 identity/provenance 失败

---

## 11. Open / Owner Decision

| 项 | 状态 |
|---|---|
| explanation 是否永远 optional | `OPEN`（依赖未来 Frozen） |
| 展示 producer vs generated 优先级 | `OPEN` |
| validation 自动规则清单 | `OPEN` |
| retry/backoff/budget 数值 | `OPEN` |
| schema 扩展（jobs 表等） | `OWNER DECISION REQUIRED` |
| identity hash 是否排除 generated | `OPEN`（对齐现有 identity projection） |

*End of Post-Admission Enrichment Contract v0.3 DRAFT.*
