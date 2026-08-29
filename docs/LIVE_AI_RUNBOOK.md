# HAKIM Ω — Live AI Runbook

## Goal
Run real remote inference while keeping device compute low and spend at exactly $0 by default.

## Runtime secrets
Credentials are environment variables only:
- OPENROUTER_API_KEY
- GEMINI_API_KEY
- GROQ_API_KEY
- CEREBRAS_API_KEY

Never commit values to Git, source files, logs, screenshots, or chat.

## Routing order
The Broker may choose among configured free providers according to capability, quota, latency, health, and privacy policy. A provider is not considered live merely because its environment variable exists.

## Live proof
A live proof requires a real runtime request that returns non-empty text. Unit tests and mocks do not count as live proof.

## Zero-cost gate
Only providers explicitly configured as free/zero-cost for the selected route may be called. Paid fallback is forbidden. Quota exhaustion causes failover or a controlled no-provider result.

## Device policy
No model download, no background inference, no local GPU requirement. Requests are bounded and cacheable.

## Failure handling
NOT_CONFIGURED -> skip
429/quota -> skip/cooldown
5xx/network -> cooldown/failover
empty response -> failover
sensitive request to public provider -> deny
all providers unavailable -> controlled fallback/error
