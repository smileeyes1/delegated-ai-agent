import os, unittest
from unittest.mock import patch
from app.provider_runtime import GeminiAdapter, OpenAICompatibleAdapter, build_adapters

class RuntimeTests(unittest.TestCase):
    def test_unconfigured_never_calls_network(self):
        adapter = OpenAICompatibleAdapter('x','MISSING_KEY','https://invalid.example','m')
        with self.assertRaisesRegex(RuntimeError,'NOT_CONFIGURED'):
            adapter.generate('hello')
    def test_probe_exposes_boolean_only(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY':'secret'}, clear=True):
            p = GeminiAdapter().probe()
            self.assertEqual(p, {'provider':'gemini','configured':True,'adapter':'gemini'})
            self.assertNotIn('secret', str(p))
    def test_build_has_independent_adapters(self):
        names = [x.name for x in build_adapters()]
        self.assertEqual(names, ['openrouter','gemini','groq','cerebras'])

if __name__ == '__main__': unittest.main()
