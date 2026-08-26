# V4 system atmospheric exchange contract R1 review

Status: `READY_FOR_EXACT_HEAD_CI`

Branch: `codex/v4-system-atmos-exchange-contract-r1`

Base main: `ec31dd43d5f8085b783d3ebb26949d9ff932f402`

## Decision

The producer/consumer exchange semantics are frozen without modifying the current V3 runtime. The normalized record is HTO-only and represents one spatial support over one positive UTC half-open interval. It requires air HTO concentration, true total surface HTO deposition flux, temperature, relative humidity, wind speed, precipitation rate, explicit spatial/height semantics, provenance and quality state.

## CTEAS-Atmos compatibility audit

Read-only reference: `RRain001/CTEAS-Atmos@341d9d6b3b45b6e2416e09aec0b381adf137fd3e`.

Compatible boundaries:

- UTC and half-open interval time semantics with explicit temporal meaning;
- radionuclide receptor concentration product in `Bq/m^3`;
- explicit grid/receptor and provenance-oriented architecture.

Unclosed production boundary:

- Stage18 dry/wet deposition ledger values are per-puff/per-interval amounts in Bq, not receptor/surface fluxes in `Bq m^-2 s^-1`;
- the reviewed snapshot does not by itself prove a production surface deposition flux product that can be bound to `AtmosphericHTOForcing.deposition_flux`.

Therefore the contract is frozen but real producer binding remains fail-closed:

```ini
CTEAS_ATMOS_TIME_SEMANTICS = COMPATIBLE
CTEAS_ATMOS_CONCENTRATION_SEMANTICS = COMPATIBLE
CTEAS_ATMOS_SURFACE_DEPOSITION_FLUX_PRODUCT = UNCONFIRMED
REAL_PRODUCER_BINDING = BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED
```

## Frozen V3 compatibility

No file under `src/cteas_ufotri/coupling/atmos_v3/` is changed by this stage. A later adapter may map the normalized exchange record to the current fields, but adapter implementation and live CTEAS-Atmos coupling require a separate stage and independent review.

The interval-start mapping remains consistent with P7.5/P7.5B:

```text
exchange.start_utc -> AtmosphericHTOForcing.timestamp
```

## Scientific safeguards

- HTO cannot be replaced by HT/DT/T2 or unspecified total tritium.
- Sampling height and vertical reference cannot be implicit.
- Stage18 ledger Bq amounts cannot be relabeled as surface deposition flux.
- Accumulated `Bq m^-2` cannot be relabeled as `Bq m^-2 s^-1`.
- Missing surface flux cannot be silently set to zero.
- Meteorological co-forcing may come from accepted Atmos inputs or another reviewed aligned source, but provenance must remain explicit.
- Replay and synthetic records remain labeled and do not constitute live coupling or empirical validation.

## Exit state

```ini
V4_SYSTEM_ATMOS_EXCHANGE_CONTRACT = PASS_CONTROL_PLANE_CONTRACT_FROZEN
V3_ATMOS_RUNTIME_CHANGED = FALSE
REAL_CTEAS_ATMOS_COUPLING_ACTIVE = FALSE
SOLVER_CHANGES_AUTHORIZED = FALSE
NUMERICAL_COUPLING_CHANGES_AUTHORIZED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
V3_PHYSICS_READY = FALSE
NEXT_STAGE = V4_SYSTEM_PHYSICS_GAP_SENSITIVITY_AUDIT
```

Exact-head CI must pass the portable suite and `tests/v4/test_v4_system_atmos_exchange_contract.py` before merge.
