# CTEAS_UFOTRI

Runnable Python 3.12+ minimal HTO model coupling rural Gaussian dispersion,
topsoil water/HTO, plant TFWT/OBT, re-emission feedback, and mass balance.
It is a tested engineering baseline, not a full reproduction of every UFOTRI
equation.

## Install and verify

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest -vv
.venv/bin/python scripts/verify_acceptance.py --recompute
```

Run the 48 h case:

```bash
.venv/bin/python -m cteas_ufotri.cli
```

Run the 24 h optional-mode acceptance case:

```bash
.venv/bin/python -m cteas_ufotri.cli \
  --case configs/advanced_test_case.yaml
```

Run the V2 physics-remediation acceptance:

```bash
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
```

Current formal disposition is:

```text
V2_STATUS = FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE
CURRENT_RELEASE_BASIS = RC2_INDEPENDENT_REAUDIT_ACCEPTED_WITH_MINOR_CORRECTIONS
FORMAL_SCOPE = HTO_ONLY_RESEARCH_CANDIDATE
SITE_CALIBRATED = NO
REGULATORY_VALIDATED = NO
COMPLETE_UFOTRI_EQUIVALENCE = NO
```

This is a formal research-candidate release claim, not a site, regulatory, or
complete-UFOTRI validation claim. The evidence chain is indexed in
`docs/v2/v2_audit_history.md`; machine-readable remaining limitations are in
`docs/v2/v2_candidate_limitations.yaml`.

The post-release validation infrastructure is documented in
`docs/v2/validation/v2_validation_master_plan.md`. Run its executable
zero-source example and infrastructure gate with:

```bash
.venv/bin/python scripts/run_v2_validation_case.py \
  --case validation/cases/example_zero_source.yaml \
  --output /tmp/ufotri-zero-source-validation
.venv/bin/python scripts/verify_v2_validation_readiness.py
```

The readiness result means that independent datasets can be connected
reproducibly. It does not mean that experimental, field, reference-model, site,
or regulatory validation has been completed.

Outputs are written to `outputs/rural_stack_short_case/`: `results.csv`, an
atmospheric grid CSV, six PNG diagnostics, and `validation_report.md`. Configuration is split between
`configs/default_parameters.yaml` and `configs/test_case.yaml`; no case
parameter is hard-coded in the calculation modules.

## Inputs

- `configs/default_parameters.yaml`: atmospheric, water/HTO, plant/OBT,
  re-emission, physical, numerical, synthetic-forcing, and output defaults.
- `configs/test_case.yaml`: source/site coordinates, stack conditions, release,
  duration, time step, receptor, and output directory.
- `configs/advanced_test_case.yaml`: optional-mode acceptance case.
- `configs/era5_mapping.yaml`: variable aliases, units/sign contract, and
  accumulation semantics for CSV/NetCDF.
- `ufotri_manual.md`: primary reviewed physical source.

ERA5 CSV/NetCDF fields are mapped by `configs/era5_mapping.yaml`; without
`--era5`, the example uses deterministic synthetic forcing. Example:

```bash
.venv/bin/python -m cteas_ufotri.cli \
  --era5 data/era5/era5_surface_2025-06-01_2025-06-02.csv \
  --output-directory outputs/rural_stack_short_case_era5
