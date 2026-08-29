"""Stable provider contract for HAKIM adapters."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol

@dataclass
class AIResponse:
    text: str
    provider: str
    model: str | None = None
    usage: dict[str, Any] | None = None
    raw: Any = None

class ProviderAdapter(Protocol):
    name: str
    def generate(self, prompt: str, context: str = "", **kwargs: Any) -> AIResponse: ...
    def probe(self) -> dict[str, Any]: ...
