# CUFOTRI scientific documentation index

This is a navigation map, not a new scientific acceptance statement. Start with the [current project status](../STATUS.md), then consult the versioned source documents below. **Manual-based functional reconstruction, numerical equivalence to original UFOTRI, and empirical validation are different claims.**

## Current scientific authority (read first)

| Question | Source | Interpretation |
|---|---|---|
| Which claims are established today? | [STATUS.md](../STATUS.md) | Current top-level scope and explicit exclusions |
| What stages were planned and audited? | [UFOTRI replication master plan](v4/roadmap/UFOTRI_REPLICATION_MASTER_PLAN.md) | Historical A–G stage ledger; its earlier atmospheric classification is superseded where corrected |
| Why was UFOTRI-native atmospheric recovery added? | [Native atmosphere recovery correction](v4/roadmap/UFOTRI_NATIVE_ATMOSPHERE_RECOVERY_PLAN.md) | Authoritative post-G4 H1–H6 correction and current manual-fidelity boundaries |
| What is the frozen internal development baseline? | [V4 RC1 baseline](v4/adr/ADR-057-v4-development-baseline-rc1.md) | Synthetic/replay software baseline, **not** field qualification |
| What is the final manual-reconstruction audit? | [H6 R2 final gate](v4/adr/ADR-084-ufotri-manual-based-functional-reconstruction-final-gate-r2.md) | Stage-specific handoff and limitations, not proof of original executable equivalence |

For current claims, read these in conjunction with `STATUS.md`. Historical documents may contain older time-bounded statuses; they should not be rewritten retroactively.

## UFOTRI 4.0 (1993) future target — source audit in progress

