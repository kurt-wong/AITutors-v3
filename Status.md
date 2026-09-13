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

### 2026-09-07 20:02（H Phase 7 方案 B 实现 + commit 前第一性原理对抗审查 + 收口）

- **Status: H Phase 7（H0-15 方案 B — Annotation Artifact success-only failure policy）实现完成 +
  commit 前第一性原理对抗审查（真 DB live 探针 L1–L5 5/5 PASS）+ 用户放行收口**。变更与文档已提交
  为 Phase 7 独立基线（P2-1 正式 Closed）。
- **方案 B 交付**：annotate 失败（provider error / JSON parse error / forbidden-field validation）一律
  **不创建 invalid artifact**、失败不再占 (stage,hash)；成功路径只写 `status="valid"`；失败经
  `llm_call_audit`（provider 失败 → audit failed；返回文本后 parse/forbidden 失败 → audit completed，
  因 executor 无法预知内容校验）+ task 状态承接。service 对三失败原样传播（provider 原异常 /
  parse `ValueError` / validation `ValueError`），不吞不遮蔽（P2-1 消解）。
- **repo/executor/gate 零改动**（git diff 仅 service.py + 2 test + 新增
  test_h_step7_failure_policy.py）：历史 invalid 残留防御保留（snapshot_repository 原样；
  S7-history / Q-3 实证 repo 直插 invalid 仍阻挡同 LE valid → 须新 LE）。
- **回归**：`test_h_step7_failure_policy.py` 6 测试锁死 S7-1..S7-6（provider 0 artifact 原异常 /
  parse 0 artifact ValueError / forbidden 0 artifact ValueError / fail→fail→success 同 LE 收敛恰 1 valid
  / 二次 provider 失败仍原异常 = P2-1 Closed 证据 / success 后同 LE retry 幂等复用）；
  test_annotation_dbflow / test_h_step5 既有 D/G 语义经 executor 注入保持。
- **commit 前对抗审查（mock 覆盖空洞实证填补）**：既有 Phase 7 测试全走 gateway mock 分支（无
  audit/budget 副作用，G4）——plan 语义区分从未在真实 live 链路证据化。新资产
  `backend/tests/_audit_phase7_live.py`（untracked 一次性，不入 Git）live executor × service × 真
  task/document/source 探针 L1–L5 **5/5 PASS**：L1 parse→audit completed + 0 artifact（error_type=None）；
  L2 provider→audit failed/network_error + 0 artifact + budget release；L3 forbidden→audit completed +
  0 artifact；L4 同 session fail→success 同 LE → 恰 1 valid + audit=[failed,completed]（无悬挂）；
  L5 成功后同 LE retry → find_existing 命中、不重调 provider、audit/invocation 不增（幂等不重复计费）。
- **两个 Note 登记（非 Phase 7 blocker → Phase 8 Required Handoff）**：
  **H8-1**——plan L238「parse 详情经 error_type 承载」未落地（L1 实证 completed 行 error_type=None；
  executor 返回后即 finalize，audit append-only 不可补记）→ **Phase 8 TaskExecutor 须把 parse/
  validation 失败详情写入 task failure，否则丢失**；**H8-2**——forbidden 分支 audit 态 plan 未显式
  冻结（L3 实证自然归 completed）→ Phase 8 冻结双层失败语义（llm_call_audit = Provider Invocation
  Runtime Truth；task = Logical Execution Outcome；`LLM completed ≠ Logical task completed`），
  parse/forbidden 在 Runtime 层判 failed、audit 维持 completed。
- **验证**：全量 pytest **261 passed ×2**（净 +6：S7 六测试，可重入，无中间清理）；真 DB 探针
  cleanup 后无污染；git diff --check 干净。
- **deferred 状态**：**P2-1 Closed**（遮蔽随方案 B 消解）；**P2-3 Closed**（随转正测试）；
  P2-2（未跟踪陈旧探针）不入历史；D1 crash-orphan reconciliation / D2 provider exception translation /
  D3 reclaim fallback / F-4 usage·token 事实源 + idempotency_key DB 唯一 = 延续 Step 4 登记
  （Phase 8/9 定夺）。BUG-V3-001..028 Open 不变。
- **下一步**：进入 plan **Phase 8 TaskExecutor**（plan 末步，最后接编排）——承接 H8-1/H8-2
  （downstream failure → task failure persistence + audit/task 双层失败语义冻结）；Phase 9 配置常量
  随步补。

### H Phase 7 — CLOSED（基线封存，2026-09-07 20:02）

- **Implementation PASS + commit 前第一性原理对抗审查（live 真 DB 探针 L1–L5 5/5）+ 用户放行**：
  Annotation Artifact persistence policy 已切换为 **success-only**——失败 attempt 不再创建 invalid
  artifact；失败由 Runtime Execution Layer（audit + task）承担而非 Artifact 状态承担。**P2-1 正式
  Closed**（遮蔽消解）；repo 级历史 invalid 残留防御未误伤。全量 **261 passed ×2** 可重入。
- **Phase 8 Required Handoff 登记（H8-1 / H8-2）**：下游失败（parse/validation/forbidden）须写入 task
  failure（H8-1）；audit（Provider Invocation Runtime Truth）与 task（Logical Execution Outcome）双层
  失败语义冻结，`LLM completed ≠ Logical task completed`（H8-2）。两者均不阻塞 Phase 7、不改 Phase 7 代码。
- **Phase 7 is closed for implementation**；A–G 七段 + Step 1–5 + Phase 7 不 reopen。下一实施步 = plan
  **Phase 8 TaskExecutor** → **Phase 9 配置常量随步补** → H 段最终收口。

### 2026-09-07 20:49（H Phase 8 TaskExecutor 实现 + 独立对抗审查 + 修复收口）

- **Status: H Phase 8（TaskExecutor + Worker CLI）实现完成 + 独立对抗审查（0 CRITICAL）+ 修复收口**。
  变更未 commit（Phase 8 独立提交点待用户放行）。
- **交付（plan Phase 8）**：
  - `app/domains/task/executor.py` `TaskExecutor`（Worker 循环编排，只拥 Runtime Authority）：
    `run_once` → `claim_next`（原子 claim）→ 逐 stage（Seal → Annotation → Compile，每个独立
    session 事务，30 §12 崩溃窗口只在 stage 边界）→ `complete`/`fail`。Seal 不分配 attempt
    （plan Phase 5：SealService 本轮不碰）；Annotation/Compile 分配 `attempt_id`（Lock-2：复用
    由 domain service LE 幂等保证，不落新 attempt）。
  - `app/worker/__init__.py` + `__main__.py` Worker CLI：`run`（safe 默认 mock/disabled）/
    `run --allow-live` / `recover [--dry-run|--confirm]`（默认 dry-run 安全）/ `retry <task_id>`。
  - `runtime_repository.py` `TaskClaimRepository.finalize_claim`（受控 claim 终态迁移：写
    outcome/error_type/end + lease_snapshot 并入 error_detail，H8-1）+ `TaskRepository.next_queued_id`。
  - `task/service.py` `TaskService.claim_next` + `complete`/`fail` 扩展写 claim 终态 + lease_seconds
    从 `settings.task_claim_lease_seconds` 读（Phase 9 常量落地）。
  - `config.py` Phase 9 常量（worker_concurrency=1 / task_claim_lease_seconds=60 /
    http_retry_count=2 / provider_fallback_enabled=False）。
  - `test_task_executor.py` 6 测试（端到端 / replay 复用 / provider·parse 失败 / claim 终态）。
- **H8-1/H8-2 落地**：下游失败（parse/forbidden/provider）经 `TaskExecutor._classify_error`
  分类（V3Error→error_type / ValueError→validation_error / 其它→system_error）+ `TaskService.fail
  (error_type, error_detail)` 持久化到 task_claims（outcome=failed + error_type +
  lease_snapshot.error_detail）。双层失败语义：audit 由 executor 终态化（completed/failed），
  task 由本层判 failed（`LLM completed ≠ Logical task completed`）。
- **独立对抗审查（sonnet 只读，0 CRITICAL / 1 HIGH / 2 MEDIUM / 3 LOW）**：
  - 边界确认：TaskExecutor 未越权（不碰 decision_status / 不判 Question Identity / 不形成第二
    主链）；Lock-2 attempt 复用由 domain service LE 命中提前返回保证；finalize_claim SQL（JSONB
    `||` 合并 + `outcome IS NULL` 条件 + 参数化）正确、并发恰一迁移。
  - **HIGH（已修复）**：Worker 从不续租——`_process` 逐 stage 前接入 `_heartbeat`（滑动续租），
    防长 stage 越过 60s lease 被 recover 误判 interrupted。
  - **MEDIUM（已修复）**：`run_once` 原 `except BaseException` 吞 CancelledError/KeyboardInterrupt/
    SystemExit → 改 `except Exception`（取消信号正常传播）。
  - **测试隔离（已修复）**：test_task_executor 依赖「tasks 表无残留 queued」，但 test_task_service
    用独立 session commit 不 cleanup → 残留 queued task 被 next_queued_id 误 claim；`_cleanup` 改为
    测试前+后清理。
- **deferred 登记（不重开；审查边界项）**：
  - **D1** claim_next 把「无 queued」与「claim 竞争失败」混为 None → run_once 提前停止循环
    （M1 worker_concurrency=1 无并发不触发；worker_concurrency>1 时须区分）。
  - **D2** config 三字段（worker_concurrency/http_retry_count/provider_fallback_enabled）M1 预留
    未接线（plan Phase 9「常量进 settings」预留语义；http_retry_count 与 llm_request_retry_count
    分层，HTTP 传输层 retry 未接）。
  - **D3** file_path 信任边界（arbitrary file read）——未来 enqueue 入口暴露给外部输入时须校验路径。
  - **D4** finalize_claim 缺行 no-op vs finalize_audit 缺行 raise 不对称（正常流程不可触发，
    一致性观察）；recover 置 interrupted 不写 claim 终态（Recovery ≠ Retry，保留开放 claim 证据）。
  - **D5** live 长 LLM stage（bounded retry 可越 60s lease）内持续 heartbeat 未接——stage 边界
    heartbeat 只覆盖 M1（mock/native 快）；live smoke（transport 接线后）须接后台 heartbeat 或提升 lease。
- **验证**：全量 pytest **267 passed ×2**（净 +6，可重入）；git diff --check 干净；Worker CLI
  `--help` smoke 通过；真 DB 探针（claim→running + heartbeat 续租 + run_once→succeeded）实证。
- **下一步**：commit Phase 8（独立基线）→ **Phase 9 配置常量随步补**（已补 config 常量，剩余
  HTTP retry/fallback 接线与 D 项定夺）→ H 段最终收口。待办不变：BUG-V3-001..028 errata 终裁。

### H Phase 8 增补 — 第一性原理对抗审查（真 DB 探针 7/7 PASS，2026-09-07 21:02）

- 用户要求 commit 前以第一性原理 × V3SPEC 对抗审查（每结论真实测试证据；不降标准 / 不自合理
  化 / 不强行解释 / 不靠推测）。新资产 `backend/tests/_audit_phase8_adversarial.py`（untracked
  一次性，不入 Git）7 探针全 PASS，实证 Phase 8 核心不变量：
  - **P1 Lock-2 Attempt 只在真执行**：同 file_path 二次 ingest（等价 replay）→ annotation/
    candidate `attempt_id` 保留首次值、零新增 artifact（复用不落新 attempt）。
  - **P2 live provider 失败双层语义（H8-2/H8-1）**：live gateway + 抛 `LLMNetworkError` 的
    provider → audit 恰 1 条 `failed`/`network_error` + task `failed` + claim 证据
    `outcome=failed`/`error_type=network_error` + `lease_snapshot.error_detail` 持久化 + 0 artifact。
  - **P3 live parse 失败双层语义（H8-2/H8-1）**：live 返回坏 JSON → audit `completed`（provider
    成功返回文本）+ task `failed` + claim `error_type=validation_error` + error_detail 持久化
    （`LLM completed ≠ Logical task completed` 实证）。
  - **P4 30 §12 每 stage 单事务**：seal 成功 + annotation 失败 → document/source_version 保留
    （seal 已 commit）+ annotation 0 行 + task failed（崩溃窗口只在 stage 边界）。
  - **P5 finalize_claim 并发 exactly-once**：两并发 `finalize_claim`（同 claim_round）→ 恰一行
    `outcome=failed`（`outcome IS NULL` 条件写恰一迁移）。
  - **P6 静态 Runtime Authority 边界**：executor/worker 零业务决策模块 import（content_repository/
    gate.admission/compile.ir/compiler/gate.policy/resolver）+ 零 `.decision_status` 属性访问 +
    `LLMExecutor` 唯一入口。
  - **P7 crash 恢复链路（30 §8/§3/§13）**：claim 后崩溃（lease 置过期）→ recover 仅置
    interrupted 且不产生内容（doc=0）→ retry → re-run → seal 复用 + annotation/compile 继续 +
    task succeeded + Question/Instance 各 1（Recovery ≠ Retry，replay 复用）。
  - **如实记录**：P6 初版字符串匹配误报（executor.py docstring「不判 decision_status/Question」
    被当作触碰）→ 修正为精确检查（import 语句 + `.decision_status` 属性访问）后 PASS；Grep 核验
    `decision_status`/`Question` 仅在 executor.py:14 docstring、非实际触碰。此修正非自我合理化。
- **结论：无 P0/P1**。7 探针全 PASS；Phase 8 核心不变量（Lock-2 / H8-1 / H8-2 / 30 §3/§8/§12/§13 /
  Runtime Authority）经真实 DB 实证；此前 sonnet 审查 1 HIGH + 2 MEDIUM 修复均被探针覆盖验证。
- **验证**：全量 pytest **267 passed** 不变；探针 cleanup 后无污染；`_audit_phase8_adversarial.py`
  不入 Git（留磁盘）。变更仍未 commit（待用户放行）。

### 2026-09-07 22:02（V3 全量第一性原理对抗审查 + 综合裁决）

- **Status：H Final Closure BLOCKED**。用户对全量对抗审查（4 路并行只读 + 13 真 DB probe + 纯函数
  复现 + 267 passed）下达综合裁决：**V3 不存在架构性推翻问题**；核心不变量（Source 唯一事实源 /
  stage 幂等 / 单主链 / 三 key 铁律 / LE 不含 task_id·attempt / 运行时双层语义 / decision_status
  唯一入口 / raw text_hash）经真实 DB 实证成立。**A–G 继续 CLOSED**（不因 post-closure 发现缺陷而
  reopen）；H Phase 1–8 = substantially complete，但 **H Final Closure BLOCKED**，Phase 9 PAUSED。
- **4 个确认 HIGH（真 DB probe FAIL / 纯函数复现实证）**：
  - **H-1** seal/document 并发幂等无 DB UNIQUE 兜底（read-then-create → 并发 seal 重复，真 DB
    并发 probe FAIL：2 doc）——须先终裁 BUG-V3-007 再决定 UNIQUE 作用域，禁随意加 global UNIQUE。
  - **H-2** 非 dict 合法 JSON 落 valid artifact（validate 只查禁字段不查顶层 dict，真 DB probe
    FAIL：`[]`→`status=valid`）——最小修复：顶层 `isinstance(dict)` 校验，非 dict 走方案 B 失败路径。
  - **H-3** Resolver 表头判定用非锚定子串「答案/解析/详解」，题干含词误判区界 → 错误 ResolvedSpan
    （违反「E 可以失败但不能猜」）——须先冻结最小 Header Grammar 再改锚定。
  - **H-4** composite shared material 未纳入 provenance 白名单，contextual 材料可 auto approve
    （违反「任一 role 为 contextual 不得自动准入」）——最小修复：provenance 统一评估所有物化 role。
- **3 个新增 closure blocker（用户额外裁决）**：
  - **B-1** `ai/executor.py` 仍 `except BaseException`（吞 CancelledError，audit 误 terminalize 为
    failed 与 task runtime truth 不一致）——逐处判断 catch/cleanup/terminalize/re-raise 边界。
  - **B-2** TaskExecutor `seal_provider` 与 extractor 可能不一致（task_params 声明 cloud 但实际
    NativeTextProvider）——M1 禁「声明 cloud 实际跑 native」，须 fail-closed 或正确构造 provider。
  - **B-3** `model_config_hash` 可能与实际 invocation 配置漂移（default hash vs task_params 覆盖
    provider/model）——model_config_hash 必须代表实际 invocation 配置，非默认配置。
- **2 个 MEDIUM 升级为 closure blocker**：complete/fail 不严格验证 lease ownership（旧 worker 误
  改新 worker 状态）；audit terminalization 与 budget settle 同事务 rollback 风险（settle 失败把
  audit 回滚成 STARTED 孤儿）。
- **修复顺序（用户裁决）**：Batch 1 = H-2（dict 校验）+ H-4（material provenance）+ H-3（先冻结
  Header Grammar）；Batch 2 = BUG-V3-007 终裁 → H-1（DB UNIQUE + ON CONFLICT + 并发 probe）；
  Batch 3 = H Runtime（BaseException/lease ownership/audit-settle 边界/model_config_hash identity）；
  Batch 4 = H Final Adversarial Re-Probe（N passed + 0 known HIGH + 0 unreviewed P1）。
- **MEDIUM/LOW 分层（用户裁决）**：Phase 9 前处理 = budget settle 校验 / task_context·budget_ok
  wiring / live 长 stage heartbeat / gate_decision nullable 对齐 / migration BUG-V3-028 / optional
  role / original_question_type / option label 丢失。Deferred 保持 = D1 claim 竞争 / D3 file_path /
  D4 recover claim finalization / D5 持续 heartbeat / nested composite / material text_hash /
  annotate 并发重复 / recover 时钟双源 / created 未使用。
- **严禁（10 条）**：不重设计架构 / 不 reopen A-G / 不迁移历史 LE hash / 不随意加 global UNIQUE /
  不把 task_id·attempt 加入业务 identity / Resolver 不用 LLM 猜 boundary / 不因 LLM 异常自动造事实 /
  不提前实现 live transport / 不引入大型 framework / 不把 D1/D3/D4/D5 升级为 blocker。
