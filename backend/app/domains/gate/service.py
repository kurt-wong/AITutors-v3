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
from app.domains.gate import GATE_POLICY_VERSION
from app.domains.gate.admission import AdmissionService
from app.domains.gate.payload import build as build_payload
from app.domains.gate.policy import evaluate
from app.domains.resolver import RESOLVER_VERSION
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.models.snapshot import AdmissionCandidate
from app.repositories.base import RepositoryError
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

_STAGE = "compile"
_IR_TO_CANDIDATE_UNIT_TYPE = {
    "standalone_question": "standalone_unit",
    "composite_unit": "composite_unit",
}


class GateService:
    def __init__(self, session) -> None:
        self._snap = SnapshotRepository(session)
        self._source = SourceRepository(session)
        self._admission = AdmissionService(session)

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
        resolved_run = SourceResolver(
            source_version_id=source_version_id, lines=lines
        ).resolve(ann.payload)
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
        """
        return {
            "annotation_id": str(annotation_id),
            "annotation_payload_hash": sha256_hex(ann.payload),
            "unit_id": unit_id,
        }

    def _input_identity(self, sv: uuid.UUID, ann_id: uuid.UUID, ann, resolved_run) -> dict:
        """input_identity（10 §9 / BUG-V3-022 M1）：对什么输入构建。"""
        resolved_summary = sorted(
            [
                [s.role, s.span_id, s.text_hash, s.resolution_status]
                for s in resolved_run.resolved_spans
            ],
            key=lambda t: t[1],
        )
        return {
            "source_version_id": str(sv),
            "annotation_id": str(ann_id),
            "annotation_payload_hash": sha256_hex(ann.payload),
            "resolver_input_hash": sha256_hex(
                {"annotation_payload": ann.payload, "source_version_id": str(sv)}
            ),
            "compiler_input_hash": sha256_hex({"resolved_spans": resolved_summary}),
        }


def _candidate_unit_type(ir_unit_type: str) -> str:
    return _IR_TO_CANDIDATE_UNIT_TYPE.get(ir_unit_type, ir_unit_type)
