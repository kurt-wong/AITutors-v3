# B2-B5-D: End-to-End Projection Safety Validation Report

**Version**: 2.0.0
**Date**: 2026-09-13
**Status**: COMPLETED - Semantic Role Provenance Contract implemented

---

## 一、测试覆盖

### 1.1 Positive Projection (S1/S2/S3)

| 测试 | 结果 | 说明 |
|------|------|------|
| S1 Standalone Subjective | ✅ PASS | 独立主观题完整链路 |
| S2 Composite + Sub-question | ✅ PASS | 层级结构保持, 不会 flatten |
| S3 Composite + Material | ✅ PASS | Shared material 不会 duplication |

### 1.2 Negative Projection Safety

| 测试 | 结果 | 说明 |
|------|------|------|
| WRONG_REGION | ✅ PASS | 错误区域 → pending_review |
| EXPLANATION_REGION | ✅ PASS | Grammar limitation documented + contract-based detection |
| SEPARATOR_REGION | ✅ PASS | 分隔符 → pending_review |
| QUESTION_REGION | ✅ PASS | 问题区域 → pending_review |

### 1.3 Safety Properties

| 测试 | 结果 | 说明 |
|------|------|------|
| No search fallback | ✅ PASS | Invalid evidence 不触发 search |
| No LLM fallback | ✅ PASS | Invalid evidence 不触发 LLM |
| No source mutation | ✅ PASS | Source 不会被修改 |
| Three-state decision | ✅ PASS | True/False/None 模型正确 |

### 1.4 Semantic Role Provenance Contract

| 测试 | 结果 | 说明 |
|------|------|------|
| Resolver produces semantic_regions | ✅ PASS | question/answer/explanation region map |
| Region non-overlap | ✅ PASS | question ∩ answer = ∅ |
| answer ∩ explanation → pending_review | ✅ PASS | Gate span-overlap check |
| answer ∩ question → pending_review | ✅ PASS | Gate span-overlap check |
| No overlap → auto_approve | ✅ PASS | 正常路径不受影响 |
| Cross-role overlap fail-closed | ✅ PASS | 绝不 auto_approve |
| 49 EXPLANATION_REGION targets | ✅ PASS | 全部非 strict-auto, fail-closed |

### 1.5 Corpus Validation

| 测试 | 结果 | 说明 |
|------|------|------|
| Gate C corpus frozen | ✅ PASS | 157 targets, 分布验证 |
| Corpus relationship | ✅ PASS | 157 ⊂ 267 ⊂ 706 |

**总测试数**: 92 (gate-related) + 491 (full suite)
**通过**: 全部
**跳过**: 0

---

## 二、发现的安全缺口与根因修正

### 2.1 原始发现

B2-B5-D 测试发现: Grammar `_option_letters()` 从任何文本提取 ASCII 字母,
导致 `verify("single_choice", "【解答】A", ("A","B"))` 返回 True。

### 2.2 根因修正 (架构审查裁决)

**原判断**: "Gate 缺少语义检测能力" → 建议增加 regex semantic layer
**修正判断**: **Semantic Role Provenance Loss**

```
真正的问题:

Preprocessing (LLM)          Manifest              Resolver
     │                          │                      │
     ├─ 知道 521-522 是 answer   ├─ 只记录 answer_zone  ├─ 只验证 line span
     ├─ 知道 523-530 是 explain  │   reference          │
     │                          │                      │
     └─ 语义角色信息丢失 ←────────┴──────────────────────┘
```

**信息丢失位置**: Preprocessing → Manifest Contract

**拒绝的修复方向**: Gate-side regex semantic patterns
- 会让 Gate 退化为半个 NLP parser (V2 trap)
- Regex 无法解决 role identity 问题
- 违反 V3 分层原则: 后面的确定性模块不能重新做语义理解

**采纳的修复方向**: 增强 manifest/resolver contract, 让语义角色信息贯穿链路

### 2.3 影响范围

| Invalid 类型 | Grammar 行为 | Role-Provenance Contract | 是否安全 |
|--------------|--------------|--------------------------|----------|
| WRONG_REGION | None | N/A | ✅ 安全 |
| EXPLANATION_REGION | True (limitation) | ✅ 检测 overlap | ✅ 安全 (defense-in-depth) |
| SEPARATOR_REGION | None | N/A | ✅ 安全 |
| QUESTION_REGION | None | ✅ 检测 overlap | ✅ 安全 |
| SUSPICIOUS_CONTENT | None | N/A | ✅ 安全 |

