# UFOTRI OBT exchangeable/non-exchangeable reconstruction R1

## Candidate result

`UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1 = CANDIDATE_SEMANTIC_RECONSTRUCTION_COMPLETE_PENDING_CI`

This stage reconstructs the recoverable plant OBT state roles without modifying the frozen `obt_v3`, `tfwt_v3`, or `food_v3` implementations.

## Main finding

The master-plan wording “exchangeable/non-exchangeable OBT reconstruction” must not be implemented as two new OBT pools.

KfK 4605 Section 2.2.6 explicitly states that exchangeable OBT is in equilibrium with free HTO in plant water and need not be distinguished from free HTO in the model. Therefore the narrow UFOTRI-compatible mapping is:

```text
free plant HTO + exchangeable OBT role -> existing TFWTState
non-exchangeable OBT                 -> existing OBTState
```

No third exchangeable-OBT activity inventory is created. This also preserves the current food interface, which already transfers TFWT and OBT as two separate plant components. Adding exchangeable OBT as a third source would risk double counting.

## First-order transfer structure

The current reduced solver uses the structure:

```text
dM_OBT/dt = kf * M_TFWT - kr * M_OBT
```

B1 initially treated the mass-basis mapping as potentially unresolved because Section 2.2.6 describes formation in terms of plant HTO concentration. A cross-check against Section 3.3.3 resolves the structural part of that concern.

Eq. (66) explicitly defines the transfer coefficient from the plant HTO compartment to the plant OBT compartment using the stated organic/inorganic plant masses and hydrogen divisors. Section 2.2.6 additionally states that ingestion transfer paths and rates are transmitted to the dispersion submodule after adaptation to hourly time steps. Therefore a first-order HTO-inventory-to-non-exchangeable-OBT-inventory transfer is a recoverable UFOTRI structure.

The current `OBTSolver` equation therefore does not require redesign merely to represent the narrow manual compartment topology.

## Numerical rate reconciliation

### Section 2.2.6

Recovered daily-average hourly values:

- HTO -> non-exchangeable OBT: `0.0006 h^-1`;
- non-exchangeable OBT loss: `0.003 h^-1`.

The manual says formation is higher in daytime and reduced at night, but no auditable normalized day/night multiplier pair is recovered. The frozen V4 `1.0/1.0` multipliers preserve the daily-average value only and are not labeled original UFOTRI diurnal parameters.

### Section 3.3.3 Eq. (65)-(66)

For the vegetable compartment:

- Eq. (65): `t15,14 = ln(2)/10 = 0.069314718... d^-1`;
- organic mass: `0.1 kg m^-2`;
- inorganic mass: `0.4 kg m^-2`;
- water hydrogen divisor: `9`;
- organic hydrogen divisor: `13`;
- Eq. (66): `t14,15 = t15,14 * M_OBT * 9 / (M_HTO * 13)`;
- exact result from those stated values: approximately `0.0119967781 d^-1`, consistent with the manual's rounded `0.012 d^-1`.

Hourly conversion gives approximately:

- Eq. (66)/24: `0.0004998658 h^-1`;
- Eq. (65)/24: `0.0028881133 h^-1`.

These are close to but not identical with the Section-2.2.6 values:

- forward rate: Section 2.2.6 is about 20.0% higher relative to Eq. (66)/24;
- loss rate: Section 2.2.6 is about 3.9% higher relative to Eq. (65)/24.

The available manual does not establish whether this difference is due to rounding, revised short-term assumptions, tuning, or another original-code choice. Both representations are therefore retained with distinct provenance.

## Implemented compatibility layer

New opt-in package:

`src/cteas_ufotri/plant/obt_ufotri_v4/`

It provides:

- `UFOTRIOBTRoleMap`;
- `UFOTRIOBTPlantStateView`;
- `UFOTRIShortTermOBTProfile`;
- `UFOTRILongTermIngestionOBTProfile`;
- `UFOTRIOBTRateReconciliation`;
- checked state-view construction that requires matching plant, crop, growth stage, timestamp and area basis;
- explicit exposure of the frozen Section-2.2.6 daily-average baseline without relabeling its `1/1` multipliers as recovered day/night physiology.

## Independent test matrix

`tests/v4/test_ufotri_obt_e_n_compartment_reconstruction_r1.py` verifies:

1. no separate exchangeable OBT pool is introduced;
2. exchangeable role maps to TFWT and non-exchangeable role maps to OBT;
3. the state view preserves exactly the two existing food-transfer activity components;
4. mismatched plant identity/time/area basis fails closed;
5. exact Section-2.2.6 daily-average values;
6. unresolved day/night multipliers remain explicit;
7. frozen baseline constants remain unchanged;
8. independent Eq. (65) reconstruction;
9. independent Eq. (66) reconstruction from the stated manual masses/divisors;
10. the Section-2.2.6 and Eq. (65)-(66) numerical profiles are related but not silently declared identical;
11. the ingestion profile is not rebound into the short-term solver in B1.

## Claim boundary

A successful exact-head merge supports:

`UFOTRI_OBT_STATE_ROLE_AND_FIRST_ORDER_STRUCTURE_RECONSTRUCTED=TRUE`

It does not support:

```text
UFOTRI_OBT_ORIGINAL_DIURNAL_PARAMETERIZATION_RECOVERED = FALSE
UFOTRI_OBT_ORIGINAL_EXECUTABLE_PARAMETER_SELECTION_ESTABLISHED = FALSE
GENERIC_MULTI_POOL_OBT_AUTHORIZED = FALSE
EMPIRICAL_VALIDATION = FALSE
PRODUCTION_PARAMETER_ACTIVATION = FALSE
UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE = FALSE
```

## Next stage

`UFOTRI_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION_R1`

B2 should numerically qualify the reconstructed compartment roles, conservation, deterministic repeat, restart equivalence, timestep behavior, and the effect of the two recoverable rate profiles while maintaining the source-ambiguity labels above.
