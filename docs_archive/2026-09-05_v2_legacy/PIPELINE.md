# AI Tutor Personal Edition — 文档入库管线规范

Version: 5.1
Status: Phase 0 文档冻结基线；v0.3 与权威文档同步待评审
Date: 2026-09-04
Supersedes: PIPELINE v4.2
Source of truth: `Docs/00_Requirements/REQUIREMENTS_AND_SOLUTION.md`

---

## 0. 已确认架构结论（2026-09-03）

### 0.0 最高优先级声明

本文件进入 Phase 0 冻结后，文档入库新链只接受：

```text
Immutable Source Version
  → Semantic Metadata Annotation
  → Source Resolver
  → Semantic Question IR
  → Deterministic Compiler
  → Semantic/Evidence Gate
  → Admission
```

Semantic Metadata Annotation 是 LLM 与新链之间的唯一语义入口。Annotation 禁止包含
`line_ref/corrected_line_ids/resolved_span/final_line_ids`，也禁止输出
stem/material/options/answer/explanation 正文。`canonical_question_type` 只属于
Semantic IR/Compiler 输出。

正文中凡描述“LLM 输出行号/粗略行号、Anchor Correction、anchor_status=exact/nearest、
Content Slicer 按行切片、quality gate/admission gate 旧规则”的内容均为旧链 legacy
诊断参考，不作为新链实现依据。详细契约见：

- `docs_archive/2026-09-03/00_SemanticPipeline_Development_Guide_v0.3.md`
- `docs_archive/2026-09-03/01_ImmutableSource_Persistence_Contract_Draft_v0.3.md`
- `docs_archive/2026-09-03/02_SemanticMetadata_Annotation_Contract_Draft_v0.3.md`
- `docs_archive/2026-09-03/03_SourceResolver_SemanticIR_Gate_Contract_Draft_v0.3.md`
- `docs_archive/2026-09-03/04_Phase0_Change_Scope_and_Acceptance_v0.3.md`

### 0.1 核心原则

LLM 负责理解语义，程序负责确定事实。原始 Markdown 永久不可变，LLM 不得重写
正文、不得计算最终行号/坐标、不得替代 Source Resolver。程序只能消费 sealed
source version，任何 raw/canonical L1 都必须在 seal 后进入下游。

### 0.2 当前根因

当前 L2 主要表达 line_id，信息粒度不足以表达题目依赖、共享材料、空位映射、
子题归属、选项/答案对应关系；后续代码只能按行机械切片和做字段非空检查。

### 0.3 目标管线

```text
L1 Immutable Source Markdown
  ↓
Source Index + LLM Semantic Metadata Annotation
  ↓
Source Resolver
  ↓
Semantic Question IR
  ↓
Deterministic Compiler
  ↓
Semantic + Evidence Gate
  ↓
Candidate / Admission
```

### 0.4 职责边界

- LLM：输出 semantic unit/role/label/dependency/mapping 等语义 claim，最多携带
  original_question_type，不输出 canonical type 和坐标。
- Source Resolver：Exact → Normalized → Context/Structural → Fuzzy/Ambiguous；
  fuzzy/ambiguous 不自动通过，必要时才走显式 disambiguation/review。
- Semantic Question IR：已解析 span + 语义链接，是确定性编译的中间表示。
- Compiler：IR → 最终题目/综合题/子题对象。
- Gate：Structural、Provenance、Semantic、Admission 四层，禁止用“字段非空”替代语义证据。

### 0.5 综合题规则

- 独立题 = 去掉共享材料后仍可独立解答。
- 综合题 = 一份共享材料 + 依赖该材料的子题，作为整体 Admission Unit。
- 任一子题不可靠，整个综合题进入 Candidate/Reject，禁止部分入库。
- 共享材料只保存一次，不得复制到每个子题 stem。

### 0.6 答案验证

`source_located`、`complete`、`verified_correct` 必须分离；
找到答案来源 ≠ 答案完整 ≠ 答案正确。

### 0.7 实施顺序

Phase 0 要求 v0.3 总纲、契约与权威 PIPELINE/DSD/DICTIONARY/ACS 作为同一次冻结
交付。Phase 0 通过后才能进入 Phase 1 Immutable Source、Phase 2 Semantic
Annotation、Phase 3 Resolver/IR、Phase 4 Compiler、Phase 5 Gate、Phase 6 Golden
迁移。
在 Phase 0 通过前，不启动 Candidate Admission 业务堆叠、旧 Gate 补丁和
0.5B Structure Annotator 训练。

