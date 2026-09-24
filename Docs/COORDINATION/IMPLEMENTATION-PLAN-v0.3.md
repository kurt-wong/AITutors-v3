# IMPLEMENTATION-PLAN-v0.3

```text
STATUS: OWNER APPROVED
AUTHORITY: IMPLEMENTATION PLAN (NON-FROZEN)
PURPOSE: IMPLEMENTATION PLANNING ONLY
OWNER-APPROVED: YES (Limited Implementation Authorization — separate doc)
RECONCILED: OD-01 ~ OD-05 + G-01 + G-02
```

> 本文档不是 Frozen Contract，不是 Frozen Spec。
> **Implementation Plan 不构成 Frozen Schema modification authorization（OD-05）。**
> 实施范围以 `LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md` 为准。
> 发现与 Frozen Spec / Frozen Contract 冲突时：STOP → 标记 `FROZEN-SPEC / FROZEN-CONTRACT CONFLICT` → `OWNER DECISION REQUIRED`。禁止自行解决。

**Companion governance docs：**

- `OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md`（D1）
- `LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md`（D3）
- `FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md`（D4 — **Proposal only**）
- `G-02-FREEZE-REGISTRATION-VERIFICATION.md`（D5）

---

## 0. Governance Baseline（实施人员必须使用）

| Item | SHA / Value |
|------|-------------|
| Contract v0.3 **Frozen Semantic Baseline** | `b743c5daf0806ea00c84afb1b92ca2a3b5dbfc98` |
| **Freeze Registration**（governance-state only） | `79348441dae0efce6855017b2b5c0491b08d6bb8` |
| Frozen Spec tree (`Docs/V3_SPEC`) | `b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`（unchanged） |
| Owner Approval (Contract freeze) | APPROVED |
| Frozen at | 2026-09-23T08:55:17+08:00 |
| AITutors-v3 HEAD at planning time | `79348441dae0efce6855017b2b5c0491b08d6bb8` |
| Aitutors-preprocessing HEAD at planning time | `2b92898f05f6541a5fc65c8300cb8a59a06c4928` |

> **Baseline 时点声明（2026-09-24 加注，历史值一律不改）**：本表及本计划内一切
> `b3eeb3e9…` / `b743c5d` / `7934844` 表述（含 Phase 0 Scope 核对项与文末 `Compiled from` 行）
> 均为 **2026-09-23 规划时点的 baseline 快照（historical）**。
> **当前事实**：Frozen Spec tree 已因 **OD-R-01** 经 **L1 `CR-003` / `90 §11 CA-003`** re-freeze
> 而改变（previous `b3eeb3e9…` → incorporation `442172f4…` → re-freeze tree）。
> 权威登记 = `Docs/V3_SPEC/CR-003_CONTRACT_CHANGE_RECORD_OD-R-01.md` §10。
> 本注记只明确 historical / baseline scope，**不**机械替换历史 hash、**不**改写本计划正文。

**G-02 绑定表述（禁止其他说法）：**

```text
b743c5d remains the Frozen Semantic Baseline.
7934844 is the Freeze Registration / governance-state commit.
7934844 does NOT replace b743c5d as semantic baseline.
```

**Authority Order（实施时不得违反）：**

```text
Frozen Spec
    >
Frozen Contract
    >
Owner Decisions          ← OD-01 ~ OD-05 / G-01 / G-02
    >
Implementation Plan（本文档）
    >
Implementation
```

Implementation Plan 不得反向修改上层规范。Implementation 不得覆盖 Owner Decisions。

---

## 0b. Owner Decisions OD-01 ~ OD-05（reconciled into this plan）

| ID | Decision | Effect on this plan |
|----|----------|---------------------|
| **OD-01** | Extend Frozen Resolved Span（P04 polymorphic option provenance） | **APPROVED design / PENDING Frozen Spec incorporation** — 见 D4 Proposal。**re-freeze 前不得实施 P04 Resolved Span ontology 扩展**；`options_lines` 保留、禁止 option=one line/span、fail closed、禁 V3 rediscovery 等约束立即生效。 |
| **OD-02** | Source-derived Metadata = **Source Authority + Conflict-as-signal** | 取代任何「以 annotation 为准」的写法。Verified Source-derived = authoritative；LLM = claim only；conflict 双保留，默认非 Admission blocker；不得擅自升为 Gate condition。 |
| **OD-03** | Evidence = **Complete Traceability**（P08/P24） | **不锁 persistence table**。禁止把「Evidence 一律进 Candidate/QuestionEvidence 表」写成既定事实。完整可追溯 + 优先复用 Frozen Schema；必须改 V3 Frozen Schema → STOP。 |
| **OD-04** | Production Entry = **Artifact-first / Artifact-authoritative** | 正式语义入口 = Artifact → Boundary → Identity → IR → Gate → Admission。禁止第二条独立 semantic authority ingestion path。不等于立即删除 TaskExecutor（可留 infrastructure/execution）。 |
| **OD-05** | **Producer-side Artifact Schema extensible / V3 Frozen Schema STOP** | Preprocessing/Producer schema 可在 Contract 语义内扩展；V3 Frozen Schema 不可自行扩展。Plan 不构成 schema modification authorization。 |
| **G-01** | Plan + Limited Authorization **入 Git** | 本 Plan 与 `LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md` 进入正式 baseline。 |
| **G-02** | `b743c5d → 7934844` **VERIFIED** | 见 §0 绑定表述与 `G-02-FREEZE-REGISTRATION-VERIFICATION.md`。 |

**Terminology（mandatory）：** Canonical Unit Type 仅 `standalone_unit` / `composite_unit`。禁止将 `standalone_question` / `Standalone Question` 当作当前 V3 概念；仅可作历史/Producer/provenance 词汇。禁止建立 `standalone_question → canonical_question_type` 兼容模型。

---

## A. Current State（仓库实际状态）

调查基准：只读代码 / 测试 / 文档。禁止根据记忆推断。

### A.1 kurt-wong/Aitutors-preprocessing

