# V3 P7.6C-2 UFOTRI source inventory

```text
P7_6C2_STATUS = PASS_SOURCE_INVENTORY_COMPLETE
UFOTRI_ORIGINAL_SOURCE_CODE = SOURCE_UNAVAILABLE
UFOTRI_MANUAL_AVAILABLE = TRUE
SOURCE_ASSETS_INSPECTED = 21
```

## Scope and evidence rule

This inventory separates original UFOTRI material from project-derived
contracts and from V3 implementation code. The recovered UFOTRI authority is
the Markdown transcription of W. Raskob, *UFOTRI Program for Assessing
Off-Site Consequences of Tritium Releases*, KfK 4605, Institut für
Neutronenphysik und Reaktortechnik, Kernforschungszentrum Karlsruhe. The
manual text does not print a software version/date in its front matter. Its
SHA-256 at audit time is
`82c7c7f07975553a51e7ba1666a912f80096e5af4fc138aba6f45a120e6d3562` and it
contains 3569 lines.

The audit maps a recovered definition only when its equation role, unit,
compartment, and time/state basis can be stated. A filename or familiar
symbol is not evidence of an original UFOTRI definition. No value is selected
or imported by this stage.

## Original and project source assets

| Source ID | Asset | Role and availability | Relevant coverage |
|---|---|---|---|
| `ufotri.manual.kfk4605` | `ufotri_manual.md` | Original manual transcription; available | Eq. (1)-(3) soil/plant HTO, Eq. (7)-(31) leaf exchange, Eq. (33)-(44) soil/re-emission, Eq. (45)-(105) food chain, Eq. (106)-(107) dose |
| `project.manual.scope.mapping` | `docs/equations/manual_scope_and_mapping.md` | Project-derived scope contract; available | Manual-to-V3 state and deferred-boundary mapping |
| `project.v2.manual.inventory` | `docs/v2/manual_equation_inventory.md` | Project audit inventory; available | Numbered equation coverage and known manual ambiguities |
| `project.v2.manual.matrix` | `docs/v2/manual_to_code_matrix.md` | Project audit matrix; available | Unified quantity, code target, and limitation boundaries |
| `project.v3.plant.equations` | `docs/equations/plant.md` | V3 equation contract; available | Leaf exchange, TFWT, OBT, root and deferred pathway boundaries |
| `project.v3.soil.equations` | `docs/equations/soil.md` | V3 equation contract; available | One-layer soil inventory and signed transport interface |
| `project.v3.variables.units` | `docs/equations/variables_and_units.md` | V3 unit contract; available | Canonical inventory, concentration, flux, and rate units |
| `project.d3.manual.field.mapping` | `validation/external_evidence_acquisition/d3/d3_ufotri_manual_data_field_mapping.yaml` | Prior D3 data-field mapping; available, not an original UFOTRI source | Data/provenance field handoff only; not an equation authority |

The eight documentation assets above were hashed during the audit. The
remaining thirteen assets were read as current V3 contracts or evidence
control-plane inputs:

| Asset group | Files inspected |
|---|---|
| V3 resistance/plant | `src/cteas_ufotri/plant/leaf_exchange_resistance/resistance.py`; `plant/tfwt_v3/tfwt_solver.py`; `plant/tfwt_v3/tfwt_state.py`; `plant/obt_v3/obt_solver.py` |
| V3 soil/root/food/exposure | `plant/root_v3/root_solver.py`; `plant/soil_v3/soil_solver.py`; `plant/soil_v3/soil_state.py`; `plant/food_v3/food_transfer_solver.py`; `exposure/intake_v3/intake_solver.py`; `exposure/dose_v3/dose_solver.py` |
| V3 evidence status | `docs/v3/parameter_evidence/parameter_inventory.yaml`; `parameter_candidate_registry.yaml`; `physical_constant_validation_registry.yaml` |

## Original-source availability findings

The repository contains the manual and project audits, but no tracked
UFOTRI/UFOMOD/MUSEMET source-code or executable asset was recovered. A tracked
source-extension search returned only `ufotri_manual.md`; virtual-environment
packages and caches were excluded from the source inventory. Therefore the
following are explicitly unavailable:

1. the original UFOTRI source implementation and its versioned parameter
   loader;
2. exact original software field names for values described only in the
   manual prose or tables;
3. an original executable regression case that could establish numerical
   equivalence with V3.

This does not make the manual unavailable. It means that any mapping requiring
software-specific semantics, undocumented defaults, or a hidden conversion is
not admitted as a direct mapping.

## Source-to-subsystem index

| V3 subsystem | Recovered UFOTRI source | Main anchors | Source disposition |
|---|---|---|---|
| leaf | `ufotri.manual.kfk4605` | Eq. (12)-(14), (19), (21), (26)-(31) | exact resistance-component roles recoverable; values not selected |
| TFWT | `ufotri.manual.kfk4605` | Eq. (3), (27)-(31) | state/flux roles recoverable; rate-to-flux conversion remains explicit |
| OBT | `ufotri.manual.kfk4605` | OBT text near Sec. 2.2.6, Eq. (65)-(66), Eq. (105) | first-order roles partly compatible; day/night/organic-compartment limits retained |
| soil | `ufotri.manual.kfk4605` | Eq. (1)-(2), (33)-(44) | flux and water-basis definitions recoverable; multi-layer hydraulic implementation not imported |
| root | `ufotri.manual.kfk4605` | Sec. 2.2.5, Eq. (57)-(60), (75)-(77) | layer rate/transpiration mechanism is conceptual relative to V3 m/s |
| food | `ufotri.manual.kfk4605` | Eq. (45)-(105), Sec. 4.3 | continuous food-chain compartments; no V3 harvest-event fraction |
| intake | `ufotri.manual.kfk4605` | Eq. (107), Table 8 human diet | consumption rate role available, explicit V3 food-mass denominator unavailable |
| dose | `ufotri.manual.kfk4605` | Eq. (106)-(107), Sec. 4.1 | dose-coefficient role available; coefficient is external/selected, not UFOTRI physics evidence |

The canonical machine-readable mapping is
`docs/v3/parameter_evidence/ufotri_parameter_mapping.yaml`. It is a
control-plane manifest and is intentionally not a runtime input.
