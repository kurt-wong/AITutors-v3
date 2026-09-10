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

### 2026-09-05 23:07:10（段 B 实证对抗审查）

- **背景**：按用户要求对段 B 完成内容做第一性 × V3SPEC 实证对抗审查（不降标准、不自我
  合理化、不强解、不推测）。
- **对抗探针取证**：临时探针 11 项全 PASS——跨事务幂等（B1 原只测同事务，commit 后新事务
  同文件仍恰 1 version）；extract 失败→doc failed（seal except 分支实测工作）；hash 分层
  确定性（同文本不同 bytes → body/integrity 同、le 异）；build_ocr_gateway 三态/mock 无
  provider/markdown parse 均正常；integrity 可从 DB lines 复算一致（真覆盖）；native 行
  粒度观察（提取片段可碎为词级，词保序非丢字符，body 为提取 line 序列非视觉行还原——
  cloud OCR 段 F 处理）。
- **真实发现（登记）**：BUG-V3-008——cloud OCR（PaddleOCR-VL）落库 provider 值
  'paddleocr-vl' 不在 10 §4.2 provider 冻结枚举（native/ppsv3/docx）；OCR_PROVIDER_POLICY
  L1 双模型 vs 10 schema 只列 ppsv3，值域未冻结。段 B cloud 仅 mock 占位，待 errata。
- **边界记录**：seal 幂等跨事务成立但无 DB UNIQUE 兜底（并发同文件 seal 极端场景不保证，
  BUG-V3-007 延伸）；同文件双 role → document 复用 + 多 version（BUG-V3-007 设计允许）。
- **补强落地**：6 项正式补测并入（test_seal_dbflow 跨事务幂等/extract fail/integrity 复算；
  test_ocr_gateway build 三态/mock 无 provider/markdown parse）；临时探针删除。
- **验证**：66 tests ×2 连续两遍（既有 60 不回归 + 新 6），coverage 不变达标。
- **结论**：段 B 无未解决 FAIL、无结构缺陷；发现均为观察/边界 + 1 登记（BUG-V3-008）。

### 2026-09-05 23:20:46（40 §2 段 B 正式关闭）

- **决策**：用户宣布 40 §2 段 B 正式完成、B1–B7 + 对抗探针全通过，关闭该阶段。
- **交付盘点**：B 五交付（config/errors/OCR 网关+provider/seal domain service/测试）+
  Gate B1–B7 PASS + 对抗探针 11 项 PASS + 6 项转正式回归（66 tests ×2）+ 真实 DB 边界
  验证（E0–E3 + T1 跨事务）+ coverage 达标 + 无 unresolved FAIL。
- **延续 Bug**：BUG-V3-007（source_version 基数）+ BUG-V3-008（cloud OCR provider 值域）
  Open deferred——B 不自行改 Frozen Spec，Errata 统一。
- **下一步**：进入 40 §2 段 D（Annotation stage）。段 D 第一原则继续沿用 A/B/C 经验：
  先读 Frozen Spec、明确 D 对象与 Entry/Exit Gate、再实施，不因 B 留下 bug 反向改 B。

### 2026-09-06 00:41:47（40 §2 段 D 骨架实现完成）

- **背景**：按已批准计划实现段 D（Annotation stage：forbidden-field 校验 + 幂等 + supersede）。
- **决策/实现**：`app/domains/annotation/`（validator 纯函数 + service AnnotationService）；
  `snapshot_repository` 扩展（prompt_version/model_config_hash 收紧 required +
  find_annotation_by_le_hash + set_annotation_status valid→superseded）；
  `test_annotation.py`（D1 validator + D4 golden fixture）+ `test_annotation_dbflow.py`
  （D2 幂等+supersede + D3 persistence boundary 真 DB roundtrip）。
- **D0 Contract Audit PASS**：核对 C LLMGateway.complete(prompt)->str、A hashing helper、
  A semantic_annotations 列定义——无 spec/实现冲突。
- **验证**：Gate D1（forbidden-field validator 正确性，深嵌套路径完整）D2（LE 幂等+显式
  supersede，create 不自动修改旧行）D3（valid 落库无禁字段；invalid schema 落库 status=invalid
  + payload 保留 + raise；json.loads 失败落库 parse_error + raise——两者同时发生）D4（正/反
  fixture golden 回归种子）**全 PASS**；79 tests ×2 连续两遍；coverage 93%；DB 边界 E0–E3
  （annotation insert / raw UPDATE rowcount 1=DB 无 trigger 如实 / UNIQUE(stage,hash)
  IntegrityError / validator forbidden detected）。
- **关键纪律**：validator 只做 20 §4.3 递归禁字段检查（P1-a：不自行升级 JSON Schema）；
  supersede 显式（P2-a：create 不自动修改旧行）；mock fixture 不进 LE hash（P2-b）；
  `created_at DESC` 是 BUG-V3-009 实现选择非 Frozen Contract。
- **影响**：annotation 可合法写入（mock）；schema 校验拦截禁字段；(stage,hash) 幂等 + 显式
  supersede；段 D 到 semantic_annotations 为止（Resolver/Compiler/Gate 未碰）。
- **下一步**：段 D 是否关闭由用户裁决；若关闭进入 40 §2 段 E（Source Resolver）。

### 2026-09-06 07:26:21（段 D 对抗审查纠偏 + Exit Gate 恢复）

- **背景**：对 A/B/C/D 交付物做第一性 × V3SPEC 对抗审查，要求每结论带真实测试证据。
- **真实缺陷（FAIL-1）**：`test_d2_cross_transaction_idempotency` 调用 `session.commit()`
  （使 conftest rollback fixture 失效）后，finally cleanup 只删 `semantic_annotations`，
  documents / source_versions / source_lines 残留 → 后续 B seal 测试 `n_docs == 1` 断言
  失败（3 failed / 78 passed）。根因是 cross-tx 测试隔离不彻底，**非 Annotation 业务失败**
  （D2 幂等/DB UNIQUE 本身经 T5 等实证正确）。
- **修复**：cleanup 改按 FK 序删净——反查 document_id → 删 source_lines → versions →
  documents（注释标注 FAIL-1 修复）。**生产代码零改动**。
- **验证**：清库 → pytest #1 **81 passed**；无中间清理 pytest #2 **81 passed**；
  DB 复查 docs=0 / vers=0 / anns=0。commit `fd9919a`。
- **纠偏（FAIL-2）**：原报「sealed 无 DB trigger = FAIL」，经 10 §4.2 原文核对撤销——
  Spec 逐字指定「status=sealed 后禁止任何 UPDATE（**Repository 抛错**）」，实现
  `SealedVersionError` 即合规；DB 层不自行加 trigger/RLS（个人规模非"数据库安全系统"）。
- **纠偏（FAIL-3）**：原报「三处 UNIQUE 缺失 = FAIL」逐项核对撤销——semantic_annotations
  / admission_candidates 的 (stage,hash) UNIQUE **实已存在**（10 §5.1/§5.2 明确「唯一」）；
  documents.original_sha256 为身份规则非 DB 约束（10 §4.1 未声明 UNIQUE）；
  audit idempotency_key 作用域 30 §10 定义为「同一 LE+attempt 内」+ 30 自登记 LOW 开放
  （line 480），加全局 UNIQUE 反可能错误；document_source_versions 幂等唯一性
  归 **BUG-V3-007 errata**（role 多版本语义未决，不自行冻结）。
- **裁决**：用户确认 FAIL-1 修复有效、FAIL-2/3 撤销、段 D **COMPLETE / CLOSED**。
  BUG-V3-001..010 保持 Open / deferred。
- **下一步**：进入 40 §2 段 E（Source Resolver）。待办不变：T/F↔A/B 映射段 G 前补。

### 2026-09-06 09:09:16（段 E 实现 + 对抗 Correction Cycle + 关闭）

- **背景**：按已批准计划实现段 E（Source Resolver，20 §5）。用户裁决全量 7 role + 合成
  fixture；实现第一步执行 E0 Contract Audit。
- **实现**：`app/domains/resolver/`（span frozen dataclass / reference 只提声明字段 /
  match_normalization §5.2 / resolver 7 独立 policy + 级联 + fuzzy 终点不变量 +
  ResolvedRun 四象限）；`source_repository` 新增 get_lines_by_version(seq)/
  get_figures_by_version(figure_id)；tests test_resolver(33)+test_resolver_dbflow(3)。
  E0 登记 BUG-V3-012（跨行 text_hash 拼接未冻结）。
- **对抗审查检出 4 FAIL**（真实探针证据）：
  - FAIL-1（P0）`startswith(qn)` 前缀错配 → qn=1 误吞 10/11/12 的 answer/explanation
    行 = 真实 false-resolved（违反「宁可 unresolved 不能错误 resolved」）；
  - FAIL-2 contextual 无 emit path（仅 docstring/常量，测试把 contextual 场景当
    ambiguous = 测试配合实现弱化）；
  - FAIL-3 material span 与子题 stem/option 重叠仍 resolve（E-owned overlap 缺失）；
  - FAIL-4 inline 同行多选项/多题答案不支持（line_character 契约未完整实现）。
- **Correction Cycle（用户授权修复 1-4；CONCERN-1 仅登记不扩 normalization）**：
  - FAIL-1 改 bounded `_ENTRY_RE`（题号 token+分隔）+ `is_question_start==qn` token
    等值，1-vs-10/11/12 消除；固化为 `test_prefix_collision_*` 回归；
  - FAIL-2 补 `_resolve_marker_cascade`：ambiguous 时用确定性题目区边界排除 → contextual，
    evidence 记排除步骤，验证 `initial>1→final==1`、exact 唯一≠contextual；
  - FAIL-3 补 `_enforce_material_overlap`：material 与子题/其他 material 共享行 → demote
    incomplete unresolved（E owns source-span overlap；IR composition 仍属 F）；
  - FAIL-4 option/answer 支持 `line_character`（有界 label/entry，单行多选项、同行多题
    答案各得 offsets，禁 first/nearest）。
- **验证**：段 E 测试 33 passed；完整 pytest **114 passed ×2**（无中间清理，可重入）；
  prefix-collision / contextual invariant / material overlap / inline 均有回归；未引入
  F/G/H 能力、未改 Frozen Spec、未回改已关闭段。
- **登记**：BUG-V3-011（B seal 未接 figures）/ 013（blank/image JSON 形态未冻结）补登记。
- **裁决**：用户批准段 E **COMPLETE / CLOSED**；进入 40 §2 段 F（F0 Contract Audit）。
- **下一步**：段 F——IR 装配 + ready 判定 + Deterministic Compiler + dedup/occurrence
  （20 §6/§7），不得把 IR 逻辑塞回 E。待办不变：T/F↔A/B 映射段 G 前补。

