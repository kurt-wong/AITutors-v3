# Open Decisions / Gaps v0.3

> **状态**：`OWNER DECISION STATUS: COMPLETE` / 配套 `PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` = `CONTRACT FREEZE CANDIDATE`
> **术语**：`Preprocessing` = `kurt-wong/Aitutors-preprocessing`；`AITutors-v3` = 当前 V3 系统；`Legacy Preprocessing Artifact (V1 format)` = 历史产物格式；`Producer` **仅**作抽象架构角色（详见 Contract §0）
> **证据标签**：`OBSERVED` / `DECISION` / `OPEN`
>
> **本轮（Owner Decisions P01–P25 落版）**：
> - Owner Decisions **P01–P25: COMPLETE**（正式落版见 Contract §1b）
> - **P04 = CLOSED** · **P07 = CLOSED** · **P08 = CLOSED**（不再把 P07 表述为 HOLD）
> - 已由 Owner Decisions **解决**的 `OWNER DECISION REQUIRED` 项 → 状态改为 `OWNER DECISION COMPLETE (P##)`
> - **真正的 implementation questions 保持 `OPEN`**，**未**伪装成 Owner Decision（本文件不追求"全绿"）
> - 本清单**不**授权实现、**不**授权历史重跑、**不**授权 migration

---

## A. Identity / Scope

| ID | 项 | 现状 | 状态 | 裁决 / 备注 |
|---|---|---|---|---|
| OD-V3-01 | Legacy (V1 format) 79 份缺 `source_content_sha256` / `identity_version` | `OBSERVED` | **`OWNER DECISION COMPLETE (P01/P02)`** | **不回填、不迁移、不建 compatibility path**；统一走 Original Source → Current AITutors-preprocessing → Current Preprocessing Artifact（§1c） |
| OD-V3-02 | REJECTED_V1（1）历史处置 | `OBSERVED` | **`OWNER DECISION COMPLETE (P01/P02)`** | 属 Legacy Preprocessing Artifact (V1 format)；同上，不作 AITutors-v3 直接输入 |
| OD-V3-03 | raw bytes 跨机可达（OQ-12） | `OBSERVED` | `OPEN` | **implementation / 传输形态**；P21/P22 已固化”提供→独立验证”义务，但传输 HOW 仍属实现（继承 v0.2 ⑥ 不冻结传输） |
| OD-V3-04 | OCR 清单 `source_sha256`（PDF bytes）是否纳入接口 | `OBSERVED` | `OPEN` | P03/P23 已**禁止**与 `source_content_sha256` 混用；”是否纳入接口面”未被 P01–P25 裁定 |

---

## B. Preprocessing 质量 / 结构

| ID | 项 | 现状 | 状态 | 裁决 / 备注 |
|---|---|---|---|---|
| OD-V3-05 | 16 × QC_FAIL 处理 | `OBSERVED` | **`OWNER DECISION COMPLETE (P02)`** | 不做 Consumer 降级、不做字段修补；统一重跑（§1c） |
| OD-V3-06 | option-label evidence 粒度 | `OBSERVED` GAP | **`CLOSED (P04)`** | Preprocessing 必须正式产出 `options[] = {label, text, provenance}`，并与 `options_lines` 并存；AITutors-v3 不重新发现/不猜。**实现未授权** |
| OD-V3-07 | subquestion decomposition | `OBSERVED` GAP | **`OWNER DECISION COMPLETE (P05)`** | Composite 保持整体 Question；sub-question 为内部结构，识别不等于拆分为独立 Question |
| OD-V3-08 | answer table mapping 502 unresolved | `OBSERVED` | **`CLOSED (P07)`** | 语义 = **共享答案表 cell → 本 Unit question_numbers 的映射不可靠**（禁止简化为”答案表错误”）；属 AITutors-preprocessing 解析/映射规则问题，重跑而非 patch。**实现未授权** |
| OD-V3-09 | 596 units printed provenance unknown | `OBSERVED` | `OPEN` | **数据现状观察**，非待裁架构题；保持 `unverified`/`unknown`，不得抬升 |
| OD-V3-10 | 41 composites material/questions 同区间 | `OBSERVED` | **`OWNER DECISION COMPLETE (P06)`** | **重叠本身不是错误**；不得为制造不重叠区间而强制重切 |
| OD-V3-11 | `andalone_question`（1）清理 | `OBSERVED` | **`OWNER DECISION COMPLETE (P09)`** | **禁止兼容映射**；只能 Owner-authorized deterministic normalization，否则重跑 |

---

## C. Canonicalization / Vocabulary

| ID | 项 | 现状 | 状态 | 裁决 / 备注 |
|---|---|---|---|---|
| OD-V3-12 | QT closed-set enforcement 未接线 | `OBSERVED` | `OPEN` | **implementation question**（接线形态）。原则已定：P10 不得擅自扩集 |
| OD-V3-13 | `listening` 等闭集外值 | `OBSERVED` | **`OWNER DECISION COMPLETE (P10)`** | **不扩集、不静默映射**；闭集外值 → `explicitly_unsupported` / `rejected`，historical value 仅作 provenance 保留 |
| OD-V3-14 | mapping_registry vs boundary.normalize_unit_type 双权威 | `OBSERVED` | `OPEN` | **implementation question**。P09 要求 canonical mapping 最终只有一个 runtime authority，但”选哪一个 / 降级另一方”未被 P01–P25 裁定 |
| OD-V3-15 | Gate grammar / auto_approve（NEW-F3） | `OBSERVED` | `OPEN` | **implementation / 产品策略**。P12/P14 已裁原则（三层互不等同；flags 不自动改 Gate），但”实现 grammar 映射 vs 书面废止 auto”未裁定 |

