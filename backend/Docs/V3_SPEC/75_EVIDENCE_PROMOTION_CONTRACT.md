# V3 Evidence Promotion Contract — Design Freeze

**Version**: 1.1.0-reviewed
**Date**: 2026-09-13
**Status**: REVIEWED — 架构审查通过 (含补充约束), 可进入 Phase 1 实现
**Parent**: 74_B2B5_D_PROJECTION_SAFETY_REPORT.md v3.3.0
**Review**: 架构审查 2026-09-13 — 批准, 含 5 条新增冻结规则 + 禁止规则 4 + 信任拆分 + Phase 1 路径修正

---

## 一、目的

定义 V3 中 Source Fragment 获得进入 Semantic IR 资格的完整生命周期。

核心问题:

> 谁可以提出 evidence proposal? 谁可以创建 claim? 谁拥有 validation 权限?
> 哪些字段是事实, 哪些是声明? 哪些状态可以进入 Semantic IR?

核心原则:

> **事实存在 ≠ 事实解释 ≠ 事实授权。**

---

## 二、状态机

```
RAW SOURCE
    | (ingest)
    v
SOURCE FRAGMENT ──────────────────────── state: immutable
    | (propose)
    v
EVIDENCE PROPOSAL ────────────────────── state: untrusted
    | (claim)                    |
    v                           v
EVIDENCE CLAIM ─────────────  REJECTED (terminal)
state: awaiting validation
    | (validate)
    v
VALIDATED EVIDENCE ────────────────────── state: trusted
    |                               |
    | (compile)                     | (source changed / human revoke)
    v                               v
SEMANTIC IR                  INVALIDATED (terminal)
```

### 禁止转换

| # | 转换 | 原因 |
|---|------|------|
| 1 | CLAIMED → IR | 未验证不得进入 |
| 2 | PROPOSED → IR | 未声明不得进入 |
| 3 | PROPOSED → VALIDATED | 必须经过 Claim |
| 4 | SOURCE FRAGMENT → IR | **最容易绕过的路径** — 位置不等于证据身份 |
| 5 | VALIDATED → CLAIMED | 不可逆 |

### 失败态

| 失败态 | 来源 | 含义 |
|--------|------|------|
| REJECTED | Proposal 或 Claim 阶段 | 验证不通过, terminal, 不可重试 |
| INVALIDATED | 已 VALIDATED | 前置条件不再满足 (source 变更/hash 不一致/人工撤销), 从 IR 移除 |

---

## 三、五条冻结规则

以下规则在本 Contract 中冻结, 变更需走架构审查:

| # | 规则 |
|---|------|
| R1 | **SourceFragment 永不包含 semantic role** — 它是事实层, 不是解释层 |
| R2 | **EvidenceProposal 永远不具备 evidence authority** — 提出不等于授权 |
| R3 | **EvidenceClaim 是 promotion request, 不是 truth assertion** — 表达"请求赋予身份", 不表达"这是答案" |
| R4 | **只有 ValidationEvent 产生 Evidence Authority** — authority 不可手动设置 |
| R5 | **Semantic IR 只能引用 ValidatedEvidence, 不允许越级引用任何前置层** |

---

## 四、每层 Schema 定义

### 4.1 Source Fragment (只读事实)

```python
@dataclass(frozen=True)
class SourceFragment:
    """Source 的不可变切片。只记录位置/哈希/版本, 不解释含义。

    冻结规则 R1: 本层永不包含 semantic role, confidence, 或 semantic_type。
    一旦出现 role, 它就不再是事实层, 而变成解释层。
    """
    fragment_id: str          # 唯一标识
    source_version_id: UUID   # 所属 source 版本
    start_line_ref: str       # 起始行引用 (P{page}L{line:03d})
    end_line_ref: str         # 结束行引用
    line_refs: tuple[str, ...]  # 覆盖的行引用
    text_hash: str            # 内容 SHA-256
    granularity: str          # "line" | "line_character"
    start_offset: int | None  # 行内起始 (line_character 时)
    end_offset: int | None    # 行内结束
    # 禁止字段: role, confidence, semantic_type, trust_level
```

**产生者**: Resolver (确定性)
**消费者**: Evidence Proposal
**权限**: 只读, 不可变

