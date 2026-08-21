from __future__ import annotations

from datetime import datetime, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.parameters import ParameterDatabase, ParameterSchemaError, ParameterUnavailableError
from cteas_ufotri.parameters.registry import SourceRegistry
from cteas_ufotri.soil import (
    SoilForcing,
    SoilLayer,
    SoilMassBalance,
    SoilModel,
    SoilParameterError,
    SoilParameters,
    SoilState,
    SoilStateError,
    SyntheticTransportKernel,
    ZeroTransportKernel,
    apply_atmospheric_input,
    get_root_zone_activity,
)
from cteas_ufotri.soil.physics import advance as advance_physics


ROOT = Path(__file__).resolve().parents[2]


PARAMETER_ROLES = {
    "interlayer_transport_rate_s": "soil.interlayer_transport_rate",
    "decay_rate_s": "soil.decay_rate",
}


def _source_registry() -> SourceRegistry:
    return SourceRegistry.from_file(ROOT / "parameters" / "parameter_sources.yaml")


def _database(*, placeholder: bool = False, negative_rate: bool = False) -> ParameterDatabase:
    values = {
        "interlayer_transport_rate_s": -0.1 if negative_rate else 0.1,
        "decay_rate_s": 0.001,
    }
    entries = []
    for role, name in PARAMETER_ROLES.items():
        if placeholder:
            entries.append(
                {
                    "name": name,
                    "value": None,
                    "unit": "PENDING_VALIDATION",
                    "category": "soil",
                    "source": "UFOTRI_VALIDATED",
                    "reference": "TEST_ONLY placeholder",
                    "confidence": "placeholder_pending_validation",
                    "applicability": {
                        "status": "pending_validation",
                        "scope": "test_only",
                    },
                    "transform": "IDENTITY",
                    "bounds": None,
                }
            )
            continue
        entries.append(
            {
                "name": name,
                "value": values[role],
                "unit": "s-1",
                "category": "soil",
                "source": "PROJECT_CUSTOM",
                "reference": "TEST_ONLY synthetic parameter",
                "confidence": "internal_default",
                "applicability": {"status": "applicable", "scope": "test_only"},
                "transform": "IDENTITY",
                "bounds": {
                    "lower": -1.0 if negative_rate and role == "interlayer_transport_rate_s" else 0.0,
                    "upper": 10.0,
                    "lower_inclusive": True,
                    "upper_inclusive": True,
                },
            }
        )
    return ParameterDatabase.from_mapping(
        {"schema_version": "1.0", "parameters": entries},
        source_registry=_source_registry(),
    )


def _parameters() -> SoilParameters:
    return SoilParameters.from_database(
        _database(), parameter_names=PARAMETER_ROLES
    )


def _layer(layer_id: int, hto_activity: float = 0.0) -> SoilLayer:
    return SoilLayer(
        layer_id=layer_id,
        depth_top=(layer_id - 1) * 0.05,
        depth_bottom=layer_id * 0.05,
        water_inventory=0.01,
        hto_activity=hto_activity,
    )


