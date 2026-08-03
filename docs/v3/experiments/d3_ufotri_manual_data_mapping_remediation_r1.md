# D3 UFOTRI manual data mapping remediation R1

This report records the fail-closed remediation self-check after the failed
independent review. It does not replace the failed review report and it does
not constitute the independent re-review required before integration.

```text
REMEDIATION_BASE = fb1c3a20994fc17d2579058ff968c05d561f0a2a
REVIEW_TARGET = b88a251f08069329d53290ccf7510080199f0561
BASE_MAIN = f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a
REMEDIATION_BRANCH = codex/v3-d3-ufotri-manual-data-mapping-remediation-r1
FAILED_REVIEW_REPORT = docs/v3/experiments/d3_ufotri_manual_data_mapping_independent_review.md
```

## Scope and preserved boundary

The remediation starts from the failed review commit, so the original
`FAIL_TARGET_NOT_REPRODUCIBLE`, `FAIL_SOURCE_ANCHOR_DEFECT` and
`FAIL_TEMPLATE_INCONSISTENCY` report remains in history. This worktree changes
only the D3 mapping/contract documentation, terminology clarifications and
tests needed to make the stated boundary executable.

No `ufotri_manual.md`, `src/`, formal root-level `configs/`, H2/H3 parameters,
classifier thresholds, primary sampling times, replicate allocation,
synthetic data, trusted registry or V3 tag was changed. No source/main merge
or independent re-review was performed.

## Mapping corrections

The three reported source-anchor defects were corrected without changing the
field count or category semantics:

| field | before | after | reason |
|---|---|---|---|
| `release_rate` | `5.2.2 Table 3; 5.3 Appendix B §1` | `5.2.2 Table 3` | Appendix B §1 does not provide release rate |
| `soil_layer_depths` | `2.2.4; 2.2.5; 3.3.3 Figure 13` | `2.2.3; 2.2.4; 2.2.5` | Figure 13 is the Vegetables flowchart, not soil-layer evidence |
| `root_hto_uptake_flux` | `2.2.4; 2.2.5; Equation (37)` | `2.2.3; Equation (37); 2.2.5` | Equation (37) is in §2.2.3 |

The independent recomputation remains 100 fields with non-exclusive category
counts `36/10/34/17/7/3` and category sum 107.

## Unresolved-field contract

`validation/external_evidence_acquisition/d3/requested_file_contract.yaml`
now contains a top-level `unresolved_items` list with exactly the three
mapping fields. Each entry is `UNRESOLVED_NO_SOURCE`,
`DEFER_UNRESOLVED`, `defer_unresolved`, optional, and has `default: null`.
Model, acceptance and trusted-registry use are all false. A future laboratory
definition or an approved alternative is allowed only with explicit approval.
No unresolved value becomes a project default or an acceptance input.

## Terminology and replicate boundary

Historical occurrences of unqualified `5270 Bq/mL water` were retained as
historical text and given adjacent clarification: the intended basis is
`5270 Bq/mL air-moisture water` in `HTO_IN_CHAMBER_AIR_MOISTURE`, not liquid
culture, irrigation or reservoir water. The derived-data changelog retains
its earlier wording because it explicitly records that clarification.

The current D3 operational design remains five independent biological
replicates per primary time point. Three is only the minimum uncensored count
for a preregistered limited-deviation analysis; it is not the recommended
design, does not reduce the allocated plant count, and does not automatically
inherit the evidence grade of the planned design. The historical H2/H3
sentence mentioning three was not rewritten; its boundary is stated adjacent
to it.

## True-reblinding test split

The public integrity test checks the ignored/untracked private path, absence of
the secret from the commit tree, the tracked SHA-256 commitment, manifest
commitment consistency and the one-generation/one-classification chronology.
It does not require reading a private file. The private test verifies the
secret hash only when the local private secret is present and otherwise emits
the explicit skip `SKIP_PRIVATE_SECRET_NOT_AVAILABLE`.

In this clean worktree `validation/external_local/` contains only its tracked
README and `.gitignore`; no secret fixture was copied or generated.

## Verification evidence

