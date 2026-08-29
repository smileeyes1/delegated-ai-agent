"""Crash-safe mission recovery primitives."""

from __future__ import annotations

from dataclasses import dataclass

from app.continuity import ContinuityStore, MissionState


@dataclass
class RecoveryManager:
    store: ContinuityStore

    def checkpoint(self, state: MissionState, action: str, status: str = "RUNNING") -> MissionState:
        state.current_action = action
        state.status = status
        self.store.save(state)
        return state

    def mark_completed(self, state: MissionState, action: str, evidence: str = "") -> MissionState:
        if action not in state.completed:
            state.completed.append(action)
        if evidence and evidence not in state.evidence:
            state.evidence.append(evidence)
        state.current_action = action
        self.store.save(state)
        return state

    def mark_failure(self, state: MissionState, action: str, error: str) -> MissionState:
        state.failures.append(f"{action}:{error}")
        state.current_action = action
        state.status = "RECOVERY_REQUIRED"
        self.store.save(state)
        return state

    def resume(self) -> MissionState:
        state = self.store.load()
        if state.status == "COMPLETED":
            return state
        state.status = "RESUMABLE"
        self.store.save(state)
        return state