**关键发现**: 49 个 EXPLANATION_REGION targets 全部是非 strict-auto 题型
(short_answer 41, reading 3, vocabulary_fill 2, cloze 1, reading_expression 1, essay 1),
经 grammar-None 路径 fail-closed。Grammar limitation 只影响 strict-auto 题型
(single_choice/multiple_choice/true_false), 语料中无此类 target。

---

## 三、Semantic Role Provenance Contract 实现

### 3.1 架构设计

```
Resolver (确定性表头解析)
  │
  ├─ 用 H-3 header grammar 划分 question/answer/explanation region
  │
  ├─ 产出 semantic_regions: tuple[SourceRegion, ...]
  │   SourceRegion(role, start_seq, end_seq, line_refs)
  │
  └─ 冻结进 ResolvedRun.semantic_regions

Gate (contract self-consistency)
  │
  ├─ 消费 resolved_run.semantic_regions
  │
  ├─ 对每个 leaf 的 answer span:
  │   answer_lines ∩ explanation_region_lines = ∅ ?
  │   answer_lines ∩ question_region_lines = ∅ ?
  │
  └─ overlap → auto_allowed=False → pending_review
```

### 3.2 实现文件

| 文件 | 变更 |
|------|------|
| `app/domains/resolver/span.py` | 添加 `SourceRegion` dataclass; `ResolvedRun` 添加 `semantic_regions` 字段 |
| `app/domains/resolver/resolver.py` | 添加 `_compute_regions()` 方法; `resolve()` 产出 region map |
| `app/domains/gate/policy.py` | provenance 层添加 role-provenance 检查; admission 层 surface violations |
| `tests/test_role_provenance.py` | 10 个测试: region production, contract check, E2E regression |

### 3.3 Contract 规则

1. **Region Production**: Resolver 用确定性表头解析产出 region map
   - question region: 首个 answer/explanation 表头之前的行
   - answer region: answer 表头之后、explanation 表头之前的行
   - explanation region: explanation 表头之后的行

2. **Gate Consistency Check**: answer span 不得与其他 role region 重叠
   - answer ∩ explanation = ∅
   - answer ∩ question = ∅
   - overlap → pending_review (非 terminal rejected)

3. **Compiler Role Filter**: Compiler 只消费 role=answer 的 span (已有行为)

### 3.4 为什么这是 Contract Self-Consistency 而非 NLP

- Region 划分由 Resolver 的确定性表头 grammar (H-3) 产出, 不是 LLM
- Gate 只做 span 集合交运算 (set intersection), 不理解自然语言
- 不引入新的 regex semantic patterns
- 不让 Gate 重新做人类语义理解

---

## 四、Grammar Limitation 与 Defense-in-Depth

### 4.1 Grammar Limitation (已知, 已记录)

```python
verify("single_choice", "A", ("A", "B"))           # → True (正确)
verify("single_choice", "【解答】A", ("A", "B"))    # → True (limitation)
```

`_option_letters()` 提取所有 ASCII 字母, 无法区分纯答案和包含答案的解释文本。

### 4.2 Defense-in-Depth 层次

| 层 | 机制 | 覆盖场景 |
|----|------|----------|
| Grammar | 字母提取 + labels 匹配 | 纯答案格式验证 |
| Role-Provenance Contract | answer span ∩ explanation region = ∅ | answer 落入 explanation region |
| Grammar-None (非 strict-auto) | 非 strict-auto 题型 → pending_review | 49 个 EXPLANATION_REGION targets |

### 4.3 残余风险

Grammar limitation 在以下场景仍存在:
- strict-auto 题型 (single_choice 等)
- answer zone 内容本身是 explanation 标记 + 选项字母
- answer span 在 answer region 内 (不与 explanation region 重叠)

**根本修复**: 需要 preprocessing 在 manifest 中声明 region role,
使 answer entry 不指向 explanation content。这是 Annotation Contract 的增强,
属于后续工作。

---

## 五、数字澄清

