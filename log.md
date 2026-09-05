# AI Tutor V3 — 变更日志

> **更新规范（参照 V2 `LOG.md`）**
> - 本文件只记录 V3 的**变更/决策落地**；**每次更新含当前时间戳（`YYYY-MM-DD HH:MM:SS`），
>   按时间顺序在文档末尾流式追加**；不改写、不置顶既有历史。早期条目为日期级。
> - 日常进度/验收数字不写这里 → `Status.md`；缺陷 → `bugs.md`；架构规则一律在
>   `Docs/V3_SPEC/`（README §3.3：分册不承载状态，状态回写本类根文档）。
> - 过旧的历史整段归档至 `docs_archive/`（保留不删），本文件只保留近段。
> - 只追加、不覆盖；每条尽量带「背景 / 决策 / 影响 / 验证」四要素。

## 变更记录

### 2026-09-05（V3 Baseline — Frozen）

- **V3 架构与开发契约冻结**：`Docs/V3_SPEC/` 六册（00 v1.2 宪法 / 10 v1.2.1 /
  20 v1.2 / 30 v1.1 / 40 v1.1 / 50 v1.1）+ README v1.1 统一为
  `V3 Architecture & Development Baseline — Frozen`。
- 7 份起草输入（`V3_*.md`）归档至 `docs_archive/2026-09-05_v3_draft/`。
- 全体系跨册对抗性审查无结构性冲突；00 服从性证据见
  `Docs/V3_SPEC/README.md §1.2`。
- **下一步**：实现前资产清点（`50 §3`）→ `40 §2` 段 A（骨架）。

### 2026-09-05（根状态文档建立）

- 在 V3 根目录建立状态四件套（记录规范参照 V2 状态文档）：`log.md`、`bugs.md`
  （编号从 `BUG-V3-001`）、`Status.md`（**取代 V2 `PROJECT_STATUS.md`**）、
  `restart-prompt.md`（重启恢复）。
- 同步 `Docs/V3_SPEC/README.md §3.3`：状态回写目标改为实际根文档名。

### 2026-09-05 16:53:15（协作规则采纳）

- 采纳用户两条规则（存记忆 `v3-plan-and-status-doc-rules`）：
  1. **计划受 V3-Spec 约束**：功能/架构类代码变更做计划前必遍阅 `Docs/V3_SPEC/`，
     确保计划在冻结 spec 约束下；
  2. **状态文档流式更新**：所有状态文档（`log.md` / `Status.md` / `bugs.md` /
     `restart-prompt.md`）更新须含当前时间戳、按时间顺序在**文档末尾**流式追加
     （取代 V2「最新置顶覆盖」习惯）。
- 本文件与 `Status.md` 的更新规范据此改为末尾流式。

### 2026-09-05 17:07:47（V2 遗留文档分类归档）

- 只读分类审计 `Docs/` 遗留（除 V3_SPEC）：A 类=V3 业务输入保留（REQUIREMENTS /
  DISPLAY_CONTRACT / QUESTION_TYPE_TREE / DICTIONARY / V1_LESSONS）；C 类=参考保留
  （PADDLEOCR_API / OCR_PROVIDER_POLICY / UI / PRD）；B 类=V2 架构/执行遗留归档。
- 按裁决移 7 份至 `docs_archive/2026-09-05_v2_legacy/`：`SAD / ACS / MIS / DSD /
  PIPELINE / ROADMAP / DECISIONS`。V3_SPEC 无引用断裂（00 仅引 REQUIREMENTS、
  DISPLAY_CONTRACT、V1_LESSONS，均未动）。
- 待办：`DISPLAY_CONTRACT` 补 T/F↔A/B canonical 映射（20 §8.4 strict-auto 前置，进段 G 前）。

### 2026-09-05 17:10:33（Docs 目录重整）

- 保留文档（业务输入 + 参考共 9 份）合并至 `Docs/reference/`；清空并移除五个旧分类目录
  （00_Requirements / 01_Product / 02_Architecture / 03_Data / 05_Development）。
- 同步：00 引用路径 errata（REQUIREMENTS / DISPLAY_CONTRACT / V1_LESSONS → `Docs/reference/`，
  仅路径，无语义变更）。`Docs/` 现仅 `reference/` + `V3_SPEC/`。

