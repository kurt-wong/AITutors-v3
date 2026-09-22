# P04 Option-Level Evidence — Root-Cause Investigation

> **Status**: `EVIDENCE INVESTIGATION` / **NON-AUTHORITATIVE** / **OWNER DECISION INPUT**
> **Verdict status**: P04 = `OWNER DECISION REQUIRED`（本文件**不**关闭 P04，**不**修改 P04 Contract / Frozen Spec / Frozen Contract / Producer Contract / V3 Schema）
> **Scope**: 只读证据调查 + 一份调查报告。无生产代码 / 测试 / Schema / corpus / migration 变更。
> **Security**: 本报告无密钥；运行时凭据仍只在 `.env`。

---

## 0. Git / Change Manifest（结论前置，便于核对）

```text
Commit:            e3a59e2 — docs(investigation): investigate P04 option-level evidence root cause
                   （本报告主提交；其后一次 docs 提交回填本行 SHA，仍只改本文件）
Branch:            main（AITutors-v3，已推送 origin/main）
Changed files:     Docs/COORDINATION/CONTRACTS/P04-OPTION-EVIDENCE-ROOT-CAUSE-INVESTIGATION.md（本文件，新增，1212 行）
Production code changed:  NO
Schema changed:           NO
Frozen Spec changed:      NO
Frozen Contract changed:  NO
Producer Contract changed: NO
Corpus changed:           NO
Migration performed:      NO
P04 decision changed:     NO
```

**仓库落点说明（OBSERVED）**：任务书给出的产出路径 `Docs/COORDINATION/CONTRACTS/` 在三仓中的实际存在情况为——`AITutors-v3` **存在**（并已含 `P04-P08-EVIDENCE-INVESTIGATION.md`）；`AITutor-X` **不存在**（其下为 `Docs/30_CONTRACTS/` 等）；`Papers` 的 `Docs/COORDINATION/` **无 CONTRACTS 子目录**。故本报告落于 `AITutors-v3`，与既有 P04 证据调查同目录、同 git 历史线（`a7a6c50 docs(contracts): add P04+P08 evidence investigation`）。

**调查前基线（任务书第十四节前置命令）**：

| 仓库 | 分支 | `git log -5 --oneline` 顶端 | 调查前工作树 |
|---|---|---|---|
| `AITutor-X` | `main` | `5618b00 docs(x2.7): record int-full-01 full-corpus end-to-end integration run baseline` | 仅 untracked 报告/临时件（`contract_check.bin`、`index.html` 等），调查未触碰 |
| `AITutors-v3` | `main` | `a7a6c50 docs(contracts): add P04+P08 evidence investigation (non-authoritative)` | 仅 untracked 既有 Contract 草稿若干，调查未触碰 |
| `Papers` | `main` | `2b92898 DEC-049: D2/D3/D4 Decision Brief` | 只读，未写入 |

---

# 一、八个核心问题 — 结论先行

> 证据标签：**OBSERVED** = 本轮实测代码/数据 · **DERIVED** = 由 OBSERVED 算术/判定规则推出 · **HYPOTHESIS** = 尚未验证的推断。

### Q1. 945 个 choice questions 为什么没有 per-option evidence？

**结论（DERIVED，证据充分）**：**不是因为选项被表格/布局毁掉了，而是因为 Producer 的 schema 从未要求、也从未产出过 per-option 结构。** per-option 信息是在**最上游的设计/规格层就没有被建立**，而不是在中途某一层被丢失。

支撑（全部 OBSERVED）：

1. Producer LLM prompt 的输出 JSON schema 中，选项**只有一个字段** `"options_lines": [起始行号, 结束行号] 或 null`（`Papers/scripts/reslice_pipeline.py:255`）。schema 中**不存在**任何 per-label / per-option 字段。
2. `INTERVAL_ROLES`（`reslice_pipeline.py:155`）与 IR 侧 `SPAN_KEYS`（`Papers/scripts/resolver_reference.py:46-47`）都只有**整块区间角色**：`stem_lines / options_lines / answer_lines / explanation_lines / extra_lines / material_lines / questions_lines`。
3. **全量扫描 166 manifests / 4,609 units / prompt v2.1–v2.7 全部版本：含 `option*` 或 `label*` 且 ≠ `options_lines` 的 unit 字段数 = 0。**
4. 71 ADMITTED / 1,664 units 的 IR 与 manifest 双面 unit key 扫描：同类字段 = **0**。
5. 而 Producer **确实做得到** per-粒度切分——同一批 prompt 里 `answer_evidence` 就是逐 unit 的结构化对象（`type / lines / value / shared`）。**有能力做细粒度、但对选项只做整块**，说明这是 schema 设计取舍，不是能力上限。

因此 945 个「有 `options_lines` 但无 per-option evidence」的直接成因是同一句话：**Producer 契约里没有 per-option 这个概念。** 945 与 163 的差别只是「整块选项区有没有被圈出来」，与 per-option 无关。

### Q2. 其中有多少与 Question Options 的 table/layout 有关？

**结论（DERIVED）**：与「选项以表格/二维布局出现」有关的，**只有 20 个 / 945 = 2.11%**；与「多选项挤在同一源行（二维布局被线性化）」有关、且**因此使 line-range 无法表达 per-option** 的，是 **498 个 / 945 = 52.70%**。

| 布局类 | 数量 | 占 945 | 与 layout 的关系 | line-range 是否足够表达 per-option |
|---|---:|---:|---|---|
| `SAME_LINE_MULTI_OPTION`（≥2 个选项标签落在同一源行） | **498** | 52.70% | **是**——PDF/OCR 二维排版被线性化进单行 | **不够**，需 sub-line 级原语 |
| `PLAIN_ONE_LABEL_PER_LINE`（每选项标签独占非空行） | **387** | 40.95% | 否，纯文本顺序排列 | **足够**（386/387 可得每选项独立源行） |
| `IRREGULAR_LABELS`（标签缺失/夹杂 `---`/配图混排） | 40 | 4.23% | 部分 | 视子类 |
| `HTML_TABLE`（选项在 `<table>/<td>` 内） | **16** | 1.69% | **是**——表格 | **不够**，需 table-cell 原语 |
| `MD_TABLE`（Markdown 管道表格） | **0** | 0.00% | — | — |
| `IMG_DEGRADED`（选项为 `<img>`，正文无标签） | **4** | 0.42% | 是（图文） | **源文本无选项文字** |

**严格意义的「选项表格」= `HTML_TABLE` 16 + `MD_TABLE` 0 = 16 个（1.69%）**。若把「二维布局被线性化进单行」也计入广义 layout 影响，则为 **498 + 16 = 514 个（54.39%）**；但这 498 个的**选项文字完整可读、可确定性切分**，损失的只是 provenance 粒度，不是选项内容。

### Q3. 其中有多少与 Answer Key Table 有关？

**结论（DERIVED）**：**0 个。** Answer Key Table 与 per-option evidence 缺失**在机制上完全无关**。

决定性证据（OBSERVED）：在 945 个有 `options_lines` 的 block 上做「布局 × flags」交叉：

| layout | (无任何 flag) | `answer_number_mismatch` | `answer_table_unresolved` | 合计 |
|---|---:|---:|---:|---:|
| `SAME_LINE_MULTI_OPTION` | 278 | 16 | 204 | 498 |
| `PLAIN_ONE_LABEL_PER_LINE` | 197 | 20 | 170 | 387 |
| `IRREGULAR_LABELS` | 17 | 2 | 21 | 40 |
| `HTML_TABLE` | 4 | 0 | 12 | 16 |
| `IMG_DEGRADED` | 3 | 0 | 1 | 4 |
| **合计** | **499** | **38** | **408** | **945** |

**499 个 block 完全没有答案表问题（无任何 flag），其中 278 个是纯文本排列、197 个是一行一选项——这 499 个的 per-option evidence 同样是 0。** 只要「无答案表问题」的样本仍然 100% 缺 per-option evidence，答案表就不能被当作成因。

### Q4. `answer_table_unresolved=502` 与 choice option 定位问题到底是什么关系？

**结论（DERIVED）**：**没有因果关系；两者是彼此独立的两个问题，只是在同一 unit 上可以并存。** 并且 `answer_table_unresolved` 的真实语义**不是「答案表有问题」**，而是「**共享答案表的 cell 无法映射到本单元的 question_numbers**」。

交叉统计（OBSERVED，分母 = 1,664 IR units / 1,108 choice）：

| 集合 | 数量 | 比例 |
|---|---:|---|
| `answer_table_unresolved` 总数 | **502** | 502/1664 = 30.17% |
| choice ∩ `answer_table_unresolved` | **472** | P(flag\|choice) = 472/1108 = **42.60%** |
| choice − `answer_table_unresolved` | **636** | 57.40% |
| `answer_table_unresolved` − choice（非选择题） | **30** | P(choice\|flag) = 472/502 = **94.02%** |
| choice ∩ `answer_number_mismatch` | **44** | 44/1108 = 3.97% |
| choice − `answer_number_mismatch` | **1064** | 96.03% |
| `answer_number_mismatch` − choice | **47** | — |
| 两 flag 同时出现 | **0** | 互斥 |
| choice 有 `answer_evidence` | **0** | 0/1108 |
| choice 无 `answer_evidence` | **1108** | 100% |

并存率（DERIVED）：472/945 = **49.95%** 的「有 `options_lines` 的 choice」同时带 `answer_table_unresolved`；但布局类分布在有/无 flag 之间几乎不变（`PLAIN_ONE_LABEL_PER_LINE` 在三类中占比 39.5% / 52.6% / 41.7%），**flags 不预测布局类，布局类也不预测 flags**。

`answer_table_unresolved` 的机制（OBSERVED，`Papers/scripts/resolver_reference.py:78-106, 144-148`）：当 answer 区是**单行 `<table>`** 时调用 `parse_answer_table(ans_text[0], question_numbers)`，把该行所有 `<td>` 用 `TD_RE` 摊平成 `cells`，再二选一映射：

- 键位形态：每个 cell 能 `NUM_PREFIX_RE` 匹配出题号（形如 `"1. A"`）且 `len(keyed) == len(cells)` → `method="td_by_question_number"`，按题号取值；**成功 26 个**（`unresolved` 为空）。
- 位置形态：否则 `method="td_positional"`，**仅当 `len(cells) == len(question_numbers)`** 才逐位 zip；否则 `unresolved = list(question_numbers)`（**全数失败**）→ 打 `answer_table_unresolved`。**472 个**。

实测（OBSERVED）：`cells == question_numbers` 在 498 个带 `answers` 对象的 choice 中命中 **0**；`unresolved == question_numbers`（全失败）命中 **472**，与 flag 数精确相等。典型形态 `(td_positional, n_cells=88, n_qnums=1, n_unresolved=1) → 115 例`、`(30, 1, 1) → 78 例`。

**根因**：语料里的答案表是**多题共享**的整张表，且表头单元格（`题号` / `答案`）与题号格、答案格被一起摊平进同一个 `cells` 列表。样本 E-1 的源行 `L601` 实测 110 个 `<td>`，`cells[0:8] = ['题号','1','2','3','4','5','6','7']`，`cells[-4:] = ['D','A','C','B']`。于是「110 个 cell」对「本单元 1–3 个 question_numbers」——位置对齐**结构性不可能**。这与选项布局毫无关系。

`answer_number_mismatch` 的机制（OBSERVED，`resolver_reference.py:109-116`）：answer 区首行的数字前缀不在本单元 `question_numbers` 内就打 flag。91 个样本全部为「首行有数字前缀且该数字 ∉ question_numbers」。样本：`question_numbers=[51]`，而 `answer_text[0] = "1. 本题共10分。每空1分。"` —— 这是**评分标准行**被圈进了 `answer_lines`，其印刷小题号 `1.` 与全卷题号 `51` 不一致。这是**答案区切分 + 题号归一化**问题，同样与选项布局无关。

### Q5. option-level information 是在哪个 processing stage 丢失的？

**结论（DERIVED）**：**严格说不是「丢失」，而是「从未被建立」——落在 Producer prompt/schema 设计层（OCR 之后、manifest 产出之前）。**