| check | result |
|---|---|
| mapping + R1 remediation tests | 28 passed |
| `tests/external_evidence_acquisition` | 48 passed |
| `tests/prospective_experiment` | 33 passed |
| `tests/independent_review_d3_true_reblinding` | 26 passed, 1 skipped |
| D3 scoped combined run | 107 passed, 1 skipped; exit 0 |
| repository collection | 700 collected; exit 0 |
| repository full pytest | 24 failed, 6 errors from missing ignored SB1/SB4 external-local inputs; no PASS claim |
| compileall | pass with `PYTHONPYCACHEPREFIX` directed to a temporary path |
| `git diff --check` | pass |
| protected `src/`, `configs/`, trusted registry diffs | empty |
| V3 tags at this target | none |

The repository-wide failures are outside this D3 remediation scope. They
include missing SB1 PDF/forcing and SB4 generated forcing under
`validation/external_local/`; no raw or generated external input was copied to
make the suite appear green. Because the R1 plan treats any repository-wide
failure as a stop condition, this prevents the overall remediation from being
marked ready even though the D3-scoped self-check passes. No out-of-scope
SB1/SB4 test changes were made to hide the missing external inputs.

## Acceptance and portability status

The verifier outcomes were recorded individually:

```text
scripts/verify_acceptance.py --recompute = FAIL_MISSING_REQUIRED_EXTERNAL_ERA5_INPUT
scripts/verify_v2_acceptance.py --recompute = FAIL_MISSING_REQUIRED_EXTERNAL_ERA5_INPUT
scripts/verify_v2_validation_readiness.py = PASS
scripts/verify_v3_compatibility.py = FAIL_MISSING_REQUIRED_EXTERNAL_ERA5_INPUT
scripts/verify_v3_architecture_readiness.py = FAIL_MISSING_REQUIRED_EXTERNAL_ERA5_INPUT
scripts/verify_v3_external_evidence_unblocking.py = READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
scripts/verify_v3_physics_start_gate.py = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

The required ERA5 path is
`data/era5/era5_surface_2025-06-01_2025-06-02.csv`. In both this worktree and
a temporary clean `BASE_MAIN` probe at `f5d1888`, it is absent, untracked and
matched by `.gitignore:20:/data/`. The BASE_MAIN probe was removed after the
read-only comparison. No ERA5 value was reconstructed or added.

```text
LOCAL_FULL_RECOMPUTE_WITH_EXTERNAL_INPUTS = HISTORICAL_PASS_NOT_REPRODUCED_IN_THIS_CLEAN_WORKTREE
PORTABLE_CLEAN_WORKTREE_RECOMPUTE = BLOCKED_MISSING_EXTERNAL_ERA5_INPUT
```

These are input-availability statuses, not claims of a numerical physics
failure. The external-evidence and V3 physics gates remain fail-closed.

## Final status

```text
D3_UFOTRI_MANUAL_DATA_MAPPING_REMEDIATION_R1 = HOLD_UNRESOLVED
D3_SCOPED_REMEDIATION_SELF_CHECK = PASS_SELF_CHECK
MANUAL_EXPLICIT_ANCHORS = PASS_36_OF_36
MANUAL_DERIVED_ANCHORS = PASS_10_OF_10
UNRESOLVED_CONTRACT_LINKAGE = PASS_3_OF_3
CROSS_DOCUMENT_TERMINOLOGY = PASS
REPLICATE_SEMANTICS = PASS_PLANNED_5_LIMITED_MINIMUM_3
PUBLIC_TRUE_REBLINDING_INTEGRITY = PASS
PRIVATE_SECRET_AUDIT = SKIP_PRIVATE_SECRET_NOT_AVAILABLE
PORTABLE_RECOMPUTE_STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_ERA5_INPUT
MODEL_OR_PARAMETER_CHANGE = NONE
INDEPENDENT_REREVIEW = NOT_STARTED
MERGE_RECOMMENDATION = DO_NOT_MERGE
```

The next action requires the missing external-local benchmark inputs to become
available, or an explicitly authorized change to the out-of-scope SB1/SB4
test boundary. This remediation session stops before creating or running an
independent re-review.