### 2026-09-06 10:59:39

- **段 F 三轮对抗审查 → 用户裁决 COMPLETE / CLOSED**。
- **实现**：compile 包（IR dataclass + IRBuilder + validate_ir 不变量 1-8 /
  identity_normalization 与 match_normalization 物理分离 / Compiler 三 key + raw 2c/2d /
  snapshot）；canonical 12 种直通 + 未知→incomplete（BUG-V3-014 不猜别名）；LaTeX 只环境
  内折叠（BUG-V3-015 符号等价延后）；unit_id 禁 UUID/random 生成；material 单次输出不复制
  进子题 stem；input immutable。
- **Correction Cycle（F1/F2/F3，用户授权）**：
  - F1 缺 answer 曾 ready + leaf；改 validator 强制 content_roles answer=required →
    incomplete + leaves=0（回归 test_answer_required_missing_incomplete）；
  - F2 material dependency 曾「声明即可 ready」；改 target 须在 shared_components 且
    span resolved 才 ready（回归 test_material_dependency_unresolved_composite_incomplete）；
  - F3 image/blank 曾静默丢弃产 ready 无图引用；改 unsupported content role →
    IRContent.unsupported → validator 判 incomplete fail-loud（回归
    test_declared_image_fail_loud_incomplete）；figure_refs 延后 BUG-V3-020，blank 闭合
    延后 invariant 4——含 blank 的 fill_in 诚实走 incomplete，非误 ready。
- **审查（第三轮对抗确认）**：真探针证明 F1/F2/F3 消除、blank fail-loud 正确、
  material.text 纯正文（marker 间排他切片）、composite 三 key 确定性、F/G boundary
  import 扫描 clean（compile 无 gate/repositories/admission/runtime/decision 实际 import）；
  未发现新 FAIL。
- **验证**：段 F 测试 19 passed；完整 pytest **133 passed ×2**（无中间清理，可重入）；
  负向矩阵 / 确定性 / input immutable / canonical 直通 / raw 2c-2d 均不回归。
- **登记**：BUG-V3-014..018（F0 audit）前 commit；019（options serialization order）/
  020（image/unsupported fail-loud）本轮补登记；010 误插完全重复条目移除（保留一份历史）。
- **裁决**：用户批准段 F **COMPLETE / CLOSED**；进入 40 §2 段 G（F0 Contract Audit）。
- **下一步**：段 G——Gate Policy + Candidate + decision_status + approve()/Admission tx +
  Allowed-Answer Grammar（20 §8）。G0 必核：F incomplete 不得被 G 强行转 Candidate；
  DISPLAY_CONTRACT T/F↔A/B canonical 映射须先补（否则 true_false 只走 pending_review）。
  G 完成自身 Contract Audit 前不得正式实现。

### 2026-09-06 13:55:25（段 G 实现 + 对抗审查 Correction Cycle）

- **背景/裁决**：段 G G0 Contract Audit **PASS → 用户授权实现**（scope 固定：grammar /
  policy / payload / ContentRepository 查重 / admission / service / G tests / 状态机探针 /
  对抗审查 / pytest ×2）；明确排除 worker/LLM live/H/后续 knowledge resolver 等（不实现）。
- **实现**：`app/domains/gate/`（grammar strict-auto 必要不充分、policy 四层 gate_decision、
  payload 冻结可重放快照、AdmissionService approve/reject + 物化事务、GateService 编排 +
  LE 幂等落 candidate）；`snapshot_repository`（_transition_decision 受控唯一迁移 +
  find_candidate_by_le_hash/lock/append_review_trail/admission_event）；
  `content_repository`（dedup 查重/复用面）；三段证据链分离（gate_decision 机器冻结 |
  decision_status 生命周期唯一入口 | review_trail 人工 append）。
- **对抗审查 Correction Cycle（检出 4 项均修复 + 回归）**：
  - HIGH：materialize 复用 occurrence 时无条件重插 role_contents/answer/link/member →
    UNIQUE 冲突（同 sv 二次标注整事务回滚）。重构：plan→Question dedup REUSE→occurrence
    复用判定→全复用短回路（不建空 group）→material 按 (sv, dedup) 复用→仅新 instance 建
    行 + member_index 计数器。
  - MED：非 stem role 的 source_span.line_refs 误记 stem 行（provenance 错位）→ 逐 role
    用自身 compiled line_refs。
  - MED：gate_decision=rejected 无自动迁移 → pending_review 僵尸（人工又被 P0-G-002 堵死）。
    service.run 对 machine rejected 调 reject(source=machine_gate) 立即终态（10 §5.2
    确定性 Gate Policy 写 decision_status）。
  - MED：admission._dedup_key 选项缺外层 normalize_identity，与 Compiler._question_dedup_key
    分叉（选项正文以数字开头时同题两 Question）→ 对齐并加数学一致性测试。
- **验证**：段 G 测试 66 passed（含 4 项新回归：同 sv 二次标注幂等复用、option source_span
  自身行、machine-rejected 自动终态、dedup 键与 Compiler 一致）；完整 pytest
  **199 passed ×2**（无中间清理，可重入）；P0-G-001/002/003 + 监控项（approve 只消费冻结
  snapshot、绝不重跑 E/F/G）探针全绿；未改 Frozen Spec、未回改已关闭段。
- **登记**：BUG-V3-021..027 已登记 bugs.md（021/022/025 等按 M1 处理，标注不冒充 Frozen）；
  G 对抗 4 项为**已修复的实现 bug**，非 spec 域 Open BUG，不入 bugs.md 新编号。
- **裁决**：段 G **COMPLETE / CLOSED**（用户流程 ⑩⑪ 完成）。
- **下一步**：段 H 及 worker/tasks、LLM live、knowledge resolver 等均属用户排除范围，
  **待用户新指令**；待办不变：BUG-V3-001..027 errata 终裁。

### 2026-09-06 15:10:52（段 G 二轮对抗审查 → F1/F2 修复收尾）

- **背景/裁决**：用户对二轮对抗审查 findings（F1/F2）批准**最小修复 + 各转正一条跨提交
  回归**；范围限定：不改 Frozen Spec、不新增 BUG 编号、不动状态机/dedup/UNIQUE、
  不重构 _materialize、_audit 探针不入常规收集。
- **F1（10 §6.5 A 域值域）**：admission 物化 create_unit_group 原取 payload IR root 的
  `unit_type`（standalone_question），把 IR 域漏入展示/持久化域；改从 `candidate.unit_type`
  （service 已把 IR 值经 _candidate_unit_type 映射到 standalone_unit/composite_unit）——
  Admission 消费 G→A 冻结边界的 candidate，不回头解释 IR 值。
- **F2（10 §6.2/§3 provenance 写路径）**：create_instance 原不带 LE provenance → DB 落
  NULL；ContentRepository.create_instance 增 logical_execution_stage/hash/attempt_id 形参
  （默认 None，兼容既有调用），物化从 candidate 原样 copy（attempt_id 段 H worker 接入前
  candidate 恒 NULL → 如实继承，不伪造执行身份）。
- **转正回归**：test_admission.py 新增两条**显式 commit + 新 session reload** 测试
  （test_materialized_unit_group_unit_type_is_candidate_a_domain /
  test_materialized_instance_inherits_candidate_le_provenance），断言持久值而非 ORM 内存
  对象；新增 _purge_materialized（FK 序删净，含 sv instance 反查新建 Question），连续两遍
  全量无中间清理证实无泄漏。
- **验证**：test_admission.py 11 passed；_audit_g2 GA1–GA6 全 PASS（GA4/GA5 由 FAIL 转
  PASS）；完整 pytest **201 passed ×2**（无中间清理，可重入）。
- **登记**：F1/F2 为已修复实现 bug（同段 G 对抗 4 项惯例，不入 bugs.md 新编号）；BUG-V3-
  021..027 保持 Open 不变。
- **裁决**：用户批准 F1/F2 关闭 + 段 G 记录为 **IMPLEMENTATION COMPLETE / VERIFIED**；
  commit 8a57a92 已 push（origin/main 同步，工作树仅剩 2 个 untracked 审计探针）。
- **下一步**：段 H 及后续未授权，待用户新指令；待办不变：BUG-V3-001..027 errata 终裁。

### 2026-09-06 15:14:30（A–G Baseline Freeze 裁决）

- **裁决**：用户将 commit `8a57a92` 定为 **V3 Core Pipeline Baseline A–G 稳定基线**
  （Implementation Complete and Verified）；F1/F2 Correction Cycle 关闭；BUG-V3-001..027
  维持 Open（留 SPEC PATCH / NEXT BASELINE，不集中清）。
- **下一步顺序（用户指定）**：H0 Runtime Readiness Audit（audit only，零生产代码；检查
  stage/execution 身份贯穿 · Retry/Replay/New/Duplicate 语义与现有幂等对齐 · LLM Live 不
  绕过 Gateway/audit/budget · Task 状态机与业务状态机维度分离 + crash 窗口）→ H Contract
  Audit → H Implementation。H0/H 未授权不擅动工。

### 2026-09-06 20:34:06（H0 Audit → H Contract Audit → H Implementation Plan Final）

- **H0 Runtime Readiness Audit**（只读，零生产代码）落盘 `Docs/reference/H0_RUNTIME_READINESS_AUDIT.md`
  （v0.1，baseline 8a57a92/8f10930；commit 8032af3）。Findings H0-1..15：R1 五项（H0-3
  attempt_id 缺失 / H0-6 find→insert 非原子 / H0-7 retry 熔断未实现 / H0-9/10 Gateway 非执行
  边界无 audit·budget / H0-12 tasks·task_claims 未建）+ R2 两项（H0-2 compile 指纹 8 项 vs
  §16 四字段 / H0-15 invalid annotation 归属）+ Carry-Forward Constraints ×10。总判：A–G =
  Runtime-ready foundation，非 Runtime 本身 ready。
- **H Contract Audit 交付**：H0-16..20（Question Identity / Occurrence / Similarity）按用户
  终版基线吸收——H0-16/17/18 为 Frozen 已覆盖（10 §6.1/6.2 去重=复用 canonical + 新建
  Instance + `UNIQUE(question_id,source_version_id,occurrence_key)`），重申+回归而非新增 schema；
  H0-19/20 为未来独立层（occurrence analytics / similarity），H 不实现。Contract
  Reconciliation 表 H0-1..20 全列。
- **H Contract Reconciliation 五条最终裁决（用户）**：① H0-2 维持 M1（不动 hash）；② H0-15
  方案 B（只存 valid 产物）；③ H0-3 attempt 由 Task Executor 分配；④ H0-6 并发幂等写 ON
  CONFLICT；⑤ H0-7 LE→Attempt→bounded retry，claim_round≠attempt_id。
