"""统一异常（40 §6 八分类 + 段 C 具体异常）。"""

ERROR_TYPES = frozenset(
    {
        "validation_error",
        "source_error",
        "provider_error",
        "network_error",
        "semantic_error",
        "conflict",
        "admission_error",
        "system_error",
    }
)


class V3Error(Exception):
    """结构化失败：保留 error_type 分类供上层映射。禁止静默 except。"""

    error_type: str = "system_error"

    def __init__(self, message: str, *, error_type: str | None = None) -> None:
        super().__init__(message)
        if error_type is not None:
            if error_type not in ERROR_TYPES:
                raise ValueError(f"unknown error_type: {error_type}")
            self.error_type = error_type


class GatewayDisabledError(V3Error):
    """Gateway disabled 态任何调用即失败（30 §6）。"""

    error_type = "system_error"


class GatewayDeniedError(V3Error):
    """live 组合放行前置不满足（缺 allow-live/task context/budget）。"""

    error_type = "conflict"


class BudgetExceededError(V3Error):
    """五账户任一超限 → 拒绝（30 §11）。"""

    error_type = "conflict"


class OCRProviderError(V3Error):
    """OCR provider 语义失败（如解析结果异常，30 §6 external provider 层）。"""

    error_type = "provider_error"


class OCRNetworkError(V3Error):
    """OCR 网络/API 传输失败（连接、超时、非 2xx；30 §6 external 网络层）。"""

    error_type = "network_error"
