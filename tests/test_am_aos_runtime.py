import pytest
from app.am_aos_runtime import MissionRuntime, MissionState, TaskState


def prepared():
    r = MissionRuntime("m-test")
    rid = r.add_requirement("runtime execution is verified", critical=True, requirement_id="R1")
    tid = r.add_task(rid, "local-test", task_id="T1")
    return r, tid


def advance_to_execute(r):
    r.transition(MissionState.VALIDATING)
    r.transition(MissionState.PLANNED)
    r.transition(MissionState.AUTHORIZED)
    r.transition(MissionState.EXECUTING)


def test_success_requires_evidence_and_gate():
    r, tid = prepared()
    advance_to_execute(r)
    assert r.run_task(tid, lambda t: {"ok": True}, lambda x: x["ok"])
    assert r.tasks[tid].state == TaskState.COMPLETED
    assert r.assurance.status("R1") == "PASSED"
    r.transition(MissionState.VERIFYING)
    r.transition(MissionState.GATED)
    assert r.release_gate() is True
    assert r.state == MissionState.RELEASED


def test_false_pass_is_rejected_when_verifier_fails():
    r, tid = prepared()
    advance_to_execute(r)
    assert r.run_task(tid, lambda t: {"ok": "not-really"}, lambda x: False) is False
    assert r.tasks[tid].state == TaskState.FAILED
    assert r.assurance.status("R1") == "NOT PROVEN"
    r.transition(MissionState.VERIFYING)
    assert r.release_gate() is False


def test_invalid_transition_is_rejected():
    r, _ = prepared()
    with pytest.raises(ValueError):
        r.transition(MissionState.RELEASED)


def test_artifact_identity_detects_mutation():
    r, _ = prepared()
    a = r.artifacts.register("A1", "1", {"x": 1})
    assert r.artifacts.verify_identity(a.id)
    r.artifacts._items[a.id].payload["x"] = 2
    assert not r.artifacts.verify_identity(a.id)
