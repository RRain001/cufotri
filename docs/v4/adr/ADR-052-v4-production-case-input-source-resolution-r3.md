# ADR-052: V4 production-case Eq.39 pressure and site-elevation source contract R3

Status: proposed for exact-head certification

Stage: `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R3`

Base main: `9943613aafad43db4e0831547f5593d02b7044ce`

## Decision

Freeze the provenance contract needed to derive the UFOTRI Eq.39 psychrometric constant without selecting or activating a production-case value.

R2 selected `FAO56_CASE_PRESSURE_DERIVED` and established the precedence:

1. explicit case-mean atmospheric pressure with provenance;
2. otherwise FAO-56 pressure derived from explicitly sourced site elevation above mean sea level.

R3 defines the identities and admissibility rules for those two paths. It does not project a value into the production manifest, does not change `src/`, and does not authorize runtime activation.

## Identity separation

`site_elevation_m_msl` is a case/site geodetic identity. It is not any of the following:

- receptor air-sampling height;
- height above local ground;
- stack height;
- terrain-following model level;
- pressure-level altitude;
- ellipsoidal height without an explicit geoid/vertical-datum transformation.

The existing Atmos exchange contract requires air-sampling height and vertical reference for atmospheric records. Those fields remain independent and cannot be silently reused as site elevation.

## Explicit-pressure path

The preferred path is `EXPLICIT_CASE_MEAN_ATMOSPHERIC_PRESSURE_WITH_PROVENANCE`.

The source must provide near-surface atmospheric pressure representative of the production case/site. The production-case mean must be an explicit transformation with source variable, source units, temporal support, spatial support, missing-data treatment, and transformation log recorded. Sea-level pressure may not be relabeled as site pressure. A fixed `101.3 kPa` or `66 Pa K^-1` fallback is forbidden.

If pressure is supplied in Pa, hPa, or another convertible pressure unit, the conversion to kPa must be explicit and logged. Silent unit conversion is forbidden.

## Elevation-derived fallback

If explicit case pressure is not available, `FAO56_PRESSURE_DERIVED_FROM_EXPLICIT_SITE_ELEVATION_WITH_PROVENANCE` is allowed.

The required elevation identity is `site_elevation_m_msl`. Its source must identify the site/location, horizontal reference, vertical datum or stated MSL/orthometric semantics, value/unit, source revision, and any transformation. If the available source is ellipsoidal height, a documented geoid transformation is required before it can satisfy `site_elevation_m_msl`.

The FAO-56 formula remains exactly the R2 policy:

`P_kPa = 101.3 * ((293 - 0.0065*z_m)/293)^5.26`

and

`gamma_Pa_per_K = 0.665 * P_kPa`.

The constant `101.3` in the FAO-56 formula is part of that documented approximation. It is not permission to substitute sea-level pressure when `z_m` is missing.

## Dual-source behavior

If both admissible explicit pressure and admissible site elevation are available, the explicit-pressure path has precedence. The elevation-derived pressure may be retained only as a diagnostic cross-check. R3 does not define a numerical disagreement tolerance and does not authorize averaging or blending the two estimates.

## Fail-closed rules

The Eq.39 psychrometric input remains unresolved when:

- no admissible explicit pressure source exists and no admissible MSL elevation source exists;
- pressure identity is sea-level pressure rather than site pressure;
- elevation vertical semantics are ambiguous;
- receptor/air-sampling height is substituted for site elevation;
- ellipsoidal height is relabeled as MSL height without a recorded conversion;
- case mean pressure is produced by an undocumented aggregation or missing-data fill;
- a synthetic/test constant is proposed as production evidence.

## Non-decisions

R3 does not:

- choose a production site or scenario;
- bind a real pressure or elevation value;
- modify the production-case manifest;
- change Eq.39 equations;
- add a pressure/elevation runtime adapter;
- activate latent heat, water density, or psychrometric parameters;
- resolve root water-flux production inputs;
- change hydrology, leaf R5, OBT physics, Atmos binding, calibration, or validation state.

## Next stage

After a clean exact-head merge, the only authorized continuation is `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R4`, restricted to `PRODUCTION_CASE_IDENTITY_AND_EQ39_PRESSURE_SOURCE_SELECTION_ONLY`. R4 must first bind an explicit production case identity before selecting a real pressure/elevation source. Manifest projection and runtime activation remain unauthorized until separately reviewed.
