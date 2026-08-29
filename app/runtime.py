"""Provider-independent execution runtime for HAKIM."""

from dataclasses import dataclass, field
from typing import Any, Callable

from capabilities import CapabilityRegistry


@dataclass
class ExecutionEvent:
    action: str
    status: str
    detail: str = ""


@dataclass
class ExecutionResult:
    status: str
    output: Any = None
    events: list[ExecutionEvent] = field(default_factory=list)


class Runtime:
    def __init__(self, capabilities: CapabilityRegistry, tools: dict[str, Callable[[dict], Any]] | None = None):
        self.capabilities = capabilities
        self.tools = tools or {}

    def execute(self, plan: list[dict[str, Any]]) -> ExecutionResult:
        events: list[ExecutionEvent] = []
        output: list[Any] = []
        for step in plan:
            action = step.get("action", "")
            capability_name = step.get("capability")
            if capability_name:
                capability = self.capabilities.get(capability_name)
                if capability is None or not capability.usable:
                    events.append(ExecutionEvent(action, "BLOCKED", f"Capability unavailable: {capability_name}"))
                    return ExecutionResult("BLOCKED", output, events)
                events.append(ExecutionEvent(action, "CAPABILITY_OK", capability.mode))
            tool = self.tools.get(action)
            if tool is None:
                events.append(ExecutionEvent(action, "BLOCKED", "No registered tool"))
                return ExecutionResult("BLOCKED", output, events)
            try:
                value = tool(step)
            except Exception as exc:
                events.append(ExecutionEvent(action, "FAILED", type(exc).__name__))
                return ExecutionResult("FAILED", output, events)
            output.append(value)
            events.append(ExecutionEvent(action, "COMPLETED"))
        return ExecutionResult("COMPLETED", output, events)
