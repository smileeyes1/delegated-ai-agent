import tempfile
import unittest
from pathlib import Path

from app.capabilities import Capability, CapabilityRegistry, CapabilityState
from app.continuity import ContinuityStore, MissionState
from app.runtime import Runtime


class RuntimeIntegrationTests(unittest.TestCase):
    def test_local_execution_persists_resume_state(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ContinuityStore(Path(directory) / "mission.json")
            state = MissionState("m1", "CORE", "generate", next_action="verify")
            registry = CapabilityRegistry()
            registry.register(Capability("lesson.generate", "local", CapabilityState.AVAILABLE, mode="local"))
            runtime = Runtime(registry, {"generate": lambda step: {"title": step["title"]}})
            result = runtime.execute([{"action": "generate", "capability": "lesson.generate", "title": "درس"}])
            self.assertEqual(result.status, "COMPLETED")
            state.completed.append("generate")
            state.evidence.append("local-runtime-completed")
            store.save(state)
            restored = store.load()
            self.assertEqual(restored.completed, ["generate"])
            self.assertEqual(restored.next_action, "verify")


if __name__ == "__main__":
    unittest.main()
