import unittest
from unittest.mock import patch

from app.model_adapters import OllamaProvider
from app.model_gateway import ModelRequest


class FakeResponse:
    status = 200
    def read(self):
        return b'{"choices":[{"message":{"content":"hello"}}]}'
    def __enter__(self): return self
    def __exit__(self, *args): return False


class LocalAdapterTests(unittest.TestCase):
    @patch("app.model_adapters.urlopen", return_value=FakeResponse())
    def test_ollama_openai_compatible_generation(self, urlopen):
        provider = OllamaProvider(model="test-model")
        result = provider.generate(ModelRequest("hello"))
        self.assertEqual(result.text, "hello")
        self.assertTrue(result.proven)
        self.assertEqual(result.provider, "ollama-local")
        self.assertTrue(urlopen.called)


if __name__ == "__main__":
    unittest.main()
