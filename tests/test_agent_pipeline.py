import unittest

from app.agent_pipeline import HakimIntent, HakimPipeline
from app.local_model import DeterministicLocalProvider
from app.model_fabric import ModelFabric
from app.runtime import Runtime
from app.capabilities import CapabilityRegistry, Capability, CapabilityState


class AgentPipelineTests(unittest.TestCase):
    def test_full_pipeline_without_cloud(self):
        fabric = ModelFabric([DeterministicLocalProvider()])
        registry = CapabilityRegistry()
        registry.register(Capability("lesson.generate", "local", CapabilityState.AVAILABLE, mode="local"))
        runtime = Runtime(registry, {"generate": lambda step: {"ok": True, "title": step["title"]}})
        planner = lambda text: [{"action": "generate", "capability": "lesson.generate", "title": "درس محلي"}]
        pipeline = HakimPipeline(fabric, runtime, planner)
        result = pipeline.run(HakimIntent("أنشئ درسًا", task="lesson"))
        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.provider, "deterministic-local")
        self.assertEqual(result.execution.output[0]["title"], "درس محلي")
        self.assertIn("model_response_proven", result.assurance)


if __name__ == "__main__":
    unittest.main()
