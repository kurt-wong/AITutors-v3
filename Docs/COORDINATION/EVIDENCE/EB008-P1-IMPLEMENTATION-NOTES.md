# EB008 P1 Implementation Notes — DSH Adversarial Review 基线

> 状态：EB-008 Phase-1 **CONVERGED**（攻击复核节点 `25933c3`；实现 commit `88aeae8`）。设计冻结基线 = 92号 FINAL。
> 用途：为 DSH 代码攻击测试提供实现事实。本文档只描述**当前代码是什么**，不提出新设计。
> 终态与遗留见 §10（2026-09-29 Owner 收敛）。全量证据见该节。

---

## 0. Identity Model（冻结，攻击测试前提）

- `AuthorityIdentity = (source_version_id, candidate_id, claim_id)`（92号 I5）
- **run_id / attempt_id 永久不得进入 Authority 身份**（I6）。`validation_events` 表无 run_id/attempt_id 列；`ValidationEventRecord` 模型无此字段。
- `claim_id` = candidate payload `ir_snapshot.units[0].unit_id`（Gate 落库与 Admission enforcement 同源：`_candidate_claim_id`）。
- 同 hash 跨 Run 复用 Candidate 属于设计目标（le_hash 语义身份，定义见 compile identity，本阶段不改动）。

---

## 1. validation_events 数据模型

文件：`backend/app/models/evidence.py` · Migration：`backend/alembic/versions/20260915_0011_validation_events.py`（revision `0011`）

| 列 | 类型 | 约束/语义 |
|---|---|---|
| `id` | UUID PK | mixin 默认 |
| `claim_id` | str NOT NULL | unit_id（claim 粒度） |
| `candidate_id` | UUID FK→`admission_candidates.id` NOT NULL | Authority 身份因素 |
| `source_version_id` | UUID FK→`document_source_versions.id` NOT NULL | Authority 身份因素 |
| `validation_result` | str NOT NULL | 值域 `validated \| rejected \| invalidated`（domain `VALID_VALIDATION_RESULTS` 冻结） |
| `checks` | JSONB NOT NULL | CheckResult 列表 `{check_id, result, detail}` |
| `validation_method` | str NOT NULL | 值域 `frozen_header_rule \| byte_proven \| structural_consistency \| human_review`（冻结） |
| `validator` | str NOT NULL | 机器事件 `"system/v1"`；human 事件 `"human/<reviewer_id>"` |
| `reference_ids` | JSONB nullable | EvidenceReference ID 列表（Proposal 层链接，R2） |
| `review_proof` | str nullable | **仅** human_review 事件非空（§2） |
| `validated_at` | timestamptz NOT NULL | 事件时间；投影排序键 |
| `created_at` | timestamptz NOT NULL | 入库时间 |

索引：`idx_ve_claim_candidate (claim_id, candidate_id)`、`idx_ve_candidate (candidate_id)`。

**无** run_id、attempt_id、mutable 状态列。Authority 不是本表的列——是投影（§3）。

### 唯一写入口

`EvidenceRepository`（`backend/app/repositories/evidence_repository.py`）：

- `append_event(event, *, candidate_id, source_version_id, review_proof=None)` — INSERT-only
- `append_human_review_event(...)` — 人工审核结果 → human_review 事件（proof 由调用方生成）
- `invalidate_claims_for_source_version(sv_id, reason=...)` / `invalidate_claims_for_annotation(annotation_id, reason=...)` — 级联（§5）

公共接口无 update/delete；模块级探针 `update_validation_event` / `delete_validation_event` 恒抛 `AppendOnlyViolation`。

### 生产调用链（谁写入）

```
GateService.run()
  └─ candidate 解析/复用后（需要 candidate.id）
     └─ EvidencePromotionService.record_validation(claim_id, gate,
            candidate_id=…, source_version_id=…, reference_ids=…)
        └─ EvidenceRepository.append_event()          # auto 路径，验证结果=gate 判定

AdmissionService.approve()  (human/golden)
  └─ _record_human_review(candidate, review_result="validated")
     └─ generate_review_proof(...) → append_human_review_event(...)

AdmissionService.reject()   (human/golden)
  └─ _record_human_review(candidate, review_result="rejected")

SnapshotRepository.set_annotation_status()  (valid→superseded)
  └─ EvidenceRepository.invalidate_claims_for_annotation(...)
```

---

## 2. Proof 生成流程

文件：`backend/app/domains/evidence/proof.py`

```
review_proof = SHA256(canonical_json({
    "candidate_id": str(uuid),
    "review_result": "validated" | "rejected",
    "reviewer_id": <str>,
    "reviewed_at": <UTC ISO-8601, timespec="microseconds">,
    "app_secret": <APP_SECRET>,
}))
```

