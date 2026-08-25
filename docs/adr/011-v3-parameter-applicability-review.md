# ADR-011: V3 parameter applicability review and validation-candidate gate

Status: Accepted for the P7.6B-1 control-plane boundary

## Context

P7.6A freezes evidence and provenance records, but a source identifier alone
does not establish that a reported parameter applies to a V3 equation,
radionuclide form, crop, soil condition, time scale, or spatial scale. A
separate review layer is required before a later validation protocol can
consider a parameter. The review must remain independent of the V3 physics
and P7.5/P7.5B runtime path.

## Decision

P7.6B-1 adds `ApplicabilityRecord` under
`src/cteas_ufotri/parameters_v3/applicability.py`. Each record is immutable
and carries the complete review coordinates:

- parameter identity and one of `DIRECT_MATCH`, `PARTIAL_MATCH`,
  `TRANSFER_REQUIRED`, `NOT_APPLICABLE`, or `UNKNOWN`;
- radionuclide, chemical form, pathway, model component, environment, crop,
  growth stage, soil condition, time scale, and spatial scale;
- source context, equation-match disposition, unit-match disposition, and an
  explicit uncertainty-availability flag;
- review notes and the P7.6A reviewer-status vocabulary.

`ParameterReviewMatrix` is a deterministic, sorted, one-to-one matrix against
the 76-record P7.6A inventory. It rejects missing, extra, duplicate, or
metadata-inconsistent records. The canonical artifact is
`docs/v3/parameter_evidence/parameter_applicability_matrix.yaml`.

## Applicability dispositions

`DIRECT_MATCH` means that the evidence context and V3 equation/scenario match
directly. `PARTIAL_MATCH` means that the mechanism is related but one or more
conditions remain incomplete. `TRANSFER_REQUIRED` records a required scaling
or assumption. `NOT_APPLICABLE` is used for scenario inputs, numerical
controls, and synthetic test fixtures that are not literature-derived model
parameters. `UNKNOWN` is used when the P7.6A source context is unresolved.

The current matrix contains 26 `UNKNOWN` model/evidence records and 50
`NOT_APPLICABLE` records. It contains no direct, partial, or transfer
disposition because the current P7.6A production records do not have a
resolved external source context. This is a fail-closed review result, not a
claim that the underlying mechanisms are impossible.

## Validation-candidate gate

`validation_gate.py` identifies, without modifying records, only a
non-test-only record with `EVIDENCE_FOUND` and either:

1. `DIRECT_MATCH` plus direct equation and unit matches; or
2. `PARTIAL_MATCH` plus direct unit match, compatible equation match, and
   `uncertainty_available: true`.

`UNKNOWN`, `TRANSFER_REQUIRED`, and `NOT_APPLICABLE` records are blocked.
`TEST_ONLY` evidence is never a physical validation candidate. The gate only
produces an auditable candidate ID set for P7.6B-2 design; it cannot validate,
calibrate, activate, or provide a runtime lookup.

## Consequences

P7.6B-1 closes with `VALIDATION_CANDIDATES_IDENTIFIED = TRUE` and a candidate
count of zero. This explicitly identifies the complete candidate universe and
its blocking reasons without importing values. Calibration remains unstarted,
the UFOTRI database remains inactive, and P6/P7 physics plus P7.5/P7.5B
numerical coupling remain unchanged.

P7.6B-2 may define a validation protocol only after source acquisition and
applicability review resolve the relevant records. It must not treat
`EVIDENCE_FOUND` test fixtures as physical evidence.
