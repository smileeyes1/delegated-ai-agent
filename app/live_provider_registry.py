"""Live provider registry metadata and quota-aware discovery for HAKIM.

No credential is stored here. Runtime adapters read credentials from the environment.
"""
from dataclasses import dataclass
from typing import Any

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
