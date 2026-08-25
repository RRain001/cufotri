# V3-P7.5B numerical coupling semantics implementation report

Status: `PASS_NUMERICAL_COUPLING_SEMANTICS_FROZEN`

Branch: `codex/v3-p7-5b-numerical-coupling-freeze`

Base commit: `8943ec2fa9f98f023ce6de4343e1892785521e47`

## Scope

P7.5B freezes the actual one-timestep software composition already present
in the P7.5 runner.  It adds no new physical equation, no external data
reader, and no parameter source.  The implementation change is limited to
the P7.5 pipeline contract comments and a focused numerical-semantics test
module.

## Frozen semantics

- Forcing timestamp: interval-start label `t_n`.
- Forcing value: representative of the complete `[t_n, t_{n+1}]` interval.
- Soil deposition: advances from step-start `SoilState` to a post-deposition
  endpoint.
- Root source snapshot: step-start soil, even though the root call follows
  the soil solver in the runner.
- Plant order: leaf exchange -> leaf-only TFWT intermediate -> OBT.
- Final TFWT order: subtract OBT-reported TFWT loss, then add root transfer.
- Soil reconciliation: subtract the root transfer from the post-deposition
  soil endpoint.
- Food/intake/dose: non-mutating endpoint readout/event assessment, not a
  continuous plant-inventory consumption process.
- Endpoint rule: soil, TFWT, OBT, root, harvest, food, intake, dose, and the
  pipeline state all end at `t_{n+1}`; forcing retains its `t_n` label.

The formal decision is recorded in
`docs/adr/009-v3-pipeline-numerical-coupling-semantics.md`.

## Boundary flags

```text
P7_5B_STATUS = PASS_NUMERICAL_COUPLING_SEMANTICS_FROZEN
V3_PIPELINE_AVAILABLE = TRUE
NUMERICAL_COUPLING_FROZEN = TRUE
TIMESTEP_REFINEMENT = PASS
RESTART_EQUIVALENCE = PASS
PIPELINE_CONSERVATION = PASS
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

## Protected scope

No V1/V2 runtime, existing subsystem equation, configuration, parameter,
trusted-registry, UFOTRI database, ERA5 input, or CTEAS-Atmos input was
modified or imported.  The pipeline still calls existing typed solver APIs
and performs only endpoint inventory reconciliation.  The synthetic tests
are software-composition evidence, not observational or physical validation.
