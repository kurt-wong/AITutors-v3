# AI Tutor V3 — 开发规则与 Agent 执行规范（把冻结契约转译成开发动作）

Version: v1.1（Baseline—Frozen，2026-09-05）
Status: V3 收敛基线（40 分册）— 已落实 v1.0 对抗性审查 P1-1~P1-6 + 4×LOW 与冻结前 3 处文字收口，冻结
Date: 2026-09-05
Supersedes: `Docs/V3_DEVELOPMENT_RULES.md`（起草输入，归档后不再作为引用锚点）;
上位约束 `00_Master_Spec.md`（宪法级，1.2-final-candidate，收尾统一冻结）;落库/执行
身份 `10_Data_Model.md`（v1.2.1 冻结）;内容管线 `20_Document_Pipeline.md`（v1.2
冻结）;任务安全 `30_Task_LLM_Safety.md`（v1.1 冻结）;术语裁决 `README.md` §2

> 本分册**不新增架构、不新增表/字段/公式/状态机**。它只做一件事：把 00/10/20/30
> 已冻结的契约转译成 Agent / 开发者实际执行时的——**先做什么、什么不能做、什么时候
> 必须停下来、哪些测试过了才能进入下一阶段**。正文引用权威分册，不复制定义；
> 正文不引用起草输入文档的节号（该文档将归档）。

---

## 1. 定位：执行转译层

| 分册 | 问的问题 | 40 的职责 |
|---|---|---|
| 00 | 为什么重建、边界是什么 | 不重复 |
| 10 | 数据/关系长什么样 | 不重复 |
| 20 | 内容怎么被稳定产生 | 不重复 |
| 30 | 执行/LLM 如何安全 | 不重复 |
| **40** | **Agent 实际开发按什么顺序、何时停下、测到什么程度才允许前进** | **本分册** |

铁律（操作化，违反 = 停）：

1. **不移植 V2**：任何 V2 代码进 V3 前过 00 §1 四问（需求/边界/测试/兼容逻辑）；
   任何一项为否，不移植。
2. **单主链**：任何改动不得新增第二条生产 pipeline、legacy 分支、第二套解析器
   （00 §7 硬门槛 10）。
3. **状态只经唯一入口**：`decision_status` 只经 Admission Service `approve()/reject()`
   （20 §8.2/30 §12）；task 状态只经 Task Service；不得在 Service 外直写。
4. **Live 是组合放行**：真实 LLM / cloud OCR 只在 live mode + `--allow-live` + task
   上下文 + budget 同时成立时发生（30 §6），否则只准 mock/disabled。
5. **"每修一个洞加一条特判"即停**（00 P5）：修复若需针对单题号/单学校/单 OCR 变体写
   分支 → 停下，质疑领域模型表达力，先改模型再改码。

---

## 2. M1 构建顺序（每阶段的出口闸 = 能进下一段的证明）

按 00 P1 M1 链排序。**闸门未过的阶段禁止进入下一段**（防止 V2 "整体搬到最稳定版本"）。

> **前置资产清点**：A/B 开工前，先**按 50 规划的资产清单**完成可复用资产清点（OCR
> 引擎选择、真实 PDF 样本、golden 种子、知识/题型种子）。**该清点不依赖 50 分册成文**——
> 清单范围由 50 规划，而清点对象来自 00 §1 继承与 V2 已验证资产（V2 仓库现存），可在
> 50 写就前先行清点。未清点前不进入段 B（seal 依赖 OCR 引擎决策）。

