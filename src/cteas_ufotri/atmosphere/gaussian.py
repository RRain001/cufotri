from __future__ import annotations

import math
import numpy as np

from .dispersion_parameters import rural_pg_sigma


def rotate_to_wind(
    receptor_east_m: float, receptor_north_m: float, wind_from_deg: float
) -> tuple[float, float]:
    """Return downwind/crosswind coordinates for meteorological wind direction."""
    toward_rad = math.radians((wind_from_deg + 180.0) % 360.0)
    downwind = receptor_east_m * math.sin(toward_rad) + receptor_north_m * math.cos(toward_rad)
    crosswind = receptor_east_m * math.cos(toward_rad) - receptor_north_m * math.sin(toward_rad)
    return downwind, crosswind


def geographic_offset_m(
    source_longitude_deg: float,
    source_latitude_deg: float,
    receptor_longitude_deg: float,
    receptor_latitude_deg: float,
) -> tuple[float, float]:
    """Equirectangular local east/north offset, appropriate for receptor scales."""
    earth_radius_m = 6_371_000.0
    mean_latitude = math.radians((source_latitude_deg + receptor_latitude_deg) / 2.0)
    east = (
        earth_radius_m
        * math.radians(receptor_longitude_deg - source_longitude_deg)
        * math.cos(mean_latitude)
    )
    north = earth_radius_m * math.radians(receptor_latitude_deg - source_latitude_deg)
    return east, north


def vertical_reflection_factor(
    effective_height_m: float,
    sigma_z_m: float,
    mixing_height_m: float | None = None,
    image_terms: int = 4,
) -> float:
    """Ground reflection, optionally with a reflecting mixing-layer top."""
    if mixing_height_m is None:
        return 2.0 * math.exp(-0.5 * (effective_height_m / sigma_z_m) ** 2)
    if mixing_height_m <= 0 or effective_height_m < 0:
        raise ValueError("Mixing height must be positive and source height non-negative")
    if effective_height_m > mixing_height_m:
        effective_height_m = mixing_height_m
    total = 0.0
    for index in range(-max(image_terms, 0), max(image_terms, 0) + 1):
        for image_height in (
            effective_height_m + 2.0 * index * mixing_height_m,
            -effective_height_m + 2.0 * index * mixing_height_m,
        ):
            total += math.exp(-0.5 * (image_height / sigma_z_m) ** 2)
    return total


def point_source_ground_concentration(
    emission_rate_bq_s: float,
    downwind_m: float,
    crosswind_m: float,
    wind_speed_m_s: float,
    effective_height_m: float,
    stability_class: str = "D",
    mixing_height_m: float | None = None,
    image_terms: int = 4,
) -> float:
    if emission_rate_bq_s <= 0 or downwind_m <= 0:
        return 0.0
    if wind_speed_m_s <= 0:
        return 0.0
    sigma_y, sigma_z = rural_pg_sigma(downwind_m, stability_class)
    lateral = math.exp(-0.5 * (crosswind_m / sigma_y) ** 2)
    vertical_with_reflection = vertical_reflection_factor(
        effective_height_m, sigma_z, mixing_height_m, image_terms
    )
    value = emission_rate_bq_s * lateral * vertical_with_reflection / (
        2.0 * math.pi * wind_speed_m_s * sigma_y * sigma_z
    )
    return float(np.maximum(value, 0.0))


def rectangular_area_source_concentration(
    surface_flux_bq_m2_s: float,
    receptor_downwind_m: float,
    receptor_crosswind_m: float,
    wind_speed_m_s: float,
    source_length_m: float,
    source_width_m: float,
    stability_class: str = "D",
    *,
    source_height_m: float = 0.0,
    quadrature_x: int = 12,
    quadrature_y: int = 12,
    mixing_height_m: float | None = None,
    image_terms: int = 4,
) -> float:
    """Midpoint integration of a uniform rectangular ground-level area source."""
    if surface_flux_bq_m2_s <= 0 or wind_speed_m_s <= 0:
        return 0.0
    if min(source_length_m, source_width_m) <= 0 or min(quadrature_x, quadrature_y) < 1:
        raise ValueError("Area-source dimensions and quadrature counts must be positive")
    dx = source_length_m / quadrature_x
    dy = source_width_m / quadrature_y
    source_x = np.linspace(
        -source_length_m / 2.0 + dx / 2.0,
        source_length_m / 2.0 - dx / 2.0,
        quadrature_x,
    )
    source_y = np.linspace(
        -source_width_m / 2.0 + dy / 2.0,
        source_width_m / 2.0 - dy / 2.0,
        quadrature_y,
    )
    cell_emission = surface_flux_bq_m2_s * dx * dy
    concentration = 0.0
    for x_position in source_x:
        for y_position in source_y:
            concentration += point_source_ground_concentration(
                cell_emission,
                receptor_downwind_m - float(x_position),
                receptor_crosswind_m - float(y_position),
                wind_speed_m_s,
                source_height_m,
                stability_class,
                mixing_height_m,
                image_terms,
            )
    return concentration


def concentration_grid(
    emission_rate_bq_s: float,
    x_m,
    y_m,
    wind_speed_m_s: float,
    effective_height_m: float,
    stability_class: str = "D",
    mixing_height_m: float | None = None,
    image_terms: int = 4,
):
    return np.array(
        [
            [
                point_source_ground_concentration(
                    emission_rate_bq_s, float(x), float(y), wind_speed_m_s,
                    effective_height_m, stability_class, mixing_height_m, image_terms
                )
                for y in y_m
            ]
            for x in x_m
        ]
    )
