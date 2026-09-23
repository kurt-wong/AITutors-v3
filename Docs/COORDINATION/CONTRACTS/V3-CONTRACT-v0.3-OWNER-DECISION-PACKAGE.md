# V3-CONTRACT-v0.3-OWNER-DECISION-PACKAGE

> **OWNER DECISION DOCUMENT**
> **NON-AUTHORITATIVE**
> **NO CODE AUTHORIZATION**
> **NO MIGRATION AUTHORIZATION**
> **NO X3 ENTRY AUTHORIZATION**
>
> **状态**：`PACKAGE` / `NOT FROZEN` / ~~`AWAITING OWNER RULING`~~ → **`OWNER DECISIONS P01-P25: COMPLETE`**
>
> ---
>
> ## 本轮状态说明（治理历史证据；**不得删除历史记录**）
>
> ```text
> OWNER DECISIONS P01-P25: COMPLETE
> IMPLEMENTATION: NOT AUTHORIZED BY THIS DOCUMENT ALONE
> ```
>
> - 本文件保留为**治理历史证据**：OD-P01–OD-P25 的原始 Question / Observed Facts / Options / Decision Required 栏**全部原样保留**，不回填、不改写、不删除。
> - **正式裁决落版**见 `PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` **§1b（Owner Decisions P01–P25）**；该文件现为 `CONTRACT FREEZE CANDIDATE`。
> - **P04 = CLOSED**（Choice Question per-option structured evidence）· **P07 = CLOSED**（`answer_table_unresolved` 最终处置）· **P08 = CLOSED**（Evidence / Flags 保留）。
> - **本文件本身不授权任何实现**：无 production code / schema / migration / corpus rerun / artifact rewrite 授权。
> - 术语按 Contract §0 规范：`Preprocessing` = `kurt-wong/Aitutors-preprocessing`；`AITutors-v3` = 当前 V3 系统；`Legacy Preprocessing Artifact (V1 format)` = 历史产物格式；`Producer` **仅**作抽象架构角色。
>
> ---
>
>
> **用途**：将已完成的 Contract + Feasibility Analysis 转换为可逐项裁决的架构决策包。本文件**不替 Owner 做任何架构选择**，**不推荐 Option**，**不修改** production code / tests / schema / Frozen Spec / Frozen Contract / v0.3 Contract / preprocessing / corpus / X3 状态。
>
> **上游材料**：
> - `PREPROCESSING-V3-CONTRACT-v0.3-DRAFT.md` 等五件套 @ `968943f`
> - `V3-CONTRACT-v0.3-IMPLEMENTATION-FEASIBILITY-ANALYSIS.md` @ `b34b618`
> - `PREPROCESSING-V3-OPEN-DECISIONS-v0.3-DRAFT.md`
> - Frozen Spec `Docs/V3_SPEC/00–50`
> - `Docs/40_DECISIONS/X2.6-OD-2-MAPPING-AUTHORIZATION.md`（Owner Closure 2026-09-21）
> - Consumer Identity M1–M5 Design v1.1
> - 相关 production code / tests / X2.7 reports（仅在 Decision 依赖事实冲突时回查）
>
> **Security（逐字）**：Never hardcode API Keys/Passwords/Tokens/Secrets; Always use .env for configuration.

---

## 0. How to Use This Package

1. 先看 §1 Decision Index（唯一 ID 全表）与 §2 Dependency Graph（先裁谁）。
2. 按 Cluster 拍板；每个 Decision 使用统一模板填写 `Decision Required / OWNER:` 空白栏。
3. §3 列出**假决策 / 已降级项**——这些**不要**当 Owner 架构题再答一遍。
4. §4 列出 **Frozen Conflict**——涉及 Frozen 的项，Contract DRAFT **不能**当作已覆盖 Frozen。
5. 裁决落盘时请另写 Owner Decision Event ID；**本包本身不创建事件**。

**模板说明**：每项含 Question / Observed Facts / Current Contract / Frozen Constraint / Current Code / Dependency / Option A|B|C（各带 Direct / Code / Schema / Contract / Frozen consequence）/ Decision Required。**无 Recommendation 字段。**

---

## 1. Decision Index（最终唯一列表）

### 1.1 计数

| 类别 | n |
|---|---|
| **本包唯一 Owner Decision（OD-P01…OD-P25）** | **25** |
| 从原清单降级 / 剔除（假决策或非架构 Owner 题） | 8 |
| 原 `OWNER DECISION REQUIRED`（14）并入本包 | 14（映射见 1.3） |
| 原 `OPEN` 中升为 Owner 架构题 | 6 |
| 可行性分析新增（NEW-01…06）并入 | 6 |

### 1.2 唯一 ID 索引

| ID | 标题 | Cluster | 映射自 |
|---|---|---|---|
| OD-P01 | Interface Scope 成员：v1 身份与 REJECTED_V1 | A | OD-V3-01, OD-V3-02 |
| OD-P02 | 16× QC_FAIL 的消费面政策 | A | OD-V3-05 |
| OD-P03 | 跨机 raw bytes 可达性与 OCR PDF identity face | A | OD-V3-03, OD-V3-04 |
| OD-P04 | option-label evidence 粒度 | B | OD-V3-06 |
| OD-P05 | subquestion decomposition | B | OD-V3-07 |
| OD-P06 | material/questions 同区间折叠 | B | OD-V3-10 |
| OD-P07 | answer-table 502 unresolved 策略 | B | OD-V3-08 |
| OD-P08 | flags / basis / answer_evidence 的消费去向 | B | OD-V3-18 |
| OD-P09 | Unit Type mapping 的唯一 runtime authority | C | OD-V3-14 |
| OD-P10 | QT 闭集外值（含 `listening`） | C | OD-V3-13 |
| OD-P11 | v0.2 UT 词面与 OD-2 canonical 词面消歧 | C | NEW-05 |
| OD-P12 | Gate grammar / auto_approve 产品策略 | D | OD-V3-15 |
| OD-P13 | `verified_correct=True` 物化的审计语义 | D | NEW-02 |
| OD-P14 | `answer_lines or answer_evidence_lines` fallback | D | NEW-04 |
| OD-P15 | Generated explanation 与 Frozen 边界 | E | NEW-01, 残余 OD-V3-21 |
| OD-P16 | Enrichment jobs 持久化 schema | E | OD-V3-25 |
| OD-P17 | ValidationEvent generation provenance | E | NEW-06 |
| OD-P18 | producer vs generated 展示优先级 | E | OD-V3-22 |
| OD-P19 | identity hash 是否排除 generated 字段 | E | OD-V3-26 |
| OD-P20 | `runner.py` 处置 | F | OD-V3-16 |
| OD-P21 | `preprocessing_consumer` 生产路径地位 | F | OD-V3-19 |
| OD-P22 | batch IR 分发与 Artifact package | F | OD-V3-17, OD-V3-20 |
| OD-P23 | v0.3 是否进入 Freeze Candidate | F | OD-V3-27 |
| OD-P24 | 与 X2.x / Migration Gate / X3 关系 | F | OD-V3-28 |
| OD-P25 | text hash family 一致性 | F | NEW-03 |

### 1.3 原 OD-V3-01…30 映射

| 原 ID | 处置 | 新 ID |
|---|---|---|
| OD-V3-01 | 并入 | OD-P01 |
| OD-V3-02 | 并入 | OD-P01 |
| OD-V3-03 | 并入 | OD-P03 |
| OD-V3-04 | 并入 | OD-P03 |
| OD-V3-05 | 保留为 | OD-P02 |
| OD-V3-06 | 保留为 | OD-P04 |
| OD-V3-07 | 保留为 | OD-P05 |
| OD-V3-08 | 保留为 | OD-P07 |
| OD-V3-09 | **降级**（见 §3） | — |
| OD-V3-10 | 保留为 | OD-P06 |
| OD-V3-11 | **降级**（见 §3） | — |
| OD-V3-12 | **降级**（见 §3） | — |
| OD-V3-13 | 保留为 | OD-P10 |
| OD-V3-14 | 保留为 | OD-P09 |
| OD-V3-15 | 保留为 | OD-P12 |
| OD-V3-16 | 保留为 | OD-P20 |
| OD-V3-17 | 并入 | OD-P22 |
| OD-V3-18 | 保留为 | OD-P08 |
| OD-V3-19 | 保留为 | OD-P21 |
| OD-V3-20 | 并入 | OD-P22 |
| OD-V3-21 | **降级为主**；残余并入 | OD-P15 |
| OD-V3-22 | 保留为 | OD-P18 |
| OD-V3-23 | **降级**（见 §3） | — |
| OD-V3-24 | **降级**（见 §3） | — |
| OD-V3-25 | 保留为 | OD-P16 |
| OD-V3-26 | 保留为 | OD-P19 |
| OD-V3-27 | 保留为 | OD-P23 |
| OD-V3-28 | 保留为 | OD-P24 |
| OD-V3-29 | **降级**（见 §3） | — |
| OD-V3-30 | **降级**（见 §3） | — |
| NEW-01 | 保留为 | OD-P15 |
| NEW-02 | 保留为 | OD-P13 |
| NEW-03 | 保留为 | OD-P25 |
| NEW-04 | 保留为 | OD-P14 |
| NEW-05 | 保留为 | OD-P11 |
| NEW-06 | 保留为 | OD-P17 |

---

## 2. Decision Dependency Graph

### 2.1 文本图

