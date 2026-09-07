"""Worker 进程（30 §2 Process Boundary）：独立显式启动，不随 API/import 自动消费队列。

启动方式：
    python -m app.worker run               # safe 默认：mock/disabled，无真实外部调用
    python -m app.worker run --allow-live  # 显式放行 live（还需 live mode + task + budget）
    python -m app.worker recover --dry-run # 预览失效租约任务
    python -m app.worker recover --confirm # 执行：置 interrupted（Recovery ≠ Retry）
    python -m app.worker retry <task_id>   # 人工 retry failed/interrupted → queued
"""
