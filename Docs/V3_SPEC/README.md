# AI Tutor V3 — 规范集索引与术语裁决

Version: v1.1（Baseline—Frozen，2026-09-05）
Status: V3 收敛基线（索引分册）— V3 Architecture & Development Baseline — Frozen
Date: 2026-09-05
Supersedes: `Docs/V3_*.md`（7 份起草输入，已归档至 `docs_archive/2026-09-05_v3_draft/`）

> 本文档是 V3 规范集（`Docs/V3_SPEC/`）的入口：先说明分册地图，再给出跨分册的
> 统一术语裁决表，消除起草期两套来源（V3 原则文档 / V2 v0.3 契约）的命名分歧。

---

## 1. 分册地图

| 分册 | 内容 | 依赖 |
|---|---|---|
| `00_Master_Spec.md` | 重建原则、系统边界、领域对象、非目标、成功标准、反模式红线 | 无 |
| `10_Data_Model.md` | 全新库数据模型 DDL、实体关系、JSONB 边界、Candidate 快照、Admission 原子事务 | 00 |
| `20_Document_Pipeline.md` | 制品分层、Semantic Annotation 契约、Resolver、Question IR、Compiler、Gate、Answer 三字段 | 00、10 |
| `30_Task_LLM_Safety.md` | 进程边界、Task 状态机、Claim/Lease、Recovery、Retry、Gateway、LLM Audit、Budget | 00 |
| `40_Development_Rules.md` | Agent 开发顺序、复杂度预算、LLM 使用边界、测试层级、DoD | 00 |
| `50_Migration_Assets.md` | V2→V3 迁移取舍、可复用资产清单、Golden Corpus 计划 | 全部 |

阅读顺序：先 `README.md`（术语）→ `00`（边界）→ 按任务进入 `10` 或 `20` 或 `30`；
开发与测试规范统一看 `40`；资产与迁移看 `50`。

### 1.1 版本与状态（2026-09-05）

> **整体系状态：V3 Architecture & Development Baseline — Frozen（2026-09-05）**

| 分册 | 版本 | 状态 |
|---|---|---|
| `00_Master_Spec.md` | v1.2 | 宪法；冻结（Baseline—Frozen） |
| `10_Data_Model.md` | v1.2.1 | 冻结（v1.2 锚点 errata） |
| `20_Document_Pipeline.md` | v1.2 | 冻结 |
| `30_Task_LLM_Safety.md` | v1.1 | 冻结 |
| `40_Development_Rules.md` | v1.1 | 冻结 |
| `50_Migration_Assets.md` | v1.1 | 冻结 |
| `README.md` | v1.1 | 索引（本册；Baseline—Frozen） |

### 1.2 00 服从性证据（00 P1-P7 → 分册落实；收尾汇总，非重设计）

| 00 原则 | 落实分册与关键锚点 |
|---|---|
| P1 最小闭环 M1 | 20 §1 单链 / 40 §2 A-I 段与出口闸 / 50 §2 单主链 |
| P2 LLM 无 Admission Authority | 20 §8.2 唯一入口 + §8.4 grammar / 30 §12 / 40 §1 铁律 3、§4 |
| P3 Source 唯一事实源 | 10 §6.3 text 禁 LLM / 20 §4.3 禁字段 + §7.2 确定性编译 / 40 §2 D-E-F 闸 |
| P4 副作用显式 | 30 §2 进程边界 + §6 Live 放行链 + §10 audit + §11 budget / 00 §7 门槛 1-4 |
| P5 稳定由不变量保证 | 20 §3 硬边界 + §6.2 IR 不变量 / 40 §3 停表（特判即停）/ 50 §5 绝不迁 |
| P6 Idempotency | 10 §3 双列 / 30 §4+§16（`task_type` 进 key）/ 20 §4.7 + §8.2 / 40 §10 |
| P7 Replayability | 10 §9 input_identity+build_versions / 20 §7.3 normalization / 30 §16 utility / 50 §4 golden versioned |

关键闭环核对（收尾逐项，均已在冻结分册锚定）：

