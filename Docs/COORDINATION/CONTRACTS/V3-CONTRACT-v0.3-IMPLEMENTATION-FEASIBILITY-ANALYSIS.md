# V3-CONTRACT-v0.3-IMPLEMENTATION-FEASIBILITY-ANALYSIS

> **状态**：`ANALYSIS` / `NON-AUTHORITATIVE` / `NOT FROZEN` / `NOT A MIGRATION AUTHORIZATION` / `NOT AN X3 ENTRY DECISION`
>
> **性质**：Contract-to-Code Gap Analysis / Implementation Feasibility Analysis
> **不是** production code 实现任务；**不修改** production code / schema / Frozen Spec / corpus / Contract v0.3
>
> **对照合同**：`AITutors-v3@968943f` 五件套 v0.3-DRAFT + `PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md`
> **对照实现**：`AITutors-v3/backend/app/**` + `backend/scripts/preprocessing_consumer/**` + `backend/tests/**`
> **对照 Spec**：`Docs/V3_SPEC/00–50`（Baseline—Frozen）
>
> **证据标签**：`OBSERVED` / `DERIVED` / `PROPOSED` / `OPEN` / `OWNER DECISION REQUIRED`
> **分类标签**：`ALREADY IMPLEMENTED` / `PARTIALLY IMPLEMENTED` / `ADAPTATION REQUIRED` / `NEW IMPLEMENTATION REQUIRED` / `BLOCKED BY OWNER DECISION` / `BLOCKED BY FROZEN SPEC` / `BLOCKED BY SCHEMA` / `NOT YET IMPLEMENTABLE`

**Security（逐字）**：Never hardcode API Keys/Passwords/Tokens/Secrets; Always use .env for configuration.

---

## 1. Executive Summary

> **当前 V3 距离实现 v0.3 Contract 到底还有多远？**

**一句话**：核心准入链（IR → Compiler → Gate → Admission → Persistence）已按 Frozen Spec 落地且可运行；但 **v0.3 真正新增的边界保真、统一 identity、Post-Admission Enrichment 三大块，分别处于「丢失未接」「半接线」「Schema/Spec 双阻塞」状态**。完成 14 项 Owner Decision 之后，仍需要 **6 个实现阶段** 才能宣称 v0.3 可运行，其中 Enrichment 必须先过 Schema 与 Frozen 边界。

### 1.1 距离总览

| Contract 区块 | 当前距离 | 主分类 |
|---|---|---|
| A. Consumer Boundary（Scope/M1–M5/统一入口） | **远** | `PARTIALLY IMPLEMENTED` + `BLOCKED BY OWNER DECISION` |
| B. Producer Facts 信息保真 | **远** | `PARTIALLY IMPLEMENTED`（大量 silent drop） |
| C. V3 Semantic Enrichment（difficulty/knowledge/skills） | **中** | `PARTIALLY IMPLEMENTED`（knowledge 表有、写路径无） |
| D. Gate / Admission | **近** | `ALREADY IMPLEMENTED`（与 Frozen 一致）+ 少量 `ADAPTATION` |
| E. Post-Admission Enrichment | **很远** | `BLOCKED BY SCHEMA` + `BLOCKED BY FROZEN SPEC` + `BLOCKED BY OWNER DECISION` |

### 1.2 五个决定性事实（`OBSERVED`）

1. **Producer 字段在 Consumer 层大量静默丢失**——`flags`/`qc_verdict` **从未被 consumer 读取**；`basis`/`basis_evidence`/`answer_evidence`/`printed_provenance`/`section_ref`/`printed_number` 在 reader 保留后被 adapter 丢弃。这直接违反 v0.3 P1/P3（尚未实现，不是实现 bug 误判）。
2. **M1–M5 只存在于 `runner_b2`**；`TaskExecutor`/`GateService` 生产链 **不调用** M1–M5。`runner.py` 仅有 Interface Scope 却可进入 production `GateService`（NEW-F1）。
3. **`mapping_registry` 是治理脚手架，生产零 import**；runtime 归一化权威在 `scripts/preprocessing_consumer/boundary.normalize_unit_type`（双权威，OD-V3-14）。
4. **explanation 在 Frozen Spec 与代码中均为 optional**——v0.3「缺 explanation 不阻入库」与 Frozen 一致，**不是** Contract 相对代码的缺口；真正的缺口是 **generated explanation 无处安放**（`InstanceRoleContent.text` Frozen 禁 LLM 来源）。
5. **Post-Admission Enrichment 无 job 模型、无 generated 槽、无 difficulty/skills schema**；可复用的是 Task/LLM/Budget/live_guard/ValidationEvent 基础设施。

### 1.3 分类计数（本报告矩阵）

| 分类 | 约计 |
|---|---|
| `ALREADY IMPLEMENTED` | 18 |
| `PARTIALLY IMPLEMENTED` | 22 |
| `ADAPTATION REQUIRED` | 11 |
| `NEW IMPLEMENTATION REQUIRED` | 14 |
| `BLOCKED BY OWNER DECISION` | 16 |
| `BLOCKED BY FROZEN SPEC` | 6 |
| `BLOCKED BY SCHEMA` | 7 |
| `NOT YET IMPLEMENTABLE` | 3 |

> 计数为矩阵行归类主标签；一行可同时具有次级阻塞（正文注明）。

---

## 2. Contract → Code Matrix

### 图例

| 列 | 含义 |
|---|---|
| Req | Contract requirement |
| Code | FILE · SYMBOL · CURRENT BEHAVIOR |
| Test | 测试/执行证据 |
| Class | 上表八分类之一 |
| Why | 分类理由（禁止 “needs work / minor change”） |

### A. Consumer Boundary

| Req | Code | Test | Class | Why |
|---|---|---|---|---|
| A1 Producer Artifact input | `manifest_reader.load_manifest` 读入 units/identity/行区间/answer_evidence/basis 等；`source_loader.load_source_lines` 读 .md 行 | `test_x26_integration_boundary.py` | `PARTIALLY IMPLEMENTED` | 输入面存在，但 `flags`/`qc` 全目录零命中，未构成完整 Producer Artifact 消费 |
| A2 Interface Scope | `boundary.enforce_interface_scope` 唯一接入点；`identity_version∈{2,"2"}`；sha 64 hex | `test_x26_frb01_identity_version_types.py`；runner/runner_b2 均调用 | `ALREADY IMPLEMENTED`（harness）/ `PARTIALLY IMPLEMENTED`（production） | harness 已统一；`TaskExecutor`/`GateService` 不经过 Scope |
| A3 M1 Manifest identity | `core/manifest_identity.read_manifest_identity` | `test_x26_m1_acceptance_shapes.py` | `PARTIALLY IMPLEMENTED` | 仅 `runner_b2` 调用；生产入口未接 |
| A4 M2 raw bytes | `core/raw_bytes_identity.load_raw_bytes_identity` | 同上 + `test_raw_bytes_identity.py` | `PARTIALLY IMPLEMENTED` | 同上 |
| A5 M3 IR identity | `core/ir_identity.read_ir_identity` | 同上 | `PARTIALLY IMPLEMENTED` | 同上；batch 定位含 path/positional fallback（弱定位） |
| A6 M4 三方一致+双轴 | `core/identity_verifier.verify_identity` | `test_identity_verifier.py`、`test_adversarial_m4_round2.py` | `PARTIALLY IMPLEMENTED` | 仅 runner_b2 |
| A7 M5 Identity Gate | `core/identity_gate.evaluate_identity_gate`（VERIFIED+PENDING=BLOCK） | `test_identity_gate.py`、`test_adversarial_m5_*` | `PARTIALLY IMPLEMENTED` | 仅 runner_b2；生产无调用 |
| A8 Scope∧M1–M5 统一入口 | v0.3 §2.2 要求所有 entrypoint | NEW-F1：`runner.py` 无 M1–M5 可进 GateService | `BLOCKED BY OWNER DECISION` | OD-V3-16/19 未裁决；对齐方式未定 |
| A9 canonicalization 仅授权映射 | `boundary.normalize_unit_type` OD-2 两条 + 幂等 + fail closed | `test_x26_integration_boundary.py:273-320` | `PARTIALLY IMPLEMENTED` | 规则正确，但生产 IR 不经 boundary（拒 legacy）；映射双权威未决 |
| A10 evidence preservation | adapter `known_gaps` 登记部分；flags/basis 未进任何 V3 通道 | consumer-report-b2-r2 | `NEW IMPLEMENTATION REQUIRED` | P3 要求的可下链能力在集成边界后断裂 |
| A11 provenance preservation | span `line_refs`/`text_hash` 保留；`printed_provenance`/`source_lines` 明细未进 IR/payload | `resolved_span_adapter` | `PARTIALLY IMPLEMENTED` | 行锚保留，Producer provenance 语义丢失 |
| A12 fail-closed | `BoundaryViolation`；IR `unit_type` ValueError；Gate pending/rejected | `test_ir.py` F-M3-04；`test_gate_policy.py` | `ALREADY IMPLEMENTED` | 词表/身份/结构层 fail-closed 已落地 |
| A13 no silent information loss | P1 八归类 | — | `NEW IMPLEMENTATION REQUIRED` | 当前存在多处 silent drop/默认值（见 §3） |
| A14 no silent semantic mutation | P2 | `normalize_unit_type` 拒 `andalone_question` | `PARTIALLY IMPLEMENTED` | UT 路径合规；`verified_correct` 物化时被置 True（见 §4） |