### 5.1 集合关系

```
gate_b2b5_frozen_testset.json (706 targets)
├── deterministically_representable: 429
├── invalid_binding_evidence: 267
│   ├── EMPTY_REGION: 120
│   ├── WRONG_REGION: 56
│   ├── EXPLANATION_REGION: 49
│   ├── SEPARATOR_REGION: 27
│   └── QUESTION_REGION: 15
└── suspicious_content: 10

gate_c_invalid_binding_corpus.json (157 targets)
├── WRONG_REGION: 56
├── EXPLANATION_REGION: 49
├── SEPARATOR_REGION: 27
├── QUESTION_REGION: 15
└── SUSPICIOUS_CONTENT: 10

关系: 157 = 267 - 120 (EMPTY_REGION) + 10 (SUSPICIOUS_CONTENT)
```

### 5.2 EXPLANATION_REGION 题型分布

| 题型 | 数量 | strict-auto? |
|------|------|-------------|
| short_answer | 41 | ❌ |
| reading | 3 | ❌ |
| vocabulary_fill | 2 | ❌ |
| cloze | 1 | ❌ |
| reading_expression | 1 | ❌ |
| essay | 1 | ❌ |

**结论**: 0 个 EXPLANATION_REGION targets 是 strict-auto 题型,
全部经 grammar-None 路径 fail-closed。

---

## 六、Gate C 状态

### 6.1 修正前

**BLOCKED** - 原因: "EXPLANATION_REGION security gap, 需要 regex semantic layer"

### 6.2 修正后

**BLOCKED** - 原因: **"Source Binding Contract incomplete"**

Semantic Role Provenance Contract 已实现 (Resolver region map + Gate span-overlap check),
但 Grammar limitation 仍存在于 strict-auto 题型的 answer zone 内容层面。
根本修复需要增强 Annotation Contract, 让 preprocessing 声明 region role。

### 6.3 关闭条件

- [x] Role provenance test — answer role + explanation span → reject
- [x] Cross-role overlap test — answer_lines ∩ explanation_lines → fail closed
- [x] E2E regression — 49 个 EXPLANATION_REGION targets 全部非 strict-auto, fail-closed
- [x] Resolver produces semantic_regions map
- [x] Gate consumes semantic_regions for span-overlap check
- [ ] Annotation Contract enhancement (preprocessing declares region roles) — 后续工作
- [ ] 完整 157 targets E2E 测试通过真实 pipeline

---

## 七、测试证据

### 7.1 测试文件

- `tests/test_b2b5_d_projection_safety.py` — 13 tests (12 PASS + 1 documented limitation)
- `tests/test_role_provenance.py` — 10 tests (10 PASS)
- `tests/test_gate_c_invalid_binding.py` — 11 tests (11 PASS)

### 7.2 测试结果

```
gate-related: 92 passed, 0 skipped
full suite: 491 passed, 0 failed
```

### 7.3 Contract 验证证据

```python
# Resolver produces region map
run = resolver.resolve(payload)
assert run.semantic_regions  # (SourceRegion(question,...), SourceRegion(answer,...))

# Gate detects overlap
overlap_region = SourceRegion("explanation", 0, 999, answer_span.line_refs)
run_with_overlap = ResolvedRun(..., semantic_regions=run.semantic_regions + (overlap_region,))
d = evaluate(root, ir, compiled, run_with_overlap)
assert d["decision"] == "pending_review"
assert "role provenance" in " ".join(d["reasons"])
```

---

## 八、后续工作

1. **Annotation Contract Enhancement**: preprocessing 在 manifest 中声明 region role,
   使 answer entry 不指向 explanation content (根本修复 Grammar limitation)
2. **完整 157 targets E2E**: 用真实 pipeline 跑通全部 Gate C corpus
3. **Gate C Closure**: 所有条件满足后关闭 Gate C
4. **B2-B5 Closure**: Gate C 关闭后关闭 B2-B5
5. **Gate D (Adapter Boundary)**: 下一个 Gate

---

**报告生成**: AI Tutor V3 Team
**审核状态**: Semantic Role Provenance Contract implemented, Gate C BLOCKED (Source Binding Contract incomplete)
**下一步**: Annotation Contract enhancement + 完整 157 targets E2E
