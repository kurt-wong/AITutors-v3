"""QUESTION-VISUAL-INSPECTION-V1：学生实际视图只读 API。

安全边界（服务端强制，前端不得绕过）：
- 只输出学生可见字段：无 text_hash / source_span / occurrence_key / dedup_key /
  answer_status 诊断链（candidate_text、BindingFact、publish_seal 概念不出现）。
- answer / explanation 文本仅当该题 answer_publish == "official" 时输出非空；
  其余（withheld_review / mixed / none）强制文本为空并以真实状态标注。
  （Repository 写入期已保证非 official 答案 text 恒空——此处为读出期双闸。）
- stem / option / material 随题可见（题干是练习对象本身）。
- 本路由不做任何写入。
"""

from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas import (
    StudentInstanceInfo,
    StudentQuestionDetail,
    StudentQuestionListResponse,
    StudentQuestionSummary,
    StudentRoleContentInfo,
)
from app.models.content import InstanceRoleContent, Question, QuestionInstance

router = APIRouter(prefix="/student/questions", tags=["student"])

_ANSWER_ROLES = ("answer", "explanation")

# 04-C F2/P0-14：display_note 学生可读化。数据层原文保留完整记录（含内部
# 裁决语境），学生 API 出参不得出现内部工程/裁决语言（Owner/Manifest/Word
# 母本/内部审查/方案裁定等）。
# 04-C-R3（Owner 内容裁定 2026-11-04）：已裁定的说明文案按 label 映射直出
# ——Q9 题干 0.110 为源文件笔误、真值 0.10（答案区 p14 交叉印证），学生面
# 文案必须反映「笔误、以 0.10 为准」而非中立双值并列；数据层不动。
_DISPLAY_NOTE_STUDENT_TEXT = {
    "q9_concentration_original": (
        "题目区 0.110 mol·L⁻¹ 为源文件笔误，应以 0.10 mol·L⁻¹ 为准（答案区可证）"
    ),
}
# 未映射 note 的通用改写规则（从文案自身派生，不硬编码题目数值）：
# 1) 移除含内部语言的括号旁注；2) 旁注内的「答案解析区 X」读数转写为
# 「；答案解析区作 X <单位>」（单位取自主文数值后的单位串）；
# 3) 兜底：改写后仍含内部关键词 → 只回主文；仍不安全 → 极简安全文案。
_INTERNAL_NOTE_MARKERS = (
    "owner", "裁定", "裁决", "word 母本", "word母本", "manifest",
    "内部", "审查", "方案 b", "方案b", "预处理", "preprocessing",
    "适配层", "候选", "candidate", "bindingfact", "裁决语",
)
_INTERNAL_PAREN_RE = re.compile(r"[（(][^（）()]*[）)]")
_READING_RE = re.compile(r"答案解析区\s*作?\s*([0-9]+(?:\.[0-9]+)?)")
_UNIT_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?\s*([^\s；;，,、。]+)")


def _has_internal_marker(text: str) -> bool:
    low = (text or "").lower()
    return any(m in low for m in _INTERNAL_NOTE_MARKERS)


def _student_display_note_text(text: str, label: str | None = None) -> str:
    mapped = _DISPLAY_NOTE_STUDENT_TEXT.get((label or "").strip())
    if mapped:
        return mapped
    raw = text or ""
    if not _has_internal_marker(raw):
        return raw
    # 1) 记录并移除含内部语言的括号旁注
    removed: list[str] = []

    def _drop(m: re.Match) -> str:
        seg = m.group(0)
        if _has_internal_marker(seg):
            removed.append(seg)
            return ""
        return seg

    base = _INTERNAL_PAREN_RE.sub(_drop, raw).strip(" 　;；")
    if not base:
        return "原文如此。"
    # 2) 旁注里的「答案解析区 X」读数 → 学生可读补充说明
    alt = ""
    for seg in removed:
        m = _READING_RE.search(seg)
        if m:
            alt = m.group(1)
            break
    if alt:
        um = _UNIT_RE.search(base)
        unit = um.group(1) if um else ""
        base = f"{base}；答案解析区作 {alt}{(' ' + unit) if unit else ''}"
    # 3) 兜底：仍含内部语言 → 只回主文；仍不安全 → 极简安全文案
    if _has_internal_marker(base):
        base = re.sub(r"[（(][^（）()]*[）)]", "", raw).strip(" 　;；")
    if _has_internal_marker(base):
        return "原文如此。"
    return base


def _aggregate_publish(statuses: list[dict | None]) -> str:
    """按 answer 行 answer_status.publish 聚合：official/withheld_review/mixed/none。"""
    pubs = {(s or {}).get("publish") or "withheld_review" for s in statuses}
    if not pubs:
        return "none"
    if pubs == {"official"}:
        return "official"
    if pubs == {"withheld_review"}:
        return "withheld_review"
    return "mixed"


