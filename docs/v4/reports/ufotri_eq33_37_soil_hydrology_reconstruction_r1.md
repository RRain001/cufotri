# UFOTRI Eq. (33)-(37) Soil Hydrology Reconstruction R1

Stage: `UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`

Candidate status: `PENDING_EXACT_HEAD_CI`

## 1. Question

Can the missing UFOTRI soil-water closure be reconstructed without replacing the frozen three-layer inventory solver, and without inventing original UFOTRI soil hydraulic parameters that are not recoverable from the available evidence?

## 2. Manual finding

KfK 4605 Section 2.2.3 defines the relevant structure:

- Eq. (33): total water potential is decomposed into matric, osmotic, gravitational and pressure/gas-related terms;
- Eq. (34): vertical one-dimensional continuity;
- Eq. (35): Darcy flux depends on hydraulic conductivity and potential gradient;
- Eq. (36): for the matric-only case, the continuity/Darcy system reduces to a Richards-type moisture equation using `K(Theta)` and `Psi_m(Theta)`;
- Eq. (37): vegetation contributes a root-water sink `S(z,t)`.

The manual also warns that the detailed soil hydraulic data needed for a high-complexity model were not sufficiently available and that practical transport estimates carry large uncertainty. The repository does not contain the original executable/source constitutive curves or exact discretization.

## 3. Existing post-RC1 boundary

`plant/soil_v4` already provides the correct stable inventory boundary:

- three canonical layers: 0–5, 5–15, 15–30 cm;
- water inventory in m water per m2 soil;
- HTO inventory in Bq/m2;
- signed L1↔L2 and L2↔L3 water/HTO fluxes;
- conservative bookkeeping and decay.

Its source explicitly states that Richards/Darcy hydrology is not solved and that inter-layer fluxes are caller inputs.

Therefore C1 does not rewrite that core.

## 4. Reconstruction decision

A new opt-in package `plant/soil_ufotri_v4` generates the missing internal fluxes and projects them into the frozen forcing contract.

### 4.1 Constitutive relation

The new `TabulatedSoilHydraulicRelation` requires explicit, versioned/provenanced arrays for:

- volumetric water content `Theta`;
- signed matric potential head `Psi_m`;
- hydraulic conductivity `K`.

There is no built-in production/default soil curve. Piecewise-linear interpolation is a transparent implementation choice and is restricted to the supplied domain. Extrapolation is rejected.

This prevents a modern generic parameterization from being silently presented as recovered UFOTRI physics.

### 4.2 Layer state to hydrologic state

For each canonical layer:

`Theta_i = water_inventory_i / layer_thickness_i`.

Potential and conductivity are evaluated from the explicit relation. Potential gradients use layer-centre separation.

### 4.3 Eq. (35)-(36) signed water flux

With depth positive downward:

`q = -K_interface * (dPsi_m/dz - 1)`.

A uniform matric-potential profile therefore yields `q=+K`, downward gravity drainage. A sufficiently positive matric-potential gradient with depth yields `q<0`, upward capillary-direction transport.

Interface `K` uses a harmonic mean. This is explicitly identified as a numerical implementation choice, not as recovered original UFOTRI source logic.

### 4.4 HTO transport

HTO follows water using interval-start upwind advection:

`J_HTO = q * C_donor`.

For `q>0`, the upper layer is the donor; for `q<0`, the lower layer is the donor. This maps exactly onto the frozen positive-downward signed forcing convention.

### 4.5 Eq. (37) root sink

C1 does not invent or infer `S(z,t)`. Existing `root_v4` explicit water-uptake forcing remains authoritative. The projection adapter copies root water and HTO extraction unchanged.

## 5. Double-count protection

The projection adapter refuses a base `ThreeLayerSoilForcing` that already contains any non-zero internal water or HTO flux. The new closure therefore cannot silently coexist with an explicit replay/RC1 internal transport on the same interval.

## 6. Candidate verification set

Independent tests cover:

1. Eq. (33) additive potential identity;
2. Eq. (35) gravity direction under zero non-gravitational gradient;
3. uniform-head downward gravity transport;
4. wetter-lower-layer upward capillary-direction transport;
5. correct upwind HTO donor for both directions;
6. interpolation within explicit constitutive domain;
7. fail-closed extrapolation;
8. malformed/negative-conductivity table rejection;
9. preservation of surface/lower/root forcing;
10. rejection of inter-layer double counting;
11. one-step water and HTO conservation through the unchanged `soil_v4` core;
12. machine-visible reconstruction gate.

## 7. C1 versus C2 boundary

C1 is a mechanism/interface reconstruction stage. It does **not** close the full dynamic hydrology qualification.

The following remain for C2 `UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION_R1`:

- dry/wet limiting cases over multi-step trajectories;
- lower-boundary behavior;
- explicit root-sink coupled dynamics;
- deterministic repeat/restart;
- timestep refinement;
- coupled water/HTO balance under the selected hydrology closure.

## 8. Candidate conclusion

If exact-head CI passes, C1 supports the conclusion:

`UFOTRI_EQ33_37_SOIL_HYDROLOGY_MECHANISM_RECONSTRUCTED=TRUE`

with the following simultaneously true:

- `UFOTRI_ORIGINAL_CONSTITUTIVE_CURVES_RECOVERED=FALSE`
- `UFOTRI_ORIGINAL_NUMERICAL_DISCRETIZATION_RECOVERED=FALSE`
- `PRODUCTION_HYDROLOGY_READY=FALSE`
- `EMPIRICAL_VALIDATION=FALSE`
- `CALIBRATION=FALSE`
- `REAL_CTEAS_ATMOS_BINDING=FALSE`
- `C2_COUPLED_HYDROLOGY_VERIFICATION_COMPLETE=FALSE`

The candidate therefore advances manual-based functional reconstruction while preserving the distinction between recovered mechanism, numerical implementation choice, and unavailable original parameters/source behavior.
