# HAKIM Ω — Next Action

## Current action
Implement and prove the provider-independent runtime orchestration.

## Acceptance criteria
- Accept a normalized intent.
- Build an executable plan.
- Resolve required capabilities through a registry.
- Use a local/mock provider when cloud providers are unavailable.
- Execute deterministic tool calls.
- Record each transition in durable state/audit data.
- Fail closed for unavailable capabilities.
- Distinguish simulated output from real external execution.
- Provide a resume-safe execution record.

## After this action
Run regression across planner, permissions, audit, enterprise gate, and runtime tests. Then proceed to model gateway and educational workflow contracts.

## Blocker
None. Azure/Foundry/Graph/Teams are not blockers for this action.