```text
Cluster F（入口治理，宜先裁）
OD-P21 ──先于──► OD-P20
   │
   ├──► 解锁：Producer→V3 统一 M1–M5+Scope 接线（实现授权另议）
   │
OD-P25（hash 族）──可与 P21 并行──► Adapter/boundary 对齐
OD-P22（IR/Artifact 分发）──依赖──► OD-P21（路径地位定后）
OD-P23（v0.3 Freeze）──依赖──► 建议在 A–E 簇决策基本闭合后
OD-P24（X3/Migration）──可并行于实现簇；冻结/迁移授权独立

Cluster A（Producer 身份 / 质量）
OD-P01 ──独立──► Scope 成员工具/清单
OD-P02 ──独立──► QC_FAIL 消费面
OD-P03 ──可与 P01 并行──► 传输/OCR face
  （P01 先于任何“扩大接口面”的实现）

Cluster B（证据保真）——多题可并行
OD-P04 ─┐
OD-P05 ─┼─ 可并行 ──► Producer 升级 或 Consumer unsup 策略
OD-P06 ─┤
OD-P07 ─┘
OD-P08 ──依赖──► OD-P07（answer_evidence 策略）但主要可独立
           └──► 解锁：flags/basis 进 Gate 或 review 的实现设计

Cluster C（词表）
OD-P11 ──先于或同批──► OD-P09
           │
           ├──► 唯一 mapping runtime authority 接线
           │
OD-P10 ──先于──► QT closed-set boundary 实现（原 OD-12，非 Owner 题）
           └──► listening 扩集若选择，可能触发 Frozen QT 变更（见 §4）

Cluster D（Gate）——相对独立
OD-P12 ──受 Frozen STRICT_AUTO 约束（§4）──► auto 策略书面化
OD-P13 ──独立──► 审计/展示语义（通常无 schema 变更）
OD-P14 ──独立──► runner_b2 答案源 fallback

Cluster E（Enrichment）——严格串行主链
OD-P15 ──必须先裁──► OD-P16 ──► OD-P17 ──► OD-P18
   │                      │
   │                      └──► OD-P19（identity 与 generated 正交）
   │
   ├──► 若选“属 00§5 非目标”则 PAE 主链 BLOCKED，需 Frozen 变更提案
   └──► 若选“不属非目标 / 或需 errata”则 P16 schema 才可进入 migration 立项
```

### 2.2 裁决批次建议（非推荐选项，仅为减依赖的排序事实）

| 批次 | 决策 | 理由 |
|---|---|---|
| 批次 1（可并行） | P21, P25, P11, P01, P02, P13, P14, P12 | 低依赖，不卡实现簇根 |
| 批次 2 | P20（←P21）, P09（←P11）, P10, P08, P04–P07, P03 | 解锁 boundary/Gate 信号与 Producer 策略 |
| 批次 3 | P15 → P16 → P17 → P18 → P19 | Enrichment 主链严格依赖 |
| 批次 4 | P22（←P21）, P23（建议在 1–3 后）, P24 | 分发与治理收口 |

### 2.3 同簇决策簇（可一次会话打包答）

- **簇 A 身份/质量**：P01 + P02 + P03
- **簇 B Producer 结构**：P04 + P05 + P06 + P07（+ P08 策略向）
- **簇 C 词表**：P11 + P09 + P10
- **簇 D Gate**：P12 + P13 + P14
- **簇 E Enrichment**：P15 单独必须先拍；随后 P16+P17+P18+P19
- **簇 F 路径治理**：P21 → P20；P22/P23/P24 收口

---

## 3. 假决策 / 降级项（不作为 Owner 架构题）

下列原清单项经核验后**剔除或降级**。理由只陈述事实，不替 Owner 做新架构选择。

| 原 ID | 处置 | 理由 |
|---|---|---|
| OD-V3-09 printed provenance unknown | **降级为已决** | v0.3 IPM / SAM / Open Decisions 备注已写明「保持 UNKNOWN」；P1 禁止 unknown→source_line。残留工作 = 实现层把 `printed_provenance` 带入保真通道（并入 OD-P08 实现范围），**无新架构二选一**。 |
| OD-V3-11 `andalone_question` corpus | **降级** | 运行时已 fail-closed（OD-1 / `normalize_unit_type` / IR 闭集）。corpus 清理属 **Producer implementation**，且 V3 任务禁改 corpus。非 V3 Owner 架构题；若将来要改语料，走 Producer/治理流程另案。 |
| OD-V3-12 QT closed-set enforcement 未接线 | **降级为实现** | 决策本体是 OD-P10（闭集外值如何处置）。值集定了之后，boundary 接线属 `NEW IMPLEMENTATION REQUIRED`，不是独立 Owner 题。 |
| OD-V3-21 explanation 是否永远 optional | **降级为 Frozen 已决** | Frozen 20 §6.3：12 型 explanation 全为 `optional`；代码 `content_roles_for` 一致。v0.3 PAE 不改变 Frozen。**仅当** Owner 拟将 explanation 升为 hard requirement 时，才构成 **Frozen amendment 提案**（超出本包“在现行 Frozen 内裁决”范围；残余解释性问题并入 OD-P15 的 Frozen 约束说明）。 |
| OD-V3-23 validation 自动规则清单 | **降级为实现** | 依赖 OD-P15/P16/P17 落地后的规则细节；PAE §5 已给 `PROPOSED` 最小集。属实现与测试选择，不单独作为架构二选一。 |
| OD-V3-24 retry / budget / backoff | **降级为工程配置** | Frozen 30 §3/§7 已定：failed 无自动出口；retry 语义二分已有边界；Budget 五账户已存在。backoff/次数属实现配置。若要“无限自动重试”才会撞 Frozen——那将是 Frozen 冲突而非本题。 |
| OD-V3-29 跨仓 Decision 编号统一 | **降级为流程** | 编号统一是治理记账，不改变架构语义；v0.2 已记 3 处撞号。 |
| OD-V3-30 F-05-A mapping event 交叉验证 | **降级为实现** | 依赖 OD-P09 唯一权威选定后的接线工作；`mapping_registry` 已自述该缺口。 |

**以上 8 项不得再计入 “最终唯一 Owner Decision 数量”。**

---

## 4. Frozen Conflict Register（Contract DRAFT ≠ 覆盖 Frozen）

| # | 主题 | Frozen authority（明文） | Contract proposed change | Owner action required |
|---|---|---|---|---|
| FC-1 | **Live text / generated explanation 落点** | **10 §1.1**：LLM 输出永远是 C 域 annotation，不是 live 文本；`instance_role_contents.text` 不来自 LLM | PAE 允许 post-admission 生成 explanation 并持久化到 Question 槽 | 判定生成物落点必须为 **独立 V3D/AI-Generated 槽**（非 role_contents）；并裁决是否与 00 §5 非目标冲突（OD-P15） |
| FC-2 | **00 §5 复杂统计富化 = M1 非目标** | **00 §5**：复杂统计富化不阻塞 M1 / 非目标 | PAE §1/§8 把 explanation 生成列为 PROPOSED 目标 | OD-P15：是否将 explanation 生成解释为「属/不属」该非目标；若属，PAE 需 Frozen 变更/errata，**不能**在 DRAFT 内视为可实现 |
| FC-3 | **ADMISSION Authority** | **00 P3 + 20 §8**：Derived 无 provenance 不得伪装 Source-derived 进 approved；approved answer 三字段规则 | SAM V3D/EVD 分层；PAE 禁止生成物冒充 Producer | 实现必须遵守 Frozen；OD-P13/P15/P17 只决定 **如何标注**，不决定是否可绕过 Frozen |
| FC-4 | **STRICT_AUTO / grammar** | **20 §8.4（BUG-V3-023）**：`STRICT_AUTO_TYPES` 仅 3 型；禁为其余 9 型编造 grammar | OD-V3-15/OD-P12 讨论 auto 策略 | 若 Owner 要扩大 auto 覆盖 9 型 → **Frozen 变更**；若书面承认其余恒 pending_review → 与 Frozen 一致，属产品策略书面化 |
| FC-5 | **QT 闭集** | **20 §6.3 / §7.2**：12 型 closed-set；exact passthrough；禁 alias | OD-P10：`listening` 等如何处置 | 扩闭集 = Frozen/Display 契约变更；标 unsup/rejected = 现行 Frozen 内合法 |
| FC-6 | **Unit Type canonical** | **20 §4.5 + Owner D1**：canonical = `{standalone_unit, composite_unit}`；禁 legacy 作 canonical | OD-2 legacy→canonical **boundary normalization**（非 QT→UT） | OD-P09/P11 选择的是 **runtime 权威挂哪** 与 **v0.2 词面记账**，**不得**改写 D1/OD-2 已授权词面 |
| FC-7 | **Post-admission derived 数据** | **10 §2**：post-admission 派生 = 显式 Repository 步骤，不得回改已提交内容行 | PAE 异步 enrichment | P16/P17 schema 必须表现为独立步骤 + 追加，不 UPDATE 掉 PRD 行 |
| FC-8 | **Knowledge optional** | **10 §6.7**：Knowledge = optional derived，非 admission 硬依赖 | PAE knowledge_generated | 与 Frozen 一致；写路径实现不构成 Frozen 冲突 |
| FC-9 | **explanation optional** | **20 §6.3**：optional | PAE「禁止因缺 explanation 拒入库」 | 与 Frozen 一致；见 §3 OD-V3-21 降级 |

**纪律**：在未获得 Frozen 变更/errata 授权前，任何 Option 若直接违反上表 Frozen authority，该 Option 的 Frozen consequence 必须写明 **BLOCKED / 需 Frozen amendment**。

---

# Decision Bodies

---

## OD-P01 — Interface Scope 成员：v1 身份与 REJECTED_V1

### Question
Interface Scope 内如何处置 `identity_version` 非 2 的 Producer 资产（约 79 份 v1 manifest）与既往 REJECTED_V1（1）？

### Observed Facts
- FACT-01：Interface Scope 字段口径 = `identity_version==2` 且 `source_content_sha256` 合法（Frozen Contract / v0.2 继承项；`enforce_interface_scope`）。
- FACT-02：v1 face 缺 `source_content_sha256` / `identity_version`（`OBSERVED` 可行性/Open Decisions）。
- FACT-03：REJECTED_V1 = 1，已在 88 条 resolver_ir 记录外或历史拒收语境（`OBSERVED`）。
- FACT-04：v0.2 ⑤「16 项 Identity-only recovery」与路径≠identity 已冻结候选语义，v0.3 声明继承不改写。

### Current Contract
v0.3 继承 Scope 87/71/16；v1 不得 silent 升为 v2（P4 / P5）。

### Frozen Constraint
v0.2 冻结候选 identity/Scope 项（若已按 v0.2 冻结口径执行，则 Scope 收缩为身份面变更，须与 migration gate 关系一并考虑——见 OD-P24）。Frozen V3_SPEC 本身不定义 preprocessing v1/v2 面。

