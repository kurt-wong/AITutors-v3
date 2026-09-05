# AI Tutor V3

本地部署的 AI 题库 / 教学平台。自 V2 **全量重写**（V2 仅作失败样本库，不搬其代码/库/规则）。

**状态**：V3 Architecture & Development Baseline — Frozen（实现未开始，2026-09-05）。

## 文档地图

- 唯一规范导航：`Docs/V3_SPEC/README.md`（六册 00/10/20/30/40/50，冻结约束）
- 状态 / 变更 / 缺陷 / 重启恢复：`Status.md`、`log.md`、`bugs.md`、`restart-prompt.md`
- 资产清点：`Docs/reference/ASSET_INVENTORY.md`；迁移标注源料：`assets/annotations_src/`（重标源料，非 corpus，见其 README）
- 实现入口：`Docs/V3_SPEC/40 §2`（段 A→I，出口闸推进；cloud OCR 序修正 A→C→B）

## 版本管理纪律

- 密钥 / token 一律走 `.env`，**绝不 commit**（`.gitignore` 已拦）。
- 提交信息格式 `<type>: <desc>`（feat / fix / refactor / docs / chore / test / perf / ci）。
- 架构 / 功能类代码变更：计划前必遍阅 `Docs/V3_SPEC/`，确保在冻结约束下。
- 状态文档更新：带当前时间戳、在文末按时间顺序流式追加（不覆盖既有）。
