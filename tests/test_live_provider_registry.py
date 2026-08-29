import unittest
from app.live_provider_registry import build_probes, discover

class LiveRegistryTests(unittest.TestCase):
    def test_discovery_never_exposes_secret_values(self):
        result = discover({"GEMINI_API_KEY": "secret"})
        self.assertTrue(next(x for x in result if x["name"] == "gemini")["configured"])
        for item in result:
            self.assertNotIn("secret", str(item))
            self.assertIn("env_key", item)

    def test_registry_has_multiple_capability_sources(self):
        result = discover({})
        names = {x["name"] for x in result}
        self.assertTrue({"openrouter", "gemini", "groq"}.issubset(names))

    def test_missing_probe_is_not_claimed_live(self):
        result = build_probes({})
        self.assertTrue(all(x["status"] == "NOT_CONFIGURED" for x in result))

    def test_probe_can_prove_live_only_when_runtime_call_succeeds(self):
        result = build_probes({"gemini": lambda: {"ok": True}})
        gemini = next(x for x in result if x["name"] == "gemini")
        self.assertEqual(gemini["status"], "LIVE")

if __name__ == "__main__":
    unittest.main()