| 段 | 建什么 | 权威 | 出口闸（全部过才前进） |
|---|---|---|---|
| A | 骨架：配置/密钥校验、DB + Alembic + A/B/C 表（10）、Repository、canonical hashing utility（30 §16） | 10 §3-6、30 §16 | **API 启动零 LLM（00 硬门槛 1）**；**未显式启动 Worker 不消费 Task（门槛 2）**；常规 pytest 不碰真实外部 API（门槛 9）；schema 模型测试过；hash utility 同键序同串黄金测试 |
| B | B 域 seal + line/figure 索引 | 10 §4 | seal 幂等（原始文件 hash 唯一）；line_ref 确定性；sealed 行禁 UPDATE 测试。**默认本地确定性 seal**；若启用 **cloud OCR（external）必须先有 C 段 external 闸**（30 §6/§16），否则只准本地 OCR |
| C | LLM Gateway + audit + budget 骨架（mock/disabled） | 30 §6/§10/§11 | disabled 态创建 HTTP 即失败；audit 不可变；budget 条件 UPDATE 并发测试；五账户正交实现（30 §11 禁令） |
| D | Annotation stage（Envelope/Payload、递归禁字段、Semantic Reference schema） | 20 §4、30 §4.2 | schema 校验拒绝携带 line_ref/正文；annotation (stage,hash) 幂等 + supersede（20 §4.7）；无正文入库；每题型带**段内 fixture golden**（正/反例，作种子） |
| E | Source Resolver | 20 §5 | 级联确定性；missing/ambiguous/fuzzy **永不自动**；contextual 不自动准入（20 §8.2）；fixture golden 解析率对照 |
| F | IR + Deterministic Compiler（含 dedup/occurrence/normalization） | 20 §6/§7、30 §16 | IR 不变量 1-8（20 §6.2）；per-leaf dedup + occurrence_key（20 §7.3 铁律）；text_hash raw 校验（10 §8 2c/2d） |
| G | Gate + Candidate + approve()/Admission 事务 + **Allowed-Answer Grammar** | 20 §8、10 §5.4 | 20 §9 七项验收全过；无 "approved 但未物化" 中间态测试；payload 不调 LLM 可重建测试；**strict-auto 只对"已定义 Allowed-Answer Grammar 且已有正/反例 fixture golden"的题型开放（20 §8.4）**——grammar 文档 + golden 正/反例是 G 段子任务，true_false 的 T/F↔A/B canonical 映射先补 DISPLAY_CONTRACT，未完成则该题型只走 pending_review 人工；**人工路径测试：pending_review → review_trail 追加 → approve()/reject() + 唯一入口禁直改（20 §8.2）** |
| H | Worker/task/claim/recovery/retry/预算 | 30 §3-§13 | 30 §14 灾难测试全绿（含预算 reservation 对账回收）；防双物化断言 |
| I | Golden Corpus 编排 + replay 工具 + 端到端门禁 | 00 §7、50 | 00 §7 漏斗各层在 versioned Golden Corpus 上可测；`replay` 只读比对通过 |

**段内迭代**：需求 → Domain 不变量 → 数据契约（10）→ Application Service → 实现 →
测试。禁止先写代码再反推架构。

**Golden 的两层含义（冻结，消除依赖循环）**：

```text
段内 fixture golden —— 随 D/E/F/G 随建随增的正/反例（每题型少量），作实现与改 prompt 的
                       回归种子；不是正式评测集
versioned Golden Corpus —— 00 §7 的正式评测集：固定样本 + 固定预期 + 变更记录；在
                       I 段（配合 50）汇成并版本化；段内 fixture 是它的种子
```

D/E/F 出口闸引用的"golden 对照"指**段内 fixture**；I 段与 00 §7 的评测指
**versioned Corpus**——两义从此不混。改 prompt 回归用 fixture；发布/门禁用 Corpus。

---

## 3. 复杂度预算：什么时候必须停下来重审

开发中出现任一（00 P5/§6 具体化）：

```text
新增第二条生产 pipeline / 第二套解析器
新增第三层 retry 或第二套恢复机制
新增针对题号/学校/OCR 变体的特判分支
新增"兼容 V2"的中间格式 / legacy 分支
新增无法独立测试的全局状态 / 隐式依赖
为"省一张表"把内容语义塞进 JSONB 或运行域表
绕过 approve()/唯一入口 / 绕过 Gateway 构造真实 provider"快一点写完"
在确定性阶段引入 LLM（resolver/compiler/gate 加 LLM = 架构违规）
LLM 直接写库 / 改 task 状态 / 改 decision_status
```

