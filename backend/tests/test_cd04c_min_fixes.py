# -*- coding: utf-8 -*-
"""04-C-R1 最小修复回归（DSH 退回项）。

- BP-A：多段合并答案的恢复性（分段全证；consistent 不算）
- BP-B：完整答案窗 + foreign 不救援
- BP-E：update_answer_text 行选择（复合 6 行只更新 1 行）
- F2/P0-14：display_note 学生可读化（内部裁决语言不出学生 API）
"""
import hashlib
import uuid

import pytest


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


SVID = "22222222-2222-2222-2222-222222222222"


async def _seed_sv(session, lines):
    from app.models.source import Document, DocumentSourceLine, DocumentSourceVersion

    doc = Document(
        id=uuid.uuid4(),
        original_object_key=f"obj/{uuid.uuid4()}.md",
        original_sha256=_sha(str(uuid.uuid4())),
        file_name="t.md", file_type="md", upload_meta={}, processing_status="sealed",
    )
    session.add(doc)
    await session.flush()
    sv = DocumentSourceVersion(
        id=uuid.UUID(SVID), document_id=doc.id,
        artifact_kind="raw_l1", role="native", provider="native",
        body_text="\n".join(lines), body_hash=_sha("\n".join(lines)),
        integrity_hash=_sha("\n".join(lines)),
        page_count=1, line_count=len(lines), status="sealed",
    )
    session.add(sv)
    await session.flush()
    for i, text in enumerate(lines, 1):
        session.add(DocumentSourceLine(
            source_version_id=uuid.UUID(SVID),
            line_ref=f"P1L{i:03d}", seq=i, page_no=1, line_no_in_page=i,
            text=text, block_type="text", line_hash=_sha(text),
        ))
    await session.flush()
    return doc, sv


# ============================= BP-A：分段全证 =============================
class TestValueRecoverableInBlock:
    def test_multi_segment_packed_answer_recovers(self):
        """Q8 子问 2 形态：段(2)+(3) 空格打包；源条目带 (N) 标记。"""
        from app.domains.source.answer_segment_verify import value_recoverable_in_block

        block = "【答案】 (1). 加快反应 (2). Fe2+ (3). VO+ +MnO2 (4). Mn2+"
        assert value_recoverable_in_block("Fe2+ VO+ +MnO2", block) is True

    def test_four_segment_packed_answer_recovers(self):
        """Q9 子问 5 形态：段(5)-(8) 四段合并。"""
        from app.domains.source.answer_segment_verify import value_recoverable_in_block

        block = "(1)烧杯 (2)KCl (3)石墨 (4)0.09 (5)Fe3+ (6)Fe-2e- (7)Fe3+2 (8)Fe"
        val = "Fe3+ Fe-2e- Fe3+2 Fe"
        assert value_recoverable_in_block(val, block) is True

    def test_allowed_labels_block_cross_sub(self):
        """收窄：命中条目不在 span 自身行窗条目号内 → 拒（防跨子问错位）。"""
        from app.domains.source.answer_segment_verify import value_recoverable_in_block

        block = "(1)AAA (2)BBB (3)CCC (4)DDD (5)EEE (6)FFF"
        # 子问 5 的答案文本，但 allowed=子问 2 行窗条目 {1,2,3,4} → 拒
        assert value_recoverable_in_block("EEE", block, allowed_labels={"1", "2", "3", "4"}) is False
        assert value_recoverable_in_block("EEE", block, allowed_labels={"5", "6"}) is True

    def test_garbage_answer_rejected(self):
        from app.domains.source.answer_segment_verify import value_recoverable_in_block

        block = "(1)AAA (2)BBB"
        assert value_recoverable_in_block("完全不同XYZ", block) is False

    def test_consistent_subset_not_enough(self):
        """压缩/子集一致（consistent）不足以证归属 → 拒。"""
        from app.domains.source.answer_segment_verify import value_recoverable_in_block

        block = "(1)升高温度加快酸浸和氧化反应速率"
        # 声明只含源条目内容串的子集（压缩/子集形态）→ consistent ≠ verified → 拒
        assert value_recoverable_in_block("升高温度", block) is False

    def test_or_alternative_form_recovers(self):
        """R11 备选（或）形态：声明与源同备选 → verified。"""
        from app.domains.source.answer_segment_verify import value_recoverable_in_block

        block = "(1)NaAlO2或Na[Al(OH)4]"
        assert value_recoverable_in_block("NaAlO2或Na[Al(OH)4]", block) is True

    def test_empty_inputs_rejected(self):
        from app.domains.source.answer_segment_verify import value_recoverable_in_block

        assert value_recoverable_in_block("", "(1)A") is False
        assert value_recoverable_in_block("A", "") is False


