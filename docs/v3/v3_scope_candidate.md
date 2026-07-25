# V3 scope candidate

## Status

This is an architecture-only candidate list under:

```text
V3_GATE_VERDICT =
READY_FOR_V3_ARCHITECTURE_ONLY_EXTERNAL_VALIDATION_CONTINUES
```

It is not an implementation plan and does not select every item for V3.

## Prioritized candidates

### 1. Long observed-forcing workflow

- **Evidence gap:** The candidate tag's 72-hour case used a deterministic third
  day; Phase 1 showed measurable downstream bias from that substitution.
- **Scientific value:** Makes forcing provenance and coverage explicit for
  longer post-release redistribution studies.
- **Required data:** Consecutive ERA5 or site meteorology with checksums, units,
  accumulation semantics, spatial metadata, and missing-hour policy.
- **Dependency:** Existing read-only acquisition and preparation adapter.
- **Risk:** Reanalysis may be mistaken for station or site HTO validation.
- **Validation method:** Coverage checks, raw-to-derived checksums, extension
  sensitivity, and comparisons against available site meteorology.
- **Backward compatibility:** Keep the frozen hybrid case and add explicit new
  forcing manifests; do not silently replace candidate inputs.
- **Candidate reproducibility:** Yes; the V2 tag and its input semantics remain
  unchanged.

### 2. External-evidence and calibration data model

- **Evidence gap:** No executable experiment/field case and no parameter
  identifiability result.
- **Scientific value:** Enforces preregistration, calibration/holdout separation,
  detection-limit handling, and non-identifiability reporting.
- **Required data:** Complete licensed soybean or equivalent experiment, or a
  co-located air-soil-plant field package with uncertainties.
- **Dependency:** External-data adapters, ignored raw-data paths, checksum
  manifests, and a frozen observable/unit schema.
- **Risk:** Overfitting, data leakage, parameter compensation, or falsely
  labeling reanalysis/model output as empirical evidence.
- **Validation method:** Independent repeats or a frozen calibration/holdout
  split; posterior/range, correlation, boundary-hit, and benchmark regression
  checks.
- **Backward compatibility:** Calibration packages must be optional overlays;
  V2 defaults and case values remain unchanged.
- **Candidate reproducibility:** Yes, if raw data remain external and every
  adapter/manifest is versioned.

### 3. Advanced re-emission manual-fidelity architecture

- **Evidence gap:** The candidate omits the UFOTRI rain-start 3% rule and
  concentration-dependent `DIFF` detail.
- **Scientific value:** Closes a known manual-fidelity gap that can affect
  post-deposition air and surface inventories.
- **Required data:** Reviewed equation mapping, dimensional contract, manual
  numeric anchors, and preferably a soil/re-emission experiment.
- **Dependency:** Explicit surface inventory ledger and the existing
  re-emission closure plan.
- **Risk:** Double counting, discontinuous rain-start activity, or breaking
  global conservation.
- **Validation method:** Independent hand calculation, rain-start impulse tests,
  concentration grid, time-step convergence, and full activity conservation.
- **Backward compatibility:** New mode must be opt-in; frozen V2 re-emission
  behavior remains selectable.
- **Candidate reproducibility:** Yes, with versioned mode semantics and the
  unchanged V2 tag.

### 4. Formal three-box soil coupling architecture

- **Evidence gap:** The conservative three-box solver is standalone and not
  coupled to the formal ecological pathway.
- **Scientific value:** Represents vertical water/activity transport and
  root-zone structure without collapsing every process into one box.
- **Required data:** Layer water/soil properties, root fractions, boundary
  fluxes, and calibration or benchmark evidence across layers.
- **Dependency:** Stable layer-state schema, explicit surface allocation, root
  uptake interface, and one-box degeneration contract.
- **Risk:** Hidden cross-layer mass loss, non-identifiable transport
  coefficients, and silent changes to legacy cases.
- **Validation method:** Layer and global ledgers, one-box limit, refinement
  convergence, unequal footprint tests, and a controlled soil/field case.
- **Backward compatibility:** The one-box V2 path remains the default; formal
  multibox coupling is a named opt-in mode.
- **Candidate reproducibility:** Yes, if V2 mode dispatch and configuration
  interpretation stay frozen.

### 5. Dynamic-air inventory architecture

- **Evidence gap:** V2 uses a steady Gaussian source-sink ledger and has no
  dynamic air inventory.
- **Scientific value:** Could support time-varying storage and re-emission
  feedback when a research case demonstrates the need.
- **Required data:** Time-resolved releases, meteorology and air HTO at adequate
  resolution, plus an independent transport reference.
- **Dependency:** A conservative state ledger and a documented coupling
  boundary between plume transport and environmental boxes.
- **Risk:** Large scope, poorly identifiable mixing/storage terms, double
  counting plume and box activity, and accidental replacement of the stable
  Gaussian baseline.
- **Validation method:** Analytic pulse/storage cases, inventory conservation,
  independent transport comparison, and matched air observations.
- **Backward compatibility:** Retain the V2 steady Gaussian mode exactly.
- **Candidate reproducibility:** Yes only as a new versioned mode; no candidate
  tag movement.

## Deferred candidates

- **Site-calibrated parameter packages:** subsumed under candidate 2 and blocked
  until a complete site package exists.
- **Experimental calibration modes:** architecture may be designed under
  candidate 2; no calibration algorithm should be promoted without executable
  data and holdout evidence.
- **HT chemistry:** excluded from the current V3 candidate scope because no
  explicit research question or external validation case requires it.
- **Broad food/animal expansion:** excluded until a process-specific external
  dataset and validation question are available.

## Stop boundary

The next phase may design interfaces and migration rules for these candidates.
It must not implement formal physics unless a subsequent gate reaches
`READY_FOR_V3_ARCHITECTURE_AND_BOUNDED_IMPLEMENTATION`.
