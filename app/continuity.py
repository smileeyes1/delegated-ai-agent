"""Durable, resume-safe mission state for HAKIM."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class MissionState:
    mission_id: str
    phase: str
    current_action: str
    status: str = "RUNNING"
    completed: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    next_action: str = ""
    updated_at: str = ""


class ContinuityStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, state: MissionState) -> None:
        state.updated_at = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def load(self) -> MissionState:
        data: dict[str, Any] = json.loads(self.path.read_text(encoding="utf-8"))
        return MissionState(**data)

    def exists(self) -> bool:
        return self.path.exists()
