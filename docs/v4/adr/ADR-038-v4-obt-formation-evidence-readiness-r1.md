# ADR-038: V4 OBT formation evidence readiness R1

Status: `PASS_EVIDENCE_READINESS_AWAITING_CLOSURE_EXACT_HEAD_CI`

## Context

The post-endpoint system review merged at `d8c3336c14db1d695e70dc62755b00ce5235d04d` and selected `V4_OBT_FORMATION_EVIDENCE_READINESS_R1` as the next scientific control-plane stage. The runnable OBT baseline remains the reduced first-order storage relation

`dB/dt = k_f T - k_r B`.

P7.8B-2 selected `option_b_two_pool_biological_extension` as the future V4 direction, and the V4 symbolic contract already freezes three candidate inventories: precursor/activity `P`, exchangeable OBT `B_x`, and non-exchangeable OBT `B_n`. That architecture decision did not select biological source functions, response functions, rate values, calibration data, or a runtime implementation.

The purpose of this stage is therefore not to write the selected solver. It is to determine whether the evidence required to discriminate the selected candidate from the reduced baseline is already available or can realistically be acquired under a preregistered case contract.

## Biological and observational state interpretation

The following interpretation is frozen for evidence acquisition only.

- `T` is the TFWT activity inventory available at the OBT formation boundary. It is a directly measurable quantity when the water extraction, tissue, area/mass basis, timestamp and analytical method are explicit.
- `P` is a **latent lumped precursor/activity state**. R1 does not identify it with a single molecule, carbohydrate pool, photosynthetic product or directly measured chemical species. A future implementation may use `P` only as a model state whose observability/identifiability is demonstrated from matched data.
- `B_x` is the candidate exchangeable-OBT inventory. It may be treated as an operational analytical observable only when the exchange/de-exchange protocol, tissue, basis, recovery and uncertainty are explicit. It is not automatically equivalent to TFWT or to an unspecified generic fast kinetic pool.
- `B_n` is the candidate non-exchangeable-OBT inventory. It may be treated as an operational analytical observable only when the analytical protocol and basis are explicit. It is not automatically equivalent to all slowly turning-over organic matter.
- `B_total` is a diagnostic aggregate. `B_x + B_n` may be formed only when both components belong to the same sample, tissue, time support and basis. A separately measured aggregate OBT value cannot be silently partitioned into `B_x` and `B_n`.
- `u_P` is a derived candidate formation flux, not a directly observed state. Its dependence on TFWT, day/night, photosynthetic activity/PAR, temperature and stage remains unselected.
- day/night state, activity/PAR, leaf temperature and crop/developmental stage are external evidence/forcing variables with independent provenance. No current V3 multiplier is reinterpreted as a future mechanistic forcing.

This classification prevents an analytical separation protocol from being mistaken for a fully identified biological mechanism.

## Repository evidence audit

The repository does not currently contain a complete matched packet capable of validating Option B.

The earlier soybean external-evidence package was prepared but never sent. Its recorded state remains `BLOCKED_EXTERNAL_DATA`; preregistration was not executed, calibration was not run, and identifiability was not assessed. The SB1 interface audit also classifies soybean organ OBT as averages/structural diagnostics rather than a component-resolved kinetic dataset.

The repository contract explicitly requires matched TFWT, exchangeable OBT, non-exchangeable OBT, day/night or light state, activity/PAR context, leaf temperature, crop stage, tissue/mass/area basis, timestamps/time support, biological replicate identifiers and provenance. Sparse aggregate OBT alone is insufficient.

Therefore:

`REPOSITORY_MATCHED_PACKET_AVAILABLE = FALSE`.

## External evidence feasibility audit

R1 reviewed external sources only to determine acquisition feasibility. No publication values are imported as runtime parameters, no plots are digitized, and no independent experiments are spliced into a synthetic validation case.

### VATO / La Hague grassland

Maro et al. (2017), DOI `10.1016/j.jenvrad.2016.10.016`, describes the IRSN/EDF VATO platform and a high-frequency environmental dataset for tritium transfer in grass. The public article describes daily atmospheric measurements/reconstruction and fortnightly grass TFWT/OBT sampling. IAEA-TECDOC-1991 later states that first-phase VATO data were used to evaluate TFWT and OBT kinetics, including E-OBT and NE-OBT, but the published dynamic model comparison primarily reports total grass OBT.