### Current Code
`scripts/preprocessing_consumer/boundary.enforce_interface_scope`：v1 → `OUT_OF_SCOPE_IDENTITY_VERSION` 拒绝。

### Dependency
OD-P24（若选择回填，可能触达 Migration Gate 叙事）；不阻塞 OD-P04–P08。

### Option A
永久排除非 v2 于 Interface Scope；仅文档披露 79+1 历史。

Direct consequence:
接口面维持 87（v2）口径不变；无回填工程。

Code consequence:
现 Scope 逻辑可保持；需文档/报表披露清单。

Schema consequence:
无。

Contract consequence:
与 v0.2 Scope 冻结兼容；Open Decisions OD-01/02 关闭为「排除」。

Frozen consequence:
不触碰 Frozen V3 Spec；若 v0.2 Scope 冻结项已冻，则一致。

### Option B
Migration Gate 路径回填 v2 身份字段后按 Scope 成员处理（回填本身另需 migration/gate 授权）。

Direct consequence:
历史资产可能重新进入消费面；须防 silent upgrade。

Code consequence:
新增回填工具与 M1–M5 重验；Scope 判定在回填后。

Schema consequence:
manifest 数据修订（Producer/迁移侧），非 V3 DB schema 直接变更。

Contract consequence:
需在 Contract 写清「回填 ≠ 改 identity 语义」；依赖 OD-P24。

Frozen consequence:
不改 V3 Frozen Spec；但可能触及 v0.2 冻结 Scope 叙事与 Migration Gate 程序。

### Option C
分档：仅 QC 可恢复子集回填，其余永久排除。

Direct consequence:
接口面部分扩大；处置矩阵变复杂。

Code consequence:
回填 + 分档白名单；测试面增大。

Schema consequence:
同 B（Producer/迁移侧）。

Contract consequence:
需增补分档规则表。

Frozen consequence:
同 B 的程序依赖。

### Decision Required
OWNER:
________________

---

## OD-P02 — 16× QC_FAIL 的消费面政策

### Question
Producer `qc_verdict=FAIL` / `disposition` 非 ADMITTED 的 16 份资产，在 Consumer 侧如何处置？

### Observed Facts
- FACT-01：Interface Scope = 87 = 71 ADMITTED + 16 QC_FAIL/semantic pending（`OBSERVED`）。
- FACT-02：v0.3 P5：Producer ADMITTED ≠ V3 APPROVED；QC_FAIL 不得被读成 PASS。
- FACT-03：当前 consumer **未读取** flags/qc（可行性 §3）——FAIL 在消费面不可见。

### Current Contract
IPM：`qc_verdict` / `disposition` = `pres`；QC_FAIL → 非 ADMITTED 不进语义消费面（`OBSERVED` 表述）。

### Frozen Constraint
NONE（V3 Spec 不定义 preprocessing QC 枚举处置）。

### Current Code
Consumer 无 QC 闸门；是否进入 adapter 取决于上层是否喂入这些 manifest。

### Dependency
与 OD-P08 相关（字段要先进得来）；独立于 QT/Grammar。

### Option A
Consumer 强制：非 ADMITTED → 显式 block/skip（类 Scope 拒绝）。

Direct consequence:
16 份不进 IR/Gate。

Code consequence:
Scope 旁路或后置 QC gate；读 qc 字段。

Schema consequence:
无 V3 DB 变更。

Contract consequence:
把 IPM「不进消费面」写成运行闸。

Frozen consequence:
NONE。

### Option B
允许进入但全程 `retained_as_uncertainty` + 强制 pending_review（不 auto）。

Direct consequence:
16 份可见但仍不可 auto_approve（若另有过 Gate 路径）。

Code consequence:
flags/qc 进 payload + Gate/review（依赖 OD-P08）。

Schema consequence:
无（或仅 payload 扩展）。

Contract consequence:
与「不进 ADMITTED 消费面」字面需对齐（若消费面=语义消费，需澄清语义）。

Frozen consequence:
NONE。

### Option C
Producer 重切/重标后再按 v2 进 Scope（消费面暂不含 16）。

Direct consequence:
V3 侧最小改动；等待 Producer。

Code consequence:
V3 可不改；Producer 工程另案。

Schema consequence:
无。

Contract consequence:
记录「等待重标」状态。

Frozen consequence:
NONE。

### Decision Required
OWNER:
________________

---

## OD-P03 — 跨机 raw bytes 可达性与 OCR PDF identity face

### Question
（1）`source_content_sha256` 对应 raw bytes 的跨机传输是否纳入接口义务？（2）OCR/PDF 的 `source_sha256`（PDF bytes）是否纳入同一接口，或与 md 面严格分面？

### Observed Facts
- FACT-01：v0.2 冻「raw bytes 能力」不冻「传输」（OQ-12 语境）。
- FACT-02：PDF bytes hash 与 md `source_content_sha256` 语义不同（Open Decisions 禁混用备注）。
- FACT-03：M2 = `hashlib.sha256(raw bytes)`，禁 text 规范化（tests AST 强制）。

### Current Contract
v0.2 ⑥ Source bytes capability 继承；OD-V3-03/04 原 OPEN。

### Frozen Constraint
V3 Spec 对 seal 层 PDF identity 另有 figure/source 模型；**不**自动等同 preprocessing md 接口键。

### Current Code
M2 可读本地文件；无跨机协议实现。

### Dependency
OD-P01；OD-P22（artifact 包可携带 bytes 引用）。

### Option A
接口义务 = 提供 bytes **能力**（可本地 M2）；不规定跨机协议；OCR hash 分面登记、不并入 md Scope 键。

Direct consequence:
Scope 键保持单一 md 语义；传输非契约。

Code consequence:
文档化；无强制传输层。

Schema consequence:
无。

Contract consequence:
关闭 OQ-12 为「能力非传输」。

Frozen consequence:
NONE。

### Option B
Artifact package 强制携带可校验 bytes（或 bytes 密钥），M2 跨机必达。

Direct consequence:
分发变重；M2 在消费机可重算。

Code consequence:
package 校验逻辑；依赖 OD-P22。

Schema consequence:
package schema（若新建）。

Contract consequence:
扩展 v0.2 能力→义务。

Frozen consequence:
NONE。

### Option C
双接口：md Scope + 独立 OCR/PDF identity face（不同键名、禁混用），各自成员表。

Direct consequence:
两个 identity 面并行治理。

Code consequence:
第二套 Scope 函数/字段（须避免双权威叙事）。

Schema consequence:
OCR 清单字段治理。

Contract consequence:
接口合同分面章节。

Frozen consequence:
不改 md 键语义；PDF face 需单独合同措辞。

### Decision Required
OWNER:
________________

---

## OD-P04 — option-label evidence 粒度

### Question
Producer 是否升级为 per-option-label 行锚/证据；若否，Consumer 是否永久接受 options 整块 span + `OPTION_LABEL_SPAN_UNAVAILABLE`？

### Observed Facts
- FACT-01：现仅 `options_lines` 整块；adapter 登记 `OPTION_LABEL_SPAN_UNAVAILABLE`（`OBSERVED`）。
- FACT-02：选择题 auto 路径依赖 option label 集合（grammar / labels）。
- FACT-03：Producer Gap ≠ V3 bug（可行性 §12）。

### Current Contract
IPM：per-label 缺 = `unsup`，须登记 GAP；禁 fabricate A/B/C。OD-V3-06 = OWNER。

### Frozen Constraint
NONE（不改 QT/AnswerToken；label 质量属 Producer 证据）。

### Current Code
`resolved_span_adapter` / `runner_b2` options 单 span；`runner_b3` 为 label 实验非生产。

### Dependency
与 OD-P12（auto 范围）相关；不阻塞 Scope。

### Option A
Producer 升级 per-label 证据后再消费。

Direct consequence:
Consumer 可接 label 级 span；grammar 证据更稳。

Code consequence:
Producer 改造 + adapter 解析升级。

Schema consequence:
manifest 粒度（Producer 侧）。

Contract consequence:
IPM 从 unsup 升为 pres/canon 路径。

Frozen consequence:
NONE。

### Option B
接受整块 span；label 级不进 V3；choice auto 保持受限（与现行 pending_review 一致处继续）。

Direct consequence:
无 Producer 改造；IPM unsup 为终态策略。

Code consequence:
仅登记与文档；不改 IR 形状。

Schema consequence:
无。

Contract consequence:
明确 unsup 为持久策略。

Frozen consequence:
NONE。

### Option C
双轨：历史卷整块；新切 per-label（版本化 artifact）。

Direct consequence:
两代 manifest 规则。

Code consequence:
版本分支。

Schema consequence:
两代 producer version。

Contract consequence:
分版本条款。

Frozen consequence:
NONE。

### Decision Required
OWNER:
________________

---

## OD-P05 — subquestion decomposition

### Question
多小题是否由 Producer 真实拆分为多 sub IR 节点；否则是否永久 `SUB_QUESTION_DECOMPOSITION_UNAVAILABLE`？

### Observed Facts
- FACT-01：现 1:1 单 sub + gap（`annotation_adapter`）。
- FACT-02：54/148 multi-q 缺部分印刷题号在 questions 区（`OBSERVED`）。
- FACT-03：IPM 要求显式 unsup，非 silent。

### Current Contract
IPM / OD-V3-07；与 P1 可逆性相关。

### Frozen Constraint
NONE；composite IR 形状已 Frozen（sub_questions[] 已存在），缺的是 Producer 拆分质量。

### Current Code
adapter 折叠单 sub；IR 支持多 sub 结构。

### Dependency
OD-P06（同区间结构）；OD-P04 可并行。

### Option A
Producer 拆分升级。

Direct consequence:
V3 IR 多 sub 充实；material_dependency 更真实。

Code consequence:
adapter 读取多 sub；测试扩。

Schema consequence:
manifest 结构（Producer）。

Contract consequence:
gap 关闭。

Frozen consequence:
NONE。

### Option B
接受折叠 + 显式 gap 为终态。

