"""Top-level deterministic integrity gate for the autonomous book factory."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
required = [
    ROOT / "FACTORY_STATE.json",
    ROOT / "CHAPTER_01_STATE.json",
    ROOT / "CHAPTER_01_EVIDENCE_LEDGER.json",
    ROOT / "AUTONOMOUS_COMPLETION_MATRIX.md",
    ROOT / "RELEASE_GATES.md",
]
missing = [str(p.relative_to(ROOT.parent)) for p in required if not p.exists()]
if missing:
    raise SystemExit("VERIFY_FAIL missing: " + ", ".join(missing))

factory = json.loads((ROOT / "FACTORY_STATE.json").read_text(encoding="utf-8"))
chapter = json.loads((ROOT / "CHAPTER_01_STATE.json").read_text(encoding="utf-8"))
assert isinstance(factory, dict) and isinstance(chapter, dict)
assert "status" in factory
assert "status" in chapter
print("PASS: top-level durable state and governance files present")
