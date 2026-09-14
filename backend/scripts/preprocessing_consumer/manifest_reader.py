"""Preprocessing manifest reader — 只读，零 V3 依赖。"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManifestUnit:
    unit_id: str
    unit_type: str                          # standalone_question | composite_question
    question_numbers: tuple[int, ...]
    original_question_type: str
    section: str | None = None
    printed_number: str | None = None
    stem_lines: tuple[int, int] | None = None
    options_lines: tuple[int, int] | None = None
    extra_lines: tuple[int, int] | None = None
    answer_lines: tuple[int, int] | None = None
    explanation_lines: tuple[int, int] | None = None
    material_lines: tuple[int, int] | None = None
    questions_lines: tuple[int, int] | None = None
    answer_evidence_type: str | None = None
    answer_evidence_lines: tuple[int, int] | None = None
    answer_evidence_value: str | None = None


@dataclass(frozen=True)
class Manifest:
    source_file: str                        # absolute path to source .md
    model: str
    prompt_version: str
    validation_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    units: tuple[ManifestUnit, ...]


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
            extra_lines=_pair(u.get("extra_lines")),
            answer_lines=_pair(u.get("answer_lines")),
            explanation_lines=_pair(u.get("explanation_lines")),
            material_lines=_pair(u.get("material_lines")),
            questions_lines=_pair(u.get("questions_lines")),
            answer_evidence_type=ae.get("type"),
            answer_evidence_lines=_pair(ae.get("lines")),
            answer_evidence_value=ae.get("value"),
        ))
    return Manifest(
        source_file=raw["source_file"],
        model=raw.get("model", ""),
        prompt_version=meta.get("prompt_version", ""),
        validation_issues=tuple(meta.get("validation_issues", [])),
        warnings=tuple(meta.get("warnings", [])),
        units=tuple(units),
    )


def find_manifests(root: Path) -> list[Path]:
    """递归找 root 下全部 *.manifest.json。"""
    return sorted(root.rglob("*.manifest.json"))
