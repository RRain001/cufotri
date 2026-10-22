# IWASH=0 P1–Physics R1 — KfK5194 opt-in wet-source depletion

**Scope:** First P1-profiled physical computation, not the full UFOTRI 4.0 solver or complete P0 scientific acceptance. No original FORTRAN source/executable is available; no original-code numeric equivalence is claimed.

## Direct evidence

Official 1993 source: [KfK 5194 §7.3.3 printed pp.46–47 (PDF zero-based pp.55–56)](https://publikationen.bibliothek.kit.edu/270034158/3813483). The original PDF page images were independently inspected.

- `IWASH=0` is the historical default for `ISOPAR`, while `IWASH=1` is the separate optional power-law parameterization. In model-description §5.3.3 p.14 the author discusses and recommends the power law; **that recommendation is not the §7.3.3 NAMELIST default**.
- `IREGGR` source units are **0.01 mm/h**, with 100 and 300 corresponding to 1 and 3 mm/h. Classes are [0,1), [1,3), and [3,+∞) mm/h when rain is present.
- `AMDA(HT,IR)=0`, `AMDA(HTO,IR)=6e-5/1e-4/4e-4 s^-1`, with `REGTIM(HT,IR)=0` and `REGTIM(HTO,IR)=0.50/0.75/0.72`. At **zero precipitation**, active washout is zero even though class 1 *documented* coefficients exist.
- The source's isotope order is **HT first, HTO second**, and historical dry deposition velocities are `0.0005 / 0.005 m/s`.

## New physical API

`cteas_ufotri.atmosphere.kfk5194_1993_washout.kfk5194_iwash0_profiled_source_budget` requires an explicitly loaded `Historical1993SourceProfile`, explicit HT/HTO form, rain rate **mm/h**, source **Bq/s**, downwind **m**, wind **m/s**, source height/mixing lid **m**, stability class, and **explicit duration treatment**.

It reuses the existing H4/KfK4332 Eq.(2.20)/(2.27) dry+wet depletion budget and previously verified `kfk5194_washout` coefficient lookup. Its returned frozen data object provides the original `AMDA` parameter, the printed `REGTIM` value, **the actual modelled wet rate**, the atmospheric source remaining, dry/wet removed source (all Bq/s), the conservation residual, and a provenance record.

The documented source does not unambiguously expose how the original FORTRAN applies `REGTIM` to the full travel time. Therefore the numerical assumption is **never implicit**. Callers must choose one of:

- `MEAN_FRACTION_OF_TRAVEL`: independent reconstruction assumption: wet exposure time = `REGTIM * distance / wind speed`. Effective wet rate is `AMDA * REGTIM`.
- `FULL_RAIN_TRAVEL_UPPER_BOUND`: sensitivity comparison, using full travel time for wet exposure. Effective wet rate is `AMDA`.

These are **research interpretations**, not recovered original FORTRAN behavior; `SOURCE_LIMITED_NOT_ESTABLISHED` stays in every output. Full-rain treatment is an upper-exposure assumption for this simplified trajectory segment, not a bound for every possible future dynamic meteorology.

Example (opt-in, not the project CLI default):

```python
from cteas_ufotri.versioned_inputs_1993 import load_1993_source_profile
from cteas_ufotri.atmosphere.ufotri_native_v4 import TritiumAtmosphericForm
from cteas_ufotri.atmosphere.kfk5194_1993_washout import (
    KFK5194DurationTreatment,
    kfk5194_iwash0_profiled_source_budget,
)

p = load_1993_source_profile(
    "configs/ufotri_1993_manual_source_profile.yaml",
    selected_profile="KFK5194_1993_V4",
)
budget = kfk5194_iwash0_profiled_source_budget(
    profile=p,
    species=TritiumAtmosphericForm.HTO,
    precipitation_mm_h=2.0,
    source_bq_s=1e8,
    downwind_m=3000,
    wind_speed_m_s=5,
    effective_release_height_m=15,
    stability_class="D",
    mixing_lid_m=560,
    duration_treatment=KFK5194DurationTreatment.MEAN_FRACTION_OF_TRAVEL,
)
assert abs(budget.residual_bq_s) < 1e-7
```

## Quality gates and exclusions

Tests check class boundaries at 0, 1, and 3 mm/h, independently recompute the exponential wet-attenuation ratio, reject silent source edits, check isotope-specific zero wet removal for HT, verify mass conservation and mathematical dry/wet budget identity, and ensure legacy CLI/config remain untouched. No new default, no `IWASH=1` change, no changed existing solver/1990 output, no food-chain coupling, no field validation, and no general 1993 runtime activation. P0 remains OPEN; a whole-model 1993 physical certification requires an independent end-to-end scientific review.
