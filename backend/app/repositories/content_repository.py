"""数据域 A Repository：live 行只经 Repository 创建（10 §6）。段 A 无物化，仅提供创建面。"""

import uuid

from app.models.content import (
    InstanceRoleContent,
    Material,
    Question,
    QuestionInstance,
    UnitGroup,
)
from app.repositories.base import BaseRepository


class ContentRepository(BaseRepository):
    async def create_question(
        self,
        *,
        subject: str,
        grade: str,
        canonical_question_type: str,
        dedup_key: str,
    ) -> Question:
        question = Question(
            subject=subject,
            grade=grade,
            canonical_question_type=canonical_question_type,
            dedup_key=dedup_key,
        )
        await self.add(question)
        return question

    async def create_instance(
        self,
        *,
        question_id: uuid.UUID,
        document_id: uuid.UUID,
        source_version_id: uuid.UUID,
        occurrence_key: str,
        page_no: int,
        instance_order: int,
        question_number: str | None = None,
        question_number_range: str | None = None,
        unit_group_id: uuid.UUID | None = None,
    ) -> QuestionInstance:
        instance = QuestionInstance(
            question_id=question_id,
            document_id=document_id,
            source_version_id=source_version_id,
            unit_group_id=unit_group_id,
            occurrence_key=occurrence_key,
            question_number=question_number,
            question_number_range=question_number_range,
            page_no=page_no,
            instance_order=instance_order,
        )
        await self.add(instance)
        return instance

    async def create_role_content(
        self,
        *,
        instance_id: uuid.UUID,
        role: str,
        role_index: int,
        text: str,
        text_hash: str,
        label: str | None = None,
        source_span: dict | None = None,
        answer_status: dict | None = None,
    ) -> InstanceRoleContent:
        role_content = InstanceRoleContent(
            instance_id=instance_id,
            role=role,
            label=label,
            role_index=role_index,
            text=text,
            text_hash=text_hash,
            source_span=source_span,
            answer_status=answer_status,
        )
        await self.add(role_content)
        return role_content

    async def create_material(
        self,
        *,
        subject: str,
        grade: str,
        source_version_id: uuid.UUID,
        text: str,
        text_hash: str,
        source_span: dict | None = None,
        dedup_key: str | None = None,
    ) -> Material:
        material = Material(
            subject=subject,
            grade=grade,
            source_version_id=source_version_id,
            text=text,
            text_hash=text_hash,
            source_span=source_span,
            dedup_key=dedup_key,
        )
        await self.add(material)
        return material

    async def create_unit_group(
        self,
        *,
        unit_type: str,
        document_id: uuid.UUID,
        source_version_id: uuid.UUID,
        question_number_range: str | None = None,
        shared_material_id: uuid.UUID | None = None,
    ) -> UnitGroup:
        unit_group = UnitGroup(
            unit_type=unit_type,
            document_id=document_id,
            source_version_id=source_version_id,
            question_number_range=question_number_range,
            shared_material_id=shared_material_id,
        )
        await self.add(unit_group)
        return unit_group
