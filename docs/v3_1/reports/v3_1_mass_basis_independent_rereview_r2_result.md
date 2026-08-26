# V3.1 Mass-Basis Contract — Independent Rereview R2 Result

## Verdict

```ini
STATUS = PASS_INDEPENDENT_REREVIEW
REVIEWED_SHA = 95f78801d0fa3b507e6bd76249b192adf8b107cb
REVIEWER = codex-local-gpt-5.6-luna
REVIEW_ID = LOCAL_CODEX_GPT56LUNA_V3_1_REREVIEW_R2
REVIEW_DATE = 2026-08-26
BLOCKING_FINDINGS = 0
PRIOR_R1_VERDICT = HOLD_REMEDIATION_REQUIRED (preserved, not rewritten)
```

This reviewer did not participate in the R1 remediation implementation and did
not trust any pre-existing PASS claim: every gate below was re-derived from the
frozen code in a fresh detached worktree at `95f78801d0fa3b507e6bd76249b192adf8b107cb`
(`/private/tmp/cteas_ufotri_mass_basis_rereview_r2`), plus a reviewer-owned
adversarial probe script executed against that worktree from outside the
repository.

## Reviewer independence

- The R2 reviewer is not an author of any commit on
  `codex/v3-1-mass-basis-contract` between `d24aa03b00dcb586a2d93e678f42cb7853b7c078`
  and `95f78801d0fa3b507e6bd76249b192adf8b107cb`.
- All probes were written by the reviewer in this session; existing V3.1 tests
  were additionally re-run but never used as the sole evidence for any gate.
- The implementation branch was not modified; review artifacts live only on
  `codex/v3-1-mass-basis-independent-rereview-r2`.

## Environment

```text
Python 3.14.6 (venv of the main repository checkout)
macOS 26.4, arm64
pytest 9.1.1 / jsonschema 4.26.0
CI comparison environment: Python 3.12 on ubuntu-latest (per workflow)
```

## Gate-by-gate results

### A. PRIOR_BLOCKER_WHITESPACE_SCHEMA_PARITY — PASS

Reviewer-owned probes attacked every `_require_text()`-guarded serialized field
(`subject_id`, `tissue_scope.identifier` for leaf and custom kinds,
`area_basis.identifier` for ground_area and custom kinds,
`provenance.source_id`, `provenance.source_locator`, `provenance.revision`,
`provenance.note`, `conversion_evidence_id`) with `" "`, `"   "`, `"\t"`,
`"\n"`, `" \t\n "` (and empty string where constructible). For each attack:

- Python raised `BasisContractError`;
- the equivalent serialized payload was rejected by `jsonschema` against
  `schemas/v3_1/mass_basis_contract.schema.json` (`minLength: 1` plus `.*\S.*`
  pattern, and the `evidence_declared` conditional forcing a non-blank string
  id or strict null).

Additional fail-closed checks: custom scope/area without identifier rejected by
both sides; `conversion_evidence_id` present while status is not
`evidence_declared` rejected by both sides; declared status with missing id
rejected by both sides. No parity gap found.

### B. NO_NUMERICAL_BASIS_CONVERSION — CONFIRMED ABSENT

- Repo-wide `src` search: no `conversion_factor`, `water_fraction`,
  `moisture_fraction`, `dry_matter_fraction`, `hydrogen_fraction`,
  `composition_factor`; no scale/ratio logic in the V3.1 package.
- The only `multiplier` hits are pre-existing OBT day/night formation-rate
  parameters (`plant/obt.py`, `plant/obt_v3/*`) that are blob-identical to the
  baseline (see gate J) and unrelated to mass-basis conversion.
- AST analysis of `contract.py`: no arithmetic operations outside PEP 604 type
  annotations, no numeric unary ops, no `float()/int()/round()/sum()` calls.
  The module performs metadata validation only.
- `BasisConversionEvidence.__post_init__` rejects `source_basis is
  target_basis`, so a same-basis conversion record cannot even be constructed;
  fresh↔dry, fresh↔water, dry↔water, hydrogen↔mass relations carry no numbers
  anywhere in V3.1.

