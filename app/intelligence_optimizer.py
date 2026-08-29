"""Lightweight request optimizer for internet-first intelligence.

The optimizer reduces device/network load before a request reaches a model.
It never fabricates an answer: it only decides whether to cache, compress,
or route the request to a deterministic local capability.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Callable

from app.model_gateway import ModelRequest


@dataclass(frozen=True)
class OptimizationDecision:
    mode: str  # cache | deterministic | internet
    request: ModelRequest
    cache_key: str
    reason: str


class IntelligenceOptimizer:
    def __init__(self, deterministic_tasks: set[str] | None = None):
        self.deterministic_tasks = deterministic_tasks or {"math", "unit_conversion", "date_time"}

    @staticmethod
    def _normalize(text: str) -> str:
        text = re.sub(r"\s+", " ", text.strip())
        return text

    @staticmethod
    def cache_key(request: ModelRequest) -> str:
        material = "|".join([
            request.prompt,
            request.task,
            str(request.sensitive),
            str(request.require_tools),
            str(request.require_structured),
        ])
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def prepare(self, request: ModelRequest) -> OptimizationDecision:
        prompt = self._normalize(request.prompt)
        optimized = ModelRequest(
            prompt,
            task=request.task,
            sensitive=request.sensitive,
            require_tools=request.require_tools,
            require_structured=request.require_structured,
        )
        if request.task in self.deterministic_tasks:
            return OptimizationDecision("deterministic", optimized, self.cache_key(optimized), "deterministic task")
        return OptimizationDecision("internet", optimized, self.cache_key(optimized), "internet intelligence preferred")


class MemoryCache:
    def __init__(self):
        self._data: dict[str, object] = {}

    def get(self, key: str):
        return self._data.get(key)

    def put(self, key: str, value: object) -> None:
        self._data[key] = value

    def __len__(self) -> int:
        return len(self._data)
