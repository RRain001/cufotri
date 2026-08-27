# V4 post-controlled-UFOTRI system review R1

Status: `REVIEW_DECISION_COMPLETE_AWAITING_EXACT_HEAD_GATE`

Base main: `589d23a81fb27509fb8591dac8695971dc14905f`

## Review result

The controlled UFOTRI software path is now connected end to end under synthetic/replay forcing. PR #43 merged with no content drift: parent1 is `2814579b6bc345d31cabf36f7712ede78292ce46`, parent2 is certified head `64ea75593b34f864cc4c96f36bc8561ebaac5279`, and both head and merge use tree `b75843f57bb2fdb308083f76d6267f68933133a1`. The head-to-merge comparison contains no changed files.

The certified PR #43 head passed Remediation `33054272035` and Protected `33054272016`; the portable suite reported `1355 passed, 1 skipped, 57 deselected, 1 warning`, and the frozen/current-boundary suite reported `375 passed`. The warning is the existing NumPy binary-compatibility warning and is not a gate failure.

Therefore the following software/control states are now treated as resolved for the selected V4 baseline route:

- `SOFTWARE_CHAIN_CONNECTED_WITH_CONTROLLED_UFOTRI_PROFILES=TRUE`;
- `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE` for the controlled Eq.39 construction path;
- UFOTRI 20/40/40 root distribution is the controlled layer profile;
- reduced UFOTRI `kf/kr` is the controlled OBT baseline;
- `PRESERVE_V3_POST_OBT_ROOT_GAIN` remains selected;
- `KEEP_HARVEST_EVENT` remains the terminal environmental/food boundary.

These are not empirical-validation or full-production-readiness claims.

## Re-ranking

The previous post-endpoint ranking is no longer current. Its leading OBT evidence-acquisition item was explicitly superseded by the project decision to use the UFOTRI baseline parameters directly, and its root-`q_w` item has been closed by the Eq.39 + 20/40/40 implementation and integration.

The updated ranking is:

1. **V4_PRODUCTION_INPUT_READINESS_AUDIT_R1 — ADVANCE.** Before adding physics, enumerate every input needed for a real production case and identify which ones are controlled UFOTRI profiles, physical constants, scenario inputs, real upstream prerequisites, or still synthetic/unresolved.
2. **REAL_CTEAS_ATMOS_BINDING — HOLD.** The exchange contract exists, but a true surface-deposition-flux product remains unconfirmed. Binding is therefore still fail-closed.
3. **LEAF_R5_DYNAMIC_STOMATAL_IMPLEMENTATION — HOLD.** The baseline resistance pathway is already connected. The R4 evidence checkpoint has not been executed, so R5 is not justified.
4. **FULL_SOIL_HYDROLOGY_OR_PLANT_WATER_DYNAMICS — HOLD.** The controlled Eq.39 root path no longer depends on adding a full hydrology subsystem; additional complexity requires a demonstrated system need.
5. **OBT_MULTI_POOL_OR_EXTERNAL_MATCHED_EVIDENCE_TRACK — HOLD.** The controlled route uses the reduced UFOTRI baseline. No multi-pool implementation, external email acquisition, calibration, or matched-data fitting is authorized.

## Next stage

Select `V4_PRODUCTION_INPUT_READINESS_AUDIT_R1` with control-plane/input-inventory scope only.

The audit must cover atmospheric HTO concentration and deposition, meteorology and temporal/spatial identity; Eq.39 net radiation, LAI, soil-water state and thresholds; physical constants; leaf resistance/equilibrium semantics; harvest and food basis; consumption and dose coefficient; units, missing-data policy, scenario identity and provenance.

No solver change is pre-authorized by this selection. If the audit finds that the only material remaining production blocker is a real upstream CTEAS-Atmos product, the correct disposition is to hold at that external prerequisite rather than manufacture additional internal physics.

## Frozen boundaries

```ini
SOFTWARE_CHAIN_CONNECTED_WITH_CONTROLLED_UFOTRI_PROFILES = TRUE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED = TRUE
FULL_MODEL_PRODUCTION_READY = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
LEAF_R5 = FALSE
FULL_HYDROLOGY = FALSE
MULTI_POOL_OBT = FALSE
CALIBRATION_STARTED = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
NEXT_STAGE = V4_PRODUCTION_INPUT_READINESS_AUDIT_R1
```
