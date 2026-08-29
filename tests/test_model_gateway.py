import unittest

from app.model_gateway import ModelGateway, ModelRequest, ModelResponse, ZeroCostPolicy


class FakeProvider:
    def __init__(self, name, mode="local", payment=False, available=True, fail=False):
        self.name = name
        self.mode = mode
        self.requires_payment = payment
        self._available = available
        self.fail = fail

    def available(self, request):
        return self._available

    def generate(self, request):
        if self.fail:
            raise TimeoutError()
        return ModelResponse("real answer", self.name, "test-model", True)


class ModelGatewayTests(unittest.TestCase):
    def test_local_provider_works_with_zero_cost_policy(self):
        gateway = ModelGateway([FakeProvider("local")])
        result = gateway.generate(ModelRequest("hello"))
        self.assertEqual(result.provider, "local")

    def test_paid_provider_is_blocked(self):
        gateway = ModelGateway([FakeProvider("paid", payment=True)])
        with self.assertRaises(RuntimeError):
            gateway.generate(ModelRequest("hello"))

    def test_sensitive_request_skips_public_cloud(self):
        gateway = ModelGateway([FakeProvider("cloud", mode="public_cloud"), FakeProvider("local")])
        result = gateway.generate(ModelRequest("private", sensitive=True))
        self.assertEqual(result.provider, "local")

    def test_failover(self):
        gateway = ModelGateway([FakeProvider("first", fail=True), FakeProvider("second")])
        result = gateway.generate(ModelRequest("hello"))
        self.assertEqual(result.provider, "second")
        self.assertEqual(gateway.failures[0]["provider"], "first")


if __name__ == "__main__":
    unittest.main()
