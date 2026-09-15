# EB-008 Evidence Authority Enforcement — Final (Revision-5)

- **Status**: L2 FROZEN DESIGN — implementation entry point
- **Supersedes**: 91号 (Revision-4)
- **Trigger**: Owner Review-5 confirmation of core design direction
- **Date**: 2026-09-15

---

## 0. 文档定位

本文档是 EB-008 的最终冻结设计，作为实现阶段入口。设计内容基于 Rev-4（91号），本版变更：

| # | 变更 | 位置 |
|---|---|---|
| 1 | Identity Model 确认（无变更，明确禁止 run_id 回归） | §1 |
| 2 | Human Review Proof 补充三项声明 | §2 |
| 3 | IR Boundary 确认 Option B（无变更） | §3 |
| 4 | DEC 编号治理：DEC-013 → DEC-016 | §4 |
| 5 | Implementation Checklist | §5 |

Rev-4 中未变更内容在本文档中完整保留要点；实现以本文档 + Rev-4 为准。

---

## 1. Identity Model（确认，无变更）

Owner 确认保持 Rev-4 定义：

```
I1: Run = Process（处理过程，非数据库实体）
I2: Candidate = Entity（处理结果，le_hash 唯一决定）
I3: le_hash 决定 Semantic Identity
    （输入：task_type + stage + contract_domain + input_domain）
I4: 同 hash 跨 Run 复用属于正确行为（idempotent，非漏洞）
I5: AuthorityIdentity = (source_version_id, candidate_id, claim_id)
I6: run_id / attempt_id 不参与 AuthorityIdentity
```

**约束：不得重新引入 run_id 作为 Authority 身份因素。** Replay 语义 R1-R5（Rev-3 §2）不变：replay 不改变 Authority 状态，已 VALIDATED 为幂等 no-op。

---

## 2. Human Review Proof（补充三项声明）

Proof 机制定义不变（Rev-3 §4）：`review_proof = SHA256(canonical_json({candidate_id, review_result, reviewer_id, reviewed_at, app_secret}))`。

本版补充三项边界声明：

### 声明 1：proof 粒度为 candidate 级

```
proof 绑定 candidate_id，不绑定 claim_id / unit 级。
一个 candidate 的人工审核产生一个 proof，覆盖该 candidate 全部 claims。
Admission Boundary 按 candidate 查询 human_review ValidationEvent 并验证 proof。
```

### 声明 2：proof 用于防止数据库直接篡改，不负责 API 身份认证

```
proof 的防御目标：
- 直接修改 DB 中 review_trail / validation_events 伪造审核结果
- 跨 candidate / 跨 result 重放 proof

proof 不负责：
- 验证调用者是谁（API 身份认证）
- 验证调用者是否有权提交审核（API 授权）
```

### 声明 3：API 访问控制属于当前系统外部边界

```
API 身份认证与授权（谁能访问审核页面、谁能提交审核）是系统外部边界职责
（反向代理 / 本地网络边界 / 部署环境访问控制）。

EB-008 范围内：proof 保证"审核结果未被篡改"，
不保证"审核者身份经过强认证"。
个人系统威胁模型（Decision-2）接受此边界。
```

---

## 3. IR Boundary（确认 Option B，无变更）

Owner 确认 Rev-4 定义：

```
D4-1: IR 允许 provisional 存在（无 Authority 前置条件）
D4-2: IR 不代表事实（IR 是 Intermediate Representation，非知识资产）
D4-3: IR 不能直接成为 Question Knowledge
D4-4: Admission 是唯一进入知识资产层的入口（approve() enforcement）
```

Boundary 双层与未验证 IR 权限边界（Rev-4 §3-§4）不变。Authority Projection 生命周期（Rev-4 §5）不变。

---

## 4. 文档治理：DEC 编号冲突处理

### 冲突说明

V3 ledger 中 DEC-013（EB-008 Owner business rules，本 session 2026-09-15 创建）与其他 ledger 中既有 DEC-013 存在语义冲突。为避免未来 agent 根据旧编号产生错误推理，执行重编号。

### 治理方案（采用：修改业务决策编号）

