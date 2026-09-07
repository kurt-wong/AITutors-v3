# AI Tutor V3 — 项目状态（Status）

Version: v1.0
Status: V3 Spec Baseline — Frozen（实现未开始）
Date: 2026-09-05

> 本文件**取代 V2 的 `PROJECT_STATUS.md`**。
> **更新规范（2026-09-05 起按规则二）**：每次更新含当前时间戳，**在文档末尾按时间顺序
> 流式追加状态快照**；不覆盖既有结论、不置顶。初始「当前结论」即首条快照；最新状态 =
> 文末最新一条。细节变更进 `log.md`；缺陷进 `bugs.md`；架构规则一律在 `Docs/V3_SPEC/`。

## 当前结论（2026-09-05）

- **Status: Baseline — Frozen（实现未开始）**。
- `Docs/V3_SPEC/` 六册 + README 已冻结（00 v1.2 / 10 v1.2.1 / 20 v1.2 / 30 v1.1 /
  40 v1.1 / 50 v1.1 / README v1.1）；7 份起草输入已归档
  `docs_archive/2026-09-05_v3_draft/`。
- **实现入口**：按 `40 §2` 的 A→I 出口闸推进；**前置** = 按 `50 §3` 完成可复用资产
  清点（OCR 引擎 / 真实 PDF / 知识·题型种子 / DISPLAY_CONTRACT），再开段 A/B。

## 当前阶段

- **文档基线**：✅ V3 Baseline — Frozen（00 服从性证据：`Docs/V3_SPEC/README.md §1.2`）。
- **实现**：⏳ 未开始（段 A 骨架待建；资产清点先于段 B）。

## 关键验收（文档期）

| 项 | 状态 |
|---|---|
| 00-50 + README 收敛冻结 | ✅ Baseline—Frozen |
| 跨册对抗性审查（无结构性冲突） | ✅ |
| 起草输入归档 | ✅ `docs_archive/2026-09-05_v3_draft/` |
| 实现段 A-I | ⏳ 未开始 |

## 下一步

1. 资产清点（`Docs/V3_SPEC/50 §3`）：OCR 引擎、真实 PDF、knowledge/题型种子、
   DISPLAY_CONTRACT。
2. `40 §2` 段 A：骨架（配置/密钥校验、DB+Alembic+A/B/C 表、Repository、canonical
   hashing utility），过 A 出口闸。
3. 按 A→I 依次推进，逐段过闸（`40 §2`）。

---

### 2026-09-05 16:53:15

- **Status: Baseline — Frozen（实现未开始），不变**。
- 变更：采纳两条协作规则（计划受 V3-Spec 约束 / 状态文档末尾流式更新）——本文件自本条起
  改为**文末按时间顺序流式追加**（见顶部更新规范）。
- 其余：六册 + README 冻结、起草归档、00 服从性证据位置不变（`Docs/V3_SPEC/README.md §1.2`）。

### 2026-09-05 17:12:14

- **Status: Baseline — Frozen（实现未开始），不变**。
- **待办登记（进段 G 前完成，勿丢）**：`Docs/reference/DISPLAY_CONTRACT.md` 补
  **T/F↔A/B canonical 映射**（20 §8.4 strict-auto 前置；未完成则 true_false 只走
  pending_review）。已同步：记忆、restart-prompt、本文件三处。
- 其他已知前置：资产清点（50 §3）先于段 A/B；见顶部"下一步"。

### 2026-09-05 17:18:07

- **Status: Baseline — Frozen；实现未开始，资产清点已完成**（`Docs/reference/ASSET_INVENTORY.md` v0.1）。
- 资产两裁决：**①样本 PDF 用户自有可随时补，V3 不复制**；**②M1 启用 cloud OCR（PaddleOCR-VL）**。
- **实现顺序影响**：因启用 cloud OCR（external），40 §2 段序前置修正为
  **A（骨架）→ C（Gateway/audit/budget external 闸）→ B（seal，可用 cloud VL）**——
  B 依赖 C 完成方可启用 cloud；其余 D-I 顺序不变。token 走 `.env`，不入 git。

### 2026-09-05 17:22:41

- **Status: Baseline — Frozen（实现未开始），不变**。
- **标注源料迁移（golden 裁决更新）**：剔 2 份机器草稿，迁 15 份入
  `assets/annotations_src/`（real/3 human 验收级 + contract/5 契约标注 0.4 +
  structure/7 卷面分组）。契约标注族 + structure = 用户协助 LLM 完成的契约文档，作
  V3 结构·语义重标源料（50 §4.2），JSON 原样、PDF 仍用户自有。
- **资产清单 §3 修正**：`english/physics_2026_real_golden` 实为 `0.1-draft` 草稿（非
  human），清点误判已改。
- 资产决策三落定：① PDF 用户自有不复制；② M1 启用 cloud OCR（序 A→C→B）；
  ③ 标注源料 15 份已迁 V3。待办不变：DISPLAY_CONTRACT T/F↔A/B 映射段 G 前补。

### 2026-09-05 19:34:46

- **Status: Baseline — Frozen（实现未开始），不变**。
- **迁移物对抗性审查修正完成**：对 `assets/annotations_src/`（15 份）做第一性 × V3SPEC
  审查，检出 LLM 污染漏网——`physics_2026_chaoyang_contract_golden` 含 llm answer +
  needs_manual（物理朝阳卷无人工 answer 真值）→ 移 `quarantine/`；`math_chaoyang_contract`
  标 superseded（answer 以 human `math_real_golden` 权威）；human 版 explanation 全
  llm_fallback → 一律非真值。建 `MANIFEST.csv`（sha256 + 来源分级）+ README v0.2
  可靠性矩阵。覆盖缺口登记：大兴生物/朝阳英语/朝阳语文无 human golden，exercise×2 PDF 断链。
