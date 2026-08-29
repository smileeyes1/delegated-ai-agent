"""Lightweight Internet AI adapters.

This module keeps HAKIM's device thin: inference may run on a remote
OpenAI-compatible endpoint while the app only sends the request and receives
text. Credentials are supplied at runtime through environment variables and
never stored in the repository.

The adapter is provider-neutral. It can front free-tier endpoints when the
account/provider terms permit free use, and the zero-cost policy blocks any
provider explicitly marked as paid.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.model_gateway import ModelRequest, ModelResponse


@dataclass
class RemoteOpenAICompatibleProvider:
    name: str
    base_url: str
    model: str
    api_key: str = ""
    free_only: bool = True
    timeout: float = 20.0
    mode: str = "public_cloud"
    requires_payment: bool = False
    _fail_until: float = field(default=0.0, init=False, repr=False)

    def available(self, request: ModelRequest) -> bool:
        if not self.base_url or not self.model or time.time() < self._fail_until:
            return False
        if self.free_only and self.requires_payment:
            return False
        return True

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def generate(self, request: ModelRequest) -> ModelResponse:
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "stream": False,
        }).encode("utf-8")
        req = Request(
            self.base_url.rstrip("/") + "/v1/chat/completions",
            data=payload,
            headers=self._headers(),
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            return ModelResponse(text, self.name, self.model, True)
        except (HTTPError, OSError, URLError, TimeoutError, KeyError, ValueError) as exc:
            # Short circuit repeated outages without freezing the application.
            self._fail_until = time.time() + 30.0
            raise RuntimeError(f"remote provider unavailable: {self.name}") from exc


def provider_from_env(prefix: str, *, default_mode: str = "public_cloud") -> RemoteOpenAICompatibleProvider | None:
    """Build one provider from environment variables; returns None if absent.

    PREFIX_URL, PREFIX_MODEL, PREFIX_API_KEY are read. PREFIX_REQUIRES_PAYMENT
    may be set to 1/true/yes. PREFIX_FREE_ONLY defaults to true.
    """
    url = os.getenv(f"{prefix}_URL", "").strip()
    model = os.getenv(f"{prefix}_MODEL", "").strip()
    if not url or not model:
        return None
    requires_payment = os.getenv(f"{prefix}_REQUIRES_PAYMENT", "0").lower() in {"1", "true", "yes"}
    free_only = os.getenv(f"{prefix}_FREE_ONLY", "1").lower() not in {"0", "false", "no"}
    return RemoteOpenAICompatibleProvider(
        name=prefix.lower(),
        base_url=url,
        model=model,
        api_key=os.getenv(f"{prefix}_API_KEY", ""),
        free_only=free_only,
        requires_payment=requires_payment,
        mode=default_mode,
    )


def configured_free_internet_providers() -> list[RemoteOpenAICompatibleProvider]:
    """Discover optional Internet providers without changing application code."""
    prefixes = (
        "GEMINI_FREE",
        "GROQ_FREE",
        "OPENROUTER_FREE",
        "HF_FREE",
        "CLOUDFLARE_AI",
    )
    return [p for p in (provider_from_env(prefix) for prefix in prefixes) if p is not None]


class ResponseCache:
    """Tiny in-memory cache to avoid repeat Internet inference calls."""

    def __init__(self, max_items: int = 256):
        self.max_items = max_items
        self._data: dict[str, ModelResponse] = {}

    def key(self, request: ModelRequest) -> str:
        raw = json.dumps(request.__dict__, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, request: ModelRequest) -> ModelResponse | None:
        return self._data.get(self.key(request))

    def put(self, request: ModelRequest, response: ModelResponse) -> None:
        if len(self._data) >= self.max_items:
            self._data.pop(next(iter(self._data)))
        self._data[self.key(request)] = response
