"""Live 授权边界：`--allow-live`（人类授权）为 live 组合放行前置之一（30 §6）。"""

import argparse
from contextvars import ContextVar

from app.core.errors import GatewayDeniedError

_allow_live: ContextVar[bool] = ContextVar("allow_live", default=False)


def add_allow_live_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--allow-live",
        action="store_true",
        help="显式授权 live external 调用（缺省拒绝，30 §6 组合放行）",
    )


def set_allow_live(value: bool) -> None:
    _allow_live.set(value)


def require_allow_live(allow_live: bool | None = None) -> None:
    """live 放行前置：无 --allow-live 即拒绝并记原因。"""
    value = _allow_live.get() if allow_live is None else allow_live
    if not value:
        raise GatewayDeniedError(
            "live external call denied: --allow-live not granted (30 §6)"
        )