- 资产目录现 real/3 + contract/4 + structure/7 + quarantine/1（15 份原样 +1 已隔离）。
- 待办不变：DISPLAY_CONTRACT T/F↔A/B 映射段 G 前补；物理卷人工核对出 quarantine；
  段 D/E 前补样。实现序 A→C→B 不变。

### 2026-09-05 20:31:32

- **Status: 实现开始——段 A 完成**（规范仍 Baseline—Frozen）。
- **段 A 骨架落地**：`backend/app`（core: config+hashing；db: base/session/mixins；
  models: A/B/C 三域 19 表；repositories: sealed/append-only/decision 唯一入口防护；
  main: /health）+ Alembic baseline 0001。Gate A1–A5 **全 PASS**（26 tests / coverage 93%）。
- **缺口**：BUG-V3-001..005 登记 `bugs.md`（documents 归类 / selection_events 列 /
  embedding 模型名 / replay 措辞 / 浮点 precision），不改冻结正文。
- **下一步**：40 §2 段 C（Gateway + audit + budget external 闸）。因 A→C→B，B 的 cloud OCR
  需 C 段先完成。待办不变：T/F↔A/B 映射段 G 前补。

### 2026-09-05 20:40:02

- **Status: 实现开始——段 A 完成（经对抗审查修正）**，不变。
- **段 A 对抗性审查修正（R1–R3）**：Repository 创建候选固定 `pending_review`（30 §12 唯一
  入口无旁路）；6 处列收紧 NOT NULL（10 未标 NULL 即 required）；撤 6 列 server_default →
  python default；migration `0002`。R4–R7 作实现说明记录。27 tests / coverage 94%。
- 下一步：段 C 不变；待办不变：T/F↔A/B 映射段 G 前补。

### 2026-09-05 20:44:51

- **Status: 段 A 完成（实证复核通过）**，不变。
- 下一步：段 C 不变；待办不变：T/F↔A/B 映射段 G 前补。

### 2026-09-05 20:55:39

- **Status: 段 A 正式关闭（用户裁决 A1–A5 全通过）→ 进入 40 §2 段 C。**
- 段 A 交付不变：28 tests / coverage 99%、E1–E3 实库核验通过、B1/B2 边界如实记录
  （sealed/decision 唯一入口为应用层，DB 级 enforcement 待 Spec 授权）；BUG-V3-001..005
  挂起待 errata。
- **段 C 范围**：Gateway（disabled/mock/live 组合放行）+ audit（llm_call_audit 不可变）+
  budget（五账户）+ 运行域 4 表（tasks/task_claims/llm_call_audit/budget）——锚 30
  §6/§10/§11/§17；cloud OCR external 走同一闸（30 §16）。A→C→B，段 C 完成后方启 B cloud。

### 2026-09-05 21:18:44

- **Status: 段 C 骨架完成**（external side-effect control plane）。
- **交付**：运行域 2 表（llm_call_audit + budget，migration 0003）+ `app/ai/`（Gateway 三态
  /providers/live_guard/audit/budget 五账户原子）+ 运行域 repository。Gate C1–C4 全 PASS
  （43 tests / coverage 93%，既有 28 不回归）。BUG-V3-006（reserved 补列）登记。
- 下一步：段 B（Source Seal + OCR，cloud 走 C 闸）。待办不变：T/F↔A/B 映射段 G 前补。

### 2026-09-05 21:52:36

- **Status: 段 C 正式关闭（用户裁决 C1–C4 全通过）→ 进入 40 §2 段 B。**
- **关闭依据**：Gate C1–C4 全 PASS；**连续两遍 pytest 43 passed**（可重入修复后）；无未解决
  FAIL；实证证据 D1–D4（disabled 零 HTTP client / audit append-only Repository 层如实 /
  budget UNIQUE NULLS NOT DISTINCT 真唯一 / LE 同 hash 不同 stage 独立行）已记录。真实缺陷
  （budget 测试不可重入）已修复并重复验证。BUG-V3-006（reserved 补列）挂起待 errata。
- **段 B 范围**：Source Seal + OCR（documents/source_versions/source_lines/figures 密封 +
  cloud PaddleOCR-VL 走 C 闸）——锚 10 §1/§4 B 域、30 §16、50 §3；A→C→B 序成立，cloud OCR
  经 C 闸合法放行。
- **待办不变**：T/F↔A/B 映射段 G 前补；BUG-V3-001..006 errata 裁决；quarantine 物理卷人工核。

### 2026-09-05 22:50:58

- **Status: 段 B 骨架完成**（本地确定性 seal + 独立 OCRGateway）。
- **交付**：`app/ai/ocr/`（OCRGateway 三态 + Native/Cloud/Mock provider）+ `app/domains/source/`
  （line_index 纯函数 + SealService 幂等编排）。Gate B1–B7 全 PASS（60 tests ×2 连续两遍，
  既有 43 不回归；coverage 92%）。实证 E0–E3（sealed+stage / DB unique / raw UPDATE sealed
  rowcount 1 如实 app 层 / dup line_ref 拦截）。
- **架构边界**：SealService 不碰 audit/budget、不直调 CloudOCRProvider（P0）；OCRGateway
  与 LLMGateway 同构骨架，budget/audit full lifecycle 段 H task 驱动统一接入（如实细化）。
- **缺口**：BUG-V3-007（original_sha256 与 source_version 基数未冻结）登记 Open。
- **下一步**：40 §2 段 D（Annotation stage）。待办不变：T/F↔A/B 映射段 G 前补。

### 2026-09-05 23:07:10

- **Status: 段 B 实证对抗审查通过**（无未解决 FAIL、无结构缺陷）。
- **证据**：对抗探针 11 项全 PASS（跨事务幂等 / extract 失败→failed / hash 分层确定性 /
  integrity DB 复算 / gateway 分支 / native 行粒度观察）；66 tests ×2 连续两遍；coverage 达标。
- **登记**：BUG-V3-008（cloud OCR role/provider 值域未冻结，10 §4.2 vs OCR_PROVIDER_POLICY
  L1 双模型）Open。
