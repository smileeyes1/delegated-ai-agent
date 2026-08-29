"""Provider-independent capability registry for HAKIM."""

from dataclasses import dataclass
from enum import Enum


class CapabilityState(str, Enum):
    AVAILABLE = "AVAILABLE"
    CONFIGURED = "CONFIGURED"
    CONNECTED = "CONNECTED"
    AUTHORIZED = "AUTHORIZED"
    PROVEN = "PROVEN"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Capability:
    name: str
    provider: str
    state: CapabilityState
    mode: str = "real"
    reason: str = ""

    @property
    def usable(self) -> bool:
        return self.state != CapabilityState.BLOCKED

    @property
    def proven(self) -> bool:
        return self.state == CapabilityState.PROVEN


class CapabilityRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        self._items[capability.name] = capability

    def get(self, name: str) -> Capability | None:
        return self._items.get(name)

    def require(self, name: str) -> Capability:
        capability = self.get(name)
        if capability is None or not capability.usable:
            raise RuntimeError(f"Capability unavailable: {name}")
        return capability

    def snapshot(self) -> dict[str, dict[str, str | bool]]:
        return {
            name: {
                "provider": item.provider,
                "state": item.state.value,
                "mode": item.mode,
                "usable": item.usable,
                "proven": item.proven,
                "reason": item.reason,
            }
            for name, item in sorted(self._items.items())
        }
