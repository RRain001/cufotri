from __future__ import annotations

from dataclasses import dataclass

from ..soil.hto_balance import limit_inventory_outflows


@dataclass(frozen=True)
class AnimalState:
    body_hto_bq: float = 0.0
    body_obt_bq: float = 0.0

    @property
    def total_bq(self) -> float:
        return self.body_hto_bq + self.body_obt_bq


@dataclass(frozen=True)
class EcologicalMassClosure:
    initial_bq: float
    input_bq: float
    boundary_output_bq: float
    decay_bq: float
    final_bq: float

    @property
    def residual_bq(self) -> float:
        return (
            self.initial_bq
            + self.input_bq
            - self.boundary_output_bq
            - self.decay_bq
            - self.final_bq
        )

    @property
    def relative_error(self) -> float:
        scale = max(
            abs(self.initial_bq) + abs(self.input_bq),
            abs(self.boundary_output_bq) + abs(self.decay_bq) + abs(self.final_bq),
            1.0e-30,
        )
        return abs(self.residual_bq) / scale


@dataclass(frozen=True)
class AnimalDiagnostics:
    feed_hto_input_bq_s: float
    feed_obt_input_bq_s: float
    water_hto_input_bq_s: float
    milk_hto_output_bq_s: float
    milk_obt_output_bq_s: float
    excretion_output_bq_s: float
    slaughter_output_bq_s: float
    milk_hto_bq_l: float
    milk_obt_bq_l: float
    beef_hto_bq_kg: float
    beef_obt_bq_kg: float
    closure: EcologicalMassClosure


def step_animal(
    state: AnimalState,
    dt_s: float,
    feed_hto_bq_kg_fresh: float,
    feed_obt_bq_kg_fresh: float,
    drinking_water_hto_bq_l: float,
    config: dict,
    *,
    slaughter_event: bool = False,
    feed_hto_input_bq_m2_s: float | None = None,
    feed_obt_input_bq_m2_s: float | None = None,
) -> tuple[AnimalState, AnimalDiagnostics]:
    if dt_s <= 0:
        raise ValueError("Animal time step must be positive")
    area = max(float(config["animal_support_area_m2"]), 0.0)
    if area <= 0:
        raise ValueError("Animal support area must be positive")
    feed_rate = (
        max(float(config["feed_intake_kg_fresh_day"]), 0.0) / 86400.0 / area
    )
    water_rate = max(float(config["drinking_water_l_day"]), 0.0) / 86400.0 / area
    feed_hto = (
        feed_rate * max(feed_hto_bq_kg_fresh, 0.0)
        if feed_hto_input_bq_m2_s is None
        else max(feed_hto_input_bq_m2_s, 0.0)
    )
    feed_obt = (
        feed_rate * max(feed_obt_bq_kg_fresh, 0.0)
        if feed_obt_input_bq_m2_s is None
        else max(feed_obt_input_bq_m2_s, 0.0)
    )
    water_hto = water_rate * max(drinking_water_hto_bq_l, 0.0)
    if slaughter_event:
        feed_hto = feed_obt = water_hto = 0.0
    formation = max(float(config["obt_formation_rate_s"]), 0.0) * state.body_hto_bq
    turnover = max(float(config["obt_turnover_rate_s"]), 0.0) * state.body_obt_bq
    if slaughter_event:
        formation = turnover = 0.0
    hto_out = limit_inventory_outflows(
        state.body_hto_bq,
        dt_s,
        formation=formation,
        milk=0.0 if slaughter_event else max(float(config["milk_hto_transfer_rate_s"]), 0.0)
        * state.body_hto_bq,
        excretion=0.0 if slaughter_event else max(float(config["hto_excretion_rate_s"]), 0.0)
        * state.body_hto_bq,
        decay=0.0 if slaughter_event else max(float(config["decay_rate_s"]), 0.0) * state.body_hto_bq,
        slaughter=state.body_hto_bq / dt_s if slaughter_event else 0.0,
    )
    obt_out = limit_inventory_outflows(
        state.body_obt_bq,
        dt_s,
        turnover=turnover,
        milk=0.0 if slaughter_event else max(float(config["milk_obt_transfer_rate_s"]), 0.0)
        * state.body_obt_bq,
        excretion=0.0 if slaughter_event else max(float(config["obt_excretion_rate_s"]), 0.0)
        * state.body_obt_bq,
        decay=0.0 if slaughter_event else max(float(config["decay_rate_s"]), 0.0) * state.body_obt_bq,
        slaughter=state.body_obt_bq / dt_s if slaughter_event else 0.0,
    )
    final = AnimalState(
        state.body_hto_bq
        + dt_s * (feed_hto + water_hto + obt_out["turnover"] - sum(hto_out.values())),
        state.body_obt_bq
        + dt_s * (feed_obt + hto_out["formation"] - sum(obt_out.values())),
    )
    boundary_rate = (
        hto_out["milk"]
        + obt_out["milk"]
        + hto_out["excretion"]
        + obt_out["excretion"]
        + hto_out["slaughter"]
        + obt_out["slaughter"]
    )
    decay_rate = hto_out["decay"] + obt_out["decay"]
    closure = EcologicalMassClosure(
        state.total_bq,
        (feed_hto + feed_obt + water_hto) * dt_s,
        boundary_rate * dt_s,
        decay_rate * dt_s,
        final.total_bq,
    )
    milk_rate_l_s = (
        max(float(config["milk_production_l_day"]), 0.0) / 86400.0 / area
    )
    beef_mass = max(float(config["beef_edible_mass_kg"]), 0.0) / area
    return final, AnimalDiagnostics(
        feed_hto,
        feed_obt,
        water_hto,
        hto_out["milk"],
        obt_out["milk"],
        hto_out["excretion"] + obt_out["excretion"],
        hto_out["slaughter"] + obt_out["slaughter"],
        hto_out["milk"] / milk_rate_l_s if milk_rate_l_s > 0 else 0.0,
        obt_out["milk"] / milk_rate_l_s if milk_rate_l_s > 0 else 0.0,
        final.body_hto_bq / beef_mass if beef_mass > 0 else 0.0,
        final.body_obt_bq / beef_mass if beef_mass > 0 else 0.0,
        closure,
    )


