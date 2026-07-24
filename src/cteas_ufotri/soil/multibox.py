from __future__ import annotations

from dataclasses import dataclass

from .hto_balance import limit_inventory_outflows


@dataclass(frozen=True)
class ThreeBoxSoilState:
    water_m: tuple[float, float, float]
    hto_bq_m2: tuple[float, float, float]

    @property
    def total_water_m(self) -> float:
        return sum(self.water_m)

    @property
    def total_hto_bq_m2(self) -> float:
        return sum(self.hto_bq_m2)


@dataclass(frozen=True)
class ThreeBoxDiagnostics:
    surface_evaporation_m_s: float
    root_uptake_m_s: tuple[float, float, float]
    downward_water_m_s: tuple[float, float]
    deep_leakage_m_s: float
    diffusion_bq_m2_s: tuple[float, float]
    root_hto_bq_m2_s: tuple[float, float, float]
    surface_evaporation_hto_bq_m2_s: float
    deep_leakage_hto_bq_m2_s: float
    water_residual_m: float
    hto_residual_bq_m2: float


def advance_three_box_soil(
    state: ThreeBoxSoilState,
    dt_s: float,
    precipitation_m_s: float,
    surface_hto_input_bq_m2_s: float,
    requested_surface_evaporation_m_s: float,
    requested_root_uptake_m_s: float,
    config: dict,
) -> tuple[ThreeBoxSoilState, ThreeBoxDiagnostics]:
    """Conservative experimental 0-5/5-15/15-30 cm box solver."""
    if dt_s <= 0:
        raise ValueError("Three-box time step must be positive")
    if len(state.water_m) != 3 or len(state.hto_bq_m2) != 3:
        raise ValueError("Three-box state must contain exactly three layers")
    root_fractions = tuple(float(v) for v in config["root_fractions"])
    if len(root_fractions) != 3 or abs(sum(root_fractions) - 1.0) > 1.0e-9:
        raise ValueError("Three-box root fractions must sum to one")
    maximum = tuple(float(v) for v in config["maximum_water_m"])
    if len(maximum) != 3 or min(maximum) <= 0:
        raise ValueError("Three-box maximum water must be positive")

    water = [max(value, 0.0) for value in state.water_m]
    rain = max(precipitation_m_s, 0.0)
    water[0] += rain * dt_s
    evaporation = min(
        max(requested_surface_evaporation_m_s, 0.0),
        water[0] / dt_s,
    )
    water[0] -= evaporation * dt_s
    root = []
    for index, fraction in enumerate(root_fractions):
        uptake = min(
            max(requested_root_uptake_m_s, 0.0) * fraction,
            water[index] / dt_s,
        )
        root.append(uptake)
        water[index] -= uptake * dt_s

    drainage_rates = tuple(float(v) for v in config["interlayer_drainage_rate_s"])
    downward = []
    for donor in (0, 1):
        requested = max(drainage_rates[donor], 0.0) * water[donor]
        excess = max(water[donor] - maximum[donor], 0.0) / dt_s
        flux = min(max(requested, excess), water[donor] / dt_s)
        water[donor] -= flux * dt_s
        water[donor + 1] += flux * dt_s
        downward.append(flux)
    leakage = min(
        max(float(config["deep_leakage_rate_s"]), 0.0) * water[2],
        water[2] / dt_s,
    )
    water[2] -= leakage * dt_s

    inventory = [max(value, 0.0) for value in state.hto_bq_m2]
    inventory[0] += max(surface_hto_input_bq_m2_s, 0.0) * dt_s
    mixed_water = [
        max(state.water_m[0] + rain * dt_s, 1.0e-15),
        max(state.water_m[1], 1.0e-15),
        max(state.water_m[2], 1.0e-15),
    ]
    concentration = [
        inventory[index] / mixed_water[index] for index in range(3)
    ]
    advective = [
        downward[0] * concentration[0],
        downward[1] * concentration[1],
    ]
    diffusion = [0.0, 0.0]
    conductance = max(float(config["diffusive_exchange_m_s"]), 0.0)
    for interface in (0, 1):
        diffusion[interface] = conductance * (
            concentration[interface] - concentration[interface + 1]
        )

    requested_out: list[dict[str, float]] = []
    for index in range(3):
        rates = {
            "root": root[index] * concentration[index],
            "decay": max(float(config["decay_rate_s"]), 0.0) * inventory[index],
        }
        if index == 0:
            rates["evaporation"] = evaporation * concentration[0]
            rates["advection_down"] = advective[0]
            rates["diffusion_down"] = max(diffusion[0], 0.0)
        elif index == 1:
            rates["advection_down"] = advective[1]
            rates["diffusion_up"] = max(-diffusion[0], 0.0)
            rates["diffusion_down"] = max(diffusion[1], 0.0)
        else:
            rates["leakage"] = leakage * concentration[2]
            rates["diffusion_up"] = max(-diffusion[1], 0.0)
        requested_out.append(limit_inventory_outflows(inventory[index], dt_s, **rates))

    incoming = [0.0, 0.0, 0.0]
    incoming[1] += requested_out[0].get("advection_down", 0.0)
    incoming[2] += requested_out[1].get("advection_down", 0.0)
    incoming[1] += requested_out[0].get("diffusion_down", 0.0)
    incoming[0] += requested_out[1].get("diffusion_up", 0.0)
    incoming[2] += requested_out[1].get("diffusion_down", 0.0)
    incoming[1] += requested_out[2].get("diffusion_up", 0.0)
    final_inventory = [
        inventory[index] + dt_s * (incoming[index] - sum(requested_out[index].values()))
        for index in range(3)
    ]
    final = ThreeBoxSoilState(tuple(water), tuple(final_inventory))
    root_hto = tuple(out["root"] for out in requested_out)
    evap_hto = requested_out[0].get("evaporation", 0.0)
    leak_hto = requested_out[2].get("leakage", 0.0)
    decay = sum(out["decay"] for out in requested_out) * dt_s
    hto_boundary = (sum(root_hto) + evap_hto + leak_hto) * dt_s
    water_boundary = (evaporation + sum(root) + leakage) * dt_s
    return final, ThreeBoxDiagnostics(
        evaporation,
        tuple(root),
        tuple(downward),
        leakage,
        tuple(diffusion),
        root_hto,
        evap_hto,
        leak_hto,
        state.total_water_m + rain * dt_s - water_boundary - final.total_water_m,
        (
            state.total_hto_bq_m2
            + max(surface_hto_input_bq_m2_s, 0.0) * dt_s
            - hto_boundary
            - decay
            - final.total_hto_bq_m2
        ),
    )