出现即**暂停、回 00/10/20/30 对照、改设计**，不得用补丁绕过。

---

## 4. LLM 使用边界（00 P2 操作化）

### 可以做（semantic 层）

- semantic classification / relation extraction / metadata judgment / ambiguity 检测 /
  答案归属/难度等**语义 claim**（只进 annotation payload，20 §4）。

### 不可以做

- 改写 source / 生成正文（20 §4.3 递归禁字段）；
- 决定数据库写 / task 状态 / admission / decision_status（00 P2/30 §12）；
- 隐藏 retry / 无限 fallback（30 §7/§11）；
- 证据缺失时猜行号/猜选项/猜图/猜答案（20 §5/§8；unknown 允许，禁猜填）。

### 不确定性三态

LLM 输出必须允许 `known / unknown / ambiguous`；**禁止为填满 schema 强行输出猜测**。
低置信 ≠ 决策依据（20 §8.1：confidence 仅诊断）。

### Prompt / 契约版本纪律

每个正式 prompt 带 `prompt_version + schema_version + model + test fixture`。**改 prompt
必跑该题型的段内 fixture golden**；契约升级走 build_versions → Rebuild（10 §9），不改
旧行。

---

## 5. 测试层级与契约锚点

```text
Unit → Contract → Integration → Live E2E（单独运行）
```

默认 mock 外部（30 §14）：pytest 不碰真实 LLM/OCR/网络/生产任务。

- **Contract / Golden**：验证**结构与语义契约**，不只比字符串。锚点：unit 数/结构、
  题号、composite 依赖、material 依赖、**Semantic Reference 可解析性**、options
  完整性、answer 三字段独立（20 §8.3）、image provenance（10 §8 2a-2d/IS-7）。
- **每功能强制归属声明**：一个功能必须能声明它验证 **00 §7 漏斗的哪一层**与 **20 §9
  七项中的哪条**；无法归属 → 视为 M1 延后的外围能力（统计富化/AI 生成题等），不进本期
  主链（00 §5 非目标）。
- **新功能必带**：单元 + 契约 + 错误路径测试；错误分类（§6）+ 崩溃窗口（30 §12 单事务）
  边界测试。
- **命中契约变更的功能**：必须加**契约级**测试，禁止只加字符串快照了事。

测试与分册验收映射（写测试前先读）：

| 测试面 | 验收来源 |
|---|---|
| 内容管线 | 20 §9 Reviewer 7 项验收表 |
| 分层漏斗 | 00 §7（Source/Semantic/Resolved/IR/Answer/Image/Admission/Replay/Idempotency） |
| 执行/预算/崩溃 | 30 §14 灾难测试 + §11 并发安全 + §12 防双物化 |

---

## 6. 事务、错误与崩溃窗口

- 一个业务动作必须有明确 transaction boundary：approve/物化（10 §5.4/20 §8.2）、每
  stage 产物单事务（30 §12）、幂等命中既有产物行即**复用不 UPDATE 覆盖**（30 §13，
  "materialize 复用"指 compile/annotation 幂等写返回既有行，不在物化层做第二写）。
- **禁止依赖"最后 flush 一下就算成功"**；Repository 管事务，Domain 不依赖 Infra
  （00 §3）。
- 异常分类：

```text
validation_error / source_error / provider_error / network_error
semantic_error / conflict / admission_error / system_error
```

- **禁止 `except Exception: pass`**；异常要么被显式转换为结构化失败并保留 cause，
  要么沿调用链上抛进 audit（30 §10）。

---

## 7. Observability 与首次 live