- 哈希基元：`app.core.hashing.sha256_hex`（canonical_json：键字典序、禁 float、禁隐式转换）。
- 粒度 = **candidate 级**（绑定 candidate_id，不绑定 claim/unit）——92号 声明 1，冻结。
- 生成时机：`AdmissionService` human approve/reject 分支内，从 `review_trail` 最新对应 entry 取 `reviewer_id` 与 `time`（BUG-V3-025：time 由 `append_review_trail` 注入；缺失时 fail-safe 兜底当前 UTC），随即落 human_review 事件。
- 验证：`verify_review_proof(record)` — 要求 `validation_method=="human_review"` 且 `review_proof` 非空且 `validator` 为 `human/<id>` 前缀；重算后 `hmac.compare_digest` 恒时比较。非 human_review / 无 proof → 返回 False（fail-closed 由调用方执行）。
- `APP_SECRET`：`settings.app_secret`（.env 提供）；`require_app_secret()` 要求 ≥32 字节 UTF-8，缺失/过短抛 `RepositoryError`（fail-closed）。非 test 环境由 `main.py` lifespan 在启动时校验。

---

## 3. Authority 投影逻辑

文件：`backend/app/repositories/evidence_repository.py` + 状态机 `backend/app/domains/evidence/models.py`

```
project_authority(candidate_id, claim_id) -> (state, latest_record)
  events = find_events_for_claim(...)           # 按 validated_at 升序
  if not events: return (AUTHORITY_NONE, None)
  latest = max(events, key=validated_at)        # latest-by-validated_at wins（Rev-4 §5）
  return (latest.validation_result, latest)
```

状态常量：`AUTHORITY_NONE / VALIDATED / REJECTED / INVALIDATED`（定义于 domain `models.py`）。

**投影内不做 proof 验证**——Repository 管存储，Boundary 管准入（关注点分离）。proof 验证在 Admission Boundary（§4）。

### 状态机（唯一实现：`enforce_state_transition`）

domain `AppendOnlyEventLog`（内存）与 `EvidenceRepository.append_event`（DB）共用同一函数：

- 首事件：`validated`/`rejected` 允许；`invalidated` 禁止（无 prior VALIDATED）
- `rejected` / `invalidated` = **terminal**：拒一切新事件（无 resurrection；恢复路径 = 新 le_hash → 新 candidate → 新 Authority）
- `validated` → 仅 `invalidated` 允许

### Replay 语义（R1–R5）

`append_event` 在状态机检查**之前**判定：同 `(candidate_id, claim_id)` 既有 latest 同结果 → **no-op 返回既有行**（Authority 永不因 replay 改变；表内单行）。不同结果仍走状态机。

---

## 4. Admission Enforcement 位置

文件：`backend/app/domains/gate/admission.py`（Admission Boundary = 20 §8.2 段 G 唯一 decision-transition owner）

`approve()` 在 path 校验（auto_gate 需 `gate_decision=auto_approve`；human 需 review_trail 人工 approve entry）**之后**、物化**之前**：

```
if source in {human, golden}:
    await self._record_human_review(candidate, review_result="validated")   # §2
await self._require_evidence_authority(candidate)                            # ↓
```

`_require_evidence_authority`：

1. `claim_id = _candidate_claim_id(candidate)`（payload IR root unit_id）
2. `state, latest = project_authority(candidate.id, claim_id)`
3. 若 latest 为 `human_review` 事件 → `verify_review_proof(latest)`；False → `RepositoryError`（防 DB 篡改）
4. `state != VALIDATED` → `RepositoryError` — **fail-closed**：candidate 保持 `pending_review`，**不**自动 reject

双入口保持（20 §8.2）：

- **auto_gate**：依赖 Gate 已落的 validated 事件（§1 生产调用链）
- **human/golden**：enforcement 前自动生成 human_review 事件 + proof

`reject()`：human/golden 分支在 append review_trail 后生成 `rejected` 的 human_review 事件 + proof，再 transition。machine_gate 分支不写 ValidationEvent（Gate 已写 rejected 事件）。

---

## 5. Invalidate 生命周期

```
(none) ──validated──▶ VALIDATED ──invalidated──▶ INVALIDATED (terminal)
(none) ──rejected───▶ REJECTED (terminal)
```

- 级联入口：`invalidate_claims_for_source_version` / `invalidate_claims_for_annotation`；对每个 candidate 下每个 claim，latest==validated 时 append `invalidated` 事件（rejected/已 invalidated 跳过）。
- 审计：事件 `checks` 含 `{check_id:"INVALIDATE_CASCADE", result:"fail", detail:<reason>}`；validator 默认 `"system/v1"`。
- **生产接线（已接）**：`SnapshotRepository.set_annotation_status` 在 valid→superseded 时调用 annotation 级联。
- **生产接线（未接）**：source_version supersede 自动触发 — 方法已提供并测试，无生产触发点（见 §6 风险声明）。
- INVALIDATED 之后 `approve()` 必被 `_require_evidence_authority` 拒绝。无同 claim 复活路径。

