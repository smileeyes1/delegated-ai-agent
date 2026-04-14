
"""
Permission and approval module
Responsible for enforcing human authorization before any sensitive action.
"""

# Actions that always require explicit human approval
SENSITIVE_ACTIONS = {
    "create_issue",
    "create_pull_request",
    "merge_pull_request",
    "delete_repository",
    "run_ci",
}

def require_approval(plan: list) -> dict:
    """
    Inspect the execution plan and determine which actions
    require human approval.

    Returns a structured approval request.
    """
    approval_required = []

    for step in plan:
        action = step.get("action")

        if action in SENSITIVE_ACTIONS or step.get("requires_approval", False):
            approval_required.append({
                "action": action,
                "description": step.get("description"),
                "approved": False
            })

    return {
        "approval_needed": len(approval_required) > 0,
        "actions": approval_required
    }
