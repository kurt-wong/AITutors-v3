# CONTRACT-CHANGE-RECORD-CR-002-OD-01

```text
Document ID:           CR-002
Title:                 Contract Change Record — OD-01 Option Provenance / Resolved Span
Document Type:         Contract Change Record
Authority Level:       L1
Status:                NOT RELEASED
Normative:             NO
Purpose:               OD-01 修改 L0 的 Change Record 候选；承载 CHANGE 分类、Gate、影响面与授权边界
Derives From:          OD-01（OWNER-DECISIONS）· OD-01R-01…10（同文件附录）· P04 · Proposal v3 · 00/10/20/50（L0 只读）· 90/91 · 69 §5
May Change:            本 CR 候选文本；与 Proposal v3 的引用一致性；Gate evidence/status 行（仅当有证据）
Must Not Change:       L0 00–50 · L0-META 90/91 · Frozen Contract / P01–P25 · Gate/Admission/Question Core · 生产代码 · Schema · Corpus · Preprocessing
Supersedes:            CR-002 v1（2026-09-23，治理格式不合规版本）
Superseded By:         —
Gate State Authority:  NO（唯一 YES = 82 §3）
Change Record ID:      CR-002
Audit ID (planned):    CA-002（仅在 L0 实际修改后按 90 §11 登记）
Date:                  2026-09-23
```

> **Status: NOT RELEASED（合法 Status，对齐 `91 §3.1` 与先例 `67`）。**
> **Formal L1 registration = NOT REGISTERED。**
> 本文件是 **L1 candidate**，**不是**已正式注册、已生效的 L1 Change Record。
> **尚未修改 Frozen Spec。尚未 re-freeze。Owner Authorization 未授予。**

---

## 0. R-01 正式 L1 状态（必须能明确回答）

> **问：按照 Frozen Document Governance，CR-002 当前是否已经是一个正式注册的 L1 Change Record？**
> **答：否。**

| 项 | 判定 |
|----|------|
| `90 §1` L1 = Contract Change Record | 本文件 Document Type 对齐 |
| `90 §1.2` 新增 L1 落位 = `Docs/V3_SPEC/` | **未能落位** |
| 原因 | 本轮禁止改变 Frozen Spec tree hash（`b3eeb3e9…`）；向 `Docs/V3_SPEC/` 加文件即改变 tree hash |
| 第二正式 registry | **不存在**（目录模型内） |
| `Docs/COORDINATION/` | **不在** `90 §1.2` 目录模型 |
| 自创 L1 目录/层级/Status | **未使用**（无 `L1-proposal`；Status=`NOT RELEASED`） |
| 修改 90/91 迁就 CR-002 | **未做** |
| **GOVERNANCE GAP** | **RECORDED** |
| **CR-002 formal L1 status** | **NOT REGISTERED / L1 candidate / NOT RELEASED** |
| 对齐先例 | `67`（CHANGE-4/5 候选，NOT RELEASED） |

**禁止表述：**「已注册 L1」「L1 已生效」「可据此修改 L0」。

---

## 1. 为什么修改（Why）

1. P04（Frozen Contract，CLOSED）要求 Choice Question 具备 per-option structured evidence。
2. 现行 L0 Resolved Span 缺少 polymorphic option provenance form；`00 §5`/`10 §4`/`20 §5.5` 对 table_cell/fragment 明确延后。
3. OD-01 Owner Decision：扩展 Frozen Resolved Span。
4. DSH F-OD01R-01…10：治理落位、格式、CHANGE 分类、双路径、diff 完整性、locator、双层 status、degraded、Owner 记录、引用坐标。
5. Owner 已 ACCEPT 并裁决（OWNER-DECISIONS 附录 OD-01R）。

**OD-01 不改变 Gate / Admission / Question Core 等其他冻结语义。**

---

## 2. Owner Decision 依据

| 来源 | 内容 |
|------|------|
| OD-01 | 扩展 Frozen Resolved Span；options[]={label,text,provenance}；options_lines 保留；禁一行一 option 假设；table_cell/multiple 可表达；不可靠 → fail closed；V3 不用 LLM 猜边界 |
| OD-01R-01 | CR-002 须正式 L1；否则 Gap + 不得自称 L1 |
| OD-01R-02 | 服从 90/91 格式；禁自创层/Status |
| OD-01R-03 | 如实 CHANGE-3/4/5；`00 §5`=放宽；`20 §5.3`=删除/替换 |
| OD-01R-04 | Path A + Path B；汇聚 Canonical IR |
| OD-01R-05 | 补 `10 §4:107-108` / `20 §6.2` / `50:51` + 全树核对 |
| OD-01R-06 | form 分型 locator；禁伪造 line_ref |
| OD-01R-07 | Provenance Resolution ≠ Option/Evidence Resolution |
| OD-01R-08 | degraded 非 fail-closed 后门 |
| OD-01R-09 | 正式 Owner Disposition 记录 |
| OD-01R-10 | options_unresolved / sp-M1 坐标 |

