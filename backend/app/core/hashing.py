"""V3 canonical hashing utility（30 §16 / 00 P6 落地，段 A）。

身份语义：
- logical_execution_hash 由 { task_type, stage, contract_domain(stage), input_domain(stage) }
  的 canonical JSON 的 SHA-256 得出；**不含 task_id**，不含 attempt/worker/时间。
- canonical_json 是 V3 logical identity primitive，**不是 JSON 通用序列化器**：只支持
  dict/list/int/str/float/None/bool；其余类型（datetime/UUID/Decimal/set/自定义）显式抛错，
  **禁止 default=str 类隐式转换**。

数字规范纪律（BUG-V3-005 终裁）：float **不是**允许的 identity 输入类型。identity domain
不需要连续浮点，为 float 冻结 precision 是 YAGNI；canonical identity 序列化遇 float 必须
fail-fast（`_ALLOWED` 不含 float）。身份 schema 需要数值时必须用显式非 float 的确定性表示。
"""

import hashlib
import json

HASHING_UTILITY_VERSION = "1.0.0"

_ALLOWED = (dict, list, str, int, bool)


def _reject_float(obj) -> None:
    """递归探测 float（BUG-V3-005）：identity 输入任意嵌套层出现 float → fail-fast。"""
    if isinstance(obj, float):
        raise ValueError(
            "float forbidden in canonical identity input (BUG-V3-005); "
            "use an explicit non-float deterministic representation"
        )
    if isinstance(obj, dict):
        for key, value in obj.items():
            _reject_float(key)
            _reject_float(value)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _reject_float(item)


def canonical_json(obj: object) -> str:
    """确定性序列化：键字典序、无多余空白、字符串 UTF-8、数组保序。

    float 禁止（BUG-V3-005）：identity domain 不需要浮点；任意层级遇 float fail-fast。
    """
    if obj is not None and not isinstance(obj, _ALLOWED):
        raise ValueError(
            f"unsupported type in canonical input: {type(obj).__name__}; "
            f"allowed: dict/list/int/str/bool/None (float forbidden, BUG-V3-005)"
        )
    _reject_float(obj)
    try:
        return json.dumps(
            obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"unsupported type nested in canonical input: {exc}"
        ) from exc


def sha256_hex(obj: object) -> str:
    """canonical_json -> UTF-8 bytes -> SHA-256 -> lowercase 64-char hex。"""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def logical_execution_hash(
    *,
    task_type: str,
    stage: str,
    contract_domain: dict,
    input_domain: dict,
) -> str:
    """30 §16：hash = SHA256(canonical_json({task_type, stage, contract_domain, input_domain}))。

    调用方（段 B/C/D）喂入各 stage 的 contract/input 域；本函数不做业务语义。
    """
    payload = {
        "task_type": task_type,
        "stage": stage,
        "contract_domain": contract_domain,
        "input_domain": input_domain,
    }
    return sha256_hex(payload)
