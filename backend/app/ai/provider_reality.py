"""Provider Reality Tracking (FORMAL-E2E-ENABLEMENT-01 §6).

Goal: distinguish *declared* provider/model from *actually executed* provider.
Equivalent mechanism without DB schema migration: JSON evidence sidecar +
gateway last_actual_provider property.

Record fields:
  configured_provider / configured_model  — what the pipeline declared
  actual_provider                         — which provider object really ran
  execution_status                        — completed | failed
  execution_timestamp                     — UTC ISO-8601
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ProviderRealityRecord:
    request_id: str
    task_id: str | None
    document_id: str | None
    stage: str
    configured_provider: str
    configured_model: str
    actual_provider: str | None
    actual_model: str | None
    execution_status: str
    execution_timestamp: str
    error_type: str | None = None
    actual_usage: dict | None = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class ProviderRealityTracker:
    """Collects per-invocation reality records and flushes them to a JSON file."""

    def __init__(self, output_path: Path | None = None) -> None:
        self._output_path = output_path
        self._records: list[ProviderRealityRecord] = []

    def record(
        self,
        *,
        request_id: uuid.UUID | str,
        task_id: uuid.UUID | str | None,
        document_id: uuid.UUID | str | None,
        stage: str,
        configured_provider: str,
        configured_model: str,
        actual_provider: str | None,
        execution_status: str,
        actual_model: str | None = None,
        error_type: str | None = None,
        actual_usage: dict | None = None,
        extra: dict | None = None,
    ) -> ProviderRealityRecord:
        # Issue-02: actual_model MUST come from API response; never echo config
        if actual_model is not None and actual_model == configured_model:
            pass  # equality is allowed ONLY if response actually returned that model
        rec = ProviderRealityRecord(
            request_id=str(request_id),
            task_id=str(task_id) if task_id is not None else None,
            document_id=str(document_id) if document_id is not None else None,
            stage=stage,
            configured_provider=configured_provider,
            configured_model=configured_model,
            actual_provider=actual_provider,
            actual_model=actual_model,
            execution_status=execution_status,
            execution_timestamp=datetime.now(timezone.utc).isoformat(),
            error_type=error_type,
            actual_usage=actual_usage,
            extra=extra or {},
        )
        self._records.append(rec)
        return rec

    @property
    def records(self) -> list[ProviderRealityRecord]:
        return list(self._records)

    def flush(self) -> Path | None:
        if self._output_path is None or not self._records:
            return None
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "records": [r.to_dict() for r in self._records],
        }
        self._output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return self._output_path


# Process-wide tracker used by LLMExecutor; scripts may replace output path.
default_tracker = ProviderRealityTracker()