- **边界记录**：seal 跨事务幂等成立、无 DB UNIQUE 并发兜底（BUG-V3-007 延伸）；同文件双
  role → 多 version（007 设计允许）。
- **下一步**：段 B 是否关闭由用户裁决；若关闭进入 40 §2 段 D（Annotation stage）。待办不变：
  T/F↔A/B 映射段 G 前补。

### 2026-09-05 23:20:46

- **Status: 段 B 正式关闭（用户裁决 COMPLETE / CLOSED）→ 进入 40 §2 段 D。**
- **交付盘点**：Gate B1–B7 全 PASS + 对抗探针 11 项全 PASS + 6 项转正式回归（66 tests ×2）+
  真实 DB 边界验证 + coverage 达标 + 无 unresolved FAIL。
- **延续 Bug**：BUG-V3-007（source_version 基数 / original_sha256 语义）+ BUG-V3-008
  （cloud OCR provider 值域）保持 Open / deferred——B 阶段不自行改 Frozen Spec，待
  Errata 统一裁决。**Open bug ≠ B failure**。
- **实现清单（按 Frozen Spec）**：Source Seal 幂等/line_ref/body_rebuild/integrity/
  sealed 禁 UPDATE / 独立 OCRGateway（P0 独占 external 入口）/ Native PyMuPDF /
  CloudOCRProvider 骨架（transport 未接线）/ BUG-V3-007/008 登记。
- **明确未实现**：PP-StructureV3 / MinIO / object storage / semantic annotation /
  resolver / compiler / gate / tasks / worker / lease / live OCR smoke。
- **待办不变**：T/F↔A/B 映射段 G 前补。

### 2026-09-06 00:41:47

- **Status: 段 D 骨架完成**（Annotation stage：forbidden-field 校验 + 幂等 + supersede）。
- **交付**：`app/domains/annotation/`（validator + service）+ snapshot_repository 扩展
  （find/set_status + required 收紧）。Gate D1–D4 全 PASS（79 tests ×2，coverage 93%）；
  DB 边界 E0–E3 实证（insert/UPDATE/UNIQUE/validator）。
- **关键纪律**：validator 只做禁字段检查（P1-a）；supersede 显式（P2-a）；mock fixture 不进
  LE（P2-b）；`created_at DESC` 是 BUG-V3-009 实现选择非 Frozen Contract。
- **延续 Bug**：BUG-V3-007/008（B 阶段延续）+ BUG-V3-009（latest 排序）+ BUG-V3-010
  （parse error payload 形态）保持 Open / deferred。
- **下一步**：段 D 是否关闭由用户裁决；若关闭进入 40 §2 段 E（Source Resolver）。待办不变：
  T/F↔A/B 映射段 G 前补。

### 2026-09-06 07:26:21

- **Status: 段 D 正式关闭（COMPLETE / CLOSED）**。此前曾因测试隔离缺陷暂时阻塞 Exit Gate
  （Temporary Gate Block — RESOLVED），修复后全量回归通过，用户裁决关闭。
- **对抗审查纠偏闭环**：对 A/B/C/D 做第一性 × V3SPEC 对抗审查，检出真实缺陷 FAIL-1
  （cross-tx 测试 cleanup 泄漏 documents 域数据污染 B seal 测试），已修复。
  FAIL-2（sealed 无 DB trigger）/ FAIL-3（三处 UNIQUE 缺失）经 Frozen Spec 原文核对后
  **撤销 FAIL**：10 §4.2 明确 sealed 由 Repository 抛错强制（实现合规）；
  semantic_annotations/admission_candidates 的 (stage,hash) UNIQUE 实已存在；
  audit idempotency_key 作用域 30 自登记 LOW 开放；document_source_versions 幂等唯一性
  归 BUG-V3-007 errata。
- **修复验证**：cleanup 改按 FK 序删净（source_lines→versions→documents）后，连续两遍
  pytest **81 passed, 0 failed**（无中间清理），DB 复查 docs=0 / vers=0 / anns=0。
  commit `fd9919a`（test，生产代码零改动）。
- **延续 Bug**：BUG-V3-001..010 全部保持 Open / deferred（不改已关闭阶段）。
- **下一步**：进入 40 §2 段 E（Source Resolver）。待办不变：T/F↔A/B 映射段 G 前补；
  BUG-V3-007/008 errata 终裁；quarantine 物理卷人工核。

### 2026-09-06 09:09:16

- **Status: 段 E 正式关闭（COMPLETE / CLOSED）**。A→E 五段齐。
- **段 E 交付**：`app/domains/resolver/`（span/reference/match_normalization/resolver，
  纯确定性 Resolver，7 role 独立 policy + 级联 + contextual + fuzzy 终点不变量）；
  `source_repository` 只读扩展（get_lines_by_version / get_figures_by_version）；
  tests（test_resolver 33 + dbflow 3）。
- **对抗审查 Correction Cycle**：检出并修复 4 FAIL——FAIL-1 题号前缀错配
  （`startswith(qn)` 误吞 10/11/12，改 bounded entry + token equality，P0 false-resolved
  消除）；FAIL-2 contextual 无 emit path（补确定性题目区边界收窄 + `initial>1→final==1`
  invariant）；FAIL-3 material 重叠未校验（补 E-owned overlap demote）；FAIL-4 inline
  同行定位（option/answer 支持 line_character）。prefix-collision 已固化为回归。
- **验证**：Gate 全 PASS；完整 pytest **114 passed ×2**（无中间清理）；不可猜测矩阵、
  确定性、input immutable、raw text_hash 均不回归；未引入 F/G/H 能力、未改 Frozen Spec。
- **登记**：BUG-V3-011（B seal 未接 figures）/ 012（跨行 text_hash 拼接未冻结）/
  013（blank/image JSON 形态未冻结）Open，不改已关闭段。
