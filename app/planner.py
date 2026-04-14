
"""
planner.py
==========
Core planning module for task scheduling, prioritization, and execution control.

Design goals:
- Simple
- Deterministic
- Extensible
- No external dependencies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime


# -----------------------------
# Enums
# -----------------------------

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Status(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


# -----------------------------
# Data Models
# -----------------------------

@dataclass
class Task:
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: Status = Status.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    due_at: Optional[datetime] = None

    def is_overdue(self) -> bool:
        if self.due_at is None:
            return False
        return datetime.utcnow() > self.due_at


# -----------------------------
# Planner Core
# -----------------------------

class Planner:
    def __init__(self) -> None:
        self.tasks: List[Task] = []

    # -------- Task Management --------

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        for t in self.tasks:
            if t.title == title:
                self.tasks.remove(t)
                return True
        return False

    def get_task(self, title: str) -> Optionalfor task in self.tasks:
            if task.title == title:
                return task
        return None

    # -------- Querying --------

    def list_tasks(self, status: Optional[Status] = None) -> Listif status is None:
            return list(self.tasks)
        return [t for t in self.tasks if t.status == status]

    def overdue_tasks(self) -> Listreturn [t for t in self.tasks if t.is_overdue()]

    # -------- Planning Logic --------

    def next_task(self) -> Optional"""
        Returns the highest-priority pending task.
        Deterministic ordering:
        1. Status == PENDING
        2. Highest priority
        3. Earliest due date
        """
        pending = [t for t in self.tasks if t.status == Status.PENDING]
        if not pending:
            return None

        pending.sort(
            key=lambda t: (
                -t.priority.value,
                t.due_at if t.due_at else datetime.max,
                t.created_at
            )
        )
        return pending[0]

    # -------- Execution Control --------

    def start_task(self, title: str) -> bool:
        task = self.get_task(title)
        if task and task.status == Status.PENDING:
            task.status = Status.IN_PROGRESS
            return True
        return False

    def complete_task(self, title: str) -> bool:
        task = self.get_task(title)
        if task and task.status in (Status.IN_PROGRESS, Status.PENDING):
            task.status = Status.DONE
            return True
        return False

    def block_task(self, title: str) -> bool:
        task = self.get_task(title)
        if task and task.status != Status.DONE:
            task.status = Status.BLOCKED
            return True
        return False


# -----------------------------
# Example Usage (Optional)
# -----------------------------
if __name__ == "__main__":
    planner = Planner()

    planner.add_task(
        Task(
            title="Write planner module",
            description="Core planning logic",
            priority=Priority.CRITICAL
        )
    )

    planner.add_task(
        Task(
            title="Review code",
            priority=Priority.HIGH
        )
    )

    next_up = planner.next_task()
    if next_up:
        print(f"Next task: {next_up.title} [{next_up.priority.name}]")
