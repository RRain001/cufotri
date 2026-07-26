# SB4 data-quality report

```text
CASE_ID = EMRAS_SOYBEAN_SB4_PDF_ERA5_V1
SB4_DATA_STATUS = PASS_TRACEABLE_PUBLISHED_TABLE_TRANSCRIPTION
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
```

The local IAEA EMRAS report has SHA-256
`15b2591d82d8276c83030327d6a65d3f5a2e2ec3b11429d63b7c39461f50d211`.
Its text layer and rendered PDF pages 105, 287 and 290 were reviewed
cell-by-cell. The source PDF remains ignored local evidence and was not
recommitted.

Tracked publication-table content comprises:

| table | source | cells or rows |
|---|---|---:|
| plant-body and pod TFWT | Table 5.2 | 14 observations |
| harvest OBT | Table 5.3 | 6 observations |
| exposure/harvest fresh/dry biomass | Tables I.4.2-I.4.5 | 16 cells |
| plant-body and pod sampling schedule | Table I.4.10 | 14 rows |

The dataset builder and independent verifier reproduce the exact source
values, schedule and checksums. TFWT values are retained as published in
`Bq mL-1 water` and are converted explicitly to `Bq L-1 water` only at the
model interface. OBT values remain in `Bq mL-1 combustion water`.

The report does not provide a complete SB4 five-minute chamber curve,
five-minute chamber meteorology, a detection limit, or fully quantified total
measurement uncertainty. Those gaps are not filled with invented
observations. The case is therefore classified
`HYBRID_LITERATURE_REANALYSIS_RECONSTRUCTED_CHAMBER`, not empirical
validation.
