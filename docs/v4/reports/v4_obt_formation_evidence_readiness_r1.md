# V4 OBT formation evidence readiness R1

## Status

`EVIDENCE_READINESS_ASSESSED_AWAITING_FIRST_EXACT_HEAD_CI`

This stage is a control-plane and evidence-readiness assessment only. It changes no production source, solver equation, numerical coupling, active parameter, calibration state, or runnable default.

## Entry state

`V4_SYSTEM_POST_ENDPOINT_REVIEW_R1` merged as `d8c3336c14db1d695e70dc62755b00ce5235d04d` with tree `e00d73be6c26f127e2274f59b1139c99eed5a168` and no head-to-merge file drift. That review selected OBT formation evidence readiness because the full opt-in software chain now reaches dose while the highest-ranked unresolved internal physics records remain OBT daylight, nighttime and activity/photosynthetic formation.

The runnable baseline remains:

`dB/dt = k_f T - k_r B`.

The future V4 candidate remains the value-free symbolic `P -> B_x -> B_n` architecture selected in P7.8B-2. No candidate rate or response function is active.

## State observability freeze

| Quantity | R1 evidence interpretation |
| --- | --- |
| TFWT `T` | Direct observable if extraction, tissue, basis, time and method are explicit |
| Precursor/activity `P` | Latent lumped model state; no single chemical identity is asserted |
| Exchangeable OBT `B_x` | Operational analytical observable only under explicit exchange/de-exchange protocol and basis |
| Non-exchangeable OBT `B_n` | Operational analytical observable only under explicit protocol and basis |
| Aggregate `B_total` | Derived from matched `B_x+B_n`, or a separate aggregate observation; no silent partition |
| Formation flux `u_P` | Derived/latent source flux; functional form not selected |
| day/night, activity/PAR, leaf temperature, stage | External evidence/forcing variables with independent provenance |

This is deliberately narrower than treating an analytical fraction as a proven kinetic pool. A future model-to-measurement mapping must remain auditable.

## Repository evidence inventory

The repository does **not** contain a complete Option-B-ready packet.

The historical soybean request package remains `READY_TO_SEND_MANUALLY` and was not sent. The external-evidence handoff records `SOYBEAN_DATA_STATUS=BLOCKED_EXTERNAL_DATA`, preregistration not executed, calibration not run and identifiability not assessed. The SB1 interface audit treats organ OBT as averages/structural diagnostics and cannot supply a matched E-OBT/NE-OBT trajectory.

Therefore:

```ini
REPOSITORY_MATCHED_PACKET_AVAILABLE = FALSE
CURRENT_EMPIRICAL_OPTION_B_VALIDATION = FALSE
```

## External acquisition-feasibility audit

External publications were reviewed only to decide whether acquisition is realistic. Their values are not runtime parameters and their observations are not combined across experiments.

### VATO grassland programme

Maro et al., *Journal of Environmental Radioactivity* 167 (2017) 235-248, DOI `10.1016/j.jenvrad.2016.10.016`, documents the IRSN/EDF VATO field platform and environmental/grass tritium measurements. The paper describes high-frequency environmental reconstruction and routine grass TFWT/OBT sampling. IAEA-TECDOC-1991 later describes first-phase VATO data as being used to evaluate TFWT and OBT formation kinetics including E-OBT and NE-OBT. However, the public dynamic-model comparison uses total grass OBT and the repository has not obtained a raw per-sample E-OBT/NE-OBT table with complete metadata.

Disposition: `PRIORITY_A_OWNER_CLARIFICATION_AND_ACQUISITION_TARGET`.

Admission requires confirmation that the component values were direct matched measurements rather than inferred partitions, followed by raw tables, methods, time support, forcing metadata, replicate/cut identities, basis, uncertainty and licence terms.

### Renard ryegrass controlled experiment

Renard et al., *Journal of Environmental Radioactivity* 177 (2017) 194-205, DOI `10.1016/j.jenvrad.2017.06.026`, reports controlled tritium exposure in ryegrass and direct determination of exchangeable OBT fractions for plant organs together with TFWT/OBT discrimination and time-resolved biomass observations.

This demonstrates component-separation feasibility and provides an identifiable data-owner route. Because the exposure is approximately constant, it cannot by itself establish identifiability for every day/night/activity response term without additional excitation.

Disposition: `PRIORITY_B_CONTROLLED_COMPONENT_ACQUISITION_TARGET`.

### MicroTom controlled experiment

Portuphy, Katayama and Faanu, SSRN abstract `5059446` (2024), reports a 14-day controlled MicroTom study analyzing TFWT, E-OBT and NE-OBT. This is strong feasibility evidence for component-resolved acquisition.

