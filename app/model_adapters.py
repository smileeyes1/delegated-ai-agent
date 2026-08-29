"""Concrete optional adapters for local AI endpoints and AI over LAN."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.model_gateway import ModelRequest, ModelResponse


@dataclass
class OpenAICompatibleHTTPProvider:
    """Adapter for Ollama, llama.cpp server, vLLM, LocalAI, or similar endpoints."""

    base_url: str
    model: str
    name: str = "openai-compatible-local"
    mode: str = "local"
    requires_payment: bool = False
    timeout: float = 20.0

    def available(self, request: ModelRequest) -> bool:
        try:
            req = Request(self.base_url.rstrip("/") + "/v1/models", method="GET")
            with urlopen(req, timeout=3) as response:
                return 200 <= response.status < 300
        except (OSError, URLError):
            return False

    def generate(self, request: ModelRequest) -> ModelResponse:
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": 0.2,
        }).encode("utf-8")
        req = Request(
            self.base_url.rstrip("/") + "/v1/chat/completions",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        return ModelResponse(text, self.name, self.model, True)


@dataclass
class OllamaProvider(OpenAICompatibleHTTPProvider):
    """Ollama-specific convenience adapter using its OpenAI-compatible API."""

    base_url: str = "http://127.0.0.1:11434"
    model: str = ""
    name: str = "ollama-local"


@dataclass
class LlamaCppServerProvider(OpenAICompatibleHTTPProvider):
    """llama.cpp server adapter using its OpenAI-compatible endpoint."""

    base_url: str = "http://127.0.0.1:8080"
    model: str = "local-model"
    name: str = "llama-cpp-local"
