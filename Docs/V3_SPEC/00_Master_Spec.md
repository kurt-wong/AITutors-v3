# AI Tutor V3 — 总纲：重建原则、边界与反模式红线

Version: v1.2（Baseline—Frozen，2026-09-05）
Status: V3 收敛基线（00 分册，宪法）— 已落实二轮审查 6 项修正与收尾服从性验证（10/20/30/40/50 已冻结且服从本册）；正式冻结（Baseline—Frozen）
Date: 2026-09-05
Supersedes: `Docs/V3_MASTER_SPEC.md`、`Docs/V3_LESSONS.md`（起草输入，收敛后归档）

> 本分册是 V3 规范集的总纲，回答"为什么重建、边界是什么、什么不可为"。
> 字段级 schema 见 10（数据模型）、20（管线）、30（任务安全）；执行规则见 40；
> 资产迁移见 50。术语裁决以 `README.md` §2 为准。

---

## 1. 定位：V3 是重建，不是 V2 的干净重构

V3 不以修复 V2 代码为目标。V2 应作为 V3 的"失败样本库 + 资产来源"，不作为代码基础。

只继承四类内容：

1. 已确认的业务需求（`Docs/reference/REQUIREMENTS_AND_SOLUTION.md`）。
2. 已验证有效的外部能力与测试样本（OCR 双源、知识/题型种子、golden corpus、真实 PDF）。
3. V1/V2 已验证的失败教训与设计约束（本规范集与 `Docs/reference/V1_LESSONS.md`）。
4. 已验收的产品/展示契约（`DISPLAY_CONTRACT.md`、canonical question type、true_false
   映射等——这些是 V2 后期经多轮真实文档验收固化的业务语言，V3 数据模型必须能表达）。

V2 任何代码只有在满足 V3 契约并通过重新设计后的测试后才允许移植；不得因
"它是 V2 最稳定的版本"而整体搬入（典型：`simple_pipeline.py`、`content_slicer.py`、
`anchor_corrector.py`、旧 `quality_gate.py`/`admission_gate.py` R 规则）。

---

## 2. 宪法级原则（P1-P7）

### P1 — 最小闭环优先

V3 首个稳定里程碑（M1 — Core Ingestion closed loop）只建立可可靠完成以下闭环的最小系统：

```text
原始文档 → Source Version(L0/L1)
  → Semantic Annotation
  → Source Resolver → Resolved Span
  → Semantic Question IR
  → Deterministic Compiler
  → Evidence/Semantic Gate → 决策
  → Candidate → Admission Transaction
  → Question + Instance + Material + Image + Knowledge
```

闭环稳定前，不开发 AI 生成题、复杂推荐、Agent、统计富化等外围能力。

### P2 — LLM 是语义判断器，不是数据库编译器，且不拥有 Admission Authority

LLM 可以：判断题目/子题/共享材料语义结构、题型、语义关系、答案归属、难度等元数据；
对"某答案与题干是否匹配"等产生**语义验证结果与证据**。

LLM 不负责：改写原文、计算最终字符/行位置、决定数据库事务、直接写 Question、
决定是否入库、通过隐藏重试无限调用外部 API。

**LLM 可以提供语义证据，但不能拥有 Admission Authority。** Admission 权限属于确定性
的 Gate Policy。即使 LLM 声称"这道题完整"，也必须经过 Gate 的结构/来源/语义检查才能
进入 approved。

> 语义 → LLM（含语义证据）；事实来源 → Source；位置解析 → Resolver；
> 确定性转换 → Compiler；质量/Admission 决策 → Gate Policy；
> 数据库写入 → Application/Repository；异步消费 → Explicit Worker；
> 外部副作用 → Gateway + Audit + Budget。

### P3 — Source 是 Source-derived factual content 的唯一事实源

原始文件及其解析制品一旦 seal 即不可变。所有真题的题干、选项、材料、答案、详解及
图片等 **Source-derived content**，必须能够追溯至 Source Version + Resolved Span。

系统存在三类不同性质的东西，必须区分：