### 2026-09-05 17:15:03（资产清点完成）

- 按 50 §3 产出 `Docs/reference/ASSET_INVENTORY.md`（v0.1）：外部能力（PaddleOCR-VL 云端 +
  PP-StructureV3 双源、本地 ollama LLM、qwen3-embedding）、真实 PDF ~40（9 科，V2 test/pdf）、
  golden 8 份（real/contract，V2 test/annotations/golden）、question type / knowledge tree
  seed（V2 backend 内嵌 Python）、非代码契约与失败教训全部定位；本体留 V2。
- 缺口 5 项列清单 §7；两项待用户裁决：**①样本是否复制入 V3 及路径**；**②cloud OCR
  （PaddleOCR-VL）M1 是否启用**（默认不启用，本地 PP 优先）。

### 2026-09-05 17:18:07（资产两项裁决）

- ① **样本 PDF：用户自有、可随时补充**；V3 不复制、不依赖 V2 路径（清单 §2/§7#1）。
- ② **M1 启用 cloud OCR（PaddleOCR-VL）**；实现前置 = 40 §2 **C 段 external 闸先行**，
  B 段 seal 方能启用 cloud；token 走 `.env` 不硬编码；本地 PP 作辅助（清单 §7#2；30 §16）。
- golden 结构确认：与 PDF 精确 filename 严格匹配；文本真值可复用，行号坐标废弃（清单 §3）。

### 2026-09-05 17:22:41（golden 甄别 + 迁移）

- **甄别修正**：V2 `test/annotations/golden/` 10 份实为三族，非全 human——human 验收级 3
  （`math_real_golden` v4.0 / `english|math_exercise_2024` v3.1）、契约标注族 5
  （`display_contract_version: 0.4`）、**机器草稿 2**（`english|physics_2026_real_golden`
  标 `0.1-draft`，V2 自注"不得直接用于验收"）。清点此前将草稿误记为人 gold，已修正。
- **契约文档定位**：用户所称"协助 LLM 完成的契约文档" = 契约标注族 + `structure/` 7 份
  卷面分组（schema_version 1）。承载复合题分组 / shared_material 归属 / canonical type /
  answer 出处，较纯内容真值更贴 V3 结构·语义重标（50 §4.2）。
- **迁移落地**：剔 2 份草稿，迁 15 份入 V3 `assets/annotations_src/`
  （real/3 + contract/5 + structure/7），V2 JSON 原样；配套 README + 资产清单 §3/§8 修正。
- **背景**：用户改判 golden 可迁（早前仅 PDF 本体不迁）；样本 PDF 仍用户自有不复制。
- **验证**：15 份落盘 ls 通过；README 与清单三处同步完成。
- **影响**：段 D/E fixture 与 50 §4 corpus 源料已就位（重标前不作直接预期）。

### 2026-09-05 19:34:46（迁移物对抗性审查修正）

- **背景**：按用户要求对 `assets/annotations_src/` 15 份迁移物做第一性原理 × V3SPEC
  对抗审查，检出 2 阻断/1 高/3 中/3 低。
- **关键发现**：① `physics_2026_chaoyang_contract_golden` 与被剔 draft 绑定同物理 PDF，
  其 q11 `answer_source=llm_fallback` + `answer_needs_manual`（LLM answer 入真值源=反模式
  评测层复发）；② human 版 `math_real_golden` 8/8 explanation 皆 llm_fallback（仅 answer
  人工）；③ README contract/ "最贵事实源"定位虚高（实为抽样示范，chemistry/chinese/
  dongcheng 干净）；④ exercise×2 PDF 断链 + 旧码 type；⑤ 大兴生物/朝阳英语/朝阳语文无
  human 真值（覆盖虚高）。
- **决策/影响**：physics_chaoyang_contract 移 `quarantine/`（禁作真值源，人工核对后出）；
  math_chaoyang_contract 标 superseded（answer 以 math_real_golden 权威）；建
  `MANIFEST.csv` 逐份指纹+来源分级；loader 纪律：llm/explanation 拒作真值；README v0.2。
