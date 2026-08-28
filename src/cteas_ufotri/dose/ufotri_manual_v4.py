"""Opt-in UFOTRI public-exposure compatibility path for KfK 4605 Eq. (106)-(107).

The historical UFOTRI manual and the retained modern application dose path use
different coefficient and food-class policies. This module reconstructs only
the recoverable manual semantics:

* Eq. (106): HTO inhalation plus skin absorption equal to 50% of inhalation;
* Eq. (107): ingestion of one representative green vegetable, beef, and milk;
* HTO and OBT food activity are tracked separately upstream but added before
  dose calculation and use the same selected dose coefficient.

The existing ``dose.public.calculate_public_dose_step`` remains the modern
application path with age-specific HTO/OBT coefficients and expanded foods.
No breathing/consumption habit is inferred here; all habits are explicit inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

SECONDS_PER_DAY = 86400.0
MANUAL_ADULT_REFERENCE_DF_SV_BQ = 1.7e-11
MANUAL_QUALITY_FACTOR = 1.0
MANUAL_SKIN_TO_INHALATION_FRACTION = 0.5
MANUAL_REFERENCE_POLICY_ID = "KFK4605_EQ106_107_ADULT_REFERENCE_R1"


class UFOTRIExposureInputError(ValueError):
    """Fail-closed error for the isolated UFOTRI manual exposure path."""


def _finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UFOTRIExposureInputError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise UFOTRIExposureInputError(f"{field} must be finite")
    return result


def _nonnegative(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if result < 0.0:
        raise UFOTRIExposureInputError(f"{field} must be non-negative")
    return result


def _required_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UFOTRIExposureInputError(f"{field} is required")
    return value.strip()


@dataclass(frozen=True)
class UFOTRIManualDosePolicy:
    """Explicit Eq. (106)-(107) coefficient policy.

    ``dose_coefficient_sv_bq`` is deliberately required: the manual states that
    the coefficient is selected for the integration time and exposed age group.
    ``ufotri_manual_adult_reference_policy`` is a convenience constructor for
    the manual's stated adult reference value of 1.7e-11 Sv/Bq.
    """

    dose_coefficient_sv_bq: float
    coefficient_id: str
    source_reference: str
    quality_factor: float = MANUAL_QUALITY_FACTOR
    skin_to_inhalation_fraction: float = MANUAL_SKIN_TO_INHALATION_FRACTION
    ingested_obt_uses_hto_coefficient: bool = True
    production_binding_authorized: bool = False
    modern_application_policy: bool = False

    def __post_init__(self) -> None:
        if _nonnegative(
            self.dose_coefficient_sv_bq, field="dose_coefficient_sv_bq"
        ) <= 0.0:
            raise UFOTRIExposureInputError("dose_coefficient_sv_bq must be positive")
        _required_text(self.coefficient_id, field="coefficient_id")
        _required_text(self.source_reference, field="source_reference")
        if _finite(self.quality_factor, field="quality_factor") != MANUAL_QUALITY_FACTOR:
            raise UFOTRIExposureInputError(
                "manual Eq.106/107 compatibility requires QF=1"
            )
        if (
            _finite(
                self.skin_to_inhalation_fraction,
                field="skin_to_inhalation_fraction",
            )
            != MANUAL_SKIN_TO_INHALATION_FRACTION
        ):
            raise UFOTRIExposureInputError(
                "manual Eq.106 compatibility requires skin absorption = 50% of inhalation"
            )
        if not self.ingested_obt_uses_hto_coefficient:
            raise UFOTRIExposureInputError(
                "manual UFOTRI ingestion treats OBT with the selected HTO dose coefficient"
            )
        if self.production_binding_authorized:
            raise UFOTRIExposureInputError(
                "D5 does not authorize production coefficient binding"
            )
        if self.modern_application_policy:
            raise UFOTRIExposureInputError(
                "modern application coefficients belong to dose.public, not the manual path"
            )


@dataclass(frozen=True)
class UFOTRIManualConsumptionRates:
    """Explicit receptor habits required by Eq. (106)-(107)."""

    breathing_rate_m3_s: float
    green_vegetable_kg_d: float
    beef_kg_d: float
    milk_kg_d: float
    provenance_id: str

    def __post_init__(self) -> None:
        for field in (
            "breathing_rate_m3_s",
            "green_vegetable_kg_d",
            "beef_kg_d",
            "milk_kg_d",
        ):
            _nonnegative(getattr(self, field), field=field)
        _required_text(self.provenance_id, field="provenance_id")


@dataclass(frozen=True)
class UFOTRIFoodSpecificActivity:
    """Instantaneous food activity used only to build Eq. (107) integrals.

    Units are Bq/kg for both HTO and OBT. The manual Eq. (107) is mass based;
    this module performs no implicit litre-to-kilogram conversion for milk.
    """

    hto_bq_kg: float
    obt_bq_kg: float

    def __post_init__(self) -> None:
        _nonnegative(self.hto_bq_kg, field="hto_bq_kg")
        _nonnegative(self.obt_bq_kg, field="obt_bq_kg")


@dataclass(frozen=True)
class UFOTRIManualFoodSnapshot:
    """The three representative food classes explicitly present in Eq. (107)."""

    green_vegetable: UFOTRIFoodSpecificActivity
    beef: UFOTRIFoodSpecificActivity
    milk: UFOTRIFoodSpecificActivity

    def __post_init__(self) -> None:
        for field in ("green_vegetable", "beef", "milk"):
            if not isinstance(getattr(self, field), UFOTRIFoodSpecificActivity):
                raise UFOTRIExposureInputError(
                    f"{field} must be UFOTRIFoodSpecificActivity"
                )


@dataclass(frozen=True)
class UFOTRIManualExposureState:
    """Time-integrated Eq. (106)-(107) exposure quantities.

    Air is Bq s m-3. Food terms are Bq d kg-1. Keeping the manual's integral
    units explicit makes the equations additive under arbitrary time partition.
    """

    elapsed_s: float
    air_hto_bq_s_m3: float
    green_vegetable_hto_bq_d_kg: float
    green_vegetable_obt_bq_d_kg: float
    beef_hto_bq_d_kg: float
    beef_obt_bq_d_kg: float
    milk_hto_bq_d_kg: float
    milk_obt_bq_d_kg: float
    exposure_provenance_id: str

    def __post_init__(self) -> None:
        for field in (
            "elapsed_s",
            "air_hto_bq_s_m3",
            "green_vegetable_hto_bq_d_kg",
            "green_vegetable_obt_bq_d_kg",
            "beef_hto_bq_d_kg",
            "beef_obt_bq_d_kg",
            "milk_hto_bq_d_kg",
            "milk_obt_bq_d_kg",
        ):
            _nonnegative(getattr(self, field), field=field)
        _required_text(self.exposure_provenance_id, field="exposure_provenance_id")

    @classmethod
    def zero(cls, *, exposure_provenance_id: str) -> "UFOTRIManualExposureState":
        return cls(
            elapsed_s=0.0,
            air_hto_bq_s_m3=0.0,
            green_vegetable_hto_bq_d_kg=0.0,
            green_vegetable_obt_bq_d_kg=0.0,
            beef_hto_bq_d_kg=0.0,
            beef_obt_bq_d_kg=0.0,
            milk_hto_bq_d_kg=0.0,
            milk_obt_bq_d_kg=0.0,
            exposure_provenance_id=exposure_provenance_id,
        )


@dataclass(frozen=True)
class UFOTRIManualDoseResult:
    """Pathway-resolved manual-fidelity individual dose."""

    inhalation_dose_sv: float
    skin_absorption_dose_sv: float
    green_vegetable_ingestion_dose_sv: float
    beef_ingestion_dose_sv: float
    milk_ingestion_dose_sv: float
    ingestion_dose_sv: float
    total_effective_dose_sv: float
    inhaled_hto_bq: float
    ingested_hto_bq: float
    ingested_obt_bq: float
    eq106_residual_sv: float
    eq107_residual_sv: float

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            value = _finite(getattr(self, field), field=field)
            if field not in {"eq106_residual_sv", "eq107_residual_sv"} and value < 0.0:
                raise UFOTRIExposureInputError(f"{field} must be non-negative")


@dataclass(frozen=True)
class UFOTRIExposurePolicyBoundary:
    """Machine-readable separation between manual and modern exposure policies."""

    manual_module: str = "cteas_ufotri.dose.ufotri_manual_v4"
    modern_application_module: str = "cteas_ufotri.dose.public"
    manual_food_classes: tuple[str, str, str] = (
        "green_vegetable",
        "beef",
        "milk",
    )
    manual_drinking_water_in_eq107: bool = False
    manual_root_crop_in_eq107: bool = False
    manual_grain_in_eq107: bool = False
    manual_separate_obt_coefficient: bool = False
    modern_age_specific_coefficients_retained: bool = True
    modern_separate_obt_coefficient_retained: bool = True
    existing_modern_path_replaced: bool = False
    production_binding_authorized: bool = False

    def __post_init__(self) -> None:
        if self.manual_food_classes != ("green_vegetable", "beef", "milk"):
            raise UFOTRIExposureInputError(
                "manual Eq.107 food classes must remain green vegetable, beef, and milk"
            )
        forbidden = (
            self.manual_drinking_water_in_eq107,
            self.manual_root_crop_in_eq107,
            self.manual_grain_in_eq107,
            self.manual_separate_obt_coefficient,
            self.existing_modern_path_replaced,
            self.production_binding_authorized,
        )
        if any(forbidden):
            raise UFOTRIExposureInputError(
                "manual/modern exposure policy boundary was violated"
            )
        if not self.modern_age_specific_coefficients_retained:
            raise UFOTRIExposureInputError(
                "D5 must retain the modern age-specific application policy"
            )
        if not self.modern_separate_obt_coefficient_retained:
            raise UFOTRIExposureInputError(
                "D5 must retain the modern separate OBT application coefficient"
            )


def ufotri_manual_adult_reference_policy() -> UFOTRIManualDosePolicy:
    """Return the manual's stated adult HTO reference coefficient."""

    return UFOTRIManualDosePolicy(
        dose_coefficient_sv_bq=MANUAL_ADULT_REFERENCE_DF_SV_BQ,
        coefficient_id=MANUAL_REFERENCE_POLICY_ID,
        source_reference="KfK4605_4.1_4.3_Eq106_107",
    )


