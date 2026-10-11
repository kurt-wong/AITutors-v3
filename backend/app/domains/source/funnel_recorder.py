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
    run_id: str | None = None
    input_hashes: dict = field(default_factory=dict)
    database: str | None = None

    def set(self, stage: str, n: int) -> None:
        if stage not in self.counts:
            raise ValueError(f"unknown stage {stage!r}; allowed={list(self.counts)}")
        self.counts[stage] = int(n)

    def bump(self, stage: str, n: int = 1) -> None:
        self.set(stage, self.counts[stage] + n)

    def set_run_identity(
        self,
        run_id: str,
        input_hashes: dict | None = None,
        *,
        database: str | None = None,
    ) -> None:
        """Bind this funnel to one run: run_id + input hashes + target database."""
        self.run_id = run_id
        self.database = database
        if input_hashes:
            self.input_hashes = dict(input_hashes)

    def fail_unit(self, unit_id: str, stage: str, reason: str) -> None:
        self.failures.append(
            {"unit_id": unit_id, "stage": stage, "reason": reason}
        )

    def skip_unit(
        self,
        unit_id: str,
        stage: str,
        reason: str,
        *,
        evidence: dict | None = None,
    ) -> None:
        """Record a skip with optional structured evidence (line ranges, IR problems).

        Never invents success. Evidence is optional metadata; reason stays human-readable.
        """
        self.failures.append(
            {
                "unit_id": unit_id,
                "stage": stage,
                "reason": reason,
                "evidence": evidence or {},
            }
        )

    def note(self, text: str) -> None:
        self.notes.append(text)

    def to_dict(self) -> dict:
        # pending_review ⊆ ir_ready（候选子集），不得从 input 再扣一次；
        # unexplained_loss = 无失败记录且未就绪的单元。
        explained = self.counts["ir_ready"] + len(self.failures)
        raw_loss = self.counts["input_units"] - explained
        return {
            "package_id": self.package_id,
            "run_id": self.run_id,
            "database": self.database,
            "input_hashes": self.input_hashes,
            "started_at": self.started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "stages": self.counts,
            "failures": self.failures,
            "notes": self.notes,
            # 保留原始值；负值=阶段计数异常，不静默夹成 0
            "unexplained_loss_raw": raw_loss,
            "unexplained_loss": max(0, raw_loss),
            "unexplained_loss_anomaly": raw_loss < 0,
        }

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path


def ir_skip_reasons(node) -> tuple[str, list[str]]:
    """Derive (summary, problem_list) for an IR node that is not semantic_status=ready.

    Single source of truth: compile/ir.collect_validation_problems
    (same list _validate_node uses — no drift).
    """
    from app.domains.compile.ir import collect_validation_problems

    problems = collect_validation_problems(node, set())
    summary = "; ".join(problems) if problems else f"semantic_status={node.semantic_status}"
    return summary, problems
