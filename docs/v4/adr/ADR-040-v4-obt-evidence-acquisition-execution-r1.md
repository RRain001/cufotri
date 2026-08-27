# ADR-040: V4 OBT evidence acquisition execution R1

Status: `PASS_EXECUTION_CONTROL_EXACT_HEAD_AWAITING_CLOSURE_GATE`

## Context

PR #36 merged at `ca77d8abf4d7babe2669aa829f028e4ac45f653d` after closure exact-head Protected and Remediation success. The merge has parent1 `d28695a13eae1fe4a7afb55a7a8a179d366de44c`, parent2 `acfd0f087b3a05d414a55a1d3a480eee8223a83b`, and tree `2be97abe215c365bd496123719ac99863bccb210`. The locked PR head has the same tree and head-to-merge comparison has no files, so `MERGE_TREE_DRIFT=FALSE`.

That no-drift merge authorizes only `V4_OBT_EVIDENCE_ACQUISITION_EXECUTION_R1`: external request execution and metadata-only intake under the frozen preregistration. It does not authorize Option-B implementation, quantitative fitting, parameter activation, current `kf/kr` recalibration, holdout-value inspection, Leaf R5, root `q_w` activation, full hydrology or real CTEAS-Atmos binding.

## Decision

R1 starts with an auditable execution-control head before any external message is sent. This head:

- binds execution to the exact no-drift PR #36 merge;
- preserves the frozen request package unchanged;
- resolves public contact routes without silently treating historical addresses as current;
- prepares provider-specific request text derived from the frozen package;
- records `REQUESTS_SENT=FALSE` and `RAW_PACKET_RECEIVED=FALSE` truthfully;
- requires a certified execution head before an external send is recorded;
- keeps every received raw byte outside Git and permits only metadata/schema/checksum manifests in tracked files.

This execution-control head is not a new scientific preregistration layer and does not change the observation operator, acceptance rules, holdout policy or identifiability requirements frozen by PR #36.

## First exact-head certification

The valid first execution-control exact head is `15f3e4be9e03cf9ff49fe1a1fe1b0a516de628a5`.

- Protected run `33045107295`: `SUCCESS`.
- Remediation run `33045107285`: `SUCCESS`.
- Protected checkout merge ref: `d20da58ac9721d5703ade8bcc5807453596466c7`.
- portable suite: `1311 passed, 1 skipped, 57 deselected`.
- frozen/current-boundary suite: `373 passed`.
- sensitivity screening: `PASS_SOFTWARE_SCREENING`.
- root operator split: `PASS_SELECTION`.
- soil-root-TFWT-OBT integration: `PASS_INTEGRATION`.
- replay orchestration: `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`.
- food-intake-dose endpoint: `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.

The earlier head `f92b2e962acbc4c6cedfe4a1bd872b53cd084f9c` is retained only as `SUPERSEDED_NON_CERTIFYING_HEAD`. Its Protected run failed one newly added governance test because the expected sentence contained an unnecessarily exact wording variant. The follow-up commit changed only that assertion (`+1/-1` in one test file). The obsolete failure is not scientific, production, numerical-coupling or regression evidence and is not used for certification.

The certified first-head condition is now satisfied, but this governance/status closure must pass its own exact-head Protected + Remediation gates and merge without tree drift before the PR is treated as closed on `main`.

## Contact-route audit

### Priority A — VATO / former IRSN-EDF programme

Current ASNR research pages still identify the VATO programme and name Séverine Le Dizès-Maurel as a contact. Historical peer-reviewed records expose `denis.maro@irsn.fr`, `severine.ledizes@irsn.fr` and related former IRSN addresses. Because IRSN has since been reorganized into ASNR, those historical addresses are retained only as provenance and are not asserted to be current deliverable routes.

Execution state: `CURRENT_INSTITUTION_ROUTE_FOUND_DIRECT_ADDRESS_NOT_REVERIFIED`.

### Priority B1 — MicroTom / Kyushu University

The SSRN record identifies Michael Ofotsu Portuphy as contact author and Kyushu University as the study affiliation. Current Kyushu laboratory pages list Portuphy as staff and Kazunari Katayama as the responsible laboratory professor. A recent IAEA record and Kyushu publication metadata provide the current direct laboratory route `katayama.kazunari.947@m.kyushu-u.ac.jp`.

Execution state: `CURRENT_DIRECT_LAB_ROUTE_VERIFIED_REQUEST_NOT_SENT`.

### Priority B2 — Renard ryegrass

The 2017 PubMed record identifies Hugo Renard as corresponding author at IRSN and gives the historical address `hugo.renard@irsn.fr`. Current ASNR pages retain the associated VATO research lineage, but a current direct Hugo Renard institutional address has not been independently verified.

Execution state: `HISTORICAL_CORRESPONDING_ROUTE_FOUND_CURRENT_ROUTE_NOT_REVERIFIED`.

## Send boundary

No request is claimed sent merely because an address or template exists. A send event must record target, exact recipient route, UTC timestamp, subject/message identity and channel. If the route is historical or ambiguous, the request remains unsent until a current institutional route is verified.

Provider replies may be recorded immediately, but received raw files must be stored in Git-ignored external storage and hashed before any content inspection. Only filenames, checksums, schema/field names, units, timestamps/support, run/replicate IDs, analytical-method metadata, uncertainty/detection-limit metadata, quality/missing flags and licence/use terms may enter the Layer-B metadata-only review.

## Hard invariants

```text
REQUESTS_SENT = FALSE
RAW_PACKET_RECEIVED = FALSE
QUANTITATIVE_MODEL_FIT_INSPECTION = FALSE
HOLDOUT_VALUES_INSPECTED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED = FALSE
OBT_PARAMETER_ACTIVATION_AUTHORIZED = FALSE
CURRENT_KF_KR_CALIBRATION_AUTHORIZED = FALSE
LEAF_R5_AUTHORIZED = FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED = FALSE
FULL_HYDROLOGY_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
```

## Next transition

After this closure passes its own exact-head Protected + Remediation CI and merges with `expected_head_sha` plus parent/tree/main/head-to-merge no-drift verification, request execution may proceed only on a currently verified route. The first send may update the execution registry to `REQUEST_SENT_AWAITING_RESPONSE`; it still does not authorize quantitative inspection or model fitting.
