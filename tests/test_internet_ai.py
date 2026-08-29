import os
import unittest

from app.internet_ai import RemoteOpenAICompatibleProvider, ResponseCache, provider_from_env
from app.model_gateway import ModelRequest, ModelResponse


class InternetAIContractTests(unittest.TestCase):
    def test_environment_discovery_needs_no_hardcoded_secret(self):
        old = {k: os.environ.get(k) for k in ("TESTAI_URL", "TESTAI_MODEL", "TESTAI_API_KEY")}
        try:
            os.environ["TESTAI_URL"] = "https://example.invalid"
            os.environ["TESTAI_MODEL"] = "free-model"
            os.environ.pop("TESTAI_API_KEY", None)
            provider = provider_from_env("TESTAI")
            self.assertIsNotNone(provider)
            self.assertEqual(provider.api_key, "")
            self.assertTrue(provider.free_only)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_paid_provider_is_unavailable_under_free_only(self):
        provider = RemoteOpenAICompatibleProvider(
            "paid", "https://example.invalid", "model", requires_payment=True, free_only=True
        )
        self.assertFalse(provider.available(ModelRequest("x")))

    def test_response_cache(self):
        cache = ResponseCache()
        request = ModelRequest("hello")
        response = ModelResponse("world", "test", "model", True)
        cache.put(request, response)
        self.assertEqual(cache.get(request).text, "world")


if __name__ == "__main__":
    unittest.main()
