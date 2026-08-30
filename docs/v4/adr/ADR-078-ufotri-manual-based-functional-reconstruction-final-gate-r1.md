# ADR-078 — UFOTRI manual-based functional reconstruction final gate R1

## Status

Candidate pending exact-head CI.

## Context

The replication roadmap authorizes `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1` only after G3 and its roadmap synchronization are merged and no-drift audited. That condition is now satisfied at the G4 base `main@e7dde52b405a467b6f3f17552f40ba9891f8da98`.

G4 is the final internal claim gate. It must answer one narrow question: whether the repository has completed every recoverable manual-required internal UFOTRI mechanism and reconciliation that can be supported by the available KfK 4605 manual and repository evidence.

It must not broaden that question into real CTEAS-Atmos integration, calibration, production parameter activation, empirical validation, optional model extensions, or original-executable equivalence.

## Decision

G4 is qualification-only. No production source file, default, workflow, or roadmap file is changed in the candidate.

The machine gate performs four independent checks:

1. It audits the 19 required A–G3 internal stages recorded by the master roadmap. For each stage it requires `Status: COMPLETE`, a recorded no-drift result, an actual certified-head commit and merge commit in Git history, the certified head as a merge parent, the merge commit as an ancestor of the candidate, and exact equality between the certified-head tree and merge tree.
2. It re-executes the merged G3 aggregate machine gate. G3 in turn re-executes the selected RC1/end-to-end, OBT, hydrology, HT/HTO provenance, re-emission, Canada and ITER qualification gates.
3. It verifies the complete 30-entry gap disposition: 20 `COMPLETE_INTERNAL`, one `RECONCILED_EXISTING_OPTION`, three `COMPLETE_WITH_SOURCE_LIMIT`, four `DEFERRED_EXTERNAL_DEPENDENCY`, and two `BLOCKED_SOURCE_UNAVAILABLE`. This leaves no unimplemented recoverable internal gap.
4. It verifies the claim boundary. E4/E5 remain `DEFERRED_EXTERNAL_DEPENDENCY`; complete Eq. (44) recovery, Canada full numerical/empirical replay, ITER full atmospheric replay, empirical site validation and original UFOTRI executable/parameter-loader equivalence remain explicitly unavailable, false, or not established.

## Completion-flag rule

A passing candidate does **not** edit the roadmap or declare the final flag true before merge.

The candidate may return `PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE` and state that `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE` is eligible only after:

- exact-head Remediation CI succeeds;
- exact-head Protected Integration Gate succeeds;
- the G4 PR is merged with the certified head locked;
- post-merge parent/tree/head-to-merge/main no-drift audit succeeds; and
- a separate roadmap-status sync records the completed G4 evidence and activates the flag.

This prevents the final claim from being preempted by an unmerged candidate.

## Claim boundary after successful G4 merge/no-drift

The strongest permitted internal claim becomes:

`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`

This does not imply any of the following:

- real CTEAS-Atmos HTO binding is complete;
- real CTEAS-Atmos HT binding is complete;
- full real-Atmos UFOTRI replication is complete;
- Canada 1987 full numerical or empirical replay is complete;
- ITER full atmospheric numerical replay is complete;
- complete Eq. (44) rate recovery has been achieved;
- empirical validation, physical-accuracy validation, or production readiness has been established;
- the original UFOTRI parameter loader or hidden defaults have been recovered;
- original MUSEMET/ISOLA/UFOTRI executable numerical equivalence has been established.

`UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED` remains unchanged.

## Consequences

If the machine gate and exact-head CI pass, G4 requires no new physics implementation. If any one of the 19 stage ledgers, G3 aggregate gate, 30-gap disposition, Git no-drift evidence, or claim-boundary checks fails, the final reconstruction flag must remain false and the discrepancy must be repaired before completion.