- **H Implementation Plan Final 冻结**：`~/.claude/plans/giggly-enchanting-volcano.md`，经
  用户多轮裁决收敛，锁入：
  - **6 Locks**：Lock-1 TaskClaim 字段一致性（worker_id/lease_token 仅进 lease_snapshot 不进
    顶层列）/ Lock-2 Attempt 不可恢复续跑 / Lock-3 Domain 不依赖 Gateway / Lock-4
    MAX_LLM_CALLS_PER_TASK 按真实 Provider Invocation 计数 / Lock-5 Runtime/Business Identity
    隔离 / Lock-6 reserve+audit STARTED 同事务边界（失败补偿）。
  - **4 Notes**：Note-1 熔断计数点在 Provider Invocation Port / Note-2 Attempt:Audit=1:N /
    Note-3 Resolve 非独立 Runtime Recovery Unit（禁新增持久化模型）/ Note-4 migration 0004
    限定 tables=[Task,TaskClaim]。
  - **3 Clarifications**：Clar-1 四层执行单位 LE→Attempt→Logical LLM Request→Provider
    Invocation（idempotency_key 归 Logical Request）/ Clar-2 熔断 consume() 原子化前置 /
    Clar-3 UNKNOWN 不自动→Failed/Retry，Artifact Readiness 先行。
  - **严格 Step 1–7**：Schema→Task 状态机→Audit→LLMExecutor→Domain 依赖倒置→attempt+幂等→
    TaskExecutor。
- **红线固化**：不改 compile hash / 不改 Question Identity / 不加 global Question dedup UNIQUE
  （BUG-V3-027 保持 Open）/ Worker 不直写 decision_status / Similarity 不进 H / Duplicate 不
  discard。
- **下一步**：H 段编码 Step 1（Runtime Schema：tasks/task_claims + migration 0004 + schema
  guard）。

### 2026-09-06 23:39:54（H Step 1 实现 + 第一性原理对抗审查 + Remediation）

- **H Step 1 实现（Runtime Schema）**：models/runtime.py +Task/TaskClaim（30 §17 + §5 lease，
  14/8 列）、models 导出、`alembic/versions/20260906_0004_tasks.py`（Note-4 tables 限定）、
  test_models_schema._RUNTIME 扩容、test_task_schema（schema guard）。alembic 往返 + 全量
  207 passed ×2。
- **对抗审查（用户要求第一性原理 + 真证据）**：空库逐步迁移实证（tests/_audit_h1_migration.py，
  scratch 库）发现 F-1——0001/0003 全量 `Base.metadata.create_all`（以**当前** models 为快照）
  使空库 replay 时 tasks/task_claims（及 budget/llm_call_audit）在 **0001** 即被建出，0004
  no-op；「0004 建这两表」只在 A–G 时代增量库成立。F-2：schema guard 只锁列名，不锁
  nullable/type/PK。F-3：无 from-empty / before-after 差分测试。
- **用户裁决**：F-1 选 **B**（登记 BUG-V3-028，不修改 0001/0003/0004、不重开 A–G、8a57a92
  基线不动；不引入 migration checksum/ownership registry）；F-2 采纳；F-3 采纳且按 B 语义
  重定义（from-empty 不断言「0004 必须 +2」，incremental 保留「pre-0004 → 0004 +2」）。
- **Remediation（Step 1 收口）**：test_task_schema 强化为结构契约（information_schema SQL
  type/nullable + PK + FK + Lock-1 + ORM nullable/类型契约）；新增 `test_migration_replay.py`
  两层回归（层 1 from-empty 空库 `upgrade head` 终态表集 == ORM metadata + alembic_version
  且两表结构 == TASKS_SPEC/TASK_CLAIMS_SPEC；层 2 增量库 `downgrade 0003 → upgrade head`
  delta == {tasks, task_claims}）。0004 docstring 与 plan Note-4 措辞改 B 语义；bugs.md 登记
  BUG-V3-028（Open/deferred，Owner = A–G migration history）。
- **验证**：全量 pytest **212 passed ×2**（无中间清理，可重入；增量库 head 无残留）。BUG-V3-001..028
  均 Open 不变。
- **下一步**：按 plan 严格 Step 顺序进入 **Step 2 Task State Machine**（Phase 2：TaskRepository /
  TaskClaimRepository + TaskService——原子 claim 同事务写 claim 证据 + lease/zombie +
  recover/retry）。

### 2026-09-07 00:04（H Step 2 实现 + 第一性原理对抗审查 F-2/F-1 + 最小修复收口）

- **H Step 2 实现（Task State Machine）**：`runtime_repository.py` +TaskRepository/
  TaskClaimRepository——claim 用单条条件 `UPDATE … RETURNING` 从 queued→running +
  claim_round+1（禁 SELECT→判断→UPDATE）；heartbeat/complete/fail 四元组条件写（zombie 拒，
  terminal 释放 lease 字段）；retry 仅 failed/interrupted；recover 失效租约→interrupted
  （不等价重跑）+ dry-run；task_claims append-only（update_claim → AppendOnlyViolation）。
  `app/domains/task/` TaskService：唯一入口，**不 commit**（调用方持事务，claim 的 tasks 更新
  与 task_claims 证据原子同事务），Lock-1 snapshot 只进 JSONB。`tests/test_task_service.py`
  13 测试（生命全程 / 禁迁移 / claim 原子 / zombie / recover / append-only / 值域）。225 passed。
- **对抗审查（用户要求第一性原理 + 真证据）**：真 DB 探针 `tests/_audit_h2_task.py` 实证——
  **F-2（CONFIRMED，最高）**：heartbeat 只更 heartbeat_at 不滑动 lease_expires_at
  （P1：lease 完全不变、仅 hb 前进）；recover 只看 lease 不看 liveness（P2：lease=-60 已过期但
  刚心跳的任务仍被 recover 置 interrupted）→ 持续健康心跳但运行超初始租约（默认 60s）的长任务
  会被误中断。**F-1（CONFIRMED，覆盖缺口）**：无真并发 claim 永久回归（P3 实证实现正确：两
  session gather → 恰一胜 claim_round=1 + 单证据行 + running）。
- **用户裁决（不改 Frozen Spec，最小修复）**：F-2 采纳——heartbeat = **滑动续租**（liveness
  renewal，**非 reclaim/recovery**）：`SET heartbeat_at=now(), lease_expires_at=now()+
  make_interval(secs=>:lease) WHERE id/worker_id/lease_token/status='running'
  AND lease_expires_at>now()`——DB now() 单源，应用层不回写旧 lease；已过期 claim 的 heartbeat
  拒（LeaseConflict）→ recover 接管，绝不靠心跳抢救失效 claim。记录为实现/状态机语义缺陷
  （非 Spec 变更）；default lease 60s 维持（不放大掩盖）。F-1 采纳——P3 真并发转正。
- **修复与回归（13→17）**：repo/service heartbeat 增 `lease_seconds` 透传 + 续租 + 过期拒。
  新增 4 测试——F2-1 `test_heartbeat_slides_lease_expiry`（跨 commit 断言 lease 严格后移，
  因 PG now()=事务开始时刻，claim 与 heartbeat 须分事务）；F2-2 `test_continuous_heartbeat_
  survives_initial_lease`（lease=2s、每 ~0.8s 心跳 ×3 穿过原 lease 边界 → recover 不中断）；
  F2-3 `test_expired_claim_heartbeat_refused_then_recovered`（停止心跳 1.5s>1s lease →
  heartbeat LeaseConflict + recover interrupted）；F-1 `test_concurrent_claim_exactly_one_winner`
  （两独立 session `asyncio.gather` → 恰一 win/一 lose + claim_round=1 + 恰一证据行 +
  status=running）。
- **验证**：全量 pytest **229 passed ×2**（无中间清理，可重入）。探针 P1 lease 严格后移 /
  P2 心跳任务不被 recover（running）/ P3 过期拒 + 停止可回收（interrupted）/ P4 并发恰一胜
  单证据，全通过。BUG-V3-001..028 Open 不变。
- **下一步**：commit Step 2（独立提交点，含 Status.md/log.md/restart-prompt v1.6 收口）→ plan
  Step 3（Audit Lifecycle / Phase 3：`finalize_audit` exactly-once terminalization）。

### 2026-09-07 00:36（H Step 3 实现 + Baseline 对抗审查 + F-1 采纳 + F-2 分层）

- **Baseline 对抗审查（只读）**：llm_call_audit 现状 = create_audit(started) + update_audit 抛
  AppendOnlyViolation，无 terminal 路径；status 无 DB CHECK、idempotency_key 无唯一约束；无生产
  调用方。**两不变量分离**——A「不重复写 terminal audit」=finalize 条件 UPDATE；B「不重复执行/不
  重复建账」=request_id 复用+attempt+(stage,hash) ON CONFLICT，**finalize no-op 不等于整体
  exactly-once**（你警示的核心）。
- **裁决**：F-1 采纳（缺行 raise，缺行≠已终态 no-op，不被 0 行掩盖）；F-2 分层采纳（Phase 3 供
  STARTED→UNKNOWN primitive；「何时判 orphan」归 Phase 4，绑 task lease/worker liveness，禁按 audit
  年龄判死——防重蹈 Step 2 F-2）；F-2b 归 Phase 4；F-3/F-4 carry-forward → Phase 4/5。
- **实现**：`LlmCallAuditRepository.finalize_audit` 四态判定（缺行→AuditNotFoundError / started→
  `UPDATE … WHERE request_id=:id AND status='started' RETURNING status` 恰一迁移 / 已终态→no-op 返
  回既有终态不改写 / 并发败者 0 行→reread 确认 terminal）。`AUDIT_TERMINAL_STATUSES` 值域门；
  `update_audit` 仍抛；`"end"` 保留字引号（踩坑修正）；end 缺省 COALESCE now()（DB 单源）。零越界
  （无 reconciliation/task lease/executor/budget/attempt/schema 扩展）。
- **验证**：test_audit.py 3→8（+5：三向终态化 / 二次 no-op 不改写 end·usage / 缺行 raise / 非法
  status raise / 双 session 并发 completed-vs-failed 恰一迁移 + DB 终态=胜者请求态）。全量 pytest
  **234 passed ×2** 可重入。
- **下一步**：commit Step 3（独立基线）→ plan **Step 4 LLMExecutor 唯一执行入口**（Phase 4）——
  先 Baseline/对抗审查：① 真单入口（禁 Domain→Gateway/Provider 旁路）；② mock/disabled/live 同
  径；③ retry 计数点 = Provider Invocation Port（Lock-4/Note-1）；④ reserve→audit STARTED→
  invocation→terminal→settle 接线（Lock-6）+ ⑤ Attempt·LE 分离；F-3 request identity 由真实请求
  模型定夺（不预加 request_seq）。

