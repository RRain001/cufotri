# D3 UFOTRI manual mapping independent rereview R1

## Review disposition

This review was performed in the fresh worktree
`/Users/rain/Documents/Doctor/Topic/CETAS_ufotri_d3_manual_mapping_independent_rereview_r1`
on branch
`codex/v3-d3-ufotri-manual-data-mapping-independent-rereview-r1`.
The audited target was the fixed portability-remediation commit
`0164a99cae30ab44411fe98be9ea9cc512c51966`, with the fixed chain
`f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a -> b88a251f08069329d53290ccf7510080199f0561 -> fb1c3a20994fc17d2579058ff968c05d561f0a2a -> 29f59c83cb2ed6b8c4111799a3e3878c8b568b72 -> 0164a99cae30ab44411fe98be9ea9cc512c51966`.

No external SB1, SB4, ERA5, raw, or private-secret input was copied or read.
SB1/SB4 tests were not executed because their authorized external inputs are
absent; ERA5 verifiers were exercised only to confirm the required blocked
status. No other worktree, home-directory, cache, network, download, model
source, configuration, threshold, H2/H3 parameter, registry, or V3 tag was
used or changed.

```text
D3_UFOTRI_MANUAL_DATA_MAPPING_INDEPENDENT_REREVIEW_R1 = PASS_TRACEABLE_PORTABLE_AND_FAIL_CLOSED
MANUAL_EXPLICIT_REVIEW = PASS_36_OF_36
MANUAL_DERIVED_REVIEW = PASS_10_OF_10
UNRESOLVED_FIELD_REVIEW = PASS_3_OF_3_DEFERRED_AND_CONTRACTED
PORTABLE_TEST_BEHAVIOR = PASS
STRICT_TEST_BEHAVIOR = PASS_FAIL_CLOSED
ERA5_VERIFIER_BEHAVIOR = PASS_BLOCKED_EXIT_2
MODEL_OR_PARAMETER_CHANGE = NONE
REAL_EXTERNAL_EVIDENCE = FALSE
FORMAL_V3_PHYSICS = NOT_STARTED
MERGE_RECOMMENDATION = READY_FOR_FAST_FORWARD_MERGE
```

## Independent baseline recomputation before adding review files

With no external-input environment variables and before adding this test or
report, the fresh worktree produced:

```text
pytest --collect-only -q                         = 711 collected
pytest -q -rs                                    = 660 passed, 51 skipped, exit 0
public marker expression collect                 = 661 collected
public marker expression run                     = 660 passed, 1 skipped, exit 0
strict SB1/SB4/ERA5 marker collect               = 49 collected
strict SB1/SB4/ERA5 run                          = 49 errors, exit 1
```

The 51 default-mode skips were independently observed as exactly:

```text
SKIP_EXTERNAL_SB1_INPUT_NOT_AVAILABLE   = 21
SKIP_EXTERNAL_SB4_INPUT_NOT_AVAILABLE   = 27
SKIP_EXTERNAL_ERA5_INPUT_NOT_AVAILABLE  = 1
SKIP_PRIVATE_SECRET_NOT_AVAILABLE       = 1
```

Every skip reported `STATUS = MISSING`; no `INCOMPLETE`, `INVALID`, parse,
fixture, marker, code, or numeric failure was converted into a skip. The
public-only marker expression was independently constructed as:

```text
not external_sb1_data and not external_sb4_data and not external_era5_data and not private_reblinding_secret
```

Public schema, published-table, mapping, request, manifest, gate, threshold,
synthetic-contract, and public true-reblinding tests were not marked as direct
external-input readers.

The exact strict command selected 49 items. Independent output inspection
found only these statuses:

```text
DATASET = SB1; STATUS = MISSING       = 21
DATASET = SB4; STATUS = MISSING       = 27
DATASET = ERA5_ACCEPTANCE; STATUS = MISSING = 1
```

No strict item reached model, numeric, fixture, or assertion logic. The
missing file lists were emitted with `MISSING_FILES` and `INVALID_FILES = []`.

## Portability and resolver audit

The resolver contract was independently inspected and exercised. Its order is
explicit environment path first, otherwise the current worktree's documented
ignored location. Its only statuses are `AVAILABLE`, `MISSING`, `INCOMPLETE`,
and `INVALID`; it checks only declared paths. Source inspection found no home
directory walk, other-worktree search, cache search, network client, or
download path.

Negative probes returned:

```text
empty root                         = MISSING
dataset directory with no files   = INCOMPLETE
dataset path replaced by a file    = INVALID
illegal explicit environment path  = MISSING, no fallback
invalid marked test                = nonzero, STATUS = INVALID, never skip
```