| Item | Current State | Evidence |
|------|---------------|----------|
| HEAD | `2b92898` DEC-049 | `git log -1` |
| Primary entry | `scripts/reslice_pipeline.py` (`main`:824, `process_file`:703) | file:line |
| Resolver entry | `scripts/resolver_reference.py` → `resolver_ir.json` | :279–312 |
| Prompt | `reslice-pilot-v2.7` | `reslice_pipeline.py:161` |
| Artifact schema | LLM prompt JSON + dict validation；**无** pydantic/jsonschema | PROMPT_HEAD :182–306 |
| Manifest file keys | `source_file`, `units[]`, `annotation_meta`, `model`, `sections?`, `identity_version?`, `source_content_sha256` | FACTS-v2 :72–81 |
| Unit keys | `unit_id/unit_type/question_numbers/printed_number/section/section_ref/basis/basis_evidence/printed_provenance/*_lines/answer_evidence/original_question_type` | FACTS-v2 :83 |
| IR | `resolver-ir-0.1`；unit = `content{*_lines text}` + `answers` + `flags[]` + `provenance` | `resolver_reference.py:150–175` |
| Options | **仅** `options_lines: [start,end]\|null`；**无** per-label `{label,text,provenance}` | prompt :255；FACTS.md:145 |
| answer | `answer_lines` + `answer_evidence{type,lines,value,shared}` | prompt :258; AE_TYPES :159 |
| answers.cells | Resolver 单行 `<table>` → `{cells[], method, answers{}, unresolved[]}` | `resolver_reference.py:78–106` |
| explanation | 仅 `explanation_lines` span；无 type/reasoning schema | prompt :259 |
| Source metadata | **无结构化字段**；仅路径/文件名隐含；`doc_meta=""` | `process_file`:708 |
| flags | 仅 2 值：`answer_number_mismatch`, `answer_table_unresolved` | `_answer_flags`:109–116; :147–148 |
| basis | 闭集 6 值：`answer_key\|shift\|keep\|printed_as_is\|explicit\|unverified` | design :62–63 |
| provenance | **仅行级** `[start,end]`；`extraction_method: line_span_v1` | IR unit :191–208 |
| identity | `source_content_sha256` / `identity_version=2` / section_ref | Contract DEC-030 |
| Tests | ~40 files；canonical baseline 338 passed / 1 xfailed | `tests/` |
| M1–M5 | 实现在 **V3**；Preprocessing 仅 Guardian 监控 | Contract DEC-049 |
| P04 能力 | options region only；EB-005 `options_region` **OPEN** | CURRENT.md:215 |
| P07 能力 | `parse_answer_table` + `answer_table_unresolved` flag **已有** | :78–106, :147–148 |
| Not implemented | per-option schema、source metadata、char/table provenance、figure registry、basis enum enforcement、continuous IR、flags registry | — |

### A.2 kurt-wong/AITutors-v3

| Item | Current State | Evidence |
|------|---------------|----------|
| HEAD | `7934844` freeze registration | `git log -1` |
| Consumer Boundary | `scripts/preprocessing_consumer/boundary.py` (`enforce_interface_scope`:283) | **仅 scripts**，未接 production API |
| Identity M1–M5 | `app/core/{manifest,raw_bytes,ir}_identity.py`, `identity_verifier.py`, `identity_gate.py` | 仅 `runner_b2._verify_identity_boundary` |
| Production ingest | `TaskExecutor` → LLM annotation → `GateService` | `executor.py:325` |
| Question model | `subject, grade, canonical_question_type, dedup_key` | `content.py:31–34` |
| QuestionInstance | question_id, document_id, source_version_id, unit_group_id, occurrence_key, question_number, page_no, LE keys | `content.py:45–64` |
| InstanceRoleContent | role, label, role_index, text, text_hash, source_span, answer_status | `content.py:67–84` |
| Admission | `AdmissionService` `app/domains/gate/admission.py:62`；materialize TX | :228–442 |
| Gate | 四层 structural/provenance/semantic/admission | `policy.py:88–297` |
| STRICT_AUTO_TYPES | single_choice, multiple_choice, true_false | `gate/__init__.py:17` |
| Material | composite shared OK；standalone **未消费** CL-22 | `annotation_adapter.py:77–91` |
| Knowledge Node | 表已有（`content.py:166–191`）；**零 writer** | — |
| Metadata 持久化 | 仅 subject/grade；adapter claims 全 None stub | `admission.py:249–251` |
| Enrichment | **零** production 代码（enrich/difficulty/skills/jobs） | repo-wide scan |
| Async worker | 自研 asyncio `app/worker/__main__.py` + `TaskExecutor` | :70–129 |
| Options 消费 | LLM 路径 per-label `InstanceRoleContent(role=option)`；Preprocessing 路径 `GAP_OPTION_LABEL_SPAN_UNAVAILABLE` | `annotation_adapter.py:40,66–71` |
| answer/explanation | source-grounded only；explanation optional；无 generation authority 拆分 | `executor.py:93–97` |
| flags/basis | ManifestUnit 透传（reader only）；**不入 A-domain**；**不进 Gate** | `manifest_reader.py:48–51` |
| IR | `semantic-question-ir/v0.3`；Compiler v1；`ready/incomplete/unknown` | `compile/__init__.py:16–37` |
| DB | 21 tables；无 enrichment/difficulty/skills/jobs | `test_models_schema.py:9–34` |
| Tests | ~89 files；无 enrichment / option.provenance / answer_table 测试 | `backend/tests/` |

---

## B. Contract Traceability Matrix（P01–P25）