- **下一步**：登记裁决（本文件 + bugs.md 登记 4 HIGH）→ Batch 1 最小修复（H-2/H-4 直接修；H-3 先
  提 Header Grammar 冻结方案供裁决）→ Batch 2-4。BUG-V3-001..028 Open 不变（含 BUG-V3-028 延续）。

### 2026-09-07 22:xx（Batch 1 CLOSED + BUG-V3-007 终裁）

- **H Batch 1 = H-2 + H-3 + H-4 修复闭环**。用户批准 CLOSED；全量 pytest **308 passed**（净 +41），
  git diff --check 干净。H-2/H-3/H-4 三个 HIGH 修复落定（BUG-V3-030/031/032 标 Resolved）。
- **H-2 修复**：`validate_annotation_payload` 顶层加 `isinstance(payload, dict)`，非 dict 走方案 B
  失败路径（BUG-V3-030 Resolved；`test_s7_non_dict_json_rejected`）。
- **H-3 修复**：冻结 Header Grammar——`is_answer_header`/`is_explanation_header`（行首锚定 + 完整
  token + 显式白名单），替换 Resolver 6 处 substring 判定（`_qzone_end`/`_region_end`/`_answer_span`/
  `_explanation_span` 统一 grammar）。正例（裸 token/冒号/bracket）、负例（「参考答案如下」「试题
  答案」「请写出正确答案」等 20+ 项）+ 端到端「题干含答案不误判」全锁（BUG-V3-031 Resolved；
  `test_resolver_header_grammar.py` 39 项）。
- **H-4 修复**：`policy.evaluate` provenance 层把 shared material 纳入 resolution 白名单（BUG-V3-032
  Resolved；`test_composite_material_contextual_not_auto`）。
- **BUG-V3-007 终裁（用户 Final Ruling）**：`original_sha256` 定义 Source/Document Identity，**不
  定义全局唯一 Sealed Version**；同一 sha256 允许多 sealed version；跨 frozen seal role/provider
  合法共存不视为 duplicate；同 `original_sha256 + seal role/provider scope` 内 canonical sealed
  version 至多一个；**禁 `UNIQUE(original_sha256)`**；不得擅自引入 Frozen Spec 未定义的 identity
  字段。
- **当前状态**：H-2/H-3/H-4 CLOSED；**H-1 BLOCKED**（BUG-V3-007 已终裁，待 Batch 2 按终裁设计
  scoped uniqueness）；Runtime blockers（BaseException/lease ownership/audit-settle/model_config_hash）
  属 Batch 3；Phase 9 NOT STARTED。
- **下一步**：commit Batch 1（独立提交点）→ Batch 2（H-1：BUG-V3-007 终裁 → identity scope
  verification → scoped DB uniqueness → 并发 seal probe → regression）。

### 2026-09-07 22:xx（Batch 2 = H-1 CLOSED）

- **H-1（BUG-V3-029）Resolved**。Batch 2 Step 1-5 完成：Identity Scope Verification（Case A：
  当前字段足够，LE Identity 已编码 original_sha256 + role + provider）→ Constraint Design（用户
  批准）→ Migration 0006 + ON CONFLICT → 并发 seal probe → 全量回归。
- **约束冻结**：`documents.UNIQUE(original_sha256)`（Source/Document Identity，一个原始文件一个
  主档，放行）+ `document_source_versions.UNIQUE(logical_execution_stage, logical_execution_hash)`
  （Seal Version canonical uniqueness，跨 role/provider 多 version 合法）+ 禁
  `document_source_versions.UNIQUE(original_sha256)`（Seal 层全局唯一）。
- **实现**：migration 0006（DO 块 IF NOT EXISTS 双路径安全）；`create_document`/`create_source_version`
  改 `pg_insert ON CONFLICT DO NOTHING` + re-read；`SealService` 并发收敛（re-read sealed → 复用）。
- **验证**：全量 pytest **310 passed**（净 +2：`test_h_seal_concurrency` 并发收敛 + 跨 role 多
  version）；真并发 seal 恰 1 doc + 1 version + 无重复 line。
- **当前 H Closure 状态**：H-1/H-2/H-3/H-4 全 Resolved（4 HIGH 关闭）；剩余 Runtime blockers
  （ai/executor.py except BaseException / complete-fail lease ownership / audit-settle rollback /
  model_config_hash 漂移）属 Batch 3；Phase 9 NOT STARTED。
- **下一步**：commit Batch 2（独立提交点）→ Batch 3（H Runtime correctness）。

### 2026-09-07 22:xx（Batch 3 = H Runtime correctness 完成）

- **Batch 3 = 4 个 Runtime blocker 逐个修复（4 个独立 commit）**，全量 pytest **314 passed**（净 +4）。
  - **3-1 cancellation semantics（94f74c8）**：`ai/executor.py` Phase B/C `except BaseException` →
    `except Exception`（CancelledError 传播，audit 保持 STARTED 由 recovery 判 unknown）。
  - **3-2 lease ownership（1e58710）**：`TaskRepository._terminal` 补 `lease_expires_at > now()`
    （与 heartbeat 一致，过期 worker 不得改终态）。
  - **3-3 audit/settle boundary（2f40514）**：`_complete_live` Phase C 拆两事务（audit
    terminalization C1 先行 commit，settle C2 后行失败不回滚 audit，30 §10/§11 + F-6）。
  - **3-4 model_config_hash identity（617da01）**：`TaskExecutor._annotation_stage` 的
    model_config_hash 编码实际 provider/model（30 §7：不同 provider/model → 新 LE），杜绝 identity 漂移。
- **4 个 HIGH + 4 个 Runtime blocker 全部关闭**。每个 blocker 带 adversarial regression：
  cancellation（CancelledError 传播 + audit STARTED）、lease（过期 complete/fail 拒 + recover）、
  audit-settle（settle 失败不回滚 audit）、model_config（不同 provider → 2 annotation）。
- **下一步**：Batch 4 = H Final Adversarial Re-Probe（4 HIGH + 4 runtime blocker + core invariants
  全 PASS → H Final Closure → Phase 9）。

### 2026-09-07 22:xx（H Phase 1–8 FINAL CLOSURE）

- **用户正式宣布 H Phase 1–8 FINAL CLOSED**。H Runtime Execution Layer 已完成 Frozen Contract
  运行时闭环；A–G 继续 CLOSED。H Phase 1–8 不因后续普通缺陷自动 reopen，未来问题走 post-closure
  defect/errata 流程。
- **Closure 证据链**：Contract（4 HIGH + 4 Runtime blocker 全关闭）→ Implementation →
  Adversarial Probe（4 HIGH + 4 runtime 全 PASS）→ Real DB Probe（并发/幂等/exactly-once）→
  Regression（**314 passed**）→ Closure。Known HIGH = 0，Unreviewed P1 = 0。
- **提交链（H Runtime 收敛，已 push origin/main）**：`5a44245`（Batch 1）/ `d9bdeed`（Batch 2）/
  `94f74c8`（3-1）/ `1e58710`（3-2）/ `2f40514`（3-3）/ `617da01`（3-4）/ `55de2ef`（docs）。
- **当前 V3 状态**：A–G FINAL CLOSED；H Phase 1–8 FINAL CLOSED；Phase 9 NOT STARTED（批准进入
  范围冻结阶段 Phase 9-0 Scope Freeze，先不改代码）。
- **Phase 9 范围（用户批准，先冻结后实施）**：9.1 config constants / 9.2 HTTP retry + LLM retry
  分层 / 9.3 provider exception translation / 9.4 fallback boundary。**不自动纳入** D1/D3/D4/D5/F-4。
  红线：retry 层级不得合并；`MAX_LLM_CALLS_PER_TASK` 按实际 provider invocation 计数不变。
- **下一步**：Phase 9-0 Scope Freeze（纯审查，不改代码——逐项回答 Frozen Spec 契约/缺什么/
  impl gap vs spec gap/是否改 identity/retry/audit/budget/Gate/是否触碰 deferred）→ Phase 9-1 逐项实施。

### 2026-09-07 22:xx（Phase 9-0 Scope Freeze 终裁 + 3 spec gap 冻结）

- **Phase 9-0 Scope Freeze CLOSED**（用户选择 B：先冻结语义再实施）。3 个 spec gap 冻结为
  implementation 语义（BUG-V3-033/034/035 标 Frozen for implementation）。
- **BUG-V3-033**：HTTP retry **不计**新 Provider Invocation（同一 invocation 内 transport retry；
  HTTP retry 不增 invocation/audit/budget）。
- **BUG-V3-034**：transport exception → `LLMNetworkError`（可重试）；HTTP response error →
  `LLMProviderError`；408/429/5xx → retryable，4xx 其他 → non-retryable。不得混 transport failure
  与 HTTP response failure。
- **BUG-V3-035**：fallback 默认关闭；触发 = primary retryable failure + retry exhausted + enabled +
  显式 provider；禁触发 = cancellation/parse/validation/budget/lease/system；fallback = 新 LE +
  新 invocation + 独立 budget；provider 列表显式有限有序。
- **核心红线（用户重申）**：HTTP retry（transport）≠ LLM retry（同 LE invocation）≠ fallback
  （新 config/新 LE/新 invocation），三者绝不混为一种 retry。
- **Phase 9 执行顺序（用户指令）**：9-1A 登记（✅ 本步）→ 9-1B（9.1 config 收口 + 9.3 provider
  exception translation）→ 9-2（HTTP retry transport-only）→ 9-3（fallback）。
- **下一步**：commit 登记 → Phase 9-1B（9.1 已接线 config 收口 + 9.3 provider exception
  translation：transport exception mapping + HTTP status mapping + adversarial tests）。

### 2026-09-08 06:17（Phase 9 全量实现完成 + 第一性原理对抗审查 + B-1/B-2 修复收口）

- **Status: Phase 9 实现完成（9-1B/9-2/9-3）+ 对抗审查 2 缺陷（B-1 HIGH / B-2 MEDIUM）已修复**。
  H Phase 1–8 维持 CLOSED；A–G 维持 CLOSED。
- **Phase 9 实现（commit 链）**：
  - `6543969` 9-0 Scope Freeze（3 spec gap 冻结 BUG-V3-033/034/035）
  - `fabf560` 9-1B provider exception translation（BUG-V3-034：transport→LLMNetworkError /
    HTTP status→LLMProviderError(retryable)；LLMExecutor 识别 non-retryable 不重试）
  - `5f7b9b1` 9-2 HTTP transport retry（BUG-V3-033：transport-only retry，不增
    invocation/audit/budget）
  - `4f44ad4` 9-3 explicit provider fallback（BUG-V3-035：新 config→新 LE + 新 invocation +
    独立 budget；primary retry 耗尽后才降级；dedup 禁回退 primary）
- **Phase 9 全量对抗审查（第一性原理 × V3SPEC，6 探针真证据）**：`_audit_phase9_adversarial.py`
  6 探针，发现 2 真实缺陷（修复前 P3 FAIL = 缺陷证据）：
  - **B-1（HIGH）**：`_resolve_live_provider` 未注册 provider 名静默回退 `_live_provider`
    （primary）→ audit 记 fallback 名、实际调 primary 对象，identity 漂移破坏 Runtime Truth。
    违反 BUG-V3-035「显式有序 provider」+ fail-closed 原则。
  - **B-2（MEDIUM）**：HTTP 200 + malformed body（非 JSON / choices 缺失·空 / message·content
    缺失·null）泄漏裸 IndexError/KeyError/JSONDecodeError → audit error_type='unknown'（非
    provider_error），且不在 retry/fallback 白名单内。BUG-V3-034 翻译遗漏第三类 provider
    failure（payload contract violation）。
- **修复（各独立 commit + 对抗回归）**：
  - `1e435a9` B-1：multi-provider 模式 provider 名未命中 → None（fail-closed→GatewayDenied），
    single-provider 模式（live_providers 空）才回退默认（向后兼容）。+4 test。
  - `312d1f7` B-2：`HTTPLLMProvider.complete` 响应解析 try/except（KeyError/IndexError/TypeError/
    JSONDecodeError）+ content null 显式检查 → LLMProviderError(retryable=False)（用户裁决保守
    分类）。+8 test（7 单元 + 1 audit 层端到端 error_type='provider_error'）。
- **验证**：全量 pytest **344 passed**（原 332 + 12 新增）；re-probe `_audit_phase9_adversarial.py`
  6/6 PASS（P1/P2/P3/P6 断言由「缺陷存在」反转为「修复生效」）；git diff --check 干净。
- **deferred 状态**：BUG-V3-001..028 Open 不变；BUG-V3-033/034/035 Frozen（其实现边界 B-1/B-2
  已在本轮细化修复，不入新编号）。Phase 8 的 D1/D3/D4/D5 + F-4 延续登记不变。
- **下一步**：Phase 9 Final Closure 待用户裁决（B-1/B-2 已修复 + re-probe 6/6 + 344 passed）。
  若关闭 → H 段（含 Phase 9）最终收口完成。

### 2026-09-08 06:30（Phase 9 FINAL CLOSURE）

- **用户正式宣布 Phase 9 FINAL CLOSED**。Runtime transport / exception translation / retry
  layering / explicit fallback / adversarial failure boundaries 全部 verified。
- **Closure 范围**：9-1A（BUG-V3-033/034/035 登记）+ 9-1B（provider exception translation）+
  9-2（HTTP transport retry）+ 9-3（explicit provider fallback）+ Adversarial Fixes（B-1/B-2）。
- **Closure 证据**：全量 pytest **344 passed**；Phase 9 adversarial re-probe **6/6 PASS**；
  B-1 HIGH resolved；B-2 MEDIUM resolved；documentation closure committed；all Phase 9 commits
  synchronized to origin/main（`1e435a9` / `312d1f7` / `67737b5`）。
- **Closure 边界（严格，不顺带关闭）**：Phase 9 范围关闭 ≠ V3 全部关闭。A–G 保持 CLOSED（按
  既有裁决）；H Runtime FINAL CLOSED；**D1/D3/D4/D5/F-4 保持 Deferred/Open**；**BUG-V3-001..028
  仍待系统性 errata 终裁**；Phase 10+ Not Started。
- **下一步（用户建议）**：不立即新增 Runtime 功能；下一优先级 = **BUG-V3-001..028 系统性分类
  审计**（已被后续设计覆盖 / 纯文档 errata / 真实 implementation gap / 必须改 Frozen Spec /
  可正式关闭）→ **A–F Errata Final Ruling** → 再决定下一开发 Phase 范围。

### 2026-09-08（Phase 9 Closure Reopened → C-1 修复 → Re-Closure）

- **背景**：外部独立审查（读取 GitHub main）发现 C-1 新缺陷——负 retry 配置穿透执行层。Phase 9
  FINAL CLOSED 暂时重开为「Closure Reopened / Corrective Patch Pending」。
- **C-1（MEDIUM）BUG-V3-036**：`llm_request_retry_count` / `http_retry_count` 无 `ge=0` 约束且构造
  不校验。`-1` → `range(0)` 零迭代 → 0 次 Provider Invocation 却 finalize_audit(failed,'unknown')
  + settle(0) + return None（违反 `-> str`）；HTTP `-1` → `LLMNetworkError("...: None")` 零请求。
- **修复（最小双保险，用户裁决选择 A）**：`config.py` 两字段 `Field(ge=0)`（env/Settings 路径）；
  `LLMExecutor.__init__` / `HTTPLLMProvider.__init__` `if < 0: raise ValueError`（构造路径）。不捆绑
  `max_llm_calls_per_task` / `task_claim_lease_seconds` / `worker_concurrency`（单独 errata 硬化）。
- **测试（TDD，RED 4 failed → GREEN 6 passed）**：+6 test——2 Settings validation（负 llm/http retry
  → ValidationError）+ 2 构造 fail-fast（负 retry → ValueError + 0 invocation/audit/budget/provider
  side effect）+ 2 retry=0 边界（恰 1 invocation / 恰 1 attempt，attempts = 1 + retry_count 不变）。
- **验证**：全量 pytest **350 passed**（原 344 + 6 新增）；git diff --check 干净；commit `7ace837`。
- **Phase 9 Re-Closure**：C-1 MEDIUM resolved；B-1 HIGH / B-2 MEDIUM 保持 resolved；Phase 9
  adversarial probes + 全量 pytest 全 PASS；文档收口 + origin/main 同步后重新 FINAL CLOSED。

### 2026-09-08 14:01（errata 分类审计 + E/B/A Closure + D-1 Schema 完成）

- **Status: BUG-V3-001..028 errata 分类审计完成；E/B/A Closure + D-1 Schema 五条已关闭**。
  H Phase 1–8 / Phase 9 维持 FINAL CLOSED；A–G 维持 CLOSED。
- **分类（5 类，方法论「先证伪、后修复」）**：A=010；B=003/004；C=011；D=22 项；E=007/028。
- **执行顺序（用户裁决）**：先闭 E/B/A → D-1 Schema → D-2 Identity/Hash → D-3 Annotation →
  D-4 IR/Compiler → D-5 Gate → D-6 Figure Contract → BUG-011。每条 D 类 8 项裁决；红线
  「先冻结 Spec 再改代码」。
- **E/B/A Closure（`b02c16c`）**：003/004（B 文档 errata）、007/028（E 正式关闭）、010（A 已覆盖）。
- **D-1 Schema 完成（`60bc497` + `eb0e450` + `5b0f767`）**：
  - 001/002/006：Spec 文案 errata（域归属 / role-provider 枚举 / selection-event 冻结 /
    dedup_key UNIQUE 声明）。
  - 008：`paddleocr-vl`/`ocr_ppsvl` 封闭配对 + `validate_seal_role_provider` fail-fast +
    `_seal_stage` role 默认 `native`。
  - 027：`questions.dedup_key` UNIQUE + migration 0007 fail-loud + `create_question`
    ON CONFLICT 幂等收敛。
- **验证**：全量 pytest **355 passed**。
- **下一步**：D-2 Identity/Hash（005/012/017/019/022 + H0-2 R2，高风险组；BUG-022 单独首优先
  级，BUG-017 须明确 10 §6.3 vs 20 §7.3 唯一 canonical definition）。
