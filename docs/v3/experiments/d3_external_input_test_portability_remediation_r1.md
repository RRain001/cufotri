# D3 external-input test portability remediation R1

## Status

```text
D3_PORTABLE_CLEAN_WORKTREE_TESTS = PASS_WITH_DOCUMENTED_EXTERNAL_INPUT_SKIPS
D3_STRICT_EXTERNAL_INPUT_TESTS = BLOCKED_MISSING_SB1_SB4_INPUTS
D3_LOCAL_FULL_RECOMPUTE_WITH_EXTERNAL_INPUTS = HISTORICAL_PASS_NOT_REPRODUCED_IN_THIS_WORKTREE
D3_PORTABLE_ERA5_RECOMPUTE = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT
D3_UFOTRI_MANUAL_DATA_MAPPING_REMEDIATION_R1 = READY_FOR_INDEPENDENT_REREVIEW
```

This remediation is isolated on
`codex/v3-external-input-test-portability-r1`, based on R1 snapshot
`29f59c83cb2ed6b8c4111799a3e3878c8b568b72`. It does not provide, reconstruct,
download, copy, or synthesize missing SB1/SB4/ERA5 data and does not change
model physics, configurations, thresholds, timing, replicate counts, trusted
registry state, or the V3 physics gate.

## 1. Unmodified baseline

The baseline was run before portability changes in the clean worktree:

```text
pytest --collect-only -q = 700 collected
pytest -q = 669 passed, 1 skipped, 24 failed, 6 errors; exit 1
```

The local ignored inventory is
`validation/external_local/external_input_portability_r1/baseline_failure_inventory.yaml`;
it is not tracked. Every failure/error resolved to missing files under
`validation/external_local`; no `REAL_TEST_OR_CODE_FAILURE` was found.

The 24 failures were 7 SB1 independent-review tests, 10 SB4
independent-review tests, 2 public SB1 tests, and 5 public SB4 tests. The 6
setup errors were SB4 independent recomputation/ledger tests. The missing
inputs were classified only as `MISSING_SB1_EXTERNAL_INPUT` or
`MISSING_SB4_EXTERNAL_INPUT`.

## 2. Declared input contract

The source of truth is
`validation/external_input_requirements.py`. Resolution order is:

1. An explicitly supplied `CTEAS_EXTERNAL_EVIDENCE_ROOT` or
   `CTEAS_ERA5_INPUT_ROOT`.
2. The current worktree's documented ignored location.

The resolver does not search other worktrees, the home directory, caches, or
the network. It reports `AVAILABLE`, `MISSING`, `INCOMPLETE`, or `INVALID` and
reports every missing declared file. A dataset that exists but is incomplete
or has a path of the wrong type is never converted into a portable skip.

The required SB1 paths are:

```text
emras_soybean_sb1/references/IAEA-emras-tritium-wg.pdf
emras_soybean_sb1/generated_forcing/sb1_chamber_profiles.csv
emras_soybean_sb1/generated_forcing/sb1_chamber_profile_summary.json
emras_soybean_sb1/generated_forcing/sb1_forcing_primary.csv
emras_soybean_sb1/outputs/calibration_grid.csv
emras_soybean_sb1/era5_raw/{CENTRE,NORTH_0P25,SOUTH_0P25,EAST_0P25,WEST_0P25}/era5_surface_2001-05-20_2001-10-06.nc
emras_soybean_sb1/era5_processed/{CENTRE,NORTH_0P25,SOUTH_0P25,EAST_0P25,WEST_0P25}/era5_surface_2001-05-20_2001-10-06.nc
emras_soybean_sb1/era5_processed/{CENTRE,NORTH_0P25,SOUTH_0P25,EAST_0P25,WEST_0P25}/era5_hourly_processed.csv
```

The SB1 contract expands to 20 files. The SB4 contract expands to 32 files:
the SB1 PDF, the five SB1 raw NetCDF files, the ten SB1 processed files, the
SB4 chamber profile and manifest, and these 14 forcing files:

