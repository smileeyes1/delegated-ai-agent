# AUTONOMY ARCHITECTURE LOCK

## Canonical executor
`.github/workflows/book-free-runner.yml` is the sole scheduled executor for autonomous book production.

## Supporting workflows
Integrity, E2E proof, compile, and self-heal may remain event-driven support gates. Legacy research/orchestration workflows are manual-only and must not schedule competing production cycles.

## Single-writer rule
Only the canonical executor may autonomously mutate book production state on a scheduled cycle. Supporting workflows validate or repair; they do not create competing research cycles.

## Progress rule
Every autonomous cycle must produce a real state change, a justified repair, a justified gap task, or an explicit external-dependency block. A scheduler tick without progress is not success.

## Completion rule
The factory continues until a verified release or a genuine sovereign decision gate. `RELEASE_CHECK.py` remains authoritative; presence of a draft never equals release readiness.

## Recovery rule
Failures are durable. The next cycle resumes from the last valid checkpoint and must not silently reset or bypass a blocked gate.
