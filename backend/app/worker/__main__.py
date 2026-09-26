"""Worker CLI（30 §2 / plan Phase 8）：run / recover / retry。

安全默认：run 无 --allow-live 时 gateway 缺省 disabled/mock（无真实外部调用）。live 模式
还需 settings.llm_gateway_mode=live + 真实 provider 接线（段 F 后 live smoke；M1 live
provider transport 未接线 → live 调用会被 gateway 拒绝并记原因）。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid

from app.ai.gateway import build_gateway
from app.ai.live_guard import add_allow_live_arg, set_allow_live
from app.ai.ocr.providers import NativeTextProvider
from app.ai.providers.mock import MockLLMProvider
from app.db.session import async_session_maker
from app.domains.task.executor import TaskExecutor
from app.domains.task.service import TaskService

# Phase I-2B mock annotation response（符合 20 §4.1-4.5 Frozen Contract）
_MOCK_ANNOTATION = json.dumps(
    {
        "document_metadata_claims": {
            "subject": "数学",
            "grade": "高一",
            "year": "2026",
            "school": "北京北师大实验中学",
        },
        "sections": [],
        "semantic_units": [
            {
                "unit_id": f"Q{i}",
                "unit_type": "standalone_unit",
                "question_number": str(i),
                "section_id": "SEC-1",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {"role": "stem", "question_label": str(i)},
                    "options": [
                        {"label": "A", "role": "option", "question_label": str(i)},
                        {"label": "B", "role": "option", "question_label": str(i)},
                        {"label": "C", "role": "option", "question_label": str(i)},
                        {"label": "D", "role": "option", "question_label": str(i)},
                    ],
                    "answer": {
                        "role": "answer",
                        "question_label": str(i),
                        "answer_zone": "answer_table",
                    },
                },
            }
            for i in range(1, 18)  # 17 questions in the test
        ],
    },
    ensure_ascii=False,
)


class AnnotationMockProvider(MockLLMProvider):
    """返回有效 annotation JSON 的 mock provider。"""

    async def complete(self, prompt: str) -> str:
        return _MOCK_ANNOTATION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.worker")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="消费 queued tasks（safe 默认 mock/disabled）")
    add_allow_live_arg(run_p)

    rec_p = sub.add_parser("recover", help="失效租约 → interrupted（Recovery ≠ Retry）")
    rec_p.add_argument("--dry-run", action="store_true", help="预览将受影响任务（默认）")
    rec_p.add_argument("--confirm", action="store_true", help="执行置 interrupted")

    ret_p = sub.add_parser("retry", help="人工 retry failed/interrupted → queued")
    ret_p.add_argument("task_id", help="task UUID")
    return parser


async def _run(args: argparse.Namespace) -> None:
    set_allow_live(args.allow_live)
    # FORMAL-E2E-ENABLEMENT-01: do NOT hardcode task_context/budget_ok here.
    # TaskExecutor authorizes the gateway from the real claimed task + budget ensure.
    gateway = build_gateway(allow_live=args.allow_live)
    # Phase I-2B：mock 模式下使用返回有效 JSON 的 provider
    if gateway.mode == "mock":
        gateway._mock = AnnotationMockProvider()
    executor = TaskExecutor(
        async_session_maker,
        llm_gateway=gateway,
        ocr_extractor=NativeTextProvider().extract,
    )
    worker_id = f"worker-{uuid.uuid4().hex[:8]}"
    processed = 0
    while await executor.run_once(worker_id=worker_id):
        processed += 1
    # Flush provider reality evidence (configured vs actual)
    try:
        from app.ai.provider_reality import default_tracker
        from pathlib import Path as _Path
        out = _Path("provider_reality.json")
        default_tracker._output_path = out
        path = default_tracker.flush()
        if path is not None:
            print(f"provider reality evidence: {path}")
    except Exception as exc:
        print(f"provider reality flush skipped: {exc}")
    print(f"processed {processed} task(s)")


async def _recover(args: argparse.Namespace) -> None:
    async with async_session_maker() as s:
        svc = TaskService(s)
        if args.confirm:
            recovered = await svc.recover(dry_run=False)
            await s.commit()
            print(f"interrupted {len(recovered)} task(s): {recovered}")
        else:
            expired = await svc.recover(dry_run=True)
            print(f"{len(expired)} task(s) would be interrupted: {expired}")


async def _retry(args: argparse.Namespace) -> None:
    async with async_session_maker() as s:
        await TaskService(s).retry(uuid.UUID(args.task_id))
        await s.commit()
        print(f"task {args.task_id} → queued")


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run":
        asyncio.run(_run(args))
    elif args.command == "recover":
        asyncio.run(_recover(args))
    elif args.command == "retry":
        asyncio.run(_retry(args))


if __name__ == "__main__":
    main()
