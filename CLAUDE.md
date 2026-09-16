# AITutors-v3 — 会话引导（CLAUDE.md）

> **用途**：新会话启动时快速返回工作状态。本文件只做引导与快照，**不承载独立裁决**。
> **权威状态**：`Docs/COORDINATION/state.yaml`（机器）+ `Docs/COORDINATION/CURRENT.md`（人读）+ `Docs/COORDINATION/log.md`（轮次流水）。

---

## 启动协议（每次新会话必做）

1. 读 `Docs/COORDINATION/state.yaml` —— workstream / agents / facts / decisions / open_questions
2. 读 `Docs/COORDINATION/CURRENT.md` —— 状态行 / Owner Decisions 表 / Shared Facts / EB-009 / Evidence Locations
3. 需要轮次历史时读 `Docs/COORDINATION/log.md`（append-only，DEC-032 起建档）
4. 只在 OPEN 项上工作；引用任何 DEC 时核对 state.yaml 原文

---

## 当前状态快照（2026-09-16，DEC-036 后）

| 项 | 值 |
|---|---|
| **Contract v0.2** | **`FROZEN`**（Owner Freeze 令，V3 `DEC-036`，2026-09-16） |
| Freeze Object（唯一冻结对象） | commit **`f4941ff`** · `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` · sha256 `9c6b9063e81fb2a66d85794b280c9d931f1b0074b39abf472033218149b17528` |
| Freeze Registration（非冻结对象） | `DEC-036` 账本 commit `3b3b397`（**≠ `f4941ff`**，分离保持） |
| 冻结范围 | 六项（未扩展）：Identity Authority / 双层职责 / 命名 / 16 份 Semantic Pending / bytes 能力（只冻能力不冻传输）/ 双状态体系 |
| 接口键（跨系统唯一） | `source_content_sha256` = SHA256(original source bytes)，64 位小写 hex |
| V3 内部键 | `source_version_id` = uuid.UUID FK（内部含义，禁作跨系统键） |
| path / `source_file` | locator only —「path → 找文件；SHA256(bytes) → 证明文件身份」 |
| Scope | 接口面 **87** · IR ADMITTED **71**（1,664 单元）· **16 份 = Identity Available / Semantic Pending** |
| 冻结时证据链 | Step 1 DONE + Step 2 DONE + Verification PASS（DSH `DEC-026`/`027`/`028`，commits `e70807b`/`aad2237`/`67f564c`）+ B-1 CLOSED / REMOTE VERIFIED（`DEC-035`） |
| preprocessing 仓基线 | `67f564c`（kurt-wong/Aitutors-preprocessing，canonical ledger） |

### 下一阶段（未获授权，勿开工）

**V3 Consumer Identity Verification 实现阶段**：raw bytes → SHA256 recompute → Manifest verification → IR verification → fail-closed → Gate → Admission。

- 契约边界已立：输入 Manifest + raw bytes + IR（§5.6.2）；**五项能力 NOT IMPLEMENTED**（§5.6.1 / G-15）：Manifest identity verification / raw bytes acquisition / independent SHA256 verification / IR identity verification / identity gate
- **须另获 Owner 实现令**——Contract Freeze ≠ Implementation；冻结本身不构成实现授权

### 开放项（非阻塞）

OQ-21（16 份呈现机制）· OQ-17（存量 1 例）· OQ-16′（pending→rejected 准则+载体）· OQ-10 PDF 面 · OQ-12″ bytes 传输方式 · 跨仓 DEC 编号统一（撞号 3 处：DSH DEC-021/022/023 ≠ V3 同号）· EB-008 P1 外部对抗验证 pending

### 已裁决、不再讨论

path 是否 identity · `source_version_id` 命名 · 16 份是否重跑 · hash 是否唯一

---

## 协作约定（跨会话必须遵守）

- **双仓**：V3 = `kurt-wong/AITutors-v3`（D:\Project\AITutors-v3）；preprocessing = `kurt-wong/Aitutors-preprocessing`（D:\Project\Papers，**canonical ledger**，V3 侧是 mirror）
- **声明协议**：OBSERVED / DECISION / REQUIREMENT / UNKNOWN；**DECISION ≠ IMPLEMENTATION**（禁止把裁决写成已实现）
- **账本纪律**：状态变更只登记 `state.yaml` / `CURRENT.md` / `log.md`；Freeze Registration 与 Freeze Artifact 分离；**禁止修改 `f4941ff` 处契约正文**（改之变更 sha256，破坏冻结对象——现态由账本承载）
- **commit 约定**：无 auto-commit；每轮 Owner 指令后手动 commit 三账本（或含本轮涉及的 CONTRACTS 文档）
- **刻意不跟踪的历史文件**（保持 untracked，勿提交）：`PREPROCESSING-V3-CONTRACT-v0.2-DRAFT-SKELETON.md`、`PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW.md`、`PREPROCESSING-V3-CONTRACT.md`
- **GateGuard**（ecc plugin fact-forcing hook）：每文件首次 Edit/Write/Bash 会拦截，按提示陈述四项事实后重试同一操作即可；只读工具不受影响
- **DEC 编号**：V3 与 DSH 各自编号，引用任一侧必须双向标注（对照表见 CURRENT.md）

## 关键文档地图

| 文档 | 位置 |
|---|---|
| **Contract v0.2（FROZEN，唯一冻结对象）** | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-DRAFT.md` @ `f4941ff` |
| V3 Consumer Gap Map（消费面事实 + G-1~G-15） | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONSUMER-GAP-MAP.md` |
| Consumer Alignment v3（DEC-028 对齐，最新） | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONSUMER-DECISION-ALIGNMENT-v3.md` |
| Freeze Candidate Review（DEC-029 历史记录） | `Docs/COORDINATION/CONTRACTS/PREPROCESSING-V3-CONTRACT-v0.2-FREEZE-CANDIDATE-REVIEW.md` |
| EB-008 实现入口 | `Docs/DECISIONS/92_EB008_EVIDENCE_AUTHORITY_ENFORCEMENT_FINAL.md` |
| 项目技术约束（硬件/栈/Local-first） | 见全局规则 project-rules.md（i7-14700 / 64GB / RTX 4060 8GB；FastAPI + React + PostgreSQL + ChromaDB；KISS/DRY/YAGNI） |
