# UFOTRI Manual-Based Functional Reconstruction Final Gate R2

Stage: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Base: `main@23ca602fe136a805d9be268acf33194b8ce9fd35`

## Purpose

This is the corrected final gate after recovery of the UFOTRI-native modified-MUSEMET atmospheric route. It is a qualification stage only.

Historical G4 is preserved as the final gate for its original A-G scope. R2 adds H1-H5 and becomes the current final-gate authority only if its own lifecycle closes cleanly.

## Evidence audited

### Historical internal reconstruction

R2 preserves the prior G3/G4 evidence chain and re-executes the G3 aggregate gate. It does not use the obsolete historical assumption that all primary atmospheric transport belongs to CTEAS-Atmos.

### H1-H5 native atmosphere correction

R2 audits the current correction-roadmap ledgers and actual git ancestry/tree identity for:

- H1 native primary atmosphere core;
- H2 hourly segmented/bent trajectory;
- H3 native HT/HTO forcing adapters;
- H4 KfK 4332/KfK 5194 atmospheric-process reconciliation;
- H5 native atmosphere → soil/root/leaf/TFWT/OBT → food → dose qualification.

Each H1-H5 machine gate is re-executed rather than accepted solely from prose status.

## Required source boundaries

Passing R2 requires the following to remain explicit non-claims/source limits:

- original MUSEMET three-case closed-form numerical equivalence;
- `IWASH=1` power-law `REGTIM` numeric default;
- numerical KfK 4332 lift-off Eq. (3.22);
- complete original building-wake numerics;
- complete `PLRISE/RISEFX` plume-rise numerics;
- original executable Eq. (44) rate-generation semantics;
- reconstruction of HT-derived versus primary HTO after provenance-destructive aggregation;
- full Canada 1987 numerical/empirical replay;
- full ITER atmospheric numerical replay;
- original UFOTRI executable equivalence.

These are not filled with modern surrogate physics.

## Chemical boundary

For the KfK 4605 route:

`ATMOSPHERIC_HT_TO_HTO_CONVERSION=DISABLED`

while the already-qualified soil path remains:

`DEPOSITED_HT → SOIL_HTO`

The conflicting `0.5 %/d` ITER input remains evidence-only unless a separately versioned UFOTRI implementation proves it active.

## CTEAS-Atmos boundary

CTEAS-Atmos is now a deferred optional higher-fidelity backend. Its future HT/HTO bindings may be important for the broader CTEAS software product and real project applications, but they do not block standalone manual-based UFOTRI functional reconstruction.

## Qualification lifecycle

The H6 candidate does **not** set the reconstruction completion flag true.

Expected machine result:

`PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`

Only after exact-head Remediation and Protected CI, expected-head merge, and merge-tree/no-drift certification may a separate correction-roadmap sync restore:

`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`

Broader replication, empirical validation, production readiness, physical accuracy and original numerical equivalence remain outside that claim.
