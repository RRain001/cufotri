from __future__ import annotations

import hashlib
import json

from .plant.leaf_exchange import (
    LEAF_EQUILIBRIUM_FORMULA_DESCRIPTION,
    LEAF_EQUILIBRIUM_FORMULA_ID,
    LEAF_EQUILIBRIUM_VAPOUR_DENSITY_BASIS,
)


MODEL_SCOPE = "HTO_ONLY_STEADY_GAUSSIAN_ENVIRONMENTAL_PATHWAYS"
VALIDATION_STATUS = "RESEARCH_CANDIDATE_NOT_SITE_OR_REGULATORY_VALIDATED"
CALENDAR_BASIS = "ACTUAL_GREGORIAN_365_366"
ROOT_SHOOT_ACTIVE = "TOTAL_PLUS_EXPLICIT_ROOT_DERIVED_SHOOT"
ROOT_SHOOT_INACTIVE = "AGGREGATE_ONLY_ROOT_ACTIVITY_FRACTION_ZERO"


def merged_config_sha256(config: dict) -> str:
    """Return the canonical hash used by V2 runtime provenance."""

    return hashlib.sha256(
        json.dumps(config, sort_keys=True).encode("utf-8")
    ).hexdigest()


def v2_named_provenance(config: dict) -> dict[str, str | float]:
    """Expand release-critical model metadata from the effective config."""

    deposition = config["deposition"]
    depletion = config["atmosphere"]["depletion"]
    crop_name = config["crops"]["active_crop"]
    crop = config["crops"]["parameters"][crop_name]
    root_fraction = float(crop.get("root_activity_fraction", 0.0))
    root_representation = (
        ROOT_SHOOT_ACTIVE if root_fraction > 0.0 else ROOT_SHOOT_INACTIVE
    )
    return {
        "ecological_reference_area_m2": float(
            deposition["ecological_reference_area_m2"]
        ),
        "leaf_equilibrium_formula_id": LEAF_EQUILIBRIUM_FORMULA_ID,
        "leaf_equilibrium_formula_description": (
            LEAF_EQUILIBRIUM_FORMULA_DESCRIPTION
        ),
        "leaf_equilibrium_vapour_density_basis": (
            LEAF_EQUILIBRIUM_VAPOUR_DENSITY_BASIS
        ),
        "root_activity_fraction": root_fraction,
        "root_shoot_representation": root_representation,
        "calendar_basis": CALENDAR_BASIS,
        "dry_footprint_area_m2": float(
            deposition["dry_footprint"]["area_m2"]
        ),
        "wet_footprint_area_m2": float(
            deposition["wet_footprint"]["area_m2"]
        ),
        "wet_scavenging_parameter_set": str(
            depletion["wet_scavenging_parameter_set"]
        ),
        "model_scope": MODEL_SCOPE,
        "validation_status": VALIDATION_STATUS,
    }


def validate_v2_named_provenance(
    provenance: dict,
    config: dict,
) -> None:
    """Fail closed if named provenance differs from the effective config."""

    expected = v2_named_provenance(config)
    missing = sorted(set(expected) - set(provenance))
    if missing:
        raise ValueError(f"Missing named V2 provenance fields: {missing}")
    mismatches = {
        key: {"expected": value, "actual": provenance[key]}
        for key, value in expected.items()
        if provenance[key] != value
    }
    if mismatches:
        raise ValueError(f"Named V2 provenance mismatch: {mismatches}")
    if provenance.get("merged_config_sha256") != merged_config_sha256(config):
        raise ValueError("Merged V2 configuration hash mismatch")