# ============================= BP-A/B：fallback DB =============================
class TestFallbackMultiSegAndWindow:
    async def test_multiseg_packed_answer_fallback_match(self, session):
        """多段打包子问答案 → fallback 重建 ownership=match（BP-A 修复）。"""
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry

        get_registry().clear()
        await _seed_sv(session, ["【答案】 (1). AAA (2). Fe2+ (3). VO+ +MnO2"])
        payload = {
            "ir_snapshot": {"units": [{"unit_id": "Q1", "question_number": "1"}]},
            "resolved_spans": [
                {"span_id": "sp.sub1", "line_refs": ["P1L001"]},
                {"span_id": "sp.sub2", "line_refs": ["P1L001"]},
            ],
            "answer": [
                {"text": "AAA", "unit_id": "Q1.sub1", "question_number": "1",
                 "span_id": "sp.sub1", "line_refs": ["P1L001"]},
                {"text": "Fe2+ VO+ +MnO2", "unit_id": "Q1.sub2", "question_number": "2",
                 "span_id": "sp.sub2", "line_refs": ["P1L001"]},
            ],
        }
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp.sub2",
            answer_payload=payload["answer"][1],
            candidate_payload=payload, allow_fallback=True,
        )
        assert r is not None, "多段打包答案必须可重建"
        assert r.ownership == "match", f"expected match, got {r.ownership}"
        assert r.question_number == "2"

    async def test_cross_line_entry_window_no_foreign(self, session):
        """BP-B：答案行在 P1L002（条目 (5)-(8)），子问号 4 不在该行条目集——
        完整答案窗（含 P1L001 的 (1)-(4)）后不得再误判 foreign。"""
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry

        get_registry().clear()
        await _seed_sv(session, [
            "【答案】 (1). AAA (2). BBB (3). CCC (4). Mn2+",
            "(5). EEE (6). Fe(OH)3 (7). GGG (8). HHH",
        ])
        payload = {
            "ir_snapshot": {"units": [{"unit_id": "Q1", "question_number": "8"}]},
            "resolved_spans": [
                {"span_id": "sp.sub3", "line_refs": ["P1L001", "P1L002"]},
                {"span_id": "sp.sub4", "line_refs": ["P1L002"]},
                {"span_id": "sp.sub5", "line_refs": ["P1L002"]},
                {"span_id": "sp.sub6", "line_refs": ["P1L002"]},
            ],
            "answer": [
                {"text": "Mn2+", "unit_id": "Q1.sub3", "question_number": "3",
                 "span_id": "sp.sub3", "line_refs": ["P1L001", "P1L002"]},
                {"text": "Fe(OH)3", "unit_id": "Q1.sub4", "question_number": "4",
                 "span_id": "sp.sub4", "line_refs": ["P1L002"]},
                {"text": "EEE", "unit_id": "Q1.sub5", "question_number": "5",
                 "span_id": "sp.sub5", "line_refs": ["P1L002"]},
                {"text": "HHH", "unit_id": "Q1.sub6", "question_number": "6",
                 "span_id": "sp.sub6", "line_refs": ["P1L002"]},
            ],
        }
        svc = AdmissionService(session)
        for ans in payload["answer"]:
            r = await svc._resolve_fact_with_fallback(
                source_version_id=SVID, span_id=str(ans["span_id"]),
                answer_payload=ans, candidate_payload=payload, allow_fallback=True,
            )
            assert r is not None, f"{ans['span_id']} 必须可重建"
            assert r.ownership == "match", (
                f"{ans['span_id']} 期望 match（完整答案窗修复），得到 {r.ownership}"
            )

    async def test_foreign_not_rescued_by_dual_qn(self, session):
        """BP-B 反例：条目集只含 (5)-(8)、子问号 1、文本属该块——分类为
        foreign 时双试父题号也**不得**救援为 match（foreign 永不可发布）。"""
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry

        get_registry().clear()
        await _seed_sv(session, [
            "(5). EEE (6). FFF (7). GGG (8). HHH",
        ])
        payload = {
            "ir_snapshot": {"units": [{"unit_id": "Q1", "question_number": "1"}]},
            "resolved_spans": [{"span_id": "sp.a1", "line_refs": ["P1L001"]}],
            "answer": [
                {"text": "EEE", "unit_id": "Q1.sub1", "question_number": "1",
                 "span_id": "sp.a1", "line_refs": ["P1L001"]},
            ],
        }
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp.a1",
            answer_payload=payload["answer"][0],
            candidate_payload=payload, allow_fallback=True,
        )
        # 文本可恢复（content gate 过）但条目号不认 1 → foreign；不得被救成 match
        assert r is not None
        assert r.ownership == "foreign", f"foreign 必须保持，得到 {r.ownership}"

    async def test_garbage_text_still_rejected(self, session):
        """BP-A 反例：源块恢复不了的答案文本 → 拒（None），不得重建 fact。"""
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry

        get_registry().clear()
        await _seed_sv(session, ["【答案】 (1). AAA (2). BBB"])
        payload = {
            "ir_snapshot": {"units": [{"unit_id": "Q1", "question_number": "1"}]},
            "resolved_spans": [{"span_id": "sp.a1", "line_refs": ["P1L001"]}],
            "answer": [
                {"text": "伪造的答案XYZ", "unit_id": "Q1.sub1", "question_number": "1",
                 "span_id": "sp.a1", "line_refs": ["P1L001"]},
            ],
        }
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp.a1",
            answer_payload=payload["answer"][0],
            candidate_payload=payload, allow_fallback=True,
        )
        assert r is None


