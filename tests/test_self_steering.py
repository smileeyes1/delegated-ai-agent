import unittest

from app.self_steering import (
    Candidate,
    ChangeClass,
    Evidence,
    GovernanceViolation,
    SelfSteeringEngine,
    State,
)


class SelfSteeringTests(unittest.TestCase):
    def setUp(self):
        self.engine = SelfSteeringEngine()
        self.candidate = Candidate(
            change_id="TEST-001",
            change_class=ChangeClass.NORMAL_IMPROVEMENT,
            baseline_ref="main@baseline",
        )

    def advance_to(self, target):
        path = [
            State.DIAGNOSE, State.PRIORITIZE, State.PLAN,
            State.EXECUTE, State.VERIFY, State.EVIDENCE,
            State.REGRESSION, State.GOVERNANCE_GATE,
        ]
        for state in path:
            if self.candidate.state is not state:
                self.engine.transition(self.candidate, state)
            if state is target:
                return

    def test_happy_path_reaches_governance_gate(self):
        self.candidate.evidence = Evidence(
            objective="fix defect",
            observed_problem="test failure",
            root_cause="bad branch",
            expected_effect="tests pass",
            risk="low",
            tests=("unit", "regression"),
            test_results=("PASS", "PASS"),
            regression_result="PASS",
            decision="ADOPT",
        )
        self.advance_to(State.GOVERNANCE_GATE)
        self.assertEqual(self.candidate.state, State.GOVERNANCE_GATE)
        self.engine.transition(self.candidate, State.ADOPTED)
        self.assertEqual(self.candidate.state, State.ADOPTED)

    def test_cannot_skip_verification(self):
        with self.assertRaises(GovernanceViolation):
            self.engine.transition(self.candidate, State.ADOPTED)

    def test_failed_regression_cannot_be_adopted(self):
        self.candidate.evidence = Evidence(
            "fix", "bug", "cause", "effect", "low",
            ("unit",), ("PASS",), "FAIL", "ADOPT"
        )
        self.advance_to(State.GOVERNANCE_GATE)
        with self.assertRaises(GovernanceViolation):
            self.engine.transition(self.candidate, State.ADOPTED)

    def test_governance_change_requires_human_approval(self):
        self.candidate.change_class = ChangeClass.GOVERNANCE_CHANGE
        self.candidate.evidence = Evidence(
            "change rule", "gap", "old rule", "safer rule", "high",
            ("governance",), ("PASS",), "PASS", "ADOPT"
        )
        self.advance_to(State.GOVERNANCE_GATE)
        with self.assertRaises(GovernanceViolation):
            self.engine.transition(self.candidate, State.ADOPTED)
        self.candidate.human_approval = True
        self.engine.transition(self.candidate, State.ADOPTED)
        self.assertEqual(self.candidate.state, State.ADOPTED)

    def test_protected_tests_require_explicit_pass(self):
        self.assertTrue(self.engine.protected_tests(["PASS", "PASS"]))
        self.assertFalse(self.engine.protected_tests(["PASS", "UNKNOWN"]))
        self.assertFalse(self.engine.protected_tests([]))


if __name__ == "__main__":
    unittest.main()
