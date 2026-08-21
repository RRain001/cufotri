# V3-P5.5 UFOTRI Physics Boundary Audit Report

Date: 2026-08-21

## Final classification

```text
V3_P5_5_STATUS = REQUIRES_PHASE_RECLASSIFICATION
P5_5_RESULT = REQUIRES_PHASE_RECLASSIFICATION
NEXT = UPDATE_ROADMAP
```

## Reality freeze

```text
AUDIT_TARGET_SHA = 9e783acb0734d40347e845f1cf17d10f10cef9ab
P5_4_SHA = 9e783acb0734d40347e845f1cf17d10f10cef9ab
MAIN_SHA = 6671f5793d04842bf2ceae4904f3c0cf30a0d7e0
P5_5_BRANCH = codex/v3-ufotri-p5-5-boundary-audit
```

The audit was performed on a new branch. The P5.4 target branch was not
modified, merged, or rebased.

## Required status distinctions

```text
UFOTRI_PHYSICS_IMPLEMENTED = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
V3_FORMAL_PHYSICS = NOT_STARTED
SRC_CHANGE = 0              # P5.5 working diff relative to P5.4
CONFIG_CHANGE = 0           # P5.5 working diff relative to P5.4
SCHEMA_CHANGE = 0           # P5.5 working diff relative to P5.4
TRUSTED_REGISTRY_CHANGE = 0  # P5.5 working diff relative to P5.4
```

`UFOTRI_PHYSICS_IMPLEMENTED = FALSE` is supported by source inspection: no
reviewed UFOTRI equation, resistance law, stomatal conductance calculation, or
validated physical coefficient was found in the V3 modules. It must not be
expanded into the stronger claim that the repository contains only passive
interfaces.

## Why pure boundary confirmation fails

1. The P5-added V3 leaf, soil, food-chain, and dose packages include explicit
   `Synthetic*Kernel` numerical behavior. The leaf kernel evolves TFWT/OBT;
   the soil kernel transfers and decays layer inventory; the food-chain kernel
   transfers TFWT to OBT and decays it; the dose kernel computes intake times a
   supplied coefficient.
2. The existing repository soil tree includes `multibox.py` with three-box
   water/HTO advection, diffusion, drainage, evaporation, and root-uptake
   rates. This file is inherited from `main`, not introduced by P5.4, but a
   repository-level audit cannot omit it.
3. The specified unit tests assert numerical outputs for those test-only
   kernels. They are classified as `PREMATURE_PHYSICS_TEST` under the literal
   P5.5 rule, even though they do not claim UFOTRI validation.

These findings are phase-boundary findings, not evidence that validated
UFOTRI physics has been imported.

## Parameter result

The UFOTRI parameter database is still placeholder-only: all five entries
load with `value=None`, placeholder confidence/status, and pending units. The
reserved `UFOTRI_VALIDATED` source is not production-allowed and requires
external evidence. Therefore:

```text
UFOTRI_PARAMETER_IMPORTED = FALSE
```

## Decision and next action

The P5.4 **delta** is interface/review-only and has zero protected-path
changes. The **accumulated P1-P5 branch**, however, contains test-only
numerical kernels, food/dose arithmetic, and inherited experimental soil
transport. Consequently the label “interface freeze only” is too broad for a
repository-level statement.

```text
P5_5_RESULT = REQUIRES_PHASE_RECLASSIFICATION
NEXT = UPDATE_ROADMAP
```

The roadmap should distinguish passive contracts, retained test-only
numerical harnesses, inherited experimental solvers, and future reviewed
UFOTRI physics. P6 should not be described as the first point at which any
numerical behavior exists; it should be the first reviewed UFOTRI physics and
validated-parameter migration stage.
