# Advanced re-emission validation closure plan

```text
LIMITATION = M_REEM_MANUAL_FIDELITY
VAL_REEM_RAIN_START_3_PERCENT = PARTIAL
VAL_REEM_CONCENTRATION_DEPENDENT_DIFF = PARTIAL
CANDIDATE_MODEL_CHANGE = NONE
```

## Frozen manual anchors

The primary source is `ufotri_manual.md`. The reviewed text states that the
initial no-insolation diffusive rate is 1% h-1, decreases with time after
release to represent the atmosphere-soil concentration difference, and is
modified for soil water content. The manual input table states a rain
re-emission starting rate of 3%, also decreasing with time. These statements
are anchors, not yet a complete executable relation: the exact state
transition at rain start and the full concentration/water modifiers must be
mapped before implementation.

## Independent calculations to freeze

### `VAL_REEM_RAIN_START_3_PERCENT`

For an initial available surface activity \(I_0\), the first independent
anchor is:

\[
Q_{\mathrm{rain,start}} = 0.03 I_0
\]

The final test vector must specify whether the 3% is an instantaneous boundary
loss, an hourly fractional rate, or a first-hour integrated loss, based on the
manual program description rather than inference. It must then independently
reconstruct initial inventory, rain input, re-emission boundary, decay and
final inventory.

### `VAL_REEM_CONCENTRATION_DEPENDENT_DIFF`

The test grid will vary soil-water HTO concentration, atmospheric HTO
concentration, soil-water content and elapsed time. It must establish:

- the manual equilibrium/direction convention;
- the exact DIFF concentration-difference term;
- the water-content modifier;
- the time-decrease term;
- units before percent-per-hour conversion;
- zero flux at the declared equilibrium, if the manual relation requires it.

Independent expected values must be computed without calling the candidate
reemission function.

## Candidate comparison and implementation decision

The current advanced candidate rate is compared against the frozen vectors,
with activity, relative difference and flux direction reported. Until the
manual mapping is complete, differences are `DOCUMENTED_LIMITATION`, not model
defects silently repaired in the released candidate.

After the mapping is frozen, choose one of:

1. a new explicit `ufotri_manual_advanced` mode if semantics differ;
2. a compatibility correction if the current mode is explicitly intended to
   implement the same manual relation;
3. retention as a project extension with a clear non-UFOTRI label.

Any model change occurs after candidate release, receives new conservation and
manual-anchor tests, and requires independent review. Status cannot exceed
`PARTIAL` before the complete mapping and independent vectors exist; it cannot
be empirically validated without external re-emission observations.