```text
Source Fact             原文实际存在的事实（正文/图片/答案/详解）
  ↓
Semantic Interpretation LLM 对 Source 的解释（question_type/subject/关系/difficulty…）
  ↓
Derived Domain Fact     经确定性编译/推导进入领域模型的结果（Question.subject 等）
```

- `single_choice`、`subject=physics` 等是**对 Source 的语义解释**，不是 Source 中直接
  存在的事实；它们作为 Annotation claim / Derived 结果存在，不得反向伪装成原文。
- Semantic Annotation、Question IR、Question 属于 Derived Representation，
  **不得反向修改 Source**。
- 无法证明来源的内容只能作为 `AI Generated / Inferred / Unverified` 存在，
  不得伪装成 Source-derived content 自动进入 approved 真题。

### P4 — 外部服务调用与持久化副作用必须显式

有副作用的动作，不得因启动 API / reload / 数据库恢复 / worker 重启 / 超时扫描 /
测试收集而自动发生。副作用按性质分列，避免语义混淆：

```text
Local OCR / Local embedding   = deterministic computation（非外部副作用）
Cloud OCR API / LLM API       = external service call（外部副作用）
Object Storage / DB write     = persistence side effect（持久化副作用）
Task consumption / retry      = lifecycle side effect（生命周期副作用）
```

每类动作必须有明确的执行边界与显式入口：

- 外部服务调用（Cloud OCR / LLM API）、持久化副作用（DB/Object Storage 写入）与
  生命周期副作用（Task 消费/重试）必须**可审计**；外部服务调用额外受
  Gateway + Audit + Budget 约束（见 30）。
- 本地确定性计算（Local OCR / embedding）记录 stage、版本、输入/输出 hash 与执行
  结果即可，不需要与 LLM Call Audit 同级强审计。

### P5 — 稳定性由分层不变量保证，不是补丁

V2 的核心病是"每修一个问题加一层中间件/一条特判"。V3 若某修复需要针对具体题号、
学校、题型、OCR 变体写特殊分支，一律先质疑领域模型是否缺表达能力；把样本的偶然性
写进系统必然性是被禁止的（见 §6 红线）。

### P6 — 每个阶段必须具备可判定的幂等边界（Idempotency）

Task、Logical Execution、Attempt 与持久化结果必须能区分"同一逻辑执行的重复尝试"
与"新的逻辑执行"。

```text
Task
  └── Logical Execution      ← 由 logical_execution_key 标识
        └── Stage
              └── Idempotency Key
                    ↓
                 Attempts    ← attempt_id 标识一次实际执行尝试
```

```text
logical_execution_key = task_type + stage + input_hash + contract_version + model_config_hash
```

- key **不含 `task_id`**：task_id 只指向 Task 生命周期对象，不天然等于逻辑执行身份；
  同一 Task 内对同一 stage 的重试（attempt 1 / attempt 2）共享同一个 logical execution。
- 持久化结果必须归属其 logical execution，并带 attempt_id 作为审计线索（见 30）。
- 同一 logical execution 重复执行不得产生两个不同的持久化结果（重复 Candidate /
  Annotation / Image / Instance / LLM Call）。
- 幂等键不替代 Task lease，也不等于禁止所有重复请求（详见 30）。

### P7 — Derived Data 必须可重放（Replayability）

Question、Instance、Material、Image association 等 Source-derived domain data，
必须能根据版本化的构建输入重新构建。构建输入的 version set 至少包括：

```text
Source Version
+ Annotation Schema Version + Semantic Annotation
+ Resolver Version + IR Schema Version
+ Compiler Version + Gate Policy Version
```

任何编译产物（含 Candidate 快照）必须记录它由哪一组 version set 构建。

- **Exact Replay**：相同 version set 下重放，必须得到确定性等价结果（同一逻辑执行
  不产生语义漂移）。
- **Rebuild**：更换任一版本（如 Compiler v1 → v2）允许产生新的 Derived
  Representation——这是版本演进的正常机制，不等于数据错误。

