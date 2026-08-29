"""Lightweight Internet AI Mesh for HAKIM."""
from __future__ import annotations
import hashlib, json, time
from dataclasses import dataclass
from app.model_gateway import ModelRequest, ModelResponse, ModelProvider, ZeroCostPolicy

@dataclass(frozen=True)
class InternetPolicy:
    max_spend: float = 0.0
    max_prompt_chars: int = 12000
    cache_ttl_seconds: int = 86400
    allow_public_cloud_for_sensitive: bool = False

class MemoryResponseCache:
    def __init__(self): self._items = {}
    def get(self, key, now=None):
        item = self._items.get(key)
        if not item: return None
        if (now or time.time()) >= item[0]:
            self._items.pop(key, None); return None
        return item[1]
    def put(self, key, response, ttl, now=None):
        self._items[key] = ((now or time.time()) + ttl, response)

class InternetAIMesh:
    def __init__(self, providers: list[ModelProvider], policy=None, cache=None):
        self.policy = policy or InternetPolicy()
        self.providers = providers
        self.cache = cache or MemoryResponseCache()
        self.failures = []
    def _key(self, request):
        material = json.dumps(request.__dict__, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(material.encode()).hexdigest()
    def generate(self, request: ModelRequest) -> ModelResponse:
        if len(request.prompt) > self.policy.max_prompt_chars:
            raise ValueError("prompt exceeds lightweight Internet Mesh limit")
        key = self._key(request)
        cached = self.cache.get(key)
        if cached is not None: return cached
        for provider in self.providers:
            if not ZeroCostPolicy(self.policy.max_spend).allows(provider): continue
            if request.sensitive and provider.mode == "public_cloud" and not self.policy.allow_public_cloud_for_sensitive: continue
            if not provider.available(request): continue
            try:
                response = provider.generate(request)
                if not response.proven: raise RuntimeError("unproven response")
                self.cache.put(key, response, self.policy.cache_ttl_seconds)
                return response
            except Exception as exc:
                self.failures.append({"provider": provider.name, "error": type(exc).__name__})
        raise RuntimeError("No eligible Internet AI provider available")
    def status(self):
        return [{"provider": p.name, "mode": p.mode, "payment_required": p.requires_payment} for p in self.providers]
