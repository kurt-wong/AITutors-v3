"""段 H 运行域 Task 状态机（30 §5/§17）。TaskService = tasks/task_claims 迁移唯一入口。

依赖方向：TaskService → TaskRepository/TaskClaimRepository → Base。TaskService 不 commit
（调用方持事务），所有方法在同一 session 事务内执行，保证 claim 的 task 状态更新与
task_claims 证据同事务。
"""
