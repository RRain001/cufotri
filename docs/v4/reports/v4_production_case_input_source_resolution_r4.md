# V4 production-case input source resolution R4 report

Stage: `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R4`

Base main: `25e2b50e2096bfd3953a5f5fdc637b1f7eaee8b3`

Status: `BLOCKED_PRODUCTION_CASE_IDENTITY_NOT_INDEPENDENTLY_DECLARED_AWAITING_EXACT_HEAD_GATE`

## 1. Purpose

R3 froze the provenance contract for Eq.39 atmospheric pressure and MSL site elevation. R4 applies that contract to repository evidence and asks a narrower question: is there already an independently declared production case against which a real pressure/elevation source can be selected?

The answer is no. R4 therefore remains fail-closed and does not select a pressure, elevation, or gamma value.

## 2. R3 closure prerequisite

PR #49 merged as `25e2b50e2096bfd3953a5f5fdc637b1f7eaee8b3` from certified head `2d0c7f936237b739a2e8bf590838ff9f3f9da015`.

- parent 1: `9943613aafad43db4e0831547f5593d02b7044ce`;
- parent 2: `2d0c7f936237b739a2e8bf590838ff9f3f9da015`;
- certified-head tree: `1215bedd4dd26610d93f03c4e59cd617c2409aa9`;
- merge tree: `1215bedd4dd26610d93f03c4e59cd617c2409aa9`;
- head-to-merge changed files: none;
- remote main: `25e2b50e2096bfd3953a5f5fdc637b1f7eaee8b3`.

Therefore `MERGE_TREE_DRIFT=FALSE` for PR #49.

## 3. Production-case identity audit

The production manifest remains `TEMPLATE_NOT_PRODUCTION / UNSET` and contains no independently bound production case.

Repository search did find historical Hefei-related test context:

- requested ERA5 point: `117.141610855 E, 31.939774444 N`;
- returned nearest ERA5 grid point: `117.25 E, 32.00 N`;
- historical period: 2025-06-01 00:00 through 2025-06-02 23:00 UTC;
- software request label: `Hefei-H3-ERA5/1.0`.

These artifacts are not sufficient for production identity. `docs/assumptions.md` explicitly states that the short-case values are finite test values rather than site claims and that crop defaults are not claims about the Hefei receptor or a specific agricultural survey.

The requested coordinate is therefore frozen as `HISTORICAL_TEST_CONTEXT_NOT_PRODUCTION_BINDING`. The nearest ERA5 grid point is frozen as `METEOROLOGICAL_TEST_GRID_POINT_NOT_SITE_IDENTITY`. A software label is not an external or project-authoritative case declaration.

## 4. Pressure-source audit

The historical ERA5 audit documents the mapped variables:

`t2m`, `d2m`, `u10`, `v10`, `tp`, `ssrd`, `strd`.

Surface atmospheric pressure is not documented in that audit. R4 therefore cannot select a case-mean pressure source from the existing historical input, independent of the stronger production-identity blocker.

State:

- `selected_case_mean_atmospheric_pressure_source = null`;
- `explicit_pressure_path_ready = false`.

## 5. Site-elevation source audit

No independently sourced `site_elevation_m_msl` satisfying the R3 horizontal/vertical datum and transformation requirements was found in the repository.

State:

- `selected_site_elevation_m_msl_source = null`;
- `elevation_derived_pressure_path_ready = false`.

Consequently no production psychrometric constant is available.

## 6. Binding packet required to proceed

R4 freezes `PRODUCTION_CASE_IDENTITY_BINDING_PACKET_R1`. Before pressure/elevation source selection can occur, an independent declaration must provide:

- case and scenario identifiers;
- facility/site and location identifiers;
- site latitude/longitude and horizontal CRS/datum;
- production start/end in UTC;
- operational mode or release case;
- declaration source/revision/provenance.

The declared site must be the site for which pressure/elevation representativeness is assessed. Historical test coordinates, receptor coordinates, and ERA5 nearest-grid coordinates require explicit reconciliation and are never silently authoritative.

## 7. Frozen result

`BLOCKED_PRODUCTION_CASE_IDENTITY_NOT_INDEPENDENTLY_DECLARED`

This result means the source-selection process is behaving correctly. It is not a software failure and must not be bypassed by choosing convenient historical coordinates or test meteorology.

## 8. No activation or physics claim

R4 does not modify the production manifest, `src/`, workflow, solver equations, numerical coupling, runtime imports, or calibration state.

All hard boundaries remain false/zero, including:

- `PRODUCTION_INPUT_PACKET_READY=FALSE`;
- `FULL_MODEL_PRODUCTION_READY=FALSE`;
- `ACTIVE_PARAMETERS=0`;
- `CALIBRATION_STARTED=FALSE`;
- `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=FALSE`;
- `FULL_HYDROLOGY_AUTHORIZED=FALSE`;
- `REAL_CTEAS_ATMOS_BINDING=FALSE`;
- `EMPIRICAL_VALIDATION=FALSE`;
- `PHYSICAL_ACCURACY_CLAIM=FALSE`.

Atmos surface deposition remains `BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED`.

## 9. Next stage

If R4 passes exact-head gates and merges without drift, the only authorized next stage is `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R5`, restricted to `INDEPENDENT_PRODUCTION_CASE_DECLARATION_INTAKE_ONLY`.

R5 may record a genuinely independent production-case declaration. It may not infer missing declaration fields from test artifacts, project labels, or historical ERA5 requests, and it may not project source values into the production manifest/runtime until separately reviewed.