def plant_food_outputs(
    active_crop: str,
    tfwt_bq_m3_water: float,
    obt_bq_kg_fresh: float,
    water_content_fraction_fresh: float,
    water_density_kg_m3: float,
) -> dict[str, float]:
    tfwt_fresh = (
        max(tfwt_bq_m3_water, 0.0)
        * water_content_fraction_fresh
        / water_density_kg_m3
    )
    values = {
        "leafy_tfwt_bq_kg_fresh": 0.0,
        "leafy_obt_bq_kg_fresh": 0.0,
        "root_crop_tfwt_bq_kg_fresh": 0.0,
        "root_crop_obt_bq_kg_fresh": 0.0,
        "grain_tfwt_bq_kg_fresh": 0.0,
        "grain_obt_bq_kg_fresh": 0.0,
        "pasture_tfwt_bq_kg_fresh": 0.0,
        "pasture_obt_bq_kg_fresh": 0.0,
    }
    if active_crop == "leafy_vegetable":
        values["leafy_tfwt_bq_kg_fresh"] = tfwt_fresh
        values["leafy_obt_bq_kg_fresh"] = max(obt_bq_kg_fresh, 0.0)
    elif active_crop == "root_vegetable":
        values["root_crop_tfwt_bq_kg_fresh"] = tfwt_fresh
        values["root_crop_obt_bq_kg_fresh"] = max(obt_bq_kg_fresh, 0.0)
    elif active_crop == "cereal":
        values["grain_tfwt_bq_kg_fresh"] = tfwt_fresh
        values["grain_obt_bq_kg_fresh"] = max(obt_bq_kg_fresh, 0.0)
    elif active_crop in {"grass", "pasture"}:
        values["pasture_tfwt_bq_kg_fresh"] = tfwt_fresh
        values["pasture_obt_bq_kg_fresh"] = max(obt_bq_kg_fresh, 0.0)
    return values
