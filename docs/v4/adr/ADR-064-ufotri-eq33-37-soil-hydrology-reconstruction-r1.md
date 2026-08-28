# ADR-064 — UFOTRI Eq. (33)-(37) soil-hydrology reconstruction R1

## Status

`PROPOSED_C1_CANDIDATE`

Stage: `UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`

## Context

The frozen V4 three-layer soil core is an inventory and conservation solver. Its signed L1↔L2 and L2↔L3 water/HTO fluxes are caller-supplied; it explicitly does not solve Richards/Darcy hydrology.

KfK 4605 Section 2.2.3 provides the recoverable UFOTRI hydrologic structure:

- Eq. (33): additive soil-water-potential components;
- Eq. (34): one-dimensional continuity;
- Eq. (35): Darcy water flux `q=-K(Theta)[dPsi/dz-1]`;
- Eq. (36): matric-potential/conductivity Richards form when other potential terms/sources are omitted;
- Eq. (37): vegetation root sink `S(z,t)`.

The same manual states that detailed soil hydraulic parameters are uncertain and that practical UFOTRI transport used simplified/estimated water-transfer information. The available repository does not recover the original executable's constitutive `K(Theta)` and `Psi_m(Theta)` curves or its numerical discretization.

## Decision

Create an opt-in compatibility package `cteas_ufotri.plant.soil_ufotri_v4` that generates only the missing internal signed inter-layer water and advective HTO fluxes. Keep `soil_v4` unchanged as the authoritative storage/conservation boundary.

### Manual identities

1. Eq. (33) is exposed as an explicit additive potential-head helper.
2. Eq. (35) is exposed directly using depth positive downward. Under this convention an equal non-gravitational potential profile gives `q=+K`, i.e. downward gravity drainage.
3. The active C1 closure uses the Eq. (36) matric-only route because no defensible default osmotic/pressure constitutive closure is recovered.
4. Eq. (37) root uptake remains external and is supplied by the existing `root_v4` forcing path; C1 does not infer it.

### Constitutive evidence boundary

No van Genuchten, Brooks-Corey, Campbell, or other modern generic parameterization is selected as an implicit UFOTRI default.

Instead, callers must supply `TabulatedSoilHydraulicRelation` containing versioned/provenanced `Theta -> Psi_m` and `Theta -> K` values. Piecewise-linear interpolation is allowed only inside the supplied domain. Extrapolation fails closed. Matric potential values are signed heads, not unsigned suction magnitudes.

This table contract is an implementation interface, not evidence that the original UFOTRI executable used piecewise-linear interpolation.

### Spatial discretization

The canonical V4 layers remain 0–5, 5–15 and 15–30 cm. Volumetric moisture is derived from inventory divided by layer thickness. Potential gradients use layer-centre separation.

Interface hydraulic conductivity uses a harmonic mean. This is explicitly labeled `HARMONIC_MEAN_IMPLEMENTATION_CHOICE_NOT_MANUAL_SOURCE`; no original-UFOTRI discretization claim is made.

### HTO projection

HTO advection uses the interval-start upwind donor concentration:

`J_HTO = q * C_donor`.

The signed result maps directly onto the frozen `ThreeLayerSoilForcing` convention. Positive is downward; negative is upward.

### Compatibility and double counting

`project_ufotri_hydrology_to_soil_forcing` copies all existing surface, lower-boundary, re-emission and root-sink inputs unchanged and injects only the two internal interfaces. If a base forcing already contains non-zero internal water or HTO transport, projection fails closed rather than overwriting or adding it.

## Verification required for C1

- independent Eq. (33) additive identity;
- Eq. (35) gravity-direction identity;
- downward gravity-drainage case;
- upward capillary-direction case;
- upwind HTO donor selection in both signs;
- constitutive table interpolation and fail-closed domain behavior;
- invalid-table rejection;
- preservation of external/root forcing;
- double-count prevention;
- one-step compatibility with frozen `soil_v4` water/HTO conservation;
- machine-visible C1 gate.

Full wet/dry limiting cases, lower-boundary coupling, root-sink coupled dynamics, deterministic restart and timestep refinement remain C2 responsibilities.

## Consequences

C1 restores the recoverable Eq. (33)-(37) hydrologic mechanism as an opt-in closure while preserving RC1/replay compatibility. It does not establish production soil parameters, empirical accuracy, original executable numerical equivalence, or full coupled hydrology verification.

## Explicit non-claims

- `PRODUCTION_HYDROLOGY_READY=FALSE`
- `UFOTRI_ORIGINAL_CONSTITUTIVE_CURVES_RECOVERED=FALSE`
- `UFOTRI_ORIGINAL_NUMERICAL_DISCRETIZATION_RECOVERED=FALSE`
- `EMPIRICAL_VALIDATION=FALSE`
- `CALIBRATION=FALSE`
- `REAL_CTEAS_ATMOS_BINDING=FALSE`
- `C2_COUPLED_HYDROLOGY_VERIFICATION_COMPLETE=FALSE`
