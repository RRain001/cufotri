# ADR-039: V4 OBT matched-evidence acquisition preregistration R1

Status: `PREREGISTRATION_FROZEN_REQUESTS_NOT_SENT_AWAITING_FIRST_EXACT_HEAD_CI`

## Context

The OBT formation evidence-readiness stage merged at `d28695a13eae1fe4a7afb55a7a8a179d366de44c` with no tree drift and classified the selected future precursor/exchangeable/non-exchangeable OBT architecture as `ACQUIRABLE_WITH_PREREGISTRATION`. No complete matched Option-B raw packet is currently available, and no OBT candidate parameter or response function is active.

This stage freezes the rules that must exist **before** any external packet is inspected for model fit. It is a data-acquisition/control-plane stage only. It does not send requests, inspect hidden raw values, fit parameters, implement Option B, or alter the reduced OBT baseline.

## Decision

The preregistration is frozen around a two-layer blind workflow.

### Layer A — acquisition preregistration, frozen now

Before any requested raw packet is received, R1 fixes:

- the observation operator for TFWT, exchangeable OBT and non-exchangeable OBT;
- the admissible relationship between total OBT and component measurements;
- raw-file acceptance, checksum, licence and provenance requirements;
- target priority and request contents;
- exclusion, missing-data and below-detection handling boundaries;
- the rule that calibration/holdout separation occurs by complete biological replicate or experimental run, never by random time row;
- the requirement that a future dataset-shape amendment is completed before model fitting or holdout inspection;
- the identifiability diagnostics required before any candidate implementation or parameter activation.

### Layer B — metadata-only dataset-shape amendment, future and pre-fit

Exact numerical thresholds that depend on the number of independent runs, analytical uncertainty, sampling cadence, observation covariance or data scale are **not invented before the packet exists**. After a candidate packet is received, an intake process may inspect only filenames, schema, units, timestamps, replicate/run identifiers, analytical uncertainty metadata, detection limits, licence terms and checksums. Before any quantitative plant-tritium values are used for fitting, a separately reviewed dataset-shape amendment must freeze:

- the complete-run calibration/holdout allocation;
- the quantitative identifiability thresholds and numerical tolerances;
- the treatment of censored observations based on the declared analytical method;
- the exact model-comparison metrics and uncertainty weighting;
- any predeclared exclusion arising from metadata/quality flags.

The holdout values remain unopened during this amendment. If the raw provider cannot support a blind/sealed holdout, the packet may still be used for exploratory/component-method evidence but not for an independent validation claim.

## Frozen observation operator

### TFWT `T`

TFWT is a direct observable only when tissue, sample time, sampling support, extraction method, activity unit and water/mass/area basis are explicit. A concentration may be converted to model inventory only when the measured denominator and conversion basis required by the existing mass-basis contract are present. No inferred plant water mass or silent fresh/dry/hydrogen conversion is allowed.

### Non-exchangeable OBT `B_n`

Measured NE-OBT may map to candidate `B_n` only when the analytical de-exchange/combustion protocol, tissue, mass basis, area basis, recovery/context, uncertainty and timestamp are explicit. The mapping is operational/analytical; R1 does not claim that all slowly turning organic matter is one biological pool.

### Exchangeable OBT `B_x`

Directly reported E-OBT may map to candidate `B_x` only under an explicit exchange/de-exchange protocol and matched basis. If `B_x` is derived as total OBT minus NE-OBT, total and NE-OBT must come from the same sample or documented matched aliquots, share tissue/time/basis, and have an uncertainty/covariance rule frozen before fitting. A literature E-OBT fraction, a fraction from another crop, or a fitted hidden partition is forbidden.

### Aggregate OBT

`B_total = B_x + B_n` is a consistency diagnostic only when the components have compatible sample identity and basis. A separately reported aggregate OBT value may be compared as aggregate evidence, but it cannot be silently split into components.

### Precursor `P` and source `u_P`

`P` remains a latent lumped precursor/activity state with no asserted chemical identity. No existing photosynthesis, starch, PAR or carbohydrate variable is relabelled as `P`. `u_P` remains a model-derived source flux. A future proxy/observation operator requires a separate preregistered scientific decision.

## Acquisition target hierarchy

### Target A — VATO / IRSN-EDF owner clarification

Request the original first-phase grass sample-level data and analytical metadata needed to determine whether exchangeable and non-exchangeable OBT were measured on compatible samples. Required fields include synchronized TFWT, E-OBT/NE-OBT or the raw component assay outputs, atmospheric HTO and relevant light/radiation/temperature forcing, sample/cut/replicate IDs, tissue/basis metadata, analytical uncertainty/detection limits, missing/quality flags, original filenames, data dictionary and local-use/licence terms.

The VATO project and dynamic-model publications establish a credible owner/institution route and show why a fast OBT component is scientifically relevant; they do not prove that the complete component-resolved raw packet is publicly available.

### Target B1 — controlled MicroTom component experiment

Request sample-level TFWT, E-OBT, NE-OBT, plant/tissue identity, exposure/boundary data, light/PAR or activity information, temperature, stage, timestamps, biological replicate IDs, analytical uncertainty/detection limits and assay metadata from the 14-day controlled MicroTom study reported by Portuphy, Katayama and Faanu (SSRN 5059446 / DOI `10.2139/ssrn.5059446`). Publication access alone is not data acceptance.

