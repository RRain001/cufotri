# Soybean external-data unblocking manifest

```text
SOYBEAN_DATA_STATUS = BLOCKED_EXTERNAL_DATA
SOYBEAN_INTAKE_STATUS = READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
```

The IAEA EMRAS soybean scenario cannot be executed or calibrated from the
currently available publication alone. `Available` below means available to
the project as a legally usable, machine-readable input, not merely mentioned
or summarized in a publication.

| Item | Requirement | Availability | Candidate source | Licence status | Blocking reason |
|---|---|---|---|---|---|
| Organizer meteorology workbook | required | missing | experiment organizer | use/redistribution not established | continuous post-exposure forcing unavailable |
| Air HTO time series | required | missing; partial publication values only | organizer air workbook | raw-data permission not established | complete exposure and depuration boundary unavailable |
| Exposure start/stop timing | required | partial | publication plus organizer workbook | publication may be cited | exact common UTC/time basis not frozen |
| Chamber volume | required | missing | chamber metadata | not established | air inventory and replacement boundary undefined |
| Ventilation or mixing rate | required | missing | chamber metadata | not established | concentration boundary cannot be reproduced |
| Air replacement boundary | required | missing | chamber protocol | not established | inlet/outlet HTO accounting undefined |
| Temperature | required | partial exposure summary | organizer meteorology workbook | not established | continuous series unavailable |
| Relative humidity | required | partial exposure summary | organizer meteorology workbook | not established | continuous series unavailable |
| Wind or chamber mixing condition | required | missing | chamber protocol | not established | leaf boundary-layer condition undefined |
| Plant-water HTO observations | required | publication tables exist but are not an executable local package | organizer plant workbook | table reuse/raw-data permission not established | values, timing and metadata are not frozen together |
| Plant OBT observations | optional if measured; required for an OBT claim | partial publication tables | organizer plant workbook | table reuse/raw-data permission not established | no complete machine-readable series |
| Sampling times | required | partial | publication and plant workbook | not established | common time axis and exact sample mapping incomplete |
| Measurement uncertainty | required | partial approximate statement | analytical-method metadata | not established | value/replicate-level uncertainty unavailable |
| Detection limit | required | missing | analytical-method metadata | not established | censored-value policy cannot be preregistered |
| Replicate identifiers | required | missing/incomplete | organizer plant workbook | not established | calibration/holdout independence cannot be demonstrated |
| Unit definitions | required | partial | publication and workbook headers | publication may be cited | basis such as plant water/combustion water must be explicit |
| Licence/local-use conditions | required | missing for supporting workbooks | organizer/data owner | unresolved | lawful local analysis and redistribution boundary unknown |
| File checksum | required | missing because files are absent | local intake process | not applicable until receipt | version and provenance cannot be frozen |

Publication plots or selected table values must not be OCRed, digitized, or
combined with invented meteorology. Data from different experiments, sites, or
periods must not be spliced.

Unblocking requires a local package under the Git-ignored
`validation/external_local/soybean_emras/` directory. The adapter then checks
licence, fields, units, continuous air/meteorology series, exposure coverage,
mixing boundary, detection limits, replicate IDs, and disjoint
calibration/holdout IDs. It generates checksums and a metadata-only intake
manifest. Passing intake can only produce `READY_FOR_PREREGISTRATION`; it does
not authorize calibration or establish empirical validation.
