"""Device-light Internet intelligence optimizer.

The client remains thin: normalize, cache, choose a route, stream/receive,
and verify. It never downloads or runs a large model on the device by default.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class NetworkProfile:
    online: bool = True
    metered: bool = False
    latency_ms: int | None = None


@dataclass
class ProviderHealth:
    failures: int = 0
    cooldown_until: float = 0.0
    requests: int = 0
    successes: int = 0


@dataclass
class InternetPolicy:
    max_spend_usd: float = 0.0
    max_prompt_chars: int = 12000
    cache_ttl_seconds: int = 86400
    max_attempts: int = 3
    metered_max_prompt_chars: int = 5000


class IntelligenceOptimizer:
    def __init__(self, policy: InternetPolicy | None = None):
        self.policy = policy or InternetPolicy()
        self.cache: dict[str, tuple[float, Any]] = {}
        self.health: dict[str, ProviderHealth] = {}

    @staticmethod
    def normalize(prompt: str, context: str = "") -> tuple[str, str]:
        clean = " ".join(prompt.split())
        ctx = " ".join(context.split())
        return clean, ctx

    def cache_key(self, prompt: str, context: str, task: str, model_class: str) -> str:
        payload = json.dumps(
            {"p": prompt, "c": context, "t": task, "m": model_class},
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def _eligible(self, name: str) -> bool:
        h = self.health.setdefault(name, ProviderHealth())
        return time.monotonic() >= h.cooldown_until

    def _record_failure(self, name: str) -> None:
        h = self.health.setdefault(name, ProviderHealth())
        h.failures += 1
        h.cooldown_until = time.monotonic() + min(60, 2 ** min(h.failures, 6))

    def _record_success(self, name: str) -> None:
        h = self.health.setdefault(name, ProviderHealth())
        h.successes += 1
        h.failures = 0

    def run(
        self,
        prompt: str,
        providers: list[tuple[str, Callable[[str, str], Any]]],
        *,
        context: str = "",
        task: str = "general",
        model_class: str = "general",
        network: NetworkProfile | None = None,
        force_refresh: bool = False,
    ) -> tuple[Any, str, bool]:
        network = network or NetworkProfile()
        if not network.online:
            raise RuntimeError("OFFLINE: no internet route available")
        prompt, context = self.normalize(prompt, context)
        limit = self.policy.metered_max_prompt_chars if network.metered else self.policy.max_prompt_chars
        prompt = prompt[:limit]
        context = context[: max(0, limit - len(prompt))]
        key = self.cache_key(prompt, context, task, model_class)
        if not force_refresh and key in self.cache:
            created, value = self.cache[key]
            if time.time() - created <= self.policy.cache_ttl_seconds:
                return value, "cache", True
        attempts = 0
        for name, call in providers:
            if attempts >= self.policy.max_attempts:
                break
            if not self._eligible(name):
                continue
            attempts += 1
            h = self.health.setdefault(name, ProviderHealth())
            h.requests += 1
            try:
                value = call(prompt, context)
                if value is None:
                    raise RuntimeError("empty provider response")
                self._record_success(name)
                self.cache[key] = (time.time(), value)
                return value, name, False
            except Exception:
                self._record_failure(name)
        raise RuntimeError("NO_FREE_INTERNET_PROVIDER_AVAILABLE")