Direct consequence:
子题粒度永久损失但非 silent。

Code consequence:
维持现 adapter + 登记。

Schema consequence:
无。

Contract consequence:
IPM unsup 固化。

Frozen consequence:
NONE。

### Option C
V3 侧再解析 questions_lines 为多 sub（V3-derived）。

Direct consequence:
出现 V3 再发现，与「不重复 Fact Discovery」基线张力。

Code consequence:
新解析器（V3 内）。

Schema consequence:
payload/IR 补充。

Contract consequence:
需改写 §2.1「不做重复题发现」边界或标 V3D。

Frozen consequence:
20 层间不补语义条款可能冲突 → 须谨慎表述。

### Decision Required
OWNER:
________________

---

## OD-P06 — material/questions 同区间折叠

### Question
41 个 composite 上 `material_lines == questions_lines` 是否重切，或接受为 known structural fold？

### Observed Facts
- FACT-01：41 composites 同区间（`OBSERVED`）。
- FACT-02：IPM：flag/known fold 保留；禁 silent 合并语义。

### Current Contract
IPM C 区 material/questions；OD-V3-10 OPEN 升为本包 Owner。

### Frozen Constraint
NONE。

### Current Code
行锚来自 manifest；无自动重切。

### Dependency
OD-P05 相关可并行。

### Option A
Producer 重切。

Direct consequence:
material vs questions 分离；composite 语义更清晰。

Code consequence:
等 Producer；V3 可暂维持。

Schema consequence:
manifest。

Contract consequence:
gap 关闭。

Frozen consequence:
NONE。

### Option B
接受 fold + 显式 known_gaps 标记（并入保真通道，见 OD-P08）。

Direct consequence:
无重切；下游可见 fold。

Code consequence:
gap 字段进 payload/evidence。

Schema consequence:
无/轻量 payload。

Contract consequence:
IPM 登记为保留策略。

Frozen consequence:
NONE。

### Option C
仅对影响 material_dependency 校验失败的子集重切。

Direct consequence:
按 Gate 失败驱动的最小 Producer 工作。

Code consequence:
失败清单驱动。

Schema manifest 同 A。

Contract consequence:
分档规则。

Frozen consequence:
NONE。

（schema impact：manifest）

### Decision Required
OWNER:
________________

---

## OD-P07 — answer-table 502 unresolved 策略

### Question
`answer_table_unresolved` 约 502：保持 flag 不猜，还是要求 Producer 补解析，或 V3 再解析？

### Observed Facts
- FACT-01：`answer_table_unresolved` 502（`OBSERVED`）。
- FACT-02：IPM：`answers.unresolved` = `unc`；禁填假答案。
- FACT-03：当前 consumer 不读 flags——该 flag 尚未进 V3。

### Current Contract
IPM F 区；P4 fail closed；P2 禁覆盖答案。

### Frozen Constraint
**00 §6 / 00 §7**：missing evidence 禁 guessed answer；Gate 未过不静默入库。

### Current Code
无 answer-table 消费；IR answer 依赖 annotation role + span。

### Dependency
OD-P08（flag 必须先可见）；OD-P14（answer 源）。

### Option A
保持 unresolved + 进保真/review（不进 auto）。

Direct consequence:
不猜；可能大量 pending。

Code consequence:
读 flags；Gate/review 信号（OD-P08）。

Schema:
payload 扩展可选。

Contract:
与 IPM 一致。

Frozen:
一致。

### Option B
Producer 补 answer-table 映射后再消费。

Direct consequence:
Producer 工程；V3 暂等。

Code:
V3 可不改。

Schema:
Producer。

Contract:
gap 关闭路径。

Frozen:
NONE。

### Option C
V3 确定性表解析（非 LLM）产出 candidate answer + 强制人工/auto 规则。

Direct consequence:
超出「不重复 Fact Discovery」需改写边界或标明确确定性增强。

Code:
新解析模块。

Schema:
payload。

Contract:
v0.3 §2.1 边界可能要修（需后续 Contract 修订授权，本包不改 v0.3）。

Frozen:
若无 evidence 仍禁进 approved；须带 evidence。

### Decision Required
OWNER:
________________

---

## OD-P08 — flags / basis / answer_evidence 的消费去向

### Question
上述 Producer 证据字段进入 V3 后：只保 payload/provenance，还是进 Gate 层，还是进独立 review 队列？

### Observed Facts
- FACT-01：reader 有 basis 等；adapter/span 丢；flags/qc **未读**（`OBSERVED` 可行性 §3）。
- FACT-02：IPM：flags 必须保留，丢 = violation；且现「未进 Gate」= CONSUMER GAP。
- FACT-03：OD-V3-18 = OWNER。

### Current Contract
P1/P3 强制保真；进 Gate 属 `PROPOSED` 未定。

### Frozen Constraint
NONE 直接要求 flags 进 Gate；Frozen Gate 四层**不包含** flags——故「进 Gate」是 **Gate 策略扩展**，不改 Frozen 四层结构的话应落在 pending_review **原因/人工队列**，而非发明第五层（若发明层则可能触 20 §8 结构，见 consequence）。

### Current Code
`gate/policy.evaluate` 不读 flags/basis；`manifest_reader` 读部分字段；flags 不读。

### Dependency
OD-P07；OD-P12（auto 与 pending 边界）；建议在 OD-P21 路径确定后实现。

### Option A
仅保真进 payload/evidence/provenance；Gate 决策面不读（人工在 review UI 看）。

Direct consequence:
P1/P3 可满足；auto 路径不因 flags 变复杂。

Code:
adapter 透传 + payload 字段；policy 不动。

Schema:
payload 扩展。

Contract:
关闭「必须进 Gate」为「必须可见不丢」。

Frozen:
与现四层一致。

### Option B
非空 flags/basis 非 printed_as_is → 强制 pending_review（**不改**四层，只作 auto blocker 理由）。

Direct consequence:
auto 更保守；与 P4 一致。

Code:
policy admission 层加 blocker（仍属 G 层决策语义，需确认是否算改 Gate 结构——见 Frozen consequence）。

Schema:
payload。

Contract:
OD-18 关为「进 auto 阻断」。

Frozen:
若解释为 20 §8 检查项扩展 → **需对照 Frozen 是否只允许注释内清单**；若 Frozen 检查项冻结则冲突，必须 Frozen errata。**（实现前 Owner 应确认 20 §8 检查项是否可增补。）**

### Option C
独立 review 队列（不进 Gate 层代码，出 pending_review 时附带证据清单）。

Direct consequence:
人审可见；Gate 决策逻辑尽量不动。

Code:
candidate 附加 review_payload；Gate 仍四层。

Schema:
payload。

Contract:
OD-18 关为「review 通道」。

Frozen:
四层结构不动 → 与 Frozen 较易兼容。

### Decision Required
OWNER:
________________

---

## OD-P09 — Unit Type mapping 的唯一 runtime authority

### Question
legacy UT 归一化的唯一 runtime authority 是 `mapping_registry` 接线，还是维持 `boundary.normalize_unit_type` 并降级 registry 为纯治理表？

### Observed Facts
- FACT-01：`mapping_registry.py` 自述 GOVERNANCE SCAFFOLD，生产零 import（`OBSERVED`）。
- FACT-02：`boundary.normalize_unit_type` 已实现 OD-2 两条 + andalone fail closed，harness 使用。
- FACT-03：v0.3 §9：最终只能有一个 authority；OD-V3-14 = OWNER。
- FACT-04：IR/Gate 生产对 legacy 是 **拒收**（须先 boundary），不是自动映射。

### Current Contract
v0.3 §2.3/§4.2/§9；OD-2 两条授权仍有效。

### Frozen Constraint
**D1 / 20 §4.5**：canonical 词面不变；**不**因 authority 选择而改词面。OD-2 Hard Boundary：曾禁 mapping production activation——若选择接线 registry，需 Owner 确认该禁令与现授权关系（程序性，非改 D1）。

### Current Code
见 FACT-01/02。

### Dependency
OD-P11（词面记账）应先决或同批；OD-P10 独立。

### Option A
接线 `mapping_registry` 为唯一 authority；boundary 调 registry 或迁到 registry。

Direct consequence:
治理事件 ID（OD-2 event）进入运行时；F-05-A 可内建。

Code:
production import registry；boundary 收缩或删除重复表。

Schema:
无。

Contract:
OD-14 关为 registry。

Frozen:
不改词面；须确认 OD-2 历史「禁 production activation」是否仍有效（Owner 程序确认）。

### Option B
`boundary.normalize_unit_type` 为唯一 runtime；registry 降级纯治理登记。

Direct consequence:
harness 规则上生产化；registry 不进热路径。

Code:
将 boundary 规则提升至 production 模块（供 entrypoint 共用）；registry 保持测试/文档。

Schema:
无。

Contract:
OD-14 关为 boundary。

Frozen:
不改词面。

### Option C
合并实现：registry 为数据，boundary 为门面，禁止第三份表。

Direct consequence:
单表单门面，消除重复。

Code:
重构引用关系（仍要 Owner 授权「接线」是否违反历史禁令）。

Schema:
无。

Contract:
双权威关闭为「单表+单门面」。

Frozen:
同 A 的程序确认。

### Decision Required
OWNER:
________________

---

## OD-P10 — QT 闭集外值（含 `listening`）

### Question
`original_question_type` 出现闭集外值时：扩 QT 闭集、标 explicitly_unsupported/rejected，还是 Owner 授权 per-value 映射？

### Observed Facts
- FACT-01：12 型闭集 + exact passthrough（`map_canonical_type`）。
- FACT-02：语料出现过 `listening` 等（v0.3 §5.3 `OBSERVED`）；`listening` ∉ 闭集。
- FACT-03：现路径：verbatim → IR map 失败 → incomplete / 不产 leaf。
- FACT-04：Contract §5.2：缺/未知 → UNKNOWN，禁默认 short_answer；映射须 per-value Owner rule。

### Current Contract
v0.3 §5；OD-V3-13 = OWNER。

### Frozen Constraint
**20 QT 闭集与 exact passthrough；禁 alias**。扩集 = Frozen/Display 契约变更；映射若非 Owner 事件则违 §5.2 且可能违禁 alias 精神。

