# UFOTRI Physics Regression Contract

Status: architecture-only contract for V3-P6 preparation.

P5.2 defines regression cases and evidence requirements without importing
reference numerical values or freezing concrete tolerances. Therefore this
document cannot be read as UFOTRI equivalence or physical validation.

## Common case requirements

Each case must record the input artifact identity, source/provenance, units,
UTC time basis, time step, initial inventories, parameter package hash, and
model version. The required trajectories are `TFWT(t)` and `OBT(t)`, with
inventory units and reference area stated explicitly.

Every case must also report a mass-balance residual with separately identified
atmospheric input, internal TFWT-to-OBT transfer, decay/turnover loss, and
final inventory. Internal transfers must not be counted as external input.

The numerical tolerance is intentionally left as
`TO_BE_FROZEN_IN_P6`; no concrete value is introduced here.

## Case A: constant air HTO

Input: constant `C_air` with fixed meteorological conditions and a declared
initial plant state.

Required comparison:

```text
reference UFOTRI TFWT(t)  <->  CTEAS-UFOTRI TFWT(t)
reference UFOTRI OBT(t)   <->  CTEAS-UFOTRI OBT(t)
```

The report must include trajectory comparison, final inventory comparison,
mass-balance residual, parameter/provenance identity, and the disposition of
any mismatch. Tolerance remains `TO_BE_FROZEN_IN_P6`.

## Case B: step or pulse release

Input: an HTO step or finite-duration pulse followed by background forcing.

The case must expose atmospheric uptake, post-release decay or turnover, and
OBT formation. It must check that the forcing discontinuity is represented at
the declared time resolution and that no hidden reset or missing-to-zero rule
creates inventory.

## Case C: diurnal forcing

Input: a declared diurnal cycle in temperature, humidity, and radiation, with
HTO concentration and time resolution specified independently.

The case must test time-varying exchange behavior, optional-field handling,
day/night applicability, and trajectory/mass-balance reproducibility. It must
not infer a resistance or response law until that law is reviewed and frozen.

## Validation layers

P6 should separate the following outcomes:

1. interface and dimensional contract checks;
2. conservation and ledger checks;
3. trajectory regression against a frozen reference artifact;
4. independent physical/equivalence assessment.

Passing the first two layers is not evidence of UFOTRI numerical equivalence.
P5.2 claims none of the four physical/equivalence layers.
