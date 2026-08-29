# HAKIM Ω — Next Action

## Current action
Build the model gateway and deterministic local/mock model path, then connect it to planner → runtime.

## Acceptance criteria
- Accept a normalized HAKIM intent.
- Select a model provider through an abstraction, not provider-specific core logic.
- Run with a deterministic local/mock model when no cloud provider exists.
- Clearly label simulated/local output.
- Preserve provider identity and execution mode in audit events.
- Pass planner → model gateway → runtime without Azure, Foundry, Graph, Teams, approvals, or payment.
- Fail closed when a requested external provider is unavailable.

## After this action
Build automated recovery/resume, then run regression across planner, permissions, audit, capability registry, runtime, continuity, and model gateway.

## External capability path
Azure / Foundry / Entra / Graph / Teams / SharePoint / OneDrive remain optional adapters and must never become core dependencies.

## Resume protocol
At the beginning of every new execution session, read CURRENT_MISSION.md, PROJECT_STATE.md, and this file, then inspect the latest repository commit and CI evidence before continuing.
