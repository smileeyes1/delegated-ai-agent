"""Environment-driven provider runtime. Credentials never enter source control."""
from __future__ import annotations
import json, os, urllib.request
from typing import Any
from .provider_contract import AIResponse


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float = 12) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

class OpenAICompatibleAdapter:
    def __init__(self, name: str, api_key_env: str, base_url: str, model: str):
        self.name, self.api_key_env, self.base_url, self.model = name, api_key_env, base_url.rstrip('/'), model
    def generate(self, prompt: str, context: str = "", **kwargs: Any) -> AIResponse:
        key = os.getenv(self.api_key_env)
        if not key: raise RuntimeError(f"NOT_CONFIGURED:{self.name}")
        messages = [{"role":"user","content": (context + "\n\n" + prompt).strip()}]
        body = {"model": self.model, "messages": messages, "temperature": kwargs.get("temperature", 0.2), "max_tokens": kwargs.get("max_tokens", 1024)}
        out = _post_json(self.base_url + "/chat/completions", body, {"Authorization": f"Bearer {key}"})
        text = out.get("choices", [{}])[0].get("message", {}).get("content")
        if not text: raise RuntimeError(f"EMPTY_RESPONSE:{self.name}")
        return AIResponse(text=text, provider=self.name, model=self.model, usage=out.get("usage"), raw=out)
    def probe(self) -> dict[str, Any]:
        return {"provider": self.name, "configured": bool(os.getenv(self.api_key_env)), "adapter": "openai-compatible"}

class GeminiAdapter:
    def __init__(self, model: str = "gemini-2.5-flash-lite"):
        self.name, self.model = "gemini", model
    def generate(self, prompt: str, context: str = "", **kwargs: Any) -> AIResponse:
        key = os.getenv("GEMINI_API_KEY")
        if not key: raise RuntimeError("NOT_CONFIGURED:gemini")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={key}"
        body = {"contents":[{"parts":[{"text":(context + "\n\n" + prompt).strip()}]}],"generationConfig":{"temperature":kwargs.get("temperature",0.2),"maxOutputTokens":kwargs.get("max_tokens",1024)}}
        out = _post_json(url, body, {})
        text = out.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
        if not text: raise RuntimeError("EMPTY_RESPONSE:gemini")
        return AIResponse(text=text, provider=self.name, model=self.model, usage=out.get("usageMetadata"), raw=out)
    def probe(self) -> dict[str, Any]:
        return {"provider": self.name, "configured": bool(os.getenv("GEMINI_API_KEY")), "adapter": "gemini"}


def build_adapters() -> list[Any]:
    return [
        OpenAICompatibleAdapter("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", os.getenv("OPENROUTER_MODEL", "openrouter/free")),
        GeminiAdapter(os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")),
        OpenAICompatibleAdapter("groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1", os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")),
        OpenAICompatibleAdapter("cerebras", "CEREBRAS_API_KEY", "https://api.cerebras.ai/v1", os.getenv("CEREBRAS_MODEL", "gpt-oss-120b")),
    ]
