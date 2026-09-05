# AI Tutor 语义入库管线开发指引

Version: GUIDE-0.3
Status: Phase 0 开发前总纲（有条件通过）；未启动代码
Date: 2026-09-04
目的：把已确认的语义管线方向固化为下一步开发可执行的指引，并防止旧管线的
结构性问题在新管线中复现。

## 0. 文档关系

本文件是总纲，解决“为什么这样设计、按什么顺序开发、什么时候算完成”的问题。

配套详细契约：

1. `01_ImmutableSource_Persistence_Contract_Draft_v0.3.md`
2. `02_SemanticMetadata_Annotation_Contract_Draft_v0.3.md`
3. `03_SourceResolver_SemanticIR_Gate_Contract_Draft_v0.3.md`
4. `04_Phase0_Change_Scope_and_Acceptance_v0.3.md`

进入代码前，应先完成本文件第 5 节的 Phase 0 DoD，并以对应详细契约为准。

## 1. 第一性原理

### 1.1 原始事实不可再生

PDF/DOCX 经 OCR、Native 提取、行拆分、去重后得到的文本一旦丢失，后续无法可靠恢复。
因此正文、行、图片、provider、bbox、evidence 必须先成为 sealed source，再进入下游。

### 1.2 LLM 只产生语义 claim，不产生位置事实

“这是题目 11 的子题”“它依赖 M1”“这个 blank 属于 11”是语义判断，可以由 LLM 表达。
“P1L005 到 P1L009”是位置事实，必须由程序从 sealed source 中解析。
位置解析只能被验证，不能由 LLM 代算，也不能由后处理规则猜补。

### 1.3 question 是模型核心，line 不是

中间表示必须是可编译成 question/composite 的语义对象，而不是行号包。
一行文本只有在被某个 semantic role 指向后才成为该 question 的证据；
不允许系统先切行、再拼凑成题。

### 1.4 组合关系必须显式

连续题号不等于共享材料；同 section 不等于共享材料；共享行号不等于独立题。
唯一可信的组合来源是 Annotation 中显式的 semantic unit + dependency，
Resolver 解析后由 IR/Gate 校验。代码不得按重叠行号或邻近关系重建组合。

### 1.5 Admission 不能替代上游

Gate 只能拒绝证据不足的候选，不能把错误内容改成正确内容。
任何需要语义猜测才能通过的结果，应进入 incomplete/candidate/review，
而不是增加一条后处理规则或 R 规则继续放行。

### 1.6 最小可实现系统优先

个人系统规模下，先实现单文档、串行、可回放、可审计的最小闭环；
不先做批量队列、向量检索、训练数据平台或通用题型解析器。

## 2. 旧管线痛点与规避矩阵

| 旧管线现象 | 根因 | 新管线规避 | 对应契约 | 回归门 |
|---|---|---|---|---|
| 东城英语 11/11 approved，入库内容仍是灾难 | Gate 只做字段/来源/布尔 verified 判断 | 先建 IR，Gate 只对 ready IR 放行 | 03 §8-13 | Gate 不接收无 IR 对象 |
| L2 主要表达 line_id | LLM 被要求输出行号，中间层没有题目语义 | LLM payload 禁止 line_ref，Resolver 负责定位 | 02 §4、§10 | Annotation schema 禁止字段 |
| 重复子题材料 | 代码按共享行号合并/把材料并进独立 stem | Material 是独立 span，编译器只保存一次 | 01 §8、03 §8.2 | IR 无重叠 material/stem span |
| 词库与答案不一致 | 语义关系没有落成 dependency/mapping | word_bank/option_pool/answer 关系显式 | 02 §8-9 | IR 悬空引用检测 |
| 答案截断 | 用子串存在代替完整答案 | source_located/complete/verified_correct 分离 | 03 §13 | Answer Status 三字段独立断言 |
| question_type_id 缺失 | 自由字符串直接映射，缺少编译契约 | Compiler 按原始类型生成 canonical type，Gate 校验映射结果 | 03 §10 | Compiler 输出 schema 校验 |
| 代码到处补语义 | 每次用正则/if/else 修上次 LLM 错误 | 语义决策留在 Annotation；程序只做解析和编译 | 02 §2、03 §10 | 禁止语义后处理规则 |
| fuzzy/nearest 被接受 | 锚点校正用近似匹配并静默接受 | 只有 exact/normalized/contextual 且证据闭合可自动 | 03 §4 | resolver status 测试 |
| 综合题被拆成独立题或独立题被误并 | 代码按题号/重叠猜组合 | Annotation 是唯一组合声明来源 | 02 §7、§16 | 组合一致性 golden |
| 任意一道子题坏了，父题仍 approved | 检查只落在字段级 | Composite 是 Admission Unit | 03 §12.1 | 原子性测试 |
| 重跑覆盖旧证据 | 只有 documents 三个 markdown 文本字段 | sealed source version + active pointer | 01 §9、§15 | repository update 拒绝测试 |
| verified=True 不等于正确 | 把“找到来源”当验证 | verified_correct 需要权威/人工确认 | 03 §13 | 三字段语义测试 |

## 3. 核心对象与边界

```text
documents (上传元数据)
  └── document_source_versions (raw/canonical sealed source)
        └── document_source_lines
        └── document_source_lines_image_refs

semantic annotation run
  └── semantic units / dependencies / semantic references

source resolver run
  └── resolved spans / resolved relations

semantic question ir
  └── standalone/composite units

deterministic compiler
  └── question/composite objects compatible with DISPLAY_CONTRACT

semantic/evidence gate
  └── admission decision
```

边界约束：

