# UFOTRI leaf Eq. (7)-(31) fidelity implementation R1

## Stage

`UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1`

## Candidate status

`CANDIDATE_PENDING_EXACT_HEAD_CI`

This report describes the A2 implementation candidate. Exact-head CI evidence is
recorded in PR metadata after the candidate head is frozen; post-merge evidence
is recorded by the master-plan synchronization stage.

## Base

`main = 4ff6fc0d6fd5a5f93f8b65fc05c11d3e3b8ed507`

This is the clean post-merge state of PR #59, where the master plan names A2 as
the immediate required stage.

## Source implementation

New opt-in package:

`src/cteas_ufotri/plant/leaf_ufotri_v4/`

Existing historical/default source files are intentionally not modified:

- `src/cteas_ufotri/plant/leaf_exchange.py`
- `src/cteas_ufotri/plant/leaf_exchange_resistance/resistance.py`
- `src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py`

Therefore the new path is available only through explicit import/call and cannot
silently replace RC1.

## Implemented manual roles

1. Eq. (12)-(14) canopy compatibility:
   day/night resistance, LAI scaling, soil-water-exhaustion switch, daytime-rain
   zero resistance, nighttime-rain epidermal resistance, and no VPD multiplier.
2. Eq. (18), (22)-(25): explicit station->100 m power-law step followed by the
   stability-dependent logarithmic transformation to vegetation height;
   `z0=0.1H`, `d=0.6H`, `FLQH=max(0.8H,1 m)`.
3. Monin-Obukhov provenance: either explicit length plus source/revision or the
   named `GOLDER_1972_APPROXIMATION`. The latter is explicitly not exact original
   UFOTRI logic.
4. Eq. (21): `r_b = 2/(k u_*)`.
5. Eq. (26): reuse the existing single signed `LeafExchangeFlux` conservation
   boundary.
6. Eq. (27): saturated-vapour-density equilibrium on the `TFWTState` mass basis.
7. Eq. (27)-(30): exact exponential interval update under interval-constant
   forcing/resistance/water content, with exact integrated inventory transfer.
8. Eq. (31): zero-air re-emission fraction diagnostic from the same exponential
   decay; no second conservation flux is created.

## Numerical/contract tests included

`tests/v4/test_ufotri_leaf_eq7_31_fidelity_implementation_r1.py` covers:

- canopy day/night/soil-water/rain branches;
- fail-closed zero LAI;
- recovered geometry ratios and FLQH floor;
- exact Eq. (21);
- Eq. (25) two-step wind mapping;
- explicit and Golder Monin-Obukhov provenance routes;
- rejection of missing/ambiguous provenance;
- projection of manual resistance components onto frozen `ResistanceChain`;
- Eq. (27) saturated-vapour equilibrium;
- Eq. (27)-(30) inventory/mean-flux identity;
- equilibrium fixed point;
- one-interval vs two-half-interval restart equivalence;
- Eq. (31) zero-air decay diagnostic;
- exact leaf transfer through the existing TFWT storage contract;
- source isolation from the historical V2 and frozen RC1 files.

## Interpretation boundary

A successful A2 exact-head CI means only that the selected manual-fidelity leaf
mechanisms are implemented and internally tested as an opt-in compatibility
path. It does not establish empirical validation, calibrated parameters,
production readiness, real CTEAS-Atmos coupling, physical-accuracy claims, or
original-executable numerical equivalence.

A3 remains mandatory after a clean A2 merge:

`UFOTRI_LEAF_EQ7_31_MANUAL_REGRESSION_CLOSURE_R1`
