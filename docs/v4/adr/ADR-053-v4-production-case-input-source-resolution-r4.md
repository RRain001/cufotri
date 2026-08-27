# ADR-053: V4 production-case identity and Eq.39 pressure-source selection R4

Status: proposed for exact-head certification

Stage: `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R4`

Base main: `25e2b50e2096bfd3953a5f5fdc637b1f7eaee8b3`

## Decision

Apply the R3 pressure/elevation provenance contract to the production-case evidence currently present in the repository.

The selection result is fail-closed:

`BLOCKED_PRODUCTION_CASE_IDENTITY_NOT_INDEPENDENTLY_DECLARED`.

No production pressure source, site-elevation source, or psychrometric-constant value is selected.

## Why the historical Hefei coordinate is not promoted

The repository contains a requested ERA5 test point at `117.141610855 E, 31.939774444 N` and a returned nearest grid point at `117.25 E, 32.00 N`. These records occur in the ERA5 test/audit context. `docs/assumptions.md` explicitly states that the short-case source/receptor values are finite test values, not site claims, and that crop defaults are not claims about the Hefei receptor or a specific agricultural survey.

Accordingly the requested coordinate is classified as:

`HISTORICAL_TEST_CONTEXT_NOT_PRODUCTION_BINDING`.

Name strings such as `Hefei-H3-ERA5/1.0` are software/request labels, not production-case declarations.

A matching coordinate does not override provenance semantics. R4 therefore does not infer a production `case_id`, `scenario_id`, facility identity, operational mode, or production time window from those test artifacts.

## Independent source blockers

Even after the identity blocker is considered separately, the historical 48 h ERA5 audit does not document surface atmospheric pressure among its mapped variables. It lists temperature, dew point, wind, precipitation, downward solar energy, and downward thermal energy.

The repository also contains no independently sourced `site_elevation_m_msl` satisfying the R3 vertical-datum contract.

Therefore:

- `selected_case_mean_atmospheric_pressure_source = null`;
- `selected_site_elevation_m_msl_source = null`;
- `selected_psychrometric_constant = null`.

The explicit-pressure and elevation-derived paths both remain unavailable for production use.

## Minimum production-case identity binding packet

Before any real pressure/elevation source can be selected, an independent production-case declaration must provide all of the following identities with provenance:

- `case_id`;
- `scenario_id`;
- `facility_or_site_id`;
- `site_location_id`;
- `site_latitude_deg`;
- `site_longitude_deg`;
- `horizontal_crs_or_datum`;
- `production_time_start_utc`;
- `production_time_end_utc`;
- `operational_mode_or_release_case`;
- `declaration_source_id`;
- `declaration_source_revision`;
- `declaration_provenance_note`.

The time interval must be positive and explicit. The site coordinate must identify the site whose pressure/elevation source will be selected. A receptor coordinate, ERA5 nearest-grid coordinate, or test-request coordinate may only be reconciled to the declared site through an explicit mapping; none is silently authoritative.

## Selection rule after declaration

After an admissible production-case declaration exists, R3 source precedence remains unchanged:

1. explicit case-mean near-surface atmospheric pressure with full provenance;
2. otherwise pressure derived from an independently sourced `site_elevation_m_msl` using the frozen FAO-56 relation.

R4 does not authorize source selection before the declaration is independently bound.

## Non-decisions

R4 does not:

- modify `docs/v4/contracts/v4_production_case_input_manifest_r1.yaml`;
- promote historical test coordinates;
- choose a real scenario or operational mode;
- download or bind meteorology;
- choose a site elevation;
- compute a production gamma value;
- add runtime adapters;
- change Eq.39, root, soil, leaf, OBT, food, intake, or dose physics;
- activate parameters;
- start calibration;
- unblock CTEAS-Atmos surface flux.

## Next stage

After a clean exact-head merge, the only authorized continuation is `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R5`, restricted to `INDEPENDENT_PRODUCTION_CASE_DECLARATION_INTAKE_ONLY`.

R5 may record an independently supplied production-case declaration against the frozen binding packet. It may not infer missing declaration fields from historical test artifacts and may not project quantities into the production manifest or runtime until separately reviewed.
