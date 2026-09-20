"""X2.6 Mapping Registry — Legacy → Canonical Unit-Type mapping table structure.

OD-MAP-01 + OD-CL21-01 implementation scaffold (M.1-A).
Structure defined; ALL values = PENDING_OWNER until Owner provides decision event ids.

Authority chain (Owner OD-CL21-01, F-03 corrected):
    IR Semantic Resolution + Owner-authorized mapping table = normalization authority

Rules (Owner OD-MAP-01):
- mapping_basis MUST reference a real Owner decision event id before activation
- PENDING_OWNER rows MUST NOT be applied as effective mapping
- andalone_question = PROHIBITED (D8: NON-CANONICAL LEGACY OBSERVATION)
- missing/null/invalid/conflicting -> unknown (never default standalone)
- legacy value is evidence, not canonical authority (D7)

F-05-A acceptance: mapping event identity must be independently cross-validated
against AITutor-X governance documents. Fake/reused/wrong event ids must be detectable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MappingStatus(Enum):
    """Mapping row lifecycle status."""

    PENDING_OWNER = "pending_owner"  # structure defined; Owner has not provided event id
    AUTHORIZED = "authorized"  # Owner decision event id present and cross-validated
    PROHIBITED = "prohibited"  # D8: must never map to canonical; -> unknown + isolate


@dataclass(frozen=True)
class MappingEntry:
    """A single legacy -> canonical mapping row with full provenance.

    mapping_basis: Owner decision event id (e.g. "OD-MAP-01-2026-09-20")
                   Empty string = not yet authorized (PENDING_OWNER).
    condition:     Additional evidence condition that must be satisfied.
    """

    source_value: str
    canonical_target: str | None  # None = must resolve to unknown
    status: MappingStatus
    mapping_basis: str  # Owner decision event id; "" = pending
    condition: str


# Current mapping table (Resolution Package §3.4; Owner OD-MAP-01 APPROVED framework).
# Values remain PENDING_OWNER until Owner provides decision event ids.
LEGACY_TO_CANONICAL_MAP: dict[str, MappingEntry] = {
    "standalone_question": MappingEntry(
        source_value="standalone_question",
        canonical_target="standalone_unit",  # direction only; not activated
        status=MappingStatus.PENDING_OWNER,
        mapping_basis="",  # Owner event id required
        condition="Owner authorizes; evidence chain must be present; provenance recorded",
    ),
    "composite_question": MappingEntry(
        source_value="composite_question",
        canonical_target="composite_unit",  # direction only; not activated
        status=MappingStatus.PENDING_OWNER,
        mapping_basis="",  # Owner event id required
        condition="Owner authorizes; D2 Condition A or B evidence present; provenance recorded",
    ),
    "andalone_question": MappingEntry(
        source_value="andalone_question",
        canonical_target=None,  # PROHIBITED: must never map to canonical
        status=MappingStatus.PROHIBITED,
        mapping_basis="OD-DI01-01",  # D8 permanent role APPROVED
        condition="D8: NON-CANONICAL LEGACY OBSERVATION; -> unknown + isolate",
    ),
}


def lookup_mapping(source_value: str | None) -> MappingEntry | None:
    """Look up a legacy unit_type value in the mapping table.

    Returns:
        MappingEntry if the value is in the table
        None if the value is missing/unknown (caller must resolve to semantic_status=unknown)

    NEVER returns an activated canonical mapping for PENDING_OWNER rows.
    """
    if source_value is None:
        return None
    return LEGACY_TO_CANONICAL_MAP.get(source_value)


def resolve_canonical(source_value: str | None) -> tuple[str | None, str]:
    """Resolve a legacy unit_type to canonical form.

    Returns:
        (canonical_target, provenance_note)

    Rules:
        - PENDING_OWNER -> (None, "pending_owner: awaiting Owner decision event id")
        - PROHIBITED -> (None, "prohibited: D8 NON-CANONICAL LEGACY OBSERVATION")
        - AUTHORIZED with valid mapping_basis -> (canonical_target, mapping_basis)
        - Not in table -> (None, "unmapped: no entry in mapping table")
        - None/missing -> (None, "missing: no unit_type value")

    NEVER defaults to standalone_unit or composite_unit without authorization.
    """
    entry = lookup_mapping(source_value)
    if entry is None:
        if source_value is None:
            return None, "missing: no unit_type value"
        return None, f"unmapped: {source_value!r} not in mapping table"
    if entry.status == MappingStatus.PROHIBITED:
        return None, f"prohibited: {entry.condition}"
    if entry.status == MappingStatus.PENDING_OWNER:
        return None, "pending_owner: awaiting Owner decision event id"
    if not entry.mapping_basis:
        return None, "invalid: AUTHORIZED row missing mapping_basis"
    return entry.canonical_target, f"authorized: {entry.mapping_basis}"


def validate_mapping_event_identity(
    mapping_basis: str,
    authorized_event_ids: set[str],
) -> bool:
    """F-05-A: Cross-validate a mapping event id against known Owner decision records.

    Args:
        mapping_basis: The event id claimed by a mapping row
        authorized_event_ids: Set of event ids that exist in AITutor-X governance docs

    Returns:
        True if mapping_basis is non-empty AND present in authorized_event_ids

    This function enables detection of:
        - missing event id (empty string)
        - fake event id (not in authorized set)
        - reused event id (same id used for different mappings — caller must check)
        - wrong event id (id exists but for a different decision — caller must check)
    """
    if not mapping_basis:
        return False
    return mapping_basis in authorized_event_ids


def get_current_authorized_event_ids() -> set[str]:
    """Return the set of currently known Owner decision event ids.

    As of M.1, the following governance events are registered:
    - D1-D10: FINALIZED (X2.6-UQ-01)
    - OD-MAP-01 through OD-REPO-01: APPROVED (X2.6-OD-FINAL-01)
    - F-01 batching: SAME-BATCH (X2.6-OD-F01-01)
    - Implementation Authorization: AUTHORIZED (X2.6-IMPL-AUTH-01)

    NOTE: None of these constitute per-value mapping event ids.
    OD-MAP-01 approved the FRAMEWORK; specific value activation
    requires Owner to provide dedicated event ids per mapping row.
    """
    return {
        "D1-D10-FINALIZED",
        "OD-MAP-01-APPROVED",
        "OD-UNKNOWN-01-APPROVED",
        "OD-CL21-01-APPROVED",
        "OD-D9-01-APPROVED",
        "OD-DI01-01-APPROVED",
        "OD-PP-01-APPROVED",
        "OD-TEST-01-APPROVED",
        "OD-REPO-01-APPROVED",
        "F-01-SAME-BATCH",
        "IMPL-AUTH-01-AUTHORIZED",
    }
