import tempfile
import unittest
from pathlib import Path

from app.continuity import ContinuityStore, MissionState
from app.recovery import RecoveryManager


class RecoveryTests(unittest.TestCase):
    def test_resume_after_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = RecoveryManager(ContinuityStore(Path(directory) / "state.json"))
            state = MissionState("m1", "CORE", "start")
            manager.checkpoint(state, "step-1")
            manager.mark_failure(state, "step-2", "timeout")
            resumed = manager.resume()
            self.assertEqual(resumed.status, "RESUMABLE")
            self.assertIn("step-2:timeout", resumed.failures)

    def test_completion_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = RecoveryManager(ContinuityStore(Path(directory) / "state.json"))
            state = MissionState("m1", "CORE", "start")
            manager.mark_completed(state, "step-1", "e1")
            manager.mark_completed(state, "step-1", "e1")
            self.assertEqual(state.completed, ["step-1"])
            self.assertEqual(state.evidence, ["e1"])


if __name__ == "__main__":
    unittest.main()
