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
