# B2-B5 Subjective / Sub-question / Material 裁决记录

> ⚠️ **SUPERSEDED — 已归档，不得作为引用来源（`90 §2 R8`，D-01 裁决 2026-09-13）**
>
> 本文件是 **71 号的 stale 份**。同号曾存在两份且内容不同（`diff` = DIFFERENT）：
>
> | 份 | 时间 | 大小 | 现状 |
> |---|---|---|---|
> | **本文件**（原 `Docs/V3_SPEC/71_…`） | Sep 12 **21:33** | 6914 B | **STALE，已归档** |
> | `Docs/DECISIONS/71_B2B5_…`（原 `backend/Docs/V3_SPEC/71_…`） | Sep 12 **23:05** | 7783 B | **(CORRECTED) — 权威版** |
>
> **权威版**：`Docs/DECISIONS/71_B2B5_SUBJECTIVE_SUBQUESTION_ADJUDICATION.md`
>
> **本文件正文保留为审计证据**（不删除、不改写）；但按 `90 §2 R8`：
> 不得作为引用来源、不得进入新文档的引用搜索结果、`docs_audit/` 标 `deprecated`。

**Document Type**: Experiment Report
**Authority Level**: L4
**Status**: **SUPERSEDED**
**Normative**: NO
**Supersedes**: —
**Superseded By**: `Docs/DECISIONS/71_B2B5_SUBJECTIVE_SUBQUESTION_ADJUDICATION.md`
**Gate State Authority**: NO

Status: Adjudicated — 语义裁决 + 测试集冻结完成
Date: 2026-09-11
Predecessors: 68_QUESTION_STRUCTURE_DEFINITION.md, 69_ARCHITECTURE_REVIEW_ADJUDICATION.md
Context: Phase I-5 Path B Full Closure — B2-B5 Domain Contract First

---

## 1. 裁决目标

验证当前 V3 Domain Model 是否能够表达真实语料中的 Subjective、Sub-question、Composite、Material 结构。

**核心问题**：已有 preprocessing evidence 能否被 V3 确定性验证，并投影到当前 Domain / IR；如果不能，是 Binding Evidence 问题、Domain Contract expressiveness gap，还是上游 manifest defect？

**禁止事项**：
- 扩展 preprocessing parser
- 增加 regex 以提高覆盖率
- 让 LLM 重新解释 preprocessing artifact
- 让 Resolver 搜索 Source 作为 fallback
- 修改 Domain Model 以迎合单个样本

---

## 2. 冻结语义原则

| 原则 | 状态 |
|------|------|
| Composite = 一个 Question | ✅ 已确认（68 §2.1） |
| Sub-question 是 Question 内部的 answerable part，不是独立 Question entity | ✅ 已确认（68 §1.4） |
| Subjective 可以是独立 Question，也可以是 Composite 内部的 sub-question | ✅ 已确认 |
| Material 是语义支撑对象，不是"纯文本附件" | ✅ 已确认（68 §1.5） |
| Material 可以是 text / image / figure / table / chart / map / diagram / mixed | ✅ 已确认（68 §1.5） |
| Composite + Material 是合法结构 | ✅ 已确认（68 §1.5） |
| Standalone Question + Material 在语义上也是合法结构 | ✅ 已确认（68 §1.5） |
| Composite 不要求必须存在 textual Material | ✅ 已确认（68 §1.5） |
| 不得因为当前 Annotation Contract 表达能力不足，就反向修改语义定义 | ✅ 已确认 |

---

## 3. Domain Contract Matrix

### 3.1 S1: Standalone Subjective / Sub-question

**Count**: 469 targets

**Evidence**: answer_lines + original_question_type

**Current Domain**: Question + InstanceRoleContent (role=answer)

**Projection**: Direct: QuestionInstance → InstanceRoleContent with answer role

**Status**: deterministically_representable

**Sub-types**:
- short_answer: 407
- fill_in: 37
- essay: 17
- single_choice: 4
- true_false: 4

---

### 3.2 S2: Composite + Sub-question

**Count**: 94 targets

**Evidence**: answer_lines + material_lines + questions_lines

**Current Domain**: UnitGroup + UnitGroupMember + Material + MaterialLink

**Projection**: UnitGroup(shared_material_id) → QuestionInstances → InstanceRoleContent

**Status**: deterministically_representable

**Sub-types**:
- short_answer: 81
- reading: 9
- cloze: 1
- reading_expression: 1
- vocabulary_fill: 2

---

### 3.3 S3: Composite + Material + Subjective

**Count**: 143 targets

**Evidence**: answer_lines + material_lines