### 2026-09-07 13:21（H Step 4 LLMExecutor 实现 + 三路独立对抗审查无 P0 + P1/P2 修复）

- **交付**：`app/ai/executor.py` LLMExecutor 唯一执行入口（mock/disabled/live 同 complete() 入口）
  + ProviderInvocationCounter。live 生命周期 = Phase A ensure 五账户+reserve+audit STARTED 同事务
  （Lock-6）→ Phase B bounded retry（每轮 gateway.complete(task_id, invocation_counter)，provider
  seam 前 `counter.consume(task_id)` 原子计数，Lock-4/Note-1）→ Phase C finalize(completed)+settle
  (actual=reserve) 或 finalize(failed)+settle(actual=0)→re-raise。`errors.py` +BudgetSettlementError
  /CircuitOpen/LLMProviderError/LLMNetworkError。`gateway.py` provider seam。`models/runtime.py`
  tasks.llm_invocations + migration 0005（双路径安全）。test_executor 10 + test_budget G1–G3 转正。
- **用户裁决落实**：F-5 部分采纳（reclaim 不绑 Task Lease，仅 crash/orphan fallback；孤儿
  reconciliation F-5B 延后登记）；F-6 BudgetSettlementError 语义化；F-7 G1–G5 随 Phase 4 交付；
  F-3 不加 request_seq（M1 每 attempt=1 Logical Request）；四数量级分锁（Attempt=1/Request=1/
  Audit=1/Invocations=N，MAX_LLM_CALLS 按真实 N 累计）；counter 在 provider seam（consume →
  provider.complete，非 executor.complete +=1）；Lock-6 reserve+audit 同事务。
- **三路独立对抗审查（sonnet ×3 只读，冻结 diff，R1–R12）**：A（R1/R2/R8）唯一入口无旁路
  （annotation Domain→Gateway 直连 = 已知 Phase 5 carry-forward，Lock-3 收口）、Gateway 职责无
  回归、request_id/attempt_id/idempotency_key 身份一致；B（R3–R7/R9）consume seam 唯一、Lock-6
  全异常路径覆盖、Phase A/B/C commit 边界无半状态、retry taxonomy 仅 transient、计数无过计误导；
  C（R10–R12）settle 失败显式暴露不掩盖 provider 成功不重调 provider、reclaim 仅 fallback 路径。
  **三审均无 P0**。
- **修复**：C-1（P1）ORM `llm_invocations` `server_default=text("0")` 对齐 0005 `DEFAULT 0`
  （消除 from-empty/增量 `column_default` 漂移）+ 双路径 default 锁定（test_task_schema 主库 +
  test_migration_replay from-empty 断言 '0'）+ 0005 docstring 改准双路径语义。B-1（P2）gateway
  `_live` 缺 counter/task_id 改 fail-closed（Lock-4 熔断不可绕过），test_gateway allowed 用例带
  fake counter + 2 新增 denied。
- **deferred 登记**：D1 crash-orphan reconciliation = F-5B（Phase 8 recover）；D2 provider exception
  translation = Phase 9 接线；D3 reclaim 不绑 lease 仅 fallback（F-5A）；A-2 finalize 不落 token/cost
  + idempotency_key 无 DB UNIQUE = F-4/D2 carry-forward。
- **验证**：定向 runtime ×2（53 passed）；全量 pytest **250 passed ×2**（净 +3：2 gateway
  fail-closed + 1 schema default 断言，可重入）；migration 双路径（from-empty→head + incremental
  rebuild）llm_invocations column_default 均 '0'；git diff --check 干净。
- **下一步**：commit Step 4（独立基线）→ plan **Step 5**（attempt_id 贯通 + AnnotationService 依赖
  倒置 Lock-3，删除 annotation Domain→Gateway 旁路）+ Phase 6 并发幂等写。Phase 8 起接 TaskExecutor。

### 2026-09-07 14:05（H Step 5 attempt_id 贯通 + Lock-3 依赖倒置 + Phase 6 并发幂等写；审查无 P0/P1）

- **交付**（plan 第 5/6 项合并为一次 Step；Phase 7 方案 B / Phase 8 TaskExecutor 明确不包含）：
  - **Lock-3 依赖倒置**：`AnnotationService.__init__(session, llm_executor: LLMExecutor)`，删除
    annotation Domain→Gateway 直连旁路（app/domains + app/repositories 扫描确认零 gateway 导入；
    Domain 唯一 `complete` 调 executor）。test_annotation_dbflow 全部经 `_svc` =
    `AnnotationService(session, LLMExecutor(session, gw))` 注入。
  - **attempt_id 贯通（Lock-5，仅 Artifact Runtime Provenance，不进 LE hash / business identity /
    dedup / occurrence）**：`annotate()` 3 处 create + `GateService.run` → create_admission_candidate
    全透传；reviewer 复核 admission `_dedup_key`/`_occurrence_key` 仅由 payload 身份重算、无 attempt。
    `executor.complete` 身份参数（attempt_id/task_id/document_id/provider/model）放宽默认 None
    （mock/disabled 忽略）；`_complete_live` 补 task_id/document_id/provider/model 任一缺失
    fail-closed raise（live 仍不会无身份放行）。
  - **Phase 6 并发幂等写（H0-6）**：snapshot_repository 两 create 改 `pg_insert … ON CONFLICT DO
    NOTHING` 锚 `UNIQUE(logical_execution_stage, logical_execution_hash)` + `.returning`；插入成功 →
    新行；冲突 → 任意-status re-read（新 helper `_annotation_by_le`）：valid/superseded → 幂等返回
    既有；invalid 残留（find 不复用）阻挡 valid 写 → `RepositoryError`（原 IntegrityError 语义显式
    化）；candidate 冲突 → `find_candidate_by_le_hash` re-read 返回既有（恒 pending_review）。
    FK / NOT NULL 其它约束冲突不被 DO NOTHING 吞（唯一冲突锚点单一）。
  - **测试适配**：`test_repositories.test_candidate_created_pending_review` 改先建真实 source_version
    + annotation 父行再建 candidate（Phase 6 create 立即落库 pg_insert，不再惰性 ORM add，须满足 FK）。
  - **新增回归**：`test_h_step5_attempt_provenance.py` 5 测试——attempt A 落库 + 同输入 attempt B
    复用既有行（provenance 保 A，证明 Lock-5 排除）；GateService attempt 贯通 candidate；Phase 6
    annotation/candidate 同 LE 幂等单行（首个 attempt 保留）；annotation invalid 残留阻挡 valid 写。
- **独立对抗审查（sonnet 只读，R-A~R-G，冻结 diff）**：**无 P0/P1**。R-A Lock-3 无旁路；R-B attempt_id
  不进 business identity / LE hash / dedup；R-C Phase 6 仅锚单 UNIQUE、FK/NOT NULL 仍抛、并发败者无
  死锁、client-side default（uuid4）纳入 INSERT 无 PK 风险；R-D executor 参数放宽无 live 绕过（mock/
  disabled 忽略、live fail-closed）；R-G D/G 既有测试语义 preserve（invalid 不复用、新 LE 重试保持）。
- **deferred 登记（不重开；3 P2）**：P2-1——annotate 失败路径同 LE 已有 invalid 残留再失败时，create
  内 `RepositoryError` 遮蔽原始 provider/parse/validation 错误；**owner = Phase 7 方案 B**（届时触碰
  同一 D 失败路径、annotate 失败不再落 invalid 行，遮蔽随路径重写自然消解），仅违反「retry 须新 LE」
  契约才触发，非正常路径。P2-2——未跟踪 `_audit_d.py` 仍用旧签名直连 Gateway（Lock-3 前）；无 test_
  前缀 pytest 不收集、不入 Git 历史（一次性探针惯例），探针废弃自动消除。P2-3——缺服务层「同 LE
  invalid + 再失败」错误类型测试，与 P2-1 耦合，随 P2-1 一并由 Phase 7 定夺。
- **验证**：定向 D/G/runtime 34 ×2；全量 pytest **255 passed ×3**（净 +5：attempt provenance 5 新增，
  可重入）；git diff --check 干净；变更未 commit（Step 5 独立提交点待用户放行）。
- **下一步**：commit Step 5（独立基线，含 Status.md/log.md/restart-prompt v1.9 收口 + P2 deferred 登记）
  → **Phase 7（H0-15 方案 B）**：annotate 失败路径不落 invalid 行（失败留 audit+task 证据），顺带定夺
  P2-1/P2-3 → **Phase 8 TaskExecutor**（plan 末步，最后接编排）→ Phase 9 配置常量随步补。

### 2026-09-07 15:40（Step 5 第一性原理对抗审查 addendum：6 真 DB 探针全 PASS，无 P0/P1；P-4②③ 转正 → 256）

在 commit 前依用户要求做更强的第一性原理对抗审查（基于 V3 重建目标 + V3SPEC 约束；每结论以真实
PostgreSQL 测试为证据；不降低标准 / 不自合理化 / 不强行解释失败 / 不靠推测）。新资产
`backend/tests/_audit_step5_adversarial.py`（untracked 一次性探针，不入 Git 历史）：

- **P-1 / P-2（Phase 6 真并发败者路径，annotation + candidate）**：双独立 session，B 在 A 未提交时同
  (stage,hash) insert → `assert not b_task.done()` 证实阻塞于唯一索引（防假绿）；A commit 后 B ON
  CONFLICT no-op + re-read 返回 A 行 → 恰单行、胜者 attempt 保留。×3 稳定。
- **P-3（FK 不被 DO NOTHING 吞）**：非法 source_version_id → IntegrityError 照常传播（DO NOTHING 只锚
  (stage,hash)，FK 冲突不受影响）。
- **P-4（服务层端到端 invalid 残留 + attempt 落库 + P2-1 遮蔽签名）**：① 坏 provider 失败 → 落
  invalid(attempt=A) 且抛原始 RuntimeError；② 同 LE 好 provider 重试 → RepositoryError（服务层而非仅
  repo 层）；③ 同 LE 坏 provider 再失败 → RepositoryError 遮蔽原始 provider 错误（P2-1 签名 DB 实证，
  如实记录不自合理化）。
- **P-5（Lock-3 静态锁，import-line-only）**：domains/repositories 零 LLM gateway/provider import；
  domains 唯一 app.ai 引用 = `annotation/service.py: from app.ai.executor import LLMExecutor`（构造注入）。