- **下一步**：进入 40 §2 **段 F（F0 Contract Audit）**——IR 装配 + ready 判定 +
  Deterministic Compiler + dedup/occurrence（20 §6/§7），不得把 IR 逻辑塞回 E。
  待办不变：T/F↔A/B 映射段 G 前补；BUG-V3-001..013 errata 终裁。

### 2026-09-06 10:59:39

- **Status: 段 F 正式关闭（COMPLETE / CLOSED）**。A→F 六段齐。
- **段 F 交付**：`app/domains/compile/`（ir/identity_normalization/compiler/snapshot——
  IR 装配 + 不变量 1-8 + Deterministic Compiler + 三 key + text_hash raw 2c/2d）；
  tests（test_ir + test_compiler 共 19）。
- **对抗审查三轮闭环**：F1 required answer（缺答案曾 ready → 现 incomplete + leaves=0）、
  F2 material dependency（target unresolved → 现 incomplete）、F3 image/blank 静默丢弃
  （现 fail-loud unsupported → incomplete，宁可拒绝 ready 不静默丢语义）均以真探针证明
  消除；F/G boundary 扫描 clean（compile 无 gate/repositories/decision_status 实际
  import）；含 blank 的 fill_in 走 incomplete 是 invariant 4 未实现 + BUG-V3-020 延后的
  诚实状态，非误 ready。
- **验证**：段 F 测试 19 passed；完整 pytest **133 passed ×2**（无中间清理，可重入）；
  负向矩阵、确定性、input immutable、canonical 直通、raw hash 均不回归。
- **登记**：BUG-V3-014..020 Open / deferred（Open BUG ≠ 当前阶段 Failure；不改 Frozen
  Spec，M1 已采用经审计的最小确定性行为）。
- **下一步**：进入 40 §2 **段 G（F0 Contract Audit）**——Gate Policy + Candidate +
  decision_status + approve()/Admission tx + Allowed-Answer Grammar。**G0 必核**：F 的
  incomplete 不得被 G 强行转 Candidate（应 not gate-eligible，否则 F3 fail-loud 被绕过）；
  DISPLAY_CONTRACT T/F↔A/B canonical 映射须先补。待办不变：T/F↔A/B 映射段 G 前补；
  BUG-V3-001..020 errata 终裁。

### 2026-09-06 13:55:25

- **Status: 段 G 正式关闭（COMPLETE / CLOSED）**。A→G 七段齐（H 及后续未授权）。
- **段 G 交付**：`app/domains/gate/`（grammar/policy/payload/admission/service——Gate 四层
  gate_decision + 冻结可重放 payload + AdmissionService 物化事务唯一入口 + GateService
  LE 幂等编排 + auto approve/reject 双自动）；snapshot/content Repository 扩展
  （_transition_decision 受控迁移 / candidate 幂等 lock / review_trail append /
  admission_event / dedup 查重复用）；G tests（grammar/policy/payload/admission/service）。
- **对抗审查 Correction Cycle（一 TRUE-HIGH + 三 TRUE-MED，全修复 + 回归）**：
  HIGH 复用 occurrence 无条件重插子行 → UNIQUE 冲突（同 sv 二次标注崩溃）——物化改
  plan/Question REUSE/occurrence 复用/全复用短回路/material dedup/仅新 instance 建行；
  MED role source_span 误记 stem 行——逐 role 自身 line_refs；MED machine-rejected 无
  自动迁移 → pending 僵尸——service.run 自动 reject(machine_gate)；MED _dedup_key 与
  Compiler 键分叉——对齐 normalize_identity。4 项均以真实 DB 回归锁死。
- **验证**：段 G 测试 66 passed；完整 pytest **199 passed ×2**（无中间清理，可重入）；
  P0-G-001/002/003 状态机探针 + 监控项（approve 只消费冻结 snapshot、不重跑 E/F/G）全绿。
- **登记**：BUG-V3-021..027 已登记 bugs.md（021/022/025 等 M1 处理）；G 对抗 4 项为已修复
  实现 bug，非 spec 域 Open BUG，不入 bugs.md 编号。
- **下一步**：段 H + worker/tasks、LLM live、knowledge resolver 均属用户排除范围，待新指令；
  待办不变：BUG-V3-001..027 errata 终裁。

### 2026-09-06 15:10:52

- **Status: 段 G 收尾——IMPLEMENTATION COMPLETE / VERIFIED**（二轮对抗审查 F1/F2 修复后）。
- **二轮对抗审查（跨提交，_audit_g2 GA1–GA6）证实并修复两缺陷（commit 8a57a92，已 push）**：
  - F1 `unit_groups.unit_type` 误用 payload IR `standalone_question` → 改从
    `candidate.unit_type`（service 已映射 A 域 standalone_unit/composite_unit，10 §6.5）；
  - F2 `create_instance` 增加 LE provenance（stage/hash/attempt_id）透传，物化从
    candidate 原样继承（copy，10 §6.2/§3），不再落 NULL；
  - 各转正一条显式 commit + 新 session reload 回归（test_admission.py，11 passed）。
- **验证**：GA4/GA5 由 FAIL 转 PASS（GA1–GA6 全绿）；完整 pytest **201 passed ×2**（无中间
  清理，可重入）；工作树已同步 origin（8a57a92），仅剩 2 个 untracked 审计探针。
- **登记**：F1/F2 为已修复实现 bug（同段 G 对抗 4 项惯例，不入 bugs.md 编号）；BUG-V3-001..027
  保持 Open 不变。
- **下一步**：段 H + worker/tasks、LLM live、knowledge resolver 未授权，待用户新指令；待办
  不变：BUG-V3-001..027 errata 终裁。

### 2026-09-06 15:14:30

- **Status: V3 Core Pipeline Baseline A–G 定格（用户裁决）——Implementation Complete and
  Verified**；commit `8a57a92` 定为 **A–G 稳定工程基线**。
