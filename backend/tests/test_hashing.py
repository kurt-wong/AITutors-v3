"""Gate A4 — canonical_json / sha256_hex / logical_execution_hash 黄金测试（30 §16）。"""

import hashlib
import uuid
from datetime import date

import pytest

from app.core.hashing import canonical_json, logical_execution_hash, sha256_hex


def test_canonical_json_key_order_independent_golden() -> None:
    obj = {"b": 2, "a": [2, 1], "nested": {"y": 1, "x": 2}}
    assert canonical_json(obj) == '{"a":[2,1],"b":2,"nested":{"x":2,"y":1}}'
    # 同键序同串（递归确定性）
    assert canonical_json({"nested": {"x": 2, "y": 1}, "a": [2, 1], "b": 2}) == canonical_json(obj)


def test_canonical_json_array_order_preserved() -> None:
    assert canonical_json([1, 2]) != canonical_json([2, 1])


def test_canonical_json_scalars_stable() -> None:
    assert canonical_json(7) == "7"
    assert canonical_json("中文") == '"中文"'  # UTF-8，不 ASCII 转义
    assert canonical_json(None) == "null"
    assert canonical_json(True) == "true"
    assert canonical_json(False) == "false"


def test_canonical_json_float_forbidden() -> None:
    """BUG-V3-005：float 禁止进入 canonical identity serialization，任意层级遇 float fail-fast。"""
    for bad in (1.5, 1e-5, 0.30000000000000004, 2.0, -0.0):
        with pytest.raises(ValueError):
            canonical_json(bad)
    # 嵌套 float 同样 fail-fast（json.dumps 会静默序列化 float，须在序列化前拦截）
    for bad in ({"score": 1.5}, {"x": [1, 2.0]}, [1, {"y": 0.1}]):
        with pytest.raises(ValueError):
            canonical_json(bad)


def test_canonical_json_unsupported_raises() -> None:
    for bad in ({1, 2}, date(2026, 9, 5), uuid.uuid4(), {"x": b"bytes"}):
        with pytest.raises(ValueError):
            canonical_json(bad)


def test_canonical_determinism_over_runs() -> None:
    obj = {"task_type": "document_ingest", "stage": "seal", "nested": {"a": [1, 2, 3]}}
    out = canonical_json(obj)
    for _ in range(3):
        assert canonical_json(obj) == out


def test_sha256_hex_is_lowercase_64() -> None:
    h = sha256_hex("x")
    assert len(h) == 64
    assert h == h.lower()
    assert h == hashlib.sha256(b'"x"').hexdigest()


def test_logical_execution_hash_deterministic() -> None:
    args = dict(task_type="document_ingest", stage="seal",
                contract_domain={"resolver": "v1"}, input_domain={"file_sha": "abc"})
    assert logical_execution_hash(**args) == logical_execution_hash(**args)


def test_le_hash_identity_inputs_change_it() -> None:
    base = dict(task_type="document_ingest", stage="seal",
                contract_domain={"resolver": "v1"}, input_domain={"file_sha": "abc"})
    assert logical_execution_hash(task_type="re-annotate", stage=base["stage"],
                                  contract_domain=base["contract_domain"],
                                  input_domain=base["input_domain"]) != logical_execution_hash(**base)
    assert logical_execution_hash(task_type=base["task_type"], stage="ann",
                                  contract_domain=base["contract_domain"],
                                  input_domain=base["input_domain"]) != logical_execution_hash(**base)


def test_le_hash_no_task_id_variation_surface() -> None:
    """签名不含 task_id/attempt/time——仅同输入重复即稳定；身份只随 task_type/stage/contract/input 变。"""
    args = dict(task_type="document_ingest", stage="compile",
                contract_domain={"compiler": "v1"}, input_domain={"annotation_id": "u"})
    a = logical_execution_hash(**args)
    for _ in range(3):
        assert logical_execution_hash(**args) == a
