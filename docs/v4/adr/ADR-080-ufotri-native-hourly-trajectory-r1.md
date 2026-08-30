# ADR-080 — UFOTRI Native Hourly Trajectory R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1`

## Context

H1 restored the directly recoverable UFOTRI-native Gaussian primary-atmosphere core, but intentionally stopped before the time-varying MUSEMET trajectory. The post-G4 authoritative correction therefore authorizes H2 before any native forcing adapter or atmospheric-process extension.

Primary sources are KfK 4605 Section 2.1 and KfK 4332, *UFOMOD - atmospheric dispersion and deposition* (1989), especially the MUSEMET model fundamentals and Appendix C TRAJEC description. These sources establish the following recoverable semantics:

- hourly wind direction and speed are taken from one meteorological station representative of the source region;
- one trajectory starts at the source at each hourly start time;
- meteorological conditions are homogeneous within an hourly interval;
- a trajectory is a sequence of straight segments, with later-hour wind changes bending the trajectory rather than rotating already-computed upstream segments;
- successive horizontal coordinates relative to a source-fixed Cartesian system are retained;
- stability, precipitation and mixing-layer state follow the hourly segment;
- travel time and the maximum source distance are explicit termination controls.

KfK 4332 describes MUSEMET as a segmented plume model and separately describes RIMPUFF as a puff model. H2 must therefore not replace the required segmented-trajectory semantics with a multiple-puff implementation.

## Decision

Add the isolated module:

`src/cteas_ufotri/atmosphere/ufotri_native_trajectory_v4.py`

The module introduces a pure, deterministic trajectory layer over hourly source-region meteorology. It does not yet calculate environmental forcing or revise the H1 dispersion/deposition process formulas.

### Meteorological contract

`NativeHourlyMeteorology` requires:

- timezone-aware UTC hourly start;
- one explicit `station_id` shared by the full sequence;
- meteorological wind direction in degrees **FROM** north, clockwise;
- wind speed at the atmospheric-transport height used by the caller;
- Pasquill stability class A-F;
- precipitation intensity;
- mixing-layer height.

Records must be consecutive one-hour intervals. Spatially varying meteorology is outside the MUSEMET H2 contract.

### Coordinate convention

The canonical implementation frame is source-relative east/north. Meteorological FROM direction is converted to the downwind TO vector. An optional rigid Cartesian rotation exists only to test representation invariance; it is not a new physical input and no claim is made that east/north reproduces an unavailable original internal axis orientation.

### Segmented trajectory semantics

For a trajectory beginning at hourly record `i`:

1. the initial coordinate is the source `(0, 0)`;
2. record `i` advances the first straight segment;
3. record `i+1` advances the next segment from the already-computed endpoint;
4. later wind changes never modify earlier endpoints;
5. each segment retains the meteorology that advanced it.

`build_musemet_hourly_trajectory_family()` starts one independent trajectory at each hourly source time. There is no particle or puff collection.

### Termination

H2 supports explicit:

- `max_travel_time_s`;
- `max_source_distance_m`.

The source-distance boundary is radial distance from the source, not cumulative curved path length. If a straight hourly segment crosses that boundary, the segment is truncated at the line/circle intersection. This matches the source-distance/predefined-area role described for TRAJEC more closely than using travelled arc length.

### Restart

A checkpoint records the source start, next hourly meteorology index, current source-relative coordinate, elapsed time, cumulative path length and coordinate frame. Restart is permitted only on an hourly meteorology boundary. Qualification requires direct and restarted trajectories to match exactly within floating-point representation.

## Non-decisions / forbidden claims

H2 does not:

- implement a multiple-puff model;
- use CTEAS-Atmos wind fields;
- introduce spatially heterogeneous meteorology;
- rotate all released material when a later wind direction changes;
- close H3 HT/HTO forcing adapters;
- close H4 source depletion, washout, building wake or thermal lift;
- claim original MUSEMET executable numerical equivalence.

The KfK 4605 atmospheric HT→HTO exclusion from H1 remains unchanged.

## Acceptance

H2 may be marked `COMPLETE` only after:

- the machine gate returns `PASS_UFOTRI_NATIVE_HOURLY_TRAJECTORY`;
- focused pytest passes;
- exact-head Remediation CI passes;
- exact-head Protected CI passes;
- the merge is locked to the certified head;
- candidate tree / merge tree / remote main no-drift audit passes.

After clean closure the only authorized next native-atmosphere stage is:

`UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1`.