### Current Code
`compile/__init__.map_canonical_type`；adapter verbatim。

### Dependency
先决 → 原 OD-12 接线（非 Owner）；与 OD-P12 grammar 相关（扩集是否进 strict-auto 另受 FC-4 约束）。

### Option A
闭集不扩：闭集外 → `explicitly_unsupported` / incomplete（现状语义产品化）。

Direct consequence:
listening 等永不 ready；无扩集 Frozen 变更。

Code:
boundary 显式 unsup 登记（实现）。

Schema:
无。

Contract:
OD-13 关为「不扩」。

Frozen:
与现行 Frozen 一致。

### Option B
扩 QT 闭集（含 listening）→ **Frozen 变更提案**。

Direct consequence:
闭集与 Role Contract、grammar 叙事都变。

Code:
CANONICAL_TYPES、role 表、测试全改（**需 Frozen 授权后**）。

Schema:
无 DB 但 build_versions 语义变。

Contract:
v0.3 §5.1 表改（须另开 Contract 修订，本包不改）。

Frozen:
**必须** Frozen/Display 修订；DRAFT 不能自称已覆盖。

### Option C
per-value Owner 映射到现有 12 型之一（若存在忠实映射）。

Direct consequence:
不扩集但引入映射事件（须 event id，类 OD-2 流程）。

Code:
authorized map 表扩展（AT 限 QT，注意与 UT 边界）。

Schema:
无。

Contract:
§5.2 走通 per-value。

Frozen:
不扩集；须防「实质扩语义」被判 alias 违规——映射忠实性由 Owner 声明。

### Decision Required
OWNER:
________________

---

## OD-P11 — v0.2 UT 词面与 OD-2 canonical 词面消歧

### Question
如何在文档与治理上消歧：v0.2 曾写 canonical UT 闭集词面与 OD-2/Frozen/代码 `{standalone_unit, composite_unit}` 不一致？

### Observed Facts
- FACT-01：v0.2 冻结候选文本存在以 `standalone_question/composite_question` 为 canonical 的表述（可行性矛盾 #1）。
- FACT-02：Frozen 20 §4.5 + D1 + OD-2 Closure：canonical = `{standalone_unit, composite_unit}`；question 形为 legacy。
- FACT-03：v0.3 称继承 v0.2 但 OD-2 已换词面。
- FACT-04：代码 `UNIT_TYPES` = unit 词面。

### Current Contract
v0.3 §4.1；OD-2 Closure 2026-09-21。

### Frozen Constraint
**以 Frozen 20 §4.5 / D1 为准的 canonical 词面不得在本包被改写**。本 Decision **不是**重新选择 canonical 词面，而是选择 **历史文本如何记账/映射**。

### Current Code
`UNIT_TYPES`；`PRODUCER_UNIT_TYPE_TO_CANONICAL` legacy 键为 question 形。

### Dependency
OD-P09。

### Option A
书面声明 v0.2 相关句段为 **historical vocabulary 笔误/过时**，以 Frozen+OD-2 为准；发布映射附录。

Direct consequence:
单一 canonical 读法；无代码变。

Code:
无。

Schema:
无。

Contract:
v0.3 附录消歧（**待 v0.3 修订授权**，本包只记录选择）。

Frozen:
与 Frozen 一致。

### Option B
保留双文档并行 + 强制 OD-2 映射表作为唯一解释桥。

Direct consequence:
阅读成本；无立即代码变。

Code:
无。

Schema:
无。

Contract:
增加「读桥」条款。

Frozen:
不改 Frozen；依赖 OD-2。

### Option C
仅当 Owner 拟改 canonical 词面时才构成新 Ontology 决策——**本选项 = 明确拒绝改词面**，只做文档勘误。

Direct consequence:
Ontology 稳定。

Code:
无。

Schema:
无。

Contract:
勘误清单。

Frozen:
完全一致。

### Decision Required
OWNER:
________________

---

## OD-P12 — Gate grammar / auto_approve 产品策略

### Question
在 Frozen `STRICT_AUTO_TYPES` 仅 3 型的约束下：书面接受「其余恒 pending_review」并定义人工路径产品，还是提出 Frozen 变更以扩大 strict-auto？

### Observed Facts
- FACT-01：`STRICT_AUTO_TYPES = {single_choice, multiple_choice, true_false}`（20 §8.4 / BUG-V3-023）。
- FACT-02：其余型 `grammar None` → policy → `pending_review`；`auto_approve` 不可达（`OBSERVED` X2.7 NEW-F3）。
- FACT-03：approve 双入口：auto（strict-auto）或 human review_trail（Frozen 20 §8.2）。

### Current Contract
OD-V3-15；v0.3 §5.3 记录缺口。

### Frozen Constraint
**FC-4**：禁为 9 型编造 grammar；扩大 auto = Frozen 变更。

### Current Code
`grammar.verify`；`policy._leaf_grammar`；`AdmissionService.approve` 双入口。

### Dependency
OD-P10（型集）；OD-P08（证据 blockers）。

### Option A
书面废止「扩大 auto」预期：3 型外产品化人工 review SLA；auto 仅 3 型。

Direct consequence:
与 Frozen 完全一致；吞吐依赖人审。

Code:
可能只改文档/报表解释；policy 不动。

Schema:
无。

Contract:
OD-15 关为「维持 Frozen auto 面」。

Frozen:
一致。

### Option B
提出 Frozen 修订扩展 STRICT_AUTO_TYPES / 新 grammar 契约。

Direct consequence:
可能提高 auto 覆盖；工程+契约双变。

Code:
grammar 大改（**仅在 Frozen 修订后**）。

Schema:
无。

Contract:
Display/Gate 契约修订。

Frozen:
**阻塞至 Frozen 变更完成**。

### Option C
保持 auto 定义不变，但优化 human 入口（批处理 UI 等）——纯工程，不另作架构二选一。

（若认为已含于 A，可不选 C。）

Direct consequence:
无架构变。

Code:
工程。

Schema:
无。

Contract:
无新条款。

Frozen:
一致。

### Decision Required
OWNER:
________________

---

## OD-P13 — `verified_correct=True` 物化的审计语义

### Question
如何向审计/下游表述：`verified_correct=True` 是 Source 事实还是 Admission 语义状态？是否需要额外 provenance/validation 标注以避免与 PRD/SRC 混淆？

### Observed Facts
- FACT-01：Compiler payload answer `verified_correct=None`（`compiler.py`）。
- FACT-02：Admission `_materialize` 对 answer role 写 `verified_correct: True`（`admission.py`）。
- FACT-03：Frozen 20 §8.3 / §8.2：approved 物化 `verified_correct = payload ∨ 人工确认`；approved 三字段路径要求。
- FACT-04：90 治理：`Validated Evidence` ≠ `verified_correct`，永不可互换。
- FACT-05：source_located/complete 更接近源结构事实；verified_correct 是 Admission 结果。

### Current Contract
SAM：EVD 经 Gate/Validation；禁 UNK 静默升级——物化 True 必须可解释为 **Admission 结果**而非改写 PRD。

### Frozen Constraint
**不得**在 approved 物化上取消 Frozen 要求的三字段路径（10 §8 / 20 §8.3）；同时 90 文档已区分证据与 verified_correct。

### Current Code
见 FACT-01/02。

### Dependency
独立；建议与 OD-P08 审计叙事一起读。

### Option A
文档/治理：明确 `verified_correct=True` **仅** = Admission semantic state；source 字节事实看 span/text_hash；不改代码。

Direct consequence:
消除 authority 误读；零代码风险。

Code:
无（或仅注释/文档）。

Schema:
无。

Contract:
SAM/审计说明补一句（v0.3 修订另授权）。

Frozen:
一致（Frozen 本身就这么定义）。

### Option B
物化时增加显式 provenance/validation 标注（如 admission_event 已有则强化查询契约，或 role 侧旁路 JSON 注明 admission_confirmed）。

Direct consequence:
审计更显式；有 schema/payload 变更面。

Code:
materialize 附带字段。

Schema:
JSONB 扩展或依赖已有 admission_event 关联。

Contract:
补充 provenance 条款。

Frozen:
不得削弱三字段；增加标注通常兼容，**须避免**造成第二「正确性」权威（见 FC-3）。

### Option C
改变物化逻辑使 verified_correct 不再 True——**直接撞 Frozen approved 路径**。

Direct consequence:
违反 10 §8/20 §8.3。

Code:
admission 改 → 与 Frozen 冲突。

Schema:
无帮助。

Contract:
与 Frozen 矛盾。

Frozen:
**BLOCKED（需 Frozen 变更，且与 approved 定义冲突）**。

### Decision Required
OWNER:
________________

---

## OD-P14 — `answer_lines or answer_evidence_lines` fallback

### Question
`runner_b2` 在 `answer_lines` 缺失时改用 `answer_evidence_lines` 是否允许为合法 answer 定位源？何时必须 fail closed？

### Observed Facts
- FACT-01：`runner_b2`：`answer_lines or answer_evidence_lines`（`OBSERVED`）。
- FACT-02：两者都来自 Producer manifest；语义分别为「印刷答案行区」vs「answer_evidence.lines」。
- FACT-03：IPM：`answer_lines` = prov+unc；`answer_evidence` = ev/unsup；二者同属 Producer 声明，但 **不是同一字段**。
- FACT-04：若 `answer_evidence.type/value` 与 lines 内容不一致而被当成同一线锚，存在错误 source 定位风险。

### Current Contract
P2 禁语义突变；P3 证据保留但须可回源；无专条授权该 fallback。

### Frozen Constraint
NONE 字面禁止；**00 §6** 禁 missing evidence → guessed answer——若 evidence.lines 本身是合法 Producer 声明，属「有证据的定位」而非 guess；若空/矛盾则仍须 fail closed。

### Current Code
`runner_b2.py` 约 272–274。

### Dependency
OD-P07；OD-P21（若 runner 升格生产则更关键）。

### Option A
允许：仅当 `answer_lines` 缺失且 `answer_evidence.lines` 合法在界且（若可）与 evidence.type 一致时使用；否则 fail closed。