---

## 3. Frozen Spec 变更真实范围（Target）

| # | Target | 动作 | CHANGE |
|---|--------|------|--------|
| T1 | `00 §5` table cell/fragment 非目标 | table_cell **option provenance 子集**放宽；fragment/完整表格索引仍非目标 | **CHANGE-4** |
| T2 | `10 §4:107-108` M1 裁剪 `_tables/_cells/_fragments` | 与 T1 联动澄清；**不**自动授权建表/migration | **CHANGE-4** |
| T3 | `20 §5.3` option_label 无条件 V3 边界规则 | **删除/替换**为 Path A/B 分路径 authority | **CHANGE-5**（+2/3） |
| T4 | `20 §5.5` granularity/延后注/form | form 维度 + 延后放宽 + 分型 locator | **CHANGE-4**（+2/3） |
| T5 | `20 §6.1` IR option source_span | 单链路权威语义；示例 key=`sp-Q1-A` | CHANGE-2+1 |
| T6 | `20 §6.2` IR 不变量 + 三层状态隔离 | 纳入新 form / 双层 resolution / degraded 纪律 | CHANGE-2+3 |
| T7 | `20 §7.2` Compiler 提取 | 扩展 form；Path B 禁 rediscovery | **CHANGE-3** |
| T8 | `20 §7.3` dedup_key | 输入来源澄清；**组合不变** | CHANGE-1 |
| T9 | `10 §6.3` source_span JSONB | 划界；对齐 00 §5 JSONB 非目标；不授权 DDL | CHANGE-1+2 |
| T10 | `10 §8` 2b/2c | 非 line form locator/hash 核验 | CHANGE-2 |
| T11 | `50:51` 图像/表格 bbox 能力行 | 对齐 table_cell / image_region provenance | CHANGE-2+3 |

完整 Current → Proposed 文本 = Proposal v3 **§5**（唯一 diff 权威文本）。

**UNCHANGED：** Gate 四层语义 · Admission · Question Core · vocabulary · QT→UT · dedup **组合** · P01–P25 · OD-02…G-02 · 历史重处理 · Migration policy · X3 · fragment 延后 · Schema DDL · 代码 · Preprocessing · Corpus。

---

## 4. CHANGE-3 / CHANGE-4 / CHANGE-5（禁止压低）

| 项 | 原 Rule | 新 Rule | 实际变化 | CHANGE | Gate |
|----|---------|---------|----------|--------|------|
| `00 §5` table_cell 非目标 | M1 不做文档级 cell/fragment 字符粒度 | option provenance 子集做 table_cell | **放宽既有约束** | **CHANGE-4** | **四道门** |
| `10 §4` `_cells` 不建 | M1 裁剪 | option table_cell 可验证定位不被裁剪语义禁止 | **放宽** | **CHANGE-4** | **四道门** |
| `20 §5.3` option_label | V3 无条件 A/B/C/D 发现边界 | Path B：Producer authority + 禁 rediscovery；Path A：Native 首次解析 | **删除/替换既有约束** | **CHANGE-5** | **四道门** |
| `20 §5.5` 延后注 | table_cell/fragment 延后 | table_cell option 子集解除 | **放宽** | **CHANGE-4** | **四道门** |
| Compiler / form / 状态隔离等 | 见 T5–T11 | 见 Proposal v3 | 改变行为 / 新增 | CHANGE-3 / CHANGE-2 | 回归 |

```text
CHANGE-3: PRESENT（Compiler 提取、状态隔离、path-aware 行为等）
CHANGE-4: PRESENT（00 §5 / 10 §4 / 20 §5.5 非目标或延后放宽）— 四道门 REQUIRED
CHANGE-5: PRESENT（20 §5.3 无条件 V3 option 边界规则删除/替换）— 四道门 REQUIRED
```

**禁止：**「不是 CHANGE-4/5 → 不需要 Gate。」

---

## 5. Native / Artifact 双路径（与 Proposal v3 §3 一致）

```text
Path A Native:  Source → … → Native Resolver → ResolvedRun → Canonical V3 IR
Path B Artifact: Source → preprocessing Artifact → Adapter/Consumer → ResolvedRun → Canonical V3 IR
```

