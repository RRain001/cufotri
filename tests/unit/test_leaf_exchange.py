"""Framework-only tests for the non-UFOTRI leaf-exchange harness."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.leaf_exchange import (
    LeafExchangeForcing,
    LeafExchangeMassBalance,
    LeafExchangeModel,
    LeafExchangeParameters,
    LeafExchangeState,
    LeafExchangeStateError,
    SyntheticLinearLeafExchangePhysics,
    ZeroExchangePhysics,
)
from cteas_ufotri.leaf_exchange.parameters import LeafExchangeParameterError
from cteas_ufotri.parameters import ParameterDatabase, ParameterUnavailableError
from cteas_ufotri.parameters.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]
TEST_CLASSIFICATION = "FRAMEWORK_TEST_ONLY"
SYNTHETIC_KERNEL_STATUS = "NOT_VALIDATED_UFOTRI_PHYSICS"


PARAMETER_ROLES = {
    "tfwt_exchange_rate_s": "leaf_exchange.tfwt_exchange_rate",
    "obt_formation_rate_s": "leaf_exchange.obt_formation_rate",
    "obt_decay_rate_s": "leaf_exchange.obt_decay_rate",
    "air_to_tfwt_partition_m3_per_kg": "leaf_exchange.air_to_tfwt_partition",
}


def _source_registry() -> SourceRegistry:
    return SourceRegistry.from_file(ROOT / "parameters" / "parameter_sources.yaml")


def _database(*, placeholder: bool = False, negative_rate: bool = False) -> ParameterDatabase:
    values = {
        "tfwt_exchange_rate_s": -0.1 if negative_rate else 0.1,
        "obt_formation_rate_s": 0.01,
        "obt_decay_rate_s": 0.001,
        "air_to_tfwt_partition_m3_per_kg": 1.0e-3,
    }
    entries = []
    for role, name in PARAMETER_ROLES.items():
        if placeholder:
            entries.append(
                {
                    "name": name,
                    "value": None,
                    "unit": "PENDING_VALIDATION",
                    "category": "leaf_exchange",
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
        value = values[role]
        entries.append(
            {
                "name": name,
                "value": value,
                "unit": "s-1" if role != "air_to_tfwt_partition_m3_per_kg" else "m3 kg-1",
                "category": "leaf_exchange",
                "source": "PROJECT_CUSTOM",
                "reference": "TEST_ONLY synthetic parameter",
                "confidence": "internal_default",
                "applicability": {"status": "applicable", "scope": "test_only"},
                "transform": "IDENTITY",
                "bounds": {
                    "lower": -1.0 if negative_rate and role == "tfwt_exchange_rate_s" else 0.0,
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


def _parameters() -> LeafExchangeParameters:
    return LeafExchangeParameters.from_database(
        _database(), parameter_names=PARAMETER_ROLES
    )


def _state(*, tfwt_activity: float = 0.0, obt_activity: float = 0.0) -> LeafExchangeState:
    return LeafExchangeState(
        hto_air_concentration=0.0,
        air_temperature=293.15,
        relative_humidity=0.5,
        tfwt_activity=tfwt_activity,
        obt_activity=obt_activity,
        leaf_water_mass=1.0,
        dry_matter_mass=0.1,
        current_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _forcing(hto_air_concentration: float = 1000.0) -> LeafExchangeForcing:
    return LeafExchangeForcing(
        hto_air_concentration=hto_air_concentration,
        air_temperature=295.15,
        relative_humidity=0.6,
    )


def test_state_initialization_inventory_and_validated_copy() -> None:
    state = _state(tfwt_activity=2.0, obt_activity=30.0)

    assert state.tfwt_inventory == pytest.approx(2.0)
    assert state.obt_inventory == pytest.approx(3.0)
    assert state.total_inventory == pytest.approx(5.0)
    copied = state.copy(tfwt_activity=4.0)
    assert copied.tfwt_activity == pytest.approx(4.0)
    assert copied.obt_activity == state.obt_activity
    assert state.tfwt_activity == pytest.approx(2.0)


@pytest.mark.parametrize(
    "changes",
    [
        {"tfwt_activity": -1.0},
        {"obt_activity": float("nan")},
        {"leaf_water_mass": 0.0},
        {"relative_humidity": 1.1},
        {"air_temperature": float("inf")},
    ],
)
def test_state_rejects_invalid_values(changes: dict[str, object]) -> None:
    with pytest.raises(LeafExchangeStateError):
        _state().copy(**changes)


def test_parameter_database_placeholder_fails_closed() -> None:
    with pytest.raises(ParameterUnavailableError, match="placeholder"):
        LeafExchangeParameters.from_database(
            _database(placeholder=True), parameter_names=PARAMETER_ROLES
        )


def test_parameter_database_provenance_is_attached_to_model() -> None:
    parameters = _parameters()
    model = LeafExchangeModel(
        parameters=parameters,
        physics=ZeroExchangePhysics(),
    )

    provenance = model.provenance()
    assert provenance["implementation_status"] == "FRAMEWORK_COMPLETE"
    assert provenance["physics_equivalence"] == "NOT_CLAIMED"
    assert provenance["parameter_provenance"]["status"] == "TEST_ONLY"
    assert len(provenance["parameter_provenance"]["database_sha256"]) == 64


def test_zero_exchange_is_a_closed_system() -> None:
    model = LeafExchangeModel(parameters=_parameters(), physics=ZeroExchangePhysics())

    new_state, balance = model.advance(_state(tfwt_activity=2.0, obt_activity=30.0), _forcing(), 60.0)

    assert new_state.tfwt_activity == pytest.approx(2.0)
    assert new_state.obt_activity == pytest.approx(30.0)
    assert new_state.delta_t == pytest.approx(60.0)
    assert balance.initial_inventory == pytest.approx(balance.final_inventory)
    assert balance.atmospheric_input == 0.0
    assert balance.leaf_exchange_flux == 0.0
    assert balance.decay_loss == 0.0
    assert balance.closure_error == pytest.approx(0.0, abs=1.0e-15)


def test_synthetic_kernel_conserves_activity_and_updates_both_pools() -> None:
    model = LeafExchangeModel(
        parameters=_parameters(),
        physics=SyntheticLinearLeafExchangePhysics(),
    )

    new_state, balance = model.advance(_state(), _forcing(), 1.0)

    assert new_state.tfwt_activity > 0.0
    assert new_state.obt_activity == pytest.approx(0.0)
    assert balance.atmospheric_input > 0.0
    assert balance.closure_error == pytest.approx(0.0, abs=1.0e-12)
    assert new_state.total_inventory == pytest.approx(
        balance.initial_inventory + balance.atmospheric_input
    )


def test_timestep_is_deterministic_and_scales_the_initial_air_input() -> None:
    model = LeafExchangeModel(
        parameters=_parameters(),
        physics=SyntheticLinearLeafExchangePhysics(),
    )
    state = _state()

    one_state, one_balance = model.advance(state, _forcing(), 1.0)
    two_state, two_balance = model.advance(state, _forcing(), 2.0)
    repeat_state, repeat_balance = model.advance(state, _forcing(), 1.0)

    assert one_state == repeat_state
    assert one_balance == repeat_balance
    assert two_balance.atmospheric_input == pytest.approx(
        2.0 * one_balance.atmospheric_input
    )
    assert two_state.total_inventory == pytest.approx(
        2.0 * one_state.total_inventory
    )


def test_negative_synthetic_inventory_and_invalid_parameter_fail_closed() -> None:
    model = LeafExchangeModel(
        parameters=_parameters(),
        physics=SyntheticLinearLeafExchangePhysics(),
    )
    with pytest.raises(LeafExchangeStateError, match="negative inventory"):
        model.advance(_state(tfwt_activity=1.0), _forcing(hto_air_concentration=0.0), 20.0)

    with pytest.raises(LeafExchangeParameterError, match="non-negative"):
        LeafExchangeParameters.from_database(
            _database(negative_rate=True), parameter_names=PARAMETER_ROLES
        )


def test_framework_default_does_not_silently_run_without_physics() -> None:
    model = LeafExchangeModel(parameters=_parameters())

    with pytest.raises(RuntimeError, match="physics kernel"):
        model.advance(_state(), _forcing(), 1.0)


def test_mass_balance_rejects_nonfinite_and_reports_signed_closure() -> None:
    balance = LeafExchangeMassBalance(
        initial_inventory=10.0,
        atmospheric_input=2.0,
        leaf_exchange_flux=1.0,
        decay_loss=3.0,
        final_inventory=8.0,
    )
    assert balance.closure_error == pytest.approx(0.0)
    with pytest.raises(ValueError):
        LeafExchangeMassBalance(
            initial_inventory=math.nan,
            atmospheric_input=0.0,
            leaf_exchange_flux=0.0,
            decay_loss=0.0,
            final_inventory=0.0,
        )
