"""P1 R1 manual-1993 metadata profile: strict explicit opt-in, no solver activation."""
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, Historical1993SourceProfile, load_1993_source_profile,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "configs" / "ufotri_1993_manual_source_profile.yaml"


def _load() -> dict:
    return yaml.safe_load(PROFILE.read_text(encoding="utf-8"))


def _write(tmp_path: Path, d: dict) -> Path:
    path = tmp_path / "override.yaml"
    path.write_text(yaml.safe_dump(d, sort_keys=False), encoding="utf-8")
    return path


def test_documented_profile_requires_explicit_version_and_does_not_run_physics() -> None:
    with pytest.raises(TypeError):
        load_1993_source_profile(PROFILE)
    with pytest.raises(ValueError, match="explicit"):
        load_1993_source_profile(PROFILE, selected_profile="KFK4605_1990")
    profile = load_1993_source_profile(PROFILE, selected_profile=PROFILE_ID)
    assert isinstance(profile, Historical1993SourceProfile)
    assert profile.nuclides == ("HT", "HTO")
    assert profile.wind_speed_m_s == 5.0
    assert dict(profile.flag_defaults) == {
        "IMODEL": 1, "ICOVER": 1, "IPHOTO": 1, "IMONT": 1,
        "IFLAGS": 1, "IFLAGR": 1, "IDEPHT": 1, "IBODEX": 1,
    }
    assert profile.washout_mode == 0
    assert profile.washout_class_boundaries_mm_h == (1.0, 3.0)
    assert profile.washout_hto_rates_per_s == (6e-5, 1e-4, 4e-4)
    assert profile.washout_hto_duration_fraction == (0.5, 0.75, 0.72)
    provenance = profile.provenance()
    assert provenance["runtime_activation"] is False
    assert provenance["original_executable_equivalence"] == "NOT_ESTABLISHED"
    assert provenance["flag_printed_pages"]["IMODEL"] == 54
    assert provenance["flag_printed_pages"]["IBODEX"] == 55
    assert provenance["unresolved_source_limited"] == ["RELFA_PERCENT_OR_FRACTION"]
    assert provenance["historical_washout_default"].startswith("IWASH=0")


@pytest.mark.parametrize("mutation", [
    ("profile_id", "KFK4605_1990"),
    ("runtime_activation", True),
    ("original_executable_equivalence", "PASS"),
    ("extra_runtime_key", True),
])
def test_identity_and_runtime_mutations_fail_closed(tmp_path: Path, mutation: tuple) -> None:
    data = _load()
    data[mutation[0]] = mutation[1]
    with pytest.raises(ValueError):
        load_1993_source_profile(_write(tmp_path, data), selected_profile=PROFILE_ID)


@pytest.mark.parametrize("path,value", [
    (("feature_flags", "IPHOTO", "value"), 0),
    (("feature_flags", "IMONT", "value"), True),
    (("feature_flags", "IBODEX", "pdf0"), 63),
    (("nuclides", "order"), ["HTO", "HT"]),
    (("nuclides", "deposition_velocity_m_s"), [0.005, 0.0005]),
    (("wet_scavenging", "IWASH"), 1),
    (("wet_scavenging", "class_boundaries_raw"), [1, 3]),
    (("wet_scavenging", "class_boundaries_mm_h"), [100, 300]),
    (("wet_scavenging", "HTO_rates_per_s"), [0.00009, 0.0001, 0.0004]),
    (("wet_scavenging", "optional_IWASH_1_power_law"), "DEFAULT"),
    (("meteorology", "NOSHFT"), 1),
    (("meteorology", "IWNDG_raw_unit"), "m_s"),
    (("meteorology", "IWNDG_m_s"), 500),
    (("source_limited", "RELFA", "normalized_value"), 0.5),
    (("source_limited", "RELFA", "status"), "SOURCE_RESOLVED"),
])
def test_historical_defaults_and_ambiguities_not_silently_overridden(
    tmp_path: Path, path: tuple[str, ...], value: object
) -> None:
    data = _load()
    cur = data
    for key in path[:-1]:
        cur = cur[key]
    cur[path[-1]] = value
    with pytest.raises(ValueError):
        load_1993_source_profile(_write(tmp_path, data), selected_profile=PROFILE_ID)


def test_source_metadata_matches_primary_r2_r6b_registry() -> None:
    p = _load()
    source_dir = ROOT / "docs" / "v4" / "1993_upgrade"
    r2 = yaml.safe_load((source_dir / "primary_source_formula_audit_r2.yaml").read_text(encoding="utf-8"))
    r6 = yaml.safe_load((source_dir / "primary_source_input_washout_r6.yaml").read_text(encoding="utf-8"))
    known_defaults = {x["name"]: x for x in r2["documented_defaults"]}
    for name, entry in p["feature_flags"].items():
        assert known_defaults[name]["value"] == entry["value"]
        assert known_defaults[name]["print_page"] == entry["printed_page"]
        assert known_defaults[name]["pdf_page_index"] == entry["pdf0"]
    assert p["nuclides"]["order"] == r6["isotope"]["nuclide_order"]
    assert p["nuclides"]["deposition_velocity_m_s"] == r6["isotope"]["deposition_velocity_m_per_s"]
    assert p["wet_scavenging"]["IWASH"] == r6["isotope"]["washout_mode_default"] == 0
    m = r6["isotope"]["mode_zero"]
    assert p["wet_scavenging"]["class_boundaries_raw"] == m["rain_class_boundaries_source_scaled"]
    assert p["wet_scavenging"]["HTO_rates_per_s"] == m["hto_washout_rate_per_s"]
    assert p["wet_scavenging"]["HTO_rain_duration_fraction"] == m["hto_relative_precipitation_duration"]
    assert p["meteorology"]["IWNDG_m_s"] == r6["meteorology"]["iWNDG_physical_default_m_per_s"]
    assert p["meteorology"]["NOSHFT"] == r6["meteorology"]["noshft_default"]


def test_legacy_runtime_does_not_import_or_auto_select_1993_profile() -> None:
    # P1 metadata contract stays separate from the frozen 1990 execution path.
    config = (ROOT / "src" / "cteas_ufotri" / "config.py").read_text(encoding="utf-8")
    cli = (ROOT / "src" / "cteas_ufotri" / "cli.py").read_text(encoding="utf-8")
    assert "versioned_inputs_1993" not in config
    assert "versioned_inputs_1993" not in cli
    assert "ufotri_1993_manual_source_profile.yaml" not in (
        ROOT / "configs" / "default_parameters.yaml"
    ).read_text(encoding="utf-8")
