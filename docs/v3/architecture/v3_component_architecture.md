# V3 component architecture

Status: `ARCHITECTURE_ONLY`

| Layer | Components | Owns | Must not own |
|---|---|---|---|
| Core contracts | state, flux, ledger, units, versions | immutable definitions | case execution |
| Input contracts | forcing, source, parameters | validated manifests | hidden defaults |
| Transport | atmosphere, depletion, deposition | air diagnostics and boundary transfer | soil/food state |
| Environmental media | surface allocation, soil, plant | media inventories and internal transfer | dose mutation |
| Consumption | food, animal | product inventories and boundaries | atmospheric transport |
| Consequence | dose | dose accumulation | environmental activity mutation |
| Evidence | validation, calibration, holdout | comparisons and claims | production physics |
| Reproducibility | configuration, result, provenance | hashes and versions | numerical feedback |

Every numerical component consumes typed state/flux records and returns new
records plus a module ledger. A coordinator may order components, but modules
cannot import or mutate the coordinator.

Candidate implementations use a registry lookup by `module_id` and
`module_version`. Unknown or disallowed combinations fail closed. The current
registry contains architecture metadata only and dispatches no V3 physics.