逐层实证链路（OBSERVED，样本 B-1 全链回溯通过）：

```text
Original PDF                       [未取证：本轮未打开 PDF 二进制，见 §16]
   ↓ OCR / layout extraction
   ↓                            MinerU/mimo-x-pro-preview → 线性化 Markdown
Markdown / source representation  L11: "A. 禅让制 B. 内外服制 C. 分封制 D. 郡县制"
   ↓                            ★ 四选项在此层已并入同一行（二维布局丢失）
   ↓                            ★ 但 A/B/C/D 标签与四段文字 100% 完好
Question segmentation             reslice_pipeline.py PROMPT v2.x（LLM 只被要求填行区间）
   ↓                            ★★★ per-option 概念在此层就不存在（schema 只有 options_lines）
Producer annotation               manifest.units[].options_lines = [11, 11]
   ↓                            ★★ 确定性搬运，无信息再丢失（options_lines 一致率 945/945）
Producer IR                       provenance.source_lines.options_lines = [11,11]
                                  content.options_lines = ["A. 禅让制 B. … D. 郡县制"]
   ↓                            ★★ 仍无 per-option（SPAN_KEYS 无 per-option 角色）
V3 Consumer Boundary              ManifestUnit.options_lines = (11, 11)   ← 完整传到
   ↓
V3 annotation_adapter             有意不声明 content.options；登记
                                  known_gap=OPTION_LABEL_SPAN_UNAVAILABLE   ← 诚实不伪造
   ↓
V3 IRBuilder                      ir.py:256-259  required_roles["options"]=="required_for_choice"
                                  → "options missing for choice type" → semantic_status=incomplete
   ↓
Compiler / Gate / Admission       runner_b2.py:408-420 在 Gate 前跳过非 ready → 不达 Gate
```

**分层归属**：

| 层 | 是否造成 per-option 缺失 | 证据 |
|---|---|---|
| PDF 版式 | 部分（52.70% 的二维排版在此层被线性化） | 样本 B-1；但标签/文字完好 |
| OCR / Markdown 线性化 | 部分（同上：丢的是**列/格结构**，不是**选项内容**） | L11 单行四选项可读 |
| Question segmentation（prompt schema） | **主要（决定性）** | schema 只有 `options_lines`；4,609 units 零 per-option key |
| Producer annotation | 无额外损失 | manifest→IR `options_lines` 一致率 945/945 |
| Producer IR 序列化 | 无额外损失 | `SPAN_KEYS` 与 manifest 同粒度 |
| V3 Consumer Boundary | 无损失 | `ManifestUnit.options_lines` 完整 |
| V3 adapter / IRBuilder | **不制造，也不恢复**（策略性诚实失败） | `annotation_adapter.py:66-71` 注释明写「不再 fabricate」 |

**Case 1–5 归类（本报告核心根因分类）**：

| Case | 定义 | 命中量 | 占 945 |
|---|---|---:|---:|
| **Case 1** | Producer 已有，V3 Consumer 丢了 | **0** | 0% |
| **Case 2** | Producer 没有，但 source Markdown 已有足够信息 | **871** | **92.17%** |
| **Case 3** | Markdown 已丢 layout，PDF 仍有 | ≤13（仅「视觉左右列」这一层；标签/文字仍在 Markdown） | ≤1.38% |
| **Case 4** | 原始 PDF 也难可靠恢复 | **4** | 0.42% |
| **Case 5** | 不是 option 问题，而是 answer-table mapping 问题 | 另计 502+91 flags（与上表**不重叠计量**） | — |

Case 2 的 871 = 386（`PLAIN_ONE_LABEL_PER_LINE` 中每选项独占独立源行）+ 485（`SAME_LINE_MULTI_OPTION` 中可确定性字符切分出全部选项）。**这是绝对主导根因。**

### Q6. 当前问题主要属于哪一类？

**结论（DERIVED）**：**多因素共同造成，但主因明确且可排序。**

| 归因 | 权重（对 945） | 判定依据 |
|---|---:|---|
| **Producer capability gap**（schema/prompt 从未要求 per-option） | **主因，覆盖 ~100%** | 4,609 units / 7 个 prompt 版本零 per-option key；Producer Contract §2.1 把 `options_lines` 明文定义为「区域级」 |
| **source/layout loss**（二维排版被线性化） | **次因，影响 provenance 粒度而非内容** | 498/945 = 52.70% 需 sub-line 原语；但 485/498 可确定性切分 |
| **Consumer adapter gap** | **无**（0%） | adapter 边界 `options_lines` 完整抵达；adapter 的不声明是**遵守「禁止伪造」的正确行为**，非缺陷 |
| **V3 contract gap / Frozen Spec 不对称** | **放大器（阻断面）** | V3 Spec 要求 `content.options[].label` + `sp-<unit>.option.<label>`，Producer Contract 只要求区域级——**需求侧超前于供给侧** |
| **Frozen Spec gap** | **否**（就 per-option 而言 Spec 已定义） | `20_Document_Pipeline.md:168` 已定义 per-label options + source_span |

一句话：**供给侧只承诺了整块，需求侧冻结了逐标签；P04 卡在两份契约的粒度不对称上，而不是卡在 OCR 或表格上。**

### Q7. 要解决 P04，真正应该要求 Producer 提供什么 authority primitive？

**结论（DERIVED，作为决策输入而非裁决）**：**单一「source line range」原语不足**（Producer Contract §1.2 现规定「行号是唯一定位原语」）。证据支持的最小充分集是：

```text
option label            （必需；95%+ 场景为 A–D 单 ASCII 大写）
+ option text           （必需；须可从 source 确定性重建）
+ provenance ∈ { line_range | char_span_in_line | table_cell | image_region }   （多态，必需其一）
```

各原语的适用面（DERIVED）：

| 原语 | 覆盖 | 说明 |
|---|---:|---|
| `line_range`（1-based 闭区间） | **387 / 945 = 40.95%** | 一行一选项；现契约原语即可 |
| `char_span_in_line`（line + start_offset + end_offset） | **+485 = 871 / 945 = 92.17%** | 多选项同行必需；`runner_b3` 实验记录已预留 `start_offset`/`end_offset` 字段 |
| `table_cell`（table node + row/col） | **+16 = 887 / 945 = 93.86%** | HTML_TABLE 必需 |
| `image_region` / 显式 `degraded` | **+4 = 891 / 945 = 94.29%** | 图片化选项，须显式降级声明而非伪造 |
| 残差（标签缺失 / LaTeX 误检 / `---` 混排） | **54 / 945 = 5.71%** | 需更稳健标签识别或人工 review |

**同时必须决定**：Producer Contract §1.2 的「行号是唯一定位原语」是否要扩展为多态 provenance —— 这是**契约变更**，属 Owner 决策，本轮不改。

**并列决策项（OBSERVED，超出纯 provenance）**：V3 Spec §7.3 的 Question `dedup_key` = canonical question type + own stem + **own options**（按 label 排序，label 重复 fail-fast）。即 **option label 参与 Question identity**。P04 若不定，不仅阻断 ready-IR，也阻断 choice 题的 dedup_key 计算——**影响范围需 Owner 确认**（见 §17）。

### Q8. 现有证据是否足够让 Owner 正式关闭 P04？

**结论：不足以「关闭」；但足以「大幅收窄决策面」。** 根因侧证据已充分，缺的是**裁决输入**而非事实。

**已充分（可支撑裁决的部分）**：

- 945 的成因分类、各布局类精确计数、可恢复性实测（871/945 = 92.17%）
- 「答案表 ≠ 选项布局」的正交性证明（499 无 flag 样本仍全缺 per-option）
- `answer_table_unresolved` / `answer_number_mismatch` 的**真实语义与机制**（已消除「答案表有问题」的误读）
- information loss stage 定位（Producer prompt/schema 层，非 OCR 层、非 Consumer 层）
- Producer Contract 与 V3 Frozen Spec 的粒度不对称原文

**仍缺（关闭 P04 前必须补齐）**：

1. **Owner 对 Direction A vs B 的裁决**（Producer Contract §7.1 待确认清单第 1 项：A = DSH 增加 `options_labels: [{label, lines}]`；B = 维持区域级、V3 区域内检测）。这是**决策**，不是证据，本报告不能代裁。
2. **Authority primitive 多态化的契约变更令**：若采纳 sub-line / table-cell 原语，须先修订 Producer Contract §1.2（「行号是唯一定位原语」）——本轮未改。
3. **残差 5.71%（54 个）的 disposition 裁决**：是否允许 `degraded` 显式声明进入，还是必须全部可解析才放行。
4. **`answer_evidence` 契约符合性缺口的归属裁决**：Producer Contract §2.1 把 `answer_evidence` 列为「必需」，§2.5「缺失 → incomplete」；但 ADMITTED 71 全部为 prompt v2.1/v2.3，**该字段 100% 缺失**（见 §8）。这是否并入 P04，还是单列 P08/新议题，需 Owner 定。
5. **影响面确认**：P04 是否涵盖 Question `dedup_key` 阻断（V3 Spec §7.3），还是只涵盖 ready-IR/Gate 面。
6. **Direction B 的生产级验证**：本轮可恢复性实测基于 IR `content.options_lines` 确定性解析；既有实验 `gate_b2b1_result.json`（1,166 regions，structure_extracted 91.34%）跑在**更广语料**上，`consumer-report-b3.json`（38 manifests，resolved 527/548 = 96.17%）跑在 `reslice-p2-b1`。**尚未**在 71 ADMITTED 面上以生产口径复跑并签署。

---

# 二、Baseline Facts（OBSERVED）

## 2.1 证据基座

| 角色 | 本地路径 | HEAD @ 调查 |
|---|---|---|
| Producer / Preprocessing | `D:\Project\Papers` | `2b92898`（`DEC-049`） |
| Consumer / V3 | `D:\Project\AITutors-v3` | `a7a6c50` |
| Integration / Owner record | `D:\Project\AITutor-X` | `5618b00` |

| 工件 | 路径 | 角色 |
|---|---|---|
| Resolver IR | `Papers/data/resolver_ref_r52/resolver_ir.json` | Producer 语义 IR 面（88 records / 71 ADMITTED） |
| Interface census | `Papers/data/producer_interface_census.json` | unit 级 key 普查（4,609 units / 166 manifests） |
| Manifests | `Papers/Ocr-markdown/**/*.manifest.json` | 166 份 |
| Source Markdown | `Papers/Ocr-markdown/**/*.md` | provenance 回溯对象 |
| Producer prompt | `Papers/scripts/reslice_pipeline.py` | LLM 标注契约（`PROMPT_VERSION = "reslice-pilot-v2.7"`） |
| Producer IR builder | `Papers/scripts/resolver_reference.py` | manifest → IR |
| V3 boundary | `AITutors-v3/backend/scripts/preprocessing_consumer/` | 消费边界 |
| V3 IR / Gate | `AITutors-v3/backend/app/domains/compile/ir.py`、`gate/policy.py` | 生产代码 |
| Frozen Spec | `AITutors-v3/Docs/V3_SPEC/**` | 冻结规格 |
| Producer Contract | `AITutors-v3/Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT.md` | 跨系统输出契约 |

## 2.2 与任务书 OBSERVED FACTS 的复核（全部一致）

| 任务书给定 | 本轮实测 | 一致 |
|---|---|---|
| Producer corpus eligible = 172 | 本轮未重算 eligible 面（超出本议题）；IR records = 88，manifests = 166 | n/a |
| 71 ADMITTED IR | `dispositions: {ADMITTED: 71, REJECTED_QC_FAIL: 16, REJECTED_V1: 1}` | ✅ |
| choice-family Question = 1108 | 1108（single_choice 1042 + multiple_choice 66 + true_false 0） | ✅ |
| 其中 945 有 `options_lines` | 945 | ✅ |
| per-option label/text/line/evidence = 0 | 0（IR + manifest 双面 key 扫描） | ✅ |
| `answer_table_unresolved = 502` | 502 | ✅ |
| `answer_number_mismatch = 91` | 91 | ✅ |
| `answer_evidence` 在 71 ADMITTED face = 0 | 0（**且已查明原因**，见 §8） | ✅ |