- **P-6（parse / forbidden 失败分支 attempt 落库）**：两分支各落 invalid 行且 attempt 正确、诊断 payload
  保留（不只 provider-error 单分支，逐分支 DB 实证）。
- **转正**：P-4 ②③ 由一次性探针转正为永久回归
  `test_service_invalid_residue_blocks_valid_and_masks_second_failure`（rollback fixture，含 P2-1
  masking 签名断言）。
- **结论：无 P0/P1**。6 探针全 PASS。P2-1 已确认（owner=Phase 7 方案 B）；P2-3 随转正测试关闭；
  IntegrityError 契约无生产调用方（grep：仅 docstring 提及）；approve/reject 自身终态幂等由
  test_gate_service（GateService.run auto_approve 双跑 reuse）覆盖。
- **验证**：全量 pytest **256 passed ×2**（净 +1：P-4②③ 转正）；probe cleanup 后无污染；
  git diff --check 干净；变更仍未 commit（本次审查即 commit 放行前最后一道门）。
- **下一步（不变）**：commit Step 5 独立基线（待用户放行）→ Phase 7（H0-15 方案 B）→ Phase 8
  TaskExecutor → Phase 9 配置常量随步补。

### 2026-09-07 20:02（H Phase 7 方案 B 实现 + commit 前第一性原理对抗审查 + 用户放行收口）

Step 5 已于 commit `0917404` 落盘（含 Status/log/restart v1.10 收口）。Phase 7（H0-15 方案 B）随后
实现并在 commit 前按用户要求以第一性原理 × V3SPEC 对抗审查（每结论真实 DB 测试证据；不降标准 /
不自合理化 / 不强行解释失败 / 不靠推测），结论无 P0/P1，用户放行收口：

- **交付（方案 B，零越界）**：`app/domains/annotation/service.py` 删除 3 条 failure-path
  `create_semantic_annotation(status="invalid")`（provider error / JSON parse error / forbidden-field），
  失败**不再落 invalid artifact**、不再占 (stage,hash)；成功路径只写 `status="valid"`。三失败均以异常
  原样传播（provider 原异常 / parse→`ValueError("LLM response not valid JSON: …")` / validation→
  `ValueError("annotation payload contains forbidden fields: …")`），service 不吞。repository /
  executor / gateway **零改动**——历史 invalid 残留防御（snapshot_repository `_annotation_by_le` +
  ON CONFLICT + RepositoryError）原样保留。
- **失败语义区分（与 llm_call_audit 的关系）**：provider/timeout/HTTP 失败 → executor finalize audit
  `failed` + settle(actual=0) → re-raise；HTTP-OK 但 parse/forbidden 失败 → executor 已在 provider 返回
  文本后 finalize audit `completed`（executor 无法预知内容校验），失败详情经 service 的 ValueError 传给
  caller → 由 task 层承接。audit 与 annotation artifact 两轨解耦。
- **回归**：新增 `test_h_step7_failure_policy.py` 6 测试锁死 S7-1..S7-6（见 Status）。既有
  test_annotation_dbflow / test_h_step5_attempt_provenance / test_d2.. 经 executor 注入语义保持
  （git diff 仅 service.py + 2 test 适配 + 1 新增）。`test_service_invalid_residue_blocks_valid_and_masks_second_failure`
  （P-4②③ 转正）被方案 B 取代——失败不再落 invalid → 无残留累积、无遮蔽（P2-1 消解），repo 级防御由
  test_h_step7_failure_policy S7-history + test_h_step5 test_phase6_annotation_invalid_residue_blocks_valid 保留。
- **commit 前对抗审查（mock 覆盖空洞实证填补）**：既有 Phase 7 测试全走 gateway mock 分支（mock 无
  audit/budget/计数副作用，G4）——plan Phase 7 语义区分（L229-238：HTTP 成功 + parse 失败 → audit
  COMPLETED / provider 失败 → audit FAILED / 两者都 0 artifact）**从未在真实 live 链路证据化**。新资产
  `backend/tests/_audit_phase7_live.py`（untracked 一次性，不入 Git）：live executor × service × 真
  task/document/source（LLMGateway("live", allow_live, task_context, budget_ok, live_provider)），
  **L1–L5 全 PASS**：
  - **L1**（parse，live 返回坏 JSON）→ service 抛 ValueError("not valid JSON")；audit 恰 1 行
    `completed` + **error_type=None**（L1 实证 plan「parse 详情经 error_type 承载」未落地——
    executor 在 service parse 前已 finalize，audit append-only 不可补记 → 登记 H8-1）；annotation 0 行；
    invocation 1；task budget used=1/reserved=0。
  - **L2**（provider，live 抛 LLMNetworkError）→ 原异常原样传播；audit 恰 1 行 `failed`/
    `network_error`；annotation 0 行；invocation 1；task budget used=0/reserved=0（失败释放 reserve，
    settle actual=0，P2-1 遮蔽在 live 下亦根除）。
  - **L3**（forbidden payload）→ ValueError("forbidden fields")；audit `completed`（provider 成功返回文本，
    与 parse 同族）；annotation 0 行——实证 forbidden 分支自然归 audit completed，plan 语义区分表未显式
    冻结该分支 → 登记 H8-2。
  - **L4**（同 session fail→success 同 LE）→ provider 失败后 session 未被悬挂（executor 内
    commit/rollback 干净），同 LE 换好 provider 成功 → 收敛恰 1 valid；audit=[failed, completed]
    （attempt 各自独立终态）。
  - **L5**（success 后同 LE retry）→ find_existing 命中 → 复用既有 valid；provider 不重调、audit 不增、
    invocation 不增（幂等不重复计费；30 §7 attempt 语义）。
- **对抗结论**：A1–A9 全部符合 plan/spec（plan 字面 diff 无越界；10 §5.1 status 三值仅取值域无
  「失败必写 invalid」消费者契约；20 §4.3 「失败即 invalid」是 payload 校验语义非持久化命令；20 §4.7
  consumers 只消费 valid、supersede 写者=确定性 Application 未受影响；30 §7 retry 二分正交）。无 P0/P1。
- **两个 Note → Phase 8 Required Handoff（不阻塞 Phase 7，不改 Phase 7 代码）**：
  - **H8-1**：parse/validation 失败详情现只经 service ValueError 传给 caller；audit completed 行
    error_type=None（append-only 不可补记）——**Phase 8 TaskExecutor 须把下游失败详情写入 task
    failure，否则丢失**。
  - **H8-2**：冻结双层失败语义——`llm_call_audit` = Provider Invocation Runtime Truth（provider 返回即
    completed）；`task` = Logical Execution Outcome（下游失败 → task failed + failure reason =
    parse/validation/provider…）。`LLM completed ≠ Logical task completed`。
- **验证**：全量 pytest **261 passed ×2**（净 +6：S7 六测试，无中间清理，可重入）；真 DB 探针 cleanup
  后无污染（FK 序删净 doc/version/annotation）；git diff --check 干净。
- **deferred 状态**：**P2-1 Closed**（遮蔽随方案 B 消解，S7-5/Q-1 实证）；**P2-3 Closed**（随转正）；
  P2-2 不入历史；D1 crash-orphan reconciliation / D2 provider exception translation / D3 reclaim fallback /
  F-4 usage·token 事实源 + idempotency_key DB 唯一 = 延续登记（Phase 8/9 定夺）。BUG-V3-001..028 Open 不变。
- **commit**：Phase 7 独立基线已提交（代码 + Status/log/restart v1.11 收口；全部 `_audit_*.py` 探针排除
  Git 历史）。**下一步**：plan **Phase 8 TaskExecutor**（承接 H8-1/H8-2）→ Phase 9 配置常量随步补 →
  H 段最终收口。

### 2026-09-07 20:49（H Phase 8 TaskExecutor 实现 + 独立对抗审查 + 修复收口）

- **背景**：按 plan 末步实现 Phase 8 TaskExecutor（最后接编排），承接 H8-1（下游失败详情持久化）/
  H8-2（audit/task 双层失败语义）。
- **决策/实现**：
  - `TaskExecutor`（`app/domains/task/executor.py`）只拥 Runtime Authority：`run_once` →
    `claim_next`（原子 claim）→ 逐 stage（Seal→Annotation→Compile，各独立 session 事务）→
    `complete`/`fail`；stage 边界 `_heartbeat` 续租（审查 HIGH 修复）；`_classify_error` 分类
    （V3Error→error_type / ValueError→validation_error / 其它→system_error）→ `fail(error_type,
    error_detail)` 持久化（H8-1/H8-2）。
  - Worker CLI（`app/worker/__main__.py`）：run（safe 默认）/ run --allow-live / recover
    （默认 dry-run）--confirm / retry。复用 live_guard + settings 常量。
  - `TaskClaimRepository.finalize_claim`（受控 claim 终态迁移，类比 audit finalize_audit）：
    写 outcome/error_type/end + lease_snapshot `||` 并入 error_detail；`TaskRepository.next_queued_id`。
  - `TaskService.claim_next` + complete/fail 扩展写 claim 终态 + lease_seconds 从 settings 读。
  - `config.py` Phase 9 常量：worker_concurrency=1 / task_claim_lease_seconds=60 /
    http_retry_count=2 / provider_fallback_enabled=False。
- **独立对抗审查（sonnet 只读，0 CRITICAL / 1 HIGH / 2 MEDIUM / 3 LOW）**：确认无越权、Lock-2
  attempt 复用正确、finalize_claim SQL 正确。检出并修复——HIGH（Worker 从不续租 → stage 边界
  `_heartbeat`）；MEDIUM（`except BaseException` 吞取消信号 → 改 `except Exception`）；测试隔离
  （残留 queued task 污染 next_queued_id → cleanup 前移）。
- **deferred 登记**：D1 claim_next 并发语义缺口（worker_concurrency=1 不触发）；D2 config 三字段
  M1 预留未接线；D3 file_path 信任边界（未来 enqueue 校验）；D4 finalize_claim 缺行语义不对称 +
  recover 不写 claim 终态（观察项）；D5 live 长 stage 持续 heartbeat 未接（live smoke 后）。
- **验证**：全量 pytest **267 passed ×2**（净 +6）；git diff --check 干净；Worker CLI `--help`
  smoke；真 DB 探针（claim→running + heartbeat 续租 + run_once→succeeded）实证。
- **影响**：LLM Runtime Execution Layer 收敛为「唯一入口（Step 4）→ attempt 贯通（Step 5）→
  success-only artifact（Phase 7）→ TaskExecutor 编排（Phase 8）」，Worker 可驱动 document_ingest
  全链路（M1 mock/native；live transport 接线待 live smoke）。变更未 commit（待用户放行）。