### 4.2 Evidence Proposal (可提出, 不可消费)

```python
@dataclass(frozen=True)
class EvidenceProposal:
    """任何模块可以提出的 evidence 候选。无证据身份。

    冻结规则 R2: 本层永远不具备 evidence authority。
    Proposal 只表达"这里可能是 evidence", 不表达"这就是 evidence"。
    """
    proposal_id: str
    fragment_id: str              # 指向 SourceFragment
    proposed_role: str            # "answer" | "explanation" | "stem" | "option" | ...
    proposer: ProposerIdentity    # 提出者身份 (见 4.2.1)
    proposal_reason: str          # 为什么认为这是 evidence
    created_at: datetime
    # 禁止字段: confidence (伪授权), trust_level (不是 Proposal 的属性)


@dataclass(frozen=True)
class ProposerIdentity:
    """提出者身份。用于审计回答"这个错误是谁提出的"。"""
    producer_type: str            # "native_parser" | "ocr" | "llm" | "heuristic" | "human"
    model: str | None             # 具体模型 (e.g., "qwen3.5-9b", "paddleocr-v4")
    pipeline_version: str | None  # 提出者的版本
```

**产生者**: 任何模块 (Resolver, OCR, LLM, heuristic parser, human)
**消费者**: Evidence Claim promotion
**权限**: 只能创建, 不能直接进入 IR

### 4.3 Evidence Claim (受控升级, 等待验证)

```python
@dataclass(frozen=True)
class EvidenceClaim:
    """V3 contract 接受 proposal 后的正式升级请求。

    冻结规则 R3: Claim 是 promotion request, 不是 truth assertion。
    表达"我请求把 Fragment X 作为 Answer Evidence", 而非"Fragment X 是 Answer Evidence"。
    后者偷渡结论, 违反 Contract 设计意图。

    禁止字段: confidence (伪授权 — Claim 不是"相信程度", 是"请求身份")
    """
    claim_id: str
    proposal_id: str              # 指向 EvidenceProposal
    fragment_id: str              # 指向 SourceFragment
    claimed_role: str             # 请求赋予的证据角色
    claim_creator: str            # 谁创建了这个 claim (必须 != proposal.proposer)
    claim_reason: str             # 请求依据 (e.g., "header_boundary", "frozen_rule")
    created_at: datetime
```

**产生者**: Contract-controlled promotion (非任意模块)
**消费者**: Evidence Validation
**权限**: 受控升级动作, 必须有明确 authority, 创建者 != Proposal 提出者

### 4.4 Evidence Validation (确定性, append-only, event sourcing)

```python
@dataclass(frozen=True)
class ValidationEvent:
    """验证结果。Event sourcing 模式 — 不是状态, 是事件。

    冻结规则 R4: 只有 ValidationEvent 产生 Evidence Authority。
    禁止 Evidence.validated = True 这种 mutable field 模式。

    未来一定会遇到: OCR 模型升级 / source version 变化 / Resolver bug 修复 / 人工重新审核。
    届时不能修改历史, 只能追加 INVALIDATED event。
    """
    event_id: str
    claim_id: str
    validation_result: str        # "validated" | "rejected" | "invalidated"
    checks_passed: tuple[str, ...]   # 通过的检查项
    checks_failed: tuple[str, ...]   # 失败的检查项
    validation_method: str        # "frozen_header_rule" | "byte_proven" | "human_review"
    validated_at: datetime
    validator: str                # "gate/v1" (确定性, 非 LLM)
```

**产生者**: Gate (确定性函数)
**消费者**: Semantic IR admission
**权限**: 确定性, append-only, 不可变

### 4.5 Validated Evidence (唯一可进入 IR)

