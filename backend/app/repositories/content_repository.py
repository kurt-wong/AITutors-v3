"""数据域 A Repository：live 行只经 Repository 创建（10 §6）。段 G 增查重/复用面。"""

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.content import (
    InstanceRoleContent,
    Material,
    MaterialLink,
    Question,
    QuestionInstance,
    UnitGroup,
    UnitGroupMember,
)
from app.repositories.base import BaseRepository, RepositoryError


class ContentRepository(BaseRepository):
    async def find_question_by_dedup_key(self, *, dedup_key: str) -> Question | None:
        """Question 精确查重（10 §6.1 应用层 dedup：命中复用 / 未命中新建）。"""
        res = await self._session.execute(
            select(Question).where(Question.dedup_key == dedup_key)
        )
        return res.scalars().first()

    async def find_instance_by_occurrence(
        self,
        *,
        question_id: uuid.UUID,
        source_version_id: uuid.UUID,
        occurrence_key: str,
    ) -> QuestionInstance | None:
        """Instance 防重复（10 §6.2 UNIQUE(question_id, source_version_id, occurrence_key)）。"""
        res = await self._session.execute(
            select(QuestionInstance).where(
                QuestionInstance.question_id == question_id,
                QuestionInstance.source_version_id == source_version_id,
                QuestionInstance.occurrence_key == occurrence_key,
            )
        )
        return res.scalars().first()

    async def find_material_by_dedup(
        self,
        *,
        source_version_id: uuid.UUID,
        dedup_key: str,
    ) -> Material | None:
        """Material 复用（10 §6.4 M1：source-scoped，不跨 Source Version 自动共享）——
        同 source_version 重标注按 dedup 命中既有行，不再重复建。"""
        res = await self._session.execute(
            select(Material).where(
                Material.source_version_id == source_version_id,
                Material.dedup_key == dedup_key,
            )
        )
        return res.scalars().first()

    async def create_question(
        self,
        *,
        subject: str,
        grade: str,
        canonical_question_type: str,
        dedup_key: str,
    ) -> Question:
        """幂等写（BUG-V3-027 errata）：锚 UNIQUE(dedup_key) ON CONFLICT DO NOTHING。

        插入成功 → returning 新行；同 dedup_key 冲突（并发 approve）→ re-read existing
        （幂等收敛，同一 canonical identity 恰一个 Question 行）。
        """
        stmt = (
            pg_insert(Question)
            .values(
                subject=subject,
                grade=grade,
                canonical_question_type=canonical_question_type,
                dedup_key=dedup_key,
            )
            .on_conflict_do_nothing(index_elements=["dedup_key"])
            .returning(Question)
        )
        row = (await self._session.execute(stmt)).scalars().first()
        if row is not None:
            return row
        existing = await self.find_question_by_dedup_key(dedup_key=dedup_key)
        if existing is None:
            raise RepositoryError(
                "question (dedup_key) conflict but no existing row readable"
            )
        return existing

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
        logical_execution_stage: str | None = None,
        logical_execution_hash: str | None = None,
        attempt_id: uuid.UUID | None = None,
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
            # F2（二轮对抗审查修复）：provenance 列由产生它的 admission 显式带出（10 §6.2 /
            # §3），不在此层自行推断。
            logical_execution_stage=logical_execution_stage,
            logical_execution_hash=logical_execution_hash,
            attempt_id=attempt_id,
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

    async def create_material_link(
        self,
        *,
        instance_id: uuid.UUID,
        material_id: uuid.UUID,
        role: str,
        order: int,
    ) -> MaterialLink:
        """material_links（10 §6.4 复合 PK(instance_id, material_id, role, order)）。"""
        link = MaterialLink(
            instance_id=instance_id,
            material_id=material_id,
            role=role,
            order=order,
        )
        await self.add(link)
        return link

    async def create_unit_group_member(
        self,
        *,
        unit_group_id: uuid.UUID,
        instance_id: uuid.UUID,
        member_order: int,
        role_in_group: str | None = None,
    ) -> UnitGroupMember:
        """unit_group_members（10 §6.5 复合 PK(unit_group_id, instance_id, member_order)）。"""
        member = UnitGroupMember(
            unit_group_id=unit_group_id,
            instance_id=instance_id,
            member_order=member_order,
            role_in_group=role_in_group,
        )
        await self.add(member)
        return member
