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
