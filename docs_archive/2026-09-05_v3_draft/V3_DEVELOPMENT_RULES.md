# AI Tutor V3 — 开发规则与 Agent 执行规范

Version: 3.0
Date: 2026-09-05
Status: V3 Agent 强制规则

## 1. 开发总原则

V3 是重建项目，不是 V2 的修补分支。

任何来自 V2 的代码必须先回答：

1. 它是否表达 V3 的业务需求？
2. 它是否符合 V3 架构边界？
3. 是否有对应测试？
4. 是否会把 V2 的兼容逻辑带入 V3？

任何一项为否，不移植。

## 2. Agent 开发顺序

每个功能必须按：

```text
需求
 ↓
Domain Contract
 ↓
Data Contract
 ↓
Application Service
 ↓
Implementation
 ↓
Unit Test
 ↓
Integration Test
 ↓
E2E
```

禁止先写代码再反推架构。

## 3. 复杂度预算

如果新增一个核心模块导致：

- 新增第二条生产 pipeline；
- 新增第三层 retry；
- 新增特殊题号判断；
- 新增一个兼容 V2 的中间格式；
- 新增无法独立测试的全局状态；

必须暂停并重新审查设计。

## 4. LLM 使用规则

### LLM 可以做

- semantic classification
- relation extraction
- metadata judgment
- ambiguity detection
- generation

### LLM 不可以做

- source rewriting
- database writes
- task state changes
- final admission
- hidden retries
- arbitrary guessing when evidence is absent

## 5. 不确定性处理

LLM 输出必须允许：

```text
known
unknown
ambiguous
```

不能为了填满 schema 而强行输出一个猜测。

## 6. Prompt 版本

每个正式 Prompt 必须有：

- prompt_version
- schema_version
- model
- test fixture

Prompt 修改后必须运行固定 golden。

## 7. Golden / Contract Test

Golden 用于验证结构和语义契约，不应只比较字符串。

至少验证：

- unit count / structure
- question number
- composite relationship
- material dependency
- anchor resolvability
- options completeness
- answer provenance
- image provenance

## 8. 测试层级

```text
Unit
  ↓
Contract
  ↓
Integration
  ↓
Live E2E
```

Unit/Contract/Integration 默认 mock 外部 API。

Live E2E 单独运行。

## 9. 数据库事务

一个业务动作必须有明确 transaction boundary。

尤其：

- Candidate approval
- Question merge
- QuestionInstance creation
- Knowledge mapping

禁止依赖“最后 flush 一下就算成功”。

## 10. 错误处理

异常必须分类：

```text
validation_error
source_error
provider_error
network_error
semantic_error
conflict
admission_error
system_error
```

禁止：

```python
except Exception:
    pass
```

除非异常被明确转换为结构化失败状态并保留 cause。

## 11. Observability

所有异步任务必须有：

- task_id
- stage
- attempt
- worker_id

所有 LLM 调用必须有：

- request_id
- task_id
- document_id
- stage
- provider
- model
- token usage

## 12. Definition of Done

核心功能只有同时满足以下条件才算完成：

- 代码完成
- schema/migration 完成
- 单元测试完成
- integration test 完成
- 错误路径测试完成
- 文档更新
- 没有新增隐式外部副作用
- 没有新增第二条生产主链

## 13. 变更日志

每次架构级变更记录：

- 背景
- 决策
- 替代方案
- 影响
- 测试结果

不要把 LOG.md 变成巨型状态数据库；当前状态放 PROJECT_STATUS，架构规则放本目录文档。
