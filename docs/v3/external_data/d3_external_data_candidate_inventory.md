# D3 external-data candidate inventory

Status: `COMPLETE_NO_EXECUTABLE_PUBLIC_DATA`
Protocol: `D3_EXTERNAL_DATA_SEARCH_V1`
Search date (UTC): `2026-07-27`

## Conclusion

No public Tier A or Tier B dataset was found that can execute the frozen D3
comparison. Three sources contain public numeric TFWT tables and are retained
as Tier C mechanism-support evidence. Five additional primary records were
reviewed but are non-executable because the public material is abstract- or
figure-only, or lacks reusable forcing and observations.

The result does not authorize calibration, H2/H3 execution, trusted-registry
changes, formal external validation, or production physics.

## Fixed scoring rule

Each of the 13 protocol criteria is scored 0--2. The aggregate scores are:

- `exact_match_score`: first five design-match criteria, maximum 10;
- `forcing_completeness_score`: air, background and meteorology, maximum 6;
- `observation_completeness_score`: replicates, uncertainty, biomass and
  raw/numeric data, maximum 8;
- `licence_score`: licence clarity, maximum 2;
- `overall_executability_score`: all 13 criteria, maximum 26.

Scores rank follow-up effort only. A hard gap always overrides the numerical
score.

## Inventory summary

| ID | Source | Tier | Numeric | Overall / 26 | Hard result |
|---|---|---:|---:|---:|---|
| D3C-001 | IAEA/KAERI EMRAS soybean final report | C | yes | 14 | 1 h exposure; no 48 h point; forcing workbooks inaccessible |
| D3C-002 | Boyer lettuce thesis | C | yes | 12 | different crop; no post-exposure 0.2/48/120 h series |
| D3C-003 | NNC Kazakhstan vegetable study | C | yes | 11 | different crops and 6--8 h exposure; no target series |
| D3C-004 | KAERI/KNS short-term plant paper | non-executable | no | 3 | figure-only; sampling and forcing incomplete |
| D3C-005 | KAERI soybean DBpia record | non-executable | no | 1 | public record only; no reusable numeric data |
| D3C-006 | 2016 daytime/nighttime soybean paper | non-executable | no | 0 | no public numeric post-exposure series located |
| D3C-007 | 2019 maize acute-exposure paper | non-executable | no | 0 | abstract only and different crop |
| D3C-008 | IAEA EMRAS-II wheat presentation | non-executable | no | 0 | figure-only and different crop |

Counts: `TIER_A=0`, `TIER_B=0`, `TIER_C=3`,
`NON_EXECUTABLE=5`.

## Best candidate

`D3C-001` is the highest-priority request target because it is soybean,
reports plant-body TFWT, and contains numeric observations at 0.2 h and
120 h. It remains Tier C and non-executable for frozen D3 because:

1. exposure was 1 h, not approximately 24 h;
2. 48 h was not sampled;
3. `sbTbox.xls`, `sbTHS.xls`, and `sbWR.xls` are referenced but are not
   accessible at the reviewed public URLs;
4. sample-level raw data are not public;
5. licence and redistribution terms are unknown.

The IAEA report also states that the samples were composites from multiple
plants and gives an approximately 10% counting error, but it does not provide
the number of plants per composite or a complete detection-limit statement.

## EMRAS attachment search

The IAEA scenario/report references the three workbooks, so their status is
not `NOT_LOCATED`. Direct checks of plausible current IAEA download paths and
exact-filename checks in Internet Archive did not yield downloadable files.

```text
sbTbox.xls = REFERENCED_NOT_ACCESSIBLE
sbTHS.xls  = REFERENCED_NOT_ACCESSIBLE
sbWR.xls   = REFERENCED_NOT_ACCESSIBLE
```

This means only that they were not publicly retrievable during this search;
it is not a claim that the files do not exist.

## Source review record

Primary pages or files opened during review:

- IAEA EMRAS tritium working-group page, soybean scenario PDF and final report;
- IAEA EMRAS-II wheat working-group presentation;
- KAERI/Korean Nuclear Society public conference paper;
- DBpia primary article record;
- Nuclear Science and Techniques primary article record/DOI;
- Université de Franche-Comté public Boyer thesis;
- National Nuclear Center of Kazakhstan public bulletin PDF;
- PubMed primary bibliographic record and publisher DOI for the maize study.

Searches covered English, Korean, Japanese and French. Institution-specific
queries also covered IAEA, KAERI, JAEA/NRA-related sources, CEA/IRSN-oriented
French repositories, publisher sites, university repositories and formal
data-repository queries. Search-result snippets were never treated as
experimental facts.

## Public download and licence boundary

`PUBLIC_RAW_DATA_FOUND=false`. The public PDFs were inspected as source
documents, not accepted as raw candidate datasets. Therefore no file was
placed under `validation/external_local/d3_candidate_*/raw`, no raw manifest
was created, and `RAW_FILE_DOWNLOAD_COUNT=0`.

`PUBLIC_NUMERIC_DATA_FOUND=true` refers only to numeric tables embedded in
public PDF documents. No reviewed source supplied an explicit data licence
that authorizes raw-data redistribution, so `LICENCE_REVIEW_STATUS` remains
`BLOCKED_NO_CANDIDATE_RAW_DATA_AND_TERMS_UNKNOWN`.

## Machine-readable records

The YAML inventory is normative for tests and preserves criterion-level
scores. The CSV contains the same candidate fields for audit and spreadsheet
review. Unknown values use only `UNKNOWN`, `NOT_REPORTED`, or
`NOT_AVAILABLE`; no missing experimental values were inferred.