### Target B2 — controlled Renard ryegrass component experiment

Request sample-level TFWT/OBT component observations, exchangeable-fraction assay data, biomass, timestamps, replicate IDs, hydroponic exposure histories, environmental metadata and analytical method/uncertainty information from Renard et al. (2017), DOI `10.1016/j.jenvrad.2017.06.026`.

The constant-exposure design may support component discrimination but cannot by itself justify all day/night/activity/temperature response functions.

### Supporting-only soybean/nocturnal evidence

IAEA/KAERI soybean and nocturnal-physiology data may be requested to support day/night/stage/forcing design or reduced-baseline comparisons. They are not component-calibration substitutes when E-OBT/NE-OBT are absent from the same matched case.

### Prospective experiment fallback

If no historical owner can provide an acceptable packet, the next correct route is a separately preregistered prospective experiment. It is not cross-study data fusion and it is not permission to infer missing components from the model.

## Raw packet acceptance

A packet is accepted for metadata-only intake only if all of the following can be recorded without changing the original bytes:

- owner/source identifier and original filenames;
- raw-file SHA-256 checksums;
- licence or explicit local-research-use status;
- machine-readable tables or an owner-supplied documented export;
- data dictionary with units and missing/quality codes;
- experiment/run/biological-replicate identifiers;
- sample timestamps and sampling support;
- tissue, crop/cultivar/stage and activity/mass/area basis;
- analytical component definitions and methods;
- uncertainty and detection/quantification limits;
- forcing/source data required by the claimed model terms.

Publication plots, OCR, graph digitization and model-generated pseudo-observations do not satisfy raw-data acceptance.

## Frozen exclusion and missing-data policy

Before the dataset-shape amendment, the only automatic exclusions are non-machine-readable/untraceable values, missing identity/basis/provenance required for the intended comparison, or provider-declared invalid/quality-failed observations. Missing quantitative values remain missing. Below-detection values remain censored with the reported detection/quantification limit; the project does not automatically substitute zero, half the limit or the limit. Any censoring likelihood/substitution rule must be frozen in the future pre-fit amendment.

No observation may be excluded because it worsens model fit.

## Calibration/holdout partition rule

Random row-wise or time-point splitting is forbidden. Calibration and holdout must use whole independent biological replicates or complete experimental runs. The exact number of holdout groups is not guessed before the dataset structure is known. The metadata-only amendment must select the full-group allocation using only identifiers and design metadata, before quantitative holdout values are inspected.

If fewer independent groups exist than required for a defensible external holdout, the disposition is `INSUFFICIENT_FOR_INDEPENDENT_HOLDOUT`; no random time split may repair it.

## Identifiability preregistration

Before Option B implementation or fitting, the future amendment must freeze:

- structural-identifiability analysis for the selected observation operator, including latent `P`;
- practical identifiability using profile likelihood or equivalent profiles;
- scaled Jacobian/Fisher singular values and conditioning;
- parameter-correlation/compensation diagnostics;
- boundary-hit and interval-width diagnostics;
- stability across independent calibration runs/replicates;
- the exact criteria for `IDENTIFIABLE`, `PARTIALLY_IDENTIFIABLE`, or `NON_IDENTIFIABLE`;
- Option A versus Option B metrics on the same cases.

Optimizer convergence is never an identifiability result. Non-identifiability leads to dimensionality reduction or HOLD, not parameter activation.

## Request execution boundary

The repository only freezes request text and target requirements. It does not claim that any request has been sent. Request/response dates, owner identity, permission reference and received-file checksums remain empty until an explicit acquisition execution stage records them.

## Next stage

After this preregistration passes both exact-head CI rounds, merges with `expected_head_sha`, and passes no-drift verification, authorize only:

`V4_OBT_EVIDENCE_ACQUISITION_EXECUTION_R1`

Scope: `EXTERNAL_DATA_REQUEST_AND_METADATA_INTAKE_ONLY`.

That stage may record requests, responses and metadata-only intake. It may not implement Option B, expose holdout values for tuning, activate or calibrate candidate parameters, change current `kf/kr`, or alter V3/V4 runtime defaults.

## Hard invariants

```ini
V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1 = PREREGISTRATION_FROZEN_REQUESTS_NOT_SENT_AWAITING_FIRST_EXACT_HEAD_CI
REQUESTS_SENT = FALSE
RAW_PACKET_RECEIVED = FALSE
QUANTITATIVE_MODEL_FIT_INSPECTION = FALSE
HOLDOUT_VALUES_INSPECTED = FALSE
OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED = FALSE
OBT_PARAMETER_ACTIVATION_AUTHORIZED = FALSE
CURRENT_KF_KR_CALIBRATION_AUTHORIZED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
LEAF_R5_AUTHORIZED = FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED = FALSE
FULL_HYDROLOGY_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
NEXT_STAGE_AFTER_SUCCESSFUL_MERGE = V4_OBT_EVIDENCE_ACQUISITION_EXECUTION_R1
```
