# AI Tutor V3 — Task / Worker / LLM 安全边界规范

Version: 3.0
Date: 2026-09-05
Status: V3 强制基础设施规范

## 1. 基本原则

> 启动 API ≠ 启动 Worker ≠ 调用 LLM。

只有显式 Worker + queued Task + live mode + budget allowed 才能产生真实 LLM 调用。

## 2. Process Boundary

### API

只负责：

- HTTP
- authentication
- upload
- query
- create task
- read task

绝不：

- consume queue
- run document worker
- start answer retry worker
- automatically call LLM because of startup

### Worker

独立入口：

```bash
python -m app.worker run
```

默认 safe mode。

真实 live 运行需要显式：

```bash
python -m app.worker run --allow-live
```

## 3. Task State Machine

```text
created
  ↓
queued
  ↓
running
  ├── succeeded
  ├── failed
  └── interrupted
          ↓
      manual retry
          ↓
        queued
```

禁止：

```text
running → timeout → queued → automatic retry
```

## 4. Claim / Lease

Task 至少包含：

- worker_id
- lease_token
- started_at
- heartbeat_at
- lease_expires_at
- attempt_count

Claim 必须原子完成：

```text
UPDATE ...
WHERE status = 'queued'
RETURNING ...
```

或者使用 `FOR UPDATE SKIP LOCKED` 等价方案。

禁止：

```text
SELECT queued
→ Python 判断
→ UPDATE running
```

Heartbeat / completion 必须验证：

- task_id
- worker_id
- lease_token
- status=running

旧 Worker 即使诈尸，也不能修改已经被恢复/重试的新状态。

## 5. Recovery

Recovery 只负责：

```text
expired lease → interrupted
```

命令：

```bash
python -m app.worker recover --dry-run
python -m app.worker recover --confirm
```

Recovery 不执行 LLM，不重新排队。

## 6. Retry

四层职责必须独立：

| 层级 | 规则 |
|---|---|
| Task Retry | 人工触发 |
| Pipeline Retry | bounded |
| LLM Request Retry | bounded |
| HTTP Retry | bounded |
| Provider Fallback | explicit |

此外必须存在：

```text
MAX_LLM_CALLS_PER_TASK
```

它是最终熔断器，而不是正常业务逻辑。

## 7. LLM Gateway

唯一调用链：

```text
Domain/Application
   ↓
LLMGateway
   ↓
Provider
   ↓
HTTP
```

业务代码禁止直接构造真实 Provider。

Gateway 模式：

```text
disabled
mock
live
```

### disabled

不得创建 HTTP 请求。

### mock

允许测试流程运行，不产生真实外部副作用。

### live

必须同时满足：

- live mode
- explicit allow-live（CLI/脚本）
- task context
- budget available

## 8. LLM Call Audit

每次请求至少记录：

- request_id
- idempotency_key
- task_id
- document_id
- pipeline_stage
- attempt
- provider
- model
- process_id
- process_name
- hostname
- start/end
- status
- prompt_chars
- input_tokens
- output_tokens
- reasoning_tokens
- total_tokens
- estimated_cost
- error_type

状态至少：

```text
started
completed
failed
unknown
```

`started` 不等于确认 HTTP 已发出。

如果进程在未知时刻死亡，使用 `unknown`，不得假装失败或成功。

## 9. Budget

至少四级：

```text
request
 ↓
task
 ↓
document
 ↓
daily
```

请求前进行 reservation；请求完成后以实际 usage 结算。

预算检查必须具备并发安全性，不能使用简单的：

```text
read → compare → write
```

而导致两个请求同时通过预算检查。

## 10. Oversized Output

异常大的 reasoning/output 不只是成本问题，也是 pipeline 异常信号。

超过阈值必须：

- audit 标记 oversized_output；
- 允许 Gate/Task 决定失败或 review；
- 不得自动无限 retry。

## 11. Idempotency

建议：

```text
task_id + stage + operation + attempt
```

用于识别逻辑请求。

它不替代 task lease，也不等于“禁止所有重复请求”。

## 12. CLI

建议：

```bash
python -m app.worker tasks
python -m app.worker run
python -m app.worker run --allow-live
python -m app.worker audit --task-id <id>
python -m app.worker recover --dry-run
python -m app.worker recover --confirm
python -m app.worker retry <task_id>
```

任何改变 Task 状态的命令都应显式。

## 13. 测试红线

默认 pytest：

- 不访问真实 LLM
- 不访问真实 OCR
- 不发送真实网络请求
- 不消费生产任务

Live 测试必须同时满足：

```text
explicit test
+ explicit --allow-live
+ safe fixture
+ bounded budget
```

必须有灾难测试：

```text
claim
→ running
→ LLM call
→ kill worker
→ restart
→ recover
→ interrupted
→ manual retry
→ queued
```

并验证不存在自动重跑。
