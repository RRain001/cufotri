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
    slaughter_hto_output_bq_s: float
    slaughter_obt_output_bq_s: float
    slaughter_output_bq_s: float
    milk_hto_bq_l: float
    milk_obt_bq_l: float
    closure: EcologicalMassClosure


@dataclass(frozen=True)
class BeefProductState:
    hto_bq_m2: float = 0.0
    obt_bq_m2: float = 0.0
    edible_mass_kg_m2: float = 0.0

    @property
    def total_bq_m2(self) -> float:
        return self.hto_bq_m2 + self.obt_bq_m2


@dataclass(frozen=True)
class BeefProductDiagnostics:
    produced_hto_bq_m2_s: float
    produced_obt_bq_m2_s: float
    produced_mass_kg_m2_s: float
    consumed_hto_bq_m2_s: float
    consumed_obt_bq_m2_s: float
    consumed_mass_kg_m2_s: float
    decay_loss_bq_m2_s: float
    beef_hto_bq_kg: float
    beef_obt_bq_kg: float
    activity_closure: EcologicalMassClosure
    mass_residual_kg_m2: float


def step_animal(
    state: AnimalState,
    dt_s: float,
    feed_hto_bq_kg_fresh: float,
    feed_obt_bq_kg_fresh: float,
    drinking_water_hto_bq_l: float,
    config: dict,
    *,
    slaughter_event: bool = False,
    slaughter_rate_s: float = 0.0,
    feed_hto_input_bq_m2_s: float | None = None,
    feed_obt_input_bq_m2_s: float | None = None,
) -> tuple[AnimalState, AnimalDiagnostics]:
    if dt_s <= 0:
        raise ValueError("Animal time step must be positive")
    if slaughter_rate_s < 0:
        raise ValueError("Animal slaughter rate must be non-negative")
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
        slaughter=(
            state.body_hto_bq / dt_s
            if slaughter_event
            else slaughter_rate_s * state.body_hto_bq
        ),
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
        slaughter=(
            state.body_obt_bq / dt_s
            if slaughter_event
            else slaughter_rate_s * state.body_obt_bq
        ),
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
    return final, AnimalDiagnostics(
        feed_hto,
        feed_obt,
        water_hto,
        hto_out["milk"],
        obt_out["milk"],
        hto_out["excretion"] + obt_out["excretion"],
        hto_out["slaughter"],
        obt_out["slaughter"],
        hto_out["slaughter"] + obt_out["slaughter"],
        hto_out["milk"] / milk_rate_l_s if milk_rate_l_s > 0 else 0.0,
        obt_out["milk"] / milk_rate_l_s if milk_rate_l_s > 0 else 0.0,
        closure,
    )


def step_beef_product(
    state: BeefProductState,
    dt_s: float,
    produced_hto_bq_m2_s: float,
    produced_obt_bq_m2_s: float,
    produced_mass_kg_m2_s: float,
    requested_consumption_kg_m2_s: float,
    decay_rate_s: float,
) -> tuple[BeefProductState, BeefProductDiagnostics]:
    """Produce, store, and inventory-limit consumption of edible beef."""

    if dt_s <= 0:
        raise ValueError("Beef-product time step must be positive")
    if min(
        produced_hto_bq_m2_s,
        produced_obt_bq_m2_s,
        produced_mass_kg_m2_s,
        requested_consumption_kg_m2_s,
        decay_rate_s,
    ) < 0:
        raise ValueError("Beef-product rates must be non-negative")
    mixed_hto = state.hto_bq_m2 + produced_hto_bq_m2_s * dt_s
    mixed_obt = state.obt_bq_m2 + produced_obt_bq_m2_s * dt_s
    mixed_mass = state.edible_mass_kg_m2 + produced_mass_kg_m2_s * dt_s
    requested_mass = requested_consumption_kg_m2_s * dt_s
    consumed_mass = min(requested_mass, mixed_mass)
    consumption_fraction = consumed_mass / mixed_mass if mixed_mass > 0.0 else 0.0
    requested_hto = mixed_hto * consumption_fraction / dt_s
    requested_obt = mixed_obt * consumption_fraction / dt_s
    hto_out = limit_inventory_outflows(
        mixed_hto,
        dt_s,
        consumed=requested_hto,
        decay=decay_rate_s * mixed_hto,
    )
    obt_out = limit_inventory_outflows(
        mixed_obt,
        dt_s,
        consumed=requested_obt,
        decay=decay_rate_s * mixed_obt,
    )
    final = BeefProductState(
        mixed_hto - sum(hto_out.values()) * dt_s,
        mixed_obt - sum(obt_out.values()) * dt_s,
        mixed_mass - consumed_mass,
    )
    activity_closure = EcologicalMassClosure(
        state.total_bq_m2,
        (produced_hto_bq_m2_s + produced_obt_bq_m2_s) * dt_s,
        (hto_out["consumed"] + obt_out["consumed"]) * dt_s,
        (hto_out["decay"] + obt_out["decay"]) * dt_s,
        final.total_bq_m2,
    )
    mass_residual = (
        state.edible_mass_kg_m2
        + produced_mass_kg_m2_s * dt_s
        - consumed_mass
        - final.edible_mass_kg_m2
    )
    consumed_mass_rate = consumed_mass / dt_s
    return final, BeefProductDiagnostics(
        produced_hto_bq_m2_s,
        produced_obt_bq_m2_s,
        produced_mass_kg_m2_s,
        hto_out["consumed"],
        obt_out["consumed"],
        consumed_mass_rate,
        hto_out["decay"] + obt_out["decay"],
        (
            hto_out["consumed"] / consumed_mass_rate
            if consumed_mass_rate > 0.0
            else (final.hto_bq_m2 / final.edible_mass_kg_m2
                  if final.edible_mass_kg_m2 > 0.0 else 0.0)
        ),
        (
            obt_out["consumed"] / consumed_mass_rate
            if consumed_mass_rate > 0.0
            else (final.obt_bq_m2 / final.edible_mass_kg_m2
                  if final.edible_mass_kg_m2 > 0.0 else 0.0)
        ),
        activity_closure,
        mass_residual,
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