### 0.8 旧链到 v0.3 新链阶段映射

| 旧链位置 | 旧职责 | v0.3 新职责 |
|---|---|---|
| `line_annotator.py` | LLM 输出行号并解析成 L2 question list | Semantic Metadata Annotation 输出 semantic units/references |
| `semantic_anchor.py` / `anchor_corrector.py` | marker 模糊定位/吸附/校正 line_id | Source Resolver exact/normalized/contextual 解析；无 nearest 自动通过 |
| `content_slicer.py` | 按 corrected line_id 切 stem/options/material | Deterministic Compiler 从 resolved IR span 编译正文 |
| `quality_gate.py` | confidence/issues 判断 | Structural/Provenance/Semantic Gate 分层 |
| `answer_matcher.py` / `answer_extractor.py` | 规则/LLM 匹配答案并置 verified | Answer Verifier 对 resolved answer span 做 source_located/complete/verified_correct |
| `admission_gate.py` | 旧 R01-R18 三态入库 | Semantic IR + Evidence Gate 输出 approved/candidate/rejected |
| `ingestion.py` | 直接 consume SlicedQuestion | consume Compiler 输出 + IR provenance，再落库 |

## 1. 目标

本管线负责将教师版 PDF/DOCX 转换为结构化题库数据。

最终输出：

- 题目内容：题干、选项、答案、详解、配图
- 元数据：学科、年级、年份、学校、题型、分值、难度、知识点、出现次数
- 状态：高置信度自动入库，低置信度进入人工审核

### 1.1 V1 教训固化（LEGACY，仅诊断参考）

> 本节仍执行 V1 历史记录，但其中“LLM 只输出行号/元数据”“LLM 行号只是粗定位，
> 代码必须做锚点校正后再切片”“复合题 section 级切分/quality gate 部分保存/L2
> 行号透传”全部属于旧链 legacy。新链见 §0.0。

- LLM 只输出行号/元数据，不输出题干原文；代码从 L1 原文切片。
- LLM 行号只是粗定位；代码必须做锚点校正后再切片。
- PDF 采用双源证据路由：PyMuPDF native 与 PP-StructureV3 并存，canonical L1 由代码按行选择；不再以单一提取器为整份正文基座。
- 配图必须携带 `page/bbox/placement/source`，禁止猜页和整页兜底。
- 教师版答案/详解优先，LLM 推理只做缺失项兜底并保留来源。
- JSONL 必须遍历全部 `layoutParsingResults`，并用 `extractProgress` 校验页面完整性。
- 复合题 section 级切分、quality gate 部分保存、单行选项、L2 行号透传、OCR 题号换行、答案区不截断、Solution draft 等按 `V1_LESSONS.md` 3.16-3.29 执行。

---

## 2. 输入范围

支持：

- 带文字层的 PDF
- 排版规范的 DOCX
- 扫描版或图片型 PDF

扫描版和图片型 PDF 会进入 OCR/VL 处理，识别结果默认按低置信度处理。

单个文件上限：50MB。

---

## 3. 管线总览（LEGACY）

> 本节描述旧链十个阶段。新链阶段见 §0.0 和
> `docs_archive/2026-09-03/03_SourceResolver_SemanticIR_Gate_Contract_Draft_v0.3.md`。

```text
1. 上传与原始文件存储
2. 源文件解析
3. 文本/公式/表格/图片提取
4. 题目切分
5. 配图关联
6. 答案与详解匹配
7. 元数据标注
8. 置信度判断
9. 重复题合并
10. 入库与异步富化
```

---

## 4. 阶段说明（LEGACY）

> §4.2/§4.3 的 raw/native/PP/DOCX 提取可作为新链 source producer 的输入来源，
> 但 §4.4 起的题目切分、答案匹配、quality gate、admission gate 均为旧链路径。

### 4.1 上传与原始文件存储

- 管理员批量上传 PDF/DOCX。
- 原始文件写入 MinIO 或 NAS 对象存储。
- 创建 documents 记录。
- 解析任务进入统一 Background Task 队列。

### 4.2 源文件解析

PDF：