```

Raw data and credentials are ignored and treated as read-only.
CDS credentials may be supplied as the paired environment variables
`CDSAPI_URL`/`CDSAPI_KEY` or through an ignored `era5_key.txt`; see
`era5_key.example.txt`. Credential values are never logged by project code.

## Result variables

`results.csv` contains:

| Variable | Meaning / unit |
|---|---|
| `air_hto_concentration` | receptor air HTO, Bq m-3 |
| `soil_water_storage` | topsoil water depth, m |
| `soil_hto_inventory` | topsoil HTO inventory, Bq m-2 |
| `soil_hto_concentration` | soil-water HTO, Bq m-3 |
| `soil_evaporation` | soil water evaporation, m s-1 |
| `plant_transpiration` | plant transpiration, m s-1 |
| `root_water_uptake` | HTO-carrying root water uptake, m s-1 |
| `deep_drainage` | downward water flux, m s-1 |
| `plant_tfwt_inventory` | plant TFWT inventory, Bq m-2 |
| `plant_tfwt_concentration` | plant-water HTO, Bq m-3 |
| `plant_obt_inventory` | plant OBT inventory, Bq m-2 |
| `soil_reemission_flux` | soil-to-air HTO, Bq m-2 s-1 |
| `plant_reemission_flux` | plant-to-air HTO, Bq m-2 s-1 |
| `total_reemission_flux` | total secondary area flux, Bq m-2 s-1 |
| `mass_balance_error` | signed step residual, Bq m-2 |
| `mass_balance_relative_error` | absolute relative step residual |
| `external_stack_input_bq` | integrated stack release, Bq |
| `dry_plume_loss_bq`, `wet_plume_loss_bq` | integrated steady-plume removals, Bq |
| `dry_surface_input_bq`, `wet_surface_input_bq` | allocated surface inputs, Bq |
| `environmental_inventory_bq` | current soil/plant/animal/product activity over the accounting area, Bq |
| `activity_residual_bq` | combined surface/ecological activity-ledger residual, Bq |

Formal fields are `surface_box_absolute_residual_bq_m2` and
`surface_box_relative_residual`; the two `mass_balance_*` fields are deprecated
compatibility aliases. This ledger covers soil HTO + TFWT + OBT only. The
steady Gaussian atmosphere has a separate source/sink budget, not a dynamic
air inventory.
The complete RC2 activity-field semantics are in
`docs/v2/activity_propagation_protocol.md`.

## Implemented scope

- ERA5 CSV/NetCDF mapping, UTC/time validation, interval/cumulative-reset
  conversion, RH/VPD, radiation and wind derivations.
- UFOTRI Eq. (38)-(43) PET/LAI/moisture route and replaceable water fallback.
- Rural Gaussian point plume, rectangular area source, PG dispersion,
  wind rotation/profile, fixed or simplified Briggs rise, and mixing-layer
  reflection.
- Conservative 5 cm soil water/HTO, plant TFWT/OBT, rain HTO, optional root
  delay, basic or empirical re-emission, and lagged atmospheric feedback.
- Bounded explicit integration, continuous SciPy references, time-step
  regression, per-step mass balance, CSV/grid/plot/report outputs.

## V2 extensions and deliberate UFOTRI differences

V2 adds wet deposition, meteorology-responsive bidirectional leaf exchange,
crop/edible inventories, minimal pasture-cow-milk-beef pathways,
research-screening dose, perennial pasture, and mode-aware uncertainty. These
are bounded project extensions, not complete UFOTRI or field validation. The
model still excludes multi-layer Richards coupling, HT oxidation/chemistry,
regulatory dosimetry, and dynamic three-dimensional atmospheric conservation.
Simplified Briggs, Penman aerodynamic, uniform footprint, ERA5
net-radiation/extension fallbacks, empirical REEM/DIFF/ZT detail, crop yields,
habits, and hydrology remain replaceable assumptions.

See `docs/implementation_status.md` for exact status and remaining differences
from the manual, `docs/assumptions.md` for defaults, and
`docs/equations/variables_and_units.md` for the unit contract.

Implemented replaceable modes include rectangular re-emission area sources,
fixed or simplified Briggs plume rise, fixed or Turner stability, optional
mixing-layer reflection, immediate or delayed root HTO uptake, basic or
REEM/DIFF/ZT soil re-emission, and constant-average or day/night OBT formation.

The formal minimal v1 baseline adds explicit precipitation/infiltration/runoff
HTO routing, recorded calm-wind handling, project-level dry source depletion,
3600 s re-emission feedback, radiation-term-only Eq. (40) shading, and strict
feedback-area validation. Wet scavenging is explicitly not implemented and
advanced REEM/DIFF/ZT remains provisional.
