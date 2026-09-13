# OQ-1: B5-3 Identity 分层分析

Status: **Adjudicated / CLOSED — PASS / TEST-EVIDENCED**
Date: 2026-09-11
Predecessors: 67 §3.3, 69 §3 B5-3, 69 §9 Step 3 裁决
Gate: A（Identity Closure）— **PASS / TEST-EVIDENCED**（514/514 regression）

---

## 0. 问题定义

67 号提议允许 Annotation payload 携带 `line_refs`（Source Binding Claim）。
69 号 B5-3 裁决：**不能直接从 P6 推导 "line_refs 必须/不必进入 identity hash"**，
需要定义三层 Identity 的关系并证明 A1/A2/A3。

核心问题：**Semantic Annotation 的身份由什么决定？Source Binding Claim 的变化
是否构成 Annotation 的语义变化？**

---

## 1. 当前 Identity 体系（代码事实）

### 1.1 Identity 清单

| Identity | 代码位置 | 输入 | UNIQUE? | 用途 |
|----------|---------|------|---------|------|
| `logical_execution_hash` | `hashing.py:65` | `{task_type, stage, contract_domain, input_domain}` | ✓ `(stage, hash)` | Annotation/Candidate 幂等 |
| `annotation_payload_hash` | `service.py:231` | `_annotation_identity_projection(payload)` | — | LE hash 成分 |
| `resolver_input_hash` | `service.py:255` | `{projected_payload, source_version_id}` | — | input_identity 存储列 |
| `compiler_input_hash` | `service.py:258` | `{resolved_spans_summary}` | — | input_identity 存储列 |
| Question `dedup_key` | `compiler.py:146` | `{canonical_type, stem_norm, options_canonical}` | ✓ | 跨文档语义去重 |
| `occurrence_key` | `compiler.py:165` | `{unit_id, qn, stem_refs, stem_offsets}` | — | 文档内出现位置 |

### 1.2 compile-stage LE hash 的 input_domain

```python
# service.py:229-235
input_domain = {
    "annotation_id": str(annotation_id),
    "annotation_payload_hash": sha256_hex(_annotation_identity_projection(ann.payload)),
    "unit_id": unit_id,
}
```

`_annotation_identity_projection` 当前只剔除 `confidence`（BUG-V3-039），
其余字段原样进入 hash。

### 1.3 关键观察

**annotation_id 已经在 input_domain 中。** 由于 Annotation 是不可变的（创建后
payload 不可修改），同一 annotation_id 的 payload 恒定 → annotation_payload_hash 恒定
→ LE hash 恒定 → 幂等成立。

这意味着：**annotation_payload_hash 的实际作用不是区分"不同 annotation"（annotation_id
已经做了），而是检测"同一 annotation_id 下 payload 是否被篡改"（防御性校验）。**

---

## 2. 三层 Identity 模型定义

### 2.1 Semantic Identity（语义身份）

**回答："这是什么？"**

| 成分 | 来源 | 进入 hash? |
|------|------|-----------|
| `unit_id` | annotation | ✓ |
| `original_question_type` | annotation | ✓ |
| `content.stem.question_label` | annotation | ✓ |
| `content.options[].label` | annotation | ✓ |
| `content.answer.*` | annotation | ✓ |
| `shared_components` | annotation | ✓ |
| `sub_questions[]` | annotation | ✓ |
| `confidence` | annotation | ✗（诊断元数据） |
| **`line_refs`** | annotation (67 新增) | **✗（Source Binding Claim）** |

**hash 载体**：`annotation_payload_hash = sha256_hex(_annotation_identity_projection(payload))`

**投影规则**：`_annotation_identity_projection` 剔除 `confidence` + `line_refs`。

### 2.2 Source Binding Claim（源绑定声明）

**回答："我认为它在哪里？"**

| 成分 | 来源 | 性质 |
|------|------|------|
| `line_refs` | annotation (67 新增) | LLM 的定位声明，非事实 |

**存储**：完整保留在 `annotation.payload` 中（不可变存储）。

**不进入**：`annotation_payload_hash`（Semantic Identity）。

