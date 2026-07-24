"""Query the live CDS catalogue for the ERA5 single-level time-series dataset."""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


DATASET = "reanalysis-era5-single-levels-timeseries"
CATALOGUE_URL = f"https://cds.climate.copernicus.eu/api/catalogue/v1/collections/{DATASET}"
WAVE_VARIABLES = {
    "mean_wave_direction",
    "mean_wave_period",
    "significant_height_of_combined_wind_waves_and_swell",
}
LABEL_OVERRIDES = {
    "slhf": "Surface latent heat flux",
    "sshf": "Surface sensible heat flux",
}


def _load_json(url: str, timeout: int = 30) -> Any:
    request = Request(url, headers={"User-Agent": "Hefei-H3-ERA5/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def fetch_catalogue() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return collection metadata and its current request-form definition."""
    metadata = _load_json(CATALOGUE_URL)
    form_url = next(link["href"] for link in metadata["links"] if link["rel"] == "form")
    form = _load_json(form_url)
    return metadata, form


def field(form: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(item for item in form if item.get("name") == name)


def available_variables(form: list[dict[str, Any]]) -> list[dict[str, str]]:
    variable_field = field(form, "variable")
    details = variable_field["details"]
    labels = details.get("labels", {})
    result = []
    for name in details["values"]:
        result.append(
            {
                "name": name,
                "label": LABEL_OVERRIDES.get(name, labels.get(name, name)),
                "group": "wave" if name in WAVE_VARIABLES else "surface",
            }
        )
    return result


def date_limits(form: list[dict[str, Any]]) -> tuple[str, str]:
    details = field(form, "date")["details"]
    return details["minStart"], details["maxEnd"]