R1 has not verified a machine-readable raw table with all required sample times, replicates, light/PAR, leaf temperature, stage, analytical uncertainty and basis metadata.

Disposition: `PRIORITY_B_CONTROLLED_COMPONENT_ACQUISITION_TARGET`.

### Soybean day/night evidence

The existing soybean day/night/stage experiment is relevant to forcing and stage discrimination, but its OBT evidence is aggregate rather than E-OBT/NE-OBT component trajectories.

Disposition: `SUPPORTING_FORCING_AND_STAGE_FEASIBILITY_ONLY`.

It must not be spliced with a different component experiment to create a fictitious complete case.

## Readiness verdict

The formal evidence disposition is:

`ACQUIRABLE_WITH_PREREGISTRATION`.

It is not `AVAILABLE`: no complete matched raw packet has been received, checksummed, licensed, mapped and frozen.

It is not `UNAVAILABLE_OR_INSUFFICIENT`: multiple controlled studies demonstrate component measurement feasibility, and VATO plus controlled-study authors provide credible acquisition routes.

This classification is intentionally procedural. It authorizes a preregistered acquisition attempt, not a model implementation.

## Required single-case packet

Before any Option B implementation can be considered, one internally aligned experimental case/program must supply or validly derive:

- time-resolved TFWT;
- time-resolved exchangeable OBT;
- time-resolved non-exchangeable OBT;
- daylight/light state;
- photosynthetic activity or an explicitly typed PAR/activity proxy;
- temperature;
- crop and developmental stage;
- tissue scope;
- sample timestamps and sampling time support;
- biological replicate identifiers;
- activity unit, mass basis and area basis;
- analytical method/protocol, uncertainty and detection/quantification limits;
- missing-data flags;
- raw-file identity, SHA-256, licence/local-use status and provenance.

A publication figure, literature E-OBT fraction or synthetic benchmark cannot fill a missing field.

## Identifiability and holdout gate

The future evidence packet must be capable of testing the model distinction, not merely fitting more parameters.

Required before activation:

1. `B_x`/`B_n` must be component observations under explicit operational definitions; aggregate OBT may not be split using a literature fraction.
2. Option A and Option B must be compared on the same case(s).
3. The exposure/forcing pattern must excite every response term that is claimed to be identified; constant exposure cannot prove a full day/night/activity response model by itself.
4. Structural and practical identifiability assessments are mandatory before parameter activation.
5. Calibration and independent holdout identities must be frozen before holdout inspection.
6. Unidentifiable terms remain absent/HOLD rather than receiving guessed defaults.

No exact parameter values, response-function shapes or numerical acceptance thresholds are selected in this stage.

## Acquisition hierarchy

The next stage must preregister the packet before inspecting data for fit:

1. VATO owner clarification and raw component-data request.
2. If VATO cannot supply directly measured matched components, request a controlled component packet from the MicroTom or Renard experimental lines.
3. If no existing packet meets the contract, prepare a new preregistered experiment or conclude `UNAVAILABLE_OR_INSUFFICIENT`.

Independent studies may inform measurement design and biological interpretation, but cannot be fused into a single calibration trajectory.

## Next stage

After exact-head CI, governance closure, expected-head merge and no-drift verification, authorize only:

`V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1`

Scope: `CONTROL_PLANE_AND_DATA_ACQUISITION_ONLY`.

That stage may prepare a data-owner request package, acceptance schema, licence/provenance manifest, field mapping, missing-data/exclusion rules and calibration/holdout partition. It may not implement the multi-pool solver or activate/calibrate any OBT parameter.

## Hard state

```ini
V4_OBT_FORMATION_EVIDENCE_READINESS_R1 = EVIDENCE_READINESS_ASSESSED_AWAITING_FIRST_EXACT_HEAD_CI
EVIDENCE_DISPOSITION = ACQUIRABLE_WITH_PREREGISTRATION
REPOSITORY_MATCHED_PACKET_AVAILABLE = FALSE
P_STATE = LATENT
CROSS_STUDY_CASE_FUSION = FORBIDDEN
LITERATURE_FRACTION_COMPONENT_PARTITION = FORBIDDEN
OBT_MULTI_POOL_IMPLEMENTATION = FALSE
OBT_PARAMETER_ACTIVATION = FALSE
CURRENT_KF_KR_CALIBRATION = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
V3_DEFAULT_CHANGED = FALSE
V4_RUNTIME_CHANGED = FALSE
LEAF_R5 = FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED = FALSE
FULL_HYDROLOGY = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
NEXT_STAGE = V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1
```

The status remains provisional until both exact-head CI rounds and post-merge no-drift are complete.
