# AI Tutor V3 — 资产清点清单（50 §3 执行）

Version: v0.1
Date: 2026-09-05 17:15:03
Status: 清点完成（初版）；实现段 A/B 前置依据
Location: 本清单为 40 §2 前置资产清点的执行结果；资产本体仍在 V2 仓库（路径列出），
V3 侧仅 `Docs/reference/` 保留业务契约与参考。

> **更新规范**：本清单是工作文档（非状态文档）；任何更新带当前时间戳，追加至文末。
> 清点对象来自 00 §1 继承与 V2 仓库现存；**不搬 V2 代码/库/规则**（50 §5）。

## 0. 结论摘要

- V3 段 B（seal/OCR）、段 C（gateway/embedding）、corpus/fixture 所需能力与样本**均已在
  V2 现存定位**；无外部新增采集需求。
- **本体不动**：PDF/golden/seed 资产留在 V2；V3 需要时复制选定子集入 V3 资产目录（决策见 §7）。
- V2 golden 结构不可直接作 V3 预期：按 50 §4.2 需以 **V3 逐层结构**重标，V2 golden 仅作
  内容真值/覆盖清单来源。

## 1. 外部能力源

| 能力 | V2 现存（定位） | V3 复用方式 | 备注 |
|---|---|---|---|
| OCR 双源 | PaddleOCR-VL 云端异步 API（`paddleocr_api_base_url` / `paddleocr_vl_token`，`ocr_mock_mode` 默认 True，`config.py`）；PP-StructureV3（`Docs/reference/PADDLEOCR_API.md` 参考）；政策 `Docs/reference/OCR_PROVIDER_POLICY.md`（PPS/PVL 主识别，LLM VL 移出驱动链） | 引擎名与政策结论保留；**部署参数/token 不搬**，段 B 重配 | cloud OCR 是否 M1 启用 = 跨册裁决（30 §16 external 闸 / 00 本地优先），见 §7 |
| 本地 LLM | ollama（`ollama_base_url/model`，config.py） | V3 走 30 Gateway（disabled/mock/live），段 C 起 | 00 主 LLM Qwen 系本地 |
| Embedding | ollama + `qwen3-embedding:4b`，dim 2560，本地 | 保留（查重/检索，非 M1 阻塞） | 00 偏好 Qwen3 Embedding |

## 2. 数据样本（真实 PDF，经验收）

