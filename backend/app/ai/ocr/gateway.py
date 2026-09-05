"""OCR Gateway（段 B，30 §6）：external OCR 唯一收敛链，三态 disabled/mock/live。

live 为组合放行（与 LLMGateway 同构）：live mode + `--allow-live` + task context +
budget 可用。SealService 只依赖本 gateway `extract()`；cloud OCR 的 audit/budget 由
本 gateway（external 层）在段 H task 驱动后统一接管——段 B SealService 不操作
audit/budget、不直调 CloudOCRProvider（P0 边界以结构保证）。
"""

from __future__ import annotations

from app.ai.live_guard import require_allow_live
from app.core.config import settings
from app.core.errors import GatewayDeniedError, GatewayDisabledError


class OCRGateway:
    """三态：disabled（默认，调用即抛）/ mock（测试）/ live（四前置组合放行）。"""

    def __init__(
        self,
        mode: str,
        *,
        allow_live: bool = False,
        task_context: object | None = None,
        budget_ok: bool = False,
        mock_provider: object | None = None,
        live_provider: object | None = None,
    ) -> None:
        self.mode = mode
        self._allow_live = allow_live
        self._task_context = task_context
        self._budget_ok = budget_ok
        self._mock_provider = mock_provider
        self._live_provider = live_provider

    async def extract(self, file_bytes: bytes):
        if self.mode == "disabled":
            # 不构造 HTTP client / 不调用 CloudOCRProvider / 无网络副作用（Gate B6）
            raise GatewayDisabledError("OCR gateway is disabled (30 §6)")
        if self.mode == "mock":
            if self._mock_provider is None:
                raise GatewayDisabledError("mock OCR provider not configured")
            return await self._mock_provider.extract(file_bytes)
        if self.mode == "live":
            return await self._live(file_bytes)
        raise GatewayDisabledError(f"unknown gateway mode: {self.mode}")

    async def _live(self, file_bytes: bytes):
        reasons: list[str] = []
        if not self._allow_live:
            reasons.append("--allow-live not granted")
        if self._task_context is None:
            reasons.append("task context missing")
        if not self._budget_ok:
            reasons.append("budget unavailable")
        if self._live_provider is None:
            reasons.append("no live OCR provider configured")
        if reasons:
            raise GatewayDeniedError("live denied: " + "; ".join(reasons))
        require_allow_live(self._allow_live)
        return await self._live_provider.extract(file_bytes)


def build_ocr_gateway() -> OCRGateway:
    """从配置建 OCRGateway：disabled/mock 不构造 live CloudOCRProvider（段 B 零 external）。"""
    mode = settings.ocr_gateway_mode
    if mode == "live":
        from app.ai.ocr.providers import CloudOCRProvider

        token = settings.paddleocr_vl_token
        live_provider = None
        if token:
            live_provider = CloudOCRProvider(
                model=settings.paddleocr_model,
                base_url=settings.paddleocr_api_base_url,
                token=token,
            )
        return OCRGateway(mode, live_provider=live_provider)
    return OCRGateway(mode)