补充（OBSERVED）：`true_false` 在本面为 **0** 个 unit，choice-family 实际只有 `single_choice` / `multiple_choice` 两类。

---

# 三、Corpus Sampling Method

## 3.1 全量统计（非抽样）

**Choice/option 统计、flags 交叉、布局分类、可恢复性测试全部在 71 ADMITTED / 1,664 units / 945 options block 上全量计算，无抽样外推。** 任务书「不允许用少数样本推断整个 945」据此满足。

## 3.2 样本级回溯（§9）的抽样规则

| 组 | 目标 | 抽样池规模 | 取样规则 |
|---|---|---:|---|
| A | 普通文本选项 | 387 | 取池内前 2 个（按 IR 顺序，无挑选） |
| B | 两列/多列布局 | 498 | 同上 |
| C | Markdown/HTML table | 16 | 同上 |
| D | 答案表明显存在且已解析 | 26 | 同上 |
| E | `answer_table_unresolved` = true | 472 | 同上 |
| F | 有 `options_lines` 但无法建立 option-level evidence | 207 | 同上 |

**无「代表性手挑」**——一律取池内顺序前 N 个，避免挑选偏差。样本 A/B/F 出自同一源文档并非刻意，而是该文档位于 IR 顺序前端。

## 3.3 布局分类判定规则（可复现）

对每个 block 的 `content.options_lines` 文本：

```text
1. 匹配 <table|<tr|<td>              → HTML_TABLE
2. 匹配行首 | 或 ｜（全角）           → MD_TABLE
3. 任一非空行检出 ≥2 个选项标签        → SAME_LINE_MULTI_OPTION
4. 含 <img>/<div> 且去重标签 < 4      → IMG_DEGRADED
5. 每个非空行恰 1 标签 且 去重标签 ≥ 4 → PLAIN_ONE_LABEL_PER_LINE
6. 其余                                → IRREGULAR_LABELS
```

选项标签正则（含全角字母与中英文标点）：

```text
(?:(?<=^)|(?<=[\s　（(\[【《<>"'|｜/:：]))([A-Ha-hＡ-Ｈ])\s*[.．、)）:：]\s*
全角 Ａ–Ｈ 归一为 A–H 后参与比对。
```

---

# 四、Choice / Option Statistics

## 4.1 Choice × options_lines

```text
choice-family total                     1108
 ├─ options_lines present                945   (85.29%)
 └─ options_lines absent                 163   (14.71%)
      ├─ composite_question               99   （options 落在 questions_lines 区内）
      └─ standalone_question              64
non-choice units                         556
 └─ with options_lines                     0   (0%)
```

OBSERVED：IR `provenance.source_lines.options_lines` 与 manifest `options_lines` 的一致性 = **945/945，零分歧**。163 个缺失中 99 个 manifest **连 key 都没有**（composite schema 无此字段），64 个 key 存在但为 `null`。

## 4.2 Choice × option-level evidence（字段存在性）

| 字段 | available |
|---|---:|
| option **label** | **0** |
| option **text**（结构化字段） | **0** |
| option **line**（per-option） | **0** |
| option **evidence** | **0** |
| **none of the above** | **1108**（全部 choice） |

**unit 级 key 全量扫描（OBSERVED，1,664 IR units + 对应 manifest units）**：含 `option` 或 `label` 子串且 ≠ `options_lines` 的字段种类数 = **0**。

**全语料扫描（OBSERVED，166 manifests / 4,609 units）**：同类字段数 = **0**。

> 注意区分两件事：**字段为 0** ≠ **内容为 0**。选项文字在 `content.options_lines` 里 100% 存在，只是没有被结构化切开、也没有 per-option provenance。

## 4.3 Choice × layout / table evidence（全量 945）

```text
plain text（一行一选项）        PLAIN_ONE_LABEL_PER_LINE    387   40.95%
multi-column linearized        SAME_LINE_MULTI_OPTION      498   52.70%
html table                     HTML_TABLE                   16    1.69%
markdown table                 MD_TABLE                      0    0.00%
layout-derived / OCR-degraded  IMG_DEGRADED                  4    0.42%
mixed / irregular              IRREGULAR_LABELS             40    4.23%
unknown                                                  0
────────────────────────────────────────────────────────────────────
合计                                                          945  100.00%
```

标签可读性（OBSERVED）：去重标签集 = `{A,B,C,D}` 的 block 为绝大多数；`{}`（完全检不出标签）22；`{A,B,C}` 等残缺集 12；含 E/F 的 3。**945 中无 Markdown 管道表格**。

`IRREGULAR_LABELS` 40 个的构成（OBSERVED）：夹 `---` 水平线 + 无标签续行 20；配图 + 无标签续行 9；配图 + `---` + 无标签续行 5；仅无标签续行 4；标签集残缺 2。

## 4.4 可恢复性实测（DERIVED/OBSERVED）

| 测试 | 池 | 成功 | 率 |
|---|---:|---:|---:|
| TEST 1：`SAME_LINE_MULTI_OPTION` 用**字符偏移**确定性切分出全部选项 | 498 | **485** | **97.39%** |
| TEST 2：`PLAIN_ONE_LABEL_PER_LINE` 每选项得**独立源行** | 387 | **386** | **99.74%** |
| **合计可得 per-option label+text** | 945 | **871** | **92.17%** |

TEST 1 的 13 个失败全部是**标签误检**而非布局丢失——典型如 LaTeX `$ \ddot{C} $` 被正则误判为标签 `C`、`A 的化学反应速率` 中的 `A` 被误判。属识别器稳健性，可通过排除数学模式/中文紧邻规则修复。

独立佐证（OBSERVED，V3 既有实验工件，非本轮产出）：

| 工件 | 语料 | 结果 |
|---|---|---|
| `gate_b/gate_b2b1_result.json` | 1,166 option regions | `structure_extracted = 1065 (91.34%)`、`label_sequence_valid = 1061 (90.99%)` |
| `preprocessing_consumer/consumer-report-b3.json` | 38 manifests（`reslice-p2-b1`） | `{"resolved": 527, "no_labels": 16, "incomplete": 5}` = 96.17% resolved |

---

# 五、Question Options Layout Investigation（Owner 假设 A）

## 5.1 假设原文

> 「A/B/C/D 选项本身是否以表格、二维布局、列布局等形式出现在原始 PDF / OCR / Markdown 中？」

## 5.2 分层回答

| 层 | 选项是否以表格/二维/列布局出现 | OBSERVED 证据 |
|---|---|---|
| **原始 PDF** | **本报告未直接取证** | 见 §16 Remaining Uncertainty。`maintainess/PDF` 与 `original/` 存在，但本轮未打开 PDF 二进制核对版面。**不得据此断言 PDF 侧结论。** |
| **OCR / 解析结果（Markdown）** | **是，且以两种形态被线性化** | ① 52.70% 多选项挤入同一源行；② 1.69% 保留为 `<table>/<td>` |
| **Markdown** | **部分保留** | HTML 表格保留 `<td>` 边界（16）；纯列排版的列边界**已丢失**（498）；Markdown 管道表格 0 |
| **source line 能否建立 option-level provenance** | **40.95% 可以；52.70% 不可以（需 sub-line）** | TEST 2 / TEST 1 |
| **在哪一层丢失列/格结构** | **OCR → Markdown 线性化层**（列边界）；**Producer prompt 层**（per-option 概念） | 见 §9 链路 |

## 5.3 关键澄清：布局损失 ≠ 选项内容损失

样本 B-1（源文件 `Ocr-markdown/会考/历史/2018北京夏季高中会考历史（教师版）(1).md`，`options_lines=[11,11]`，**实测源行逐字回读**）：

```text
L11: A. 禅让制 B. 内外服制 C. 分封制 D. 郡县制
```

- 四个标签 A/B/C/D **全部完好**
- 四段文字 **全部完好**
- 丢失的只是「谁在左列、谁在右列」的**视觉列关系**
- 一个从标签边界切分的确定性算法即可还原四选项 —— 实测 498 个同类 block 中 **485 个（97.39%）**可完全还原

**因此 Owner 假设 A 的答案是**：选项确实大量以二维/列布局出现并被线性化（52.70%），**但这只让「source line range」这一种 provenance 原语失效，绝不构成 per-option evidence 无法建立的理由。** 真正让 per-option evidence 为 0 的，是 Producer 从未实现 option slicing（Case 2 = 92.17%）。

## 5.4 「完整定位」的真实形态（任务书第九节）

**「一个 option = 一个 source line」这个默认假设在本语料上是错的。** 实测真实形态：

```text
形态 1（40.95%）  A → L22      B → L24      C → L26      D → L28     每选项独立源行
形态 2（52.70%）  A → L11[0:5) B → L11[6:11) C → L11[12:17) D → L11[18:23)  同行字符偏移
形态 3（1.69%）   A → <table> cell(0,0)  B → cell(0,1)  C → cell(1,0)  D → cell(1,1)  表格单元格
形态 4（0.42%）   A → image region       （正文无选项文字）
形态 5（4.23%）   混合：标签行 + 无标签续行 + `---` + 配图
```

实测还存在**跨行选项**（选项正文续到下一行、下一行无标签）——见样本 F-1。因此即使在形态 1 中，也可能出现 `A → L289-L290`（含空行）这类区间。

---

# 六、Answer Key Table Investigation（Owner 假设 B）

## 6.1 与 §5 严格分离

本节只讨论**答案表**（题号→答案 的对照表），**不涉及**题目选项。

## 6.2 答案表是否存在？—— 存在，且有两种 cell 形态

**触发条件（OBSERVED，`resolver_reference.py:142-144`）**：`answer_lines` 是**单行**且该行含 `<table`。满足的 unit = **528**，全部成功建出 `answers` 对象（其中 choice 498 + 非 choice 30）。

**`answers` 对象结构（OBSERVED）**：

```text
{"cells": [...],     # 该行所有 <td> 的纯文本，摊平成一维列表
 "method": "td_by_question_number" | "td_positional",
 "answers": {qnum: value},   # 成功映射结果
 "unresolved": [qnum, ...]}  # 映射失败的题号
```

**两种 cell 形态（OBSERVED，实测源行）**：

| 形态 | 源行实测 | `method` | 结果 |
|---|---|---|---|
| **键位形态** | `cells = ["1. A","2. A","3. C","4. A",…]`（每格自带题号前缀） | `td_by_question_number` | **成功 26** |
| **表头网格形态** | `cells = ["题号","1","2",…,"答案","A","B",…]`（表头格与数据格一起摊平） | `td_positional` | **全失败 472** |

样本 E-1 源行实测（`会考/地理/2018北京春季高中会考地理（教师版）(1).md` **L601**，行长 6,920 字符）：

```text
L601 head : <table border=1 …><tr><td …>题号</td><td …>1</td><td …>2</td>…
td cell count : 110
cells[0:8]    : ['题号', '1', '2', '3', '4', '5', '6', '7']
cells[-4:]    : ['D', 'A', 'C', 'B']
```

样本 D-1 源行（同表另一形态）：

```text
cells[0:8] : ["1. A", "2. A", "3. C", "4. A", "5. D", "6. C", "7. D", "8. B"]
answers map: {"1": "1. A", "2": "2. A", "3": "3. C"}   →  resolved
```

## 6.3 答案表属于 Question options 还是独立 Answer Evidence？

**结论（DERIVED）**：**独立的 Answer Evidence，绝不属于 Question options。**

- 载体字段不同：答案表落在 `answer_lines` / IR `answers`；选项落在 `options_lines` / IR `content.options_lines`
- 触发条件不同：答案表解析只看 `answer_lines` 单行 `<table`（`resolver_reference.py:142-144`）；选项与该判定**完全无交集**
- Producer prompt 里二者分属不同规则：`options_lines` 在输出 JSON 的 unit 字段；`answer_evidence` 是独立对象（`type ∈ {answer_lines, inline_in_explanation, answer_table, range_string, absent}`）
- Producer Contract §2.1 分列两行：`options_lines | choice 类型必需 | …——区域级` 与 `answer_evidence | 必需 | {type:"answer_table", …}`

