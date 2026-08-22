# V3-P7.6B-1 parameter applicability review

Status: `PASS_PARAMETER_APPLICABILITY_REVIEW`

## Scope

This stage reviews whether an evidence context can apply to a V3 model
variable. It does not determine a final parameter value, fit a parameter to
observations, replace a provisional value, or activate a database. The review
matrix covers every record in the P7.6A inventory at
`docs/v3/parameter_evidence/parameter_inventory.yaml`.

The executable control plane is isolated under
`src/cteas_ufotri/parameters_v3/`. The canonical matrix is
`docs/v3/parameter_evidence/parameter_applicability_matrix.yaml` and is tied
to P7.6A commit `ff75826c0da9773c7297b592bcb66ea35951329c`.

## Frozen result

```text
P7_6B1_STATUS = PASS_PARAMETER_APPLICABILITY_REVIEW
PARAMETER_APPLICABILITY_SCHEMA = TRUE
PARAMETER_REVIEW_MATRIX = TRUE
VALIDATION_CANDIDATES_IDENTIFIED = TRUE
VALIDATION_CANDIDATE_COUNT = 0
CALIBRATION_STARTED = FALSE
ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

All 76 records have a complete immutable applicability record. The candidate
set is identified even though no record is currently admitted.

| Applicability disposition | Count | Meaning in this matrix |
|---|---:|---|
| `DIRECT_MATCH` | 0 | No resolved source/equation/unit package is present. |
| `PARTIAL_MATCH` | 0 | No partial source package with resolved uncertainty is present. |
| `TRANSFER_REQUIRED` | 0 | No transfer assumption is authorized in this stage. |
| `UNKNOWN` | 26 | Production/model evidence context remains unresolved. |
| `NOT_APPLICABLE` | 50 | Scenario inputs, numerical controls, or synthetic fixtures. |

The 26 unknown records cover physical, empirical, biological, crop, soil,
exposure, and dose parameter classes. The 50 non-applicable records are the
28 scenario inputs, 2 numerical controls, and 20 test-only parameters already
classified by P7.6A. The latter 20 have software-fixture evidence only and
cannot become physical validation evidence.

## Class review coverage

| Parameter class | Total | `UNKNOWN` | `NOT_APPLICABLE` | Candidate IDs |
|---|---:|---:|---:|---:|
| `PHYSICAL_CONSTANT` | 1 | 1 | 0 | 0 |
| `EMPIRICAL_MODEL_PARAMETER` | 8 | 8 | 0 | 0 |
| `BIOLOGICAL_PARAMETER` | 4 | 4 | 0 | 0 |
| `CROP_PARAMETER` | 7 | 7 | 0 | 0 |
| `SOIL_PARAMETER` | 3 | 3 | 0 | 0 |
| `EXPOSURE_PARAMETER` | 2 | 2 | 0 | 0 |
| `DOSE_PARAMETER` | 1 | 1 | 0 | 0 |
| `SCENARIO_INPUT` | 28 | 0 | 28 | 0 |
| `NUMERICAL_CONTROL` | 2 | 0 | 2 | 0 |
| `TEST_ONLY_PARAMETER` | 20 | 0 | 20 | 0 |
| **Total** | **76** | **26** | **50** | **0** |

## Mechanism-specific review questions

| V3 area | Required applicability questions | Frozen disposition |
|---|---|---|
| Leaf exchange | HTO form, leaf exchange mechanism, same aerodynamic/boundary/canopy resistance formulation, and units | Model records remain `UNKNOWN`; forcing/coordinates are `NOT_APPLICABLE`. |
| TFWT | Plant-water pool definition, water-loss basis, time scale, and crop dependence | Model records remain `UNKNOWN`; initial state input is `NOT_APPLICABLE`. |
| OBT | HTO-to-OBT formation versus general organic-isotope exchange, `k_f`/`k_r`, day/night conditions | Model records remain `UNKNOWN`; day/night and initial-state inputs are `NOT_APPLICABLE`. |
| Soil | Soil depth, water-content basis, transport mechanism, and decay convention | Model records remain `UNKNOWN`; initial inventory is `NOT_APPLICABLE`. |
| Root uptake | Soil-water concentration versus total inventory and root-zone conditions | `k_root` remains `UNKNOWN`; root-zone identity is `NOT_APPLICABLE`. |
| Food transfer | Edible part, fresh/dry-mass basis, crop specificity, and harvest timing | Fractions and crop basis remain `UNKNOWN`; endpoint identifiers/area are `NOT_APPLICABLE`. |
| Intake | Demographic scenario input versus model parameter, food mass basis, and exposure period | Consumption and mass remain `UNKNOWN`; identifiers are `NOT_APPLICABLE`. |
| Dose | Radionuclide, age group, pathway, coefficient source, and `Sv/Bq` unit | Dose coefficient remains `UNKNOWN`; identifiers are `NOT_APPLICABLE`. |

These are applicability questions for later source screening. They are not
claims that an unreviewed source exists and do not authorize a value import.

## Disposition

The review is complete at the control-plane level. P7.6B-2 must acquire and
screen actual literature/standard packages before any row can move to a
direct/partial disposition. No numerical calibration, observation fitting,
solver change, P6 physical change, P7.5/P7.5B coupling change, or UFOTRI
database activation occurred.
