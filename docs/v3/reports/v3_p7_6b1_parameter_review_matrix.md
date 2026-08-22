# V3-P7.6B-1 parameter review matrix report

Status: `PASS_PARAMETER_APPLICABILITY_REVIEW`

## Artifact and schema

The canonical matrix is
`docs/v3/parameter_evidence/parameter_applicability_matrix.yaml`. It uses
schema `v1`, stage `P7.6B-1`, and contains exactly 76 sorted entries. Each
entry repeats the P7.6A evidence status, class, source type, and canonical
unit, then supplies an `ApplicabilityRecord` with:

`parameter_id`, `assessment_status`, `radionuclide`, `chemical_form`,
`pathway`, `model_component`, `environment_type`, `crop_type`,
`growth_stage`, `soil_condition`, `time_scale`, `spatial_scale`,
`source_context`, `model_equation_match`, `unit_match`,
`uncertainty_available`, `review_notes`, and `reviewer_status`.

`required_action` and `validation_candidate` are matrix-level audit fields.
The parser accepts the example-compatible `applicability` status alias only
when it agrees with `assessment_status`.

## Coverage checks

`ParameterReviewMatrix.validate_against_inventory()` requires exact ID
coverage and rejects metadata drift. The matrix was loaded against the
P7.6A registry with these results:

```text
inventory_records = 76
review_records = 76
missing_records = 0
extra_records = 0
duplicate_records = 0
metadata_mismatches = 0
```

All records are `INTERNAL_REVIEWED` as a control-plane review status. This
does not represent independent external scientific review or validation.

## Disposition policy

`UNKNOWN` is a deliberate fail-closed value when the source context is
`UNRESOLVED_SOURCE_REQUIRED`; it is not silently converted to
`TRANSFER_REQUIRED` or `PARTIAL_MATCH`. Scenario inputs, numerical controls,
and test-only fixtures are `NOT_APPLICABLE` to a literature-to-model
parameter transfer. Their values remain owned by their scenario/test
contracts.

No matrix row contains a validation candidate. The matrix therefore records
the complete reviewed universe while leaving candidate admission to the
separate gate.
