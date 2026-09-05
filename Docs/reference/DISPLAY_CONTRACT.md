# AI Tutor 题库展示与切片契约

Version: 0.5
Status: 全科目综合题/独立题判定收口；后续问题按 LOG 更新
Date: 2026-09-03
用途：根据用户提供的英语、理科、语文展示期望，定义入库题目在 golden、API 与前端展示中应保留的结构。

## 0. 已确认决策

1. 展示标记统一为”题干区/答案区/详解区/配图锚点”。
2. 标记只作为 golden 校验和切片入库元数据，不进入前端页面渲染。
3. 所有科目统一按“独立解答判定”建模：去掉共享材料后仍能独立解答的题才建模为独立题，
   无法独立作答的题必须归入综合题。全科目强规则见 §0.1。
4. 写作参考范文放 `answer`。
5. 理科化学式统一使用标准化显示：`Cl₂`、`OH⁻`、`Fe₃O₄`；OCR 原文中的 `Cl(2)` 只作为 provenance。
6. 配图锚点统一为”配图锚点”；`配图起始点`、`配图位置锚点`、`配图锚点指示` 作为兼容输入，归一化后保存为 `配图锚点`。
7. golden 不约束题量、组数、子题数；只作为题型种类与展示结构样例，不作为数量验收标准。
8. golden 答案比较必须忽略全半角、引号样式、题号前缀、常见分隔符和 OCR 转义噪音；格式差异不视为内容不匹配。
9. **综合题容器（分组题头）不是独立题目，只是承载统一材料和子题分组。容器不保存答案类字段，答案只在子题中。**

## 0.1 全科目强规则：独立解答判定

1. **全科目统一标准**：去掉共享材料后，题目若仍能独立解答，才允许建模为独立题；
   若必须依赖共享材料/情境才能作答，必须建模为综合题。本规则适用于语文、英语、
   数学、物理、化学、生物、历史、政治、地理及跨学科题型。
2. **综合题是原子单元**：一份共享材料与其依赖的若干子题必须整体保存、整体校验、
   整体审核；禁止把子题拆成脱离材料的独立题。
3. **共享材料只保存一次**：材料放 `shared_material`，子题只保存自身题干、选项、
   答案、详解所需数据；禁止把整篇材料复制进每个子题 `stem`。
4. **综合题完整性判定**：材料存在，且每个子题结合该材料后可以独立解答，才允许
   进入 approved；任一子题缺题干/选项/答案/所需行号，或与材料/答案区无法对应，
   则整个综合题不得 approved。
5. **禁止按 section 或题型批量合并**：无材料依赖、题目本身包含完整作答信息的题，
   即使属于同一 section，也必须建模为独立题，不得强行并入综合题容器。

共享材料包括但不限于：阅读文章与选段、文言文原文与注释、词库、语法/完形短文、
七选五短文与共享选项区、情境/实验/图表/数据条件、材料分析题共同题干、默写与任务
式大题的共同要求。各科目应用示例见 §4。

## 0.2 Canonical Question Types

Phase 5 前置 DoD（03 契约 §13.1）：以下为 canonical question_type 枚举，
所有新链和旧链入库均使用此映射；非 canonical 值必须在入库前映射到以下之一。

| canonical_question_type | 中文名 | answer 格式 | 选项要求 |
|---|---|---|---|
| single_choice | 单选题 | 单个大写字母（A/B/C/D/...） | required |
| multiple_choice | 多选题 | 大写字母集合，canonical 排序去重 | required |
| true_false | 判断题 | `T` 或 `F`（canonical 映射见下） | required，固定 2 选项 |
| fill_in | 填空题 | 不开放 strict auto grammar | not_applicable |
| short_answer | 解答题 | 不开放 strict auto grammar | not_applicable |
| essay | 写作 | 不开放 strict auto grammar | not_applicable |
| cloze | 完形填空 | 由题型子结构决定 | 按题型 |
| reading | 阅读理解 | 由题型子结构决定 | 按题型 |
| grammar_fill | 语法填空 | 由题型子结构决定 | not_applicable |
| vocabulary_fill | 选词填空 | 由题型子结构决定 | 按词库 |
| seven_to_five | 七选五 | 由题型子结构决定 | 按共享选项 |
| reading_expression | 阅读表达 | 由题型子结构决定 | 按题型 |

