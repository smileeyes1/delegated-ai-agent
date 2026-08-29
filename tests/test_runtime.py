import unittest

from app.capabilities import Capability, CapabilityRegistry, CapabilityState
from app.runtime import Runtime


class RuntimeTests(unittest.TestCase):
    def test_executes_without_cloud_provider(self):
        registry = CapabilityRegistry()
        registry.register(Capability("lesson.generate", "local", CapabilityState.AVAILABLE, mode="local"))
        runtime = Runtime(registry, {"generate": lambda step: {"title": step["title"]}})
        result = runtime.execute([{"action": "generate", "capability": "lesson.generate", "title": "جمع"}])
        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.output[0]["title"], "جمع")
        self.assertEqual(result.events[-1].status, "COMPLETED")

    def test_blocks_missing_capability(self):
        runtime = Runtime(CapabilityRegistry(), {"generate": lambda step: step})
        result = runtime.execute([{"action": "generate", "capability": "foundry"}])
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.events[-1].status, "BLOCKED")

    def test_distinguishes_local_mode(self):
        registry = CapabilityRegistry()
        registry.register(Capability("model", "local", CapabilityState.AVAILABLE, mode="local"))
        runtime = Runtime(registry, {"infer": lambda step: "ok"})
        result = runtime.execute([{"action": "infer", "capability": "model"}])
        self.assertEqual(result.events[0].detail, "local")


if __name__ == "__main__":
    unittest.main()