### 2026-09-07 21:02（Phase 8 第一性原理对抗审查：真 DB 探针 7/7 PASS）

- **背景**：用户要求 commit 前以第一性原理 × V3SPEC 对抗审查，每结论真实测试证据。
- **探针**：新资产 `backend/tests/_audit_phase8_adversarial.py`（untracked 一次性，不入 Git）
  7 探针全 PASS——P1 Lock-2 attempt 复用（replay 保留首次 attempt_id + 零新增）；P2 live provider
  失败双层语义（audit failed/network_error + task failed + claim error_type=network_error +
  error_detail）；P3 live parse 失败双层语义（audit completed + task failed + validation_error，
  `LLM completed ≠ Logical task completed`）；P4 stage 单事务边界（seal 保留 + annotation 0 +
  task failed）；P5 finalize_claim 并发 exactly-once（恰一迁移）；P6 静态 Runtime Authority（零
  业务决策 import + 零 decision_status 访问 + LLMExecutor 唯一入口）；P7 crash 恢复链路（recover
  仅置 interrupted 不产生内容 → retry → re-run 复用）。
- **如实记录**：P6 初版字符串匹配误报（executor.py docstring「不判 decision_status/Question」
  被当作触碰）→ 修正为精确检查（import + `.decision_status` 属性访问）后 PASS；Grep 核验二者
  仅在 executor.py:14 docstring、非实际触碰。非自我合理化。
- **结论**：无 P0/P1；Phase 8 核心不变量经真实 DB 实证；此前 sonnet 审查修复均被探针覆盖。
- **验证**：全量 pytest **267 passed** 不变；探针 cleanup 无污染；不入 Git。

### 2026-09-07 22:xx（V3 全量对抗审查 + H Batch 1 修复闭环 + BUG-V3-007 终裁）

- **背景**：用户要求对 V3 全部代码做第一性原理对抗审查（每结论真实测试证据）。4 路并行只读
  审查（段 A/B/C、D/E、F/G、H）+ 13 真 DB probe + 纯函数复现 + 全量测试，确认 4 HIGH + 12
  MEDIUM + 9 LOW 实现层缺陷 + 28 Spec 域缺口（BUG-V3-001..028 已登记）。
- **4 HIGH 裁决**：H-1 seal 并发幂等无 DB UNIQUE 兜底（真 DB 并发 probe FAIL：2 doc）；H-2 非
  dict JSON 落 valid（真 DB probe FAIL：`[]`→valid）；H-3 表头非锚定子串误判区界（纯函数复现）；
  H-4 contextual material 绕过 Gate（纯函数复现）。用户下达综合裁决：A–G 继续 CLOSED，H Phase
  1-8 substantially complete 但 FINAL CLOSURE BLOCKED，Phase 9 PAUSED。
- **Batch 1 修复（H-2/H-3/H-4，用户批准 CLOSED）**：
  - H-2（BUG-V3-030）：`validate_annotation_payload` 顶层 `isinstance(payload, dict)`，非 dict
    走方案 B 失败路径。
  - H-3（BUG-V3-031）：冻结 Header Grammar（`is_answer_header`/`is_explanation_header`），替换
    Resolver 6 处 substring 判定；完整 token 匹配非 prefix substring。
  - H-4（BUG-V3-032）：`policy.evaluate` provenance 层把 shared material 纳入 resolution 白名单。
  - 测试：`test_s7_non_dict_json_rejected` + `test_composite_material_contextual_not_auto` +
    `test_resolver_header_grammar.py`（39 项正反例 + 端到端「题干含答案不误判」）。
- **BUG-V3-007 终裁（用户 Final Ruling）**：`original_sha256` 定义 Source/Document Identity，不
  定义全局唯一 Sealed Version；同 `original_sha256 + seal role/provider scope` 内至多一个
  canonical sealed version；跨 role/provider 允许多 version；禁 `UNIQUE(original_sha256)`。
- **验证**：全量 pytest **308 passed**（净 +41）；git diff --check 干净。
- **下一步**：Batch 2 = H-1（BUG-V3-007 终裁 → identity scope verification → scoped DB
  uniqueness → 并发 seal probe → regression）。

### 2026-09-07 22:xx（Batch 2 = H-1 seal 并发幂等修复）

- **背景**：H-1（BUG-V3-029）seal/document 并发幂等无 DB UNIQUE 兜底。BUG-V3-007 终裁
  （用户 Final Ruling + Clarification）：documents.UNIQUE(original_sha256) 放行（Source/Document
  Identity），document_source_versions.UNIQUE(logical_execution_stage, logical_execution_hash)
  放行（Seal LE Identity），禁 document_source_versions.UNIQUE(original_sha256)。
- **实现**：migration 0006（两约束，DO 块 IF NOT EXISTS 双路径安全）；`create_document`/
  `create_source_version` 改 `pg_insert ON CONFLICT DO NOTHING` + re-read；`SealService` 并发收敛
  （re-read sealed → 复用，跳过 append/seal）；schema guard DECLARED_UNIQUES +2（总数 6→8）。
- **验证**：全量 pytest **310 passed**（净 +2：`test_h_seal_concurrency` 并发 seal 恰 1 doc + 1
  version + 无重复 line + 跨 role 多 version 合法）；真并发 seal winner/loser 收敛同 canonical identity。
- **影响**：H-1 Resolved（BUG-V3-029 关闭）；4 个 HIGH 全部关闭。剩余 Runtime blockers（Batch 3）。

### 2026-09-07 22:xx（Batch 3 = H Runtime correctness 4 blocker 修复）

- **背景**：V3 全量对抗审查确认 4 个 Runtime blocker。逐个最小修复 + adversarial test + 全量
  regression + 独立提交。
- **3-1 cancellation semantics**：`ai/executor.py` `_complete_live` Phase B/C `except BaseException`
  → `except Exception`——CancelledError/KeyboardInterrupt/SystemExit 不被吞/不误 finalize 为 failed，
  直接传播（audit 保持 STARTED 由 recovery 判 unknown，30 §10）。
- **3-2 lease ownership**：`TaskRepository._terminal` 补 `lease_expires_at > now()`（与 heartbeat
  一致）——已失去 lease 的 worker 不得再改 task 终态。
- **3-3 audit/settle boundary**：`_complete_live` Phase C 拆两事务——audit terminalization 独立于
  budget settle 先行 commit（settle 失败不回滚 audit，30 §10/§11 + F-6）。
- **3-4 model_config_hash identity**：`TaskExecutor._annotation_stage` 的 model_config_hash 编码
  实际 provider/model（30 §7），杜绝 LE identity 与实际 invocation 漂移。
- **验证**：全量 pytest **314 passed**（净 +4）。每个 blocker 带 adversarial regression。
- **影响**：4 HIGH + 4 Runtime blocker 全部关闭；H Runtime 主链边界收紧。下一步 Batch 4（H Final
  Re-Probe）。

### 2026-09-07 22:xx（H Phase 1–8 FINAL CLOSURE）

- **用户正式宣布 H Phase 1–8 FINAL CLOSED**。H Runtime Execution Layer 完成 Frozen Contract 运行时
  闭环（Task State Machine → Claim/Lease → Attempt → LLMExecutor → Artifact → Task Outcome + audit/
  budget 双层语义）。A–G 继续 CLOSED。
- **Closure 证据**：4 HIGH + 4 Runtime blocker 全关闭；Batch 4 Re-Probe（4 HIGH + 4 runtime +
  core invariants 全 PASS）；全量 **314 passed**；Known HIGH = 0 / Unreviewed P1 = 0。
- **裁决边界**：H Phase 1–8 不因后续普通缺陷自动 reopen（走 post-closure defect/errata）；Phase 9
  批准进入范围冻结（Scope Freeze 先于实施）；不自动纳入 D1/D3/D4/D5/F-4 deferred。
- **影响**：V3 的 A–H 主链从「设计+实现」进入「冻结后下一阶段开发」；下一步 Phase 9-0 Scope Freeze。

### 2026-09-07 22:xx（Phase 9-0 Scope Freeze 终裁）

- **Phase 9-0 Scope Freeze CLOSED**（用户选 B：先冻结语义再实施）。3 个 spec gap 冻结为
  implementation 语义并登记 BUG-V3-033/034/035（Frozen for implementation）。
- **冻结语义**：HTTP retry ≠ 新 Provider Invocation（transport retry，不增 invocation/audit/budget）；
  transport exception → LLMNetworkError、HTTP response error → LLMProviderError（408/429/5xx
  retryable、4xx 其他 non-retryable）；fallback 默认关闭、仅 transient provider/network failure +
  retry exhausted + 显式有序 provider 才触发、= 新 LE + 新 invocation。
- **红线**：HTTP retry（transport）≠ LLM retry（同 LE）≠ fallback（新 config/新 LE/新
  invocation），三者不混。MAX_LLM_CALLS_PER_TASK 仍按真实 Provider Invocation 计数。
- **影响**：Phase 9 范围与语义冻结；下一步 9-1B（config 收口 + provider exception translation）。

### 2026-09-08 06:17（Phase 9 全量实现 + 第一性原理对抗审查 + B-1/B-2 修复收口）

- **背景**：Phase 9-0 Scope Freeze 冻结 3 spec gap（BUG-V3-033/034/035）后，按 9-1B→9-2→9-3
  顺序实现，随后用户要求以第一性原理 × V3SPEC 对抗审查（每结论真实测试证据；不降标准 /
  不自合理化 / 不强行解释失败 / 不靠推测）。
- **Phase 9 实现（决策/实现，commit 链）**：
  - `fabf560` 9-1B：`LLMProviderError` 加 `retryable` 属性；`HTTPLLMProvider` 翻译
    `httpx.TransportError`→`LLMNetworkError`、`httpx.HTTPStatusError`→`LLMProviderError`
    （408/429/5xx retryable、4xx 其他 non-retryable）；`LLMExecutor` 识别 non-retryable 不重试。
  - `5f7b9b1` 9-2：`HTTPLLMProvider.complete` transport retry 循环（`http_retry_count`，仅
    `httpx.TransportError`），bounded，不增 invocation/audit/budget（计数点仍在 gateway provider
    seam，先于本层）；CancelledError 为 BaseException 自然传播。
  - `4f44ad4` 9-3：`LLMGateway.live_providers` 按 provider 名路由；`LLMExecutor`/`LLMGateway.complete`
    透传 provider；`TaskExecutor._annotation_stage` fallback 链（显式有序有限 + dedup 禁回退
    primary + `retryable=False` 立即抛 + attempt_id 贯穿 primary/fallback）。