def ufotri_exposure_policy_boundary() -> UFOTRIExposurePolicyBoundary:
    return UFOTRIExposurePolicyBoundary()


def advance_ufotri_manual_exposure(
    state: UFOTRIManualExposureState,
    *,
    dt_s: float,
    air_hto_bq_m3: float,
    foods: UFOTRIManualFoodSnapshot,
) -> UFOTRIManualExposureState:
    """Accumulate constant-within-step concentrations into manual integral units."""

    if not isinstance(state, UFOTRIManualExposureState):
        raise UFOTRIExposureInputError("state must be UFOTRIManualExposureState")
    if not isinstance(foods, UFOTRIManualFoodSnapshot):
        raise UFOTRIExposureInputError("foods must be UFOTRIManualFoodSnapshot")
    dt = _finite(dt_s, field="dt_s")
    if dt <= 0.0:
        raise UFOTRIExposureInputError("dt_s must be strictly positive")
    air = _nonnegative(air_hto_bq_m3, field="air_hto_bq_m3")
    day_fraction = dt / SECONDS_PER_DAY

    return UFOTRIManualExposureState(
        elapsed_s=state.elapsed_s + dt,
        air_hto_bq_s_m3=state.air_hto_bq_s_m3 + air * dt,
        green_vegetable_hto_bq_d_kg=(
            state.green_vegetable_hto_bq_d_kg
            + foods.green_vegetable.hto_bq_kg * day_fraction
        ),
        green_vegetable_obt_bq_d_kg=(
            state.green_vegetable_obt_bq_d_kg
            + foods.green_vegetable.obt_bq_kg * day_fraction
        ),
        beef_hto_bq_d_kg=(
            state.beef_hto_bq_d_kg + foods.beef.hto_bq_kg * day_fraction
        ),
        beef_obt_bq_d_kg=(
            state.beef_obt_bq_d_kg + foods.beef.obt_bq_kg * day_fraction
        ),
        milk_hto_bq_d_kg=(
            state.milk_hto_bq_d_kg + foods.milk.hto_bq_kg * day_fraction
        ),
        milk_obt_bq_d_kg=(
            state.milk_obt_bq_d_kg + foods.milk.obt_bq_kg * day_fraction
        ),
        exposure_provenance_id=state.exposure_provenance_id,
    )