| ID | Requirement (essence) | Owner Decision / Clause | Producer / Preprocessing | V3 Consumer | Current Status | Gap | Phase |
|----|----------------------|-------------------------|--------------------------|-------------|----------------|-----|-------|
| P01 | Legacy Artifact 不得直入 V3；唯一路径 Original → Current Preprocessing → Artifact → Boundary | Contract §1b:242–253 | reslice_pipeline 当前产物 | Boundary 存在但未接 production | **PARTIAL** | production Gate/API 未强制 Boundary；Legacy 识别靠 disposition | Ph1–2 |
| P02 | 历史不合规必须重跑；禁 field-patch / compat / special-case / manual DB | §1b:255–268 | 无 patch 通道（正确） | 无 compat 入口（正确） | **COMPLIANT (policy)** | 无正式 rerun 编排 | Ph4 |
| P03 | `source_content_sha256` = Source Content Identity；V3 独立校验 | §1b:270–276 | 产出 sha；identity_version=2 | M1–M5 有校验模块 | **PARTIAL** | production 路径未 AND Identity Gate | Ph2 |
| P04 | 选择题必须 per-option `{label,text,provenance}`；禁 V3 重发现 | §1b:278–320 | **无** per-label；仅 options_lines | GAP_OPTION_LABEL_SPAN_UNAVAILABLE | **MISSING** | schema+prompt+parser+validation+tests | Ph1→2 |
| P05 | Composite = 一个完整 Unit；识别子问 ≠ 拆成独立 Question | §1b:322–326 | prompt 明确 no sub_questions | unit_type composite_unit | **COMPLIANT** | 子问识别能力可选 | Ph1 optional |
| P06 | material_lines ⊇ questions_lines 合法；不强制重切 | §1b:328–338 | prompt 允许嵌套 | composite material 编译 | **COMPLIANT** | — | — |
| P07 | answer_table_unresolved = cell↔question_numbers 映射不可靠；禁猜测 | §1b:340–366 | flag + answers.unresolved **已有** | **零消费**；无映射机制 | **PARTIAL** | V3 无 answer-table mapping；fail-closed 未接 Gate | Ph1→2 |
| P08 | 禁 silent drop flags/basis/answer_evidence/option evidence/provenance/unresolved | §1b:368–382 | 产出（答案证据等） | reader 透传；**不入 A-domain** | **PARTIAL** | P08 要求 evidence 保留；当前不入持久化 | Ph2 |
| P09 | Legacy Unit Type 仅经 Owner 授权确定性归一；`andalone_question` 禁 map | §1b:384–386 | 产出 unit_type | OD-2 两映射 | **PARTIAL** | `andalone_question` fail-closed 需确认 | Ph2 |
| P10 | Canonical Question Type 闭集；禁 silent expand/map | §1b:388–390 | original_question_type 12 值 | CANONICAL_TYPES 12 | **COMPLIANT** | — | — |
| P11 | QT ⊥ UT 独立维度 | §1b:392–398 | 分字段 | 分字段 | **COMPLIANT** | — | — |
| P12 | Preprocessing QC ≠ V3 Gate ≠ V3 Admission | §1b:400–404 | reslice_qc 独立 | Gate/Admission 分层 | **COMPLIANT** | — | — |
| P13 | pending_review 后全链路重跑 | §1b:406–410 | 支持重跑 | 无特殊通道 | **POLICY OK** | 无编排工具 | Ph4 |
| P14 | Preprocessing flags 不得自动改 V3 Gate | §1b:412–414 | 仅 evidence | 不读 flags（正确） | **COMPLIANT** | — | — |
| P15 | 有详解不生成/不覆盖；缺详解可 Post-Admission 生成 | §1b:416–427 | explanation_lines 保留 | explanation optional 不覆盖 | **PARTIAL** | 无 enrichment 生成 | Ph5 |
| P16 | 生成 explanation = V3 Derived Enrichment，非 Source/Preprocessing Authority | §1b:429–435 | N/A | 无 dual-slot | **MISSING** | explanation_preprocessing vs generated 拆分 | Ph5 |
| P17 | MIMO generate → DeepSeek validate | §1b:437–441 | N/A | 无 | **MISSING** | Enrichment pipeline | Ph5 |
| P18 | Enrichment 失败不 rollback Admission | §1b:443–447 | N/A | N/A | **POLICY OK** | 实现时强制 | Ph5 |
| P19 | max 1 retry；二次失败 suspended | §1b:449–451 | N/A | 无 | **MISSING** | 状态机 | Ph5 |
| P20 | 正式入口必须过 Boundary + Interface Scope + M1–M5 | §1b:453–459 | N/A | scripts 有；production 无 | **PARTIAL** | production 接入 | Ph2 |
| P21 | Preprocessing 提供 Source Identity；V3 独立验证 | §1b:461–463 | 提供 sha | M1–M5 | **PARTIAL** | production 未 AND | Ph2 |
| P22 | V3 独立算/验 SHA256；mismatch fail closed | §1b:465–467 | 提供 | identity_gate FAIL closed | **PARTIAL** | production 未接 | Ph2 |
| P23 | source_content_sha256 ⊥ derived_text_hash | §1b:469–475 | 分离 | text_hash 独立 | **COMPLIANT** | — | — |
| P24 | evidence/provenance 必须保留或显式 unsupported；禁 silent discard | §1b:477–479 | 产出 | **丢在 boundary 外** | **MISSING** | A-domain 无 evidence 持久化槽 | Ph2 |
| P25 | Contract ≠ Frozen Spec → STOP → Owner；禁自改 Frozen Spec | §1b:481–489 | N/A | N/A | **PROCESS** | 发现冲突即 STOP | All |

### B.1 重点条款细化

#### P04 Implementation Gap（Option Provenance）

```text
CURRENT
  reslice_pipeline.py PROMPT_HEAD:255  options_lines: [start,end]|null
  resolver_ir.json content.options_lines = text lines only
  PREPROCESSING-PRODUCER-INTERFACE-FACTS.md:145  明确无 options_labels[]
  V3 annotation_adapter.py:40,66–71  GAP_OPTION_LABEL_SPAN_UNAVAILABLE
  V3 production LLM path executor.py:75–90  content.options[{label,role,question_label}]
  （V3 自标 option 但不经 Preprocessing provenance — 违反 P04.1「V3 must not rediscover」）
  provenance 仅 line_span_v1；无 char_span / table_cell / multi-span

GAP
  1. Preprocessing 无 per-option 结构
  2. 无 polymorphic provenance（line_range / char_span_in_line / table_cell / multi-span）
  3. 无 option 级 validation（label 唯一性、A–D 完备性）
  4. 无 option 级 tests
  5. V3 无 options[]={label,text,provenance} 消费
  6. HTML-table options（bio Q51）options_lines=null 吸入 stem（FACT-011）
  7. Image options region 存在但 content 为 <img>

TARGET
  Preprocessing Artifact unit:
    options_lines: [start,end]|null          # P04.2 必须保留
    options: [
      {
        label: "A",
        text: "...",
        provenance: [                         # P04.3 polymorphic
          {type: "line_range", start: 85, end: 85},
          {type: "char_span_in_line", line: 85, start: 3, end: 20},
          {type: "table_cell", ...} |
          {type: "multiple_source_spans", spans: [...]} |
          {type: "...", ...}                  # 其他可验证 provenance
        ]
      }, ...
    ]
  不可靠 → options: unresolved（显式），禁猜测（P04.4）
  V3: 消费 options[]，校验 provenance 可验证，禁自行切分 options_lines 造 option

IMPLEMENTATION STEPS
  1. Preprocessing: 定义 option JSON 形状（in prompt JSON + validate_manifest）
  2. Preprocessing: prompt 扩展（v2.8+）要求 per-option label/text/provenance
     - 保留 options_lines 整区
     - table/image options 显式 unresolved 或 table_cell provenance
  3. Preprocessing: parser 接受 options[]；缺省 = incomplete
  4. Preprocessing: validation（label 闭集 A–Z、text 非空、provenance 合法 span）
  5. Preprocessing: resolver IR 拷贝 options[] + 保留 options_lines
  6. V3 annotation_adapter: 消费 options[]；拒绝 V3 自切 options_lines
  7. V3 IRBuilder/Compiler: option leaf 绑定 provenance → source_span
  8. V3 Gate: option provenance 进 provenance 层校验
  9. V3 Admission: InstanceRoleContent(label=…) 来自 Preprocessing options[]

TESTS
  Preprocessing:
    - test_option_schema.py：per-option 形状、label 唯一、provenance 类型
    - test_option_provenance_polymorphic.py：line/char/table/multi-span
    - test_option_fail_closed.py：不完整 → unresolved，禁部分填充
    - test_options_lines_coexist.py：options_lines 与 options[] 并存
  V3:
    - test_option_provenance_consume.py
    - test_option_fail_closed_boundary.py
    - test_adversarial_option_label.py（label 重复/缺失/猜测）
    - test_no_v3_option_rediscovery.py（禁 V3 从 options_lines 切 option）
```