# ============================= BP-E：行选择 =============================
class TestUpdateAnswerTextRowSelection:
    async def test_updates_only_target_row_in_composite(self, session):
        """复合多答案行：一次调用只更新 span_id 匹配的 1 行，其余行保持原样。"""
        from app.domains.gate.binding_fact import (
            derive_binding_fact,
            get_registry,
            register_trusted_binding_fact,
        )
        from app.models.content import (
            InstanceRoleContent,
            Question,
            QuestionInstance,
        )
        from app.repositories.content_repository import ContentRepository

        get_registry().clear()
        doc, sv = await _seed_sv(session, ["【答案】 (1). AAA (2). BBB (3). CCC"])
        q = Question(
            id=uuid.uuid4(), subject=None, grade=None,
            canonical_question_type="short_answer",
            dedup_key=f"t-{uuid.uuid4()}",
        )
        session.add(q)
        await session.flush()
        inst = QuestionInstance(
            id=uuid.uuid4(), question_id=q.id, document_id=doc.id,
            source_version_id=sv.id,
            occurrence_key=f"occ-{uuid.uuid4()}",
            question_number="8", question_number_range="8",
            instance_order=1, page_no=1,
        )
        session.add(inst)
        await session.flush()
        for n in ("1", "2", "3"):
            session.add(InstanceRoleContent(
                instance_id=inst.id, role="answer", label=n,
                role_index=int(n), text="", text_hash=_sha(""),
                source_span={"span_id": f"imp:Q1:sub{n}:answer", "line_refs": ["P1L001"]},
                answer_status={"ownership": "match", "publish": "withheld_review"},
            ))
        await session.flush()

        # 只为子问 2 注册可信 fact（其余 span 无 fact——正好证明不会误写）
        from app.domains.gate.publish_seal import issue_publish_seal

        fact = derive_binding_fact(
            span_id="imp:Q1:sub2:answer", source_version_id=SVID,
            unit_id="Q1.sub2", question_number="2",
            source_lines=["【答案】 (1). AAA (2). BBB (3). CCC"],
            answer_text="BBB", declared_value="",
        )
        register_trusted_binding_fact(fact)
        seal = issue_publish_seal(fact=fact, official_text="BBB", publish="official")

        repo = ContentRepository(session)
        updated = await repo.update_answer_text(
            instance_id=inst.id,
            text="BBB",
            text_hash=_sha("BBB"),
            answer_status={
                "ownership": "match", "publish": "official",
                "binding_fact_id": fact.fact_id, "binding_unit_id": fact.unit_id,
                "binding_question_number": fact.question_number,
                "answer_text_hash": fact.answer_text_hash,
                "publish_grant": "human", "publish_seal": seal,
            },
            span_id="imp:Q1:sub2:answer",
        )
        await session.flush()
        from sqlalchemy import select as _sa_select

        rows = {}
        for r in (
            await session.execute(
                _sa_select(InstanceRoleContent).where(
                    InstanceRoleContent.instance_id == inst.id,
                    InstanceRoleContent.role == "answer",
                )
            )
        ).scalars():
            rows[r.label] = r.text or ""
        assert updated is True
        assert rows == {"1": "", "2": "BBB", "3": ""}, (
            f"复合 6/3 行必须只更新目标行，得到 {rows}"
        )

    async def test_no_target_row_no_write(self, session):
        """span_id 不匹配任何行 → 不写任何行（返回 False）。"""
        from app.models.content import InstanceRoleContent, Question, QuestionInstance
        from app.repositories.content_repository import ContentRepository

        doc, sv = await _seed_sv(session, ["x"])
        q = Question(
            id=uuid.uuid4(), subject=None, grade=None,
            canonical_question_type="short_answer", dedup_key=f"t-{uuid.uuid4()}",
        )
        session.add(q)
        await session.flush()
        inst = QuestionInstance(
            id=uuid.uuid4(), question_id=q.id, document_id=doc.id,
            source_version_id=sv.id,
            occurrence_key=f"occ-{uuid.uuid4()}",
            question_number="8", question_number_range="8",
            instance_order=1, page_no=1,
        )
        session.add(inst)
        await session.flush()
        session.add(InstanceRoleContent(
            instance_id=inst.id, role="answer", label="1",
            role_index=1, text="", text_hash=_sha(""),
            source_span={"span_id": "imp:Q1:sub1:answer"},
        ))
        await session.flush()
        repo = ContentRepository(session)
        updated = await repo.update_answer_text(
            instance_id=inst.id, text="AAA", text_hash=_sha("AAA"),
            answer_status={"ownership": "match", "publish": "official"},
            span_id="imp:Q1:NOPE",
        )
        await session.flush()
        assert updated is False


