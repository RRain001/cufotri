# D3 EMRAS attachment search and licence review

Search date (UTC): `2026-07-27`  
Scope: read-only public-source discovery  
Candidate: `D3C-001`

## Result

```text
sbTbox.xls = REFERENCED_NOT_ACCESSIBLE
sbTHS.xls  = REFERENCED_NOT_ACCESSIBLE
sbWR.xls   = REFERENCED_NOT_ACCESSIBLE
```

The files are explicitly referenced by the public soybean scenario material:

- `sbTbox.xls`: detailed glove-box air HTO data;
- `sbTHS.xls`: temperature, humidity and solar-radiation data;
- `sbWR.xls`: wind and rain data.

The final report confirms that air concentration, background concentration,
biomass and meteorological information were supplied to scenario
participants. It does not embed the three original workbooks.

## Locations checked

The search opened the current IAEA EMRAS working-group page, the public
soybean scenario PDF, and the public soybean final report. Direct requests
were made to plausible paths under both:

```text
https://www-ns.iaea.org/downloads/rw/projects/
https://www-ns.iaea.org/downloads/rw/projects/emras/tritium/
```

for the exact filenames and common case-preserving forms. These requests did
not return the workbooks. Exact-filename web searches and Internet Archive
index checks did not locate a downloadable archived copy during the bounded
search. KAERI, Korean conference/database records, EMRAS meeting material and
author/report discovery paths were also checked without finding a public
workbook download.

This evidence does not support `NOT_LOCATED`, because the files are explicitly
named in the scenario. It also does not support `FOUND_PUBLICLY`, because no
downloadable copy was recovered. `REFERENCED_NOT_ACCESSIBLE` is therefore the
only supported status.

## Licence review

The IAEA PDFs are publicly readable. The reviewed pages do not provide an
explicit licence for the unlocated workbooks, sample-level observations, or
redistribution of those data.

```text
RAW_DATA_LICENCE = UNKNOWN
REDISTRIBUTION_ALLOWED = UNKNOWN
REGISTRY_ELIGIBLE = FALSE
LICENCE_REVIEW_STATUS =
BLOCKED_NO_CANDIDATE_RAW_DATA_AND_TERMS_UNKNOWN
```

Public readability is not treated as permission to redistribute a dataset.
No raw file was downloaded, copied into `validation/external_local`, or added
to Git.

## Required next action

Use the prepared request package to ask IAEA/KAERI or the scenario authors for:

1. the three original workbooks in native or lossless tabular form;
2. a data dictionary, units, timestamps, missing-value codes and quality flags;
3. sample-level TFWT and biomass data if retained;
4. the applicable licence and redistribution conditions.

The request remains a draft and has not been sent.
