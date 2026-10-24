# P2 R12 — Mitchell (1991) archived-primary location and Eq.(30) proof obligations

**Disposition: PRIMARY_PDF_LOCATED_ACCESS_DENIED / EQUATIONS_NOT_READ / COUPLING_BLOCKED.**
This audit supplements R9–R11 for P0 #126 and P2 #128. It is an access/provenance audit and a dimensional *proof-obligation* worksheet, **not** equation validation, an assumption that Mitchell's coefficients equal those printed in KfK 5194, or UFOTRI original-code parity.

## Reproducible source-identification results — 2026-10-24

- Bibliographic target: R. A. C. Mitchell, D. W. Lawlor, A. T. Young (1991), *Dark Respiration of Winter Wheat Crops in Relation to Temperature and Simulated Photosynthesis*, *Annals of Botany* 67(1), pp. 7–16; DOI `10.1093/oxfordjournals.aob.a088102`; publisher record https://academic.oup.com/aob/article-abstract/67/1/7/257984 .
- Newly identified authoritative institutional article record: https://repository.rothamsted.ac.uk/item/86731/dark-respiration-of-winter-wheat-crops-in-relation-to-temperature-and-simulated-photosynthesis ; redirects to https://repository.rothamsted.ac.uk/id/eprint/5335/ .
- Corresponding institutional full-text asset *locator only*: https://repository.rothamsted.ac.uk/id/eprint/5335/1/42758396.pdf . A GET via the host's configured HTTP(S) proxy returned **401 Unauthorized** on 2026-10-24; the institutional item returned **200**. **No PDF bytes were acquired, no page rendered, no PDF checksum exists, and no original equation or table from Mitchell was inspected.**
- Independent DOI identity/discovery registry: OpenAlex work `W2401308966`, https://openalex.org/W2401308966 . The live OpenAlex API record `https://api.openalex.org/works/https://doi.org/10.1093/oxfordjournals.aob.a088102` lists the institutional item/PDF locators, with `open_access.is_oa=false`, `oa_status=closed`, `best_oa_location=null`; metadata indexing a PDF link **does not grant full-text access**.
- The publisher abstract is available, but the publisher/full-methods article could not be retrieved on the research host. This is `FULL_TEXT_EQUATIONS_NOT_RUN`, not a negative scientific finding and not grounds to infer a historical formula.
- Do not commit copied PDFs, publisher text, login tokens, credentials, or an invented SHA256.

## What the *published abstract* supports (not its unavailable methods)

1. Whole winter-wheat crop shoot respiration was measured before anthesis; ears after anthesis. Measurements include 1982 and 1985 crops with irrigation/fertilization contrasts, 12–14 h dark intervals, hourly measurements; normalization is described as **per unit dry mass**. These are publisher-abstract facts, not original formula transcriptions.
2. The abstract reports shoot-respiration correlation is stronger with the preceding **two-day mean** of simulated photosynthesis than with the preceding single day. That correlation statement is **not** a verified computational lag in KfK 5194 Eq.(30).
3. The abstract's approximate ~35% pre-anthesis and ~40% late-ear growth-respiration assimilation consumption are stage-dependent descriptive findings, **not** documented substitutions for KfK 5194 Eq.(30) coefficients `0.36` and `1.67e-4`. Do not use these percentages to calibrate a new 1993 solver.
4. Neither abstract nor OpenAlex metadata shows an Eq.(30) derivation, `W` mapping, crop-organ aggregation, or the historical iteration order of `Pc` and `Rd`.

## Minimum dimensional bridge to prove *before* implementing Eq.(30)

KfK 5194 (1993) §5.5.1 printed Eq.(30) is `Rd = 0.36*Pc + 1.67e-4*W`, with `W` labelled as `g CO2 equivalent / m²` (see R9 primary-PDF gate); it does not itself show how Mitchell's per-unit-*dry-mass* respiration becomes this quantity. The following identities are **conditional algebra**, not original UFOTRI equations:

- Let `M_dry,G` have units `g dry matter / m² ground` and let an independently substantiated conversion `c_eq` have units `g CO2 equivalent / g dry matter`. Then and **only with such a documented conversion**: `W_G = c_eq * M_dry,G`, in `g CO2 equivalent / m² ground`. `c_eq` is **unknown**, not assumed to be 1, 0.65, 1.5, or a fixed crop-independent constant.
- If `r_m` is measured per unit dry mass and unit time, its ground-area equivalent requires the same organ/time-specific `M_dry,G`: `R_G = r_m * M_dry,G`. This is a dimensional identity and cannot be used numerically without the original paper's actual rate and mass units, biomass time, organ partition and conversion to the target `Rd` representation.
- If `Pc` and `Rd` are on different *leaf* vs *ground* area bases, they cannot be added directly. A per-leaf-area flux maps to per-ground-area flux by an **appropriate canopy integral** over leaf-area index, not an unconditionally assumed scalar LAI multiplier. LAI=0 / varying-illumination / organ partition are discriminating tests still required.
- Under the **hypothesis**, *not established as the manual's effective conventions*, that `Pc` and `Rd` are both `g CO2 equivalent m^-2 ground h^-1` and `W` is `g CO2 equivalent m^-2 ground`, the dimension of the coefficient multiplying `W` must be `h^-1`; `0.36` is dimensionless. This says **nothing** about whether KfK5194 actually intends precisely these bases.
- A faithful Eq.(30) implementation would additionally need the original-time `Pc` evaluation, `Rd` solve/iteration ordering and consistency with printed Eq.(28), Eq.(31) `COA`, and stage-dependent shoot/ear versus whole-crop assumptions. Each remains `NOT_ESTABLISHED`.

## Access/review handoff and release rule

Authorized follow-up: obtain the exact Mitchell publisher/institutional full-text PDF through a legitimate university/library or rights-holder request, independently verify bibliographic identity, page numbers and SHA256, visually review equations/tables and units, then compare with KfK5194 Eq.(30). A primary paper read **still would not** prove original-executable parity without original UFOTRI source/executable and same-input outputs. Record external reviewer and decision on an exact commit.

**Blocking remains:** `eq30_dry_matter_to_w_bridge=NOT_ESTABLISHED`, `eq30_respiration_area_basis=NOT_ESTABLISHED`, `eq28_eq30_original_solve_order=NOT_ESTABLISHED`, `mitchell_full_text_equation_review=NOT_RUN`, independent scientific review `NOT_RUN`; production coupling forbidden. No changes to existing `src/`, `configs/`, 1990 default, thresholds, or CI admission. PR #159 remains Draft; no `science-validated` / `merge-verified`, no merge.