- **验证**：MANIFEST 15 行 sha256 落盘；quarantine 移动确认；目录= real/3 + contract/4 +
  structure/7 + quarantine/1；JSON 本体零改动。

### 2026-09-05 19:43:36（V3 git 仓库建立 + 首次推送）

- **背景**：用户指示 V3 立**严格版本管理**，提供 GitHub private 空仓库
  `kurt-wong/AITutors-v3`，并补充本机访问 GitHub 走 `127.0.0.1:55219` 代理。
- **决策**：`git init -b main`；`.gitignore`（密钥/token 绝不入 git，保留 `.env.example`）+
  `.gitattributes`（统一 LF 防 CRLF 抖动）；本地身份 `kurt-wong /
  kurt-wong@users.noreply.github.com`（复用 V2，仅 local，未改 global）；根 `README.md`
  （文档地图 + Git 纪律）。
- **首提交 `88e7a29`**：123 文件 / 42035 行——spec 六册 + reference 契约文档 +
  `assets/annotations_src` 15 份源料 + docs_archive 归档 + 状态四件套；secret 预扫描 CLEAN。
- **推送**：`remote add origin` + `push -u origin main`，凭据经 `gh auth git-credential`
  （keyring）+ 本机代理；未写任何全局 git config。
- **验证**：本地/远端 HEAD 一致 `88e7a29`；`main` 已跟踪 `origin/main`。
- **影响**：V3 全程受控版本管理；此后文档/代码变更先 commit 再推送，密钥恒走 `.env`。

### 2026-09-05 20:31:32（40 §2 段 A 骨架完成）

- **背景**：按已批准计划实现段 A（config / DB 19 表 / Repository / canonical hashing）。
- **决策/实现**：`backend/` 骨架（pyproject / .env.example / alembic.ini / docker-compose
  仅 postgres / Dockerfile）；`app/`（core: config+hashing；db: base/session/mixins；
  models: A/B/C 三域 19 表；repositories: sealed/append-only/decision 唯一入口防护；
  main: /health）；Alembic baseline `0001`（19 表一次建齐，DDL 源 = Base.metadata）。
- **验证**：Gate A1（启动零外部副作用，导入路径仅 app/app.main）A2（19 表 exact、
  ORM==DB、7 组唯一性存在、link 无额外 UNIQUE）A3（sealed UPDATE→异常、append-only、
  decision_status 唯一入口）A4（hash 确定性/身份语义）A5（/health ok）**全 PASS**；
  26 tests、coverage 93%。
- **缺口登记**：BUG-V3-001..005（documents 域归类 / selection_events 列冻结缺失 /
  embedding 模型名 / replay 措辞 / 浮点 precision），不改冻结正文，均待 errata/终裁。
- **影响**：段 A 出口闸通过；按 A→C→B 序进入段 C（Gateway/audit/budget external 闸）。

### 2026-09-05 20:40:02（段 A 对抗性审查修正 R1–R3）

- **背景**：对段 A 完成内容做第一性 × V3SPEC 对抗复核，检出 1 阻断 + 2 中/高 + 4 低。
- **关键发现**：R1 `create_admission_candidate` 暴露 `decision_status` 参数，可被 future
  以 `approved` 越权创建（违反 30 §12/20 §8.2 唯一入口，段 G 地雷）；R2 多列可空性放宽
  （10 以显式 NULL 表可空、未标即 required：`prompt_version`/`model_config_hash`/
  `annotation_id`/`question_number(_range)`/`source_span`×2）；R3 `server_default=now()`
  为越权 default（段 A 计划明令禁止自行加 default）。
- **决策/修正**：Repository 创建候选**固定 `pending_review`**（不暴露 decision_status 参数）
  + 回归测试；6 处列收紧 NOT NULL；撤 6 列 server_default → python default（`_utcnow`）；
  migration `0002`。R4–R7（link 复合 PK、figure-links 以 PK 实现唯一、/health 不校验
  DATABASE_URL、浮点 nan 说明）作为实现说明记录，不改。
