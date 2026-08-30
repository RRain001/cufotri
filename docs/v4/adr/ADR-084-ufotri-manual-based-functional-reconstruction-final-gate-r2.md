# ADR-084 — UFOTRI Manual-Based Functional Reconstruction Final Gate R2

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`

## Context

Historical G4 closed the then-known recoverable internal reconstruction. A later source/architecture review showed that UFOTRI's own modified-MUSEMET atmospheric path had been incorrectly externalized to CTEAS-Atmos. The post-G4 correction roadmap therefore reopened the whole-model reconstruction claim and authorized H1-H6.

H1-H5 have now completed the native-atmosphere recovery sequence through the environment and dose endpoint. H6 is the corrected qualification-only final gate.

## Decision

R2 must not erase or reinterpret G4 as a failed stage. G4 remains valid historical evidence for the A-G scope it audited. R2 supersedes G4 only as the **current** final-gate authority by adding the later H1-H5 native-atmosphere evidence.

R2 qualifies completion only if all of the following hold simultaneously:

1. H1-H5 are recorded COMPLETE in the correction roadmap and each certified head is a parent of its recorded merge with identical candidate/merge tree and merge ancestry to the H6 candidate.
2. H1-H5 machine gates re-execute with their expected PASS states.
3. The historical G3 cross-module aggregate gate still re-executes PASS and the historical G4 evidence remains present rather than rewritten.
4. H4/H5 source-limited mechanisms remain explicitly source-limited: original MUSEMET closed-form numerical identity, `IWASH=1` REGTIM, lift-off Eq. (3.22), complete building wake, complete plume rise, Eq. (44) original executable rate generation, mixed-origin partition, Canada full replay and ITER full atmospheric replay.
5. Atmospheric HT→HTO remains disabled on the KfK 4605 fidelity route while deposited-soil HT→HTO remains complete.
6. CTEAS-Atmos remains an optional later higher-fidelity backend, not a blocker for the standalone manual reconstruction.
7. The candidate remains qualification-only and does not preemptively set the reconstruction flag true.

If these checks pass, the permitted machine result is:

`PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`

The reconstruction flag still remains false in the H6 candidate. It may be restored to true only after exact-head CI, expected-head merge, post-merge no-drift certification, and a separate correction-roadmap status sync.

## Source-limited versus recoverable

R2 distinguishes an unimplemented recoverable internal mechanism from a mechanism whose exact historical numerics cannot be recovered from available authoritative material. The latter does not get silently approximated and does not block a *manual-based functional reconstruction* claim when the boundary is explicit.

This distinction does not grant an original-executable numerical-equivalence claim.

## Claim boundary after a future clean status sync

Permitted:

`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`

Still not permitted:

- `UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE=TRUE`;
- original UFOTRI executable numerical equivalence;
- full Canada empirical/numerical replay;
- full ITER atmospheric numerical replay;
- complete historical building-wake/plume-rise numerical equivalence;
- production parameter readiness;
- empirical validation or physical-accuracy validation;
- CTEAS-Atmos binding completion.

## Scope

H6 changes only its ADR, governance ledger, report, machine gate and focused tests. It changes no production source, defaults, workflow or roadmap.
