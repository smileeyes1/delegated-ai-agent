import unittest

from app.internet_optimizer import IntelligenceOptimizer, InternetPolicy, NetworkProfile


class InternetOptimizerTests(unittest.TestCase):
    def test_cache_prevents_second_network_call(self):
        calls = []
        def provider(prompt, context):
            calls.append(1)
            return "AI"
        opt = IntelligenceOptimizer()
        first = opt.run("  اكتب   درس  ", [("free-a", provider)])
        second = opt.run("اكتب درس", [("free-a", provider)])
        self.assertEqual(first[0], "AI")
        self.assertEqual(second[1], "cache")
        self.assertEqual(len(calls), 1)

    def test_failover(self):
        def bad(prompt, context):
            raise RuntimeError("down")
        def good(prompt, context):
            return "OK"
        opt = IntelligenceOptimizer(InternetPolicy(max_attempts=3))
        value, provider, cached = opt.run("x", [("bad", bad), ("good", good)])
        self.assertEqual((value, provider, cached), ("OK", "good", False))

    def test_metered_network_compacts_request(self):
        seen = []
        def provider(prompt, context):
            seen.append((prompt, context))
            return "OK"
        opt = IntelligenceOptimizer(InternetPolicy(metered_max_prompt_chars=5))
        opt.run("123456789", [("free", provider)], context="abcdefgh", network=NetworkProfile(metered=True))
        self.assertLessEqual(len(seen[0][0]), 5)
        self.assertLessEqual(len(seen[0][1]), 5)

    def test_offline_is_explicit(self):
        opt = IntelligenceOptimizer()
        with self.assertRaisesRegex(RuntimeError, "OFFLINE"):
            opt.run("x", [("free", lambda p, c: "bad")], network=NetworkProfile(online=False))


if __name__ == "__main__":
    unittest.main()