- 生成两份 raw L1：PyMuPDF native 文本层（行号 `N1L001`）、PP-StructureV3 OCR/Layout（行号 `P1L001`）。
- PyMuPDF 负责页面尺寸、图片 xref/bbox、答案表定位、上下标几何信息。
- PP-StructureV3 负责公式符号、复杂版面、扫描页和视觉识别。
- 代码按每行/每区块证据生成 canonical L1，保留 `raw_sources/selected_source/evidence/confidence`；canonical 保留 PP 行号体系，native 行号通过 `raw_sources["native_line_id"]` 溯源。
- 上下标/化学式/计量单位默认双源校验；冲突时进入低置信度，禁止直接接受 PP。

DOCX：

- 解析段落、表格、图片和公式对象。
- 尽量利用 Word 排版结构辅助题目切分。

### 4.3 文本/公式/表格/图片提取

输出统一的中间表示：

- 文本块
- 公式块
- 表格块
- 图片块
- 题目编号和题型线索
- 每页按行编号的 canonical L1（canonical 使用 PP 行号；native/ppsv3 raw L1 保留为可追溯源，native 行号写入 raw_sources）
- 图片的 `page/bbox/placement/source` 元数据

公式内部使用结构化表示，页面和导出时渲染为印刷体，不显示 LaTeX 源码。

### 4.4 题目切分（LEGACY，新链不再采用）

> 本节描述旧链“LLM 输出粗略行号范围 → Anchor Corrector → Content Slicer”路径。
> 该路径已被真实 E2E 证伪，不再作为 active 设计；继续保留只为旧代码和旧测试提供
> 诊断参考。

旧链历史行为：

- LLM 输出题号、题型、`stem_lines/options_lines/answer_lines/explanation_lines`
  等粗略行号范围。
- 代码先对粗略行号做锚点校正，保存 `llm_anchor/corrected_anchor/anchor_status`。
- 只有 `anchor_status` 为 `exact` 或 `nearest` 且内容校验通过时才切片入库。

新链替代：

1. LLM Semantic Metadata Annotation 输出 semantic unit、role、dependency、
   blank/option/answer/image 归属，不输出行号。
2. Source Resolver 在 sealed source version 上把 role/label/marker 解析成
   resolved source span。
3. Semantic Question IR 保存已解析 span 和关系。
4. Deterministic Compiler 从 IR 编译成题目/综合题对象。

任何新实现不得继续把本节的旧路径作为核心。

### 4.5 配图关联（LEGACY 流程；新链按 IR image_reference 编译）

- 数学/物理/化学中的几何图、电路图、装置图、函数图需要独立截取。
- 图片资源写入对象存储。
- 每张配图与 question_id 建立关联。
- 每张配图必须保留 `page_no/bbox/placement/source`。
- 图片去重是文档级，同一物理图只关联一个题目；bbox 用 IoU/中心距离判断。
- 无 page/bbox 时禁止整页猜测或自动关联，记录 `missing_figure` 并进入审核。
- 如果题目本身是图片，保留原图，并尽量提取图片文本。

### 4.6 答案与详解匹配（LEGACY 流程；新链按 resolved answer span + Answer Verification）

支持两种结构：

- 文末答案：按题号反查。
- 题后答案：就近匹配。

匹配规则：

- 优先使用教师版文档结构信息和参考答案区原文。
- LLM 负责判断答案归属和解释归属。
- LLM 答案/详解只能作为缺失项兜底，并标记 `llm_generated` 来源。
- 匹配失败进入低置信度审核。

### 4.7 元数据标注（LEGACY；新链按 Annotation metadata claims + Compiler 落事实）

使用 LLM 按规范自动标注：

- 学科
- 年级
- 年份
- 学校
- 题型
- 分值
- 难度
- 知识点

元数据必须符合 `Docs/03_Data/DSD.md` 中的定义。

来源优先级：

1. 上传表单/文件名/文档路径解析出的元数据。
2. 高置信度 LLM 标注。
3. 任何 `None` 不得写成字符串 `"None"`。

### 4.8 置信度判断（LEGACY；confidence 不是 semantic proof）

判定维度：

- 题目切分是否完整
- 题干是否完整
- 答案是否匹配
- 详解是否匹配
- 配图是否关联
- 元数据是否可信
- 内容是否完整（选项数量、公式/符号保留、表格/图表识别）

高置信度自动入库。

