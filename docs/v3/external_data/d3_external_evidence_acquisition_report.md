# D3 external evidence acquisition report

## Executive result

The D3 discriminability research was independently reviewed, merged to
`main`, and remains a research design rather than an empirical mechanism
selection. The subsequent public-data search found no executable Tier A or
Tier B dataset. Three public sources contain numeric TFWT tables usable only
as Tier C mechanism-support evidence; five other primary records are
non-executable.

The highest-priority request target is the IAEA/KAERI EMRAS soybean source
package. Its public report has the correct crop, plant-body TFWT and 0.2/120 h
observations, but the exposure is 1 h, the 48 h point is missing, the original
forcing workbooks are inaccessible and the data licence is unknown.

No contact was sent. A manual data-request draft and a prospective experiment
commission package are ready. The acquisition branch is intentionally
unmerged.

## Machine-readable status

```text
MERGED_D3_DESIGN_HEAD =
1f44f8f847e8869e09b6f87262b81cafc2f2828e

ACQUISITION_BRANCH =
codex/v3-d3-external-evidence-acquisition

ACQUISITION_EVIDENCE_PARENT =
242af8b

ACQUISITION_BRANCH_HEAD =
THIS_REPORT_COMMIT

SEARCH_PROTOCOL_STATUS =
FROZEN_BEFORE_FORMAL_SEARCH

SEARCH_DATE_UTC =
2026-07-27

SEARCH_LANGUAGES =
English,Korean,Japanese,French

SOURCES_SEARCHED =
IAEA,KAERI,KNS,DBpia,JAEA_NRA_RELATED_QUERIES,
CEA_IRSN_RELATED_QUERIES,UNIVERSITY_REPOSITORIES,
JOURNAL_PUBLISHERS,PUBMED,FORMAL_DATA_REPOSITORIES,
INTERNET_ARCHIVE,NNC_KAZAKHSTAN

TIER_A_COUNT = 0
TIER_B_COUNT = 0
TIER_C_COUNT = 3
NON_EXECUTABLE_COUNT = 5

PUBLIC_RAW_DATA_FOUND = FALSE
PUBLIC_NUMERIC_DATA_FOUND = TRUE

EMRAS_ATTACHMENTS_STATUS =
sbTbox.xls:REFERENCED_NOT_ACCESSIBLE,
sbTHS.xls:REFERENCED_NOT_ACCESSIBLE,
sbWR.xls:REFERENCED_NOT_ACCESSIBLE

BEST_CANDIDATE_ID = D3C-001
BEST_CANDIDATE_TIER = TIER_C
BEST_CANDIDATE_BLOCKING_GAPS =
1H_NOT_24H;NO_48H_SAMPLE;FORCING_WORKBOOKS_INACCESSIBLE;
NO_PUBLIC_SAMPLE_LEVEL_RAW_DATA;LICENCE_UNKNOWN

RAW_FILE_DOWNLOAD_COUNT = 0
RAW_MANIFEST_STATUS = NOT_CREATED_NO_RAW_FILES
LICENCE_REVIEW_STATUS =
BLOCKED_NO_CANDIDATE_RAW_DATA_AND_TERMS_UNKNOWN

DATA_REQUEST_PACKAGE_STATUS =
DRAFT_READY_NOT_SENT

EXPERIMENT_COMMISSION_PACKAGE_STATUS =
READY

REAL_EXTERNAL_VALIDATION_RUN =
NOT_STARTED

TRUSTED_REGISTRY_CHANGE_COUNT =
0

FORMAL_V3_PHYSICS =
NOT_STARTED

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Search and evidence review

The protocol and tier definitions were committed before formal search. Each
retained fact came from an opened primary organization page, report, thesis,
paper, presentation or bibliographic record; search-result snippets were used
only for discovery.

The main evidence paths were:

- IAEA EMRAS working-group page, soybean scenario and final report;
- IAEA EMRAS-II wheat presentation;
- KAERI/Korean Nuclear Society public paper and DBpia record;
- the Nuclear Science and Techniques article record/DOI;
- the public Boyer thesis hosted by Université de Franche-Comté;
- the National Nuclear Center of Kazakhstan bulletin PDF;
- the PubMed/publisher record for the maize study.

Institution- and language-specific queries covered the sources required by
the frozen protocol. No public raw-data repository or supplementary-material
page yielded a complete D3-like dataset.

## Candidate result

The normative candidate inventory is
`validation/external_evidence_acquisition/d3/d3_external_data_candidate_inventory.yaml`.
It includes every required field, criterion-level 0--2 scores, aggregate
scores and hard blocking gaps. The CSV is a same-row audit view. Hard gaps,
not total scores, determine execution status.

No Tier B candidate was assigned merely because a crop was broadleaf: a Tier B
case still needs a 12--48 h exposure, bracketing samples, complete forcing and
recombinable TFWT. The public lettuce thesis matches 24 h exposure but lacks
the required post-exposure trajectory. The NNC study has a useful public
washout table but uses different crops, a 6--8 h exposure and different
sampling times.

## EMRAS workbook and licence boundary

`sbTbox.xls`, `sbTHS.xls` and `sbWR.xls` are explicitly referenced, so
`NOT_LOCATED` would overstate the negative result. Direct current IAEA path
checks, exact-filename web searches, Internet Archive index checks, KAERI
records and EMRAS meeting paths did not produce downloadable workbooks.
`REFERENCED_NOT_ACCESSIBLE` is the supported status for all three.

Public readability of an IAEA PDF is not treated as a raw-data redistribution
licence. No candidate has adequate raw-file licence terms for registry intake.
The source PDFs inspected during search were not copied into a candidate raw
directory; therefore the raw-file download and manifest counts are zero.

## Request and prospective experiment

The request package asks for air HTO, exact exposure times, post-exposure
background, temperature/RH/mixing, plant-body and organ TFWT, timestamps,
replicate identity, fresh/dry mass, uncertainty, detection limits,
instrument/method metadata, dictionary, missing-value and quality-flag
semantics, licence and redistribution conditions.

The email is a draft only:

```text
REQUEST_STATUS = DRAFT_READY_NOT_SENT
```

Because executable Tier A data count is zero, the commission package specifies
the minimum prospective experiment as:

- soybean exposed to 5270 Bq/mL water in air moisture for 24 h;
- 25 degrees C, RH 70%, mixing 0.5 m/s and zero precipitation;
- measured post-exposure HTO background;
- 120 h post-exposure follow-up, for 144 h total;
- post-exposure samples at 0.2, 48 and 120 h;
- at least three biological replicates per destructive time;
- total plant-body TFWT in Bq/L tissue water;
- target total uncertainty at or below 20%;
- air HTO and temperature/RH/mixing at 5-minute resolution or finer.

`EXTENDED_120_DAY_FOLLOWUP=OPTIONAL`; it is not a minimum requirement.

## Fail-closed tests

Twenty acquisition tests pass. They cover the required schema/tier/gate
checks and reject:

- Tier A without air HTO;
- registry eligibility without a licence;
- OBT-only evidence marked D3-executable;
- a draft email marked sent;
- synthetic CSV marked as real experiment;
- an ignored raw file represented as Git-tracked.

Full repository collection is 586 tests (the prior 566 plus 20 acquisition
tests), and the full pytest run exits successfully.

```text
ACQUISITION_TEST_STATUS = PASS_20_OF_20
FULL_REPOSITORY_COLLECTED_TEST_COUNT = 586
FULL_REPOSITORY_PYTEST_EXIT = PASS
COMPILEALL_STATUS = PASS
V1_RECOMPUTE_ACCEPTANCE = PASS_5_FROZEN_CASES
V2_RECOMPUTE_ACCEPTANCE = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
V2_VALIDATION_READINESS = PASS
V3_COMPATIBILITY = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE = READY_ARCHITECTURE_ONLY
V3_EXTERNAL_EVIDENCE = READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
V3_PHYSICS_START_GATE_VERIFICATION =
PASS_BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Future gate order

