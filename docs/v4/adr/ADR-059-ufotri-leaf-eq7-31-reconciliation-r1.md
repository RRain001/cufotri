# ADR-059: UFOTRI leaf Eq. (7)-(31) reconciliation R1

## Status

Proposed post-RC1 replication-fidelity decision.

## Context

`UFOTRI_REPLICATION_GAP_AUDIT_R1` identified the plant/atmosphere exchange chain as a required replication gap. The frozen V4 RC1 path consumes explicit `r_a + r_b + r_c` values and a signed leaf boundary flux. Historical V2 contains a meteorology-responsive implementation in `src/cteas_ufotri/plant/leaf_exchange.py`, but that implementation mixes recoverable UFOTRI relations with later literature substitutions.

The purpose of this stage is to reconcile the available KfK 4605 manual Eq. (7)-(31), the historical V2 implementation, and the frozen V4 RC1 interfaces. This stage does not change source physics.

## Decision

The current V2 implementation is **not** sufficient to close manual fidelity without source changes.

`SOURCE_CHANGES_REQUIRED = TRUE`

Authorize a subsequent opt-in fidelity implementation stage:

`UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1`

The RC1 default/fallback leaf boundary remains frozen and must not be replaced silently.

## Equation reconciliation

### Eq. (7)-(14): resistance analogy and canopy composition

- Eq. (7)-(8): conceptual resistance/flux analogy is represented by the signed resistance boundary.
- Eq. (9): total plant resistance role is represented by `r_a + r_b + r_c` in the current V4 boundary.
- Eq. (10)-(11): the manual presents water-vapour-pressure/latent-heat relations as physical interpretation before switching to parameterized resistances; they are not required as a separate runtime solver for the selected fidelity path.
- Eq. (12)-(13): canopy aerodynamic and boundary identities are represented structurally.
- Eq. (14): `r_c = r_ST / LAI` is present in historical V2 but is not computed by the frozen V4 RC1 boundary.

### Manual canopy/stomatal rules associated with Eq. (14)

The recoverable manual uses a deliberately simple operational rule set:

- separate daytime and nighttime stomatal/epidermal resistance;
- nighttime resistance at least one order larger than daytime resistance in the source discussion;
- available-soil-water exhaustion closes stomata by switching to the nighttime resistance;
- daytime precipitation drives canopy resistance toward zero;
- nighttime precipitation does not remove the epidermal resistance;
- LAI converts leaf/stomatal resistance to canopy resistance.

Historical V2 reproduces day/night, LAI and the day-rain zero-resistance branch, but it replaces the manual soil-water threshold with no equivalent switch and adds a continuous VPD multiplier not required by the recoverable UFOTRI rule.

Therefore the historical VPD multiplier is a project/literature extension, not the required repair.

### Eq. (15)-(18): aerodynamic resistance and friction velocity

Historical V2 implements the Eq. (18) role `r_a = u/u_*^2` and uses stability-corrected logarithmic profiles. The current implementation is functionally close but not yet a clean manual compatibility mode because its geometry and Monin-Obukhov-length estimation are mixed with later assumptions.

### Eq. (19)-(21): boundary-layer resistance

This is a concrete fidelity gap.

UFOTRI reduces the scalar boundary resistance to:

`r_b = 2 / (k u_*)`  (Eq. 21)

Historical V2 instead uses a laminar flat-plate Sherwood correlation based on leaf characteristic length, kinematic viscosity and vapour diffusivity. That is a documented literature substitution and must remain available only as a non-UFOTRI alternative.

The fidelity path must implement Eq. (21) explicitly.

### Eq. (22)-(25): stability wind profile and vegetation-height mapping

Historical V2 contains neutral/stable/unstable logarithmic profile relations broadly corresponding to Eq. (22)-(24), but two fidelity issues remain:

1. the recovered manual does not expose a complete original formula for estimating Monin-Obukhov length; the current Golder mapping is therefore a named literature substitution, not an exact UFOTRI import;
2. the manual explicitly describes the Eq. (25) two-step procedure: station wind is first mapped to 100 m with the power law and then transformed to vegetation height with the stability-dependent logarithmic relation. Historical V2 does not implement that procedure as an explicit compatibility mode.

The fidelity implementation must therefore:

- expose the Eq. (25) two-step wind mapping;
- use the recoverable manual vegetation geometry (`z0 = 0.1 H`, `d = 0.6 H`, `FLQH = 0.8 H`, minimum area-source emission height 1 m) where applicable;
- accept an explicit/provenanced Monin-Obukhov length or an explicitly named estimator; it must not present the Golder approximation as exact UFOTRI source code.

### Eq. (26)-(31): HTO exchange, analytic equilibration and re-emission

The current signed V4 flux boundary has the correct bidirectional sign structure and historical V2 implements the Eq. (27) equilibrium concentration using saturated water-vapour density and liquid/vapour isotope fractionation.

However, the current post-RC1 chain advances TFWT storage using a precomputed interval-start flux multiplied by `dt`. The manual Eq. (27)-(30) provides a first-order ODE with an analytic exponential update under interval-constant `chi`, `mu`, `rho` and `r`.

Therefore a manual fidelity mode requires an opt-in analytic interval transfer implementing the Eq. (27)-(30) time constant and exponential approach/decay. The existing TFWT inventory solver remains valid as the general storage/conservation boundary and must not be removed.

Eq. (31) should be exposed as a compatibility diagnostic/re-emission-rate representation derived from the same analytic decay, while the authoritative conservation transfer remains one signed boundary quantity.

## Smallest authorized A2 implementation

The next stage is limited to an opt-in UFOTRI compatibility path containing:

1. manual canopy resistance rules: day/night, LAI, soil-water exhaustion switch, day-rain zero resistance;
2. Eq. (18) aerodynamic resistance with Eq. (22)-(25) wind-profile/geometry compatibility logic;
3. Eq. (21) boundary-layer resistance;
4. Eq. (27) saturated-vapour equilibrium conversion;
5. Eq. (27)-(30) analytic interval exchange/update;
6. Eq. (31) compatibility diagnostic;
7. explicit provenance when a Monin-Obukhov estimator is substituted because the original estimator is not recoverable from the available manual.

## Explicitly not authorized

This reconciliation does not authorize:

- replacing the RC1 default leaf path;
- generic Leaf R5 `g_s,max * F_light * F_VPD * F_temp * F_stage` physiology;
- parameter calibration;
- production parameter activation;
- real CTEAS-Atmos binding;
- unrelated crop physiology changes;
- removal of the historical V2 literature parameterization.

## Selected next stage

`UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1`

After implementation, the roadmap still requires a separate manual-regression/benchmark closure before Phase A is complete.