### C. EXPLICIT_SOURCE_TARGET_PAIRING — PASS

`PairedMeasurement` declares required `pair_id`, `source_measurement_id`,
`target_measurement_id` with no defaults (verified by dataclass field
inspection and positional construction). Evidence requires at least one such
pair (`len(paired_measurements) < 1` raises).

### D. PAIR_REUSE_FAIL_CLOSED — PASS

All attacks rejected inside one `BasisConversionEvidence`:

| Attack | Result |
| --- | --- |
| `source == target` within one pair | rejected |
| duplicate `pair_id` across pairs | rejected |
| same measurement reused as source twice | rejected |
| same measurement reused as target twice | rejected |
| source of pair 1 reused as target of pair 2 | rejected |
| target of pair 1 reused as source of pair 2 | rejected |
| reversed duplicate content `(a,b),(b,a)` | rejected |
| legitimate two-pair evidence `(a,b),(c,d)` | constructs |

The global measurement-id set check makes all reuse variants impossible, not
just symmetric ones.

### E. EVIDENCE_TISSUE_SCOPE_BINDING — PASS

For cross-basis proposals, `validate_conversion_proposal` enforces source/target
scope agreement first, then `evidence.tissue_scope != source.tissue_scope`.
Probes: kind mismatch (leaf vs root) raises; custom-kind with differing
identifier raises; matching custom identifier passes to `EVIDENCE_DECLARED`.

### F. EVIDENCE_AREA_BASIS_BINDING — PASS

Same mechanism for `area_basis`. Probes: `ground_area` vs `leaf_area` raises;
custom plot identifiers `plot-1` vs `plot-2` raise.

### G. CROSS_BASIS_EVIDENCE_ID_BINDING — PASS

On a valid fresh→dry proposal:

- missing evidence (`None`) → fail closed ("cross-basis conversion blocked");
- source declares conflicting `conversion_evidence_id` → raise;
- target declares conflicting id → raise;
- source/target declaring different ids → raise;
- both declaring the matching id → returns `EVIDENCE_DECLARED`;
- swapped-direction evidence (dry→fresh) → raise ("source basis");
- wrong-side basis evidence (water→dry, fresh→hydrogen) → raise.

### H. SAME_BASIS_EVIDENCE_STATE_BYPASS — PASS (R1 core blocker remediated)

All six scenarios independently reproduced at the frozen SHA:

1. same basis + no evidence + no declaration → `IDENTITY_ONLY`;
2. same basis + source `EVIDENCE_DECLARED` → reject;
3. same basis + target `EVIDENCE_DECLARED` → reject;
4. same basis + supplied legal cross-basis `BasisConversionEvidence` → reject;
5. same basis + declared state + supplied matching evidence → still reject;
6. `require_direct_comparison` continues to admit true direct comparison on
   mass/tissue/area equality, rejects any mismatch, and does not consume or be
   blocked by unrelated declared evidence metadata.

Structural confirmation: `validate_conversion_proposal` contains exactly two
`return` statements; `_require_same_scope`, the supplied-evidence guard, and
the declared-state guard all execute before the identity return. The R1
early-return bypass is gone.

### I. PYTHON_SCHEMA_BOUNDARY — PASS

Programmatic comparison verified: enum value lists identical for `MassBasis`,
`TissueScopeKind`, `AreaBasisKind`, `ConversionStatus`; eight required top-level
fields; nullability semantics for `tissue_scope.identifier`,
`area_basis.identifier`, `provenance.note`, `conversion_evidence_id`;
`additionalProperties: false` at the root and every nested object; `version`
const `v3.1-mass-basis-v1`; whitespace pattern parity on every text field.

Persistence boundary: `schemas/v3_1/` contains only
`mass_basis_contract.schema.json`. Neither the schema nor
`docs/v3_1/contracts/mass_basis_contract.yaml` claims persisted-schema status
for `PairedMeasurement` or `BasisConversionEvidence` records; those remain
in-memory governance objects only.

