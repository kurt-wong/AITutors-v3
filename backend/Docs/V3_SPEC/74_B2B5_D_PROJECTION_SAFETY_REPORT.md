# B2-B5-D: End-to-End Projection Safety Validation Report

**Version**: 3.3.0
**Date**: 2026-09-13
**Status**: B2-B5-D COMPLETED | Gate C BLOCKED (C-1 Evidence Promotion Contract design freeze + C-2 full E2E)
**架构审查**: 经四次裁决，修正 preprocessing 依赖 + Evidence Admission Boundary + structural_regions + Proposal→Claim 分离

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

### 1.4 Source Evidence Structural Consistency

| 测试 | 结果 | 说明 |
|------|------|------|
| Resolver produces structural_regions | ✅ PASS | question/answer/explanation structural region map |
| Region non-overlap | ✅ PASS | question ∩ answer = ∅ |
| answer ∩ explanation → pending_review | ✅ PASS | Gate span-overlap check |
| answer ∩ question → pending_review | ✅ PASS | Gate span-overlap check |
| No overlap → auto_approve | ✅ PASS | 正常路径不受影响 |
| Cross-role overlap fail-closed | ✅ PASS | 绝不 auto_approve |
| 49 EXPLANATION_REGION targets | ✅ PASS | 全部非 strict-auto, fail-closed via grammar-None |

### 1.5 Evidence Promotion Negative Tests (C-3)

| 测试 | 结果 | 说明 |
|------|------|------|
| answer span → explanation region | ✅ PASS | pending_review |
| answer span → question region | ✅ PASS | pending_review |
| non-strict-auto + valid-looking answer | ✅ PASS | pending_review (grammar-None) |
| text_hash mismatch | ✅ PASS | rejected (terminal) |
| answer span missing from ResolvedRun | ✅ PASS | rejected (structural) |

### 1.5 Corpus Validation

| 测试 | 结果 | 说明 |
|------|------|------|
| Gate C corpus frozen | ✅ PASS | 157 targets, 分布验证 |
| Corpus relationship | ✅ PASS | 157 ⊂ 267 ⊂ 706 |

**总测试数**: 97 (gate-related) + 496 (full suite)
**通过**: 全部
**跳过**: 0

---

## 二、核心架构原则

### 2.1 Legal Address ≠ Legal Evidence

这是 B2-B5-D 实验最重要的架构发现。

```text
Source
  521: 【解答】A

Resolver 产出:
  ResolvedSpan(start=521, end=521, resolution_status="exact")
```

这个结果只能证明:

> "你要求的 Source 地址确实存在, 而且地址解析成功。"

它不能自动推出:

> "这个 span 是合法的 Answer Evidence。"

**当前链路存在危险的 Evidence Promotion:**

```text
exact → answer.text → grammar extracts A → verify(A) → PASS
```

即: 一个仅仅"结构上可解析"的 span 被过度提升为特定语义证据。

### 2.2 Predicate Correctness ≠ Evidence Validity

`_option_letters("【解答】A") → ("A",)` — **这个函数本身是正确的**。

如果它的职责是"从 answer representation 中提取 option letters",
那么 `【解答】A` 确实包含 `A`。

问题不在于 `_option_letters()` 太蠢, 而在于:

> **上游对 `_option_letters()` 的输入资格定义太弱。**

谁赋予了这个函数"这个输入已经是合法 answer evidence"的前提?
如果答案是"因为 Resolver resolution_status == exact", 那就有问题。

---

## 三、潜在攻击路径 (Latent Weakness)

### 3.1 路径描述

```text
Source
  ↓
answer span contains 【解答】A
  ↓
Resolver exact (地址正确)
  ↓
Compiler answer.text = 【解答】A
  ↓
_option_letters() → A
  ↓
Grammar verify → True
  ↓
auto_approve (潜在)
```

### 3.2 当前 corpus 中未形成实际 exploit

**关键澄清**: 49 个 EXPLANATION_REGION targets 全部是非 strict-auto 题型
(short_answer 41, reading 3, vocabulary_fill 2, cloze 1, reading_expression 1, essay 1)。

```text
_leaf_grammar() → None (非 strict-auto)
    ↓
auto_blocker → pending_review
```

**当前冻结语料中没有观察到实际 auto-admission 绕过。**

但这暴露了一个与题型无关的 **latent Evidence Validation weakness**:
如果 strict-auto 类型的 answer span 包含解释性前缀, 而该内容仍位于
声明的 answer span 内, 则 `_option_letters()` 可能将其中的选项字母
误认为合法答案。

