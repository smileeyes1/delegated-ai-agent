# HAKIM Ω Release Contract

## Critical acceptance
1. Runtime loads on GitHub Pages.
2. Free AI route is optional and resilient; failure is explicit.
3. No provider secret is shipped to the browser.
4. Generation and validation are separate stages.
5. Invalid educational content cannot receive PASS.
6. Export is blocked for NO-GO content.
7. Mathematical visual order is explicit and tested.
8. Numeric visual groups are count-verified.
9. Repeated output is detected and normalized/rejected.
10. Offline/deterministic features remain usable without AI.
11. Every release identifies its commit and verification scope.

## State model
BUILT: code exists.
TESTED: specified automated checks pass.
DEPLOYED: Pages deployment exists.
RUNTIME VERIFIED: deployed URL was exercised successfully.
FIELD PILOT: limited real-world trial completed.
FIELD READY: all defined field criteria met.

## Release rule
Critical failure = NO-GO. Never infer runtime verification from a successful commit or build. Never infer correctness from a green UI badge alone.
