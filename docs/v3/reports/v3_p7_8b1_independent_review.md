# V3 P7.8B-1 Independent Review

Review type: control-plane specification completeness, equation dimensionality,
compatibility, coupling, and governance review
Review status: `PASS_REDESIGN_SPECIFICATION`
Review boundary: candidate design artifacts only; no implementation or
physical-validation claim

## Review checklist

| # | Review question | Verdict | Evidence |
|---:|---|---|---|
| 1 | Does the specification trace to P7.8A priorities? | PASS | Nine redesign IDs and two deferred IDs are represented in the specification registry |
| 2 | Does every specification include the required schema fields? | PASS | `current_model`, `current_equation`, gap, scientific requirement, candidate model, states, parameters, interfaces, coupling, validation, complexity, priority, and decision are present |
| 3 | Are candidate equations distinguished from implemented equations? | PASS | Registry flags `candidate_equations_are_implemented = false` and every candidate has `equation_status` |
| 4 | Are candidate parameters value-free and runtime-isolated? | PASS | Parameters are symbolic names/descriptors with `CANDIDATE_NOT_ADMITTED` or contract-only status; no numerical values are recorded |
| 5 | Is the OBT Option A/Option B decision explicit? | PASS | Reduced first-order baseline, two-pool candidate, and organ-specific research option are separated |
| 6 | Are root effective-velocity, water-flux, and moisture-dependent options evaluated? | PASS | Options A/B/C are recorded with units, data requirements, and coupling implications |
| 7 | Is soil transport conservative and boundary-aware? | PASS | Layer candidate uses incoming/outgoing interface fluxes plus explicit root/evaporation terms and requires layer data |
| 8 | Is leaf resistance preserved as a compatibility baseline? | PASS | `r_a + r_b + r_c` and reciprocal `g_ex` remain the default; dynamic stomatal response is opt-in |
| 9 | Is TFWT water turnover separated from activity loss? | PASS | Candidate introduces explicit water mass `W` and concentration `C_T`; no hidden dilution factor is proposed |
| 10 | Are food OBT and TFWT product states separated? | PASS | Separate continuous/hybrid candidate equations and product-water state requirements are specified |
| 11 | Are coupling states and affected modules complete? | PASS | All four P7.8B-1 coupling states are used in the specification/baseline matrix |
| 12 | Can a specification activate a parameter directly? | PASS | Direct transitions to `ACTIVE_PARAMETER` are forbidden and implementation authorization remains false |
| 13 | Are P7.5/P7.5B semantics protected? | PASS | No current numerical-coupling or pipeline source is changed; future root/soil/food work requires separate review |

## Scientific findings

The OBT two-pool candidate is the most informative biological extension, but
its activity, day/night, temperature, and pool-scope functions remain
unidentified without matched time-resolved data. The root water-flux option is
scientifically preferable to a guessed velocity conversion, but it is a
numerical state redesign. Soil hydrology and TFWT water turnover are deferred
because their water-balance boundaries are not yet evidenced. Food transfer
must be redesigned as a plant-product state/event question and cannot be
selected from downstream dose behavior.

## Review limitations

This review does not establish that any candidate equation is the UFOTRI
equation, does not validate any parameter, and does not authorize code. A
future P7.8B2 implementation requires a new equation-selection record and an
independent review of the selected model.

## Executed verification

The registry, reports, ADR, implementation-status update, and isolation
contract were checked with:

```text
PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/v3/test_p7_8b1_redesign_specification.py
```

The focused suite completed with `12 passed`; `git diff --check` passed. The
isolation test compares the branch against the P7.8A baseline and found no
plant, soil, exposure, pipeline, coupling, runtime, or parameter-runtime
source modification.
