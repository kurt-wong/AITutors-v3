"""GateService（段 G，service.py，20 §8.2/§9）：编排 E→F→G + 幂等落 candidate。

run()：一次处理一份 annotation（source_version_id + annotation_id）。对每个 semantic_status=
ready 的 top-level unit：
1. E：SourceResolver → ResolvedRun
2. F：IRBuilder → IR；Compiler → CompiledSnapshot
3. G：payload.build() 组 candidate payload；GatePolicy.evaluate() → gate_decision
4. 计算 input_identity(5) + build_versions(8) + compile-stage logical_execution_hash
   （candidate LE 覆盖 gate_policy_version，D7）
5. 幂等：find_candidate_by_le_hash → 命中返回既有；未命中 create_admission_candidate
   （decision_status 固定 pending_review）
6. gate_decision=auto_approve → AdmissionService.approve(provenance={source: auto_gate})
   —— approve 只消费冻结 candidate snapshot，不重跑 E/F/G（监控项；admission 独立入口）
7. gate_decision=rejected → AdmissionService.reject(source=machine_gate)：确定性 Gate Policy
   直接把 decision_status 写为 terminal rejected（10 §5.2），不留 pending_review 僵尸。

incomplete top-level unit 不进 candidate（20 §8.2 / §5.2 回 Annotation），返回 skipped。
"""

from __future__ import annotations

import uuid

from app.core.hashing import logical_execution_hash, sha256_hex
from app.domains.annotation import ANNO_SCHEMA_VERSION, ANN_PROMPT_VERSION
from app.domains.compile import COMPILER_VERSION, IR_SCHEMA_VERSION
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.evidence import EvidencePromotionService, ProposerIdentity
from app.domains.gate import GATE_POLICY_VERSION
from app.domains.gate.admission import AdmissionService
from app.domains.gate.payload import build as build_payload
from app.domains.gate.policy import evaluate, partition_candidate
from app.domains.resolver import RESOLVER_VERSION
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceFigureView, SourceLineView
from app.models.snapshot import AdmissionCandidate
from app.repositories.base import RepositoryError
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

_STAGE = "compile"
_IR_TO_CANDIDATE_UNIT_TYPE = {
    "standalone_question": "standalone_unit",
    "composite_unit": "composite_unit",
}


def _annotation_identity_projection(payload: object) -> object:
    """Annotation payload → identity projection（BUG-V3-039 + OQ-1 Gate A）。

    Frozen Spec（20 §4.5:172 confidence 示例 / §8.1:568、P1-6:768）：confidence 是
    诊断元数据（annotation_meta），不作 decision 触发，因此**不得进入** canonical
    identity。

    OQ-1 Gate A（70 号）：line_refs 是 Source Binding Claim（67 号），不是 Semantic
    Identity 成分。不同 line_refs + same semantic → Semantic Identity 必须相同（A1）。
    line_refs 完整保留在 payload 存储中，仅从 identity hash 输入中剔除。

    职责严格限定：只剔除 semantic_units[] 各 unit 顶层的 `confidence` 和 `line_refs`
    两个键，其余字段（含嵌套 content）原样保留。不删 unknown fields、不过滤其它
    float——BUG-V3-005 float 红线对 semantic float 继续 fail-fast。不 mutate 入参
    （浅拷贝 unit 层）。

    三处 hash 输入（`_compile_input_domain` / `_input_identity` 的 annotation_payload_hash
    与 resolver_input_hash）全部复用本函数，避免「hash A 排除了 confidence、hash B 忘了排」
    的再次漂移。
    """
    if not isinstance(payload, dict):
        return payload
    units = payload.get("semantic_units")
    if not isinstance(units, list):
        return payload
    projected_units = [
        ({k: v for k, v in u.items() if k not in ("confidence", "line_refs")}
         if isinstance(u, dict) else u)
        for u in units
    ]
    return {**payload, "semantic_units": projected_units}