**Current Domain**: UnitGroup + Material + MaterialLink + InstanceRoleContent

**Projection**: UnitGroup(shared_material_id) → Material → QuestionInstances

**Status**: deterministically_representable

**Sub-types**:
- reading: 58
- short_answer: 75
- seven_to_five: 5
- reading_expression: 4
- essay: 1

---

### 3.4 S4: Standalone + Material

**Count**: 0 targets（当前语料中无此结构）

**Evidence**: material_lines（如果存在）

**Current Domain**: Material + MaterialLink（standalone_question schema 无 material/depends_on 字段）

**Projection**: NOT EXPRESSIBLE — standalone_question schema 没有 material/depends_on 字段

**Status**: domain_contract_gap

**说明**：68 §1.5 明确指出这是 Contract Expressiveness Gap，不是业务模型冲突。当前语料中无此结构，属于理论缺口。

---

## 4. Coverage Boundary Report

### 4.1 四类分类

| 类别 | Count | 说明 |
|------|-------|------|
| A. Deterministically Representable | 530 | 已有 evidence 可以机械验证，并且当前 V3 Domain / IR 可以表达 |
| B. Domain Contract Expressiveness Gap | 0 | Evidence 本身可以确定性验证，但当前 Domain / Annotation / IR 无法表达 |
| C. Invalid Binding Evidence | 176 | answer_lines 指向空行（上游 manifest defect） |
| D. Insufficient Evidence | 0 | 当前材料不足以判断 |

### 4.2 Category A 明细

**By category**:
- S1: 349
- S2: 92
- S3: 89

**By original_question_type**:
- short_answer: 436
- fill_in: 37
- reading: 26
- essay: 15
- reading_expression: 5
- single_choice: 4
- true_false: 4
- cloze: 1
- vocabulary_fill: 2

### 4.3 Category C 明细

**By category**:
- S1: 120
- S2: 2
- S3: 54

**说明**：这些 targets 的 answer_lines 指向空行，是上游 preprocessing manifest defect，不是 Path B coverage failure。应冻结为 Invalid Binding Evidence Corpus，供 Gate C 对抗性测试使用。

---

## 5. Expressiveness Gap 清单

### 5.1 已发现的 Gap

**当前语料中：0 个**

### 5.2 理论 Gap（68 §1.5 确认）

**Standalone + Material**

- **描述**：独立 Question 引用 Material（如"阅读下面材料，回答第 1 题"）
- **当前 Domain**：standalone_question schema 无 material/depends_on 字段
- **状态**：DEFERRED / ERRATA CANDIDATE
- **当前语料**：0 个 cases
- **影响**：不影响当前 Gate B 闭合，留待后续 Errata 处理

---

## 6. B2-B5 Adjudication

### 6.1 核心结论

> **当前 V3 Domain Model 足以支撑真实语料中的 Subjective / Sub-question / Material 场景（706 个 targets 中 530 个 deterministically representable，176 个是上游 manifest defect）。**

### 6.2 关键发现

1. **Domain Model 表达能力充足**：所有 S1/S2/S3 结构都可以通过 Question + InstanceRoleContent + Material + MaterialLink + UnitGroup 表达。

2. **Standalone + Material 是理论缺口**：当前语料中无此结构，不影响 Gate B 闭合。

3. **176 个 Invalid Binding Evidence**：上游 manifest defect（answer_lines 指向空行），应冻结为 Gate C 对抗性语料。

4. **0 个 Insufficient Evidence**：所有 targets 都有足够 evidence 进行判断。

### 6.3 对 Gate B 的影响

**正面**：
- Domain Model 表达能力已验证
- 不需要扩展 Domain Model
- 不需要 Errata（除 Standalone + Material 理论缺口）

**负面**：
- 176 个 manifest defect 需要在 Gate C 中作为负向语料测试

### 6.4 下一步

1. **Gate B 可以关闭**（Subjective / Sub-question / Material 边界已验证）
2. **进入 Gate C**（Safety Invariant Preservation）
3. **Gate C 使用 176 个 Invalid Binding Evidence 作为对抗性语料**

---

## 7. 附录

### 7.1 Frozen Testset

文件：`backend/Docs/V3_SPEC/gate_b2b5_frozen_testset.json`

- audit_version: B2-B5-A-v1
- total_targets: 706
- category_distribution: S1=469, S2=94, S3=143
- v3_status_distribution: deterministically_representable=530, invalid_binding_evidence=176

### 7.2 语义原则来源

- 68_QUESTION_STRUCTURE_DEFINITION.md
- 69_ARCHITECTURE_REVIEW_ADJUDICATION.md
