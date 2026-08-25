# V3 Repository Audit Remediation

Date: 2026-08-25

Branch: `codex/v3-repository-audit-remediation`

Base: `codex/v3-p7-8b2-physics-selection` at
`5ba891ec5e2d24cffdfe197afcf9006d2e4c5280`

## Scope

This branch remediates repository-governance and verification defects found by
an independent read-only audit of the post-2026-08-20 Codex development
history. It intentionally does not change V3 physics equations, P7.5/P7.5B
operator-split semantics, solver state equations, runtime parameter values, or
parameter activation.

```text
CORE_RUNTIME_CHANGED = FALSE
PHYSICS_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

## Closed finding: P7.6C-1 provenance revision/path mismatch

`docs/v3/parameter_evidence/physical_constant_validation_registry.yaml`
previously identified its own records with revision `25195cf...`, although the
registry file did not exist at that revision. The file was created by P7.6C-1
commit `2d6a0d1174795980406355055c4855df46ba583f`.

All three in-file provenance records now point to the creation revision
`2d6a0d1174795980406355055c4855df46ba583f`. The validated half-life value,
uncertainty, evidence lineage, validation decision, and `ACTIVE_PARAMETERS = 0`
were not changed.

An evergreen architecture test now verifies each registry `revision:file`
object with `git cat-file -e` so this class of provenance error fails closed.

## Closed finding: historical stage tests evaluated descendants as stage scope

Several architecture and governance tests used a historical `BASE_SHA` but
compared it to the current `HEAD`. Those tests were valid only on the original
stage branch. Later legitimate source or documentation additions therefore
appeared as false stage-scope violations.

Historical scope tests now freeze an immutable interval:

```text
BASE_SHA -> STAGE_TIP_SHA
```

rather than:

```text
BASE_SHA -> current HEAD
```

The remediation covers the P6 leaf-resistance, TFWT, plant pathway, OBT, soil,
root, food, intake, and dose boundaries; P7 Atmos and pipeline boundaries;
P7.6A applicability/candidate/evidence gates; P7.6C-3/P7.6D boundaries; P7.7A;
and P7.8A/B-1/B-2 isolation tests.

The parameter-control-plane subprocess tests also use `sys.executable` instead
of a repository-local `.venv/bin/python`, removing a host-specific test
assumption.

Historical stage tests are retained because they still prove what changed at
the original stage. Current protection is supplied separately by evergreen
invariant tests.

## Closed finding: missing top-level coupled activity conservation regression

The P7.7B end-to-end benchmark checked subsystem ledger residuals. Those checks
prove local ledger arithmetic but, by themselves, do not prove a composite
activity balance across the coupled Soil -> Root -> TFWT -> OBT pathway.

`tests/integration/test_v3_pipeline_composite_conservation.py` adds a separate
regression without changing `V3PipelineRunner`.

The physical storage boundary is:

```text
M_physical = M_soil + M_TFWT + M_OBT
```

Food, intake, and dose remain endpoint/readout products in the current V3
contract and are not added as duplicate physical stores.

For each timestep, the external net activity is defined from the existing
ledger as:

```text
+ soil deposition
+ soil signed transport input
- soil signed transport loss
+ signed leaf exchange
- soil radioactive decay
- TFWT explicit water loss
- TFWT explicit transformation loss
- OBT turnover/other loss
```

Root uptake and TFWT-to-OBT formation are internal transfers and cancel from
the composite boundary. The new regression checks both every-step residual and
cumulative trajectory residual while requiring non-zero root and OBT transfer
to exercise those cancellation paths.

This remediation does not redefine P7.5B ordering or add a new production
ledger field.

## Closed finding: Codex branch ambiguity

`docs/v3/governance/codex_branch_disposition.yaml` classifies every Codex branch
present at this remediation point into one of four non-overlapping classes:

- `CURRENT_CANDIDATE_LINE`;
- `CURRENT_RUNTIME_SOURCE_CHECKPOINT`;
- `SUPERSEDED_ARCHITECTURE_DO_NOT_MERGE`;
- `HISTORICAL_MAIN_ANCESTOR_OR_EVIDENCE_LINE`.

The older V3 line containing the alternate `leaf_exchange`, `soil`,
`food_chain`, `dose`, and `parameters` packages is explicitly `DO_NOT_MERGE`.
The typed P6/P7 implementation checkpoints are retained for provenance/bisect
only because their runtime was replayed into `codex/v3-integration-review`.
Future development continues only from the reviewed current candidate line.

## Frozen current capability boundaries

Two limitations identified by the audit remain deliberate properties of the
current frozen baseline and are now covered by evergreen tests.

### Integrated soil transport

`SoilStorageSolver` supports an explicit signed transport flux, but the current
`AtmosphericHTOForcing.to_soil_forcing()` adapter used by
`V3PipelineRunner` supplies deposition only. Therefore integrated pipeline soil
transport is currently zero unless a future explicitly reviewed interface is
added.

This is not a claim that soil transport is physically zero. It is a statement
of current integrated software capability.

### Biological forcing

`PlantBiologicalForcing` is currently carried in `V3PipelineParameters` and is
therefore runner-static across repeated `advance()` calls. The frozen baseline
must not be described as supporting time-varying day/night, temperature,
photosynthetic-activity, or growth-stage forcing through the pipeline.

The selected V4 OBT/stomatal work remains responsible for any future dynamic
forcing contract.

## Open P2 finding: historical synthetic SHA-256 sentinels

P7.7A/P7.7B historical synthetic fixtures contain values such as repeated
`a`, `b`, or `e` characters in fields named `artifact_sha256`. They satisfy the
schema's 64-hex-character shape requirement but are not demonstrated
content-authenticated artifact digests.

This remediation does **not** replace those strings with invented hashes.
Without a frozen definition of the exact historical source artifact bytes or
canonical subdocument, generating a new arbitrary SHA-256 would create false
provenance rather than repair it.

Disposition:

```text
HISTORICAL_SYNTHETIC_HASH_STATUS = UNAUTHENTICATED_TEST_SENTINEL
PHYSICAL_EVIDENCE_STATUS = NOT_EVIDENCE
RUNTIME_RISK = NONE
PROVENANCE_GRADE_ARCHIVAL = BLOCKED_PENDING_REAL_CONTENT_DIGESTS
```

New remediation test fixtures use real SHA-256 digests of their explicitly
declared synthetic labels. Before P7.7 synthetic artifacts are promoted to
provenance-grade archival evidence, a separate migration must define the
canonical bytes/subdocument for each fixture, compute the real content digest,
regenerate the checked-in result registry, and preserve the old sentinel values
in migration history.

## CI added for this branch

The repository previously had no GitHub Actions workflow. This branch adds
`.github/workflows/v3-remediation-ci.yml` with Python 3.12 and full git history.
It runs:

- remediation whitespace diff check;
- repaired historical boundary/governance tests;
- P7.8A/B-1/B-2 governance tests;
- current evergreen invariants;
- composite pipeline conservation regression;
- P7.7B synthetic benchmark tests.

External SB1/SB4/ERA5/private-reblinding datasets are not part of this focused
workflow.

## Main-branch policy

This remediation does not merge or modify `main`. A later integration review
should require the focused remediation CI to pass and should separately decide
whether to enable branch protection / required status checks before the current
candidate enters `main`.

## Exit state

The intended remediation exit state is:

```text
REMEDIATION_BRANCH = codex/v3-repository-audit-remediation
CORE_RUNTIME_CHANGED = FALSE
PHYSICS_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
VALIDATED_PARAMETER_PROVENANCE = REPRODUCIBLE
HISTORICAL_STAGE_TEST_SEMANTICS = FROZEN_TO_STAGE_TIPS
EVERGREEN_GOVERNANCE = ADDED
COMPOSITE_ACTIVITY_CONSERVATION_REGRESSION = ADDED
BRANCH_DISPOSITION = FROZEN
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
MAIN_MERGE = NOT_PERFORMED
```

A CI PASS is required before changing `REMEDIATION_STATUS` from implementation
complete to verification complete.