```text
emras_soybean_sb4/generated_forcing/sb4_chamber_profiles.csv
emras_soybean_sb4/generated_forcing/sb4_forcing_manifest.json
emras_soybean_sb4/generated_forcing/sb4_constant_reported_mean_run_{01..07}.csv
emras_soybean_sb4/generated_forcing/sb4_scaled_sb1_observed_shape_run_{01..07}.csv
```

The ERA5 acceptance contract is exactly:

```text
data/era5/era5_surface_2025-06-01_2025-06-02.csv
```

The private D3 reblinding contract is the two untracked files declared by the
existing protocol: `sealed_generation_secret.json` and `truth_key_v3.json`
under `validation/external_local/d3_prospective_reblind_v3/`. No private key
or secret fixture was created.

## 3. Pytest portability behavior

The following markers are registered in `pyproject.toml` and
`tests/conftest.py`:

```text
external_sb1_data
external_sb4_data
external_era5_data
private_reblinding_secret
```

Only direct external readers or tests whose declared external-derived artifact
is required are marked. Public schema, manifest, contract, mapping, gate,
threshold, and synthetic-contract tests remain unmarked and continue to run.

Default portable mode:

```text
missing SB1       -> SKIP_EXTERNAL_SB1_INPUT_NOT_AVAILABLE
missing SB4       -> SKIP_EXTERNAL_SB4_INPUT_NOT_AVAILABLE
missing ERA5      -> SKIP_EXTERNAL_ERA5_INPUT_NOT_AVAILABLE
missing secret    -> SKIP_PRIVATE_SECRET_NOT_AVAILABLE
incomplete/invalid input -> explicit test error, not skip
```

Strict mode is enabled with `--require-external-inputs`. Missing required input
then produces a non-zero pytest result with `DATASET`, `STATUS`,
`MISSING_FILES`, and `INVALID_FILES`; original assertions and numerical
thresholds are unchanged when inputs are available.

## 4. Verifier behavior

With the required ERA5 file absent, each verifier returned exit code 2 and the
same machine-readable status block:

```text
STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT
DATASET = ERA5_ACCEPTANCE
MISSING_FILES = [.../data/era5/era5_surface_2025-06-01_2025-06-02.csv]
```

Verified commands:

```text
scripts/verify_acceptance.py --recompute              exit 2
scripts/verify_v2_acceptance.py --recompute           exit 2
scripts/verify_v3_compatibility.py                    exit 2
scripts/verify_v3_architecture_readiness.py           exit 2
```

The verifier logic and thresholds are unchanged when the input is present. The
external-evidence unblocking verifier remains
`READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA`; its local intake remains
`READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA`, and the physics start gate remains
`BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA`.

## 5. Verification results

```text
pytest --collect-only -q                                      = 711 collected
pytest -q --disable-warnings                                  = 660 passed, 51 skipped; exit 0
pytest -q --disable-warnings -m "public-only expression"      = 660 passed, 1 skipped; exit 0
pytest -q --require-external-inputs -m "SB1 or SB4 or ERA5"  = 49 explicit missing-input errors; exit 1
tests/external_evidence_acquisition                         = 59 passed; exit 0
tests/prospective_experiment                                = 33 passed; exit 0
tests/true_reblinding                                       = 26 passed, 1 private skip; exit 0
compileall src tests era5 scripts validation                 = exit 0
git diff --check                                            = exit 0
```

The 51 portable skips comprise 50 declared external-input marker items and
the existing independent-review private-secret skip. The strict run excludes
the private marker and therefore checks 49 SB1/SB4/ERA5 items.

## 6. Protected boundary and review state

The diff from the R1 snapshot has no changes under `src/`, `configs/`, the
SB1 frozen mechanism reports, the SB4 protocol/thresholds, the trusted
external-evidence registry, raw data, ERA5 files, or private secret paths.
The ignored baseline inventory is local only and is not staged. No V3 tag was
created. No independent rereview has been performed in this session; the
branch is ready for an independent fresh-worktree review.