```text
Source V1 + Annotation V3 + IR V2 + Compiler V1 + Gate V1  → 确定性等价
Source V1 + Annotation V3 + Compiler V2                    → 允许新的 Derived 产物
```

Question 不是黑盒结果，而是可重放的编译结果。任何无法记录其构建 version set 的
持久化结果都不得成为唯一事实依据。这是 V3 与 V2 最清晰的分界之一。

---

## 3. 系统边界与分层职责

```text
Frontend
   ↓
HTTP API
   ↓
Application Service   ← orchestration / transaction boundary
   ↓
Domain                ← 领域规则（IR/关系/composite/candidate/question 不变量）
   ↓
Repository
   ↓
PostgreSQL / Object Storage

Explicit Worker
   ↓
Task Executor
   ↓
Application Service
   ↓
LLM Gateway
   ↓
Provider
```

### 分层职责

| 层 | 职责 | 禁止 |
|---|---|---|
| Application Service | 用例编排、事务边界、调用 Domain/Repository/Gateway/生命周期 | 承载领域判定逻辑 |
| Domain | Question IR、关系、composite 判定、Candidate/Question 不变量 | **依赖 Repository / LLM / HTTP / ORM 实现** |
| Repository | 数据访问、事务控制 | 业务规则 |
| Infrastructure | PostgreSQL、对象存储、OCR、LLM、文件系统 | — |

强制边界：

- API 进程永远不启动 Worker；Worker 是独立进程且必须显式启动。
- 业务代码不能绕过 Gateway 直接构造真实 LLM Provider。
- Domain Model/Domain Service 不得依赖 Infrastructure implementation；
  Application Service 负责跨 Domain、Repository、Gateway 的编排。
- 调用链单向：UI → API → Application Service → Domain → Repository → Infra。
- Agent 只能通过 Application Service / MCP Tool 进入，不直连 DB 或 LLM。

> 个人项目不建议把 Domain Service 定义得过重（防止重新形成 V2 的 pipeline/assembler/
> corrector/gate/manager/helper/processor 大杂烩）；大多数用例应由 Application Service
> 直接编排 Repository 与 Gateway，Domain 只保留真正需要表达领域不变量的小对象。

---

## 4. 核心领域对象

| 对象 | 定义 | 详表 |
|---|---|---|
| Source Version / Source Index | 不可变解析制品与定位索引 | 10、20 |
| Semantic Annotation | LLM 语义 claim（Derived Representation，不含坐标/正文） | 20 |
| Resolved Span / Relation | Resolver 定位结果 | 20 |
| Semantic Question IR | 已解析的题目语义与依赖（Resolver/Compiler 之间） | 20 |
| Compiled Question Snapshot | Compiler 输出，进入 Gate 的待审快照 | 20 |
| Candidate | **完整、不可变、可重放的 admission snapshot** | 10 |
| Admission Transaction | **对 Candidate 批准后的原子 materialization 事务**（动作，非状态） | 10 |
| Question | 去重后题目实体（Derived Domain Fact） | 10 |
| Question Instance | 一道题在具体来源中的出现 | 10 |
| Material | 只存一次的共享材料实体 | 10 |
| Task | 异步工作生命周期对象 | 30 |
| LLM Call Audit | 真实 LLM 请求的不可变审计 | 30 |

**Candidate 与 Admission 分离**（P0 裁决）：

- Candidate 是**对象**：一个完整、不可变、可重放的 admission snapshot，能不经重新
  运行 LLM 而重建 Question/Instance/Material/Image/Knowledge。
- Admission 是**动作/事务**：`approve(candidate_id)` 对已批准 Candidate 做一次原子
  materialization，不是独立的持久化业务对象，也不是一个"状态集合"。

```text
Question IR → Compiler → Compiled Snapshot → Gate
                                                ↓
                                       Candidate（对象）
                                         └── decision_status
                                              ├─ pending_review → 人工 decision → approve / reject
                                              ├─ approved → Admission Transaction → Question + Instance + ...
                                              └─ rejected → terminal（不留实体，写审计原因）
```

固定术语三元组（冻结）：

