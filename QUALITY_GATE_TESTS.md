# HAKIM Ω Quality Gate v8 — regression cases

## Critical acceptance cases

- Grade 1 math range 10: `٣ + ٥ = ٨` → PASS.
- Grade 1 math range 10: `٧ + ٢ = ٩` → PASS.
- Grade 1 math range 10: `١٠ + ١ = ١١` → FAIL (`MATH_RESULT_OUT_OF_RANGE`).
- Grade 1 foundational number lesson containing multiplication/division → FAIL (`GRADE1_SCOPE_OPERATION_MISMATCH`).
- Incorrect equation such as `٣ + ٥ = ٩` → FAIL (`MATH_EQUATION_ERROR`).

## Release rule

`Validator PASS` is not sufficient unless the resource-level gate also passes. A critical quality failure is `NO-GO` until repaired and regression-tested.