- **A–G Baseline Freeze**：不再视 A–G 为"开发中"——从 Source Seal 到 A 域物化的确定性
  数据主线已闭环；F1/F2 Correction Cycle 关闭；BUG-V3-001..027 维持 Open（留 SPEC PATCH /
  NEXT BASELINE，不集中清）。
- **下一步（用户指定顺序）**：**H0 Runtime Readiness Audit**（audit only，零生产代码；
  范围 = stage/execution 身份贯穿 · Retry/Replay/New/Duplicate 语义 · LLM Live 不绕
  Gateway/audit/budget · Task vs 业务状态机维度分离 + crash 窗口）→ H Contract Audit →
  H Implementation。H/H0 均未授权，不擅动工。

### 2026-09-06 20:34:06

- **Status: H Contract Audit PASS → H Implementation Plan Final 冻结（未开始编码）**。
- **H0 Runtime Readiness Audit**（audit only，零生产代码）已落盘
  `Docs/reference/H0_RUNTIME_READINESS_AUDIT.md`（commit 8032af3）：总判 A–G = **Runtime-ready
  foundation**（非 Runtime 本身 ready）；R1 五项（attempt_id 缺失 / 并发幂等写非原子 / retry
  熔断未实现 / Gateway 非执行边界无 audit·budget / tasks·task_claims 未建）+ R2 两项
  （compile 指纹口径 / invalid annotation 归属）+ Carry-Forward Constraints ×10。
- **H Contract Reconciliation 五条最终裁决（用户下达）**：
  ① H0-2 compile 指纹维持 M1（不动 hash，BUG-V3-022 保持 Open）；
  ② H0-15 方案 B（Artifact 表只存 `valid` 成功产物，失败进 audit+task，不落 invalid 行）；
  ③ H0-3 attempt_id 由 Task Executor 分配、domain/repository 只透传；
  ④ H0-6 并发幂等写升级 `INSERT…ON CONFLICT DO NOTHING`（锚 `UNIQUE(stage,hash)`）；
  ⑤ H0-7 两层模型 `LE→Attempt→bounded internal retry`，`claim_round≠attempt_id`。
- **H Implementation Plan Final 冻结**：`~/.claude/plans/giggly-enchanting-volcano.md`，
  含 **6 Locks + 4 Notes + 3 Clarifications + 严格 Step 1–7 实施顺序**。核心边界已锁：
  LLMExecutor 唯一入口（Domain 不依赖 Gateway）、Attempt 不可恢复续跑、Runtime/Business
  Identity 隔离、Duplicate≠Discard、Replay≠New Occurrence、New Occurrence≠New Question、
  Similarity 不进 H。
- **下一步**：按 **Step 1–7** 开始 H 段编码，第一步 = **Runtime Schema**（tasks/task_claims
  + migration 0004 限定 tables + schema guard）。尚未 commit H 计划。
- **待办不变**：BUG-V3-001..027 errata 终裁。

### 2026-09-06 23:39:54

- **Status: H Step 1（Runtime Schema）实现完成 + 第一性原理对抗审查 + Remediation 关闭**。
  commit 未做（Step 1 变更尚未提交）。
- **Step 1 交付**：`models/runtime.py` +Task/TaskClaim（14/8 列，30 §17 + §5 lease）；
  `alembic/versions/20260906_0004_tasks.py`（Note-4 tables 限定）；test_models_schema._RUNTIME
  扩容；test_task_schema（schema guard）。增量库 0004 建两表，alembic 往返干净，207 passed ×2。
- **对抗审查实证（用户第一性原理要求）**：scratch 空库逐步迁移证实 **F-1**——0001/0003 全量
  metadata bootstrap 使空库 replay 时 tasks/task_claims（含 budget/llm_call_audit）由 **0001**
  建出，0004 no-op；「0004 建表」只在 A–G 时代增量库成立。F-2 guard 未锁 nullable/type/PK；
  F-3 无 from-empty/差分测试。
- **用户裁决（Closed means closed）**：F-1 选 **B**——登记 BUG-V3-028、**不修改 0001/0003/
  0004**、不重开 A–G、8a57a92 不动、不引入 checksum/ownership registry；F-2 采纳；F-3 采纳
  按 B 语义重定义。
- **Remediation**：test_task_schema 强化为结构契约（SQL type/nullable/PK/FK/Lock-1 + ORM
  contract）；新增 test_migration_replay（层 1 from-empty HEAD shape；层 2 incremental
  0003→0004 delta = +2）；0004 docstring / plan Note-4 措辞改 B 语义；bugs.md 登记 BUG-V3-028
  （Open/deferred，Owner = A–G migration history）。
- **验证**：全量 pytest **212 passed ×2**（无中间清理，可重入）。BUG-V3-001..028 Open 不变。
- **下一步**：按 plan 严格 Step 顺序进入 **Step 2 Task State Machine**（Phase 2 原子 claim +
  claim 证据同事务 + lease/zombie + recover/retry）。变更未 commit，待用户决定提交节奏。

### H Step 1 — CLOSED（基线封存，2026-09-06 23:45）

- **Implementation PASS + Known Historical Erratum Open**（非「Migration Architecture Fully
  Correct」）：Runtime Schema（Task/TaskClaim）+ migration 0004 + F-2 结构契约强化 +
  F-3 from-empty/incremental 双路径回归全部落定；212 passed ×2；from-empty replay 与
  incremental 0003→head 均实证。
- **F-1 = B 维持**：BUG-V3-028（A–G full-metadata bootstrap）**仍 Open / deferred**，
  不阻塞 Step 2；A–G 不 reopen，仅保留 migration historical erratum。
- **Step 1 is closed for implementation**；后续（H/J）再遇 migration replay 问题时，以
  BUG-V3-028 状态为准，不产生「是否已解决」歧义。

### 2026-09-07 00:04

- **Status: H Step 2（Task State Machine）实现完成 + 第一性原理对抗审查（F-2/F-1）+ 最小
  修复收口**。变更未 commit（Step 2 独立提交点待用户放行）。
