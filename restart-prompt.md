# AI Tutor V3 — RESTART PROMPT

Version: v1.3
Status: 段 G 实现完成并经二轮对抗审查收尾（VERIFIED；A–G 已关闭；段 H 未授权）
Date: 2026-09-06

## 0.0 当前结论（2026-09-06 15:14:30）

- V3 架构与开发契约已冻结（Baseline—Frozen）；**V3 Core Pipeline Baseline A–G 定格**
  （用户裁决 15:14:30）：A–G 七段 Implementation Complete and Verified，commit `8a57a92`
  为 A–G 稳定工程基线——从 Source 到 A 域物化的确定性数据主线已闭环。
- 段 G 当前状态：**IMPLEMENTATION COMPLETE / VERIFIED**——G0 Contract Audit PASS 后用户
  授权实现，grammar/policy/payload/admission/service + 状态机探针 + 对抗审查 Correction
  Cycle（4 项修复）+ **二轮跨提交对抗审查 F1/F2 修复（8a57a92）**均完成；完整 pytest
  **201 passed ×2**；监控项（approve 只消费冻结 snapshot、不重跑 E/F/G）全绿。
  详见 Status.md / log.md。
- **下一步（用户指定顺序）**：先 **H0 Runtime Readiness Audit**（audit only，零生产代码）
  → H Contract Audit → H Implementation。H0/H 均未授权，不擅动工。
- 重启后第一任务：读本文件 → Status.md 尾 → log.md 尾恢复上下文 → 等待用户对 H0/H 或后续
  的授权/新指令。**H0/H + worker/LLM live/knowledge resolver 未授权，不要擅自动工。**

## 0. 当前工作状态（2026-09-06 15:14:30）

- **已完成（A–G 七段关闭）**：`Docs/V3_SPEC/` 六册 + README 冻结；段 A（config/DB 19 表/
  Repository/hashing）、段 C（Gateway/audit/budget external 闸）、段 B（Source Seal + OCR）、
  段 D（Annotation）、段 E（Source Resolver）、段 F（IR + Compiler）、段 G（Gate +
  Admission + Grammar）全部关闭。完整 pytest 201 passed ×2。
- **段 G 已关闭（实现要点）**：`app/domains/gate/` grammar/policy/payload/admission/service
  ——Gate 四层 gate_decision + 冻结可重放 payload + AdmissionService 物化事务唯一入口 +
  GateService LE 幂等编排；auto_approve 自动 approve、machine rejected 自动 reject
  （10 §5.2）。对抗审查 Correction Cycle 4 项已修复（见 Status.md/log.md）。
  - 三个 P0-G 边界（实现已落实）：
    - P0-G-001：decision_status 唯一入口 = application-level enforcement（Repository
      公共接口直改抛 AppendOnlyViolation），**不加** ORM event / DB trigger/RLS。
    - P0-G-002：approve() 拒绝 gate_decision=terminal rejected 的 candidate（即使
      decision_status 仍 pending_review）。
    - P0-G-003：reject() 区分 machine_gate / human 两种来源；machine 只 transition，
      人工理由只进 review_trail，不覆盖 gate_decision。
- **G0 用户裁决（勿忘）**：
  1. true_false 开放 strict-auto；DISPLAY_CONTRACT §0.2 已冻结 T/F 映射（禁 A/B）即满足，
     **不需要**再补 A/B 映射（判断题答案区写 A/B → 不通过 grammar → pending_review）。
  2. strict-auto 只开 single_choice / multiple_choice / true_false + composite 子题递归；
     fill_in/short_answer/essay/共享选项池 → 转人工。
- **BUG 登记状态**：BUG-V3-001..020 Open（A–F 遗留）；BUG-V3-021..027 **已写入 bugs.md**
  （G 相关：021 subject/grade 来源、022 LE hash 序列化、023 composite grammar、024 Gate 细则、
  025 review_trail JSON、026 gate_decision/review_trail 边界、027 Question dedup_key 无
  DB UNIQUE；021/022/025 实现按 M1 处理并标注不冒充 Frozen）。G 对抗审查 4 项为已修复
  实现 bug，不入 BUG 编号。
- **当前不要执行**：段 H + worker/tasks、LLM live、knowledge resolver 未授权前不实现；
  **H0 Runtime Readiness Audit 亦未授权，不擅动工**；不改冻结分册（除非 changelog/errata）；
  不重开已关闭的 A–G 段（不回头修 BUG-V3-001..027）。
- **关键文件**：
  - `Docs/V3_SPEC/README.md` — 唯一导航 + 术语裁决 + Baseline 状态
  - `Docs/V3_SPEC/20_Document_Pipeline.md` — 段 G 核心（§8 Gate 四层/decision_status/
    §8.4 Grammar/§9 验收）
  - `Docs/V3_SPEC/10_Data_Model.md` — 段 G 数据（§5.2-5.4 candidate/event/物化、§6、§9）
  - `Docs/V3_SPEC/40_Development_Rules.md` — A-I 顺序与出口闸
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