#### P07 Implementation Gap（Answer Table Mapping）

```text
链路:
  Source → reslice/ocr → manifest answer_lines/answer_evidence
    → resolver parse_answer_table
    → IR answers{cells,method,answers,unresolved} + flags[answer_table_unresolved]
    → V3 (当前: answer_zone enum only；零消费)

CURRENT
  产生点: resolver_reference.py:78–106 parse_answer_table
          :147–148 build_unit_records → flag answer_table_unresolved
  answers.cells: 原始 <td> 文档序扁平数组（含题号/答案表头）
  method: td_by_question_number | td_positional
  answers: {qnum: cell_text}；unresolved: [qnum,...]
  映射无法确定的原因（实测）:
    - cell 数 ≠ unit question 数（整卷共享表）
    - td_positional 无法绑定题号
    - 表头行/合并单元格
  counts: answer_table_unresolved 91 units；answer_number_mismatch 502

  V3: answer_zone ∈ {answer_table, inline_answer} 仅为 enum 标签
      无 cell↔question mapping；无 flag 消费

GAP
  1. mapping 规则不足（td_by_question_number 覆盖不全；td_positional 易错）
  2. unresolved 时信息保留不完整进入 V3（answers.cells 未传到 V3）
  3. V3 无 fail-closed 路径把 unresolved 变成 pending_review/QC_FAIL
  4. 无测试覆盖「禁猜测」

RULES TO MODIFY (Preprocessing only)
  - parse_answer_table: 强化 td_by_question_number（解析题号列；支持「题号」表头）
  - 明确 positional 仅在 cells==questions 一一对应且无表头时允许
  - 其余一律 unresolved[]，保留 answers.cells 全文
  - 禁 answers.get(q,"") 静默默认（consumer 侧已有禁令，producer 也应对齐）

INFO TO RETAIN
  - answers.cells 全文（P07.4：unresolved mapping ≠ delete answer-table info）
  - method
  - unresolved[]
  - flags: answer_table_unresolved
  - answer_evidence {type: answer_table, ...}
  - source span of table

FAIL CLOSED
  unresolved 非空 → flag + answers 保留 + disposition 明示
  V3: answer_table_unresolved → retained_as_uncertainty（IPM）
      不得 auto-reject / auto-pending（P14：无正式规则不改 Gate）
      但 answer 角色若无法 source_located+complete → 现有 Gate 已 pending
      禁止 V3 猜测 cell→question 对应

TESTS
  Preprocessing:
    - test_answer_table_mapping.py（题号列/位置/表头/合并）
    - test_answer_table_unresolved_fail_closed.py
    - test_answer_cells_retained.py
  V3:
    - test_answer_table_unresolved_preserved.py
    - test_no_answer_mapping_guess.py
```

#### Historical Source Reprocessing Principle（绑定）

```text
所有历史 Preprocessing Artifact 均不得被视为当前 AITutors-v3 的兼容输入标准。
凡历史 Artifact 不满足当前 Preprocessing → AITutors-v3 Consumer Contract，
必须保留 Original Source Document 及历史 provenance，
并使用当前版本 AITutors-preprocessing 重新生成 Current Preprocessing Artifact。
AITutors-v3 只消费满足当前 Contract、Identity、QC 与 Consumer Boundary 要求的当前产物。

禁止替代物: artifact field-patch / compatibility conversion /
            AITutors-v3 special-case / manual DB mutation as re-admission
覆盖: Legacy V1 · QC_FAIL · REJECTED_V1 · P04 historical choice ·
      P07 answer_table_unresolved historical · pending_review after human review
本原则不自动授权任何历史 rerun（需单独 Owner order）。
```

---

## D. Architecture Boundary

