# P1 Composite 跨题写入修复 — DSH 独立复核

复核对象：MIMO《P1 Composite 跨题答案写入 — 修复交付》
结论：**不通过。跨父实例的主路径已加成员集合，但仍存在“无 role 行 + 有 qn/range”的 fail-open；且反例测试并未构造两个真正的 composite parent instance。不 commit、不 push。**

---

## 1. 已成立的部分

- 旧 `_is_composite` 分支已删除；`content_repository.create_role_content` 现在对所有非空 official 统一读取该 instance 已有 role 行的 `source_span.unit_id`，要求 `fact.unit_id ∈ known_units`（`content_repository.py:314-336`）。
- 有 role 行时，跨父实例（目标 B 只有 Q3/Q4 stems，fact 属于 A 的 Q2）会被成员集合拒绝。
- 无 role 行且无 qn/range 时，`RepositoryError`（`:337-355`）。
- 合法 composite 正向：`test_gate_service.py` 的 composite 真实链路 45 passed；`test_p0_r14` 13 passed；`p2 dedup + real_e2e + domain_keys` 31 passed。
- `git diff --check` 仅 CRLF warning；HEAD `f8316fc`；未 commit。

---

## 2. 阻断问题：无 role 行但有 qn/range 时仍 fail-open

`content_repository.py:337-374` 的 fallback：

```python
else:
    # No persisted unit identity on role rows. Fall back to
    # question-number / range (instance + unit_group).
    ...
    _qn_sources = (_instance_qn, _instance_qn_range, _ug_range)
    _has_qn_identity = any(s.strip() for s in _qn_sources)
    if not _has_qn_identity:
        raise RepositoryError(...)
    if not any(_qn_belongs_to_instance(...) for src in _qn_sources):
        raise RepositoryError(...)
```

这没有做到任务第 6 条“信息不足时 fail-closed”：

- 一个 composite parent B **没有任何 per-child unit 行**，只有 `question_number_range="1-5"`；
- 来自 parent A 的 Q2 fact，`fact.question_number="2"` 落在 B 的 1-5 内；
- 代码认为归属成立，非空 official 写入被接受。

我用真实 DB 临时探针（已删除）验证：

```text
tests/_dsh_probe_composite_gap.py
  test_composite_no_roles_but_range_accepts_foreign_child_fact
  -> 1 passed
```

该探针构造 `UnitGroup(unit_type="composite_unit")`、instance 无 qn/range 的 role 行但 range `1-5`，用 Q2 fact + seal 写入，断言 `row.text == "B"` **通过**。qn/range 只能证明“题号在范围内”，不能证明该 fact 属于这个 composite 父实例；两个 composite 父实例 range 重叠时无法区分。任务要求此时拒绝，当前代码放行。

### 需要的最小修复

在 `_known_units` 为空的分支：

- 查 `UnitGroup.unit_type`；
- 若 instance 属于 `composite_unit`：直接 `RepositoryError`（没有 per-child unit 身份，不能确认归属）；
- 仅 standalone 保留 qn/range fallback；
- 仍无 qn/range → 拒绝。

并补真实 DB 测试：composite B 无 role 行、range `1-5`，A 的 Q2 fact 写入必须拒绝，DB 无非空 official。

---

## 3. 反例测试不满足任务 A 的“两个 composite parent instance”

`test_p0_r14_fact_question_binding.py:417-488`：

- 只创建了目标 B：`qi_b = await _seed_instance(session, SVID)`；
- `_seed_instance`（`test_p0_publish_contract.py:78-125`）创建的是 **普通 standalone instance**，没有 `unit_group_id`，也没有 `UnitGroup(unit_type="composite_unit")`；
- 没有创建 parent A 的 instance，A 只是一个 resolver fact；
- B 的 stems 是手工 `create_role_content(role="stem", source_span={"unit_id": ...})` 写入的，不是真实 composite 父子结构。

因此该测试证明的是“fact.unit_id 不在已知 role unit 集合中会被拒绝”，不是任务要求的“两个 composite parent instance 之间跨写被拒绝”。报告“构造两个不同的 composite parent instance”与代码不符。

需要改成：

1. 创建两个 `UnitGroup(unit_type="composite_unit")` 的 parent instance A/B；
2. 两者 `question_number=""`、`question_number_range=""`；
3. A 有子题 stems Q1/Q2（真实 Q2 fact 来源），B 有 Q3/Q4；
4. Q2 fact + seal 写 B，省略 `binding_*`；
5. 断言 `RepositoryError`；DB 回读 B 无非空 official。

同时保留正向：同一 parent A 的 Q2 fact 写 A 成功（现有 `test_composite_sibling_fact_same_parent_accepted` 也应改为真实 composite，而不是 plain instance）。

---

## 4. C 项覆盖不完整

`test_no_unit_identity_and_no_qn_fails_closed`（`:548-585`）只覆盖“无 unit 且无 qn/range”。缺少：

- composite 无 role unit、但有 qn/range → 应拒绝（当前放行，见第 2 节）；
- 无 role unit、qn/range 与 fact 不匹配 → 应拒绝；
- 正向 standalone 无 role unit 但 qn 精确匹配 → 应接受（控制组）。

---

## 5. 其它观察（不改变本次不通过结论）

- `_known_units` 来自该 instance 的所有 role 行，而 `create_role_content(role="stem"/"answer", text="")` 允许调用方写任意 `source_span.unit_id`；若 Repository 的调用方不可信，攻击者可先写一个 `unit_id=Q2` 的 stem 空行，再写 Q2 fact。任务把 stem 的持久化 `source_span` 列为候选可信信息，因此这不是本次唯一阻断，但它意味着“成员集合”不是独立于调用方的信任锚；需明确调用方信任边界，或只从 admission 可控路径取 unit 身份。
- 本次实测：`test_p0_r14` 13 passed；`test_gate_service + golden + publish` 45 passed；`p2 + real_e2e + domain_keys` 31 passed。未跑全量/前端全量。
- 工作区：65 项差异（含本 review 目录与既有未提交修改）；HEAD `f8316fc`；未 commit、未 push、未 E2E。

---

## 6. 裁决

**不通过，不 push。**

必须先修：

1. composite 在 `_known_units` 为空时 fail-closed，不允许仅凭 qn/range 放行；
2. 反例测试改成真正的两个 composite parent instance（UnitGroup=composite_unit）；
3. 补 C 项“无 role unit + 有 qn/range”的真实 DB 拒绝测试。

三项目标测试通过后，再交 DSH 审阅最终 diff；合法 composite 正向（`test_gate_service`）不得回归。
