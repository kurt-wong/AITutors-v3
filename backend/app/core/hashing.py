"""V3 canonical hashing utility（30 §16 / 00 P6 落地，段 A）。

身份语义：
- logical_execution_hash 由 { task_type, stage, contract_domain(stage), input_domain(stage) }
  的 canonical JSON 的 SHA-256 得出；**不含 task_id**，不含 attempt/worker/时间。
- canonical_json 是 V3 logical identity primitive，**不是 JSON 通用序列化器**：只支持
  dict/list/int/str/float/None/bool；其余类型（datetime/UUID/Decimal/set/自定义）显式抛错，
  **禁止 default=str 类隐式转换**。

数字规范纪律：30 §16 要求浮点按定长十进制、避免科学计数/尾数漂移，但未冻结 precision 位数
（规格缺口，见 bugs.md）。本实现用 Python 浮点 repr 语义（`json.dumps` 对 float 即调用
`float.__repr__`）作**临时 deterministic representation**，不代表对 30 §16 最终语义的冻结
解释；当前 LE hash 身份输入不含 float，不阻塞 Gate A4/A5。
"""

import hashlib
import json

HASHING_UTILITY_VERSION = "1.0.0"

_ALLOWED = (dict, list, str, int, float, bool)


def canonical_json(obj: object) -> str:
    """确定性序列化：键字典序、无多余空白、字符串 UTF-8、数组保序。"""
    if obj is not None and not isinstance(obj, _ALLOWED):
        raise ValueError(
            f"unsupported type in canonical input: {type(obj).__name__}; "
            f"allowed: dict/list/int/str/float/bool/None"
        )
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
