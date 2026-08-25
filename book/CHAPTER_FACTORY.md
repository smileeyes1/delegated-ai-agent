# Chapter Factory v1

A chapter is produced as a bounded evidence-controlled unit.

## Pipeline
1. Select highest-value unresolved question.
2. Build an evidence map.
3. Build an argument map.
4. Draft section-by-section with evidence IDs.
5. Run factual/scholarly critic.
6. Run contradiction and uncertainty checks.
7. Run structural/language critic.
8. Repair identified defects.
9. Re-run all applicable regression tests.
10. Mark `candidate` only when all automated gates pass.

## Required chapter record
- thesis/question
- scope and exclusions
- evidence ledger
- competing interpretations
- uncertainty map
- argument map
- draft
- critic findings
- repair history
- regression results
- status

## Prohibited shortcuts
- no unsupported citation generation
- no fabricated quotation
- no silent removal of disagreement
- no promotion from draft to approved solely because the prose is fluent

## Continuous production
After a candidate chapter is checkpointed, the factory selects the next highest-value unblocked chapter task. If a later discovery materially changes an earlier chapter, that chapter becomes `REVIEW_REQUIRED` and is queued for repair before release.
