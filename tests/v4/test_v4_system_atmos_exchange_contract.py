"""V4 system atmospheric exchange-contract governance invariants."""
from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/v4/contracts/v4_system_atmos_exchange_contract.yaml"
SCHEMA = ROOT / "schemas/v4/v4_atmos_exchange_record.schema.json"
ADR = ROOT / "docs/v4/adr/ADR-027-v4-system-atmos-exchange-contract.md"
REVIEW = ROOT / "docs/v4/reports/v4_system_atmos_exchange_contract_review.md"


def _contract() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_stage_is_control_plane_only_and_preserves_v3_runtime() -> None:
    c = _contract()
    assert c["status"] == "PASS_CONTROL_PLANE_CONTRACT_FROZEN"
    assert c["base_main_sha"] == "ec31dd43d5f8085b783d3ebb26949d9ff932f402"
    snap = c["compatibility_snapshot"]["cteas_ufotri"]
    assert snap["current_runtime_changed"] is False
    assert snap["atmospheric_forcing_blob_sha"] == "76500c048caac1d9d1bce8a463560adc91d521a0"
    assert snap["atmospheric_metadata_blob_sha"] == "97c47e99bde50af1b8c1a8934bc197bc35cfedb9"
    assert snap["atmospheric_validation_blob_sha"] == "2255d2c5871205639aad9505e32fea2df9f54441"


def test_cteas_atmos_reference_and_semantics_are_pinned() -> None:
    a = _contract()["compatibility_snapshot"]["cteas_atmos"]
    assert a["repository"] == "RRain001/CTEAS-Atmos"
    assert a["reference_sha"] == "341d9d6b3b45b6e2416e09aec0b381adf137fd3e"
    assert a["time_contract"] == "UTC_HALF_OPEN_INTERVAL_WITH_EXPLICIT_TEMPORAL_MEANING"
    assert a["receptor_concentration_contract"] == "RADIONUCLIDE_BQ_M3"
    assert a["deposition_ledger_contract"] == "PER_PUFF_INTERVAL_AMOUNT_NOT_SURFACE_FLUX"


def test_exchange_is_hto_only_and_time_mapping_preserves_p7_semantics() -> None:
    record = _contract()["record_contract"]
    assert record["chemical_identity"] == "HTO"
    assert {"HT", "DT", "T2", "TOTAL_TRITIUM_UNSPECIFIED_MIXTURE"}.issubset(
        set(record["excluded_chemical_identities"])
    )
    time = record["time"]
    assert time["interval"] == "HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE"
    assert time["timezone"] == "UTC"
    assert time["normalized_value_semantics"] == "INTERVAL_REPRESENTATIVE_MEAN_OR_RATE"
    assert time["v3_timestamp_mapping"] == "INTERVAL_START"
    assert time["silent_resampling"] == "FORBIDDEN"


def test_required_quantities_have_exact_consumer_units() -> None:
    q = _contract()["record_contract"]["required_quantities"]
    assert q["air_hto_concentration"]["canonical_unit"] == "Bq m^-3"
    assert q["surface_deposition_flux_total"]["canonical_unit"] == "Bq m^-2 s^-1"
    assert q["air_temperature"]["canonical_unit"] == "K"
    assert q["relative_humidity"]["canonical_unit"] == "1"
    assert q["wind_speed"]["canonical_unit"] == "m s^-1"
    assert q["precipitation_rate"]["canonical_unit"] == "m s^-1"


def test_deposition_ledger_amount_cannot_be_used_as_surface_flux() -> None:
    dep = _contract()["record_contract"]["deposition_components"]
    forbidden = set(dep["forbidden_substitutes"])
    assert "STAGE18_DRY_DEPOSITED_LEDGER_AMOUNT_BQ" in forbidden
    assert "STAGE18_WET_DEPOSITED_LEDGER_AMOUNT_BQ" in forbidden
    assert "PUFF_INVENTORY_LOSS_WITH_HIDDEN_AREA" in forbidden
    assert "ACCUMULATED_BQ_M2_RELABELED_AS_RATE" in forbidden
    assert "SILENT_ZERO_WHEN_FLUX_PRODUCT_UNAVAILABLE" in forbidden
    assert set(dep["allowed_total_derivation_kinds"]) == {
        "DIRECT_SURFACE_PRODUCT",
        "EXPLICIT_DRY_PLUS_WET_SUM",
    }


