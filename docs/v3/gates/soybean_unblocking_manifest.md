# Soybean external-data unblocking manifest

Status: `BLOCKED_EXTERNAL_DATA`

The IAEA EMRAS soybean scenario cannot be executed or calibrated from the
currently available publication alone. The minimum missing package is:

| Item | Required state | Current state |
|---|---|---|
| Organizer meteorology Excel | complete, checksum recorded | missing |
| Air HTO time series/workbooks | complete exposure and depuration | missing/partial publication table only |
| Chamber mixing/ventilation boundary | measured or documented | missing |
| Detection limits | per observable/method | missing |
| Measurement uncertainty | per value or defensible method | partial |
| Exact timing | exposure, forcing, samples in one time basis | incomplete |
| Licence/local-use rule | documented use and redistribution decision | redistribution not established |

Publication plots or selected table values must not be digitized and combined
with invented meteorology. Data from different experiments, sites, or periods
must not be spliced.

Unblocking requires a local manifest under the Git-ignored
`validation/external_local/` directory with file checksums and licence
decision. The adapter may then report `READY_FOR_PREREGISTRATION`; it cannot
run calibration until a preregistration commit predates holdout inspection.
