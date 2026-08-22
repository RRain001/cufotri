# V3-P6.6B intake-to-dose assessment test report

Status: PASS_DOSE_ASSESSMENT_IMPLEMENTED

Branch: codex/v3-p6-6b-dose-assessment

## Required test matrix

| Requirement | Evidence | Result |
|---|---|---|
| Positive intake and coefficient | `test_positive_intake_and_coefficient_produce_positive_dose` | PASS |
| Zero intake | `test_zero_intake_produces_zero_dose` | PASS |
| Dose equation closure | `test_dose_equation_closes_with_zero_residual` | PASS |
| Adult/child separation | `test_adult_and_child_coefficients_remain_separate_states` | PASS |
| Immutable dose boundary | `test_dose_state_is_immutable_and_has_no_upstream_or_assessment_fields` | PASS |
| Provisional coefficient contract | `test_dose_requires_explicit_provisional_parameters` | PASS |
| Full Soil -> Root -> TFWT -> OBT -> Food -> Intake -> Dose path | `test_soil_root_tfwt_obt_food_intake_dose_toy_pathway_closes` | PASS |

## Commands and results

P6.6B focused command:

    PYTHONPATH=.:src .venv/bin/pytest -q \
      tests/unit/test_dose_v3.py \
      tests/integration/test_dose_interface.py \
      tests/architecture/test_dose_v3_boundary.py

Result: 12 tests passed, including 7 unit, 1 integration, and 4 boundary
tests.

The cross-stage command covered the P6.2B through P6.6B typed boundaries,
related deposition/multibox/wet-deposition tests, and the timestep
regression. Result: 126 tests passed: 34 architecture, 30 integration, 1
regression, and 61 unit tests.

Additional checks passed:

- `PYTHONPATH=.:src .venv/bin/python -m compileall -q
  src/cteas_ufotri/exposure/dose_v3
  src/cteas_ufotri/exposure/intake_v3`;
- import smoke for `DoseParameters`, `DoseSolver`, and `DoseState`;
- `git diff --check`.

## Test boundary

The toy pathway and equation checks establish a software conversion
interface. They do not establish validated dose coefficients, physical dose
assessment, regulatory compliance, risk, emergency criteria, observational
validation, or V3 physics readiness. Existing external-evidence tests were
not modified or forced green.
