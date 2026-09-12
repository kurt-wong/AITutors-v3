# B2-B5-D: End-to-End Projection Safety Validation Report

**Version**: 1.0.0  
**Date**: 2026-01-27  
**Status**: COMPLETED - **发现真实安全缺口**

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
| **EXPLANATION_REGION** | ❌ **FAIL** | **发现安全缺口** |
| SEPARATOR_REGION | ✅ PASS | 分隔符 → pending_review |
| QUESTION_REGION | ✅ PASS | 问题区域 → pending_review |

### 1.3 Safety Properties

| 测试 | 结果 | 说明 |
|------|------|------|
| No search fallback | ✅ PASS | Invalid evidence 不触发 search |
| No LLM fallback | ✅ PASS | Invalid evidence 不触发 LLM |
| No source mutation | ✅ PASS | Source 不会被修改 |
| Three-state decision | ✅ PASS | True/False/None 模型正确 |

### 1.4 Corpus Validation

| 测试 | 结果 | 说明 |
|------|------|------|
| Gate C corpus frozen | ✅ PASS | 157 targets, 分布验证 |
| Corpus relationship | ✅ PASS | 157 ⊂ 267 ⊂ 706 |

**总测试数**: 13  
**通过**: 12  
**失败**: 1 (EXPLANATION_REGION)

---

## 二、发现的安全缺口

### 2.1 问题描述

**EXPLANATION_REGION 无效绑定可能绕过所有检查, 错误 auto_approve**

### 2.2 复现路径

```
场景: answer_lines 指向解释区域

Source:
  【解答】A
  【考点】fruit classification

Invalid Evidence:
  answer_lines = ["指向【解答】A"]
```

### 2.3 当前架构检查流程

```
1. Resolver: 检查结构有效性
   - answer_zone 存在? YES
   - question_number 找到? YES
   - → resolution_status = exact ✓

2. Grammar: 检查答案格式
   - _option_letters() 从 "【解答】A" 提取字母 "A"
   - "A" 在 labels 中? YES
   - → verify() = True ✓

3. Provenance: 检查 resolution_status
   - resolution_status = exact
   - → PASS ✓

4. Admission:
   - auto_blockers = []
   - → decision = auto_approve ⚠️
```

### 2.4 根本原因

**Grammar 的局限性**:

```python
def _option_letters(answer_text: str) -> tuple[str, ...]:
    """抽取出现在答案文本中的 ASCII 字母"""
    return tuple(m.group(0).upper() for m in _LETTER_RE.finditer(answer_text))
```

`_option_letters()` 会从**任何文本**提取字母, 无法区分:
- `"A"` (纯答案) → True
- `"【解答】A"` (解释包含答案) → True
- `"【答案】A"` (答案标记) → True

### 2.5 影响范围

| Invalid 类型 | Grammar 行为 | 是否安全 |
|--------------|--------------|----------|
| WRONG_REGION | None | ✅ 安全 |
| **EXPLANATION_REGION** | **True** | ❌ **不安全** |
| SEPARATOR_REGION | None | ✅ 安全 |
| QUESTION_REGION | None | ✅ 安全 |
| SUSPICIOUS_CONTENT | None | ✅ 安全 |

**影响**: EXPLANATION_REGION (49 targets) 可能错误 auto_approve

---

## 三、架构分析

### 3.1 当前分层职责

| 层 | 职责 | 是否检测 EXPLANATION_REGION |
|----|------|---------------------------|
| Resolver | 结构有效性 | ❌ 不检测 |
| Compiler | 编译 IR | ❌ 不检测 |
| Grammar | 答案格式 | ❌ **误判为 True** |
| Provenance | resolution_status | ❌ 不检测语义 |
| Admission | 准入控制 | ❌ 无 blocker |

### 3.2 为什么现有机制失效

1. **Resolver 不验证语义**: 符合架构设计 (结构层 ≠ 语义裁判)
2. **Grammar 无法识别上下文**: `_option_letters()` 是纯正则, 无语义理解
3. **Provenance 只检查 resolution_status**: 不检查 answer 内容语义
4. **无 answer region 分类**: 系统不知道 answer 指向哪种区域

---

## 四、建议修复方案

### 方案 A: Preprocessing 增加 answer region 标记 (推荐)

在 Preprocessing 阶段标记每个 answer 的区域类型:

```json
{
  "answer_zone": "【解答】A",
  "answer_region_type": "EXPLANATION",
  "is_valid_answer_region": false
}
```