### true_false Canonical 映射

判断题的 canonical answer 格式为 `T`（正确/对/是）或 `F`（错误/错/否）。

映射规则：

| 原始答案 | canonical |
|---|---|
| T / t / 正确 / 对 / 是 / √ / ✓ | T |
| F / f / 错误 / 错 / 否 / × / ✗ | F |

LLM 输出或答案表中的判断题答案必须在入库前映射为 `T` 或 `F`。
不允许 `true`/`false`/`True`/`False` 作为 canonical 值。
不允许 `A`/`B` 作为判断题答案（与选择题混淆）。

严格自动 `verified_correct=true` 路径要求：
1. 答案已映射为 `T` 或 `F`；
2. Resolver status 为 exact/normalized；
3. 答案来源为教师版答案区（非 LLM fallback）；
4. 通过 Allowed-Answer Grammar 校验。

## 1. 核心原则

1. 题目内容按“题干区、答案区、详解区、配图区”结构化保存，不依赖原始文本中的“开始/结束”标记做最终渲染。
2. 同一篇文章/词库/情境材料只保存一次，作为 `shared_material`，各子题引用它。
3. 每道题的答案必须独立、干净，不得把多个题答案拼在一个字符串里。
4. 配图和答案图必须保留来源、页码、位置和锚点。
5. 综合题的子题必须有完整独立的 stem/options/answer/explanation 数据，父题不拼接子题选项。
6. 评分标准与答案分开保存，例如“任选其中三道小题作答”“每空1分”“言之成理即可”。

## 2. 统一展示标记

| 语义 | 标准标记 | 兼容输入 |
|---|---|---|
| 题干区开始 | `题干区开始` | `题干开始` |
| 题干区结束 | `题干区结束` | `题干结束` |
| 答案区开始 | `答案区开始` | `答案开始` |
| 答案区结束 | `答案区结束` | `答案结束` |
| 详解区开始 | `详解区开始` | `详解开始` |
| 详解区结束 | `详解区结束` | `详解结束` |
| 配图锚点 | `配图锚点` | `配图起始点` / `配图位置锚点` / `配图锚点指示` |

这些标记不写入前端展示文本，只用于 golden 校验、切片边界识别和人工核对。

## 3. 通用题目结构

```json
{
  "question_number": "1",
  "question_type": "single_choice",
  "section_id": "单项选择题_1",
  "stem": "题干文本",
  "stem_line_ids": ["P1L005"],
  "stem_region": {"start": "题干区开始", "end": "题干区结束"},
  "shared_material": null,
  "shared_material_line_ids": [],
  "options": [
    {"label": "A", "text": "选项文本"}
  ],
  "options_line_ids": {"A": ["P1L006"]},
  "answer": "D",
  "answer_line_ids": ["P5L003"],
  "answer_region": {"start": "答案区开始", "end": "答案区结束"},
  "explanation": "详解文本",
  "explanation_line_ids": ["P12L022"],
  "explanation_region": {"start": "详解区开始", "end": "详解区结束"},
  "scoring_standard": "每空1分，任选3小题完成",
  "images": [
    {
      "image_key": "object_key",
      "page_no": 3,
      "bbox": {"x1": 0, "y1": 0, "x2": 100, "y2": 100},
      "placement": "stem",
      "source": "ppsv3",
      "anchor": "配图锚点",
      "url": "https://..."
    }
  ],
  "answer_images": [],
  "is_composite": false,
  "sub_questions": [],

  "shared_material_notes": null,
  "shared_material_notes_line_ids": [],
  "word_bank": null,
  "answer_structure": null,
  "answer_source": "document_answer_table",
  "explanation_source": "document_inline_explanation",
  "score": 5,
  "difficulty": 1
}
```

