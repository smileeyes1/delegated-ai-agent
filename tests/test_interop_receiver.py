import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "interop" / "example.json"


class ContinuationReceiverTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        self.inbox = self.folder / "inbox #1.sqlite3"

    def command(self, *args, producer="hakim", recipient="dot"):
        return subprocess.run(
            [sys.executable, "-m", "interop", *args, "--db", str(self.inbox),
             "--from", producer, "--for", recipient],
            cwd=ROOT, capture_output=True, check=False, timeout=20,
        )

    def receive(self, path=EXAMPLE, *, digest=None, **route):
        approved = digest if digest is not None else sha256(path.read_bytes()).hexdigest()
        return self.command("receive", str(path), "--sha256", approved, **route)

    def record(self, name, **changes):
        record = json.loads(EXAMPLE.read_bytes())
        path = self.folder / name
        path.write_text(json.dumps({**record, **changes}, ensure_ascii=False), encoding="utf-8")
        return path

    def latest(self, **route):
        result = self.command("latest", "book-factory-e2e", **route)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_wrong_digest_and_route_leave_no_inbox(self):
        for kwargs, message in [
            ({"digest": "f" * 64}, b"does not match the approved SHA-256"),
            ({"producer": "automation"}, b"does not match the approved route"),
            ({"recipient": "chatgpt-work"}, b"different recipient"),
        ]:
            with self.subTest(kwargs=kwargs):
                result = self.receive(**kwargs)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertFalse(self.inbox.exists())

    def test_competing_processes_store_one_receipt_with_exact_readback(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(self.receive, (EXAMPLE,) * 4))
        for response in responses:
            self.assertEqual(response.returncode, 0, response.stderr)
        receipts = [json.loads(response.stdout) for response in responses]
        self.assertCountEqual([receipt.pop("disposition") for receipt in receipts],
                              ["new", "duplicate", "duplicate", "duplicate"])
        self.assertEqual(receipts, [receipts[0]] * 4)
        self.assertEqual(self.latest(), EXAMPLE.read_bytes())
        with closing(sqlite3.connect(self.inbox)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM continuation_receipts").fetchone()[0], 1)

    def test_advancement_preserves_receipts_and_rejects_stale_or_conflicting_input(self):
        self.assertEqual(self.receive().returncode, 0)
        next_record = self.record("next.json", revision=2, next_step="افحص نتيجة الاختبار.")
        advanced = self.receive(next_record)
        self.assertEqual(advanced.returncode, 0, advanced.stderr)
        self.assertEqual(json.loads(advanced.stdout)["disposition"], "advanced")
        conflict = self.record("conflict.json", revision=2, next_step="استخدم دليلًا آخر.")
        for record, message in [(EXAMPLE, b"stale"), (conflict, b"conflicts")]:
            with self.subTest(record=record):
                rejected = self.receive(record)
                self.assertEqual(rejected.returncode, 1)
                self.assertIn(message, rejected.stderr)
        self.assertEqual(self.latest(), next_record.read_bytes())
        with closing(sqlite3.connect(self.inbox)) as db:
            first = db.execute("SELECT payload FROM continuation_receipts WHERE revision = 1").fetchone()[0]
        self.assertEqual(first, EXAMPLE.read_bytes())

    def test_equal_document_with_different_bytes_cannot_replace_accepted_receipt(self):
        self.assertEqual(self.receive().returncode, 0)
        reformatted = self.record("reformatted.json")
        self.assertEqual(json.loads(reformatted.read_bytes()), json.loads(EXAMPLE.read_bytes()))
        self.assertNotEqual(reformatted.read_bytes(), EXAMPLE.read_bytes())
        result = self.receive(reformatted)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"bytes conflict", result.stderr)
        self.assertEqual(self.latest(), EXAMPLE.read_bytes())

    def test_separate_route_reads_only_its_stream_and_detects_tampering(self):
        self.assertEqual(self.receive().returncode, 0)
        work_record = self.record("work.json", producer="dot", recipient="chatgpt-work")
        route = {"producer": "dot", "recipient": "chatgpt-work"}
        self.assertEqual(self.receive(work_record, **route).returncode, 0)
        self.assertEqual(self.latest(**route), work_record.read_bytes())
        self.assertEqual(self.latest(), EXAMPLE.read_bytes())
        with closing(sqlite3.connect(self.inbox)) as db, db:
            db.execute("UPDATE continuation_receipts SET payload = ? WHERE recipient = 'dot'", (b"{}",))
        result = self.command("latest", "book-factory-e2e")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"digest does not match", result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(self.latest(**route), work_record.read_bytes())


if __name__ == "__main__":
    unittest.main()
