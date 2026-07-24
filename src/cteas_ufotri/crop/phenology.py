from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math


@dataclass(frozen=True)
class CropParameters:
    name: str
    growth_start_doy: int
    harvest_doy: int
    max_lai: float
    constant_lai: float
    aboveground_biomass_kg_fresh_m2: float
    edible_fraction: float
    water_content_fraction_fresh: float
    root_fraction_by_layer: tuple[float, ...]
    obt_formation_rate_s: float
    biological_turnover_rate_s: float
    edible_allocation_rate_s: float
    harvest_loss_fraction: float
    perennial: bool

    @classmethod
    def from_mapping(cls, name: str, values: dict) -> "CropParameters":
        root = tuple(float(value) for value in values["root_fraction_by_layer"])
        if not root or abs(sum(root) - 1.0) > 1.0e-9:
            raise ValueError(f"Crop {name} root fractions must sum to one")
        result = cls(
            name=name,
            growth_start_doy=int(values["growth_start_doy"]),
            harvest_doy=int(values["harvest_doy"]),
            max_lai=float(values["max_lai"]),
            constant_lai=float(values.get("constant_lai", values["max_lai"])),
            aboveground_biomass_kg_fresh_m2=float(
                values["aboveground_biomass_kg_fresh_m2"]
            ),
            edible_fraction=float(values["edible_fraction"]),
            water_content_fraction_fresh=float(
                values["water_content_fraction_fresh"]
            ),
            root_fraction_by_layer=root,
            obt_formation_rate_s=float(values["obt_formation_rate_s"]),
            biological_turnover_rate_s=float(
                values["biological_turnover_rate_s"]
            ),
            edible_allocation_rate_s=float(values["edible_allocation_rate_s"]),
            harvest_loss_fraction=float(values["harvest_loss_fraction"]),
            perennial=bool(values["perennial"]),
        )
        if not 1 <= result.growth_start_doy <= 366:
            raise ValueError(f"Crop {name} has invalid growth start")
        if not 1 <= result.harvest_doy <= 366:
            raise ValueError(f"Crop {name} has invalid harvest day")
        if min(
            result.max_lai,
            result.constant_lai,
            result.aboveground_biomass_kg_fresh_m2,
            result.obt_formation_rate_s,
            result.biological_turnover_rate_s,
            result.edible_allocation_rate_s,
        ) < 0:
            raise ValueError(f"Crop {name} parameters must be non-negative")
        if not all(
            0.0 <= value <= 1.0
            for value in (
                result.edible_fraction,
                result.water_content_fraction_fresh,
                result.harvest_loss_fraction,
            )
        ):
            raise ValueError(f"Crop {name} fractions must be within [0, 1]")
        return result


def lai_at_time(
    timestamp: datetime,
    crop: CropParameters,
    mode: str,
    *,
    external_lai: float | None = None,
) -> float:
    if mode == "external_timeseries":
        if external_lai is None:
            raise ValueError("external_timeseries LAI requires a forcing value")
        return max(float(external_lai), 0.0)
    if mode == "constant":
        return crop.constant_lai
    doy = timestamp.timetuple().tm_yday
    start = crop.growth_start_doy
    harvest = crop.harvest_doy
    if crop.perennial and start == harvest:
        season_fraction = (doy - 1) / 365.0
    elif start <= harvest:
        if doy < start or doy > harvest:
            return 0.0
        season_fraction = (doy - start) / max(harvest - start, 1)
    else:
        season_length = (366 - start) + harvest
        if doy >= start:
            season_fraction = (doy - start) / season_length
        elif doy <= harvest:
            season_fraction = (366 - start + doy) / season_length
        else:
            return 0.0
    if mode == "smooth_seasonal":
        return crop.max_lai * math.sin(math.pi * season_fraction) ** 2
    if mode == "piecewise_growth_stage":
        if season_fraction < 0.2:
            return crop.max_lai * season_fraction / 0.2
        if season_fraction <= 0.75:
            return crop.max_lai
        return crop.max_lai * max((1.0 - season_fraction) / 0.25, 0.0)
    raise ValueError(f"Unsupported LAI mode: {mode}")


def growth_fraction_at_time(
    timestamp: datetime,
    crop: CropParameters,
    mode: str,
    *,
    external_lai: float | None = None,
) -> float:
    if mode == "constant":
        return 1.0
    lai = lai_at_time(timestamp, crop, mode, external_lai=external_lai)
    return min(lai / crop.max_lai, 1.0) if crop.max_lai > 0 else 0.0
