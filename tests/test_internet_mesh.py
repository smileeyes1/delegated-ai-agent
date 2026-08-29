import unittest
from app.internet_mesh import InternetAIMesh, MemoryResponseCache
from app.model_gateway import ModelRequest, ModelResponse

class Fake:
    def __init__(self, name, mode="public_cloud", payment=False, fail=False):
        self.name=name; self.mode=mode; self.requires_payment=payment; self.fail=fail; self.calls=0
    def available(self, request): return True
    def generate(self, request):
        self.calls += 1
        if self.fail: raise RuntimeError("down")
        return ModelResponse("real", self.name, "free-test", True)

class InternetMeshTests(unittest.TestCase):
    def test_cache_avoids_second_remote_call(self):
        p=Fake("free")
        m=InternetAIMesh([p])
        r=ModelRequest("same")
        self.assertEqual(m.generate(r).text, "real")
        self.assertEqual(m.generate(r).text, "real")
        self.assertEqual(p.calls, 1)
    def test_failover(self):
        bad=Fake("bad", fail=True); good=Fake("good")
        self.assertEqual(InternetAIMesh([bad,good]).generate(ModelRequest("x")).provider, "good")
    def test_paid_blocked(self):
        paid=Fake("paid", payment=True)
        with self.assertRaises(RuntimeError): InternetAIMesh([paid]).generate(ModelRequest("x"))
    def test_sensitive_public_cloud_blocked(self):
        public=Fake("public")
        with self.assertRaises(RuntimeError): InternetAIMesh([public]).generate(ModelRequest("x", sensitive=True))

if __name__ == "__main__": unittest.main()