- **验证**：27 tests PASS、coverage 94%、模型↔DB 一致（0002 已应用）。
- **影响**：进段 C 前 schema 可空/默认与 10 冻结正文对齐；approve 唯一入口无旁路面。

### 2026-09-05 20:44:51（段 A 实证对抗审查）

- **背景**：按用户要求以**真实运行证据**复核段 A（不推测、不降标准）。
- **实证**：E1 审计 7 required 列实库全 NOT NULL；E2 nullable 列全 YES（审计清单曾误加
  `documents.processing_status`——实为 required，非缺陷）；E3 全库 `column_default` 残留
  = 无（0002 已撤净）；B1 raw UPDATE sealed version → rowcount 1、B2 raw UPDATE
  decision_status → rowcount 1（**DB 层无 trigger 强制**，sealed/decision 唯一入口当前
  仅 Repository/Service 应用层保证——如实记录，DB 级 enforcement 待 Spec 授权）。
- **缺口补测**：此前 `create_role_content`/`create_material`/`create_unit_group`/
  `create_semantic_annotation`/`create_admission_candidate(flush)`/`append_figure` 等
  create 方法**未曾在真实 DB 往返执行**（coverage 行证）；新增 DB 往返全链路测试
  （B→A→C 依赖链 flush）。初跑暴露测试自身 client-default 时序缺陷（id 于 flush 才赋值），
  修正后通过。
- **验证**：28 tests PASS、coverage **94% → 99%**（content/snapshot repository 100%，
  source 92%——余 3 行错误分支未覆盖）。
- **影响**：Repository create 面全部经真实 DB 验证；段 A 验收证据链完整。

### 2026-09-05 20:55:39（段 A 正式关闭）

- **决策**：用户宣布 40 §2 段 A 正式完成、A1–A5 全通过，关闭该阶段。
- **交付盘点**：段 A 五交付（config/密钥校验、DB+Alembic+19 表、Repository、canonical
  hashing、/health）+ Gate A1–A5 PASS + 28 tests / coverage 99% + E1–E3 实库核验 +
  B1/B2 边界记录 + BUG-V3-001..005 挂起。
- **下一步**：进入 40 §2 段 C——Gateway（disabled/mock/live）+ audit（不可变）+
  budget（五账户）+ 运行域 4 表（30 §6/§10/§11/§17）；cloud OCR external 同闸；
  A→C→B。段 C 为架构类实现，计划前遍阅 V3-Spec 段 C 约束。

### 2026-09-05 21:18:44（40 §2 段 C 骨架完成）

- **背景**：按已批准计划实现段 C（Gateway 三态 + audit + budget 五账户）。
- **决策/实现**：运行域 2 表（llm_call_audit 24 列 + budget 含 reserved 补列，migration
  `0003`）；`app/ai/`（gateway 三态 live 四前置、providers base/mock/http、live_guard、
  audit idempotency_key、budget 五账户原子）；`repositories/runtime_repository.py`
  （audit append-only + budget 条件 UPDATE）；`core/errors.py` 八分类。
- **验证**：Gate C1（disabled 抛错零外部）C2（audit 不可变）C3-A（同 scope 并发仅一成功）
  C3-B（五账户 rollback 无残留）C4（LE 跨 attempt 共享/正交）**全 PASS**；43 tests /
  coverage 93%（既有 28 不回归）。
- **缺口登记**：BUG-V3-006（budget reserved 补列）；audit 列类型/跨段 FK 时序/预算单位
  未冻结按自由度实现并记录。
- **影响**：external side-effect control plane 建立；段 C 出口闸通过；段 B 的 cloud OCR
  路径现在有合法放行闸（A→C→B 顺序成立）。

### 2026-09-05 21:40:39（段 C 实证对抗审查）

- **背景**：按用户要求以真实运行证据复核段 C（不推测、不降标准）。
- **真实缺陷发现**：连续两遍 pytest，**第一遍即 2 FAIL**（test_budget C3-A/C4）——上一轮
  43 passed 是残留为空的首跑；此前 committed 的 budget 行（固定 scope R1/HX）跨会话残留，
  使 budget 测试**不可重入且污染预算表**。修复：budget 测试每 run 用唯一 scope
  （uuid4 hex），连续两遍后 43 passed 稳定。