@router.get("", response_model=StudentQuestionListResponse)
async def student_list_questions(
    subject: str | None = None,
    document_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> StudentQuestionListResponse:
    """学生视图题单：真实入库题 + 真实发布状态，无诊断字段。"""
    stmt = (
        select(Question, QuestionInstance)
        .join(QuestionInstance, QuestionInstance.question_id == Question.id)
        .order_by(QuestionInstance.instance_order, QuestionInstance.question_number)
    )
    if subject is not None:
        stmt = stmt.where(Question.subject == subject)
    if document_id is not None:
        stmt = stmt.where(QuestionInstance.document_id == document_id)
    rows = (await db.execute(stmt)).all()
    total = len(rows)
    page = rows[offset : offset + limit]

    inst_ids = [qi.id for _, qi in page]
    contents_by_inst: dict[uuid.UUID, list[InstanceRoleContent]] = {}
    if inst_ids:
        crows = (
            await db.execute(
                select(InstanceRoleContent)
                .where(InstanceRoleContent.instance_id.in_(inst_ids))
                .order_by(
                    InstanceRoleContent.role,
                    InstanceRoleContent.role_index,
                    InstanceRoleContent.label,
                )
            )
        ).scalars().all()
        for c in crows:
            contents_by_inst.setdefault(c.instance_id, []).append(c)

    items: list[StudentQuestionSummary] = []
    for q, qi in page:
        contents = contents_by_inst.get(qi.id, [])
        ans_statuses = [c.answer_status for c in contents if c.role == "answer"]
        publish = _aggregate_publish(ans_statuses)
        stem = next((c.text for c in contents if c.role == "stem"), "")
        items.append(
            StudentQuestionSummary(
                id=q.id,
                subject=q.subject,
                grade=q.grade,
                canonical_question_type=q.canonical_question_type,
                question_number=qi.question_number,
                question_number_range=qi.question_number_range,
                page_no=qi.page_no,
                stem_excerpt=(stem or "")[:120],
                answer_publish=publish,
                student_answer_visible=publish == "official",
            )
        )
    return StudentQuestionListResponse(questions=items, total=total)


@router.get("/{question_id}", response_model=StudentQuestionDetail)
async def student_get_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StudentQuestionDetail:
    """学生实际视图详情：发布门控在服务端执行，非 official 答案/解析文本恒空。"""
    q = await db.get(Question, question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="question not found")

    inst_rows = (
        await db.execute(
            select(QuestionInstance)
            .where(QuestionInstance.question_id == question_id)
            .order_by(QuestionInstance.instance_order)
        )
    ).scalars().all()

    # 先聚合整题发布状态，再按状态对 answer/explanation 文本做读出期双闸
    all_contents: list[tuple[QuestionInstance, list[InstanceRoleContent]]] = []
    all_ans_statuses: list[dict | None] = []
    for qi in inst_rows:
        contents = (
            await db.execute(
                select(InstanceRoleContent)
                .where(InstanceRoleContent.instance_id == qi.id)
                .order_by(
                    InstanceRoleContent.role,
                    InstanceRoleContent.role_index,
                    InstanceRoleContent.label,
                )
            )
        ).scalars().all()
        all_contents.append((qi, contents))
        all_ans_statuses.extend(c.answer_status for c in contents if c.role == "answer")

    publish = _aggregate_publish(all_ans_statuses)
    answer_visible = publish == "official"

    instances: list[StudentInstanceInfo] = []
    for qi, contents in all_contents:
        out_contents: list[StudentRoleContentInfo] = []
        for c in contents:
            text = c.text or ""
            if c.role in _ANSWER_ROLES and not answer_visible:
                text = ""  # 读出期双闸：非 official 不出答案/解析文本
            if c.role == "display_note":
                # 04-C F2/P0-14：display_note 学生面文案改写（内部裁决语言不出 API）
                text = _student_display_note_text(text, label=c.label)
            out_contents.append(
                StudentRoleContentInfo(
                    role=c.role,
                    label=c.label,
                    role_index=c.role_index,
                    text=text,
                )
            )
        instances.append(
            StudentInstanceInfo(
                question_number=qi.question_number,
                question_number_range=qi.question_number_range,
                page_no=qi.page_no,
                contents=out_contents,
            )
        )

    first_qn = inst_rows[0].question_number if inst_rows else ""
    first_range = inst_rows[0].question_number_range if inst_rows else ""
    return StudentQuestionDetail(
        id=q.id,
        subject=q.subject,
        grade=q.grade,
        canonical_question_type=q.canonical_question_type,
        question_number=first_qn,
        question_number_range=first_range,
        answer_publish=publish,
        student_answer_visible=answer_visible,
        instances=instances,
    )
