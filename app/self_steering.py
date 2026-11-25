"""HAKIM Ω self-steering control plane.

This module is deliberately deterministic: the model may propose actions, but
this state machine decides whether a transition is legal under governance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class State(str, Enum):
    OBSERVE = "OBSERVE"
    DIAGNOSE = "DIAGNOSE"
    PRIORITIZE = "PRIORITIZE"
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    EVIDENCE = "EVIDENCE"
    REGRESSION = "REGRESSION"
    GOVERNANCE_GATE = "GOVERNANCE_GATE"
    ADOPTED = "ADOPTED"
    ROLLED_BACK = "ROLLED_BACK"
    BLOCKED = "BLOCKED"
    LEARN = "LEARN"


class ChangeClass(str, Enum):
    LOCAL_REPAIR = "LOCAL_REPAIR"
    NORMAL_IMPROVEMENT = "NORMAL_IMPROVEMENT"
    GOVERNANCE_CHANGE = "GOVERNANCE_CHANGE"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"


@dataclass(frozen=True)
class Evidence:
    objective: str
    observed_problem: str
    root_cause: str
    expected_effect: str
    risk: str
    tests: tuple[str, ...]
    test_results: tuple[str, ...]
    regression_result: str
    decision: str

    def complete(self) -> bool:
        values = (
            self.objective, self.observed_problem, self.root_cause,
            self.expected_effect, self.risk, self.tests, self.test_results,
            self.regression_result, self.decision,
        )
        return all(bool(v) for v in values)


@dataclass
class Candidate:
    change_id: str
    change_class: ChangeClass
    baseline_ref: str
    state: State = State.OBSERVE
    evidence: Evidence | None = None
    human_approval: bool = False
    history: list[State] = field(default_factory=lambda: [State.OBSERVE])


class GovernanceViolation(RuntimeError):
    """Raised when a requested transition violates immutable governance."""


class SelfSteeringEngine:
    """Deterministic gatekeeper around an otherwise model-driven agent."""

    _ALLOWED: dict[State, frozenset[State]] = {
        State.OBSERVE: frozenset({State.DIAGNOSE, State.BLOCKED}),
        State.DIAGNOSE: frozenset({State.PRIORITIZE, State.BLOCKED}),
        State.PRIORITIZE: frozenset({State.PLAN, State.BLOCKED}),
        State.PLAN: frozenset({State.EXECUTE, State.BLOCKED}),
        State.EXECUTE: frozenset({State.VERIFY, State.BLOCKED}),
        State.VERIFY: frozenset({State.EVIDENCE, State.EXECUTE, State.BLOCKED}),
        State.EVIDENCE: frozenset({State.REGRESSION, State.BLOCKED}),
        State.REGRESSION: frozenset({State.GOVERNANCE_GATE, State.ROLLED_BACK, State.BLOCKED}),
        State.GOVERNANCE_GATE: frozenset({State.ADOPTED, State.ROLLED_BACK, State.BLOCKED}),
        State.ADOPTED: frozenset({State.LEARN}),
        State.ROLLED_BACK: frozenset({State.LEARN}),
        State.BLOCKED: frozenset({State.LEARN}),
        State.LEARN: frozenset(),
    }

    def transition(self, candidate: Candidate, target: State) -> Candidate:
        current = candidate.state
        if target not in self._ALLOWED[current]:
            raise GovernanceViolation(f"illegal transition: {current.value} -> {target.value}")

        if target is State.GOVERNANCE_GATE:
            if candidate.evidence is None or not candidate.evidence.complete():
                raise GovernanceViolation("governance gate requires complete evidence")

        if target is State.ADOPTED:
            self._assert_adoption_allowed(candidate)

        candidate.state = target
        candidate.history.append(target)
        return candidate

    def _assert_adoption_allowed(self, candidate: Candidate) -> None:
        if candidate.evidence is None or not candidate.evidence.complete():
            raise GovernanceViolation("adoption requires complete evidence")
        if candidate.evidence.regression_result.upper() != "PASS":
            raise GovernanceViolation("adoption requires regression PASS")
        if candidate.evidence.decision.upper() != "ADOPT":
            raise GovernanceViolation("evidence decision must be ADOPT")
        if candidate.change_class in {
            ChangeClass.GOVERNANCE_CHANGE,
            ChangeClass.PERMISSION_CHANGE,
        } and not candidate.human_approval:
            raise GovernanceViolation("governance/permission changes require human approval")

    @staticmethod
    def protected_tests(results: Iterable[str]) -> bool:
        """True only when every supplied protected result is an explicit PASS."""
        values = [str(x).upper() for x in results]
        return bool(values) and all(x == "PASS" for x in values)
