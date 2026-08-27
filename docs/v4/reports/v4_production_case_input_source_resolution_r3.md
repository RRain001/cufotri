# V4 production-case input source resolution R3 report

Stage: `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R3`

Base main: `9943613aafad43db4e0831547f5593d02b7044ce`

Status: `PRESSURE_ELEVATION_SOURCE_CONTRACT_FROZEN_AWAITING_EXACT_HEAD_GATE`

## 1. Purpose

R2 resolved the Eq.39 physical-property source policy but intentionally left the psychrometric constant without a production-case value. R3 closes the next governance gap: the provenance and identity contract for the pressure/elevation information needed by the selected FAO-56 derivation path.

This is a control-plane stage only. No real production case, pressure, elevation, or gamma value is selected.

## 2. Repository audit before R3

The post-merge audit for PR #48 is complete:

- certified head: `34dc9be8258da4c2c80fc65ca05fec20812d8c0b`;
- merge: `9943613aafad43db4e0831547f5593d02b7044ce`;
- certified-head tree: `3607031e374eee001321ffde6bb63f2376b051be`;
- merge tree: `3607031e374eee001321ffde6bb63f2376b051be`;
- certified head to merge changed files: none;
- remote `main`: `9943613aafad43db4e0831547f5593d02b7044ce`.

Therefore `MERGE_TREE_DRIFT=FALSE` for PR #48.

## 3. Existing-contract finding

The current Atmos exchange contract requires atmospheric records to carry an air-sampling height and vertical reference. Those are receptor/forcing support identities. The production-case manifest, however, does not contain a separate bound site-elevation value; its case identity remains `TEMPLATE_NOT_PRODUCTION / UNSET`.

Consequently, the Atmos record height cannot be reused as the FAO-56 site elevation. R3 freezes that distinction explicitly.

## 4. Selected source contract

Contract ID: `EQ39_PRESSURE_SITE_ELEVATION_PROVENANCE_CONTRACT_R1`.

Source precedence remains the R2 decision:

1. `EXPLICIT_CASE_MEAN_ATMOSPHERIC_PRESSURE_WITH_PROVENANCE`;
2. `FAO56_PRESSURE_DERIVED_FROM_EXPLICIT_SITE_ELEVATION_WITH_PROVENANCE`.

### 4.1 Explicit-pressure path

The canonical derived case field is `case_mean_atmospheric_pressure_kpa`.

It must represent near-surface atmospheric pressure for the production case/site. Required provenance includes source dataset and revision, source variable, original units, location/spatial support, temporal support, missing-data treatment, and transformation log. The averaging operation that creates the case mean must be explicit.

The following are not admissible substitutes:

- sea-level pressure;
- an unqualified model pressure level;
- synthetic/test constants;
- fixed 101.3 kPa;
- fixed 66 Pa K^-1.

Unit conversion from Pa/hPa/kPa is allowed only when logged explicitly.

### 4.2 Elevation-derived fallback

The canonical field is `site_elevation_m_msl`.

It means site orthometric or equivalent height above mean sea level. Required provenance includes location identity, horizontal reference, vertical datum or explicit MSL semantics, source revision, original value/unit, and transformations.

The following are forbidden substitutes:

- Atmos air-sampling height;
- receptor height above local ground;
- stack height;
- terrain-following model level;
- pressure-level altitude;
- ellipsoidal height without a documented geoid/vertical-datum conversion.

The FAO-56 equations remain:

`P_kPa = 101.3 * ((293 - 0.0065*z_m)/293)^5.26`

`gamma_Pa_per_K = 0.665 * P_kPa`.

The 101.3 term is part of the FAO-56 approximation. It is not an allowed default when `z_m` is absent.

## 5. Dual-source behavior

If both admissible pressure and elevation sources are available, explicit pressure wins. Elevation-derived pressure may be retained as a diagnostic cross-check only. R3 does not define a disagreement threshold and does not authorize averaging/blending.

## 6. Fail-closed state

Eq.39 psychrometric production input remains unresolved if neither admissible source path is complete. Ambiguous vertical semantics, sea-level-pressure relabeling, undocumented aggregation/fill, receptor-height substitution, or promotion of test values all fail closed.

## 7. No production activation

R3 does not modify:

- `docs/v4/contracts/v4_production_case_input_manifest_r1.yaml`;
- `src/`;
- Eq.39 equations;
- workflow files;
- runtime imports;
- numerical coupling;
- calibration state.

The following remain false/zero:

- `PRODUCTION_INPUT_PACKET_READY`;
- `FULL_MODEL_PRODUCTION_READY`;
- `ACTIVE_PARAMETERS=0`;
- `CALIBRATION_STARTED`;
- `OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED`;
- `OBT_PARAMETER_ACTIVATION_AUTHORIZED`;
- `CURRENT_KF_KR_CALIBRATION_AUTHORIZED`;
- `LEAF_R5_AUTHORIZED`;
- `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED`;
- `FULL_HYDROLOGY_AUTHORIZED`;
- `REAL_CTEAS_ATMOS_BINDING`;
- `EMPIRICAL_VALIDATION`;
- `PHYSICAL_ACCURACY_CLAIM`.

Atmos surface deposition flux remains `BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED`.

## 8. Next stage

If R3 passes exact-head Remediation and Protected gates and merges without drift, the only authorized next stage is `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R4`, restricted to `PRODUCTION_CASE_IDENTITY_AND_EQ39_PRESSURE_SOURCE_SELECTION_ONLY`.

R4 must bind an explicit production case identity before selecting a real pressure/elevation source. Manifest projection, runtime activation, solver change, calibration, and any physical-readiness claim remain unauthorized.
