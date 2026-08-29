import unittest

from app.model_providers import BrowserProviderContract, LocalOpenAICompatibleProvider, NetworkNodeContract


class ProviderContractTests(unittest.TestCase):
    def test_local_provider_is_zero_cost_capable(self):
        provider = LocalOpenAICompatibleProvider("ollama", "http://127.0.0.1:11434", "model")
        self.assertTrue(provider.available(None))
        self.assertFalse(provider.requires_payment)
        self.assertEqual(provider.mode, "local")

    def test_browser_contract_starts_unloaded(self):
        provider = BrowserProviderContract()
        self.assertFalse(provider.available(None))
        self.assertFalse(provider.requires_payment)

    def test_lan_node_is_optional(self):
        provider = NetworkNodeContract()
        self.assertFalse(provider.available(None))
        self.assertFalse(provider.requires_payment)


if __name__ == "__main__":
    unittest.main()