**进入**：`resolver_input_hash`（Resolver 需要知道 LLM 声称的位置才能验证）。

### 2.3 Resolved Evidence（已验证证据）

**回答："代码验证后，它实际引用了什么？"**

| 成分 | 来源 | 性质 |
|------|------|------|
| `span_id` | Resolver | 确定性验证结果 |
| `line_refs` | Resolver（验证后的引用） | 已验证的 Source 位置 |
| `text_hash` | Resolver（从 Source 计算） | Source 内容完整性 |
| `resolution_status` | Resolver | exact/normalized/contextual/... |

**hash 载体**：`compiler_input_hash = sha256_hex({resolved_spans_summary})`

**进入**：`occurrence_key`（`stem_refs` 来自已验证的 resolved span）。

---

## 3. Identity 关系推导

### 3.1 层间关系

```text
Semantic Identity (annotation_payload_hash)
        │
        │ 1:N（同一语义结构可有不同绑定声明）
        ▼
Source Binding Claim (line_refs in payload)
        │
        │ 1:N（同一声明可验证出不同结果，取决于 Source Version）
        ▼
Resolved Evidence (compiler_input_hash / occurrence_key)
```

**关键结论**：三层之间是 **1:N:N** 关系，不是 1:1。

- 同一 Semantic Identity + 不同 Binding Claim → 不同 Resolved Evidence
- 同一 Binding Claim + 不同 Source Version → 不同 Resolved Evidence
- 同一 Semantic Identity + 同一 Binding Claim + 同一 Source Version → 同一 Resolved Evidence

### 3.2 与现有 hash 的映射

| 层 | hash 载体 | 67 后的变化 |
|----|----------|-----------|
| Semantic Identity | `annotation_payload_hash` | 投影增加剔除 `line_refs` |
| Source Binding Claim | `resolver_input_hash` | 输入增加 `line_refs`（已在 payload 中） |
| Resolved Evidence | `compiler_input_hash` / `occurrence_key` | 不变（已消费 resolved span） |

### 3.3 LE hash 的语义

```text
LE hash = f(task_type, stage, contract_domain, {annotation_id, annotation_payload_hash, unit_id})
```

- `annotation_id`：唯一标识一个不可变 Annotation 实例
- `annotation_payload_hash`：防御性校验（payload 未被篡改）
- `unit_id`：区分多 top-level unit

**67 后**：`annotation_payload_hash` 剔除 `line_refs` → 同一 annotation_id 的 LE hash
不受 `line_refs` 影响 → 幂等不变。

**但**：`annotation_id` 本身已经唯一。如果 LLM 重新标注产生不同 `line_refs`，
这是一个新的 annotation（新 annotation_id）→ 新 LE hash → 新 Candidate。
这是正确行为：不同的 Binding Claim 应该产生不同的 Candidate。

---

## 4. A1/A2/A3 证明

### A1: 不同 line_refs + same semantic annotation → 不无意义地制造不同 Annotation identity

**场景**：同一文档，同一语义结构，LLM 两次标注产生不同 `line_refs`。

**分析**：
- 两次标注产生两个不同的 annotation（不同 `annotation_id`）
- `annotation_payload_hash`（剔除 `line_refs`）相同 → Semantic Identity 相同
- LE hash 不同（因为 `annotation_id` 不同）→ 两个 Candidate
- Question `dedup_key` 相同（基于 compiled text）→ 复用同一 Question
- `occurrence_key` 不同（`stem_refs` 不同）→ 两个 Instance

**结论**：Semantic Identity 不分裂（`dedup_key` 相同），Instance 正确区分
（不同 occurrence）。**A1 满足。**

**边界情况**：如果两个 annotation 的 `line_refs` 验证后指向完全相同的
span（LLM 输出格式微调但语义位置相同），则 `occurrence_key` 也相同 →
Instance 复用。这也是正确行为。

### A2: 真正不同的 semantic content → different identity，不能因 line_refs 被剥离而错误合并

**场景**：两个 annotation 有不同语义结构，但恰好有相同 `line_refs`。

