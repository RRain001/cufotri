# ADR-058: UFOTRI replication gap audit R1

## Status

Proposed replication-fidelity audit after the frozen `V4_DEVELOPMENT_BASELINE_RC1`.

## Context

The RC1 merge established that the selected internal V4 software baseline is complete under controlled synthetic/replay forcing. That state does not establish full UFOTRI replication. The repository contains the KfK 4605 UFOTRI manual, historical V1/V2 implementations, V3 equation mappings, and the frozen V4 baseline, but the original UFOTRI source code and executable have not been recovered.

The purpose of this stage is therefore to distinguish three different claims:

1. completion of the selected V4 software baseline;
2. manual-based functional reconstruction of UFOTRI;
3. numerical equivalence to the original UFOTRI executable.

Only item 1 is currently complete. Item 2 remains incomplete. Item 3 is unprovable with the presently available source assets.

## Decision

Create `UFOTRI_REPLICATION_GAP_AUDIT_R1` as a governance-only comparison against the available manual and current repository. The audit classifies 30 manual/software capabilities using an explicit ontology and does not modify solver code, runtime parameters, production inputs, Atmos binding, or the frozen RC1 baseline.

The strongest claim permitted by this audit is `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION`; the audit explicitly forbids an exact-original-executable claim unless original source/executable regression material is recovered.

## Findings relevant to the three candidate extensions

### Leaf R5

The replication gap is real, but the existing `LEAF_R5_DYNAMIC_STOMATAL_IMPLEMENTATION` candidate is not automatically the required repair.

UFOTRI requires the recoverable Eq. (7)-(31) aerodynamic, boundary, stomatal/canopy, LAI, day/night, precipitation and meteorological exchange semantics. The repository already contains a historical V2 manual-informed dynamic leaf implementation in `src/cteas_ufotri/plant/leaf_exchange.py`, while the frozen V4 RC1 path uses the simpler explicit `r_a+r_b+r_c` boundary.

Therefore:

`CURRENT_R5_AS_DESIGNED_NOT_REQUIRED_FOR_REPLICATION`

but:

`UFOTRI_LEAF_EQ7_31_FIDELITY_RECONCILIATION_REQUIRED`

The required next action is to reconcile the historical V2 manual path against the original equations and determine the smallest post-RC1 fidelity path. Any empirical `g_s_max * F_light * F_vpd * F_temp * F_stage` enhancement beyond the recovered manual remains optional unless that reconciliation proves it necessary.

### Richards/Darcy

UFOTRI Eq. (33)-(37) explicitly describes soil water potential and Darcy/Richards transport. The current V4 soil solver accepts signed transport fluxes from its caller and does not compute those fluxes from the manual hydrologic relations.

Therefore:

`REPLICATION_REQUIRED_MANUAL_EQ33_37`

The required scope is the UFOTRI soil-hydrology mechanism, not an unconstrained general-purpose Richards solver.

### Multi-pool OBT

The current reduced `k_f/k_r` OBT baseline is compatible with first-order formation/loss roles but stores one aggregate OBT inventory. UFOTRI explicitly distinguishes exchangeable and non-exchangeable tritium and later embeds OBT in crop/grass/cow ingestion compartments.

Therefore:

`REPLICATION_REQUIRED_IN_NARROW_UFOTRI_FORM_ONLY`

A manual-faithful exchangeable/non-exchangeable reconstruction is required. A generic multi-pool or precursor-rich architecture is not automatically UFOTRI-equivalent and is not authorized by this audit.

## Other mandatory replication gaps

The three candidate extensions are not the complete remaining replication workload. The audit also identifies:

- separate HT atmospheric transport;
- HT-to-HTO soil conversion;
- pasture 40/60/0 root-layer behavior;
- reconciliation of historical re-emission/area-source feedback;
- reconciliation of historical V2 vegetable/grass/cow/milk/beef/inhalation/skin pathways with the post-RC1 architecture;
- replacement of the V4 terminal-harvest project boundary with an optional UFOTRI continuous-ingestion compatibility path;
- Canada 1987 and ITER manual benchmark reproduction.

The HT atmospheric branch and real atmospheric reconciliation remain deferred while the independent Atmos project is under development.

## Selected next stage

After a clean exact-head audit merge, select:

`UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1`

This is a reconciliation and fidelity-decision stage, not automatic Leaf R5 implementation. It must preserve RC1 as the default/fallback baseline and must not activate empirical parameters.

The subsequent high-priority replication items are:

1. `UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`;
2. `UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`;
3. `UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`.

The order after the first leaf reconciliation may be re-ranked if that reconciliation exposes a dependency.

## Explicit non-claims and frozen boundaries

This audit does not establish production readiness, real CTEAS-Atmos binding, empirical validation, physical accuracy, original UFOTRI executable equivalence, or active parameter calibration.

It does not authorize:

- the current Leaf R5 empirical candidate implementation;
- a generic full Richards/Darcy hydrology package;
- a generic multi-pool OBT architecture;
- changes to the frozen RC1 default path;
- changes to V3 defaults.
