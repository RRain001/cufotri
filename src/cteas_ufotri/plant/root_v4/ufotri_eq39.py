"""Opt-in UFOTRI Eq.39 total root-water uptake boundary for V4."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ...meteorology.derived_variables import saturation_curve_slope_pa_k
from ...meteorology.fallback_fluxes import partition_evapotranspiration
from .root_solver import ThreeLayerRootWaterFluxForcingV4
from .root_state import RootWaterFluxProvenanceV4
from .ufotri_profile import ufotri_three_layer_root_water_flux_forcing
from .validation import (
    WATER_FLUX_UNIT,
    RootV4InputError,
    require_finite,
    require_text,
    require_unit,
    validate_provenance,
    validate_utc_timestamp,
)

TEMPERATURE_UNIT = "K"
NET_RADIATION_UNIT = "W m^-2"
LAI_UNIT = "1"
WATER_STORAGE_UNIT = "m water"
LATENT_HEAT_UNIT = "J kg^-1"
WATER_DENSITY_UNIT = "kg m^-3"
PSYCHROMETRIC_CONSTANT_UNIT = "Pa K^-1"
EQ39_MODE = "EQUILIBRIUM_RADIATION_EQ39"


@dataclass(frozen=True)
class UFOTRIEq39RootUptakeInputV4:
    """Explicit inputs required by the controlled UFOTRI Eq.39 root boundary.

    The three provenance records deliberately remain independent so meteorology,
    case/state inputs, and physical conversion constants cannot be silently
    collapsed into one opaque source.
    """

    plant_identifier: str
    timestamp: datetime
    temperature_k: float
    net_radiation_w_m2: float
    lai: float
    soil_water_m: float
    maximum_water_m: float
    wilting_water_m: float
    latent_heat_j_kg: float
    water_density_kg_m3: float
    psychrometric_constant_pa_k: float
    meteorology_provenance: RootWaterFluxProvenanceV4
    case_provenance: RootWaterFluxProvenanceV4
    physical_constants_provenance: RootWaterFluxProvenanceV4
    temperature_unit: str = TEMPERATURE_UNIT
    net_radiation_unit: str = NET_RADIATION_UNIT
    lai_unit: str = LAI_UNIT
    water_storage_unit: str = WATER_STORAGE_UNIT
    latent_heat_unit: str = LATENT_HEAT_UNIT
    water_density_unit: str = WATER_DENSITY_UNIT
    psychrometric_constant_unit: str = PSYCHROMETRIC_CONSTANT_UNIT

    def __post_init__(self) -> None:
        require_text(self.plant_identifier, field="plant_identifier")
        validate_utc_timestamp(self.timestamp, field="eq39.timestamp")
        require_unit(self.temperature_unit, TEMPERATURE_UNIT, field="temperature")
        require_unit(self.net_radiation_unit, NET_RADIATION_UNIT, field="net_radiation")
        require_unit(self.lai_unit, LAI_UNIT, field="lai")
        require_unit(self.water_storage_unit, WATER_STORAGE_UNIT, field="soil_water")
        require_unit(self.latent_heat_unit, LATENT_HEAT_UNIT, field="latent_heat")
        require_unit(self.water_density_unit, WATER_DENSITY_UNIT, field="water_density")
        require_unit(
            self.psychrometric_constant_unit,
            PSYCHROMETRIC_CONSTANT_UNIT,
            field="psychrometric_constant",
        )

        temperature = require_finite(self.temperature_k, field="temperature_k")
        radiation = require_finite(self.net_radiation_w_m2, field="net_radiation_w_m2")
        lai = require_finite(self.lai, field="lai")
        soil_water = require_finite(self.soil_water_m, field="soil_water_m")
        maximum_water = require_finite(self.maximum_water_m, field="maximum_water_m")
        wilting_water = require_finite(self.wilting_water_m, field="wilting_water_m")
        latent_heat = require_finite(self.latent_heat_j_kg, field="latent_heat_j_kg")
        density = require_finite(self.water_density_kg_m3, field="water_density_kg_m3")
        gamma = require_finite(
            self.psychrometric_constant_pa_k,
            field="psychrometric_constant_pa_k",
        )

        if temperature <= 0.0:
            raise RootV4InputError("temperature_k must be strictly positive")
        # Negative net radiation is valid forcing and is clipped to zero by the
        # frozen Eq.39 daytime-energy semantics; it is therefore not rejected.
        _ = radiation
        if lai < 0.0:
            raise RootV4InputError("lai must be non-negative")
        if soil_water < 0.0:
            raise RootV4InputError("soil_water_m must be non-negative")
        if maximum_water <= 0.0:
            raise RootV4InputError("maximum_water_m must be strictly positive")
        if wilting_water < 0.0 or wilting_water > maximum_water:
            raise RootV4InputError("wilting_water_m must be within [0, maximum_water_m]")
        if latent_heat <= 0.0:
            raise RootV4InputError("latent_heat_j_kg must be strictly positive")
        if density <= 0.0:
            raise RootV4InputError("water_density_kg_m3 must be strictly positive")
        if gamma <= 0.0:
            raise RootV4InputError("psychrometric_constant_pa_k must be strictly positive")

        for name, provenance in (
            ("meteorology_provenance", self.meteorology_provenance),
            ("case_provenance", self.case_provenance),
            ("physical_constants_provenance", self.physical_constants_provenance),
        ):
            if not isinstance(provenance, RootWaterFluxProvenanceV4):
                raise RootV4InputError(f"{name} must be RootWaterFluxProvenanceV4")
            validate_provenance(provenance)


@dataclass(frozen=True)
class UFOTRIEq39RootUptakeResultV4:
    """Computed Eq.39 total uptake and the resulting typed 20/40/40 forcing."""

    potential_total_m_s: float
    potential_soil_m_s: float
    soil_evaporation_m_s: float
    plant_transpiration_m_s: float
    root_uptake_m_s: float
    moisture_factor: float
    layer_forcing: ThreeLayerRootWaterFluxForcingV4
    mode: str = EQ39_MODE
    aerodynamic_coefficient_w_m2_pa: float = 0.0
    water_flux_unit: str = WATER_FLUX_UNIT

    def __post_init__(self) -> None:
        if self.mode != EQ39_MODE:
            raise RootV4InputError(f"mode must be {EQ39_MODE}")
        if self.aerodynamic_coefficient_w_m2_pa != 0.0:
            raise RootV4InputError("controlled Eq.39 aerodynamic coefficient must be exactly zero")
        require_unit(self.water_flux_unit, WATER_FLUX_UNIT, field="eq39_output_water_flux")
        for field in (
            "potential_total_m_s",
            "potential_soil_m_s",
            "soil_evaporation_m_s",
            "plant_transpiration_m_s",
            "root_uptake_m_s",
            "moisture_factor",
        ):
            value = require_finite(getattr(self, field), field=field)
            if value < 0.0:
                raise RootV4InputError(f"{field} must be non-negative")
        if self.moisture_factor > 1.0:
            raise RootV4InputError("moisture_factor must not exceed one")
        if self.root_uptake_m_s != self.plant_transpiration_m_s:
            raise RootV4InputError("root uptake must equal plant transpiration for the selected UFOTRI boundary")
        if not isinstance(self.layer_forcing, ThreeLayerRootWaterFluxForcingV4):
            raise RootV4InputError("layer_forcing must be ThreeLayerRootWaterFluxForcingV4")


def ufotri_eq39_potential_total_m_s(inputs: UFOTRIEq39RootUptakeInputV4) -> float:
    """Evaluate UFOTRI Eq.39 without introducing Eq.38 wind/VPD inputs."""

    if not isinstance(inputs, UFOTRIEq39RootUptakeInputV4):
        raise RootV4InputError("inputs must be UFOTRIEq39RootUptakeInputV4")
    delta = float(saturation_curve_slope_pa_k(inputs.temperature_k))
    gamma = inputs.psychrometric_constant_pa_k
    radiation = max(inputs.net_radiation_w_m2, 0.0)
    latent_flux_w_m2 = delta * radiation / (delta + gamma)
    return latent_flux_w_m2 / inputs.latent_heat_j_kg / inputs.water_density_kg_m3


def ufotri_eq39_root_uptake(
    inputs: UFOTRIEq39RootUptakeInputV4,
    *,
    output_provenance: RootWaterFluxProvenanceV4,
) -> UFOTRIEq39RootUptakeResultV4:
    """Compute Eq.39 -> Eq.40-43 transpiration -> UFOTRI 20/40/40 forcing."""

    if not isinstance(inputs, UFOTRIEq39RootUptakeInputV4):
        raise RootV4InputError("inputs must be UFOTRIEq39RootUptakeInputV4")
    if not isinstance(output_provenance, RootWaterFluxProvenanceV4):
        raise RootV4InputError("output_provenance must be RootWaterFluxProvenanceV4")
    validate_provenance(output_provenance)

    potential_total = ufotri_eq39_potential_total_m_s(inputs)
    fluxes = partition_evapotranspiration(
        potential_total_m_s=potential_total,
        lai=inputs.lai,
        water_m=inputs.soil_water_m,
        maximum_water_m=inputs.maximum_water_m,
        wilting_water_m=inputs.wilting_water_m,
        shading_mode="radiation_term_only",
        radiation_component_m_s=potential_total,
        aerodynamic_component_m_s=0.0,
    )
    if fluxes.root_uptake_m_s != fluxes.plant_transpiration_m_s:
        raise RootV4InputError("UFOTRI Eq.40-43 boundary violated root uptake = plant transpiration")

    layer_forcing = ufotri_three_layer_root_water_flux_forcing(
        total_water_uptake_flux_m_s=fluxes.root_uptake_m_s,
        plant_identifier=inputs.plant_identifier,
        timestamp=inputs.timestamp,
        provenance=output_provenance,
    )
    return UFOTRIEq39RootUptakeResultV4(
        potential_total_m_s=fluxes.potential_total_m_s,
        potential_soil_m_s=fluxes.potential_soil_m_s,
        soil_evaporation_m_s=fluxes.soil_evaporation_m_s,
        plant_transpiration_m_s=fluxes.plant_transpiration_m_s,
        root_uptake_m_s=fluxes.root_uptake_m_s,
        moisture_factor=fluxes.moisture_factor,
        layer_forcing=layer_forcing,
    )


__all__ = [
    "EQ39_MODE",
    "LAI_UNIT",
    "LATENT_HEAT_UNIT",
    "NET_RADIATION_UNIT",
    "PSYCHROMETRIC_CONSTANT_UNIT",
    "TEMPERATURE_UNIT",
    "UFOTRIEq39RootUptakeInputV4",
    "UFOTRIEq39RootUptakeResultV4",
    "WATER_DENSITY_UNIT",
    "WATER_STORAGE_UNIT",
    "ufotri_eq39_potential_total_m_s",
    "ufotri_eq39_root_uptake",
]