低置信度进入审核队列，由管理员修正后入库。

### 4.11 页面与内容完整性（基础校验可复用，语义 Gate 见 03 契约）

- JSONL/OCR 任务必须检查 `extractProgress`，`extractedPages < totalPages` 时告警或失败。
- 选择题必须校验选项数量与重复项。
- 对公式、希腊字母、关键符号做保留检查。
- ASCII 表格、HTML 表格、茎叶图等按表格/图片处理，不能作为普通文本静默接受。

### 4.9 重复题合并（LEGACY；新链先 Admission 后按 Question 内容去重）

查重方式：

- 文本规则匹配。
- embedding 语义相似度。

同一道题重复出现时：

- 合并为一道题。
- 保留多个来源信息。
- 累加出现次数。

### 4.10 入库与异步富化（LEGACY；新链由 Compiler/Gate 决定 admission）

入库后通过统一 Background Task 异步执行：

- 生成 embedding。
- 更新出现次数统计。
- 校验答案和详解完整性。
- 生成可供统计分析使用的聚合数据。

---

## 5. 准确率策略（LEGACY 指标；新链验收以 04_Phase0 黄金清单为准）

- 高优先级科目：数学、物理、化学、英语、语文、生物、政治。
- 使用字段级指标验收，不只用单一“95%准确率”。
- 其他科目可以适当降低精度要求。
- 开发阶段使用真实教师版文档建立测试集，按科目统计准确率。

字段级目标：

| 指标 | 目标 |
|---|---|
| 题目切分准确率 | 98% |
| 题干提取准确率 | 98% |
| 题号识别准确率 | 98% |
| 答案匹配准确率 | 95% |
| 详解匹配准确率 | 90% |
| 配图关联准确率 | 90% |
| 学科/年级/年份/学校元数据 | 95% |
| 题型识别准确率 | 95% |
| 知识点映射准确率 | 85%，低置信度人工修正 |
| 自动通过题目无需修改比例 | 95% |
| 100 道题人工审核时间 | 10 分钟内 |

说明：

- 自动通过题目无需修改比例是“减少人工”的核心指标。
- 审核效率用于验证 Human-in-the-loop 的成本是否可控。

---

## 6. 模型分工（LEGACY 旧链；新链补充 Semantic Annotator/Resolver/Compiler 为程序模块）

| 任务 | 模型/方式 |
|---|---|
| PDF 版面解析 | PyMuPDF native + OCR 双源；canonical L1 按证据选择 |
| DOCX 解析 | 本地解析 + LLM 结构化 |
| OCR（学科路由）| 化学 → PaddleOCR-VL；其余 → PP-StructureV3（见 V1_LESSONS 3.30） |
| 题目切分 | LLM |
| 配图截取 | 本地图像处理 + 文档结构 |
| 答案匹配 | 文档结构 + LLM |
| 元数据标注 | DeepSeek / MIMO |
| embedding | NAS 本地轻量模型 |
| 难度评估 | LLM + 规则 + 学习数据 |

所有 LLM 调用必须经过 LLM Gateway。

---

## 7. 配置项（基础 OCR/LLM 配置可复用）

主要配置项：

| 配置 | 说明 |
|---|---|
| PADDLEOCR_VL_ENABLED | 是否启用 PP-StructureV3 |
| PADDLEOCR_VL_TOKEN | PP-StructureV3 API Token |
| PADDLEOCR_API_BASE_URL | PP-StructureV3 API 地址 |
| PADDLEOCR_POLL_INTERVAL_SECONDS | PP-StructureV3 任务轮询间隔 |
| PADDLEOCR_JOB_TIMEOUT_SECONDS | PP-StructureV3 任务超时 |
| NATIVE_MARKDOWN_ENABLED | 是否启用电子文本 PDF Native Markdown |
| NATIVE_TEXT_THRESHOLD | Native 文本层覆盖率阈值 |
| DEEPSEEK_API_KEY | DeepSeek API Key |
| MIMO_API_KEY | MIMO API Key |
| MIMO_BASE_URL | MIMO OpenAI 兼容地址 |
| MIMO_MODEL | MIMO 模型名 |
| DEEPSEEK_VL_MODEL | DeepSeek Vision 模型名（VL 回退） |
| MIMO_VL_MODEL | MIMO 多模态模型名（VL 首选） |
| EMBEDDING_PROVIDER | Ollama |
| EMBEDDING_MODEL | qwen3-embedding:4b |
| EMBEDDING_DIMENSION | 2560 |
| DOCUMENT_MAX_SIZE_MB | 单文件大小上限，默认 50 |
| BATCH_UPLOAD_LIMIT | 批量上传上限 |
| AUTO_APPROVE_THRESHOLD | 高置信度自动入库阈值 |

