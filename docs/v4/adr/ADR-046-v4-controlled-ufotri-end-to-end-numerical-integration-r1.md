# ADR-046: Controlled UFOTRI end-to-end numerical integration R1

## Status

Accepted for software/numerical integration only.

## Context

The controlled V4 path now has three previously separate UFOTRI decisions implemented and individually tested:

1. reduced OBT uses the adopted UFOTRI `kf/kr` baseline;
2. total root-water uptake uses the controlled UFOTRI Eq.39 equilibrium-radiation boundary;
3. total uptake is distributed across the three root-zone layers as 20/40/40.

The software chain to the terminal food/intake/dose endpoint already exists, but the newly adopted UFOTRI root and OBT profiles had not yet been exercised together through the entire replay-to-dose chain.

## Decision

Run a 24 h deterministic synthetic/replay numerical integration through:

`replay atmosphere + explicit net-radiation support -> Eq.39 root total uptake -> UFOTRI 20/40/40 -> atmospheric leaf exchange + three-layer soil/root -> TFWT -> UFOTRI OBT baseline -> terminal harvest -> intake -> dose`.

No production solver equation is changed. Net radiation remains an explicit replay-support input to the Eq.39 boundary; it is not inferred from CTEAS-Atmos. The current three-layer soil water inventory is passed explicitly as the Eq.41 soil-water state for this numerical integration, while maximum/wilting water and LAI remain synthetic case inputs.

## Required numerical gates

The integration must demonstrate:

- positive Eq.39 root uptake under positive daytime net radiation;
- exact zero root uptake at zero nighttime net radiation;
- exact 20/40/40 distribution and layer-sum identity;
- `J_root,i = q_w,i C_w,i` in the existing root solver;
- plant and coupled conservation closure;
- deterministic repeat;
- restart equivalence after serialization at 12 h;
- nonzero UFOTRI-baseline OBT at 24 h;
- non-mutating terminal harvest endpoint;
- nonzero food inventory, annual intake and committed dose;
- preserved H-3 food-ingestion identity and no hidden mass/area conversion.

## Interpretation

A pass means `SOFTWARE_CHAIN_CONNECTED_WITH_CONTROLLED_UFOTRI_PROFILES=TRUE` and preserves `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE` for the controlled Eq.39 construction path.

It does not mean the complete model is production ready. It does not authorize empirical validation claims, calibration, Leaf R5, multi-pool OBT, full soil hydrology, the UFOTRI short-term 3 h delay, Eq.38 empirical aerodynamic production use, or real CTEAS-Atmos binding.

## Next control-plane action

After a clean merge, perform `V4_POST_CONTROLLED_UFOTRI_SYSTEM_REVIEW_R1` before adding another physics subsystem. That review must re-rank the remaining blockers with the OBT-baseline and root-`q_w` items removed from the unresolved list.