- **对抗审查发现（真实缺陷，6 探针）**：`_audit_phase9_adversarial.py` 6 探针，发现 2 缺陷：
  - **B-1（HIGH）**：`_resolve_live_provider` 未注册 provider 名静默回退 `_live_provider`
    （primary）→ audit 记 fallback 名、实际调 primary，identity 漂移（Runtime Truth 破坏）。
  - **B-2（MEDIUM）**：HTTP 200 + malformed body 泄漏裸 IndexError/KeyError/JSONDecodeError →
    audit error_type='unknown'（非 provider_error），BUG-V3-034 翻译遗漏第三类 provider
    failure（payload contract violation）。
- **修复（决策/实现，独立 commit）**：
  - `1e435a9` B-1：multi-provider 模式名未命中 → None（fail-closed→GatewayDenied），
    single-provider 模式才回退默认（向后兼容）。+4 test。
  - `312d1f7` B-2：响应解析 try/except + content null 显式检查 → `LLMProviderError(retryable=False)`
    （用户裁决保守分类：HTTP 200 属 contract violation 非 transient）。+8 test（7 单元 + 1 audit
    层端到端 error_type='provider_error'）。
- **验证**：全量 pytest **344 passed**（原 332 + 12 新增，可重入）；re-probe 6/6 PASS（P1/P2/P3/P6
  断言由「缺陷存在」反转为「修复生效」）；git diff --check 干净。
- **影响**：Phase 9 三层 retry 语义（transport / LLM / fallback）+ provider boundary 全量
  fail-closed 收口；provider boundary 不泄漏裸异常、identity resolution 不漂移。下一步 Phase 9
  Final Closure 待用户裁决。

### 2026-09-08 06:30（Phase 9 FINAL CLOSURE）

- **裁决**：用户正式宣布 **Phase 9 FINAL CLOSED**。push 3 个 commit（`1e435a9` B-1 /
  `312d1f7` B-2 / `67737b5` docs）到 origin/main，验证远端 HEAD = `67737b5` 且工作树同步后，
  状态落为 FINAL CLOSED。
- **Closure 证据**：344 passed；re-probe 6/6 PASS；B-1 HIGH resolved；B-2 MEDIUM resolved；
  documentation closure committed；all Phase 9 commits synchronized to origin/main。
- **Closure 边界（严格）**：Phase 9 范围关闭 ≠ V3 全部关闭。A–G / H Runtime 保持 FINAL CLOSED；
  D1/D3/D4/D5/F-4 保持 Deferred/Open；BUG-V3-001..028 待 errata 终裁；Phase 10+ Not Started。
- **影响/下一步**：Runtime Layer 相对完整；不再立即新增 Runtime 功能。下一优先级 = BUG-V3-001..028
  系统性分类审计 → A–F Errata Final Ruling → 再决定下一开发 Phase 范围。

### 2026-09-08（Phase 9 Closure Reopened → C-1 修复 → Re-Closure）

- **裁决**：外部独立审查发现 C-1（负 retry 配置穿透执行层）。用户裁决选择 A——最小范围双保险修复，
  重开 Phase 9 Final Closure assertion。
- **C-1（MEDIUM）BUG-V3-036**：`llm_request_retry_count` / `http_retry_count` 无 `ge=0` 约束 +
  构造不校验。负值 → `range(0)` 零迭代 → 0 真实调用却 failed/unknown audit + settle(0) + return
  None；HTTP 负值 → `LLMNetworkError("...: None")` 零请求。
- **修复（决策/实现）**：`config.py` 两字段 `Field(ge=0)`；`LLMExecutor.__init__` /
  `HTTPLLMProvider.__init__` `if < 0: raise ValueError`。TDD：RED 4 failed → GREEN 6 passed。
  commit `7ace837`。
- **验证**：全量 pytest **350 passed**（原 344 + 6 新增）；git diff --check 干净。
- **影响**：非法 retry 配置不再进入有副作用的执行路径（0 invocation/audit/budget/provider +
  0 None-return 被永久钉死）；retry=0 合法语义（attempts = 1 + retry_count）保持。

### 2026-09-08 14:01（BUG-V3-001..028 errata 分类审计 + E/B/A Closure + D-1 Schema 完成）

- **背景**：Phase 9 Re-Closure 后，用户授权 BUG-V3-001..028 系统性 errata 终裁，方法论
  「先证伪、后修复」（falsify-first），5 类分类：A=已被后续设计覆盖 / B=纯文档 errata /
  C=真实 implementation gap / D=必须改 Frozen Spec / E=可正式关闭。
- **分类结果（并行审计）**：A=010；B=003/004；C=011；D=22 项（001/002/005/006/008/009/012/013/
  014/015/016/017/018/019/020/021/022/023/024/025/026/027）；E=007/028。
- **执行顺序（用户裁决）**：先闭 E/B/A → D-1 Schema → D-2 Identity/Hash → D-3 Annotation →
  D-4 IR/Compiler → D-5 Gate → D-6 Figure Contract → BUG-011 实现。每条 D 类 8 项裁决
  （Canonical Rule / Rejected Alternatives / Backward Compat / Migration Impact / Identity
  Impact / Rebuild / 代码改动 / 验证 Gate）；红线「先冻结 Spec，再改代码」，绝不倒序。
- **E/B/A Closure（commit `b02c16c`）**：003/004（B 类文档 errata）、007/028（E 正式关闭）、
  010（A 已覆盖）。
- **D-1 Schema（5 项，`60bc497` Spec + `eb0e450` 008 + `5b0f767` 027）**：
  - 001/002/006（Spec 文案 errata）：域归属裁决 / role-provider 枚举 / selection-event 9 列
    冻结 / dedup_key UNIQUE 声明，写入 10_Data_Model.md 正文。
  - 008（独立 provider/role）：新增 `paddleocr-vl`/`ocr_ppsvl` 封闭配对，`seal.py` 加
    `validate_seal_role_provider` fail-fast；`task/executor.py` `_seal_stage` role 默认
    `"main"`→`"native"`。TDD RED→GREEN（17 passed）。
  - 027（全局 UNIQUE）：`questions.dedup_key` 加 `UNIQUE`；migration 0007 前置查重 fail-loud；
    `create_question` 改 `ON CONFLICT DO NOTHING` + re-read 幂等收敛。并发/串行测试锁死
    「恰 1 Question」。
- **验证**：全量 pytest **355 passed**（350 + 3 配对 + 2 并发幂等）；git diff --check 干净。
- **影响**：E/B/A + D-1 Schema 五条收口；questions canonical identity 全局唯一 + seal role/
  provider 封闭配对成为 runtime 事实。下一步 D-2 Identity/Hash（高风险组，identity 一旦形成
  生产数据难回滚，须逐条 8 项终裁）。
- **待办**：4 commit（b02c16c/60bc497/eb0e450/5b0f767）本地未 push，待用户明示 push。

### 2026-09-09 05:55（D-6 Figure Contract + BUG-011 实现 + Final Closure）

- **D-6 Figure Contract（BUG-V3-020）closure**：commit `0b0a4d3`——冻结 figure_refs 跨层契约
  （spec-only，A-Guarded；E ResolvedSpan ↔ SourceFigure/IS-7 跨层契约）。D-1 → D-6 六类 errata
  全链完成。
- **BUG-011 Scope Freeze（`5c9ecc9`，docs-only）**：Frozen Spec 同步（10 §4.4/§6.6 + 20 §5.3/
  §7.2.5 + 两册 §12 变更记录）；canonical notation `FIG-{page_no}-{ordinal:02d}`；placement M1 =
  standalone（source-level 未定，≠ figure_refs[].role unit-level）；4 项裁决 + 2 语义修订 +
  IS-7 重定义为完整写入门（7 字段齐 + deterministic）。
- **BUG-011 Implementation（A/B/C/E，依赖序推进，每个 commit 后跑最小测试子集）**：
  - A Figure Identity（`a8cd129`）：`build_figure_index` 纯函数 + canonical sort + figure_id/
    object_key/figure_hash 确定性；
  - B Native Extraction（`dd26a6b`）：PyMuPDF `get_image_info` → `OCRResult.figures`；失败语义 =
    「无 image placement」合法空集 / 「发现但无法形成完整 figure」→ seal failure（IS-7 fail-loud）；
  - C Persistence+Integrity（`716875e`）：`seal.py` `append_figure` + `integrity_hash` 计入
    `figure_hashes` + `SourceFigure` ORM（`UNIQUE(source_version_id, figure_id)` __table_args__）；
  - E DB UNIQUE（`9da09db`）：migration 0009 DO block IF NOT EXISTS（复刻 0007 幂等模式），
    前置查重 fail-loud。
- **Gate / Migration 验证**：全量 pytest **413 passed**；migration replay 双路径 PASS（from-empty
  0001 create_all 建约束 + incremental 0008→0009 delta == {uq_source_figures_figure_id}）。
- **Final Closure**：BUG-V3-011 → Resolved / Closed；**BUG-011-E2 保持 Open 独立记录**（E
  `_image_span` IS-7 消费 4 字段 vs B 写 7 字段跨层 drift；Spec 已区分写入门 10 §4.4 7 字段 /
  消费资格 20 §5.3 4 字段子集，E 代码对齐留待后续统一处理，不随 BUG-011 关闭）。origin/main ==
  local main == `9da09db`。

### 2026-09-09 06:16（Errata Final Closure）

- **BUG 状态收口**：剩余 17 项（005/009/012..026）bugs.md Status → Resolved（逐条 Closure
  evidence，锚 D-2..D-6 冻结裁决）。至此 BUG-V3-001..036 全部 Resolved（033/034/035 = Frozen
  for implementation，非 Open）；BUG-011-E2 保持独立记录。
- **`_audit_*.py` 处置（用户裁决 = 归档到非正式目录）**：12 份一次性审计/对抗探针移入
  `backend/tests/_audit_archive/`（untracked，不入 git）；findings 已在各阶段转正为正式测试。

### 2026-09-09 14:58（Phase I Live Data Plane Integration + BUG-V3-037 lease 修复完成）

- **背景**：Errata Final Closure（BUG-V3-001..036 收口）后进入新阶段 Phase I（Live Data Plane
  Integration）——证明真实 Ollama/Qwen 数据面（非 mock）驱动完整 V3 Runtime 链并在 PostgreSQL
  留下可验证 provenance。
- **I-0 Prompt Contract Alignment**：旧 prompt 从不把 Frozen Annotation Contract 传给模型 →
  真实 Qwen 输出栅栏 + schema 全盘漂移。`build_annotation_prompt` 把 20 §4.1–4.5 真实写入前缀
  （顶层三字段 / standalone_question 完整结构 / 字段约束 / 硬性禁止）。`test_prompt_contract.py`
  锁 presence + strength。
