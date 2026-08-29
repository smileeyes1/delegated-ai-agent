import unittest

from app.local_model import DeterministicLocalProvider
from app.model_gateway import ModelRequest


class LocalModelTests(unittest.TestCase):
    def test_local_fallback_is_always_available(self):
        provider = DeterministicLocalProvider()
        response = provider.generate(ModelRequest("درس", task="lesson"))
        self.assertTrue(provider.available(ModelRequest("x")))
        self.assertEqual(response.mode if hasattr(response, "mode") else provider.mode, "local")
        self.assertTrue(response.proven)
        self.assertEqual(response.provider, "deterministic-local")


if __name__ == "__main__":
    unittest.main()