```text
┌─────────────────────────────────────────────────────────────────┐
│ A. Question Core（决定 Question 是否完整）                         │
│    stem · options · answer · explanation · composite structure   │
│    · necessary material/context                                  │
│    Admission 必需；缺失 = Question 不完整，禁止 enrichment 洗白    │
├─────────────────────────────────────────────────────────────────┤
│ B. Source-derived Metadata（可靠提取则随 Question 进入）           │
│    year · grade · semester · exam phase · exam name · region ·   │
│    school · subject · original question number · source location │
│    Authority: Source/Preprocessing 提供；Boundary 验证            │
│    不因 LLM enrichment 未完成而阻塞                               │
├─────────────────────────────────────────────────────────────────┤
│ C. LLM-derived Metadata（不得成为普通 Admission 阻碍）            │
│    difficulty · knowledge_nodes · skills · cognitive level ·      │
│    tested concepts · prerequisite · misconception · recommend.   │
│    Authority: AITutors-v3 Derived Enrichment (V3D)               │
│    缺失 ≠ Question 不完整 ≠ 不可 Admit                           │
│    例外: 若 Frozen Spec 明文将某字段升为 Admission-necessary       │
│          → 以 Frozen 为准（禁止绝对「metadata 永不影响 Admission」）│
├─────────────────────────────────────────────────────────────────┤
│ D. Post-Admission Enrichment（异步派生信息生成）                   │
│    (A) Derived Metadata: difficulty / knowledge_nodes / skills   │
│    (B) Missing Explanation（仅 P15 覆盖规则；非「只准补 explanation」）│
│    不 rollback Admission（P18）；max 1 retry（P19）                │
└─────────────────────────────────────────────────────────────────┘

Admission formula（Contract §1d:576–593 / PAE:65–73）:
  Question Core
  + Frozen Spec required conditions
  + Identity / Evidence / Gate
  → Admission
  →（可选）Async Enrichment

Admission requires:
  1. stem（非空；Frozen content_roles: required for all 12 QT）
  2. options（choice 类型 required_for_choice；其余 not_applicable）
  3. answer（required for all 12；「无标准答案」≠ not_applicable）
  4. question_type（canonical 闭集）
  5. unit_type / internal structure（Frozen）
  6. Identity / provenance 可验证（M1–M5 + text_hash；P21–P23）
  7. Evidence / Gate 通过（Structural / Provenance / Semantic / Admission 四层）
  8. Frozen Spec 明文要求的其他 admission 字段

Admission does NOT require（Frozen Spec 未升格为 admission 必需字段者）:
  1. difficulty
  2. knowledge_nodes
  3. skills
  4. 其他 ordinary LLM-derived metadata
  5. missing explanation（explanation = optional for all 12 QT）
  ※ 不得凭空增加「Admission 不需要」字段；以上均有 Frozen/Contract 依据。
  ※ Source-derived Metadata「随 Question 进入」但不等于 Admission 阻碍
    （缺失 source metadata 不挡 Admission，除非 Frozen 升格）。
```

### D.1 依赖链（Knowledge Graph / Analysis / Recommendation）

```text
Question (Admitted)
   ↓
difficulty · knowledge_nodes · skills   ← Post-Admission Enrichment
   ↓
Knowledge Graph / Statistics / Recommendation

结论: 后续能力依赖 Derived Metadata；
      但 Metadata 不是 Question Admission 的前置条件。
```

---

## E. Schema Gap Analysis

> 发现 schema 缺口 ≠ 立即修改 schema。需 Frozen Spec 变更者 → STOP / OWNER DECISION REQUIRED。
> **OD-05：** Producer-side / Preprocessing Artifact Schema 可在 Contract 语义内扩展；**V3 Frozen Schema 不可由 Implementation 自行扩展**。本 Plan 不构成 schema modification authorization。
> **OD-03：** Evidence 要求是完整可追溯；**不预先锁定 persistence table**。禁止把「一律进 Candidate / QuestionEvidence 表」写成既定事实。

### E.1 Preprocessing Artifact schema

| Capability | Supported? | Notes |
|------------|------------|-------|
| Question Core (stem/options region/answer/explanation spans) | PARTIAL | options 仅 region |
| Source-derived Metadata | **NO** | 无 year/grade/semester/exam_*/region/school/subject 字段 |
| option provenance | **NO** | 仅 options_lines；无 {label,text,provenance} — **OD-01 要求扩展；Resolved Span ontology 见 D4 Proposal（pending re-freeze）** |
| answer evidence | YES | `answer_evidence` v2.4+ |
| flags | PARTIAL | 仅 2 值；未入 rule_registry |
| basis | YES | 6 值闭集 |
| explanation | PARTIAL | 仅 span |
| unresolved information | PARTIAL | answers.unresolved + flags；options 无 |
| polymorphic provenance | **NO** | line_span_v1 only |
| figure registry/hash | **NO** | inline `<img>` only |
| Formal JSON Schema / pydantic | **NO** | prompt+dict |

### E.2 V3 schema

| Capability | Supported? | Notes |
|------------|------------|-------|
| Question Core | YES | role_contents stem/options/answer/explanation |
| Source-derived Metadata | PARTIAL | 仅 subject/grade 列 |
| Derived Metadata | **NO** | 无 difficulty/skills 列；knowledge_nodes 表无 writer |
| explanation provenance (source) | PARTIAL | source_span + text_hash |
| explanation_generated slot | **NO** | 无 dual-slot |
| enrichment state / job / validation result | **NO** | 无表 |
| option provenance (polymorphic) | PARTIAL | source_span JSONB 可装；消费路径无 |
| Producer flags / basis 持久化 | **NO** | reader 透传即止 |
| answer_evidence 持久化 | **NO** | 不入 A-domain |
| enrichment_jobs[] | **NO** | OD-V3-25 OPEN |

**Schema 变更涉及 Frozen Spec (`10_Data_Model` / `20_Document_Pipeline`) 者一律 OWNER DECISION（OD-05）。**
v0.3 逻辑槽（非 DDL，PAE:241–254）可作为实现参考，**落地 DDL 前须授权**（不得视为已批准 persistence design）：

```text
explanation_preprocessing · explanation_generated (+generation provenance,
validation_state, retry_count) · difficulty_generated · knowledge_generated ·
skills_generated · enrichment_jobs[]
```

Evidence persistence（P08/P24）在 OD-03 下只要求 complete traceability；**table 选择未决**，优先复用 Frozen Schema 现有结构。

---

## F. Implementation Phases

**执行顺序（Owner 令）：**

```text
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 5 → Phase 6 → Phase 4
```

Historical Rerun（Phase 4）在实现完成后验证阶段执行，不作为开发过程中的活动数据集。

### Phase 0 — Contract / Frozen Baseline Verification

| Item | Content |
|------|---------|
| **Entry** | Owner 已批准 Implementation Plan + Limited Implementation Authorization |
| **Scope** | 确认治理基线 `b743c5d`（Semantic）+ `7934844`（Registration）+ Frozen Spec tree `b3eeb3e9`；核对两 repo HEAD；打印 Authority Order；测试基线 |
| **Forbidden** | 任何代码/schema 修改；任何 corpus 操作 |
| **Tests** | 双仓 pytest 基线 |
| **Evidence** | Baseline Verification Report |
| **Exit** | `Authority baseline verified` |

### Phase 1 — Preprocessing Contract Implementation

