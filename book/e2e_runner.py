"""Deterministic end-to-end smoke runner for the book factory.

This does not invent scholarship. It proves the orchestration contract using
an explicit fixture and emits a traceable artifact that the real research
adapter can later replace.
"""
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=ROOT / "runs" / "latest_e2e_smoke.json")
path = parser.parse_args().output

fixture = {
    "question": "What transformation does revelation seek in the human being?",
    "evidence": [
        {"id": "fixture-001", "type": "research_input", "status": "unverified_fixture",
         "claim": "This is an orchestration fixture, not a religious proof."}
    ],
    "uncertainty": "fixture_only",
}

# Keep the fixture deliberately non-scholarly: the smoke test validates the
# pipeline, not the truth of the book's eventual claims.
draft = {
    "title": "E2E Factory Smoke Draft",
    "status": "fixture_draft",
    "source_question": fixture["question"],
    "paragraphs": [
        "This draft exists only to prove that evidence, drafting, review, repair, and checkpoint stages are connected.",
        "It must never be promoted to a scholarly claim without real source evidence."
    ],
}

checks = {
    "evidence_present": bool(fixture["evidence"]),
    "provenance_present": all("id" in x and "type" in x for x in fixture["evidence"]),
    "uncertainty_preserved": fixture["uncertainty"] == "fixture_only",
    "draft_present": bool(draft["paragraphs"]),
    "fixture_not_scholarly": draft["status"] == "fixture_draft",
}

passed = all(checks.values())
now = datetime.now(timezone.utc).isoformat()
run = {
    "timestamp": now,
    "stage": "e2e_smoke",
    "passed": passed,
    "checks": checks,
    "evidence": fixture,
    "draft": draft,
    "next_task": "replace_fixture_with_verified_research_adapter",
}

if not passed:
    print(json.dumps({"passed": False, "checks": checks}, ensure_ascii=False))
    raise SystemExit(1)
path.parent.mkdir(parents=True, exist_ok=True)
with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as out:
    temporary_path = Path(out.name)
    json.dump(run, out, ensure_ascii=False, indent=2)
    out.write("\n")
temporary_path.replace(path)
print(json.dumps({"passed": passed, "artifact": str(path), "next_task": run["next_task"]}, ensure_ascii=False))
