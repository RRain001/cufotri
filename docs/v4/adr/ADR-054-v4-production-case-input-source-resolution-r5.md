# ADR-054: V4 production-case declaration intake R5

## Status

Accepted for exact-head certification on the R5 branch. This ADR is control-plane only and does not constitute a production-case declaration.

## Context

R4 closed with `BLOCKED_PRODUCTION_CASE_IDENTITY_NOT_INDEPENDENTLY_DECLARED`. The repository contains historical Hefei/ERA5 test coordinates and labels, but R4 explicitly classified those artifacts as test context rather than an independent production declaration. R3 also froze the Eq.39 pressure/elevation provenance contract: production pressure or site elevation cannot be selected until production case identity and temporal support are independently declared.

The current production manifest therefore remains `TEMPLATE_NOT_PRODUCTION / UNSET`. No independent declaration artifact containing the complete R4 binding packet is present at the R5 base.

## Decision

R5 is restricted to `INDEPENDENT_PRODUCTION_CASE_DECLARATION_INTAKE_ONLY`.

The intake contract is `PRODUCTION_CASE_IDENTITY_DECLARATION_INTAKE_R1`. It preserves the thirteen fields frozen by R4:

1. `case_id`
2. `scenario_id`
3. `facility_or_site_id`
4. `site_location_id`
5. `site_latitude_deg`
6. `site_longitude_deg`
7. `horizontal_crs_or_datum`
8. `production_time_start_utc`
9. `production_time_end_utc`
10. `operational_mode_or_release_case`
11. `declaration_source_id`
12. `declaration_source_revision`
13. `declaration_provenance_note`

At this revision no declaration has been received. All declaration values therefore remain null and the current transition token is `DECLARATION_NOT_RECEIVED`.

## Intake state machine

- `DECLARATION_NOT_RECEIVED` — no independent declaration artifact is available.
- `DECLARATION_RECEIVED_UNVALIDATED` — an independent artifact has been received but has not passed schema, identity, time-support and provenance checks.
- `DECLARATION_ACCEPTED_FOR_SOURCE_RESOLUTION` — all required fields are explicit, the time interval is positive, coordinate/datum semantics are explicit, and declaration provenance is traceable.
- `DECLARATION_REJECTED_INCOMPLETE` — one or more required fields are absent.
- `DECLARATION_REJECTED_AMBIGUOUS` — identity, coordinate/datum, time support or provenance semantics are ambiguous.

Acceptance at the intake boundary does **not** write values into the production manifest, select pressure/elevation, compute Eq.39 gamma, activate runtime parameters, bind real CTEAS-Atmos, start calibration, or authorize a physical-accuracy claim.

## Prohibited inference

The following cannot be used to fill missing declaration fields:

- historical ERA5 requested coordinates;
- ERA5 nearest-grid coordinates;
- software request labels;
- synthetic/test configurations;
- receptor height or Atmos sampling height;
- conversational/project background that has not been supplied as an explicit controlled production-case declaration artifact.

No missing field may be inferred merely to close the model chain.

## Current outcome

`DECLARATION_NOT_RECEIVED_FAIL_CLOSED`

Consequently:

- `PRODUCTION_CASE_IDENTITY_BOUND=FALSE`
- `PRODUCTION_PRESSURE_SOURCE_SELECTED=FALSE`
- `PRODUCTION_SITE_ELEVATION_SOURCE_SELECTED=FALSE`
- `PRODUCTION_PSYCHROMETRIC_CONSTANT_AVAILABLE=FALSE`
- `EQ39_PRODUCTION_INPUT_READY=FALSE`
- `PRODUCTION_INPUT_PACKET_READY=FALSE`
- `FULL_MODEL_PRODUCTION_READY=FALSE`

All standing V4 hard boundaries remain unchanged.

## Conditional next stage

Only after an independent declaration is received and accepted may the project enter `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R6`, limited to production-case identity binding and case-specific Eq.39 pressure/elevation source resolution. Manifest projection, runtime activation and production activation remain separate gates.
