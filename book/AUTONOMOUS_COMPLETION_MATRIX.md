# Autonomous Completion Matrix v1

## Purpose
Close the remaining gap between an automated scheduler and a genuinely self-directed book-production system.

## Required closed loops
- [x] durable state
- [x] scheduled orchestration
- [x] self-heal contract
- [x] evidence ledger contract
- [x] chapter gate
- [x] task selection contract
- [x] cost-first policy
- [ ] verified source acquisition with provenance
- [ ] evidence extraction + validation
- [ ] counter-evidence generation + review
- [ ] argument synthesis with claim-to-evidence links
- [ ] autonomous bounded drafting
- [ ] independent critique passes
- [ ] automatic repair with regression protection
- [ ] release assembly
- [ ] dependency-aware impact analysis when evidence changes
- [ ] repeatability proof across at least two real chapter runs
- [ ] long-run idle/gap discovery

## Completion rule
An item changes to `[x]` only after runtime evidence exists. Documentation is not proof.

## Autonomous continuation rule
If no task is currently runnable, the system must audit gaps, stale assumptions, failed validations, changed sources, and unfinished deliverables, then enqueue the highest-value repair/research task. It must not manufacture content merely to remain active.

## Sovereign gate
If evidence remains materially ambiguous after automated research and criticism, the item becomes `HUMAN_SOVEREIGN_REVIEW`, preserving all evidence and competing interpretations rather than forcing a conclusion.
