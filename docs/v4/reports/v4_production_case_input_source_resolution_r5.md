# V4 production-case input source resolution R5 report

## Outcome

`DECLARATION_NOT_RECEIVED_FAIL_CLOSED`

R5 was opened only to establish the independent production-case declaration intake boundary required by R4. No independent production declaration artifact is present at base `59055c22a44795ad3ef45228fe2816510478d8c5`, so R5 does not bind a site, time window, operational case, pressure source, site elevation or psychrometric constant.

## Frozen intake contract

`PRODUCTION_CASE_IDENTITY_DECLARATION_INTAKE_R1` requires thirteen explicit fields: case/scenario identity, facility/site identity, location identity, latitude/longitude, horizontal CRS or datum, production start/end UTC, operational/release case, declaration source ID/revision and provenance note.

Current receipt state is `NOT_RECEIVED`; all thirteen declared values are null. Validation has not been performed because there is no independent artifact to validate.

## Fail-closed rules

Historical ERA5 requested coordinates, ERA5 nearest-grid coordinates, software request labels, assumptions/test constants, synthetic configurations, receptor height and Atmos air-sampling height cannot fill missing declaration fields. Conversational or project background that has not been supplied as an explicit controlled declaration artifact is likewise not promoted automatically.

The allowed intake transition is:

`DECLARATION_NOT_RECEIVED` → `DECLARATION_RECEIVED_UNVALIDATED` → either `DECLARATION_ACCEPTED_FOR_SOURCE_RESOLUTION`, `DECLARATION_REJECTED_INCOMPLETE`, or `DECLARATION_REJECTED_AMBIGUOUS`.

Even `DECLARATION_ACCEPTED_FOR_SOURCE_RESOLUTION` does not itself modify the production manifest or select Eq.39 pressure/elevation/gamma.

## Repository mutations

R5 changes only:

- one ADR;
- one machine-readable governance file;
- this report;
- one governance test.

R5 changes no `src/` file, production manifest, solver equation, numerical coupling, workflow, runtime parameter import or calibration state.

## Frozen production states

- `PRODUCTION_CASE_IDENTITY_BOUND=FALSE`
- `PRODUCTION_PRESSURE_SOURCE_SELECTED=FALSE`
- `PRODUCTION_SITE_ELEVATION_SOURCE_SELECTED=FALSE`
- `PRODUCTION_PSYCHROMETRIC_CONSTANT_AVAILABLE=FALSE`
- `EQ39_PRODUCTION_INPUT_READY=FALSE`
- `PRODUCTION_INPUT_PACKET_READY=FALSE`
- `FULL_MODEL_PRODUCTION_READY=FALSE`
- `ACTIVE_PARAMETERS=0`
- `CALIBRATION_STARTED=FALSE`
- `OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED=FALSE`
- `OBT_PARAMETER_ACTIVATION_AUTHORIZED=FALSE`
- `CURRENT_KF_KR_CALIBRATION_AUTHORIZED=FALSE`
- `LEAF_R5_AUTHORIZED=FALSE`
- `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=FALSE`
- `FULL_HYDROLOGY_AUTHORIZED=FALSE`
- `REAL_CTEAS_ATMOS_BINDING=FALSE`
- `EMPIRICAL_VALIDATION=FALSE`
- `PHYSICAL_ACCURACY_CLAIM=FALSE`

Atmos surface deposition flux remains `BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED`.

## Conditional handoff

R6 must not be created merely to advance stage numbering. Only an accepted independent declaration permits `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R6`, whose scope is limited to production-case identity binding and case-specific Eq.39 pressure/elevation source resolution. Manifest projection, solver change, runtime activation and production activation remain unauthorized by R5.