def _state(*activities: tuple[float, float, float] | None) -> SoilState:
    values = activities[0] if activities else (0.0, 0.0, 0.0)
    return SoilState(
        layers=tuple(_layer(index + 1, value) for index, value in enumerate(values)),
        current_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _forcing(*, deposition_flux: float = 0.0) -> SoilForcing:
    return SoilForcing(
        hto_air_concentration=100.0,
        deposition_flux=deposition_flux,
    )


def test_three_layer_state_initialization_and_derived_quantities() -> None:
    state = _state((10.0, 20.0, 30.0))

    assert tuple(layer.layer_id for layer in state.layers) == (1, 2, 3)
    assert state.layers[0].depth == pytest.approx(0.05)
    assert state.layers[0].water_content == pytest.approx(0.2)
    assert state.layers[0].hto_inventory == pytest.approx(10.0)
    assert state.layers[0].hto_concentration == pytest.approx(1000.0)
    assert state.total_water_inventory == pytest.approx(0.03)
    assert state.total_hto_inventory == pytest.approx(60.0)
    assert state.copy(delta_t=30.0).delta_t == pytest.approx(30.0)
    assert state.delta_t == 0.0


@pytest.mark.parametrize(
    "factory",
    [
        lambda: SoilLayer(1, 0.05, 0.01, 0.01, 0.0),
        lambda: SoilLayer(1, 0.0, 0.05, 0.01, -1.0),
        lambda: SoilLayer(1, 0.0, 0.05, 0.0, 1.0),
        lambda: SoilLayer(1, 0.0, 0.05, 0.01, float("nan")),
        lambda: SoilLayer(1, 0.0, 0.05, float("inf"), 0.0),
    ],
)
def test_invalid_layer_geometry_or_activity_is_rejected(factory) -> None:
    with pytest.raises(SoilStateError):
        factory()


def test_soil_state_rejects_non_three_layer_or_misordered_profile() -> None:
    with pytest.raises(SoilStateError, match="exactly three"):
        SoilState((_layer(1), _layer(2)))  # type: ignore[arg-type]
    with pytest.raises(SoilStateError, match="ordered"):
        SoilState((_layer(1), _layer(3), _layer(2)))


def test_placeholder_soil_parameters_fail_closed_and_numeric_provenance_is_kept() -> None:
    with pytest.raises(ParameterUnavailableError, match="placeholder"):
        SoilParameters.from_database(
            _database(placeholder=True), parameter_names=PARAMETER_ROLES
        )

    parameters = _parameters()
    assert parameters.status == "TEST_ONLY"
    assert len(parameters.database_hash) == 64
    assert set(parameters.provenance) == set(PARAMETER_ROLES)


def test_zero_transport_is_closed_and_updates_only_time() -> None:
    model = SoilModel(parameters=_parameters(), physics=ZeroTransportKernel())
    state = _state((10.0, 20.0, 30.0))

    final, balance = model.advance(state, _forcing(), 60.0)

    assert final.layers == state.layers
    assert final.current_time > state.current_time
    assert final.delta_t == pytest.approx(60.0)
    assert balance.initial_inventory == pytest.approx(balance.final_inventory)
    assert balance.atmospheric_input == 0.0
    assert balance.internal_transfer == 0.0
    assert balance.decay_loss == 0.0
    assert balance.output_to_plants == 0.0
    assert balance.closure_error == pytest.approx(0.0, abs=1.0e-15)


def test_atmospheric_input_enters_surface_and_closes_inventory() -> None:
    state = _state((10.0, 0.0, 0.0))
    updated, input_bq_m2 = apply_atmospheric_input(state, _forcing(deposition_flux=2.0), 10.0)

    assert input_bq_m2 == pytest.approx(20.0)
    assert updated.layers[0].hto_inventory == pytest.approx(30.0)
    assert updated.layers[1:] == state.layers[1:]
    assert updated.current_time == state.current_time

    model = SoilModel(parameters=_parameters(), physics=ZeroTransportKernel())
    final, balance = model.advance(state, _forcing(deposition_flux=2.0), 10.0)
    assert final.total_hto_inventory == pytest.approx(30.0)
    assert balance.atmospheric_input == pytest.approx(20.0)
    assert balance.closure_error == pytest.approx(0.0)


def test_synthetic_transport_is_deterministic_and_conservative() -> None:
    model = SoilModel(parameters=_parameters(), physics=SyntheticTransportKernel())
    state = _state((100.0, 0.0, 0.0))

    final, balance = model.advance(state, _forcing(), 1.0)
    repeat, repeat_balance = model.advance(state, _forcing(), 1.0)

    assert final == repeat
    assert balance == repeat_balance
    assert balance.internal_transfer > 0.0
    assert balance.decay_loss > 0.0
    assert balance.output_to_plants == 0.0
    assert balance.closure_error == pytest.approx(0.0, abs=1.0e-12)
    assert final.total_hto_inventory == pytest.approx(
        state.total_hto_inventory - balance.decay_loss
    )
    assert min(layer.hto_inventory for layer in final.layers) >= 0.0


def test_root_zone_activity_is_read_only_and_has_no_uptake_side_effect() -> None:
    state = _state((10.0, 20.0, 30.0))
    root = get_root_zone_activity(state)

    assert root.layer_id == 2
    assert root.hto_activity == pytest.approx(20.0)
    assert root.hto_concentration == pytest.approx(2000.0)
    assert root.status == "SEAM_ONLY_NO_ROOT_UPTAKE"
    assert state.total_hto_inventory == pytest.approx(60.0)
    with pytest.raises(ValueError):
        get_root_zone_activity(state, layer_id=4)


def test_large_timestep_would_be_negative_and_fails_closed() -> None:
    model = SoilModel(parameters=_parameters(), physics=SyntheticTransportKernel())

    with pytest.raises(SoilStateError, match="negative inventory"):
        model.advance(_state((100.0, 0.0, 0.0)), _forcing(), 20.0)


def test_invalid_parameter_and_forcing_values_fail_closed() -> None:
    with pytest.raises(SoilParameterError, match="non-negative"):
        SoilParameters.from_database(
            _database(negative_rate=True), parameter_names=PARAMETER_ROLES
        )
    with pytest.raises(ParameterSchemaError):
        _database_with_nan()
    with pytest.raises(SoilStateError):
        SoilForcing(hto_air_concentration=math.inf, deposition_flux=0.0)
    with pytest.raises(SoilStateError):
        SoilForcing(hto_air_concentration=0.0, deposition_flux=-1.0)


def _database_with_nan() -> ParameterDatabase:
    document = {
        "schema_version": "1.0",
        "parameters": [
            {
                "name": "soil.interlayer_transport_rate",
                "value": float("nan"),
                "unit": "s-1",
                "category": "soil",
                "source": "PROJECT_CUSTOM",
                "reference": "TEST_ONLY invalid",
                "confidence": "internal_default",
                "applicability": {"status": "applicable", "scope": "test_only"},
                "transform": "IDENTITY",
                "bounds": {
                    "lower": 0.0,
                    "upper": 10.0,
                    "lower_inclusive": True,
                    "upper_inclusive": True,
                },
            }
        ],
    }
    return ParameterDatabase.from_mapping(document, source_registry=_source_registry())


def test_default_physics_and_model_provenance_are_explicit() -> None:
    model = SoilModel(parameters=_parameters())

    with pytest.raises(RuntimeError, match="physics kernel"):
        model.advance(_state(), _forcing(), 1.0)
    provenance = model.provenance()
    assert provenance["implementation_status"] == "FRAMEWORK_COMPLETE"
    assert provenance["root_uptake_status"] == "NOT_IMPLEMENTED"
    assert provenance["physics_equivalence"] == "NOT_CLAIMED"


def test_physics_advance_adapter_accepts_explicit_test_kernel() -> None:
    result = advance_physics(
        _state((10.0, 0.0, 0.0)),
        _forcing(),
        1.0,
        _parameters(),
        kernel=ZeroTransportKernel(),
    )

    assert result.layers[0].hto_inventory == pytest.approx(10.0)
    assert result.internal_transfer == 0.0


def test_mass_balance_contract_exposes_internal_transfer_without_net_effect() -> None:
    balance = SoilMassBalance(
        initial_inventory=100.0,
        atmospheric_input=20.0,
        internal_transfer=7.0,
        decay_loss=10.0,
        output_to_plants=5.0,
        final_inventory=105.0,
    )

    assert balance.closure_error == pytest.approx(0.0)
    assert balance.scale >= 100.0
    with pytest.raises(ValueError):
        SoilMassBalance(
            initial_inventory=math.nan,
            atmospheric_input=0.0,
            internal_transfer=0.0,
            decay_loss=0.0,
            output_to_plants=0.0,
            final_inventory=0.0,
        )