- **待办**：4 commit 本地未 push（待用户明示）。

### 2026-09-09 05:55（D-1 → D-6 errata 全链完成 + BUG-011 Final Closure）

- **Status: BUG-V3-001..028 errata 执行完成（D-1 → D-6 全链）+ BUG-011（C 类真实 gap）
  Final Closed**。A–G / H Phase 1–8 / Phase 9 维持 FINAL CLOSED。
- **errata 执行进度（自 E/B/A Closure `b02c16c` 起，已全部 push origin/main）**：
  - **D-1 Schema**（001/002/006/008/027）——前快照已关闭；
  - **D-2 Identity/Hash**（005/012/017/019/022）——`95c1700` Spec + `7cf21ba` 022 + `878fb10`
    019/012 + `a731e0d` 005；
  - **D-3 Annotation/Content Shape**（009/013/021）——`5ae9853` Spec + `3429671` 021 +
    migration 0008 + `3bbcf53` 013；
  - **D-4 IR/Compiler**（014/015/016/018）——`ff64352` 014 + `a105bf8` 015 + `c6014f7` 018 +
    `3cca050` 016；
  - **D-5 Gate**（023/024/025/026）——`9c1d43f` 023 + `b24b5a7` 024 + `19d236b` 025 + `5f0d3d0`
    026；
  - **D-6 Figure Contract**（020）——`0b0a4d3`（figure_refs 跨层契约冻结，spec-only，A-Guarded）。
- **BUG-011（C 类真实 gap）Final Closure**：Scope Freeze → Implementation（A/B/C/E）→ Gate →
  Migration 全链闭环。5 个 atomic commits：`5c9ecc9`（docs Scope Freeze）/ `a8cd129`（A Figure
  Identity）/ `dd26a6b`（B Native Extraction）/ `716875e`（C Persistence+Integrity）/ `9da09db`
  （E DB UNIQUE + migration 0009）。**BUG-011-E2 保持 Open 独立记录**（E/B 跨层 figure 字段
  drift，后续统一处理，不随 BUG-011 关闭）。
- **验证基线**：全量 pytest **413 passed**；migration replay 双路径 PASS；origin/main == local
  main == `9da09db`。
- **下一步**：**Errata Final Closure**——系统性收口剩余 BUG 状态（005/009/012..026 共 17 项的
  bugs.md Status → Resolved 逐条 Closure evidence）+ `backend/tests/_audit_*.py`（12 份）处置
  裁决（删除 / 归档 / 转正）。之后进入新的功能 / Bug 阶段。

### 2026-09-09 06:16（Errata Final Closure 完成）

- **Status: BUG-V3-001..036 全量 errata 收口完成**——E/B/A + D-1..D-6 + BUG-011 全部关闭；
  剩余 17 项（005/009/012..026）bugs.md Status → Resolved（逐条 Closure evidence，锚
  D-2..D-6 冻结裁决）。A–G / H Phase 1–8 / Phase 9 维持 FINAL CLOSED。
- **BUG 终态**：001..032/036 = Resolved；033/034/035 = Frozen for implementation（Phase 9
  spec gap，非 Open）；BUG-011-E2 保持独立记录（E/B 跨层 figure 字段 drift，后续统一处理）。
- **`_audit_*.py` 处置（用户裁决 = 归档到非正式目录）**：12 份一次性审计/对抗探针移入
  `backend/tests/_audit_archive/`（untracked，不入 git；findings 已在各阶段转正为正式测试）。
- **下一步**：进入新的功能 / Bug 阶段（待用户裁决下一 Phase 范围）。D1/D3/D4/D5/F-4 deferred
  项维持 Deferred/Open；BUG-011-E2 延续为独立记录。

### 2026-09-09 14:58（Phase I Live Data Plane Integration 进行中 + BUG-V3-037 lease 修复完成）

- **Status: Phase I（Live Data Plane Integration）进行中**。A–G / H Phase 1–8 / Phase 9 维持
  FINAL CLOSED；Errata Final Closure（BUG-V3-001..036 收口）维持。新阶段目标 = 证明真实
  Ollama/Qwen 数据面（非 mock）驱动完整 V3 Runtime 链（Task→Attempt→Audit→Budget→Artifact→
  Candidate→Question→Instance）+ PostgreSQL provenance 可验证。
- **I-0 Prompt Contract Alignment 完成**：`build_annotation_prompt`（`executor.py`）首次把真实
  Frozen Annotation Payload Contract（20 §4.1–4.5）写入模型输入（Schema Source of Truth =
  `20_Document_Pipeline.md`，非 test fixture）。`test_prompt_contract.py` 4 测试锁 presence +
  strength（JSON-only / 禁 fence / nested schema example / 正文注入）。
- **I-1-D live smoke harness**：`scripts/live_smoke_ollama.py`（不进 pytest；真实 Ollama +
  `LLM_GATEWAY_MODE=live` + 12 层 Hard Gate）。live gateway 显式构造（task_context/budget_ok），
  不 monkeypatch / 不绕过 `_live()` 放行。
- **BUG-V3-037（lease loss）修复完成**：`TaskExecutor._lease_heartbeat`
  （`@asynccontextmanager` 后台 renew loop，周期 = lease/4）包裹 `_annotation_stage`，长 LLM
  调用（~300s > 60s lease）期间持续续租。targeted 18 passed + 全量 pytest **426 passed**（零
  回归）；live smoke 核心层 PASS（Task succeeded / audit ollama completed / budget settled /
  annotation valid / replay 零重复）。
- **Status: Phase I-1-D live smoke 12 层 Hard Gate 全 PASS（2026-09-09 18:09）**。真实
  Ollama/Qwen（qwen3.5:4b）数据面驱动完整 V3 Runtime 链：Task succeeded + Candidate +
  Gate approved + **Question=1** + **Instance=1** + audit ollama completed + budget settled +
  replay 零重复。全量 pytest **433 passed**。
- **I-0 Prompt Contract Alignment 完成**：`build_annotation_prompt`（`executor.py`）首次把真实
  Frozen Annotation Payload Contract（20 §4.1–4.5）写入模型输入（Schema Source of Truth =
  `20_Document_Pipeline.md`，非 test fixture）。`test_prompt_contract.py` 锁 presence + strength
  （JSON-only / 禁 fence / nested schema example / 正文注入 / explanation 源证据约束）。
- **I-1-D live smoke harness**：`scripts/live_smoke_ollama.py`（不进 pytest；真实 Ollama +
  `LLM_GATEWAY_MODE=live` + 12 层 Hard Gate）。live gateway 显式构造（task_context/budget_ok），
  不 monkeypatch / 不绕过 `_live()` 放行。
- **Phase I live data plane 四层阻断全部关闭**（mock/contract test 均未覆盖，live smoke 逐一
  暴露）：
  1. **I-0-1 Prompt Contract 缺失**：旧 prompt 不喂 Frozen Schema → 真实模型输出全盘漂移。
  2. **BUG-V3-037 Lease loss（Resolved）**：`TaskExecutor._lease_heartbeat` renew loop
     （lease/4）包裹 annotation stage，长 LLM 调用期间持续续租。
  3. **BUG-V3-038 Resolver 字段漂移（Resolved）**：`reference.py` `_answer_target`/
     `_explanation_target` 读 `answer.question_number`，Frozen Schema（20 §4.5）content role 用
     `question_label`。修 Resolver（**禁止 alias fallback**）+ 9 个 mock fixture 迁移 + strict
     contract 回归锁（payload 无 question_number 必须完整解析）。
  4. **BUG-V3-039 Diagnostic metadata 泄漏进 Compile identity（Resolved）**：真实 Qwen 输出
     `confidence: 0.98`（float）→ `gate/service.py` 三处 `sha256_hex(ann.payload)` → BUG-V3-005
     fail-fast → validation_error。建立单一 `_annotation_identity_projection`（仅剔 unit 顶层
     confidence，三处 hash 复用）；prompt 示例删除 confidence；新增 5 类回归锁（核心 =
     confidence 波动不改 identity + 其它 semantic float 仍 fail-fast 反向锁）。
- **两项独立 harness/prompt 修正（独立 commit，不计入 BUG 根因）**：smoke fixture `[Answer]`→
  `【答案】`+`china-s` 字体+补【详解】区；Prompt Contract explanation 源证据约束（无源证据 →
  省略字段，禁止凭空声明/占位）。
- **未 commit（4 个 commit 边界已冻结，待用户明示）**：① BUG-V3-037 lease heartbeat；②
  BUG-V3-038 Resolver question_label 对齐 + fixture 迁移 + strict regression；③ Live Smoke
  Fixture + Prompt Grounding；④ BUG-V3-039 identity projection + 5 锁 + prompt 减噪。
- **模式警示**：test fixture / Frozen Spec / Prompt Example / Real Model Output 四者漂移风险
  已重复出现两次（038 + 039）。Post-Implementation Gate Review 应专项检查所有 identity-bearing
  production path 是否存在「测试 fixture 未覆盖、真实模型可能生成」的字段。
- **下一步**：用户明示后按 4-commit 边界提交 → Post-Implementation Gate Review → 判断 Phase
  I-1 是否 closure。I-1-B（worker per-task task_context/budget_ok）仍 deferred；I-2（Cloud
  OCR data plane）未来阶段。

### 2026-09-09 18:30:00

- **Status: Phase I-1-D CLOSED → Phase I Live Data Plane Verified → Real File E2E Next**。
- **4 commits 已提交**（精确 staging，无无关文件混入）：
  1. `9730351` fix: BUG-V3-037 lease heartbeat for long-running annotation stage
  2. `02c3431` fix: BUG-V3-038 resolver question_label contract alignment
  3. `168d17b` test: live smoke fixture + explanation source-grounding prompt contract
  4. `0f71241` fix: BUG-V3-039 exclude diagnostic confidence from compile identity
- **Post-Implementation Gate Review PASS**：所有 annotation identity path 统一经
  `_annotation_identity_projection`；无绕过 projection 的 production hash path；unknown field
  policy 明确（semantic fields 进 identity，仅 confidence 作为 diagnostic metadata 被排除）；
  fixture 无已确认 contract blind spot。Required Action: None。
- **验证**：全量 pytest **433 passed**；live smoke 12 层 Hard Gate 全 PASS。
- **Working Tree 剩余**（不属于本轮 4 commits）：gateway.py / providers/http.py /
  worker/__main__.py / test_gateway.py / test_http_provider.py（早期 Phase I transport）；
  Status.md / log.md / restart-prompt.md / bugs.md（文档）；_audit_archive/ / probe 脚本 /
  PDF fixtures（辅助工具）。
- **下一步**：Phase I-2 Real File E2E Validation（Native PDF → Cloud OCR → Minimal API）。
  I-1-B（worker per-task task_context/budget_ok）仍 deferred；I-2（Cloud OCR data plane）
  在 Native PDF E2E 后接线。

### 2026-09-09 20:15（Phase I-1 Closure — Heartbeat Flaky 修复 + Identity Gate Review）

- **Status: Phase I-1 CLOSED**。Closure Gate 5/5 全部通过。
- **BUG-V3-037 Heartbeat Flaky 修复**（`bfe4434`）：全量测试实证 `test_long_annotation_keeps_lease_alive`
  间歇性失败（单独 PASS / 全量 FAIL / 再全量 PASS）。根因 = `_renew_loop` 先 `sleep(interval)`
  再 heartbeat，首次续租延迟一个 interval；全量测试 event-loop 竞争 + NullPool 连接建立下，
  首次续租可能晚于 lease 过期 → LeaseConflict → 循环退出 → 后续续租全部停止。修复 = 循环倒置
  为先 heartbeat 再 sleep，进入 context 立即续租。压力验证：单测 ×20 全 PASS、heartbeat 组
  ×20 全 PASS、全量 ×3 全 PASS。
- **Post-Implementation Identity Gate Review**（`1f08882`）：裁决 **PASS WITH DOCUMENTATION**。
  Identity Projection Rule 契约固化（bugs.md）：仅剔 `semantic_units[*].confidence`（unit 顶层），
  不做递归剥离 / unknown-field 剥离 / float 归一化。新增反向锁
  `test_nested_confidence_is_not_silently_projected`（嵌套 float → fail-fast；嵌套 str → 参与
  identity；unit 顶层仍剥离）。
- **全量对抗性审查完成**：434 tests 全 PASS。SPEC 约束逐条验证（Identity/Hash、Gate Grammar、
  Gate Policy、Admission、Task State Machine、Budget、Compiler/IR、Seal/Source、Annotation、
  Gateway、Resolver）全部通过。0 个 TODO/FIXME/HACK。仅 4 个 deferred items（M1 设计决策）。
- **Closure Gate 汇总**：
  - Gate 1 Commit Boundary: 6 commits 干净（4 frozen + heartbeat fix + identity review）
  - Gate 2 Heartbeat Stability: 20/20 单测 + 100/100 组
  - Gate 3 Full Suite: 433×3 → 434（含新增反向锁）
  - Gate 4 Identity Review: PASS WITH DOCUMENTATION
  - Gate 5 Regression: 126 targeted PASS
- **Phase I Transport 接线**（I-1-A / I-1-B，本轮提交）：
  - I-1-A: `HTTPLLMProvider` 条件 Authorization 头（api_key 非空才发）+ `trust_env=False`
    （防 Windows 本地代理劫持 localhost）。
  - I-1-B: `build_gateway()` 工厂从 settings 构造 `HTTPLLMProvider(Ollama)`，worker 改用工厂。
    3 新测试锁 live 注入 / mock 不注入 / disabled 不注入。
- **下一步**：Phase I-2 Real File E2E Validation。

### 2026-09-09 20:30:00（Phase I-2 Revision CLOSED — Source Quality Gate + Real File E2E）

- **Status: Phase I-2 Revision CLOSED**。SourceQualityGate 架构层验证完成，真实 PDF E2E
  边界建立。文档冻结 → PUA 修复 → 进入 Phase I-2C。
- **关键认知修正（BUG-V3-040 Resolved）**：初始判断 "PyMuPDF 中文编码失败" **不存在**。
  实际为 Windows 终端编码显示问题。Native extraction 正确提取中文文本（经文件写入验证）。
  核心教训："不要相信观察层输出，要相信 Source Artifact"。
- **SourceQualityGate 正式架构层确立**：
  ```
  Import → Seal → SourceQualityGate → Annotation → Resolve → Compile → Gate → Admission
  ```
  - 纯函数（无 IO，确定性）
  - 位于 Seal 后、Annotation 前（fail-loud before LLM consumption）
  - QualityReport 落 source_meta 供 Review Console 展示
- **测试证据**：
  - 全量 pytest：421 passed（baseline 417，net +4）
  - Quality Gate：11/11 tests PASSED
  - Import E2E：4/4 tests PASSED
  - Frontend TypeScript：0 errors
  - API：GET /source-quality → 200，GET /source-lines → 200，invalid id → 404
- **真实 PDF E2E 验证**：
  - PDF：2026北京北师大实验中学高一（下）阶段测试一数学（教师版）.pdf
  - 11 pages / 2377 lines / 11 figures
  - Quality status：valid（CJK 42%, replacement 0%, non-printable 7%）
- **架构瓶颈定位**：Resolver 成为 Phase I-2 真正瓶颈（17 resolved / 85 unresolved）。
  数学公式被 native extraction 物理拆散（BUG-V3-041），非 OCR 问题。OCR 不应优先。
- **BUG 登记**：
  - BUG-V3-040（PDF Encoding False Alarm）：Resolved（认知修正）
  - BUG-V3-041（Mathematical Layout Fragmentation）：Open / Deferred（Phase I-2C）
  - BUG-V3-042（PUA False Positive）：Open（本轮 P0 修复）
- **下一阶段：Phase I-2C Resolver Robustness Validation**：
  - 目标：建立 Source Evidence → Resolved Span → Semantic Question IR 的可靠转换
  - 范围：Resolver debug view / line-block relationship / formula fragment detection /
    ambiguous status display
  - 不做：OCR integration / LLM auto-repair / LaTeX reconstruction
- **文档冻结**：
  - `Docs/V3_PHASE_STATUS/Phase_I2_Revision_Closure.md`：完整 Closure 文档
  - `bugs.md`：BUG-V3-040/041/042 登记
  - 本文件：Phase I-2 Revision CLOSED

### 2026-09-09 21:30:00（Phase I-2 Revision 文档冻结 + Git 收口）

- **Status: Phase I-2 Revision CLOSED WITH NOTES**。
- **已完成**：
  - Real PDF import boundary validated
  - SourceQualityGate implemented（纯函数，Seal 后 Annotation 前）
  - Quality gate integrated after Seal stage
  - Review Console supports source inspection
  - Mathematical PDF validation completed
- **验证 Pipeline**：
  ```
  Import → Document Created → Task Queued → Seal →
  Source Quality Gate → Annotation → Review Console
  ```
- **已知限制**：
  1. Mathematical PDF layout fragmentation（BUG-V3-041 Deferred → Phase I-2C）
     - Formula symbols may be split into multiple source lines
     - Resolver cannot reconstruct semantic structure automatically
  2. Native PDF extraction ≠ semantic extraction
     - Source layer preserves extracted facts only
     - Resolver/compiler responsibility begins after source sealing
- **关键认知**：Native extraction succeeded; semantic reconstruction remains incomplete。
  这是 V3 架构设计成功的体现（Source ≠ Semantic 边界成立）。
- **BUG 状态**：
  - BUG-V3-040（PDF Encoding False Alarm）：Resolved
  - BUG-V3-041（Mathematical Layout Fragmentation）：Deferred（Phase I-2C）
  - BUG-V3-042（PUA False Positive）：Resolved（Co excluded from non_printable）
- **No blocking defects remain.**
- **Git**：tag `v3-phase-i2-closed`；Closure 文档
  `Docs/V3_SPEC/Closure/PHASE_I2_REVISION_CLOSURE.md`。

### 2026-09-09 22:30:00（Phase I-2C CLOSED — Resolver Diagnostic + 真实 PDF 失败模式确认）

