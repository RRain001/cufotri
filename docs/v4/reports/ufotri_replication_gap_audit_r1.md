# UFOTRI replication gap audit R1

## Executive result

`UFOTRI_REPLICATION_GAP_AUDIT_R1 = PASS_GAP_INVENTORY_AND_EXTENSION_DECISION`

The frozen V4 RC1 baseline is internally complete, but the repository is not a complete UFOTRI replication.

```text
V4_SOFTWARE_DEVELOPMENT_BASELINE_COMPLETE = TRUE
UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE = FALSE
UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE = NOT_ESTABLISHED
UFOTRI_ORIGINAL_SOURCE_CODE = SOURCE_UNAVAILABLE
UFOTRI_ORIGINAL_EXECUTABLE = SOURCE_UNAVAILABLE
```

The available KfK 4605 manual is sufficient to audit recoverable equation roles and functional pathways. It is not sufficient to establish undocumented original defaults, software-specific field semantics, or numerical equivalence to the original executable.

## Evidence reviewed

Primary evidence:

- `ufotri_manual.md` — recovered KfK 4605 manual transcription;
- `docs/v2/manual_equation_inventory.md` — complete numbered-equation inventory for the available manual;
- `docs/v2/manual_to_code_matrix.md` — historical V2 process mapping;
- `docs/v3/reports/v3_p7_6c2_ufotri_source_inventory.md` — original-source availability audit;
- `docs/v3/reports/v3_p7_6c2_equation_mapping_report.md` — V3 equation-semantic audit;
- `docs/v4/governance/v4_current_system_state.yaml` and ADR-057 — frozen post-RC1 selected baseline;
- current leaf, soil, OBT and food-chain source files.

The original UFOTRI source implementation and executable are absent. Consequently this audit uses `manual-based functional reconstruction` as the achievable replication target.

## Matrix result

The machine-readable governance file contains 30 audited capabilities.

| Classification | Count |
|---|---:|
| MANUAL_ROLE_COVERED | 2 |
| FUNCTIONAL_RECONSTRUCTION | 5 |
| PARTIAL_RECONSTRUCTION | 5 |
| HISTORICAL_IMPLEMENTATION_NOT_IN_RC1 | 8 |
| NOT_IMPLEMENTED | 5 |
| PROJECT_REPLACEMENT_NOT_EQUIVALENT | 1 |
| NOT_IMPLEMENTED_AS_VALIDATION | 2 |
| UNVERIFIABLE_SOURCE_UNAVAILABLE | 2 |
| **Total** | **30** |

The counts are descriptive, not a percentage score. A missing HT conversion pathway is not equivalent in importance to a missing benchmark regression, so no synthetic “replication percentage” is claimed.

## What is already structurally strong

The current project already covers a large part of the HTO environmental chain:

- Gaussian atmospheric transport and deposition framework;
- three-layer soil activity states;
- controlled UFOTRI Eq.39 root-water uptake;
- nutrient-crop 20/40/40 root profile;
- explicit leaf resistance identity `r_a+r_b+r_c`;
- TFWT dynamic inventory;
- reduced first-order OBT formation/loss;
- food/intake/dose endpoint;
- historical V2 re-emission, animal, milk, beef, inhalation and skin-dose code.

This explains why RC1 legitimately closed the selected V4 software baseline. It does not close the UFOTRI fidelity target because several original manual mechanisms are either collapsed, historical-only, replaced by a project boundary, or absent.

## Highest-impact replication gaps

### 1. HT branch

UFOTRI is a two-chemical-form model. The original model treats HT/T2 as a separate atmospheric form and includes conversion of deposited HT into HTO in soil. The selected V4 baseline is HTO-only. No current post-RC1 HT-to-HTO soil oxidation path was found.

This is a mandatory full-replication gap. Atmospheric HT transport is deferred while CTEAS-Atmos is still under development; the internal chemistry gap remains recorded for later work.

### 2. Leaf Eq. (7)-(31) fidelity

The V4 resistance subsystem implements the direct manual component identity:

`r_total = r_a + r_b + r_c`

but it consumes resistance components rather than calculating the complete dynamic manual chain.

Historical V2 code is materially closer to the manual: it calculates aerodynamic resistance, boundary resistance, day/night stomatal behavior, LAI effects, VPD response, precipitation handling and the Eq.27 saturated-vapour equilibrium relation. However, it also contains literature substitutions and is not the frozen V4 path.

Therefore the replication problem is a reconciliation problem before it is a new-model problem.

### 3. Soil Eq. (33)-(37) hydrology

