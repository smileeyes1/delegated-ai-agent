"""Deterministic local fallback used when no external model is available.

This is an execution-safe fallback, not a claim of general LLM intelligence.
It produces structured educational scaffolding from normalized intents.
"""

from dataclasses import dataclass

from app.model_gateway import ModelRequest, ModelResponse


@dataclass
class DeterministicLocalProvider:
    name: str = "deterministic-local"
    model: str = "hakim-educational-fallback-v1"
    mode: str = "local"
    requires_payment: bool = False

    def available(self, request: ModelRequest) -> bool:
        return True

    def generate(self, request: ModelRequest) -> ModelResponse:
        task = request.task or "general"
        if task in {"lesson", "planning", "reasoning"}:
            text = (
                "خطة محلية آمنة: حدّد الهدف، استخرج القيود، ابنِ النشاط، "
                "ثم تحقّق من الناتج قبل التسليم."
            )
        elif task == "summary":
            text = "وضع التلخيص المحلي متاح؛ يلزم تمرير النص المراد تلخيصه إلى أداة التلخيص."
        else:
            text = "HAKIM يعمل في الوضع المحلي المحدود دون مزود سحابي."
        return ModelResponse(text, self.name, self.model, True)