| Item | Content |
|------|---------|
| **Entry** | Phase 0 Exit **+ OD-01 Frozen Spec Change Proposal 完成 Owner review / re-freeze**（P04 Resolved Span ontology 部分） |
| **Scope** | **P04** per-option `{label,text,provenance}` + polymorphic provenance（**ontology 以 re-freeze 后 Frozen Resolved Span 为准**；`options_lines` 必须保留；fail closed）；**P07** mapping 规则强化 + fail-closed + cells 保留；**Source-derived Metadata** 提取字段（year/grade/semester/exam_phase/exam_name/region/school/subject）写入 manifest/IR（**Producer-side 可扩展 — OD-05**）；required provenance preservation（P24 保留义务，非锁定表）；option/answer validation。**Source-derived authority = OD-02** |
| **Forbidden** | 改 V3；migration；历史 corpus 重跑；LLM 生产调用（prompt 设计可写，批量跑需另授权）；改 Frozen Spec/Contract；改 P01–P25；**在 re-freeze 前实施 OD-01 Resolved Span 扩展**；自行扩大 V3 Frozen Schema |
| **Tests** | §B.1 P04/P07 测试清单 + source metadata extract 测试 + 回归 `tests/` 全绿 |
| **Evidence** | 新 prompt 版本号；sample Artifact 含 options[]；resolver_ir 样本含 answers.cells+unresolved；pytest 日志 |
| **Exit** | P04 形状落地且 fail-closed；P07 mapping/unresolved/retain 全过测试；source metadata 字段出现在 Artifact；无 silent discard；现有 338+ 基线不回归 |

### Phase 2 — V3 Consumer Boundary

| Item | Content |
|------|---------|
| **Entry** | Phase 1 Exit（或并行：V3 侧接口可先按 Contract 形状开发） |
| **Scope** | artifact consumption（manifest+IR 全量）；Identity M1–M5 **接入 production**（P20–P22）；**OD-04 Artifact-first 接入设计**（保留 infrastructure，禁止第二 semantic authority path）；metadata preservation（**OD-02**：verified Source-derived = authoritative；annotation = claim；conflict-as-signal）；evidence preservation（**OD-03** complete traceability：flags/basis/answer_evidence/option provenance 可追溯、非 silent drop；**不锁 table**）；options[] 消费（禁 rediscovery）；answer-table unresolved 保留（不进 Gate 自动决策） |
| **Forbidden** | 改 Gate 语义（P14）；改 Admission 条件；改 Frozen Spec；migration；enrichment 实现；自行新增 V3 Frozen Schema 属性（OD-05） |
| **Tests** | identity production path 测试；P08 preservation 测试；option consume/adversarial；answer_table preserved；boundary fail-closed；conflict-as-signal |
| **Evidence** | production 路径调用 enforce_interface_scope + evaluate_identity_gate 的代码引用；evidence 可追溯样本 |
| **Exit** | Production ingest 强制 Boundary+Identity；P08 字段可查可追溯；无 V3 option rediscovery；unresolved 不丢失；无第二 semantic authority path |

### Phase 3 — Admission Alignment

| Item | Content |
|------|---------|
| **Entry** | Phase 2 Exit |
| **Scope** | 确认 **Question Core 完整即可 Admission**；普通 Derived Metadata 缺失不阻塞；对齐 Frozen content_roles（stem/options/answer required 语义）；explanation optional 不挡门；保留 Frozen Spec 明文 admission 字段 |
| **Forbidden** | 移除 Frozen admission 条件；为 metadata 新增 Gate 条件；改 P15–P19 |
| **Tests** | admission_without_difficulty_knowledge_skills；admission_missing_explanation_ok；admission_core_missing_rejected；admission_frozen_required_fields |
| **Evidence** | 测试通过日志 + policy 对照表 |
| **Exit** | Core+Identity+Gate → Admission 稳定；metadata/enrichment 缺失零阻塞；Frozen 必需字段仍强制 |

### Phase 4 — Historical Source Rerun

**执行顺序（Owner）：Phase 0 → 1 → 2 → 3 → 5 → 6 → 4。** Historical Rerun 在实现验证后执行，不作为开发过程中的活动数据集。

| Item | Content |
|------|---------|
| **Entry** | Phase 1–3 + 5–6 Exit + **单独 Owner order**（Historical Rerun 执行令；原则已 AUTHORIZED IN PRINCIPLE） |
| **Scope** | 对历史原始文件重跑 Current Preprocessing → Boundary → Gate → Admission（§H） |
| **Forbidden** | artifact patch；compat conversion；V3 special-case；manual DB mutation；删除 Original Source；覆盖 source_content_sha256 |
| **Tests** | rerun 幂等性；identity 不变；旧 Artifact 隔离；失败清单可审 |
| **Evidence** | Rerun Registry；前后对比；QC 报告 |
| **Exit** | 目标 corpus 全部走当前标准链路；无旧 Artifact 误入；provenance 完整 |

### Phase 5 — Post-Admission Enrichment

| Item | Content |
|------|---------|
| **Entry** | Phase 3 Exit + schema 变更授权（若需 DDL）+ Enrichment 实现授权 |
| **Scope** | difficulty · knowledge_nodes · skills · missing explanation；MIMO generate → DeepSeek validate；persist Derived Metadata；P15 覆盖规则；P16 V3D authority；P18 不 rollback；P19 max 1 retry → suspended |
| **Forbidden** | 覆盖已有 explanation；把 V3D 标成 Source/Preprocessing Authority；无限 retry；用 enrichment 洗白 Core 缺失；阻塞 Admission 等待 enrichment |
| **Tests** | P15 preserve/overwrite 禁令；P16 authority 标签；P17 chain；P18 no-rollback；P19 retry/suspended；validation min set |
| **Evidence** | enrichment_jobs 审计链；validation_event 样本 |
| **Exit** | 全链路 Core → Admission → Persistence → Async Enrichment；状态机完整；失败策略符合 P18–P19 |

### Phase 6 — Full End-to-End Verification

| Item | Content |
|------|---------|
| **Entry** | Phase 1–5 Exit |
| **Scope** | Source → Preprocessing → Consumer Boundary → IR → Gate → Admission → Enrichment 全链路金样验证 |
| **Forbidden** | 任何规范修改 |
| **Tests** | E2E 金样 + 对抗样例 + 回归 |
| **Evidence** | E2E Report |
| **Exit** | 全链路可重复运行；治理基线未漂移；无未决 FROZEN CONFLICT |

---

## G. Tests / Exit Criteria 汇总