异步任务链路带 `task_id / stage / attempt_id(LE) / claim_round(task) / worker_id`
（30 §4/§5/§10）；真实 LLM 调用进不可变 audit（30 §10 字段表）。本地确定性计算
（本地 OCR/embedding/seal）记录版本 + 输入/输出 hash + 结果即可，不强审计（00 P4）。

**首次真实 LLM 冒烟定位**：在段 F（compiler 完成）之后、以 30 §6 组合放行
（live + `--allow-live` + task + budget）跑一次最小 fixture 的 live 注解——过早
（A-E 无产物可验）会空耗，过晚会把 mock 假设积压到集成期。

---

## 8. 迁移、sealed 与 spec 修改纪律

- 所有 schema 变更走 Alembic：`Model + Migration + Test + 文档`（10 §11）；禁止手工
  ALTER 当正常流程；禁止对 sealed/append-only 表覆盖式 backfill。
- V3 全新库，**不迁移 V2 任何列/镜像**（10 §11 / 00 §1）。
- **规格分册修改纪律**：00 为宪法级（1.2-final-candidate，收尾随 10/20/30 服从性验证
  完成后统一冻结）；10（v1.2.1）/20（v1.2）/30（v1.1）已冻结。改动只经两种方式：
  (a) 追加 changelog + 版本号（文字澄清）；(b) 显式 **errata**（仅修正引用/锚点，
  标注 vX.Y.Z，如 10 v1.2.1）。禁止静默改写冻结正文。

---

## 9. Definition of Done（核心功能）

同过才算完成：

- 代码完成 + schema/migration 完成；
- 单元 / 契约 / 集成 / 错误路径测试完成，覆盖率 ≥ 80%；
- 相关 contract/golden（段内 fixture，若影响则含 versioned Corpus）更新并跑过；
- **功能归属声明**（§5：验证 00 §7 哪层 + 20 §9 哪条）；
- 文档与规格引用更新（README §2 术语若新增先登记）；
- **无新增隐式外部副作用**（任何 external 都过 30 §6 放行链 + audit + budget）；
- **无新增第二条生产主链**；
- 若涉及执行/物化：30 §14 灾难测试 + 防双物化断言过；
- 密钥不硬编码、不进 git；启动前校验缺失拒绝启动（00 硬门槛 11）。

---

## 10. 代码评审红线（评审者必查）

- 术语：出现 `Anchor / corrected_line_ids / content_slicer / nearest(自动接受)` 即打回
  （README §2/20 §11）。
- **annotation 递归禁字段**：LLM 输出 schema 是否携带 line_ref / 正文 / 坐标（20 §4.3）
  ——评审者逐段检 LLM payload 定义。
- **dedup / occurrence 铁律**：`dedup_key` 是否误含 answer / shared material / question
  no. / page / source / unit（20 §7.3：Question identity ≠ Answer identity、材料不入
  子题键）；`occurrence_key` 是否误含 `question_id`。
- 幂等：任何 `(stage,hash)` 键是否误含 `task_id/attempt/worker/时间`；是否漏 `task_type`
  （30 §16）。**`task_type` 必须表示业务执行目的 / 语义执行契约**（如 `document_ingest`、
  `re-annotate`），**不得作为手工重跑 / retry / force-rerun 的幂等绕过手段**（把
  `retry-1`/`manual-retry` 之类当 task_type = 把 task 实例语义偷塞回 LE 键，即违规）。
- 状态写：是否有绕过 approve()/Task Service 直接 UPDATE 的路径（20 §8.2/30 §12）。
- 预算：是否被实现成父子树而非五账户正交；reserve/settle 是否逐账户（30 §11）。
- live：真实 provider 构造是否只出现在 Gateway 单链；测试是否默认 mock（30 §6/§14）。
- 引用一致性：正文/代码引用的 10/20/30 节号是否与冻结分册一致（防止旧节号残骸，
  参照 10 v1.2.1 errata 先例）。
- 大/深/嵌套：函数 <50 行、文件 <800 行、嵌套 ≤4（全局 coding rules）。

