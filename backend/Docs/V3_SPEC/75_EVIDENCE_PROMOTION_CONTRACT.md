# V3 Evidence Promotion Contract — Design Freeze

**Version**: 1.0.0-draft
**Date**: 2026-09-13
**Status**: DESIGN FREEZE — 待架构审查确认后进入实现
**Parent**: 74_B2B5_D_PROJECTION_SAFETY_REPORT.md v3.3.0

---

## 一、目的

定义 V3 中 Source Fragment 获得进入 Semantic IR 资格的完整生命周期。

核心问题:

> 谁可以提出 evidence proposal? 谁可以创建 claim? 谁拥有 validation 权限?
> 哪些字段是事实, 哪些是声明? 哪些状态可以进入 Semantic IR?

---

## 二、状态机

```
                    +-------------+
                    |    RAW      |
                    |   SOURCE    |
                    +------+------+
                           | (ingestion)
                           v
                    +-------------+
                    |   SOURCE    |
                    |  FRAGMENT   |  <-- 只读事实
                    +------+------+
                           | (any module may propose)
                           v
                    +-------------+
              +-----|   EVIDENCE  |
              |     |  PROPOSAL   |
              |     +-------------+
              |            | (contract-controlled promotion)
              |            v
              |     +-------------+
              |     |   EVIDENCE  |
              |     |    CLAIM    |
              |     +------+------+
              |            | (deterministic validation)
              |            v
         REJECTED    +-------------+
         (terminal)  |  VALIDATED  |--> Semantic IR
                     |  EVIDENCE   |
                     +-------------+
                            |
                     INVALIDATED (terminal)
```

### 禁止转换

| 转换 | 原因 |
|------|------|
| CLAIMED -> IR | 未验证不得进入 |
| PROPOSED -> IR | 未声明不得进入 |
| PROPOSED -> VALIDATED | 必须经过 Claim |
| VALIDATED -> CLAIMED | 不可逆 |

---

## 三、每层 Schema 定义

### 3.1 Source Fragment (只读事实)

```python
@dataclass(frozen=True)
class SourceFragment:
    """Source 的不可变切片。只记录位置/哈希/版本, 不解释含义。"""
    fragment_id: str          # 唯一标识
    source_version_id: UUID   # 所属 source 版本
    start_line_ref: str       # 起始行引用 (P{page}L{line:03d})
    end_line_ref: str         # 结束行引用
    line_refs: tuple[str, ...]  # 覆盖的行引用
    text_hash: str            # 内容 SHA-256
    granularity: str          # "line" | "line_character"
    start_offset: int | None  # 行内起始 (line_character 时)
    end_offset: int | None    # 行内结束
```

**产生者**: Resolver (确定性)
**消费者**: Evidence Proposal
**权限**: 只读, 不可变

### 3.2 Evidence Proposal (可提出, 不可消费)

```python
@dataclass(frozen=True)
class EvidenceProposal:
    """任何模块可以提出的 evidence 候选。无证据身份。"""
    proposal_id: str
    fragment_id: str              # 指向 SourceFragment
    proposed_role: str            # "answer" | "explanation" | "stem" | "option" | ...
    proposer: str                 # 提出者标识
    proposer_trust: str           # "low" | "high" (见信任等级表)
    proposal_reason: str          # 为什么认为这是 evidence
    confidence: float | None      # 提出者的置信度 (可选, 不影响 Validation)
    created_at: datetime
```

**产生者**: 任何模块 (Resolver, OCR, LLM, heuristic parser, human)
**消费者**: Evidence Claim promotion
**权限**: 只能创建, 不能直接进入 IR

### 3.3 Evidence Claim (受控升级, 等待验证)