### B. Producer Facts（对照 Information Preservation Matrix）

| Req | Code | Test | Class | Why |
|---|---|---|---|---|
| B1 identity (`source_content_sha256`) | M1/M2/boundary | M1–M5 tests | `PARTIALLY IMPLEMENTED` | 能力在，入口不全 |
| B2 unit identity (`unit_id`) | `IRBuilder`/payload/`occurrence_key` 含 unit_id | `test_ir_identity.py` | `ALREADY IMPLEMENTED` | 原样进入 IR 与 occurrence |
| B3 question identity (`question_numbers`) | adapter：standalone 取 `[0]`；composite `"a-b"` | `annotation_adapter._qn` | `PARTIALLY IMPLEMENTED` | 原列表未保留；IPM 要求可逆 |
| B4 stem | role 声明 + ResolvedSpan + CompiledRole | `test_compiler.py` | `ALREADY IMPLEMENTED` | 表示变化合法（line→span） |
| B5 options | 整块 span；per-label gap `OPTION_LABEL_SPAN_UNAVAILABLE` | `annotation_adapter:92-101` | `PARTIALLY IMPLEMENTED` | 整块保真；label 粒度 `unsup`（OD-V3-06） |
| B6 answer | span + `CompiledAnswer`；`answer_lines or answer_evidence_lines` fallback | `runner_b2:273-274` | `PARTIALLY IMPLEMENTED` | 正文可进；`answer_evidence.type/value` 丢 |
| B7 explanation | optional role；可缺 | `content_roles_for` | `ALREADY IMPLEMENTED`（保留路径） | Producer explanation 有 span 路径；generated 无槽（见 E） |
| B8 material | composite shared_components + Material 表 | `test_compiler.py`、admission 物化 | `ALREADY IMPLEMENTED` | 278/278 ref 可解析（历史验证） |
| B9 subquestion | 单子题折叠 + gap `SUB_QUESTION_DECOMPOSITION_UNAVAILABLE` | `annotation_adapter:132-148` | `PARTIALLY IMPLEMENTED` | 显式 gap，符合 unsup；粒度不足是 Producer Gap（OD-V3-07） |
| B10 question type | `original_question_type` 进 IR；`map_canonical_type` exact | `compile/__init__.py:49` | `PARTIALLY IMPLEMENTED` | verbatim 到 IR；闭集 enforcement 未在 boundary（OD-V3-12） |
| B11 unit type | boundary OD-2；IR 闭集 | F-M3-04 tests | `PARTIALLY IMPLEMENTED` | 正确规则 + 双权威未决 |
| B12 printed number | reader 读入 | adapter/span **丢** | `NEW IMPLEMENTATION REQUIRED` | IPM `pres`/`unc` 未满足 |
| B13 basis | reader 读入 | adapter/span **丢** | `NEW IMPLEMENTATION REQUIRED` | P3 明确不得消失 |
| B14 basis_evidence | reader 读入 | adapter/span **丢** | `NEW IMPLEMENTATION REQUIRED` | 同上 |
| B15 answer_evidence | reader 读入 | 仅 b2 用 lines fallback；type/value 丢 | `NEW IMPLEMENTATION REQUIRED` | IPM `ev`/`unsup` 未登记到 V3 |
| B16 flags | **consumer 未读** | grep 零命中 | `NEW IMPLEMENTATION REQUIRED` | IPM：丢 flag = violation |
| B17 QC | **consumer 未读** | 同上 | `NEW IMPLEMENTATION REQUIRED` | `qc_verdict`/`disposition` 未进消费面 |
| B18 provenance | 部分 span；`printed_provenance`/`section_ref` 丢 | — | `PARTIALLY IMPLEMENTED` | 见 A11 |

### C. V3 Semantic Enrichment

| Req | Code | Test | Class | Why |
|---|---|---|---|---|
| C1 difficulty | **无列/无表** | models grep 空 | `BLOCKED BY SCHEMA` | Frozen 10 无 difficulty 字段；需 OD-V3-25 同类 schema 决策 |
| C2 knowledge nodes | `KnowledgeNode`/`QuestionKnowledgeLink` 表存在；payload `knowledge_links=[]` 恒空 | `test_models_schema.py` | `PARTIALLY IMPLEMENTED` | Frozen 允许 optional derived；写路径未建 |
| C3 skills/abilities | **无表** | grep 空 | `BLOCKED BY SCHEMA` | 同 C1 |
| C4 其它 V3D 元数据 | 无通用 derived 槽 | — | `NOT YET IMPLEMENTABLE` | 00 §5「复杂统计富化」= M1 非目标；扩大的能力面需先裁决范围 |
| C5 V3D ≠ PRD | SAM §1 铁律 | identity projection 分离 confidence | `PARTIALLY IMPLEMENTED` | 原则在代码注释/投影中可见；generated 槽未建则无法完整落实 |

### D. Gate / Admission