- **Candidate = noun**（对象：admission snapshot）
- **Admission = action**（事务：approve(candidate_id) 的原子 materialization）
- **decision_status = state**（状态值：pending_review / approved / rejected）

不再使用 "candidate/review" 这类把对象当状态的混合写法。

---

## 5. 明确非目标（M1 不做）

- 自动从错误状态恢复并重新消费任务。
- 多级自动重试链；running 超时自动回 queued。
- API 与 Worker 共进程。
- LLM 直接生成真题抽取文本。
- 用 JSONB 隐式承载整个业务模型。
- 自动扩展知识树。
- 复杂 Agent 编排；多 Provider 自动无限 fallback。
- 为兼容 V2 保留任何旧 pipeline 分支。
- 文档级表格 cell/fragment 字符粒度索引（首版只做 line + 必要 inline，见 20；待样本
  证明需要再加回）。
- **自动语义去重 / Question Family 自动聚类 / 自动知识点扩展 / 复杂统计富化**：
  exact hash 去重可作基础设施层能力，但 semantic dedup / family / merge 不阻塞 M1
  ingestion closed loop。

---

## 6. 反模式红线（V3 禁止）

```text
- API startup → worker
- worker startup → automatic recovery
- running 超时 → queued → 自动重跑
- stale → queued（无审计地把 interrupted/stale 状态重新进入 queued）
- recovery 与 retry 混为一谈（recovery 只负责把失效租约置为 interrupted，不等价于重跑）
- LLM → database direct write
- business domain → Provider direct call
- LLM output → final source text
- LLM 输出 → approved（LLM 无 Admission Authority）
- fuzzy/ambiguous match → silent acceptance
- missing evidence → guessed image/answer
- nested retry without global budget
- 为兼容保留第二条生产 pipeline
- 核心管线里针对单题号/单学校/单 OCR 变体的特判
- schema 变更无 migration
- 默认测试真实调用外部 API
- 密钥/token 硬编码或进 git 历史
- Derived data 无 source provenance 却进入 approved
```

---

## 7. 成功标准（分层漏斗，替代单点"95%"）

V3 首个稳定版本不追求单一宏观准确率，而是**在 versioned Golden Corpus 上逐层度量**，
使问题可定位到具体环节。Golden Corpus 是固定样本 + 固定预期，不是生产随机抽样；
必须版本化，样本增减或预期答案变更要有变更记录（见 50）。

```text
Golden Corpus: N questions
├─ Source 层：source seal 完整、hash 可回放（100/100）
├─ Semantic 层：unit/依赖识别一致（golden 对照）
├─ Resolved 层：Semantic Reference 解析率（exact/normalized/contextual → resolved）
├─ IR 层：Semantic Question IR valid 且 dependency 闭合
├─ Answer 层：source_located / complete / verified_correct 分列
├─ Image 层：page/bbox/provenance 关联正确
├─ Admission 层：decision_status（pending_review/approved/rejected）及原因可审计
├─ Replay 层：相同 version set 重复编译不产生语义漂移（Exact Replay）
└─ Idempotency 层：重复执行不产生重复实体/重复物化
```

硬性门槛：

1. API 启动不产生任何 LLM 调用。
2. 未显式启动 Worker，不消费任何 Task。
3. Worker 崩溃不会自动重跑任务；任务进入 interrupted 待人工 recovery。
4. 所有真实 LLM 调用均可追溯到 task/document/stage/attempt（LLM Call Audit）。
5. 每道 approved 真题均可从 Source Version 重建（Replayability，P7）。
6. composite_unit 的 shared_material 只存一次，子题通过关系引用。
7. Resolver 无法唯一定位时进入 ambiguous/unresolved，不猜第一匹配。
8. Gate 未通过进入 pending_review（待人工）或 rejected（terminal），不静默入库。
9. 常规 pytest 永不调用真实外部 API。
10. V3 核心解析管线只有一条生产主路径。
11. LLM 密钥不硬编码、不进 git；启动前校验，缺失拒绝启动。
12. 同一 logical execution 重复执行不产生重复实体（Idempotency，P6）。

