"""Current, concise invariants distilled from the frozen V4 production-source R1–R4 gates.

Those four historical stage-specific tests checked much of the same prohibition
on silently promoting synthetic/test data into production input. Keep source
and unit semantics here, while the original stage tests stay in Git history.
This is not empirical validation or original-executable equivalence.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "docs/v4/governance"
MANIFEST = ROOT / "docs/v4/contracts/v4_production_case_input_manifest_r1.yaml"
PHYSICAL = ROOT / "docs/v3/parameter_evidence/physical_constant_validation_registry.yaml"
STAGES = ("r1", "r2", "r3", "r4")


def _load(path: Path) -> dict:
    record = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(record, dict)
    return record


def _stage(name: str) -> dict:
    return _load(GOV / f"v4_production_case_input_source_resolution_{name}.yaml")


def _input(quantity_id: str) -> dict:
    return next(
        record for record in _load(MANIFEST)["inputs"]
        if record["quantity_id"] == quantity_id
    )


@pytest.mark.parametrize("stage", STAGES)
def test_historical_stage_snapshots_never_authorize_production(stage: str) -> None:
    gov = _stage(stage)
    assert gov["stage"] == f"V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_{stage.upper()}"
    scope = gov["scope"]
    for key in ("src_changed", "solver_equations_changed", "numerical_coupling_changed",
                "workflow_changed", "calibration_changed"):
        assert scope[key] is False
    hard = gov["hard_boundaries"]
    assert hard["production_input_packet_ready"] is False
    assert hard["full_model_production_ready"] is False
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["empirical_validation"] is False
    assert hard["physical_accuracy_claim"] is False
    flux = gov["atmos_surface_flux_blocker"]
    assert flux["token"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert flux["surrogate_or_zero_substitution_authorized"] is False


def test_r1_manifest_dispositions_remain_complete_and_unique() -> None:
    gov = _stage("r1")
    summary = gov["resolution_summary"]
    ids: list[str] = []
    for category, records in gov["resolution_registry"].items():
        if category in ("SOURCE_RESOLVED_NOT_ACTIVATED",
                        "CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED"):
            ids.extend(records.keys())
        else:
            ids.extend(records)
    manifest = _load(MANIFEST)["inputs"]
    assert len(manifest) == summary["total"] == len(ids) == len(set(ids)) == 49
    assert {r["quantity_id"] for r in manifest} == set(ids)
    assert sum(bool(r["required"]) for r in manifest) == 48
    assert sum(int(v) for k,v in summary.items() if k != "total") == 49


def test_half_life_source_resolved_but_not_silently_activated() -> None:
    gov = _stage("r1")
    resolved = gov["resolution_registry"]["SOURCE_RESOLVED_NOT_ACTIVATED"][
        "soil_three_layer.tritium_half_life"
    ]
    registry = _load(PHYSICAL)
    parameter = next(p for p in registry["parameters"]
                     if p["parameter_id"] == "soil.tritium_half_life")
    assert parameter["selected_value"] == resolved["validated_value_s"] == 388540800.0
    assert parameter["selected_uncertainty"] == resolved["validated_uncertainty_s"] == 777600.0
    assert parameter["selected_source_evidence_id"] == resolved["selected_evidence_id"]
    assert not resolved["production_use_authorized"]
    assert not resolved["runtime_import_authorized"]
    assert not resolved["active_parameter"]
    manifest = _input("soil_three_layer.tritium_half_life")
    assert manifest["readiness"] == "SOURCE_REQUIRED"
    assert manifest["source"] is None
    assert manifest["production_use_authorized"] is False


def test_eq39_fao_reference_conventions_are_source_bound_not_universal() -> None:
    r1 = _stage("r1")
    properties = _stage("r2")["properties"]
    assert set(properties) == set(
        r1["resolution_registry"]["CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED"]
    ) == {
        "root_eq39.latent_heat",
        "root_eq39.water_density",
        "root_eq39.psychrometric_constant",
    }
    latent = properties["root_eq39.latent_heat"]
    density = properties["root_eq39.water_density"]
    gamma = properties["root_eq39.psychrometric_constant"]
    assert (latent["selected_value"], latent["unit"]) == (2450000.0, "J kg^-1")
    assert latent["source_role"] == "MODEL_CONVENTION_NOT_UNIVERSAL_CONSTANT"
    assert latent["applicability"]["temperature_dependence_acknowledged"] is True
    assert latent["applicability"]["universal_exact_property_claim"] is False
    assert latent["authority"]["organization"] == "FAO"
    assert (density["selected_value"], density["unit"]) == (1000.0, "kg m^-3")
    assert density["source_role"] == "WATER_DEPTH_CONVERSION_MODEL_CONVENTION_NOT_UNIVERSAL_CONSTANT"
    assert density["physical_property_boundary_authority"]["organization"] == "IAPWS"
    assert gamma["selected_value"] is None
    assert gamma["source_role"] == "CASE_PRESSURE_DERIVED_PROPERTY"
    assert gamma["unit"] == "Pa K^-1"
    assert gamma["derivation"]["gamma_pa_per_k_from_pressure_kpa"]["coefficient"] == 0.665
    assert gamma["derivation"]["gamma_kpa_per_k_from_pressure_kpa"]["coefficient"] == 0.000665
    for quantity, item in properties.items():
        assert item["implementation"]["production_use_authorized"] is False
        assert _input(quantity)["readiness"] == "SOURCE_REQUIRED"
        assert _input(quantity)["source"] is None


def test_r3_pressure_and_site_elevation_are_distinct_provenanced_quantities() -> None:
    r3 = _stage("r3")
    precedence = [
        "EXPLICIT_CASE_MEAN_ATMOSPHERIC_PRESSURE_WITH_PROVENANCE",
        "FAO56_PRESSURE_DERIVED_FROM_EXPLICIT_SITE_ELEVATION_WITH_PROVENANCE",
    ]
    assert r3["source_precedence"] == precedence
    pressure = r3["explicit_pressure_contract"]
    assert pressure["field_id"] == "case_mean_atmospheric_pressure_kpa"
    assert pressure["canonical_unit"] == "kPa"
    for key in ("silent_resampling_allowed", "silent_fill_allowed",
                "silent_unit_conversion_allowed"):
        assert pressure["case_mean_rule"][key] is False
    assert pressure["forbidden_defaults"]["sea_level_pressure_101_3_kpa"]
    assert pressure["forbidden_defaults"]["fixed_gamma_66_pa_k"]
    elevation = r3["site_elevation_contract"]
    assert elevation["field_id"] == "site_elevation_m_msl"
    assert "RECEPTOR_HEIGHT_ABOVE_LOCAL_GROUND" in elevation["forbidden_substitutes"]
    assert "STACK_HEIGHT" in elevation["forbidden_substitutes"]
    assert elevation["ellipsoidal_height_rule"]["direct_relabel_to_msl_allowed"] is False
    assert elevation["ellipsoidal_height_rule"][
        "explicit_geoid_or_vertical_datum_transformation_required"
    ] is True
    d = r3["fao56_derivation"]
    assert d["pressure_from_elevation"]["formula"] == (
        "P_kPa = 101.3 * ((293 - 0.0065*z_m)/293)^5.26"
    )
    assert d["psychrometric_constant"]["formula"] == "gamma_Pa_per_K = 0.665 * P_kPa"
    assert d["psychrometric_constant"]["fixed_66_pa_k_allowed"] is False
    assert r3["dual_source_rule"]["explicit_pressure_has_precedence"] is True
    assert r3["dual_source_rule"]["automatic_blending_allowed"] is False


def test_r4_historical_test_meteorology_does_not_become_production_source() -> None:
    r4 = _stage("r4")
    r5 = _stage("r5")
    assert r4["selection_outcome"]["token"] == (
        "BLOCKED_PRODUCTION_CASE_IDENTITY_NOT_INDEPENDENTLY_DECLARED"
    )
    assert r4["pressure_source_audit"]["surface_pressure_documented_in_historical_audit"] is False
    selection = r4["psychrometric_selection"]
    for field in ("selected_pressure_source_kind", "selected_pressure_kpa",
                  "selected_site_elevation_m_msl", "selected_gamma_pa_k"):
        assert selection[field] is None
    historical = r4["historical_repository_evidence"]
    assert historical["era5_requested_test_point"]["disposition"] == (
        "HISTORICAL_TEST_CONTEXT_NOT_PRODUCTION_BINDING"
    )
    assert historical["era5_returned_nearest_grid_point"]["disposition"] == (
        "METEOROLOGICAL_TEST_GRID_POINT_NOT_SITE_IDENTITY"
    )
    packet = r4["production_case_identity_binding_packet"]
    assert packet["required_fields"] == r5["declaration_intake"]["required_fields"]
    rules = packet["rules"]
    for name in ("historical_test_coordinate_may_be_silently_promoted",
                 "era5_nearest_grid_may_be_silently_promoted",
                 "receptor_coordinate_may_be_silently_promoted",
                 "missing_declaration_fields_may_be_inferred_from_test_artifacts"):
        assert rules[name] is False
    assert _load(MANIFEST)["case_identity"]["case_id"] == "TEMPLATE_NOT_PRODUCTION"