```python
@dataclass(frozen=True)
class EvidenceClaim:
    """V3 contract 接受 proposal 后赋予的证据身份。等待验证。"""
    claim_id: str
    proposal_id: str              # 指向 EvidenceProposal
    fragment_id: str              # 指向 SourceFragment
    claimed_role: str             # 声明的证据角色
    claim_authority: str          # 谁授权了这个 claim
    claim_reason: str             # 授权依据 (e.g., "header_boundary", "frozen_rule")
    created_at: datetime
```

**产生者**: Contract-controlled promotion (非任意模块)
**消费者**: Evidence Validation
**权限**: 受控升级动作, 必须有明确 authority

### 3.4 Evidence Validation (确定性, append-only)

```python
@dataclass(frozen=True)
class ValidationEvent:
    """验证结果。append-only, 不可修改。"""
    event_id: str
    claim_id: str
    validation_result: str        # "validated" | "rejected" | "invalidated"
    checks_passed: tuple[str, ...]   # 通过的检查项
    checks_failed: tuple[str, ...]   # 失败的检查项
    validated_at: datetime
    validator: str                # "gate/v1" (确定性, 非 LLM)
```

**产生者**: Gate (确定性函数)
**消费者**: Semantic IR admission
**权限**: 确定性, append-only, 不可变

### 3.5 Validated Evidence (唯一可进入 IR)

```python
@dataclass(frozen=True)
class ValidatedEvidence:
    """通过验证的 evidence。唯一允许进入 Semantic IR 的状态。"""
    evidence_id: str
    claim_id: str
    fragment_id: str
    role: str                     # 验证后的证据角色
    text: str                     # 从 fragment 切片的正文
    text_hash: str                # 与 fragment 一致
    validation_event_id: str      # 指向 ValidationEvent
    validated_at: datetime
```

**产生者**: Validation 成功后自动产生
**消费者**: Semantic IR / Compiler
**权限**: 只读, 不可变

---

## 四、状态转换规则

### 4.1 RAW SOURCE -> SOURCE FRAGMENT

**触发**: Resolver 完成地址解析
**条件**: resolution_status in {exact, normalized}
**产生者**: Resolver (确定性)
**失败**: 不产生 Fragment (unresolved reference)

### 4.2 SOURCE FRAGMENT -> EVIDENCE PROPOSAL

**触发**: 任何模块提出 evidence 候选
**条件**: Fragment 存在且可读
**产生者**: 任意模块
**信任分级**:

| proposer | proposer_trust |
|----------|----------------|
| Native parser | low |
| OCR detector | low |
| LLM annotation | low |
| Frozen rule (header grammar) | high |
| Human review | high |

**失败**: 不产生 Proposal

### 4.3 EVIDENCE PROPOSAL -> EVIDENCE CLAIM

**触发**: Contract-controlled promotion
**条件**:
1. Proposal 指向的 Fragment 存在
2. proposed_role 在合法值域内
3. Promotion authority 授权 (非 proposal 提出者自己)

**产生者**: Contract promotion service
**失败**: Proposal 保持 PROPOSED 状态 (不升级)

### 4.4 EVIDENCE CLAIM -> VALIDATED EVIDENCE

**触发**: Gate 执行确定性验证
**检查项**:

| 检查 | 内容 | 失败后果 |
|------|------|----------|
| fragment_exists | Fragment 存在且可读 | REJECTED |
| text_hash_match | Claim 引用的 text_hash 与 Fragment 一致 | REJECTED |
| role_region_consistency | claimed_role 与 structural_regions 一致 | REJECTED |
| span_traceable | Fragment 的 span 在 ResolvedRun 中可追溯 | REJECTED |
| no_cross_version | Fragment 的 source_version_id 一致 | REJECTED |

**全部通过** -> VALIDATED
**任一失败** -> REJECTED (terminal)

**产生者**: Gate (确定性函数, 非 LLM)
**失败**: REJECTED (terminal, 不可重试)

### 4.5 VALIDATED EVIDENCE -> INVALIDATED

