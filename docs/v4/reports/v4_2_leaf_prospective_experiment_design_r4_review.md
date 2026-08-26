# V4-2 Prospective Soybean Experiment Design R4 Review

## Decision

`READY_FOR_FEASIBILITY_REVIEW_NOT_EXECUTED`

R2 and R3A established that the reviewed public soybean datasets do not provide a
single internally aligned dynamic stomatal-response packet. R3B documented but
then closed the author-held data path without contacting authors. R4 therefore
moves to a prospective evidence design rather than lowering the packet contract or
combining incompatible datasets.

R4 is a design-control stage only. No experiment has been executed and no
empirical observations have been collected under this protocol.

## What R4 is designed to identify

The candidate leaf contract remains symbolic:

`g_s = g_s,max F_light(L) F_vpd(VPD) F_temp(T_leaf) F_stage(s)`

R4 does not choose any response-function equation or numerical coefficient. It
specifies the evidence structure needed to determine whether those dependencies
can later be estimated and validated from one soybean experiment.

The core measurement record must bind absolute stomatal conductance, PAR/PPFD,
leaf VPD, leaf temperature, time, plant identity, developmental stage and run /
condition provenance. Setpoints are not interchangeable with measured values.

## Independence and repeated measurements

The biological independent unit is the **plant**. Instrument rows are repeated
measurements nested within a plant and cannot be counted as biological
replicates. This prevents a high-frequency LI-COR trace from creating artificial
sample size.

Exact replicate counts are intentionally not frozen in R4. They require a
feasibility and precision/power review before execution. However, the final design
must contain enough independent plants to create disjoint calibration and final
validation groups.

## Driver coverage and confounding

For the full candidate to be reviewable, light, VPD and Tleaf need non-degenerate
support, and developmental stage needs more than one source-bound category. R4
requires at least three distinct support levels for each continuous driver as a
minimum structural condition for candidate-shape review and at least two stage
categories for a stage-effect review.

Those are design-support constraints, not fitted model parameters. Exact levels
remain `TBD_FEASIBILITY_REVIEW`.

The design must also avoid perfect driver confounding. For example, all high-VPD
observations cannot occur only at one temperature or in one stage. The exact
factorial, response-surface, blocked or sequential arrangement is deferred to the
feasibility review.

## Dynamic records

Time-resolved records around controlled condition transitions must be retained.
A later preregistration may define plateau or stabilization windows, but R4 does
not add a kinetic stomatal ODE and does not discard transient records at design
time.

## Holdout protection

Final validation is plant-level, not row-level. Calibration and final validation
plants must be disjoint before any parameter fit. Final validation records cannot
be used to define empirical response-domain bounds, select a response function,
tune preprocessing, or set acceptance thresholds.

If an out-of-domain challenge is later useful, it must be labeled separately from
the primary in-domain final validation set.

## Data provenance

The prospective data contract requires unchanged raw instrument files, SHA-256
before processing, explicit instrument/export metadata, a composite measurement
record key, explicit unit conversions and a derived-table manifest that points
back to raw hashes. Raw and derived artifacts cannot share identity.

Direct `VPDleaf` is preferred. If it is absent, derivation is allowed only from
complete row-aligned humidity, pressure and Tleaf inputs under a preregistered
equation. A humidity range or its midpoint cannot be broadcast across records.

## What remains before experiment execution

A separate feasibility/readiness review must freeze:

- exact driver levels or design points;
- biological replicate count and rationale;
- soybean developmental-stage categories and ontology;
- randomization/counterbalancing plan;
- stabilization or plateau extraction rule;
- instrument availability and required output fields;
- calibration/final-validation assignment rule;
- response-domain estimator;
- metric statistics and acceptance thresholds;
- missing-data and instrument-QC rules;
- the final file/schema contract.

Until those are complete, experiment execution remains HOLD.

## Frozen implementation boundary

```ini
EXPERIMENT_EXECUTED = FALSE
EMPIRICAL_PACKET_COLLECTED = FALSE
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
SOLVER_IMPLEMENTATION_STARTED = FALSE
CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE
CALIBRATION_STARTED = FALSE
ACTIVE_PARAMETERS = 0
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```
