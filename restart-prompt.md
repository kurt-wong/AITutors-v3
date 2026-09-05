# AI Tutor V3 — RESTART PROMPT

Version: v1.0
Status: V3 Spec Baseline — Frozen（实现未开始）
Date: 2026-09-05

## 0.0 当前结论（2026-09-05）

- V3 架构与开发契约已冻结（Baseline—Frozen）；**实现未开始**。
- 重启后第一任务：按 `Status.md` 下一步执行——先资产清点（`Docs/V3_SPEC/50 §3`），
  再 `40 §2` 段 A 骨架。

## 0. 当前工作状态（2026-09-05）

- **已完成**：`Docs/V3_SPEC/` 六册 + README 冻结（00 v1.2 / 10 v1.2.1 / 20 v1.2 /
  30 v1.1 / 40 v1.1 / 50 v1.1 / README v1.1）；7 份起草归档
  `docs_archive/2026-09-05_v3_draft/`；全体系跨册审查无冲突。
- **入口**：先读 `Docs/V3_SPEC/README.md`（§1 地图 / §1.1 状态 / §1.2 00 服从性证据 /
  §2 术语裁决）。
- **当前不要执行**：不搬 V2 代码/库（V2 只作失败样本库）；不改冻结分册（除非 changelog
  或显式 errata）；实现中不越过 Gateway / approve() 唯一入口 / live 组合放行；不为
  单题号/学校/OCR 变体加特判。
- **实现期已知前置（勿丢）**：进段 G（40 §2）前补 `Docs/reference/DISPLAY_CONTRACT.md`
  的 **T/F↔A/B canonical 映射**（20 §8.4 strict-auto 前置；未完成则该题型只走
  pending_review）。2026-09-05 17:12 登记。
- **关键文件**：
  - `Docs/V3_SPEC/README.md` — 唯一导航 + 术语裁决 + Baseline 状态
  - `Docs/V3_SPEC/00_Master_Spec.md` — 宪法（P1-P7 / 非目标 / 红线）
  - `10_Data_Model.md`、`20_Document_Pipeline.md`、`30_Task_LLM_Safety.md`、
    `40_Development_Rules.md`（A-I 顺序与出口闸）、`50_Migration_Assets.md`（资产/Golden/归档）
- 详细状态见 `Status.md` 与 `log.md`。

## 1. 用途

Codex/Claude 重启后先读本文件恢复上下文。本文件只承载稳定信息：项目目标、基线状态、
强制规则、文档地图、恢复流程；最新状态细节以 `Status.md` / `log.md` 为准。
**更新约定（规则二）**：`0.0/0` 节结论每次更新带当前时间戳（`YYYY-MM-DD HH:MM:SS`），
在对应小节下记录最近更新时刻。

## 2. 项目目标

从 V2 继承业务需求并**全量重写**（V2 需求见 `Docs/00_Requirements/
REQUIREMENTS_AND_SOLUTION.md`）：批量上传教师版 PDF/DOCX → 自动提取题目/配图/答案/
详解/元数据；题库统计分析；AI 生成题（延后）；错题本；个性化练习。V3 目标 = 杜绝
V2 的「LLM→文本→特判→Gate→回填」模式，以 Source 为唯一事实源、stage-scoped 幂等、
Replay 可重建。

## 3. 强制规则（摘要，权威在六册）

- 单主链：不建第二条 pipeline；状态只经唯一入口（decision_status → approve()/reject()）。
- Live 是组合放行：LLM/cloud OCR 须 live mode + `--allow-live` + task + budget 同时成立。
- LE key = `{task_type, stage, contract_domain, input_domain}`（不含 task_id）。
- 预算五账户正交、禁父子树；Recovery ≠ Retry；Worker 崩溃不自动重跑。
- 实现顺序、测试层级、DoD、评审红线：`40`；资产/Golden：`50`。
