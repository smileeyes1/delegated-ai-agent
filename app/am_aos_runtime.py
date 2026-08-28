"""AM-AOS governed autonomous mission runtime core.

This module turns the AM-AOS control-plane rules into executable, testable
primitives using only the Python standard library. It intentionally keeps
policy/authority separate from orchestration and treats evidence as a first
class object.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from hashlib import sha256
from time import time
from typing import Any, Callable, Dict, Iterable, List, Optional
import copy
import json
import threading
import uuid


class MissionState(str, Enum):
    CREATED="CREATED"; VALIDATING="VALIDATING"; PLANNED="PLANNED"; AUTHORIZED="AUTHORIZED"
    EXECUTING="EXECUTING"; VERIFYING="VERIFYING"; REPAIRING="REPAIRING"; REGRESSION="REGRESSION"
    GATED="GATED"; RELEASE_CANDIDATE="RELEASE_CANDIDATE"; RELEASED="RELEASED"; DELIVERING="DELIVERING"
    DELIVERED="DELIVERED"; POST_RELEASE="POST_RELEASE"; COMPLETED="COMPLETED"; BLOCKED="BLOCKED"
    FAILED="FAILED"; CANCELLED="CANCELLED"

class TaskState(str, Enum):
    PROPOSED="PROPOSED"; READY="READY"; AUTHORIZED="AUTHORIZED"; RUNNING="RUNNING"
    OBSERVED="OBSERVED"; VERIFYING="VERIFYING"; PASSED="PASSED"; FAILED="FAILED"
    RETRYING="RETRYING"; REPAIRING="REPAIRING"; BLOCKED="BLOCKED"; CANCELLED="CANCELLED"; COMPLETED="COMPLETED"

class Decision(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; REQUIRE_APPROVAL="REQUIRE_APPROVAL"; REQUIRE_EVIDENCE="REQUIRE_EVIDENCE"

class EvidenceStatus(str, Enum):
    SUFFICIENT="SUFFICIENT"; INSUFFICIENT="INSUFFICIENT"; INVALID="INVALID"

@dataclass(frozen=True)
class Requirement:
    id: str
    description: str
    critical: bool = False

@dataclass
class Evidence:
    id: str
    requirement_id: str
    test_id: str
    artifact_id: Optional[str]
    observation: Any
    method: str
    scope: str
    status: EvidenceStatus
    hash: str
    timestamp: float = field(default_factory=time)

@dataclass
class Artifact:
    id: str
    version: str
    payload: Any
    hash: str
    verification_state: str = "UNVERIFIED"
    release_state: str = "UNRELEASED"

@dataclass
class Event:
    id: str
    action: str
    actor: str
    before: str
    after: str
    authorization: Decision
    result: str
    evidence_ids: List[str] = field(default_factory=list)
    artifact_id: Optional[str] = None
    timestamp: float = field(default_factory=time)

@dataclass
class Task:
    id: str
    requirement_id: str
    action: str
    state: TaskState = TaskState.PROPOSED
    attempts: int = 0
    result: Any = None

class AppendOnlyEventLog:
    def __init__(self) -> None:
        self._events: List[Event] = []
        self._lock = threading.Lock()

    def append(self, event: Event) -> None:
        with self._lock:
            if self._events and event.timestamp < self._events[-1].timestamp:
                raise ValueError("event timestamp regression")
            self._events.append(copy.deepcopy(event))

    def all(self) -> List[Event]:
        with self._lock:
            return copy.deepcopy(self._events)

class StateStore:
    """Thread-safe checkpoint store with monotonic revisions."""
    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def save(self, mission_id: str, state: Dict[str, Any]) -> int:
        with self._lock:
            previous = self._data.get(mission_id, {}).get("revision", 0)
            revision = previous + 1
            self._data[mission_id] = {"revision": revision, "state": copy.deepcopy(state)}
            return revision

    def load(self, mission_id: str) -> Dict[str, Any]:
        with self._lock:
            if mission_id not in self._data:
                raise KeyError(mission_id)
            return copy.deepcopy(self._data[mission_id])

class EvidenceStore:
    def __init__(self) -> None:
        self._items: Dict[str, Evidence] = {}

    def put(self, evidence: Evidence) -> None:
        self._items[evidence.id] = copy.deepcopy(evidence)

    def get(self, evidence_id: str) -> Evidence:
        return copy.deepcopy(self._items[evidence_id])

    def for_requirement(self, requirement_id: str) -> List[Evidence]:
        return [copy.deepcopy(x) for x in self._items.values() if x.requirement_id == requirement_id]

class ArtifactRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, Artifact] = {}

    @staticmethod
    def digest(payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()
        return sha256(raw).hexdigest()

    def register(self, artifact_id: str, version: str, payload: Any) -> Artifact:
        artifact = Artifact(artifact_id, version, copy.deepcopy(payload), self.digest(payload))
        self._items[artifact_id] = artifact
        return copy.deepcopy(artifact)

    def verify_identity(self, artifact_id: str) -> bool:
        a = self._items[artifact_id]
        return self.digest(a.payload) == a.hash

class PolicyEngine:
    """Conservative default policy: local reversible work is autonomous."""
    def evaluate(self, action: str, reversible: bool = True, high_impact: bool = False,
                 requires_approval: bool = False) -> Decision:
        if high_impact or requires_approval:
            return Decision.REQUIRE_APPROVAL
        if not reversible:
            return Decision.REQUIRE_APPROVAL
        return Decision.ALLOW

class AssuranceEngine:
    def __init__(self, requirements: Iterable[Requirement], evidence: EvidenceStore) -> None:
        self.requirements = {r.id: r for r in requirements}
        self.evidence = evidence

    def status(self, requirement_id: str) -> str:
        items = self.evidence.for_requirement(requirement_id)
        if any(e.status == EvidenceStatus.INVALID for e in items):
            return "FAILED"
        if not items:
            return "UNTESTED"
        if any(e.status == EvidenceStatus.SUFFICIENT for e in items):
            return "PASSED"
        return "NOT PROVEN"

    def all_critical_passed(self) -> bool:
        return all(self.status(r.id) == "PASSED" for r in self.requirements.values() if r.critical)

class MissionRuntime:
    """Small but real execution loop: authorize -> act -> observe -> verify -> checkpoint."""
    ALLOWED = {
        MissionState.CREATED: {MissionState.VALIDATING, MissionState.CANCELLED},
        MissionState.VALIDATING: {MissionState.PLANNED, MissionState.BLOCKED},
        MissionState.PLANNED: {MissionState.AUTHORIZED, MissionState.BLOCKED},
        MissionState.AUTHORIZED: {MissionState.EXECUTING, MissionState.BLOCKED},
        MissionState.EXECUTING: {MissionState.VERIFYING, MissionState.REPAIRING, MissionState.FAILED},
        MissionState.VERIFYING: {MissionState.GATED, MissionState.REPAIRING, MissionState.FAILED},
        MissionState.REPAIRING: {MissionState.REGRESSION, MissionState.FAILED},
        MissionState.REGRESSION: {MissionState.EXECUTING, MissionState.GATED, MissionState.FAILED},
        MissionState.GATED: {MissionState.RELEASE_CANDIDATE, MissionState.BLOCKED},
        MissionState.RELEASE_CANDIDATE: {MissionState.RELEASED, MissionState.BLOCKED},
        MissionState.RELEASED: {MissionState.DELIVERING},
        MissionState.DELIVERING: {MissionState.DELIVERED, MissionState.FAILED},
        MissionState.DELIVERED: {MissionState.POST_RELEASE},
        MissionState.POST_RELEASE: {MissionState.COMPLETED, MissionState.FAILED},
    }

    def __init__(self, mission_id: Optional[str] = None) -> None:
        self.id = mission_id or str(uuid.uuid4())
        self.state = MissionState.CREATED
        self.requirements: Dict[str, Requirement] = {}
        self.tasks: Dict[str, Task] = {}
        self.evidence = EvidenceStore()
        self.artifacts = ArtifactRegistry()
        self.events = AppendOnlyEventLog()
        self.checkpoints = StateStore()
        self.policy = PolicyEngine()
        self.assurance = AssuranceEngine([], self.evidence)
        self._lock = threading.RLock()

    def add_requirement(self, description: str, critical: bool = False, requirement_id: Optional[str] = None) -> str:
        rid = requirement_id or str(uuid.uuid4())
        self.requirements[rid] = Requirement(rid, description, critical)
        self.assurance = AssuranceEngine(self.requirements.values(), self.evidence)
        return rid

    def add_task(self, requirement_id: str, action: str, task_id: Optional[str] = None) -> str:
        if requirement_id not in self.requirements:
            raise KeyError(requirement_id)
        tid = task_id or str(uuid.uuid4())
        self.tasks[tid] = Task(tid, requirement_id, action, TaskState.READY)
        return tid

    def transition(self, new_state: MissionState, actor: str = "orchestrator",
                   authorization: Decision = Decision.ALLOW, result: str = "") -> None:
        with self._lock:
            if new_state not in self.ALLOWED.get(self.state, set()):
                raise ValueError(f"invalid transition {self.state}->{new_state}")
            old = self.state
            self.state = new_state
            self.events.append(Event(str(uuid.uuid4()), "STATE_TRANSITION", actor, old.value,
                                     new_state.value, authorization, result))
            self.checkpoint()

    def checkpoint(self) -> int:
        snapshot = {
            "mission_id": self.id,
            "state": self.state.value,
            "tasks": {k: {"state": v.state.value, "attempts": v.attempts} for k, v in self.tasks.items()},
        }
        return self.checkpoints.save(self.id, snapshot)

    def record_evidence(self, requirement_id: str, test_id: str, observation: Any,
                        method: str, scope: str, sufficient: bool,
                        artifact_id: Optional[str] = None) -> str:
        if requirement_id not in self.requirements:
            raise KeyError(requirement_id)
        payload = json.dumps(observation, sort_keys=True, ensure_ascii=False, default=str)
        eid = str(uuid.uuid4())
        evidence = Evidence(eid, requirement_id, test_id, artifact_id, copy.deepcopy(observation),
                            method, scope, EvidenceStatus.SUFFICIENT if sufficient else EvidenceStatus.INSUFFICIENT,
                            sha256(payload.encode()).hexdigest())
        self.evidence.put(evidence)
        self.events.append(Event(str(uuid.uuid4()), "RECORD_EVIDENCE", "assurance", self.state.value,
                                 self.state.value, Decision.ALLOW, evidence.status.value, [eid], artifact_id))
        self.checkpoint()
        return eid

    def run_task(self, task_id: str, executor: Callable[[Task], Any], verifier: Callable[[Any], bool],
                 *, reversible: bool = True, high_impact: bool = False) -> bool:
        task = self.tasks[task_id]
        decision = self.policy.evaluate(task.action, reversible, high_impact)
        if decision != Decision.ALLOW:
            task.state = TaskState.BLOCKED
            return False
        with self._lock:
            if self.state != MissionState.EXECUTING:
                raise ValueError("mission must be EXECUTING")
            if task.state in {TaskState.PASSED, TaskState.COMPLETED}:
                return True
            task.attempts += 1
            task.state = TaskState.RUNNING
            try:
                task.result = executor(task)
                task.state = TaskState.OBSERVED
                task.state = TaskState.VERIFYING
                ok = bool(verifier(task.result))
                if ok:
                    task.state = TaskState.PASSED
                    self.record_evidence(task.requirement_id, f"verify:{task.id}", task.result,
                                         "runtime-verifier", "task-result", True)
                    task.state = TaskState.COMPLETED
                    return True
                task.state = TaskState.FAILED
                self.record_evidence(task.requirement_id, f"verify:{task.id}", task.result,
                                     "runtime-verifier", "task-result", False)
                return False
            finally:
                self.checkpoint()

    def release_gate(self) -> bool:
        """Strict release gate: every requirement must have sufficient evidence."""
        if any(self.assurance.status(rid) != "PASSED" for rid in self.requirements):
            return False
        if self.state != MissionState.GATED:
            return False
        self.transition(MissionState.RELEASE_CANDIDATE)
        self.transition(MissionState.RELEASED)
        return True

    def snapshot(self) -> Dict[str, Any]:
        return {
            "mission_id": self.id,
            "state": self.state.value,
            "requirements": {k: asdict(v) for k, v in self.requirements.items()},
            "tasks": {k: {**asdict(v), "state": v.state.value} for k, v in self.tasks.items()},
            "assurance": {rid: self.assurance.status(rid) for rid in self.requirements},
            "events": [asdict(e) for e in self.events.all()],
        }
