# AI Tutor V3 — 系统基线与重建总规范

Version: 3.0-draft
Status: V3 重建基线
Date: 2026-09-05

> 本文档用于从 V1/V2 经验重新建立 V3 的系统边界。
> V3 不以修复 V2 代码为目标，而以保留已确认业务需求、删除已证明有害的架构复杂度为目标。

## 1. V3 重建原则

### 1.1 重建而非迁移

V3 默认不继承 V2 的代码、数据库结构、任务状态、历史兼容层和临时修复逻辑。

只继承三类内容：

1. 已确认的业务需求。
2. 已验证有效的外部能力和测试样本。
3. V1/V2 已证明的失败教训与设计约束。

V2 的任何代码只有在满足 V3 契约并通过重新设计后的测试后才允许移植。

### 1.2 最小闭环优先

V3 第一阶段只建立一个能够可靠完成以下闭环的系统：

```text
原始文档
  → L1 源制品
  → Semantic Metadata
  → Source Resolver
  → Question IR
  → Deterministic Compiler
  → Evidence/Quality Gate
  → Candidate / Admission
  → Question + Instance
```

在该闭环稳定前，不开发 AI 生成题、复杂推荐、Agent、统计富化等外围能力。

### 1.3 LLM 是语义判断器，不是数据库编译器

LLM 可以判断：

- 题目/子题/共享材料的语义结构；
- 题型；
- 语义关系；
- 答案/详解属于哪个区域；
- 难度等非确定性元数据。

LLM 不负责：

- 改写原文；
- 计算最终字符/行位置；
- 决定数据库事务；
- 直接写 Question；
- 直接决定是否入库；
- 通过隐藏重试无限调用外部 API。

### 1.4 Source 是唯一事实源

原始文件及其解析制品不可变。

所有最终题干、选项、材料、答案、详解必须可以追溯到 Source Artifact 或明确标记为 AI Generated。

任何无法证明来源的内容不得自动进入 approved 真题。

### 1.5 外部副作用必须显式

真实 LLM、OCR、对象存储、任务消费等有外部副作用的动作不得因：

- 启动 API；
- reload；
- 数据库恢复；
- worker 重启；
- 超时扫描；
- 测试收集；

而自动发生。

## 2. 核心系统边界

```text
Frontend
   ↓
HTTP API
   ↓
Application Service
   ↓
Domain Service
   ↓
Repository
   ↓
PostgreSQL / Object Storage

Explicit Worker
   ↓
Task Executor
   ↓
Application Service
   ↓
LLM Gateway
   ↓
Provider
```

API 进程永远不启动 Worker。

Worker 是独立进程，并且必须显式启动。

业务代码不能绕过 Gateway 直接调用真实 LLM Provider。

## 3. V3 核心领域对象

### Source Artifact

不可变的原始文件、L1 Native/OCR 制品及其版本信息。

### Semantic Annotation

LLM 对 Source 的语义标注。它描述“Source 中有什么”，不复制 Source。

### Question IR

与具体数据库表解耦的中间表示，是从 Semantic Annotation + Source Resolver 编译得到的标准题目结构。

### Question

去重后的题目实体，代表“这道题本身”。

### Question Instance

一道 Question 在某份文档/某次来源中的具体出现。

### Candidate

尚未获得自动入库资格的不可变 admission snapshot。

### Task

异步工作的生命周期对象。Task 不直接等于 LLM Request。

### LLM Call Audit

每次真实 LLM 请求的不可变审计记录。

## 4. V3 明确非目标

第一阶段不做：

- 自动从错误状态恢复并重新消费任务；
- 多级自动重试链；
- API 与 Worker 共进程；
- LLM 直接生成真题抽取文本；
- 通过 JSONB 隐式承载整个业务模型；
- 自动扩展知识树；
- 复杂 Agent 编排；
- 多 Provider 自动无限 fallback；
- 为兼容 V2 而保留旧 pipeline 分支。

## 5. 成功标准

V3 首个稳定版本必须满足：

1. API 启动不会产生任何 LLM 调用。
2. 未显式启动 Worker，不消费任何 Task。
3. Worker 崩溃不会自动重跑任务。
4. 所有真实 LLM 调用均可追溯到 task/document/stage/attempt。
5. 每道 approved 真题均可从 Source 重建。
6. Composite 的共享材料只保存一次，子题通过关系引用。
7. Source Resolver 无法唯一定位时不得猜测。
8. Quality Gate 失败必须进入 candidate/review/failed，而不是静默入库。
9. 正常 pytest 永远不调用真实外部 API。
10. V3 的核心解析管线只有一条生产主路径。
