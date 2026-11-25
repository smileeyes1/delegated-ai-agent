import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from interop.__main__ import RecordError, check_record, read_record


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "interop" / "example.json"


class ContinuationExchangeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "received.json"
        self.record = read_record(EXAMPLE)

    def write(self, **changes):
        record = {**self.record, **changes}
        self.path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    def command(self, recipient, *args):
        return subprocess.run(
            [sys.executable, "-m", "interop", "check", str(self.path), "--for", recipient, *args],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )

    def test_cli_accepts_addressed_files(self):
        for producer, recipient in [("hakim", "dot"), ("dot", "chatgpt-work"), ("automation", "hakim")]:
            with self.subTest(producer=producer, recipient=recipient):
                self.write(producer=producer, recipient=recipient)
                contents = self.path.read_bytes()
                result = self.command(recipient)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {
                    "goal_id": "book-factory-e2e", "revision": 1, "disposition": "new",
                })
                self.assertEqual(self.path.read_bytes(), contents)

    def test_compares_records_without_replaying_duplicates(self):
        self.write()
        duplicate = self.command("dot", "--previous", str(EXAMPLE))
        self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
        self.assertEqual(json.loads(duplicate.stdout)["disposition"], "duplicate")
        self.write(revision=2, status="waiting", next_step="انتظر تشغيل الاختبار المجدول.")
        advanced = self.command("dot", "--previous", str(EXAMPLE))
        self.assertEqual(advanced.returncode, 0, advanced.stderr)
        self.assertEqual(json.loads(advanced.stdout)["disposition"], "advanced")
        with self.assertRaisesRegex(RecordError, "stale"):
            check_record(self.record, "dot", read_record(self.path))

    def test_rejects_wrong_destination_and_equivocation(self):
        self.write()
        wrong = self.command("chatgpt-work")
        self.assertEqual(wrong.returncode, 1)
        self.assertIn("different recipient", wrong.stderr)
        self.write(next_step="افحص آخر دليل متاح.")
        conflict = self.command("dot", "--previous", str(EXAMPLE))
        self.assertEqual(conflict.returncode, 1)
        self.assertIn("conflicts", conflict.stderr)
        self.write(goal_id="different-goal", revision=2)
        with self.assertRaisesRegex(RecordError, "different continuation stream"):
            check_record(read_record(self.path), "dot", self.record)

    def test_rejects_invalid_fields_and_statuses(self):
        cases = [
            ({"schema": "hakim.continuation/v2"}, "unsupported"),
            ({"revision": True}, "positive exact JSON integer"),
            ({"revision": 9_007_199_254_740_992}, "positive exact JSON integer"),
            ({"goal_id": "../../db"}, "invalid goal_id"),
            ({"updated_at": "2026-02-30T19:54:00Z"}, "valid timestamp"),
            ({"status": "blocked"}, "requires a blocker"),
            ({"status": "complete"}, "cannot include a next step"),
            ({"status": "pending"}, "unknown continuation status"),
            ({"authority_token": "sample"}, "must match"),
            ({"goal_label": "الفصل\nالأول"}, "single line"),
        ]
        for changes, error in cases:
            with self.subTest(changes=changes):
                self.write(**changes)
                with self.assertRaisesRegex(RecordError, error):
                    read_record(self.path)

    def test_rejects_ambiguous_or_oversize_documents(self):
        for contents, error in [
            (b'{"status":"active","status":"complete"}', "duplicate JSON member"),
            (b"\xff", "invalid UTF-8 JSON"),
            (b" " * 16_385, "exceeds 16384 bytes"),
        ]:
            with self.subTest(error=error):
                self.path.write_bytes(contents)
                with self.assertRaisesRegex(RecordError, error):
                    read_record(self.path)


if __name__ == "__main__":
    unittest.main()