| Req | Code | Test | Class | Why |
|---|---|---|---|---|
| D1 canonical IR | `IRBuilder` + `validate_ir` 不变量 1–8 | `test_ir.py` | `ALREADY IMPLEMENTED` | 与 20 §6 对齐 |
| D2 Gate 四层 | `gate/policy.evaluate` | `test_gate_policy.py` | `ALREADY IMPLEMENTED` | structural/provenance/semantic/admission |
| D3 AdmissionCandidate | `create_admission_candidate` LE 幂等 | `test_gate_service.py` | `ALREADY IMPLEMENTED` | |
| D4 AdmissionService | `approve`/`reject` 唯一迁移 | `test_admission.py` | `ALREADY IMPLEMENTED` | P0-G-001/002/003 |
| D5 persistence | Question/Instance/role_contents/Material/UnitGroup | `test_repositories*.py` | `ALREADY IMPLEMENTED` | |
| D6 explanation 可缺 | content_roles_for optional；Gate 不因缺 explanation fail | Frozen 20 §6.3 | `ALREADY IMPLEMENTED` | **不是** v0.3 相对代码的缺口 |
| D7 grammar None / auto_approve | `STRICT_AUTO_TYPES` 仅 3 型；其余 None→pending | `test_gate_grammar.py`；Frozen 20 §8.4 | `ALREADY IMPLEMENTED`（相对 Frozen）/ `BLOCKED BY OWNER DECISION`（相对 OD-V3-15） | Frozen **禁止**为 9 型编造 grammar；若 Owner 要扩大 auto = Frozen 变更 |
| D8 flags/basis 进 Gate | policy **不读** flags/basis | — | `NEW IMPLEMENTATION REQUIRED` + `BLOCKED BY OWNER DECISION` | OD-V3-18：进 Gate 还是 review 未定 |
| D9 hard/optional 字段 | stem+answer 硬必；explanation optional；choice 需 options | `content_roles_for` | `ALREADY IMPLEMENTED` | |
| D10 pending_review 形成 | grammar None / 非 byte-proven / answer 不完整 | policy | `ALREADY IMPLEMENTED` | |
| D11 Admission ⊥ Enrichment | approve 只物化核心；无 enrichment 钩子 | admission.py | `ALREADY IMPLEMENTED`（解耦）/ Enrichment 侧见 E | 解耦本身符合 v0.3 §8.3 |

### E. Post-Admission Enrichment

| Req | Code | Test | Class | Why |
|---|---|---|---|---|
| E1 detect missing explanation | 无检测器；Question 无 explanation 列（在 role_contents） | — | `NEW IMPLEMENTATION REQUIRED` | 需查询 role_contents 或新槽 |
| E2 async job | Task 表可承载 `task_type`；**无 enrichment 类型** | `test_task_service.py` | `ADAPTATION REQUIRED` | Task/Worker 基建可复用；需新 task_type + 编排 |
| E3 LLM generation | `LLMGateway`/`LLMExecutor` 已有 | `test_gateway.py` | `ALREADY AVAILABLE`（基建） | 可复用 |
| E4 generated authority 分槽 | 无 `explanation_generated` 槽 | Frozen 10 §1.1：role_contents.text **永不来自 LLM** | `BLOCKED BY FROZEN SPEC` + `BLOCKED BY SCHEMA` | 禁止写入 live content；需新表/新槽（OD-V3-25） |
| E5 validation | `ValidationEvent` 绑定 candidate_id/claim_id | `test_evidence*.py` | `ADAPTATION REQUIRED` | 可扩展复用，但 post-admission claim 身份未定义；禁止平行 authority |
| E6 persistence of enrichment | 无 enrichment_jobs 表 | — | `BLOCKED BY SCHEMA` | OD-V3-25 |
| E7 retry/regeneration | TaskService.retry 人工显式；无自动 backoff | 30 §3 failed 无自动出口 | `ADAPTATION REQUIRED` | 边界已定，算法 `OPEN` |
| E8 failure 不回滚 Question | 当前无 enrichment 故无回滚路径 | PAE §6 | `NOT YET IMPLEMENTABLE` | 待 E2–E6 落地后验证 |
| E9 provenance of generation | `llm_call_audit` 可记调用 | `test_executor.py` | `PARTIALLY IMPLEMENTED` | 调用审计在；generation_job 关联未建 |
| E10 identity ⊥ enrichment | dedup_key 不含 explanation | `compiler._question_dedup_key` | `ALREADY IMPLEMENTED` | Frozen 20 §7.3 已排除 explanation |
| E11 budget/live_guard 复用 | `BudgetService`/`live_guard` 已有 | `test_budget.py` | `ALREADY AVAILABLE` | |
| E12 difficulty/knowledge/skills 生成 | knowledge 表可挂；difficulty/skills 无家 | — | `BLOCKED BY SCHEMA` | 见 C |

---

## 3. Information Preservation Analysis

> **问题：当前 V3 IR 是否真的能够承载 Producer Artifact 的业务信息？**

**结论（`DERIVED`）**：**不能完整承载。** 结构性正文（stem/options/answer/explanation/material 行锚）可经 ResolvedSpan → IR → Compiler → payload → role_contents 保真传递；但 **Producer 的证据/质量/溯源语义层在 Consumer Boundary 发生系统性丢失**，且部分为 silent。

### 3.1 逐字段命运（Producer → V3 全链）

| Producer field | 进入 V3？ | 形式 | 原值保留？ | canonicalize？ | evidence？ | provenance？ | flag/UNK？ | 丢弃层？ | 符合 P1？ | semantic mutation 风险 |
|---|---|---|---|---|---|---|---|---|---|---|
| `source_content_sha256` | 是（判定） | M1/M2/Scope | 是 | 否 | M2 计算值 | — | 失败=BLOCK | 否 | 是 | 无 |
| `identity_version` | 是（判定） | Scope | 归一 `"2"` | 仅 `{2,"2"}` | — | — | 出界=rej | 否 | 是 | 禁默认成 2 |
| `unit_id` | 是 | IR/occurrence | 是 | 否 | — | occurrence | — | 否 | 是 | 禁重编号 |
| `question_numbers` | 部分 | question_label / range 字符串 | **否**（原列表丢） | 首号/range | — | 弱 | — | adapter | **否** | 中（范围字符串非可逆） |
| `printed_number` | **否** | — | — | — | — | — | — | adapter/span | **否** | 若用 question_numbers 冒充则高 |
| `stem_lines` | 是 | ResolvedSpan | 行文本 | 否 | text_hash | line_refs | — | 否 | 是 | 低（slice 只读） |
| `options_lines` | 是（整块） | 单 option span | 整块 | 否 | text_hash | line_refs | label gap | 否 | 部分 | 禁 fabricate A/B/C |
| `answer_lines` | 是 | answer span | 是 | 否 | text_hash | line_refs | — | 否 | 是 | 禁猜答案 |
| `explanation_lines` | 是（可选） | explanation span | 是 | 否 | text_hash | line_refs | 可缺 | 否 | 是 | 生成物另槽 |
| `material_lines` | 是 | material span | 是 | 否 | text_hash | line_refs | 折叠 flag 未带 | 否 | 部分 | 禁 silent 合并 |
| `questions_lines` | 是（composite） | sub stem | 是 | 否 | text_hash | line_refs | 拆分 gap | 否 | 部分 | — |
| `material_ref` | 是 | relations/shared | 是 | 否 | — | 关系 | dangling→fail | 否 | 是 | 禁改指向 |
| `extra_lines` | **否** | — | — | — | — | — | — | adapter | **否**（弱语义，须登记） | 低 |
| `unit_type` | 是 | canonical + producer 双值 | producer 保留 | OD-2 两条 | mapping event | — | 非法→fail | 否 | 是 | 禁 QT→UT / andalone |
| `original_question_type` | 是（verbatim） | IR 字段 | 是 | 闭集 exact | — | — | unknown→incomplete | 否 | 是 | 禁默认题型 |
| `answer_evidence` | **基本否** | b2 仅用 lines | type/value 丢 | — | 未转 Evidence | — | — | adapter | **否** | 若假装无证据则高 |
| `basis` | **否** | — | — | — | — | — | — | adapter | **否** | unverified→printed_as_is 禁 |
| `basis_evidence` | **否** | — | — | — | — | — | — | adapter | **否** | 不得补造 |
| `printed_provenance` | **否** | — | — | — | — | — | — | adapter | **否** | unknown→source_line 禁 |
| `provenance.source_lines` | 部分 | span line_refs | 行号 | 否 | — | 是 | — | 否 | 是 | 禁改行号 |
| `flags` | **否** | — | — | — | — | — | — | **reader 未读** | **否** | 丢 flag=violation |
| `qc_verdict` | **否** | — | — | — | — | — | — | **reader 未读** | **否** | FAIL→PASS 禁 |
| `disposition` | **否** | — | — | — | — | — | — | 未进消费面 | **否** | ADMITTED≠V3 APPROVED |
| `answers.unresolved` | **否** | — | — | — | — | — | — | 未读 | **否** | 不得填假答案 |
| `confidence_state` | **否** | — | — | — | — | — | — | 未读 | **否** | 不得抬升置信 |
| `section` / `section_ref` | **否**（payload `sections:[]`） | — | — | — | — | — | — | adapter | **否** | 禁重绑 |
| `validation_issues`/`warnings` | **否** | — | — | — | — | — | — | adapter | **否** | — |

