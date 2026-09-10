"""Candidate API endpoints：详情 + approve/reject（经 AdmissionService 唯一入口）。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas import ApproveRequest, CandidateDetail, RejectRequest
from app.domains.gate.admission import AdmissionService
from app.models.snapshot import AdmissionCandidate
from app.repositories.base import RepositoryError
from app.repositories.snapshot_repository import SnapshotRepository

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("/{candidate_id}", response_model=CandidateDetail)
async def get_candidate(
    candidate_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CandidateDetail:
    """Candidate 详情（含完整 payload）。"""
    c = await db.get(AdmissionCandidate, candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    return CandidateDetail(
        id=c.id,
        unit_type=c.unit_type,
        source_version_id=c.source_version_id,
        annotation_id=c.annotation_id,
        decision_status=c.decision_status,
        gate_decision=c.gate_decision,
        build_versions=c.build_versions,
        input_identity=c.input_identity,
        payload=c.payload,
        review_trail=c.review_trail,
        created_at=c.created_at,
        decided_at=c.decided_at,
        logical_execution_stage=c.logical_execution_stage,
        logical_execution_hash=c.logical_execution_hash,
    )


@router.post("/{candidate_id}/approve", response_model=CandidateDetail)
async def approve_candidate(
    candidate_id: uuid.UUID,
    body: ApproveRequest,
    db: AsyncSession = Depends(get_db),
) -> CandidateDetail:
    """人工 approve：先 append review_trail，再经 AdmissionService.approve() 物化。"""
    service = AdmissionService(db)
    try:
        # 先追加人工 review 证据（20 §8.2 manual path 要求）
        snap = SnapshotRepository(db)
        entry = {
            "decision": "approve",
            "verified_by": "human",
            "reviewer_id": body.reviewer_id,
            "confirmed_fields": body.confirmed_fields,
        }
        await snap.append_review_trail(candidate_id, entry)

        # 经 AdmissionService 唯一入口物化
        result = await service.approve(
            candidate_id=candidate_id,
            provenance={
                "source": "human",
                "reviewer_id": body.reviewer_id,
                "confirmed_fields": body.confirmed_fields,
            },
        )
        await db.commit()
    except RepositoryError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        await db.rollback()
        raise

    return CandidateDetail(
        id=result.id,
        unit_type=result.unit_type,
        source_version_id=result.source_version_id,
        annotation_id=result.annotation_id,
        decision_status=result.decision_status,
        gate_decision=result.gate_decision,
        build_versions=result.build_versions,
        input_identity=result.input_identity,
        payload=result.payload,
        review_trail=result.review_trail,
        created_at=result.created_at,
        decided_at=result.decided_at,
        logical_execution_stage=result.logical_execution_stage,
        logical_execution_hash=result.logical_execution_hash,
    )


@router.post("/{candidate_id}/reject", response_model=CandidateDetail)
async def reject_candidate(
    candidate_id: uuid.UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
) -> CandidateDetail:
    """人工 reject：经 AdmissionService.reject()（P0-G-003 human path）。"""
    service = AdmissionService(db)
    try:
        result = await service.reject(
            candidate_id=candidate_id,
            reasons=body.reasons,
            source="human",
            reviewer_id=body.reviewer_id,
        )
        await db.commit()
    except RepositoryError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        await db.rollback()
        raise

    return CandidateDetail(
        id=result.id,
        unit_type=result.unit_type,
        source_version_id=result.source_version_id,
        annotation_id=result.annotation_id,
        decision_status=result.decision_status,
        gate_decision=result.gate_decision,
        build_versions=result.build_versions,
        input_identity=result.input_identity,
        payload=result.payload,
        review_trail=result.review_trail,
        created_at=result.created_at,
        decided_at=result.decided_at,
        logical_execution_stage=result.logical_execution_stage,
        logical_execution_hash=result.logical_execution_hash,
    )