- **位置**：`D:\Project\AITutors-v2\test\pdf\`（~31 教师版期末卷）+ `test\pdf\new\`（~9）
  ≈ **40 份，覆盖 9 科**（历史/政治/英语/物理/语文/地理/化学/生物/数学；北京各区/校
  高一上期末教师版）。
- **配套**：`manifest.csv`（filename,size_bytes,subject,year,school,has_answer,has_images）
  + `manifests/{math,english,physics}_manifest.json`。
- **V3 用法**：作 50 §4 corpus / 40 段内 fixture 与段 B seal 的真实样本。**用户裁决
  （2026-09-05 17:18）：PDF 用户自有、可随时补充，V3 不复制 V2 样本、不依赖 V2 路径**——
  段 B / fixture 所需样本按需由用户提供。

## 3. Golden / 对照素材（已迁入 V3 `assets/annotations_src/`，作重标源料）

- **甄别（2026-09-05 17:22）**：V2 `golden/` 10 份实为**三族**，非全 human——
  - **human 验收级**（`annotator: human_golden`，v4.0 / v3.1，含 `expected_content` +
    `expected_anchor` 双结构）：`math_real_golden`、`english_exercise_2024`、
    `math_exercise_2024`
  - **契约标注族**（`display_contract_version: 0.4`，canonical type / shared_material /
    行号）：`chemistry_2026_bashi` / `chinese_2026_chaoyang` / `math_2026_chaoyang` /
    `physics_2026_chaoyang` `contract_golden` + `english_2026_dongcheng_real_golden`
    （虽名 real，带 0.4 契约字段）
  - **机器草稿**（`dsh_draft_from_native_live`，`0.1-draft`，V2 自标"不得直接用于验收"）：
    `english_2026_real_golden`、`physics_2026_real_golden` —— **清点曾误判为 human，实为
    草稿，已剔，不入真值源**
- **迁移裁决（2026-09-05 17:22）**：剔 2 份 draft，迁 15 份入 V3
  `assets/annotations_src/`。JSON 逐字节原样保留；V2 路径 `test/annotations/{golden,structure}`
  留档可溯。
- **对抗性审查修正（2026-09-05 19:34，目录现况）**：`physics_2026_chaoyang_contract_golden`
  含 LLM answer + needs_manual → `quarantine/`；`math_2026_chaoyang_contract_golden` 标
  `superseded_by_math_real_golden`。现组成 **real/3 + contract/4 + structure/7 +
  quarantine/1**；逐份 sha256/来源分级见该目录 `MANIFEST.csv`，可靠性分级与覆盖缺口见
  README v0.2。
- **V3 用法**：作 corpus / fixture **重标源料**（50 §4.2），不导入 V2 JSON 结构；文本真值
  （`expected_content` / 题干 / 选项 / 答案 / 详解）可复用为 V3 语义层/答案层预期；
  **行号坐标（`*_line_ids`、region 行号）与 `l1_fixture` 为 V2 表示，废弃**——V3 由
  Resolver 以 Semantic Reference 重定位。PDF 本体仍用户自有（§2）。

## 4. Knowledge / 题型种子（代码内嵌数据）

| 种子 | V2 定位 | V3 用法 |
|---|---|---|
| Question type seed | `backend/app/domains/question_type_seed/data.py`（`ALL_QUESTION_TYPE_SEEDS`，9 科 code 树，含 parent_code） | 作 annotation 语义 taxonomy（题型细分）参考；**canonical 权威 = DISPLAY_CONTRACT** |
| Knowledge tree seed | `backend/app/domains/knowledge/tree_seed/`（`ALL_NODES` / `ALL_KNOWLEDGE_TREES` / `CROSS_DISCIPLINARY_LINKS` / `SUBJECT_CODES` + `types`） | V3 knowledge_nodes seed（10 §6.7，optional，非 M1 阻塞）候选；需重编码/导出 |
| 题型树文档 | `Docs/reference/QUESTION_TYPE_TREE.md` | 业务语言参考 |

## 5. 非代码资产 / 已验收业务契约

- `Docs/reference/REQUIREMENTS_AND_SOLUTION.md` — 需求基线（00 §1/§8）。
- `Docs/reference/DISPLAY_CONTRACT.md` — 展示/题型契约 + canonical type（10/20/50 权威）；
  **待办：T/F↔A/B canonical 映射补丁（20 §8.4，段 G 前）**（已在 restart-prompt / Status /
  记忆三处登记）。
- `Docs/reference/V1_LESSONS.md` — V1 教训（00 §1/§8）。
- `Docs/reference/PRD.md` / `DICTIONARY.md` / `OCR_PROVIDER_POLICY.md` /
  `PADDLEOCR_API.md` / `UI.md` — 参考（见 §1 与 Docs 合并记录）。

## 6. 失败教训（只读引用，不移植）

- `Docs/reference/V1_LESSONS.md`（权威约束）；V2 根 `bugs.md`/`LOG.md` 与审计（V2 仓库，
  作失败样本库；50 §3"只读参考"）。V3 实现只服从 V3_SPEC。

## 7. 清点缺口 / 待裁决（实现前置）

| # | 缺口 | 建议 | 归属 |
|---|---|---|---|
| 1 | 样本 PDF 如何持有 | **已裁决（2026-09-05）：用户自有、可随时补充；V3 不复制、不依赖 V2 路径**。段 B / fixture 按需取用户样本 | 已决 |
| 2 | cloud OCR（PaddleOCR-VL）M1 启用 | **已裁决（2026-09-05）：M1 启用 cloud OCR（VL）**。实现前置：40 §2 **C 段 external 闸**（Gateway + audit + budget）先完成，B 段 seal 方能启用 cloud；token 由用户 `.env` 配置（不硬编码、不入 git）；本地 PP 作辅助。走 30 §16 external 闸 | 已决（30 §16 / 40 §2 C） |
| 3 | V2 golden 需以 V3 逐层重标 | 进 40 §2 D-E fixture 段时执行（50 §4.2），先不投入 | 40 §2 段 D/E |
| 4 | knowledge/题型 seed 是否 V3 化（optional） | M1 不阻塞；knowledge_nodes seed（10 §6.7）在后续派生阶段再做 | 延后 |
| 5 | T/F↔A/B canonical 映射 | 段 G 前补 DISPLAY_CONTRACT（已登记） | 20 §8.4 / 40 段 G |
| 6 | **corpus 覆盖缺口 + 物理卷无人工 answer 真值** | 15 份已迁但九科不均衡：物理朝阳无人工 answer（`quarantine/` 待人工核对）；大兴生物/朝阳英语/朝阳语文无 human golden；`exercise_2024`×2 PDF 断链（引用文件不在 V2 test/pdf） | 段 D/E 重标前补样（用户可补 PDF）；物理卷人工核对后方可出 quarantine。详见 `assets/annotations_src/` README 覆盖缺口 | 资产 / 40 §2 D/E |

## 8. 变更记录

### 2026-09-05（v0.1 建立）

- 按 50 §3 完成 V3 资产清点：外部能力（OCR 双源/本地 LLM/embedding）、真实 PDF ~40（9 科）、
  golden 8 份（real/contract）、knowledge/题型 seed（Python 内嵌）、非代码契约、失败教训
  全部定位；本体留 V2，V3 侧只引用；缺口 5 项列 §7。

### 2026-09-05 17:18:07（两项裁决）

- ① 样本 PDF：用户自有、可随时补充；V3 不复制、不依赖 V2 路径（§2/§7#1）。
- ② cloud OCR（PaddleOCR-VL）：**M1 启用**；前置 = 40 §2 C 段 external 闸先行，token 走
  `.env` 不硬编码（§7#2）。

### 2026-09-05 17:22:41（golden 甄别 + 迁移裁决）

- **甄别修正（§3 误判）**：V2 `golden/` 10 份三族——human 验收级 3 / 契约标注族 5 /
  机器草稿 2。`english_2026_real_golden`、`physics_2026_real_golden` 实为
  `0.1-draft` 草稿（V2 自标"不得直接用于验收"），原清点误记为 human 真值，已剔。
- **迁移裁决**：剔 2 份 draft，迁 15 份入 V3 `assets/annotations_src/`
  （real/3 + contract/5 + structure/7），JSON 原样保留；PDF 本体仍用户自有。
- **契约文档定位**：用户所指"协助 LLM 完成的契约文档" = 契约标注族 +
  `structure/` 卷面分组；承载复合题分组 / shared_material 归属 / canonical type /
  answer 出处，最贴近 V3 结构·语义重标（§3）。

### 2026-09-05 19:34:46（迁移物对抗性审查修正）

- **审查结论**：迁移大方向合规（50 §3 数据样本），但未达"去 V2 污染"声明：检出 2 阻断
  （B1 物理卷 contract 含 llm answer + needs_manual；B2 human 版 explanation 全
  llm_fallback 非真值）、1 高（README contract/ 定位名不副实）、3 中（exercise×2 PDF
  断链 + 旧码 type；覆盖虚高——大兴生物/朝阳英语/朝阳语文无 human 真值；数学卷双绑定）、
  3 低（缺逐份指纹/落位临时/exercise 分类）。
- **修正落地**：`physics_2026_chaoyang_contract_golden` 移 `assets/annotations_src/
  quarantine/`（禁作真值源）；`math_2026_chaoyang_contract_golden` 标
  `superseded_by_math_real_golden`；建 `MANIFEST.csv`（15 份 sha256_16 + answer/explanation
  来源 + needs_manual + PDF 绑定 + flag）；README v0.2 加可靠性分级与覆盖缺口；
  §7 新增 #6 缺口行。JSON 本体零改动。
