# V3-P7.6A parameter gap analysis

Status: `PASS_PARAMETER_EVIDENCE_PROVENANCE_FROZEN`

The manifest contains 76 records. The gap category is derived from the
record class, source marker, applicability, and evidence notes; it is not a
scientific validity claim.

| Category | Meaning | Count | Disposition |
|---|---|---:|---|
| A | Evidence sufficient for future validation | 0 | No record is promoted to this category without a traceable evidence package. |
| B | Evidence found but applicability unresolved | 0 | Applicability remains unresolved for the current unsourced model inputs. |
| C | Conflicting evidence | 0 | No conflict is adjudicated in P7.6A. |
| D | No evidence | 28 | Requires source acquisition and applicability review before validation. |
| E | Scenario input | 28 | Must be supplied by a future case/data contract; not calibrated here. |
| F | Test-only parameter | 20 | Synthetic/reproducible software fixtures only; never production defaults. |

The highest-priority future evidence gaps are:

1. the tritium physical half-life source and exact model-unit mapping;
2. `r_a`, `r_b`, and `r_c` applicability for crop, growth stage, and
   environment;
3. `k_f`, `k_r`, day/night multipliers, and TFWT loss/transformation terms;
4. `k_root` evidence under the declared `J_root = k_root * C_soil` contract;
5. crop-specific harvest fractions and harvest basis;
6. age-group food consumption, food mass basis, and dose-coefficient
   provenance.

P7.6A does not fit, optimize, calibrate, select, or activate any of these
values. P7.6B must define the validation/calibration gate separately.