```
旧编号: DEC-013（EB-008 Owner business rules）
新编号: DEC-016

理由：
- DEC-014 / DEC-015 已被其他 ledger 占用（Owner 指示）
- 本 session 创建的 DEC-013 无外部引用（仅 state.yaml / CURRENT.md / 91号）
- 重编号一次性消除冲突，优于 amendment 链（避免双重编号长期共存）
```

### 历史文档引用规则

87-91号文档中出现的 "DEC-013" 均指本 EB-008 business rules，即现 DEC-016。历史文档不回改（snapshot 原则）；以 state.yaml / CURRENT.md / 本文档为编号 source of truth。

### DEC-016 内容（冻结）

```
EB-008 Owner business rules (frozen):
(1) HASH identity = same Question Entity, idempotent replay
(2) Human Review Trust = review proof token, no IAM (personal system)
(3) all evidence persisted, no in-memory
(4) IR Boundary = Option B: IR provisional, IR not trusted knowledge asset,
    Authority required for Question Knowledge Layer
source: Owner Decision-1~4, 2026-09-15; confirmed Review-5
```

---

## 5. Implementation Checklist

实现阶段必须完成以下项。每项含验收标准。

### 5.1 validation_events 表

| 项 | 内容 |
|---|---|
| Alembic migration | 新表 validation_events（schema 见 §6） |
| ORM Model | ValidationEventRecord（app/models/），INSERT-only Repository 接口 |
| Repository | insert_validation_event() 唯一写入口；无 update/delete 方法 |
| 状态机接入 | 写入前调用 AppendOnlyEventLog 状态机逻辑（现有 models.py:268-304 迁移到 DB 写入路径） |
| EvidencePromotionService 改造 | 移除 in-memory AppendOnlyEventLog（promotion.py:207-209），改为注入 DB Repository |

**验收**：Gate 运行后 validation_events 表有对应行；进程重启后 Authority 投影结果不变；重复 append 违反状态机时抛错。

### 5.2 Review Proof 生成与验证

| 项 | 内容 |
|---|---|
| 配置 | APP_SECRET 从 .env 读取；启动时校验非空（32 字节） |
| 生成模块 | app/domains/evidence/proof.py：generate_review_proof(candidate_id, review_result, reviewer_id, reviewed_at) → SHA256 hex |
| 生成时机 | 人工 approve/reject 路径写入 validation_events.review_proof |
| 人工 ValidationEvent | human approve → INSERT validation_events(validation_result=validated, validation_method=human_review, validator="human/<reviewer_id>", review_proof=proof) |
| 验证模块 | verify_review_proof(event) → bool：从事件字段重算 proof 并比较 |
| 验证时机 | Admission Boundary（approve() 入口，human_review 事件时） |

**验收**：合法 proof 通过验证；篡改 DB 中 review_result 后验证失败；无 proof 的 human_review 事件不产生 Authority。

### 5.3 Admission Authority Enforcement

| 项 | 内容 |
|---|---|
| 投影函数 | project_authority(candidate_id, claim_id) → "none"\|"validated"\|"rejected"\|"invalidated" |
| approve() 接入 | admission.py approve() 入口：对 candidate 各 claim 投影 Authority；任一 claim 非 validated → RepositoryError → fail-closed |
| human_review 分支 | validation_method=human_review 的事件 → verify_review_proof；失败 → fail-closed |
| 双入口保持 | auto_gate 路径：gate_decision=auto_approve + Authority validated；human 路径：review_trail + proof 验证 + Authority validated（20 §8.2 不破坏） |
| fail-closed 语义 | Authority 缺失/无效 → 拒绝 approve，candidate 保持 pending_review（不 reject） |

**验收**：无 ValidationEvent 的 candidate approve 失败；VALIDATED candidate approve 成功物化；篡改 proof 后 approve 失败。

### 5.4 Invalidate 级联机制

