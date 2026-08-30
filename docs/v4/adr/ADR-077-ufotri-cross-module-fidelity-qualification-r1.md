# ADR-077 — UFOTRI cross-module fidelity qualification R1

## Status

Candidate pending exact-head CI.

## Context

The replication roadmap authorizes `UFOTRI_CROSS_MODULE_FIDELITY_QUALIFICATION_R1` after completion of the internal A–F reconstruction phases and the G1/G2 benchmark-contract stages. Real CTEAS-Atmos HT/HTO binding remains a deferred external dependency and must not be replaced by a synthetic surrogate labeled as real validation.

G3 must qualify deterministic repeat, restart equivalence, timestep refinement, cross-module conservation, HT/HTO provenance, plant/soil/food inventory accounting, RC1-versus-fidelity distinctions, and disposition of all 30 original replication-gap entries.

## Decision

G3 is a qualification stage, not a new production-pipeline implementation.

The stage therefore reuses and re-executes the existing machine-visible numerical gates instead of creating a second orchestrator. The frozen RC1 composition remains the fallback baseline. Post-RC1 fidelity paths remain opt-in/manual-compatibility mechanisms.

The G3 machine gate additionally requalifies UFR-16. KfK 4605 Section 2.2.5 states an approximately three-hour delay between plant moisture loss and root uptake. The repository already retains the historical optional implementation in `case.py`: `root_uptake_delay_seconds` is converted to an integral queue length, the queue begins with zeros, and root uptake uses transpiration from exactly that many completed intervals earlier. `configs/advanced_test_case.yaml` selects 10800 s with a 600 s step, giving 18 intervals. G3 tests this relationship dynamically. The V4 root core continues to contain no hidden delay and continues to consume explicit upstream layer-water-flux forcing.

No new root-delay physics is therefore authorized or required.

## RC1 versus fidelity

G3 does not require RC1 and the fidelity paths to be numerically equal. Such equality would be conceptually wrong because the post-RC1 paths intentionally restore manual mechanisms absent from the frozen fallback.

The qualification records explicit differences for leaf exchange, OBT state semantics, Eq. (33)–(37) hydrology, continuous food-chain behavior, the HT branch, Eq. (4)–(6) re-emission/area-source compatibility, and the optional three-hour root-delay mode.

The comparison is a mechanism-and-boundary audit, not a calibration or ranking exercise.

## Gap disposition rule

All 30 entries from `UFOTRI_REPLICATION_GAP_AUDIT_R1` must have one of five dispositions:

- `COMPLETE_INTERNAL`;
- `RECONCILED_EXISTING_OPTION`;
- `COMPLETE_WITH_SOURCE_LIMIT`;
- `DEFERRED_EXTERNAL_DEPENDENCY`;
- `BLOCKED_SOURCE_UNAVAILABLE`.

UFR-01, UFR-03, UFR-04 and UFR-05 remain tied to real atmospheric transport/deposition/washout and are deferred to CTEAS-Atmos reconciliation. UFR-29 and UFR-30 remain blocked by unavailable original UFOTRI assets. Source-limited Eq. (44), Canada and ITER evidence is retained as source-limited rather than silently repaired.

## Consequences

G3 may pass under controlled synthetic/replay/manual-compatible forcing while real Atmos checks remain deferred. Passing G3 does not set `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`; the final G4 gate remains a separate roadmap decision after G3 merge and roadmap synchronization.

No `src/` modification, production-parameter activation, calibration, empirical-validation claim, physical-accuracy claim, real-Atmos claim, or original-executable-equivalence claim is authorized by this ADR.
