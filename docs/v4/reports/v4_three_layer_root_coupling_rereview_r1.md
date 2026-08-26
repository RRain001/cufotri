# V4 three-layer root coupling re-review R1

## Verdict

`PASS_CONTROL_PLANE`

The V4 root-water-flux contract required a fresh review of P7.5/P7.5B coupling before root implementation. This review authorizes an isolated three-layer root flux subsystem only. It does **not** authorize V4 pipeline integration or a change to the frozen V3 operator split.

## UFOTRI evidence recovered

KfK 4605 supports two distinct root-uptake contexts that must remain separate.

For the long-term ingestion compartment model, the root-zone soil is explicitly 0–5, 5–15 and 15–30 cm. Chapter 3.3.2 assigns 20%, 40% and 40% of plant water uptake to those layers. Equation (57) derives layer transfer rates from total plant uptake and the layer hydrogen inventory; Equations (58)–(60) give the manual reference values of about 0.026, 0.026 and 0.017 d^-1.

For the short-term secondary model, root uptake replenishes plant transpiration and the manual assumes an approximately 3 h delay between moisture loss and root uptake. This short-term lag is not equivalent to the daily-mean ingestion transfer-rate model.

The original UFOTRI source code is unavailable, so the exact original software scheduling of these transfers cannot be claimed.

## Selected isolated root contract

For an interval beginning at `t_n`, root flux is evaluated from the authoritative three-layer soil state at `S_n`:

`J_root,i = q_w,i * C_w,i(S_n)`

where `q_w,i` is an explicit, non-negative layer water-uptake flux in m/s and `C_w,i` is the layer HTO concentration in Bq/m3 water. The result is an HTO flux in Bq/m2/s.

The root core is non-mutating. It may calculate and ledger the water/HTO transfer, but it does not update soil or TFWT. It may not derive `q_w,i`, convert an unrelated s^-1 rate into m/s, guess a missing water flux, or hide a transpiration-delay model.

Time, provenance, units and layer identity are mandatory and fail closed.

## Ownership and single-application rule

When future pipeline integration is authorized:

- `soil_v4` owns the actual per-layer water and HTO sink;
- the TFWT boundary receives exactly the same integrated HTO transfer as a gain;
- the root subsystem only computes the transfer plan/ledger;
- the transfer must be applied once to soil and once to the receiving plant inventory, never twice on either side.

This rule is necessary because `soil_v4` already exposes explicit per-layer root sink slots. A future root adapter must populate those slots rather than subtracting the same inventory again after the soil step.

## P7.5/P7.5B operator-order result

The frozen V3 path reads step-start soil, advances OBT before the root gain is reconciled into final TFWT, and therefore introduces a one-step root-to-OBT lag. V3 remains unchanged.

For V4, this review does not choose an operator split because exact UFOTRI source-code scheduling is unavailable and the two plausible choices have different numerical consequences:

1. `PRESERVE_V3_POST_OBT_ROOT_GAIN`: preserve the existing one-step lag while replacing the scalar root abstraction with three-layer fluxes.
2. `ROOT_GAIN_BEFORE_OBT`: include same-interval root HTO gain in TFWT before OBT formation.

Before V4 pipeline integration, these candidates must be compared with multi-step synthetic cases, timestep refinement, restart equivalence, deterministic repeat and explicit soil→TFWT conservation. The chosen split must also state whether it represents the short-term dynamic or long-term daily-mean profile.

## Parameter status

The UFOTRI 20/40/40 fractions and 0.026/0.026/0.017 d^-1 rates are reference evidence. They are not activated as the default physical parameterization by this review. Likewise, the 3 h delay is evidence for the short-term model and is not silently implemented inside the root core.

## Authorization

The next authorized stage is `V4_THREE_LAYER_ROOT_FLUX_CORE_IMPLEMENTATION_R1` with isolated subsystem scope only. It may implement typed `q_w,i` forcing, `J_root,i=q_w,i C_w,i`, ledgers, fail-closed validation and a clearly labeled UFOTRI reference fixture.

It may not modify `root_v3`, `v3_pipeline`, select a V4 pipeline operator split, derive transpiration, implement Richards/Darcy hydrology, calibrate parameters or activate the UFOTRI reference profile.

```ini
V4_THREE_LAYER_ROOT_COUPLING_REREVIEW_R1 = PASS_CONTROL_PLANE
ROOT_FLUX_CORE_IMPLEMENTATION_AUTHORIZED = TRUE
V4_PIPELINE_INTEGRATION_AUTHORIZED = FALSE
V4_OPERATOR_SPLIT_SELECTED = FALSE
UFOTRI_20_40_40_ACTIVE = FALSE
UFOTRI_REFERENCE_LAYER_RATES_ACTIVE = FALSE
SHORT_TERM_3H_DELAY_ACTIVE = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
V3_DEFAULT_PROFILE_CHANGED = FALSE
```
