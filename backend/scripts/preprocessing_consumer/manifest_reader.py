"""Preprocessing manifest reader — 只读，零 V3 依赖。

纯读取层：**不做**词表转换、不做校验、不改写 Producer 取值。
判定（归一化 / 边界校验）在 `boundary.py`，与读取严格分离。

Provenance preservation（X2.6 task §12）：此前本层在读取时丢弃
`source_content_sha256` / `identity_version` / `sections` 及单元级
`section_ref` / `printed_provenance` / `basis` / `basis_evidence`，
导致身份与血缘在集成边界处不可见。现已全部保留（verbatim）。
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ManifestSection:
    """Producer 声明的文档分节（ordinal 序 = 阅读顺序）。"""

    id: str | None
    title: str | None
    ordinal: int | None
    start_line: int | None
    end_line: int | None
    occurrence: int | None


@dataclass(frozen=True)
class ManifestOption:
    """Producer 声明的单个选项 span（label + 行号区间）。"""
    label: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class ManifestUnit:
    unit_id: str
    unit_type: str                          # Producer 词表: standalone_question | composite_question
    question_numbers: tuple[int, ...]
    original_question_type: str
    section: str | None = None
    printed_number: str | None = None
    stem_lines: tuple[int, int] | None = None
    options_lines: tuple[int, int] | None = None
    options: tuple[ManifestOption, ...] = field(default_factory=tuple)
    extra_lines: tuple[int, int] | None = None
    answer_lines: tuple[int, int] | None = None
    explanation_lines: tuple[int, int] | None = None
    material_lines: tuple[int, int] | None = None
    questions_lines: tuple[int, int] | None = None
    answer_evidence_type: str | None = None
    answer_evidence_lines: tuple[int, int] | None = None
    answer_evidence_value: str | None = None
    # ── provenance（verbatim 保留；不在本层解释）──
    section_ref: str | None = None
    printed_provenance: str | None = None
    basis: str | None = None
    basis_evidence: str | None = None


@dataclass(frozen=True)
class Manifest:
    source_file: str                        # absolute path to source .md（locator only，非 identity）
    model: str
    prompt_version: str
    validation_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    units: tuple[ManifestUnit, ...]
    # ── identity / provenance（verbatim 保留；判定在 boundary.py）──
    source_content_sha256: str | None = None
    identity_version: int | str | None = None
    sections: tuple[ManifestSection, ...] = field(default_factory=tuple)


def _pair(v) -> tuple[int, int] | None:
    if v is None:
        return None
    return (int(v[0]), int(v[1]))


def load_manifest(path: Path) -> Manifest:
    raw = json.loads(path.read_text(encoding="utf-8"))
    meta = raw.get("annotation_meta", {})
    units = []
    for u in raw.get("units", []):
        ae = u.get("answer_evidence") or {}
        units.append(ManifestUnit(
            unit_id=u["unit_id"],
            unit_type=u["unit_type"],
            question_numbers=tuple(u.get("question_numbers", [])),
            original_question_type=u.get("original_question_type", ""),
            section=u.get("section"),
            printed_number=u.get("printed_number"),
            stem_lines=_pair(u.get("stem_lines")),
            options_lines=_pair(u.get("options_lines")),
            options=tuple(
                ManifestOption(label=o["label"], start_line=int(o["start_line"]),
                               end_line=int(o["end_line"]))
                for o in (u.get("options") or [])
                if isinstance(o, dict) and "label" in o and "start_line" in o
            ),
            extra_lines=_pair(u.get("extra_lines")),
            answer_lines=_pair(u.get("answer_lines")),
            explanation_lines=_pair(u.get("explanation_lines")),
            material_lines=_pair(u.get("material_lines")),
            questions_lines=_pair(u.get("questions_lines")),
            answer_evidence_type=ae.get("type"),
            answer_evidence_lines=_pair(ae.get("lines")),
            answer_evidence_value=ae.get("value"),
            section_ref=u.get("section_ref"),
            printed_provenance=u.get("printed_provenance"),
            basis=u.get("basis"),
            basis_evidence=u.get("basis_evidence"),
        ))
    sections = tuple(
        ManifestSection(
            id=s.get("id"),
            title=s.get("title"),
            ordinal=s.get("ordinal"),
            start_line=s.get("start_line"),
            end_line=s.get("end_line"),
            occurrence=s.get("occurrence"),
        )
        for s in raw.get("sections", [])
        if isinstance(s, dict)
    )
    return Manifest(
        source_file=raw["source_file"],
        model=raw.get("model", ""),
        prompt_version=meta.get("prompt_version", ""),
        validation_issues=tuple(meta.get("validation_issues", [])),
        warnings=tuple(meta.get("warnings", [])),
        units=tuple(units),
        source_content_sha256=raw.get("source_content_sha256"),
        identity_version=raw.get("identity_version"),
        sections=sections,
    )


def find_manifests(root: Path) -> list[Path]:
    """递归找 root 下全部 *.manifest.json。"""
    return sorted(root.rglob("*.manifest.json"))
