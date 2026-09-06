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