def _confidence_only_projection(payload: object) -> object:
    """仅剔除 confidence（保留 line_refs）——供 resolver_input_hash 使用。

    OQ-1 §6.2 规则 3：line_refs 进入 resolver_input_hash（Resolver 需要知道
    LLM 声称的位置才能验证）。与 _annotation_identity_projection 的区别：
    后者额外剔除 line_refs（Semantic Identity 不含 Source Binding Claim）。
    """
    if not isinstance(payload, dict):
        return payload
    units = payload.get("semantic_units")
    if not isinstance(units, list):
        return payload
    projected_units = [
        ({k: v for k, v in u.items() if k != "confidence"} if isinstance(u, dict) else u)
        for u in units
    ]
    return {**payload, "semantic_units": projected_units}


class GateService:
    def __init__(self, session) -> None:
        self._snap = SnapshotRepository(session)
        self._source = SourceRepository(session)
        self._admission = AdmissionService(session)
        # Evidence Promotion Contract Phase 1: fresh per run, not singleton.
        # Phase 1 Hardening (Medium 9 fix): per-run isolation prevents accumulation.
        self._evidence: EvidencePromotionService | None = None

    @property
    def evidence_promotion(self) -> EvidencePromotionService | None:
        """Evidence Promotion Contract Phase 1: access ValidationEvents and EvidenceReferences.

        R4: Only ValidationEvent produces Evidence Authority.
        Returns None if run() has not been called yet.
        """
        return self._evidence

    async def run(
        self,
        *,
        source_version_id: uuid.UUID,
        annotation_id: uuid.UUID,
        task_type: str = "document_ingest",
        attempt_id: uuid.UUID | None = None,
    ) -> tuple[list[AdmissionCandidate], list[str]]:
        """编排一次 admission candidate 生成。返回 (candidates, skipped_incomplete_unit_ids)。

        attempt_id：compile-stage Runtime Provenance 透传（Lock-5，仅落 Artifact，不进 LE hash）。
        """
        version = await self._source.get_version(source_version_id)
        if version is None:
            raise RepositoryError(f"source_version {source_version_id} not found")
        ann = await self._snap.find_annotation_by_id(annotation_id)
        if ann is None:
            raise RepositoryError(f"annotation {annotation_id} not found")
        if ann.status != "valid":
            raise RepositoryError(f"annotation {annotation_id} status={ann.status} (not valid)")

        lines = tuple(
            SourceLineView(
                line_ref=r.line_ref, text=r.text, seq=r.seq,
                page_no=r.page_no, line_no_in_page=r.line_no_in_page,
            )
            for r in await self._source.get_lines_by_version(source_version_id)
        )
        # BUG-V3-043：figures 必须传入 SourceResolver，否则 image reference 恒 ambiguous
        figures = tuple(
            SourceFigureView(
                figure_id=f.figure_id, page_no=f.page_no, bbox=f.bbox,
                placement=f.placement, source=f.source,
                object_key=f.object_key, figure_hash=f.figure_hash,
            )
            for f in await self._source.get_figures_by_version(source_version_id)
        )
        resolved_run = SourceResolver(
            source_version_id=source_version_id, lines=lines, figures=figures
        ).resolve(ann.payload)

        # Evidence Promotion Contract Phase 1: fresh service per run (Medium 9 fix).
        # Prevents accumulation across run() calls.
        self._evidence = EvidencePromotionService()

        # Phase 1 Hardening (High 6 fix): ProposerIdentity is "llm", not "native_parser".
        # The annotation payload was produced by an LLM. The Resolver merely verified
        # locations. The actual proposer of the semantic roles is the LLM.
        proposer = ProposerIdentity(
            producer_type="llm",
            pipeline_version=RESOLVER_VERSION,
        )
        self._evidence.create_references(resolved_run, proposer)

        ir = IRBuilder.build(resolved_run, ann.payload, source_version_id, annotation_id)
        compiled = Compiler(
            {s.span_id: s for s in resolved_run.resolved_spans},
            {l.line_ref: l for l in lines},
        ).compile(ir)

        candidates: list[AdmissionCandidate] = []
        skipped: list[str] = []
        for root in ir.units:
            if root.semantic_status != "ready":
                skipped.append(root.unit_id)  # incomplete 不进 candidate（20 §5.2）
                continue
            gate = evaluate(
                root=root, ir=ir, compiled=compiled, resolved_run=resolved_run
            )

            # Evidence Promotion Contract Phase 1: record ValidationEvent.
            # R4: Only ValidationEvent produces Evidence Authority.
            # Phase 1 Hardening (Critical 3 fix): pass reference_ids to link
            # ValidationEvent → EvidenceReference.
            span_ids = _extract_unit_span_ids(root, compiled)
            ref_ids = tuple(
                f"er-{sid}" for sid in span_ids
            )
            self._evidence.record_validation(
                root.unit_id, gate, reference_ids=ref_ids
            )

            payload = build_payload(
                root=root, ir=ir, compiled=compiled, resolved_run=resolved_run
            )
            build_versions = self._build_versions(ann)
            input_identity = self._input_identity(
                source_version_id, annotation_id, ann, resolved_run
            )
            # BUG-V3-022：compile-stage LE 用最小 identity 字段集（contract 4 + input 3），
            # 与存储列 build_versions(8)/input_identity(5) 分离；unit_id 区分多 top-level unit。
            le_hash = logical_execution_hash(
                task_type=task_type,
                stage=_STAGE,
                contract_domain=self._compile_contract_domain(),
                input_domain=self._compile_input_domain(annotation_id, ann, root.unit_id),
            )
            candidate = await self._snap.find_candidate_by_le_hash(
                logical_execution_stage=_STAGE, logical_execution_hash=le_hash
            )
            if candidate is None:
                candidate = await self._snap.create_admission_candidate(
                    unit_type=_candidate_unit_type(root.unit_type),
                    source_version_id=source_version_id,
                    annotation_id=annotation_id,
                    build_versions=build_versions,
                    input_identity=input_identity,
                    payload=payload,
                    gate_decision=gate,
                    logical_execution_stage=_STAGE,
                    logical_execution_hash=le_hash,
                    attempt_id=attempt_id,
                )
                await self._snap.flush()  # candidate.id 回填后供 approve lock
            candidates.append(candidate)

            if gate.get("decision") == "rejected":
                # 机器已判 rejected → decision_status 由确定性 Gate Policy 写入终态
                # （10 §5.2）；machine_gate 只 transition，不重写 gate_decision（P0-G-003），
                # 否则 candidate 会永久卡在 pending_review 且无法 approve（P0-G-002）。
                await self._admission.reject(
                    candidate_id=candidate.id,
                    reasons=gate.get("reasons", []),
                    source="machine_gate",
                )
            elif gate.get("decision") == "auto_approve":
                # 自动路径：approve 只消费冻结 candidate snapshot（不重跑 E/F/G）。
                await self._admission.approve(
                    candidate_id=candidate.id, provenance={"source": "auto_gate"}
                )

        await self._snap.flush()
        return candidates, skipped

    # ------------------------------------------------------------------ identity
    def _build_versions(self, ann) -> dict:
        """build_versions（10 §9）：用什么版本构建（8 项，含 gate_policy_version）。"""
        return {
            "annotation_schema_version": ann.annotation_schema_version,
            "prompt_version": ann.prompt_version,
            "model_config_hash": ann.model_config_hash,
            "resolver_version": RESOLVER_VERSION,
            "ir_schema_version": IR_SCHEMA_VERSION,
            "compiler_version": COMPILER_VERSION,
            "gate_policy_version": GATE_POLICY_VERSION,
            "source_version": str(ann.source_version_id),
        }

    @staticmethod
    def _compile_contract_domain() -> dict:
        """compile LE contract_domain（30 §16 / BUG-V3-022）：4 项相关 build_versions 子集。

        不含 annotation_schema_version / prompt_version / model_config_hash / source_version
        ——compile 为确定性阶段，ann 契约经 payload hash 间接反映；model_config 明文禁用。
        """
        return {
            "resolver_version": RESOLVER_VERSION,
            "ir_schema_version": IR_SCHEMA_VERSION,
            "compiler_version": COMPILER_VERSION,
            "gate_policy_version": GATE_POLICY_VERSION,
        }

    @staticmethod
    def _compile_input_domain(annotation_id: uuid.UUID, ann, unit_id: str) -> dict:
        """compile LE input_domain（30 §16 / BUG-V3-022）：3 项（含 unit_id 多 unit 区分）。

        不含 source_version_id / resolver_input_hash / compiler_input_hash——它们是存储列
        （input_identity）派生指纹，annotation_payload_hash 已唯一决定 resolved/compiled
        结果；重复纳入会漂移 execution identity。

        hash 输入经 _annotation_identity_projection（BUG-V3-039）：诊断元数据 confidence
        不进 identity。
        """
        return {
            "annotation_id": str(annotation_id),
            "annotation_payload_hash": sha256_hex(
                _annotation_identity_projection(ann.payload)
            ),
            "unit_id": unit_id,
        }

    def _input_identity(self, sv: uuid.UUID, ann_id: uuid.UUID, ann, resolved_run) -> dict:
        """input_identity（10 §9 / BUG-V3-022 M1 + OQ-1 Gate A）：对什么输入构建。

        annotation_payload_hash 经 _annotation_identity_projection（剔除 confidence +
        line_refs）——Semantic Identity，不含 Source Binding Claim。

        resolver_input_hash 仅剔除 confidence（保留 line_refs）——Resolver 需要知道
        LLM 声称的位置才能验证（OQ-1 §6.2 规则 3）。
        """
        resolved_summary = sorted(
            [
                [s.role, s.span_id, s.text_hash, s.resolution_status]
                for s in resolved_run.resolved_spans
            ],
            key=lambda t: t[1],
        )
        projected = _annotation_identity_projection(ann.payload)
        # resolver_input_hash 保留 line_refs：Resolver 验证需要知道声明位置
        resolver_payload = _confidence_only_projection(ann.payload)
        return {
            "source_version_id": str(sv),
            "annotation_id": str(ann_id),
            "annotation_payload_hash": sha256_hex(projected),
            "resolver_input_hash": sha256_hex(
                {"annotation_payload": resolver_payload, "source_version_id": str(sv)}
            ),
            "compiler_input_hash": sha256_hex({"resolved_spans": resolved_summary}),
        }


def _candidate_unit_type(ir_unit_type: str) -> str:
    return _IR_TO_CANDIDATE_UNIT_TYPE.get(ir_unit_type, ir_unit_type)


def _extract_unit_span_ids(root, compiled) -> tuple[str, ...]:
    """Extract span_ids consumed by a root unit from CompiledSnapshot.

    Phase 1 Hardening (Critical 3 fix): Enables linking ValidationEvent to
    EvidenceReference via reference_ids. Traverses the compiled leaves and
    materials for this unit to collect all consumed span_ids.
    """
    from app.domains.gate.policy import partition_candidate

    leaves, materials = partition_candidate(root, compiled)
    span_ids: set[str] = set()

    for leaf in leaves:
        if leaf.stem is not None:
            span_ids.add(leaf.stem.span_id)
        for opt in leaf.options:
            span_ids.add(opt.span_id)
        if leaf.explanation is not None:
            span_ids.add(leaf.explanation.span_id)
        if leaf.answer is not None:
            span_ids.add(leaf.answer.span_id)

    for mat in materials:
        span_ids.add(mat.span_id)

    return tuple(sorted(span_ids))