| Phase | 必须通过 | Exit 一句话 |
|-------|----------|-------------|
| 0 | Baseline checklist | 双 SHA + Authority Order 确认 |
| 1 | Preprocessing 全量回归 + P04/P07/metadata 新测试 | Producer 能产出 Contract 形状且 fail-closed |
| 2 | Boundary/Identity production + P08 preservation + option consume | V3 强制 Boundary 且不丢 evidence |
| 3 | Admission alignment 测试集 | Core 完整即可进；metadata 不挡门 |
| 4 | Rerun 幂等/隔离/identity | 历史全走当前链路，无 patch |
| 5 | P15–P19 全测试 | Enrichment 异步、可审计、不 rollback |
| 6 | E2E 金样 | 全链路可重复、无冲突未决 |

---

## H. Historical Rerun Plan（只规划，不执行）

```text
Original historical source
        ↓
Current AITutors-preprocessing（Phase 1 后版本）
        ↓
Current-standard artifact
        ↓
V3 Consumer Boundary（Identity + Interface Scope）
        ↓
Gate
        ↓
Admission
```

| Question | Plan |
|----------|------|
| 原始来源在哪里 | Preprocessing `Ocr-markdown/**` 及网络卷宗原始 PDF/DOCX/扫描件；保留 Original Source Document 不可变 |
| 如何识别历史 corpus | Legacy V1 / identity_version 缺失或 ≠2 / disposition ∈ {REJECTED_*, MISSING, REJECTED_V1} / P04 无 per-option 证据 / P07 `answer_table_unresolved` historical / QC_FAIL / pending_review-processed |
| 如何保证 source identity | 每次 rerun 计算 `source_content_sha256=SHA256(raw bytes)`；与历史记录比对；派生变更 → 新 hash+provenance，不覆盖 Source Identity |
| 如何避免旧 Artifact 误当新 Artifact | 新 Artifact 写入 `identity_version=2` + `prompt_version`（≥ Phase 1 版本）+ `source_content_sha256`；入库侧 Boundary 拒绝缺失三者；旧 Artifact 物理隔离目录（不删除） |
| 如何记录 provenance | 保留历史 provenance 文件 + rerun 映射表（map_plan 风格）+ manifest `printed_provenance`/`basis_evidence`/spans；registry 追加不覆盖 |
| preprocessing 失败 | fail-loud 记录文件级原因；不进 V3；进入 Rerun Failure Ledger；禁止 silent skip |
| pending_review | 全链路重跑（P13）；人工决定后重新 Original → … → Admission；禁止只改 DB |
| 如何验证 rerun 后结果 | source_content_sha256 不变；unit 覆盖率对照；P04 options 抽样可验证；P07 unresolved 数下降且 cells 保留；Gate/Admission 分布报告 |
| 如何保证可重复运行 | 固定 prompt_version + model config + 输入字节；registry 记录 attempt；幂等键 `(source_content_sha256, pipeline_version)` |

**本 Phase 不得在无 Owner order 时启动。**

---

## I. OWNER DECISION REQUIRED（reconciled）

> 只列真正需要 Owner 裁决的事项。已由 OD-01~OD-05 / G-01 / G-02 裁决者不再重复开单。

| # | Item | Why Owner | Blocks Phase | Reconciled |
|---|------|-----------|--------------|------------|
| **OD-01 / D4** | **Frozen Resolved Span 扩展（P04 option provenance ontology）** | 必须改 Frozen Spec；Proposal ≠ 生效 | Ph1 P04 部分 | **APPROVED design / pending re-freeze** |
| OD-IMP-1 | **Historical Source Rerun 执行令** | 原则已批；需范围/顺序/资源/时机 | Ph4 | 原则=OD/Authorization 已批；**执行另令** |
| OD-IMP-2 | **Enrichment persistence schema（DDL）** | PAE 逻辑槽非 DDL；改 `10_Data_Model` = Frozen Spec（P25/OD-05） | Ph5 | 仍 OPEN |
| OD-IMP-3 | **Explanation dual-slot 落库字段名与权威标签** | 涉及 Frozen `instance_role_contents` 语义扩展 | Ph5 | 仍 OPEN |
| OD-IMP-4 | **Source-derived Metadata 正式 schema 字段集（若升格 Frozen 属性）** | 改 `questions` 表 = Frozen Spec（OD-05） | Ph1–2 落库 | Producer 侧扩展已允许；**V3 Frozen 落库仍 OPEN** |
| OD-IMP-5 | **`answer_table_unresolved` → Gate/Admission 正式规则** | P14：flags 不得自动改 Gate | Ph2–3 | 仍 OPEN（**未授权**） |
| OD-IMP-7 | **Material / CL-22 / OD-BLOCK-02** | 先执行既有裁决；仅未决冲突才升级 | 非阻塞 | 按既有裁决 |
| OD-IMP-8 | **`semantic_status=unknown` → reviewable 路径** | 未授权新 formal state（见 Authorization §3.9） | Ph2–3 | 仍 OPEN |
| OD-IMP-9 | **P25 冲突裁决通道**（预留） | STOP 机制 | 按需 | 预留 |

**已由 Owner Decision 关闭（不再作为 Implementation 自选）：**

| Former question | Resolution |
|-----------------|------------|
| Production 双轨 vs Artifact-only | **OD-04 = Artifact-first / Artifact-authoritative**；禁第二 semantic authority path；可保留 execution infrastructure |
| Source-derived authority | **OD-02 = Source Authority + Conflict-as-signal** |
| Evidence 放哪张表 | **OD-03 = complete traceability only**；table 未锁 |
| Producer schema 能否扩展 | **OD-05 = YES within Contract**；V3 Frozen Schema = STOP |
| G-02 基线表述 | **VERIFIED**：`b743c5d` = Semantic Baseline；`7934844` = Registration |

**非 Owner 决定（Implementation 可选，留给 Agent）：** 函数命名、模块拆分、测试文件名、prompt 措辞（在不改语义前提下）、日志格式、内部迭代顺序。

---

## J. Forbidden / Not Authorized（本 Planning 任务实际执行结果）

```text
Code:
NOT MODIFIED

Preprocessing Code:
NOT MODIFIED

V3 Code:
NOT MODIFIED

Schema:
NOT MODIFIED

Corpus:
NOT RERUN

Migration:
NOT EXECUTED

Historical Artifact:
NOT REWRITTEN

LLM Calls:
NOT MADE

Enrichment:
NOT IMPLEMENTED

Gate:
NOT MODIFIED

Admission:
NOT MODIFIED

Frozen Spec:
UNCHANGED

Frozen Contract:
UNCHANGED

P01–P25:
NOT MODIFIED

X3:
NOT ENTERED

Implementation:
LIMITED SCOPE AUTHORIZED (see LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md)
Phase 1 NOT STARTED
```

