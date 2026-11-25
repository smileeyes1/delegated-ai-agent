"""Identify requests understood by the existing plan builder."""

import re


def extract_intent(request: str) -> dict[str, str]:
    """Classify GitHub repository requests without calling a model or service."""
    if re.search(r"\b(?:github|غيت\s*هاب|جيت\s*هاب|جِت\s*هاب)\b", request, re.IGNORECASE):
        return {"domain": "github", "goal": "repository_task"}
    return {"domain": "unknown", "goal": "unknown"}
