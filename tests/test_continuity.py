import tempfile
import unittest
from pathlib import Path

from app.continuity import ContinuityStore, MissionState


class ContinuityTests(unittest.TestCase):
    def test_round_trip_state(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ContinuityStore(Path(directory) / "state.json")
            original = MissionState(
                mission_id="m1",
                phase="CORE",
                current_action="runtime",
                completed=["gate"],
                evidence=["test-1"],
                next_action="model-gateway",
            )
            store.save(original)
            restored = store.load()
            self.assertEqual(restored.mission_id, "m1")
            self.assertEqual(restored.completed, ["gate"])
            self.assertEqual(restored.next_action, "model-gateway")
            self.assertTrue(restored.updated_at)


if __name__ == "__main__":
    unittest.main()
