"""
Main application entry point
Combines intent extraction, planning, permission checking,
and auditing into a single controlled workflow.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from app.intent import extract_intent
from app.planner import build_plan
from app.permissions import require_approval
from app.audit import log_event


app = FastAPI(
    title="Delegated AI Agent",
    description="Human-authorized AI agent (GitHub-first)",
    version="0.1.0"
)


class UserRequest(BaseModel):
    request: str


@app.post("/request")
def handle_user_request(user_request: UserRequest):
    """
    Handle a single user request end-to-end
    without executing any external action.
    """

    # 1. Extract intent
    intent = extract_intent(user_request.request)
    log_event("intent", intent)

    # 2. Build execution plan
    plan = build_plan(intent)
    log_event("plan", {"plan": plan})

    # 3. Determine required approvals
    approval = require_approval(plan)
    log_event("approval_check", approval)

    # 4. Return response (no execution)
    return {
        "status": "waiting_for_approval",
        "intent": intent,
        "plan": plan,
        "approval": approval
    }

