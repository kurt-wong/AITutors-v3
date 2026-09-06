"""Compiler 输出结构（段 F，20 §7.2 → 10 §5.3 payload 形态；transient）。

只承载确定性编译结果；不承载 gate_decision / decision_status（属段 G）。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CompiledRole:
    """一个 content role 的编译产物。text = resolved span slice 的权威正文（不归一化）。"""

    role: str
    span_id: str
    line_refs: tuple[str, ...]
    text: str
    text_hash: str  # 2c = source raw slice hash；text 与 slice 一致时 2d 同值
    label: str | None = None  # option/blank 的标签（dedup canonical input 用）


@dataclass(frozen=True)
class CompiledAnswer:
    """answer role：正文 + answer_status 三字段独立（verified_correct 由 G 处理，F 置 None）。"""

    span_id: str
    line_refs: tuple[str, ...]
    text: str
    text_hash: str
    source_located: bool
    complete: bool
    verified_correct: bool | None = None


@dataclass(frozen=True)
class CompiledLeaf:
    """一个待物化 Question 的编译叶子（standalone=自身；composite=每个 sub_question）。"""

    unit_id: str
    question_number: str
    canonical_question_type: str
    stem: CompiledRole | None
    options: tuple[CompiledRole, ...] = field(default_factory=tuple)
    answer: CompiledAnswer | None = None
    explanation: CompiledRole | None = None
    dedup_key: str | None = None
    occurrence_key: str | None = None


@dataclass(frozen=True)
class CompiledMaterial:
    """一个共享材料的编译产物（只输出一次，不复制进子题 stem）。"""

    unit_id: str
    role: str
    span_id: str
    text: str
    text_hash: str
    dedup_key: str | None = None


@dataclass(frozen=True)
class CompiledSnapshot:
    """Compiler 对一份 IR 的全部编译产物（10 §5.3 payload 形态的 transient 快照）。"""

    source_version_id: uuid.UUID
    annotation_id: uuid.UUID
    leaves: tuple[CompiledLeaf, ...] = field(default_factory=tuple)
    materials: tuple[CompiledMaterial, ...] = field(default_factory=tuple)
