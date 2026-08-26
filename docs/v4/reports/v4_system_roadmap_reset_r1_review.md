# V4 system roadmap reset R1 review

Status: `READY_FOR_EXACT_HEAD_CI`

Branch: `codex/v4-system-roadmap-reset-r1`

Base main: `d4bb2def0e81fe5a26b772a239e8c6de8f0d0dcc`

## Scope

This stage is a system-level roadmap reset only. It preserves the V3/V3.1 runnable baseline and freezes V4-2 R4 as a leaf evidence/design checkpoint. It does not implement a new physical model.

The next work is intentionally re-sequenced to:

1. close the CTEAS-Atmos to CTEAS-UFOTRI data exchange contract without waiting for CTEAS-Atmos solver completion;
2. run a complete physics-gap and sensitivity-priority audit across atmosphere, soil, leaf, TFWT, OBT, root, food, intake and dose;
3. only then authorize subsystem-specific physics work according to dependency and output sensitivity.

## Clarified soil status

The current V3 soil runtime is one layer with an HTO inventory and signed transport boundary. A three-layer soil-water/HTO system is recorded only as a future candidate. Full Richards/Darcy hydrology remains unauthorized.

## Non-implementation boundary

```ini
SOLVER_CHANGES_AUTHORIZED = FALSE
NUMERICAL_COUPLING_CHANGES_AUTHORIZED = FALSE
LEAF_R5_AUTHORIZED = FALSE
THREE_LAYER_SOIL_IMPLEMENTED = FALSE
FULL_SOIL_HYDROLOGY_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_COUPLING_ACTIVE = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
V3_PHYSICS_READY = FALSE
```

## Verification target

Exact-head CI must pass the portable integration suite and the explicit frozen-boundary suite including `tests/v4/test_v4_system_roadmap_reset_r1.py`. The PR should remain draft until that result is independently checked.