```text
task_type → LE hash            30 §16 / 40 §10
五账户正交预算（禁父子树）          30 §11 / 40 §10
fixture golden ≠ versioned Corpus 40 §2 / 50 §4.1
Corpus 逐层预期（防同构）         50 §4.2
Admission 唯一入口 / approve()    20 §8.2 / 30 §12 / 40 §1 铁律 3
strict-auto ↔ Allowed-Answer Grammar 20 §8.4 / 40 §2 G 段
source immutability（sealed）    10 §4 + §8 不变量 1 / 40 §2 B 段
replay tuple（Exact Replay/Rebuild）10 §9 / 20 §7.3 / 30 §16
API/Worker 进程边界             30 §2 / 00 §7 门槛 1-2
no automatic recovery/requeue    30 §3/§8 / 00 §5-§6
```

## 2. 术语裁决（权威）

起草期两套来源不一致时，以本表为最终裁决。全部为 V3 词汇；V2 词汇只用于对照。

### 2.1 管线与制品

| 裁决术语（V3 用） | 含义 | V2/v0.3 曾用 | 备注 |
|---|---|---|---|
| Source Version | 不可变解析制品版本（sealed） | Immutable Source / source version | 裁决采用 v0.3 语义：seal 后不可改 |
| Source Index | source version 下用于定位的正文/行/图片索引 | line index | — |
| Semantic Annotation | LLM 对 Source 的语义标注 | L2 / llm_annotated_markdown | 只含 claim，不含坐标/正文 |
| Semantic Reference | LLM 指认"要找哪段"，如 question_label、instruction_marker | **Anchor** | **禁用 "Anchor/Anchor Corrector" 词汇**，V2 的 anchor 修正语义作废 |
| Resolved Span | Resolver 输出的真实 source 范围 | resolved_span / line_ref 结果 | 坐标属 Resolver，不进 Annotation |
| Semantic Question IR | 已解析 question/composite 语义与依赖的中间表示 | **Question IR / IR** | 裁决加 "Semantic"，V3 不再用裸 "Question IR" 作为管线对象名（数据库实体 Question 除外） |
| Deterministic Compiler | 只做确定性编译 | content_slicer / compiler | 不做语义猜测 |
| Evidence / Semantic Gate | 判断是否允许 admission | quality_gate / admission_gate | 禁止沿用旧 R 规则思维 |
| Candidate | 未获自动入库资格的 admission snapshot | question_candidates | 必须是完整可重放快照 |

### 2.2 题目结构

| 裁决术语（V3 用） | 含义 | V2 曾用 | 备注 |
|---|---|---|---|
| standalone_unit | 可独立解答的题 | standalone_question / independent | V2 "独立题"仅指去掉共享材料可独立作答 |
| composite_unit | 共享材料 + 依赖子题的原子组 | composite / 综合题 | 任一子题不合格，整组不 approved |
| shared_material | 只存一次的共享材料 | shared_material | 不复制进子题 stem |
| content_role | 语义角色（stem/options/answer/…） | content | Compiler 按角色组装 |
| answer_status | source_located / complete / verified_correct | verified=True | 三字段独立，见 20 |
| Source-derived content | 必须溯源至 Source 的题目内容（题干/选项/材料/答案/详解/图片） | 正文内容 | 与 Semantic Interpretation、Derived Domain Fact 区分，见 00 P3 |
| Admission Authority | 决定 approved/candidate/rejected 的权限 | 无 | **属于确定性 Gate Policy，不属于 LLM**，见 00 P2 |

### 2.3 任务与外部副作用

| 裁决术语（V3 用） | 含义 | V2 曾用 | 备注 |
|---|---|---|---|
| Task | 异步工作生命周期对象 | BackgroundTask | Task ≠ LLM Request |
| Worker | 显式启动的独立进程 | document_worker | API 进程绝不启动 Worker |
| Claim / Lease | 原子领取 + 租约 | recover stale | 详见 30 |
| Claim Round（task 级） | Task 被人工放行消费一次的租约轮次 | attempt（旧义含混） | 与 `attempt_id`（LE 级，见 30 §4/§5/§16）**不同粒度、不混写**：一次 claim 可驱动多个 stage 的 LE |
| Logical Execution Key | `task_type + stage + input_hash + contract_version + model_config_hash`（不含 task_id） | 幂等键（旧含 task_id） | 标识"同一逻辑执行"；同一 Task 内重试共享，attempt_id 标识实际尝试，见 00 P6、30 |
| LLM Call Audit | 每次真实 LLM 请求的不可变审计 | llm_call 日志 | 基础设施，见 30 |
| Budget | 五账户正交：request / task / le / document / daily；LE 跨 attempt 累计；任一账户独立 reserve/settle、互不派生，**禁父子预算树** | token 预算（旧四级） | 含熔断，见 30 §11 |
| Live Mode | 显式允许真实调用的模式 | LLM_GATEWAY_MODE=live | 默认 disabled |