```python
@dataclass(frozen=True)
class ValidatedEvidence:
    """通过验证的 evidence。唯一允许进入 Semantic IR 的状态。

    冻结规则 R5: Semantic IR 不接受任何非 ValidatedEvidence 引用。
    禁止 Question.answer_span → SourceFragment 这种越级引用。
    正确: Question.answer_evidence → ValidatedEvidence
    """
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

## 五、信任拆分: Provenance vs Reliability

审查意见: 不要设计成简单的 `trust_level = high/low` 容易误用。
LLM temperature=0 不代表高可靠。

**正确拆分**:

| 维度 | 字段 | 含义 | 示例 |
|------|------|------|------|
| **Provenance** | `producer_type` | 谁产生 (事实) | "ocr", "llm", "frozen_rule", "human" |
| **Reliability** | `validation_method` | 系统如何验证 (规则) | "frozen_header_rule", "byte_proven", "human_review" |

Provenance 是 Proposal 的属性 (谁提出的)。
Reliability 是 ValidationEvent 的属性 (怎么验证的)。

**示例**:

```yaml
proposal:
    producer_type: llm          # provenance: LLM 提出
    model: qwen3.5-9b

validation:
    method: frozen_header_rule  # reliability: 用冻结 header 规则验证
    result: validated
```

LLM 提出 + 冻结规则验证 = 可信。
LLM 提出 + LLM 验证 = 不可信 (自声明自验证)。

---

## 六、状态转换规则

### 6.1 RAW SOURCE → SOURCE FRAGMENT

**触发**: Resolver 完成地址解析
**条件**: resolution_status in {exact, normalized}
**产生者**: Resolver (确定性)
**失败**: 不产生 Fragment (unresolved reference)

### 6.2 SOURCE FRAGMENT → EVIDENCE PROPOSAL

**触发**: 任何模块提出 evidence 候选
**条件**: Fragment 存在且可读
**产生者**: 任意模块 (必须携带 ProposerIdentity)
**失败**: 不产生 Proposal

### 6.3 EVIDENCE PROPOSAL → EVIDENCE CLAIM

**触发**: Contract-controlled promotion
**条件**:
1. Proposal 指向的 Fragment 存在
2. proposed_role 在合法值域内
3. Claim creator != Proposal proposer (防自声明)

**产生者**: Contract promotion service
**失败**: Proposal 保持 untrusted 状态 (不升级), 或 REJECTED

### 6.4 EVIDENCE CLAIM → VALIDATED EVIDENCE

**触发**: Gate 执行确定性验证
**检查项**:

| 检查 | 内容 | 失败后果 |
|------|------|----------|
| fragment_exists | Fragment 存在且可读 | REJECTED |
| text_hash_match | Claim 引用的 text_hash 与 Fragment 一致 | REJECTED |
| role_region_consistency | claimed_role 与 structural_regions 一致 | REJECTED |
| span_traceable | Fragment 的 span 在 ResolvedRun 中可追溯 | REJECTED |
| no_cross_version | Fragment 的 source_version_id 一致 | REJECTED |

**全部通过** → VALIDATED
**任一失败** → REJECTED (terminal)

**产生者**: Gate (确定性函数, 非 LLM)

### 6.5 VALIDATED EVIDENCE → INVALIDATED

**触发**: Source 版本变更 / hash 不一致 / 人工撤销
**条件**: 已 VALIDATED 的 evidence 的前置条件不再满足
**产生者**: Gate / Human review
**结果**: INVALIDATED (terminal, 从 IR 移除)

---

## 七、权限边界

### 7.1 谁可以做什么

| 操作 | 允许者 | 禁止者 |
|------|--------|--------|
| 创建 SourceFragment | Resolver | 任何人 (只读) |
| 创建 EvidenceProposal | 任何模块 (必须带 ProposerIdentity) | — |
| 创建 EvidenceClaim | Contract promotion service | Proposal 提出者自己 |
| 执行 Validation | Gate (确定性) | LLM, 人工 |
| 创建 ValidatedEvidence | Validation 成功后自动 | 任何人手动 |
| 修改任何已创建对象 | 无 (全部 frozen) | 任何人 |

### 7.2 防自声明自验证

```
X  LLM 提出 Proposal → LLM 创建 Claim → LLM 验证
OK LLM 提出 Proposal → Contract 创建 Claim → Gate 验证
```

关键约束:
- Claim 的创建者 != Proposal 的提出者
- Validation 由确定性 Gate 执行, 不是提出者自己

---

## 八、与现有架构的映射

### 8.1 当前实现 → Contract 映射

| 当前实现 | Contract 状态 | 差距 |
|----------|---------------|------|
| ResolvedSpan | SourceFragment | 保持纯净 — 只做 location + resolution |
| EvidenceReference (新增) | EvidenceProposal | Phase 1 新增, 承接 ResolvedSpan → Proposal |
| annotation answer_zone reference | EvidenceProposal (implicit) | 无显式 proposal 层 |
| Resolver role="answer" | EvidenceClaim (implicit) | 无显式 authority |
| Gate evaluate() | ValidationEvent (部分) | 未持久化为 event |
| CompiledAnswer | ValidatedEvidence (部分) | 缺 validation_event_id |

### 8.2 Phase 1 路径修正 (架构审查)

**原方案**: 在 ResolvedSpan 上添加 proposer/trust 字段

**修正**: 不污染 ResolvedSpan

原因: ResolvedSpan 本质属于 Source Binding (在哪里), 不是 Evidence Lifecycle (凭什么)。
给 ResolvedSpan 加 proposer/trust 会让 Resolver 承担定位 + 语义 + 信任三重职责, 最终退化。

**修正方案**:

```
ResolvedSpan (保持纯净: location + resolution)
    |
    v
