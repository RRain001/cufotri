# ADR-062: UFOTRI OBT exchangeable/non-exchangeable reconstruction R1

## Status

Proposed closure for:

`UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`

## Context

Phase A closed the recoverable leaf Eq. (7)-(31) mechanism. The replication master plan therefore advances to the plant OBT compartment semantics described by KfK 4605 Section 2.2.6 and the related ingestion-compartment equations in Section 3.3.3.

The frozen post-RC1 implementation already contains:

- `TFWTState`, an activity inventory on the plant-water pathway;
- `OBTState`, one aggregate organic-tritium inventory;
- `OBTSolver`, a first-order `kf * TFWT - kr * OBT` operator;
- the controlled Section-2.2.6 daily-average baseline `kf=0.0006 h^-1`, `kr=0.003 h^-1`, represented internally in `s^-1`;
- downstream food transfer that already consumes TFWT and OBT as separate components.

The question for B1 is therefore not whether to invent a new generic multi-pool OBT model. It is whether the existing two public plant states can be mapped faithfully onto the recoverable UFOTRI exchangeable/non-exchangeable semantics, and which rate contexts may be attached to that mapping.

## Manual reconciliation

### Exchangeable OBT

KfK 4605 Section 2.2.6 states that exchangeable organically bound tritium is in equilibrium with free HTO in plant water and need not be distinguished from free HTO in the model.

Decision:

- no independent exchangeable-OBT inventory is added;
- `TFWTState` remains the model representation for the free-HTO plus exchangeable-OBT role;
- exchangeable OBT must not be added again when plant activity is transferred to food, because that would double count activity already represented on the TFWT path.

### Non-exchangeable OBT

The same section identifies the persistent organic-tritium compartment as the separate modelling state. The current `OBTState` is therefore interpreted, only within the opt-in UFOTRI semantic path, as non-exchangeable OBT.

The existing first-order inventory structure is compatible with the manual compartment formulation:

`plant HTO -> non-exchangeable OBT -> loss/return`

No change to the frozen `obt_v3` solver is required for this structural mapping.

## Rate reconciliation

Two linked manual descriptions are recoverable.

### Section 2.2.6 hourly atmospheric/dispersion context

The manual states:

- daily-average OBT incorporation: `0.06 % h^-1 = 0.0006 h^-1` of plant HTO;
- mean organic-tritium loss: `0.3 % h^-1 = 0.003 h^-1`;
- daytime formation is increased and nighttime formation reduced;
- no unambiguous normalized day/night multiplier pair is recovered in the available text.

The current controlled baseline uses exactly the two stated daily-average rates and `1/1` day/night multipliers. The `1/1` pair is a neutral average-preserving software choice, not a recovered original UFOTRI diurnal parameterization.

### Section 3.3.3 ingestion context, Eq. (65)-(66)

For vegetables the manual states:

- Eq. (65): `t15,14 = ln(2)/10 d = 0.069314718... d^-1`;
- organic plant mass `0.1 kg m^-2`;
- inorganic plant mass `0.4 kg m^-2`;
- water-hydrogen divisor `9`;
- organic-hydrogen divisor `13`;
- Eq. (66): `t14,15 = t15,14 * M_OBT * 9 / (M_HTO * 13)`, approximately `0.012 d^-1`.

The exact value reconstructed from the stated masses is approximately `0.0119967781 d^-1`.

Section 2.2.6 also says ingestion transfer paths/rates are transmitted to the dispersion submodule by adaptation to hourly time steps. This establishes the intended first-order inventory-transfer role and resolves the earlier concern that the current `kf * TFWT inventory` form lacks any manual compartment basis.

However, the two numerical expressions are not identical after simple division by 24:

- Eq. (66)/24 ≈ `0.0004998658 h^-1`, versus Section 2.2.6 `0.0006 h^-1`, about 20.0% higher relative to Eq. (66)/24;
- Eq. (65)/24 ≈ `0.0028881133 h^-1`, versus Section 2.2.6 `0.003 h^-1`, about 3.9% higher relative to Eq. (65)/24.

The available evidence does not establish whether these differences arise from rounding, a different short-term parameter basis, later model tuning, or another original implementation choice. B1 therefore preserves both profiles and does not assert exact original-executable parameter equivalence.

## Decision

Create an opt-in `plant/obt_ufotri_v4` semantic compatibility layer that:

1. maps exchangeable OBT to the existing TFWT representation without adding a third inventory;
2. maps `OBTState` to non-exchangeable OBT;
3. validates plant identity, crop, growth stage, timestamp and area basis before the two states can be viewed together;
4. records the Section-2.2.6 daily-average profile separately from the Section-3.3.3 Eq. (65)-(66) ingestion profile;
5. quantifies their numerical difference rather than silently choosing one as the unique original parameterization;
6. exposes the frozen daily-average `obt_v3` profile as a controlled short-term baseline without changing it;
7. leaves normalized day/night formation multipliers explicitly unresolved.

No existing RC1/V3 source file is modified in B1.

## Consequences

After B1, the project may claim that the recoverable exchangeable/non-exchangeable plant-state roles and first-order OBT transfer structure have been reconstructed at the manual-semantic level.

B1 does not establish:

- exact original UFOTRI day/night OBT formation multipliers;
- exact original-executable selection between the Section-2.2.6 and Eq. (65)-(66) numerical values;
- empirical validation;
- production parameter calibration;
- generic multi-pool OBT physiology;
- continuous ingestion food-chain closure;
- whole-model UFOTRI completion.

## Next stage

After exact-head CI and merge/no-drift closure, the selected next stage is:

`UFOTRI_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION_R1`

That stage must qualify the reconstructed state semantics numerically, explicitly compare the controlled Section-2.2.6 daily-average profile with the Eq. (65)-(66)-derived rate profile, and preserve all unresolved-source labels rather than converting numerical agreement into an original-equivalence claim.
