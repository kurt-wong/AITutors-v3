# Phase 2 最小修复 — DSH 独立复核

复核对象：MIMO《Phase 2 最小修复与定向验证 — 交付报告》
复核时间：本轮 DSH 实测（非引用报告数字）
结论：**P1-A 已关闭；P1-B 只关闭了 standalone 的“省略 binding 字段”路径，Repository 仍不是报告所称的“unbypassable”。不 push。**

---

## 1. 实测基线

| 项目 | 实测 |
|---|---|
| HEAD | `f8316fcdf180730c8a81aad9e79b2c6ecdd4a581` |
| ahead | 4（`origin/od01-r3-convergence = 755563d`） |
| 工作区 | 29 modified + 35 untracked = 64；无 staged |
| 后端全量 | **3001 passed / 6 failed / 2 skipped / 1 xfailed / 2 errors**，73.92s |
| 历史失败 | 6F 与 2E 与既有基线一致，非本轮新增 |
| 前端 | `AnswerSection.test.tsx` 9 passed |
| 保护库 | 未触碰；测试仅 `aitutors_testsuite` |
| commit/push/E2E | 未 commit、未 push、未启动真实 E2E |

全量失败仍是：`test_adv_state_audit` ×2、`test_migration_replay`、`test_models_schema`、`test_preprocessing_import_negative`、`test_providers`；2 ERROR 仍是 `test_question_dedup_concurrency` 的 FK 清理。报告的全量数字成立。

---

## 2. P1-A：域分离密钥 — 已关闭

代码证据：

- `backend/app/core/secrets.py:21-45`：`require_app_secret()` 对 `settings.app_secret` 做 ≥32 字节校验；`derive_domain_key(label)` 用 `HMAC-SHA256(secret, label)` 派生；无固定密钥回退。
- `binding_fact.py:47-51`、`publish_seal.py:28-32`：只保留 label，旧 `_FACT_KEY` / `_SEAL_KEY` 常量已移除；全局 grep 未发现旧常量或其它硬编码 HMAC key。
- `conftest.py:17` 在 app import 前注入 32+ 字节 test secret。

实测：

```
pytest tests/test_p0_r16_domain_keys.py -q  -> 10 passed
```

10 个测试覆盖 issue/verify 往返、不同 label 密钥不等、同 label 稳定、缺失/过短 secret 连续两次 fail-closed、篡改 fact_id/ownership/seal/文本失败、foreign 不能签发非空 official。

**结论成立**：P1-A 已关闭。

仍需登记的 P2：

1. `main.py:14-21` 启动校验用的是 `app.domains.evidence.proof.require_app_secret`，与 `app.core.secrets.require_app_secret` 是两份重复实现（阈值同为 32 字节）。当前行为一致，但未来改阈值/错误类型会分叉。建议启动校验也走 `app.core.secrets`。
2. `derive_domain_key` 的 `_derived` 缓存只按 label 缓存，不绑定 secret。生产进程内不轮换 secret 时无影响；若运行期轮换，旧缓存会继续签发。需明确“secret 变更必须重启进程”，或让缓存 key 包含 secret 摘要。
3. 没有测试“旧硬编码 key 签出的 fact/seal 必须被拒绝”。代码上旧 key 已删除，风险低，但严格说这是 P1-A 的回归缺口。
4. 未定义 APP_SECRET 轮换时已持久化 `answer_status.publish_seal` 的处置策略。seal 在 Repository 写入时校验，历史行读取时不重验；但重新物化/重放时旧 seal 会失败。需在运维文档中写明。

---

## 3. P1-B：Repository 独立归属 — 只关闭了 standalone 路径

### 3.1 已修好的部分

`content_repository.py:230-357` 现在从 DB 取：

```
QuestionInstance.source_version_id / question_number /
question_number_range / unit_group_id
UnitGroup.unit_type
InstanceRoleContent(role=stem).source_span.unit_id
```

并对非空 official：

- registry fact 必须存在且 `verify_binding_fact` 通过；
- fact SV 必须等于 DB instance SV；
- fact unit_id / question_number 必须非空；
- instance 有 qn/range 时，fact qn 必须等于 qn 或落在 range 内；
- standalone 且 stem 有 unit_id 时必须与 fact unit_id 相等；
- standalone 且 instance 无 qn 且 stem 无 unit_id → 拒绝；
- 调用方 `binding_unit_id` / `binding_question_number` 降为附加检查，省略不再跳过主门。

新测试 `test_q2_fact_q1_instance_rejected_when_status_omits_binding_fields`（`test_p0_r14...:288-338`）走真实 `create_role_content` + DB 回读，Q2 fact 写 Q1 instance 且故意省略两个 binding 字段 → `RepositoryError`，DB 无非空 official。这一条**成立**。

`pytest tests/test_p0_r14_fact_question_binding.py -q -> 10 passed`。

### 3.2 仍未关闭：composite 无 qn/range 时整段身份检查被跳过

`content_repository.py:323-345`：

```python
_is_composite = (
    _ug_type == "composite_unit"
    or _is_range_qn(_instance_qn)
    or _is_range_qn(_instance_qn_range)
)
...
if not _is_composite:
    # stem unit 等值 + “无 qn 且无 stem → 拒绝”都在这里
```