This is a strong acquisition target, not a verified ready packet. R1 has not obtained a raw per-sample table proving direct E-OBT/NE-OBT measurements together with the complete forcing, replicate and basis metadata required by the V4 contract. Owner clarification is required before VATO can be admitted as a component-validation case.

### Controlled ryegrass component experiment

Renard et al. (2017), DOI `10.1016/j.jenvrad.2017.06.026`, reports controlled ryegrass cultures under constant tritium exposure, exchangeable OBT fractions for plant organs, TFWT/OBT discrimination and time-resolved dehydrated biomass during early growth. This demonstrates that component separation and controlled acquisition are feasible. Constant exposure and the publicly verified metadata do not by themselves establish the full day/night/activity excitation needed to identify every Option B forcing term.

The publication provides an identifiable author/institution contact route, but no complete raw matched packet has been ingested into this repository.

### Controlled MicroTom component experiment

Portuphy, Katayama and Faanu (SSRN abstract `5059446`, posted 2024) reports a 14-day controlled MicroTom experiment in which TFWT, E-OBT and NE-OBT were analyzed. This is direct evidence that a component-resolved time-series experiment is technically feasible. R1 has not verified a reusable raw table containing all sample times, biological replicate identifiers, PAR/light history, leaf temperature, stage, uncertainty and analytical basis metadata required by the candidate contract.

It is therefore an acquisition target, not an `AVAILABLE` validation packet.

### Soybean day/night experiment

The existing soybean evidence is useful for day/night and developmental-stage feasibility because the controlled exposures include day/night timing and matched TFWT/aggregate OBT observations. It does not resolve E-OBT and NE-OBT components and therefore cannot validate Option B by itself.

## Evidence readiness decision

The stage disposition is:

`ACQUIRABLE_WITH_PREREGISTRATION`.

This means:

1. no complete Option-B-ready raw packet has been obtained and frozen in the repository;
2. multiple credible experimental programmes demonstrate that the required component measurements are technically feasible and provide realistic data-owner contact/acquisition routes;
3. raw-data access, licence/use conditions, component definitions and the complete matched-variable schema must be verified before any dataset becomes admissible;
4. studies may support acquisition feasibility or biological interpretation, but unrelated experiments must never be merged into one calibration/validation case.

The disposition is **not** `AVAILABLE`, because publication-level evidence and model-intercomparison summaries are not the same as a frozen matched raw packet. It is not `UNAVAILABLE_OR_INSUFFICIENT`, because component-resolved experiments and identifiable acquisition routes exist.

## Preregistered acquisition hierarchy

The next stage must use a single-case-first strategy.

1. **Target A — VATO owner clarification/acquisition.** Request the first-phase grass sample table and analytical metadata needed to determine whether E-OBT and NE-OBT were directly measured per sample. Request synchronized TFWT, atmospheric HTO/light or radiation/temperature/meteorology, sample/cut/replicate identities, tissue and mass/area bases, analytical uncertainty/detection limits, missing-data flags and licence terms.
2. **Target B — controlled component dataset.** If VATO cannot supply direct component trajectories, request a raw controlled component dataset from the MicroTom or Renard experimental lines with the same completeness requirements.
3. **New experiment fallback.** If no existing owner can provide a packet that meets the contract, the correct outcome is a preregistered new acquisition design or `UNAVAILABLE_OR_INSUFFICIENT`; it is not cross-study data fusion.

No raw data may be inspected for model fit before the acceptance schema, calibration/holdout partition rule and exclusion policy are preregistered.

## Minimum identifiability gate before any OBT implementation

A future implementation remains blocked unless an accepted packet supports all of the following:

- `B_x` and `B_n` are component observations under explicit analytical definitions, not inferred by a fixed literature fraction from aggregate OBT;
- TFWT and candidate OBT observations refer to compatible tissue, time support and basis;
- forcing variation is sufficient to test the proposed day/night/activity/temperature dependence rather than fitting effective constants to an unexcited condition;
- the reduced Option A and selected Option B are evaluated on the same cases;
- structural/practical identifiability is assessed before parameter activation;
- calibration and independent holdout identities are frozen before holdout performance is inspected;
- component and aggregate conservation identities are auditable;
- uncertainty, detection limits, missing data and provenance are retained.