---

## D. Consumer Boundary / Runner

| ID | 项 | 现状 | 状态 | 裁决 / 备注 |
|---|---|---|---|---|
| OD-V3-16 | `runner.py` 缺 M1–M5（NEW-F1） | `OBSERVED` | `OPEN` | **implementation question under P20**。P20 已裁”所有正式 entrypoint 必经 Consumer Boundary + Interface Scope + M1–M5”；删除 / 硬阻断 / 对齐 B2 的**处置形态**未裁定 |
| OD-V3-17 | batch resolver IR 分发（NEW-F2） | `OBSERVED` | `OPEN` | **implementation question**；Contract §13 只定义不实现 |
| OD-V3-18 | flags / basis / answer_evidence 进 Gate 或 review | `OBSERVED` CONSUMER GAP | **`CLOSED (P08/P14)`** | 默认属于 **Preprocessing evidence / provenance / review signal**，**不是** AITutors-v3 Gate authority；未经正式 Contract/Owner rule 不得自动变 reject 或 pending_review。**实现未授权** |
| OD-V3-19 | preprocessing_consumer 从 scripts 升格 production path | `OBSERVED` 仅 harness | `OPEN` | **implementation question under P20**（升格 vs 书面永久旁路未裁定） |
| OD-V3-20 | Artifact package / publication contract 实现 | `DECISION` 仅定义 | `OPEN` | **implementation question**；Contract §13 不实现 |

---

## E. Post-Admission Enrichment

| ID | 项 | 现状 | 状态 | 裁决 / 备注 |
|---|---|---|---|---|
| OD-V3-21 | explanation 是否永远 optional | `OBSERVED` | `OPEN` | **依赖未来 Frozen**。P15 = **Explanation 生成与覆盖专属规则**（只补**缺失** detailed explanation；已有不生成不覆盖），**不**定义 Post-Admission 全部范围；Derived Metadata 可另走 §8.1 A。optional 与否属 Frozen 层 |
| OD-V3-22 | Preprocessing vs generated 展示优先级 | `OBSERVED` | `OPEN` | **implementation / display policy**。P16 已裁 authority 归属（generated = AITutors-v3 Derived Enrichment，非 Source/Preprocessing Authority），展示优先级未裁定 |
| OD-V3-23 | validation 自动规则清单 | `OBSERVED` | `OPEN` | **implementation question**。P17 已裁链路（MIMO generate → DeepSeek validate），规则清单未裁定 |
| OD-V3-24 | retry / budget / backoff | `OBSERVED` | **`OWNER DECISION COMPLETE (P19)`** + `OPEN`(残项) | P19 已裁：**最多一次 retry；第二次 validation failure → `suspended`；禁止无限 retry**。budget / backoff = `OPEN`（implementation） |
| OD-V3-25 | enrichment jobs 持久化 schema | `OBSERVED` | `OPEN` | **implementation / schema**；DB schema 明令本任务禁改 |
| OD-V3-26 | identity hash 是否排除 generated 字段 | `OPEN` | `OPEN` | P03/P16/P23 已界定 authority 与 hash 语义（`source_content_sha256` = Source Content Identity；`derived_text_hash` 独立），但 **Question identity hash 的排除规则**未被 P01–P25 明文裁定 |

---

## F. 治理 / 流程

| ID | 项 | 现状 | 状态 | 裁决 / 备注 |
|---|---|---|---|---|
| OD-V3-27 | v0.3 是否进入 Freeze Candidate | `DECISION` | **`OWNER DECISION COMPLETE`** | 本轮已形成 **CONTRACT FREEZE CANDIDATE**；**冻结令仍属 Owner**，本文件不宣布冻结 |
| OD-V3-28 | 与 X2.x / Migration Gate / X3 关系 | — | **`OWNER DECISION COMPLETE (P25)`** | v0.3 **非迁移授权**、**非 X3 入场**；v0.3 ≠ Frozen Spec 时 → STOP + 记录 conflict + 等 Owner |
| OD-V3-29 | 跨仓 Decision 编号统一 | `OBSERVED` 累积撞号 | `OPEN` | **治理流程题**，未被 P01–P25 裁定（v0.2 已记 3 处；另有本文件 P1–P5 vs P01–P25 消歧见 Contract §0） |
| OD-V3-30 | F-05-A mapping event 跨库交叉验证 | `OBSERVED` 实现缺口 | `OPEN` | **implementation question**（mapping_registry 自述） |

---

## G. 汇总计数

| 状态 | n | 说明 |
|---|---:|---|
| **`CLOSED (P04/P07/P08)`** | **3** | OD-V3-06 / 08 / 18 |
| **`OWNER DECISION COMPLETE (P##)`** | **9** | OD-V3-01 / 02 / 05 / 07 / 10 / 11 / 13 / 27 / 28 |
| `OWNER DECISION COMPLETE (P19)` + `OPEN`(残项) | 1 | OD-V3-24 |
| **`OPEN`（implementation / 未裁 / 数据观察）** | **17** | OD-V3-03 / 04 / 09 / 12 / 14 / 15 / 16 / 17 / 19 / 20 / 21 / 22 / 23 / 25 / 26 / 29 / 30 |
| **合计** | **30** | |

**Owner Decision 待裁项 = 0**（P01–P25 全部完成）。
**`OPEN` 17 项均为 implementation question / 数据观察 / 依赖未来 Frozen**，**不是** Owner Decision 欠账——本文件**未**为追求”全绿”而把实现问题伪装成 Owner Decision。

---

# OWNER DECISION STATUS: COMPLETE

*End of Open Decisions / Gaps v0.3.*