### 2.4 Admission：Candidate 对象、Admission 事务、decision_status 状态三分（P0 裁决）

固定术语：**Candidate = noun（对象）；Admission = action（事务）；decision_status =
state（状态）**。三者在模型中不再混用。

```text
Candidate 是对象：完整、不可变、可重放的 admission snapshot（可重建 Question/Instance/Material/Image/Knowledge）
Admission 是事务：approve(candidate_id) → 原子 materialization → 上述实体
decision_status 是状态：pending_review / approved / rejected
```

| decision_status（Candidate 状态） | 含义 | 去向 |
|---|---|---|
| pending_review | fuzzy/ambiguous/缺证据/需人工 | 人工 decision → approve / reject |
| approved | 结构/来源/语义全通过且答案达标 | 触发 Admission Transaction → Question + Instance + … |
| rejected | 明确矛盾/证据不成立 | terminal，不留实体，写审计原因 |

| V2 曾用 | 说明 |
|---|---|
| approved / review / rejected | 概念并入上表（"review"→pending_review） |
| question_candidates（部分不完整） | V3 Candidate 必须完整可重放 |

---

## 3. 本规范集的书写约定

1. 每份分册自带文件头：`Version / Status / Date / Supersedes`。
2. 变更记录统一追加到分册尾部（`YYYY-MM-DD HH:mm:ss`），禁止覆盖历史。
3. 分册只承载契约与规则，不承载项目状态/进度/验收数字；状态回写根目录
   `Status.md`、`log.md`、`bugs.md`（V3 根，取代 V2 的 `PROJECT_STATUS.md` / `LOG.md` /
   `bugs.md`）；重启恢复见根目录 `restart-prompt.md`。
4. 引用权威源：本文档指向 V2 `docs_archive/2026-09-03/00-04 v0.3` 契约作唯一遗留参考；
   正文以本规范集为准，V2 文档一律不指导新实现。
5. 术语分歧以此表为准；新增术语必须先在 §2 登记再使用。

---

## 4. 变更记录

### 2026-09-05

- 建立 V3 规范集索引；登记跨源术语裁决表（含禁用 "Anchor/裸 Question IR" 说明）。
- 二轮审查：§2.3 幂等键改 Logical Execution Key（去 task_id，attempt_id 标尝试）；
  §2.4 升级为 Candidate(noun)/Admission(action)/decision_status(state) 三分，
  状态值定 pending_review / approved / rejected。

### 2026-09-05（v1.1，收尾统一）

- §1 分册地图下增 **§1.1 版本与状态**（00 待冻结裁决；10 v1.2.1 / 20 v1.2 / 30 v1.1 /
  40 v1.1 / 50 v1.1 已冻结）与 **§1.2 00 服从性证据**（P1-P7 → 分册落实 + 关键闭环核对）。
- Supersedes 更新：7 份起草输入已归档至 `docs_archive/2026-09-05_v3_draft/`。
- **正式冻结（Baseline—Frozen，2026-09-05）**：00 转正式冻结；本册与各分册版本行统一为
  `v<ver>（Baseline—Frozen，2026-09-05）`；体系状态 = **V3 Architecture & Development
  Baseline — Frozen**。

### 2026-09-05（全体系跨册对抗性审查，收口）

- 术语表登记 **Claim Round（task 级）**，与 `attempt_id`（LE 级）粒度区分（违 §3.5 已补，
  供 30/40 使用）。
- Budget 行从"四级限额"同步为**五账户正交 + LE 跨 attempt 累计 + 禁父子树**（30 §11）。
- 记录 00/10 header Status stale 修正（服从性验证已完成，见 §1.1/§1.2）。