| | Path A | Path B |
|--|--------|--------|
| Option Segmentation Authority | Native Resolver 确定性解析 | **Producer Artifact `options[]`** |
| V3 禁止 | LLM 猜边界；冒充 Path B rediscovery 许可 | **rediscovery / 第二 segmentation authority** |
| 汇聚 | ResolvedRun（唯一消费入口） | 同左 |
| IR | **语义等价、结构一致** | 同左 |

**provenance 链路（Path B）：** `options[].provenance`（输入证据）→ verification/normalization → Frozen Resolved Span → IR `source_span`；冲突 = conflict signal，不静默覆盖。

---

## 6. Provenance ontology / fail-closed（摘要）

| 主题 | 规则 |
|------|------|
| Locator | form 分型；**禁止**给 table_cell / image_region / 多来源伪造 line_ref |
| Provenance Resolution | `20 §5.2` ResolvedStatus（E 层） |
| Option/Evidence Resolution | 独立语义；不与 E 层共用字段；新 Schema 字段仅经本 CR → Owner |
| degraded | 可验证但质量下降；**非**后门；默认不得直通 Admission |
| 无法可靠验证 | unresolved / incomplete / QC_FAIL → **fail closed** |
| resolved cardinality | form **1..n**；禁止 0-span 静默通过 |
| `options_unresolved` | **从未在 L0**；禁止引入（坐标见 Proposal v3 §6.1） |

---

## 7. Gate（四道门，69 §5）— 有证据才算通过

| Gate | Requirement | Evidence | Status |
|------|-------------|----------|--------|
| **A Identity Closure** | identity 闭合；form 不破坏跨层 identity | 无 OD-01 form 级 identity 测试 | **PENDING** |
| **B Legacy / Path B 对比** | 真实 corpus 可重复对比 | 无 option provenance 对比实验 | **PENDING** |
| **C Safety Invariant** | C1–C6（immutable / no LLM admission / fail-closed pointer / span integrity / replay） | 未就新 form 重证 | **PENDING** |
| **D Adapter Boundary** | Adapter≠第二 Resolver；禁 fuzzy/自主生成 | 原则一致，无 evidence package | **PENDING** |

```text
Gate A: PENDING
Gate B: PENDING
Gate C: PENDING
Gate D: PENDING
```

**不得**用 Proposal 完成 / Owner 同意 OD-01 / DSH 无阻塞 / 设计合理替代 Gate PASS。

---

## 8. 回归要求（登记；不执行）

1. form 全集 + legacy 无 form 读取  
2. 分型 locator 真实性（禁伪造 line_ref）  
3. Path A / Path B → Canonical IR 等价  
4. Path B 禁 rediscovery 负向  
5. Provenance vs Option/Evidence status 隔离  
6. degraded 不绕过 fail-closed  
7. conflict signal  
8. text_hash / 10 §8 2c  
9. no double consumption  
10. options_lines 保留  
11. dedup 组合不变  

---

## 9. 当前状态与未授权事项

```text
CR-002 formal L1 status     = NOT REGISTERED / L1 candidate / NOT RELEASED
CR-002 document status      = NOT RELEASED
OD-01 as Frozen Spec        = NOT EFFECTIVE
Owner Authorization         = REQUIRED / NOT GRANTED
Freeze Order                = NOT ISSUED
Gate A/B/C/D                = PENDING / PENDING / PENDING / PENDING
```

**尚未获得授权：** 修改 L0 00–50 · re-freeze · 实现 · Schema migration · corpus rerun · Phase 1 · X3 · push。

**本轮允许：** Proposal v3 · 本 CR 候选 · OWNER-DECISIONS（含 OD-01R）· 治理记录。

---

## 10. 显式不主张

1. 不主张本 CR 已正式注册为 L1。  
2. 不主张 L0 已修改或已 re-freeze。  
3. 不主张四道门已通过。  
4. 不主张可开始 Phase 1 / schema / corpus / migration。  
5. 不主张修改 Gate / Admission / Question Core。  
6. 不主张 CA-002 已在 90 §11 登记（绑定未来 L0 commit）。

---

## 11. Document control

| Field | Value |
|-------|-------|
| Path | `Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md` |
| Document Type | Contract Change Record |
| Authority Level | L1（candidate；**NOT REGISTERED**） |
| Status | **NOT RELEASED** |
| Change Class | **CHANGE-4 + CHANGE-5**（并含 CHANGE-3/2/1） |
| Source Proposal | `FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md` v3 |
| Owner Authority | OD-01 + OD-01R-01…10 |
| Effective Frozen Spec | **UNCHANGED** (`b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f`) |