- **Status: Phase I-2C CLOSED**。Resolver 可观测性建立，真实失败模式确认。
- **Completed**：
  - BUG-V3-043 figures 注入修复（`5f8a3a8`）
  - Resolver Diagnostic Layer（`diagnostic.py`，15 tests）
  - 真实 PDF 诊断数据采集（`8267bfd`）
- **核心发现**：85/85 unresolved 为 `marker_ambiguous`（非 `marker_not_found`）。
  根因 = 题号/选项标签在数学 PDF 中出现 190+ 次，Resolver 单行 marker 匹配无法唯一确定。
- **架构判断**：Resolver fail-loud 行为符合 V3 invariant（宁可拒绝确定，不允许错误定位）。
  失败不是 Resolver bug，是 Source Provider Layer layout reconstruction 能力缺失。
- **BUG 状态**：
  - BUG-V3-043（figures 注入缺失）：Resolved
  - BUG-V3-041（Mathematical Layout Fragmentation）：Deferred → Phase I-3
- **Decision**：Resolver robustness enhancement deferred。下一阶段 = **Phase I-3 Source
  Provider Layer Evaluation**（评估 native/OCR/hybrid provider 对数学试卷的结构恢复能力）。
- **文档**：`Docs/V3_SPEC/Closure/PHASE_I2C_CLOSURE.md` + `PHASE_I2C_DIAGNOSTIC_REPORT.json`。

### 2026-09-09 23:59:00（Phase I-3 CLOSED — Source Evidence Preservation Layer）

- **Status: Phase I-3 CLOSED. Gate PASS**。Source Evidence Preservation Layer 实现正确，
  架构基础闭环完成：`Source Provider → Source Evidence → Immutable Storage → Replay Verification`。
- **Completed**：
  - I-3-0: 评估文档冻结（`f15dfb2`）
  - I-3-1: SourceSpan 定义 + NativeTextProvider span 提取（`a9c32f3`）
  - I-3-2: 存储决策冻结——独立表 `document_source_spans`（`c42b8dc`）
  - I-3-3: document_source_spans 表 + seal 持久化（`9645a81`）
  - I-3-4: FK 违例修复（`6ec69df`）
  - I-3-5: 对抗性审查（10 维度，9/10 PASS + 1 CRITICAL 已修复）
  - I-3-6: Closure 文档 + 架构护栏（本 commit）
- **核心交付**：`SourceSpan` frozen dataclass（seq/text/font/size/flags/bbox/origin/span_hash），
  `NativeTextProvider` 从 PyMuPDF `get_text("dict")` 提取完整 span metadata，经 SealService
  持久化到 `document_source_spans` 表。span_hash = SHA256(text+font+size+flags+bbox+origin)，
  描述 layout evidence identity（非 semantic equality）。
- **对抗性审查结果**：Data Integrity / Deterministic Extraction / Span Ordering / Layout Loss
  Audit / Provider Round-Trip / Backward Compatibility / Migration Safety / V3SPEC Compliance /
  No Resolver Changes = 9 PASS；Seal Persistence = FAIL→已修复（FK 违例）。
- **Gate Criteria**：6/6 全部通过（零回归 / 确定性 / 零丢失 / round-trip / 无 Resolver 改动 /
  无 provider 特判）。
- **BUG 状态**：
  - BUG-V3-041（Mathematical Layout Fragmentation）：Partially Addressed（Source 已保留
    layout evidence，Resolver 消费待 Phase I-4）
- **架构护栏冻结**：`63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md`——Source Layer 只保存
  immutable evidence，不做 semantic interpretation；新增 Source 实体须过四项审查；
  Resolver 修改前须完成 Evidence Utilization Gate。
- **验证基线**：全量 pytest **454 passed**（1 预存失败 `test_h_seal_concurrency`）；
  migration replay 双路径 PASS；test_source_span.py 19/19。
- **下一阶段：Phase I-4 Resolver Evidence Utilization Evaluation**——验证 SourceSpan 是否
  真的能降低 marker_ambiguous。**不直接修改 Resolver matching algorithm**。先测量收益，
  再决定是否修改。
- **文档**：`Docs/V3_SPEC/Closure/PHASE_I3_CLOSURE.md` +
  `63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md`。

### 2026-09-10（Phase I-4 CLOSED — Valid Negative Result）

- **Status: Phase I-4 CLOSED**。Closure Type = **Valid Negative Result**（§10.8 Option 3）。
  工程目标成功完成；span-level layout evidence 对当前数学 PDF marker ambiguity 无有效改善。
- **实验闭环**：I-4-1（evidence read path + diagnostic layer，21 tests）→ I-4-2（真实数学
  PDF replay，frozen input：11 页 / 2377 行 / 3641 spans / 19 题 / 51 targets，权重不调优）
  → Before/After 测量 → 负结果冻结。
- **核心测量结果**：
  - Before: 42 marker_ambiguous / 9 resolved（17.6%）
  - After: **0 unique with evidence** / 42 still ambiguous（**0% unique rate**）
  - Tied top-2 scores: **34/42（81%）**
  - 正确答案排名：P1L006（Q1 真正起点）排第 **123/190**（score 0.30），被孤立数字 span
    （坐标值/分数分子，score 0.90）压倒
- **根因**：数学 PDF 产生数千个孤立数字 span（坐标/分数/指数），其 layout evidence 与题号
  完全相同。**Layout evidence 无法区分 semantic role**——这是 information insufficiency
  problem，不是 algorithm deficiency。
- **架构结论**：Phase I-4 的目标不是降低 unresolved，而是验证 SourceSpan evidence 是否具有
  实际 diagnostic value。实验成功回答：**在当前 failure mode 下，没有**。这是一个
  valid negative result。
- **冻结负结果**（§10.10）：在出现新测量证据之前，禁止继续调 evidence scoring 权重、增加
  span-level layout heuristic、为特定 marker 加规则、把 evidence.py 演化成第二个 Resolver、
  建 Document Layout Engine。
- **新增架构原则**（§10.9）：**Evidence Sufficiency Before Architecture Expansion**——在引入
  新结构层前，必须先审计当前 immutable Source evidence 是否已包含所需信息。
- **代码变更**：evidence.py 空 marker 防御边界（`if not marker: return []`）；权重常量文档
  标注 experimental diagnostic heuristics；evidence_replay.py 修复 2 个字段错误；test_evidence.py
  +2 空 marker 测试。全量 pytest **506 passed**（1 flaky seal concurrency）。
- **Commit**：`759c5a3`（evidence 空 marker 修复 + I-4-2 replay + 评估文档 + 架构约束 §10）。
- **下一方向**（NOT STARTED）：**Phase I-5 Context Sufficiency Investigation**——调查当前
  Source evidence 中 line/page/document context 是否已足以区分 question marker 的 semantic role。
  I-5 必须从 context audit 开始，不从代码开始。只有 I-5 证明 context 能解决 ambiguity，才值得
  修改 Resolver。
- **文档**：`Docs/V3_SPEC/Closure/PHASE_I4_CLOSURE.md` + `64_PHASE_I4_EVIDENCE_EVALUATION.md`
  + `63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md` §10.9/§10.10。

### 2026-09-10（Phase I-5-0 Scope Freeze — Preprocessed Source Integration）

- **Status: Phase I-5 I-5-0 完成**。Phase I-5 定义为 **Preprocessed Source Integration
  Feasibility Experiment**，不是 subsystem implementation。
- **外部预处理管线**：PaddleOCR-VL → LLM semantic annotation → manifest。17 份试点文档，
  12 份已人工审核（高一 9 科 + 高二 2 科）。集成验证：319 units，100% answer 覆盖，
  42/42 Phase I-4 numeric marker 被 manifest structural role 正确分类，24/24 composite
  material ⊆ questions 约束成立。
- **核心架构边界（冻结）**：Markdown Source = Source Evidence（唯一正文事实）；
  Manifest = Structural Annotation Evidence（语义解释，非事实）。Manifest 不得成为第二套
  Source Truth。Manifest 只能引用 Source 中已存在的内容，不得复制正文。
- **十二约束**：不修改 SourceResolver、不引入永久 Source 抽象、不修改 Source evidence
  不变式、不将 manifest 视为 immutable source fact、测量真实 pipeline 结果（非标注可用性）、
  使用已审核高一/高二文档、主要指标为端到端正确性提升、无证据不建子系统、保留无 manifest
  的原始 Source 路径、需大量 domain 改动时暂停重审。
- **Candidate Evidence 分类**：stem/options/answer/explanation/material/questions_lines →
  Candidate Evidence；unit_id → Experimental Mapping Identifier；unit_type/question_numbers/
  original_question_type → Candidate Semantic Evidence（≠ V3 canonical type，需 Adapter
  mapping）；annotation_meta/model/source_file → Forbidden。
- **Adapter 位置**：`experiments/phase_i5/`（实验执行）+ `backend/tests/phase_i5/`（集成
  测试）。禁止进入 `backend/app/`。
- **Decision Matrix**：A（集成可行）/ B（可行但低价值）/ C（边界冲突）/ D（复杂度失败）/
  E（正确性失败→不接受）。不冻结数值阈值，I-5-1 根据实际 baseline 确定。
- **Commit**：本次提交（65_PHASE_I5_SCOPE_FREEZE.md + 状态文档更新）。
- **下一阶段**：I-5-1 Integration Boundary Analysis——分析 manifest 字段与 V3 contract
  的对应关系，确定最小 Adapter 需求。No code until I-5-1 analysis is complete。
- **文档**：`Docs/V3_SPEC/65_PHASE_I5_SCOPE_FREEZE.md`。

### 2026-09-10（Phase I-5-1 Boundary Analysis + Step 0/0.5 盲测 + Question 结构定义）

- **Status: Phase I-5-1 完成 + Step 0/0.5 盲测完成 + Question 结构定义（68 号）待进入 Step 4**。
  A–G / H / Phase 9 / Errata 维持 FINAL CLOSED。
- **I-5-1 Boundary Analysis**（`66_PHASE_I5_1_BOUNDARY_ANALYSIS.md`）：Manifest 字段逐字段
  追踪到 V3 contract。Path B（直接构造 ResolvedSpan → IRBuilder → Compiler）实测可行
  （21/21 ready，21 CompiledLeaf）。14 项测试：seq 映射 / ResolvedSpan 构造 / 错误拒绝 /
  IRBuilder 消费 / Compiler 输出 = PASS；Resolver 简单用例全部 UNRESOLVED / option_tokens()
  无法拆分同行多选项 = FAIL（确认 Phase I-4 结论）。
- **Manifest Capability Check**：Composite = 原子单元（不拆子题，用户裁决）；共享答案表 =
  manifest 未提取 per-question answer（需 LLM，预处理项目职责）；Options = 仅范围无逐选项
  拆分（需预处理层增强）。
- **架构方向讨论收敛**：LLM 负责理解（这是什么、在哪里），代码负责验证（引用是否合法）。
  Resolver 从"搜索器"变为"校验器"。67 号文档（`67_ANNOTATION_RESOLVER_BOUNDARY_ADJUSTMENT.md`）
  经两轮对抗性审查修订，方向冻结但实施暂停——需先完成 Step 0 验证。
- **Step 0（非盲测）**：Claude 基于带行号源文本输出结构标注，45/45 = 100%（有数据污染，
  仅 Proof of Capability）。
- **Step 0.5（盲测，MIMO API mimo-x-pro-preview）**：
  - Case A 数学（21 units）：84/84 = **100% exact**（stem/options/answer/explanation 全对）
  - Case C 物理（24 units，共享答案表）：answer **24/24 = 100%**，explanation 24/24 = 100%，
    options 20/20 = 100%，stem 19/24（5 partial 是 GT stem 定义不够精确）
  - Case B 地理（19 units，composite 为主）：修正 prompt 后 19/19 units，explanation 19/19，
    answer 18/19 = 94.7%；material 范围不完整（LLM 只取首行）
  - **Composite grouping 对 prompt contract 具有明显响应性**（34→19 units），普遍性待验证
- **Question 结构定义**（`68_QUESTION_STRUCTURE_DEFINITION.md`）：Question = 题库最小完整
  使用单元；Composite = 一个 Question（非 parent+child）；判定 OR（显式 grouping / 共同
  依赖）；stem = 题干语义区域（不含 options）。经对抗性审查修订（stem 必须存在 → 作答内容
  必须存在；material 不限于 composite；Rule B 边界约束；answer reference 非 value）。
- **新文件**：`66_PHASE_I5_1_BOUNDARY_ANALYSIS.md` / `67_ANNOTATION_RESOLVER_BOUNDARY_
  ADJUSTMENT.md` / `68_QUESTION_STRUCTURE_DEFINITION.md` / `scripts/step0_blind_test.py` /
  `scripts/geo_llm_output.json`。
- **下一步**：Step 4（Manifest Expressiveness Check）——按 68 号 Question 模型检查 manifest
  是否能完整表达全部结构关系。在此之前不修改 V3 正式代码。

### 2026-09-10（Step B/B5/Step C 架构审查裁决完成 — 69 号文档）

- **Status: Step B / B5 / Step C 三轮对抗性审查完成，项目负责人裁决固化**。
  A–G / H / Phase 9 / Errata 维持 FINAL CLOSED。65/66/67/68 不再是"未审查文档"。
- **Step B Frozen Impact Matrix**（四层分类法 + 核心不变量比对）：
  - 65 = Evidence（Path B 可行性；可行性 ≠ 架构优越性）
  - 66 = Analysis（Manifest expressiveness；V3 语义模型原则上更强）
  - 67 = Proposal + **Contract Change**（必须 Errata；20 §4.3/§3/§5 三条字面冲突确认）
  - 68 = Proposal（核心语义与 Frozen IR 一致；三个待裁决点）
- **Step B.5（67 Identity/Authority Review）**：
  - B5-1 line_refs = **Source Binding Claim**（非 Source Fact / Position Fact）
  - B5-2 **Source Binding Selection Authority** 从 Resolver 前移至 LLM（确定性层保留
    Reference Integrity Authority）
  - B5-3 **OPEN**——Annotation Identity / Logical Execution Identity / Source Binding
    Identity 的关系需定义；A/B/C 三方案均不得预选
  - B5-4 Frozen Resolver 优势 = ambiguity/missing 拒绝 + 确定性解析机会（非语义纠错）
- **Step C（68 ↔ Frozen Data Model）**：
  - C-1 Composite = ONE Question：**IR 层 PASS**；物化层语义张力需 Application 层裁决
  - C-2 Standalone + Material：**Contract Expressiveness Gap**（20 §4.5 standalone 无
    material 字段）；不是业务模型冲突
  - C-3 Material ≠ text only：**NO CONFLICT / CLOSED**（Material = supporting content）
- **Question 语义模型裁决确认**：Composite = ONE Question；sub_question ≠ Question entity；
  Material = supporting content（text/image/figure/table/chart/map/diagram/mixed）；
  Standalone + Material 合法；Composite 判定 = Explicit grouping OR shared dependency。
- **新文件**：`69_ARCHITECTURE_REVIEW_ADJUDICATION.md`（裁决记录权威文件）+
  `68` 更新（Material 语义澄清 §1.5 + Adjudicated 状态）。
- **Open Questions**：OQ-1（B5-3 Identity 分层）/ OQ-2（Standalone + Material Annotation
  Contract）/ OQ-3（物化层 leaf Question 独立性）。
- **下一步**：OQ-1 Identity 分层分析 → OQ-2 Standalone + Material Contract 设计 →
  Step D（67 Structural Claim ↔ Resolver Contract）→ Step 4 → Errata Decision →
  Owner Decision → I-5-2。**在此之前不修改 V3 正式代码。**

---

## 2026-09-10（全代码库对抗性审查收敛）

### 背景

用户要求基于 V3 核心冻结规范（00/10/20/30）对全部代码和结构开启严格对抗性审查，
每个结论必须有真实测试作为证据。Claude 执行了 10 维度 40+ 不变量的系统性审查，
ChatGPT 独立执行了代码静态审查，双方经过多轮 meta-review 收敛共识。

### 审查方法

- 10 个审查维度（架构边界/Source 不可变/Annotation/Resolver/IR/Compiler/Gate/幂等/任务安全/Schema）
- 40+ 条具体不变量，每条对应冻结规范条款
- 运行 508 个测试（506 通过，2 失败）
- 逐维度验证：读取源代码 → 对照规范 → 运行测试 → 记录证据

### 最终状态基线

| 维度 | 状态 |
|------|------|
| Architecture Design | PASS WITH RESERVATIONS |
| Core Safety Model | PASS |
| Local Invariants | PASS / TEST-EVIDENCED |
| Cross-Boundary Invariants | PARTIAL |
| Resolver Algorithm Safety | PASS |
| Resolver Real-World Coverage | FAIL (16.7%) |
| Phase I-5 Path B → IR/Compiler | PROVEN (21/21) |
| Phase I-5 Full Closure | NOT YET PROVEN |
| Manifest Expressiveness | 2 GAPS |
| 67 Contract Change | OPEN / P0 DECISION |
| Test Isolation | FAIL |
| Full Production Pipeline | NOT YET CLOSED |

### 发现的真实问题

**P0（必须修复）**：
1. test_config `.env` 泄漏：`LLM_GATEWAY_MODE=live` 覆盖默认值，测试未隔离
2. test_h_seal_concurrency DB 隔离失败：全量运行时统计全表 document 数
3. Admission 失败原子性测试缺失：无"物化中途异常 → ROLLBACK → A 域行数为 0"测试
4. 并发 Approval 测试缺失：无两个 DB Session 同时 approve 同一 Candidate 的测试

**P1（应修复）**：
5. Domain→Infrastructure 依赖：domains/ 下 7 个模块 import repositories/models/ai（目录归位即可）
6. policy.py 重复 span 检查不完整：只检查 byte_proven_spans，不检查 contextual/fuzzy
7. test_db_tables_exact_19 命名不一致：函数名 19，断言 20

**OPEN（需先回 Frozen Spec）**：
8. Figure placement 不进 integrity_hash：需先定义"修改一张图"的语义