API Key 必须通过 `.env` 管理，禁止硬编码。

---

## 8. 目标源码结构（LEGACY，不指导新链）

> 本节代码结构描述旧链文件。新链实现位置由 v0.3 契约的 Phase 顺序和边界决定，
> 禁止把 `line_annotation.py/anchor_corrector.py/content_slicer.py` 作为新链核心。

建议按以下结构实现：

```text
backend/app/domains/document/
├── api.py
├── service.py
├── pdf_parser.py
├── docx_parser.py
├── image_extractor.py
├── question_splitter.py
├── answer_matcher.py
├── metadata_annotator.py
├── confidence.py
├── question_extractor.py
├── parser.py
├── evaluation.py
├── native_markdown.py
├── line_annotation.py
├── image_metadata.py
├── ocr/
│   ├── __init__.py
│   ├── paddle_client.py
│   └── providers.py
└── tasks.py
```

当前 P2 已落地部分：`ocr/paddle_client.py` 负责 PP-StructureV3 提交、轮询和 JSONL 解析；`question_extractor.py` 通过 LLM Gateway 输出 Question Aggregate JSON。

> **2026-08-25 起（OCR Provider 策略，见 `OCR_PROVIDER_POLICY.md`）**：
> L1 识别仅使用 paddle 系（PP-StructureV3 / PaddleOCR-VL，学科路由）；
> **mimo-vl / deepseek-vl 移出 OCR 驱动链**（不再自动降级驱动入库），
> 仅保留为可选交叉验证入口（默认关）。paddle 不可用时任务标记
> `ocr_unavailable` 等待恢复重跑，不降级 LLM VL。

注意：当前 `question_extractor.py` 仍是临时验证版，允许 LLM 直接输出内容文本。
该文件与“粗略行号标注 + 代码锚点校正”范式都属于旧链，禁止复用到新链正式入库链路。

## 9. 表格选项提取（LEGACY 旧链行号处理；新链以 source index/table_cell span 表达）

- 化学等试卷的选项可能位于 HTML table，PPS/VL 直接按行拆分会丢失选项内容。
- **方案（2026-08-26 定稿，见 LOG v6.37）**：仅对**选项表**（选项标签 A/B/C/D 在
  表格内部，即 `<td>A</td>` 作为表格行的一部分）拆行——把含选项标签的行拆成
  独立 L1 行（`A. ` 前缀 + 其余 `<td>` 用 `，` 合并，保留 VL 公式文本）；
  **资料表/答案表**（选项在表格外的普通行，或表格单元格内容是数据而非选项）
  保持单行不动。区分判据：表格内部首列存在 A-G 标签且该行 ≥2 列 → 选项表。
- 集成点：`ocr_l1_converter.py` 的 `_split_block_lines` / `_split_markdown_lines`
  （VL 表格单行合并处）拆行后 L1 行号重排，LLM 看到独立行、给出独立行号，
  锚点校验（`_STRICT_OPTION_LABEL_RE`）与选项切片（`_strip_option_label`）
  无需改动即可工作。
- 已验证：Q8（五行表）、Q10（2×2 图+文）、Q1（大兴 5 列表）、Q6（装置表）
  拆行后均可被标签正则识别；Q13（资料表，选项在表外）不受影响。
- 验收必须覆盖化学表格选项题。

## 10. PP 主路径（LEGACY）

> `simple_pipeline.py` 是旧链 active，不是新链 active。新链 active 路径见 §0.0。

- 主路径为 `simple_pipeline.py`：PP canonical 为正文源，native 只做证据补充，LLM 输出行号/锚点，代码负责定位与切片。
- `pipeline.py`、`l1_arbiter.py` 保留为 fallback。
- 详细实验过程和归档版本见 `docs_archive/2026-08-24/SIMPLE_PIPELINE.md`。

> 变更记录统一记录在根目录 `LOG.md`；历史版本文档见 `docs_archive/2026-08-24/`。
