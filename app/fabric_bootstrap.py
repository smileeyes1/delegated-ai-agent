"""Zero-cost-first Model Fabric bootstrap.

Order is intentionally device-light: Internet free-tier providers first for
speed/quality when configured, then trusted LAN, then local runtime, then the
bounded deterministic fallback. No paid provider is admitted by default.
"""

from app.local_model import DeterministicLocalProvider
from app.model_fabric import ModelFabric
from app.model_gateway import ZeroCostPolicy
from app.model_providers import LocalOpenAICompatibleProvider, NetworkNodeContract
from app.internet_ai import configured_free_internet_providers


def build_default_fabric() -> ModelFabric:
    providers = []
    providers.extend(configured_free_internet_providers())

    lan_url = __import__("os").getenv("HAKIM_LAN_URL", "").strip()
    lan_model = __import__("os").getenv("HAKIM_LAN_MODEL", "").strip()
    if lan_url and lan_model:
        providers.append(LocalOpenAICompatibleProvider(
            name="trusted-lan",
            base_url=lan_url,
            model=lan_model,
            mode="trusted_lan",
            requires_payment=False,
        ))

    local_url = __import__("os").getenv("HAKIM_LOCAL_URL", "http://127.0.0.1:11434").strip()
    local_model = __import__("os").getenv("HAKIM_LOCAL_MODEL", "").strip()
    if local_model:
        providers.append(LocalOpenAICompatibleProvider(
            name="local-llm",
            base_url=local_url,
            model=local_model,
            mode="local",
            requires_payment=False,
        ))

    providers.append(DeterministicLocalProvider())
    return ModelFabric(providers, ZeroCostPolicy(max_spend=0.0))
