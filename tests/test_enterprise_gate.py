import json

from app.enterprise_gate import BLOCKED_EXTERNAL, PROVEN, READY_FOR_PROVISIONING, evaluate_manifest


def base_manifest():
    return {
        "personal_azure_trial_allowed": False,
        "azure": {
            "tenant_id": "tenant",
            "subscription_id": "subscription",
            "resource_group": "rg-hakim-dev",
            "location": "eastus",
        },
        "foundry": {
            "resource_name": "foundry",
            "project_name": "hakim",
            "project_endpoint": "https://example.services.ai.azure.com",
        },
        "assurance": {
            "identity": "NOT_PROVEN",
            "foundry_runtime": "NOT_PROVEN",
        },
    }


def test_empty_example_manifest_is_blocked_external():
    manifest = {
        "personal_azure_trial_allowed": False,
        "azure": {},
        "foundry": {},
        "assurance": {},
    }
    result = evaluate_manifest(manifest)
    assert result["state"] == BLOCKED_EXTERNAL
    assert "subscription_id" in result["missing"]
    assert result["personal_azure_trial_allowed"] is False


def test_configured_but_unproven_is_not_proven():
    result = evaluate_manifest(base_manifest())
    assert result["state"] == READY_FOR_PROVISIONING
    assert result["missing"] == []


def test_only_explicit_assurance_can_reach_proven():
    manifest = base_manifest()
    manifest["assurance"] = {"identity": PROVEN, "foundry_runtime": PROVEN}
    result = evaluate_manifest(manifest)
    assert result["state"] == PROVEN


def test_manifest_is_json_serializable():
    assert json.dumps(evaluate_manifest(base_manifest()))
