"""Live provider registry and zero-cost eligibility probes.
Credentials are read only from the runtime environment and never persisted.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class ProviderSpec:
    name: str
    env_key: str
    capabilities: tuple[str, ...]
    free_claim: str
    adapter: str

PROVIDERS = (
    ProviderSpec("openrouter", "OPENROUTER_API_KEY", ("text", "vision", "structured"), "free-model routing", "openai_compatible"),
    ProviderSpec("gemini", "GEMINI_API_KEY", ("text", "vision", "audio", "pdf"), "free API tier for eligible models", "gemini"),
    ProviderSpec("groq", "GROQ_API_KEY", ("text", "audio", "transcription"), "free-plan limits", "openai_compatible"),
    ProviderSpec("cerebras", "CEREBRAS_API_KEY", ("text", "reasoning"), "eligible free limits", "openai_compatible"),
    ProviderSpec("cloudflare", "CLOUDFLARE_API_TOKEN", ("text", "vision", "audio"), "10,000 neurons/day on Workers Free", "cloudflare"),
)

def discover(env: dict[str, str] | None = None) -> list[dict[str, Any]]:
    env = env or {}
    return [{
        "name": p.name,
        "configured": bool(env.get(p.env_key)),
        "env_key": p.env_key,
        "capabilities": list(p.capabilities),
        "free_claim": p.free_claim,
        "adapter": p.adapter,
    } for p in PROVIDERS]

def build_probes(callers: dict[str, Callable[[], Any]]) -> list[dict[str, Any]]:
    """Run only explicitly supplied runtime probes; never invent connectivity."""
    results = []
    for name in [p.name for p in PROVIDERS]:
        fn = callers.get(name)
        if fn is None:
            results.append({"name": name, "status": "NOT_CONFIGURED"})
            continue
        try:
            value = fn()
            results.append({"name": name, "status": "LIVE", "result": value})
        except Exception as exc:
            results.append({"name": name, "status": "FAILED", "error_type": type(exc).__name__})
    return results