---

## 6. 已接受风险（Owner 裁决，攻击测试不得当作新发现重复上报）

| # | 声明 | 依据 |
|---|---|---|
| R-1 | **proof 不负责 API 身份认证**。proof 唯一职责 = 防数据库直接篡改（改 review_result / 重放旧 proof → 验证失败）。谁能调 API 是外部问题。 | 92号 §2 声明 2 |
| R-2 | **APP_SECRET 泄露属于 Deployment Environment Boundary**。本地 .env 提供、不入库；泄露后攻击者可伪造 proof——这是部署边界失守，不是本层缺陷。secret 缺失/过短本身 fail-closed。 | 92号 §2 声明 3 |
| R-3 | **DB 触发器级 append-only 属于 Phase-2**。当前 append-only = 应用层（Repository 无 update/delete + insert 前状态机 + 探针函数）。拥有 DB 直连权限者可 UPDATE/DELETE——与 R-1/R-2 同属 Deployment Boundary 威胁模型（家庭内部弱信任模型）。92号 §7 风险 2 已记录此 trade-off。 | 92号 §5.5 |
| R-4 | **source_version supersede 自动触发属于 Source 域职责**。`invalidate_claims_for_source_version` 已提供并测试；Source 域尚无 supersede 生产流程可接线。annotation 级联已接。 | 92号 §5.4 |
| R-5 | **Machine validation events assume trusted in-process callers.** 自动路径不证明「谁产生了事件」，只证明「事件符合存储与状态机约束」。`append_event` 写入的机器 `validated` 事件会被 `auto_gate` approve 接受——与 R-3 同属 in-process / DB 信任模型。多服务 / 外部 Worker / 第三方 Gate 进入前须重开此项。 | Owner 2026-09-29 裁决（EB-008 A2 攻击向量） |

---

## 7. 攻击测试支持（DSH 操作手册）

测试基座：`backend/tests/eb008_helpers.py`（`seed_candidate` / `seed_validated_authority` / `CLAIM_ID`）；参考用例：`backend/tests/test_eb008_evidence_authority.py`（26 条验收测试，类名对应下列场景）。

### 7.1 如何制造非法 ValidationEvent

绕过正常业务路径、直接构造事件写入，以验证 Repository 层拒绝：

```python
# 非法 1：首事件即 invalidated（无 prior VALIDATED）→ ValueError
await repo.append_event(
    ValidationEvent(event_id="ve-x", claim_id="Q1", validation_result="invalidated",
                    checks=(), validation_method="byte_proven", validator="system/v1",
                    validated_at=now),
    candidate_id=cand.id, source_version_id=sv.id,
)
# 预期：ValueError("Cannot INVALIDATE claim ...")

# 非法 2：terminal 后追加（先 rejected 再 validated）→ ValueError
# 非法 3：VALIDATED 后再 append validated（同结果走 replay no-op 返回既有行，
#         不同结果非法迁移才抛）
# 非法 4：human_review 事件缺 review_proof → RepositoryError
# 非法 5：非法值域（validation_result="maybe"）→ ValidationEvent.__post_init__ ValueError
```

参考：`TestAppendOnlyProtection.test_insert_replay_and_state_machine`、`TestValidationEventsPersistence.test_state_machine_violation_raises`。

### 7.2 如何验证 proof 失败

```python
proof = generate_review_proof(candidate_id=cid, review_result="validated",
                              reviewer_id="r1", reviewed_at=ts)
# 篡改 result / reviewer / 时间 / proof 字符串任一 → verify_review_proof False
# DB 篡改攻击：直接 UPDATE validation_events SET validation_result='rejected'
#   WHERE …（利用 R-3 的 DB 直连能力）→ 下次 approve 时 Boundary verify 失败 → 拒
```

参考：`TestReviewProof.test_tampered_result_fails_verify`、`TestAdmissionEnforcement.test_tampered_human_proof_blocks_approve`。

另可测：`APP_SECRET=""` 或 <32 字节 → `require_app_secret` / generate / verify 抛 `RepositoryError`（fail-closed，不 fail-open）。

### 7.3 如何验证 Authority 投影 fail-closed

