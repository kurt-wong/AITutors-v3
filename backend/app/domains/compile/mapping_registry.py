"""X2.6 Mapping Registry — Legacy → Canonical Unit-Type mapping table structure.

OD-MAP-01 + OD-CL21-01 implementation scaffold (M.1-A).
OD-2 registration (2026-09-20): Owner authorized two canonical mappings.
OD-1 registration (2026-09-20): Owner decided DI-01 = migrate-as-UNKNOWN.

IMPORTANT: Owner authorization != production enforcement.
This module is a GOVERNANCE SCAFFOLD. No production code imports it.
Production mapping enforcement = NOT IMPLEMENTED (P1-P13 all OPEN).

Authority chain (Owner OD-CL21-01, F-03 corrected):
    IR Semantic Resolution + Owner-authorized mapping table = normalization authority

Rules (Owner OD-MAP-01 + OD-2):
- mapping_basis MUST reference a real Owner decision event id
- AUTHORIZED rows carry Owner decision event ids (OD-2)
- Production enforcement requires M.2-M.6 implementation (NOT done)
- andalone_question = PROHIBITED (D8 + OD-1: migrate-as-UNKNOWN)
- missing/null/invalid/conflicting -> unknown (never default standalone)
- legacy value is evidence, not canonical authority (D7)

F-05-A acceptance: mapping event identity must be independently cross-validated
against AITutor-X governance documents. Semantic binding = IMPLEMENTATION GAP.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MappingStatus(Enum):
    """Mapping row lifecycle status.

    After OD-2 registration (2026-09-20):
      AUTHORIZED = Owner has provided per-value authorization event id
      Production enforcement is a SEPARATE concern (NOT IMPLEMENTED)
    """

    PENDING_OWNER = "pending_owner"  # Owner has not provided event id
    AUTHORIZED = "authorized"  # Owner decision event id present (OD-2)
    PROHIBITED = "prohibited"  # D8 + OD-1: -> unknown + isolate; never canonical


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


# Mapping table after OD-1 + OD-2 Owner Decision Registration (2026-09-20).
# Owner authorization = APPROVED for standalone_question and composite_question.
# Production mapping enforcement = NOT IMPLEMENTED (no production code imports this module).
LEGACY_TO_CANONICAL_MAP: dict[str, MappingEntry] = {
    "standalone_question": MappingEntry(
        source_value="standalone_question",
        canonical_target="standalone_unit",
        status=MappingStatus.AUTHORIZED,  # OD-2: Owner authorized
        mapping_basis="X2.6-OD-2-MAP-STANDALONE-01",  # OD-2 per-value event id
        condition=(
            "OD-2: Owner authorized standalone_question -> standalone_unit; "
            "production enforcement NOT implemented; "
            "evidence chain must be present at application time"
        ),
    ),
    "composite_question": MappingEntry(
        source_value="composite_question",
        canonical_target="composite_unit",
        status=MappingStatus.AUTHORIZED,  # OD-2: Owner authorized
        mapping_basis="X2.6-OD-2-MAP-COMPOSITE-01",  # OD-2 per-value event id
        condition=(
            "OD-2: Owner authorized composite_question -> composite_unit; "
            "production enforcement NOT implemented; "
            "D2 Condition A or B evidence required at application time"
        ),
    ),
    "andalone_question": MappingEntry(
        source_value="andalone_question",
        canonical_target=None,  # PROHIBITED: must never map to canonical
        status=MappingStatus.PROHIBITED,  # D8 + OD-DI01-01 permanent role
        mapping_basis="X2.6-OD-1-DI01-MIGRATE-AS-UNKNOWN",  # OD-1: final disposition
        condition=(
            "OD-DI01-01: NON-CANONICAL LEGACY OBSERVATION (Preserve+Isolate+Observe); "
            "OD-1: Owner disposition = migrate-as-UNKNOWN; "
            "UNKNOWN migration NOT implemented"
        ),
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

    After OD-1 + OD-2 registration (2026-09-20):
    - Framework-level governance events (D1-D10, OD-* approvals)
    - Per-value mapping authorization events (OD-2)
    - DI-01 disposition event (OD-1)

    NOTE: Framework-level IDs are NOT per-value mapping authorization IDs.
    OD-2 provides per-value event IDs for the two authorized mappings.
    F-05-A semantic binding enforcement = IMPLEMENTATION GAP.
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
        # OD-1: DI-01 final disposition (2026-09-20)
        "X2.6-OD-1-DI01-MIGRATE-AS-UNKNOWN",
        # OD-2: Per-value mapping authorization (2026-09-20)
        "X2.6-OD-2-MAP-STANDALONE-01",
        "X2.6-OD-2-MAP-COMPOSITE-01",
    }
