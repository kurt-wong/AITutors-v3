"""M2 funnel recorder: per-stage counts + per-unit failure reasons (M1-D prep).

Usage (in M2 real-run scripts):
    funnel = FunnelRecorder("chem-2018-spring-huikao-teacher")
    funnel.set("input_units", 40)
    funnel.fail_unit("Q3", "annotation", "LLM parse error: ...")
    funnel.write(Path("e2e_run/funnel_chem.json"))

Never invents success. Missing stages stay 0. Failures keep stage + reason.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

STAGES = (
    "input_units",
    "identity_ok",
    "ir_ready",
    "candidates",
    "questions",
    "question_instances",
    "pending_review",
)


@dataclass
class FunnelRecorder:
    package_id: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    counts: dict[str, int] = field(default_factory=lambda: {s: 0 for s in STAGES})
    failures: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def set(self, stage: str, n: int) -> None:
        if stage not in self.counts:
            raise ValueError(f"unknown stage {stage!r}; allowed={list(self.counts)}")
        self.counts[stage] = int(n)

    def bump(self, stage: str, n: int = 1) -> None:
        self.set(stage, self.counts[stage] + n)

    def fail_unit(self, unit_id: str, stage: str, reason: str) -> None:
        self.failures.append(
            {"unit_id": unit_id, "stage": stage, "reason": reason}
        )

    def note(self, text: str) -> None:
        self.notes.append(text)

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "started_at": self.started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "stages": self.counts,
            "failures": self.failures,
            "notes": self.notes,
            "unexplained_loss": self.counts["input_units"]
            - self.counts["ir_ready"]
            - self.counts["pending_review"]
            - len(self.failures),
        }

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path
