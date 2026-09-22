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

# 跨系统身份键格式（Frozen Contract §1.2）：SHA-256(original source bytes)，
# 64 字符小写 hex。path 仅 locator，永不作 identity（DEC-031 原则 1）。
_SHA256_LOWER_HEX = re.compile(r"^[0-9a-f]{64}$")

# Interface Scope 的 identity_version 字段口径（Frozen Contract §1.6）：
# `identity_version == "2"`。corpus 中存在 int 2 与 str "2" 两种编码形态，
# 二者表达同一事实，均接受；其余取值一律显式拒绝（含 v1 legacy）。
_INTERFACE_IDENTITY_VERSIONS = {2, "2"}

# 允许进入 Interface Scope 成员判定的 `identity_version` 输入形态（JSON 标量）。
# 必须**显式列举类型**：`x in {...}` 的成员判定要调 `hash(x)`，遇到 unhashable
# 类型（list / dict / set / bytearray）抛的是 `TypeError` 而**不是**返回 False。
# 该异常不是 `BoundaryViolation`，会穿透 `enforce_interface_scope` 的决策层并中止
# 整个 corpus runner（F-RBC-01）。类型闸门把这类输入转成确定性的 `BoundaryViolation`，
# 而不是用 `except TypeError` 掩盖真正的程序错误（F-RBC-01 §4.2）。
#
# 白名单与修改前**逐值等价**（本任务不得借机改 Interface Scope 语义，§3）：
#   bool  → 放行到成员判定。`True == 1 != 2` 故仍被 OUT_OF_SCOPE_IDENTITY_VERSION
#           拒绝，不会因 bool/int 继承关系被误接受。
#   float → 放行到成员判定，以**原样保留既有行为**：`2.0 == 2` 使 `2.0` 在修改前
#           就被接受（F-RBC-05：`2.0` 的语义是独立 Contract / Owner Decision，
#           本任务不得自行收紧为 BLOCK）。
#   int / str → 语义承载类型（int `2` / str `"2"`）。
# 其余类型（list / dict / set / tuple / complex / 自定义对象）→ MALFORMED_IDENTITY_VERSION。
_IDENTITY_VERSION_ACCEPTED_TYPES: tuple[type, ...] = (bool, int, float, str)


# ── 显式错误（确定性错误报告，X2.6 task §12/§13）─────────────────────────────