### 3.2 重点字段深挖（任务 §6 特别关注）

#### `basis` / `basis_evidence`
- **`OBSERVED`**：`manifest_reader.py` 解析进 `ManifestUnit.basis` / `basis_evidence`。
- **`OBSERVED`**：`annotation_adapter` / `resolved_span_adapter` / `runner_b2` **均不消费**。
- **`OBSERVED`**：`IRBuilder`/`Compiler`/`payload`/`AdmissionService` 无对应字段。
- **分类**：`NEW IMPLEMENTATION REQUIRED`（P3 保真通道）+ 消费策略 `BLOCKED BY OWNER DECISION`（OD-V3-18）。
- **P1 判定**：当前 = silent loss（reader 有、下游无、无 unsup 登记于 V3 侧）。

#### `answer_evidence`
- **`OBSERVED`**：reader 读 `{type,lines,value}`；`runner_b2:273-274` 仅 `answer_lines or answer_evidence_lines` fallback。
- **`OBSERVED`**：type/value 丢；不进 EvidenceReference/ValidationEvent。
- **分类**：`NEW IMPLEMENTATION REQUIRED`；显式 `unsup` 登记亦缺。

#### `flags`
- **`OBSERVED`**：全 consumer 目录 grep 无 `flags`/`qc_verdict` 业务读取（OCR span `flags` 位图是另一物，落在 `DocumentSourceSpan`，语义管线不消费）。
- **分类**：`NEW IMPLEMENTATION REQUIRED`。IPM 明确「丢 flag = violation」。

#### `printed_provenance` / `provenance.source_lines`
- `source_lines` → span `line_refs`：**representation change，允许**（P1 `prov`）。
- `printed_provenance`：**丢弃**，596 unknown 无法在 V3 保持 UNKNOWN 可见性 → `NEW IMPLEMENTATION REQUIRED`。

#### `material_ref` / `questions_lines` / `options_lines`
- `material_ref`：进入 `relations`/shared，dangling 有校验 → `ALREADY IMPLEMENTED`。
- `questions_lines`：composite 保留 span，但 1:1 折叠为单 sub → `PARTIALLY IMPLEMENTED` + Producer Gap。
- `options_lines`：整块 span 保留；per-label `OPTION_LABEL_SPAN_UNAVAILABLE` **已显式登记** → 符合 P1 `unsup`，分类 `PARTIALLY IMPLEMENTED`（Producer Gap OD-V3-06）。

### 3.3 Silent drop / 静默默认清单（违反 P1 的实锤，`OBSERVED`）

| 位置 | 行为 | 性质 |
|---|---|---|
| `manifest_reader` | `flags`/`qc` 不读 | silent drop |
| `annotation_adapter:201` | `"sections": []`（Manifest.sections 已读却被丢） | silent drop |
| `annotation_adapter:195-200` | document_metadata_claims 全 None | silent drop |
| `manifest_reader:84` | `original_question_type=""` | silent default |
| `manifest_reader:116-118` | `model`/`prompt_version=""` | silent default |
| `resolved_span_adapter:69-70` | 未声明行区间 → 静默不产 span | silent skip |
| `runner_b2:273-274` | `answer_lines or answer_evidence_lines` | 文档化 fallback（非 silent，但须 Contract 确认） |

**允许的 representation change（非 loss）**：`[a,b]` line range → ResolvedSpan；options 整块；question_numbers → range 字符串（若保留原列表则完全合法）。

---

## 4. Semantic Authority Analysis

### 4.1 链上实态（SRC → PRD → CAN → V3D → EVD → UNK）

```text
SRC  sealed source bytes / lines / text_hash
  ↓  （只读）
PRD  Producer/LLM claim：unit_type, original_question_type, 行区间, basis*, flags*, QC*
  ↓  boundary.normalize_unit_type（仅 UT OD-2）     ← 唯一合法 CAN 产生点（harness）
CAN  standalone_unit / composite_unit
  ↓  IRBuilder 闭集校验（拒 legacy）
V3D  canonical_question_type, dedup_key, occurrence_key, verified_correct(物化), subject/grade 收敛
  ↓  GatePolicy + ValidationEvent
EVD  gate_decision, evidence[], review_trail, answer_status
UNK  semantic_status=unknown / incomplete / pending_review
```

### 4.2 逐项 Authority 矩阵 vs 代码

| 事实 | 期望 Authority | 代码实态 | 判定 |
|---|---|---|---|
| 源字节/行文本 | SRC | seal 后只读；Compiler raw slice | **保持** |
| `source_content_sha256` | SRC 计算 + PRD 声明 + EVD 验证 | M2 计算 vs M1 声明 | **保持** |
| stem/options/answer 正文 | SRC + PRD 行锚 | span 切片，不改写 | **保持** |
| `unit_type` legacy | PRD → CAN（授权映射） | boundary 映射 + 双值保留 | **保持**（权威双轨待决） |
| `original_question_type` | PRD verbatim + 可选 CAN | IR verbatim；`map_canonical_type` exact | **保持** |
| difficulty/knowledge/skills | V3D | knowledge 表有、无写；difficulty/skills 无 | **未建** |
| Producer explanation | PRD/SRC | role_contents（源切片） | **保持** |
| generated explanation | V3D 分槽 | **无槽**；且 Frozen 禁 LLM 入 role_contents | **阻塞** |
| `basis`/`flags`/QC | PRD + UNK | 消费面丢失 | **破坏 P3** |
| answer 最终正确性 | PRD 声明 + EVD 验证 | Compiler `verified_correct=None`；**approve 物化强制 `True`** | **见 4.3** |
| Gate decision | EVD | gate_decision 不可变；机器/人工分链 | **保持** |

### 4.3 Authority 异常发现

#### F-AUTH-01 `verified_correct` 物化置 True（`OBSERVED` + `DERIVED`）
- **FILE**：`app/domains/gate/admission.py` `_materialize`
- **SYMBOL**：`create_role_content(..., answer_status={..., "verified_correct": True})`
- **CURRENT BEHAVIOR**：Compiler 冻结 payload 中 `verified_correct=None`；Admission 物化时强制写 `True`，注释称「approved 语义置 true」。
- **TEST**：`test_admission.py`；Frozen 10 §8 不变量「approved answer 必须三字段全 true」。
- **CONTRACT**：SAM 铁律① V3D 不得伪装 PRD/SRC；⑤ UNK 不得静默升级。
- **CLASSIFICATION**：`ALREADY IMPLEMENTED`（相对 Frozen 20 §8 / 10 §8：approved 路径要求三 true）——**不是** v0.3 新缺口；但与「payload 冻结 None」并存，**展示/审计时必须能区分 source_located/complete（源事实）与 verified_correct（Admission 语义）**。
- **注意**：历史 BUG-V3-044 曾使错误 auto_approve 把污染答案标 True；AnswerTokenContract 已收紧。本分析不重开该缺陷。

#### F-AUTH-02 subject/grade 收敛（`OBSERVED`）
- **FILE**：`content_repository.converge_subject_grade`
- **BEHAVIOR**：NULL→known 补写；known→different fail-loud。
- **CLASSIFICATION**：`ALREADY IMPLEMENTED`。非 silent mutation。