**任务书警告「严禁把 Question Options Table 与 Answer Key Table 混为一谈」已被证据支持**：两者在 schema、触发条件、失败机制上均无共用。

## 6.4 答案表映射失败的根因（DERIVED）

`parse_answer_table` 把**整张多题共享答案表**的全部 cell，拿来与**单个 unit 的 question_numbers**（1–3 个）做对齐：

- 键位形态要求 `len(keyed) == len(cells)` —— 表头网格形态下 `题号`/`答案` 格不匹配 `NUM_PREFIX_RE`，`keyed` 为空 → 落入位置分支
- 位置分支要求 `len(cells) == len(question_numbers)` —— 110 cells vs 1–3 qnums，**恒不成立** → `unresolved = 全部 question_numbers`

实测交叉验证（OBSERVED）：

```text
cells == question_numbers 命中        : 0 / 498
cells != question_numbers            : 498 / 498
unresolved == question_numbers(全失败): 472 / 498   ← 精确等于 answer_table_unresolved 的 choice 数
典型 (td_positional, 88 cells, 1 qnum, 1 unresolved) : 115 例
典型 (td_positional, 30 cells, 1 qnum, 1 unresolved) :  78 例
```

**语义修正**：`answer_table_unresolved` **不等于「答案表有问题」**。答案表文本完整、cell 全部保留（`answers.cells` 完好）。失败的是**「共享答案表 cell → 单元 question_number」的映射**，且这是 `resolver_reference.py` 「两者推不出的题号标 unresolved,不猜测」这条**正确反伪造策略**在**粒度不匹配**下的必然结果。

独立佐证（OBSERVED，`gate_b/gate_b2b2_result.json`）：2,282 answer targets 中 `extraction_success = 1245 (54.56%)`；**shared 区 `shared_extraction_rate = 30.16%` vs 非 shared `68.48%`** —— 共享答案区正是难点，与上述机制吻合。

---

# 七、`answer_table_unresolved` Cross Analysis

## 7.1 四向交叉（OBSERVED，分母见列）

| 集合 | 数量 | 比例 |
|---|---:|---|
| `answer_table_unresolved` 全量 | **502** | 502/1664 = 30.17% |
| **choice ∩ flag** | **472** | P(flag\|choice) = 472/1108 = **42.60%** |
| **choice − flag** | **636** | 57.40% |
| **flag − choice** | **30** | P(choice\|flag) = 472/502 = **94.02%** |

## 7.2 flag × options_lines × layout（OBSERVED）

见 §Q3 矩阵。要点重述：

| | (无 flag) | `answer_number_mismatch` | `answer_table_unresolved` |
|---|---:|---:|---:|
| 945 中有 `options_lines` | 499 | 38 | 408 |
| 其中 `options_lines` 存在率 | 499/592 = **84.29%** | 38/44 = **86.36%** | 408/472 = **86.44%** |

**三类的 `options_lines` 存在率在 84.3%–86.4% 之间，几乎相同（极差 2.15 个百分点）。** 这是「答案表问题与选项定位正交」的定量证据。

## 7.3 `unresolved` 字段形态（OBSERVED）

| 形态 | 数量 | 含义 |
|---|---:|---|
| `list(len=1)` | 437 | 单题 unit 全失败 |
| `list(len=2)` | 20 | 2 题 composite 全失败 |
| `list(len=3)` | 13 | 3 题 composite 全失败 |
| `list(len=4)` | 2 | 4 题 composite 全失败 |
| `list(len=0)` | 26 | **成功**（`td_by_question_number`） |
| 无 `answers` 对象 | 610 | 未触发单行 `<table` 条件 |

`list(len>=1)` 合计 472 = `answer_table_unresolved` 的 choice 数，**精确吻合**。

---

# 八、`answer_number_mismatch` Cross Analysis + `answer_evidence`

## 8.1 四向交叉（OBSERVED）

| 集合 | 数量 | 比例 |
|---|---:|---|
| 全量 | **91** | 91/1664 = 5.47% |
| **choice ∩ flag** | **44** | 44/1108 = **3.97%** |
| **choice − flag** | **1064** | 96.03% |
| **flag − choice** | **47** | P(choice\|flag) = 44/91 = 48.35% |
| 与 `answer_table_unresolved` 同现 | **0** | 互斥 |

choice 内 44 个的 `options_lines`：present **38** / absent **6**（86.36%，与总体一致）。

## 8.2 机制与真实语义（OBSERVED）

`resolver_reference.py:109-116`：`answer_lines` 首行 `NUM_PREFIX_RE` 命中的数字 ∉ `question_numbers` → flag。91/91 全部满足「首行有数字前缀 且 该数字 ∉ question_numbers」。

样本（OBSERVED）：

```text
question_numbers = [51]   answer_text[0] = "1. 本题共10分。每空1分。"
question_numbers = [52]   answer_text[0] = "2. 本题共10分。每空1分。第（3）小题选择填空2分…"
question_numbers = [53]   answer_text[0] = "3. 本题共10分。每空1分。"
question_numbers = [54]   answer_text[0] = "4. 本题共10分。每空1分。第（2）小题…"
```

**语义修正**：这不是「答案号错」，而是 **`answer_lines` 被误锚到【评分标准】块**（印刷小题号 `1./2./3.`）而非答案本体，其小题号与全卷归一化题号（51/52/53/54）不一致，于是被 flag。属**答案区切分 + 题号归一化（`printed_number` vs `question_numbers`）**问题，与选项布局、与答案表映射**均无关**。

## 8.3 与 P04 的关系

**无因果关系。** 44 个命中里 38 个有 `options_lines`，其布局分布与总体一致。该 flag 不预测 per-option evidence 的有无（后者恒为 0）。

## 8.4 `answer_evidence` Cross Analysis（任务书第四节第 6 项）

| 项 | 数量 |
|---|---:|
| choice **with** `answer_evidence` | **0** |
| choice **without** `answer_evidence` | **1108** |
| IR units with `answer_evidence` key | **0** |
| 71 ADMITTED 的 manifest units with `answer_evidence` key | **0** |

**层级与原因（OBSERVED，已查明）**：`answer_evidence` 是 **unit 级 manifest 字段**（对象 `{type, lines, value, shared}`），**不进 IR unit**（IR 的 unit key 里本就没有它）。全语料 28 manifests / 906 units 有该 key，**全部落在 `reslice-p2-*` 目录，与 ADMITTED 71 零交集**。

按 prompt 版本切分（OBSERVED，166 manifests 全量）：

| prompt_version | files | files 带 AE | units | units 带 AE |
|---|---:|---:|---:|---:|
| `reslice-pilot-v2.1` | 64 | 0 | 1,969 | 0 |
| `reslice-pilot-v2.3` | 74 | 0 | 1,734 | 0 |
| `reslice-pilot-v2.4` | 2 | 2 | 56 | 56 |
| `reslice-pilot-v2.5` | 6 | 6 | 127 | 127 |
| `reslice-pilot-v2.6` | 8 | 8 | 272 | 272 |
| `reslice-pilot-v2.7` | 12 | 12 | 451 | 451 |

**结论（DERIVED）**：`answer_evidence` 是 **prompt v2.4 才引入**的字段（`reslice_pipeline.py:159` 注释：`P2.1-c 答案证据类型词表(prompt v2.4;…)`），v2.4 起 **100% unit 覆盖**。ADMITTED 71 全部产自 v2.1（38 files）/ v2.3（33 files），**早于该字段引入**，故为 0。

**这构成一处 Producer Contract 符合性缺口**（OBSERVED）：Producer Contract §2.1 把 `answer_evidence` 列为「**必需**」，§2.5 规定「answer_evidence 缺失 → answer role 未解析 → incomplete」；而 ADMITTED 71 的实际产出 100% 缺失。V3 消费侧**已就绪**（`manifest_reader.py:44-46, 94-96` 建有 `answer_evidence_type/lines/value` 字段，`runner_b2._answer_span` 亦有 `answer_evidence_lines` fallback）。**属 Case 1 的镜像**：Consumer 有槽位、Producer 无数据。是否并入 P04 由 Owner 裁（见 §17）。

---

# 九、Source-to-IR Provenance Trace

## 9.1 实证回读（OBSERVED — IR 切片 == 真实源文件行）

对 6 处切片做**源文件逐字回读**，全部吻合：

```text
A-1 stem     会考/历史/2018…历史（教师版）(1).md  L20
             "3.《汉书》记载：\"武帝施主父之册……据此判断汉武帝实行的是"
A-1 options  同文件 L22–L28
             L22 "A. 宗法制"   L23 ""   L24 "B. 郡国并行制"   L25 ""
             L26 "C. 推恩令"   L27 ""   L28 "D. 行省制度"
A-1 answer   同文件 L651   "3. 【答案】C"
B-1 options  同文件 L11    "A. 禅让制 B. 内外服制 C. 分封制 D. 郡县制"
F-2 options  同文件 L301–L307
             L301 "A. 迪亚士" … L305 "C. 哥伦布" L307 "D 麦哲伦"   ← D 后缺点号
C-1 options  合格考/化学/2020…化学（第一次）(1).md L19
             "<table border=1 …><tr><td …>A. 医用酒精</td><td …"
E-1 answer   会考/地理/2018…地理（教师版）(1).md L601（110 个 <td>，见 §6.2）
```

**证明**：Producer IR 的 `content.*` 切片与 `provenance.source_lines.*` 行区间是**真实、可回溯、无加工**的。provenance 链条在「源行」这一粒度上是完好的。

## 9.2 典型失败样本的完整链路（Case 2 主导型）

样本 **B-1**（`unit_id=Q1`, `question_numbers=[1]`, `single_choice`）：

| 阶段 | 状态 | 证据 |
|---|---|---|
| Original PDF | 未知（未取证） | — |
| OCR / layout extraction | **二维列布局 → 单行文本**（列边界丢失） | 产出 `L11` |
| Markdown | A/B/C/D 标签与四段文字**完整** | 实测回读 |
| Question segmentation（prompt schema） | **per-option 概念不存在**，只要求 `options_lines: [11,11]` | `reslice_pipeline.py:255` |
| Producer annotation | `options_lines = [11, 11]` | manifest unit |
| Producer IR | `provenance.source_lines.options_lines=[11,11]`；`content.options_lines=["A. 禅让制 B. …"]` | `resolver_reference.py:46-47, 119-125` |
| V3 Consumer Boundary | `ManifestUnit.options_lines = (11, 11)` | `manifest_reader.py:38, 88` |
| V3 IRBuilder | 无 `content.options[].label` → `incomplete` | `ir.py:256-259` |
| Gate / Admission | `runner_b2.py:408-420` 在 Gate 前跳过 | 未达 Gate |

**丢失层定位**：`Question segmentation`（prompt schema）——因为在此层之前，A/B/C/D 的身份与文字一直在；在此层之后，只是原样搬运整块。

## 9.3 Case 3 型样本

样本 **F-2**（`Q29`, `options_lines=[301,307]`）：`L307 "D 麦哲伦"`（`D` 后缺点号）。属 OCR 标点退化 → 标签识别残缺（检出 `{A,B,C}`）。**列布局已丢，但文字仍在**；需要更稳健的标签识别（允许 `D ` 无点号），而非新的 provenance 原语。

## 9.4 Case 4 型样本

样本（`IMG_DEGRADED`，`options_lines=[71,71]`，合格考化学）：

```text
L71: <div style="text-align: center;"><img src="../../_imgs/2020北京高中合格考化学（第一次）（教师版）(1)/img_in_image_box_185_1020_998_1263.jpg" alt="Image" width="68%" /></div>
```

选项文字**不在 Markdown 文本层**，只存在于图片。此为真正 Case 4（需图片 OCR 才可能恢复），占比 4/945 = 0.42%。

## 9.5 Case 1 检验

**option 维度：Case 1 = 0。** Producer 双面（manifest + IR）都无 per-option，Consumer 不可能「丢」掉不存在的东西。Boundary 到 `ManifestUnit` 的 `options_lines` 传递实测完好。