| 项 | 内容 |
|---|---|
| 触发场景 | source_version 被取代、annotation 变更、OCR 升级、人工判定 evidence 失效 |
| 级联范围 | 受影响 (candidate_id, claim_id) 集合：该 source_version_id / annotation_id 下所有已有 VALIDATED 事件的 claim |
| 写入 | 对每个受影响 claim append ValidationEvent(validation_result=invalidated, validator="system/v1", validation_method=derived) |
| 状态机 | VALIDATED → INVALIDATED 允许；INVALIDATED 为 terminal（无 resurrection） |
| 恢复路径 | 不在同 claim 恢复；新 pipeline 运行产生新 le_hash → 新 candidate → 新 Authority |
| 审计 | INVALIDATED 事件 checks.detail 记录触发原因（source superseded / annotation changed / manual） |

**验收**：source 变更后旧 candidate Authority 投影为 invalidated；approve 被拒；新运行产生独立新 Authority。

### 5.5 Append-Only 保护策略

| 层级 | 策略 | 阶段 |
|---|---|---|
| 应用层 | Repository 无 update/delete 方法；唯一写入口 insert_validation_event() | Phase-1 必做 |
| 应用层 | 状态机检查在 insert 前执行（terminal 状态拒新事件） | Phase-1 必做 |
| DB 层 | 触发器：BEFORE UPDATE OR DELETE ON validation_events → RAISE EXCEPTION | Phase-1 后加固（trade-off 已记录） |

**验收**：应用代码无 UPDATE/DELETE validation_events 路径；状态机违规 insert 抛错；（加固后）直接 SQL UPDATE 被触发器拒绝。

---

## 6. validation_events 表 schema（实现参考）

```sql
CREATE TABLE validation_events (
    event_id UUID PRIMARY KEY,
    claim_id VARCHAR NOT NULL,              -- unit_id
    candidate_id UUID NOT NULL REFERENCES admission_candidates(id),
    source_version_id UUID NOT NULL,
    validation_result VARCHAR NOT NULL,     -- 'validated' | 'rejected' | 'invalidated'
    checks JSONB NOT NULL,                  -- [{"check_id","result","detail"}]
    validation_method VARCHAR NOT NULL,     -- enum VALID_VALIDATION_METHODS
    validator VARCHAR NOT NULL,             -- 'gate/v1' | 'human/<id>' | 'system/v1'
    reference_ids JSONB,                    -- ["er-<span_id>", ...]
    review_proof VARCHAR,                   -- human_review only; 其他 NULL
    validated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ve_claim_candidate ON validation_events(claim_id, candidate_id);
CREATE INDEX idx_ve_candidate ON validation_events(candidate_id);
```

---

## 7. 风险列表（最终）

| # | 风险 | 缓解 | 状态 |
|---|---|---|---|
| 1 | APP_SECRET 泄露 → 伪造 proof | 运维责任（Decision-2 接受） | accepted |
| 2 | validation_events 无 DB 层 append-only（Phase-1） | 应用层双保护；DB 触发器为加固项 | trade-off, §5.5 |
| 3 | IR 被误当作知识资产 | Boundary 文档 + Admission enforcement | mitigated by design |
| 4 | provisional IR 调试泄露 | IR transient；仅物化产物对外 | mitigated by design |
| 5 | INVALIDATED 误触发 | 需新 Entity 重建；审计原因 | accepted (terminal semantics) |
| 6 | pending_review 无事件落库 | 符合 fail-closed | by design |
| 7 | 单层 enforcement | IR 非知识资产；新消费者出现时重评 | accepted (Decision-4) |
| 8 | proof 不做 API 认证 | 外部边界职责（§2 声明 3） | accepted (Review-5) |

---

## 8. 冻结清单（供后续引用）

```
DEC-016: EB-008 Owner business rules（§4）
Identity Model: I1-I6（§1）
Review Proof: 机制 + 三项声明（§2；机制定义见 Rev-3 §4）
IR Boundary: Option B D4-1~D4-4（§3；Boundary 详情见 Rev-4 §3-§4）
Authority Projection: Rev-4 §5（状态机、时机、消费点）
Issuer Contract: C1-C7 + H1-H3（Rev-3 §9）
Lifecycle: INVALIDATED terminal；恢复 = 新 Entity（Rev-3 §6 / Rev-4 §8）
Implementation Checklist: §5（五项，含验收标准）
```

**EB-008 设计阶段结束。实现阶段入口 = 本文档 + commit。**
