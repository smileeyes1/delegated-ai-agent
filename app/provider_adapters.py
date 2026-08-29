"""Minimal provider adapters using only runtime credentials.
No SDK dependency is required; adapters use urllib so the client stays light.
"""
from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen

class ProviderHTTPError(RuntimeError):
    pass

def _post_json(url: str, headers: dict[str, str], body: dict, timeout: float = 20.0) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=data, headers={**headers, "content-type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except Exception as exc:
        raise ProviderHTTPError(type(exc).__name__) from exc

def openai_compatible_call(base_url: str, api_key: str, model: str, prompt: str, context: str = "") -> str:
    messages = [{"role": "user", "content": prompt if not context else f"{context}\n\n{prompt}"}]
    data = _post_json(base_url.rstrip("/") + "/chat/completions", {"Authorization": f"Bearer {api_key}"}, {"model": model, "messages": messages, "temperature": 0.2})
    return data["choices"][0]["message"]["content"]

def openrouter_call(model: str, prompt: str, context: str = "") -> str:
    return openai_compatible_call("https://openrouter.ai/api/v1", os.environ["OPENROUTER_API_KEY"], model, prompt, context)

def groq_call(model: str, prompt: str, context: str = "") -> str:
    return openai_compatible_call("https://api.groq.com/openai/v1", os.environ["GROQ_API_KEY"], model, prompt, context)

def cerebras_call(model: str, prompt: str, context: str = "") -> str:
    return openai_compatible_call("https://api.cerebras.ai/v1", os.environ["CEREBRAS_API_KEY"], model, prompt, context)

def gemini_call(model: str, prompt: str, context: str = "") -> str:
    key = os.environ["GEMINI_API_KEY"]
    text = prompt if not context else f"{context}\n\n{prompt}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    data = _post_json(url, {}, {"contents": [{"parts": [{"text": text}]}]})
    return data["candidates"][0]["content"]["parts"][0]["text"]