## 3.1 综合题容器字段标准

综合题容器（分组题头）不是独立题目，只是承载统一材料和子题分组。

**容器应该保存的字段：**

| 字段 | 含义 | 示例 |
|---|---|---|
| question_number | 分组标识 | "1-10"、"11-13" |
| question_type | 综合题类型 | "cloze"、"grammar_fill"、"reading" |
| is_composite | true | true |
| stem | 统一任务说明/指令 | "第一节(共10小题;每小题1.5分，共15分)" |
| stem_line_ids | 任务说明行号 | ["P1L001"] |
| shared_material | 统一材料文本 | "The Ultimate Goal\nI sat..." |
| shared_material_line_ids | 材料行号 | ["P1L002", "P1L003"] |
| shared_material_notes | 文言注释等附属材料 | null |
| shared_material_notes_line_ids | 注释行号 | [] |
| scoring_standard | 整个分组的评分标准 | "共10小题，每空1.5分，共15分" |
| images | 材料配图 | [] |
| sub_questions | 真正的小题 | [{...}, {...}] |

**容器不应该保存的字段（应为 null 或 []）：**

| 字段 | 原因 |
|---|---|
| answer | 答案只在子题中 |
| answer_line_ids | 答案行号只在子题中 |
| answer_region | 答案区域只在子题中 |
| answer_images | 答案图片只在子题中 |
| explanation | 详解只在子题中 |
| explanation_line_ids | 详解行号只在子题中 |
| explanation_region | 详解区域只在子题中 |
| options | 选项只在子题中 |
| options_line_ids | 选项行号只在子题中 |

**容器字段示例（完形填空）：**

```json
{
  "question_number": "1-10",
  "question_type": "cloze",
  "section_id": "完形填空_1",
  "is_composite": true,
  "stem": "第一节(共10小题;每小题1.5分，共15分) 阅读下面短文，掌握其大意...",
  "stem_line_ids": ["P1L001", "P1L002"],
  "stem_region": {"start": "题干区开始", "end": "题干区结束"},
  "shared_material": "The Ultimate Goal\nI sat in the dressing room...",
  "shared_material_line_ids": ["P1L003", "P1L004", "P1L005"],
  "scoring_standard": "共10小题，每空1.5分，共15分",
  "images": [],
  "answer": null,
  "answer_line_ids": null,
  "answer_region": null,
  "answer_images": null,
  "explanation": null,
  "explanation_line_ids": null,
  "explanation_region": null,
  "options": null,
  "options_line_ids": null,
  "sub_questions": [
    {
      "qno": "1",
      "question_type": "single_choice",
      "answer": "C",
      "answer_line_ids": ["P5L001"],
      "explanation_line_ids": [],
      "scoring_standard": "每空1.5分",
      "answer_images": []
    }
  ]
}
```

## 4. 各题型要求

### 4.1 单项选择题

- `stem` 必须完整。
- `options` 必须 A-D 等完整列表。
- `answer` 只保存单题答案，例如 `D`。
- 禁止保存 `"A43.B44.D"`、`"D2.C3.A4"` 这类跨题答案串。
- 分值不要混入答案，例如 `"B (2分)"` 应拆为 `answer="B"` + `score=2`。

### 4.2 多项选择题

- `question_type` 使用 `multiple_choice` 或对应题型树 code。
- `answer` 建议保存为数组或紧邻字母，例如 `["A", "B", "D"]` 或 `"ABD"`。
- 每个选项仍保留独立的 `options_line_ids`。

### 4.3 完形填空

- 整篇文章作为 `shared_material`。
- 10 个空位建模为同一综合题的 `sub_questions`。
- 子题 `stem` 可只保留题号/空位信息，选项和答案归属子题。
- 父题 `options` 置空，禁止把 10 个题的选项拼接在父题上。