### 关键裁决

- **Resolver 覆盖率问题的定性**：不是"Resolver 算法不够强"，是"Annotation→Resolver 架构边界设计有问题"。
  解决路径 = Phase I-5 Path B + 67 号架构调整，而非加强 Resolver。
- **Path B 状态**：→ IR/Compiler PROVEN，→ Gate/Admission NOT YET PROVEN，Full Closure NOT YET PROVEN。
- **67 号核心原则**：Source Pointer ≠ Source Content；Source Pointer is an untrusted claim requiring Source-side validation。
- **OQ 优先级**：OQ-3（leaf Materialization）> OQ-2（Standalone+Material）> OQ-1（Identity 分层）。

### 下一步（按序执行）

1. Step 1：修测试隔离（.env + DB）→ 508/508 干净基线
2. Step 2：补 Admission 失败原子性 + 并发 Approval 测试
3. Step 3：裁决 67 号 Contract Change
4. Step 4：裁决 OQ-3 → OQ-2
5. Step 5：补 Manifest Contract（answer_text + options）
6. Step 6：设计 I-5-2 Adapter
7. Step 7：Path B Full Closure E2E

---

## 2026-09-11（P0 Closure Pack 关闭 + 对抗性审查通过）

### 背景

上轮对抗性审查（2026-09-10）发现 4 个 P0 + 3 个 P1。本轮按 Step 1→2 顺序修复，
每轮修复后开启严格对抗性审查（每个结论必须有真实测试证据）。

### Step 1：测试隔离修复

| 问题 | 根因 | 修复 |
|------|------|------|
| test_config `.env` 泄漏 | `Settings()` 缺 `_env_file=None` | 添加 `_env_file=None` |
| test_h_seal_concurrency DB 隔离 | count 无 WHERE + 无前置 cleanup | WHERE `original_sha256` + 前后双 cleanup |
| test_question_dedup_concurrency DB 隔离 | 同上 | WHERE `dedup_key` + 前后双 cleanup |

### Step 2：Admission 测试补全

| 新测试 | 验证内容 |
|--------|----------|
| `test_materialize_failure_rolls_back_all_a_domain_rows` | 物化中途异常 → ROLLBACK → A 域 5 表全空 + candidate 仍 pending_review |
| `test_concurrent_approve_single_materialization` | 两个 DB Session 并发 approve → FOR UPDATE 串行化 → 恰 1 物化 |

### P1 修复

| 问题 | 修复 |
|------|------|
| `test_db_tables_exact_19` 命名不一致 | 重命名为 `test_db_tables_exact_20` |
| `policy.py` 重复 span 检查不完整 | 扩展到所有 resolution 类型（含 contextual/fuzzy） |
| `test_minimal_required_ok` `.env` 泄漏 | `_env_file=None` + `monkeypatch.delenv`（LLM_GATEWAY_MODE, MIMO_API_KEY） |
| `test_future_surface_defaults_and_not_required` 同上 | 同上 |

### 对抗性审查结果（三轮）

**第一轮（Step 1+2+P1）**：7 维度审查，全部 PASS。
- test_config `_env_file=None` 有效阻止 `.env` 泄漏（真实对比验证）
- test_h_seal_concurrency JOIN 查询正确可执行
- 原子性测试有效：Question/Instance flush=True → rollback → 0 行
- 并发测试可靠：10/10 passed，`lock_candidate` 确认使用 `FOR UPDATE`
- policy.py 重复 span 检查扩展有效：exact/contextual 重复均检测到
- P1 发现：`test_minimal_required_ok` 仍泄漏 `.env`（无 `_env_file=None`）

**第二轮（test_minimal_required_ok 修复）**：6 维度审查，发现 P1。
- `_env_file=None` 阻止 `.env` 文件有效
- 新断言能捕获 `.env` 泄漏（旧断言不能）
- P1 发现：`_env_file=None` 不阻止 OS 环境变量；两个测试均缺 `monkeypatch.delenv`

**第三轮（monkeypatch.delenv 修复）**：7 维度审查，全部 PASS。
- delenv 移除 OS 环境变量有效（`'live'`→`None`）
- 空字符串边界正确处理
- 全面污染（5 变量）下 6/6 passed
- 真实 pytest 进程验证 monkeypatch scoping 有效
- P2 观察：`MIMO_BASE_URL`/`MIMO_MODEL`/`OCR_GATEWAY_MODE` 可泄漏但当前未断言（不处理）

### 最终状态基线

| 维度 | 状态 |
|------|------|
| Architecture Design | PASS WITH RESERVATIONS |
| Core Safety Model | PASS |
| Local Invariants | PASS / TEST-EVIDENCED |
| Cross-Boundary Invariants | PASS / TEST-EVIDENCED |
| Admission Atomicity | PASS |
| Admission Concurrency | PASS — 10/10 |
| Test Isolation | PASS / TEST-EVIDENCED |
| Resolver Algorithm Safety | PASS |
| Resolver Real-World Coverage | FAIL — 16.7% |
| Path B → IR | PROVEN — 21/21 |
| Path B → Compiler | PROVEN — 21/21 |
| Path B → Gate | NOT YET PROVEN |
| Path B → Admission | NOT YET PROVEN |
| Manifest Expressiveness | 2 GAPS |
| 67 Contract Change | OPEN |
| OQ-1 / OQ-2 / OQ-3 | OPEN |
| Figure Integrity Semantics | OPEN / P1 |
| Full Production Pipeline | NOT YET CLOSED |

### 关键判断

- **P0-2/P0-3/P0-4 已关闭**，不再是项目阻塞项。
- **唯一剩余 P0 = Phase I-5 Path B Full Closure**。
- **V3 安全执行框架已基本证明**（Source Truth / Resolver safety / Gate / Admission /
  Concurrency / Idempotency / Replay / Task safety / Budget / Audit / Schema / Test isolation）。
- **V3 真实试题数据生产闭环未证明**（Manifest → Adapter → IR → Compiler → Gate → Admission）。
- **21/21 ready IR ≠ Full Closure**——只证明 Manifest→IR 路径成立，Gate/Admission 未验证。
- **不再做大范围基础架构对抗审查**——注意力全部转向 Phase I-5。

### 下一步（按序执行）

1. **Step 3**：裁决 67 号 Contract Change（Source Pointer ≠ Source Content）
2. **Step 4**：裁决 OQ-3（leaf Materialization）→ OQ-2（Standalone+Material Annotation）
3. **Step 5**：补 Manifest Contract（answer_text + options）
4. **Step 6**：设计 I-5-2 Adapter（Translator + Validator，非第二个 Resolver）
5. **Step 7**：Path B Full Closure E2E（含 Provenance Golden Test + Replay 验证）

---

## 2026-09-11（Step 3 裁决：67 号 Conditional Acceptance）

### 裁决结果

**有条件接受（Conditional Acceptance）。**

67 号核心架构方向获得原则性接受：**Source Pointer ≠ Source Content。**
Resolver 从"搜索 Source"调整为"验证 Source Binding Claim"，架构原则上成立。
本裁决不等同于立即修改 Frozen Spec 或发布 Errata。

### 已接受的架构原则

- `line_refs` = Source Binding Claim（非 Source Content / 非 Position Fact）
- LLM = Semantic + Binding Proposal Authority
- Resolver = Reference Integrity Authority
- Source = Fact Authority
- Admission = Persistence Authority
- Adapter 不得成为第二个 Semantic Resolver

### Authority 分层

| 权限 | LLM | Resolver | Admission |
|------|-----|----------|-----------|
| 理解语义 / 提出 line_refs | ✓ | | |
| 引用合法性 / Source 存在 / span integrity | | ✓ | |
| 语义正确性最终确认 / 创建 Question | | | ✓ |

### Errata Gate（四道门）

| Gate | 内容 | 状态 |
|------|------|------|
| A — Identity Closure | B5-3 Identity 分层：Semantic Identity / Binding Claim / Resolved Evidence | **OPEN** |
| B — Legacy vs Path B 对比 | 真实 corpus 对比（exact/normalized/contextual/fuzzy/ambiguous/missing/validated） | **OPEN** |
| C — Safety Invariant Preservation | Source immutable / LLM 无 Admission Authority / invalid fail-closed / cross-source fail-closed / span integrity / replay identity | **OPEN** |
| D — Adapter Boundary | Contract Translator，非 Semantic Resolver | **OPEN** |

### 当前禁止事项（OQ-1 完成前）

- 不修改 Frozen Spec §4.3 FORBIDDEN_FIELDS
- 不发布 67 号 Errata
- 不将 Path B 实验代码视为正式管线

### 正式状态

```
67 号：CONDITIONALLY ACCEPTED（Gate A PASS；Pending Gate B/C）
Frozen Spec：UNCHANGED
Errata：BLOCKED BY Gate B/C（Gate A 已解除）
Path B：VALIDATED EXPERIMENTAL PATH
```

### 下一步（按序执行）

1. **OQ-1**：B5-3 Identity 分层分析（Gate A）
2. **Gate B**：Legacy vs Path B 真实 corpus 对比
3. **Gate C**：Safety Invariant Preservation 验证
4. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决
5. **Errata Decision**（Gate A-D 全部通过后）
6. **I-5-2 Adapter**（Gate D 约束）
7. **Path B Full Closure E2E**

---

## 2026-09-11（Gate A 关闭：OQ-1 Identity 分层 PASS / TEST-EVIDENCED）

### 裁决

**Gate A：PASS / TEST-EVIDENCED。B5-3 Identity Semantics：OPEN → CLOSED。**

### 三层 Identity 模型（正式确认）

| 层 | 回答 | hash 载体 | 进入 LE hash? |
|----|------|----------|--------------|
| Semantic Identity | "这是什么？" | `annotation_payload_hash`（剔除 confidence + line_refs） | ✓ |
| Source Binding Claim | "我认为它在哪里？" | `resolver_input_hash`（含 line_refs） | ✗ |
| Resolved Evidence | "实际引用了什么？" | `compiler_input_hash` / `occurrence_key` | ✗ |

**核心结论**：line_refs 属于 Source Binding Claim，不属于 Semantic Identity。

### Gate A 关闭证据

| 条件 | 证据 |
|------|------|
| A1: 不同 line_refs 不分裂 Semantic Identity | `test_line_refs_change_does_not_change_semantic_identity` |
| A1 补充: 不同 line_refs → resolver_input_hash 不同 | `test_line_refs_change_changes_resolver_input_hash` |
| A2: 不同语义 → 不同 identity | `test_semantic_change_with_same_line_refs_still_changes_identity` |
| 向后兼容 | `test_line_refs_absent_backward_compatible` |
| call-site audit | `_annotation_identity_projection` 仅 2 处调用，无隐藏依赖 |
| 全量回归 | 514/514 passed |

### 代码修改

| 文件 | 修改 |
|------|------|
| `service.py` `_annotation_identity_projection` | 剔除键 `{confidence}` → `{confidence, line_refs}` |
| `service.py` `_confidence_only_projection` | 新增：仅剔除 `confidence`，供 `resolver_input_hash` |
| `service.py` `_input_identity` | `resolver_input_hash` 改用 `_confidence_only_projection` |
| `test_identity_projection.py` | 新增 4 个 A1/A2 测试 |

### 67 号状态更新

```
Gate A: PASS / TEST-EVIDENCED
Gate B: OPEN（Legacy vs Path B corpus 对比）
Gate C: OPEN（Safety Invariant Preservation）
Gate D: OPEN（Adapter Boundary）
Errata: BLOCKED BY Gate B/C
```

### 下一步（按序执行）

1. **Gate B**：Legacy vs Path B 真实 corpus 对比
2. **Gate C**：Safety Invariant Preservation 验证
3. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决
4. **Errata Decision**（Gate B/C/D 通过后）
5. **I-5-2 Adapter**（Gate D 约束）
6. **Path B Full Closure E2E**

## 状态快照：Gate B 裁决（2026-09-11）

### Gate B：CONDITIONAL PASS / NOT CLOSED

**"18% vs 100%" 结论正式撤销。** 两者度量不同事物：搜索成功率 vs range 合法率。

### 实验结果

| 项目 | 结果 | 说明 |
|------|------|------|
| Corpus | 67 cases / 1885 units / 10 学科 | 80 manifest 中 67 mapping-consistent |
| Legacy Resolver | ~18% resolution rate | 与 Phase I-4 17.6% 一致，失败模式有重复性 |
| Path B | 100% Range-Valid Rate | **仅行号范围有效，非内容正确** |

### P0 发现（对抗性审查，12 维度）

| 发现 | 数据 |
|------|------|
| Path B spans 指向空行 | 25.9%（600/2314，sample） |
| answer_lines 指向选项行 | 12.2%（66/540，sample） |
| 度量口径不一致 | Legacy target 7631 ≠ Path B span 8089 |

### Binding Integrity 分层（正式确认）

```text
Level 1 — Range Validity    "行号在范围内"
Level 2 — Content Validity  "resolved_text 非空"
Level 3 — Role Validity     "内容属于正确 role"
Level 4 — Semantic Validity "内容符合 unit 语义（需独立证据）"
```

### Gate 状态更新

```text
Gate A: PASS / TEST-EVIDENCED
Gate B: CONDITIONAL PASS / NOT CLOSED
  Gate B1 (Binding Integrity): OPEN
  Gate B2 (Strategy Comparison): BLOCKED BY B1
Gate C: OPEN
Gate D: OPEN
Errata: BLOCKED BY Gate B/C
```

### 下一步（按序执行）

1. **Gate B1**：Binding Integrity 重设计——统一 Content Role Target `(unit_id, role)`，
   增加 content_valid / role_valid 检查，重跑完整 corpus
2. **Gate B2**：Strategy Comparison——Legacy vs Path B 同口径 Role-Level Binding 成功率
3. **Gate C**：Safety Invariant Preservation 验证
4. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决
5. **Errata Decision**（Gate B1/B2/C/D 通过后）
6. **I-5-2 Adapter**（Gate D 约束）
7. **Path B Full Closure E2E**

## 状态快照：Gate B1 裁决（2026-09-11）

### Gate B1：FAIL / Corpus Not Ready

**瓶颈不在 Path B 架构，而在 manifest 生成管线的数据质量。**

### 实验结果（67 cases / 8367 role targets）

| 验证层 | 通过数 | 通过率 | 裁决 |
|--------|--------|--------|------|
| Level 1 — Range Validity | 8367 | 100.0% | PASS |
| Level 2 — Content Validity | 6263 | 74.9% | **FAIL** |
| Level 3 — Role Validity | 1051 | 12.6% | **FAIL — severe** |
| Level 4 — Structural Validity | — | 未评估 | INSUFFICIENT |
| Level 5 — Semantic Validity | — | 未评估 | UNPROVEN |

### 按 Role 分解

| Role | Total | Range | Content | Role |
|------|-------|-------|---------|------|
| stem | 1556 | 1556 (100%) | 1333 (85.7%) | 205 (13.2%) |
| option | 4328 | 4328 (100%) | 2774 (64.1%) | 701 (16.2%) |
| answer | 1874 | 1874 (100%) | 1559 (83.2%) | 133 (7.1%) |
| explanation | 609 | 609 (100%) | 597 (98.0%) | 12 (2.0%) |

失败原因：role_mismatch 5212（71.2%）/ content_empty 2104（28.8%）。

### 根因

reslice pipeline 插入区域标记（"题干区开始"/"答案区结束"等），
line_refs 大量指向标记而非实际内容；options 按行拆分产生假 target；
answer_lines 指向答案表标记或题目编号。

**核心区分**：不能推出"Path B 架构有问题"，只能推出"当前 manifest 管线
无法提供满足 Path B Binding Contract 的输入"。

### Phase I-5 状态矩阵

| 项目 | 当前状态 |
|------|---------|
| Gate A (Identity Closure) | PASS / TEST-EVIDENCED |
| Gate B1 Range Validity | PASS |
| Gate B1 Content Validity | FAIL |
| Gate B1 Role Validity | FAIL — severe |
| Gate B1 Structural Validity | NOT YET EVALUATED |
| Gate B1 overall | **FAIL — Corpus Not Ready** |
| Gate B2 formal | BLOCKED |
| B2 Preflight | 允许（仅 clean subset，仅作诊断） |
| Legacy Resolver weakness | TEST-EVIDENCED |
| Path B technical operability | TEST-EVIDENCED |
| Path B correctness | NOT PROVEN |
| Manifest generator quality | FAIL |
| Production code change | 暂缓 |

### 下一步（按序执行）

1. **审计并修复 reslice/manifest generator**：区域标记、空行、answer_lines、options_lines
2. **Role classifier 对抗性验证**：确认 12.6% 是 manifest 错误，非 validator 过度严格
3. **重新生成完整 67 cases manifest，重跑 B1**
4. **B1 达到 corpus-readiness 门槛后，进入正式 Gate B2**
5. **Gate C**：Safety Invariant Preservation 验证
6. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决
7. **Errata Decision**（Gate B1/B2/C/D 通过后）
8. **I-5-2 Adapter**（Gate D 约束）
9. **Path B Full Closure E2E**

## 状态快照：Gate B1 修正（2026-09-11）

### Gate B1：CONDITIONAL PASS（旧 FAIL 作废）

**旧 FAIL 裁决基于两个实验缺陷，正式作废：**
1. 读错源文件（切片展示视图 vs 原始源）
2. validator 过度严格（转义点号、markdown 前缀、答案表格式未覆盖）

### 修正后结果（79 cases / 10343 role targets）

| 验证层 | 修正前 | 修正后 |
|--------|--------|--------|
| Range Validity | 100% | **100%** |
| Content Validity | 74.9% | **79.0%** |
| Role Validity | 12.6% | **63.3%** |

### 按 Role 分解

| Role | Total | Content | Role | Role Rate |
|------|-------|---------|------|-----------|
| stem | 1870 | 1870 (100%) | 1820 | **97.3%** |
| explanation | 880 | 880 (100%) | 851 | **96.7%** |
| option | 5311 | 3138 (59.1%) | 2753 | **51.8%** |
| answer | 2282 | 2280 (99.9%) | 1120 | **49.1%** |