**分析**：
- `annotation_payload_hash` 不同（语义成分不同）→ Semantic Identity 不同
- LE hash 不同 → 两个 Candidate
- Question `dedup_key` 不同 → 两个 Question

**结论**：语义不同 → identity 不同。剥离 `line_refs` 不影响语义区分。**A2 满足。**

### A3: ResolvedSpan 的 Source identity 不得被 Annotation identity 覆盖

**场景**：Annotation identity 变化（如 prompt 版本升级），但 Source Version 不变。

**分析**：
- `ResolvedSpan` 的身份由 `source_version_id` + `span_id` + `text_hash` 决定
- 这些字段来自 Source（Seal 层），不来自 Annotation
- `compiler_input_hash` 基于 `resolved_spans_summary`（含 `text_hash`），
  不基于 `annotation_payload_hash`
- `occurrence_key` 基于 `stem_refs`（来自 resolved span），不基于 annotation identity

**结论**：ResolvedSpan 的 Source identity 独立于 Annotation identity。**A3 满足。**

---

## 5. 对现有代码的影响

### 5.1 需要修改

| 文件 | 修改 | 原因 |
|------|------|------|
| `service.py:48` `_annotation_identity_projection` | 增加剔除 `line_refs` | Semantic Identity 不含 Binding Claim |
| `service.py:255` `resolver_input_hash` | 无需修改（payload 已含 line_refs） | Resolver 需要知道声明位置 |

### 5.2 不需要修改

| 文件 | 原因 |
|------|------|
| `hashing.py` | LE hash 计算逻辑不变 |
| `compiler.py` | dedup_key / occurrence_key 消费 resolved span，不消费 annotation line_refs |
| `admission.py` | 物化逻辑不变 |
| 数据库 schema | 不变 |

### 5.3 兼容性

- 旧 annotation（无 `line_refs`）：`_annotation_identity_projection` 剔除不存在的字段 → 无影响
- 新 annotation（有 `line_refs`）：投影后 payload 与旧格式一致 → Semantic Identity 兼容

---

## 6. 结论

### 6.1 Identity 分层裁决

```text
Semantic Identity    = annotation_payload_hash（剔除 confidence + line_refs）
                       → 决定 "这是什么题"
                       → 进入 LE hash（幂等锚点）

Source Binding Claim = line_refs in payload（完整存储，不进 Semantic Identity）
                       → 决定 "LLM 认为在哪里"
                       → 进入 resolver_input_hash（供 Resolver 验证）

Resolved Evidence    = compiler_input_hash / occurrence_key（基于 resolved span）
                       → 决定 "实际引用了什么"
                       → 进入 Candidate / Instance
```

### 6.2 核心规则

1. **`line_refs` 不进入 `annotation_payload_hash`**（Semantic Identity）
2. **`line_refs` 完整保留在 payload 中**（不可变存储）
3. **`line_refs` 进入 `resolver_input_hash`**（Resolver 需要知道声明位置）
4. **`occurrence_key` 基于验证后的 resolved span**（不基于原始声明）
5. **Question `dedup_key` 基于 compiled text**（不基于 line_refs）

### 6.3 Gate A 通过条件

| 条件 | 状态 |
|------|------|
| A1: 不同 line_refs 不无意义分裂 Semantic Identity | ✓ 已证明 |
| A2: 不同语义不因剥离 line_refs 错误合并 | ✓ 已证明 |
| A3: ResolvedSpan Source identity 不被 Annotation identity 覆盖 | ✓ 已证明 |
| 实施修改范围明确且最小 | ✓ 仅 `_annotation_identity_projection` 一处 |
| 向后兼容 | ✓ 旧 payload 无 line_refs → 无影响 |

---

## 7. 遗留问题

本分析解决了 Gate A（Identity Closure）。以下问题不在 OQ-1 范围内：

- OQ-2：Standalone + Material 的 Annotation Contract 表达
- OQ-3：物化层 leaf Question 独立性
- Gate B：Legacy vs Path B 真实 corpus 对比
- Gate C：Safety Invariant Preservation 验证
