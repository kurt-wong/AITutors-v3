"""
B2-B5 Pre: 125 Unknown Triage - Gate B Coverage Boundary Audit
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from scripts.gate_b.gate_b2b2_answer_table import (
    load_corpus,
    detect_answer_type,
    _extract_question_number,
)


@dataclass
class UnknownTarget:
    case_id: str
    unit_id: str
    subject: str
    region: list[int]
    question_number: int | None
    raw_lines: list[str]
    line_count: int
    non_empty_count: int
    triage_class: str = ""
    triage_detail: str = ""
    requires_search: bool = False