class BoundaryViolation(Exception):
    """集成边界违规：Producer 输入无法确定性地归一化为 canonical 词表/身份。

    携带稳定 `code`，供测试与 DSH 独立验证按码断言，不靠错误文案匹配。
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


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


@dataclass(frozen=True)
class NormalizedIdentity:
    """Interface Scope 身份事实的归一化结果（只读，不改写 Producer 声明值）。"""

    source_content_sha256: str
    identity_version: str
    already_canonical: bool


def normalize_interface_identity(
    source_content_sha256: object,
    identity_version: object,
) -> NormalizedIdentity:
    """校验并归一化跨系统身份事实（Frozen Contract §1.2 / §1.6 / §1.7）。

    - `source_content_sha256` 必须为 64 字符小写 hex（= SHA-256(raw source bytes)）。
      **path 不得替代 identity**（DEC-031 原则 1：path 只能找文件，不能证明身份）。
    - `identity_version` 必须落在 Interface Scope 字段口径（== 2）。
      v1 legacy（79 份）不属 v0.2 接口（§1.7 C-IN-1 consumer 侧闸门）。

    输入形态闸门（F-RBC-01）：`identity_version` 先按**显式类型白名单**判定形态，
    再做成员判定。这样 list / dict / set 等 JSON 合法但不可 hash 的取值会得到确定性
    的 `BoundaryViolation`，而**不是** `TypeError`（`x in {...}` 对 unhashable 抛异常，
    不返回 False），更不会穿透决策层中止 corpus runner。

    缺失 / 形态非法 / 格式非法 / 越界 → `BoundaryViolation`。不猜、不补、不默认、
    不隐式转换（`[]` 绝不变成 `"[]"` 或 `2`）。
    """
    if source_content_sha256 is None:
        raise BoundaryViolation(
            CODE_MISSING_IDENTITY,
            "Manifest does not declare source_content_sha256; cross-system identity "
            "cannot be established (path must never be used as identity).",
        )
    if not isinstance(source_content_sha256, str) or not _SHA256_LOWER_HEX.match(
        source_content_sha256
    ):
        raise BoundaryViolation(
            CODE_MALFORMED_IDENTITY,
            f"source_content_sha256 must be 64 lowercase hex chars "
            f"(SHA-256 of raw source bytes), got {source_content_sha256!r}.",
        )

    if identity_version is None:
        raise BoundaryViolation(
            CODE_MISSING_IDENTITY_VERSION,
            "Manifest does not declare identity_version; Interface Scope membership "
            "cannot be established (Frozen Contract §1.6).",
        )
    # 形态闸门先于成员判定（F-RBC-01）：`in` 对 unhashable 输入抛 TypeError，
    # 故必须先确定性地拒绝非法形态，避免异常穿透 boundary decision layer。
    if not isinstance(identity_version, _IDENTITY_VERSION_ACCEPTED_TYPES):
        raise BoundaryViolation(
            CODE_MALFORMED_IDENTITY_VERSION,
            f"identity_version must be a JSON scalar (bool/int/float/str), got "
            f"{type(identity_version).__name__} value {identity_version!r}; no "
            f"coercion is permitted (list/dict/set are rejected as malformed — "
            f"never stringified, never defaulted to 2).",
        )
    if identity_version not in _INTERFACE_IDENTITY_VERSIONS:
        raise BoundaryViolation(
            CODE_OUT_OF_SCOPE_IDENTITY_VERSION,
            f"identity_version {identity_version!r} is outside the Interface Scope "
            f"field criterion (identity_version == 2). v1 legacy assets are not part "
            f"of the interface (Frozen Contract §1.7) and are not silently consumed.",
        )

    return NormalizedIdentity(
        source_content_sha256=source_content_sha256,
        identity_version="2",
        already_canonical=isinstance(identity_version, str) and identity_version == "2",
    )


@dataclass(frozen=True)
class InterfaceScopeDecision:
    """Interface Scope 判定的统一决策形状（所有 runtime runner 一致执行/记录）。

    `code` 为稳定边界错误码（拒绝时）或 None（接受时）；`identity` 为归一化后的
    身份事实（接受时），拒绝时为 None。**不改写** Producer 声明值。
    """

    accepted: bool
    code: str | None
    reason: str
    identity: NormalizedIdentity | None


def enforce_interface_scope(
    source_content_sha256: object,
    identity_version: object,
) -> InterfaceScopeDecision:
    """Interface Boundary 的**唯一 runtime 接入点**（F-INT-01 / F-INT-08）。

    所有 preprocessing → V3 的 runtime runner 入口，必须在把输入交给任何 V3
    semantic consumption（annotation payload / ResolvedRun / IRBuilder / Compiler /
    Gate / Admission）**之前**调用本函数。这解决了 F-INT-01：

        helper 已实现  ≠  helper 已接入实际 runtime path

    判定逻辑 **100% 委托** `normalize_interface_identity`（唯一权威）。本函数
    **不复制**判定规则、**不建立**第二套平行 identity validation 系统、**不抛**异常，
    只把 fail-loud 权威判定收敛为统一决策形状，使多个 runner 以同一方式执行与留痕。

    不变量（F-INT-08 + F-RBC-01）::

        identity_version == 2              → accepted
        identity_version == 1 / 3 / 其它   → rejected  OUT_OF_SCOPE_IDENTITY_VERSION
        identity_version 缺失 / null        → rejected  MISSING_IDENTITY_VERSION
        identity_version 形态非法           → rejected  MALFORMED_IDENTITY_VERSION
            （list / dict / set / tuple / complex / 自定义对象）
        identity 缺失                       → rejected  MISSING_IDENTITY
        identity 格式非法                   → rejected  MALFORMED_IDENTITY

    明确禁止（X2.6 task §13 No Silent Repair）::

        version != 2  →  默认当成 v2          禁止
        version != 2  →  fallback → 继续运行   禁止
        [] / {}       →  str() / 默认值        禁止
        任意输入      →  TypeError 上抛中止 runner  禁止

    这是 **Interface Boundary Enforcement**，不是 V3 内部补救：判定发生在集成边界，
    不在 `compile/ir.py` / `gate/`（F-M3-04 / M.3 已 CLOSED，不重复实现、不触碰）。

    本函数**只**捕获 `BoundaryViolation`：非法输入形态必须由权威做确定性类型校验
    并转成 `BoundaryViolation`（F-RBC-01 §4.2），**不**用宽泛 `except TypeError`
    掩盖真正的程序错误。
    """
    try:
        identity = normalize_interface_identity(source_content_sha256, identity_version)
    except BoundaryViolation as exc:
        return InterfaceScopeDecision(
            accepted=False,
            code=exc.code,
            reason=f"interface_scope_rejected: {exc.code}: {exc.message}",
            identity=None,
        )
    return InterfaceScopeDecision(
        accepted=True,
        code=None,
        reason="interface_scope_accepted: identity_version==2",
        identity=identity,
    )


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
