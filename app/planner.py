
"""
Planning module
Responsible for converting intent into executable steps (without execution).
"""

def build_plan(intent: dict) -> list:
    """
    Generate a step-by-step plan based on the extracted intent.
    No step is executed automatically.
    """
    domain = intent.get("domain")
    goal = intent.get("goal")

    plan = []

    if domain == "github" and goal == "repository_task":
        plan.append({
            "action": "analyze_repository",
            "description": "Read repository structure and files for analysis",
            "requires_approval": False
        })

        plan.append({
            "action": "create_issue",
            "description": "Create a GitHub issue with findings and suggestions",
            "requires_approval": True
        })

    return plan
