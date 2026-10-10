"""Producer → V3/X Integration Boundary：确定性词表归一化 + 边界校验。

边界位置（X2.6 integration task §8）::

    Producer / preprocessing（legacy vocabulary）
            │  Producer contract（Frozen Contract 9c6b9063…17528）
            ▼
    Integration Boundary  ← 本模块
            │  normalize + validate（确定性；无 LLM；不猜）
            ▼
    V3 canonical IR（Unit Type ∈ {standalone_unit, composite_unit}）

**性质**：这是 **boundary normalization rule**（legacy vocabulary normalization），
**不是** semantic Question-Type→Unit-Type mapping。Question Type 与 Unit Type 正交
（Owner D1 / 10 §5.2）。本模块**从不**把 Question Type 推导为 Unit Type。

两条 legacy→canonical 翻译的授权来源 = Owner OD-2
（`Docs/40_DECISIONS/X2.6-OD-2-MAPPING-AUTHORIZATION.md`，AITutorX 仓）::

    standalone_question → standalone_unit   event X2.6-OD-2-MAP-STANDALONE-01
    composite_question  → composite_unit    event X2.6-OD-2-MAP-COMPOSITE-01

OD-2 Owner Closure（2026-09-21）语义更正：上述是 legacy vocabulary boundary
normalization，**不是** canonical QT→UT ontology mapping。

**No Silent Repair（X2.6 task §13）**——下列情形一律显式失败，不给默认值、
不 fallback、不静默 skip、不猜测::

    missing → error      unknown → error      legacy noise → error
    invalid → error      ambiguous → error

本模块**不做**的事：

- 不 import / 不激活 `compile.mapping_registry`（OD-2：production enforcement
  NOT IMPLEMENTED；X2.6 task §17 禁止把它接到 production runtime）
- 不改 production 域（`compile/ir.py` / `gate/` / `admission/`）——canonical 闭集
  强制由 F-M3-04 / M.3 负责，且已 CLOSED，不在本模块重复实现
- 不做 QT→UT 映射
- 不改写 / 不迁移 corpus 或 manifest 取值（边界只读）

Canonical Unit Type 闭集**复用** `app.domains.compile.UNIT_TYPES` 作为唯一真源，
避免出现第二套独立的 Unit Type 校验体系（X2.6 task §4）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domains.compile import UNIT_TYPES

# ── OD-2 授权的 legacy → canonical 归一化（唯一允许的两条翻译）──────────────

PRODUCER_UNIT_TYPE_TO_CANONICAL: dict[str, str] = {
    "standalone_question": "standalone_unit",
    "composite_question": "composite_unit",
}

# 每条翻译绑定唯一 Owner authorization event ID（OD-2 §2）；provenance 必须可追溯。
NORMALIZATION_EVENT_IDS: dict[str, str] = {
    "standalone_question": "X2.6-OD-2-MAP-STANDALONE-01",
    "composite_question": "X2.6-OD-2-MAP-COMPOSITE-01",
}

# 已是 canonical 的取值：幂等直通（不改写、不重释义）。
# 同一闭集真源（compile.UNIT_TYPES），不是第二套定义。
CANONICAL_UNIT_TYPES = UNIT_TYPES

# 稳定错误码（新增须登记；不得改语义复用旧码）。
CODE_MISSING_UNIT_TYPE = "MISSING_UNIT_TYPE"
CODE_UNKNOWN_UNIT_TYPE = "UNKNOWN_UNIT_TYPE"
CODE_MISSING_IDENTITY = "MISSING_IDENTITY"
CODE_MALFORMED_IDENTITY = "MALFORMED_IDENTITY"
CODE_MALFORMED_IDENTITY_VERSION = "MALFORMED_IDENTITY_VERSION"
CODE_MISSING_IDENTITY_VERSION = "MISSING_IDENTITY_VERSION"
CODE_OUT_OF_SCOPE_IDENTITY_VERSION = "OUT_OF_SCOPE_IDENTITY_VERSION"
CODE_BROKEN_LINE_REFERENCE = "BROKEN_LINE_REFERENCE"
CODE_BROKEN_MATERIAL_REFERENCE = "BROKEN_MATERIAL_REFERENCE"
CODE_BROKEN_FIGURE_REFERENCE = "BROKEN_FIGURE_REFERENCE"


@dataclass(frozen=True)
class NormalizedUnitType:
    """一次 Unit Type 归一化的完整 provenance（UQ-01 Decision 7：保留 legacy 值）。

    `producer_unit_type` 是 Producer 侧原始取值，**仅**作为 legacy evidence 保存；
    canonical runtime 结构只允许出现 `canonical_unit_type`。
    """

    canonical_unit_type: str
    producer_unit_type: str | None
    normalization_event_id: str | None
    already_canonical: bool


def normalize_unit_type(producer_unit_type: object) -> NormalizedUnitType:
    """Producer unit_type → canonical Unit Type（确定性，fail-loud）。

    允许的输入恰好三类，其余全部显式失败：

    1. OD-2 授权的 legacy 值（`standalone_question` / `composite_question`）
       → 翻译为对应 canonical 值，并绑定 Owner authorization event ID；
    2. 已是 canonical 的值（`standalone_unit` / `composite_unit`）
       → 幂等直通，`already_canonical=True`，无 event ID（无翻译发生）；
    3. 其它任何值（缺失 / None / 非字符串 / 未知字符串 / legacy 噪声
       如 `andalone_question`）→ `BoundaryViolation`。

    禁止（OD-2 / UQ-01 Decision 7 / X2.6 task §13）：静默默认、静默 fallback、
    把噪声值「修好」、按结构猜类型、QT→UT 推导。
    """
    if producer_unit_type is None:
        raise BoundaryViolation(
            CODE_MISSING_UNIT_TYPE,
            "Producer unit_type is missing; boundary normalization requires an "
            "explicit Producer value (no default is permitted).",
        )
    if not isinstance(producer_unit_type, str):
        raise BoundaryViolation(
            CODE_UNKNOWN_UNIT_TYPE,
            f"Producer unit_type must be a string, got {type(producer_unit_type).__name__} "
            f"value {producer_unit_type!r}; no coercion is permitted.",
        )

    # 1) OD-2 授权的 legacy → canonical 翻译
    if producer_unit_type in PRODUCER_UNIT_TYPE_TO_CANONICAL:
        return NormalizedUnitType(
            canonical_unit_type=PRODUCER_UNIT_TYPE_TO_CANONICAL[producer_unit_type],
            producer_unit_type=producer_unit_type,
            normalization_event_id=NORMALIZATION_EVENT_IDS[producer_unit_type],
            already_canonical=False,
        )

    # 2) 已 canonical：幂等直通（闭集真源 = compile.UNIT_TYPES）
    if producer_unit_type in CANONICAL_UNIT_TYPES:
        return NormalizedUnitType(
            canonical_unit_type=producer_unit_type,
            producer_unit_type=producer_unit_type,
            normalization_event_id=None,
            already_canonical=True,
        )

    # 3) 其余一律显式失败——含 legacy 噪声（如 `andalone_question`，OD-1：永不 canonical）
    raise BoundaryViolation(
        CODE_UNKNOWN_UNIT_TYPE,
        f"Producer unit_type {producer_unit_type!r} has no Owner-authorized boundary "
        f"normalization; authorized legacy values = "
        f"{sorted(PRODUCER_UNIT_TYPE_TO_CANONICAL)}, canonical values = "
        f"{sorted(CANONICAL_UNIT_TYPES)}. "
        f"No silent repair is permitted (OD-1: such values are never canonical).",
    )


# ─── Identity rules: FORWARDED to production module (B1-R2-BOUNDARY-AND-DB-ISOLATION-03) ───
# Sole authority lives in app.domains.source.identity_scope. This layer is a
# compatibility forwarder only — do NOT re-implement or drift the rule sets here.
from app.domains.source.identity_scope import (  # noqa: E402
    CODE_MALFORMED_IDENTITY,
    CODE_MALFORMED_IDENTITY_VERSION,
    CODE_MISSING_IDENTITY,
    CODE_MISSING_IDENTITY_VERSION,
    CODE_OUT_OF_SCOPE_IDENTITY_VERSION,
    BoundaryViolation,
    InterfaceScopeDecision,
    NormalizedIdentity,
    enforce_interface_scope,
    normalize_interface_identity,
)

# Re-export names that previously lived here (public surface unchanged).
_SHA256_LOWER_HEX = __import__("app.domains.source.identity_scope", fromlist=["_SHA256_LOWER_HEX"])._SHA256_LOWER_HEX
_INTERFACE_IDENTITY_VERSIONS = __import__("app.domains.source.identity_scope", fromlist=["_INTERFACE_IDENTITY_VERSIONS"])._INTERFACE_IDENTITY_VERSIONS
_IDENTITY_VERSION_ACCEPTED_TYPES = __import__("app.domains.source.identity_scope", fromlist=["_IDENTITY_VERSION_ACCEPTED_TYPES"])._IDENTITY_VERSION_ACCEPTED_TYPES


@dataclass(frozen=True)
class ReferenceCheck:
    """一次引用完整性检查的结果（material / figure / 行区间）。"""

    code: str
    reference: str
    detail: str


# 行内图片/图形引用（markdown image + HTML img）——确定性正则，无语义推断。
_FIGURE_REF = re.compile(
    r"!\[[^\]]*\]\(([^)\s]+)[^)]*\)"      # markdown: ![alt](path)
    r"|<img[^>]+src=[\"']([^\"']+)[\"']",  # html:    <img src="path">
    re.IGNORECASE,
)


def scan_figure_references(source_text: str) -> tuple[str, ...]:
    """确定性抽取正文中的行内 figure/image 相对路径引用（去重、保持首见顺序）。

    只做引用**发现**，不做解析、不做恢复、不做 OCR（BUG-V3-020 延后；OQ-3 开放）。
    """
    seen: dict[str, None] = {}
    for m in _FIGURE_REF.finditer(source_text):
        ref = m.group(1) or m.group(2)
        if ref:
            seen.setdefault(ref, None)
    return tuple(seen)


def validate_figure_references(
    figure_refs: tuple[str, ...],
    source_path,
) -> tuple[ReferenceCheck, ...]:
    """逐个校验 figure 引用是否可解析到存在的文件（path 仅 locator）。

    返回**断链**清单；空 tuple = 全部可解析。不静默丢弃、不猜测替代路径。
    外部 URL（http/https/data:）不在本地 locator 校验范围，跳过且不计入断链。
    """
    broken: list[ReferenceCheck] = []
    base = source_path.parent
    for ref in figure_refs:
        if re.match(r"^(https?:|data:)", ref, re.IGNORECASE):
            continue  # 非本地 locator，不参与本地存在性校验
        candidate = (base / ref).resolve() if not ref.startswith(("/", "\\")) else None
        if candidate is None or not candidate.exists():
            broken.append(
                ReferenceCheck(
                    code=CODE_BROKEN_FIGURE_REFERENCE,
                    reference=ref,
                    detail=f"figure reference does not resolve under {base}",
                )
            )
    return tuple(broken)


def validate_material_references(
    material_spans: dict[str, tuple[int, int] | None],
    line_count: int,
) -> tuple[ReferenceCheck, ...]:
    """校验 material 行区间引用是否落在源文件行范围内（1-based 闭区间）。

    越界 / 反转区间 = broken material reference，显式报告，不静默裁剪。
    """
    broken: list[ReferenceCheck] = []
    for role, span in material_spans.items():
        if span is None:
            continue  # 未声明 ≠ 断链；缺席由 IR 不变量判 incomplete
        start, end = span
        if start < 1 or end > line_count or start > end:
            broken.append(
                ReferenceCheck(
                    code=CODE_BROKEN_MATERIAL_REFERENCE,
                    reference=f"{role}:{span}",
                    detail=f"material line range out of bounds 1..{line_count}",
                )
            )
    return tuple(broken)


__all__ = [
    "BoundaryViolation",
    "CANONICAL_UNIT_TYPES",
    "CODE_BROKEN_FIGURE_REFERENCE",
    "CODE_BROKEN_LINE_REFERENCE",
    "CODE_BROKEN_MATERIAL_REFERENCE",
    "CODE_MALFORMED_IDENTITY",
    "CODE_MALFORMED_IDENTITY_VERSION",
    "CODE_MISSING_IDENTITY",
    "CODE_MISSING_IDENTITY_VERSION",
    "CODE_MISSING_UNIT_TYPE",
    "CODE_OUT_OF_SCOPE_IDENTITY_VERSION",
    "CODE_UNKNOWN_UNIT_TYPE",
    "NORMALIZATION_EVENT_IDS",
    "InterfaceScopeDecision",
    "NormalizedIdentity",
    "NormalizedUnitType",
    "PRODUCER_UNIT_TYPE_TO_CANONICAL",
    "ReferenceCheck",
    "enforce_interface_scope",
    "normalize_interface_identity",
    "normalize_unit_type",
    "scan_figure_references",
    "validate_figure_references",
    "validate_material_references",
]
