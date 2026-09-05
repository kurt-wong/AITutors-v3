# AI Tutor V3 — 标注源料（annotations_src）

> 定位：V2 `test/annotations/` 迁入的**重标源料 / 参考素材**，**非 V3 corpus**。
> 依 50 §4.2：须按 V3 逐层结构重标后方可作 corpus / fixture 预期；V2 行号坐标
> （`*_line_ids`、region 行号、`l1_fixture`）废弃，由 V3 Resolver 以 Semantic Reference
> 重定位。
> 版本：v0.2。迁移 2026-09-05 17:22:41（剔机器草稿迁 15 份）；**对抗性审查修正
> 2026-09-05 19:34:46**（隔离 LLM 污染、superseded、可靠性矩阵）。目录规范随 40 §2 段 A
> 定后归位。逐份指纹/来源分级见 `MANIFEST.csv`（sha256_16、answer/explanation 来源、
> needs_manual、PDF 绑定、flag）。

## 目录现状（15 份）

| 目录 | 份数 | 文件 | 状态 flag |
|---|---|---|---|
| `real/` | 1 | `math_real_golden.json`（human v4.0，answer 全 document_answer_table） | **ok_human_answer**（explanation 全 llm_fallback → 非真值） |
| `real/` | 2 | `english_exercise_2024.json`、`math_exercise_2024.json`（human v3.1） | **exercise_pdf_missing**（引用 PDF 不在 V2 test/pdf，断链） |
| `contract/` | 3 | `chemistry_2026_bashi`、`chinese_2026_chaoyang`、`english_2026_dongcheng_real`（dcv 0.4） | **ok_structure_demo**（answer 纯 document_answer_table、无 llm、3–11 题抽样） |
| `contract/` | 1 | `math_2026_chaoyang_contract_golden.json` | **superseded_by_math_real_golden**（同卷 human real 为 answer 权威；此份 expl 为 llm，仅结构参考） |
| `structure/` | 7 | `*.paper_structure.json`（schema_version 1，7 卷全绑定 V2 现存 PDF） | **structure**（卷面分组真值候选） |
| `quarantine/` | 1 | `physics_2026_chaoyang_contract_golden.json` | **quarantine**（含 llm answer + answer_needs_manual，禁作真值源） |

## 可靠性分级（第一性：answer 须人工单一真值源，50 §4.2 ↔ 20 §8.2）

- **answer 可作真值**（answer_source 全 `document_answer_table` / `document_inline_answer`，
  无 needs_manual）：`math_real_golden`、`english|math_exercise_2024`、chemistry/chinese/
  english_dongcheng 三份 contract（结构+答案，抽样）。
- **answer 禁作真值**：`quarantine/physics_2026_chaoyang_contract_golden`（q11
  answer_source=llm_fallback + needs_manual，q15 无答案）。物理朝阳卷**无人工 answer
  真值**，须人工核对后方可出 quarantine。
- **explanation 一律非真值**：凡 `explanation_source` 含 `llm_fallback`（math_real_golden
  8/8、math_chaoyang_contract 4/4、quarantine physics）的详解，均非人工，重标只参考、
  不作预期。
- **loader 纪律（段 D fixture 工具须遵守）**：只允许把上述"answer 可作真值"的 answer/
  题干文本入预期；llm 来源与 explanation 拒作真值。

## 剔除（未迁入，留在 V2）

- `english_2026_real_golden.json`、`physics_2026_real_golden.json`：V2 自标
  `annotator: dsh_draft_from_native_live`、`version 0.1-draft`、"不得直接用于验收"。
  机器草稿不入真值源。注意 `physics_2026_chaoyang_contract_golden`（已 quarantine）与
  `physics_2026_real_golden`（draft）**绑定同一物理 PDF**——物理卷整体无人工真值。

## 覆盖缺口与断链（2026-09-05 19:34 对抗审查登记）

- **物理朝阳**：无人工 answer 真值（见 quarantine）。
- **大兴生物 / 朝阳英语 / 朝阳语文**：无 human golden（朝阳英语 real 为已剔 draft；
  生物无 golden；语文 contract 3 题含写作无答）。
- **exercise×2 PDF 断链**：`english|math_exercise_2024.pdf` 不在 V2 test/pdf；V3 作
  corpus 题源需用户补同名 PDF，且其 question_type 用旧码（fill_blank/choice/fill/
  subjective）非 canonical，重标须经 DISPLAY_CONTRACT canonical 映射。
- 结论：当前 15 份**不足以支撑 50 §4.3 起步多样性判据**；补样归用户（PDF 可随时补）。

## 结构族速览

- human 验收级：`annotator: human_golden` + `version` + `expected_content{stem,options,answer,explanation}`
  + `expected_anchor{…_line_ids}`。文本真值可复用；行号坐标弃。
- contract：`display_contract_version: 0.4`，逐题 canonical `question_type` /
  `stem_region` / `shared_material`（含行号绑定）/ `answer_source`。
- paper_structure：`schema_version: 1`，`groups[{question_number, kind, question_types,
  sub_questions, shared_material}]`（required / forbidden）。

## 变更记录

- 2026-09-05 17:22:41 v0.1：剔 2 draft，迁 15 份入 real/3 + contract/5 + structure/7。
- 2026-09-05 19:34:46 v0.2（对抗性审查修正）：physics_chaoyang_contract 移 quarantine/；
  math_chaoyang_contract 标 superseded；建 MANIFEST.csv + 可靠性分级；README 定位与
  覆盖/断链如实登记。

## 关联资产

- PDF 本体：用户自有，V3 不复制（`Docs/reference/ASSET_INVENTORY.md §2`）。
- DISPLAY_CONTRACT / 契约上下文：`Docs/reference/`。
- corpus 版本化与逐层预期：`Docs/V3_SPEC/50 §4`。
