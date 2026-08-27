# V4 development completeness review R1

## Verdict

`PASS_NO_MANDATORY_INTERNAL_BLOCKERS`

With real production-input binding and real CTEAS-Atmos binding explicitly deferred from the present development phase, the selected V4 controlled baseline has no remaining mandatory internal software or selected-physics implementation blocker before RC entry.

## Reviewed chain

The review follows the project north-star software path from controlled atmospheric input to dose and checks whether every selected internal boundary has an implemented, fail-closed and tested software owner.

### Contracts and input ownership

V4 already has explicit time/unit/provenance contracts and replay input ownership. Silent spatial reconciliation, hidden area conversion, pre-populated deposition/root slots and provenance collapse are rejected at the orchestration boundary.

### Three-layer soil

The selected soil geometry is implemented as 0–5, 5–15 and 15–30 cm layers. Each layer owns water and HTO inventory. The core exposes signed inter-layer transport, surface/lower/root/re-emission boundaries, exact timestamp matching, per-layer/global conservation ledgers and restart serialization. It intentionally does not derive full hydrology.

### Root pathway

The root flux identity is implemented as `J_root,i = q_w,i C_w,i`. The later Eq.39 stage resolves the controlled construction of total root-water uptake, and the adopted 20/40/40 profile distributes total uptake across the three layers. The earlier isolated root-core report's external-qw limitation is therefore superseded for the selected controlled path; it is not a current mandatory blocker.

### Leaf, TFWT and OBT

The baseline resistance chain is connected and reaches TFWT. Dynamic stomatal Leaf R5 remains evidence-blocked rather than implementation-required. TFWT and the reduced UFOTRI OBT baseline participate in the selected orchestration using `PRESERVE_V3_POST_OBT_ROOT_GAIN`.

### Coupled orchestration

The soil-root-TFWT-OBT integrator has passed root-plan identity, plant/soil/coupled balance, deterministic repeat and restart-equivalence gates. Replay orchestration adds atmospheric deposition/leaf exchange with explicit ownership and has passed its software-integration machine gate.

### Food, intake and dose

The endpoint adapter composes terminal harvest, food transfer, annual intake and dose without mutating upstream environmental state or silently converting mass/area bases. `KEEP_HARVEST_EVENT` remains the selected boundary.

### Controlled full-chain execution

The controlled UFOTRI numerical integration exercises replay atmosphere + explicit net radiation → Eq.39 → 20/40/40 → leaf/soil/root → TFWT → reduced OBT → harvest → intake → dose with deterministic repeat, restart equivalence, conservation and identity gates.

## Mandatory-blocker decision

No reviewed domain requires a new internal physics subsystem before a development RC. The mandatory internal blocker count is therefore:

`0`

The following remain explicitly non-blocking extensions:

- Leaf R5 dynamic stomatal model;
- full Richards/Darcy hydrology;
- multi-pool OBT;
- UFOTRI short-term ~3 h delay;
- Penman Eq.38 aerodynamic term.

Their scientific relevance is not denied. They are simply not required for the selected controlled V4 development baseline, and no current evidence authorizes promoting them into mandatory work.

## Deferred boundaries

The review intentionally excludes real production-input binding and real CTEAS-Atmos binding because both are deferred to later phases. It also does not claim calibration, empirical validation, physical accuracy or production readiness.

The following remain false:

```text
FULL_MODEL_PRODUCTION_READY = FALSE
PRODUCTION_INPUT_PACKET_READY = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
CALIBRATION_STARTED = FALSE
ACTIVE_PARAMETERS = 0
V3_DEFAULT_PATH_CHANGED = FALSE
```

## Next stage

The only remaining mandatory internal development stage is:

`V4_DEVELOPMENT_BASELINE_RC1`

RC1 is a combined regression and freeze stage. It must certify the already selected baseline; it must not add another physics subsystem merely to increase completeness.