#### F-AUTH-03 identity hash 投影（`OBSERVED`）
- **FILE**：`gate/service.py::_annotation_identity_projection`
- **BEHAVIOR**：Semantic Identity 剔除 `confidence` + `line_refs`；resolver_input_hash 仅剔 `confidence`。
- **CLASSIFICATION**：`ALREADY IMPLEMENTED`（OQ-1 Gate A 设计）。与 OD-V3-26（generated 是否排除）同族，后者 `OPEN`。

#### F-AUTH-04 未发现的禁止项（阴性清单，`OBSERVED` negative）
- 无 V3D 写回 Producer 字段（除 F-AUTH-01 的 Admission 语义位）。
- 无 generated explanation 覆盖 source explanation（因 generated 通道不存在）。
- 无 source answer 被推导 answer 覆盖（Compiler 不猜答案）。
- 无 flags 消费后消失（因 flags 根本未进入）。

---

## 5. Consumer Boundary Gap

| 缺口 | 证据 | 分类 |
|---|---|---|
| 统一入口未成立：`runner.py` 可绕 M1–M5 进 GateService | `runner.py:149-154, 256-264` | `BLOCKED BY OWNER DECISION`（OD-V3-16/19）+ `NEW IMPLEMENTATION REQUIRED`（接线） |
| 生产 `TaskExecutor` 无 Scope/M1–M5 | `task/executor.py` 无 import | `NEW IMPLEMENTATION REQUIRED` |
| `runner_b2` 绕过 `GateService`/`SourceResolver` 编排 | `runner_b2` 直调 IRBuilder/Compiler/policy | `ADAPTATION REQUIRED`（实验链 ≠ 生产架构） |
| Producer 证据层不进 V3 | §3 | `NEW IMPLEMENTATION REQUIRED` |
| hash 族不一致：adapter `hashlib.sha256` vs b2 `sha256_hex` | `resolved_span_adapter` vs `runner_b2` | `ADAPTATION REQUIRED`（对齐 text_hash 语义，Frozen 20 要求 raw SHA256） |
| body_hash 丢 CRLF/BOM | `source_loader` splitlines+join | `ADAPTATION REQUIRED`（与 M2 raw-bytes 语义差） |
| 未声明 span 静默 skip | `resolved_span_adapter:69-70` | `NEW IMPLEMENTATION REQUIRED`（改为显式 unsup/incomplete） |

**调用图（`OBSERVED`）**：

```text
runner.py:        Scope ──────────────────────────────► GateService ► Admission
                  （无 M1–M5）

runner_b2.py:     Scope ∧ M1→M2→M3→M4→M5 ─► IRBuilder ► Compiler ► policy.evaluate
                  （不进 GateService / SourceResolver / 不 commit）

TaskExecutor:     Seal ► Quality ► Annotation(LLM) ► GateService ► Admission
                  （无 Scope / 无 M1–M5；输入=file_path 本地文档，非 Producer manifest）
```

> **判定**：v0.3 §2.2「统一 identity boundary」**当前不成立**。

---

## 6. Identity / M1–M5 Gap

| ID | 实现位置 | 生产接线 | 测试 | 分类 |
|---|---|---|---|---|
| M1 | `core/manifest_identity.py` | **无** | `test_x26_m1_*` | `PARTIALLY IMPLEMENTED` |
| M2 | `core/raw_bytes_identity.py` | **无** | `test_raw_bytes_identity.py` | `PARTIALLY IMPLEMENTED` |
| M3 | `core/ir_identity.py` | **无** | 同上族 | `PARTIALLY IMPLEMENTED` |
| M4 | `core/identity_verifier.py` | **无** | `test_identity_verifier.py` | `PARTIALLY IMPLEMENTED` |
| M5 | `core/identity_gate.py` | **无** | `test_identity_gate.py` | `PARTIALLY IMPLEMENTED` |
| Scope | `boundary.enforce_interface_scope` | harness 有 / production 无 | `test_x26_frb01_*` | `PARTIALLY IMPLEMENTED` |

**复用结论**：M1–M5 **可以直接复用**（纯函数/清晰签名/测试完备），接入方式是 **在所有 Producer→V3 entrypoint 最前调用 `_verify_identity_boundary` 同构逻辑**（或将其从 scripts 提升为 production 模块）。

**注意命名冲突（`OBSERVED`）**：V3_SPEC 的 “M1” = Core Ingestion closed loop；Consumer Identity 的 M1–M5 来自 `PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN`。本报告 M1–M5 **一律指后者**。

**附加缺口**：M3 batch 定位的 path fallback / 无参 positional 首条命中是 **locator fallback**（path 不作 identity 仍成立），但无参首条属弱定位 → `ADAPTATION REQUIRED`（收紧为显式失败或强制唯一命中）。

---

## 7. Canonicalization Gap

### 7.1 UT（`OBSERVED`）

| 输入 | `boundary.normalize_unit_type` | `IRBuilder` |
|---|---|---|
| `standalone_question` | → `standalone_unit` + event | 拒（须先 boundary） |
| `composite_question` | → `composite_unit` + event | 拒 |
| `standalone_unit`/`composite_unit` | 幂等 | 接受 |
| `andalone_question` | `UNKNOWN_UNIT_TYPE` fail closed | 拒 |
| 其它/missing | fail closed | 拒 |

- **runtime authority 现状**：harness = `boundary.normalize_unit_type`；production IR = 闭集 fail-closed（不映射）；`mapping_registry` = **零 import 治理表**。
- **双权威**：是（OD-V3-14）。
- **fallback**：无（合规）。
- **original 保留**：`NormalizedUnitType.producer_unit_type` 保留。
- **mapping event 可追溯**：`normalization_event_id` 有；F-05-A 跨库交叉验证未实现（OD-V3-30）。
- **分类**：规则 `ALREADY IMPLEMENTED`；唯一权威裁决 `BLOCKED BY OWNER DECISION`；生产接线 `NEW IMPLEMENTATION REQUIRED`（若裁决 boundary 为权威则 `ADAPTATION`）。

### 7.2 v0.2 vs v0.3 词面张力（`OBSERVED`，内部矛盾）
v0.2 冻结候选写 canonical UT = `{standalone_question, composite_question}`；v0.3/OD-2/Frozen 20 §4.5 写 canonical = `{standalone_unit, composite_unit}`。v0.3 称「继承不改写 v0.2 冻结项」但 OD-2 实际更换词面。→ 记入 §15 内部矛盾，需 Owner 映射表消歧，**不得由本分析关闭**。

---

## 8. Resolver Gap

| 路径 | 需要 Resolver？ | 证据 | 裁决 |
|---|---|---|---|
| Producer path（精确 line anchors） | **跳过 marker search**；仍需 ResolvedSpan 形状 | v0.3 §10.1；`resolved_span_adapter` | **ADAPT**（producer path） |
| Raw V3 LLM path | **必须保留** Source→Annotation→Resolver | `GateService.run` → `SourceResolver` | **KEEP** |
| 整体删除 | **禁止** | v0.3 §10.3；Frozen fail-closed 语义 | **不得 REMOVE** |

**分类**：
- Resolver 核心：`ALREADY IMPLEMENTED` + **KEEP**
- Producer line anchors → ResolvedSpan：`ALREADY IMPLEMENTED`（adapter）+ **ADAPT**（跳过搜索）
- **REMOVE FROM PRODUCER PATH**：仅指 marker search / semantic rediscovery，不是组件删除
- **REMOVE ENTIRELY**：**否**

**空白能力仍须 Resolver 保留**：blank 恒 unresolved（`resolver.py:_blank_span`）；image figure_id 结构化；explanation 无表头→missing 不截断。

