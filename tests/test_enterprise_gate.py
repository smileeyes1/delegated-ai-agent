import json
import unittest

from app.enterprise_gate import (
    BLOCKED_EXTERNAL,
    PROVEN,
    READY_FOR_PROVISIONING,
    evaluate_manifest,
)


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


class EnterpriseGateTests(unittest.TestCase):
    def test_empty_example_manifest_is_blocked_external(self):
        manifest = {
            "personal_azure_trial_allowed": False,
            "azure": {},
            "foundry": {},
            "assurance": {},
        }
        result = evaluate_manifest(manifest)
        self.assertEqual(result["state"], BLOCKED_EXTERNAL)
        self.assertIn("subscription_id", result["missing"])
        self.assertFalse(result["personal_azure_trial_allowed"])

    def test_configured_but_unproven_is_not_proven(self):
        result = evaluate_manifest(base_manifest())
        self.assertEqual(result["state"], READY_FOR_PROVISIONING)
        self.assertEqual(result["missing"], [])

    def test_only_explicit_assurance_can_reach_proven(self):
        manifest = base_manifest()
        manifest["assurance"] = {"identity": PROVEN, "foundry_runtime": PROVEN}
        result = evaluate_manifest(manifest)
        self.assertEqual(result["state"], PROVEN)

    def test_manifest_is_json_serializable(self):
        self.assertTrue(json.dumps(evaluate_manifest(base_manifest())))


if __name__ == "__main__":
    unittest.main()
