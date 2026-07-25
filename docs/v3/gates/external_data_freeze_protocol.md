# External-data freeze protocol

Status: `READY_PROTOCOL_NOT_EXECUTED`

1. Place received raw files under the appropriate Git-ignored
   `validation/external_local/<case>/` directory. Never copy raw values into
   tracked fixtures.
2. Record the data owner, licence/local-use statement, receipt date, and exact
   original filenames in the local source manifest.
3. Compute SHA-256 for every original file. Checksums identify bytes, not
   scientific adequacy.
4. Run the fail-closed adapter to generate a metadata-only intake manifest and
   field mapping.
5. Freeze unit definitions and explicit conversions, including air volume,
   plant water, combustion water, fresh/dry mass, and time basis.
6. Freeze sample/replicate identifiers and a disjoint calibration/holdout
   split. Holdout values must not be inspected during parameter selection.
7. Complete and commit the preregistration, including parameters, bounds,
   metrics, thresholds, exclusions, missing/detection-limit rules, regression
   requirements, and identifiability criteria.
8. Only after the preregistration commit may calibration execute. Freeze the
   resulting parameter package and its SHA-256 before any holdout execution.
9. Execute the holdout once under the frozen contract. Do not use holdout
   results for additional tuning; a revised model requires a new independent
   holdout or an explicitly exploratory claim.
10. Any corrected/reissued data file receives a new dataset version, checksum,
    intake manifest, field map, split review, and preregistration decision.
    Historical versions remain traceable and are never overwritten.

The internal numerical reference and synthetic contract case cannot substitute
for steps 1-10 and cannot satisfy an empirical gate.
