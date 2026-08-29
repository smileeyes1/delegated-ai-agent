"""End-to-end HAKIM pipeline: intent -> model fabric -> execution -> assurance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.model_fabric import ModelFabric
from app.model_gateway import ModelRequest
from app.runtime import ExecutionResult, Runtime


@dataclass(frozen=True)
class HakimIntent:
    prompt: str
    task: str = "general"
    sensitive: bool = False
    require_tools: bool = False
    require_structured: bool = False


@dataclass
class PipelineResult:
    status: str
    model_text: str
    provider: str
    model: str
    execution: ExecutionResult | None
    assurance: list[str]


class HakimPipeline:
    def __init__(self, fabric: ModelFabric, runtime: Runtime, planner: Callable[[str], list[dict[str, Any]]]):
        self.fabric = fabric
        self.runtime = runtime
        self.planner = planner

    def run(self, intent: HakimIntent) -> PipelineResult:
        response = self.fabric.generate(ModelRequest(
            prompt=intent.prompt,
            task=intent.task,
            sensitive=intent.sensitive,
            require_tools=intent.require_tools,
            require_structured=intent.require_structured,
        ))
        plan = self.planner(response.text)
        execution = self.runtime.execute(plan)
        assurance = [
            "model_response_proven",
            f"provider={response.provider}",
            f"model={response.model}",
            f"execution={execution.status}",
        ]
        status = "COMPLETED" if execution.status == "COMPLETED" else execution.status
        return PipelineResult(status, response.text, response.provider, response.model, execution, assurance)