---

## 9. QT Gap

| 阶段 | `original_question_type` 行为 | 证据 |
|---|---|---|
| Producer | 声明值（含 `listening` 等） | 语料 |
| Adapter | **verbatim 进 payload** | `annotation_adapter` |
| IR | verbatim；`map_canonical_type` exact | `ir.py` / `compile/__init__.py` |
| 非闭集值（如 `listening`） | map→`None`→IR `unknown canonical type`→**incomplete** | `validate_ir` |
| missing | `""` 默认（adapter）或 None→incomplete | `manifest_reader:84` |
| Compiler | 无 canonical → 不产 leaf（ready 不应发生） | `compiler._compile_leaf` |
| Gate | `canonical ∉ CANONICAL_TYPES` → structural fail→rejected | `policy` |
| Admission | `map_canonical_type` None → RepositoryError 不物化 | `admission._materialize` |

**closed-set enforcement**：
- 生产 IR/Gate **有**（exact passthrough + incomplete/rejected）。
- Consumer boundary **无**独立 QT 校验（verbatim 透传到 IR 才失败）→ `ADAPTATION REQUIRED`（边界显式 `explicitly_unsupported`）。
- **禁止 alias**（Frozen）→ 保持。

**`listening`**：`BLOCKED BY OWNER DECISION`（OD-V3-13：扩集 / unsup / 映射）。当前行为 = IR incomplete，**不是**静默映射。

**Gate grammar 使用 QT**：仅 `STRICT_AUTO_TYPES` 三型进 AnswerTokenContract；其余 `grammar=None`→pending_review。**Frozen 禁止为 9 型编造 grammar** → OD-V3-15 若选择「扩大 auto」= `BLOCKED BY FROZEN SPEC`。

---

## 10. Gate / Admission Gap

| 问题 | 答案（`OBSERVED`） | 分类 |
|---|---|---|
| hard requirement 字段 | stem 非空；answer IR required；choice 需 options；canonical type 闭集；span 可追溯 | `ALREADY IMPLEMENTED` |
| 允许 missing | explanation；answer 可 None（则不能 auto）；figure_refs/knowledge_links 恒空 | `ALREADY IMPLEMENTED` |
| explanation 是否 hard | **否**（Frozen 20 §6.3 + `content_roles_for`） | `ALREADY IMPLEMENTED` |
| grammar 为何 None | 非 STRICT_AUTO_TYPES **或** AnswerTokenContract 失败 | 设计如此（Frozen） |
| auto_approve 为何不可达 | 非 3 型恒 None；3 型还需全部 span exact/normalized + answer 完整 + grammar True | 设计如此；OD-V3-15 是产品策略问题 |
| flags 影响 Gate？ | **否** | `NEW IMPLEMENTATION REQUIRED` + OD-V3-18 |
| basis / answer evidence 影响 Gate？ | **否** | 同上 |
| pending_review 如何形成 | 非 byte-proven / grammar None / answer 不完整 / role overlap | `ALREADY IMPLEMENTED` |
| Admission 与 enrichment 解耦 | approve 只物化核心；无 enrichment 钩子 | `ALREADY IMPLEMENTED` |

**额外**：`figure_refs=[]`、`knowledge_links=[]` 恒空（BUG-V3-020）→ `NEW IMPLEMENTATION REQUIRED`（图通路）/ knowledge 写路径。

---

## 11. Post-Admission Enrichment Feasibility

### 11.1 可复用基础设施（`OBSERVED`）

| 组件 | 位置 | 复用度 |
|---|---|---|
| Task / TaskClaim / TaskService | `models/runtime.py`、`task/service.py` | **高**——可加 `task_type="post_admission_enrichment"` |
| TaskExecutor Worker 循环 | `task/executor.py` | **高**——需新 stage 编排 |
| LLMGateway / LLMExecutor | `ai/gateway.py`、`ai/executor.py` | **高** |
| BudgetService 五账户 | `ai/budget.py` | **高** |
| live_guard | `ai/live_guard.py` | **高** |
| llm_call_audit | `models/runtime.py` | **高** |
| ValidationEvent + EvidenceAuthority | `evidence/*` | **中**——claim 身份需扩展；禁平行 authority |
| KnowledgeNode / QuestionKnowledgeLink | `models/content.py` | **中**——Frozen 允许 optional derived |
| LE 幂等 / attempt_id | compile/ann/seal | **高** |

### 11.2 需要新建的能力

| 能力 | 分类 | 阻塞 |
|---|---|---|
| enrichment job 持久化（`enrichment_jobs[]`） | `BLOCKED BY SCHEMA` | OD-V3-25 |
| `explanation_generated` 双槽 | `BLOCKED BY SCHEMA` + `BLOCKED BY FROZEN SPEC` | Frozen 10 §1.1：`InstanceRoleContent.text` 永不来自 LLM |
| difficulty 存储 | `BLOCKED BY SCHEMA` | 无列 |
| skills 存储 | `BLOCKED BY SCHEMA` | 无表 |
| validation_state for generated | `NEW IMPLEMENTATION REQUIRED` | 可挂 ValidationEvent 扩展（SAM §5 = OWNER） |
| 缺 explanation 检测器 + enqueue | `NEW IMPLEMENTATION REQUIRED` | |
| 生成 worker 编排 | `ADAPTATION REQUIRED` | 复用 TaskExecutor |
| retry/backoff 策略 | `BLOCKED BY OWNER DECISION` | OD-V3-24；Frozen 30：failed 无自动出口 |

### 11.3 Frozen Spec 硬约束（实现 Enrichment 前必须对齐）

1. **10 §1.1**：LLM 输出永远是 C 域 annotation，**不是 live 文本**；`instance_role_contents.text` 永不来自 LLM。
2. **00 §5**：复杂统计富化 = M1 非目标。
3. **00 P3**：无 provenance 只能作 **AI Generated/Inferred/Unverified**，不得伪装 Source-derived 进 approved。
4. **10 §2**：post-admission 派生 = 显式 Repository 步骤，不得回改已提交内容行。
5. **30 §3**：failed/interrupted 无自动出口。

**推论（`DERIVED`）**：
- Generated explanation **可以**做，但必须落在 **独立的 V3D/AI-Generated 槽**（新表），**绝不能**写入 `instance_role_contents`。
- 这与 PAE §8 逻辑槽设计一致，但 **物理 schema 不存在** → `BLOCKED BY SCHEMA`（OD-V3-25）。
- 若被解释为「复杂统计富化」非目标，则还可能 `BLOCKED BY FROZEN SPEC`——**OWNER 需确认 explanation 生成属于允许的 AI Generated 派生，而非 M1 非目标**。

---

## 12. Producer-side Gaps

**不得把下列误判为 V3 implementation bug**（任务 §15.C）：

| Gap | 证据 | 影响 | 处置 |
|---|---|---|---|
| option-label 粒度缺失 | 仅 `options_lines` 整块 | choice grammar 难 auto | OD-V3-06 `OWNER DECISION REQUIRED` |
| subquestion 不分解 | multi-q 折叠单 sub | 子题粒度丢失 | OD-V3-07 |
| v1 79 份缺 identity | 无 `source_content_sha256`/`identity_version` | 被 Scope 拒 | OD-V3-01 |
| 16×QC_FAIL | disposition 非 ADMITTED | 不应进 ADMITTED 消费面 | OD-V3-05 |
| answer table 502 unresolved | flags 有、解析无 | answer 不完整 | OD-V3-08 |
| 596 printed provenance unknown | `printed_provenance=unknown` | 须保持 UNK | OD-V3-09 |
| 41 composites 同区间折叠 | material==questions | 结构弱 | OD-V3-10 |
| `andalone_question`×1 | legacy 噪声 | fail closed | OD-V3-11（运行时已拒） |
| REJECTED_V1×1 | 历史 | 接口外 | OD-V3-02 |