- **BUG-V3-037（Live Long-Running Stage Lease Loss）**：live smoke 实证 Task 卡 running
  （`lease already lost (recover-owned)`）——annotation stage 内 ~300s 冷加载 LLM 调用期间无
  heartbeat，60s lease 中途过期。方案 2（用户裁决，不延长 lease）：新增
  `TaskExecutor._lease_heartbeat` 后台 renew loop（周期 = lease/4，严格 < lease），`finally`
  清理无 orphan；LeaseConflict 停循环 + 边界 fail-loud；不 cancel 在途 LLM 调用（避免与
  BUG-V3-035 fallback/cancellation 契约交叉）。Compile stage（M1 确定性无 LLM）暂不接入。
- **验证**：targeted（test_task_executor.py）18 passed + 全量 pytest **426 passed**（零回归）；
  live smoke 核心层 PASS（Task succeeded / audit ollama completed / budget settled /
  annotation valid / replay 零重复）。
- **BUG-V3-038（Resolver 跨层契约漂移）→ Resolved（2026-09-09 18:09）**：用户裁决方向 =
  Resolver 读 `question_label`，**禁止 alias fallback**。修 `reference.py` `_answer_target`/
  `_explanation_target`；`resolver.py:486` 诊断文案对齐；9 个 mock fixture 文件 content-role
  字段迁移；新增 strict contract 回归锁（payload 仅带 question_label、全文无 question_number
  → 必须完整解析 stem/answer/explanation）。
- **smoke harness correction（独立 commit）**：`_SMOKE_LINES` `[Answer]`→`【答案】` +
  `fontname="china-s"`；补【详解】区（模型声明 explanation role 时 fixture 须提供 source
  evidence，否则 Resolver fail-loud 判 missing——行为正确，非生产 bug）。
- **Prompt Contract（独立 commit）**：新增【explanation 源证据约束】块——仅当源中有
  【详解/解析】证据才声明 explanation；无证据省略字段；禁止凭空声明/占位。回归锁
  `test_prompt_explanation_source_grounding`（只锁文本 presence，服从由 live probe 证明）。
- **BUG-V3-039（Diagnostic Metadata Leaks into Compile Identity）→ Resolved（2026-09-09
  18:09）**：live smoke 实证真实 Qwen 输出 `confidence: 0.98`（float）→ `gate/service.py` 三处
  `sha256_hex(ann.payload)` → BUG-V3-005 `_reject_float` fail-fast → validation_error。
  Frozen Spec（20 §8.1:568/P1-6:768）confidence 是诊断元数据不作 decision 触发 → 建单一
  `_annotation_identity_projection`（仅剔 unit 顶层 confidence，不 mutate，三处 hash 复用）；
  prompt 示例删除 `"confidence": 0.98`（不新增「禁止输出 confidence」规则）；新增 5 类回归锁
  （`tests/test_identity_projection.py`）：confidence float 不破 identity / confidence 波动
  不改 identity（核心）/ semantic 变化仍改 identity / 其它 float 仍 fail-fast（BUG-V3-005
  反向锁）/ 无 confidence 向后兼容。
- **验证（2026-09-09 18:09）**：targeted 全绿；全量 pytest **433 passed**（428 + 5 新锁）；
  live smoke 12 层 Hard Gate **全 PASS**（Task succeeded + Candidate + Gate approved +
  Question=1 + Instance=1 + audit ollama completed + budget settled + replay 零重复）。
- **Phase I live data plane 四层阻断全部关闭**：I-0-1 prompt contract → BUG-V3-037 lease →
  BUG-V3-038 field drift → BUG-V3-039 identity leakage。mock/contract test 均未覆盖，由 live
  smoke 逐一暴露。
- **影响**：Phase I-1-D 验收达成。Phase I 全部变更未 commit；4 个 commit 边界已冻结（①
  BUG-V3-037；② BUG-V3-038；③ Live Smoke Fixture + Prompt Grounding；④ BUG-V3-039），待
  用户明示执行。
- **下一步**：用户明示 commit → Post-Implementation Gate Review（重点：identity-bearing
  production path 是否存在「fixture 未覆盖、真实模型可能生成」的字段）→ 判断 Phase I-1
  closure。

### 2026-09-09 18:30 — Phase I-1-D CLOSED（4 Commits + Gate Review PASS）

- **4 commits 已提交**（精确 staging，executor.py 跨 commit hunk 经中间版本分离）：
  1. `9730351` fix: BUG-V3-037 lease heartbeat（executor.py heartbeat hunks + test_task_executor.py）
  2. `02c3431` fix: BUG-V3-038 resolver question_label（reference.py + resolver.py + 9 test fixtures）
  3. `168d17b` test: live smoke fixture + prompt grounding（live_smoke_ollama.py + executor.py prompt + test_prompt_contract.py）
  4. `0f71241` fix: BUG-V3-039 identity projection（gate/service.py + test_identity_projection.py + executor.py prompt 减噪）
- **Post-Implementation Gate Review PASS**：
  - Identity-bearing Path Inventory：所有 annotation payload hash（`_compile_input_domain` /
    `_input_identity` 三处）统一经 `_annotation_identity_projection`；`logical_execution_hash` /
    `build_idempotency_key` 继承上游 projected input；`identity_hash`（question 级）消费
    compiled/normalized text 非 annotation payload；无绕过路径。
  - Unknown Field Policy：`validate_annotation_payload` 仅 FORBIDDEN_FIELDS 检查，不拒绝
    unknown fields（P1-a 冻结）；unknown semantic fields 进 identity（正确）；仅 confidence
    被 projection 排除（diagnostic metadata，20 §8.1:568）。
  - Fixture Coverage：无 confirmed gap。
  - Required Action: None。
- **验证**：全量 pytest **433 passed**；live smoke 12 层 Hard Gate 全 PASS（代码未变，仅
  staging）。
- **Working Tree 剩余**（不属于本轮 4 commits）：gateway.py / providers/http.py /
  worker/__main__.py / test_gateway.py / test_http_provider.py（早期 Phase I transport）；
  Status.md / log.md / restart-prompt.md / bugs.md（文档）；_audit_archive/ / probe 脚本 /
  PDF fixtures（辅助工具）。
- **Phase I-1-D 正式 CLOSED**。项目状态：V3 Core Architecture Closed → Phase I Live Data
  Plane Verified → Real File E2E Next → Productization Not Started。

### 2026-09-09 20:15 — Phase I-1 Closure（Heartbeat Flaky 修复 + Identity Gate Review + Transport 接线）

- **BUG-V3-037 Heartbeat Flaky 修复**（`bfe4434`）：全量测试实证
  `test_long_annotation_keeps_lease_alive` 间歇性失败。根因 = `_renew_loop` 先 sleep 再
  heartbeat，首次续租延迟一个 interval；NullPool 连接建立 + event-loop 竞争下首次续租可能
  晚于 lease 过期 → LeaseConflict → 循环退出。修复 = 循环倒置为先 heartbeat 再 sleep。
  压力验证：单测 ×20 / heartbeat 组 ×20 / 全量 ×3 全 PASS。
- **Post-Implementation Identity Gate Review**（`1f08882`）：PASS WITH DOCUMENTATION。
  Identity Projection Rule 契约固化（bugs.md）。新增反向锁
  `test_nested_confidence_is_not_silently_projected`。
- **全量对抗性审查**：434 tests 全 PASS。SPEC 约束逐条验证通过。0 TODO/FIXME/HACK。
- **Phase I Transport 接线**（本轮提交）：
  - I-1-A: `HTTPLLMProvider` 条件 Authorization + `trust_env=False`。
  - I-1-B: `build_gateway()` 工厂 + worker 改用工厂 + 3 新测试。

### 2026-09-09 22:30 — Phase I-2C Closure（Resolver Diagnostic + 真实 PDF 失败模式确认）

- **背景**：Phase I-2 Revision 关闭后，Resolver 在真实数学 PDF 上 17 resolved / 85 unresolved。
  需要诊断失败原因，决定是否进入 Resolver robustness 改进。
- **I-2C-1 BUG-V3-043 修复**（`5f8a3a8`）：`GateService.run()` 创建 `SourceResolver` 时未传
  `figures` 参数 → 所有 image reference 恒 `ambiguous`。修复 = 加载 `source_figures` 转
  `SourceFigureView` 传入。52 passed 零回归。
- **I-2C-2 Diagnostic Layer**（`5f8a3a8` + `1192108`）：新增 `resolver/diagnostic.py`
  （MatchAttempt / CandidateLine / UnresolvedDiagnostic / DiagnosticReport）。15 tests。
  Pure functions, no IO, deterministic。
- **真实 PDF 诊断**（`8267bfd`）：85/85 unresolved = `marker_ambiguous`（非 `marker_not_found`）。
  根因 = 题号 "1" 出现 190 次、选项标签 "A" 在数学公式中大量出现。Resolver 单行 marker 匹配
  无法唯一确定。
- **架构判断**：Resolver fail-loud 符合 V3 invariant（宁可拒绝确定，不允许错误定位）。失败不是
  Resolver bug，是 Source Provider Layer layout reconstruction 能力缺失。
- **Decision**：Resolver robustness enhancement deferred。下一阶段 = Phase I-3 Source Provider
  Layer Evaluation。
- **BUG 状态**：BUG-V3-043 Resolved；BUG-V3-041 Deferred → Phase I-3。
- **验证**：52 gate+resolver+dbflow passed；15 diagnostic passed；436 full suite passed
  （预存 FK/isolation 问题不计）。
- **Closure Gate 5/5 通过** → Phase I-1 CLOSED → Phase I-2 Real File E2E Next。

### 2026-09-10（Phase I-5-0 Scope Freeze）

- **背景**：Phase I-4 CLOSED（Valid Negative Result）后，用户引入外部预处理项目
  （PaddleOCR-VL → LLM semantic annotation → manifest）。12 份已审核高一/高二文档
  集成验证通过（319 units, 42/42 marker 消歧, 24/24 composite）。
- **决策**：Phase I-5 定义为 Preprocessed Source Integration Feasibility Experiment。
  I-5-0 只冻结边界与约束，不写 Adapter、不改 Resolver、不改 Domain、不改 Migration。
- **核心边界**：Manifest = Structural Annotation Evidence（非 Source Truth）。正文只有一份
  （Markdown Source），manifest 只能引用不能复制。
- **产出**：`Docs/V3_SPEC/65_PHASE_I5_SCOPE_FREEZE.md`——12 条约束、Candidate Evidence
  三层分类、Adapter 位置（experiments/phase_i5/）、Decision Matrix A-E、Measurement
  Dimensions（不冻结数值阈值）。
- **下一步**：I-5-1 Integration Boundary Analysis。No code until analysis complete。
