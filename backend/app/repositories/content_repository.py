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

_RANGE_QN_RE = __import__("re").compile(r"(\d{1,3})\s*[-–—~～]\s*(\d{1,3})")


def _is_range_qn(value: str) -> bool:
    return bool(_RANGE_QN_RE.fullmatch((value or "").strip()))


def _qn_belongs_to_instance(
    *, fact_qn: str, instance_qn: str, instance_qn_range: str
) -> bool:
    """Independent question-identity check (P1-B).

    Leaf: fact qn must equal instance.question_number.
    Composite: instance.question_number is a range (or question_number_range
    is); fact qn (child) must fall inside that range. Empty fact qn never
    matches — missing identity is not a match.
    """
    fq = (fact_qn or "").strip()
    if not fq:
        return False
    iq = (instance_qn or "").strip()
    ir = (instance_qn_range or "").strip()
    if fq == iq:
        return True
    for candidate in (iq, ir):
        m = _RANGE_QN_RE.fullmatch(candidate)
        if not m:
            continue
        lo, hi = int(m.group(1)), int(m.group(2))
        try:
            n = int(fq)
        except ValueError:
            continue
        if lo <= n <= hi:
            return True
    return False


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

    async def converge_subject_grade(
        self,
        row,
        *,
        subject: str | None,
        grade: str | None,
    ) -> None:
        """BUG-V3-021 metadata 单调收敛（Question/Material 共用）。

        NULL → known 补写；known → same no-op；known → different → RepositoryError
        （fail-loud，禁 first-write-wins 静默覆盖）。unknown = None（非空串）。
        """
        changed = False
        for attr, incoming in (("subject", subject), ("grade", grade)):
            current = getattr(row, attr)
            if incoming is None or current == incoming:
                continue
            if current is None:
                setattr(row, attr, incoming)
                changed = True
            else:
                raise RepositoryError(
                    f"{type(row).__name__} {attr} metadata conflict: "
                    f"existing={current!r} incoming={incoming!r}"
                )
        if changed:
            await self.flush()

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
        # P0 CONTRACT-FINAL publish boundary (unbypassable).
        # role=answer may only receive official_text; candidate text is forbidden.
        if role == "answer":
            status = dict(answer_status or {})
            own = status.get("ownership") or "unknown"
            publish = status.get("publish") or "withheld_review"
            span_id = status.get("span_id") or (source_span or {}).get("span_id") or ""
            fact_id = status.get("binding_fact_id") or ""

            # P0-R16b invariant C: empty text / withheld / pending can be
            # safely persisted WITHOUT a binding fact. Only non-empty
            # official text requires full binding verification.
            if text:
                # P0-R16: Repository MUST fetch Instance and verify
                # source_version_id BEFORE authorizing non-empty text.
                from sqlalchemy import select as _sa_select
                from app.models.content import InstanceRoleContent as _IRC
                from app.models.content import QuestionInstance as _QI
                from app.domains.gate.binding_fact import (
                    fact_matches_answer_text,
                    resolve_trusted_binding_fact,
                    verify_binding_fact,
                )
                _qi_row = (await self._session.execute(
                    _sa_select(
                        _QI.source_version_id,
                        _QI.question_number,
                        _QI.question_number_range,
                        _QI.unit_group_id,
                    ).where(_QI.id == instance_id)
                )).first()
                if _qi_row is None:
                    raise RepositoryError(
                        "instance not found — cannot authorize official answer"
                    )
                _instance_sv = str(_qi_row[0])
                _instance_qn = str(_qi_row[1] or "")
                _instance_qn_range = str(_qi_row[2] or "")
                _instance_ug = _qi_row[3]

                fact = resolve_trusted_binding_fact(
                    source_version_id=_instance_sv,
                    span_id=span_id,
                )
                if fact is None:
                    raise RepositoryError(
                        "no trusted binding fact for (SV, span) — cannot authorize official answer"
                    )
                if not verify_binding_fact(fact):
                    raise RepositoryError(
                        "binding fact failed verification — cannot authorize official answer"
                    )
                if fact.source_version_id != _instance_sv:
                    raise RepositoryError(
                        "binding fact source_version_id does not match instance — "
                        "cannot authorize official answer"
                    )
                if fact_id and fact.fact_id != fact_id:
                    raise RepositoryError(
                        "binding_fact_id mismatch — cannot authorize official answer"
                    )
                if own == "foreign":
                    raise RepositoryError(
                        "foreign answer must not be published (ownership=foreign)"
                    )
                if publish != "official":
                    raise RepositoryError(
                        "non-official answer text must be empty "
                        f"(publish={publish!r}, ownership={own!r})"
                    )
                if "candidate_text" in status:
                    raise RepositoryError(
                        "candidate_text must not be stored in official answer_status"
                    )
                if (fact.ownership or "unknown") == "foreign":
                    raise RepositoryError(
                        "trusted binding fact is foreign — cannot authorize official answer"
                    )
                if (fact.ownership or "unknown") != (own or "unknown"):
                    raise RepositoryError(
                        "answer_status ownership disagrees with trusted binding fact "
                        f"(status={own!r}, fact={fact.ownership!r})"
                    )
                if not (fact.unit_id or ""):
                    raise RepositoryError(
                        "binding fact missing unit_id — cannot authorize official answer"
                    )
                # P1-B: independently verify question identity against the
                # QuestionInstance row (NOT caller-supplied answer_status).
                # Omitting binding_unit_id / binding_question_number must not
                # skip the ownership gate.
                if not (fact.question_number or "").strip():
                    raise RepositoryError(
                        "binding fact missing question_number — cannot authorize official answer"
                    )
                _has_instance_qn = bool(_instance_qn.strip() or _instance_qn_range.strip())
                if _has_instance_qn:
                    if not _qn_belongs_to_instance(
                        fact_qn=fact.question_number or "",
                        instance_qn=_instance_qn,
                        instance_qn_range=_instance_qn_range,
                    ):
                        raise RepositoryError(
                            "binding fact question_number does not belong to this "
                            f"instance (fact={fact.question_number!r}, "
                            f"instance={_instance_qn!r}, range={_instance_qn_range!r})"
                        )
                # Independent unit identity (P1 composite bypass fix):
                # Stems/options/materials for this instance are written BEFORE
                # answers and carry the real unit_id in source_span. A fact
                # may only bind if its unit_id is a member of that set.
                # Composite children ARE members (per-child stems); a fact
                # belonging to another parent's child is NOT.
                _role_rows = (await self._session.execute(
                    _sa_select(_IRC.source_span).where(
                        _IRC.instance_id == instance_id
                    )
                )).scalars().all()
                _known_units = {
                    str((sp or {}).get("unit_id") or "").strip()
                    for sp in _role_rows
                }
                _known_units.discard("")
                _fact_uid = str(fact.unit_id or "").strip()
                if _known_units:
                    if _fact_uid not in _known_units:
                        raise RepositoryError(
                            "binding fact unit_id is not a member of this instance "
                            f"(fact={fact.unit_id!r}, instance_units={sorted(_known_units)!r})"
                        )
                else:
                    # No persisted unit identity on role rows. Fall back to
                    # question-number / range (instance + unit_group). Missing
                    # both is NOT a match — fail closed.
                    from app.models.content import UnitGroup as _UG
                    _ug_range = ""
                    if _instance_ug is not None:
                        _ug_range = str((await self._session.execute(
                            _sa_select(_UG.question_number_range).where(
                                _UG.id == _instance_ug
                            )
                        )).scalar_one_or_none() or "")
                    _qn_sources = (_instance_qn, _instance_qn_range, _ug_range)
                    _has_qn_identity = any(s.strip() for s in _qn_sources)
                    if not _has_qn_identity:
                        raise RepositoryError(
                            "instance has no unit identity on role rows and no "
                            "question_number/range — cannot authorize official answer"
                        )
                    if not any(
                        _qn_belongs_to_instance(
                            fact_qn=fact.question_number or "",
                            instance_qn=src if src.strip() and not _is_range_qn(src) else "",
                            instance_qn_range=src if _is_range_qn(src) else "",
                        )
                        or _qn_belongs_to_instance(
                            fact_qn=fact.question_number or "",
                            instance_qn=_instance_qn,
                            instance_qn_range=src,
                        )
                        for src in _qn_sources
                    ):
                        raise RepositoryError(
                            "binding fact question_number does not belong to this "
                            f"instance (fact={fact.question_number!r}, "
                            f"instance={_instance_qn!r}, range={_instance_qn_range!r}, "
                            f"group_range={_ug_range!r})"
                        )
                # Caller-supplied binding_* fields remain as extra checks only.
                _status_unit = str(status.get("binding_unit_id") or "")
                if _status_unit and _status_unit != (fact.unit_id or ""):
                    raise RepositoryError(
                        "binding_unit_id mismatch — cannot authorize official answer"
                    )
                _status_qn = str(status.get("binding_question_number") or "")
                if fact.question_number and _status_qn and fact.question_number != _status_qn:
                    raise RepositoryError(
                        "binding fact question_number does not match answer_status "
                        f"(fact={fact.question_number!r}, status={_status_qn!r})"
                    )
                if not fact_matches_answer_text(fact, text):
                    raise RepositoryError(
                        "official text does not match binding fact answer_text — "
                        "cannot authorize official answer"
                    )
                from app.domains.gate.publish_seal import verify_publish_seal
                seal = status.get("publish_seal") or ""
                if not verify_publish_seal(
                    fact=fact,
                    official_text=text,
                    publish=publish,
                    seal=seal,
                ):
                    raise RepositoryError(
                        "publish seal missing or invalid — cannot authorize official answer"
                    )
            if publish == "withheld_review" and text:
                text = ""
                text_hash = __import__("hashlib").sha256(b"").hexdigest()
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

    async def update_answer_verified_correct(
        self, *, instance_id: uuid.UUID, verified_correct: bool | None
    ) -> int:
        """WP7-C: update answer role_contents' answer_status.verified_correct.

        Used by approve's reuse path when the Instance was previously created
        by materialize_for_review (verified_correct=null).  Only touches
        role='answer' rows; never downgrades True → null/False.
        Returns number of rows updated.
        """
        res = await self._session.execute(
            select(InstanceRoleContent).where(
                InstanceRoleContent.instance_id == instance_id,
                InstanceRoleContent.role == "answer",
            )
        )
        rows = res.scalars().all()
        n = 0
        for row in rows:
            status = dict(row.answer_status or {})
            current = status.get("verified_correct")
            # Never downgrade: True stays True regardless of requested value.
            if current is True:
                continue
            if verified_correct is None:
                continue
            status["verified_correct"] = verified_correct
            row.answer_status = status
            n += 1
        return n

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
