# UFOTRI Coupled Water/HTO Hydrology Verification R1

Stage: `UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION_R1`

Candidate status: `PENDING_EXACT_HEAD_CI`

## 1. Purpose

C1 recovered the manual-required Eq. (33)-(37) soil-hydrology mechanism and mapped its signed internal water/HTO fluxes to the frozen three-layer soil core. C2 asks a different question: does that closure remain numerically coherent when it is recomputed from the evolving soil state and coupled to the existing lower-boundary, root, TFWT and OBT interfaces over multiple time steps?

C2 is a qualification stage. It does not introduce new production physics.

## 2. Execution path under test

Each interval uses the existing boundaries in this order:

1. current `ThreeLayerSoilState`;
2. C1 `build_ufotri_eq33_37_interlayer_fluxes`;
3. C1 `project_ufotri_hydrology_to_soil_forcing`;
4. explicit `root_v4` water-uptake forcing;
5. existing `V4SoilRootTFWTOBTIntegrator`;
6. frozen `soil_v4` water/HTO ledger and existing plant-side coupled ledger.

The hydrology closure is therefore recomputed from the endpoint of the preceding step. No second soil solver or second integration path is introduced.

## 3. Controlled synthetic profiles

All constitutive relations are explicit and provenance-bearing test inputs.

### Gravity profile

Matric head is held equal across the supplied theta domain while conductivity increases with theta. This isolates the Eq. (35) gravity term and produces positive/downward flow. Because conductivity depends on the evolving water content, repeated time steps also demonstrate that C1 is recomputed from the current state rather than frozen at the initial flux.

### Capillary profile

Signed matric head increases with theta. The test begins with successively wetter lower layers, giving a sufficiently positive downward potential gradient that Eq. (35) returns negative/upward water flux. HTO follows the same sign through C1 upwind advection.

### Dry/wet limiting profile

The dry endpoint explicitly has `K=0`; equal-head dry layers must therefore have zero internal flow. The wet endpoint has positive `K` and must produce downward gravity drainage.

None of these profiles is a production UFOTRI soil parameterization.

## 4. Conservation qualification

The candidate machine gate checks both interval and trajectory closure:

- per-step soil water residual;
- per-step soil HTO residual;
- per-step coupled soil+TFWT+OBT HTO residual;
- cumulative water input/loss/storage identity;
- cumulative coupled HTO input/loss/decay/storage identity;
- exact root water-transfer identity;
- exact root HTO-transfer identity.

Internal L1↔L2 and L2↔L3 transport must cancel globally through the existing soil ledger.

## 5. Signed transport and limiting cases

The gate requires:

- positive water and HTO flux on both internal interfaces in the gravity case;
- negative water and HTO flux on both interfaces in the capillary case;
- persistence of negative/upward flux during a multi-step capillary trajectory;
- zero internal flow at the explicit dry `K=0` limit;
- positive gravity flow at the wet positive-conductivity limit.

These are controlled mechanism tests, not empirical soil validation.

## 6. Lower boundary and root coupling

A separate probe exercises non-zero lower-boundary water and HTO loss together with non-zero root uptake.

The lower-boundary HTO loss rate is constructed from the interval-start L3 water concentration and the explicit lower water-loss rate for a transparent synthetic transport case. It remains an explicit forcing boundary; C2 does not claim to reconstruct an original UFOTRI bottom-boundary algorithm.

Root uptake remains owned by `root_v4`. The existing integrator must apply the resulting transfer exactly once as a soil sink and exactly once as endpoint TFWT gain. The selected `PRESERVE_V3_POST_OBT_ROOT_GAIN` ordering must remain unchanged.

## 7. Determinism and restart

The same 900 s, two-hour coupled case is executed twice and must produce identical result structures. A third run performs a JSON state round-trip at 3600 s; its final result must equal the uninterrupted result.

## 8. Timestep refinement

One four-hour coupled case is run at:

- 3600 s;
- 1800 s;
- 900 s;
- 450 s;
- 225 s.

The 225 s result is a numerical comparison reference only. The maximum absolute state-vector distance to that reference must decrease from coarse to fine, allowing only a small 5% monotonicity tolerance between adjacent levels. This verifies numerical refinement behavior without declaring the finest step physically authoritative.

## 9. Candidate file scope

C2 is designed to add only:

- `scripts/v4/run_ufotri_coupled_water_hto_hydrology_verification_r1.py`;
- `tests/v4/test_ufotri_coupled_water_hto_hydrology_verification_r1.py`;
- ADR-065;
- this report;
- the corresponding governance YAML.

No existing `src/` file is intended to change.

## 10. Candidate conclusion

If exact-head CI passes and the merge/no-drift audit is clean, the permitted C2 conclusion is:

`UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_NUMERICAL_QUALIFICATION=COMPLETE`

At that point Phase C can close for recoverable manual-based mechanism plus controlled numerical qualification, and the next roadmap stage becomes:

`UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`.

The following remain false:

- production hydraulic parameters recovered;
- production hydrology readiness;
- empirical validation;
- calibration;
- physical-accuracy claim;
- original UFOTRI constitutive curves recovered;
- original UFOTRI numerical discretization recovered;
- real CTEAS-Atmos binding;
- original-executable numerical equivalence.
