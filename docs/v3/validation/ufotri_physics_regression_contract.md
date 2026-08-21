# UFOTRI Physics Regression Contract

Status: `V3-P5.3_VALIDATION_CONTRACT_FROZEN`; architecture and benchmark
format only.

P5.3 freezes the future validation inputs, outputs, provenance, and ledger
format without importing reference values or assigning numerical tolerances.
This document is not UFOTRI equivalence or physical validation.

## Common benchmark envelope

Each benchmark records:

- the `AtmosphericHTOForcing` payload and its UTC time sequence;
- source, adapter, spatial reference, temporal resolution, artifact hash, and
  parameter package hash;
- units, area basis, time step, initial inventories, and model version;
- `TFWT(t)` and `OBT(t)` trajectories;
- pathway-resolved input/output terms and a mass-balance residual.

The ledger separates atmospheric/soil boundary inputs, leaf and root pathway
terms, internal TFWT-to-OBT transfer, decay/turnover, and final inventory.
Internal transfers must not be counted as external input. Missing required
forcing fields, non-contiguous time, invalid units, or a required-but-absent
optional field are `FAIL_CLOSED`.

The numerical tolerance remains `TO_BE_FROZEN_IN_P6`. No concrete tolerance is
introduced here.

## Benchmark A: constant HTO

Input:

```text
C_air = constant
```

Outputs:

```text
TFWT(t)
OBT(t)
```

The comparison package must include the two trajectories, final inventories,
pathway ledger, mass-balance residual, and all provenance hashes. Any future
reference comparison must identify whether a discrepancy is interface,
parameter, numerical, or physical.

## Benchmark B: step release / HTO pulse

Input:

```text
HTO pulse or step release followed by declared background forcing
```

Outputs:

```text
uptake
release
decay
TFWT(t)
OBT(t)
```

The benchmark checks the release discontinuity, post-release decline, and OBT
formation without hidden reset, nearest-time repair, or missing-to-zero
behavior.

## Benchmark C: diurnal cycle

Input:

```text
temperature
humidity
radiation
```

Outputs:

```text
day/night response
TFWT(t)
OBT(t)
```

The benchmark checks time-varying response, optional-field requirements, and
reproducible day/night pathway behavior. It does not prescribe a resistance or
response equation.

## Validation layers

P6 must report these separately:

1. payload, units, time-continuity, and provenance checks;
2. pathway and mass-balance checks;
3. trajectory regression against a frozen reference artifact;
4. independent physical/equivalence assessment.

Passing the first two layers is not evidence of UFOTRI numerical equivalence.
