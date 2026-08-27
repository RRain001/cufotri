# V4 production-case input source resolution R2 report

## Verdict

```text
V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R2 = PASS_EQ39_PHYSICAL_PROPERTY_SOURCE_POLICY_DECISION_AWAITING_EXACT_HEAD_GATE
POLICY = FAO56_EQ39_REFERENCE_PROPERTY_POLICY_R1
PRODUCTION_INPUT_PACKET_READY = FALSE
FULL_MODEL_PRODUCTION_READY = FALSE
ACTIVE_PARAMETERS = 0
REAL_CTEAS_ATMOS_BINDING = FALSE
```

R2 resolves only the source policy for the three caller-owned Eq.39 physical-property inputs. It does not edit the production-case manifest, change Eq.39 equations, import runtime parameters, add a thermodynamic solver, or authorize a production run.

## 1. Latent heat

Selected policy:

```text
FAO56_REFERENCE_ET_FIXED_CONVENTION
lambda = 2.45e6 J kg^-1
```

FAO Irrigation and Drainage Paper 56 states that latent heat varies with temperature, but its simplified Penman-Monteith procedure takes a single value of `2.45 MJ kg^-1`, corresponding to about 20 degC. R2 adopts that value only as a controlled reference-ET convention for the selected Eq.39 path.

The decision is explicitly not:

- a claim that latent heat is temperature-independent;
- a new temperature-dependent latent-heat implementation;
- a calibration result;
- a runtime parameter activation.

## 2. Water density

Selected policy:

```text
REFERENCE_WATER_DEPTH_CONVERSION_CONVENTION
rho_w = 1000 kg m^-3
```

The Eq.39 code divides a water mass flux by `rho_w` to express the result as metres of water per second. R2 freezes `1000 kg m^-3` as the reference conversion convention for that unit transformation.

IAPWS-95 remains the physical-property boundary: real ordinary-water density is a thermodynamic state property. Therefore the selected value is not labelled an exact or universal density. R2 deliberately avoids adding an IAPWS runtime property solver.

## 3. Psychrometric constant

Selected policy:

```text
FAO56_CASE_PRESSURE_DERIVED
```

No fixed gamma value is selected. FAO-56 defines the psychrometric constant from atmospheric pressure. With the same reference latent-heat convention:

```text
gamma_kPa_per_K = 0.000665 * P_kPa
gamma_Pa_per_K  = 0.665 * P_kPa
```

The case-pressure source precedence is frozen as:

1. explicit case mean atmospheric pressure with provenance;
2. otherwise, pressure derived from explicitly sourced site elevation using FAO-56 Eq.7.

The elevation route is:

```text
P_kPa = 101.3 * ((293 - 0.0065*z_m)/293)^5.26
```

where `z_m` is site elevation above mean sea level.

Fail-closed rules:

```text
SEA_LEVEL_PRESSURE_DEFAULT_ALLOWED=FALSE
ZERO_ELEVATION_DEFAULT_ALLOWED=FALSE
FIXED_GAMMA_66_PA_K_ALLOWED=FALSE
PRESSURE_OR_ELEVATION_SOURCE_BOUND=FALSE
```

Thus R2 resolves the derivation policy but does not yet resolve a case-specific gamma value.

## 4. Why this is preferred over three fully state-dependent properties

The selected UFOTRI boundary is already a reduced Eq.39 equilibrium-radiation model. Replacing all three conversion inputs with a new IAPWS/thermodynamic subsystem would widen the model beyond the authorized source-resolution task while adding negligible conceptual value to the current governance stage.

R2 therefore distinguishes between:

- a deliberate reference-model convention (`lambda`);
- a deliberate water-depth conversion convention (`rho_w`);
- a genuinely case-dependent atmospheric property (`gamma`).

This keeps the selected model interpretable without disguising approximations as exact physics.

## 5. No source or runtime mutation

The existing manifest records for all three quantities remain unresolved and `production_use_authorized=false`. R2 is a decision overlay only.

No `src/` file or workflow is changed. Existing synthetic values remain test-only and are not used as evidence.

## 6. Atmos blocker remains unchanged

```text
atmosphere.surface_deposition_flux = BLOCKED_EXTERNAL
soil_three_layer.surface_deposition_flux = BLOCKED_EXTERNAL
BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED
REAL_CTEAS_ATMOS_BINDING=FALSE
```

R2 creates no substitute deposition flux.

## 7. Frozen hard boundaries

```text
PRODUCTION_INPUT_PACKET_READY=FALSE
FULL_MODEL_PRODUCTION_READY=FALSE
ACTIVE_PARAMETERS=0
CALIBRATION_STARTED=FALSE
OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED=FALSE
OBT_PARAMETER_ACTIVATION_AUTHORIZED=FALSE
CURRENT_KF_KR_CALIBRATION_AUTHORIZED=FALSE
LEAF_R5_AUTHORIZED=FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=FALSE
FULL_HYDROLOGY_AUTHORIZED=FALSE
REAL_CTEAS_ATMOS_BINDING=FALSE
EMPIRICAL_VALIDATION=FALSE
PHYSICAL_ACCURACY_CLAIM=FALSE
```

## 8. Next stage

After exact-head dual-green CI and clean no-drift merge, proceed only to:

```text
V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R3
FOCUS=EQ39_CASE_PRESSURE_AND_SITE_ELEVATION_SOURCE_CONTRACT_ONLY
```

R3 may define the provenance contract for case atmospheric pressure and site elevation. It may not project any value into runtime, alter Eq.39 equations, activate Eq.38, add full hydrology, implement Leaf R5, redesign OBT, calibrate parameters, or bind real CTEAS-Atmos data.
