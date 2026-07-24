# UFOTRI manual equation inventory

Status:
`MANUAL_EQUATION_INVENTORY_STATUS = COMPLETE_FOR_AVAILABLE_MANUAL`

The available Markdown manual was reviewed from the model description through
the food-chain and dose sections, including numbered equations and parameter
tables. OCR defects are retained as source limitations; reviewed repository
equations override an inference from damaged OCR.

| Manual equations | Subject | V2 use and status |
|---|---|---|
| (1)-(3) | soil and plant HTO balances | inventory-form contract; `MANUAL_DERIVED` |
| (4)-(6) | area and point Gaussian sources | existing implementation; (4),(6) tested |
| (7)-(14) | resistance analogy, plant/canopy resistances | leaf-exchange basis; `MANUAL_DERIVED` |
| (15)-(25) | aerodynamic/boundary resistance and wind profile | selected resistance closure; (25) existing |
| (26)-(31) | bidirectional water/HTO exchange and equilibration | dynamic leaf exchange; `MANUAL_DERIVED` |
| (32) | OCR-ambiguous plant deposition relation | not treated as a deposition-velocity identity; reviewed interpretation required |
| (33)-(37) | soil potential, Darcy/Richards transport | three-box interface only; full PDE deferred |
| (38)-(43) | Penman ET, LAI shading, moisture reduction | existing implementation contract |
| (44-1),(44-2) | REEM, DIFF, ABFLR, C1/C2, ZT | audited empirical mode; `PROVISIONAL` until reproduced |
| (45)-(54) | plant-soil-atmosphere daily transfer system | benchmark/parameter anchors |
| (55)-(64) | three soil layers and nutrient-plant root uptake | optional three-box parameter anchors |
| (65)-(66) | vegetable HTO/OBT exchange | crop OBT anchors |
| (67)-(81) | grass-atmosphere and three-layer soil transfer | pasture/soil anchors |
| (82)-(84) | cow water loss to atmosphere/soil | minimal animal boundary-loss anchors |
| (85)-(91) | grass/cow to milk HTO and OBT | minimal milk pathway anchors |
| (92)-(97) | cow OBT turnover and formation | minimal animal OBT anchors |
| (98) | cow inhalation/skin uptake | animal exposure anchor, not public dose |
| (99)-(105-2) | grass-to-cow and grass HTO/OBT balance | minimal pasture-beef/milk anchors |
| (106) | inhalation plus skin dose | public dose anchor; skin separated diagnostically |
| (107) | ingestion dose | pathway-resolved public dose anchor |

## Unnumbered manual constraints

- HTO whole-plume washout uses rain-dependent coefficients; the manual's two
  rain classes are an available exact mode, while a power law is a documented
  V2 parameterization.
- Direct plant exchange is bidirectional. Day/night stomatal resistance,
  precipitation response, LAI, soil-water closure, and equilibrium fractionation
  must remain explicit.
- Only topsoil participates directly in soil evaporation. Manual ingestion
  soil layers are 0-5, 5-15, and 15-30 cm, with nutrient-crop root fractions
  20/40/40% and pasture fractions 40/60/0%.
- Eq. (44) is calibrated at 20% initial water, about 10% h-1 strong-insolation
  re-emission and about 1% h-1 initial nighttime diffusion. HTO-only uses C2=1.
- The manual's food-chain parameters are equilibrium-oriented daily transfer
  rates and explicitly imperfect balances. V2 inventory closure therefore
  treats harvest, milk, slaughter, excretion, and deep loss as boundaries.
- The manual uses one adult HTO coefficient and treats ingested OBT as HTO.
  V2's age-specific and separate OBT coefficients must come from versioned YAML
  and are a literature/project extension, not a manual-exact claim.

## Known source ambiguities

- Several headings contain transposed transfer-rate indices.
- Eq. (32) has an apparent concentration-ratio inversion in OCR.
- Some equation references in prose are shifted by four numbers.
- Table and appendix values use historical units and assumptions; conversion to
  SI is mandatory before use.