---

## 13. Schema Gaps

| 缺口 | 现状 | 需要 | 分类 |
|---|---|---|---|
| generated explanation 槽 | 无；role_contents 禁 LLM | 新表或 JSONB derived 槽（须 Frozen 兼容） | `BLOCKED BY SCHEMA` + `BLOCKED BY FROZEN SPEC` |
| difficulty | 无 | 新列/表 | `BLOCKED BY SCHEMA` |
| skills | 无 | 新表 | `BLOCKED BY SCHEMA` |
| enrichment_jobs | 无 | 新表（append-only） | `BLOCKED BY SCHEMA`（OD-V3-25） |
| ValidationEvent 扩展（generation provenance） | 绑定 candidate | 扩展或旁表 | `BLOCKED BY OWNER DECISION`（SAM §5） |
| flags/basis 等 Producer 证据持久化 | candidate payload 未含 | payload 扩展或 evidence 对象 | `ADAPTATION REQUIRED` + OD-V3-18 |
| figure 编译表示 | payload `figure_refs=[]` | 按 Frozen 10 figure 七字段 | `NEW IMPLEMENTATION REQUIRED`（BUG-V3-020） |

**注意**：10 §11 要求变更走 Alembic；本分析 **不创建 migration**。

---

## 14. Owner Decision Dependencies

### 14.1 原 14 项 `OWNER DECISION REQUIRED` 对实现的阻塞面

| ID | 阻塞的实现工作 |
|---|---|
| OD-V3-01 | v1 接口策略 → Scope 回填工具 / 排除清单 |
| OD-V3-05 | QC_FAIL 消费面 |
| OD-V3-06 | options label evidence 设计 |
| OD-V3-07 | subquestion IR 形状 |
| OD-V3-13 | QT 闭集 enforcement 对 `listening` |
| OD-V3-14 | **唯一** mapping runtime authority |
| OD-V3-15 | auto_approve 产品策略（注意 Frozen 限制） |
| OD-V3-16 | runner.py 处置 |
| OD-V3-17 | batch IR 分发 |
| OD-V3-18 | flags/basis/answer_evidence 进 Gate 还是 review |
| OD-V3-19 | preprocessing_consumer 是否 production path |
| OD-V3-25 | **Enrichment schema**（最大阻塞） |
| OD-V3-27 | v0.3 Freeze |
| OD-V3-28 | X3/Migration 关系 |

### 14.2 本分析新识别的 `OWNER DECISION REQUIRED`（新增）

| 新 ID | 项 | 理由 |
|---|---|---|
| **OD-V3-NEW-01** | Generated explanation 是否被 Frozen 00 §5「复杂统计富化非目标」排除 | 决定 PAE 是否 `BLOCKED BY FROZEN SPEC` |
| **OD-V3-NEW-02** | `verified_correct` 物化置 True 的审计展示语义（源事实 vs Admission 语义） | 避免与 SAM 铁律被误读冲突；非改行为 |
| **OD-V3-NEW-03** | Consumer text_hash 族统一（raw `hashlib.sha256` vs `sha256_hex`） | Frozen 20 要求 raw；实现不一致 |
| **OD-V3-NEW-04** | `runner_b2` `answer_lines or answer_evidence_lines` fallback 是否合法 | 可能构成 semantic mutation 边界 |
| **OD-V3-NEW-05** | v0.2 UT 闭集词面 vs OD-2 canonical 词面的映射消歧 | 合同内部矛盾 |
| **OD-V3-NEW-06** | ValidationEvent 扩展 generation provenance（= SAM §5 已写但未编号） | schema/governance |

> 以上 **不自行决定**，仅登记。

---

## 15. Implementation Plan Classification

### 15.1 总分类（KEEP / ADAPT / NEW / BLOCKED / OWNER DECISION）

| 工作项 | 分类 |
|---|---|
| SourceResolver（Raw V3 path） | **KEEP** |
| IRBuilder / Compiler / GatePolicy / AdmissionService 主链 | **KEEP** |
| M1–M5 模块本体 | **KEEP** |
| `boundary.normalize_unit_type` 规则 | **KEEP**（权威归属待 OWNER） |
| `STRICT_AUTO_TYPES` 三型 grammar | **KEEP** |
| Budget / live_guard / LLMGateway / TaskService | **KEEP** |
| KnowledgeNode 表 | **KEEP** |
| Consumer adapters 证据保真 | **ADAPT** |
| runner.py 入口对齐 | **ADAPT** 或阻断（OWNER） |
| runner_b2 对齐 GateService 编排 | **ADAPT**（若升格 production） |
| text_hash 族统一 | **ADAPT** |
| M1–M5 接入生产 entrypoint | **NEW** |
| flags/basis/answer_evidence/printed_provenance 通道 | **NEW** |
| QT boundary closed-set enforcement | **NEW** |
| figure_refs 编译表示 | **NEW** |
| knowledge 写路径 | **NEW** |
| enrichment task_type + worker 编排 | **NEW** |
| enrichment_jobs / generated slots / difficulty / skills schema | **BLOCKED**（SCHEMA + OD-V3-25） |
| Generated explanation 入 live content | **BLOCKED**（FROZEN SPEC） |
| 扩大 STRICT_AUTO / grammar for 9 型 | **BLOCKED**（FROZEN SPEC）若 Owner 要 auto |
| 全部 OD-V3-* 与 NEW-01..06 | **OWNER DECISION** |

### 15.2 v0.3 合同内部互相矛盾（任务 §21 要求报告）

| # | 矛盾 | 级别 |
|---|---|---|
| 1 | v0.2 UT 闭集词面 vs v0.3/OD-2 canonical 词面 | **实质** |
| 2 | PAE「禁止 no explanation→拒入库」措辞 vs OD-V3-21 仍 OPEN | **规范张力** |
| 3 | SAM「闭集内映射」vs Contract「须 per-value Owner rule」（当前零 rule） | **实质** |
| 4 | §5.3 `true_false`/`listening` 并列表述易误读 | 表述 |
| 5 | §2.2 统一 M1–M5 要求 vs runner.py 现状可执行路径 | **实质**（已标 OD-V3-16） |
| 6 | §4.2「唯一 mapping authority」vs 双位置并存 | **实质**（OD-V3-14） |
| 7 | PAE §3.2 状态机 vs §5/SAM validation_state 4 值 | **实质**（词汇未对齐） |
| 8 | IPM flags「必须保留」vs「未进 Gate」 | 张力（OD-V3-18） |
| 9 | 与 Frozen 20 `semantic_status∈{ready,incomplete}` vs 代码 `{...,unknown}`（X2.6 M.2） | **跨文档**：代码有 Owner 扩展，合同未声明与 Frozen 关系 |
| 10 | PAE generated explanation vs Frozen 10 §1.1「LLM 不写 live 文本」 | **跨文档实质**（→ OD-V3-NEW-01） |

### 15.3 若 Owner 明天完成 14 项 Owner Decision，V3 最小实现路径

> **前提**：14 项裁决完毕；NEW-01..06 亦应尽量同批裁决。以下 **不开始实现**，只给最小路径。