### 4.4 语法填空

- 每篇短文作为一个共享材料组。
- 同一篇下的空位是 `sub_questions`，例如 `11-13`、`14-17`、`18-20` 各一组。
- 子题 `answer` 必须是该空位的独立答案，例如 `itself`、`to`、`to stay`。
- 提示词原文可作为子题 stem 的补充信息。

### 4.5 选词填空 / 词库

- 方框单词保存为 `word_bank`。
- 每个句子作为独立子题或独立题目。
- `word_bank` 示例：

```json
{
  "title": "请用方框中单词的正确形式完成句子。",
  "words": ["pack", "confuse", "equal", "contribute", "athlete"],
  "line_ids": ["P3L001", "P3L002", "P3L003", "P3L004", "P3L005"]
}
```

### 4.6 阅读理解

- 整篇文章作为 `shared_material`。
- 每道小题是独立 `single_choice` 或对应题型。
- 每道小题保留自己的 `stem_line_ids`、`options_line_ids`、`answer_line_ids`。
- 禁止把同一篇文章的所有答案拼进某一题的 answer。

### 4.7 七选五

- 整篇文章作为 `shared_material`。
- A-G 七个选项作为共享选项区，或按子题引用。
- 每个空位是 `sub_questions` 中的一个子题。
- 子题 answer 只保存对应选项字母，例如 `B`。
- 需要保留“选项中有两项多余”的元数据：`extra_options=2`。

### 4.8 阅读表达

- 整篇文章作为 `shared_material`。
- 42-45 等小题保存为 `sub_questions` 或独立 `short_answer`。
- 题干中的作答横线可保留为 stem 的一部分。
- 答案必须保存参考作答，不是空字符串。

### 4.9 写作

- 题目要求作为 `stem`。
- 示例作文作为 `answer` 完整保存，禁止只存 `"例文"`。
- `answer_region` 应包含完整参考范文。
- 若题目提供多个写作选项，父题保存共同要求，每个写作选项作为独立子题。

### 4.10 理科综合题 / 实验题

- `(1)(2)(3)(4)` 子问建模为 `sub_questions`。
- 每个子问保留独立 `stem`、`answer`、`explanation`。
- 题干/子问中的图片绑定到对应 `images`。
- 答案区中的图片保存到 `answer_images`。
- 如果答案是“见试题解答内容”，该文本可保留，但要同时有 `answer_source` 和完整 `explanation`。

### 4.11 语文题型

语文试卷按“综合题 + 子题”为主建模。

#### 4.11.1 语文基础知识选择

- 没有共享材料或共享材料很短的题可以建模为独立 `single_choice` / `multiple_choice`。
- 例如成语解说、加点词意思、语句理解等，直接保存题干、选项、答案、详解。

#### 4.11.2 默写题

- 题目说明保存为父题 `stem`，例如“任选其中三道小题作答”。
- 每个空位是 `sub_questions` 的子题。
- 每个子题保存独立 `answer`。
- 评分标准保存到 `scoring_standard`，例如“每空1分，任选3小题完成，若全选按前3小题计分”。

#### 4.11.3 现代文阅读 / 名著阅读

- 整篇选段作为 `shared_material`。
- 选择题、标点题、简答题均作为独立子题或题目。
- 表格题使用 `answer_structure` 保存表格行/列结构。
- 多选/不定项保存独立 `answer`，例如 `["B", "C"]` 或 `"BC"`。

#### 4.11.4 文言文阅读

- 文言原文和注释整体保存为 `shared_material`。
- 文言注释可保存为 `shared_material_notes`。
- 选择题、分析题、表格题、综合问答均作为 `sub_questions`。
- 表格类答案使用 `answer_structure`。

#### 4.11.5 综合研学任务 / 任务式大题

