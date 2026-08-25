# Continuous Execution Contract v1

## Objective
Keep the autonomous factory progressing until the project reaches a verified terminal state, without requiring a user message for ordinary work.

## Loop
WAKE → HEALTH_CHECK → LOAD_STATE → SELECT_NEXT_UNBLOCKED_TASK → EXECUTE → VALIDATE → CHECKPOINT → REPLAN → CONTINUE.

## No false continuity
A scheduler tick is not progress by itself. Each cycle must either:
1. complete a real task and checkpoint its result;
2. repair a real failure;
3. create a justified gap/research task; or
4. record an external dependency block.

## Terminal states
The factory stops only when:
- all release gates pass and a final release artifact is verified; or
- a sovereign decision is genuinely required and has been recorded as such.

## External interruptions
GitHub Actions, network, quotas, credentials, and third-party services may interrupt execution. The durable state must make the next scheduled run resume from the last valid checkpoint rather than restarting blindly.

## Anti-stall
Repeatedly selecting the same task without a state change is a stall. Detect it, classify the cause, change strategy, and create a recovery task.

## Human intervention
No human message is required for ordinary research, writing, testing, repair, or project management. Human intervention is reserved for explicit sovereign gates or unavailable external authority/credentials.