The original numerical assertions and comparison directions were preserved.
The diff from `29f59c83cb2ed6b8c4111799a3e3878c8b568b72` added the resolver,
marker gate, portability path plumbing, and fail-closed verifier boundary;
it did not add a broad catch-and-skip. The SB4 support criteria, frozen SB1
mechanism parameters, configurations, and trusted registry diff from
`f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a` are empty.

## ERA5 verifier audit

Each verifier was run with the required ERA5 CSV absent. Each exited 2 and
printed the same machine-readable boundary, including the target CSV:

```text
STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT
DATASET = ERA5_ACCEPTANCE
MISSING_FILES = [.../data/era5/era5_surface_2025-06-01_2025-06-02.csv]
```

Verified commands were `scripts/verify_acceptance.py --recompute`,
`scripts/verify_v2_acceptance.py --recompute`,
`scripts/verify_v3_compatibility.py`, and
`scripts/verify_v3_architecture_readiness.py`. When the required input exists,
the original numerical path remains the only path after the availability
check; no missing-input path can report PASS or a physical/numeric failure.

## Manual mapping R1 audit

The read-only `ufotri_manual.md` SHA-256 was independently recomputed as
`82c7c7f07975553a51e7ba1666a912f80096e5af4fc138aba6f45a120e6d3562`.
The matrix contains 100 fields with 36 manual-explicit, 10 manual-derived,
34 D3-design-specific, 17 modern-QA, 7 controlled-chamber N/A, and 3
unresolved-no-source classifications. The complete explicit and derived sets
were checked for non-null manual authority and section/table/equation anchors.

The R1 anchor corrections are preserved:

```text
release_rate          -> 5.2.2 Table 3; no Appendix B §1
soil_layer_depths     -> 2.2.3; 2.2.4; 2.2.5; no Figure 13
root_hto_uptake_flux  -> 2.2.3; Equation (37); 2.2.5
```

The unresolved contract is exactly:

```text
cultivar_specific_resistance_parameter
chamber_mixing_to_outdoor_wind_transform
root_zone_hto_transfer_function
```

All three are `DEFER_UNRESOLVED`, have null defaults, and are unauthorized for
model use, acceptance use, or trusted-registry use.

The current medium is `5270 Bq/mL air-moisture water`, not liquid culture,
irrigation water, or reservoir water. Planned biological replicates per
primary time are 5. Three is only the minimum uncensored count for limited
deviation analysis; it does not replace the planned five or become a
recommended three-replicate design.

## Reblinding and evidence boundary

The common true-reblinding helper and independent review were audited. The
public generation, classification, and unblinding artifacts remain tracked;
only the private-secret path is resolved through the declared current-
worktree input contract. The private secret and truth key were absent and were
not read. The only authorized private behavior was the explicit
`SKIP_PRIVATE_SECRET_NOT_AVAILABLE` audit item. No key, default, truth mapping,
other-worktree content, or secret value was introduced. The public synthetic
classification remains synthetic and is not external evidence.

`verify_v2_validation_readiness.py` returned the V2 readiness token;
`verify_v3_external_evidence_unblocking.py` remained
`READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA` with local intake blocked; and
`verify_v3_physics_start_gate.py` remained
`BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA`. Real external evidence is FALSE
and formal V3 physics is NOT_STARTED.

## Added independent rereview and final checks

The independent test file contains 21 test items and was added without
duplicating the full manual or YAML contracts. After the three allowed files
were added, the following final checks were run:

```text
TARGET_MAPPING_TESTS = 22 passed; exit 0
TARGET_REMEDIATION_TESTS = 6 passed; exit 0
TARGET_PORTABILITY_TESTS = 11 passed; exit 0
REREVIEW_TESTS = 21 passed; exit 0
EXTERNAL_EVIDENCE_ACQUISITION = 80 passed; exit 0
PROSPECTIVE_EXPERIMENT = 33 passed; exit 0
TRUE_REBLINDING = 51 passed, 2 private-secret skips; exit 0
FULL_PORTABLE = 732 collected; 681 passed, 51 skipped; exit 0
PUBLIC_FINAL = 682 collected; 681 passed, 1 private-secret skip; exit 0
STRICT_FINAL = 49 explicit missing-input errors; exit 1
COMPILEALL = exit 0
GIT_DIFF_CHECK = exit 0
```

The protected diff from BASE_MAIN to the audited target remains empty for
`src/`, root `configs/`, and the trusted external-evidence registry. No raw
SB1/SB4/ERA5 file, private secret, or tag is tracked or changed.