- **Step 2 交付**：`runtime_repository.py` +TaskRepository/TaskClaimRepository（条件 UPDATE…
  RETURNING：claim 原子 / heartbeat / terminal / retry / recover；task_claims append-only）；
  `app/domains/task/` TaskService（状态机唯一入口，不 commit，调用方持事务——claim 的 tasks
  更新与 task_claims 证据原子同事务；Lock-1 worker_id/lease_token 只进 lease_snapshot）；
  `tests/test_task_service.py` 13 测试。
- **对抗审查实证（真 DB 探针 _audit_h2_task.py）**：**F-2（CONFIRMED）** heartbeat 只更
  heartbeat_at 不滑动 lease_expires_at，recover 只看 lease 不看 liveness——「持续健康心跳但
  运行超初始租约」的长任务会被误中断（实证：lease 已过期但刚心跳的任务仍被 recover 置
  interrupted）。**F-1（CONFIRMED，覆盖缺口）** 无真并发 claim 永久回归（P3 实证实现正确：
  恰一胜 + 单证据）。
- **用户裁决（最小修复，不改 Frozen Spec）**：F-2 采纳——heartbeat = 滑动续租（liveness
  renewal，**非 reclaim**）：`UPDATE … SET heartbeat_at=now(), lease_expires_at=
  now()+make_interval(secs=>:lease) WHERE id/worker_id/lease_token/status='running'
  AND lease_expires_at>now()`（DB now() 单源；**已过期 claim 的 heartbeat 拒** → recover
  接管）。记录为实现/状态机语义缺陷。F-1 采纳——真并发转正。default lease 60s 维持（不靠
  放大掩盖错误）。
- **修复与回归（13→17）**：repo/service heartbeat 增 `lease_seconds` 透传 + 续租 + 过期拒。
  新增 4 测试——`test_heartbeat_slides_lease_expiry`（F2-1 lease 跨事务严格后移）、
  `test_continuous_heartbeat_survives_initial_lease`（F2-2 间隔<lease 连续心跳穿过原 lease
  边界不被 recover）、`test_expired_claim_heartbeat_refused_then_recovered`（F2-3 停止心跳超
  lease → heartbeat 拒 + recover interrupted）、`test_concurrent_claim_exactly_one_winner`
  （F-1 两 session gather 并发 → 恰一 winner/claim_round=1/单证据/status=running）。
- **验证**：全量 pytest **229 passed ×2**（可重入）。探针 P1 lease 严格后移 / P2 心跳任务不被
  recover / P3 过期拒 + 停止可回收 / P4 并发恰一胜单证据，全通过。BUG-V3-001..028 Open 不变。
- **下一步**：commit Step 2（独立提交点）→ plan Step 3（Audit Lifecycle / Phase 3：
  finalize_audit exactly-once terminalization）。

### H Step 2 — CLOSED（基线封存，2026-09-07 00:04）

- **Implementation PASS + 对抗审查 F-2/F-1 最小修复已落定**：heartbeat 滑动续租（liveness
  renewal，非 reclaim，过期拒）语义经真实 DB 回归 + 探针双重实证；真并发 claim 恰一胜已转正
  为永久回归。全量 **229 passed ×2** 可重入。
- **F-2 属实现/状态机语义缺陷（非 Spec 变更）**：不改 Frozen Spec、不改 8a57a92、不重开 A–G；
  default lease 60s 维持。**F-1 为覆盖补强，非实现错误**。
- **Step 2 is closed for implementation**；A–G 七段 + Step 1/2 均不 reopen。下一实施步 =
  plan **Step 3**（Audit Lifecycle / finalize_audit exactly-once terminalization）。

### 2026-09-07 00:36

- **Status: H Step 3（Audit Lifecycle / Phase 3）实现完成 + Baseline 对抗审查 + F-1 采纳 +
  F-2 分层**。变更未 commit（Step 3 独立提交点待用户放行）。
- **Baseline 对抗审查（只读，真证据）**：llm_call_audit 现仅有 create_audit(started) +
  update_audit→AppendOnlyViolation（runtime_repository.py），无任何 terminal 路径；模型 status 无
  DB CHECK、idempotency_key 无唯一约束（runtime.py:25/39）；无生产调用方。分离两不变量——A
  「不重复写 terminal audit」= finalize 条件 UPDATE（Phase 3）；B「不重复执行/不重复建账」=
  request_id 复用(Phase 4)+attempt 贯通(Phase 5)+(stage,hash) ON CONFLICT(Phase 6)——**finalize
  no-op 不构成整体 exactly-once**。
- **审查 findings（裁决）**：F-1 采纳——finalize 缺行必须 raise，缺行≠已终态 no-op，不得被 0
  行掩盖；F-2 采纳分层——Phase 3 只供 STARTED→UNKNOWN terminalization **primitive**，「何时判
  orphan」归 Phase 4 且须绑 task lease / worker liveness（禁按 audit 年龄判死，防重蹈 Step 2
  F-2）；F-2b 采纳归 Phase 4；F-3（idempotency_key 缺「请求序」）与 F-4（usage/settle 事实源）
  carry-forward → Phase 4/5。
- **实现（零越界）**：`LlmCallAuditRepository.finalize_audit(request_id, *, status, end=None,
  tokens/cost/error_type/oversized_output)`——四态：缺行 raise AuditNotFoundError / started→
  条件 UPDATE 恰一迁移 / 已终态 no-op 返回既有终态 / 并发败者 0 行 reread 确认 terminal。
  `AUDIT_TERMINAL_STATUSES` 值域门（非 terminal → ValueError）；`update_audit` 仍抛（C2 不回归）；
  DB now() 单源（end 缺省 COALESCE now()）。未加 reconciliation/task lease/executor/budget/attempt。