**触发**: Source 版本变更 / hash 不一致 / 人工撤销
**条件**: 已 VALIDATED 的 evidence 的前置条件不再满足
**产生者**: Gate / Human review
**结果**: INVALIDATED (terminal, 从 IR 移除)

---

## 五、权限边界

### 5.1 谁可以做什么

| 操作 | 允许者 | 禁止者 |
|------|--------|--------|
| 创建 SourceFragment | Resolver | 任何人 (只读) |
| 创建 EvidenceProposal | 任何模块 | — |
| 创建 EvidenceClaim | Contract promotion service | Proposal 提出者自己 |
| 执行 Validation | Gate (确定性) | LLM, 人工 |
| 创建 ValidatedEvidence | Validation 成功后自动 | 任何人手动 |
| 修改任何已创建对象 | 无 (全部 frozen) | 任何人 |

### 5.2 防自声明自验证

```
X  LLM 提出 Proposal -> LLM 创建 Claim -> LLM 验证
OK LLM 提出 Proposal -> Contract 创建 Claim -> Gate 验证
```

关键约束: **Claim 的创建者 != Proposal 的提出者**

---

## 六、与现有架构的映射

### 6.1 当前实现 -> Contract 映射

| 当前实现 | Contract 状态 |
|----------|---------------|
| ResolvedSpan | SourceFragment |
| annotation answer_zone reference | EvidenceProposal (implicit) |
| Resolver role="answer" | EvidenceClaim (implicit, 无显式 authority) |
| Gate evaluate() | ValidationEvent (部分) |
| CompiledAnswer | ValidatedEvidence (部分) |

### 6.2 差距

| 差距 | 说明 |
|------|------|
| 无显式 EvidenceProposal | 当前 annotation 直接产生 reference, 无 proposal 层 |
| 无显式 Claim authority | Resolver 直接设置 role, 无授权检查 |
| Validation 非 append-only | Gate decision 是瞬时的, 未持久化为 event |
| 无信任分级 | 所有 reference 平权 |

### 6.3 渐进式实现路径

**Phase 1** (最小改动):
- 在 ResolvedSpan 上添加 proposer 和 proposer_trust 字段
- Gate validation 结果持久化为 ValidationEvent
- 不改变现有 pipeline 流程

**Phase 2** (结构化):
- 引入显式 EvidenceProposal / EvidenceClaim dataclass
- Contract promotion service (Claim 创建 != Proposal 提出)
- 状态机 enforcement

**Phase 3** (完整):
- 信任分级影响 Validation 严格度
- INVALIDATED 状态支持
- 完整 audit trail

---

## 七、Structural Consistency 在 Contract 中的位置

Structural Consistency (structural_regions + span overlap) 是
**Validation 的一个子检查**, 不是完整的 Validation。

```
Validation
+-- fragment_exists          (地址正确)
+-- text_hash_match          (内容一致)
+-- role_region_consistency  (结构一致) <-- structural_regions 在这里
+-- span_traceable           (可追溯)
+-- no_cross_version         (版本一致)
```

Structural Consistency 解决空间错误 (拿错区域),
不解决内容错误 (OCR 误读)。
内容错误需要其他机制 (e.g., grammar validation, human review)。

---

## 八、冻结决策

以下决策在本 Contract 中冻结, 变更需走架构审查:

1. **状态机转换规则** (Section 2)
2. **每层 Schema** (Section 3)
3. **权限边界** (Section 5)
4. **禁止转换** (Section 2)
5. **信任等级表** (Section 4.2)

---

## 九、实现前置条件

在开始写代码前, 需要确认:

- [ ] 架构审查确认本 Contract 设计
- [ ] 确认 Phase 1/2/3 实现路径
- [ ] 确认与现有 pipeline 的兼容性
- [ ] 确认 ValidationEvent 持久化方案 (内存 / DB)

---

**设计状态**: DRAFT — 待审查
**下一步**: 架构审查 -> 确认后进入 Phase 1 实现