EvidenceReference (新增, 承接 Source Binding → Evidence Lifecycle 的桥接)
    |
    v
EvidenceProposal
```

```python
@dataclass(frozen=True)
class EvidenceReference:
    """Source Binding → Evidence Lifecycle 的桥接层。

    Resolver 产出 ResolvedSpan (纯地址)。
    EvidenceReference 承接地址, 赋予 proposal 身份。
    ResolvedSpan 不知道 evidence lifecycle 的存在。
    """
    reference_id: str
    span_id: str                  # 指向 ResolvedSpan
    proposed_role: str            # 提议的证据角色
    proposer: ProposerIdentity    # 谁提议的
    source_version_id: UUID       # 版本锚定
    created_at: datetime
```

### 8.3 渐进式实现路径 (修正后)

**Phase 1** (最小改动):
- 新增 `EvidenceReference` dataclass (承接 ResolvedSpan → Proposal)
- 新增 `ProposerIdentity` dataclass
- Gate validation 结果持久化为 `ValidationEvent` (append-only)
- **不改变 ResolvedSpan schema**
- 不改变现有 pipeline 流程

**Phase 2** (结构化):
- 引入显式 `EvidenceProposal` / `EvidenceClaim` dataclass
- Contract promotion service (Claim creator != Proposal proposer)
- 状态机 enforcement

**Phase 3** (完整):
- Reliability (validation_method) 影响 Validation 严格度
- INVALIDATED 状态支持
- 完整 audit trail

---

## 九、Structural Consistency 在 Contract 中的位置

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

## 十、冻结决策清单

以下决策在本 Contract 中冻结, 变更需走架构审查:

| # | 冻结项 | Section |
|---|--------|---------|
| 1 | 状态机转换规则 + 失败态 | 2 |
| 2 | 五条冻结规则 (R1-R5) | 3 |
| 3 | 每层 Schema 定义 | 4 |
| 4 | 信任拆分 (Provenance vs Reliability) | 5 |
| 5 | 权限边界 + 防自声明自验证 | 7 |
| 6 | 禁止转换 (含规则 4: Fragment→IR) | 2 |
| 7 | Phase 1 路径 (EvidenceReference, 不污染 ResolvedSpan) | 8 |

---

## 十一、实现前置条件

在开始写代码前, 需要确认:

- [x] 架构审查确认本 Contract 设计 (2026-09-13 批准, 含补充约束)
- [x] 确认 Phase 1/2/3 实现路径 (Phase 1 已修正: EvidenceReference 而非 ResolvedSpan 扩展)
- [x] 确认与现有 pipeline 的兼容性 (Phase 1 不改变现有流程)
- [ ] 确认 ValidationEvent 持久化方案 (内存 / DB)
- [ ] 确认 EvidenceReference 与 annotation answer_zone 的对接方式

---

**设计状态**: REVIEWED — 架构审查通过 (含 5 条补充规则 + 禁止规则 4 + 信任拆分 + Phase 1 修正)
**下一步**: 确认持久化方案 → Phase 1 实现 (EvidenceReference + ProposerIdentity + ValidationEvent)
