from __future__ import annotations

from copy import deepcopy

import pytest

from cteas_ufotri.config import load_configuration
from cteas_ufotri.plant.leaf_exchange import (
    LEAF_EQUILIBRIUM_FORMULA_ID,
)
from cteas_ufotri.provenance import (
    ROOT_SHOOT_ACTIVE,
    ROOT_SHOOT_INACTIVE,
    merged_config_sha256,
    v2_named_provenance,
    validate_v2_named_provenance,
)


def _config(case: str) -> dict:
    return load_configuration(
        "configs/default_parameters.yaml",
        f"configs/v2/{case}",
    )


def test_named_provenance_matches_effective_annual_configuration():
    config = _config("v2_leaf_exchange_food_dose_72h.yaml")
    fields = v2_named_provenance(config)

    assert fields["ecological_reference_area_m2"] == (
        config["deposition"]["ecological_reference_area_m2"]
    )
    assert fields["dry_footprint_area_m2"] == (
        config["deposition"]["dry_footprint"]["area_m2"]
    )
    assert fields["wet_footprint_area_m2"] == (
        config["deposition"]["wet_footprint"]["area_m2"]
    )
    assert fields["leaf_equilibrium_formula_id"] == (
        LEAF_EQUILIBRIUM_FORMULA_ID
    )
    assert fields["root_activity_fraction"] == 0.0
    assert fields["root_shoot_representation"] == ROOT_SHOOT_INACTIVE


def test_named_provenance_reports_active_perennial_root_representation():
    config = _config("v2_full_adult_dose.yaml")
    fields = v2_named_provenance(config)

    assert fields["root_activity_fraction"] == pytest.approx(0.30)
    assert fields["root_shoot_representation"] == ROOT_SHOOT_ACTIVE


def test_named_provenance_is_deterministic_and_hash_is_recomputable():
    config = _config("v2_era5_72h_wet_deposition.yaml")
    first = v2_named_provenance(config)
    second = v2_named_provenance(deepcopy(config))
    provenance = {
        **first,
        "merged_config_sha256": merged_config_sha256(config),
    }

    assert first == second
    validate_v2_named_provenance(provenance, config)


def test_named_provenance_validation_fails_on_missing_or_stale_values():
    config = _config("v2_pasture_milk_pathway.yaml")
    provenance = {
        **v2_named_provenance(config),
        "merged_config_sha256": merged_config_sha256(config),
    }

    missing = deepcopy(provenance)
    missing.pop("calendar_basis")
    with pytest.raises(ValueError, match="Missing named"):
        validate_v2_named_provenance(missing, config)

    stale = deepcopy(provenance)
    stale["root_activity_fraction"] = 0.0
    with pytest.raises(ValueError, match="mismatch"):
        validate_v2_named_provenance(stale, config)