If a complete packet cannot satisfy these conditions, the multi-pool candidate remains on HOLD and the reduced model stays explicitly labeled as a limited baseline.

## First exact-head certification

The evidence-readiness review head is `428d413230d90fc2e8960bc69217052c6b5cd95e`.

```text
Protected 33039367515 = SUCCESS
Remediation 33039367521 = SUCCESS
portable = 1293 passed, 1 skipped, 57 deselected
frozen/current-boundary = 355 passed
sensitivity = PASS_SOFTWARE_SCREENING
root operator split = PASS_SELECTION
soil-root-TFWT-OBT = PASS_INTEGRATION
replay orchestration = PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION
food-intake-dose endpoint = PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION
```

The pull-request workflow checked synthetic merge ref `f37488d2ebe57b091317942e223487f736dedfc4`, which merges exact review head `428d4132...` into base `d8c3336c...`. This checkout identity is recorded separately from the branch-head identity. The passing software gates do not convert the external evidence assessment into empirical validation or a physical-accuracy claim.

## Governance closure

The first exact head has passed both required workflows, so this governance-only closure records the certification evidence and updates `docs/implementation_status.md`. Relative to `428d4132...`, the closure may change only:

- `docs/v4/adr/ADR-038-v4-obt-formation-evidence-readiness-r1.md`;
- `docs/v4/governance/v4_obt_formation_evidence_readiness_r1.yaml`;
- `docs/v4/reports/v4_obt_formation_evidence_readiness_r1.md`;
- `tests/v4/test_v4_obt_formation_evidence_readiness_r1.py`;
- `docs/implementation_status.md`.

It changes no workflow, evidence-packet contract, `src/`, script, solver equation, runtime state, parameter, calibration state, evidence disposition or next-stage scientific decision. The closure exact head must independently pass Protected + Remediation before the PR may become Ready.

## Next stage

After this evidence-readiness PR passes the closure exact-head CI round, merges with `expected_head_sha`, and passes parent/tree no-drift verification, the only authorized follow-on is:

`V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1`

Scope: `CONTROL_PLANE_AND_DATA_ACQUISITION_ONLY`.

That stage may freeze a request package, target hierarchy, raw-file acceptance schema, licence/provenance manifest, calibration/holdout partition policy and acquisition disposition. It may not implement Option B, assign `k_P`, `k_PB`, `k_xn`, `k_x`, `k_n`, define numerical `phi_*` response functions, calibrate `kf/kr`, activate parameters, or change the V3/V4 runnable defaults.

## Hard invariants

```ini
V4_OBT_FORMATION_EVIDENCE_READINESS_R1 = PASS_EVIDENCE_READINESS_AWAITING_CLOSURE_EXACT_HEAD_CI
EVIDENCE_DISPOSITION = ACQUIRABLE_WITH_PREREGISTRATION
REPOSITORY_MATCHED_PACKET_AVAILABLE = FALSE
P_STATE = LATENT_LUMPED_PRECURSOR_ACTIVITY
BX_STATE = OPERATIONAL_ANALYTICAL_OBSERVABLE_IF_PROTOCOL_EXPLICIT
BN_STATE = OPERATIONAL_ANALYTICAL_OBSERVABLE_IF_PROTOCOL_EXPLICIT
CROSS_STUDY_CASE_FUSION = FORBIDDEN
LITERATURE_FRACTION_COMPONENT_PARTITION = FORBIDDEN
OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED = FALSE
OBT_PARAMETER_ACTIVATION_AUTHORIZED = FALSE
CURRENT_KF_KR_CALIBRATION_AUTHORIZED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
V3_DEFAULT_CHANGED = FALSE
V4_RUNTIME_CHANGED = FALSE
LEAF_R5_AUTHORIZED = FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED = FALSE
FULL_HYDROLOGY_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
NEXT_STAGE_AFTER_SUCCESSFUL_MERGE = V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1
```

The evidence-readiness decision remains non-effective for downstream authorization until the closure exact head passes both workflows, the PR is merged with `expected_head_sha`, and post-merge parent/tree/main no-drift verification succeeds.
