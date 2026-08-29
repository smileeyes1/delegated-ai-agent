"""Public HAKIM entry point for zero-cost internet intelligence."""
from __future__ import annotations
import hashlib
from typing import Any
from .intelligence_broker import IntelligenceBroker, Provider
from .provider_runtime import build_adapters

class MemoryCache:
    def __init__(self): self._data = {}
    def get(self, key): return self._data.get(key)
    def set(self, key, value): self._data[key] = value

def _key(capability: str, prompt: str, context: str) -> str:
    return hashlib.sha256(f'{capability}\0{context}\0{prompt}'.encode()).hexdigest()

def build_hakim() -> tuple[IntelligenceBroker, list[Any]]:
    adapters = build_adapters()
    providers = [
        Provider(a.name, {'text'}, free=True, available=True, call=a.generate)
        for a in adapters
    ]
    return IntelligenceBroker(providers, cache=MemoryCache()), adapters

def ask(prompt: str, *, context: str = '', capability: str = 'text', sensitive: bool = False) -> dict[str, Any]:
    broker, _ = build_hakim()
    result = broker.execute(capability, prompt, context=context, sensitive=sensitive, cache_key=_key(capability,prompt,context))
    return {'text': result.value.text if hasattr(result.value, 'text') else result.value, 'provider': result.provider, 'attempts': result.attempts, 'cached': result.cached}
