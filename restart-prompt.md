# AI Tutor V3 — RESTART PROMPT

Version: v1.46
Status: **Grammar 输入来源契约已冻结** —
Gate C CLOSED + Gate B2-B 全系列 CLOSED + AnswerTokenContract 封闭
Evidence Admission Boundary + 输入来源约束落到实现层；
下一步：Gate D
Date: 2026-09-13

## 0.0 当前结论（2026-09-13 Grammar 输入来源契约冻结）

- **Grammar 输入来源契约（实现层冻结，80 号 §6.6）**：
  - `Grammar.verify()` 的 `answer_text` **必须**是 Resolver 产出的标准化 answer span
    （`resolver.py::_answer_span` 的 char-span 切片，20 §5.5），**禁止**裸 source/OCR 文本。
  - 题号前缀属 Resolver 边界产物，由 `_clean_answer()` 剥除，**不参与** token 判定。
  - **不走正式 Errata**：20 §8.4 对该点是**沉默**而非**写错**，不属 Contract Change；
    已挂入 80 §4 显式延期项，若日后写入 20 §8.4 正文须走四道门。
  - **分层职责**：Grammar 保证 representation validity，**不保证** semantic correctness。
- **测试规范固化（40 §5 新增）**：度量实验的输入必须是上游组件的**真实输出切片**，
  禁止近似文本；度量脚本须指出它复刻哪一段 pipeline，并有测试锁死该语义。
  （反例：本轮覆盖率测量曾用「行内剩余文本」代替 E 的 char-span。）

- **BUG-V3-044: Resolved + 对抗性审查通过**（80 号 §6 实现 / §7 审查）。
  - 裁决：Q-A 白名单为主；Evidence Contract **不扩大**；Evidence Promotion
    Phase 1 **不回退**；Gate D 延后至 Grammar Contract 冻结（现已冻结，阻塞解除）。
  - 题号前缀：**剥离后白名单**（20 §5.5 切片规则不动，`1. A` 仍 approve）。
  - 语料实测扩展：`【答案】D` / `（3分）D` / `D。` 三种**全串锚定**形态。
  - 全量 pytest **802 passed**；探针 C1/C2 由 auto_approve → pending_review。
- **对抗性审查发现（80 号 §7）**：
  - **真实缺陷已修**：混合括号 `（A)` 曾被接受（正则字符类 `[）)]` 允许开闭不配对）。
    已拆为全角/半角配对分支。修复过程中自引入的 `score_fw` 命名组截断 bug 同轮捕获。
  - **方法学缺陷已修**：此前覆盖率数字基于「行内剩余文本」而非 E 的 char-span 切片。
    修正后 8166 条目：single_choice 552 保持 / 261 回归（205 垃圾 + 55 解析标记
    + **1 离群点 `A;`**，不扩展白名单）；multiple_choice 546 / 320。
- **架构分层（当前完整视图）**：
  ```text
  Source Binding Boundary        ✅ Gate B / B2-B
  Evidence Authority Boundary    ✅ Gate C Phase 1
  Semantic Answer Contract       ✅ BUG-V3-044（含对抗性审查）
  Admission / Knowledge Layer
  ```
- **Gate B2-B5: CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED**
  （权威：`backend/Docs/V3_SPEC/80_B2B5_CLOSURE.md` v1.2.0）。
- **Gate B 全系列关闭或显式延期**：B1 CONDITIONAL PASS / B2-A PASS /
  B2-B1～B2-B5 CLOSED / B2-B3-C 与 B2-B4-C DEFERRED（Domain Contract）。
- **Gate B2-A: PASS / TEST-EVIDENCED（stem-only, three-task audit）**。
  - Task A: 20 Legacy-only cases 全部为 pattern coverage gap，非验证错误。
  - Task B: 150 抽样中 96% 标准题号格式，验证结果可信。
  - Task C: Legacy 47.1% vs Path B 96.8%，+49.7pp，2.1x coverage。
