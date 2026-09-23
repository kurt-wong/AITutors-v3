# OD-01 Proposal v4 — 定向对抗性审查

```text
STATUS: TARGETED ADVERSARIAL REVIEW — COMPLETE
SCOPE: OD-01 Proposal v4 + CR-002 Candidate（文档治理 / 条款 diff / 路径 / 状态词）
SUBJECT: AITutors-v3 Docs/COORDINATION/FROZEN-SPEC-CHANGE-PROPOSAL-OD-01-OPTION-PROVENANCE.md（v4）
         AITutors-v3 Docs/COORDINATION/CONTRACT-CHANGE-RECORD-CR-002-OD-01.md
         AITutors-v3 Docs/COORDINATION/OWNER-DECISIONS-OD-01-OD-05-G-01-G-02.md（OD-01-A…J）
COMMIT: 86da69c0461449ceb0aab5ec2d7d77a3ea6c9c09
FROZEN SPEC TREE: b3eeb3e9a600347f18eae4e1becc1ec4fa4b6b4f（UNCHANGED）
VERDICT: VERIFIED WITH FINDINGS
CLOSURE BLOCKING: NO
RECOMMENDATION: READY FOR OWNER REVIEW（下列 F-OD01V4-xx 为非阻断项）
```

> 本报告**不**修改 Frozen Spec / Contract / 代码 / schema / corpus。
> **不**执行 re-freeze / Phase 1 / migration / push L0。

---

## 1. 审查问题与结论

| # | 对抗性问题 | 结论 |
|---|------------|------|
| Q1 | 是否恢复完整 Current → Proposed 条款差异？ | **是**（CI-1…CI-12 + §5 Appendix） |
| Q2 | 是否恢复缺口基线（现有/真缺口/延后/非目标）？ | **是**（§1） |
| Q3 | Proposed Frozen Text 是否可直接采纳（无 TODO/讨论/未决）？ | **基本可采纳**（见 F-OD01V4-01：编码单位仍属 Owner 钉死项，已隔离在正文外） |
| Q4 | CR-002 是否避免「已注册 L1」误解？ | **是**（Change Proposal Record / NOT REGISTERED AS L1 / Pending L1 Registration） |
| Q5 | Status 词是否含 `DONE`？ | **仅出现在「禁用/替换」说明**；状态列无 `DONE` |
| Q6 | Governance Gap 是否改为 deferred registration path？ | **是**（valid future registration path） |
| Q7 | degraded 是否被夹带进 change set？ | **否**（OD-01-F：不纳入；不完整→unresolved/incomplete/review） |
| Q8 | resolution 命名是否拆分？ | **是**（span_resolution / option_evidence_status / answer_status / semantic_status） |
| Q9 | Native / Adapter / Artifact 是否统一？ | **是**（§3；等价语义 + 禁第二 authority） |
| Q10 | 是否伪造 L0 修改或 re-freeze？ | **否**（tree `b3eeb3e9…` 未变） |
| Q11 | CHANGE-3/4/5 是否承认且挂四道门？ | **是**（Gate A–D 全部 PENDING） |
| Q12 | ID Mapping 是否唯一？ | **是**（§0） |

---

## 2. Findings（非阻断；供 Owner / 下一轮）

| ID | 级别 | 内容 | 建议 |
|----|------|------|------|
| **F-OD01V4-01** | LOW | char offset 编码单位（UTF-8 code unit vs Unicode scalar）仍在 Owner 钉死清单，未写入 Proposed Frozen Text 字面值 | Owner 在批准时钉死一种后，由 re-freeze change set 写入；**不**在 v4 伪钉死 |
| **F-OD01V4-02** | LOW | `50` 任务书作 `50_Interface_Contract`，仓库实名 `50_Migration_Assets.md` | v4 §5 已注明；Owner 批准时按实名采纳 |
| **F-OD01V4-03** | LOW | 四道门 Gate A–D 全部 PENDING，CHANGE-4/5 在门未过前不得 re-freeze | 保持 PENDING；禁止提前标 PASS |

**Closure Blocking = NO**（不影响进入 Owner Review）。

---

## 3. 正面核对

| 项 | 证据 |
|----|------|
| Frozen Spec UNCHANGED | `git rev-parse HEAD:Docs/V3_SPEC` = `b3eeb3e9…`；`git diff -- Docs/V3_SPEC` 空 |
| 仅 COORDINATION 三文件 | commit `86da69c` stat |
| 无 `standalone_question` | 全文检索 0 |
| 无状态列 `DONE` | 仅禁用说明命中 |
| 无「已注册 L1」肯定表述 | 仅否定/禁止句 |
| OD-01-A…J 已登记 | OWNER-DECISIONS 附录 |
| degraded 未入 change set | OD-01-F + CI 明示 |

---

## 4. 最终判定

```text
OD-01 Proposal v4     = VERIFIED WITH FINDINGS
CR-002                = VALID CHANGE CANDIDATE / NOT EFFECTIVE
Frozen Spec           = UNCHANGED
Production / Schema / Corpus = UNCHANGED
Phase 1               = NOT ENTERED
Re-freeze             = NOT EXECUTED
Next                  = Owner Review（OD-01-J：DSH 复核若 Owner 另令则先 DSH）
```

---

**Document control**

| Field | Value |
|-------|-------|
| Path | `Docs/60_REPORTS/OD-01-PROPOSAL-V4-TARGETED-ADVERSARIAL-REVIEW.md` |
| Status | COMPLETE — TARGETED ADVERSARIAL REVIEW |
| Verdict | VERIFIED WITH FINDINGS |
| Subject HEAD | AITutors-v3 `86da69c` |