---

## 8. 引用关系

- 术语裁决：`README.md` §2
- 数据模型：`10_Data_Model.md`
- 管线契约：`20_Document_Pipeline.md`
- 任务安全：`30_Task_LLM_Safety.md`
- 开发规则：`40_Development_Rules.md`
- 资产与迁移：`50_Migration_Assets.md`
- 需求基线：`Docs/reference/REQUIREMENTS_AND_SOLUTION.md`
- 展示契约：`Docs/reference/DISPLAY_CONTRACT.md`（作为已验收业务语言保留）
- V1 教训：`Docs/reference/V1_LESSONS.md`

---

## 9. 变更记录

### 2026-09-05 11:30

- 建立 00 分册 v1.0：合并起草期 `V3_MASTER_SPEC` + `V3_LESSONS`。

### 2026-09-05（架构审查落实）

- v1.1：落实跨源架构审查 9 项裁决——
  1. P3 改措辞为 "Source-derived factual content 的唯一事实源"，区分 Source Fact /
     Semantic Interpretation / Derived Domain Fact；
  2. Candidate 与 Admission 分离（Candidate=snapshot 对象，Admission=materialization 事务）；
  3. P2 明确 LLM 可提供语义证据但不拥有 Admission Authority；
  4. Recovery ≠ Retry，红线补充 stale/interrupted 无审计重进 queued；
  5. 新增 P6 Idempotency；
  6. 新增 P7 Replayability；
  7. §1 "三类继承"改"四类"（补已验收展示契约）；
  8. §3 分层职责表 + Domain 不依赖 Infrastructure + 轻 Domain Service 建议；
  9. P4 把本地 OCR 与外部副作用分列，§5/§7 补 non-goal 与 Replay/Idempotency 层。

### 2026-09-05（二轮审查，6 项修正）

- v1.2-final-candidate：
  1. P6 区分 Logical Execution（logical_execution_key，不含 task_id）与 Attempt
     （attempt_id），消除"同一 Task 两次尝试不可分"的歧义；
  2. P7 补全构建 version set（Source/Annotation Schema/IR Schema/Resolver/Compiler/
     Gate Policy），并区分 Exact Replay（同版本确定性等价）与 Rebuild（换版本允许
     新 Derived 产物）；
  3. Candidate 决策统一为 decision_status（pending_review/approved/rejected），
     冻结 Candidate=noun / Admission=action / decision_status=state 术语三元组；
  4. "第一阶段"改"首个稳定里程碑 M1（Core Ingestion closed loop）"，避免与阶段
     开发计划混淆；
  5. P4 区分 external/persistence 审计与本地确定性计算日志（降级为版本+hash+结果）；
  6. §7 明确成功标准在 versioned Golden Corpus 上分层评测，非生产随机抽样。

### 2026-09-05（收尾：服从性验证完成）

- 10（v1.2.1）/ 20（v1.2）/ 30（v1.1）/ 40（v1.1）/ 50（v1.1）均已冻结且服从本册；
  P1-P7 → 分册落实与关键闭环核对证据见 `README.md` §1.2。
- 7 份起草输入已归档至 `docs_archive/2026-09-05_v3_draft/`。
- **正式冻结（Baseline—Frozen，2026-09-05）**：全体系跨册对抗性审查无结构性冲突；
  遗留 stale 元数据已修（README §2.3 登记 Claim Round、Budget 五账户同步、00/10
  Status 刷新）；本册与 10/20/30/40/50/README 统一为 **V3 Architecture &
  Development Baseline — Frozen**。

### 2026-09-05 17:10（锚点路径 errata）

- 保留文档合并至 `Docs/reference/`（V2 架构遗留另入 `docs_archive/2026-09-05_v2_legacy/`）；
  本册引用路径同步：REQUIREMENTS_AND_SOLUTION / DISPLAY_CONTRACT → `Docs/reference/`、
  V1_LESSONS → `Docs/reference/`（仅引用修正，无正文/语义变更）。
