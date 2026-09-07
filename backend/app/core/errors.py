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


class BudgetSettlementError(V3Error):
    """settle 记账不一致（reserved < 释放量）：双 settle / 被 reclaim 误扫 / 状态损坏。

    F-6 裁决：与 BudgetExceededError（预算不足拒绝执行）语义不同，不得伪装成超限——
    settle 失败是 runtime accounting 不一致信号，调用方不得静默吞掉。
    """

    error_type = "conflict"


class CircuitOpen(V3Error):
    """MAX_LLM_CALLS_PER_TASK 熔断（Lock-4/Note-1/Clarification-2）。

    真实 Provider Invocation 越界 → 拒绝（provider 不发出）。计数点位于 Provider
    Invocation Port（gateway provider seam），非 gateway.complete 层。
    """

    error_type = "conflict"


class LLMProviderError(V3Error):
    """LLM provider 层服务失败（5xx / provider error）。

    retryable（BUG-V3-034 冻结）：5xx/429/408 transient → True（可 bounded retry）；4xx 其他
    （400-407/409/410-428/430-499）provider 明确拒绝 → False（重试无意义）。
    """

    error_type = "provider_error"

    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMNetworkError(V3Error):
    """LLM 网络/传输失败（连接、超时；transient，可 bounded retry）。"""

    error_type = "network_error"


class OCRProviderError(V3Error):
    """OCR provider 语义失败（如解析结果异常，30 §6 external provider 层）。"""

    error_type = "provider_error"


class OCRNetworkError(V3Error):
    """OCR 网络/API 传输失败（连接、超时、非 2xx；30 §6 external 网络层）。"""

    error_type = "network_error"