- **验证**：test_audit.py 3→8（+5：三向终态化、二次 no-op 不改写 end/usage、缺行 raise、非法
  status raise、双 session 并发恰一迁移）。全量 pytest **234 passed ×2** 可重入。
- **下一步**：commit Step 3 → plan **Step 4 LLMExecutor 唯一执行入口**（Phase 4）——先
  Baseline/对抗审查（单一入口 / mock·disabled·live 同径 / retry 计数点 Provider Invocation
  Port / reserve→audit→terminal→settle 接线 / Attempt·LE 分离 / F-3 request identity 定夺）。

### H Step 3 — CLOSED（基线封存，2026-09-07 00:36）

- **Implementation PASS + 对抗审查 F-1/F-2 已裁决落定**：finalize_audit 提供 STARTED→terminal
  （completed/failed/unknown）exactly-once 原子 primitive；缺行显式 raise（不吞噬）；已终态 no-op
  （不改写）；并发恰一迁移；update_audit 仍拒改。全量 **234 passed ×2** 可重入。
- **F-2 分层**：UNKNOWN「何时判 orphan」的 recovery policy 属 Phase 4（绑 task lease / worker
  liveness，Task 是 liveness authority，Audit 是 execution record）。F-3/F-4 carry-forward。
- **Step 3 is closed for implementation**；A–G 七段 + Step 1–3 不 reopen。下一实施步 = plan
  **Step 4（LLMExecutor）**，先 Baseline/对抗审查再编码。

### 2026-09-07 13:21

- **Status: H Step 4（Phase 4 LLMExecutor）实现完成 + 三路独立对抗审查（A/B/C，R1–R12）+ P1/P2
  修复收口**。变更未 commit（Step 4 独立提交点待用户放行）。
- **Step 4 交付**：`app/ai/executor.py` LLMExecutor 唯一执行入口 + ProviderInvocationCounter
  （ensure→reserve+audit STARTED 同事务 Lock-6 → bounded retry → finalize+settle）；
  `gateway.py` live provider seam（counter.consume 在 provider 前，Lock-4/Note-1）；`errors.py`
  +BudgetSettlementError/CircuitOpen/LLMProviderError/LLMNetworkError；`models/runtime.py`
  tasks.llm_invocations + migration 0005（双路径安全）；test_executor 10 + test_budget G1–G3。
- **三路独立对抗审查（sonnet ×3 只读，冻结 diff）**：A（Runtime Authority R1/R2/R8）唯一入口无
  旁路、Gateway 职责无回归、Audit 身份一致；B（Counter/Transaction/Retry R3–R7/R9）consume seam
  唯一、Lock-6 全异常路径覆盖、Phase A/B/C commit 边界无半状态、retry taxonomy 仅 transient；
  C（Budget/Migration R10–R12）settle 失败不掩盖 provider 成功、reclaim 仅 fallback、0005
  双路径判定。**三审均无 P0**。
- **修复（1×P1 强制 + 1×P2 同批封口）**：C-1（P1）——ORM `llm_invocations` 加
  `server_default=text("0")` 对齐 0005 `DEFAULT 0`，消除 from-empty/增量 `column_default` 漂移；
  双路径 default 锁定（test_task_schema 主库 + test_migration_replay from-empty 均断言 '0'）；
  0005 docstring 改准确双路径语义。B-1（P2 fail-open）——`gateway._live` 缺 counter/task_id 改
  **fail-closed**（Lock-4 熔断不可绕过），test_gateway allowed 用例带 counter + 2 新增 denied。
- **登记（不重开）**：deferred 边界确认无破坏——D1 crash-orphan reconciliation = F-5B（延后，
  Phase 8 recover）；D2 provider exception translation = Phase 9 接线；D3 reclaim 不绑 task lease
  仅 crash/orphan fallback（F-5A）。A-2 finalize 不落 token/cost + idempotency_key 无 DB UNIQUE
  = F-4/D2 carry-forward（登记不动）。
- **验证**：定向 runtime ×2（53 passed）；全量 pytest **250 passed ×2**（净 +3：2 gateway
  fail-closed + 1 schema default 断言）；migration 双路径 from-empty→head 与 incremental rebuild
  后 llm_invocations column_default 均 '0'；git diff --check 干净。
- **下一步**：commit Step 4 → plan **Step 5**（attempt_id 贯通 + AnnotationService 依赖倒置
  Lock-3，删除 annotation Domain→Gateway 旁路）。

### H Step 4 — CLOSED（基线封存，2026-09-07 13:21）

- **Implementation PASS + 三路独立对抗审查无 P0 + P1/P2 修复落定**：LLMExecutor = 唯一 LLM 执行
  入口（Lock-3）；Provider Invocation 计数在 provider seam（Lock-4/Note-1 原子 consume）；
  reserve+audit STARTED 同事务（Lock-6）；retry taxonomy 仅 transient（LLMNetworkError/
  LLMProviderError）；settle 失败显式暴露（F-6）不掩盖 provider 成功、不重调 provider。全量
  **250 passed ×2** 可重入。
- **deferred 登记**：D1 orphan reconciliation → F-5B（Phase 8 recover）；D2 provider exception
  translation → Phase 9 接线；D3 reclaim 仅 crash/orphan fallback（F-5A）；F-4/usage·token 事实源
  与 idempotency_key DB 唯一性 → Phase 5+。
- **Step 4 is closed for implementation**；A–G 七段 + Step 1–4 不 reopen。下一实施步 = plan
  **Step 5**（attempt_id 贯通 + Domain 依赖倒置，删除 annotation Domain→Gateway 旁路）。

### 2026-09-07 14:05

- **Status: H Step 5（attempt_id 贯通 + AnnotationService 依赖倒置 Lock-3 + Phase 6 并发幂等写）
  实现完成 + 独立对抗审查无 P0/P1**。变更未 commit（Step 5 独立提交点待用户放行）。