**answer_evidence 维度：存在 Case 1 的镜像**——V3 `ManifestUnit` 已建 `answer_evidence_*` 三个字段（`manifest_reader.py:44-46`），Producer 在 ADMITTED 71 上无数据可填。槽位在、数据无。

## 9.6 样本组 A–F 全记录（任务书第五节）

每条均含：source document / unit identity / question type / options_lines / source line range / raw representation / layout representation / answer representation / producer artifact / flags / basis / answer_evidence / option-level evidence。**源行已逐字回读验证（§9.1）**。

### Sample Group A — 普通文本排列（池 387）

**A-1 / A-2** · source: `Ocr-markdown/会考/历史/2018北京夏季高中会考历史（教师版）(1).md` · manifest: `Ocr-markdown/reslice-batch-C/会考/历史/…(1).manifest.json` · `source_content_sha256 = d4917437…62e714`

| 字段 | A-1 | A-2 |
|---|---|---|
| unit_id / printed_number / question_numbers | `Q3` / `[3]` / `[3]` | `Q4` / `[4]` / `[4]` |
| unit_type / original_question_type | `standalone_question` / `single_choice` | 同左 |
| options_lines | `[22, 28]` | `[32, 38]` |
| stem / answer / explanation lines | `[20,20]` / `[651,651]` / `[653,653]` | `[30,30]` / `[655,655]` / `[657,659]` |
| layout class | `PLAIN_ONE_LABEL_PER_LINE` | 同左 |
| raw options region | `L22 "A. 宗法制"` … `L28 "D. 行省制度"`（每选项间夹空行） | `L32 "A. 知县"` … `L38 "D. 工部侍郎"` |
| answer representation | `answer_text=["3. 【答案】C"]`；`answers=null` | `["4. 【答案】B"]`；`answers=null` |
| flags | `[]` | `[]` |
| basis / basis_evidence | `printed_as_is` / `"题干首行印刷题号 L20"` | `printed_as_is` / `"题干首行印刷题号 L30"` |
| printed_provenance | `source_line` | `source_line` |
| answer_evidence | **KEY ABSENT**（prompt v2.1/v2.3） | 同左 |
| option-level evidence | **NONE** | **NONE** |
| prompt_version | `reslice-pilot-v2.1` / `v2.3`（同批） | 同左 |

**判读**：四个选项各占独立源行，**line-range 原语完全足够**，Producer 却未产出 per-option 行区间。纯 **Case 2**。

### Sample Group B — 两列/多列布局（池 498）

**B-1 / B-2** · source / manifest 同 A 组 · `source_content_sha256 = d4917437…62e714`

| 字段 | B-1 | B-2 |
|---|---|---|
| unit_id / printed_number / question_numbers | `Q1` / `[1]` / `[1]` | `Q2` / `[2]` / `[2]` |
| unit_type / original_question_type | `standalone_question` / `single_choice` | 同左 |
| options_lines | `[11, 11]` | `[18, 18]` |
| stem / answer / explanation lines | `[9,9]` / `[637,637]` / `[639,641]` | `[13,15]` / `[643,643]` / `[645,649]` |
| layout class | `SAME_LINE_MULTI_OPTION` | 同左 |
| raw representation | `L11 "A. 禅让制 B. 内外服制 C. 分封制 D. 郡县制"` | `L18 "A. 秦朝 B. 汉朝 C. 宋朝 D. 明朝"` |
| answer representation | `["1. 【答案】C"]`；`answers=null` | `["2. 【答案】C"]`；`answers=null` |
| flags / basis / printed_provenance | `[]` / `printed_as_is` / `source_line` | 同左 |
| answer_evidence / option-level evidence | **KEY ABSENT** / **NONE** | 同左 |

**判读**：四选项共用**同一行号**，line-range 不可区分；但标签与文字完好，字符偏移切分可完全还原。属 **Case 2 + 局部 Case 3（仅视觉列关系）**。

### Sample Group C — Markdown/HTML table（池 16；`MD_TABLE` = 0）

**C-1 / C-2** · source: `Ocr-markdown/合格考/化学/2020北京高中合格考化学（第一次）（教师版）(1).md` · `source_content_sha256 = f6b13d6a…ac4fe61`

| 字段 | C-1 | C-2 |
|---|---|---|
| unit_id / question_numbers | `Q1` / `[1]` | `Q14` / `[14]`（`printed_number = None`） |
| unit_type / oqt | `andalone_question`* / `single_choice` | `standalone_question` / `single_choice` |
| options_lines | `[19, 19]` | `[105, 105]` |
| stem / answer / explanation | `[16,16]` / `[378,380]` / `None` | `[102,102]` / `[536,536]` / `[538,540]` |
| layout class | `HTML_TABLE` | `HTML_TABLE` |
| raw representation | `<table border=1 …><tr><td …>A. 医用酒精</td><td …` | `<table …><tr><td …></td><td …`（首格为空） |
| answer representation | `answer_text[0]` 实为**解析段落**；`answers=null` | `["14.【答案】D"]`；`answers=null` |
| flags / basis / printed_provenance | `[]` / `printed_as_is` / `source_line` | `[]` / `unverified` / `unknown` |
| answer_evidence / option-level evidence | **KEY ABSENT** / **NONE** | 同左 |

\* `unit_type = "andalone_question"` 为源数据异常值（疑 `standalone_question` 截断），已记入 §16 U-10，本轮不修。

**判读**：选项在 `<td>` 内，`<td>` 边界**已保留**在 Markdown 中，可用 `table_cell` 原语还原；**不是「表格毁掉选项」**。C-1 的 `answer_text` 误含解析段落，属答案区切分问题（与 T9 同类），与选项无关。

### Sample Group D — 答案表明显存在且已解析（池 26）

**D-1 / D-2** · source: `Ocr-markdown/合格考/政治/2021北京高中合格考政治（第一次）（教师版）(1).md` · `source_content_sha256 = 440592b5…449f367c`

| 字段 | D-1 | D-2 |
|---|---|---|
| unit_id / question_numbers | `U1-3` / `[1,2,3]` | `Q4` / `[4]` |
| unit_type / oqt | `composite_question` / `single_choice` | `standalone_question` / `single_choice` |
| options_lines | `None`（composite，选项在 `questions_lines` 内） | `[47, 71]` |
| stem / answer / explanation | `None` / `[477,477]` / `None` | `[41,45]` / `[477,477]` / `None` |
| layout class | `IRREGULAR`（无 options block） | `SAME_LINE_MULTI_OPTION` |
| raw options representation | — | `L47`–`L71`（25 行：配图 `<img>` + `<div>` 说明文字混排） |
| **answer representation** | **`answers.method = td_by_question_number`**；`n_cells = 30`；`answers map = {"1":"1. A","2":"2. A","3":"3. C"}`；`unresolved = []` | 同表：`answers map = {"4":"4. A"}`；`unresolved = []` |
| `answers.cells[0:8]` | `["1. A","2. A","3. C","4. A","5. D","6. C","7. D","8. B"]` | 同左 |
| flags | `[]` | `[]` |
| basis / printed_provenance | `unverified` / `unknown` | `printed_as_is` / `source_line` |
| answer_evidence / option-level evidence | **KEY ABSENT** / **NONE** | 同左 |

**判读**：答案表 cell 为**键位形态**（`1. A` 带题号前缀），`td_by_question_number` 映射**成功**。这正是 §6.2 的成功形态——证明答案表本身**可解析**，失败的只是表头网格形态下的粒度对齐。

### Sample Group E — `answer_table_unresolved` = true（池 472）

**E-1 / E-2** · source: `Ocr-markdown/会考/地理/2018北京春季高中会考地理（教师版）(1).md` · `source_content_sha256 = 3f4a7a82…2c33297d`

| 字段 | E-1 | E-2 |
|---|---|---|
| unit_id / question_numbers | `U1-2` / `[1,2]` | `U3-5` / `[3,4,5]` |
| unit_type / oqt | `composite_question` / `single_choice` | 同左 |
| options_lines / stem | `None` / `None` | `None` / `None` |
| answer lines | `[601, 601]` | `[601, 601]`（**同一共享答案表**） |
| layout class | `IRREGULAR`（无 options block） | 同左 |
| **answer representation** | `answers.method = td_positional`；`n_cells = 110`；`answers map = {}`；**`unresolved = [1, 2]`** | `n_cells = 110`；`answers map = {}`；**`unresolved = [3, 4, 5]`** |
| `answers.cells[0:8]` | `["题号","1","2","3","4","5","6","7"]` | 同左 |
| **flags** | **`['answer_table_unresolved']`** | 同左 |
| basis / printed_provenance | `unverified` / `unknown` | 同左 |
| answer_evidence / option-level evidence | **KEY ABSENT** / **NONE** | 同左 |
| 源行实测 | **L601**：行长 6,920 字符，**110 个 `<td>`**，`cells[-4:] = ['D','A','C','B']` | 同一 L601 |

**判读**：同一张 110-cell 共享答案表被多个 unit 引用（E-1 取 `[1,2]`、E-2 取 `[3,4,5]`），`td_positional` 要求 `len(cells)==len(question_numbers)`（110 vs 2 / 110 vs 3）**恒不成立** → 全数 `unresolved`。**这是共享答案表映射问题，与选项布局零关系**（两例 `options_lines` 均为 `None`，因是 composite）。

### Sample Group F — 有 `options_lines` 但无法建立 option-level evidence（池 207）

**F-1 / F-2** · source / manifest 同 A 组 · `source_content_sha256 = d4917437…62e714`

| 字段 | F-1 | F-2 |
|---|---|---|
| unit_id / printed_number / question_numbers | `Q28` / `[28]` / `[28]` | `Q29` / `[29]` / `[29]` |
| unit_type / oqt | `standalone_question` / `single_choice` | 同左 |
| options_lines | `[289, 297]` | `[301, 307]` |
| stem / answer / explanation | `[287,287]` / `[825,825]` / `[827,829]` | `[299,299]` / `[831,831]` / `[833,835]` |
| layout class | `IRREGULAR_LABELS` | `IRREGULAR_LABELS` |
| raw representation | `L289 "A. 建立长江三角洲经济特区"` / `L290 ""` / `L291 "B. 在广东等地设经济特区"` / `L292 ""` / **`L293 "---"`** / `L294 ""` / `L295 "C. 建立环渤海经济区"` … | `L301 "A. 迪亚士"` / `L303 "B. 达，伽马"` / `L305 "C. 哥伦布"` / **`L307 "D 麦哲伦"`** |
| 无法建 per-option 的直接原因 | 区块内夹杂 Markdown 水平线 `---`，朴素标签切分被噪声行打断 | **`D` 后缺点号**（`D 麦哲伦`），标签正则不命中 → 只检出 `{A,B,C}` |
| answer representation | `["28. 【答案】B"]`；`answers=null` | `["29. 【答案】C"]`；`answers=null` |
| flags / basis / printed_provenance | `[]` / `printed_as_is` / `source_line` | 同左 |
| answer_evidence / option-level evidence | **KEY ABSENT** / **NONE** | 同左 |

**判读**：二者**选项文字均完整**。F-1 是噪声行（`---`）干扰切分，F-2 是 OCR 标点退化。**属识别器稳健性（T3/T4），不是布局导致的不可定位，也不是答案表问题。**

---

# 十、Failure Taxonomy

| # | 失败型 | 数量（/945） | 占比 | Case | 真实成因 | 可否确定性恢复 |
|---|---|---:|---:|---|---|---|
| T1 | 多选项同行，line-range 无法表达 per-option | **485** | 51.32% | 2 | Producer 未做 option slicing；布局已线性化 | **是**（字符偏移） |
| T2 | 一行一选项，line-range 本可表达但未产出 | **386** | 40.85% | 2 | **纯 Producer capability gap** | **是**（行区间） |
| T3 | 标签误检（LaTeX/中文紧邻）致切分残缺 | 13 | 1.38% | 2/3 | 识别器稳健性 | 是（改进规则） |
| T4 | 标签缺失/残缺（如 `D 麦哲伦` 缺点号） | 2 | 0.21% | 3 | OCR 标点退化 | 多半可（放宽标签规则） |
| T5 | `---`/无标签续行/配图混排 | 40 | 4.23% | 2/3 | 源版式 + 线性化 | 部分可（续行归属规则） |
| T6 | HTML 表格选项 | 16 | 1.69% | 2 | 布局；需 table-cell 原语 | 是（解析 `<td>`） |
| T7 | 选项为图片、正文无文字 | 4 | 0.42% | 4 | 源文档即为图片 | **否**（需图片 OCR） |
| T8 | 共享答案表 cell→question_number 映射失败 | 472（choice） | — | **5** | `parse_answer_table` 粒度不匹配 | 是（按题号键解析表头网格） |
| T9 | `answer_lines` 误锚到评分标准块 | 44（choice） | — | **5** | 答案区切分 + 题号归一化 | 是（规则修正） |
| T10 | `answer_evidence` 字段整体缺失 | 1108（choice） | — | 镜像 1 | prompt < v2.4 | 是（重跑 v2.4+） |

