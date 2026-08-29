import unittest

from app.model_fabric import ModelFabric
from app.model_gateway import ModelRequest, ModelResponse, ZeroCostPolicy


class FakeProvider:
    def __init__(self, name, mode="local", requires_payment=False, available=True, fail=False):
        self.name = name
        self.mode = mode
        self.requires_payment = requires_payment
        self._available = available
        self.fail = fail

    def available(self, request):
        return self._available

    def generate(self, request):
        if self.fail:
            raise RuntimeError("failure")
        return ModelResponse("ok", self.name, "test", True)


class ModelFabricTests(unittest.TestCase):
    def test_sensitive_request_prefers_local(self):
        cloud = FakeProvider("cloud", mode="public_cloud")
        local = FakeProvider("local", mode="local")
        result = ModelFabric([cloud, local]).generate(ModelRequest("x", sensitive=True))
        self.assertEqual(result.provider, "local")

    def test_paid_provider_is_blocked(self):
        paid = FakeProvider("paid", requires_payment=True)
        with self.assertRaises(RuntimeError):
            ModelFabric([paid], ZeroCostPolicy()).generate(ModelRequest("x"))

    def test_failover(self):
        bad = FakeProvider("bad", fail=True)
        good = FakeProvider("good")
        result = ModelFabric([bad, good]).generate(ModelRequest("x"))
        self.assertEqual(result.provider, "good")
        self.assertEqual(len(ModelFabric([bad, good]).history), 0)


if __name__ == "__main__":
    unittest.main()
