import unittest

from app.intelligence_optimizer import IntelligenceOptimizer, MemoryCache
from app.model_gateway import ModelRequest


class IntelligenceOptimizerTests(unittest.TestCase):
    def test_math_is_kept_off_the_network(self):
        decision = IntelligenceOptimizer().prepare(ModelRequest("٣ + ٤", task="math"))
        self.assertEqual(decision.mode, "deterministic")

    def test_general_request_prefers_internet(self):
        decision = IntelligenceOptimizer().prepare(ModelRequest("اكتب درسًا", task="lesson"))
        self.assertEqual(decision.mode, "internet")
        self.assertEqual(len(decision.cache_key), 64)

    def test_cache_round_trip(self):
        cache = MemoryCache()
        cache.put("k", "answer")
        self.assertEqual(cache.get("k"), "answer")
        self.assertEqual(len(cache), 1)


if __name__ == "__main__":
    unittest.main()