```text
Phase 0  治理落盘（无 production 代码）
         - 记录 OD 裁决事件 ID
         - 明确 mapping runtime authority（OD-V3-14）
         - 明确 consumer path 地位（OD-V3-19）
         - 冻结 enrichment schema 草案（OD-V3-25）→ Alembic 立项（另授权）

Phase 1  统一 Identity Boundary（NEW-F1）           ← 最先，解锁一切入口
         - 将 M1–M5+Scope 提升为唯一 Producer→V3 前置
         - 处置 runner.py（删除 / 硬阻断 / 对齐 B2）
         - TaskExecutor 若接 Producer manifest 亦须过闸
         - 测试：全 entrypoint 负例（缺 identity / v1 / andalone）

Phase 2  Information Preservation（P1/P3）
         - adapter 携带 flags/basis/basis_evidence/answer_evidence/
           printed_provenance/qc/disposition 进 evidence/provenance 通道
         - silent default → 显式 unsup/UNK 登记
         - question_numbers 原列表可逆保留
         - 测试：字段命运矩阵对账（可审计）

Phase 3  Canonicalization 单权威
         - 按 OD-V3-14 接线或降级 mapping_registry
         - F-05-A 事件交叉验证（OD-V3-30 可后置）
         - 测试：OD-2 事件 ID 可追溯；andalone fail closed

Phase 4  QT Boundary Enforcement
         - Consumer 侧 closed-set + verbatim
         - listening 按 OD-V3-13
         - 测试：unsupported → explicitly_unsupported（非 silent）

Phase 5  Gate Review Signals（按 OD-V3-18）
         - flags/basis → pending_review 原因或 review 队列
         - 不改 STRICT_AUTO_TYPES（除非 Frozen 变更授权）

Phase 6  Post-Admission Enrichment（依赖 OD-V3-25 + NEW-01）
         - migration：enrichment_jobs + explanation_generated 等槽
         - task_type=post_admission_enrichment
         - 复用 Gateway/Budget/live_guard/llm_call_audit
         - ValidationEvent 扩展（NEW-06）
         - 生成物永不入 instance_role_contents
         - 测试：双槽分离；失败不回滚；identity 不变

Gate Evidence
         - 全量 corpus 复跑（X2.7 形态）作为验收，不在此任务
```

**最小 production diff 范围（估算，`DERIVED`）**：
- `backend/app/core/*` 或新 `backend/app/domains/consumer/*`：M1–M5+Scope 提升
- `backend/scripts/preprocessing_consumer/*`：对齐或阻断
- `backend/app/domains/compile/mapping_registry.py`：接线或降级（OWNER）
- adapters：证据字段透传
- `backend/app/domains/gate/*`：可选 review 信号（OD-V3-18）
- **schema**：Enrichment 表（OD-V3-25 授权后）
- tests：边界/保真/enrichment

**明确不在最小路径**：grammar 扩大、QT 闭集扩集、v1 回填、Producer 重切、X3/Migration、v0.3 Freeze。

---

## 16. 十个核心问题的明确回答

### Q1. Producer Artifact 能否在不发生 silent information loss 的情况下进入当前 V3 IR？
**不能。** 结构正文可保真；证据/质量/溯源层（flags、QC、basis*、answer_evidence 语义、printed_provenance、section*、printed_number 等）在 Consumer 层丢失，且多处 silent。`OBSERVED` §3.3。

### Q2. 哪些信息目前会丢失？
`flags`、`qc_verdict`、`disposition`、`basis`、`basis_evidence`、`answer_evidence.type/value`、`printed_provenance`、`printed_number`、`section`/`section_ref`、`extra_lines`、`answers.unresolved`、`confidence_state`、`validation_issues`/`warnings`、question_numbers 原列表、options per-label、subquestion 真实分解、document_metadata_claims、Manifest.sections（payload 硬编码 []）。`OBSERVED` §3.1。

### Q3. 哪些只是 representation change，而不是 information loss？
line range → ResolvedSpan；options 整块 span；question_numbers → range 字符串（若保留原列表）；`source_lines` → `line_refs`；unit_type legacy → canonical（双值保留时）；text_hash 作为证据指针。`DERIVED` + P1 允许表。

### Q4. 哪些 Producer facts 当前会被 V3 重新解释？
1. **`verified_correct`**：None → 物化 True（Admission 语义，Frozen 要求；须可审计区分）。
2. **`subject`/`grade`**：多源收敛（fail-loud，非 silent）。
3. **`answer` fallback**：`answer_lines or answer_evidence_lines`（runner_b2）。
4. **`unit_type`**：OD-2 授权映射（合法 CAN，非擅自）。
5. **identity hash 投影**：剔除 confidence/line_refs（有意降权，非改存储）。
`OBSERVED` §4。

### Q5. 哪些 V3 semantic metadata 可以安全地在 Producer facts 之上新增？
**difficulty、knowledge_nodes、skills、generated explanation（V3D 分槽）** —— 条件：新 authority 标识、不覆盖 PRD/SRC、不进 live `instance_role_contents`、与 identity/dedup 正交、走 Repository 步骤。`knowledge_nodes` Frozen 已允许 optional derived。`DERIVED` + PAE §4/§8。

### Q6. M1–M5 是否可以直接复用？需要怎样接入？
**可以直接复用**（签名清晰、测试完备、纯度高）。接入 = 所有 Producer→V3 entrypoint 前置 `Scope ∧ M1→M2→M3→M4→M5`，任一拒绝则下游 **NOT REACHED**。生产 `TaskExecutor`/`GateService` 当前未接；建议将验证逻辑从 scripts 提升为 production 模块。`OBSERVED` §6。

### Q7. Resolver 哪部分仍然必须保留？
**整个 Raw V3 path 的 SourceResolver 必须 KEEP**（marker 级联、fail-closed、structural_regions、blank/image/explanation 边界）。Producer path 仅可 **跳过 marker search**（ADAPT），仍产出 ResolvedSpan。**不得 REMOVE ENTIRELY。** `OBSERVED` §8。

### Q8. Gate / Admission 当前有哪些 Contract-to-Code gaps？
主链（IR/Compiler/Gate/Admission/Persistence/explanation optional）**无重大缺口**（相对 Frozen）。相对 v0.3 的缺口：flags/basis/answer_evidence 不进 Gate/review（OD-V3-18）；figure_refs/knowledge_links 恒空；grammar/auto 策略受 Frozen 限制（OD-V3-15）；producer 证据未进 payload。`OBSERVED` §10。

### Q9. Post-Admission explanation enrichment 当前哪些基础设施可以复用？
**可复用**：Task/TaskService/TaskExecutor、LLMGateway/Executor、Budget 五账户、live_guard、llm_call_audit、ValidationEvent（需扩展）、KnowledgeNode 表、LE 幂等。**不可复用为生成物落点**：`instance_role_contents`（Frozen 禁 LLM text）。`OBSERVED` §11。

### Q10. 完成 Owner Decisions 后，真正需要修改 production code / schema / tests 的最小范围是什么？
见 §15.3：Phase 1–2 为必做 production diff（identity 提升 + 证据透传）；Phase 3–5 视裁决；Phase 6 必须 **schema migration**（OD-V3-25）+ 新 task 编排；tests 覆盖边界负例、字段命运对账、enrichment 双槽。**不需要**改 Frozen Spec 即可做 Phase 1–5 的大部分；Enrichment 生成若被判定为非目标则还需 Frozen/errata。

---

## 17. 完成确认（任务 §21）

| 项 | 确认 |
|---|---|
| production code | **unchanged**（本任务只读） |
| schema | **unchanged** |
| migration | **未创建** |
| Frozen Spec / Contract / Ontology / QT / UT | **unchanged** |
| corpus | **unchanged** |
| Contract v0.3 五件套 | **unchanged** |
| 新增文档 | 仅本文件 |
| 新 Owner Decision Required | **有**：OD-V3-NEW-01..06（§14.2） |
| v0.3 内部矛盾 | **有**：10 条（§15.2） |
| 是否开始实现 | **否** |

---

*End of V3-CONTRACT-v0.3-IMPLEMENTATION-FEASIBILITY-ANALYSIS.*
