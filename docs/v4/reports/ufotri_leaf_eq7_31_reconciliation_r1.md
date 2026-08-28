# UFOTRI Leaf Eq. (7)-(31) Reconciliation R1 Report

## Result

`UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1 = PASS_RECONCILIATION_SOURCE_CHANGES_REQUIRED`

The recovered KfK 4605 plant/atmosphere exchange mechanism is only partially represented by the current repository. Historical V2 is manual-informed but not a clean UFOTRI compatibility implementation; frozen V4 RC1 intentionally exposes only the resistance boundary and TFWT storage interfaces.

This stage changes no solver physics. It selects the smallest subsequent fidelity implementation required to close the manual gap.

## Main findings

### What is already covered

- `r_a + r_b + r_c` resistance identity;
- one signed air↔leaf exchange boundary;
- Eq. (18)-style aerodynamic-resistance role in historical V2;
- neutral/stable/unstable logarithmic profile family in historical V2;
- day/night stomatal resistance values, LAI scaling and the daytime-rain zero-canopy-resistance branch in historical V2;
- Eq. (27) saturated-vapour-density equilibrium conversion and liquid/vapour isotope fractionation in historical V2;
- explicit TFWT inventory/state and conservation boundary in V3/V4.

### Fidelity gaps that require A2 source changes

1. **Eq. (21) boundary resistance** — historical V2 uses a flat-plate Sherwood correlation instead of `r_b = 2/(k u_*)`.
2. **Eq. (25) wind mapping** — historical V2 does not expose the manual station-wind → 100 m power-law → vegetation-height logarithmic procedure as a compatibility mode.
3. **Manual canopy rule set** — the recovered UFOTRI logic uses day/night resistance, LAI, a soil-available-water exhaustion switch and precipitation rules. Historical V2 instead adds a continuous VPD multiplier and lacks the soil-water closure switch.
4. **Eq. (27)-(30) interval dynamics** — the post-RC1 pathway uses a precomputed signed flux integrated over `dt`; the manual specifies an exponential analytic solution under interval-constant forcing.
5. **Eq. (31) compatibility diagnostic** — negative signed flux/re-emission accounting exists, but the manual percentage-per-interval diagnostic is not exposed.
6. **Monin-Obukhov estimator provenance** — the available manual references an estimator but does not recover its complete original formula. The current Golder mapping must therefore remain an explicitly named literature substitution rather than an exact-UFOTRI claim.

## A2 authorized scope

The selected next stage is:

`UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1`

A2 is authorized to add an **opt-in** manual-compatibility path implementing only:

- manual day/night + LAI + soil-water exhaustion + rain canopy rules;
- Eq. (18) aerodynamic resistance and Eq. (22)-(25) wind-profile/geometry logic;
- Eq. (21) boundary-layer resistance;
- Eq. (27) equilibrium conversion;
- Eq. (27)-(30) analytic interval exchange/update;
- Eq. (31) compatibility diagnostic;
- explicit provenance for any Monin-Obukhov estimator substitution.

The RC1 fallback/default path remains unchanged.

## Not selected

The previously discussed generic Leaf R5 formulation is not required for UFOTRI replication. It may remain a future scientific extension but is not part of the replication closure path.

Likewise, this stage does not authorize parameter calibration, real Atmos coupling, production parameter activation, or broader crop-physiology redesign.

## Evidence basis

Primary:

- `ufotri_manual.md`, Section 2.2.2, Eq. (7)-(31);
- `docs/v2/manual_equation_inventory.md`;
- `docs/v2/manual_to_code_matrix.md`;
- `docs/v4/governance/ufotri_replication_gap_audit_r1.yaml`.

Implementation inspected:

- `src/cteas_ufotri/plant/leaf_exchange.py`;
- `src/cteas_ufotri/plant/leaf_exchange_resistance/resistance.py`;
- `src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py`;
- `src/cteas_ufotri/v4_integration/replay_input_orchestration.py`;
- `configs/default_parameters.yaml`.

## Completion statement

A1 may be marked complete after exact-head CI, merge and no-drift audit. The next authorized implementation stage is A2. A separate A3 manual-regression/benchmark closure remains required after A2 before Phase A can be considered complete.