- Source 只能被读取，不能被 Annotation/Resolver/Compiler 修改。
- Annotation 只携带 claim，不携带 resolved span。
- IR 只接受已解析的 span，不接受未解析的 question_label 字符串。
- Compiler 只做确定性编译，不改变 IR。
- Gate 只判断 IR/Compiler 结果是否满足 admission 标准，不修改内容。

## 4. Question 为核心的实现约束

1. 每一道入库题都必须能从某个 semantic unit + resolved span 回溯到 sealed source。
2. 每个 semantic unit 必须有稳定的 document-local question identity，如 Q1、Q11-13、Q11。
3. 共享组件属于 composite unit，不属于任何单个子题；子题只保存 dependency。
4. blank/option/answer/image 都必须有 owner，owner 只能是 question 或 composite unit。
5. 同一个 document-local question 不得属于两个 unit。
6. 数据库 Question 是内容事实，QuestionInstance 是来源事实；Source Version 是证据事实。

## 5. 开发顺序与 DoD

### Phase 0：文档冻结

交付物：

- 本总纲、01/02/03 v0.3 契约与权威 PIPELINE/DSD/DICTIONARY/ACS 作为同一次冻结
  交付，禁止“先批准契约、之后再同步权威文档”。
- `04_Phase0_Change_Scope_and_Acceptance_v0.3.md` 通过评审。
- 权威文档同步完成：
  - PIPELINE：旧 LLM 行号/Anchor/Line Slicer 正文全部标记 legacy，§0 为新链唯一入口。
  - DSD：删除 L1/L2 不落库，落定 source/annotation/resolver/IR 表与迁移策略。
  - DICTIONARY：语义术语冻结，旧概念标 legacy，状态字典统一。
  - ACS：本轮端点变更范围和 provenance 字段说明已列出。
- 最小 golden 清单、测试迁移策略、seal 性能验收已输出。
- 状态文档已把旧链历史/旧 Gate 冻结，RESTART 恢复流程先读 v0.3 再读权威文档。

### Phase 1：Immutable Source Persistence

交付物：

- DSD 定稿 source version/line/image/active pointer/selection event。
- Alembic migration 与 ORM/Repository。
- 现有 L1 产出函数改为“纯函数构造 + 一次性 seal”。
- `documents.native_markdown/ocr_markdown` 只保留为 legacy 兼容镜像。

DoD：

- 相同输入两次 seal 得到相同 hash。
- 篡改任意一行会改变 integrity_hash 或校验失败。
- sealed 后无法 update/delete。
- 重跑产生新 version，旧 annotation 仍可按旧 source_version_id 回放。

### Phase 2：Semantic Metadata Annotation

交付物：

- Annotation schema + 递归禁字段校验。
- Prompt 构造：LLM 不看到行号，输出 semantic units/references/relations。
- Annotation Run 持久化。

DoD：

- JSON 不含 line_refs/corrected_line_ids/resolved_span/答案正文。
- 每个 dependency target 存在。
- instruction_marker 缺失或多命中时不会自动解析。
- 同一 source + 同一 prompt 输出可回放。

### Phase 3：Source Resolver + Semantic Question IR

交付物：

- Resolver 输入 sealed source + annotation。
- 输出 resolved span/relation，不修改 annotation。
- IR schema 与状态机。

DoD：

- exact/normalized/contextual 有唯一证据才能 resolved。
- ambiguous/missing/incomplete 不能进入 ready IR。
- composite 任一子题 unresolved，整组不 ready。
- IR 中 material span 与子题 stem span 不重叠。

### Phase 4：Deterministic Compiler

交付物：

- IR 到 DISPLAY_CONTRACT question/composite 的编译实现。
- question type 的 canonical 映射和缺失处理。

DoD：

- 相同 IR 产出相同对象。
- Compiler 不生成无 source span 的正文。
- 不复制共享材料。
- 输出对象可被现有前端/API schema 消费。

### Phase 5：Semantic/Evidence Gate + Admission

交付物：

- Structural/Provenance/Semantic/Admission 分层。
- Answer Status 三字段实现。
- Allowed-Answer Grammar 文档与首批题型正例/反例（见 03 §13.1、04 §5.1）。
- Phase 5 先补 DISPLAY_CONTRACT 的 true_false canonical 映射，再启用 strict auto
  verified_correct。
- Composite 原子决策。

DoD：

- 没有 ready IR 的对象不能 approved。
- 答案 source_located 不等于 complete/verified_correct。
- 没有 Allowed-Answer Grammar 的题型不能走 strict auto verified_correct。
- 任一子题不完整，整个 composite 不 approved。
- candidate/review 必须有可审计原因，不静默吞掉。

### Phase 6：Golden、迁移与替换

交付物：

- 新链 golden 验收。
- 旧链结果保留，但新链成为 active。
- 历史文档按需回填 source version。

DoD：

- golden 覆盖独立题、材料综合题、空位、词库、共享选项池、答案表、写作题。
- 不启动 0.5B Structure Annotator 训练，直到新链 golden 达到自动标准。

## 6. 本阶段冻结项

在 01/02/03 通过评审并完成 Phase 1-3 前，禁止：

- 继续给旧 `admission_gate.py` 增加 R 规则。
- 继续给旧 `quality_gate.py`、`content_slicer.py`、`anchor_corrector.py` 增加语义猜测。
- 把新 semantic IR 直接写入 questions 表。
- 用旧 answer_extractor 的输出作为新链 verified_correct。
- 开始 0.5B Structure Annotator 训练。
- 继续堆叠 question_candidates 业务功能，除非用于迁移/回放验证。

## 7. 文档更新要求

1. 每次修订同步更新版本号、状态、Date。
2. 新增字段/状态/API 必须在 DICTIONARY 有对应条目。
3. 变更后运行 `backend/scripts/validate_docs_vs_code.py`。
4. 在 `LOG.md` 文末追加完整时间戳记录。
