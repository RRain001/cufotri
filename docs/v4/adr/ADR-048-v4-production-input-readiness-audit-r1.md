# ADR-048: V4 production input readiness audit R1

## Status

Accepted as a control-plane production-input audit decision, pending exact-head CI and clean merge.

## Context

PR #44 closed the post-controlled-UFOTRI system review with a no-drift merge at `7800176751050c678ccfe24b04c5c263ec6c27bb`. The selected V4 software chain is connected under controlled synthetic/replay inputs, but `FULL_MODEL_PRODUCTION_READY=FALSE` remains.

This audit asks a narrower question than physics readiness: for every input actually consumed by the selected controlled path, is there a production-eligible source with explicit units, time/spatial semantics, provenance and scenario identity?

The answer must not confuse these distinct states:

1. an equation/pathway exists;
2. a controlled UFOTRI baseline/profile has been selected;
3. a caller input has a real or scenario-specific production source;
4. a live upstream producer is bound;
5. empirical/physical validation has been completed.

Only (1) and selected parts of (2) are broadly closed today.

## Source audit

The audit re-read the current runtime and frozen contracts rather than inheriting old parameter labels blindly. Key source observations are:

- `AtmosphericHTOForcing` requires air HTO concentration, deposition flux, temperature, humidity, wind speed, precipitation, timestamp/location and provenance. The frozen Atmos exchange contract requires a true surface activity flux and explicitly forbids relabeling puff-ledger activity or silently substituting zero.
- `UFOTRIEq39RootUptakeInputV4` makes temperature, net radiation, LAI, soil-water state, maximum/wilting water, latent heat, water density and psychrometric constant explicit, independently provenanced caller inputs. The Eq.39 equation and 20/40/40 distribution are selected; the real values are not thereby supplied.
- `ThreeLayerSoilForcing` deliberately does not solve Richards/Darcy hydrology. Surface water input/loss, signed inter-layer water and HTO fluxes, lower-boundary losses and surface HTO re-emission are explicit forcing inputs. Their API defaults are software conveniences and are not production evidence or implicit zero assumptions.
- `ResistanceChain` requires explicit `r_a`, `r_b`, `r_c`. Its parameter-database path is deliberately non-production (`production=False`) and rejects `ACTIVE` provenance. Therefore the current connected leaf pathway still lacks a production resistance source; this does not authorize Leaf R5.
- `TFWTState` requires explicit plant-water content and initial TFWT inventory; optional TFWT loss/transformation fluxes are not derived by the storage interface and their zero defaults are not production evidence.
- The reduced UFOTRI OBT `kf/kr` values are a selected controlled profile. Initial OBT inventory, plant fresh-mass basis, crop/stage identity and state provenance remain case inputs.
- `HarvestParameters`, `ConsumptionParameters` and `DoseParameters` remain explicitly `provisional` by default. Their software equations are connected, but harvest fractions/area, food mass, consumption amount/age group and dose coefficient still require production-eligible sources.
- The prior synthetic sensitivity screen showed strong computational reach for TFWT harvest fraction, atmospheric concentration and total leaf resistance. It is not a physical ranking, but it is sufficient to reject any claim that provisional endpoint or leaf inputs are harmless.

## Decision

`PRODUCTION_INPUT_PACKET_READY=FALSE`.

Do not add another physics subsystem. Select `V4_PRODUCTION_CASE_INPUT_MANIFEST_R1` as the next stage. It will define one fail-closed manifest/schema for an actual production case and require every consumed input to declare:

- canonical quantity and unit;
- classification (`CONTROLLED_UFOTRI_BASELINE_OR_PROFILE`, `PHYSICAL_CONSTANT`, `EXPLICIT_EXTERNAL_SCENARIO_INPUT`, `REAL_UPSTREAM_DATA_PREREQUISITE`, or `UNRESOLVED_OR_SYNTHETIC_ONLY`);
- source artifact/dataset and revision;
- temporal support and UTC semantics;
- spatial support / area / height basis where relevant;
- crop, growth stage, food product and age-group identity where relevant;
- transformation log;
- readiness status;
- whether an explicit zero is scientifically intended and evidenced.

The manifest must fail closed if a required input is unresolved. Existing Python defaults may not make a production field optional by accident.

## Current production blockers

1. **Production case manifest / completeness gate — ADVANCE.** The software chain is connected, but no single case-level packet proves that all inputs are production-sourced and mutually aligned.
2. **Real CTEAS-Atmos surface deposition flux — EXTERNAL HOLD.** The concentration/time semantics are compatible, but the required true surface-deposition-flux product is still unconfirmed. `REAL_CTEAS_ATMOS_BINDING=FALSE`.
3. **Leaf resistance production source — HOLD FOR SOURCE DECISION.** `r_a/r_b/r_c` are required and computationally influential, but no production-eligible source/profile is frozen. This is not authority for Leaf R5.
4. **Three-layer soil dynamic forcing source — HOLD FOR SOURCE/ZERO-POLICY DECISION.** Explicit surface/inter-layer/lower-boundary/re-emission forcing has no production source frozen. Full hydrology remains unauthorized.
5. **Endpoint and plant-state source packet — HOLD FOR MANIFEST POPULATION.** TFWT water content, OBT plant mass/initial states, harvest fractions/area, food mass, consumption and dose coefficient remain case-specific or provisional.

No physical uncertainty ranking is claimed between blockers 2–5.

## Controlled items that remain valid

- reduced UFOTRI OBT daily-average `kf/kr` baseline;
- controlled Eq.39 root-uptake equation semantics;
- UFOTRI 20/40/40 root distribution;
- selected `PRESERVE_V3_POST_OBT_ROOT_GAIN` operator split;
- `KEEP_HARVEST_EVENT` endpoint boundary;
- software connectivity through dose under explicit controlled inputs.

## Non-decisions

This audit does not activate parameters, calibrate any model, validate physical accuracy, implement Leaf R5, implement full hydrology, implement Eq.38 aerodynamic production use, activate UFOTRI reference layer rates or 3 h delay, implement multi-pool OBT, bind real CTEAS-Atmos, or declare a production case runnable.

`FULL_MODEL_PRODUCTION_READY=FALSE` remains.
