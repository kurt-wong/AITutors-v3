"""Worker CLI（30 §2 / plan Phase 8）：run / recover / retry。

安全默认：run 无 --allow-live 时 gateway 缺省 disabled/mock（无真实外部调用）。live 模式
还需 settings.llm_gateway_mode=live + 真实 provider 接线（段 F 后 live smoke；M1 live
provider transport 未接线 → live 调用会被 gateway 拒绝并记原因）。
"""

from __future__ import annotations

import argparse
import asyncio
import uuid

from app.ai.gateway import build_gateway
from app.ai.live_guard import add_allow_live_arg, set_allow_live
from app.ai.ocr.providers import NativeTextProvider
from app.db.session import async_session_maker
from app.domains.task.executor import TaskExecutor
from app.domains.task.service import TaskService


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
    gateway = build_gateway(allow_live=args.allow_live)
    executor = TaskExecutor(
        async_session_maker,
        llm_gateway=gateway,
        ocr_extractor=NativeTextProvider().extract,
    )
    worker_id = f"worker-{uuid.uuid4().hex[:8]}"
    processed = 0
    while await executor.run_once(worker_id=worker_id):
        processed += 1
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