- [1993 KfK 5194 physics delta matrix](v4/1993_upgrade/PHYSICS_DELTA_MATRIX.md): **1993 UFOTRI 4.0 is the TARGET version**; KfK 4605 (1990) is comparison-only. This source-anchored P0 audit is partial and does not enable the 1993 physics implementation.
- [1993 machine-readable evidence registry](v4/1993_upgrade/physics_delta_matrix.yaml): item IDs, primary printed source references, existing code entrypoints, uncertainty and follow-up P1–P7.
- [1993 original-equation and NAMELIST audit R2](v4/1993_upgrade/PRIMARY_SOURCE_AUDIT_R2.md): printed source equations, 21 historical defaults, source unit conflicts and 1990→1993 re-emission formula comparison. Machine-readable [R2 primary-source registry](v4/1993_upgrade/primary_source_formula_audit_r2.yaml). This is source review, **not** a 1993 solver validation.
- [1993 Table 1 and COMA Table 9–12 audit R3](v4/1993_upgrade/PRIMARY_SOURCE_TABLE_AUDIT_R3.md): source-checked crop masses, 80 daily transfer edges, historical soil/food intervention inputs and unresolved printed table discrepancies; [rate-table source registry](v4/1993_upgrade/primary_source_transfer_tables_r3.yaml) and [historical NAMELIST input registry](v4/1993_upgrade/primary_source_input_defaults_r3.yaml).
- [1993 Table 2–8 software and 1991→1993 user-guide comparison R4](v4/1993_upgrade/PRIMARY_SOURCE_SOFTWARE_AND_CROSSEDITION_R4.md): historical IMSL/COMA and AUSBPF entrypoints, parameter-default changes, input migration and Table 1 g vs g/m² correction; [R4 evidence registry](v4/1993_upgrade/primary_source_software_and_crossedition_r4.yaml).
- [1990 / 1991 / 1993 physical equations audit R5](v4/1993_upgrade/PRIMARY_SOURCE_TRIEDITION_PHYSICS_R5.md): establishes 1991 pre-existing extended stomatal, soil hydraulic, and empirical day/night OBT processes; highlights the 1990 vs 1993 re-emission evaporation time-basis difference; [R5 machine-readable evidence](v4/1993_upgrade/primary_source_triedition_physics_r5.yaml). Original executable equivalence remains unestablished.
- [1993 UFOTRI 4.0 run, re-emission, diagnostics and hourly meteorology input audit R6](v4/1993_upgrade/PRIMARY_SOURCE_RUN_IO_AUDIT_R6.md): source cutoff, geometry, time clock, stationary legacy test branch, print controls, 10-field hourly met record and unresolved printed source constraints; [R6 source contract](v4/1993_upgrade/primary_source_run_io_contract_r6.yaml).
- [1993 ISOPAR wet washout and METPAR source-input audit R6b](v4/1993_upgrade/PRIMARY_SOURCE_INPUT_WASHOUT_R6.md): confirms original **IWASH=0 default three-class** versus optional `IWASH=1` power-law, original 0.01-scaled input units, ordered HT/HTO, and stationary-mode limitations; [R6b primary-source data](v4/1993_upgrade/primary_source_input_washout_r6.yaml). Complements the separately merged R6 run/clock evidence.
- [1993 METEOZON/SOURCE/END historical cards audit R7](v4/1993_upgrade/PRIMARY_SOURCE_METEOZON_SOURCE_R7.md): KfK5194 printed pp.36–41 compile caps, weather-sequence sampling/probability branches, staged thermal SOURCE cards and historic input END; [R7 card provenance](v4/1993_upgrade/primary_source_meteozon_source_r7.yaml). Source-only, no active 1993 parser or solver.
- [1991–1993 printed input-card comparison R8](v4/1993_upgrade/PRIMARY_SOURCE_INPUT_CARDS_CROSSEDITION_R8.md): pairs KfK4853 pp.10–15 with KfK5194 pp.36–41, flags positional K1.2 discrepancy and K2.2 mismatched printed FORMAT without inventing parser behavior; [R8 structured evidence and risk ledger](v4/1993_upgrade/primary_source_input_cards_crossedition_r8.yaml). Source-only; P0 stays open.
- [1991/1993 printed UFOTRI job-card examples R9](v4/1993_upgrade/PRIMARY_SOURCE_JOB_CARD_SAMPLES_R9.md): primary Table 3 (1991) and Table 5 (1993) SOURCE/METEOZON examples, discrepancy between visible tokens and printed field/FORMAT declarations; [R9 sample and unresolved reader evidence](v4/1993_upgrade/primary_source_job_card_samples_r9.yaml). No restored parser or 1993 solver.
- [Issue #126](https://github.com/RRain001/cufotri/issues/126): finish full source/parameter/equation audit and independent verification before starting version-specific physics rewrites.

The current software baseline and its acceptance status are still governed by `STATUS.md`, not by this proposed compatibility target.

## Physical equations and implementation boundaries

- [Variables and SI units](equations/variables_and_units.md)
- [Manual scope and implementation mapping](equations/manual_scope_and_mapping.md)
- [Atmospheric transport and deposition equations](equations/atmosphere.md)
- [Soil transport equations](equations/soil.md)
- [Plant transfer equations](equations/plant.md)
- [Evapotranspiration](equations/evapotranspiration.md)
- [Coupling contracts](equations/coupling.md)
- Formal source code: [`src/cteas_ufotri/`](../src/cteas_ufotri/), with separate atmospheric, soil, plant, food-chain, exposure and V3/V4 coupling components.

Physical equations and code must retain traceability to the available UFOTRI manual; a code-level PASS does not certify site-specific or empirical accuracy.

## Scientific validation and external inputs

- [Validation workspace](../validation/README.md): adapters, case contracts, reference comparisons, admissibility and provenance.
- [External evidence recovery](ci/EXTERNAL_EVIDENCE_RECOVERY.md): public upstream candidate sources, historical SHA, licensing and **missing** SB1/SB4/ERA5/D3 inputs.
- [Data-independent tests](../tests/): `tests/unit/`, `tests/integration/`, `tests/architecture/`, `tests/v3/`, `tests/v4/`.
- [SB1 source inventory](../validation/benchmarks/emras_soybean_sb1/source_inventory.yaml) and [SB4 source inventory](../validation/benchmarks/emras_soybean_sb4/source_inventory.yaml).

SB1/SB4 literature-derived and ERA5-based benchmarks remain separate from independent empirical qualification. D3 original private blind-key evidence must not be fabricated or treated as restored. `external-evidence.yml` is manually dispatched and fails closed in strict mode.

## Cloud development, containers and reproducibility

- [Docker + uv workflow](ci/DOCKER_WORKFLOW.md): Python 3.11 locked two-stage build, verification and minimal non-root runtime.
- [Dependency lock policy](ci/DEPENDENCY_LOCK.md): `pyproject.toml`, `.python-version`, `uv.lock` and controlled dependency updates.
- [GitHub Actions](../.github/workflows/): Protected Integration Gate, Remediation CI, Python smoke, Docker stage verification and manual evidence audit.
- [Agent development rules](../AGENTS.md): branch/PR workflow, provenance, physical equations and forbidden overclaims.
- [Root README](../README.md): starting point and reproducible commands.

The official Python 3.11 Docker base is identified by the digest in [Dockerfile](../Dockerfile). Build cache is only an acceleration mechanism, not a scientific data store or substitute for the committed dependency lock.

## Historical archives — preserve, do not restructure

| Archive | Purpose |
|---|---|
| [V2 documents](v2/) | Early HTO pathways, implementation and validation milestones |
| [V3 documents](v3/) | Physical database/evidence-governance experiments, frozen boundary and review decisions |
| [V3.1 documents](v3_1/) | Mass-basis follow-up and independent review |
| [V4 documents](v4/) | H1–H6, physics reconciliation, ADRs, audited evidence and technical reports |
| [Legacy implementation ledger](implementation_status.md) | Chronological record last updated in August 2026; **not** today's project authority |
| [Historical V1/V2 README](reference/legacy-readme-v2-20261022.md) | Original documentation retained for provenance |
| [Git cleanup history](history/) | SHA evidence and historical branch traceability |

Do not delete, move or combine frozen ADRs simply to simplify this index. Any future change to physical readiness should update `STATUS.md`, cite source evidence, and pass the applicable independent scientific gate.