### Contract Readiness

| Contract | 状态 |
|----------|------|
| Stem binding | **PASS** (97.3%) |
| Explanation binding | **PASS** (96.7%) |
| Option region binding | **UNRESOLVED** — 需 schema 语义裁决 |
| Answer region binding | **UNRESOLVED** — 需共享答案表 contract 裁决 |

### Gate 状态

```text
Gate B1: CONDITIONAL PASS — Region Binding Contract 基本成立
Structured Evidence Binding: CONTRACT ADJUDICATED, IMPLEMENTATION NOT YET ESTABLISHED
Gate B2-A (stem + explanation): READY
Gate B2-B (option + answer): WAIT FOR MANIFEST CONTRACT UPDATE
```

### Contract Adjudication 裁决（2026-09-11）

**统一原则：Source Region 与 Question Evidence 必须分层。**

| 问题 | 裁决 | 核心 |
|------|------|------|
| Q1 `options_lines` | **A — Region** | 逐行拆分是 harness bug，不是 manifest 错误 |
| Q2 共享答案表 | **B — Per-question evidence** | Source region ≠ Question answer evidence |
| Q3 语法填空 | **B — Single span** | 行内多答案需 subspan/offset，不是多 span |
| Q4 HTML table | **B — Cell/row** | Region 是上层，evidence 需精确 |

### 下一步（按序执行）

1. **Gate B2-A**：stem + explanation 的 Legacy vs Path B 同口径对比（READY）
2. **B1-B Evidence Binding 实验**：验证 Q1-Q4 语义能否在真实 corpus 上稳定表达
3. **Gate B2-B**：option + answer（manifest contract 更新后）
4. **Gate C**：Safety Invariant Preservation 验证
5. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决
6. **Errata Decision**（Gate B/C/D 通过后）

## 状态快照：Gate B2-A 裁决（2026-09-11）

### Gate B2-A：PASS / TEST-EVIDENCED（stem only）

**核心证明：把"搜索问题"变成"验证问题"——Doc 67 架构变化方向正确。**

### 实验结果（79 cases / 2750 B1-clean targets）

| 指标 | Legacy Resolver | Path B |
|------|----------------|--------|
| stem | 829/1870 (**44.3%**) | 1820/1870 (**97.3%**) |

Agreement Matrix（stem）：

| | Path B validated | Path B not validated |
|---|---|---|
| **Legacy resolved** | 814 | 15 |
| **Legacy not resolved** | **1857** | 64 |

### 结论边界

- ✅ 在可信 Source Binding Claim 存在时，将 Resolver 从全文搜索转变为位置验证可以显著提高 stem binding 的可用性
- ❌ 不证明 Path B 的语义正确率为 97.3%（需独立抽样验证）
- ❌ 不证明 Path B 在所有 Question Roles 上优于 Legacy

### Explanation 不纳入对比

Legacy Resolver 没有 explanation search/binding 能力，0% 是 capability absence，不是 comparative failure。

### 关闭 B2-A 前三项补强

1. 审计 15 个 Legacy-success / Path-B-failure cases
2. 独立抽样验证 Path B 成功结果（1820 中抽 100-200）
3. 正式报告排除 explanation

### Gate 状态

```text
Gate B1: CONDITIONAL PASS
Gate B2-A: PASS / TEST-EVIDENCED（stem only；待三项补强后正式关闭）
Gate B2-B: NEXT — 结构化内容定位
Gate C: OPEN
Gate D: OPEN
```

### 下一步（按序执行）

1. **B2-A 三项补强**：审计 15 个 Legacy-only case + 独立抽样验证 + 排除 explanation
2. **Gate B2-B**：结构化内容定位（option/answer table/fill-in/HTML table）
3. **Gate C**：Safety Invariant Preservation 验证
4. **OQ-3 → OQ-2**：物化层 / Standalone+Material 裁决
5. **Errata Decision**（Gate B/C/D 通过后）

## 状态快照：Phase 1 Hardening + HIGH 严重性缺陷修复（2026-09-13）

### 背景

Evidence Promotion Contract Phase 1（EvidenceReference + ProposerIdentity +
ValidationEvent）实现完成后，进行两轮对抗性审查：
1. 第一轮（Phase 1 Hardening）：发现 9 个缺陷（3 CRITICAL + 3 HIGH + 3 MEDIUM）
2. 第二轮（架构审查裁决）：CRITICAL 全修复后，发现 2 个 HIGH severity 遗留

### Phase 1 Hardening 修复（第一轮，9 缺陷）

| 编号 | 严重性 | 缺陷 | 修复 |
|------|--------|------|------|
| C-1 | CRITICAL | append-only 可被绕过 | AppendOnlyEventLog（tuple-based） |
| C-2 | CRITICAL | 状态机在 service 层，可直接 append 绕过 | 状态机移入 AppendOnlyEventLog.append() |
| C-3 | CRITICAL | ValidationEvent 无 reference_ids 链接 | 添加 reference_ids 字段 |
| H-4 | HIGH | validation_method 硬编码 | 从 gate layers 推导 |
| H-5 | HIGH | gate reason 是叙述性字符串 | CheckResult 结构化检查 |
| H-6 | HIGH | ProposerIdentity 错误标为 native_parser | 修正为 llm |
| M-7 | MEDIUM | is_evidence_validated 按位置取最新 | 改为按 timestamp |
| M-8 | MEDIUM | 无 per-run 隔离 | GateService.run() 内 fresh instance |
| M-9 | MEDIUM | EvidencePromotionService 是 singleton | 改为 per-run |

### HIGH 严重性缺陷修复（第二轮，2 缺陷）

| 编号 | 缺陷 | 修复方案 |
|------|------|---------|
| HIGH-1 | `log._events = ()` 可清空日志 | `__slots__` + name mangling (`__events`) |
| HIGH-2 | 直接 `log.append()` 绕过状态机 | 状态机移入 `AppendOnlyEventLog.append()` |

**架构改进**：EventLog 是 Evidence Authority Ledger。状态机 enforcement 在 ledger 层，
不在 service 层。Phase 2 DB 化时状态检查仍在 ledger 层，直接调用 append() 无法绕过。

### 攻击验证

| 攻击向量 | 修复前 | 修复后 |
|----------|--------|--------|
| `log._events = ()` | 成功清空 | AttributeError |
| `service._validation_log.append(fake_event)` | 绕过状态机 | ValueError (terminal state) |
| 直接设置 `evidence.validated = True` | 可能（如果暴露） | ValidationEvent-only design |

### 测试证据

- test_evidence_promotion.py: 36 passed
- test_hardening_adversarial.py: 24 passed（新增对抗性测试）
- test_evidence_adversarial.py: 25 passed（新增对抗性测试）
- **全量回归：640 passed**

### 文档

- `backend/Docs/V3_SPEC/75_EVIDENCE_PROMOTION_CONTRACT.md` — 契约冻结
- `backend/Docs/V3_SPEC/76_EVIDENCE_PROMOTION_PHASE1_REPORT.md` — Phase 1 报告
- `backend/Docs/V3_SPEC/77_EVIDENCE_PROMOTION_PHASE1_HARDENING.md` — Hardening 报告
- `backend/Docs/V3_SPEC/78_PHASE1_HARDENING_ADVERSARIAL_REVIEW.md` — 对抗性审查
- `backend/Docs/V3_SPEC/79_PHASE1_HIGH_SEVERITY_FIXES.md` — HIGH 修复报告

### 当前状态

```
Evidence Promotion Contract Phase 1: IMPLEMENTATION COMPLETE + HARDENED
AppendOnlyEventLog: __slots__ + name mangling + state machine in append()
GateService integration: per-run isolation + reference_ids linking
全量测试: 640 passed
下一步: C-2 157 E2E → Gate C Closure
```

## 状态快照：架构审查裁决 — HIGH 修复通过，C-2 授权（2026-09-13）

### 裁决结果

**HIGH-1 / HIGH-2 修复通过。C-2 157 E2E 可以开始。**

### 关键修正

原报告声称"Evidence Authority Ledger 不可伪造、不可篡改、不可回滚"——**表述过度**。

准确表述：

> **Phase 1 Evidence Authority Ledger 已完成内存级不可绕过约束，满足进入 C-2
> 157 E2E 的最低安全条件；但距离完整生产级不可伪造审计系统仍存在 Phase 2
> 边界问题。**

`__slots__` 是 application-level immutability，不是 cryptographic immutability。
真正 immutable 需要 DB append-only table + permission control + audit hash chain（Phase 2）。

### 五项 Gate C 前置要求状态

| # | 要求 | 状态 |
|---|------|------|
| 1 | EventLog immutable | ✅ 基本完成（Phase 1 runtime model 下 externally non-mutable） |
| 2 | append transition validation | ✅ 完成（最重要项） |
| 3 | Event ↔ Reference 链接 | ✅ 完成（claim_id → EvidenceClaim → reference_ids → SourceFragment） |
| 4 | structured check_id | ✅ 完成 |
| 5 | proposer / claim creator 分离 | ⚠️ 延后 Phase 2（合理——OCR/LLM/Human adapter 进入后必须打开） |

### C-2 157 E2E 新增审查维度

不仅验证 Source → Resolver → Compiler → Gate → Admission，还需验证
**Evidence Authority Lifecycle**：

| 问题 | 必须结果 |
|------|---------|
| SourceFragment 来自哪里 | 有 hash/version |
| Proposal 谁提出 | 有 producer |
| Claim 谁提升 | 有 creator |
| ValidationEvent 为什么通过 | 有 check_id |
| ValidatedEvidence 对应哪些 span | 可追溯 |
| **IR 是否只消费 validated** | **无 bypass** |

**Semantic IR bypass test**（新增攻击向量）：

```
构造 EvidenceClaim → 不产生 ValidationEvent → 尝试 Compiler → 必须 rejected
```

核心原则：Only Validated Evidence may enter Semantic IR。

### C-2 重点观察（3 项）

1. 是否存在任何未经 ValidationEvent 的 Semantic IR 输入
2. 是否存在 resolution_status=exact 导致 evidence promotion 的隐式路径
3. 是否所有 rejection 都能追溯到结构化 check_id

### 约束

- **Evidence Contract 冻结**，C-2 不扩展
- C-2 目标单一：验证真实 157 invalid binding cases 全过程 fail-closed

### V3 状态重新评估

| 模块 | 状态 |
|------|------|
| B2-B5-D 实验 | ✅ Complete |
| Legal address ≠ legal evidence | ✅ Frozen principle |
| Structural consistency | ✅ Complete |
| Evidence Promotion Contract | ✅ Design accepted |
| Evidence Authority Ledger Phase 1 | ✅ Ready |
| C-2 157 E2E | ✅ PASS（20 tests） |
| Gate C Closure | ✅ **CLOSED (Phase 1 Evidence Authority Boundary Closure)** |

---

## 2026-09-13 — Gate C Closure (Phase 1)

### 架构审查裁决

**B2-B5-D：通过。Evidence Promotion Contract Phase 1：通过。C-2 157 E2E：通过。**

> Gate C 关闭名称限定为 **Phase 1 Evidence Authority Boundary Closure**。
> 不宣称 "生产级 Evidence Authority 完成"。

### Gate C Closure 声明

```
Gate C: CLOSED (Phase 1 Evidence Authority Validation)

Evidence Promotion Contract:    PASS
C-2 157 E2E:                     PASS
Semantic IR bypass:              PASS
Invalid Binding fail-closed:     PASS
```

### Deferred（合理延期至 Phase 2）

- Proposal/Claim creator separation（提出者=审核者自证风险）
- Persistent Evidence Ledger（DB append-only table）
- Cryptographic audit chain（audit hash chain）
- INVALIDATED state full lifecycle

### 核心架构跃迁

> 从"相信 Resolver 输出"升级为"不相信任何模块输出，
> 只相信经过 Authority Ledger 授权的 Evidence"。

关键修正：Ledger 下沉到数据层（append-only + state machine enforcement）解决 TOCTOU。
Evidence Validity 从隐含属性提升为显式授权状态（Authority State）。

### 分层边界（不可逾越）

```
Source → Evidence Authority → Semantic IR → Knowledge Reasoning
```

- Evidence Authority 保证：来源可追溯 / 提出者有身份 / 验证有 check_id / IR 只消费 validated
- Evidence Authority **不**保证：OCR 正确 / LLM annotation 正确 / 数学答案正确
- **Evidence Validity ≠ Semantic Correctness**

### 下一步优先级

| 顺序 | 项目 | 原因 |
|------|------|------|
| 1 | ~~Gate C Closure~~ | ✅ 本轮完成 |
| 2 | **Gate B2-A 三项补强** | Path B 主线真实阻塞 |
| 3 | Gate B2-B | 结构化内容定位 |
| 4 | Phase 2 Evidence Ledger | 等真实 pipeline 压力 |

---

## 2026-09-13 — Gate B2-A 三项补强审计

### 结果

| 项目 | 结果 |
|------|------|
| Total stem targets | 2342 |
| Legacy resolved | 1104 (47.1%) |
| Path B validated | 2268 (96.8%) |
| Path B improvement | +1164 targets, 2.1x coverage |

### Task A: Legacy-only Cases 分类

**20 个**（非之前报告的 15 个——那是 stem+explanation 混合统计）。

| Category | Count | 根因 |
|----------|-------|------|
| `no_pattern_match` | 17 | stem 以普通中文文本开头（作文题/材料题/公式开头），无结构标记 |
| `number_no_dot` | 3 | OCR 变体：`25：` 全角冒号 / `2018 年` 年份误匹配 |

**裁决**: 全部为 Pattern Coverage Gap，非 Path B 验证错误。
Path B fail-closed 行为正确——reject 而非 validate。

### Task B: 独立抽样验证

- Population: 2268, Sample: 150 (seed=42)
- Pattern 分布: number_dot 84.7% + number_escaped_dot 11.3% = **96% 标准题号格式**
- 目视检查 10 个随机样本：全部为合法 stem

**裁决**: Path B validated 结果可信。

### Task C: Stem-Only Comparative Metric

| | Legacy | Path B |
|---|---|---|
| Rate | 47.1% | **96.8%** |
| Agreement | Both OK 1084 / Legacy only 20 / Path B only 1184 / Neither 54 |

**Explanation 不纳入 comparative metric**（Legacy 覆盖率 0%，对比无意义）。

### Gate B2-A 补强后裁决

**Gate B2-A: PASS / TEST-EVIDENCED（stem-only, three-task audit complete）**

### 下一步优先级

| 顺序 | 项目 | 状态 |
|------|------|------|
| 1 | ~~Gate C Closure~~ | ✅ 完成 |
| 2 | ~~Gate B2-A 三项补强~~ | ✅ 完成 |
| 3 | ~~Gate B2-B（B1–B5 全系列）~~ | ✅ 完成（80 号） |
| 4 | ~~Grammar 契约裁决 / BUG-V3-044~~ | ✅ 本轮完成 |
| 5 | **Gate D** | Adapter Boundary（Grammar Contract 已冻结，阻塞解除） |
| 6 | OQ-3 → OQ-2 | 物化层 / Standalone+Material |
| 7 | B2-B2 Unknown 125 triage | 仍未清 |
| 8 | Phase 2 Evidence Ledger | 等真实 pipeline 压力 |
| 9 | Errata Decision | Gate D 通过后 |

---

## 2026-09-13 — BUG-V3-044 修复（AnswerTokenContract）

### 架构裁决（用户）

| 项目 | 裁决 |
|------|------|
| Gate B2-B5 | 保持 CLOSED，不回滚 |
| BUG-V3-044 | **必须修复** |
| 修复方案 | **Q-A 为主**（AnswerTokenContract 白名单） |
| Evidence Contract | **不扩大**（Q-B 留 Phase 2） |
| Evidence Promotion Phase 1 | **不回退** |
| Gate D | **延后**至 Grammar Contract 冻结后 |

架构定位：这是 Gate C 已解决的两层之下的**第三层**——
`Source Binding Boundary ✅ → Evidence Authority Boundary ✅ →
Semantic Answer Contract ✅（本轮）→ Admission`。
合法 Evidence 仍可能携带不符合 Answer Contract 的内容，被 strict-auto 误提升为
`verified_correct`。若先进 Gate D，外部 Adapter 产生的合法 Evidence 会经
Gate → Admission 写入错误 `verified_correct`，污染后续所有 Adapter 验证。

### 题号前缀冲突与裁决

裁决原文的拒绝清单含 `1. A`，但与三层既有冻结行为冲突：
① `_answer_span` 从题号条目起点切片（20 §5.5）→ 真实答案文本几乎总以 `N. ` 开头；
② `grammar.py` 专门剥离该前缀，注释写明刻意行为；
③ `test_gate_grammar.py` 有 8 条测试硬性要求 `1. A` 通过。
按字面拒绝会令真实 MC 答案几乎全部 pending_review，实质关闭 strict-auto。

**用户裁决：剥离后白名单**——保留 `_LEAD_QN_RE` 剥离（20 §5.5 不动），
AnswerTokenContract 只校验剥后剩余部分，`1. A` 仍 approve。

### 真实语料覆盖率实测与二次扩展

初版白名单在 101 份真实语料上造成 145 个 single_choice 回归，细分：

| 类别 | 数量 | 判定 |
|---|---:|---|
| `【答案】+字母` | 48 | ⚠️ 合法 → 扩展纳入 |
| `【分析】…` 解析类标记 | 48 | ✅ 修复收益 |
| 其他真实垃圾 | 35 | ✅ 修复收益 |
| `（N分）+字母` | 10 | ⚠️ 合法 → 扩展纳入 |
| `字母+句号` | 4 | ⚠️ 合法 → 扩展纳入 |

**用户裁决：扩至三种合法形态**（全串锚定）。关键原则区别：`【答案】` 是冻结的
答案表头 token（BUG-V3-031），直陈答案；`【分析】`/`【解答】`/`【考点】` 之后是
解释正文。二者语义不同，非特判。

扩展后 single_choice 保持通过 **56 → 119**；剩余 82 个回归全部为真实垃圾。

### 实现

