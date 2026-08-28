# ADR-060: UFOTRI leaf Eq. (7)-(31) fidelity implementation R1

## Status

Proposed implementation for the A2 stage authorized by ADR-059.

Stage:

`UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1`

## Context

ADR-059 concluded `SOURCE_CHANGES_REQUIRED=TRUE` after reconciling the recoverable
UFOTRI KfK 4605 Eq. (7)-(31) leaf/atmosphere exchange relations against the
historical V2 implementation and the frozen V4 RC1 resistance/TFWT interfaces.

The historical V2 implementation is manual-informed, but it mixes recoverable
UFOTRI relations with later literature substitutions. In particular it uses a
flat-plate Sherwood boundary-layer resistance, a continuous VPD multiplier, and
a Golder Pasquill-to-Monin mapping without a separate manual-compatibility mode.
The frozen RC1 pathway, in turn, consumes explicit `r_a + r_b + r_c` and advances
TFWT from a signed interval-start flux.

A2 must implement the smallest opt-in manual-fidelity path without silently
changing either of those existing behaviors.

## Decision

Add a separate opt-in package:

`src/cteas_ufotri/plant/leaf_ufotri_v4/`

No historical V2 leaf source and no frozen RC1 resistance/TFWT source is modified
by this stage.

### Eq. (12)-(14) and manual canopy rules

The compatibility path computes canopy resistance directly from the recoverable
manual rules:

- `r_c = r_ST / LAI`;
- daytime uses the daytime stomatal resistance;
- available-soil-water exhaustion switches daytime to the nighttime resistance;
- daytime precipitation sets canopy resistance to zero;
- nighttime retains nighttime/epidermal resistance even during precipitation;
- no VPD multiplier is present in the manual compatibility mode.

`LAI <= 0` fails closed. The compatibility path does not infer a no-leaf state or
silently substitute a finite resistance.

### Eq. (18), Eq. (22)-(25), and geometry

The compatibility geometry is explicit:

- `z0 = 0.1 H`;
- `d = 0.6 H`;
- `FLQH = 0.8 H`, with the recovered minimum area-source emission height of 1 m.

Eq. (25) is represented explicitly as two steps:

1. station wind -> 100 m by a caller-supplied power-law exponent;
2. 100 m wind -> vegetation height by the stability-dependent logarithmic
   profile used for Eq. (22)-(24).

The power-law exponent has no hidden default in the A2 public function.

The available manual does not recover the original Monin-Obukhov-length
estimator. Therefore exactly one provenance route is required:

- an explicit Monin-Obukhov length with explicit source ID and revision; or
- the named `GOLDER_1972_APPROXIMATION` literature estimator.

The Golder route is explicitly marked as a literature approximation and cannot
claim exact original-UFOTRI source logic.

Aerodynamic resistance retains the recoverable Eq. (18) identity:

`r_a = u / u_*^2`.

### Eq. (19)-(21)

The manual compatibility path implements Eq. (21) directly:

`r_b = 2 / (k u_*)`.

The historical flat-plate Sherwood implementation remains available in its
historical V2 path and is not deleted or relabeled as UFOTRI Eq. (21).

### Eq. (26)-(30)

The signed authoritative air/leaf conservation boundary remains the existing
`LeafExchangeFlux` convention: positive is air -> leaf; negative is leaf -> air.

For `TFWTState`'s mass concentration basis (Bq kg-water^-1), Eq. (27)'s
atmospheric-equivalent concentration is

`C_air,eq = C_TFWT * rho_v,sat / alpha`.

For interval-constant air concentration `chi`, plant water mass per area `mu`,
saturated vapour density `rho`, fractionation `alpha`, and total resistance `r`,
the compatibility mode evaluates the recoverable analytic interval exactly:

`k_ex = rho / (alpha * mu * r)`

`C_target = alpha * chi / rho`

`C(t+dt) = C_target + (C(t) - C_target) exp(-k_ex dt)`.

The exact integrated inventory transfer is

`Delta M_leaf = mu [C(t+dt) - C(t)]`.

It is projected onto the frozen signed flux API as the interval-mean flux
`Delta M_leaf / dt`. Therefore the existing TFWT storage boundary receives the
exact integrated Eq. (27)-(30) leaf transfer without changing its public
contract.

Root uptake, water loss and transformation remain their existing explicit
operators. A2 does not claim a new simultaneous analytic solution for those
independent terms.

### Eq. (31)

A2 exposes the compatibility zero-air re-emission diagnostic from the same
analytic decay:

`f_reemit(dt) = 1 - exp(-k_ex dt)`.

The diagnostic is not a second conservation flux. The single signed
`LeafExchangeFlux` remains authoritative for activity transfer.

## Fail-closed choices

A2 deliberately rejects:

- missing or ambiguous Monin-Obukhov provenance;
- an unstated station-to-100 m power-law exponent;
- zero/negative LAI in an activated leaf-compatibility calculation;
- non-positive resistance, water-content, temperature, fractionation or time
  interval;
- any claim that the Golder approximation is recovered original UFOTRI code.

## Frozen boundaries

- `V4_RC1_DEFAULT_PATH_CHANGED=FALSE`
- `HISTORICAL_V2_LEAF_PATH_CHANGED=FALSE`
- `GENERIC_EMPIRICAL_LEAF_R5_IMPLEMENTED=FALSE`
- `PARAMETER_CALIBRATION_STARTED=FALSE`
- `PRODUCTION_PARAMETER_ACTIVATION=FALSE`
- `REAL_CTEAS_ATMOS_BINDING=FALSE`
- `EMPIRICAL_VALIDATION=FALSE`
- `PHYSICAL_ACCURACY_CLAIM=FALSE`
- `ORIGINAL_UFOTRI_EXECUTABLE_EQUIVALENCE=NOT_ESTABLISHED`

## Completion boundary

This PR may complete A2 only after exact-head CI passes and a merge/no-drift
audit succeeds. A separate A3 manual-regression/benchmark stage remains required
before the Leaf phase can be declared complete.