### J. FROZEN_RUNTIME_ISOLATION — PASS

Independently verified with git plumbing, not via the isolation test:

```text
git diff --stat d24aa03..95f7880:
  13 files changed, 1778 insertions(+), 8 deletions(-)
  M .github/workflows/v3-integration-gate.yml          (CI additions only)
  M tests/architecture/test_v3_protected_integration_review.py (governance tightening)
  A docs/ADR-022, contract yaml, 2 reports, schema, mass_basis_v3_1 pkg, 4 test files
```

- Every `src/` file under v3/exposure/intake/dose/pipeline globs is
  blob-identical between baseline and target (zero CHANGED entries).
- Explicit `git rev-parse BASE:path == TARGET:path` equality reproduced for all
  eight pinned blobs (pipeline_runner, leaf resistance, TFWT, OBT, soil, root,
  food transfer, harvest_state) — matching the isolation test's pinned SHAs.
- All `p7_5/p7_7/p7_8` related files identical; `configs/`, `validation/`,
  `era5/` trees byte-identical.
- The two modified non-new files change CI test lists/import smoke and freeze a
  historical review-head assertion; neither touches runtime physics/state
  semantics.

### K. P7_8B2_SCOPE_COMPLIANCE — PASS

No V4 physics, dynamic stomata, two-pool OBT, root water-flux, soil hydrology,
TFWT turnover, hybrid food transfer, calibration, parameter activation, or
physical-validation declaration exists anywhere in the V3.1 diff. Declared and
tested flags remain:

```ini
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

`docs/v3_1/contracts/mass_basis_contract.yaml` explicitly sets
`evidence_declared_is_physical_validation: false`; `test_p7_8b2_physics_selection.py`
passes unchanged inside the explicit invariant set.

## Local verification record

| Check | Result |
| --- | --- |
| `python -m compileall -q src` | PASS |
| Import smoke (workflow script incl. `mass_basis_v3_1`, intake, dose) | PASS |
| Focused: 4 V3.1/isolation test files | 26 passed |
| Portable suite (marker-excluded) | 1000 passed, 1 skipped, 57 deselected, 1 warning |
| Explicit invariant set per `.github/workflows/v3-integration-gate.yml` | 79 passed |
| `git diff --check d24aa03...95f78801` | clean |
| Reviewer adversarial probes (A–I) | 8/8 groups passed |

## P7.7B macOS note

The R1 macOS observation (`test_checked_in_result_registry_matches_a_fresh_execution`
registry mismatch) **did not reproduce** in this R2 run:
`tests/v3/test_p7_7b_synthetic_benchmarks.py` passed both standalone inside the
portable suite and inside the explicit invariant set. Per the R2 policy this is
retained as `NONBLOCKING_CROSS_PLATFORM_TECHNICAL_DEBT` from R1; it is not
interpreted as physical-validation failure or success. The V3.1 diff contains
no change to that benchmark (blob-identical), so no causal link to V3.1 exists.

## Nonblocking notes

1. P7.7B macOS cross-platform reproducibility debt retained from R1 (see above).
2. Pre-existing NumPy/netCDF binary-compatibility `RuntimeWarning` in
   `tests/unit/test_era5_reader.py::test_netcdf_mapping` persists locally and is
   documented in the R1 remediation report.
3. Local Python 3.14.6/macOS vs CI Python 3.12/Ubuntu both produce passing
   suites; V3.1 introduces no version-specific behavior.
4. The reviewer adversarial probe script was kept outside the repository so
   only verdict artifacts are committed here.

## Exit policy

```ini
IMPLEMENTATION_PR_MERGE_READY = TRUE
MAIN_MERGE_AUTHORIZED_BY_THIS_REQUEST = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

PR #3 merge readiness is recorded; merging `main`, PR #3, and PR #6 remain
explicit human actions not authorized by this file. This PASS applies to exact
SHA `95f78801d0fa3b507e6bd76249b192adf8b107cb` only.
