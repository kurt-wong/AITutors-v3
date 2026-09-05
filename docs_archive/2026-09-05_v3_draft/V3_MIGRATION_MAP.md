# AI Tutor V3 — V1/V2 到 V3 的迁移取舍表

Version: 3.0
Date: 2026-09-05

| V1/V2 内容 | V3 处理 | 原因 |
|---|---|---|
| LLM 直接输出题干 | 删除 | 内容应来自 Source |
| line_id 作为最终事实 | 删除 | 行号只是定位线索 |
| Anchor Corrector 大量规则 | 重写为 Source Resolver | 降低规则堆积 |
| Native + PP 双源 | 保留思想 | 多源 provenance 已被验证必要 |
| PP-StructureV3 | 保留 | 复杂版面/OCR 仍是核心能力 |
| LLM VL 作为 L1 fallback | 默认删除 | V2 已确认不应作为入库驱动 |
| Semantic Metadata Annotator | 保留并升级 | V3 核心中间层 |
| simple_pipeline.py | 不直接迁移 | V2 管线已经承载过多补丁 |
| pipeline.py fallback | 删除 | V3 单一生产主链 |
| content_slicer.py | 重写为 Compiler | 从“按行切”升级为 IR 编译 |
| answer_matcher | 重写 | 必须区分 source-located / verified |
| admission_gate | 保留思想，重写 | Gate 必须基于 semantic IR/evidence |
| question_candidates | 保留思想，重做 snapshot | V2 Candidate 信息不完整 |
| API 内启动 worker | 删除 | 根本性安全问题 |
| recover stale → queued | 删除 | Zombie 调用放大器 |
| BackgroundTask | 保留概念，重做状态机 | 显式 Worker + lease |
| answer_retry_worker | 不作为独立隐藏消费者 | Retry 纳入显式 Task/Stage |
| LLMGateway | 保留并强化 | 唯一外部 LLM 出口 |
| Provider 多次自动 retry/fallback | 重写 | 防止乘法放大 |
| llm audit | 新增为基础设施 | 解决无法追踪调用的问题 |
| JSONB sub_questions | 谨慎使用 | 稳定关系应实体化 |
| content_hash | 保留 | 精确去重有价值 |
| 自动语义 merge | 延后 | 避免早期数据破坏 |
| 知识树 seed | 保留 | 业务需求仍需要标准知识树 |
| embedding | 保留 | 查重/检索需求明确 |
| AI 生成题 | 延后到核心解析稳定后 | 防止生成系统掩盖基础数据问题 |
