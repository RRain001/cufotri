# V3-P7.6A parameter evidence and provenance report

Status: `PASS_PARAMETER_EVIDENCE_PROVENANCE_FROZEN`

`ParameterEvidenceRecord` is an immutable record with explicit fields for
identity, subsystem, primary class, symbol, description, canonical unit,
lifecycle status, source type and identifier, original and normalized values
and units, applicability, evidence notes, provenance, and review status.

The unit policy is deliberately non-converting:

- `reported_value`/`reported_unit` preserve the source representation;
- `normalized_value`/`normalized_unit` are separate fields;
- a normalized value is accepted only with an explicit unit equal to
  `canonical_unit`;
- the control plane never computes a normalized value or overwrites the
  reported value.

Every record has a traceability anchor consisting of repository, revision,
repository-relative file, and location. `UNRESOLVED_SOURCE_REQUIRED` is an
explicit fail-closed source marker, not a citation or evidence claim.

Supported source types are the nine types in the P7.6A contract, including
literature, standards, databases, UFOTRI documentation/source code,
project assumptions, physical-constant sources, and test-only sources. The
current manifest uses project-assumption markers for unsourced model inputs
and test-only sources for synthetic fixture values. It does not claim that
synthetic tests are physical or observational evidence.

Applicability is represented independently for radionuclide, chemical form,
crop, growth stage, soil type, environment, pathway, and age group. Unknown
dimensions remain `APPLICABILITY_UNRESOLVED`; no applicability is inferred
from a parameter name or unit.

The implementation is isolated to `src/cteas_ufotri/parameters_v3/`. It is a
control-plane package and is not imported by P6/P7 solvers or the P7.5
pipeline.
