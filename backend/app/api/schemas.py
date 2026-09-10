"""Pydantic 响应模型：API 序列化边界。只读 ORM → JSON，不做业务逻辑。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


# ------------------------------------------------------------------ Document
class DocumentSummary(BaseModel):
    id: uuid.UUID
    file_name: str
    file_type: str
    processing_status: str
    created_at: datetime | None = None
    candidate_count: int = 0
    pending_count: int = 0


class SourceVersionInfo(BaseModel):
    id: uuid.UUID
    artifact_kind: str
    role: str
    provider: str
    status: str
    page_count: int
    line_count: int
    body_hash: str
    integrity_hash: str
    body_text: str | None = None


class FigureInfo(BaseModel):
    id: uuid.UUID
    figure_id: str
    page_no: int
    object_key: str
    figure_hash: str


class CandidateSummary(BaseModel):
    id: uuid.UUID
    unit_type: str
    decision_status: str
    gate_decision: dict | None = None
    created_at: datetime | None = None


class DocumentDetail(BaseModel):
    document: DocumentSummary
    source_versions: list[SourceVersionInfo]
    figures: list[FigureInfo]
    candidates: list[CandidateSummary]


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]
    total: int


class ImportResponse(BaseModel):
    document_id: uuid.UUID
    task_id: uuid.UUID | None = None
    sha256: str
    file_name: str
    is_new: bool


# ------------------------------------------------------------------ Source Quality
class SourceQualityReport(BaseModel):
    status: str  # valid / degraded / invalid / ocr_required
    total_chars: int
    replacement_char_ratio: float
    non_printable_ratio: float
    cjk_ratio: float
    issues: list[str]


class SourceLineInfo(BaseModel):
    line_ref: str
    seq: int
    page_no: int
    line_no_in_page: int
    text: str
    block_type: str
    bbox: dict | None = None
    line_hash: str


class SourceLinesResponse(BaseModel):
    source_version_id: uuid.UUID
    page_no: int | None = None
    total_lines: int
    lines: list[SourceLineInfo]


# ------------------------------------------------------------------ Candidate
class CandidateDetail(BaseModel):
    id: uuid.UUID
    unit_type: str
    source_version_id: uuid.UUID
    annotation_id: uuid.UUID
    decision_status: str
    gate_decision: dict | None = None
    build_versions: dict
    input_identity: dict
    payload: dict
    review_trail: list | None = None
    created_at: datetime | None = None
    decided_at: datetime | None = None
    logical_execution_stage: str
    logical_execution_hash: str


class ApproveRequest(BaseModel):
    reviewer_id: str
    confirmed_fields: list[str] = []


class RejectRequest(BaseModel):
    reviewer_id: str
    reasons: list[str]


# ------------------------------------------------------------------ Admin
class AdminStats(BaseModel):
    pending_review: int
    running_tasks: int
    failed_tasks: int
    approved_today: int


# ------------------------------------------------------------------ Task
class TaskSummary(BaseModel):
    id: uuid.UUID
    task_type: str
    status: str
    current_stage: str | None = None
    created_at: datetime | None = None
    decided_at: datetime | None = None
    llm_invocations: int = 0


class TaskListResponse(BaseModel):
    tasks: list[TaskSummary]
    total: int