- 父题保存总说明和任务要求。
- `task 1 / task 2 / task 3` 分别建模为 `sub_questions`。
- 示例答案保存为对应子题 `answer`，可包含路线、阐释、导游词等结构化文本。

#### 4.11.6 语文写作

- 父题保存写作总要求。
- 小写作中“任务一/任务二/任务三”这类必做任务建模为 `sub_questions`，每个任务保存独立 `answer`。
- 大写作直接按一道题建模，不拆 `choices`。
- 若题目给出多个写作选项，把所有条件和要求统一保存到该题 `stem`。
- 示例作文完整保存到 `answer`；如果有多篇示例，可保留多篇并在 `answer` 内分段区分。
- 字数要求、文体要求等保存到 `scoring_standard` 或 `stem`。

### 4.12 语文表格 `answer_structure` 示例

`answer_structure` 用于表达无法用纯文本展示的表格答案，例如标点题表格、人物形象表格。

标点题示例：

```json
{
  "type": "table",
  "title": "标点符号及理由",
  "columns": [
    {"key": "position", "title": "标点符号"},
    {"key": "reason", "title": "理由"}
  ],
  "rows": [
    {
      "position": "①",
      "answer": "！",
      "reason": "四叔对祥林嫂死在祝福之夜非常愤慨，语气强烈。"
    },
    {
      "position": "②",
      "answer": "？",
      "reason": "“我”突闻祥林嫂死讯，感到惊诧，不敢相信。"
    },
    {
      "position": "③",
      "answer": "？",
      "reason": "短工对祥林嫂的死因毫不感到意外，使用反问语气。"
    }
  ]
}
```

人物形象表格示例：

```json
{
  "type": "table",
  "title": "人物形象特点",
  "columns": [
    {"key": "character", "title": "人物"},
    {"key": "detail", "title": "细节描写"},
    {"key": "trait", "title": "形象特点"}
  ],
  "rows": [
    {
      "character": "店主人",
      "detail": "成目视主人，主人色不动……请主人自取之，主人不受",
      "trait": "镇定自若；精明；善良；不贪财"
    },
    {
      "character": "大亲王",
      "detail": "王呼曰“鹑人来，鹑人来！实给六百，肯则售，否则已耳。”",
      "trait": "沉迷玩物；精明"
    },
    {
      "character": "老祖母",
      "detail": "妪早起，使成督耕，妇督织；稍惰，辄诃之。",
      "trait": "勤快；严教儿孙；治家有方"
    }
  ]
}
```

表格类答案仍可保留 `answer` 为便于检索的汇总文本，但展示必须优先读取 `answer_structure`。

## 5. golden 校验规则

golden 必须包含上述展示结构，不能只有 `expected_content` 和 `expected_anchor`。

必查项：

- 每题 `answer` 干净独立，无跨题答案串。
- 综合题有 `is_composite=true` 且有非空 `sub_questions`。
- 共享材料只保存在 `shared_material`，子题不重复复制整篇文章。
- 文言注释单独保存为 `shared_material_notes`，不混入题干。
- 配图有 `page/bbox/placement/source/anchor`。
- 答案图有 `answer_images`。
- 写作答案完整，不能是 `"例文"`。
- 大写作直接按一道题建模，不拆 `choices`，也不当作必做 `sub_questions`。
- 理科公式标准化后仍保留 OCR 原文 provenance。
- 七选五保留 A-G 和 extra_options。
- 词库题保留 `word_bank`。
- 默写、表格题、任务题保留 `scoring_standard` 和 `answer_structure`。

## 6. 已确认/建议结论

1. 有整篇选段的语文阅读统一建模为综合题。
2. 评分标准放 `scoring_standard`。
3. 表格题 `answer_structure` 示例见 §4.12。
4. 小写作必做任务建模为 `sub_questions`；大写作直接按一道题建模，不引入 `choices`。
5. 文言注释单独保存为 `shared_material_notes`。