- **Gate C CLOSED（Phase 1 Evidence Authority Boundary Closure）**。
- **Evidence Validity ≠ Semantic Correctness**；**Legal address ≠ legal evidence**。

- **A–G / H Phase 1–8 / Phase 9 / Errata 维持 FINAL CLOSED**。
- **Phase I-3 CLOSED**：Source Evidence Preservation Layer。
- **Phase I-4 CLOSED**：Valid Negative Result——layout evidence 消歧率 0%。
- **Phase I-5 进行中**：I-5-0 → I-5-1 → 盲测 → 68/69 号 → 对抗性审查 →
  P0 Closure Pack → Step 3 裁决 → Gate A → Gate B/C → B2-B5 → BUG-V3-044 →
  **BUG-V3-044 对抗性审查（本轮）**。
- **Gate A（Identity Closure）**：**PASS / TEST-EVIDENCED**。
  - 三层 Identity 模型：Semantic Identity / Source Binding Claim / Resolved Evidence。
  - 核心结论：line_refs 属于 Source Binding Claim，不属于 Semantic Identity。
  - `_annotation_identity_projection` 剔除 `{confidence, line_refs}`；
    `_confidence_only_projection` 仅剔除 `{confidence}`（供 resolver_input_hash）。
- **状态基线（2026-09-13 对账后）**：
  - Architecture Design: **PASS WITH RESERVATIONS**
  - Core Safety Model: **PASS**
  - Local Invariants: **PASS / TEST-EVIDENCED**（802/802）
  - Cross-Boundary Invariants: **PASS / TEST-EVIDENCED**
  - Admission Atomicity: **PASS**；Admission Concurrency: **PASS — 10/10**
  - Test Isolation: **PASS / TEST-EVIDENCED**
  - Resolver Algorithm Safety: **PASS**；Resolver Real-World Coverage: **FAIL — 16.7%**
    （Legacy 搜索口径；Path B 验证口径下 stem 96.8%）
  - Path B → IR/Compiler: **PROVEN — 21/21**；→ Gate/Admission: **NOT YET PROVEN**
  - 67 Contract Change: **CONDITIONALLY ACCEPTED**（Gate A/B/C 通过；Errata BLOCKED BY Gate D）
  - OQ-1: **CLOSED**；OQ-2/OQ-3: **OPEN**
  - Full Production Pipeline: **NOT YET CLOSED**
- **Gate B1 修正后结果（2026-09-11，79 cases / 10343 role targets）**：
  - Range Validity **PASS**（100%）；Content Validity **PASS WITH RESERVATIONS**（79.0%）
  - Role Validity: stem **97.3%** / explanation **96.7%** / option **51.8%** / answer **49.1%**
  - **Gate B1 = CONDITIONAL PASS / Corpus Substantially Valid**
  - **禁止继续放宽 validator 提升数字**——那是 metric optimization
- **Contract Adjudication（2026-09-11）**：Q1=A region / Q2=B per-question evidence /
  Q3=B single span / Q4=B cell-row；**统一原则：Source Region 与 Question Evidence 必须分层**。
- **Gate B2-B 系列结果（2026-09-11/12 完成，09-13 回写）**：
  - B2-B1 option region：非 HTML 结构提取 **99.6%**（1065/1069），对抗抽样 98.0%
  - B2-B2 MC answer：extraction **99.8%**（1176/1178）；Unknown 125 **仍未清**
  - B2-B3 fill-in：原 65% 因分母污染**正式失效**；真填空 34/34 deterministic PASS
  - B2-B4 HTML：507/507 Direct targets deterministic PASS，零 HTML 解析、零 fallback
  - B2-B5 主观/子题/材料：CLOSED（706 targets / 429 representable / 157 pending_review）
  - 四条冻结原则：Address≠Authority / Claim=Promotion / Validated-only / No-inference