# ============================= F2/P0-14：学生文案 =============================
class TestStudentDisplayNoteText:
    def test_q9_note_studentized(self):
        from app.api.routers.student_questions import _student_display_note_text

        raw = (
            "原文如此；题目区作 0.110 mol·L⁻¹（题干区 0.110 / 答案解析区 0.10 "
            "为源 Word 母本自带差异，按 Owner 裁定方案 b 原样保留）"
        )
        out = _student_display_note_text(raw, label="q9_concentration_original")
        # 04-C-R3 Owner 内容裁定：0.110=源笔误、以 0.10 为准——学生文案反映裁定
        assert out == (
            "题目区 0.110 mol·L⁻¹ 为源文件笔误，应以 0.10 mol·L⁻¹ 为准（答案区可证）"
        )
        assert "Owner" not in out and "裁定" not in out and "Word" not in out
        assert "0.110" in out and "0.10" in out

    def test_clean_text_untouched(self):
        from app.api.routers.student_questions import _student_display_note_text

        assert _student_display_note_text("原文如此；题目区作 0.110 mol·L⁻¹") == (
            "原文如此；题目区作 0.110 mol·L⁻¹"
        )

    def test_internal_only_fallback_safe(self):
        from app.api.routers.student_questions import _student_display_note_text

        out = _student_display_note_text("（按 Owner 裁定方案 b 原样保留）")
        assert "Owner" not in out and "裁定" not in out
        assert out.strip(), "必须输出安全文案而非空串"

    def test_marker_leak_impossible(self):
        from app.api.routers.student_questions import (
            _has_internal_marker,
            _student_display_note_text,
        )

        for raw in (
            "X（内部审查记录）",
            "Y（按 Owner 裁定方案 b 原样保留）",
            "Z（来源：Manifest v1 内部）",
            "全文含 candidate 残留（候选 payload）",
        ):
            assert _has_internal_marker(_student_display_note_text(raw)) is False