`app/domains/gate/grammar.py`：
- 删除 `_option_letters()`（缺陷源头）
- 新增 `_SC_FORMS_RE`：单选五形态全串锚定白名单
  （裸字母 / 括号 / `【答案】`标记 / `（N分）`前缀 / 字母+句号）
- 新增 `_MC_TOKEN_RE`：多选「可选前缀 + 字母，仅既定分隔符」
- `true_false` 原有白名单不变（实测本就不受污染影响）
- grammar 三态约定不变（只 True/None，永不 False）

全串锚定是关键：`（3分）D["莫问…"]`、`【答案】D详见解析`、`D。本句采用暗喻。`
全部 → None。

### 测试

- 新增 `TestAnswerTokenContractPositive` / `BoundaryAttacks` / `TypeIsolation`
  （正向 / 边界攻击 / 题型隔离，+54 条）
- 反转 2 条原「记录缺陷」断言为「锁死修复」
- **全量 pytest 736 passed**（修复前 660），零失败
- 探针：C1/C2 由 `auto_approve` → **`pending_review`**；C0/C3 不变

### 显式不主张

1. 不主张 grammar 通过即语义正确——只验格式可表达性（必要不充分）。
2. 不主张覆盖全部真实答案形态——未见形态仍 fail-closed 到 pending_review。
3. Q-B（Evidence Claim 显式 `answer_form`）留 Phase 2，本轮未做。

### 文档回写

- `80_B2B5_CLOSURE.md` → v1.1.0，新增 §6 修复实现记录
- `bugs.md` BUG-V3-044 → **Resolved**
- log.md / restart-prompt → v1.44

### 下一步优先级

| 顺序 | 项目 | 状态 |
|------|------|------|
| 1 | ~~Grammar 契约裁决 / BUG-V3-044~~ | ✅ 完成 |
| 2 | ~~BUG-V3-044 对抗性审查~~ | ✅ 本轮完成（发现 1 真实缺陷已修） |
| 3 | **Gate D** | Adapter Boundary（阻塞已解除） |
| 4 | OQ-3 → OQ-2 | 物化层 / Standalone+Material |
| 5 | B2-B2 Unknown 125 triage | 仍未清 |
| 6 | Phase 2 Evidence Ledger | 等真实 pipeline 压力 |
| 7 | Errata Decision | Gate D 通过后 |

---

## 2026-09-13 — BUG-V3-044 对抗性审查

**审查文件**：`tests/test_bug044_adversarial_review.py`（62 项，8 维度）
**纪律**：每个结论必须有真实测试证据；发现缺陷则让测试失败并如实报告，不自我合理化。

### 发现 1 — 真实缺陷（已修复）

混合括号 `（A)` 曾被接受（应为 None）。根因：正则 `[（(]([A-Za-z])[）)]` 中
`[）)]` 是字符类，开闭括号各自独立匹配，超出裁决允许形态。
已拆为全角/半角配对分支；拒绝锁入契约测试。

**修复过程中自引入的第二个 bug（同轮捕获）**：`score_fw` 命名组只捕获数字、
字母在组外，会导致 `（3分）D` 匹配成功却返回 None。已在测试前修正。

### 发现 2 — 此前覆盖率报告的方法学缺陷（已修正）

原报告用「行内全部剩余文本」而非 E 的 char-span 切片。修正后重扫 **8166 条目**：

| 题型 | 保持通过 | 回归拒收 |
|---|---:|---:|
| single_choice | 552 | 261 |
| multiple_choice | 546 | 320 |
| true_false | 0（语料未观测到） | 0 |

261 个 single_choice 回归 = 205 真实垃圾（78.5%）+ 55 解析类标记（21.1%）
+ **1 个离群点 `A;`**（0.01%）。`A;` 非系统性合法形态，**不扩展白名单**。

### 发现 3 — 测试断言过严（非生产缺陷）

A2 期望 `'1. A'`、实际 `'1. A '`（切片天然含分隔空白）。生产行为正确，
已改为断言真正属性。

### 通过项

A2 span 语义 / A3 绕过全拒 / A5 MC / A6 true_false / A7 policy 集成 /
A8 无削弱（`_option_letters` 真正删除）——均有测试证据。

### 回归

全量 pytest **802 passed**（审查前 736，+66 项），零失败。
探针 C0/C3 不变，C1/C2 保持 pending_review。

### 下一步优先级

| 顺序 | 项目 | 状态 |
|------|------|------|
| 1 | ~~BUG-V3-044 + 对抗性审查~~ | ✅ 本轮完成 |
| 2 | **Gate D** | Adapter Boundary |
| 3 | OQ-3 → OQ-2 | 物化层 / Standalone+Material |
| 4 | B2-B2 Unknown 125 triage | 仍未清 |
| 5 | Phase 2 Evidence Ledger | 等真实 pipeline 压力 |
| 6 | Errata Decision | Gate D 通过后 |

---

## 2026-09-13 — Gate B2-B5 Closure + Gate B 文档对账

### 背景：发现状态不一致

重启对账发现 restart-prompt 仍写「下一步 = Gate B2-B」，但 git 历史显示
B2-B1～B2-B4 已于 2026-09-11 关闭、B2-B5-A/B/D 已于 2026-09-12 完成
（commits `3f0e79b` / `8bdd050` / `1bce065` / `5bce0bb` / `8ca1271`），
只是结果**从未回写** log.md / Status.md / restart-prompt，69 号 Gate B 状态块
仍写 `B2-B5: OPEN`。本轮补齐。

### 测试基线

全量 pytest：**660 passed**（零回归）。

### Gate B2-B5 正式关闭

**Gate B2-B5: CLOSED — PASS / TEST-EVIDENCED / SCOPE-BOUNDED**
权威文档：`backend/Docs/V3_SPEC/80_B2B5_CLOSURE.md`

| Phase | 裁决 | 关键数字 |
|-------|------|---------|
| A Classification | CLOSED — PASS | 706 targets（S1 469 / S2 94 / S3 143） |
| B Expressiveness | CLOSED — PASS / SCOPE-BOUNDED | 429 deterministically representable |
| C Invalid Binding | CLOSED — PASS | 157 targets → pending_review（UNRESOLVED / REVIEW REQUIRED） |
| D E2E Projection | CLOSED — PASS | 13 tests；零 search/LLM fallback / source mutation |

四条冻结架构原则保留：Address≠Authority / Claim=Promotion / Validated-only / No-inference。

### 本轮实测发现：Evidence Admission Boundary 仍 OPEN

doc 74 §6.3 记录的 latent weakness，本轮用真实 pipeline 探针确认**未关闭**：

```
backend/scripts/gate_b/gate_b2b5_closure_probe.py
backend/scripts/gate_b/gate_b2b5_closure_probe.txt
```

| Case | 答案区内容 | decision |
|------|-----------|----------|
| C0 | `1. A` | auto_approve（正确） |
| **C1** | `1. 【解答】A` | **auto_approve** |
| **C2** | `1. 【考点】…【解答】A` | **auto_approve** |

Grammar 边界：single_choice 对**任何恰好含一个 ASCII 字母**的正文返回 True，
包括 `见解析A页`、`参见教材A册第三章`。Admission 以原始文本持久化并置
`verified_correct=True`。

三层防御均未拦截：structural overlap 不触发（span 合法在 answer region 内）、
grammar-None 不触发（题型是 strict-auto）、Evidence Promotion Phase 1 是
additive-only（只记日志，不改准入判定）。

**处置**：登记为 OPEN architectural item（80 号 §3.4），**不随 B2-B5 关闭**，
**本轮不修复**——修复属生产行为变更，需先裁决 Grammar 契约（Q-A/Q-B/Q-C）。
B2-B5 语料全部为非 strict-auto，与本 weakness 正交，故不构成 B2-B5 阻塞。

### 文档回写

- 新增 `backend/Docs/V3_SPEC/80_B2B5_CLOSURE.md`（权威裁决）
- 69 号 Gate B 状态块：`B2-B5: OPEN` → `CLOSED`；Gate C/D 状态同步；下一步清单更新
- log.md：补记 B2-B1～B2-B5 系列与本轮 Closure
- restart-prompt：升版，0.0 节改为当前真实状态

---

## 2026-09-13 — Grammar 输入来源契约 + 测试规范固化

外部架构复审对 BUG-V3-044 提出三条补充。逐条核对真实代码与文档后：
**两条真缺口已补，一条确认已满足而未改**。

### 核对结论

| 复审补充项 | 结论 | 处置 |
|---|---|---|
| AnswerTokenContract 输入来源约束 | **真缺口** | 冻结为实现层契约（grammar.py + 80 §6.6） |
| 文档避免「保证答案正确」过度表述 | **已满足** | 不改——80 §6.5 / §5 与本文件均已是正确措辞 |
| 方法学错误进测试规范 | **真缺口** | 40 §5 新增一条 |

### 1. 输入来源契约（实现层冻结）

`Grammar.verify()` 的 `answer_text` **必须**是 Resolver 产出的标准化 answer span
（`resolver.py::_answer_span` 的 char-span 切片，20 §5.5），**不得**消费裸
source / OCR 文本。题号前缀属 Resolver 边界产物，不参与答案 token 判定。

此前该契约只靠唯一生产调用方（`policy.py::_leaf_grammar` 传 `leaf.answer.text`）
自觉遵守——`verify()` 签名只有 `answer_text: str`，类型上无法区分两者。

**不走正式 Errata 的理由**：冻结文本 20 §8.4 对 `answer_text` 来源**完全沉默**，
是「未规定」而非「规定错误」，不属 Contract Change，不触发 69 号四道门。该流程
当前亦 `BLOCKED BY Gate D`，走它会与「Gate D 前补上」自相矛盾。已挂入 80 §4
显式延期项——若日后要写进 20 §8.4 正文，须走正式 Errata。

### 2. 分层职责澄清（防过度承诺）

| 层 | 能保证 |
|---|---|
| Resolver | 找到哪里 |
| Evidence Authority | 证明来源 |
| **Grammar** | **表示形式合法** |
| Gate | 结构规则 |
| Semantic Model | 内容正确 |

grammar 保证 representation validity，**不保证** semantic correctness。

### 3. 测试规范（40 §5 新增）

度量实验（覆盖率 / 回归 / 通过率）的输入必须是上游组件的**真实输出切片**，
禁止近似文本代替；度量脚本须能指出它复刻的是哪一段 pipeline，并有测试锁死
该复刻语义。反例即本轮覆盖率测量曾用「行内剩余文本」代替 E 的 char-span。

### 回归

`test_gate_grammar.py` + `test_bug044_adversarial_review.py` +
`test_role_provenance.py` + `test_b2b5_d_projection_safety.py` →
**205 passed**。本轮仅改 docstring 与文档，无生产逻辑变更。

### 下一步优先级

| 顺序 | 项目 | 状态 |
|------|------|------|
| 1 | ~~BUG-V3-044 + 对抗性审查~~ | ✅ |
| 2 | ~~Grammar 输入来源契约 + 测试规范~~ | ✅ 本轮完成 |
| 3 | **Gate D** | Adapter Boundary — 阻塞已全清 |
| 4 | OQ-3 → OQ-2 | 物化层 / Standalone+Material |
| 5 | B2-B2 Unknown 125 triage | 仍未清 |
| 6 | Errata Decision | Gate D 通过后 |

---

## 2026-09-13 — Gate D CONTRACT CLOSED / IMPLEMENTATION NOT STARTED：Adapter Boundary 契约冻结

**权威**：`backend/Docs/V3_SPEC/81_GATE_D_ADAPTER_BOUNDARY.md`
**出口标准（用户裁决）**：只冻结契约，不要求实现。
**回归**：全量 pytest **802 passed**，零失败（无生产逻辑变更）。
**状态措辞**：Gate D 的要求是**契约裁决**，不是实现验收，故不用裸 `CLOSED`。

### 开题事实

adapter / preprocessing 代码**不存在**；manifest 解析**不存在**；
I-5-1 声称的 14 项实验**全仓无脚本、无测试、git 历史零提交**；
冻结的 manifest schema **V3 Spec 中无**。
**Gate D 是契约裁决，不是代码审查。**

### 四项发现

| # | 发现 | 级别 | 处置 |
|---|---|---|---|
| 1 | `Bypasses: Annotation` 与 `IRBuilder.build` 签名冲突 | 🔴 | 修正为 `Bypasses: Resolver only` |
| 2 | Grammar 输入来源契约过窄（本轮早前自引入） | 🔴 | 改写为不变量形式 |
| 3 | I-5-1 实验证据不可复现 | 🟠 | 降级为方向性参考 |
| 4 | 66 §10 要求 Adapter 加 parser，违反 66 §7 自身禁令 | 🟠 | 记录，gap 判给 preprocessing |

**发现 1 证据**：`ir.py:87` 的 `build(resolved_run, annotation_payload, ...)`
必需 annotation_payload，其 `semantic_units[]`/`unit_id`/`unit_type`/`content{}`
驱动全部语义结构；span_id 约定 `sp-{unit_id}.{role}`（`ir.py:64-76`）由 annotation
反推。绕过 Annotation 则连 span_id 都构造不出来。

**发现 2 根因**：写了**机制**（谁产出），不是**不变量**（该 span 具备哪些性质）。
`ResolvedSpan`（`span.py:61-75`）无生产者字段，「Resolver 产出」在数据上不可验证，
且会非法排除整条 Adapter 路径。

### 用户裁决

- annotation_payload 从哪来 → **preprocessing 产出 V3 形制 annotation**
- Gate D 出口标准 → **只冻结契约，不要求实现**

### 冻结的 Adapter Contract 摘要

```text
SealedSource → preprocessing → (annotation_payload + manifest)
             → Adapter → ResolvedRun → IRBuilder → Compiler → Gate → Admission
Bypasses: Resolver only
```

- Native Path（preprocessing 缺席）不受影响，两条路径同构于 ResolvedRun
- **核心不变量（高于任一单项禁令）**：**Adapter 只允许机械投影，不允许提高
  信息量**。输出的信息量 ≤ 输入（manifest ∪ SealedSource 确定切片）。六条禁令
  都是它的具体化。
- **「绕过 Resolver」的准确含义**：绕过其 search/resolve **机制**（以验证替代
  搜索），**不是**绕过 Source Binding。下游 IRBuilder / Compiler / Gate 两条
  路径完全一致。
- Adapter 职责白名单 5 项：line_ref 展开 / text_hash 计算 / 范围校验 /
  ResolvedSpan 构造 / 结构一致性检查
- 禁令黑名单 6 条：第二事实来源 / 第二 Resolver / 隐式 fuzzy matching /
  自主 Source 内容生成 / 独立 semantic decision / 内容解析与结构推断
- 判定原则：每个输出字段必须能指出来源；**指不出 = 违规**
- **契约方向不可颠倒**：V3 首先冻结它**自己要消费**的 Annotation / Manifest
  契约，preprocessing 再**实现**它。不是 preprocessing 自行设计 annotation
  再由 V3 适配（74 号）。
- V3 侧三项前置：V3 annotation schema 对外发布 / manifest schema 冻结
  （含 answer_text 与 per-option span）/ SealedSource 版本绑定

### Grammar 输入契约修订（81 §6.2）

`answer_text` 必须是 `ResolvedRun` 中 `role=answer` 的 `ResolvedSpan` 文本切片，
且 `granularity` 为字符切片、`resolution_status ∈ {exact, normalized}`、
`text_hash` 与 SealedSource 一致。**生产者可以是 Resolver 或 Adapter**。
明确不给 `ResolvedSpan` 加生产者字段（YAGNI）。

### Gate 系列最终状态

```text
Gate A   : PASS / TEST-EVIDENCED
Gate B1  : CONDITIONAL PASS
Gate B2-A: CLOSED — PASS
Gate B2-B1~B2-B5: CLOSED（B2-B3-C / B2-B4-C DEFERRED）
Gate C   : CLOSED (Phase 1)
BUG-V3-044: CLOSED（含对抗性审查）
Gate D   : CONTRACT CLOSED / IMPLEMENTATION NOT STARTED
Adapter  : NOT STARTED（阻塞于 81 §5.4 三项前置）
Errata   : UNBLOCKED
```

### 下一步优先级

| 顺序 | 项目 | 状态 |
|------|------|------|
| 1 | **Errata Decision** | Gate D 已过，阻塞解除；**不进入 Adapter 实现** |
| 2 | V3 Annotation Contract 冻结 | V3 拥有，preprocessing 实现（81 §5.4） |
| 3 | Manifest Contract 冻结 | — |
| 4 | OQ-3 → OQ-2 | 物化层 / Standalone+Material |
| 5 | B2-B2 Unknown 125 triage | 仍未清 |
| 6 | Phase 2 Evidence Ledger | 等真实 pipeline 压力 |
| 7 | Path B Full Closure E2E | — |
| 8 | I-5-2 Adapter 实现 | **最后**；阻塞于 81 §5.4 三项前置，依赖链不可倒序 |

---

## 2026-09-13 — Contract Authority Reconciliation（82 号 ACTIVE）

**权威**：`Docs/V3_SPEC/82_CONTRACT_AUTHORITY_RECONCILIATION.md`
**触发**：外部对抗性审查收紧上一轮结论——文档权威层级漂移是 P0，须先治理再谈 Errata。
**本轮不做**：不改 20；不冻结 manifest-only；不写 Errata Decision；不实现 Adapter。

### 核验结果（不靠推测，逐条到 file:line）

