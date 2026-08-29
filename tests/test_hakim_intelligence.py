import unittest
from unittest.mock import patch
from app import hakim_intelligence

class HakimEntryTests(unittest.TestCase):
    def test_key_is_deterministic_and_non_plaintext(self):
        k = hakim_intelligence._key('text','secret prompt','ctx')
        self.assertEqual(k, hakim_intelligence._key('text','secret prompt','ctx'))
        self.assertNotIn('secret prompt', k)
    def test_ask_uses_broker_result(self):
        class FakeResult:
            value = type('R', (), {'text':'hello'})()
            provider='fake'; attempts=['fake']; cached=False
        class FakeBroker:
            def execute(self, *args, **kwargs): return FakeResult()
        with patch.object(hakim_intelligence, 'build_hakim', return_value=(FakeBroker(), [])):
            r = hakim_intelligence.ask('hi')
        self.assertEqual(r['text'], 'hello')
        self.assertEqual(r['provider'], 'fake')

if __name__ == '__main__': unittest.main()
