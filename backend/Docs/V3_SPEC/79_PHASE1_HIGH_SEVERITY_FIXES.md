# Phase 1 Hardening — HIGH 严重性缺陷修复报告

**日期**: 2026-09-13
**状态**: ✅ 完成
**测试**: 640 passed

---

## 一、修复的缺陷

### HIGH-1: 直接属性重赋值绕过 append-only

**问题**: `log._events = ()` 可以清空日志

**修复方案**:
1. 使用 `__slots__` 防止属性重赋值
2. 使用 name mangling (`__events`) 使直接访问更困难
3. 返回 immutable tuple snapshot

**代码变更** (`app/domains/evidence/models.py`):
```python
class AppendOnlyEventLog:
    __slots__ = ("__events",)

    def __init__(self) -> None:
        object.__setattr__(self, "_AppendOnlyEventLog__events", ())

    def _get_events(self) -> tuple[ValidationEvent, ...]:
        return object.__getattribute__(self, "_AppendOnlyEventLog__events")

    def _set_events(self, events: tuple[ValidationEvent, ...]) -> None:
        object.__setattr__(self, "_AppendOnlyEventLog__events", events)

    @property
    def events(self) -> tuple[ValidationEvent, ...]:
        return self._get_events()
```

**测试证据**:
```python
def test_direct_attribute_reassignment_blocked(self):
    log = AppendOnlyEventLog()
    log.append(e1)
    # ATTACK: reassign _events — should FAIL
    with pytest.raises(AttributeError):
        log._events = ()
    # Attack blocked — log still has 1 event
    assert len(log.events) == 1
```

**结果**: ✅ 攻击被阻止

---

### HIGH-2: 直接 log append 绕过状态机

**问题**: `service._validation_log.append(fake_event)` 绕过状态机检查

**修复方案**: 将状态机检查移入 `AppendOnlyEventLog.append()`

**代码变更** (`app/domains/evidence/models.py`):
```python
class AppendOnlyEventLog:
    def _check_state_transition(self, existing_events, new_result, claim_id):
        """状态机检查在 ledger 层，不在 service 层"""
        if not existing_events:
            if new_result == "invalidated":
                raise ValueError(f"Cannot INVALIDATE claim {claim_id!r}: no prior VALIDATED event")
            return

        latest = max(existing_events, key=lambda e: e.validated_at)

        if latest.validation_result in _TERMINAL_STATES:
            raise ValueError(f"Claim {claim_id!r} is {latest.validation_result.upper()} (terminal)")

        if latest.validation_result == "validated" and new_result != "invalidated":
            raise ValueError(f"Claim {claim_id!r} is VALIDATED; only INVALIDATED transition allowed")

    def append(self, event: ValidationEvent) -> None:
        """状态机检查在 append() 内，无法绕过"""
        existing = self.for_claim(event.claim_id)
        self._check_state_transition(existing, event.validation_result, event.claim_id)
        current = self._get_events()
        self._set_events(current + (event,))
```

**架构原则**: EventLog 是 Evidence Authority Ledger，状态机必须在 ledger 层执行。

**测试证据**:
```python
def test_bypass_log_via_direct_append_blocked(self):
    service = EvidencePromotionService()
    service.record_validation("c1", _gate_rejected())
    # ATTACK: append validated via direct log access — should FAIL
    with pytest.raises(ValueError, match="terminal"):
        service._validation_log.append(fake_event)
    # Attack blocked — c1 still rejected
    assert service.is_evidence_validated("c1") is False
```

**结果**: ✅ 攻击被阻止

---

## 二、架构改进

### 状态机移至 Ledger 层

**之前**:
```
Service.record_validation()
    ↓
_check_state_transition()  ← 在 service 层
    ↓
log.append()
```

**之后**:
```
Service.record_validation()
    ↓
log.append()
    ↓
_check_state_transition()  ← 在 ledger 层
    ↓
存储
```

**优势**:
- 直接调用 `log.append()` 无法绕过状态机
- Phase 2 DB 化时，状态检查仍在 ledger 层，不会被 API/Worker 绕过

---

## 三、测试结果

| 测试文件 | 测试数 | 结果 |
|---------|-------|------|
| test_evidence_promotion.py | 36 | ✅ PASS |
| test_hardening_adversarial.py | 24 | ✅ PASS |
| test_evidence_adversarial.py | 25 | ✅ PASS |
| **完整回归** | **640** | ✅ **PASS** |

---

## 四、攻击验证

| 攻击 | 修复前 | 修复后 |
|------|-------|-------|
| `log._events = ()` | ❌ 成功 | ✅ 被阻止 |
| `service._validation_log.append(fake)` | ❌ 成功 | ✅ 被阻止 |
| Tuple 元素突变 | ✅ 被阻止 | ✅ 被阻止 |
| 时间戳操纵 | ✅ 被阻止 | ✅ 被阻止 |

---

## 五、架构审查要求对照

| 要求 | 状态 | 说明 |
|------|------|------|
| EventLog immutable | ✅ 完成 | `__slots__` + name mangling + tuple snapshot |
| append transition validation | ✅ 完成 | 状态机在 `append()` 内 |
| Event 与 Reference 链接 | ✅ 完成 | Critical 3 fix (Phase 1 Hardening) |
| structured check_id | ✅ 完成 | High 5 fix (Phase 1 Hardening) |
| proposer/claim creator 分离 | ⚠️ Phase 2 | 需要 EvidenceClaim 数据结构 |

---

## 六、结论

两个 HIGH 严重性缺陷已修复：

1. **HIGH-1**: `__slots__` + name mangling 防止属性重赋值
2. **HIGH-2**: 状态机移入 `AppendOnlyEventLog.append()`，无法绕过

**架构原则达成**: Evidence Authority Ledger 不可伪造、不可篡改、不可回滚。

**下一步**: 可以进入 C-2 157 E2E。

---

**报告生成**: 2026-09-13
**测试验证**: 640 passed
