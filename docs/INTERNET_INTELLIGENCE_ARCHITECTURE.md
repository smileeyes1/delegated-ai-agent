# HAKIM Ω — Internet Intelligence Architecture

## Objective
Provide real remote AI without requiring a local model, heavy device compute, Azure, institutional approval, or payment.

## Thin-client rule
The device performs only: intent capture, normalization, cache lookup, small deterministic transforms, transport, rendering, and verification. No large model download or background inference is required.

## Optimization stack
1. Exact response cache.
2. Request normalization and bounded context.
3. Metered-network prompt cap.
4. Provider health and exponential cooldown.
5. Multi-provider failover.
6. Zero-cost policy outside this transport layer.
7. Optional LAN/local/WebGPU only when explicitly beneficial.
8. Persistent state so a reconnect does not repeat completed work.

## Non-standard intelligence sources
- Free public inference endpoints where legitimately available.
- Provider free tiers/quotas.
- Open-source models exposed through hosted inference.
- Trusted LAN compute from another device.
- Browser WebGPU when device capability permits and model storage is acceptable.
- Cached previously verified answers.
- Deterministic micro-capabilities for tasks that do not need an LLM.

## Safety boundaries
- No bypassing authentication, paywalls, quotas, or provider restrictions.
- No credential harvesting.
- No hidden billing.
- Paid routes remain blocked by HAKIM's global zero-cost policy.
- Sensitive institutional data must not be routed to public providers without explicit policy authorization.

## Proof boundary
This module proves routing mechanics and device-light behavior through unit tests. It does not claim a live provider is available until a real endpoint responds in a runtime test.
