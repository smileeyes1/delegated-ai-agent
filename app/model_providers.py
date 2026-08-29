"""Concrete provider adapters for the Model Fabric.

Adapters are deliberately dependency-light. Local runtimes expose an
OpenAI-compatible HTTP endpoint; no API key or billing is required by this
module. Cloud adapters are represented by the same contract and can be added
without changing HAKIM Core.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.model_gateway import ModelRequest, ModelResponse


@dataclass
class LocalOpenAICompatibleProvider:
    name: str
    base_url: str
    model: str
    timeout: float = 30.0
    mode: str = "local"
    requires_payment: bool = False

    def available(self, request: ModelRequest) -> bool:
        return bool(self.base_url and self.model)

    def generate(self, request: ModelRequest) -> ModelResponse:
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "stream": False,
        }).encode("utf-8")
        req = Request(
            self.base_url.rstrip("/") + "/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError) as exc:
            raise RuntimeError("local inference endpoint unavailable") from exc
        text = data["choices"][0]["message"]["content"]
        return ModelResponse(text, self.name, self.model, True)


@dataclass
class BrowserProviderContract:
    """Contract for a WebGPU/WASM browser worker supplied by the UI layer."""

    name: str = "browser-webgpu"
    mode: str = "local_browser"
    requires_payment: bool = False
    loaded: bool = False

    def available(self, request: ModelRequest) -> bool:
        return self.loaded

    def generate(self, request: ModelRequest) -> ModelResponse:
        raise RuntimeError("browser provider must be executed by the browser worker")


@dataclass
class NetworkNodeContract:
    """Contract for a trusted second device running local inference."""

    name: str = "lan-node"
    mode: str = "trusted_lan"
    requires_payment: bool = False
    reachable: bool = False

    def available(self, request: ModelRequest) -> bool:
        return self.reachable

    def generate(self, request: ModelRequest) -> ModelResponse:
        raise RuntimeError("LAN node transport adapter not configured")
