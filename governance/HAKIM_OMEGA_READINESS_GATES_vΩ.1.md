# HAKIM Ω — MASTER READINESS GATES vΩ.1

A gate is PASS only when evidence exists. Missing evidence is NOT PASS.

## G0 Core Integrity
- Governance baseline present and protected.
- Protected tests present.
- No unauthorized governance mutation.

## G1 Self-Steering
- State transitions are deterministic and policy-gated.
- Illegal transitions are rejected.
- Adoption requires evidence and regression PASS.

## G2 Continuity
- Persistent mission state exists.
- Interrupted work can resume from checkpoint.
- Current-state record is maintained.

## G3 Recovery
- Backup restoration is tested.
- Rollback is tested.
- Failure injection produces safe recovery or safe block.

## G4 Truth
- Important claims have provenance/evidence semantics.
- Unknown is not converted to success.
- Completion cannot be asserted without evidence.

## G5 Security
- Permission boundaries are enforced outside model judgment.
- Secrets are isolated.
- Tool actions are auditable.
- Adversarial tests pass.

## G6 Provider Resilience
- Model/provider abstraction exists.
- At least one tested fallback path exists where practical.
- Degraded/offline behavior is defined.

## G7 Engineering Autonomy
- HAKIM can inspect repository state.
- Create controlled changes.
- Run tests.
- Read failures.
- Repair within authority.
- Produce evidence.
- Prepare a PR.

## G8 Product Readiness
- Core user workflows pass E2E acceptance.
- Data export/import works.
- Accessibility and localization are validated for supported locales.

## G9 Operational Readiness
- Logs/metrics/health checks exist.
- Incident records exist.
- Release and rollback procedures are tested.

## G10 Real-World Acceptance
- Representative tasks pass.
- Critical known failure classes have mitigations.
- No critical unresolved blocker remains.

## Final gate
`PRODUCTION-READY` is permitted only when all required gates are PASS with traceable evidence. Otherwise the status must explicitly remain NOT READY.