---

## 11. 与 P1-P7 的服从对照（00 → 40 转译）

| 00 原则 | 40 的转译 |
|---|---|
| P1 最小闭环 M1 | §2 分阶段顺序 + 出口闸 + 归属声明（§5/§9）；不超前建外围能力 |
| P2 LLM 无 Admission Authority | §4 LLM 边界 + §10 状态写/禁字段红线 |
| P3 Source 唯一事实源 | §2 段 D/E/F 闸（annotation 无正文、text_hash raw）；§6 事务；§10 dedup/occurrence 铁律 |
| P4 副作用显式 | §4 Live 组合放行 + §7 Observability 分级 + §9 DoD 无隐式副作用 |
| P5 稳定由不变量保证 | §3 复杂度预算停表（特判即停） |
| P6 Idempotency | §2 段 D/G 闸（(stage,hash) 幂等 + approve 防双物化）+ §10 幂等红线 |
| P7 Replayability | §2 段 F/G/I 闸（dedup 键、payload 自足、replay 工具）+ §8 sealed/errata 纪律 + golden 两层含义 |

---

## 12. 变更记录

### 2026-09-05

- 建立 40 分册 v1.0：收敛起草输入 + 00/10/20/30 冻结契约；转译为铁律、M1 分阶段构建
  顺序与出口闸（A-I）、复杂度预算停表、LLM 边界与 prompt/golden 纪律、测试层级与
  分册验收锚点、事务/错误/崩溃窗口、Observability、迁移与 spec 修改纪律、DoD、代码
  评审红线、P1-P7 转译对照。**不新增架构/表/字段/公式/状态机。**

### 2026-09-05（v1.1，v1.0 对抗性审查 P1-1~P1-6 + 4×LOW）

- P1-1 G 段闸补 **Allowed-Answer Grammar DoD**：strict-auto 只对已有 grammar 题型开放，
  grammar 文档 + golden 反例为 G 段子任务；true_false T/F↔A/B 映射先补 DISPLAY_CONTRACT
  （20 §8.4），未完成只走 pending_review（§2 段 G）。
- P1-2 显式区分 **段内 fixture golden 与 versioned Golden Corpus**，拆解 D/E/F 与 I 的
  依赖循环（§2）。
- P1-3 G 段闸补 **人工路径测试**：pending_review → review_trail → approve()/reject() +
  唯一入口禁直改（20 §8.2）。
- P1-4 B 段声明**默认本地确定性 seal**；cloud OCR 必须先有 C 段 external 闸（30 §6/
  §16）；§2 前置资产清点（按 50）在 A/B 前。
- P1-5 §10 补 **annotation 递归禁字段** 与 **dedup/occurrence 铁律**评审红线（20 §4.3/
  §7.3）。
- P1-6 §5/§9 加**功能归属声明**纪律（验证 00 §7 哪层 + 20 §9 哪条；无法归属 = M1
  延后外围能力）。
- LOW：正文不再引用起草输入节号（将归档）；A 段闸拆分 00 硬门槛 1/2/9；§6 "materialize
  复用"措辞改引 30 §13；§7 加首次真实 LLM 冒烟定位（段 F 后）。00 status 冻结留收尾
  统一（P1-7）。

### 2026-09-05（冻结，3 处文字收口）

- G 段闸 strict-auto 前置加"**已定义 Allowed-Answer Grammar 且已有正/反例 fixture
  golden**"（§2 段 G）。
- §2 前置资产清点改"**按 50 规划的资产清单执行清点**"，并注明清点对象来自 00 §1
  继承与 V2 仓库现存、不依赖 50 成文（§2）。
- §10 幂等红线补：`task_type` 表示业务执行目的 / 语义执行契约，**不得作手工重跑 /
  retry / force-rerun 的幂等绕过**。
- 无表/无字段/无公式/无状态机/无新增开发阶段改动。
