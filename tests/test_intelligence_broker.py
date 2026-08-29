import unittest
from app.intelligence_broker import IntelligenceBroker, Provider

class Cache:
    def __init__(self): self.data = {}
    def get(self, k): return self.data.get(k)
    def set(self, k, v): self.data[k] = v

class BrokerTests(unittest.TestCase):
    def test_quota_and_latency_routing(self):
        p1 = Provider('slow', {'text'}, quota_remaining=2, latency_ms=100, call=lambda p,c:'slow')
        p2 = Provider('fast', {'text'}, quota_remaining=5, latency_ms=10, call=lambda p,c:'fast')
        r = IntelligenceBroker([p1,p2]).execute('text','x')
        self.assertEqual(r.provider, 'fast')

    def test_failover_and_cooldown(self):
        bad = Provider('bad', {'text'}, call=lambda p,c: (_ for _ in ()).throw(RuntimeError()))
        good = Provider('good', {'text'}, call=lambda p,c:'ok')
        r = IntelligenceBroker([bad,good]).execute('text','x')
        self.assertEqual(r.provider, 'good')
        self.assertEqual(r.attempts, ['bad','good'])
        self.assertGreater(bad.failures, 0)

    def test_sensitive_blocks_public_provider(self):
        public = Provider('public', {'text'}, sensitive_ok=False, call=lambda p,c:'bad')
        with self.assertRaises(RuntimeError): IntelligenceBroker([public]).execute('text','x',sensitive=True)

    def test_cache(self):
        cache = Cache()
        calls=[]
        p=Provider('ai', {'text'}, call=lambda p,c: (calls.append(1) or 'answer'))
        b=IntelligenceBroker([p],cache)
        self.assertFalse(b.execute('text','x',cache_key='k').cached)
        self.assertTrue(b.execute('text','x',cache_key='k').cached)
        self.assertEqual(len(calls),1)

if __name__ == '__main__': unittest.main()