> T8/T9/T10 是**独立问题**，与 T1–T7 不共享失败机制；本表并列只为呈现完整面。

**归并到任务书的 Case 1–5**：

```text
Case 1  Producer 有、Consumer 丢        :  option 维度  0        （answer_evidence 维度为镜像：槽位在、数据无）
Case 2  Producer 无、Markdown 已足够     :  871 / 945  =  92.17%   ← 主导
Case 3  Markdown 已丢、PDF 仍有          :  ≤ 13 / 945 =  ≤1.38%   （仅「视觉列关系」层）
Case 4  PDF 亦难恢复                     :     4 / 945 =   0.42%
Case 5  实为 answer-table mapping 问题    :  502 + 91 flags（独立计量）
```

---

# 十一、Producer Capability Analysis

## 11.1 核心架构问题的回答

> **「当前 preprocessing 是『有意只保存 whole options region』，还是『原本想保存 per-option evidence 但由于某些输入无法定位而失败』？」**

**结论（DERIVED，证据充分）**：**是前者 —— 有意（schema 级）只保存 whole options region。不是定位失败。**

五条互相独立的证据，指向同一结论：

1. **Prompt JSON schema 从 v2.1 到 v2.7 从未包含 per-option 字段**（`reslice_pipeline.py:255` 只有 `"options_lines": [起始行号, 结束行号] 或 null`）。若是「想做但失败」，schema 里应有该字段的定义。
2. **4,609 units / 166 manifests / 7 个 prompt 版本，per-option key 计数 = 0**。若是定位失败，应出现**部分成功 / 字段空值 / 版本间不一致**；实测是**彻底不存在**。
3. **Producer Contract §2.1 明文把 `options_lines` 定义为「区域级（见 2.3 gap）」**——契约自己承认这是设计粒度。
4. **Producer Contract §2.3 把 per-label 列为「已知 Gap（不阻断，但登记在案）」，并给出方向 A / 方向 B 两个待协商方向**，§7 待确认清单第 1 项即「options 粒度走方向 A 还是方向 B？」——**这是尚未做出的设计决策，不是失败记录**。
5. **Producer 具备做细粒度的证据**：同一批 prompt 对 `answer_evidence` 就输出逐 unit 结构化对象（`type/lines/value/shared`），且 v2.4 起 100% 覆盖 906 units。**有能力做细粒度、对选项却只做整块** ⇒ 设计取舍。

**反证检验（若为「想做但失败」应观察到什么）**：字段定义存在但值恒 null / 部分 unit 有部分无 / prompt 版本间不一致 / 校验脚本报错。**四项均未观察到**——`reslice_pipeline.py` 的 `chk_range` 只校验 7 个 INTERVAL_ROLES，从不提及 per-option。

## 11.2 Producer 当前实际能力（非愿景）

| 能力 | 状态 | 证据 |
|---|---|---|
| 整块选项区行区间锚定 | **有** | `options_lines` 1386/1386（manifest）、945/945（choice 且非 null） |
| 整块选项区文本确定性切片 | **有** | IR `content.options_lines` |
| per-option label | **无** | 双面 key 扫描 = 0 |
| per-option text | **无** | 同上 |
| per-option line anchor | **无** | 同上 |
| per-option evidence | **无** | 同上 |
| `answer_evidence` 逐 unit 结构 | **v2.4+ 有；ADMITTED 71（v2.1/v2.3）无** | §8.4 |
| 答案表 cell 保留 | **有**（`answers.cells` 完好） | `resolver_reference.py:84` |
| 答案表 cell → 题号映射 | **部分**（键位形态 26；表头网格形态 472 全失败） | §6.4 |

## 11.3 「不猜测」策略的正确性与代价

`resolver_reference.py:13` 的设计原则是「两者推不出的题号标 unresolved，**不猜**」。这条反伪造策略本身**正确且必须保留**。代价是：当粒度不匹配（110 cells 对 1–3 qnums）时，`td_positional` 必然全失败。**问题不在策略，在输入粒度与对齐单位不匹配** —— 修法是让 cell 携带题号键（样本 D-1 形态）或显式解析表头网格的行/列结构，而不是放宽「不猜」。

同理，V3 `annotation_adapter.py:66-71` 的「不再 fabricate per-label 声明」也是**正确行为**，不应被视为缺陷：

```python
# options: 不再 fabricate per-label 声明。
# preprocessing 提供 options_lines 是事实，但不提供 per-label 粒度。
# 不声明 options → choice-type 单元会因 "options missing" 变 incomplete，
# 这是诚实结果：暴露 V3 格式与 preprocessing 证据粒度的真实 gap。
```

---

# 十二、V3 Consumer Requirement Analysis

## 12.1 V3 为什么要求 `content.options[].label`？

**三条来源，全部 OBSERVED：**

1. **Frozen Spec 形状定义** —— `Docs/V3_SPEC/20_Document_Pipeline.md:168`：

   ```json
   "options": {"A": {"source_span": {"span_id": "sp-Q1-A"}, "status": "resolved"}}
   ```

   即：**per-label options，且每 label 绑一个 `source_span.span_id`**。

2. **Frozen Spec role 契约（M1，BUG-V3-016 终裁）** —— `20_Document_Pipeline.md:403-424`：`content_roles` 是「canonical question type → role requirement」的**唯一规范来源**；`single_choice / multiple_choice / true_false` 的 `options` 列 = **`required_for_choice`**。生产实现 `backend/app/domains/compile/__init__.py:66` 照此实现。

3. **span_id 命名强制 label** —— `ir.py:73-76`：

   ```python
   def _content_span_id(unit_id, role, label=None):
       if role == "option":
           return f"sp-{unit_id}.option.{label}"
   ```

   `ir.py:182-189` 仅当 `isinstance(o, dict) and o.get("label")` 才产 `IRContent(role="option", label=…)`。

## 12.2 是否还要求 option-level source span？

**是（OBSERVED）。** `20_Document_Pipeline.md:168` 的每个 option 都带 `source_span: {span_id, status}`；`ir.py:187` 写入 `span_id = sp-<unit>.option.<label>` 并以 `_has_span(resolved, sid)` 校验解析状态。**label 与 source span 是绑定的**——只有 label 没有 span 同样不构成 resolved option。

## 12.3 这是 Frozen Spec 明确要求，还是当前实现自行要求？

**结论（OBSERVED）**：**是 Frozen Spec 明确要求**（`20_Document_Pipeline.md` §6.1 示例 + §6.3 `content_roles` 冻结表 + §7.3 `dedup_key`），`ir.py` 是**实现**该 Spec，不是自行加码。

**但必须同时指出（OBSERVED，关键不对称）**：

| 文档 | 对 option 粒度的要求 |
|---|---|
| **Frozen Spec**（`20_Document_Pipeline.md`） | **per-label + source_span**（§6.1/§6.3/§7.3） |
| **Producer Contract**（`PREPROCESSING-V3-CONTRACT.md` §2.1） | **`options_lines` 区域级**，明文「区域级（见 2.3 gap）」 |
| **Producer Contract §2.3** | per-label 列为 **已知 Gap，方向 A/B 待协商** |
| **Producer Contract §1.2** | 「**行号是唯一定位原语**」——连 sub-line 原语都未预留 |

**这是需求侧（V3 Frozen Spec）超前于供给侧（Producer Contract）的契约不对称。** P04 的实质就是这个不对称的裁决。

## 12.4 Producer Contract 是否明确要求 Producer 提供 per-option evidence？

**结论（OBSERVED）：没有。** 明确记载的恰是**反面**：

- §2.1：`options_lines | choice 类型必需 | [16, 23]——**区域级**（见 2.3 gap）`
- §2.3：Gap「per-label options 粒度」现状 =「preprocessing 只给 `options_lines` 区域，**不给 A/B/C/D 逐标签行号**」；方向 =「A：DSH 增加 `options_labels: [{label, lines}]`；B：维持区域级，V3 在区域内检测 Source marker（P3.2 实验路径）」；并明文「**未决前 V3 不 fabricate per-label 声明**——choice unit 因 options missing 判 incomplete 是诚实结果」
- §7 待 DSH 确认清单第 1 项：「options 粒度走方向 A（producer 给 per-label）还是方向 B（V3 区域内检测）？」

## 12.5 若 Contract 未要求，当前 P04 是否实际上是一个新的 Contract decision？

**结论（DERIVED）：是。** P04 不是「执行既有契约条款」，而是**在两个未决方向（A/B）之间做出新的 Contract 决策**，并可能连带修订 Producer Contract §1.2（定位原语）与 §2.1（`options_lines` 粒度标注）。

**严格禁止的推论**（任务书第八节末条，本轮已遵守）：**不得因为当前代码需要某字段，就反推 Frozen Spec 已经要求 Producer 提供该字段。** 事实是——Frozen Spec 要求 V3 IR 侧有 per-label；Producer Contract **从未**要求 Producer 侧提供 per-label。两者不是同一件事。

## 12.6 下游真实依赖面（OBSERVED）

| 下游 | 是否依赖 option label | 证据 |
|---|---|---|
| V3 IRBuilder `validate_ir` | **是**（choice 无 options → `incomplete`） | `ir.py:256-259` |
| Question `dedup_key` | **是**（含 own options，按 label 排序；label 重复 fail-fast） | `20_Document_Pipeline.md:523, 532` |
| Gate 答案校验 | **是** | `gate/policy.py:306-307`：`labels = tuple(str(o.label) for o in leaf.options if o.label); result = verify(leaf.canonical_question_type, leaf.answer.text, labels)` |
| Gate grammar / strict-auto | **是**（label set） | `gate/policy.py:73, 318` |
| `OPTION_LABEL_SPAN_UNAVAILABLE` gap 码 | **无任何生产消费者** | grep `backend/**`（排除 adapter/测试）= **0 命中** |
| Question Identity | 否 | Identity = `source_content_sha256` + manifest identity 字段 |

**注意**：gap 码目前只是 adapter 的**自述登记**，Gate/Compiler/Admission 都不读它。它**不构成**任何阻断规则，只是可观测性信息。

---

# 十三、Authority Primitive Analysis

## 13.1 为什么「source line range」不够

Producer Contract §1.2（OBSERVED）：

> 行号是**唯一定位原语**。所有下游声明（stem/options/answer/material lines）都以 1-based 闭区间 `[start, end]` 对引用行号。

实测（DERIVED）：在 498 个 `SAME_LINE_MULTI_OPTION` block 中，**四个选项共用同一个行号**（如样本 B-1 全部映射到 `L11`）。若 provenance 只能表达行区间，则四个选项的 provenance **完全相同、不可区分**。这在信息论上不可能表达 per-option 差异。

**line range 的表达力上限（OBSERVED/DERIVED）**：

```text
可表达：A → [22,22]   B → [24,24]   C → [26,26]   D → [28,28]     387 blocks (40.95%)
不可表达：A → L11[0:5)  B → L11[6:11)  C → L11[12:17)  D → L11[18:23)   498 blocks (52.70%)
不可表达：A → <table> cell(r,c)  …                                          16 blocks ( 1.69%)
不可表达：A → image region                                                  4 blocks ( 0.42%)
```

## 13.2 候选原语的实测覆盖

