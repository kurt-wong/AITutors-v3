"""AdmissionService（段 G，admission.py，20 §8.2 / 10 §5.4 / P0-G）。

`decision_status` 的唯一入口 = approve()/reject()（P0-G-001：Repository 公共接口直改抛
AppendOnlyViolation；本模块是唯一合法 decision-transition owner，application-level，不加
ORM/DB 物理拦截）。

approve() 是**物化事务**：lock candidate → 校验 → 物化 A 域（Question 复用/新建 +
Instance + role_contents + material/link + unit_group/member）→ INSERT admission_event
（candidate_id UNIQUE）→ decision_status=approved，同一 DB 事务原子完成；任一步失败 →
异常上抛，调用方不 COMMIT 即整体 ROLLBACK，Candidate 保持 pending_review（无 "approved
但未物化" 中间态，10 §5.2）。

约束落实：
- P0-G-002：gate_decision=rejected（结构/语义矛盾）→ 拒 approve，即使 decision_status
  仍 pending_review。
- P0-G-003：reject 区分 machine_gate（只 transition，不重写 gate_decision）与 human
  （reasons 只 append review_trail，gate_decision 保留）。
- P0-3：approve **只消费冻结 candidate.payload**（不重跑 E/F/G）；dedup_key/occurrence_key
  以 identity 纯函数从 payload 确定性重算（20 §7.3），不改 payload。
- 复用语义（10 §6.1/§6.2 冻结）：Question dedup exact 命中 → REUSE（不重建、不改写），
  仅为其新 occurrence INSERT 新 Instance；同 (question, source_version, occurrence) 二次
  导出复用既有 Instance（其 role/link/member 已由先前物化写入，不重建）。全部 leaf 均
  复用 → 无新 A 域行（approve 记录空事件，不崩溃、不留空 group）。
- D8：composite parent 无独立 answer role；物化不为父建空 answer 行。
- 20 §8.2 双入口：自动路径（gate_decision=auto_approve）或人工路径（review_trail 含
  human/golden approve 确认）。approved 的 answer verified_correct 物化为 true。
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from app.domains.compile import map_canonical_type
from app.domains.gate.binding_fact import (
    fact_matches_answer_text,
    resolve_trusted_binding_fact,
)
from app.domains.gate.publish_seal import issue_publish_seal, verify_publish_seal
from app.domains.compile.identity_normalization import (
    canonical_options_input,
    identity_hash,
    normalize_identity,
    strip_option_label,
)
from app.domains.evidence.proof import generate_review_proof, verify_review_proof
from app.models.snapshot import AdmissionCandidate
from app.repositories.base import RepositoryError
from app.repositories.content_repository import ContentRepository
from app.repositories.evidence_repository import (
    AUTHORITY_VALIDATED,
    EvidenceRepository,
)
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

_HUMAN_SOURCES = frozenset({"human", "golden"})
_LINE_REF_PAGE_RE = re.compile(r"^P(\d+)L(\d+)$")

# 人工 review entry 常量键（20 §8.2 review_trail；BUG-V3-025 终裁：统一 schema，time 由
# append_review_trail 注入，reject 用 reasons 列表，approve 用 confirmed_fields）。
_REVIEW_APPROVE = "approve"
_REVIEW_REJECT = "reject"


class AdmissionService:
    def __init__(self, session) -> None:
        self._content = ContentRepository(session)
        self._snap = SnapshotRepository(session)
        self._source = SourceRepository(session)
        # EB-008 §5.3：Evidence Authority 投影 + human_review 事件写入（Admission Boundary）
        self._evidence = EvidenceRepository(session)

    # ------------------------------------------------------------------ approve
    async def approve(
        self,
        *,
        candidate_id: uuid.UUID,
        provenance: dict,
        annotation_id: uuid.UUID | None = None,
    ) -> AdmissionCandidate:
        """唯一 approved 入口：物化事务（10 §5.4）。

        provenance：{source: "auto_gate" | "human" | "golden", reviewer_id?, confirmed_fields?}。
        自动路径要求 gate_decision.decision == auto_approve；人工路径要求 review_trail 已
        有人工 approve 确认（20 §8.2）。已 approved → no-op 返回既有（防双物化）。
        """
        source = provenance.get("source")
        candidate = await self._snap.lock_candidate(candidate_id)
        if candidate.decision_status == "approved":
            # P2-CANDIDATE-DEDUP: 防双物化 no-op，但元数据仍需收敛
            # （subject/grade claims 补齐后要到达 Question）。
            await self._converge_candidate_metadata(candidate, annotation_id=annotation_id)
            # R2-FIX: already-approved candidates must still fill empty
            # official answers. Previously this early-returned, leaving
            # empty answers forever after the first pending_review run.
            await self._update_empty_answers(
                candidate, grant=source or "none",
                review_evidence={
                    "reviewer_id": provenance.get("reviewer_id") or "",
                    "confirmed_fields": list(provenance.get("confirmed_fields") or []),
                    "source": source or "",
                },
                mark_verified=True,
            )
            return candidate
        if candidate.decision_status != "pending_review":
            raise RepositoryError(
                f"approve only from pending_review, got {candidate.decision_status!r}"
            )

        gd = candidate.gate_decision or {}
        if gd.get("decision") == "rejected":
            # P0-G-002：结构/语义明确矛盾 → terminal rejected，即使 decision_status 仍 pending。
            raise RepositoryError(
                "cannot approve: gate_decision=rejected (structural/semantic contradiction)"
            )

        if source == "auto_gate":
            if gd.get("decision") != "auto_approve":
                raise RepositoryError(
                    "auto approve requires gate_decision=auto_approve; "
                    f"got {gd.get('decision')!r}"
                )
        elif source in _HUMAN_SOURCES:
            if not _has_human_approve(candidate.review_trail):
                raise RepositoryError(
                    "manual approve requires a human/golden review_trail entry "
                    "(20 §8.2 manual path)"
                )
        else:
            raise RepositoryError(f"unknown approve source {source!r}")

        # ---- EB-008 §5.3：Evidence Authority enforcement（Admission Boundary）----
        # human 路径：人工审核结果 → human_review ValidationEvent + review_proof（§5.2）
        # 双入口保持（20 §8.2）：auto_gate 依赖 Gate 已落的 validated 事件；
        # human 依赖本步生成的 human_review 事件。随后统一投影校验，fail-closed。
        if source in _HUMAN_SOURCES:
            await self._record_human_review(candidate, review_result="validated")
        await self._require_evidence_authority(candidate)

        created_questions, created_instances = await self._materialize(
            candidate,
            annotation_id=annotation_id,
            grant=source or "none",
            review_evidence={
                "reviewer_id": provenance.get("reviewer_id") or "",
                "confirmed_fields": list(provenance.get("confirmed_fields") or []),
                "source": source or "",
            },
        )

        await self._snap.create_admission_event(
            candidate_id=candidate.id,
            created_question_ids=created_questions,
            created_instance_ids=created_instances,
        )
        decided = await self._snap._transition_decision(candidate.id, "approved")
        return decided

    async def materialize_for_review(
        self, *, candidate_id: uuid.UUID, annotation_id: uuid.UUID | None = None
    ) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
        """E2E-009R7：pending_review 候选物化为待审核 Question/Instance。

        - decision_status 保持 pending_review（不走 approve/reject）
        - answer_status.verified_correct 保持 null（未验证）
        - 不写 admission_event（candidate_id UNIQUE 留给后续 approve）
        - 不降低 strict-auto；不伪造答案
        """
        candidate = await self._snap.lock_candidate(candidate_id)
        if candidate.decision_status != "pending_review":
            raise RepositoryError(
                f"materialize_for_review only from pending_review, "
                f"got {candidate.decision_status!r}"
            )
        gd = candidate.gate_decision or {}
        if gd.get("decision") == "rejected":
            raise RepositoryError("cannot materialize rejected candidate")
        return await self._materialize(
            candidate,
            mark_verified=False,
            annotation_id=annotation_id,
            grant="none",
            review_evidence=None,
        )

    # ------------------------------------------------------------------ reject
    async def reject(
        self,
        *,
        candidate_id: uuid.UUID,
        reasons: list[str],
        source: str,
        reviewer_id: str | None = None,
    ) -> AdmissionCandidate:
        """唯一 rejected 入口（P0-G-003 区分 machine/human 证据链）。"""
        if source not in ("machine_gate", *_HUMAN_SOURCES):
            raise RepositoryError(f"unknown reject source {source!r}")
        candidate = await self._snap.lock_candidate(candidate_id)
        if candidate.decision_status == "rejected":
            return candidate  # 幂等 no-op
        if candidate.decision_status != "pending_review":
            raise RepositoryError(
                f"reject only from pending_review, got {candidate.decision_status!r}"
            )

        if source == "machine_gate":
            # gate_decision 已=rejected（GatePolicy 写入）。只 transition，不重写 gate_decision。
            gd = candidate.gate_decision or {}
            if gd.get("decision") != "rejected":
                raise RepositoryError(
                    "machine_gate reject requires gate_decision=rejected; "
                    f"got {gd.get('decision')!r}"
                )
            return await self._snap._transition_decision(candidate.id, "rejected")

        # human/golden：reasons 只 append review_trail；gate_decision 保留原机器判断。
        entry = {
            "decision": _REVIEW_REJECT,
            "verified_by": source,
            "reviewer_id": reviewer_id,
            "reasons": reasons,
        }
        candidate = await self._snap.append_review_trail(candidate_id, entry)
        # EB-008 §5.2：人工 reject → human_review ValidationEvent（rejected）+ proof
        await self._record_human_review(candidate, review_result="rejected")
        return await self._snap._transition_decision(candidate.id, "rejected")

    # -------------------------------------------------- EB-008 Authority Boundary
    async def _record_human_review(
        self, candidate: AdmissionCandidate, *, review_result: str
    ) -> None:
        """人工审核结果 → human_review ValidationEvent + review_proof（92号 §5.2）。

        reviewed_at / reviewer_id 取自 review_trail 最新对应 entry（BUG-V3-025：time 由
        append_review_trail 注入）。replay（已有同结果事件）→ Repository no-op（R4）。
        """
        entry = _latest_human_entry(candidate.review_trail, review_result)
        if entry is None:
            raise RepositoryError(
                f"no human {review_result} review_trail entry found (20 §8.2)"
            )
        reviewed_at = _parse_review_time(entry.get("time"))
        reviewer_id = entry.get("reviewer_id") or entry.get("verified_by") or "unknown"
        proof = generate_review_proof(
            candidate_id=candidate.id,
            review_result=review_result,
            reviewer_id=reviewer_id,
            reviewed_at=reviewed_at,
        )
        await self._evidence.append_human_review_event(
            candidate_id=candidate.id,
            source_version_id=candidate.source_version_id,
            claim_id=_candidate_claim_id(candidate),
            review_result=review_result,
            reviewer_id=reviewer_id,
            reviewed_at=reviewed_at,
            review_proof=proof,
        )

    async def _require_evidence_authority(self, candidate: AdmissionCandidate) -> None:
        """Admission Boundary：claim Authority 必须 VALIDATED，否则 fail-closed（92号 §5.3）。

        - 投影（latest-by-validated_at wins）
        - human_review 事件 → verify_review_proof；失败 → 拒（防 DB 篡改，§2 声明 2）
        - Authority 缺失/无效 → RepositoryError；candidate 保持 pending_review（不 reject）
        """
        claim_id = _candidate_claim_id(candidate)
        state, latest = await self._evidence.project_authority(candidate.id, claim_id)
        if latest is not None and latest.validation_method == "human_review":
            if not verify_review_proof(latest):
                raise RepositoryError(
                    f"Evidence Authority fail-closed: human_review proof invalid "
                    f"for claim {claim_id!r} (possible DB tamper, EB-008 §5.2)"
                )
        if state != AUTHORITY_VALIDATED:
            raise RepositoryError(
                f"Evidence Authority fail-closed: claim {claim_id!r} "
                f"authority={state!r}; approval forbidden (EB-008)"
            )

    # ------------------------------------------------------------------ 元数据收敛
    async def _converge_candidate_metadata(
        self, candidate: AdmissionCandidate, *, annotation_id: uuid.UUID | None = None,
    ) -> None:
        """P2-CANDIDATE-DEDUP + P2-MATERIAL-METADATA: 已 approved 的 Candidate 重跑时收敛 subject/grade。

        覆盖 Question 和 Material（NULL → known 补写），不重建物化行。
        Material 从 Candidate payload 的 compiled_roles 定位（与 _materialize 同源）。
        """
        ann = await self._snap.find_annotation_by_id(annotation_id or candidate.annotation_id)
        claims = (ann.payload or {}).get("document_metadata_claims", {}) if ann else {}
        subject = claims.get("subject")
        grade = claims.get("grade")
        if subject is None and grade is None:
            return
        from sqlalchemy import select
        from app.models.snapshot import AdmissionEvent
        from app.models.content import Question, Material
        events = (await self._snap._session.execute(
            select(AdmissionEvent).where(AdmissionEvent.candidate_id == candidate.id)
        )).scalars().all()
        for ev in events:
            for qid in (ev.created_question_ids or []):
                q = await self._snap._session.get(Question, qid)
                if q is not None:
                    await self._content.converge_subject_grade(q, subject=subject, grade=grade)
        # P2-MATERIAL-METADATA: 从 payload compiled_roles 定位 Material 并收敛
        p = candidate.payload or {}
        for m in p.get("compiled_roles", []):
            if m.get("kind") != "material":
                continue
            mdedup = identity_hash(
                {"material_type": m["role"], "text": normalize_identity(m["text"])}
            )
            mat = await self._content.find_material_by_dedup(
                source_version_id=candidate.source_version_id, dedup_key=mdedup
            )
            if mat is not None:
                await self._content.converge_subject_grade(mat, subject=subject, grade=grade)

    # ------------------------------------------------------------------ R2-HANDOFF
    async def _resolve_fact_with_fallback(
        self,
        *,
        source_version_id: str,
        span_id: str,
        answer_payload: dict | None = None,
        candidate_payload: dict | None = None,
        allow_fallback: bool = False,
    ):
        """Resolve BindingFact from registry; optionally reconstruct from real source.

        allow_fallback=True (approve path only): when registry is empty,
        reconstruct from REAL source lines in DB (never candidate text).
        allow_fallback=False (materialize_for_review): registry miss → None
        (safe withhold, frozen contract).
        """
        fact = resolve_trusted_binding_fact(
            source_version_id=source_version_id,
            span_id=span_id,
        )
        if fact is not None:
            return fact
        if not allow_fallback:
            return None
        # Registry miss: reconstruct from REAL source lines in DB.
        # NEVER use candidate answer text as source_lines (self-proof).
        if not answer_payload and not candidate_payload:
            return None
        # Find the span's line_refs from resolved_spans.
        _spans = (candidate_payload or {}).get("resolved_spans") or []
        _span = None
        for s in _spans:
            if str(s.get("span_id") or "") == span_id:
                _span = s
                break
        if _span is None:
            return None
        _line_refs = list(_span.get("line_refs") or ())
        if not _line_refs:
            return None
        # Look up REAL source lines from document_source_lines.
        _real_lines = []
        try:
            from sqlalchemy import select as _sa_select
            from app.models.source import DocumentSourceLine as _DSL
            _sess = self._content._session
            _rows = (await _sess.execute(
                _sa_select(_DSL.text).where(
                    _DSL.source_version_id == source_version_id,
                    _DSL.line_ref.in_(_line_refs),
                ).order_by(_DSL.seq)
            )).scalars().all()
            _real_lines = [str(t or "") for t in _rows]
        except Exception:
            return None
        if not _real_lines:
            return None
        # Parse evidence for declared_value and decode_loc.
        _evidence_list = (candidate_payload or {}).get("evidence") or []
        _span_ev = None
        for entry in _evidence_list:
            if str(entry.get("span_id") or "") == span_id:
                _span_ev = entry
                break
        dv = ""
        decode_loc = ""
        if _span_ev is not None:
            for e in (_span_ev.get("evidence") or ()):
                s = str(e)
                if s.startswith("fact_declared_value="):
                    dv = s.split("=", 1)[1]
                elif s.startswith("fact_decode_loc="):
                    decode_loc = s.split("=", 1)[1]
        _ans = answer_payload or {}
        _ans_text = str(_ans.get("text") or _ans.get("candidate_text") or "")
        if not _ans_text:
            return None
        # Content consistency gate: answer must be recoverable from real
        # source lines.  If not, refuse — never return an unknown fact that
        # a human/golden grant could later publish as official.
        from app.domains.gate.binding_fact import _value_supported_by_lines
        _check_val = dv.strip() if dv.strip() else _ans_text.strip()
        if not _value_supported_by_lines(_check_val, _real_lines):
            return None
        try:
            from app.domains.gate.binding_fact import (
                derive_binding_fact,
                verify_binding_fact,
                register_trusted_binding_fact,
            )
            fact = derive_binding_fact(
                span_id=span_id,
                source_version_id=source_version_id,
                unit_id=str(_ans.get("unit_id") or ""),
                question_number=str(_ans.get("question_number") or ""),
                source_lines=_real_lines,
                answer_text=_ans_text,
                evidence_kind=str(_ans.get("binding_evidence") or ""),
                decode_loc=decode_loc,
                declared_value=dv,
            )
            if verify_binding_fact(fact):
                try:
                    register_trusted_binding_fact(fact)
                except Exception:
                    pass
                return fact
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------ R2-FIX
    async def _update_empty_answers(
        self,
        candidate: AdmissionCandidate,
        *,
        grant: str = "none",
        review_evidence: dict | None = None,
        mark_verified: bool = True,
    ) -> None:
        """Fill empty official answers on reused instances (R2-FIX).

        When an Instance was materialized by materialize_for_review (empty
        official answer) and a later Candidate passes Gate with valid answer
        evidence, the empty answer must be fillable through the existing
        publish logic. Only updates rows where text is currently empty.
        Never overwrites non-empty official answers.
        """
        p = candidate.payload
        ir = p["ir_snapshot"]
        units = ir["units"]
        by_unit: dict[str, dict] = {u["unit_id"]: u for u in units}
        answers_by_unit: dict[str, dict] = {a["unit_id"]: a for a in p["answer"]}
        version = await self._source.get_version(candidate.source_version_id)
        if version is None:
            return

        for unit_id in _materialization_units(units):
            unit = by_unit.get(unit_id)
            if unit is None:
                continue
            qn = unit.get("question_number") or ""
            answers_list = None
            if unit.get("unit_type") == "composite_unit":
                # For composites, answers_override is used in _materialize.
                # Here we use the direct answer map.
                _one = answers_by_unit.get(unit_id)
                answers_list = [_one] if _one is not None else []
            else:
                _one = answers_by_unit.get(unit_id)
                answers_list = [_one] if _one is not None else []

            # Find existing instance for this unit
            from sqlalchemy import select as _sa_select
            from app.models.content import QuestionInstance as _QI
            _sess = self._content._session
            _qi_rows = (await _sess.execute(
                _sa_select(_QI.id).where(
                    _QI.source_version_id == candidate.source_version_id,
                )
            )).scalars().all()
            # Match by question_number in instance
            inst = None
            for iid in _qi_rows:
                _qi_row = (await _sess.execute(
                    _sa_select(_QI.question_number, _QI.question_number_range).where(_QI.id == iid)
                )).first()
                if _qi_row is None:
                    continue
                _iqn = str(_qi_row[0] or "")
                _iqnr = str(_qi_row[1] or "")
                if _iqn == str(qn) or (not _iqn and _iqnr and str(qn) in _iqnr):
                    inst = iid
                    break
            if inst is None:
                continue

            for ai, ans in enumerate(answers_list):
                if ans is None or ans.get("text") is None:
                    continue
                _fact = await self._resolve_fact_with_fallback(
                    source_version_id=str(candidate.source_version_id),
                    span_id=str(ans.get("span_id") or ""),
                    answer_payload=ans,
                    candidate_payload=candidate.payload,
                    allow_fallback=mark_verified and grant in ("human", "golden"),
                )
                _cand = (
                    ans.get("candidate_text")
                    if ans.get("candidate_text") is not None
                    else ans.get("text")
                    or ""
                )
                if _fact is None:
                    _trust_own = "unknown"
                    _fact_id = ""
                    _ans_h = ""
                else:
                    _trust_own = _fact.ownership or "unknown"
                    _fact_id = _fact.fact_id
                    _ans_h = _fact.answer_text_hash
                    _ans_unit = str(ans.get("unit_id") or "") or str(unit_id)
                    if _fact.span_id != str(ans.get("span_id") or ""):
                        _trust_own = "unknown"
                    elif _ans_unit and _fact.unit_id and _fact.unit_id != _ans_unit:
                        _trust_own = "unknown"
                    _check_qn = str(qn or "")
                    if _check_qn and _fact.question_number and _fact.question_number != _check_qn:
                        _trust_own = "unknown"
                    elif not fact_matches_answer_text(_fact, _cand):
                        _trust_own = "unknown"
                official_text, publish, write_nonempty = _publish_decision(
                    ownership=_trust_own,
                    candidate_text=_cand,
                    grant=grant,
                    review_evidence=review_evidence,
                    content_ok=bool(ans.get("complete")),
                    source_ok=bool(ans.get("source_located")),
                )
                if not write_nonempty:
                    official_text = ""
                _seal = issue_publish_seal(
                    fact=_fact,
                    official_text=official_text,
                    publish=publish,
                )
                await self._content.update_answer_text(
                    instance_id=inst,
                    text=official_text,
                    text_hash=_raw_sha256(official_text),
                    answer_status={
                        "source_located": bool(ans.get("source_located")),
                        "complete": bool(ans.get("complete")),
                        "verified_correct": True if mark_verified else ans.get("verified_correct"),
                        "ownership": _trust_own,
                        "binding_evidence": _fact.evidence_kind if _fact else "",
                        "binding_fact_id": _fact_id,
                        "binding_unit_id": _fact.unit_id if _fact else "",
                        "binding_question_number": _fact.question_number if _fact else "",
                        "answer_text_hash": _ans_h,
                        "publish_grant": grant,
                        "publish": publish,
                        "publish_seal": _seal,
                    },
                )

    # ------------------------------------------------------------------ 物化
    async def _materialize(
        self, candidate: AdmissionCandidate, *, mark_verified: bool = True,
        annotation_id: uuid.UUID | None = None,
        grant: str = "none",
        review_evidence: dict | None = None,
    ) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
        """从冻结 payload 物化 A 域（10 §6）。单事务：所有行同 session，flush 后任一步
        失败由外层不 COMMIT → 整体回滚。

        mark_verified：approved 路径 True（20 §8.3）；pending-review 物化 False
        （E2E-009R7：答案未经验证不得标 verified_correct=true）。

        复用语义（10 §6.1/§6.2 冻结）：Question dedup exact 命中 → REUSE + 仅为其新
        occurrence INSERT 新 Instance；同 (question, source_version, occurrence) 二次导出
        复用既有 Instance（其 role/link/member 已物化，不重建，防 UNIQUE 冲突）。全部
        leaf 均复用 → 无新 A 域行（approve 记录空事件，不建空 group）。
        """
        p = candidate.payload
        ir = p["ir_snapshot"]
        units = ir["units"]
        root = units[0]
        version = await self._source.get_version(candidate.source_version_id)
        if version is None:
            raise RepositoryError(
                f"source_version {candidate.source_version_id} not found"
            )
        ann = await self._snap.find_annotation_by_id(annotation_id or candidate.annotation_id)
        claims = (ann.payload or {}).get("document_metadata_claims", {}) if ann else {}
        subject = claims.get("subject")  # BUG-V3-021 终裁：claim 直接映射；缺失 → None（unknown）
        grade = claims.get("grade")

        by_unit: dict[str, dict] = {u["unit_id"]: u for u in units}
        roles_by_unit: dict[str, list[dict]] = {}
        materials_by_unit: dict[str, list[dict]] = {}
        for r in p["compiled_roles"]:
            if r.get("kind") == "material":
                materials_by_unit.setdefault(r["unit_id"], []).append(r)
                continue
            if r["kind"] != "content":
                continue
            roles_by_unit.setdefault(r["unit_id"], []).append(r)
        answers_by_unit: dict[str, dict] = {a["unit_id"]: a for a in p["answer"]}
        spans_by_id: dict[str, dict] = {s["span_id"]: s for s in p["resolved_spans"]}

        # Owner 2026-10: 复合题 = 一道综合题入库（完形/阅读/语法填空等），
        # 不再把子题拆成多条正式 Question。子题内容聚合成一条 stem/answer。
        plan: list[dict] = []
        for unit_id in _materialization_units(units):
            unit = by_unit[unit_id]
            if unit.get("unit_type") == "composite_unit":
                roles, stem, answers_extra = _aggregate_composite_roles(
                    unit, units, roles_by_unit, answers_by_unit, spans_by_id,
                    materials_by_unit=materials_by_unit,
                )
                # E2E-010: 七选五父级 A–G 在 IR content，但 compiler 未写入
                # compiled_roles —— 从 ir_snapshot 补齐到物化 roles。
                ir_by_id = {u.get("unit_id"): u for u in (p.get("ir_snapshot") or {}).get("units") or []}
                parent_ir = ir_by_id.get(unit_id) or {}
                _has_real_subs = bool(unit.get("sub_questions") or [])
                if not _has_real_subs:
                  for c in parent_ir.get("content") or []:
                    if c.get("role") != "option" or not c.get("label"):
                        continue
                    if any(r.get("role") == "option" and r.get("label") == f"P{c['label']}" for r in roles):
                        continue
                    sid = c.get("span_id")
                    span = spans_by_id.get(sid or "") or {}
                    roles.append({
                        "kind": "content",
                        "role": "option",
                        "unit_id": unit_id,
                        "label": f"P{c['label']}",
                        "text": c.get("label") or "",
                        "text_hash": span.get("text_hash") or "",
                        "span_id": sid,
                    })
                canonical = map_canonical_type(unit.get("original_question_type"))
                if canonical is None:
                    raise RepositoryError(
                        f"composite {unit_id!r} has no canonical type; cannot materialize"
                    )
                if stem is None:
                    # fall back to first content role (e.g. material-only)
                    stem = _role(roles, "stem") or _role(roles, "material")
                if stem is None:
                    raise RepositoryError(f"composite {unit_id!r} missing aggregated stem")
                span = spans_by_id.get(stem.get("span_id") or "") or {}
                qn = (
                    unit.get("question_number_range")
                    or unit.get("question_number")
                    or ""
                )
                plan.append({
                    "unit": unit,
                    "canonical": canonical,
                    "roles": roles,
                    "span": span,
                    "qn": qn,
                    "dedup_key": _dedup_key(canonical, stem, roles),
                    "occurrence_key": _occurrence_key(unit_id, qn, span),
                    "question": None,
                    "new_instance": False,
                    "answers_override": answers_extra,
                })
                continue
            canonical = map_canonical_type(unit.get("original_question_type"))
            if canonical is None:
                raise RepositoryError(
                    f"leaf unit {unit_id!r} has no canonical type; cannot materialize"
                )
            roles = roles_by_unit.get(unit_id, [])
            stem = _role(roles, "stem")
            if stem is None:
                raise RepositoryError(f"leaf unit {unit_id!r} missing compiled stem")
            span = spans_by_id.get(stem["span_id"]) or {}
            qn = unit.get("question_number") or ""
            plan.append({
                "unit": unit,
                "canonical": canonical,
                "roles": roles,
                "span": span,
                "qn": qn,
                "dedup_key": _dedup_key(canonical, stem, roles),
                "occurrence_key": _occurrence_key(unit_id, qn, span),
                "question": None,
                "new_instance": False,
                "answers_override": None,
            })

        created_questions: list[uuid.UUID] = []
        created_instances: list[uuid.UUID] = []
        any_new_instance = False
        for e in plan:
            question = await self._content.find_question_by_dedup_key(
                dedup_key=e["dedup_key"]
            )
            if question is None:
                question = await self._content.create_question(
                    subject=subject,
                    grade=grade,
                    canonical_question_type=e["canonical"],
                    dedup_key=e["dedup_key"],
                )
                created_questions.append(question.id)
                await self._content.flush()  # question.id 回填后供 instance FK
            else:
                # BUG-V3-021：复用既有 Question 收敛 metadata（NULL→known 补写；
                # known→different fail-loud），禁 first-write-wins 静默吞。
                await self._content.converge_subject_grade(
                    question, subject=subject, grade=grade
                )
            e["question"] = question
            instance = await self._content.find_instance_by_occurrence(
                question_id=question.id,
                source_version_id=candidate.source_version_id,
                occurrence_key=e["occurrence_key"],
            )
            e["existing_instance"] = instance
            e["new_instance"] = instance is None
            any_new_instance = any_new_instance or instance is None

        # WP7-C: reused instances (from materialize_for_review) must have their
        # answer_status.verified_correct updated when mark_verified=True (approve).
        # Previously the reuse path silently left verified_correct=null after
        # approve, leaving Candidate=approved but Instance showing 待审核.
        if mark_verified:
            for e in plan:
                inst = e.get("existing_instance")
                if inst is not None:
                    await self._content.update_answer_verified_correct(
                        instance_id=inst.id, verified_correct=True
                    )
            # R2-FIX: also fill empty official answers on existing instances
            # when mark_verified=True (approve path). Previously only
            # verified_correct was updated, leaving empty answers forever.
            for e in plan:
                inst = e.get("existing_instance")
                if inst is None:
                    continue
                unit = e["unit"]
                unit_id = unit["unit_id"]
                qn = e["qn"]
                answers_list = e.get("answers_override")
                if answers_list is None:
                    _one = answers_by_unit.get(unit_id)
                    answers_list = [_one] if _one is not None else []
                for ai, ans in enumerate(answers_list):
                    if ans is None or ans.get("text") is None:
                        continue
                    _fact = await self._resolve_fact_with_fallback(
                        source_version_id=str(candidate.source_version_id),
                        span_id=str(ans.get("span_id") or ""),
                        answer_payload=ans,
                        candidate_payload=candidate.payload,
                        allow_fallback=mark_verified and grant in ("human", "golden"),
                    )
                    _cand = (
                        ans.get("candidate_text")
                        if ans.get("candidate_text") is not None
                        else ans.get("text")
                        or ""
                    )
                    if _fact is None:
                        _trust_own = "unknown"
                        _fact_id = ""
                        _ans_h = ""
                    else:
                        _trust_own = _fact.ownership or "unknown"
                        _fact_id = _fact.fact_id
                        _ans_h = _fact.answer_text_hash
                        _ans_unit = str(ans.get("unit_id") or "") or str(
                            e.get("unit_id") or unit.get("unit_id") or ""
                        )
                        if _fact.span_id != str(ans.get("span_id") or ""):
                            _trust_own = "unknown"
                        elif _ans_unit and _fact.unit_id and _fact.unit_id != _ans_unit:
                            _trust_own = "unknown"
                        if e.get("answers_override") is not None:
                            _check_qn = str(ans.get("question_number") or "") or str(qn or "")
                        else:
                            _check_qn = str(qn or "")
                        if _check_qn and _fact.question_number and _fact.question_number != _check_qn:
                            _trust_own = "unknown"
                        elif not fact_matches_answer_text(_fact, _cand):
                            _trust_own = "unknown"
                    official_text, publish, write_nonempty = _publish_decision(
                        ownership=_trust_own,
                        candidate_text=_cand,
                        grant=grant,
                        review_evidence=review_evidence,
                        content_ok=bool(ans.get("complete")),
                        source_ok=bool(ans.get("source_located")),
                    )
                    if not write_nonempty:
                        official_text = ""
                    _seal = issue_publish_seal(
                        fact=_fact,
                        official_text=official_text,
                        publish=publish,
                    )
                    await self._content.update_answer_text(
                        instance_id=inst.id,
                        text=official_text,
                        text_hash=_raw_sha256(official_text),
                        answer_status={
                            "source_located": bool(ans.get("source_located")),
                            "complete": bool(ans.get("complete")),
                            "verified_correct": True,
                            "ownership": _trust_own,
                            "binding_evidence": _fact.evidence_kind if _fact else "",
                            "binding_fact_id": _fact_id,
                            "binding_unit_id": _fact.unit_id if _fact else "",
                            "binding_question_number": _fact.question_number if _fact else "",
                            "answer_text_hash": _ans_h,
                            "publish_grant": grant,
                            "publish": publish,
                            "publish_seal": _seal,
                        },
                    )

        if not any_new_instance:
            # 全量复用：candidate 的 occurrence 均已物化，无新 A 域行（不建 group）。
            # P2-MATERIAL-METADATA: 仍需收敛关联 Material 的 subject/grade。
            # R2-FIX: reuse path must also UPDATE empty official answers when
            # the current Candidate passes Gate with valid answer evidence.
            # Previously this early-returned, leaving empty answers forever.
            for e in plan:
                inst = e.get("existing_instance")
                if inst is None:
                    continue
                unit = e["unit"]
                unit_id = unit["unit_id"]
                qn = e["qn"]
                answers_list = e.get("answers_override")
                if answers_list is None:
                    _one = answers_by_unit.get(unit_id)
                    answers_list = [_one] if _one is not None else []
                for ai, ans in enumerate(answers_list):
                    if ans is None or ans.get("text") is None:
                        continue
                    _fact = await self._resolve_fact_with_fallback(
                        source_version_id=str(candidate.source_version_id),
                        span_id=str(ans.get("span_id") or ""),
                        answer_payload=ans,
                        candidate_payload=candidate.payload,
                        allow_fallback=mark_verified and grant in ("human", "golden"),
                    )
                    _cand = (
                        ans.get("candidate_text")
                        if ans.get("candidate_text") is not None
                        else ans.get("text")
                        or ""
                    )
                    if _fact is None:
                        _trust_own = "unknown"
                        _fact_id = ""
                        _ans_h = ""
                    else:
                        _trust_own = _fact.ownership or "unknown"
                        _fact_id = _fact.fact_id
                        _ans_h = _fact.answer_text_hash
                        _ans_unit = str(ans.get("unit_id") or "") or str(
                            e.get("unit_id") or unit.get("unit_id") or ""
                        )
                        if _fact.span_id != str(ans.get("span_id") or ""):
                            _trust_own = "unknown"
                        elif _ans_unit and _fact.unit_id and _fact.unit_id != _ans_unit:
                            _trust_own = "unknown"
                        if e.get("answers_override") is not None:
                            _check_qn = str(ans.get("question_number") or "") or str(qn or "")
                        else:
                            _check_qn = str(qn or "")
                        if _check_qn and _fact.question_number and _fact.question_number != _check_qn:
                            _trust_own = "unknown"
                        elif not fact_matches_answer_text(_fact, _cand):
                            _trust_own = "unknown"
                    official_text, publish, write_nonempty = _publish_decision(
                        ownership=_trust_own,
                        candidate_text=_cand,
                        grant=grant,
                        review_evidence=review_evidence,
                        content_ok=bool(ans.get("complete")),
                        source_ok=bool(ans.get("source_located")),
                    )
                    if not write_nonempty:
                        official_text = ""
                    _seal = issue_publish_seal(
                        fact=_fact,
                        official_text=official_text,
                        publish=publish,
                    )
                    await self._content.update_answer_text(
                        instance_id=inst.id,
                        text=official_text,
                        text_hash=_raw_sha256(official_text),
                        answer_status={
                            "source_located": bool(ans.get("source_located")),
                            "complete": bool(ans.get("complete")),
                            "verified_correct": True if mark_verified else ans.get("verified_correct"),
                            "ownership": _trust_own,
                            "binding_evidence": _fact.evidence_kind if _fact else "",
                            "binding_fact_id": _fact_id,
                            "binding_unit_id": _fact.unit_id if _fact else "",
                            "binding_question_number": _fact.question_number if _fact else "",
                            "answer_text_hash": _ans_h,
                            "publish_grant": grant,
                            "publish": publish,
                            "publish_seal": _seal,
                        },
                    )
            for m in p["compiled_roles"]:
                if m["kind"] != "material":
                    continue
                mdedup = identity_hash(
                    {"material_type": m["role"], "text": normalize_identity(m["text"])}
                )
                mat = await self._content.find_material_by_dedup(
                    source_version_id=candidate.source_version_id, dedup_key=mdedup
                )
                if mat is not None:
                    await self._content.converge_subject_grade(
                        mat, subject=subject, grade=grade
                    )
            return created_questions, created_instances

        # composite：shared material 只建一次（20 #4）；同 sv 重标注按 dedup 复用既有行
        # （10 §6.4 M1：source-scoped，不跨 Source Version 自动共享）。
        materials: list[tuple[object, str]] = []  # (material ORM, shared role)；flush 后读 .id
        for m in p["compiled_roles"]:
            if m["kind"] != "material":
                continue
            mdedup = identity_hash(
                {"material_type": m["role"], "text": normalize_identity(m["text"])}
            )
            mat = await self._content.find_material_by_dedup(
                source_version_id=candidate.source_version_id, dedup_key=mdedup
            )
            if mat is None:
                mat = await self._content.create_material(
                    subject=subject,
                    grade=grade,
                    source_version_id=candidate.source_version_id,
                    text=m["text"],
                    text_hash=m["text_hash"],
                    source_span={"span_id": m["span_id"]},
                    dedup_key=mdedup,
                )
            else:
                await self._content.converge_subject_grade(
                    mat, subject=subject, grade=grade
                )
            materials.append((mat, m["role"]))
        if materials:
            await self._content.flush()  # material.id 回填后供 material_link FK

        group = await self._content.create_unit_group(
            # F1（二轮对抗审查修复）：unit_type 是 A 域持久化字段，须用 candidate.unit_type
            # （service 已把 IR 值映射到 standalone_unit/composite_unit，10 §6.5 值域）；
            # 直接用 payload IR root 会把 IR 域 standalone_question 误写进展示/持久化域。
            unit_type=candidate.unit_type,
            document_id=version.document_id,
            source_version_id=candidate.source_version_id,
            question_number_range=root.get("question_number_range"),
            shared_material_id=materials[0][0].id if materials else None,
        )
        await self._content.flush()  # group.id 回填后供 instance/unit_group_member FK

        member_index = 0
        for e in plan:
            if not e["new_instance"]:
                continue  # 复用 occurrence：role/link/member 已由先前物化写入，不重建
            unit = e["unit"]
            unit_id = unit["unit_id"]
            roles = e["roles"]
            span = e["span"]
            qn = e["qn"]
            page_no, line_no = _page_line(span["span_id"], span)
            instance = await self._content.create_instance(
                question_id=e["question"].id,
                document_id=version.document_id,
                source_version_id=candidate.source_version_id,
                occurrence_key=e["occurrence_key"],
                question_number=qn,
                question_number_range=unit.get("question_number_range") or "",
                page_no=page_no,
                instance_order=_instance_order(page_no, line_no),
                unit_group_id=group.id,
                # F2（二轮对抗审查修复）：provenance「由产生它的 admission 带出」——从
                # candidate 原样继承（copy，非本层新建）。attempt_id 段 H worker 接入前
                # candidate 恒 NULL，如实继承。
                logical_execution_stage=candidate.logical_execution_stage,
                logical_execution_hash=candidate.logical_execution_hash,
                attempt_id=candidate.attempt_id,
            )
            created_instances.append(instance.id)
            await self._content.flush()  # instance.id 回填后供 role_contents/member FK

            idx: dict[str, int] = {}
            for r in roles:
                key = r["role"]
                i = idx.get(key, 0)
                idx[key] = i + 1
                await self._content.create_role_content(
                    instance_id=instance.id,
                    role=r["role"],
                    role_index=i,
                    text=r["text"],
                    text_hash=r["text_hash"],
                    label=r.get("label"),
                    # source_span 用该 role 自身 compiled line_refs（非 stem 的），防
                    # provenance 串行错位（对抗审查 MED：option 行被记成 stem 行）。
                    source_span=_source_span(r["span_id"], r),
                    answer_status=None,
                )
            answers_list = e.get("answers_override")
            if answers_list is None:
                _one = answers_by_unit.get(unit_id)
                answers_list = [_one] if _one is not None else []
            for ai, ans in enumerate(answers_list):
                if ans is None or ans.get("text") is None:
                    continue
                # P0-R12: ownership comes from the INDEPENDENT binding fact
                # (registry-backed, derived at resolve time). Transport payload
                # ownership is never a trust input.
                _fact = await self._resolve_fact_with_fallback(
                    source_version_id=str(candidate.source_version_id),
                    span_id=str(ans.get("span_id") or ""),
                    answer_payload=ans,
                    candidate_payload=candidate.payload,
                    allow_fallback=mark_verified and grant in ("human", "golden"),
                )
                _cand = (
                    ans.get("candidate_text")
                    if ans.get("candidate_text") is not None
                    else ans.get("text")
                    or ""
                )
                if _fact is None:
                    _trust_own = "unknown"
                    _fact_id = ""
                    _ans_h = ""
                else:
                    _trust_own = _fact.ownership or "unknown"
                    _fact_id = _fact.fact_id
                    _ans_h = _fact.answer_text_hash
                    # P0-R15: fact must belong to THIS unit (question identity).
                    # unit_id is the authoritative identity; question_number
                    # is auxiliary only (same qn can appear on different units).
                    # Transport-payload question_number is NOT trusted.
                    _ans_unit = str(ans.get("unit_id") or "") or str(
                        e.get("unit_id") or unit.get("unit_id") or ""
                    )
                    if _fact.span_id != str(ans.get("span_id") or ""):
                        _trust_own = "unknown"
                    elif _ans_unit and _fact.unit_id and _fact.unit_id != _ans_unit:
                        _trust_own = "unknown"
                    # P0-R15: auxiliary qn check.
                    # For composite: answer qn is from IR (child unit) → use it.
                    # For leaf: use e["qn"] (IR unit qn), NOT transport
                    # ans["question_number"] (can be forged).
                    if e.get("answers_override") is not None:
                        _check_qn = str(ans.get("question_number") or "") or str(qn or "")
                    else:
                        _check_qn = str(qn or "")
                    if _check_qn and _fact.question_number and _fact.question_number != _check_qn:
                        _trust_own = "unknown"
                    elif not fact_matches_answer_text(_fact, _cand):
                        _trust_own = "unknown"
                official_text, publish, write_nonempty = _publish_decision(
                    ownership=_trust_own,
                    candidate_text=_cand,
                    grant=grant,
                    review_evidence=review_evidence,
                    content_ok=bool(ans.get("complete")),
                    source_ok=bool(ans.get("source_located")),
                )
                if not write_nonempty:
                    official_text = ""
                _seal = issue_publish_seal(
                    fact=_fact,
                    official_text=official_text,
                    publish=publish,
                )
                await self._content.create_role_content(
                    instance_id=instance.id,
                    role="answer",
                    role_index=ai,
                    text=official_text,
                    text_hash=_raw_sha256(official_text),
                    label=ans.get("label"),
                    source_span=_source_span(ans.get("span_id"), ans),
                    answer_status={
                        "source_located": bool(ans.get("source_located")),
                        "complete": bool(ans.get("complete")),
                        # 20 §8.3: approved materialize → True.
                        # E2E-009R7: pending-review materialize keeps null.
                        "verified_correct": True if mark_verified else ans.get("verified_correct"),
                        "ownership": _trust_own,
                        "binding_evidence": _fact.evidence_kind if _fact else "",
                        "binding_fact_id": _fact_id,
                        "binding_unit_id": _fact.unit_id if _fact else "",
                        "binding_question_number": _fact.question_number if _fact else "",
                        "answer_text_hash": _ans_h,
                        "publish_grant": grant,
                        "publish": publish,
                        "publish_seal": _seal,
                        # R2: candidate_text lives ONLY in review payload,
                        # never in the official answer_status row.
                    },
                )
            for mat, mrole in materials:
                await self._content.create_material_link(
                    instance_id=instance.id, material_id=mat.id,
                    role=mrole, order=0,
                )
            await self._content.create_unit_group_member(
                unit_group_id=group.id,
                instance_id=instance.id,
                member_order=member_index,
            )
            member_index += 1
        return created_questions, created_instances


# ------------------------------------------------------------------ helpers
def _leaf_units(units: list[dict]) -> list[str]:
    """candidate 内应物化 Question 的 unit_id（D8：composite parent 不物化行）。

    只遍历 root 树（ir_snapshot.units[0]；units 顶层同时含扁平子题，防重复计数）递归。
    """
    out: list[str] = []
    seen: set[str] = set()

    def walk(u: dict) -> None:
        if u["unit_type"] == "composite_unit":
            subs = u.get("sub_questions", []) or []
            if not subs:
                if u["unit_id"] not in seen:
                    seen.add(u["unit_id"])
                    out.append(u["unit_id"])
                return
            for s in subs:
                walk(s)
        elif u["unit_id"] not in seen:
            seen.add(u["unit_id"])
            out.append(u["unit_id"])

    if units:
        walk(units[0])
    return out


def _materialization_units(units: list[dict]) -> list[str]:
    """Owner 2026-10：复合题物化为 1 条综合 Question；独立题仍逐条。

    composite root → [parent_id]（不拆子题）；standalone root → [self]。
    """
    if not units:
        return []
    root = units[0]
    if root.get("unit_type") == "composite_unit":
        return [root["unit_id"]]
    return _leaf_units(units)


def _child_unit_ids(u: dict) -> list[str]:
    out: list[str] = []

    def walk(n: dict) -> None:
        if n.get("unit_type") == "composite_unit":
            subs = n.get("sub_questions", []) or []
            if not subs:
                out.append(n["unit_id"])
                return
            for s in subs:
                walk(s)
        else:
            out.append(n["unit_id"])

    walk(u)
    return out


def _aggregate_composite_roles(
    root: dict,
    units: list[dict],
    roles_by_unit: dict[str, list[dict]],
    answers_by_unit: dict[str, dict],
    spans_by_id: dict[str, dict],
    materials_by_unit: dict[str, list[dict]] | None = None,
) -> tuple[list[dict], dict | None, list[dict]]:
    """Composite → 可验证结构（E2E-009R5）。

    - material：完整正文（resolver evidence range）
    - 每个子题 stem 独立 role 行（role_index 区分）
    - 每个选项保留标签，label=qn+字母（避免 canonical A–D 重复）
    - 每个子题答案独立 role 行，label=题号，text/span/hash 与该子题一致
    - verified_correct 不默认 True
    """
    child_ids = _child_unit_ids(root)
    roles: list[dict] = []
    answers: list[dict] = []
    stem_meta: dict | None = None

    # 1) shared material = full passage (kind=material compiled roles)
    for r in (materials_by_unit or {}).get(root["unit_id"], []):
        if r.get("text"):
            roles.append(dict(r))
    for r in roles_by_unit.get(root["unit_id"], []):
        if r.get("role") == "material":
            roles.append(dict(r))
        elif r.get("role") == "option" and r.get("text") and not child_ids:
            # Shared parent options only when no child subs carry options.
            lab = str(r.get("label") or "")
            roles.append({
                **r,
                "role": "option",
                "label": f"P{lab}" if lab else f"P{len(roles)}",
                "text": r["text"],
            })
        elif r.get("role") == "explanation" and r.get("text"):
            # R3-C: composite parent explanation (was silently dropped)
            roles.append(dict(r))

    # 2) per-child stems + options
    for cid in child_ids:
        c_stem = None
        child_qn = ""
        # Prefer stem.question_label; then unit_id suffix; never leave empty
        # when uniquifying option labels (two children must not share A–D).
        for r in roles_by_unit.get(cid, []):
            if r.get("role") == "stem":
                c_stem = r
                child_qn = str(r.get("question_number") or child_qn)
                break
        if not child_qn and ".sub" in cid:
            child_qn = cid.rsplit(".sub", 1)[-1]
        if not child_qn:
            child_qn = cid
        for r in roles_by_unit.get(cid, []):
            if r.get("role") == "stem" and r.get("text"):
                if c_stem is None:
                    c_stem = r
            elif r.get("role") == "option" and r.get("text"):
                lab = str(r.get("label") or "")
                qn = str(r.get("question_number") or child_qn)
                # unique label for identity; text keeps CONTENT only so the
                # UI does not show `41A. A. …` (E2E-009R7 double-label).
                uniq = f"{qn}{lab}" if lab else f"{qn}#{len(roles)}"
                opt_text = r["text"]
                if lab:
                    opt_text = re.sub(
                        rf"^\s*{re.escape(lab)}\s*[.．、，,]\s*", "", opt_text
                    )
                roles.append({
                    **r,
                    "role": "option",
                    "label": uniq,
                    "text": opt_text,
                })
        if c_stem is not None:
            if stem_meta is None:
                stem_meta = c_stem
            roles.append(dict(c_stem))

        ans = answers_by_unit.get(cid)
        if ans is not None and ans.get("text") is not None:
            qn = str(ans.get("question_number") or child_qn)
            answers.append({
                "role": "answer",
                "unit_id": cid,  # P0-R15: child unit_id, not parent root
                "label": qn,
                "text": ans["text"],
                "text_hash": ans.get("text_hash") or "",
                "span_id": ans.get("span_id"),
                "question_number": qn,  # P0-R15: preserve child qn
                "source_located": bool(ans.get("source_located")),
                "complete": bool(ans.get("complete")),
                # E2E-009R5: never default verified_correct to True
                "verified_correct": ans.get("verified_correct"),
            })

    # E2E-010 七选五：答案键为紧凑字母串 `FGDAE`，按子题顺序拆到各空
    if answers and len(answers) > 1:
        texts = [a.get("text", "").strip() for a in answers]
        if len(set(texts)) == 1 and re.fullmatch(r"[A-Ga-g]+", texts[0] or "") and len(texts[0]) == len(answers):
            key = texts[0]
            for i, a in enumerate(answers):
                a["text"] = key[i]
                a["label"] = a.get("label") or str(i)
        else:
            # E2E-010R1: 区间键 `19-23 DABCA …` 逐题取字母（共享整段时）
            from app.domains.resolver.resolver import decode_range_answer_key
            shared = texts[0] if len(set(texts)) == 1 else None
            if shared and any(a.get("label") for a in answers):
                new_texts = []
                ok = True
                for a in answers:
                    lab = str(a.get("label") or "")
                    rk = decode_range_answer_key(shared, lab)
                    if rk is None:
                        ok = False
                        break
                    new_texts.append(rk[2])
                if ok:
                    for a, nt in zip(answers, new_texts):
                        a["text"] = nt

    # synthetic stem header for display if we have children
    if stem_meta is not None:
        # keep first child stem meta for span provenance of the header only
        pass

    return roles, stem_meta, answers


def _role(roles: list[dict], role: str) -> dict | None:
    return next((r for r in roles if r["role"] == role), None)


def _dedup_key(canonical: str, stem: dict, roles: list[dict]) -> str:
    """Question dedup_key（20 §7.3）——与 Compiler._question_dedup_key 数学一致：选项文本
    剥 label 后再整体 normalize + canonical_options_input 排序（声明序无关，BUG-V3-019）。"""
    labeled = [
        (o["label"], normalize_identity(strip_option_label(o["text"])))
        for o in roles if o["role"] == "option" and o.get("label")
    ]
    options_input = canonical_options_input(labeled)
    return identity_hash(
        {
            "canonical_question_type": canonical,
            "stem": normalize_identity(stem["text"]),
            "options": options_input,
        }
    )


def _occurrence_key(unit_id: str, qn: str, span: dict) -> str:
    """occurrence_key（20 §7.3）——与 Compiler._occurrence_key 数学一致的重建。"""
    offsets = None
    if span.get("granularity") == "line_character":
        offsets = [span.get("start_offset"), span.get("end_offset")]
    return identity_hash(
        {
            "unit_id": unit_id,
            "question_number": qn,
            "stem_refs": span.get("line_refs", []),
            "stem_offsets": offsets,
        }
    )


def _page_line(span_id: str, span: dict) -> tuple[int, int]:
    refs = span.get("line_refs") or []
    m = _LINE_REF_PAGE_RE.match(refs[0]) if refs else None
    if m is None:
        raise RepositoryError(f"span {span_id!r} has no P{{page}}L{{line}} line_ref")
    return int(m.group(1)), int(m.group(2))


def _instance_order(page_no: int, line_no: int) -> int:
    """instance_order（D5）M1：page 主序 + line 次序的确定性数值键（不同 stem 起点 → 不同
    order，文档内可稳定排序）。算法未冻结（implementation choice，勿冒充 Frozen）。"""
    return page_no * 1000 + line_no


def _source_span(span_id: str, span: dict) -> dict:
    return {
        "span_id": span_id,
        "line_refs": span.get("line_refs", []),
        # P1-B: real unit identity for Repository cross-check (JSONB, no schema change).
        "unit_id": span.get("unit_id") or "",
    }


def _raw_sha256(s: str) -> str:
    import hashlib

    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def _publish_decision(
    *,
    ownership: str,
    candidate_text: str,
    grant: str,
    review_evidence: dict | None,
    content_ok: bool,
    source_ok: bool,
) -> tuple[str, str, bool]:
    """P0 CONTRACT-FINAL publish predicate.

    Returns (official_text, publish, write_nonempty).
    - foreign: never non-empty official.
    - unknown: only human/golden + valid review evidence (content+belongs_to).
    - match/local_proven: auto_gate|human|golden may publish.
    ownership is never rewritten here.
    """
    own = (ownership or "unknown").strip()
    grant = (grant or "none").strip()
    cand = candidate_text or ""

    def _review_ok(need_belongs_to: bool) -> bool:
        if not review_evidence:
            return False
        rid = (review_evidence.get("reviewer_id") or "").strip()
        fields = set(review_evidence.get("confirmed_fields") or [])
        if not rid or "content" not in fields:
            return False
        if need_belongs_to and "belongs_to" not in fields:
            return False
        return True

    if own == "foreign":
        return "", "withheld_review", False

    if own == "unknown":
        if grant in ("human", "golden") and _review_ok(need_belongs_to=True):
            return cand, "official", bool(cand)
        return "", "withheld_review", False

    # match / local_proven
    if grant == "auto_gate":
        if content_ok and source_ok:
            return cand, "official", bool(cand)
        return "", "withheld_review", False
    if grant in ("human", "golden") and _review_ok(need_belongs_to=False):
        return cand, "official", bool(cand)
    return "", "withheld_review", False


def _has_human_approve(review_trail: list | None) -> bool:
    if not review_trail:
        return False
    for entry in review_trail:
        if entry.get("decision") == _REVIEW_APPROVE and entry.get("verified_by") in _HUMAN_SOURCES:
            return True
    return False


# ------------------------------------------------------------------ EB-008 helpers
def _candidate_claim_id(candidate: AdmissionCandidate) -> str:
    """claim_id = candidate payload IR root unit_id（与 GateService record_validation 同源）。"""
    units = ((candidate.payload or {}).get("ir_snapshot") or {}).get("units") or []
    if not units or not units[0].get("unit_id"):
        raise RepositoryError(
            "candidate payload has no IR units; cannot resolve claim_id (EB-008)"
        )
    return units[0]["unit_id"]


def _latest_human_entry(review_trail: list | None, review_result: str) -> dict | None:
    """review_trail 中最新匹配的人工 entry（validated→approve / rejected→reject）。"""
    key = _REVIEW_APPROVE if review_result == "validated" else _REVIEW_REJECT
    if not review_trail:
        return None
    for entry in reversed(review_trail):
        if entry.get("decision") == key and entry.get("verified_by") in _HUMAN_SOURCES:
            return entry
    return None


def _parse_review_time(value: str | None) -> datetime:
    """review_trail entry time（ISO-8601）→ aware UTC datetime。

    缺失用当前 UTC（fail-safe 兜底）。naive ISO 按 UTC 解释（与 proof._to_utc_iso /
    EvidenceRepository._as_utc 同则），避免下游 aware/naive 比较 TypeError。
    """
    if not value:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