```text
real data arrive
-> store raw files read-only
-> create SHA-256 manifest
-> licence review
-> data-quality review
-> add trusted-registry entry on an approval branch
-> independent registry review
-> merge registry approval to main
-> freeze real external-validation protocol
-> freeze H2/H3 predictions
-> open discriminating observations
-> independent external-validation review
```

The acquisition branch cannot authorize itself. Formal discrimination before
merged registry approval remains prohibited.

## Key executed commands

```bash
git status --short --branch
git rev-parse main origin/main HEAD
git ls-remote origin
curl -I and exact public URL checks for source discovery
Internet Archive CDX exact-filename checks
pdftotext and PDF page rendering for table/source review
.venv/bin/python -m pytest -q \
  tests/external_evidence_acquisition/test_d3_external_evidence_acquisition.py
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_validation_readiness.py
.venv/bin/python scripts/verify_v3_compatibility.py
.venv/bin/python scripts/verify_v3_architecture_readiness.py
.venv/bin/python scripts/verify_v3_external_evidence_unblocking.py
.venv/bin/python scripts/verify_v3_physics_start_gate.py
.venv/bin/python -m compileall -q src tests era5 scripts validation
git diff --check
git diff main...HEAD -- src configs
```

## Stop state

```text
D3_RESEARCH =
INDEPENDENTLY_REVIEWED_AND_MERGED

EXTERNAL_DATA_SEARCH =
COMPLETE_NO_EXECUTABLE_PUBLIC_DATA

DATA_REQUEST_PACKAGE =
READY_NOT_SENT

EXPERIMENT_COMMISSION_PACKAGE =
READY

NEXT_STEP =
MANUAL_DATA_REQUEST_OR_NEW_EXPERIMENT

H2_H3_FORMAL_SELECTION =
NOT_AUTHORIZED

FORMAL_V3_PHYSICS =
NOT_STARTED

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```