The current V4 soil solver explicitly states that signed layer transport is an interface input and is not calculated from hydrology, diffusion or percolation. UFOTRI Eq. (33)-(37) describes soil water potential and Darcy/Richards transport.

This is a direct manual-mechanism omission and is required for a full manual-based reconstruction.

### 4. OBT compartment fidelity

The reduced `k_f/k_r` solver is a valid controlled first-order baseline but one aggregate OBT inventory does not reproduce the manual’s explicit exchangeable/non-exchangeable distinction. The original ingestion system further distributes HTO/OBT through crop, grass, cow and milk compartments.

A narrow UFOTRI exchangeable/non-exchangeable reconstruction is therefore required. A generic multi-pool extension is not automatically the correct solution.

### 5. Continuous ingestion model vs V4 harvest boundary

UFOTRI Eq. (45)-(105) is a continuous first-order compartment system. The V4 controlled endpoint intentionally uses `KEEP_HARVEST_EVENT`. Historical V2 already contains animal and product inventories, but these have not been reconciled into a post-RC1 UFOTRI-compatibility path.

Thus food-chain functionality exists in the repository, but the current V4 baseline is not functionally equivalent to the full original ingestion system.

### 6. Validation against manual applications

The manual includes the Canada 1987 HT release comparison and ITER HTO/HT benchmark calculations. Synthetic software tests are not substitutes for these published application cases.

A manual-based replication cannot be declared complete until recoverable benchmark inputs/outputs have been reconstructed and compared under an explicit tolerance policy.

## Decision on Leaf R5

Decision:

`CURRENT_R5_AS_DESIGNED_NOT_REQUIRED_FOR_REPLICATION`

but:

`UFOTRI_LEAF_EQ7_31_FIDELITY_RECONCILIATION_REQUIRED`

The existing R5 concept uses a new empirical response structure such as
`g_s_max * F_light * F_vpd * F_temp * F_stage`. That may be scientifically useful, but the audit found no basis for treating that exact structure as the missing UFOTRI implementation.

The next step should instead compare the historical V2 manual-informed leaf code, the V4 resistance contract and UFOTRI Eq. (7)-(31), then port only the required manual semantics into a post-RC1 optional fidelity profile. Leaf R5 remains a later evidence-driven enhancement if gaps remain.

## Decision on Richards/Darcy

Decision:

`REPLICATION_REQUIRED_MANUAL_EQ33_37`

The important qualifier is scope. The project does not need a general hydrologic research model merely to claim UFOTRI reconstruction. It needs the recoverable UFOTRI Eq. (33)-(37) water-potential / Darcy-Richards mechanism with the original compartment/depth semantics and auditable coupling to the current three-layer HTO ledger.

Therefore “full Richards/Darcy” should be renamed for this track to:

`UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION`

This prevents unnecessary physics expansion.

## Decision on multi-pool OBT

Decision:

`REPLICATION_REQUIRED_IN_NARROW_UFOTRI_FORM_ONLY`

A separate exchangeable/non-exchangeable treatment is required to close the explicit manual distinction. A three-pool precursor/exchangeable/non-exchangeable architecture, or any larger generic multi-pool model, is not automatically required.

The proper first stage is:

`UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`

It should first recover the exact state definitions, transfer roles, day/night assumptions and interfaces implied by the manual before adding any extra state.

## Recommended sequence

The next immediate stage is:

`UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1`

Reason: the relevant historical V2 implementation already exists, so this stage can produce a high-fidelity result with limited new code and without waiting for Atmos.

After leaf reconciliation, the current recommended order is:

1. `UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`;
2. `UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`;
3. `UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`.

HT atmospheric transport remains deferred to the Atmos dependency. HT-to-HTO soil chemistry remains a mandatory future UFOTRI gap and should be scheduled when the HT interface is stable.

The final replication acceptance phase should reconstruct the Canada 1987 and ITER manual cases.

## Boundary statement

This audit changes no solver, runtime parameter, production input, Atmos binding or RC1 default. It authorizes only the next reconciliation stage after a clean audit merge.

The current project may be described as:

`V4_INTERNAL_SOFTWARE_BASELINE_COMPLETE`

and:

`UFOTRI_MANUAL_BASED_RECONSTRUCTION_ADVANCED_BUT_INCOMPLETE`

It may not be described as:

`UFOTRI_FULL_REPLICATION_COMPLETE`

or:

`UFOTRI_ORIGINAL_EXECUTABLE_NUMERICAL_EQUIVALENCE_ESTABLISHED`.