- **交付**（plan 第 5/6 项合并为一次 Step；Phase 7 方案 B / Phase 8 TaskExecutor 明确不包含）：
  Lock-3 倒置——`AnnotationService` 只持 `LLMExecutor`，删 annotation Domain→Gateway 直连旁路
  （domains/repositories 零 gateway 导入扫描确认）；attempt_id 贯通 annotate 3 处 create +
  GateService.run → candidate（Lock-5 仅 Artifact Runtime Provenance，不进 LE hash；executor.complete
  身份参数放宽默认 None + `_complete_live` fail-closed 补 task_id/document_id/provider/model）；
  Phase 6——snapshot_repository 两 create 改 `pg_insert ON CONFLICT DO NOTHING` 锚
  `UNIQUE(stage,hash)`（valid/superseded 冲突 → 幂等返回既有；invalid 残留阻挡 valid 写 →
  RepositoryError；candidate 冲突 → re-read 返回既有）。新增 `test_h_step5_attempt_provenance` 5
  回归；既有 D/G 语义经 executor 注入保持（test_annotation_dbflow `_svc` helper；
  test_repositories 候选测试补真实 FK 父行）。
- **独立对抗审查（sonnet 只读，R-A~R-G，冻结 diff）无 P0/P1**：R-A Lock-3 无旁路；R-B attempt 不进
  business identity/LE hash/dedup/occurrence；R-C Phase 6 仅锚单 UNIQUE、FK/NOT NULL 仍抛、并发败者
  无死锁；R-D executor 参数放宽无 live 绕过；R-G D/G 既有语义 preserve。
- **deferred 登记（不重开；3 P2）**：P2-1 annotate 失败路径 invalid-over-invalid 时 RepositoryError
  遮蔽原始错误 → owner = Phase 7 方案 B（触碰同路径、失败改不落 invalid 行，自然消解）；P2-2 未跟踪
  `_audit_d.py` 旧签名（不入历史，一次性探针）；P2-3 服务层二次失败错误类型测试缺口（随 P2-1 由
  Phase 7 定夺）。
- **验证**：定向 34 ×2；全量 pytest **255 passed ×3**（净 +5，可重入）；git diff --check 干净。
- **下一步**：commit Step 5（独立基线，含本文件 + log.md + restart-prompt v1.9 收口 + P2 deferred 登记）
  → **Phase 7（H0-15 方案 B）** → **Phase 8 TaskExecutor** → Phase 9 配置常量随步补。待办不变：
  BUG-V3-001..028 errata 终裁。

### H Step 5 — CLOSED（基线封存，2026-09-07 14:05）

- **Implementation PASS + 独立对抗审查无 P0/P1 + P2 deferred 落定**：LLM Runtime Execution 收敛为
  唯一入口（Lock-3，Domain 不再直连 Gateway/Provider）；attempt_id 作为 Artifact Runtime Provenance
  贯通 annotation→gate→candidate 全链且不进 LE hash（Lock-5）；Phase 6 并发幂等写锚 UNIQUE(stage,hash)
  ON CONFLICT DO NOTHING（invalid 残留阻挡 valid，显式化原 IntegrityError 语义）。全量
  **255 passed ×3** 可重入。
- **deferred 登记**：P2-1 annotate 失败路径错误遮蔽 → Phase 7 方案 B（触碰同 D 失败路径）；P2-2
  陈旧未跟踪审计探针不入历史；P2-3 服务层二次失败测试缺口随 P2-1。D1/D2/D3/F-4 延续 Step 4 登记
  （Phase 8/9 定夺）。
- **Step 5 is closed for implementation**；A–G 七段 + Step 1–5 不 reopen。下一实施步 = plan
  **Phase 7（H0-15 方案 B）** → **Phase 8 TaskExecutor**。

### H Step 5 增补 — 第一性原理对抗审查（真 DB 探针 6/6 PASS，2026-09-07 15:40）

- 用户要求 commit 前以更强第一性原理对抗审查收口（V3 重建目标 + V3SPEC；每结论真实测试证据；不降低
  标准 / 不自合理化 / 不强行解释失败 / 不靠推测）。注：上记 14:05「CLOSED」指实现 + 首轮（sonnet
  只读 R-A~R-G）审查封冻；**commit 尚未执行、待用户放行**——本增补即放行前最后一道门。
- 新资产 `backend/tests/_audit_step5_adversarial.py`（untracked 一次性，不入 Git）6 探针：
  - **P-1/P-2** Phase 6 真并发败者（annotation/candidate）：B 阻塞于 A 未提交唯一行
    （`assert not b_task.done()` 防假绿），A commit 后 B ON CONFLICT no-op + re-read 返回胜者行 →
    恰单行、胜者 attempt 保留。×3。
  - **P-3** FK 不被 DO NOTHING 吞：非法 source_version_id → IntegrityError 照常传播。
  - **P-4** 服务层端到端：坏 provider 失败落 invalid(attempt=A) 抛原始错误；同 LE 好 provider 重试 →
    RepositoryError（服务层非仅 repo）；同 LE 坏 provider 再失败 → RepositoryError 遮蔽原始
    （P2-1 签名 DB 实证）。**P-4②③ 已转正**为永久回归
    `test_service_invalid_residue_blocks_valid_and_masks_second_failure`（P2-3 随转正关闭）。
  - **P-5** Lock-3 import-line-only 静态扫描：domains/repositories 零 gateway/provider import；domains
    唯一 app.ai = `annotation/service from app.ai.executor import LLMExecutor`。
  - **P-6** parse/forbidden 失败分支 attempt 落 invalid 行（不只 provider-error 分支）。
- **结论：无 P0/P1**。P2-1 保持 deferred（owner = Phase 7 方案 B）；P2-3 随转正关闭；IntegrityError
  契约无生产调用方（grep：仅 docstring）；approve/reject 终态幂等由 test_gate_service 覆盖。全量
  pytest **256 passed ×2**（净 +1）；probe cleanup 后无污染；变更仍未 commit。