Direct consequence:
扩大合法定位源；规则必须写死。

Code:
显式校验规则 + 负例测试。

Schema:
无。

Contract:
新增条款（v0.3 修订另授权）。

Frozen:
在「非 guess」前提下可与 00 §6 兼容。

### Option B
禁止 fallback：仅 `answer_lines` 为 answer 区权威；缺失 → 不完整/incomplete。

Direct consequence:
最严；evidence.lines 仅作旁证不进 answer span。

Code:
删除 or 分支。

Schema:
无。

Contract:
禁止该 fallback 写入。

Frozen:
一致。

### Option C
fallback 仅允许进入 pending_review 的人工路径，禁止任何 auto/`source_located` 自动置真。

Direct consequence:
折中：可见但不进 strict-auto 自动链。

Code:
标记 answer 源类型；policy 不因 fallback auto。

Schema:
payload 标记。

Contract:
分路径允许。

Frozen:
auto 链更保守，兼容。

### Decision Required
OWNER:
________________

---

## OD-P15 — Generated explanation 与 Frozen 边界

### Question
Post-admission 生成的 explanation：（1）是否属于 Frozen `00 §5`「复杂统计富化非目标」？（2）其持久化是否只能落在非 `instance_role_contents` 的 V3D/AI-Generated 槽？

### Observed Facts
- FACT-01：Frozen **00 §5**：自动语义去重 / Question Family / 自动知识点扩展 / **复杂统计富化** 列为不阻塞 M1 的非目标。
- FACT-02：Frozen **10 §1.1**：LLM 输出永远是 C 域 annotation，不是 live 文本。
- FACT-03：Frozen **10 §2**：post-admission 派生 = 显式 Repository 步骤。
- FACT-04：Frozen **00 P3**：无 provenance 只能作 AI Generated/Inferred/Unverified，不得伪装 Source-derived 进 approved。
- FACT-05：Frozen **20 §6.3**：explanation **optional**（非 admission 硬门）。
- FACT-06：PAE §1/§3/§8 `PROPOSED`：admission 后异步生成 explanation 并入 Question 槽；禁回滚；禁冒充 Producer。
- FACT-07：代码：无 generated 槽；`InstanceRoleContent` 注释/规范禁止 text 来自 LLM；Question 表无 explanation 列（正文在 role_contents）。
- FACT-08：`knowledge_nodes` 已是 Frozen optional derived 的先例。

### Current Contract
PAE 全文 `PROPOSED`；SAM §4 双槽；OD-V3-21 主体已降级（optional 已由 Frozen 决定），**残余**为生成物是否允许进入产品路线。

### Frozen Constraint
见 FC-1/FC-2/FC-3/FC-7。**Contract DRAFT 不覆盖 Frozen。**

### Current Code
无 enrichment 任务类型；无 generated explanation 写路径。

### Dependency
**必须先于** OD-P16/P17/P18/P19。

### Option A
解释为 **不属** 00 §5 非目标：explanation 生成 = 允许的 AI Generated 派生（P3 路径），落独立 V3D 槽；仍 **禁止** 写入 `instance_role_contents`。

Direct consequence:
PAE 技术上可进入 schema 设计（仍要 OD-P16）；与 10 §1.1 兼容前提是新槽。

Code:
新 enrichment 模块 + 新槽（**无授权不写**）。

Schema:
**必须** 新表/新列（OD-P16）；绝不用 role_contents.text 承载 LLM。

Contract:
PAE 从「可能撞 Frozen」变为「在 Frozen 边界内 PROPOSED」。

Frozen:
**不改 Frozen**；解释为 P3 AI Generated。若 Owner 担心 00 §5 仍覆盖，可选 B。

### Option B
解释为 **属** 00 §5 非目标：PAE explanation 生成路线 **BLOCKED**，除非另提 Frozen/errata 扩展 M1 非目标边界。

Direct consequence:
当前合同下不可实现生成；只能做 knowledge（若 knowledge 也不在非目标内——knowledge 已被 10 允许 optional）。

Code:
不建生成链。

Schema:
不做 explanation 生成表（或仅留空表设计不用）。

Contract:
PAE 标 `BLOCKED BY FROZEN` 直至变更。

Frozen:
承认非目标覆盖；启动 Frozen 修订才可能改判。

### Option C
分阶段：现阶段只实现 **知识/难度等已非冲突派生** 的槽与 job；explanation 生成单独出 Frozen 解释性 errata 提案后再开。

Direct consequence:
降低一次裁决范围；explanation 生成延期。

Code:
可先做 P16 中非 explanation 部分（仍需 P16 决定 schema 范围）。

Schema:
P16 可先含 jobs + knowledge/difficulty，explanation 列可预留。

Contract:
PAE 分轨标注。

Frozen:
不改 Frozen；explanation 轨保持 pending Frozen 解释。

### Decision Required
OWNER:
________________

---

## OD-P16 — Enrichment jobs 持久化 schema

### Question
Enrichment 的 job 状态、generated 内容槽、difficulty/skills（若纳入）采用何种持久化形态？（本题只定 **架构级 schema 方向**，不在此写 DDL 细节。）

### Observed Facts
- FACT-01：无 `enrichment_jobs` 表；Question 无 difficulty/skills 列；knowledge 有表无写路径。
- FACT-02：`InstanceRoleContent.text` 不得作 LLM 落点。
- FACT-03：PAE §8 逻辑槽 + append-only jobs；状态机含 absent/queued/generated/validated/accepted/failed/… 与 validation_state 4 值存在词汇差（矛盾 #7）。
- FACT-04：10 §11 变更走 Alembic；本包 **NO MIGRATION AUTHORIZATION**。

### Current Contract
OD-V3-25 = OWNER；PAE §8 `PROPOSED`。

### Frozen Constraint
FC-1/FC-7；Knowledge optional；不回改已提交内容行。

### Current Code
Task 表可扩展 `task_type`（运行域）；内容域无 job 表。

### Dependency
**必须** OD-P15 先决；OD-P17/P18/P19 后随。

### Option A
独立 `enrichment_jobs` 表 + 独立 generated 内容表（或 JSONB 槽表）+ 复用 `tasks` 运行态；内容与 jobs 分列。

Direct consequence:
符合 append-only + 独立 Repository 步骤；实现面较大。

Code:
新 domain 模块（授权后）。

Schema:
**新表**（migration 另案）。

Contract:
关闭 OD-25 为「独立表方案」。

Frozen:
兼容 10 §2/§11。

### Option B
仅复用 `tasks`/`llm_call_audit` + 在 Question 上增加 generated JSONB 槽，**不建** 独立 enrichment_jobs 表。

Direct consequence:
表更少；job 历史/审计粒度可能与 tasks 耦合。

Code:
扩展 task_type 与 JSONB 读写。

Schema:
**列/JSONB 扩展**（仍 migration）。

Contract:
关闭 OD-25 为「tasks+JSONB」。

Frozen:
须证明仍为显式步骤且不回改 PRD 行。

### Option C
与 OD-P15 选项 C 对齐：先 jobs 框架 + knowledge/difficulty 槽，explanation 槽结构预留字段名但不启用。

Direct consequence:
与 Frozen 解释解耦的最小 schema。

Code:
分阶段。

Schema:
分阶段 migration 范围。

Contract:
OD-25 标「分阶段 schema」。

Frozen:
兼容。

### Decision Required
OWNER:
________________

---

## OD-P17 — ValidationEvent generation provenance

### Question
生成物验证如何挂在现有 ValidationEvent/Evidence Authority 上，而不创建第二套证据权威？

### Observed Facts
- FACT-01：ValidationEvent 唯一产生 Evidence Authority；绑定 `candidate_id` + `claim_id`（unit_id）+ `source_version_id`。
- FACT-02：post-admission job **可能不存在** admission candidate 时点之外的新 claim 身份（Question 已 approved）。
- FACT-03：SAM §5：优先复用 ValidationEvent；扩字段 = schema/governance，不在 DRAFT 授权内。
- FACT-04：PAE 状态机 vs validation_state 4 值未对齐。

### Current Contract
PAE §5；SAM §1 铁律④ 禁平行 authority。

### Frozen Constraint
EB-008/92 号段 ValidationEvent 模型；复用为 PROPOSED；扩模型须治理程序——**不得**私自第二权威。

### Current Code
`EvidencePromotionService.record_validation_event`；gate 路径绑定 candidate；pending 不落事件。

### Dependency
OD-P15、OD-P16。

### Option A
扩展 ValidationEvent（或同模型子类）以允许 post-admission claim 键（如 `question_id`）+ generation 上下文字段。

Direct consequence:
单账本；schema/模型变更。

Code:
evidence 层扩展 + 投影规则。

Schema:
**表扩展**。

Contract:
SAM §5 落地为扩展现有。

Frozen:
在治理批准扩展的前提下与「单 authority」一致；需对照 EB-008 冻结字段是否允许扩展。

### Option B
不改 ValidationEvent：生成验证用 **独立 `enrichment_validation` 状态列/表**，但 **只映射/引用** 未来是否升级为 evidence 仍回 ValidationEvent。

（若最终也要 authority，则本选项可能滑向平行权威——须 Owner 明确禁止写 approved Evidence。）

Direct consequence:
不立刻改 EB 表；存在「状态权威 vs Evidence 权威」双轨风险。

Code:
job 状态机即可。

Schema:
依赖 P16 表内 validation_state。

Contract:
须写明 **生成 validation_state ≠ Evidence Authority**。

Frozen:
**必须**避免把 generated validated 当作 EB Evidence 去 approve 其它 claim；若产品要用其做「教材级」背书，可能仍要走 A。

### Option C
生成物 **不** 写 ValidationEvent：仅 job 内状态；Evidence Authority 继续只服务 admission claim。

Direct consequence:
最简单；生成物无 Evidence Authority 加持。

Code:
无 evidence 扩展。

Schema:
P16 内字段。

Contract:
显式降级生成验证的权威等级。

Frozen:
与现 EB 定义最兼容。

### Decision Required
OWNER:
________________

---

