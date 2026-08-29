"""Enterprise Azure / Foundry provisioning gate.

This module deliberately distinguishes configuration from proven runtime access.
It never attempts Azure authentication and never stores credentials.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BLOCKED_EXTERNAL = "BLOCKED-EXTERNAL"
READY_FOR_PROVISIONING = "READY-FOR-PROVISIONING"
PROVEN = "PROVEN"


def load_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Enterprise manifest must be a JSON object")
    return value


def evaluate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return a fail-closed readiness assessment."""
    azure = manifest.get("azure") or {}
    foundry = manifest.get("foundry") or {}
    assurance = manifest.get("assurance") or {}

    required_ids = {
        "tenant_id": azure.get("tenant_id"),
        "subscription_id": azure.get("subscription_id"),
        "resource_group": azure.get("resource_group"),
        "location": azure.get("location"),
        "foundry_resource_name": foundry.get("resource_name"),
        "foundry_project_name": foundry.get("project_name"),
        "foundry_project_endpoint": foundry.get("project_endpoint"),
    }
    missing = sorted(key for key, value in required_ids.items() if not value)

    if missing:
        state = BLOCKED_EXTERNAL
    elif assurance and all(value == PROVEN for value in assurance.values()):
        state = PROVEN
    else:
        state = READY_FOR_PROVISIONING

    return {
        "state": state,
        "missing": missing,
        "personal_azure_trial_allowed": manifest.get("personal_azure_trial_allowed") is True,
        "assurance": assurance,
    }


def main() -> int:
    manifest = load_manifest("config/enterprise.azure.example.json")
    print(json.dumps(evaluate_manifest(manifest), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
