# P3 R2 — KfK5194 (1993) night and rain canopy resistance

**P3 next physical increment, opt-in and explicitly source-limited.** Published authority: [KfK 5194 (1993), §5.2](https://publikationen.bibliothek.kit.edu/270034158/3813483), printed pp.4–5 / PDF indices 13–14, especially the paragraph between Eq.(9) and Eq.(10), independently checked in the original page image. Also see [P3 R1](P3_R1_CANOPY_MONTEITH.md).

## Source-supported qualitative branches

The printed 1993 manual states that (i) at night stomata close and transfer is via the leaf epidermis, with resistance at least approximately 10–15 times higher than stomatal resistance; (ii) daytime rainfall makes stomatal resistance very small, so atmospheric resistance dominates; and (iii) nighttime rainfall does not alter the epidermal resistance. **The manual does not provide a unique numerical rainy-day leaf resistance, a universally valid night epidermal resistance, or the original FORTRAN branch operators.** These are not silently invented.

## Code and units

`src/cteas_ufotri/plant/kfk5194_1993_canopy_regimes.py` provides `kfk5194_1993_rain_night_canopy` with explicit `KFK5194_1993_V4` source profile and enumerated regimes:

- `DAY_RAIN_EXPLICIT_FINITE`: caller provides a positive, explicitly supported wet leaf resistance smaller than its stated dry-day reference. **No universal rain resistance default**.
- `DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT`: explicitly chooses **zero leaf resistance as a limiting idealization**, retaining nonzero aerodynamic and boundary-layer resistance. It is NOT asserted to be the exact 1993 FORTRAN calculation or the only day-rain mode.
- `NIGHT_DRY_EPIDERMAL` and `NIGHT_RAIN_EPIDERMAL`: explicit epidermal resistance and a separately supplied dry-day reference. The implementation screens values below the printed 10× qualitative lower ratio; rain does **not** alter the epidermal input. The ratio constraint is a documented approximation, **not recovered original numeric branch logic**.

The R2 routine evaluates `r_av=u/u_*²` and `r_bv=1/(u_* B)` (s/m), then leaf total `r_leaf+r_av+r_bv` and canopy total `r_leaf/LAI+r_av+r_bv`. Effective exchange velocity is `1/r_total` (m/s), including the exact mathematical daytime rain zero-resistance limit. This bypasses the frozen RC1's strictly-positive component validator, **without any epsilon substitution or legacy change**.

The model returns its source/limitation tags and requires site/crop-provided leaf/epidermal and atmospheric parameters. For P3 R2, the nighttime/rain resistance result is **not** coupled to a full-night Monteith evapotranspiration calculation: nighttime net radiation and condensation/negative latent flux demand separate model review.

## Verification and boundaries

Tests check numerical resistance and velocity, limit-vs-finite daytime rain, exact nightly rain/dry equality for the same external conditions, parameter non-negativity, cross-regime input exclusion, conservative 10× minimum ratio, explicit model-version identity, and no old CLI/solver modifications.

This is a **manual-based opt-in independent reconstruction only**; KfK 5194 (1993) is normative. P0 audit #126 remains OPEN. No full 1993 solver activation, field validation, original-executable equivalence, default parameter fallback, or legacy 1990 solver behavior changes.
