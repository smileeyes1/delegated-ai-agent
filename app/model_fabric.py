"""HAKIM Model Fabric: dynamic zero-cost routing across heterogeneous AI sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.model_gateway import ModelProvider, ModelRequest, ModelResponse, ZeroCostPolicy


@dataclass(frozen=True)
class RouteDecision:
    provider: str
    reason: str


class ModelFabric:
    """Routes by task/privacy/feature fit while enforcing a $0 spend ceiling."""

    def __init__(self, providers: Iterable[ModelProvider], policy: ZeroCostPolicy | None = None):
        self.providers = list(providers)
        self.policy = policy or ZeroCostPolicy()
        self.history: list[RouteDecision] = []

    def _score(self, provider: ModelProvider, request: ModelRequest) -> int:
        score = 0
        if request.sensitive and provider.mode in {"local", "trusted_lan", "local_browser"}:
            score += 100
        if not request.sensitive and provider.mode == "local":
            score += 70
        if request.require_tools:
            score += 10
        if request.require_structured:
            score += 10
        if request.task in {"reasoning", "planning"}:
            score += 5
        return score

    def generate(self, request: ModelRequest) -> ModelResponse:
        eligible = [
            p for p in self.providers
            if self.policy.allows(p) and p.available(request)
            and not (request.sensitive and p.mode == "public_cloud")
        ]
        eligible.sort(key=lambda p: self._score(p, request), reverse=True)
        for provider in eligible:
            try:
                response = provider.generate(request)
                if not response.proven:
                    raise RuntimeError("unproven provider response")
                self.history.append(RouteDecision(provider.name, "selected and proven"))
                return response
            except Exception as exc:
                self.history.append(RouteDecision(provider.name, f"failed:{type(exc).__name__}"))
        raise RuntimeError("No eligible zero-cost provider available")

    def status(self) -> list[dict[str, str | bool]]:
        return [
            {
                "provider": p.name,
                "mode": p.mode,
                "payment_required": p.requires_payment,
                "available": p.available(ModelRequest("status")),
                "allowed": self.policy.allows(p),
            }
            for p in self.providers
        ]
