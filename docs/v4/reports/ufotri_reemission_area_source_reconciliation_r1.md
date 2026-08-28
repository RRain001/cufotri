# UFOTRI re-emission/area-source reconciliation R1

Stage: `UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION_R1`

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

## Result

The recoverable internal UFOTRI secondary-source coupling semantics require an opt-in compatibility adapter. Existing legacy feedback code is retained unchanged because it provides useful historical topology but does not reproduce the manual-selected area-source approximation exactly.

Candidate decision:

- `NEW_OPT_IN_SOURCE_MODULE_REQUIRED=TRUE`
- `EXISTING_DEFAULT_SOURCE_CHANGE=FALSE`
- `LEGACY_RECTANGULAR_QUADRATURE_PROMOTED_TO_ORIGINAL_UFOTRI=FALSE`
- `EQ44_RATE_GENERATION_RECOVERED=FALSE`
- `REAL_CTEAS_ATMOS_BOUND=FALSE`
- `BENCHMARK_STARTED=FALSE`

## Manual reconciliation

The available KfK 4605 source supports the following F1 behavior:

- hour-N soil/plant states feed the secondary model in hour N+1;
- secondary releases are area sources;
- rectangular sources are preferred;
- the selected simplified representation is a centre point with initial lateral widening;
- Eq. (5): `sigma_yg = sqrt(sigma_y^2 + sigma_y0^2)`;
- `sigma_y0 = source_width / 4.3`;
- Eq. (6) is evaluated separately for soil and vegetation;
- soil/plant secondary concentrations are linearly superposed;
- soil and plant sources share an effective source height.

Phase A already recovered `FLQH=0.8H`, constrained to a minimum of 1 m, and exposes that geometry for this later coupling role.

## Historical-code disposition

The existing `run_short_case` route keeps a one-hour configurable feedback queue and adds secondary concentration to primary concentration. Its area-source branch performs direct rectangular midpoint quadrature, while its point-equivalent branch uses a ground-level point source. Default 1000 m × 1000 m geometry and 3600 s delay are project/historical settings.

These paths remain unchanged. They are not relabeled as the manual-selected Eq. (5)/(6) implementation.

## Candidate implementation

New opt-in module:

`src/cteas_ufotri/coupling/reemission_area_source_v4.py`

It provides:

1. `ManualAreaSourceGeometry` with explicit length, width and common source height;
2. reuse of the Phase-A `max(0.8H, 1 m)` area-source emission height;
3. exact recoverable Eq. (5) initial lateral widening;
4. controlled Eq. (6) centre-equivalent concentration with explicit fallout/washout multipliers;
5. separate soil and plant secondary sources and concentration superposition;
6. `AccountedReemissionLoss` and `HourlySecondarySource` records with a conservative activity handoff ledger;
7. `HourlyReemissionHandoffBuffer` implementing the recoverable 3600 s `N -> N+1` cadence without step-rounding;
8. fail-closed provenance requiring proof for `HT_DERIVED_HTO` and preserving mixed origin after aggregation.

## Conservation boundary

F1 does not generate environmental activity. The source handoff obeys:

`environmental loss activity = routed atmospheric activity + unrouted activity`.

For the current fully routed compatibility event, the unrouted term is zero. The same Bq removed from soil/plant is therefore the Bq handed to the secondary atmospheric source.

## Numerical qualification target

The stage-specific gate and pytest suite require:

- exact `width/4.3` Eq. (5) behavior;
- controlled literal Eq. (6) agreement;
- first-hour zero secondary forcing;
- next-hour routing of source-hour losses;
- identical hourly activity and source flux for 600 s and 300 s time steps under the same flux history;
- exact handoff-ledger closure;
- separate soil/plant concentration contributions and linear superposition;
- failure on invalid geometry, incompatible timestep and inconsistent activity ledger;
- rejection of unproven HT-derived attribution and preservation of mixed origin.

## Frozen boundaries

No candidate change is made to:

- `src/cteas_ufotri/case.py`;
- `src/cteas_ufotri/config.py`;
- `src/cteas_ufotri/atmosphere/gaussian.py`;
- `configs/default_parameters.yaml`;
- current RC1/V2/V3 default execution behavior.

## Remaining gaps

F1 does not recover the advanced Eq. (44) rate relation, rain-start/DIFF details, original MUSEMET/ISOLA executable numerics, real CTEAS-Atmos coupling, or benchmark validation. After a certified F1 merge and separate roadmap synchronization, the roadmap—not this candidate report—controls authorization of the Canada 1987 benchmark stage.

## Non-claims

This candidate is software/manual-fidelity reconstruction evidence only. It is not empirical validation, physical-accuracy evidence, production readiness, production calibration, or original-executable equivalence.