def calculate_ufotri_manual_dose(
    state: UFOTRIManualExposureState,
    *,
    habits: UFOTRIManualConsumptionRates,
    policy: UFOTRIManualDosePolicy,
) -> UFOTRIManualDoseResult:
    """Evaluate literal manual Eq. (106)-(107) from integrated exposures."""

    if not isinstance(state, UFOTRIManualExposureState):
        raise UFOTRIExposureInputError("state must be UFOTRIManualExposureState")
    if not isinstance(habits, UFOTRIManualConsumptionRates):
        raise UFOTRIExposureInputError("habits must be UFOTRIManualConsumptionRates")
    if not isinstance(policy, UFOTRIManualDosePolicy):
        raise UFOTRIExposureInputError("policy must be UFOTRIManualDosePolicy")

    df = policy.dose_coefficient_sv_bq
    qf = policy.quality_factor

    inhaled_hto_bq = habits.breathing_rate_m3_s * state.air_hto_bq_s_m3
    inhalation = inhaled_hto_bq * df * qf
    skin = inhalation * policy.skin_to_inhalation_fraction
    eq106_expected = (
        habits.breathing_rate_m3_s
        * df
        * state.air_hto_bq_s_m3
        * qf
        * (1.0 + policy.skin_to_inhalation_fraction)
    )

    green_hto_bq = habits.green_vegetable_kg_d * state.green_vegetable_hto_bq_d_kg
    green_obt_bq = habits.green_vegetable_kg_d * state.green_vegetable_obt_bq_d_kg
    beef_hto_bq = habits.beef_kg_d * state.beef_hto_bq_d_kg
    beef_obt_bq = habits.beef_kg_d * state.beef_obt_bq_d_kg
    milk_hto_bq = habits.milk_kg_d * state.milk_hto_bq_d_kg
    milk_obt_bq = habits.milk_kg_d * state.milk_obt_bq_d_kg

    green = (green_hto_bq + green_obt_bq) * df * qf
    beef = (beef_hto_bq + beef_obt_bq) * df * qf
    milk = (milk_hto_bq + milk_obt_bq) * df * qf
    ingestion = green + beef + milk
    ingested_hto_bq = green_hto_bq + beef_hto_bq + milk_hto_bq
    ingested_obt_bq = green_obt_bq + beef_obt_bq + milk_obt_bq
    eq107_expected = (ingested_hto_bq + ingested_obt_bq) * df * qf

    eq106_residual = (inhalation + skin) - eq106_expected
    eq107_residual = ingestion - eq107_expected
    total = inhalation + skin + ingestion

    return UFOTRIManualDoseResult(
        inhalation_dose_sv=inhalation,
        skin_absorption_dose_sv=skin,
        green_vegetable_ingestion_dose_sv=green,
        beef_ingestion_dose_sv=beef,
        milk_ingestion_dose_sv=milk,
        ingestion_dose_sv=ingestion,
        total_effective_dose_sv=total,
        inhaled_hto_bq=inhaled_hto_bq,
        ingested_hto_bq=ingested_hto_bq,
        ingested_obt_bq=ingested_obt_bq,
        eq106_residual_sv=eq106_residual,
        eq107_residual_sv=eq107_residual,
    )


__all__ = [
    "MANUAL_ADULT_REFERENCE_DF_SV_BQ",
    "MANUAL_QUALITY_FACTOR",
    "MANUAL_REFERENCE_POLICY_ID",
    "MANUAL_SKIN_TO_INHALATION_FRACTION",
    "SECONDS_PER_DAY",
    "UFOTRIExposureInputError",
    "UFOTRIExposurePolicyBoundary",
    "UFOTRIFoodSpecificActivity",
    "UFOTRIManualConsumptionRates",
    "UFOTRIManualDosePolicy",
    "UFOTRIManualDoseResult",
    "UFOTRIManualExposureState",
    "UFOTRIManualFoodSnapshot",
    "advance_ufotri_manual_exposure",
    "calculate_ufotri_manual_dose",
    "ufotri_exposure_policy_boundary",
    "ufotri_manual_adult_reference_policy",
]