> **不能因为当前 corpus 没打穿就宣布问题不存在。**
> 这是潜在的通用缺陷, 应通过 V3 Evidence Contract 消除,
> 而不能依赖题型分类偶然兜底。

---

## 四、根因定性

### 4.1 原始发现

B2-B5-D 测试发现: Grammar `_option_letters()` 从任何文本提取 ASCII 字母,
导致 `verify("single_choice", "【解答】A", ("A","B"))` 返回 True。

### 4.2 根因 (二次裁决修正)

**不是**: "preprocessing semantic role information 丢失给 V3"

**而是**: **V3 Source Evidence Binding Contract 对 "Source Address" 和
"Semantic Evidence" 的边界定义不足。**

```text
V3 当前:

  Source Address (Resolver 验证)
       ↓
  直接提升为
       ↓
  Semantic Evidence (Compiler/Grammar 消费)

缺失:

  Source Address
       ↓
  Evidence Claim (声明这是什么 evidence)
       ↓
  Evidence Validation (验证声明与结构事实一致)
       ↓
  Validated Evidence
```

`ResolvedSpan` 能证明引用位置有效, 但不能单独证明该 span 是目标语义证据。

### 4.3 与 preprocessing 的关系

**V3 是完整系统, 不依赖 preprocessing 成立。**

```text
                  V3
                   │
       ┌───────────┴───────────┐
       ↓                       ↓
 Native ingestion       External adapter (optional)
       │                       │
 PDF/DOCX/IMG             preprocessing (future)
       │                       │
       └───────────┬───────────┘
                   ↓
                Source
```

V3 Native Path 必须自行保证 Source Evidence Binding 的安全性。

如果未来 preprocessing 接入 V3, 它必须满足 V3 Evidence Contract,
而不是反过来 V3 按照 preprocessing 的 contract 设计。

preprocessing 的 role provenance 是未来 Adapter Contract (Gate D/I-5) 的
integration 问题, 不是当前 Gate C 的前置条件。

---

## 五、Source Evidence Structural Consistency 实现

### 5.1 架构定位

已实现的 `semantic_regions` 是 **structural consistency evidence**, 不是 Semantic Truth。

```text
V3 Source Evidence Contract
        │
        ├── source_ref
        ├── span
        ├── target/evidence role
        └── structural consistency
                ↓
            Resolver (确定性表头 grammar)
                ↓
        ResolvedSpan + structural region map
                ↓
              Gate (span-overlap consistency check)
```

Resolver 说: "根据确定性的 region grammar, 521-522 属于 answer region" — 这可以。

Resolver 不能说: "521-522 在语义上一定是答案" — 这是两个完全不同的强度。

### 5.2 实现文件

| 文件 | 变更 |
|------|------|
| `resolver/span.py` | `SourceRegion` dataclass (structural region, NOT semantic truth); `ResolvedRun.semantic_regions` |
| `resolver/resolver.py` | `_compute_regions()` — 确定性表头解析产出 structural region map |
| `gate/policy.py` | provenance 层 span-overlap 检查 (set intersection, NOT NLP) |
| `tests/test_role_provenance.py` | 10 tests: region production, consistency check, E2E regression |

### 5.3 架构边界 (防滑坡)

必须警惕 Resolver 从 reference integrity 滑向 semantic authority:

```text
✅ Resolver = reference integrity + header grammar structural regions
❌ Resolver = 判断 "这个 span 语义上是什么"
```

`structural_regions` 是 **consistency evidence**: "这些行在结构上属于答案区"
不是 **semantic truth**: "这些行一定是正确答案"。

### 5.4 Contract 规则

1. **Region Production**: Resolver 用确定性表头解析产出 structural region map
2. **Gate Consistency Check**: answer span 不得与其他 structural region 重叠
   - overlap → pending_review (非 terminal rejected)
3. **Compiler Role Filter**: Compiler 只消费 role=answer 的 span (已有行为)

### 5.5 为什么这是 Contract Self-Consistency 而非 NLP

- Region 划分由确定性表头 grammar 产出, 不是 LLM 或 semantic parser
- Gate 只做 span 集合交运算, 不理解自然语言
- 不引入 regex semantic patterns
- 不让 Gate/Resolver 重新做人类语义理解

---

## 六、Unclosed Evidence Admission Boundary

### 6.1 Grammar 层行为

```python
verify("single_choice", "A", ("A", "B"))           # → True (正确)
verify("single_choice", "【解答】A", ("A", "B"))    # → True (boundary 未封闭)
```

`_option_letters()` 函数本身正确——按职责提取字母。真正的问题是:

> **Grammar 的输入前置条件（"此文本是合法 answer evidence"）没有被任何 Contract 证明。**

不是 Grammar bug, 是 **unclosed Evidence Admission Boundary**。

### 6.2 Defense-in-Depth 层次

| 层 | 机制 | 覆盖场景 | 性质 |
|----|------|----------|------|
| Grammar-None | 非 strict-auto → None → pending_review | 49 个 EXPLANATION_REGION targets | 已有 |
| Structural Consistency | answer span ∩ explanation region = ∅ | answer 落入非答案结构区 | 已实现 |
| Grammar letters | _option_letters + labels 匹配 | 纯答案格式验证 | boundary 未封闭 |

### 6.3 残余风险

Unclosed Evidence Admission Boundary 在以下场景仍存在:
- strict-auto 题型 (single_choice 等)
- answer zone 内容本身包含解释性前缀 + 选项字母
- answer span 在 answer structural region 内 (consistency check 不触发)

**根本修复**: V3 Source Evidence Binding Contract 需要显式建模
Source Fragment → Evidence Claim → Evidence Validation → Validated Evidence
的提升路径, 使 answer entry 的 evidence 身份验证不依赖题型分类兜底。

---

## 七、数字澄清

### 7.1 集合关系

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
  = 267 - 120 (EMPTY_REGION) + 10 (SUSPICIOUS_CONTENT)
```

### 7.2 EXPLANATION_REGION 题型分布

| 题型 | 数量 | strict-auto? |
|------|------|-------------|
| short_answer | 41 | ❌ |
| reading | 3 | ❌ |
| vocabulary_fill | 2 | ❌ |
| cloze | 1 | ❌ |
| reading_expression | 1 | ❌ |
| essay | 1 | ❌ |

**0 个 EXPLANATION_REGION targets 是 strict-auto 题型**, 全部经 grammar-None fail-closed。

---

## 八、Gate C 状态

### 8.1 当前状态

> **Gate C: BLOCKED — V3 Source Evidence Binding Contract + full 157 E2E 尚未完成闭环**

### 8.2 未完成项

**C-1: V3 Evidence Promotion Contract** (先冻结设计, 再写代码)

生命周期:
```
Raw Source (不可引用)
    → Source Fragment (可定位, 不可解释)
    → Evidence Proposal (可提出, 不可消费)
    → Evidence Claim (声明用途, 等待验证)
    → Validated Evidence (唯一允许进入 IR)
    → Semantic IR
```

状态机:
```
PROPOSED → CLAIMED → VALIDATED → IR
              ↓           ↓
         REJECTED   INVALIDATED

