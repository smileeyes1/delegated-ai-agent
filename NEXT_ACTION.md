# HAKIM Ω — Next Action

## Current phase
MODEL-FABRIC → E2E

## Completed and recorded
- Enterprise Azure / Foundry gate.
- Provider-independent capability registry.
- Provider-independent execution runtime.
- Durable continuity state.
- Model Gateway and Zero-Cost Policy.
- Model Fabric dynamic routing.
- Deterministic local fallback.
- Local OpenAI-compatible provider contract.
- Browser WebGPU/WASM contract.
- Trusted LAN inference-node contract.

## Current action
Connect normalized HAKIM intent → planner → ModelFabric → Runtime, with deterministic local fallback when no real model is reachable.

## Acceptance criteria
- Core execution works without Azure, Foundry, Graph, Teams, approvals, or payment.
- Real local provider is used when an actual local endpoint is available.
- Deterministic fallback is explicitly labeled as limited local intelligence, never as an LLM.
- Paid providers are blocked by policy.
- Free-provider failure triggers failover.
- Sensitive requests avoid public-cloud providers unless policy explicitly permits them.
- Provider identity, mode, route, failures, and final status are auditable.

## After this action
1. Automated interruption/recovery and resume.
2. Full regression across planner, permissions, audit, capabilities, runtime, continuity, and Model Fabric.
3. Android/local-model packaging path.
4. Browser WebGPU execution path.
5. Optional free-cloud adapters.
6. Enterprise Foundry/Graph adapters remain last-mile capabilities.

## Resume protocol
At every new session: read CURRENT_MISSION.md, PROJECT_STATE.md, and NEXT_ACTION.md; inspect latest commit and CI evidence; continue from the first unproven acceptance criterion. Never restart from conversation memory alone.