```python
# 无事件：approve(auto_gate) → RepositoryError("Evidence Authority fail-closed: ... authority='none'")
# rejected 事件为 latest → approve 被拒
# invalidated 事件为 latest → approve 被拒；且后续 append 任何事件 → ValueError（terminal）
# 被拒后 candidate.decision_status 仍 == "pending_review"（不自动 reject）
```

参考：`TestAdmissionEnforcement`（fail-closed 用例）、`TestInvalidateCascade.test_invalidate_blocks_approve`。

### 7.4 如何验证 replay 一致性

```python
# 同一 (source_version, annotation) 跑两次 GateService.run()：
#   - admission_candidates 恰 1 行（le_hash 幂等复用）
#   - validation_events 恰 1 行（append_event replay no-op）
#   - project_authority 结果与第一次相同（Authority 不因 replay 改变）
# 新 session 重读投影不变（持久化，非内存）
```

参考：`TestReplayConsistency.test_gate_rerun_same_le_single_authority`、`TestValidationEventsPersistence.test_replay_noop_single_row`。

---

## 8. 禁止事项（本阶段硬边界）

1. **禁止增加新的业务字段**（validation_events / proof schema / candidate Authority 相关）。
2. **禁止修改 Frozen Decision**（92号 FINAL / DEC-016；Identity Model、双入口、状态机、proof 边界声明均已冻结）。
3. **禁止改变 le_hash 定义**（compile identity，语义身份）。
4. **禁止将 run_id 引入 Authority**（I6；表、投影、proof 均不得出现）。

实现层可做的只有：修 bug、补测试、补攻击证据。任何上述 4 类改动需求 → 上报 Owner 裁决，不得在实现阶段自行变更。

---

## 9. 文件清单（实现 commit `88aeae8`）

| 文件 | 角色 |
|---|---|
| `backend/app/models/evidence.py` | ValidationEventRecord ORM |
| `backend/alembic/versions/20260915_0011_validation_events.py` | migration 0011 |
| `backend/app/repositories/evidence_repository.py` | 唯一写入口 + 投影 + 级联 |
| `backend/app/domains/evidence/proof.py` | proof 生成/验证 |
| `backend/app/domains/evidence/models.py` | 状态机 `enforce_state_transition` + AUTHORITY_* 常量 |
| `backend/app/domains/evidence/promotion.py` | DB-backed EvidencePromotionService |
| `backend/app/domains/gate/service.py` | Gate 落事件接线 |
| `backend/app/domains/gate/admission.py` | Admission Boundary enforcement |
| `backend/app/repositories/snapshot_repository.py` | annotation supersede 级联接线 |
| `backend/app/core/config.py` / `main.py` / `backend/.env.example` | APP_SECRET 配置与启动校验 |
| `backend/tests/eb008_helpers.py` | 测试 seed |
| `backend/tests/test_eb008_evidence_authority.py` | 26 条验收测试 |

---

## 10. P1 终态冻结（2026-09-29，Owner 收敛；不新建文档）

```text
EB-008 P1 : CONVERGED at 25933c3
全量测试   : 2096 passed / 1 skipped / 1 xfailed（xfail = F-4 空白 marker）
EB-008 验收: 26/26（test_eb008_evidence_authority.py）
```

| 项 | 终态 | 锚 / 证据 |
|---|---|---|
| **A1** 时间戳投影 / naive 时间 | **CLOSED** | `b15c9fe` + `25933c3`；`test_eb008_attack_vectors.py`、`test_adv_reaudit*.py` |
| **R-5** 机器事件无 Gate 溯源 | **ACCEPTED RISK**（非 bug / 非 TODO / 非 security debt） | Notes §6 R-5；`test_machine_event_relayed_without_provenance_proof__r5` 钉住边界 |
| **OD-R-01** Answer 业务对象 | **PARTIAL CONFIRMED** | 1 Instance × 1 Answer `role_index=0` 成立；`Answer→N ordered values` **未建模** |
| **D-07 / D-08** representation | **OPEN**（待 Owner） | CR-003 §6 显式排除；不据本节推导 |
| **R-1..R-4** | 仍按 §6 | 不变 |

**边界（本节不扩大解释）：**

```text
不做：再扫攻击向量 / 重审 Frozen Spec / 回头改历史报告 / 为 R-5 建 Decision / 为 OD-R-01 建治理文件
A1 关闭含义：UTC-aware + naive-as-UTC 下未来时间与 naive 时间均被拒或合法归一；不等于零信任
R-5 含义：架构选择信任 in-process machine caller；多服务 / 外部 Worker 进入前须重开
OD-R-01 半确认含义：只证到「缺 N-values 载体」，不裁 representation
```

**下一阻塞（业务裁决，非代码质量）：** CR-003 STOP 解除条件 = OD-R-01 representation（D-07/D-08）+ D2/D3/D4（OD-002/OD-003）。

