"""
main.py
=======
Main entry point for the planning system.

Responsibilities:
- Initialize Planner
- Provide simple CLI-style interaction
- Demonstrate execution flow
"""

from datetime import datetime, timedelta
from planner import Planner, Task, Priority, Status


def seed_sample_tasks(planner: Planner) -> None:
    """
    Adds initial tasks for testing or first-run usage.
    """
    planner.add_task(
        Task(
            title="Setup planning system",
            description="Initialize planner and verify workflow",
            priority=Priority.CRITICAL,
            due_at=datetime.utcnow() + timedelta(hours=2),
        )
    )

    planner.add_task(
        Task(
            title="Review planner logic",
            description="Check prioritization and task flow",
            priority=Priority.HIGH,
            due_at=datetime.utcnow() + timedelta(days=1),
        )
    )

    planner.add_task(
        Task(
            title="Refactor if needed",
            priority=Priority.MEDIUM,
        )
    )


def print_task(task: Task) -> None:
    """
    Pretty print a single task.
    """
    print(
        f"- {task.title}\n"
        f"  Priority : {task.priority.name}\n"
        f"  Status   : {task.status.value}\n"
        f"  Due      : {task.due_at if task.due_at else 'N/A'}\n"
    )


def print_all_tasks(planner: Planner) -> None:
    """
    Print all tasks in the planner.
    """
    print("\n📋 All Tasks:\n")
    for task in planner.list_tasks():
        print_task(task)


def run(planner: Planner) -> None:
    """
    Core execution flow.
    """
    print("🚀 Planner started\n")

    print_all_tasks(planner)

    next_task = planner.next_task()
    if not next_task:
        print("✅ No pending tasks.")
        return

    print("➡️ Next task to execute:\n")
    print_task(next_task)

    print("▶️ Starting task...\n")
    planner.start_task(next_task.title)

    print("✅ Completing task...\n")
    planner.complete_task(next_task.title)

    print_all_tasks(planner)


def main() -> None:
    """
    Application entry point.
    """
    planner = Planner()
    seed_sample_tasks(planner)
    run(planner)


if __name__ == "__main__":
    main()
