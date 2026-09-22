# Open Decisions / Gaps v0.3 — DRAFT

> **状态**：`DRAFT` / `NON-AUTHORITATIVE` / `NOT FROZEN`
> **配套**：`PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` 全套
> **证据标签**：`OBSERVED` / `DERIVED` / `PROPOSED` / `OPEN` / `OWNER DECISION REQUIRED`
>
> 本清单**不**擅自关闭任何 Finding，**不**授权实现。

---

## A. Identity / Scope

| ID | 项 | 现状 | 状态 | 备注 |
|---|---|---|---|---|
| OD-V3-01 | v1 79 份缺 `source_content_sha256` / `identity_version` | `OBSERVED` | `OWNER DECISION REQUIRED` | Migration Gate 回填 vs 永久排除 Interface Scope |
| OD-V3-02 | REJECTED_V1（1）历史处置 | `OBSERVED` | `OPEN` | 是否可恢复 / 归档策略 |
| OD-V3-03 | raw bytes 跨机可达（OQ-12） | `OBSERVED` | `OPEN` | v0.2 冻结“能力”不冻结“传输” |
| OD-V3-04 | OCR 清单 `source_sha256`（PDF bytes）是否纳入接口 | `OBSERVED` | `OPEN`（v0.2 OQ-10） | 与 md `source_content_sha256` 语义不同，禁混用 |

---

## B. Producer 质量 / 结构

| ID | 项 | 现状 | 状态 | 备注 |
|---|---|---|---|---|
| OD-V3-05 | 16 × QC_FAIL 处理 | `OBSERVED` | `OWNER DECISION REQUIRED` | Producer 重切/重标 vs Consumer 降级 |
| OD-V3-06 | option-label evidence 粒度 | `OBSERVED` GAP | `OWNER DECISION REQUIRED` | Producer 升级 vs 接受 incomplete |
| OD-V3-07 | subquestion decomposition | `OBSERVED` GAP | `OWNER DECISION REQUIRED` | 同上 |
| OD-V3-08 | answer table mapping 502 unresolved | `OBSERVED` | `OPEN` | flags 已保留；策略未定 |
| OD-V3-09 | 596 units printed provenance unknown | `OBSERVED` | `OPEN` | 保持 UNKNOWN |
| OD-V3-10 | 41 composites material/questions 同区间 | `OBSERVED` | `OPEN` | 是否重切 |
| OD-V3-11 | `andalone_question`（1）清理 | `OBSERVED` | `OPEN` | 运行时已 fail closed；corpus 未改（本任务禁改） |

---

## C. Canonicalization / Vocabulary

| ID | 项 | 现状 | 状态 | 备注 |
|---|---|---|---|---|
| OD-V3-12 | QT closed-set enforcement 未接线 | `OBSERVED` | `OPEN` | Contract §5.3 |
| OD-V3-13 | `listening` 等闭集外值 | `OBSERVED` | `OWNER DECISION REQUIRED` | 扩集 / unsup / 映射 |
| OD-V3-14 | mapping_registry vs boundary.normalize_unit_type 双权威 | `OBSERVED` | `OWNER DECISION REQUIRED` | 唯一 runtime authority |
| OD-V3-15 | Gate grammar / auto_approve（NEW-F3） | `OBSERVED` | `OWNER DECISION REQUIRED` | 实现 grammar 映射 vs 书面废止 auto |

---

## D. Consumer Boundary / Runner

| ID | 项 | 现状 | 状态 | 备注 |
|---|---|---|---|---|
| OD-V3-16 | `runner.py` 缺 M1–M5（NEW-F1） | `OBSERVED` | `OWNER DECISION REQUIRED` | 删除 / 硬阻断 / 对齐 B2 |
| OD-V3-17 | batch resolver IR 分发（NEW-F2） | `OBSERVED` | `OWNER DECISION REQUIRED` | 升格 versioned artifact vs 路径约定 |
| OD-V3-18 | flags / basis / answer_evidence 进 Gate 或 review | `OBSERVED` CONSUMER GAP | `OWNER DECISION REQUIRED` | |
| OD-V3-19 | preprocessing_consumer 从 scripts 升格 production path | `OBSERVED` 仅 harness | `OWNER DECISION REQUIRED` | 或书面永久旁路 |
| OD-V3-20 | Artifact package / publication contract 实现 | `PROPOSED` 仅定义 | `OPEN` | Contract §13 不实现 |

---

## E. Post-Admission Enrichment

| ID | 项 | 现状 | 状态 | 备注 |
|---|---|---|---|---|
| OD-V3-21 | explanation 是否永远 optional | `PROPOSED` | `OPEN` | 依赖未来 Frozen |
| OD-V3-22 | producer vs generated 展示优先级 | `PROPOSED` | `OPEN` | |
| OD-V3-23 | validation 自动规则清单 | `PROPOSED` | `OPEN` | |
| OD-V3-24 | retry / budget / backoff | `PROPOSED` 边界 | `OPEN` | |
| OD-V3-25 | enrichment jobs 持久化 schema | `PROPOSED` | `OWNER DECISION REQUIRED` | DB schema 禁本任务改 |
| OD-V3-26 | identity hash 是否排除 generated 字段 | `OPEN` | `OPEN` | 对齐 OQ-1 / identity projection |

---

## F. 治理 / 流程

| ID | 项 | 现状 | 状态 | 备注 |
|---|---|---|---|---|
| OD-V3-27 | v0.3 是否进入 Freeze Candidate | `DRAFT` | `OWNER DECISION REQUIRED` | 本文件 NOT FROZEN |
| OD-V3-28 | 与 X2.x / Migration Gate / X3 关系 | — | `OWNER DECISION REQUIRED` | 本文件非迁移授权、非 X3 入场 |
| OD-V3-29 | 跨仓 Decision 编号统一 | `OBSERVED` 累积撞号 | `OPEN` | v0.2 已记 3 处 |
| OD-V3-30 | F-05-A mapping event 跨库交叉验证 | `OBSERVED` 实现缺口 | `OPEN` | mapping_registry 自述 |

---

## G. 汇总计数

| 状态 | n |
|---|---|
| `OWNER DECISION REQUIRED` | 14 |
| `OPEN` | 16 |
| **合计** | **30** |

*End of Open Decisions / Gaps v0.3 DRAFT.*
