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
