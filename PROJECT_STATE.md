# HAKIM Ω — Persistent Project State

Status: ACTIVE

## Truth boundary
The repository is the persistent project memory. Chat sessions are not the source of truth.

## Runtime target
HAKIM Core must run with zero Azure cost and zero external institutional approval. Cloud and enterprise services are optional capability adapters.

## Proven / implemented
- Existing planning foundation.
- Existing audit and permission modules.
- Enterprise Azure / Foundry gate.
- Enterprise provisioning manifest.
- Fail-closed readiness evaluation.
- Persistent mission/resume documentation.
- Provider-independent capability registry.
- Provider-independent execution runtime.
- Durable mission-state store.
- Model Gateway and Zero-Cost Policy.
- Model Fabric dynamic routing.
- Deterministic local fallback provider.
- Local OpenAI-compatible provider contract.
- Browser WebGPU/WASM provider contract.
- Trusted LAN inference-node contract.
- Intent → Model Fabric → Runtime pipeline.
- Crash-safe recovery manager with idempotent checkpoints.
- Expanded CI regression workflow.
- Lightweight Internet AI provider adapter for OpenAI-compatible free-tier endpoints.
- Environment-only provider discovery; no secrets stored in repository.
- Response cache to reduce repeat Internet inference.
- Lightweight Internet AI Mesh with cache, failover, sensitive-data guard, prompt-size guard, and zero-cost enforcement.
- Zero-cost-first Fabric bootstrap with Internet → LAN → local → deterministic fallback.
- Intelligence Optimizer: normalize requests, classify deterministic tasks, generate cache keys, and prefer Internet AI for general tasks without loading local models.
- In-memory response cache abstraction.
- Capability/quota-aware Intelligence Broker with provider health, ranking, cooldown, failover, cache integration, and sensitive-data gating.
- Intelligence Broker regression tests.

## Not yet proven
- Full real LLM inference on target Android hardware.
- Automated CI run for the latest head (must be observed before claiming pass).
- Full assurance suite across all historical modules.
- Browser WebGPU execution implementation.
- LAN transport implementation and authentication.
- Live free-cloud account quotas/availability (provider terms and quotas change).
- Real Foundry runtime.
- Real Graph/Teams/SharePoint/OneDrive access.

## External dependency policy
No personal Azure trial. No payment dependency. No approval dependency for core development.

## Zero-cost policy
`MAX_SPEND = $0.00` by default. Paid providers are blocked. Exhausted/unavailable free providers fail over to another eligible provider or local/limited mode. No silent paid upgrade.

## Device-load policy
Internet-first by default. No model download or background inference is required for the normal path. Device work is limited to request normalization, cache lookup, transport, rendering, and deterministic micro-capabilities. Local LLM/WebGPU is opt-in based on detected capability.

## Evidence policy
Configured != connected != authorized != proven. Mocks and simulations must be labeled explicitly.
