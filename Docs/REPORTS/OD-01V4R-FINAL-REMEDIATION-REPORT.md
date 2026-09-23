# OD-01V4R Final Verification Remediation Report

```text
Document ID:           OD-01V4R-FINAL-REMEDIATION-REPORT
Title:                 OD-01V4R Final Verification Remediation Report — F-OD01V4R-30…48
Document Type:         Experiment Report
Status:                PENDING
Authority Level:       L3
Purpose:               逐项登记 DSH Final Verification F-OD01V4R-30…48 的 Old Problem / Applied Fix / Evidence / Remaining Risk
Normative:             NO
Derives From:          Docs/60_REPORTS 基线不可引用（外仓）；本仓派生自 DSH-OD-01-V4R-FINAL-VERIFICATION 发现清单（F-30…48）· Proposal v4R · CR-002 · 90/91 · AGENTS.md
May Change:            本报告文本
Must Not Change:       L0 · Frozen Contract · Schema · Code · Corpus · Migration · 历史决策语义
Related Records:       Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md · Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md · Docs/COORDINATION/OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md · Docs/REPORTS/OD-01-PROPOSAL-V4-TARGETED-ADVERSARIAL-REVIEW.md
Supersedes:            —
Superseded By:         —
Gate State Authority:  NO
```

> 本报告是 **治理修复登记**，不是 DSH Verification，不是 Frozen Spec 变更。  
> `Docs/REPORTS/` = L3/L4/L2-proposed。Authority Level: L3。  
> 不修改 `Docs/V3_SPEC/**`。不执行 re-freeze / Phase 1 / Migration / push。

**最终状态（强制保持）**

```text
Frozen Spec: UNCHANGED（tree b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f）
Schema: UNCHANGED
Production: UNCHANGED
Migration: NOT AUTHORIZED
Phase 1: NOT ENTERED
Re-freeze: NOT EXECUTED
CR-002 Status: NOT RELEASED
CR-002 Registration Level: NOT REGISTERED
```

---

## Finding → Fix 逐项（F-OD01V4R-30 … 48）

