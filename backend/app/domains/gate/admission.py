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
    ) -> AdmissionCandidate:
        """唯一 approved 入口：物化事务（10 §5.4）。

        provenance：{source: "auto_gate" | "human" | "golden", reviewer_id?, confirmed_fields?}。
        自动路径要求 gate_decision.decision == auto_approve；人工路径要求 review_trail 已
        有人工 approve 确认（20 §8.2）。已 approved → no-op 返回既有（防双物化）。
        """
        source = provenance.get("source")
        candidate = await self._snap.lock_candidate(candidate_id)
        if candidate.decision_status == "approved":
            return candidate  # 防双物化：重复 approve no-op
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

        created_questions, created_instances = await self._materialize(candidate)

        await self._snap.create_admission_event(
            candidate_id=candidate.id,
            created_question_ids=created_questions,
            created_instance_ids=created_instances,
        )
        decided = await self._snap._transition_decision(candidate.id, "approved")
        return decided

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

    # ------------------------------------------------------------------ 物化
    async def _materialize(
        self, candidate: AdmissionCandidate
    ) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
        """从冻结 payload 物化 A 域（10 §6）。单事务：所有行同 session，flush 后任一步
        失败由外层不 COMMIT → 整体回滚。

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
        ann = await self._snap.find_annotation_by_id(candidate.annotation_id)
        claims = (ann.payload or {}).get("document_metadata_claims", {}) if ann else {}
        subject = claims.get("subject")  # BUG-V3-021 终裁：claim 直接映射；缺失 → None（unknown）
        grade = claims.get("grade")

        by_unit: dict[str, dict] = {u["unit_id"]: u for u in units}
        roles_by_unit: dict[str, list[dict]] = {}
        for r in p["compiled_roles"]:
            if r["kind"] != "content":
                continue
            roles_by_unit.setdefault(r["unit_id"], []).append(r)
        answers_by_unit: dict[str, dict] = {a["unit_id"]: a for a in p["answer"]}
        spans_by_id: dict[str, dict] = {s["span_id"]: s for s in p["resolved_spans"]}

        # 逐 leaf 计划：identity 键 + 该 occurrence 是否已物化（复用 → 不重建子行）。
        plan: list[dict] = []
        for unit_id in _leaf_units(units):  # D8：parent composite 不物化独立行
            unit = by_unit[unit_id]
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
            e["new_instance"] = instance is None
            any_new_instance = any_new_instance or instance is None

        if not any_new_instance:
            # 全量复用：candidate 的 occurrence 均已物化，无新 A 域行（不建 group）。
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
            ans = answers_by_unit.get(unit_id)
            if ans is not None:
                await self._content.create_role_content(
                    instance_id=instance.id,
                    role="answer",
                    role_index=0,
                    text=ans["text"],
                    text_hash=ans["text_hash"],
                    label=None,
                    source_span=_source_span(ans["span_id"], ans),
                    answer_status={
                        "source_located": ans["source_located"],
                        "complete": ans["complete"],
                        # approved 必经 auto 或人工确认（20 §8.3）；payload 冻结 verified 保持
                        # 原值，物化侧以 approved 语义置 true（来源记 gate_decision / review）。
                        "verified_correct": True,
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
            for s in u.get("sub_questions", []):
                walk(s)
        elif u["unit_id"] not in seen:
            seen.add(u["unit_id"])
            out.append(u["unit_id"])

    if units:
        walk(units[0])
    return out


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
    return {"span_id": span_id, "line_refs": span.get("line_refs", [])}


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
    """review_trail entry time（ISO-8601）→ datetime；缺失用当前 UTC（fail-safe 兜底）。"""
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value)
