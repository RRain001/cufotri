"""Explicit 1993 KfK5194 printed-input metadata profile (P1 R1).

This module validates documented *historical defaults* and provenance for an
opt-in input contract. It does NOT select or execute a 1993 scientific solver.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path
from typing import Any

import yaml


PROFILE_ID = "KFK5194_1993_V4"
_FLAG_PAGES = {
    "IMODEL": 54, "ICOVER": 54, "IPHOTO": 54, "IMONT": 54,
    "IFLAGS": 54, "IFLAGR": 54, "IDEPHT": 55, "IBODEX": 55,
}


@dataclass(frozen=True, slots=True)
class Historical1993SourceProfile:
    """Immutable, non-executable source-backed snapshot for downstream P1 design."""

    profile_id: str
    source_url: str
    flag_defaults: tuple[tuple[str, int], ...]
    flag_printed_pages: tuple[tuple[str, int], ...]
    nuclides: tuple[str, str]
    deposition_velocity_m_s: tuple[float, float]
    washout_mode: int
    washout_class_boundaries_mm_h: tuple[float, float]
    washout_hto_rates_per_s: tuple[float, float, float]
    washout_hto_duration_fraction: tuple[float, float, float]
    wind_speed_m_s: float

    def provenance(self) -> dict[str, Any]:
        """Safe to serialize; does not carry operational source values or enable physics."""
        return {
            "profile_id": self.profile_id,
            "authority": "KfK 5194",
            "source_url": self.source_url,
            "scope": "PRINTED_HISTORICAL_DEFAULTS_METADATA_ONLY",
            "runtime_activation": False,
            "original_executable_equivalence": "NOT_ESTABLISHED",
            "flag_printed_pages": dict(self.flag_printed_pages),
            "unresolved_source_limited": ["RELFA_PERCENT_OR_FRACTION"],
            "historical_washout_default": "IWASH=0_THREE_PRECIPITATION_CLASSES",
        }


def _mapping(value: Any, name: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name}: required fields must match exactly {sorted(keys)}")
    return value


def _integer(value: Any, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer (not a boolean)")
    return value


def _number(value: Any, name: str) -> float:
    if type(value) not in (int, float) or not isfinite(float(value)):
        raise ValueError(f"{name} must be a finite numeric literal")
    return float(value)


def _equal_float_seq(value: Any, expected: tuple[float, ...], name: str) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != len(expected):
        raise ValueError(f"{name} must have {len(expected)} explicit entries")
    actual = tuple(_number(v, name) for v in value)
    if any(not isclose(a, b, rel_tol=1e-12, abs_tol=1e-15) for a, b in zip(actual, expected)):
        raise ValueError(f"{name} differs from documented KfK5194 values")
    return actual


def load_1993_source_profile(
    path: str | Path, *, selected_profile: str
) -> Historical1993SourceProfile:
    """Load an *explicitly selected* P1 source contract; never touch legacy runtime.

    This is deliberately not wired into `config.load_configuration`, CLI, or a
    model solver. The 1993 profile has no implicit fallback to 1990 defaults.
    """
    if selected_profile != PROFILE_ID:
        raise ValueError("1993 source profile requires explicit KFK5194_1993_V4 selection")
    with Path(path).open(encoding="utf-8") as f:
        root = yaml.safe_load(f)
    d = _mapping(root, "1993 input contract", {
        "schema_version", "profile_id", "authority", "source_url", "record_kind",
        "runtime_activation", "original_executable_equivalence", "feature_flags",
        "nuclides", "wet_scavenging", "meteorology", "source_limited",
    })
    if _integer(d["schema_version"], "schema_version") != 1:
        raise ValueError("Unknown 1993 input-contract schema")
    if d["profile_id"] != selected_profile or d["authority"] != "KfK 5194":
        raise ValueError("1993 source identity mismatch")
    if d["source_url"] != "https://publikationen.bibliothek.kit.edu/270034158/3813483":
        raise ValueError("1993 source URL mismatch")
    if d["record_kind"] != "PRINTED_HISTORICAL_DEFAULTS_METADATA_ONLY" or d["runtime_activation"] is not False:
        raise ValueError("1993 source-only contract cannot activate runtime")
    if d["original_executable_equivalence"] != "NOT_ESTABLISHED":
        raise ValueError("Original-executable equivalence is not established")

    flags = _mapping(d["feature_flags"], "feature_flags", set(_FLAG_PAGES))
    for name, page in _FLAG_PAGES.items():
        entry = _mapping(flags[name], name, {"value", "printed_page", "pdf0"})
        if (_integer(entry["value"], name) != 1
                or _integer(entry["printed_page"], f"{name}.printed_page") != page
                or _integer(entry["pdf0"], f"{name}.pdf0") != page + 9):
            raise ValueError(f"{name}: invalid printed 1993 default or provenance")

    n = _mapping(d["nuclides"], "nuclides", {
        "printed_pages", "order", "deposition_velocity_m_s",
    })
    if n["printed_pages"] != [46, 47] or n["order"] != ["HT", "HTO"]:
        raise ValueError("KfK5194 requires HT before HTO")
    deposition = _equal_float_seq(
        n["deposition_velocity_m_s"], (0.0005, 0.005), "deposition_velocity_m_s"
    )

    w = _mapping(d["wet_scavenging"], "wet_scavenging", {
        "printed_pages", "IWASH", "mode_zero", "class_boundaries_raw",
        "boundary_raw_unit", "class_boundaries_mm_h", "rate_unit",
        "HT_rates_per_s", "HTO_rates_per_s",
        "HT_rain_duration_fraction", "HTO_rain_duration_fraction",
        "optional_IWASH_1_power_law",
    })
    if (w["printed_pages"] != [46, 47]
            or _integer(w["IWASH"], "IWASH") != 0
            or w["mode_zero"] != "THREE_PRECIPITATION_CLASSES"
            or w["class_boundaries_raw"] != [100, 300]
            or w["boundary_raw_unit"] != "0.01_mm_h"
            or w["rate_unit"] != "per_s"
            or w["optional_IWASH_1_power_law"] != "NOT_ACTIVATED"):
        raise ValueError("1993 default is class-based IWASH=0 (not power law)")
    thresholds = _equal_float_seq(
        w["class_boundaries_mm_h"], (1.0, 3.0), "class_boundaries_mm_h"
    )
    _equal_float_seq(w["HT_rates_per_s"], (0.0, 0.0, 0.0), "HT_rates_per_s")
    rates = _equal_float_seq(
        w["HTO_rates_per_s"], (6e-5, 1e-4, 4e-4), "HTO_rates_per_s"
    )
    _equal_float_seq(
        w["HT_rain_duration_fraction"], (0.0, 0.0, 0.0), "HT_rain_duration_fraction"
    )
    durations = _equal_float_seq(
        w["HTO_rain_duration_fraction"], (0.50, 0.75, 0.72),
        "HTO_rain_duration_fraction"
    )

    m = _mapping(d["meteorology"], "meteorology", {
        "printed_page", "METIN", "NOSHFT", "IWNDG_raw",
        "IWNDG_raw_unit", "IWNDG_m_s", "IREGN_raw", "IREGN_raw_unit",
    })
    if (_integer(m["printed_page"], "meteorology.printed_page") != 48
            or _integer(m["METIN"], "METIN") != 0
            or _integer(m["NOSHFT"], "NOSHFT") != 2
            or _integer(m["IWNDG_raw"], "IWNDG_raw") != 500
            or m["IWNDG_raw_unit"] != "0.01_m_s"
            or _integer(m["IREGN_raw"], "IREGN_raw") != 0
            or m["IREGN_raw_unit"] != "0.01_mm_h"):
        raise ValueError("1993 METPAR historical units/defaults mismatch")
    wind_speed = _number(m["IWNDG_m_s"], "IWNDG_m_s")
    if not isclose(wind_speed, m["IWNDG_raw"] / 100.0, rel_tol=1e-12):
        raise ValueError("IWNDG raw 0.01 m/s versus SI value mismatch")

    a = _mapping(d["source_limited"], "source_limited", {"RELFA"})
    relfa = _mapping(a["RELFA"], "RELFA", {
        "printed_page", "printed_default", "printed_unit_label",
        "normalized_value", "status", "reason",
    })
    if (_integer(relfa["printed_page"], "RELFA.printed_page") != 66
            or _number(relfa["printed_default"], "RELFA.printed_default") != 0.5
            or relfa["printed_unit_label"] != "percent"
            or relfa["normalized_value"] is not None
            or relfa["status"] != "SOURCE_LIMITED"
            or not isinstance(relfa["reason"], str)
            or not relfa["reason"].strip()):
        raise ValueError("RELFA has no defensible normalized value")

    return Historical1993SourceProfile(
        profile_id=PROFILE_ID, source_url=d["source_url"],
        flag_defaults=tuple((name, flags[name]["value"]) for name in _FLAG_PAGES),
        flag_printed_pages=tuple(_FLAG_PAGES.items()),
        nuclides=("HT", "HTO"),
        deposition_velocity_m_s=deposition,
        washout_mode=0,
        washout_class_boundaries_mm_h=thresholds,
        washout_hto_rates_per_s=rates,
        washout_hto_duration_fraction=durations,
        wind_speed_m_s=wind_speed,
    )