| 原语 | 覆盖 blocks | 累计 | 成熟度证据 |
|---|---:|---:|---|
| `source_line_range` `[start,end]` | 387 | 40.95% | **Producer Contract §1.2 已冻结** |
| `char_span_in_line` `(line, start_offset, end_offset)` | +485 | **92.17%** | `consumer-report-b3.json` 的 `located` 记录**已预留** `start_offset`/`end_offset` 字段（line 级场景为 null） |
| `table_cell` `(table_node, row, col)` | +16 | 93.86% | `answers.cells` 已证明 `<td>` 可确定性抽取（`TD_RE`） |
| `image_region` / 显式 `degraded` | +4 | 94.29% | 需新声明；不可伪造文字 |
| 残差（需更强标签识别或人工） | 54 | 100% | — |

## 13.3 「结构化 option 对象」本身作为原语

除 provenance 外，还需**结构化 option 对象**（`label` + `text`），因为：

- V3 `dedup_key` 需要 **own options 文本**（`20_Document_Pipeline.md:523`）
- Gate `verify(...)` 需要 **label 集合**（`gate/policy.py:306-307`）
- 二者都**不能**只从 provenance 反推

**因此最小充分集是「结构化 option 对象 + 多态 provenance」，而非单一 provenance 原语。**

## 13.4 多 span 支持

实测存在**跨行选项**（选项文字续到无标签的下一行，见样本 F-1 的无标签续行、`IRREGULAR_LABELS` 中 38 个含无标签非空行）。因此 provenance 需支持**一个 option 对应多个 source span**，或以「起始 anchor + 归属规则」表达。候选形态：

```text
option A → spans: [ {line: 289}, {line: 290} ]      （多 span）
option A → anchor: {line: 289} + continuation: auto  （起始 anchor + 续行规则）
```

**本轮不决定采用哪种**（任务书第九节明令「不要提前决定答案」）。

## 13.5 小结：真正需要的 authority primitive（决策输入，非裁决）

```text
必需：option label            （A–D 为主；须允许残缺并显式标记）
必需：option text             （可从 source 确定性重建）
必需：provenance 多态之一：
        source_line_range      →  40.95%
        char_span_in_line      → +51.22%  =  92.17%
        table_cell             → + 1.69%  =  93.86%
        image_region/degraded  → + 0.42%  =  94.29%
可选：多 span / 续行归属规则    （覆盖 IRREGULAR 子集）
必需：残差显式降级声明          （不得伪造；5.71% 需 review 或放宽标签规则）
```

---

# 十四、Evidence Matrix

| # | 命题 | 标签 | 证据类型 | 证据位置 | 强度 |
|---|---|---|---|---|---|
| E-01 | 71 ADMITTED / 1,664 units | OBSERVED | IR 全量 | `resolver_ir.json` `dispositions` | 强 |
| E-02 | choice = 1108（1042+66+0） | OBSERVED | manifest join | 本轮统计 | 强 |
| E-03 | choice 有 `options_lines` = 945 / 无 = 163 | OBSERVED | IR `source_lines` | 本轮统计；与 manifest 零分歧 | 强 |
| E-04 | per-option 字段 = 0（双面 key 扫描） | OBSERVED | 1,664 units | 本轮统计 | **强（决定性）** |
| E-05 | per-option 字段 = 0（全语料 4,609 units / 166 manifests） | OBSERVED | census + 全量 | 本轮统计 | **强（决定性）** |
| E-06 | prompt schema 无 per-option 字段（v2.1–v2.7） | OBSERVED | 源码 | `reslice_pipeline.py:255` | **强（决定性）** |
| E-07 | `INTERVAL_ROLES`/`SPAN_KEYS` 仅整块角色 | OBSERVED | 源码 | `reslice_pipeline.py:155`；`resolver_reference.py:46-47` | 强 |
| E-08 | Producer Contract §2.1 定义 `options_lines` 为「区域级」 | OBSERVED | 契约原文 | `PREPROCESSING-V3-CONTRACT.md` §2.1 | **强（决定性）** |
| E-09 | per-label 是登记 Gap、方向 A/B 未决 | OBSERVED | 契约原文 | 同上 §2.3 / §7.1 | **强（决定性）** |
| E-10 | 布局分类 498/387/40/16/4 | OBSERVED | 945 全量 | 本轮分类器（规则见 §3.3） | 强 |
| E-11 | 无 Markdown 管道表格 | OBSERVED | 945 全量 | 本轮统计 | 强 |
| E-12 | TEST1 字符切分可恢复 485/498 | OBSERVED | 498 全量 | 本轮测试 | 强 |
| E-13 | TEST2 每选项独立源行 386/387 | OBSERVED | 387 全量 | 本轮测试 | 强 |
| E-14 | 综合可恢复 871/945 = 92.17% | DERIVED | E-12+E-13 | — | 强 |
| E-15 | IR 切片 == 真实源行（6 处逐字回读） | OBSERVED | 源文件 | §9.1 | 强 |
| E-16 | `answers` = `{cells,method,answers,unresolved}` | OBSERVED | IR | `resolver_reference.py:105-106` | 强 |
| E-17 | `cells == qnums` 命中 0/498；`unresolved == qnums` 472/498 | OBSERVED | 498 全量 | 本轮统计 | **强（决定性）** |
| E-18 | 答案表 L601 = 110 `<td>`，含 `题号`/`答案` 表头格 | OBSERVED | 源文件 | §6.2 | **强（决定性）** |
| E-19 | 键位形态成功 26（`td_by_question_number`） | OBSERVED | IR | 本轮统计 | 强 |
| E-20 | flags × options_lines 存在率 84.3%/86.4%/86.4% | DERIVED | 945 全量 | §7.2 | **强（决定性）** |
| E-21 | 499 无 flag block 仍全缺 per-option | OBSERVED | 945 全量 | §Q3 矩阵 | **强（决定性）** |
| E-22 | 两 flag 互斥（同现 = 0） | OBSERVED | 1,664 全量 | 本轮统计 | 强 |
| E-23 | `answer_evidence` v2.4 起 100%，v2.1/v2.3 为 0 | OBSERVED | 166 manifests | §8.4 | **强（决定性）** |
| E-24 | ADMITTED 71 全为 v2.1(38)/v2.3(33) | OBSERVED | 71 全量 | 本轮统计 | 强 |
| E-25 | Producer Contract §2.1 要求 `answer_evidence` 必需 | OBSERVED | 契约原文 | §2.1/§2.5 | 强 |
| E-26 | V3 `ManifestUnit` 已建 `answer_evidence_*` 三字段 | OBSERVED | 源码 | `manifest_reader.py:44-46, 94-96` | 强 |
| E-27 | `answer_number_mismatch` 全部为「首行数字 ∉ qnums」 | OBSERVED | 91 全量 | §8.2 | 强 |
| E-28 | 其样本实为评分标准行误锚 | OBSERVED | IR `answer_text` | §8.2 | 强 |
| E-29 | V3 Spec §6.1 要求 per-label options + `source_span` | OBSERVED | Frozen Spec | `20_Document_Pipeline.md:168` | **强（决定性）** |
| E-30 | `content_roles` 冻结 `options=required_for_choice` | OBSERVED | Frozen Spec + 代码 | `20_Document_Pipeline.md:403-424`；`compile/__init__.py:66` | 强 |
| E-31 | `span_id` 强制含 label | OBSERVED | 源码 | `ir.py:73-76, 182-189` | 强 |
| E-32 | Question `dedup_key` 含 own options | OBSERVED | Frozen Spec | `20_Document_Pipeline.md:523, 532` | 强 |
| E-33 | Gate `verify` 使用 `o.label` | OBSERVED | 源码 | `gate/policy.py:306-307` | 强 |
| E-34 | gap 码无生产消费者 | OBSERVED | grep | §12.6 | 强 |
| E-35 | adapter 有意不伪造 per-label | OBSERVED | 源码注释 | `annotation_adapter.py:66-71` | 强 |
| E-36 | `runner_b2` 只产整块 `options` span | OBSERVED | 源码 | `runner_b2.py:265-270` | 强 |
| E-37 | Producer Contract §1.2「行号是唯一定位原语」 | OBSERVED | 契约原文 | §1.2 | **强（决定性）** |
| E-38 | Direction B 实验已有结果（b3: 527/548 resolved） | OBSERVED | 实验工件 | `consumer-report-b3.json` | 中（非生产口径） |
| E-39 | gate_b2b1: structure_extracted 91.34% | OBSERVED | 实验工件 | `gate_b2b1_result.json` | 中（语料不同） |
| E-40 | gate_b2b2: shared 抽取率 30% vs 非 shared 68% | OBSERVED | 实验工件 | `gate_b2b2_result.json` | 中（独立佐证） |
| E-41 | 原始 PDF 版面结构 | **UNKNOWN** | — | 本轮未取证 | **缺** |
| E-42 | Case 2 = 92.17% 为主导根因 | DERIVED | E-04/05/06/12/13/14 | — | 强 |
| E-43 | 答案表 ≠ 选项布局（机制无关） | DERIVED | E-16/17/20/21 | — | **强（决定性）** |

**决定性证据计数：12 条。** 其中针对「表格是否为主因」的反证是 **E-20 + E-21**；针对「是设计还是失败」的正证是 **E-04/05/06/08/09**。

---

# 十五、Conclusions

### C1（Q1）945 缺 per-option evidence 的原因

**Producer schema 从未定义 per-option 结构。** 不是表格毁了选项，不是 OCR 丢了文字，不是 V3 丢了数据。选项文字与标签在 Markdown 里 95%+ 完好，92.17% 可确定性切出 per-option label+text——**缺的是「从未做过这一步」**。

### C2（Q2）与 Question Options 布局有关的份额

严格「选项表格」= **16（1.69%）**；广义「二维布局被线性化致 line-range 不够」= **498（52.70%）**；二者合计 **514（54.39%）**。但其中 485 个内容完整可切分，**布局只削减了 provenance 粒度，没有削减选项内容**。

### C3（Q3）与 Answer Key Table 有关的份额

**0。** 499 个无任何答案表问题的 block 仍 100% 缺 per-option evidence（E-21）。

### C4（Q4）`answer_table_unresolved=502` 与 choice option 定位的关系

**无因果关系，是两个独立问题。** 并且该 flag 的真实语义是「**共享答案表 cell 无法映射到本单元 question_numbers**」，**不是「答案表有问题」**——答案表文本与 cell 全部保留（`answers.cells` 完好）。根因是 `parse_answer_table` 用「整张多题共享表的全部 cell」去对齐「单个 unit 的 1–3 个 question_numbers」，在表头网格形态下结构性不可能成功（E-17/E-18）。

### C5（Q5）丢失层

**Producer prompt/schema 设计层**（OCR 之后、manifest 产出之前）——**从未建立，而非中途丢失**。OCR→Markdown 层只丢「视觉列关系」，不丢选项内容。Case 2 = **92.17%**。

### C6（Q6）问题归属

**多因素，主因明确**：Producer capability gap（主因，覆盖 ~100%）> source/layout loss（次因，影响粒度而非内容）> V3 contract gap（放大器，阻断面）；Consumer adapter gap = **无**；Frozen Spec gap = **否**（就 per-option 而言 Spec 已定义）。**本质是供给侧契约（区域级）与需求侧冻结规格（逐标签）的粒度不对称。**

### C7（Q7）应要求的 authority primitive

**单一 line range 不够**（§1.2 现规定「行号是唯一定位原语」需先修订）。最小充分集 = **结构化 option 对象（label + text）+ 多态 provenance（line_range / char_span_in_line / table_cell / image_region 或显式 degraded）+ 多 span 支持**。覆盖实测：line_range 40.95% → +char_span 92.17% → +table_cell 93.86% → +degraded 94.29%，残差 5.71% 需更强标签识别或人工 review。

### C8（Q8）能否关闭 P04

**不能关闭；但决策面已大幅收窄。** 根因侧证据充分（12 条决定性证据），缺的是**裁决**而非事实。关闭前须补齐 §Q8 列出的 6 项（Direction A/B 裁决、契约变更令、残差 disposition、`answer_evidence` 缺口归属、影响面确认、Direction B 生产级验证）。

---

# 十六、Remaining Uncertainty

