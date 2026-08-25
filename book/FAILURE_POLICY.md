# Autonomous Failure Policy v1

## State machine
`RUN → VALIDATE → PASS → CHECKPOINT → NEXT`

or

`RUN → FAIL → CLASSIFY → REPAIR → REGRESSION → PASS`

or, when evidence is insufficient:

`RUN → BLOCKED → GAP_TASK → RESEARCH → VALIDATE`

or, when ambiguity remains material:

`RUN → HUMAN_SOVEREIGN_REVIEW`

## Anti-loop rules
- bounded retries per strategy;
- repeated failure changes strategy or escalates capability;
- no success status may be written merely because a retry occurred;
- stale artifacts cannot satisfy a newer gate;
- a blocked task remains visible and cannot be bypassed by drafting around it.
