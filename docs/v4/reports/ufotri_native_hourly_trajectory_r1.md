# UFOTRI Native Hourly Trajectory R1

Stage: `UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1`

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Base: `main@e36288b7423892119d0027b848e647af6e3cc2f5`

## 1. Purpose

H2 closes the recoverable *trajectory kinematics* missing after H1. It does not yet produce the typed environmental forcing required by H3 and does not alter H1 dispersion/deposition process equations.

## 2. Authority

The reconstruction uses:

- KfK 4605 Section 2.1;
- KfK 4332, *UFOMOD - atmospheric dispersion and deposition*, MUSEMET model fundamentals;
- KfK 4332 Appendix C description of TRAJEC.

The source material supports a segmented Gaussian trajectory model driven by hourly wind speed/direction from one source-region meteorological station. A new trajectory is initiated at the source for each hourly start time. Horizontal trajectory coordinates and the corresponding hourly weather state are retained until the trajectory leaves the user-defined domain/travel-time window.

## 3. Implemented H2 path

New isolated module:

`src/cteas_ufotri/atmosphere/ufotri_native_trajectory_v4.py`

The module provides:

- `NativeHourlyMeteorology` with explicit UTC/station/wind/stability/precipitation/mixing-lid state;
- meteorological `FROM` wind-direction conversion to a downwind transport vector;
- one source-started segmented trajectory for any hourly start index;
- one trajectory family member for every hourly start time;
- unchanged historical segments when a later hour bends the path;
- per-segment attached meteorological state;
- explicit travel-time termination;
- exact straight-segment intersection with a radial maximum-source-distance boundary;
- deterministic hourly-boundary restart checkpoints;
- rigid coordinate-frame rotation for representation-invariance qualification.

## 4. Source-distance decision

KfK 4332 Appendix C describes a maximum source distance / predefined area and stores horizontal coordinates relative to the source. H2 therefore interprets the maximum-distance boundary as radial distance from the source rather than cumulative path length along a bent trajectory.

This matters after a wind-direction change: cumulative travelled distance may exceed radial source distance. The implementation keeps both quantities and uses only radial distance for the termination boundary.

## 5. Wind-direction contract

H2 does not leave direction convention implicit.

Input is meteorological direction **from** which the wind blows, clockwise from north. The physical downwind direction is the opposite vector. The canonical source-fixed representation uses x east and y north. This absolute axis orientation is an implementation coordinate convention only; it is not presented as recovered original MUSEMET internal-axis metadata.

The optional frame rotation is a pure rigid rotation. Qualification requires source distance and cumulative path length to remain invariant.

## 6. Restart semantics

A checkpoint is valid only on an hourly meteorology boundary and preserves:

- original trajectory start;
- original meteorology start index;
- next meteorology record;
- current time and coordinates;
- elapsed time;
- cumulative path length;
- segment count;
- station identity;
- coordinate-frame rotation.

A direct 3.5 h trajectory is compared with a 2 h prefix plus resumed continuation. Segment signatures and final state must agree.

## 7. Explicit non-claims

H2 does not establish:

- multiple-puff physics;
- spatially heterogeneous meteorology;
- CTEAS-Atmos coupling;
- H3 native HT/HTO forcing adapters;
- H4 original MUSEMET source-depletion discretisation;
- H4 HTO washout coefficient recovery;
- building-wake fidelity;
- thermal-lift fidelity;
- atmosphere-to-dose end-to-end qualification;
- original MUSEMET or UFOTRI executable numerical equivalence.

The KfK 4605 rule `ATMOSPHERIC_HT_TO_HTO_CONVERSION=DISABLED` remains unchanged.

## 8. Candidate validation

Focused qualification checks:

- machine gate expected: `PASS_UFOTRI_NATIVE_HOURLY_TRAJECTORY`;
- west wind (`FROM 270°`) advances east;
- south wind (`FROM 180°`) advances north;
- changing from west wind to south wind creates an L-shaped path and does not rewrite segment 1;
- segment stability/precipitation/mixing lid match the advancing hourly record;
- trajectory family starts every member at `(0,0)` at its own hourly source time;
- travel-time partial-hour termination is explicit;
- curved-path maximum source distance closes on the radial boundary, not cumulative path length;
- coordinate rotation preserves radial and path-length invariants;
- direct and restarted paths match;
- mixed station IDs and nonconsecutive hourly records fail closed.

Stage completion remains contingent on exact-head CI, locked merge and post-merge no-drift audit.

## 9. Next stage

After clean H2 closure:

`UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1`

H3 must consume the H1/H2 native atmosphere without aliasing HT and HTO and must map native air/deposition products into the already-qualified environmental contracts.