- **红线（不变）**：HTTP retry ≠ LLM retry ≠ fallback；先冻结 Spec 再改代码；
  Schema Source of Truth = 20_Document_Pipeline.md；Resolver 不猜；
  实验结果 ≠ 实施授权；提议修改 ≠ 违反 Frozen Spec。
- **下一步（按序执行）**：
  1. **Gate D**：Adapter Boundary（preprocessing 为可选上游，Contract Translator
     而非 Semantic Resolver；Grammar Contract 已冻结**且含输入来源约束**
     —— Adapter 不得绕过 Resolver 直送裸文本给 grammar，见 80 §6.6，阻塞解除）
  2. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决
  3. **B2-B2 Unknown 125 triage** + B2-B3-C / B2-B4-C 延期项
  4. **Phase 2 Evidence Ledger**：等真实 pipeline 压力出现后再启动
  5. **Errata Decision**（Gate D 通过后；含「Grammar 输入来源契约是否写入 20 §8.4 正文」）
  6. **Path B Full Closure E2E**（含 Provenance Golden Test + Replay 验证）
- 重启后第一任务：读本文件 → Status.md 尾 → log.md 尾 → bugs.md →
  按上述 Step 顺序执行。
- **对账教训（2026-09-13）**：B2-B1～B2-B5 的实验结果曾只写进 69 号与 docs 71–74，
  长期未回写 log.md / Status.md / restart-prompt，导致重启时误判「B2-B 未开始」。
  **实验关闭后必须同步回写四者**，否则状态文件会撒谎。
- **契约扩展教训（2026-09-13）**：白名单/校验类契约不能只按推理设计——初版
  AnswerTokenContract 按裁决字面实现后，在真实语料上误伤 62 个合法条目
  （`【答案】D` 等）。**收紧前必须在真实语料上量化覆盖率影响**，
  再据数据决定是否扩展允许形态。
- **测量语义教训（2026-09-13 对抗性审查）**：覆盖率测量必须复刻**真实 pipeline 的
  数据语义**（E 的 char-span 切片到下一 qn 前），而非「行内剩余文本」这类近似。
  错误语义会同时高估回归与低估收益。**测量脚本本身也要接受对抗性审查。**

## 1. 用途

Codex/Claude 重启后先读本文件恢复上下文。本文件只承载稳定信息：项目目标、基线状态、
强制规则、文档地图、恢复流程；最新状态细节以 `Status.md` / `log.md` 为准。
**更新约定（规则二）**：`0.0` 节结论每次更新带当前时间戳，
在对应小节下记录最近更新时刻。

## 2. 项目目标

从 V2 继承业务需求并**全量重写**（V2 需求见 `Docs/00_Requirements/
REQUIREMENTS_AND_SOLUTION.md`）：批量上传教师版 PDF/DOCX → 自动提取题目/配图/答案/
详解/元数据；题库统计分析；AI 生成题（延后）；错题本；个性化练习。V3 目标 = 杜绝
V2 的「LLM→文本→特判→Gate→回填」模式，以 Source 为唯一事实源、stage-scoped 幂等、
Replay 可重建。

## 3. 强制规则（摘要，权威在六册）

- 单主链：不建第二条 pipeline；状态只经唯一入口（decision_status → approve()/reject()）。
- Live 是组合放行：LLM/cloud OCR 须 live mode + `--allow-live` + task + budget 同时成立。
- LE key = `{task_type, stage, contract_domain, input_domain}`（不含 task_id）。
- 预算五账户正交、禁父子树；Recovery ≠ Retry；Worker 崩溃不自动重跑。
- 实现顺序、测试层级、DoD、评审红线：`40`；资产/Golden：`50`。
- **H 段**：LLMExecutor 唯一入口、Domain 不依赖 Gateway、Attempt 不可恢复续跑、Runtime/Business
  Identity 隔离（详见 plan 文件）。
