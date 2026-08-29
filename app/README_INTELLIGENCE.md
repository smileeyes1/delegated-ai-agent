# HAKIM Intelligence Runtime

Use `app.hakim_intelligence.ask()` as the single application-facing entry point for remote intelligence.

The entry point builds the zero-cost broker, discovers configured adapters from environment variables, routes by capability, caches repeat requests, and fails over between eligible providers.

No credentials belong in source control. A provider is only usable when its runtime credential exists. Live success must be proven by a real request; unit tests do not count as live proof.

Default device policy: network-first, no model download, no background inference.