# ============================= S5 组级解析回归（04-C-R3 修订单） =============================
class TestS5GroupExplanationFix:
    """【分析】正文与【点睛】必须归组级解析；子问解析=【详解】条目段。"""

    @pytest.fixture(scope="class")
    def adapted(self):
        import json as _json
        from pathlib import Path as _P

        from app.domains.source.short_answer_composite import (
            build_adapter_unit_payload,
        )

        man = _json.loads(
            _P(
                r"D:\Project\Papers\tests\CORE_DELIVERY_QUESTION_QUALITY"
                r"\run_20261102_143000\03_FIXED\input\高考真题\化学"
                r"\2020全国I卷高考真题化学（教师版）(1).manifest.json"
            ).read_text(encoding="utf-8")
        )
        src_lines = _P(str(man["source_file"])).read_text(encoding="utf-8").splitlines()
        out = {}
        for u in man["units"]:
            if u["unit_id"] in ("Q8", "Q9"):
                out[u["unit_id"]] = build_adapter_unit_payload(
                    u, src_lines, image_assets=man.get("image_assets") or []
                )
        return out

    def test_q9_analyze_body_in_group(self, adapted):
        g = adapted["Q9"]["group_explanation"]
        assert "根据物质的量浓度溶液的配制步骤选择所用仪器" in g
        assert "根据题给信息选择合适的物质" in g
        assert "根据刻蚀活化的原理分析作答" in g

    def test_q9_dianjing_in_group_not_sub6(self, adapted):
        g = adapted["Q9"]["group_explanation"]
        assert "【点睛】" in g and "本题的难点" in g
        subs = [
            r for r in adapted["Q9"]["compiled_roles"]
            if r.get("role") == "explanation" and r.get("label") == "6"
        ]
        assert subs, "子问 6 解析必须存在"
        assert "【点睛】" not in (subs[0].get("text") or "")

    def test_q9_sub_explanations_six(self, adapted):
        segs = [
            r for r in adapted["Q9"]["compiled_roles"]
            if r.get("role") == "explanation" and r.get("label")
        ]
        assert [r["label"] for r in segs] == ["1", "2", "3", "4", "5", "6"]
        assert all((r.get("text") or "").strip() for r in segs)

    def test_q8_group_unchanged(self, adapted):
        g = adapted["Q8"]["group_explanation"]
        assert "【分析】" in g and "黏土钒矿中" in g and "【点睛】" in g