## OD-P18 — producer vs generated 展示优先级

### Question
当 producer explanation 与 generated explanation 并存时，默认展示优先级与标识规则是什么？

### Observed Facts
- FACT-01：PAE：双槽并存；`accepted` 前不得展示为教材级；展示策略 OPEN。
- FACT-02：SAM §4：禁覆盖/伪装。

### Current Contract
OD-V3-22 OPEN；依赖 P15 使生成物存在。

### Frozen Constraint
FC-1；P3 禁伪装 Source-derived。

### Current Code
无双槽。

### Dependency
OD-P15（须有生成物才有本题）；OD-P16。

### Option A
有 producer 槽则 **永不** 默认展示 generated；generated 仅无 producer 时且 `accepted` 后展示，并带 AI 标识。

Direct consequence:
最保守；符合禁伪装。

Code:
展示层规则。

Schema:
槽 + display 策略字段或配置。

Contract:
关闭 OD-22。

Frozen:
兼容 P3。

### Option B
双显：producer 优先，generated 标签展示。

Direct consequence:
产品信息密度更高；误读风险靠标签控制。

Code:
UI/查询。

Schema:
可能存 display_policy（OPEN 原列）。

Contract:
关闭 OD-22。

Frozen:
须标识 AI Generated。

### Option C
全默认 generated 隐藏，仅人工 `accepted` 后进入推荐位——与 A 差异在无 producer 时是否仍默认隐藏。

（若 A 已含此意，C 可省略。）

Direct consequence:
更少自动展示。

Code:
同 A 类。

Schema:
同 A。

Contract:
关闭 OD-22。

Frozen:
兼容。

### Decision Required
OWNER:
________________

---

## OD-P19 — identity hash 是否排除 generated 字段

### Question
Question `dedup_key` / 相关 identity 是否显式排除 generated explanation/difficulty 等字段（对齐 OQ-1 与现 identity projection）？

### Observed Facts
- FACT-01：现 `dedup_key` = canonical type + stem + options（已不含 explanation/answer/material/no）。
- FACT-02：annotation identity projection 剔除 confidence/line_refs（OQ-1 Gate A 语境）。
- FACT-03：OD-V3-26 对齐 OQ-1。

### Current Contract
Frozen 20 §7.3 三 key 表；PAE：enrichment 不得改变 question identity 语义成分。

### Frozen Constraint
**三 key 已 Frozen**；排除 generated 是 **确认现状** 还是 **改 hash 输入集** 必须区分——改输入集 = Frozen 变更。

### Current Code
`Compiler._question_dedup_key` / `admission._dedup_key`；不含 explanation。

### Dependency
OD-P15/P16（若未来有人提议把 generated 进 identity 才有冲突面）。

### Option A
确认并书面锁定：generated 字段 **永不** 进入 dedup/occurrence/LE 语义键（维持现 Frozen 三 key）。

Direct consequence:
与现码一致；防未来误改。

Code:
无或测试锁。

Schema:
无。

Contract:
关闭 OD-26 为「维持排除」。

Frozen:
与 20 §7.3 一致。

### Option B
若未来要把 generated 摘要进某种 identity——**明确另开 Frozen 变更**，本包不选具体公式。

（作为记录性选项，实际 = 拒绝在本包内设计新 identity。）

Direct consequence:
现 identity 不动。

Code:
无。

Schema:
无。

Contract:
标注「identity 变更另案」。

Frozen:
维持。

### Option C
为 generated 单独定义 **非 Question identity** 的 artifact hash（job 输出 hash）。

Direct consequence:
丰富审计；不碰 dedup。

Code:
job 输出 hash（实现）。

Schema:
P16 内字段。

Contract:
与 OD-26 兼容。

Frozen:
不改 Question identity → 兼容。

### Decision Required
OWNER:
________________

---

## OD-P20 — `runner.py` 处置

### Question
`scripts/preprocessing_consumer/runner.py` 仅 Scope、无 M1–M5、Track A 可进 production `GateService`——删除、硬阻断，还是对齐 `runner_b2`？

### Observed Facts
- FACT-01：`runner.py` 调 `enforce_interface_scope` + `GateService.run`；无 M1–M5（NEW-F1 / `OBSERVED`）。
- FACT-02：`runner_b2`：Scope∧M1–M5；直调 IR/Compiler/policy，不进 GateService 编排。
- FACT-03：v0.3 §2.2 要求所有正式 entrypoint 过 Scope∧M1–M5。
- FACT-04：X2.7 将此标 historical/experimental alignment issue。

### Current Contract
OD-V3-16 = OWNER；与 OD-V3-19 强耦合。

### Frozen Constraint
NONE 直接规定 runner 文件命运；**统一 identity 边界**是 v0.3 PROPOSED，不是 V3 Frozen Spec 条文。

### Current Code
见 FACT-01/02。

### Dependency
**先决：OD-P21**（路径地位）；影响 OD-P14/P25 是否升格生产问题。

### Option A
删除 `runner.py`（或移入明确非 production/归档区）。

Direct consequence:
消除违规入口。

Code:
删/迁 + 文档。

Schema:
无。

Contract:
OD-16 关为删除。

Frozen:
NONE。

### Option B
硬阻断：保留文件但强制 M1–M5，否则拒绝调用 GateService（对齐 B2 边界）。

Direct consequence:
可保留 Track A 实验，同时堵洞。

Code:
入口闸。

Schema:
无。

Contract:
OD-16 关为强制对齐。

Frozen:
NONE。

### Option C
完整对齐 B2（M1–M5+Scope）且规定其与 GateService 关系（仍可能非生产）。

Direct consequence:
最大工程量对齐实验链。

Code:
大改 runner。

Schema:
无。

Contract:
OD-16 关为对齐。

Frozen:
NONE。

### Decision Required
OWNER:
________________

---

## OD-P21 — `preprocessing_consumer` 生产路径地位

### Question
`scripts/preprocessing_consumer` 是升格为正式 Producer→V3 production path，还是书面永久旁路（仅 harness/实验）？

### Observed Facts
- FACT-01：现为 scripts；生产主链是 `TaskExecutor`（file_path 本地文档）→ GateService。
- FACT-02：M1–M5 实现位于 core/，调用点主要在 runner_b2/tests。
- FACT-03：OD-V3-19 = OWNER。

### Current Contract
v0.3 目标生命周期含 Producer Artifact 消费；未指定 scripts 是否 production。

### Frozen Constraint
V3 Frozen 主链 = Source→Annotation→Resolver→…（00 P1）；Producer 预计算路径是 **集成边界** 扩展，不是对 Frozen 单主链的自动删除。

### Current Code
见上。

### Dependency
**先于 OD-P20/P22**；不阻塞 Cluster B/C 的合同裁决但阻塞「生产接线」实现范围。

### Option A
升格 production path：定义正式 Producer 入口（仍过 Scope∧M1–M5，可复用/替换 GateService 编排）。

Direct consequence:
两条生产输入：本地文档链 + Producer artifact 链。

Code:
scripts 迁 app 或正式 API 包装；M1–M5 进生产必经。

Schema:
无 DB 必变。

Contract:
明确第二输入路径条款（v0.3 修订）。

Frozen:
不删 Resolver 原链；只加集成入口 → 须写清与 00 P1 关系。

### Option B
书面永久旁路：consumer 永不生产写；production 不接 manifest。

Direct consequence:
M1–M5 仍服务 harness/验收；GateService 仅服务文档链。

Code:
runner 不得碰生产库/或只读报告（现状 b2 rollback 一致）。

Schema:
无。

Contract:
OD-19 关为旁路。

Frozen:
与单主链最兼容。

### Option C
阶段升格：先 B 书面旁路，待 OD-P01/P02/P08 等闭合后再开升格里程碑（仍需再次 Owner 授权）。

Direct consequence:
避免一次大决定。

Code:
现阶段维持。

Schema:
无。

Contract:
标「延期升格」。

Frozen:
NONE。

### Decision Required
OWNER:
________________

---

## OD-P22 — batch IR 分发与 Artifact package

### Question
批量 resolver IR 与 Producer Artifact 包：versioned artifact 升格，还是仅路径约定？package 最小字段集是否现在定？

### Observed Facts
- FACT-01：现 live manifest + `resolver_ref_r52/resolver_ir.json` 实验快照（`OBSERVED` v0.3 §13）。
- FACT-02：Contract §13 只定义不实现 distribution。
- FACT-03：NEW-F2 batch IR；OD-17+OD-20 并入本题。

### Current Contract
v0.3 §13 `PROPOSED` 字段集（identity、manifest、IR、version、QC、provenance、checksum…）。

### Frozen Constraint
NONE 立即强制新包格式；identity 键语义仍遵 v0.2/Scope。

### Current Code
无正式 package 服务。

### Dependency
**OD-P21**；影响 OD-P01/P03 的 bytes 策略。

### Option A
升格 versioned package（按 §13 最小集）并成为正式分发。

Direct consequence:
跨系统契约变强。

Code:
打包/校验工具。

Schema:
package 描述（非 DB 必选）。

Contract:
§13 从定义变实施范围（实施仍要另授权）。

Frozen:
NONE。

### Option B
维持路径约定 + 文档化 layout；不建正式 package 产品。

Direct consequence:
轻；跨机一致性弱。

Code:
文档。

Schema:
无。

Contract:
OD-17/20 关为不建包。

Frozen:
NONE。

### Option C
分件：先 versioned IR 指纹清单；bytes package 随 OD-P03。

Direct consequence:
解耦传输与 IR。

Code:
IR manifest 清单。

Schema:
无。

Contract:
分阶段。

Frozen:
NONE。

### Decision Required
OWNER:
________________

---

## OD-P23 — v0.3 是否进入 Freeze Candidate

### Question
五件套 + 本 Decision Package 是否以及何时进入 Freeze Candidate / 正式 Frozen？

### Observed Facts
- FACT-01：五件套状态 = DRAFT / NON-AUTHORITATIVE / NOT FROZEN @ `968943f`。
- FACT-02：本包 = PACKAGE / NOT FROZEN。
- FACT-03：OD-V3-27 = OWNER；内部矛盾 10 条待消（可行性 §15.2）——Freeze 前是否要求矛盾闭合属本题范围外的前提说明。

