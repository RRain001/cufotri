# EMRAS soybean SB4 transfer benchmark

```text
CASE_ID = EMRAS_SOYBEAN_SB4_PDF_ERA5_V1
EXPERIMENT = SB4
BENCHMARK_CLASS =
HYBRID_LITERATURE_REANALYSIS_RECONSTRUCTED_CHAMBER
PRIMARY_PURPOSE = CROSS_EXPERIMENT_PARAMETER_TRANSFER_TEST
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
```

This validation-only benchmark transcribes the published SB4 tables and
reuses checksum-verified SB1 ERA5 raw responses. The public report does not
provide an SB4 five-minute chamber curve, so the benchmark uses two explicitly
reconstructed profiles: a constant reported mean and the published SB1 shape
scaled to the SB4 reported mean.

H2 and H3 parameters are transferred unchanged from the SB1 frozen parameter
commit. SB4 observations are never used to fit parameters or expand bounds.
Pods are a provisional structural diagnostic and OBT is a consistency veto.
Neither is positive model-selection evidence.

The source PDF and ERA5 raw files remain in ignored local storage. No formal
`src/`, project `configs/`, trusted-registry or production-gate file belongs
to this benchmark.