- **边界实证**：D1 disabled 加载不 import httpx（无 HTTP client）；D2 raw SQL UPDATE
  audit → rowcount 1（append-only 为 Repository 层 enforcement，DB 无 trigger，如实）；
  D3 budget UNIQUE(account_dim,scope_id,stage) NULLS NOT DISTINCT 真唯一（同
  (request,scope,NULL) 第二行 IntegrityError）；D4 le 同 hash 不同 stage 两行 OK。
- **说明**：budget raw SQL 须显式给 id/updated_at（DB 无 server_default——与段 A R3
  「撤 server default」一致，非缺陷）。取证脚本初版自身漏列报错已纠正，最终取证有效。
- **影响**：段 C 测试可重入、预算表不被污染；Gateway/audit/budget 骨架经真证据验证。

### 2026-09-05 21:52:36（40 §2 段 C 正式关闭）

- **背景**：段 C 实证对抗审查通过（真实缺陷修复 + D1–D4 边界实证），用户宣布段 C 正式关闭。
- **决策**：关闭段 C。依据 = Gate C1–C4 全 PASS + 连续两遍 pytest 43 passed（无未解决 FAIL）
  + 对抗证据记录（budget 可重入缺陷修复 `3a6628f`）。
- **影响**：A→C→B 序成立——段 B（Source Seal + OCR）现可启用 cloud OCR（PaddleOCR-VL），
  走段 C 已建的 external 闸（Gateway + audit + budget）。
- **下一步**：进入 40 §2 段 B 规划——Source Seal（documents/source_versions/source_lines/
  figures 密封）+ OCR 引擎接入；沿用既定验证模式（Frozen-Spec 计划 → 机器可判定 Exit Gate
  → 真实对抗测试 → 修复重复验证 → 关闭）。

### 2026-09-05 22:50:58（40 §2 段 B 骨架实现完成）

- **背景**：按已批准计划实现段 B（B 域 seal + line/figure 索引；OCR 双源接线）。
- **决策/实现**：独立 `OCRGateway`（三态 disabled/mock/live，live 四前置同 LLMGateway；
  `extract(file_bytes)` 协议）；`app/ai/ocr/`（result dataclass / providers
  Native·Cloud·Mock / gateway）；`app/domains/source/`（line_index 纯函数 + SealService
  幂等编排）；config/errors/`.env.example`/pyproject 扩展（OCR surface + pymupdf）。
- **架构边界（P0）**：SealService 只请求 OCR + 确定性编排（line index→hash→persist→seal），
  **不操作 audit/budget、不 import/不直调 CloudOCRProvider**；cloud 路径经 OCRGateway
  （mock 测试证实）。**实现细化（如实）**：OCRGateway 与 LLMGateway 同构保持骨架——live 四
  前置检查 + provider 唯一调用点；budget reserve→audit→settle 的 DB 写编排不在段 B 落地，
  因无 task（30 §6 live 前置含 task context，tasks 段 H 建）+ 30 §11 对 seal 预算账户映射
  未冻结 + 段 C audit 终态行语义未接 → 留段 H task 驱动统一接入，避免发明 reserve 语义。
- **验证**：Gate B1（幂等 1 doc+1 version）B2（确定性+DB unique）B3（sealed 禁 UPDATE +
  append-only）B4（DB rebuild+hash）B5（integrity 敏感）B6（五前置缺一拒+零副作用）B7
  （native 零 audit/budget）**全 PASS**；60 tests ×2 连续两遍（既有 43 不回归 + 新 17），
  coverage 92%；实证 E0–E3（sealed+stage、DB unique 列、raw UPDATE sealed rowcount 1=DB
  无 trigger 如实、dup line_ref IntegrityError）。
- **缺口登记**：BUG-V3-007（original_sha256 与 source_version 基数未冻结，段 B 保守按
  (stage,hash) LE 幂等，Gate B1 只断言明确部分）。
- **影响**：本地确定性 seal 可用（native）；cloud OCR 有合法放行结构（段 H task 后接全
  lifecycle + live smoke）；40 §2 序 A→C→B 三闸齐。下一步：段 D（Annotation stage）。
