# Verified Research → Draft Adapter v1

## Objective
Replace the deterministic smoke fixture with a controlled scholarly-production adapter.

## Input contract
Each research unit must provide:
- question
- primary-source references where available
- evidence records with stable provenance
- source type
- uncertainty level
- disagreements/counter-evidence

## Transformation rules
1. Never create a source that is absent from the evidence ledger.
2. Never upgrade `unverified`, `possible`, or `disputed` evidence into certainty by prose alone.
3. Keep direct quotation, paraphrase, interpretation, inference, and application as separate fields.
4. A draft paragraph must carry the evidence IDs supporting its material claims.
5. Missing evidence produces `BLOCKED`, not invented content.
6. Counter-evidence must be surfaced before a claim can become `candidate`.
7. `candidate` is not `approved`.

## Draft lifecycle
`RESEARCHED → MAPPED → DRAFTED → CRITICIZED → REPAIRED → REGRESSION_TESTED → CANDIDATE`

Final religious claims remain subject to the appropriate human-sovereign gate when the automated evidence is insufficient.

## Exit condition
The adapter may replace the E2E fixture only after it passes the same orchestration checks and produces a traceable draft whose claims can be traced back to evidence records.
