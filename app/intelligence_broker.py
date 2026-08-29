"""HAKIM Intelligence Broker: capability-aware, quota-aware, zero-cost routing."""
from __future__ import annotations
from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Callable

@dataclass
class Provider:
    name: str
    capabilities: set[str]
    free: bool = True
    available: bool = True
    quota_remaining: int | None = None
    latency_ms: int | None = None
    sensitive_ok: bool = False
    call: Callable[..., Any] | None = None
    failures: int = 0
    cooldown_until: float = 0.0

    def eligible(self, capability: str, sensitive: bool) -> bool:
        if not self.free or not self.available or capability not in self.capabilities:
            return False
        if sensitive and not self.sensitive_ok:
            return False
        if monotonic() < self.cooldown_until:
            return False
        if self.quota_remaining is not None and self.quota_remaining <= 0:
            return False
        return True

@dataclass
class BrokerResult:
    value: Any
    provider: str
    attempts: list[str] = field(default_factory=list)
    cached: bool = False

class IntelligenceBroker:
    def __init__(self, providers: list[Provider], cache: Any | None = None):
        self.providers = providers
        self.cache = cache

    def rank(self, capability: str, sensitive: bool = False) -> list[Provider]:
        candidates = [p for p in self.providers if p.eligible(capability, sensitive)]
        return sorted(candidates, key=lambda p: (
            -(p.quota_remaining if p.quota_remaining is not None else 10**12),
            p.latency_ms if p.latency_ms is not None else 10**9,
            p.failures,
        ))

    def execute(self, capability: str, prompt: str, *, context: str = "", sensitive: bool = False, cache_key: str | None = None) -> BrokerResult:
        if self.cache is not None and cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return BrokerResult(cached, "cache", [], True)
        attempts: list[str] = []
        for provider in self.rank(capability, sensitive):
            attempts.append(provider.name)
            try:
                if provider.call is None:
                    raise RuntimeError("provider has no callable")
                value = provider.call(prompt, context)
                if value is None:
                    raise RuntimeError("empty response")
                provider.failures = 0
                if provider.quota_remaining is not None:
                    provider.quota_remaining = max(0, provider.quota_remaining - 1)
                if self.cache is not None and cache_key:
                    self.cache.set(cache_key, value)
                return BrokerResult(value, provider.name, attempts, False)
            except Exception:
                provider.failures += 1
                provider.cooldown_until = monotonic() + min(60, 2 ** min(provider.failures, 6))
        raise RuntimeError(f"NO_ELIGIBLE_PROVIDER:{capability}")