| ID | 冲突 | 证据 | 处置 |
|---|---|---|---|
| **C1** 🔴 | Gate C：74 仍 BLOCKED，80 已 CLOSED，**无废止记录** | `74:5/363/537` vs `80:439`；C-1=`75`、C-2=`76/77` 已完成 | 82 §3.1 即废止记录；74 三处加 supersede 标注 |
| **C2** 🔴 | 69 §8 无日期路线图仍写「Errata Decision（Gate A-D 全部通过后）」 | `69:306` | 加 supersede 指针 → 82 §8 |
| **C3** 🔴 | 81:11 称「Gate B 系列 CLOSED」，**过度陈述 80**（本轮自引入） | `81:11` vs `80:421` B1 CONDITIONAL、`80:432/437` DEFERRED | **已修正**，改列 Gate B 真实状态 |
| **C4** 🟠 | 80 内部 B2-B2 同时 CLOSED 与 Unknown 125 未清 | `80:426` vs `80:448` | **歧义非错误**，待 triage 补 scope 声明 |
| **C5** 🟠 | 69 历史矩阵仍写 B2-B BLOCKED/WAIT | `69:656`、`69:756` | 历史快照，保留；以 82 §3 为准 |
| **C6** 🟠 | E1 性质 | `20:662-679` 对 answer_text 来源**沉默** | 归 **CHANGE-2 Normative Addition**，不写入 20 |
| **C7** 🔴 | 无 Authority Matrix / 无变更分类 | 全仓 grep 零命中 | 82 §1/§2 建立 |
| — | 「Gate B2-B = NEXT」 | 全仓 grep | ❌ **不成立**（无「NEXT」措辞） |

### 82 号建立的治理机制

1. **五层权威矩阵**：A Frozen Spec（Normative）/ B Decision Record（仅裁决范围，
   不得覆盖 A）/ C Phase Report（Informative，**禁用规范性语言**）/ D Status
   （不得与 82 §3 矛盾）/ E Experimental（**不得单独支撑 PASS**）。
2. **CHANGE-0…5 分类**：四道门**仅适用** CHANGE-4 放宽 / CHANGE-5 删除。
   **新增强制 invariant = CHANGE-2**，需 Change Record 但不走四道门。拿不准往高里归。
3. **Gate State Authority = 82 §3**（唯一权威）。**聚合规则冻结**：存在 CONDITIONAL
   或 DEFERRED 子项时父 Gate 不得记 PASS/CLOSED。

### Gate 系列状态（依据 82 §3）

```text
Gate A   : PASS / TEST-EVIDENCED
Gate B   : NOT CLOSED
           B1 CONDITIONAL PASS（option Role 51.8% / answer 49.1%；Structural 未评估）
           B2-A / B2-B1 / B2-B2 / B2-B3-A,B / B2-B4-A,B / B2-B5 : PASS / SCOPE-BOUNDED
           B2-B3-C / B2-B4-C : DEFERRED
Gate C   : CLOSED (Phase 1)（supersedes 74）
Gate D   : CONTRACT CLOSED / IMPLEMENTATION NOT STARTED
Adapter  : NOT STARTED（阻塞于 81 §5.4）
BUG-V3-044: CLOSED
Binding Carrier : PENDING（BIND-1/2/3 未裁决）
Errata   : 暂缓（67 号 CHANGE-5 不得发布，Gate B NOT CLOSED）
```

### Binding Authority 三个未决问题（82 §5，登记未裁决）

- **BIND-1**：Annotation semantic unit ↔ Manifest binding unit 是否存在**确定性
  identity join**？若依赖顺序/题号/模糊匹配 → 重新引入 Resolver-like 问题，违反
  81 §5.6。**本轮最值得新增的审查点。**
- **BIND-2**：Native Path 能否完全脱离 `annotation.line_refs`？
- **BIND-3**：Manifest 的 role declaration 是 External Claim 还是 Semantic Authority？
- 候选：manifest-only = 🟡 PROVISIONAL；annotation 内 = 🔴 不得推进；共存 = 🔴 REJECT。
- **关键澄清**：`line_refs` 在 annotation 中**不自动违反** Source-as-Fact-Source。
  违规的是「LLM line_refs → 直接相信 → ResolvedSpan」；「→ Resolver 验证 →」不违规。

### 下一步

| 顺序 | 项目 |
|------|------|
| 1 | **Binding Authority Decision**（BIND-1 优先） |
| 2 | V3 Annotation Contract 冻结（V3 拥有，preprocessing 实现） |
| 3 | Manifest Contract 冻结 |
| 4 | Change Records（E1=CHANGE-2；67=CHANGE-4/5 REJECT） |
| 5 | Errata Decision（前置全满足后） |
| 6 | 最小 Adapter + 对抗性测试 → 真实 corpus E2E → Path B Full Closure |
| — | 非 Path B：OQ-3 → OQ-2；B2-B2 Unknown 125 triage（补 C4 scope）；Phase 2 Evidence Ledger |

**Gate 状态变更必须同 commit 更新 82 §3。**

---

## 2026-09-13 — Phase I-5-G Document Governance Audit（83 号）

**权威**：`backend/Docs/V3_SPEC/83_GOVERNANCE_AUDIT.md`（C 层）
**方法**：`backend/scripts/i5g_normative_scan.py` 机械扫描，只读；**Reconcile, don't rewrite**
**本轮不做**：不改 20；不发 67；不冻结 manifest-only；不写 Errata Decision；不实现 Adapter

### 分层合计

| 层 | 文档数 | 行数 | 命中 | 密度 |
|---|---|---|---|---|
| A Frozen Spec | 7 | 3163 | 410 | 13.0% |
| B Decision Record | 7 | 3445 | 512 | 14.9% |
| C Phase Report | 17 | 4672 | 291 | 6.2% |
| D Status | 3 | 4558 | 842 | 18.5% |
| **UNCATEGORISED** | **5** | **837** | **61** | 7.3% |

**限定**：标记词命中 ≠ 违规。A 层应高密度；「只能证明 / 本实验采用」是正确写法。

### 六项发现（全部只登记，未处置）

| ID | 发现 | 级别 |
|---|---|---|
| **G2** | **71 号同号双份且内容不同**：root 6914 B（21:33，「裁决记录」）vs backend 7783 B（23:05，「(CORRECTED)」），`diff` 判 DIFFERENT。**旧的那份在 A 层目录**，路径直觉会当更权威。比 C1 更糟——两个文件抢同一编号且无废止声明 | 🔴 |
| **G1** | **5 份文档未分类**（837 行）：4×`Closure/PHASE_I*_CLOSURE.md`（`PHASE_I3_CLOSURE.md:5` 直接写 `Gate: PASS` 却不在 82 §3 表内）+ `gate_b2a_three_task_report.md` | 🔴 |
| **G3** | **分层错误 3 份**：`63` 自述 `Frozen Constraint`（A/B 待裁决，升 A 须 Change Record）；`65` 是 scope freeze 契约（`65:95-106` 十二条禁令）；`68` 保持 C 但须注明 69 定性 | 🟠 |
| **G4** | **C 层自立规范**：`74` 对 V3 立规（`224`/`226`/`283`/`385`/`395-396`/`418`）。对照 `74:94`「这个结果只能证明」是正确用法——缺的是分类约束 | 🟠 |
| **G5** | **Gate 状态行集中面**：`Status.md` 45 行 / `69` 42 行，聚合错误最大温床（C3 即此类产物） | 🟠 |
| **G6** | `restart-prompt` 密度 36.6% 全仓最高——不压缩，改由 82 §11 读取顺序约束 | 🟡 |

### I-5-G 完成条件对账（82 §10）

**✅ 达成 4 项**：Authority Matrix / Gate State Authority / Frozen Spec 不被隐式修改 /
67-82 关系可解释。
**🟠 进行中 5 项**：归层 / 分类 / Gate 状态对账 / CHANGE 覆盖 / supersession。
**🔴 阻塞 1 项**：第 10 项「无未分类的 normative contradiction」——**G2 未解决**。

> **结论：I-5-G 未完成（不得进入 I-5-BIND）。**

### 82 号新增

- **§9 Status Header 规范**（83 号起强制）：Document Type / Authority Level /
  Status / Normative / Supersedes / Superseded By / Gate State Authority
- **§10 Phase I-5 CURRENT BASELINE**：14 行状态表，**优先于任何 Phase Report**
- **§11 Agent 强制读取顺序**：82 → 00–50 → Decision Record → 82 §3 →
  Experimental → 历史文档。**禁止「grep 到什么读什么」**

### 下一步

| 顺序 | 项目 |
|------|------|
| 1 | **裁决 83 §6 六项**（**G2 的 71 号双份优先**） |
| 2 | G1 归层 → 写入 82 §1.2，不改写正文 |
| 3 | G3-a 裁决（`63` 是 A 还是 B）+ G3-b（`65` 归 B） |
| 4 | G4 处置（`74` 逐条：指针 / 引用式改写） |
| 5 | 重跑 `i5g_normative_scan.py` 全仓复查 |
| 6 | I-5-G 10 项全绿 → Current Baseline declared |
| 7 | **I-5-BIND**（BIND-1 优先） |
| 8 | Annotation Contract → Manifest Contract → Change Records → Errata Decision → Adapter |

**Gate 状态变更必须同 commit 更新 82 §3；新增 Gate 状态行须用 82 §3.3 模板。**

---

## 2026-09-13 — 治理元规范 90 号 + Conflict Ledger 84 号 + docs_audit

**权威链**：`90`（元规范，L0-META）→ `82 §3`（Gate State Authority，**唯一**）→
`84`（Conflict Ledger）→ `docs_audit/`（机器可读）
**本轮不做**：L0 六册零改动；不发 67；不冻结 manifest-only；不写 Errata Decision；
不实现 Adapter；**不对 84 任何条目裁决**

### 90 号 — 治理元规范（吸收 82 §1/§2/§9/§11；82 降为 L2 执行记录）

| Level | 类型 | 权限 | 禁止 |
|---|---|---|---|
| **L0** | Frozen Spec `00`–`50` | 定义系统事实；Schema SoT = `20` | 不得被 L2–L5 隐式修改 |
| **L1** | Contract Change Record | **修改 L0 的唯一入口**（当前为空） | 未走完流程不得生效 |
| **L2** | Decision Record | 解释与裁决 | **不得产生新架构事实**；不得改 L0 |
| **L3** | Gate Report | 证明状态 | 不得定义规则；Gate 状态只能**引用 82 §3** |
| **L4** | Experiment Report | 提供证据 | 不得单独支撑 PASS；不得把实验结论升为事实 |
| **L5** | Status / log / restart | 项目管理 | 不得与 82 §3 矛盾 |

**最高规则**：**L3/L4/L5 永远不得改变 L0/L1；L2 只能解释与裁决，不得修改 L0。**
旧 A–E 的 C 拆为 L3+L4——Gate 报告与实验报告权限不同。

### 84 号 Conflict Ledger：15 OPEN / 4 已处置 / 3 误报

**本轮新增核验发现**：

| ID | 发现 | 级别 |
|---|---|---|
| **A-07** | `73:213` 声明 157 targets `UNRESOLVED / REVIEW REQUIRED`（`NOT proven: All 157 are correct bindings`），而 Gate C 以 C-2「157 E2E」关闭。**A-01 同类**——无文件声明 73 已关闭。**可能动摇 Gate C 证据基础** | 🔴 |
| **B-01** | **`Evidence Contract` 零定义却被 ≥4 份文档用来立规**（13 处使用，定义 grep 零命中）。违反 90 §2 R6 | 🔴 |
| **B-02** | 三近义词仅一个有宪法地位：`Validated Evidence`（10 处，**全在 L3 `74`**）/ `Verified Evidence`（零使用）/ `verified_correct`（L0 `20 §8.3`） | 🔴 |
| **A-06** | `61:4` `IN PROGRESS` vs `Closure/PHASE_I3_CLOSURE.md` CLOSED——Phase I-3 关闭后 61 从未回写 | 🟠 |
| **A-08** | `Status.md:2309`（已撤回 Grammar 契约，未标记）vs `:2423`（不变量版） | 🟠 |

**三处误报已记录（84 E 类）**：E-01 `81:208-211` 管线图是**两条显式标注分支**非 MIXED；
E-02 `10:777→20 §12.1` 是 **changelog** 记录已修正的旧值；E-03「B2-B = NEXT」全仓不存在。

### docs_audit/ 机器可读产物（`i5g_emit_audit.py`，只读扫描）

| 产物 | 内容 |
|---|---|
| `authority_matrix.yaml` | **L0=7 / L0-META=1 / L2=11 / L3=3 / L4=16 / L5=4 / UNASSIGNED=1** |
| `contradiction_candidates.json` | 84 台账机器形式 + **196 条 Gate 状态行** |
| `frozen_terms.json` | 14 个关键术语定义/使用分布 |
| `scan_report.md` | 人读汇总（OPEN 15，P0 六项） |

**归层说明**：4×Closure 在机器产物中**暂定 L2**（reason 标 `pending D-02 adjudication`）
——**提案非裁决**，D-02 仍 OPEN。`gate_b2a_three_task_report.md` 仍 UNASSIGNED。

### Gate 系列状态（依据 82 §3，未变）

```text
Gate A  : PASS          Gate B  : NOT CLOSED
Gate C  : CLOSED(P1)    Gate D  : CONTRACT CLOSED / IMPLEMENTATION NOT STARTED
Adapter : NOT STARTED   Binding Carrier : PENDING
Errata  : 暂缓          Documentation Governance Pass : 未完成
```

### 下一步

| 顺序 | 项目 |
|------|------|
| 1 | **裁决 84 台账 15 项 OPEN**：D-01 → A-07 → C-01 → B-01 → B-02 → D-02/D-03 → A-04/06/08/09 → D-04/D-05 |
| 2 | 重跑 `i5g_emit_audit.py` 复核 `docs_audit/`，diff 看治理漂移 |
| 3 | 90 §10 十项全绿 → Current Baseline declared |
| 4 | **I-5-BIND**（BIND-1 优先；`82 §5`） |
| 5 | Annotation Contract → Manifest Contract → Change Records → Errata Decision → Adapter |

**权威链**：90 → 82 §3 → 84 → docs_audit/。**Agent 读取顺序（90 §7）强制：
90 → 82 §3/§10 → L0 → L1/L2 → L3 → L4 → L5。禁止「grep 到什么读什么」。**

---

## 2026-09-13 — CA-001 L0 修改审计 + P0 三项裁决 + R7–R10

**触发**：用户指出 `40` 今日 14:33 被改而它是 **L0**，须先审计；并裁决 P0 三项、要求拆 commit。

### 🔴 CA-001 — L0 完整性问题（当前最高优先级）

`40 §5` 在 `0dd954d`（09-13 14:43，**本轮我自己改的**）被新增一条**强制**规则，
**无 Change Record**：

> 测量语义**必须**复刻真实 pipeline…**禁止**用近似文本代替…度量脚本**必须**能
> 指出它复刻哪一段 pipeline，并有测试锁死该复刻语义。

- **CHANGE-2 Normative Addition**——新增「指出复刻哪一段」+「测试锁死」两项
  此前不存在的可验证要求，**不是** Clarification。
- **时序缓解因素，非豁免**：90 生效前发生，但 `82 §2` 与「先冻结 Spec」已存在。
- **内容可辩护**（BUG-V3-044 教训），**缺 Change Record 是事实**。
- **审计范围**：`0dd954d` 后触及 L0 的**仅 40 一处**；更早 L0 修改自带 `errata` 标记。
- **待裁决**：(a) 追认 / (b) 撤回重走 L1 / (c) 挂起。见 `90 §11`。

### P0 三项已裁决

| ID | 裁决 | 处置 |
|---|---|---|
| **A-07** | **语义A 成立，Gate C CLOSED 不动摇** | `72 §3` 157 = invalid/suspicious；`73:215-221` NOT proven **全是语义正确性**；C-2 = `test_c2_evidence_authority_e2e.py` 证明**管线不变量**。已在 `73` 文首写 **C-2 Evidence Scope Clarification**，**正文未改** |
| **B-01** | **名称漂移非概念缺失** | `75` 实际标题「Evidence **Promotion** Contract」。已在 `75` 加 **Terminology** 节声明等同；**不全文替换**；新文档用全称 |
| **B-02** | **不升 L0；我先前判「零定义」是错的** | `Validated Evidence` **有 L2 定义**（`75:42` 状态机 `state: trusted`、`75:194` `§4.5`）。它是证据生命周期**状态**（系统机制）非基础原则。`90 R9` 冻结 `≠ verified_correct` |

### 90 号新增 R7–R10

- **R7 引用闭包**：L2/L3/L4 规范性结论必须存在向上闭包
- **R8 废止传播**：`supersede` 后不得作为引用来源；扫描器跳过；标 `deprecated`
- **R9 Evidence 术语不可互换（永久）**：`Validated Evidence ≠ verified_correct`；`Verified Evidence` 永久禁用
- **R10 L2 不得创造新名词**：`Binding Carrier` / `External Claim` / `Semantic Authority` 三项 ⚠️ 未定义

### 检测器改进（R6 定义形态扩展）

识别表格 / 状态机 `state:` / 「唯一可进入」。`Validated Evidence` defs 0→6、
`ResolvedSpan` 0→3、`annotation_payload` 0→1、`FORBIDDEN_FIELDS` 0→1。
**所有 HIGH 漂移风险清零**——证实全是检测器局限，不是文档缺陷。

### Closure 归层 → `L2-proposed` / `pending`

L2 本身也是治理事实，未经裁决不能成为事实。

归层：L0=7 / L0-META=1 / L2=7 / **L2-proposed=4** / L3=3 / L4=16 / L5=4 / UNASSIGNED=1

### 状态

```text
OPEN 12（P0：CA-001 / D-01 / C-01 / D-02）
已处置 7（SUPERSEDED 2 + INCORPORATED 2 + DECIDED 3）
误报 3 · MITIGATED 1
Gate 系列未变：A PASS / B NOT CLOSED / C CLOSED(P1) / D CONTRACT CLOSED
```

**本轮未裁决 CA-001 / D-01 / C-01 / D-02；未改任何 L0 内容。802 passed。**

### 下一步

| 顺序 | 项目 |
|------|------|
| 1 | **裁决 CA-001**（追认 / 撤回 / 挂起）— L0 完整性 |
| 2 | D-01（71 号双份） |
| 3 | C-01（`line_refs`，须走 BIND-1/2/3） |
| 4 | D-02 / D-03（归层） |
| 5 | A-04/06/08/09 + D-04/05 |
| 6 | 90 §10 全绿 → Current Baseline |
| 7 | I-5-BIND |

**L0 修改强制登记于 90 §11，否则违规。**
