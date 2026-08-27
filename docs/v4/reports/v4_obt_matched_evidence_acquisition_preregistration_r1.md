# V4 OBT matched-evidence acquisition preregistration R1 report

## Status

`PREREGISTRATION_FROZEN_REQUESTS_NOT_SENT_AWAITING_FIRST_EXACT_HEAD_CI`

This stage freezes external-data acquisition and blind-intake rules. It does not send requests, receive raw files, inspect quantitative plant-tritium values for fitting, implement the selected multi-pool OBT candidate, or activate/calibrate any parameter.

## Entry state

PR #35 merged the OBT formation evidence-readiness decision at:

`d28695a13eae1fe4a7afb55a7a8a179d366de44c`

with parent/tree no drift. The frozen evidence disposition is `ACQUIRABLE_WITH_PREREGISTRATION`, not `AVAILABLE`. A complete matched Option-B raw packet is still absent.

## Why two preregistration layers are required

A complete sample count, replicate structure, analytical uncertainty model and observation covariance are not known before an owner supplies a raw packet. Inventing numerical profile-likelihood thresholds, holdout counts or censoring substitutions now would be arbitrary. Waiting until after model fitting would be data-dependent governance.

R1 therefore freezes two layers:

1. **Acquisition preregistration now** — scientific observation mapping, target order, acceptance schema, blind-intake rules, missing/censoring boundaries, whole-group holdout principle and required identifiability diagnostics.
2. **Dataset-shape amendment later but pre-fit** — only after metadata/schema intake, and before any quantitative fit or holdout inspection, freeze numerical identifiability thresholds, uncertainty weighting, exact whole-group split, censoring likelihood/treatment and model-comparison metrics.

This preserves preregistration while avoiding fabricated numbers.

## Observation mapping

TFWT is a direct observation only under an explicit tissue/time/extraction/basis contract. NE-OBT may map to `B_n` under an explicit component assay. E-OBT may map to `B_x` under an explicit component assay. A `total - NE` mapping is admissible only for the same sample or documented matched aliquots, with compatible tissue/time/basis and a preregistered uncertainty/covariance treatment.

A literature E-OBT percentage is not an observation operator. A fitted hidden component is not a measured component. Aggregate OBT may be retained as an aggregate check but may not be silently partitioned.

The precursor `P` remains latent and chemically unspecified. Photosynthesis, PAR, starch or another physiological variable is not renamed `P`; any future proxy relation requires separate review.

## Acquisition order

### Priority A — VATO / IRSN-EDF

First request owner clarification and sample-level data sufficient to establish whether E-OBT and NE-OBT were directly measured on compatible grass samples together with TFWT, forcing, replicate and basis metadata. The public programme is a strong acquisition target, but its publication record is not treated as the already-frozen raw packet.

### Priority B1 — controlled MicroTom

Request the component-resolved controlled experiment reported under DOI `10.2139/ssrn.5059446`, including sample-level TFWT/E-OBT/NE-OBT, exposure, forcing, replicate, stage, basis and analytical-quality metadata.

### Priority B2 — Renard ryegrass

Request sample-level component observations and controlled exposure/biomass/replicate/analytical metadata from DOI `10.1016/j.jenvrad.2017.06.026`. The constant-exposure design may support component kinetics but does not automatically identify every day/night/activity/temperature term.

### Supporting evidence

Soybean and nocturnal-physiology datasets can support stage/forcing design and reduced-baseline comparisons, but they remain separate unless the component measurements originate from the same internally aligned experiment.

### Fallback

If no historical owner can provide an admissible packet, the route is a separately preregistered prospective matched experiment or an insufficiency decision. Cross-study row splicing is not the fallback.

## Raw packet acceptance

Future receipt is acceptable for metadata-only intake only when provenance, original filenames/checksums, licence terms, machine-readable data, a data dictionary, experiment/run/replicate IDs, timestamps/time support, crop/stage/tissue/basis, analytical component definitions, uncertainties/detection limits and the forcing fields needed for the claimed mechanisms are traceable.

Raw bytes remain local and Git-ignored. Tracked artifacts may contain metadata, checksums, schemas and field maps, not copied raw quantitative observations.

Publication summaries, OCR, plot digitization and model-generated pseudo-observations cannot repair a missing raw table.

## Missing data and detection limits

Missing remains missing. Below-detection observations remain censored with their reported limit. R1 does not select zero, half-limit or limit substitution. If a packet is later accepted, a quantitative censoring method may be selected only in the pre-fit dataset-shape amendment.

Only non-auditable identity/basis/provenance failures or provider-declared invalid/quality-failed observations are automatic exclusion candidates. Fit performance can never justify excluding an observation.

## Calibration and holdout

The split unit is the whole independent biological replicate or complete experimental run. Random timestamp/row splitting is prohibited because it leaks within-trajectory information.

The exact number of held-out groups is unknown until metadata are received. It will be frozen using identifiers/design metadata before quantitative holdout values are inspected. If too few independent groups exist, the packet is insufficient for an independent holdout; a random time split cannot fix the problem.

## Identifiability

A future candidate cannot advance from acquisition to implementation merely because an optimizer converges. The pre-fit amendment must define structural identifiability for the selected observation operator including latent `P`, profile or equivalent parameter diagnostics, Jacobian/Fisher conditioning, parameter correlations/compensation, boundary hits, interval widths, replicate/run stability and same-case Option A versus Option B metrics.

The allowed scientific outcomes remain `IDENTIFIABLE`, `PARTIALLY_IDENTIFIABLE`, `NON_IDENTIFIABLE`, or not assessed. Unsupported degrees of freedom are reduced or held; they are not activated.

## What this stage has not done

```text
REQUESTS_SENT = FALSE
RESPONSES_RECEIVED = FALSE
RAW_PACKET_RECEIVED = FALSE
QUANTITATIVE_MODEL_FIT_INSPECTION = FALSE
HOLDOUT_VALUES_INSPECTED = FALSE
CALIBRATION_STARTED = FALSE
ACTIVE_PARAMETERS = 0
```

No contact identity, request date, response date, permission reference or raw checksum is fabricated in this stage.

## Next stage

After first exact-head CI, governance closure, closure exact-head CI, expected-head merge and no-drift verification, the only authorized follow-on is:

`V4_OBT_EVIDENCE_ACQUISITION_EXECUTION_R1`

That stage may send/record requests and perform metadata-only intake. It may not implement Option B, fit OBT candidate parameters, inspect holdout values for tuning, recalibrate current `kf/kr`, or change the runnable defaults.

## Hard state

```ini
V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1 = PREREGISTRATION_FROZEN_REQUESTS_NOT_SENT_AWAITING_FIRST_EXACT_HEAD_CI
OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED = FALSE
OBT_PARAMETER_ACTIVATION_AUTHORIZED = FALSE
CURRENT_KF_KR_CALIBRATION_AUTHORIZED = FALSE
LEAF_R5_AUTHORIZED = FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED = FALSE
FULL_HYDROLOGY_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
NEXT_STAGE = V4_OBT_EVIDENCE_ACQUISITION_EXECUTION_R1
```