也就是说，只要 instance 的 `UnitGroup.unit_type == "composite_unit"`，即使该 instance **既无 question_number 也无 question_number_range**，上述两个独立门（stem unit 等值、缺身份拒绝）全部跳过。此时 Repository 只剩 fact 自洽 + SV + 非空 unit/qn + seal；**Q2 fact 可以写到另一个无 qn/range 的 composite parent instance**，只要 span_id 指向该 fact、文本与 seal 匹配。

这不是理论路径：`tests/test_gate_service.py:71-88` 的 composite fixture 就没有 `question_number_range`。而报告第 8 节自己也承认“composite 且 instance 无 qn/range 时仅靠 fact 自洽（残留风险）”。

因此：

- 报告“Repository 独立核验题目归属”对 standalone 成立；
- 对 composite 无 qn/range 不成立；
- “Repository 是最后守卫 / unbypassable”的结论不成立，仍是 P1 级防御纵深缺口（是否阻断 push 由 Owner 裁决，但不能按“P1 三项已修复”直接放行）。

需要补的验证（二选一）：

- **收窄**：对 composite 实例，若 `question_number`/`question_number_range` 都为空，则拒绝非空 official（要求 composite 必须有可核验范围）；或
- **补身份**：从 composite 的 child unit 集合（IR/UnitGroup 结构）核验 `fact.unit_id` 属于该 composite，或核验 fact qn 属于 child qn 集合。

并补一个真实 DB 测试：composite parent 无 qn/range + 另一个子题 fact → 必须拒绝，DB 无非空 official。当前没有这个测试。

### 3.3 另外三个测试质量问题

1. `test_explicit_wrong_qn_in_status_rejected`（`test_p0_r14...:340-376`）把 `binding_question_number` 设为 `"2"`，与 fact 一致，不是“status 错误值”；实际拒绝来自 instance qn 检查，未覆盖 status 字段本身。测试名与行为不符。
2. `test_instance_without_qn_fails_closed`（`:378-415`）只覆盖“instance 无 qn 且无 stem”；没有覆盖“无 qn 但 stem unit_id 与 fact 不一致”以及“stem unit_id 与 fact 一致时接受”的控制组。名称“without qn fails closed”过度概括。
3. `test_materialize_qn_check_logic` / `test_materialize_qn_check_accepts_matching` 仍是纯 predicate 复刻，不调用生产代码；它们是旧文件里的 P2，不应计入 P1-B 的证据。

---

## 4. P2 清理项复核

| 项 | 结果 |
|---|---|
| 非 test 缺 `APP_SECRET` fail-closed | 代码 + 10 测试成立；但启动检查与签名检查是两份实现（P2） |
| `test_p0_r16_final_golden_db.py:246` `assert rows` | 已补，成立 |
| `test_p0_r16c_manifest_boundary.py:266/307` 非空前置 | 已补，成立 |
| API 字段裁剪 | `questions.py:33-44` 只 drop `candidate_text`/`publish_seal`/`binding_fact_id`/`answer_text_hash`；仍暴露 `binding_unit_id`、`binding_question_number`、`binding_evidence`、`publish_grant`。且 `_public_answer_status` 只在 `get_question` 使用，没有 API 级测试。属 P2/P3。 |
| frontend `test` script | 已加，`npx vitest run` 9 passed |
| 大文件清单 | 本报告未再重复“体积无异常”的旧结论；Phase 2 报告的大文件错误仍需在最终清单中更正 |

补充：报告称“定向全集 14 个文件 282 passed”，我按报告可命名的 14 个文件实测是 **278 passed**：

```
domain_keys 10 + r14 10 + publish 24 + golden 2 + manifest 7 +
decode 20 + r12 27 + a8 6 + replay 5 + bio001 1 + real_e2e 5 +
r3 18 + r4 107 + r5 36 = 278
```

若把 `test_approve_reuse_verified.py`（5）计入、剔除 `test_p0_r16c_bio001.py`（1），则正好 282。报告没有给出文件清单，无法核对“14 个文件 282”的口径。请给出精确定义；否则按 278 记录。

---

## 5. 裁决

**可以确认：**

- P1-A 域分离密钥已关闭；
- P1-B 的“省略 binding_unit_id/binding_question_number 的 standalone Q2→Q1 攻击”已关闭，且是真实 DB 测试；
- 全量 3001/6/2/1/2 与历史基线一致，0 新增失败；
- 未 commit、未 push、未 E2E、未触碰保护库。

**不能确认：**

- “P1 三项阻断已修复”——报告只明确 P1-A/P1-B；“第三项”没有名称和证据；
- “Repository 独立核验”作为普遍结论——composite 无 qn/range 时整段身份门跳过，是已知 P1 残留，且没有测试；
- “定向全集 282”——按报告可命名的文件是 278，口径不明。

**结论：不 push。** 先处理二选一：

1. 收窄 composite 无 qn/range 路径并补真实 DB 拒绝测试；或
2. 由 Owner 明确接受该残留，并在报告中把它从“P1 已关闭”改为“已知 P1 残留，Owner 接受”，同时补测试证明可达性/影响面。

之后才进入“确认 push 版本与提交范围”阶段；真实 E2E 仍在 push 之后。生产开关继续冻结。
