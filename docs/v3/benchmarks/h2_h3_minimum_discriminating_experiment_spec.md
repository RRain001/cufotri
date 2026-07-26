# Minimum H2/H3 discriminating experiment specification

```text
SPECIFICATION_STATUS = READY_FOR_EXTERNAL_DATA_SEARCH_OR_NEW_EXPERIMENT
DESIGN_ID = D3_SHORT_STEP_24H
SYNTHETIC_DESIGN_STATUS = DESIGN_ONLY
EMPIRICAL_VALIDATION_CLAIM = FALSE
```

- Controlled chamber conditions: 25 degC, RH 70%, wind 0.5 m/s, LAI 4,
  constant daytime exchange, zero precipitation and strict zero HTO
  background outside declared exposures.
- First exposure: start 0 h, duration
  24 h, concentration
  5270 Bq/mL water.
- Washout: 0 h at strict zero background.
- Second exposure: null.
- Total planned model follow-up: 120 d after the final exposure; minimum
  TFWT sampling times after final exposure: 0.2 h, 48 h, 120 h.
- Recommended additional times: all remaining preregistered candidate times
  needed for diagnostic coverage:
  0.2, 0.5, 1, 3, 6, 12, 24, 48, 72, 120, 168, 336, 504, 768 h.
- Biological replicate recommendation: at least 3 independent plants
  or chamber-equivalent biological replicates per time. This is a Monte Carlo
  design recommendation, not a formal power proof.
- Primary measurement: total plant-body TFWT, Bq/L tissue water. Record
  combined stem+leaf result; leaf and stem separation is recommended as an
  additional diagnostic. Roots and pods are optional secondary matrices and
  must not replace the preregistered total plant-body classifier.
- Measure air-moisture HTO at 5-minute or finer resolution throughout both
  exposure and washout periods. Measure chamber temperature and RH at
  5-minute or finer resolution; record wind/mixing continuously or at the
  same interval.
- Record fresh and dry mass for each sampled organ and the water-extraction
  or combustion-water basis. Preserve raw instrument units and conversion
  metadata.
- Target total relative TFWT uncertainty: <=20%. Recommended analytical
  detection limit: <= 468.985 Bq/L tissue water, defined here as
  no more than 10% of the smallest frozen predicted concentration at the
  minimum sampling times. This is a design target, not an instrument claim.
- Background air-moisture HTO must be measured rather than assumed and should
  remain below 1% of the low-exposure setpoint. Any exceedance must be retained
  in the forcing record.
- Required data fields: experiment_id, chamber_id, replicate_id,
  sample_datetime_utc, hours_after_final_exposure, organ, fresh_mass_g,
  dry_mass_g, tissue_water_ml, tfwt_bq_l_water, analytical_uncertainty,
  detection_limit, air_hto_bq_ml_water, temperature_c, RH_percent,
  wind_speed_m_s, mixing_status, exposure_phase, method_version and
  quality_flag.
- Deliver UTF-8 CSV plus a machine-readable manifest containing SHA-256 for
  every raw and processed file, timezone, units, instrument calibration,
  detection-limit method, missing-value encoding and licence/redistribution
  terms.
