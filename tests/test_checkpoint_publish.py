import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / "book" / "push_checkpoint.sh"


class CheckpointPublishTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.remote = root / "remote.git"
        self.writer = root / "writer"
        self.other = root / "other"
        self.git(root, "init", "--bare", "--initial-branch=main", self.remote)
        self.git(root, "clone", self.remote, self.writer)
        self.configure(self.writer)
        self.commit_file(self.writer, "state.txt", "last verified")
        self.git(self.writer, "push", "origin", "HEAD:main")
        self.git(root, "clone", self.remote, self.other)
        self.configure(self.other)

    def git(self, cwd, *args):
        return subprocess.run(
            ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
        ).stdout.strip()

    def configure(self, repository):
        self.git(repository, "config", "user.name", "Checkpoint Test")
        self.git(repository, "config", "user.email", "checkpoint@example.invalid")

    def commit_file(self, repository, path, content):
        (repository / path).write_text(content, encoding="utf-8")
        self.git(repository, "add", path)
        self.git(repository, "commit", "-m", f"Update {path}")

    def publish(self):
        return subprocess.run(
            ["bash", PUBLISH, "main", "1"], cwd=self.writer,
            capture_output=True, text=True,
        )

    def test_publishes_current_checkpoint_and_repeated_confirmation(self):
        self.commit_file(self.writer, "state.txt", "new verified checkpoint")
        first = self.publish()
        self.assertEqual(first.returncode, 0, first.stderr)
        again = self.publish()
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(self.git(self.remote, "show", "main:state.txt"), "new verified checkpoint")

    def test_upstream_change_rejects_candidate_even_without_a_textual_conflict(self):
        self.commit_file(self.writer, "state.txt", "candidate from stale source")
        self.commit_file(self.other, "quality-rules.txt", "new rules")
        self.git(self.other, "push", "origin", "HEAD:main")
        candidate = self.git(self.writer, "rev-parse", "HEAD")

        result = self.publish()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CHECKPOINT_CONFLICT", result.stderr)
        self.assertEqual(self.git(self.remote, "show", "main:state.txt"), "last verified")
        self.assertEqual(self.git(self.remote, "show", "main:quality-rules.txt"), "new rules")
        self.assertEqual(self.git(self.writer, "rev-parse", "HEAD"), candidate)
