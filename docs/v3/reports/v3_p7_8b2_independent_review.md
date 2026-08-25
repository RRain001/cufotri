# V3 P7.8B-2 Independent Review

Review type: physics-selection control-plane, architecture, coupling, and
validation-dependency review
Review status: `PASS_PHYSICS_SELECTION`
Review boundary: selection and future planning only; no implementation or
physical-validation claim

## Review checklist

| # | Review question | Verdict | Evidence |
|---:|---|---|---|
| 1 | Does the registry trace to P7.8A/P7.8B-1? | PASS | All nine redesign records, two deferred records, external consumption/dose boundaries, and rejected shortcuts are represented. |
| 2 | Does every decision have the required schema fields? | PASS | Each registry item includes current model, candidates, selection, reason, basis, advantages, limitations, states, parameters, validation, coupling, stage, and status. |
| 3 | Is selection separated from implementation? | PASS | Selection control-plane flags keep equations unimplemented, parameters valueless, implementation unauthorized, and active count zero. |
| 4 | Is the OBT decision explicit? | PASS | Option A remains the baseline; Option B is selected for V4; organ-specific Option C is rejected as the first target. |
| 5 | Are all root candidates compared? | PASS | Effective velocity is the baseline, water-flux coupling is selected for V4, and standalone moisture response is rejected. |
| 6 | Is the soil decision conservative? | PASS | Signed transport remains current; layered/full hydrology is explicitly insufficient evidence and is not inferred. |
| 7 | Is the leaf decision dimensionally bounded? | PASS | Dynamic conductance is selected only as a V4 interface extension; reciprocal resistance units and response domains are required. |
| 8 | Is TFWT water turnover kept separate from activity loss? | PASS | Fixed storage remains current; dynamic water turnover is unresolved and growth correction is rejected. |
| 9 | Is food transfer separated from consumption and dose? | PASS | Harvest-event environmental transfer, external consumption, and external dose are selected/maintained independently. |
| 10 | Are future coupling impacts explicit? | PASS | Root uptake is a required numerical-coupling change; interface, pipeline, and no-impact states are separately classified. |
| 11 | Is implementation order frozen without starting it? | PASS | V3.1 contract first, then V4 data/state contracts, leaf, OBT, and root; implementation flags remain false. |
| 12 | Are validation dependencies actionable? | PASS | Required datasets, observables, metrics, case contracts, and blocking risks are mapped per selected/maintained boundary. |
| 13 | Are P7.5/P7.5B semantics protected? | PASS | No production coupling source is changed; root future work has a hard coupling-review gate. |
| 14 | Can any selected decision activate a parameter directly? | PASS | Direct transitions to `ACTIVE_PARAMETER` are forbidden; no selected parameter has a value. |
| 15 | Does the decision preserve V3 readiness boundary? | PASS | `V3_PHYSICS_READY = FALSE`; the synthetic benchmark is not promoted to empirical validation. |

## Scientific findings

1. The two-pool OBT package is the preferred future direction because it
   addresses the largest formation/turnover ambiguity with fewer states than
   an organ-allocation model. Its rates and forcing functions remain
   unidentified.
2. Water-flux-coupled root uptake is preferable to guessed velocity scaling,
   but it necessarily changes numerical state ownership and therefore cannot
   be implemented without a P7.5/P7.5B review.
3. Dynamic leaf resistance is a bounded interface extension, not a current
   solver change. The response functions need matched exchange data.
4. Soil hydrology, TFWT water turnover, and continuous/hybrid food transfer
   remain unresolved. Keeping them out of the V4 order is evidence control,
   not an assertion that they are scientifically unimportant.

## Boundary findings

- The current profile remains the only runnable V3 profile.
- No UFOTRI value, inferred conversion, calibration, or empirical claim was
  added.
- Consumption and dose cannot drive environmental-physics selection.
- Rejected shortcuts remain rejected even when they would reduce implementation
  effort.

## Review limitations

This review does not establish that a selected candidate is the UFOTRI model,
does not validate a parameter, and does not authorize P7.8C code. It is based
on the P7.8A/P7.8B-1 control-plane records and the explicit P7.8B-2 scope. A
future implementation review must re-check all equations, units, data, and
coupling assumptions against the then-current repository and evidence.

## Verification target

The associated governance test must verify registry completeness, expected
selection states, value-free parameters, roadmap order, validation dependency
coverage, artifact isolation, and unchanged production paths. A passing test
is repository governance evidence only.