| # | 未确定项 | 性质 | 为何本轮未解 | 补齐方式 |
|---|---|---|---|---|
| U-01 | **原始 PDF 的真实版面结构** | **证据缺口** | 本轮未打开 PDF 二进制核对版面（`maintainess/PDF`、`original/` 存在但未取证）。**本报告所有布局结论止于 OCR/Markdown 层**，未对 PDF 侧作任何断言 | 抽样 PDF 版面提取（table/column detection）后与 Markdown 对照 |
| U-02 | 视觉列关系（谁左谁右）在 PDF 是否可恢复 | 证据缺口 | 同 U-01 | 同上 |
| U-03 | 5.71% 残差（54 个）能否用更强标签规则全部恢复 | 可解未解 | 本轮只验证了朴素规则；未做规则迭代 | 迭代标签识别器（排除 LaTeX 数学模式、允许 `D ` 无点号、续行归属） |
| U-04 | `char_span_in_line` 在 485 个上的偏移量稳定性 | 部分验证 | 本轮验证了「可切分」，未验证「偏移量在 source_version 变更下的稳定性」 | 以 `body_hash`/`line_hash` 绑定偏移做稳定性测试 |
| U-05 | Direction B 在 71 ADMITTED 面的生产口径复跑 | 验证缺口 | 既有实验跑在 `reslice-p2-b1`（b3）与更广语料（b2b1），**非** ADMITTED 71 | 在 ADMITTED 71 上以生产口径复跑并签署 |
| U-06 | `answer_evidence` 缺口是否并入 P04 | **裁决项** | 非证据问题 | Owner 裁 |
| U-07 | P04 是否涵盖 `dedup_key` 阻断面 | **裁决项** | 非证据问题 | Owner 裁 |
| U-08 | 多 span 表达采用「多 span 列表」还是「anchor+续行」 | **裁决项** | 任务书第九节明令不提前决定 | Owner/后续设计 |
| U-09 | `true_false` 在本面为 0 的原因 | 观察项 | 超出本议题 | 另行统计 |
| U-10 | unit_type 值 `andalone_question`（1 例，疑 `standalone_question` 截断） | 数据质量观察 | 超出本议题 | 另行登记 |

**明确的证据纪律声明**：本报告**未**把任何 HYPOTHESIS 写成结论。U-01/U-02 是真实证据缺口——**若 Owner 需要「PDF 表格布局是否为主因」的直接证据，本报告不足以支撑**，只能支撑「OCR/Markdown 层的布局不是主因」。

---

# 十七、Owner Decision Inputs

> 以下为**决策输入**，不是建议裁决，更不是裁决本身。P04 保持 `OWNER DECISION REQUIRED`。

## 17.1 决策已可基于的事实

1. per-option evidence 缺失的主因是 **Producer schema 从未要求**，不是表格/OCR（12 条决定性证据）。
2. **92.17%** 的 block 可用已保留的 `options_lines` 确定性恢复 per-option label+text。
3. **答案表问题与选项定位正交**——修答案表不会解决 P04，反之亦然。
4. `answer_table_unresolved` 的语义是**共享答案表映射失败**，不是「答案表坏了」。
5. Producer Contract 与 V3 Frozen Spec 在 option 粒度上**不对称**；Producer Contract §7.1 已把方向 A/B 列为待确认清单第 1 项。
6. 若采纳 sub-line 原语，**须先修订 Producer Contract §1.2**（「行号是唯一定位原语」）。

## 17.2 需要 Owner 裁决的 6 项

| # | 决策项 | 选项 | 本报告能提供的输入 |
|---|---|---|---|
| D-1 | **option 粒度方向** | **A**：Producer 增加 `options_labels: [{label, lines}]`<br>**B**：维持区域级，V3 区域内检测 | B 已有实验：b3 resolved 527/548（96.17%）、b2b1 structure_extracted 91.34%；A 需 Producer 改 prompt+schema 并重跑。**A 可把 provenance 做进权威工件；B 不改 Producer 但 provenance 由 Consumer 派生** |
| D-2 | **authority primitive 是否多态化** | 维持 line_range 唯一 / 扩为多态 | 多态覆盖实测 40.95% → 92.17% → 93.86% → 94.29%。**维持单一行区间则上限 40.95%** |
| D-3 | **残差 5.71%（54 个）disposition** | 全部可解析才放行 / 允许显式 `degraded` 进入 | T7（4 个图片化选项）在 Markdown 层**不可能**恢复文字，除非图片 OCR |
| D-4 | **`answer_evidence` 契约符合性缺口归属** | 并入 P04 / 单列新议题 | Producer Contract §2.1 要求「必需」而 ADMITTED 71 全缺；V3 槽位已就绪；prompt v2.4+ 已 100% 产出 |
| D-5 | **P04 影响面是否含 `dedup_key`** | 含 / 只含 ready-IR+Gate | `dedup_key` 含 own options（Frozen Spec §7.3），label 重复 fail-fast——影响 choice 题身份计算 |
| D-6 | **多 span 表达形态** | 多 span 列表 / anchor+续行归属 | 38 个 block 含无标签非空续行（`IRREGULAR_LABELS` 主体） |

## 17.3 若 Owner 采纳「最小充分集」时的前置动作清单（非授权）

> **本清单不构成实施令。** 任何一项都涉及契约/规格变更，须 Owner 另行下令。

1. 修订 Producer Contract §1.2「行号是唯一定位原语」→ 多态 provenance（**契约变更**）
2. 修订 Producer Contract §2.1 `options_lines` 粒度标注与 §2.3 Gap 状态（**契约变更**）
3. 若走方向 A：扩展 `reslice_pipeline.py` prompt schema + 重跑语料（**生产代码 + 数据变更**，本轮未做）
4. 若走方向 B：把 `gate_b2b1_option_region.py` / `runner_b3.py` 的解析逻辑提升为生产路径并做 ADMITTED 71 生产口径验证（**生产代码变更**，本轮未做）
5. 明确残差 54 个的 review / degraded 通道
6. 就 `answer_evidence` 缺口单独定性（重跑 v2.4+ 属数据动作，须 Owner 令）

## 17.4 明确未做 / 禁止读取的推论

- 本轮**未**关闭 P04，**未**修改 P04 Contract / Frozen Spec / Frozen Contract / Producer Contract / V3 Schema / 生产代码 / corpus，**未**执行 migration，**未**进入 X3。
- **不得**把「V3 当前实现需要 `content.options[].label`」读成「Frozen Spec 要求 **Producer** 提供 per-option evidence」——Frozen Spec 约束的是 V3 IR 形状；Producer Contract 从未要求 per-label。
- **不得**把 `answer_table_unresolved` 读成「答案表损坏」。
- **不得**把 Question Options Table 与 Answer Key Table 混为一谈——实测机制、载体、触发条件、失败原因四者皆不同。
- **不得**用 §9.6 的样本外推整个 945；所有百分比均来自 945/1,664 全量计算。
- **不得**为了让 Gate 通过而反向修改 Producer 数据。
- U-01/U-02（PDF 版面）是**真实证据缺口**——本报告不支持「PDF 表格布局是否为主因」的直接结论。

---

## 附录 A — 本轮只读分析方法（可复现）

分析脚手架置于系统临时目录 `C:\Users\Kurtw\AppData\Local\Temp\p04\`（**非任何 git 仓库**，不进入提交），仅含一个只读 loader（`base.py`：`load_ir` / `load_manifests` / `ir_admitted` / `norm` / `read_lines`）。统计脚本全部经 `python - <<'PY'` 内联执行，未在任何仓库落盘。

数据源均为只读：

```text
Papers/data/resolver_ref_r52/resolver_ir.json
Papers/data/producer_interface_census.json
Papers/Ocr-markdown/**/*.manifest.json      (166)
Papers/Ocr-markdown/**/*.md                 (provenance 回读)
```

join 键：IR `ir.manifest_file` → manifest 路径（`norm()` 归一化，失败时按 basename 唯一匹配）；IR `units[].unit_id` → manifest `units[].unit_id`。**71/71 文件、1,664/1,664 units 全部 join 成功，零未匹配。**

布局分类器、标签正则、TEST1/TEST2 判据全文见 §3.3 与 §4.4。

## 附录 B — 样本级证据索引

| 组 | 池 | 样本 | 关键判读 | 落 Case |
|---|---:|---|---|---|
| A | 387 | A-1 `Q3` `options_lines=[22,28]`；A-2 `Q4` `[32,38]` | 一行一选项，line-range 本可表达 | **2** |
| B | 498 | B-1 `Q1` `[11,11]`；B-2 `Q2` `[18,18]` | 四选项同行，需 sub-line；内容完整 | **2** + 局部 3 |
| C | 16 | C-1 `Q1` `[19,19]`；C-2 `Q14` `[105,105]` | `<td>` 边界已保留，需 table_cell | **2** |
| D | 26 | D-1 `U1-3` `[1,2,3]`；D-2 `Q4` `[47,71]` | 键位形态答案表，映射成功 | 5 的**成功对照** |
| E | 472 | E-1 `U1-2` `[1,2]`；E-2 `U3-5` `[3,4,5]` | 110-cell 表头网格 vs 1–3 qnums | **5** |
| F | 207 | F-1 `Q28` `[289,297]`；F-2 `Q29` `[301,307]` | `---` 噪声行 / `D 麦哲伦` 缺点号 | **2/3**（识别器稳健性） |

## 附录 C — 关键源码/契约引用索引

| 引用 | 内容 |
|---|---|
| `Papers/scripts/reslice_pipeline.py:155` | `INTERVAL_ROLES`（仅整块角色） |
| `Papers/scripts/reslice_pipeline.py:159` | `AE_TYPES` + 注释「prompt v2.4」 |
| `Papers/scripts/reslice_pipeline.py:255` | prompt JSON：`"options_lines": [起始行号, 结束行号] 或 null` |
| `Papers/scripts/reslice_pipeline.py:258, 271` | prompt JSON：`answer_evidence` 对象 schema |
| `Papers/scripts/resolver_reference.py:46-47` | `SPAN_KEYS`（仅整块角色） |
| `Papers/scripts/resolver_reference.py:78-106` | `parse_answer_table`（`td_by_question_number` / `td_positional`） |
| `Papers/scripts/resolver_reference.py:109-116` | `_answer_flags` → `answer_number_mismatch` |
| `Papers/scripts/resolver_reference.py:142-148` | 单行 `<table` 触发 + `answer_table_unresolved` |
| `AITutors-v3/backend/scripts/preprocessing_consumer/manifest_reader.py:38, 44-46, 88, 94-96` | `ManifestUnit.options_lines` / `answer_evidence_*` |
| `AITutors-v3/backend/scripts/preprocessing_consumer/annotation_adapter.py:40, 66-71, 92-101` | gap 码 + 有意不伪造注释 |
| `AITutors-v3/backend/scripts/preprocessing_consumer/runner_b2.py:265-270, 408-420` | 整块 `options` span；Gate 前跳过 |
| `AITutors-v3/backend/app/domains/compile/ir.py:73-76, 182-189, 256-259` | `sp-<unit>.option.<label>`；`options missing for choice type` |
| `AITutors-v3/backend/app/domains/compile/__init__.py:66` | `required_for_choice` |
| `AITutors-v3/backend/app/domains/gate/policy.py:73, 306-307, 318` | Gate 使用 `o.label` 校验答案 |
| `AITutors-v3/Docs/V3_SPEC/20_Document_Pipeline.md:168, 365, 403-424, 523, 532` | per-label options + source_span；content_roles；dedup_key |
| `AITutors-v3/Docs/V3_SPEC/10_Data_Model.md:457-467` | `label` 列（仅 options 用）+ `(instance_id, role, label, role_index)` 唯一 |
| `AITutors-v3/Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT.md:50, 83, 84, 103, 120, 164, 196` | 「行号是唯一定位原语」；`options_lines` 区域级；`answer_evidence` 必需；Gap 2.3；§7.1 待确认 |
| 实验工件 | `gate_b/gate_b2b1_result.json`、`gate_b/gate_b2b2_result.json`、`preprocessing_consumer/consumer-report-b3.json` |
