import json
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from app.intent import extract_intent
from app.local_tasks import MAX_FILE_BYTES, TaskStore
from app.permissions import require_approval
from app.planner import build_plan


REPO = Path(__file__).resolve().parents[1]


class LocalTaskTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.database = self.workspace / "state" / "queue.sqlite"
        self.store = TaskStore(self.database, self.workspace)
        self.document = self.workspace / "evidence.json"
        self.document.write_bytes(b'{"evidence": true}')

    def cli(self, *arguments, script=False):
        entry = [str(REPO / "app/main.py")] if script else ["-m", "app.main"]
        return [
            sys.executable, *entry, "--workspace", str(self.workspace), "--db", str(self.database), *arguments,
        ]

    def test_cli_reopens_queue_and_preserves_verified_result(self):
        queued = subprocess.run(
            self.cli("enqueue", "review-1", "verify-json", "evidence.json", script=True),
            cwd=REPO, capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(queued.stdout)["state"], "pending")
        finished = subprocess.run(
            self.cli("run-next"), cwd=REPO, capture_output=True, text=True, check=True,
        )
        result = json.loads(finished.stdout)
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["result"], {
            "json_type": "object",
            "bytes": self.document.stat().st_size,
            "sha256": sha256(self.document.read_bytes()).hexdigest(),
        })
        self.document.write_text("invalid JSON", encoding="utf-8")
        repeated = self.store.enqueue("review-1", "verify-json", "./evidence.json")
        self.assertEqual(result, repeated)
        self.assertIsNone(self.store.run_next())
        with self.assertRaises(ValueError):
            self.store.retry("review-1")
        self.assertEqual([item["event"] for item in self.store.history("review-1")], ["enqueued", "completed"])

    def test_conflicting_id_and_invalid_paths_leave_the_queue_unchanged(self):
        self.store.enqueue("proof", "sha256", "evidence.json")
        with self.assertRaisesRegex(ValueError, "different specification"):
            self.store.enqueue("proof", "verify-json", "evidence.json")
        for path in ("../outside", str(self.document), ".", "a\x00b"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.store.enqueue("unsafe", "sha256", path)
        self.assertEqual([task["id"] for task in self.store.status()], ["proof"])
        elsewhere = self.workspace / "another-workspace"
        elsewhere.mkdir()
        with self.assertRaisesRegex(ValueError, "different workspace"):
            TaskStore(self.database, elsewhere)

    def test_priority_and_retry_after_fix(self):
        self.store.enqueue("ordinary", "sha256", "evidence.json")
        self.store.enqueue("repair", "verify-json", "missing.json", priority=4, max_attempts=2)
        self.assertEqual(self.store.run_next()["state"], "pending")
        self.assertEqual(self.store.run_next()["state"], "failed")
        self.assertEqual(self.store.run_next()["id"], "ordinary")
        (self.workspace / "missing.json").write_text("[]", encoding="utf-8")
        self.store.retry("repair")
        repaired = self.store.run_next()
        self.assertEqual(repaired["attempts"], 3)
        self.assertEqual(repaired["result"]["json_type"], "array")
        self.assertEqual(
            [item["event"] for item in self.store.history("repair")],
            ["enqueued", "retry_pending", "failed", "requeued", "completed"],
        )

    def test_backup_preserves_verified_state_and_refuses_an_existing_destination(self):
        self.store.enqueue("last-success", "sha256", "evidence.json")
        completed = self.store.run_next()
        destination = self.workspace / "verified.sqlite"
        result = subprocess.run(
            self.cli("backup", str(destination)), cwd=REPO, capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout)["backup"], str(destination))
        self.store.enqueue("newer-task", "sha256", "evidence.json")

        snapshot = TaskStore(destination, self.workspace)
        self.assertEqual(snapshot.status(), [completed])
        self.assertEqual(snapshot.history("last-success"), self.store.history("last-success"))
        before = destination.read_bytes()
        with self.assertRaises(FileExistsError):
            self.store.backup(destination)
        self.assertEqual(destination.read_bytes(), before)

    def test_drain_observes_the_requested_attempt_limit(self):
        for task_id in ("first", "second", "third"):
            self.store.enqueue(task_id, "sha256", "evidence.json")
        self.store.enqueue("needs-input", "sha256", "missing.json", max_attempts=1)
        result = subprocess.run(
            self.cli("drain", "--limit", "2"), cwd=REPO, capture_output=True, text=True, check=True,
        )
        self.assertEqual([item["id"] for item in json.loads(result.stdout)], ["first", "second"])
        self.assertEqual(self.store.status("third")["state"], "pending")
        remaining = subprocess.run(self.cli("drain"), cwd=REPO, capture_output=True, text=True)
        self.assertEqual(remaining.returncode, 1)
        self.assertEqual(
            [(item["id"], item["state"]) for item in json.loads(remaining.stdout)],
            [("third", "completed"), ("needs-input", "failed")],
        )
        with self.assertRaises(ValueError):
            self.store.drain(101)

    def test_concurrent_processes_commit_a_task_once(self):
        self.store.enqueue("single", "sha256", "evidence.json")
        workers = [
            subprocess.Popen(self.cli("run-next"), cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for _ in range(4)
        ]
        try:
            results = []
            for worker in workers:
                stdout, stderr = worker.communicate(timeout=15)
                self.assertEqual(worker.returncode, 0, stderr)
                results.append(json.loads(stdout))
        finally:
            for worker in workers:
                if worker.poll() is None:
                    worker.kill()
                    worker.communicate()

        [completed] = [record for record in results if record is not None]
        self.assertEqual(completed["attempts"], 1)
        self.assertEqual(len(self.store.history("single")), 2)

    def test_killed_worker_rolls_back_uncommitted_result_and_event(self):
        self.store.enqueue("interrupted", "sha256", "evidence.json")
        marker = self.workspace / "inside-transaction"
        program = """
import sys
import time
from pathlib import Path
from app.local_tasks import TaskStore

record_event = TaskStore._event

def wait_before_commit(connection, task_id, event, attempt, result=None):
    record_event(connection, task_id, event, attempt, result)
    if event == "completed":
        Path(sys.argv[3]).touch()
        time.sleep(60)

TaskStore._event = staticmethod(wait_before_commit)
TaskStore(Path(sys.argv[1]), Path(sys.argv[2])).run_next()
"""
        worker = subprocess.Popen(
            [sys.executable, "-c", program, str(self.database), str(self.workspace), str(marker)], cwd=REPO,
        )
        try:
            deadline = time.monotonic() + 10
            while not marker.exists() and worker.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(marker.exists(), "worker never reached the uncommitted completion")
        finally:
            if worker.poll() is None:
                worker.kill()
            worker.wait(timeout=5)
        self.assertEqual(self.store.status("interrupted")["state"], "pending")
        self.assertEqual([item["event"] for item in self.store.history("interrupted")], ["enqueued"])
        self.assertEqual(self.store.run_next()["state"], "completed")
        self.assertEqual([item["event"] for item in self.store.history("interrupted")], ["enqueued", "completed"])

    def test_operation_rejects_invalid_json_escaping_links_and_large_files(self):
        self.document.write_text("NaN", encoding="utf-8")
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "outside.json"
            external.write_text("{}", encoding="utf-8")
            self.workspace.joinpath("escape.json").symlink_to(external)
            with self.workspace.joinpath("large.bin").open("wb") as large:
                large.truncate(MAX_FILE_BYTES + 1)
            for task_id, operation, filename in (
                ("invalid", "verify-json", "evidence.json"),
                ("escaped", "sha256", "escape.json"),
                ("large", "sha256", "large.bin"),
            ):
                with self.subTest(task=task_id):
                    self.store.enqueue(task_id, operation, filename, max_attempts=1)
                    self.assertEqual(self.store.run_next()["state"], "failed")

    def test_regular_nested_input_works_and_links_are_rejected(self):
        nested = self.workspace / "nested"
        nested.mkdir()
        (nested / "evidence.json").write_text("{}", encoding="utf-8")
        (self.workspace / "nested-link").symlink_to(nested, target_is_directory=True)
        (nested / "file-link.json").symlink_to(nested / "evidence.json")
        for filename, expected in (
            ("nested/evidence.json", "completed"),
            ("nested-link/evidence.json", "failed"),
            ("nested/file-link.json", "failed"),
            ("nested", "failed"),
        ):
            with self.subTest(filename=filename):
                self.store.enqueue(filename, "verify-json", filename, max_attempts=1)
                self.assertEqual(self.store.run_next()["state"], expected)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are unavailable")
    def test_non_regular_input_returns_without_waiting_for_a_writer(self):
        os.mkfifo(self.workspace / "pipe")
        self.store.enqueue("pipe-check", "sha256", "pipe", max_attempts=1)
        run = subprocess.run(
            self.cli("run-next"), cwd=REPO, capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(run.stdout)["result"]["error"], "workspace input must be a regular file")

    @unittest.skipUnless(hasattr(os, "O_PATH") or hasattr(os, "O_SEARCH"), "search-only directory opens are unavailable")
    def test_file_in_traversable_unlistable_directory_is_readable(self):
        nested = self.workspace / "search-only"
        nested.mkdir()
        (nested / "evidence.json").write_text("{}", encoding="utf-8")
        try:
            nested.chmod(0o100)
            self.store.enqueue("search-only", "verify-json", "search-only/evidence.json")
            self.assertEqual(self.store.run_next()["state"], "completed")
        finally:
            nested.chmod(0o700)

    def test_secure_file_operations_fail_closed_without_descriptor_support(self):
        self.store.enqueue("platform-check", "sha256", "evidence.json", max_attempts=1)
        with patch("app.local_tasks.HAS_CONFINED_FILE_READS", False):
            result = self.store.run_next()
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["result"]["error"], "secure workspace file reads are unavailable on this platform")

    def test_intent_preserves_the_planners_approval_boundary(self):
        intent = extract_intent("راجع المستودع على غيت هاب")
        plan = build_plan(intent)
        approval = require_approval(plan)
        self.assertEqual([step["action"] for step in plan], ["analyze_repository", "create_issue"])
        self.assertTrue(approval["approval_needed"])
        self.assertFalse(approval["actions"][0]["approved"])
        self.assertEqual(build_plan(extract_intent("اقرأ الملف")), [])


if __name__ == "__main__":
    unittest.main()