**优点**:
- 在源头解决问题
- 不影响 Resolver/Grammar 职责边界
- 可追溯

**缺点**:
- 需要修改 Preprocessing
- 需要定义 region taxonomy

### 方案 B: Grammar 增加 prefix 检测

修改 `_option_letters()` 检测已知无效前缀:

```python
_INVALID_PREFIXES = ["【解答】", "【答案】", "【考点】", "【分析】"]

def _clean_answer(answer_text: str) -> str:
    # 先剥离题号前缀
    cleaned = _LEAD_QN_RE.sub("", answer_text).strip()
    # 再检测无效前缀
    for prefix in _INVALID_PREFIXES:
        if cleaned.startswith(prefix):
            return None  # 或返回特殊标记
    return cleaned
```

**优点**:
- 快速修复
- 不改架构

**缺点**:
- 正则维护成本
- 可能误判
- 不解决根本问题

### 方案 C: Gate 增加 answer semantic layer

在 Gate 增加专门的 answer semantic 检查:

```python
def _leaf_answer_semantic(leaf: CompiledLeaf) -> tuple[bool, str] | None:
    """检查 answer 是否指向有效答案区域"""
    if leaf.answer is None:
        return None
    
    text = leaf.answer.text.strip()
    
    # 检测已知无效模式
    invalid_patterns = [
        r"^【解答】",
        r"^【答案】",
        r"^【考点】",
        r"^【分析】",
        r"^---$",
    ]
    
    for pattern in invalid_patterns:
        if re.match(pattern, text):
            return False, f"answer matches invalid pattern: {pattern}"
    
    return None  # 无法确定, pending_review
```

**优点**:
- 符合 Gate 职责 (安全层)
- 可扩展
- 不破坏分层

**缺点**:
- 增加 Gate 复杂度
- 正则维护

---

## 五、推荐方案

**采用方案 A + C 组合**:

1. **短期 (Gate C 前)**: 实现方案 C, 在 Gate 增加 answer semantic 检查
2. **长期 (Path B 完善)**: 实现方案 A, 在 Preprocessing 标记 region 类型

### Gate C 前必须修复

在宣布 Gate C 通过前, 必须:

1. [ ] 实现 EXPLANATION_REGION 检测机制
2. [ ] 验证 49 个 EXPLANATION_REGION targets 全部 pending_review
3. [ ] 更新测试, EXPLANATION_REGION 测试 PASS
4. [ ] 重新运行完整 Gate C corpus 测试

---

## 六、数字澄清

### 6.1 集合关系

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

### 6.2 冻结定义

- **Gate C Invalid Binding Evidence Corpus** = 157 targets
- **排除 EMPTY_REGION**: "no answer_zone is not invalid evidence, just no answer claim"
- **包含 SUSPICIOUS_CONTENT**: 需要验证 fail-closed 行为

---

## 七、结论

### 7.1 B2-B5-D 状态

**部分完成, 发现安全缺口**

已证明:
- ✅ S1/S2/S3 正向投影可行
- ✅ WRONG_REGION/SEPARATOR_REGION/QUESTION_REGION 安全
- ✅ 无 search/LLM fallback
- ✅ 无 source mutation

未证明:
- ❌ EXPLANATION_REGION 安全性 (发现真实缺口)
- ❌ 完整 157 targets E2E 测试

### 7.2 Gate C 状态

**BLOCKED - 需要先修复 EXPLANATION_REGION 缺口**

### 7.3 下一步

1. **立即**: 实现 EXPLANATION_REGION 检测机制 (方案 C)
2. **验证**: 测试 49 个 EXPLANATION_REGION targets
3. **完成**: 运行完整 157 targets E2E 测试
4. **关闭**: Gate C

---

## 八、测试证据

### 8.1 测试文件

- `tests/test_b2b5_d_projection_safety.py`

### 8.2 测试结果

```
13 tests collected
12 passed
1 failed (EXPLANATION_REGION)
```

### 8.3 安全缺口证据

```python
from app.domains.gate.grammar import verify

# 纯答案
verify("single_choice", "A", ("A", "B"))  # → True

# 解释包含答案
verify("single_choice", "【解答】A", ("A", "B"))  # → True (BUG!)

# 两者无法区分
```

---

**报告生成**: AI Tutor V3 Team  
**审核状态**: 发现安全缺口, Gate C BLOCKED  
**下一步**: 修复 EXPLANATION_REGION 检测机制