---

## 16. End-to-End Data Flow（目标态 vs 当前差异）

```text
Original Source
      ↓
AITutors-preprocessing
      ↓
Preprocessing Artifact
      ↓
Identity Verification (M1–M5)
      ↓
Consumer Boundary
      ↓
Semantic Question IR
      ↓
Compiler
      ↓
Gate
      ↓
Admission
      ↓
Question persisted
      ↓
Post-Admission Enrichment
      ├── difficulty
      ├── knowledge_nodes
      ├── skills
      └── missing explanation
      ↓
Knowledge Graph / Analysis / Recommendation
```

**实际代码差异（不得为对齐图而强行改架构）：**

1. Production ingest 目前是 `TaskExecutor → LLM annotation → GateService`，**不是** Artifact → Boundary（OD-04 要求收敛为 Artifact-first；禁止第二 semantic authority path）。
2. Consumer Boundary + M1–M5 仅在 `scripts/preprocessing_consumer/runner_b2.py`。
3. Semantic Question IR 由 V3 `IRBuilder` 自 LLM annotation 构建；**未**消费 Preprocessing IR 语义（仅 M3 取 sha）。
4. Post-Admission Enrichment 与 Knowledge Graph 写入 **尚不存在**。

---

## IMPLEMENTATION PLANNING STATUS:

```text
Contract v0.3:
FROZEN

Frozen Semantic Baseline:
b743c5daf0806ea00c84afb1b92ca2a3b5dbfc98

Freeze Registration:
79348441dae0efce6855017b2b5c0491b08d6bb8
(governance-state commit — does NOT replace b743c5d)

Implementation Plan:
OWNER APPROVED
(reconciled with OD-01~OD-05 + G-01 + G-02)

Limited Implementation Authorization:
OWNER APPROVED — LIMITED SCOPE
(see LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md)

OD-01:
APPROVED DESIGN — PENDING FROZEN SPEC INCORPORATION
(see FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md)

OD-02 Source Authority + Conflict-as-signal:
BINDING

OD-03 Evidence Complete Traceability:
BINDING (persistence table NOT locked)

OD-04 Artifact-first / Artifact-authoritative:
BINDING

OD-05 Producer-side extensible / V3 Frozen Schema STOP:
BINDING

G-01 Plan + Authorization in Git:
APPROVED

G-02 b743c5d → 7934844:
VERIFIED

Preprocessing Gaps:
  - options[] {label,text,provenance} + polymorphic provenance (P04 / OD-01)
  - structured source metadata (Producer-side extensible — OD-05)
  - char/table-cell provenance (line_span only)
  - option validation + fail-closed tests
  - answer_table mapping rules hardening (P07) — flag/cells 已有，规则与测试不足
  - basis/unit_type enum enforcement; figure registry; formal schema

V3 Gaps:
  - production Boundary + M1–M5 Identity Gate 未接 API/GateService (P20–P22 / OD-04)
  - options[] 消费与禁止 rediscovery (P04 / OD-01)
  - answer_table mapping / unresolved 保留路径 (P07)
  - flags/basis/answer_evidence complete traceability (P08/P24 / OD-03)
  - source-derived metadata 超出 subject/grade (OD-02 authority 已定)
  - Post-Admission Enrichment 全缺 (P15–P19)
  - explanation dual-slot / V3D authority (P16)
  - knowledge_nodes writer（表有、写入无）
  - material / unknown 路径（先查既有裁决）

Question Core Boundary:
  FROZEN — stem/options/answer/explanation/structure 决定完整性；
  Admission = Core + Frozen required + Identity/Evidence/Gate；
  禁止 enrichment 洗白 Core 缺失

Source-derived Metadata:
  OD-02: Source → Preprocessing → verified = AUTHORITATIVE；
  LLM = claim only；conflict-as-signal；默认非 Admission blocker

LLM-derived Metadata:
  difficulty/knowledge_nodes/skills 等 — 不得阻塞 Admission；
  Authority = V3D；Post-Admission async

Post-Admission Enrichment:
  (A) Derived Metadata + (B) Missing Explanation；
  MIMO generate → DeepSeek validate；P15 不覆盖；P18 不 rollback；
  P19 max 1 retry → suspended
  Authorized in principle / Schema Gap → STOP (OD-05)

Historical Rerun:
  AUTHORIZED IN PRINCIPLE / NOT EXECUTED
  路径 = Original Source → Current Preprocessing → Boundary → Gate → Admission
  无 patch / 无 compat / 无 special-case / 无 manual DB
  执行顺序 = 实现验证之后（Phase 4 after Phase 6）

Owner Decisions Required (remaining):
  OD-01 re-freeze (Proposal pending)
  OD-IMP-1 Historical Rerun 执行令
  OD-IMP-2 Enrichment persistence schema (DDL)
  OD-IMP-3 Explanation dual-slot field names / authority labels
  OD-IMP-4 Source-derived Metadata V3 Frozen schema (if needed)
  OD-IMP-5 answer_table_unresolved → Gate formal rule (P14)
  OD-IMP-8 semantic_status=unknown reviewable path
  OD-IMP-9 P25 conflict channel (reserved)

Production Code:
UNCHANGED

Schema:
UNCHANGED (OD-05: no self-authorized V3 Frozen Schema change)

Corpus:
UNCHANGED

Migration:
NOT EXECUTED

X3:
NOT ENTERED

Phase 1:
NOT STARTED
(blocked on OD-01 re-freeze for P04 Resolved Span ontology)
```

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/IMPLEMENTATION-PLAN-v0.3.md` |
| Status | OWNER APPROVED |
| Authority | IMPLEMENTATION PLAN (below Owner Decisions) |
| Purpose | IMPLEMENTATION PLANNING ONLY |
| Reconciled | OD-01~OD-05 + G-01 + G-02 |
| Compiled from | Contract `b743c5d` / Registration `7934844` / Frozen Spec tree `b3eeb3e9` / Preprocessing `2b92898` / V3 live tree |
| Next | Owner review of OD-01 Frozen Spec Change Proposal → re-freeze → DSH verification → Phase 1 |
