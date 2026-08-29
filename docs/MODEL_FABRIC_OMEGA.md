# HAKIM Ω — Model Fabric Ω

## Objective
Provide real AI capability without making HAKIM dependent on a paid cloud provider, a single vendor, or continuous Internet access.

## Non-standard strategy

HAKIM treats intelligence as a federated capability, not as one API.

### Tier 0 — Deterministic cognition
Use code for arithmetic, counting, schema validation, policy checks, curriculum constraints, output validation, and other tasks where an LLM adds cost without adding reliable value.

### Tier 1 — Device-native inference
Run an open/quantized model on the user's own hardware. Preferred engines include llama.cpp and browser WebGPU/Transformers.js. This is the only layer that can guarantee zero recurring inference fees independent of third parties.

### Tier 2 — Opportunistic free inference
Use free quotas from cloud providers only when available. These are opportunistic accelerators, never dependencies.

Candidate adapters include Gemini free tier, Groq free limits, Hugging Face Inference Providers/free models, OpenRouter free models, and Cloudflare Workers AI where the current account/model quota permits free use.

### Tier 3 — Borrowed compute
Permit HAKIM to use a second device owned by the user or institution as a local inference node over a trusted local network. The primary device becomes the client; the secondary device supplies compute. No cloud subscription is required.

### Tier 4 — Browser inference
A PWA/web client can load a quantized model into the browser and execute inference with WASM or WebGPU. This is especially useful when installation of a native runtime is undesirable.

### Tier 5 — Enterprise acceleration
Azure Foundry, Entra, Graph, Teams, SharePoint and OneDrive are optional enterprise adapters. They increase capability, governance and institutional integration but are never required for HAKIM Core operation.

## Routing policy

The router selects a provider by task, privacy policy, hardware capability, availability, context size, structured-output/tool-call requirements, latency and quota.

Default priority:

1. deterministic tool when sufficient;
2. local model;
3. trusted local-network model node;
4. free cloud provider;
5. enterprise provider when configured and authorized.

The order is dynamic, not hard-coded.

## Zero-cost guard

`MAX_SPEND = 0` is the default safety policy.

A provider is blocked if it requires payment, billing activation, or a paid quota. Exhausted free quotas trigger failover. HAKIM must never silently upgrade to a paid route.

## Truth states

`AVAILABLE` = adapter exists.

`CONFIGURED` = local configuration exists.

`CONNECTED` = real provider connection succeeded.

`AUTHORIZED` = intended permissions succeeded.

`PROVEN` = the capability passed its assurance tests.

`BLOCKED` = unavailable under current policy/environment.

A mock provider is never reported as a real AI provider.

## Privacy routing

Institutional or sensitive material must not be sent to a free public provider unless an explicit policy permits it. Local inference is the default for sensitive data. Retrieval can also be performed locally before generation.

## Model diversity

HAKIM should support multiple model roles rather than searching for one universal model:

- small fast Arabic/general model for routine generation;
- stronger local model for reasoning;
- vision model for images/documents;
- embedding model for semantic retrieval;
- speech-to-text model;
- text-to-speech engine;
- deterministic math/validation engines;
- enterprise models when available.

## Failure behavior

If a provider fails, the router records the failure and tries the next eligible provider. If all model providers fail, HAKIM remains available in deterministic/limited mode rather than falsely claiming successful AI generation.

## Current implementation target

Build `ModelGateway` and adapters behind the existing provider-independent Runtime. Add routing, quota/cost policy, local-provider contracts, local-network-node contract, browser-provider contract, and enterprise adapter contracts. Then test failover and zero-cost enforcement in CI.