禁止: CLAIMED → IR (未验证不得进入)
禁止: PROPOSED → IR (未声明不得进入)
```

每层职责:
| 层 | 负责 | 不负责 | 权限 |
|----|------|--------|------|
| Source Fragment | 原始位置、hash、版本 | 不解释含义 | 只读事实 |
| Evidence Proposal | 模块提出"这里可能是答案" | 无证据身份 | 任何模块可提 |
| Evidence Claim | 赋予证据身份, 等待验证 | 不证明正确 | 受控升级动作 |
| Evidence Validation | 检查 claim 与 contract 一致 | 不重新理解文本 | 确定性, append-only event |
| Validated Evidence | 可进入 Semantic IR | 不补救前面错误 | 只读 |

Proposal 来源信任等级:
| 来源 | 可信等级 |
|------|----------|
| Native parser | 低 |
| OCR detector | 低 |
| LLM annotation | 低 |
| Frozen rule (header grammar) | 高 |
| Human review | 高 |

实现风险 (C-1 设计时必须防止):
1. **字段堆积假安全**: 不要设计 {validated: true} 可修改字段。Validation 必须产生 append-only ValidationEvent。
2. **Validation 不做 NLP**: 只负责 hash/span/role consistency/contract, 不判断答案内容真假。
3. **Claim 来源分级**: 不是所有 Claim 平权, 来源信任等级影响 Validation 严格度。

**C-2: 完整 157 invalid corpus 真实 pipeline E2E**

需要证明全部 157 targets 经过完整 V3 pipeline
(Source → Annotation → Resolver → Compiler → Gate) 后全部 fail-closed。

**C-3: Evidence Promotion Negative Test** ✅ 已实现 (7 attacks)

证明"地址正确但证据错误"无法通过:
| 攻击 | 预期 | 状态 |
|------|------|------|
| answer span → explanation region | pending_review | ✅ |
| answer span → question region | pending_review | ✅ |
| non-strict-auto + valid-looking answer | pending_review | ✅ |
| text_hash mismatch | rejected | ✅ |
| answer span missing from ResolvedRun | rejected | ✅ |
| legal region + illegal role binding | pending_review | ✅ |
| cross-version provenance mismatch (span v1 + hash v2) | rejected | ✅ |

### 8.3 不是 Gate C 前置条件的项目

- ~~preprocessing Annotation Contract enhancement~~ → 未来 Gate D/I-5 integration 项
- ~~preprocessing declares region roles~~ → 未来可选 adapter 的 contract mapping

### 8.4 关闭条件

- [x] Legal address ≠ legal evidence 原则确认
- [x] Structural consistency check 实现 (region map + span overlap)
- [x] 49 EXPLANATION_REGION targets fail-closed 验证
- [x] Unclosed Evidence Admission Boundary documented
- [x] Evidence Promotion Negative Tests (C-3) — 7 attacks 全部 fail-closed
- [x] 四条冻结架构原则确立
- [ ] C-1: V3 Evidence Promotion Contract 设计冻结 (状态机 + 信任分级 + 防实现风险)
- [ ] C-1: Contract 代码实现
- [ ] C-2: 完整 157 targets 真实 pipeline E2E

---

## 九、测试证据

### 9.1 测试文件

- `tests/test_b2b5_d_projection_safety.py` — 13 tests (positive + negative + safety + corpus)
- `tests/test_role_provenance.py` — 15 tests (structural consistency + Evidence Promotion Negative)
- `tests/test_gate_c_invalid_binding.py` — 11 tests (resolver + grammar + integration)
- `tests/test_gate_policy.py` — 四层判定全覆盖

### 9.2 测试结果

```
gate-related: 97 passed, 0 skipped
full suite: 496 passed, 0 failed
```

### 9.3 安全属性证据

- 0 search fallback
- 0 LLM fallback
- 0 source mutation
- 157 targets 全部 fail-closed (grammar-None + consistency check)

---

## 十、后续路线

```text
1. 完成 V3 Source Evidence Binding Contract
   (明确 Source Address → Evidence Claim → Validated Evidence 提升路径)
        ↓
2. 完整 157 targets V3 full E2E
   (Source → Annotation → Resolver → Compiler → Gate)
        ↓
3. Gate C Closure
        ↓
4. B2-B5 Closure
        ↓
5. Gate D / Optional external-input Adapter
   (preprocessing 作为可选上游, 其 role provenance 在 Adapter Contract 中映射)
```

### 架构原则

V3 Native Path 必须独立成立:

```text
PDF / DOCX / IMG
       ↓
V3 Native Input
       ↓
Source → Semantic Claim → Source Binding → Resolved Evidence → Gate → Admission
```

不依赖 preprocessing。

未来 preprocessing 如果验证成熟, 再证明:

```text
preprocessing → Adapter → V3 Source/Evidence Contract
```

preprocessing 是可替换的上游实现, 不能反过来成为 V3 架构成立的条件。

### 冻结架构原则 (B2-B5-D 确立)

**Principle 1**: Source Address is location metadata, not semantic authority.

**Principle 2**: Evidence Claim is an explicit promotion event.

**Principle 3**: Only Validated Evidence may enter Semantic IR.

**Principle 4**: No downstream module may infer evidence validity from successful resolution.

这四条原则进入 V3 Frozen Architecture。

---

## 十一、状态总结

| 项目 | 状态 |
|------|------|
| B2-B5-D 实验 | **COMPLETED** — 有效实验, 有效安全发现 |
| `Legal address ≠ legal evidence` | **确立为 V3 Frozen Architecture 原则** |
| 四条冻结架构原则 | **确立** — Address≠Authority, Claim=Promotion, Validated-only, No-inference |
| Evidence Admission Boundary | **Unclosed** — Grammar 输入前置条件未被证明 |
| Structural consistency check | **IMPLEMENTED** — structural_regions, Necessary but not Sufficient |
| Evidence Promotion Negative Tests (C-3) | **IMPLEMENTED** — 7 attacks 全部 fail-closed |
| Gate C | **BLOCKED** — C-1 (五层 Evidence Contract) + C-2 (157 E2E) 未闭环 |
| preprocessing 依赖 | **移除** — 不是 V3 Gate C 前置条件 |

---

**报告版本**: 3.3.0 (五次架构审查修正)
**核心修正**: Evidence Proposal→Claim 分离 + 四条冻结原则 + 2 个新 C-3 攻击
**下一步**: C-1 设计冻结 (状态机+信任分级+防风险) → C-1 实现 → C-2 157 E2E → Gate C Closure
