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
    phenology_mode: str
    dormant_min_lai: float
    cutting_doys: tuple[int, ...]
    cutting_fraction: float

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
            phenology_mode=str(
                values.get(
                    "phenology_mode",
                    (
                        "perennial_dormant_season"
                        if values["perennial"]
                        else "annual_single_harvest"
                    ),
                )
            ),
            dormant_min_lai=float(values.get("dormant_min_lai", 0.0)),
            cutting_doys=tuple(
                int(value) for value in values.get("cutting_doys", [])
            ),
            cutting_fraction=float(values.get("cutting_fraction", 1.0)),
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
            result.dormant_min_lai,
        ) < 0:
            raise ValueError(f"Crop {name} parameters must be non-negative")
        if not all(
            0.0 <= value <= 1.0
            for value in (
                result.edible_fraction,
                result.water_content_fraction_fresh,
                result.harvest_loss_fraction,
                result.cutting_fraction,
            )
        ):
            raise ValueError(f"Crop {name} fractions must be within [0, 1]")
        supported_modes = {
            "annual_single_harvest",
            "annual_multiple_harvest",
            "perennial_dormant_season",
            "perennial_evergreen",
        }
        if result.phenology_mode not in supported_modes:
            raise ValueError(f"Crop {name} has unsupported phenology mode")
        if result.perennial != result.phenology_mode.startswith("perennial_"):
            raise ValueError(f"Crop {name} perennial flag conflicts with mode")
        if result.dormant_min_lai > result.max_lai:
            raise ValueError(f"Crop {name} dormant LAI exceeds maximum LAI")
        if any(not 1 <= day <= 366 for day in result.cutting_doys):
            raise ValueError(f"Crop {name} has invalid cutting day")
        if len(set(result.cutting_doys)) != len(result.cutting_doys):
            raise ValueError(f"Crop {name} has duplicate cutting days")
        if result.phenology_mode in {
            "annual_multiple_harvest",
            "perennial_dormant_season",
            "perennial_evergreen",
        } and not result.cutting_doys:
            raise ValueError(f"Crop {name} mode requires cutting days")
        return result


def _season_fraction(doy: int, crop: CropParameters) -> float | None:
    start = crop.growth_start_doy
    harvest = crop.harvest_doy
    if start <= harvest:
        if doy < start or doy > harvest:
            return None
        return (doy - start) / max(harvest - start, 1)
    season_length = (366 - start) + harvest
    if doy >= start:
        return (doy - start) / season_length
    if doy <= harvest:
        return (366 - start + doy) / season_length
    return None


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
    if crop.phenology_mode == "perennial_evergreen":
        return crop.max_lai
    season_fraction = _season_fraction(doy, crop)
    if season_fraction is None:
        return (
            crop.dormant_min_lai
            if crop.phenology_mode == "perennial_dormant_season"
            else 0.0
        )
    if mode == "smooth_seasonal":
        seasonal = math.sin(math.pi * season_fraction) ** 2
        return crop.dormant_min_lai + (
            crop.max_lai - crop.dormant_min_lai
        ) * seasonal
    if mode == "piecewise_growth_stage":
        if season_fraction < 0.2:
            seasonal = season_fraction / 0.2
        elif season_fraction <= 0.75:
            seasonal = 1.0
        else:
            seasonal = max((1.0 - season_fraction) / 0.25, 0.0)
        return crop.dormant_min_lai + (
            crop.max_lai - crop.dormant_min_lai
        ) * seasonal
    raise ValueError(f"Unsupported LAI mode: {mode}")


def harvest_fraction_at_transition(
    timestamp: datetime,
    next_timestamp: datetime,
    crop: CropParameters,
) -> float:
    """Return the activity/biomass fraction removed at a date boundary."""

    if timestamp.date() == next_timestamp.date():
        return 0.0
    next_doy = next_timestamp.timetuple().tm_yday
    if crop.phenology_mode == "annual_single_harvest":
        return 1.0 if next_doy == crop.harvest_doy else 0.0
    return crop.cutting_fraction if next_doy in crop.cutting_doys else 0.0


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