### Current Contract
v0.3 头部自陈 NOT FROZEN。

### Frozen Constraint
Frozen V3 Spec 与 preprocessing DRAFT 是不同层；Freeze preprocessing 合同 **不**自动改 V3 Frozen。

### Current Code
NONE（文档状态）。

### Dependency
建议在 Cluster A–E 主要决策有记录后（非逻辑强制）。

### Option A
保持 DRAFT 至全部 OD-P* 有 Owner 签字栏完成 + 矛盾勘误后再开 Freeze Candidate 评审。

Direct consequence:
实现前合同仍非权威。

Code:
无。

Schema:
无。

Contract:
状态机明确。

Frozen:
NONE。

### Option B
部分 Freeze：仅身份/词表继承项（v0.2 已冻六项）升 Frozen，其余 DRAFT。

Direct consequence:
核心接口先稳。

Code:
无。

Schema:
无。

Contract:
分层冻结状态。

Frozen:
不与 V3 Spec 混淆。

### Option C
立即 Freeze 全套。

（与仍有 OPEN/未签 OD 并存时，需 Owner 明确接受残留风险。）

Direct consequence:
高权威、高摩擦。

Code:
无。

Schema:
无。

Contract:
全 Frozen。

Frozen:
NONE。

### Decision Required
OWNER:
________________

---

## OD-P24 — 与 X2.x / Migration Gate / X3 关系

### Question
本合同/决策包与 Migration Gate、X3 入场、X2.x 治理状态的关系如何书面锁定？

### Observed Facts
- FACT-01：v0.3 / 本包均声明 **非迁移授权、非 X3 入场**。
- FACT-02：OD-V3-28 = OWNER；与 OD-P01 回填路径可能交叉。

### Current Contract
头部硬边界。

### Frozen Constraint
V3 Frozen 的 migration 章节（50）与 X3 程序不在本 DRAFT 内授权。

### Current Code
NONE。

### Dependency
OD-P01 Option B 时强依赖；可与实现簇并行。

### Option A
书面锁定：本包所有裁决 **均不** 触发 Migration Gate 打开或 X3 entry；回填/迁移必须另开授权文档。

Direct consequence:
边界最清晰。

Code:
无。

Schema:
无。

Contract:
强化头部为裁决项记录。

Frozen:
与现声明一致。

### Option B
列出「若 OD-P01=B 则自动启动 Migration Gate 预检」的程序挂钩。

Direct consequence:
裁决连带程序。

Code:
无。

Contract:
程序链接条款。

Frozen:
仍需 Gate 文件本身权威。

### Option C
本包只管架构二选一；X3/Migration **完全另包**（OD-P24 记 NONE 关系）。

Direct consequence:
本包最小范围。

Code:
无。

Contract:
关系 = 「无」。

Frozen:
NONE。

### Decision Required
OWNER:
________________

---

## OD-P25 — text hash family 一致性

### Question
spans/文件/`text_hash` 在 raw `hashlib.sha256` 与 `sha256_hex`（canonical JSON 族 helper）之间如何统一？各身份域分别用哪一族？

### Observed Facts
- FACT-01：Frozen/Compiler：`text_hash` = **raw** SHA256(text)，禁 canonical JSON 包装（BUG-V3-017 族；`test_compiler` 断言 `text_hash != sha256_hex({...})`）。
- FACT-02：M2/raw_bytes：强制 `hashlib.sha256`；AST 禁 `sha256_hex`（`test_adversarial_raw_bytes`）。
- FACT-03：`resolved_span_adapter`：`hashlib.sha256(joined)`。
- FACT-04：`runner_b2` span/`file_sha` 部分使用 `sha256_hex(body_text)`（helper 族）；与 Compiler raw 族可能不一致。
- FACT-05：LE/identity_projection 使用 `sha256_hex` 是 **另一设计域**（canonical 输入 hash），与 text_hash 不同。
- FACT-06：`source_loader.compute_body_hash` 经 splitlines 重组，与 raw bytes M2 不同。

### Current Contract
20 §7.3 text_hash raw；30 §16 canonical_json 用于 LE；二者并存有 Frozen 依据。

### Frozen Constraint
**分域已 Frozen**：text/raw-bytes = raw SHA；LE/canonical 输入 = canonical_json/helper。冲突在于 **consumer 实现是否跨域误用**。

### Current Code
见 FACT-03/04/06。

### Dependency
OD-P21（升格则必须修）；可独立先修 harness。

### Option A
书面分域表 + 修 consumer：凡 **text_hash/source body identity** 一律 raw SHA256；凡 **LE/canonical object** 用 helper；禁止混用。

Direct consequence:
与 Frozen 分域一致；b2/adapter 对齐。

Code:
改 runner_b2/adapter/source_loader 中误用点。

Schema:
无。

Contract:
增加 hash 分域附录（修订另授权）。

Frozen:
符合 20/30 分域。

### Option B
全部文本哈希改走 helper——**与 test_compiler/raw_bytes 冲突**。

Direct consequence:
违反 Frozen text_hash 定义。

Code:
大改 + 测试反向。

Schema:
无。

Contract:
与 Frozen 矛盾。

Frozen:
**BLOCKED**（除非 Frozen 变更——不推荐为本包内合法 Option；列出仅表明其后果）。

### Option C
分阶段：先锁 M2/Compiler 不动，仅统一 **scripts harness** 内部 hash，并标注 harness hash 不得冒充 payload text_hash。

Direct consequence:
风险隔离在 scripts。

Code:
scripts 内改。

Schema:
无。

Contract:
harness 非权威声明。

Frozen:
兼容。

### Decision Required
OWNER:
________________

---

# Summary

## Decision Clusters

### Cluster A — Producer Identity / Quality
- **Decisions**: OD-P01, OD-P02, OD-P03
- **Dependencies**: P01 ↔ P24（若回填）；P02/P03 可并行
- **After decision, implementable**: Scope 成员披露或回填工具设计；QC 闸门设计；bytes/OCR 面合同
- **Still blocked**: 无 Frozen 阻；回填类仍可能卡 Migration Gate 程序（P24）

### Cluster B — Evidence Fidelity / Producer Structure
- **Decisions**: OD-P04, OD-P05, OD-P06, OD-P07, OD-P08
- **Dependencies**: P08 ← P07（弱）；P04/P05/P06 并行
- **After decision, implementable**: adapter 透传范围；Gate blocker 或 review 清单设计；Producer 升级 backlog
- **Still blocked**: 无 Frozen 阻（V3 再解析选项 C 若选可能碰「不补语义」边界）

### Cluster C — Canonical Vocabulary
- **Decisions**: OD-P11, OD-P09, OD-P10
- **Dependencies**: P11 → P09；P10 独立；P10 → QT 接线实现
- **After decision, implementable**: 唯一 mapping authority 接线；QT unsup 登记；F-05-A 实现（原 OD-30）
- **Still blocked**: 扩 QT 闭集 → Frozen（P10=B）；改 canonical UT 词面 → **本包禁止**（D1）

### Cluster D — Gate / Answer Verification
- **Decisions**: OD-P12, OD-P13, OD-P14
- **Dependencies**: 相对独立；P12 受 FC-4
- **After decision, implementable**: auto/人审产品说明；审计语义文档；answer fallback 规则测试
- **Still blocked**: 扩大 STRICT_AUTO → Frozen（P12=B）；取消 approved verified_correct 物化 → Frozen（P13=C）

### Cluster E — Enrichment
- **Decisions**: OD-P15, OD-P16, OD-P17, OD-P18, OD-P19
- **Dependencies**: **严格** P15 → P16 → P17 → P18；P19 ← P15
- **After decision, implementable**: （P15=A/C）schema 设计立项、job 编排、展示规则、identity 锁定测试
- **Still blocked**:
  - P15=B → explanation 生成 **BLOCKED BY FROZEN** 至 Frozen 变更
  - P16 未决 → **无 migration 授权**
  - P17 平行权威设计 → 违反 SAM 铁律④

### Cluster F — Consumer Path / Governance / Hash
- **Decisions**: OD-P21, OD-P20, OD-P25, OD-P22, OD-P23, OD-P24
- **Dependencies**: **P21 → P20**；P21 → P22；P25 可并行；P23 建议后置；P24 可并行
- **After decision, implementable**: 入口堵洞或升格路线；hash 分域修复；IR 分发形态；Freeze 评审前提
- **Still blocked**: P21 未决 → 生产接线范围不清；P23 未决 → 合同仍非权威

---

## 最终唯一 Owner Decision 数量

```text
OD-P01 … OD-P25  =  25
```

降级/剔除原清单项：8（OD-V3-09/11/12/21 主体/23/24/29/30）。

---

## Decision Dependency Graph（汇总）

```text
[批次1 并行]
OD-P21 ─────────────► OD-P20
OD-P25
OD-P11 ─► OD-P09
OD-P10
OD-P01  OD-P02  OD-P03
OD-P13  OD-P14  OD-P12
OD-P04  OD-P05  OD-P06  OD-P07 ─► (弱) OD-P08
OD-P08

[批次3 Enrichment 串行]
OD-P15 ─► OD-P16 ─► OD-P17 ─► OD-P18
   │         │
   │         └──► OD-P19
   └── (P15=B) ENRICHMENT 生成轨 FROZEN BLOCKED

[批次4]
OD-P21 ─► OD-P22
OD-P23 （建议在主体决策后）
OD-P24 （可并行；回填路径强依赖）
```

---

## 本包边界再确认

| 项 | 状态 |
|---|---|
| production code | **unchanged** |
| tests | **unchanged** |
| schema / migration | **unchanged / none created** |
| Frozen Spec | **unchanged** |
| Frozen Contract | **unchanged** |
| v0.3 Contract 五件套 | **unchanged** |
| preprocessing / corpus | **unchanged** |
| X3 | **not entered** |
| 推荐 Option | **无**（仅 A/B/C 后果描述） |
| 是否开始实现 | **否** |

*End of V3-CONTRACT-v0.3-OWNER-DECISION-PACKAGE.*