def test_spatial_support_requires_height_and_identity() -> None:
    spatial = _contract()["record_contract"]["spatial_support"]
    assert spatial["location_id_required"] is True
    assert spatial["air_sampling_height_required"] is True
    assert spatial["vertical_reference_required"] is True
    assert spatial["grid_or_receptor_identity_required"] is True
    assert spatial["hidden_height_assumption"] == "FORBIDDEN"


def test_real_binding_fails_closed_until_surface_flux_exists() -> None:
    binding = _contract()["producer_binding"]
    assert binding["contract_definition"] == "FROZEN"
    assert binding["cteas_atmos_time_semantics"] == "COMPATIBLE"
    assert binding["cteas_atmos_concentration_semantics"] == "COMPATIBLE"
    assert binding["cteas_atmos_surface_deposition_flux_product"] == "UNCONFIRMED"
    assert binding["real_binding_status"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert binding["real_cteas_atmos_coupling_active"] is False
    assert "adapter_test_against_frozen_record_contract" in binding["unblock_requires"]
    assert "independent_cross_project_review" in binding["unblock_requires"]


def test_v3_adapter_mapping_is_documented_but_not_implemented() -> None:
    mapping = _contract()["v3_adapter_mapping"]
    assert mapping["implementation_authorized"] is False
    assert mapping["current_runtime_remains_authority"] is True
    assert mapping["fields"]["start_utc"] == "AtmosphericHTOForcing.timestamp"
    assert mapping["fields"]["surface_deposition_flux_total_bq_m2_s"] == "AtmosphericHTOForcing.deposition_flux"
    assert mapping["adapter_may_change_solver_physics"] is False
    assert mapping["adapter_may_change_p7_5_time_semantics"] is False


def test_schema_requires_complete_exchange_envelope() -> None:
    schema = _schema()
    required = set(schema["required"])
    assert {
        "source_kind",
        "chemical_identity",
        "interval",
        "spatial_support",
        "air_hto_concentration_bq_m3",
        "surface_deposition",
        "air_temperature_k",
        "relative_humidity",
        "wind_speed_m_s",
        "precipitation_rate_m_s",
        "provenance",
        "quality_status",
    }.issubset(required)
    assert schema["properties"]["chemical_identity"]["const"] == "HTO"
    assert schema["properties"]["interval"]["properties"]["semantics"]["const"] == "HALF_OPEN_INTERVAL_REPRESENTATIVE_MEAN_OR_RATE"
    surface = schema["properties"]["surface_deposition"]
    assert set(surface["properties"]["total_derivation_kind"]["enum"]) == {
        "DIRECT_SURFACE_PRODUCT",
        "EXPLICIT_DRY_PLUS_WET_SUM",
    }
    conditional_required = set(surface["allOf"][0]["then"]["required"])
    assert conditional_required == {
        "dry_flux_bq_m2_s",
        "wet_flux_bq_m2_s",
        "derivation_record",
    }


def test_hard_invariants_and_next_stage() -> None:
    c = _contract()
    inv = c["hard_invariants"]
    assert inv["v3_atmos_runtime_changed"] is False
    assert inv["solver_changes_authorized"] is False
    assert inv["numerical_coupling_changes_authorized"] is False
    assert inv["real_cteas_atmos_coupling_active"] is False
    assert inv["puff_ledger_amount_as_surface_flux"] == "FORBIDDEN"
    assert inv["active_parameters"] == 0
    assert inv["calibration_started"] is False
    assert inv["v3_physics_ready"] is False
    assert c["exit_state"]["next_stage"] == "V4_SYSTEM_PHYSICS_GAP_SENSITIVITY_AUDIT"


def test_adr_and_review_preserve_blocked_real_binding() -> None:
    adr = ADR.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")
    assert "must never be relabeled" in adr
    assert "PUFF_LEDGER_AMOUNT_AS_SURFACE_FLUX = FORBIDDEN" in adr
    assert "REAL_PRODUCER_BINDING = BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED" in adr
    assert "CTEAS_ATMOS_SURFACE_DEPOSITION_FLUX_PRODUCT = UNCONFIRMED" in review
    assert "NEXT_STAGE = V4_SYSTEM_PHYSICS_GAP_SENSITIVITY_AUDIT" in review
