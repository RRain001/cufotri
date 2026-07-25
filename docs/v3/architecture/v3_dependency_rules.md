# V3 dependency rules

Status: `ARCHITECTURE_ONLY`

Allowed dependency direction:

```text
core types
  -> forcing and source contracts
  -> transport and deposition
  -> environmental media
  -> food and animal
  -> dose
  -> validation and reporting
```

Rules:

1. Core contract modules import no physics, runners, validation, or provenance.
2. Soil and plant never import a case runner.
3. Physics never imports a validation runner, report writer, or external-data
   adapter.
4. Dose consumes activities/concentrations and cannot mutate environmental
   inventories.
5. Provenance and reporting observe results and cannot participate in numeric
   calculations.
6. V3 modules cannot modify V2 defaults, V2 loader behavior, or tagged cases.
7. Validation adapters may import schemas and metrics, but not private physics
   functions.
8. A future `src/cteas_ufotri/v3/` tree is rejected by the architecture gate
   until the physics-start gate passes.

`scripts/verify_v3_architecture_readiness.py` enforces the absence of formal
V3 physics code and checks that the branch changes neither `src/` nor
`configs/` relative to `main`. When executable V3 packages are authorized, a
dedicated import-boundary linter must replace this architecture-only check.
