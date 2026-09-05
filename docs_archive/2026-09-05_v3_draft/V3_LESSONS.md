# AI Tutor V3 — V1/V2 失败经验与反模式清单

Version: 3.0
Date: 2026-09-05
Status: V3 强制设计输入

## 1. 总结

V1/V2 最大的问题不是某一个 OCR、LLM 或正则错误，而是把“不确定的语义判断”“确定性的文本编译”“异步任务生命周期”“外部 API 副作用”和“数据库入库”混在了一起。

V3 的首要任务不是继续增加规则，而是重新建立边界。

## 2. V1 已证明的问题

### 2.1 让 LLM 抄写题目会产生信息损失

V1 早期让 LLM 输出完整题干、选项、答案、解析，出现 LaTeX 转义、内容遗漏和格式损坏。

**V3 原则：** LLM 输出语义标注和短 anchor；Source 才提供最终内容。

### 2.2 行号不是事实，只是定位线索

V1/V2 中 LLM 行号存在偏移，随后不断增加 anchor correction、fuzzy match、next-question truncation 等补丁。

**V3 原则：** 让 LLM 给“我要找什么”，由 Source Resolver 根据稳定文本证据解析“它在哪里”。坐标属于 Resolver 的产物，不属于 LLM 的事实输出。

### 2.3 单一 L1 提取器会把错误传播到全链路

Native PDF 文本和 OCR 对公式、上下标、复杂版面各有损失。

**V3 原则：** Source 层保留多个 raw artifact；canonicalization 必须是显式阶段并保留 provenance。

### 2.4 图片不能靠题号或整页猜测

V1/V2 出现跨题广播、整页兜底、bbox 精确匹配过严等问题。

**V3 原则：** 图片是有空间证据的 Source Entity；page/bbox/placement/provenance 必须独立保存。没有证据就进入 review。

### 2.5 答案“找到”不等于“正确”

V1/V2 曾出现短答案只要在答案区出现就被判定成功的假阳性。

**V3 原则：** 至少区分：source_located、complete、content_verified、approved。

### 2.6 Composite 不应靠 section 规则强行构造

V2 曾在“共享材料”“section”“子题号”“父题”之间不断增加特判，最终出现材料重复、子题丢失、独立题被错误合并等问题。

**V3 原则：** Composite 是语义模型，不是 section 模型。共享材料 + 明确依赖关系才构成 composite；仅仅同处一个 section 不足以合并。

## 3. V2 暴露的架构级问题

### 3.1 API 与 Worker 共进程

V2 `main.py` 的 lifespan 可以直接启动 document worker。结果是“启动 API”具有隐藏的 LLM 副作用。

**V3 禁止：** API 进程启动任何任务消费者。

### 3.2 Zombie Task 自动 requeue

V2 对 stale running task 自动 reset 为 queued，使进程重启可能重复执行同一文档。

**V3 禁止：** running 超时自动回 queued。只能进入 interrupted，并等待人工 retry。

### 3.3 多层 retry 形成乘法

V2 同时存在 pipeline retry、Gateway provider retry、provider fallback、answer retry worker 等机制。

**V3 原则：** 每一层 retry 必须有责任边界，并且 Task 有总调用上限作为最后熔断器。

### 3.4 Worker claim 缺少严格生命周期边界

如果多个 Worker 可以同时看到 queued task，再分别 UPDATE running，就会造成重复消费和重复 API 调用。

**V3 原则：** atomic claim + lease + lease token + heartbeat。

### 3.5 Candidate / Admission 与真正入库模型脱节

V2 曾出现 approve 只创建 Question，却没有完整创建 Instance/Image/Knowledge；Candidate 又缺乏重建完整实体所需数据。

**V3 原则：** Candidate 必须是完整、不可变、可重放的 admission snapshot；批准操作必须是一个事务内的完整 materialization。

### 3.6 数据模型不断用 JSONB 吸收设计矛盾

V2 的 `sub_questions`、`answer_structure` 等 JSONB 逐步承担业务关系、结构和展示职责，导致 schema 漂移。

**V3 原则：** JSONB 只承载真正动态的结构；稳定的实体关系必须使用关系表/明确模型。

### 3.7 “让 LLM 最大化发挥能力”被错误解释

V2 曾形成“LLM 能判断的都交给 LLM”的倾向，同时又要求 LLM 输出大量行号、section、答案、切片边界等。

**V3 原则：** LLM 最大化发挥应体现在语义理解，而不是替代确定性编译器。LLM 判断，代码执行；代码不能猜语义，但也不能让 LLM 操作数据库事实。

### 3.8 质量门禁过于关注字段非空

V2 Admission Gate 曾有很多规则，但真实 E2E 仍出现“11/11 approve”的情况，而 Q45 的答案只是部分匹配也被视为 verified。

**V3 原则：** Gate 必须验证语义完整性、Source evidence、独立可答性和 composite 一致性，而不仅是字段存在。

### 3.9 通过大量补丁追逐数据集 corner case

V2 出现大量针对单题号、section、答案格式、OCR 变体的回填和特殊函数。

**V3 原则：** 如果一个 bug 需要为具体题号写特判，应先检查信息模型是否缺少表达能力。

### 3.10 测试环境与生产行为边界不清

V1/V2 曾出现 pytest 真实调用外部服务、旧进程继续消费队列、reload 影响验证等问题。

**V3 原则：** 默认 mock；live 必须显式 allow；API/Worker/Provider 生命周期独立测试。

## 4. V3 反模式红线

禁止：

- API startup → worker
- worker startup → automatic recovery
- stale → queued
- LLM → database direct write
- Provider direct call from business domain
- LLM output → final source text
- fuzzy match → silent acceptance
- missing evidence → guessed image/answer
- nested retry without global budget
- production pipeline branches kept only for historical compatibility
- one-off question-number special cases in core pipeline
- schema changes without migration
- live API calls in default tests

## 5. V3 设计判断口诀

```text
语义问题 → LLM
事实来源 → Source
位置解析 → Resolver
确定性转换 → Compiler
质量判断 → Gate
数据库写入 → Application/Repository
异步消费 → Explicit Worker
外部副作用 → Gateway + Audit + Budget
```
