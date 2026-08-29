"""Provider-agnostic, zero-cost-guarded model gateway."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    task: str = "general"
    sensitive: bool = False
    require_tools: bool = False
    require_structured: bool = False


@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str
    proven: bool


class ModelProvider(Protocol):
    name: str
    mode: str
    requires_payment: bool

    def available(self, request: ModelRequest) -> bool: ...
    def generate(self, request: ModelRequest) -> ModelResponse: ...


class ZeroCostPolicy:
    def __init__(self, max_spend: float = 0.0) -> None:
        self.max_spend = max_spend

    def allows(self, provider: ModelProvider) -> bool:
        return self.max_spend == 0.0 and not provider.requires_payment


class ModelGateway:
    def __init__(self, providers: list[ModelProvider], policy: ZeroCostPolicy | None = None):
        self.providers = providers
        self.policy = policy or ZeroCostPolicy()
        self.failures: list[dict[str, str]] = []

    def generate(self, request: ModelRequest) -> ModelResponse:
        for provider in self.providers:
            if not self.policy.allows(provider):
                continue
            if request.sensitive and provider.mode == "public_cloud":
                continue
            if not provider.available(request):
                continue
            try:
                response = provider.generate(request)
                if not response.proven:
                    raise RuntimeError("Provider returned unproven AI response")
                return response
            except Exception as exc:
                self.failures.append({"provider": provider.name, "error": type(exc).__name__})
        raise RuntimeError("No eligible AI provider is currently available")
