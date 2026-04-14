
"""
Audit and accountability module
Responsible for logging all decisions, approvals, and actions
for transparency and traceability.
"""

import json
from datetime import datetime
from pathlib import Path

AUDIT_LOG_PATH = Path("data/audit.log")


def log_event(event_type: str, payload: dict) -> None:
    """
    Record an auditable event with timestamp.

    :param event_type: Type of the event (intent, plan, approval, execution)
    :param payload: Relevant event data
    """
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "payload": payload
    }

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