| Finding | Old Problem | Applied Fix | Evidence | Remaining Risk |
|---------|-------------|-------------|----------|----------------|
| **F-OD01V4R-30** | 映射表 -11…-14 四行 Problem 与 DSH 基准不符；HIGH 跨仓复制（-14）在 60 行表中零登记 | Proposal §0 按 DSH 基线重写 -11=Path 错仓、-12=Current Rule 保真、-13=CI-12/4 同文、-14=**HIGH 治理产物逐字节复制进 AITutorX / 跨仓副本 / 独立审查边界破坏风险**；-14 单独成行含三要素 | §0 表 F-OD01V4R-11…14 四行；-14 Problem 含「逐字节复制」「跨仓副本」「独立审查边界破坏风险」 | Problem 以已提交 DSH 标题为基准；若基线报告另版定义，须再对齐（DSH L-2） |
| **F-OD01V4R-31** | -08/-09/-10 三行错配原样保留却宣告映射表 VERIFIED | §0 重写：-08=第 7 套命名空间/R-xx 无定义、-09=Gap 两版并存+90:47 未归层未登记、-10=违反 90 §5 Rule 2 | §0 表三行；处置列不再对映射表使用 Status:VERIFIED | 无 |
| **F-OD01V4R-32** | OD-01F-09/10 空号；F-OD01V3-11/12 零命中 | OD-01F-09=F-OD01V3-11（引文保真）；OD-01F-10=F-OD01V3-12（BOM）；表含 V3-01…12 全 12 项 | §0：Final ID 列 01…81 连续；V3-11/12 各一行 | 空号以「填入漏登发现」方式消除，未重编号 21…30 |
| **F-OD01V4R-33** | change set 缺 README.md §2 术语登记 target | 新增 CI-README；§7 Diff 表首行=README §2；§10 登记 Future Required Change（span_resolution / option_evidence_status / form）；**不修改 README.md 本体** | Proposal CI-README；§7；§10 | README 本体写入仍为 Future Required Change（须 L1/Owner 序） |
| **F-OD01V4R-34** | CI-4 称 form/granularity 正交却共用值名 | 维度定义：form=定位空间结构；granularity=解析粒度；M1 同名=对偶标签；绑定规则 form⇒granularity；**禁止声明正交**；table_cell/other 等 granularity 缺省 | CI-4 + §6.3 合并文本 | 若未来 form/granularity 值域分叉，须再裁决命名 |
| **F-OD01V4R-35** | 无条件 line_ref 与 table_cell 可选并存 | 删除无条件句；locator 按 form 分型（line/line_character 必需；table_cell 四元组必需、line_ref 可选） | CI-4 + §6.3 | 无 |
| **F-OD01V4R-36** | table_cell 强制无判定标准；含元陈述；table_id 无生产者未进台账 | CI-2 方案 B：identity=(source_version_id, table_id, row_index, column_index)；字段含义+生产来源表；**table_id 生产来源必须存在**；当前未定义→Future Required Change；可判定标准；无元陈述；生产来源确立前不得 resolved | CI-2 · Proposal §5 | table_id 生产来源尚未确立（planning only）；未写入 84_CONFLICT_LEDGER（该文件属 L0 面，本轮禁改）— 见 §Remaining |
| **F-OD01V4R-37** | CI-4 与 CI-12 同改 20 §5.5 无合并文本 | 新增 §6.3：合并后 20 §5.5 **完整目标文本**；迁移者整节替换 | Proposal §6.3 | 合并文本以现行 20 §5.5 结构为底；re-freeze 时再 diff |
| **F-OD01V4R-38** | 20:317 示例仍为 resolution_status | §6.3 示例 JSON 改为 `span_resolution`；正文禁止双名 | §6.3 JSON | 无 |
| **F-OD01V4R-39** | CR-002 Status=NOT REGISTERED（枚举外） | Status → **NOT RELEASED**（90 §4:376）；NOT REGISTERED 仅 Registration Level / 正文短语；移除非规范 Effective 字段 | CR-002 Header | 无 |
| **F-OD01V4R-40** | Authority Level 自创三值；Self Review 层级不符 | 全部改冻结枚举：Proposal/CR=L2-proposed；Owner Decision=L2；Self Review=L3；三分角色移出枚举；Future Required Change 登记 | 全文档 Header；§2.1 | 冻结枚举无法表达三分角色（已登记 FRC） |
| **F-OD01V4R-41** | 「状态词仅用 91 §3.1」假陈述 | §2.3 改为分层真陈述：Header Status=冻结枚举；Finding Disposition 列≠Status；禁用 91 §3.2 词 | Proposal §2.3 | 历史表 Status 列保留原文（不重写历史） |
| **F-OD01V4R-42** | D1 新附录缺 5 字段；Status/Authority 非枚举 | D1 新附录补齐 Document ID/Normative/Supersedes/Superseded By/Gate State Authority；Status=PENDING；Authority Level=L2 | D1 附录头块 | 无 |
| **F-OD01V4R-43** | Self Review 缺 4 字段；Status=PENDING 错位；Derives From 非闭包 | Status=**HISTORICAL**；补 Document ID/Normative/Supersedes/Superseded By；Derives From=文档路径闭包；Authority Level=L3 | Self Review 头块 | 无 |
| **F-OD01V4R-44** | Self Review 历史正文被删（108→45） | 自 git `b6cb762` **全文恢复**历史正文；仅追加说明；不覆盖原文 | Self Review 含 VERIFIED WITH FINDINGS / CLOSURE BLOCKING / READY FOR OWNER REVIEW 原文；行数恢复 | 无 |
| **F-OD01V4R-45** | D1 保留「Gap 路径」标题；未归层 0 命中 | 移除 Gap 路径标题；Proposal/CR/D1 均登记 **未归层**（90:47）与 COORDINATION 不在 90 §1.2 | 各文件头/§9 | 无 |
| **F-OD01V4R-46** | 非规范头字段增列；Supersedes 格式错 | Supersedes=**—**（文档清单或—）；Effective/Change Record ID/Audit ID/Current Version 移出 Header 规范块→Document control | 全文档 Header | Registration Level 仍为非规范字段（任务要求可表达注册未来状态；已与 Status/Authority 分离） |
| **F-OD01V4R-47** | v3 系列 Problem 4 行不符 + 2 行互换 | V3-01…12 Problem 按 DSH 基线重写（含 V3-05=Owner Decision 自写/未归层） | §0 V3 全 12 行 | 无 |
| **F-OD01V4R-48** | D1 OD-01-J 仍写 v4 → DSH 复核 | 统一为 **Proposal v4R → DSH 外部验证 → Owner 批准 → re-freeze** | D1 OD-01-J | 无 |

---

## 完成条件核对

| # | 条件 | 结果 |
|---|------|------|
| 1 | Mapping 与 DSH 原始 Finding 一一对应 | PENDING 自检 / 待 DSH |
| 2 | 无 Finding 遗漏（含 V3-11/12；含 09/10） | 自检：01…81 连续；系列全含 |
| 3 | 无自定义 Status | Header 仅冻结枚举；处置列非 Status |
| 4 | Authority Level 不扩展 | 仅 L2 / L2-proposed / L3 |
| 5 | Self Review 不冒充 DSH | HISTORICAL + 禁止引用声明 |
| 6 | table_cell identity 方案 B | 四元组 + 生产来源 + 可判定标准 |
| 7 | Proposed Text 可被未来迁移 | CI-4/2/12 + §6.3 合并全文 + README 序 |
| 8 | 不修改 Frozen Spec | `git diff -- Docs/V3_SPEC` 空；tree 不变 |

---

## Remaining Risk / Owner Decision Required

| 项 | 说明 |
|----|------|
| table_id 生产来源 | 未确立。Future Required Change。确立前 table_cell 不得 resolved。未写入 `84_CONFLICT_LEDGER`（L0 面禁改）→ Owner 决定是否另案登记 |
| README.md §2 术语 | 本体未改（禁改 L0）。Future Required Change：先登记后使用 |
| Authority 三分角色值域 | 冻结枚举无法表达。Future Required Change：经 L1 确立 |
| Gate A–D | 全部 PENDING |
| 正式 L1 注册四条件 | 未满足 |
| DSH Final Re-verification | 本报告完成后停止；等待 DSH |

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/REPORTS/OD-01V4R-FINAL-REMEDIATION-REPORT.md` |
| Authority Level | L3 |
| Status | PENDING |
