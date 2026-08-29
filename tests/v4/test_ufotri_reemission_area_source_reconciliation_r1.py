from __future__ import annotations

import math
from pathlib import Path
import subprocess
import sys

import pytest

from cteas_ufotri.atmosphere.dispersion_parameters import rural_pg_sigma
from cteas_ufotri.coupling.reemission_area_source_v4 import (
    AccountedReemissionLoss,
    HourlyReemissionHandoffBuffer,
    HourlySecondarySource,
    HT_DERIVED_HTO,
    MIXED_HTO_ORIGIN,
    NO_ACTIVITY,
    PLANT,
    PRIMARY_HTO,
    SOIL,
    ManualAreaSourceGeometry,
    eq5_effective_sigma_y_m,
    eq6_equivalent_area_source_concentration_bq_m3,
    superpose_secondary_sources,
)


ROOT = Path(__file__).resolve().parents[2]


def _source(compartment: str, flux: float) -> HourlySecondarySource:
    activity = flux * 400.0 * 3600.0
    return HourlySecondarySource(
        compartment=compartment,
        source_hour_index=0,
        flux_bq_m2_s=flux,
        routed_activity_bq=activity,
        environmental_loss_activity_bq=activity,
        unrouted_activity_bq=0.0,
        origin=PRIMARY_HTO if flux > 0 else NO_ACTIVITY,
        transfer_ids=((f"{compartment}-1",) if flux > 0 else ()),
        origin_proof_ids=(),
    )


def test_manual_geometry_recovers_flqh_and_eq5_width_factor() -> None:
    geometry = ManualAreaSourceGeometry.from_canopy_height(
        length_m=20.0,
        width_m=10.0,
        canopy_height_m=2.0,
    )
    assert geometry.area_m2 == pytest.approx(200.0)
    assert geometry.effective_height_m == pytest.approx(1.6)
    assert geometry.initial_sigma_y_m == pytest.approx(10.0 / 4.3)

    low_canopy = ManualAreaSourceGeometry.from_canopy_height(
        length_m=20.0,
        width_m=10.0,
        canopy_height_m=0.5,
    )
    assert low_canopy.effective_height_m == pytest.approx(1.0)

    sigma = eq5_effective_sigma_y_m(30.0, 10.0)
    assert sigma == pytest.approx(math.sqrt(30.0**2 + (10.0 / 4.3) ** 2))


def test_eq6_center_equivalent_matches_visible_printed_manual_formula() -> None:
    geometry = ManualAreaSourceGeometry(
        length_m=100.0,
        width_m=50.0,
        effective_height_m=1.0,
    )
    flux = 2.0e-4
    x = 800.0
    y = 30.0
    wind = 3.0
    sigma_y, sigma_z = rural_pg_sigma(x, "D")
    sigma_yg = math.sqrt(sigma_y**2 + (50.0 / 4.3) ** 2)
    expected = (
        flux
        * geometry.area_m2
        / (math.pi * wind * sigma_y * sigma_z)
        * math.exp(-0.5 * (y / sigma_yg) ** 2)
        * math.exp(-0.5 * (geometry.effective_height_m / sigma_z) ** 2)
        * 0.8
        * 0.9
    )
    actual = eq6_equivalent_area_source_concentration_bq_m3(
        surface_flux_bq_m2_s=flux,
        geometry=geometry,
        receptor_downwind_m=x,
        receptor_crosswind_m=y,
        wind_speed_m_s=wind,
        stability_class="D",
        fallout_factor=0.8,
        washout_factor=0.9,
    )
    assert actual == pytest.approx(expected, rel=1.0e-14)


def _complete_first_hour(dt_s: int) -> tuple[HourlySecondarySource, HourlySecondarySource]:
    geometry = ManualAreaSourceGeometry(
        length_m=20.0,
        width_m=20.0,
        effective_height_m=1.0,
    )
    buffer = HourlyReemissionHandoffBuffer(
        time_step_seconds=dt_s,
        geometry=geometry,
    )
    for index in range(3600 // dt_s):
        soil, plant = buffer.step(
            (
                AccountedReemissionLoss(
                    compartment=SOIL,
                    flux_bq_m2_s=0.25,
                    origin=PRIMARY_HTO,
                    transfer_id=f"soil-{index}",
                ),
                AccountedReemissionLoss(
                    compartment=PLANT,
                    flux_bq_m2_s=0.10,
                    origin=PRIMARY_HTO,
                    transfer_id=f"plant-{index}",
                ),
            )
        )
        assert soil.flux_bq_m2_s == 0.0
        assert plant.flux_bq_m2_s == 0.0
    return buffer.active_sources()


@pytest.mark.parametrize("dt_s", [600, 300])
def test_hour_n_losses_are_routed_only_in_hour_n_plus_one(dt_s: int) -> None:
    soil, plant = _complete_first_hour(dt_s)
    area = 400.0
    assert soil.source_hour_index == 0
    assert plant.source_hour_index == 0
    assert soil.flux_bq_m2_s == pytest.approx(0.25)
    assert plant.flux_bq_m2_s == pytest.approx(0.10)
    assert soil.routed_activity_bq == pytest.approx(0.25 * area * 3600.0)
    assert plant.routed_activity_bq == pytest.approx(0.10 * area * 3600.0)
    assert soil.environmental_loss_activity_bq == pytest.approx(soil.routed_activity_bq)
    assert plant.environmental_loss_activity_bq == pytest.approx(plant.routed_activity_bq)
    assert soil.unrouted_activity_bq == 0.0
    assert plant.unrouted_activity_bq == 0.0
    assert soil.fully_routed and plant.fully_routed


def test_hourly_handoff_is_activity_and_flux_invariant_to_dt() -> None:
    soil_600, plant_600 = _complete_first_hour(600)
    soil_300, plant_300 = _complete_first_hour(300)
    assert soil_600.flux_bq_m2_s == pytest.approx(soil_300.flux_bq_m2_s)
    assert plant_600.flux_bq_m2_s == pytest.approx(plant_300.flux_bq_m2_s)
    assert soil_600.routed_activity_bq == pytest.approx(soil_300.routed_activity_bq)
    assert plant_600.routed_activity_bq == pytest.approx(plant_300.routed_activity_bq)


def test_mixed_origin_stays_mixed_and_ht_derived_requires_proof() -> None:
    geometry = ManualAreaSourceGeometry(
        length_m=10.0,
        width_m=10.0,
        effective_height_m=1.0,
    )
    buffer = HourlyReemissionHandoffBuffer(
        time_step_seconds=1800,
        geometry=geometry,
    )
    with pytest.raises(ValueError, match="origin_proof_id"):
        AccountedReemissionLoss(
            compartment=SOIL,
            flux_bq_m2_s=0.2,
            origin=HT_DERIVED_HTO,
            transfer_id="bad-derived",
        )

    with pytest.raises(ValueError, match="origin proof"):
        HourlySecondarySource(
            compartment=SOIL,
            source_hour_index=0,
            flux_bq_m2_s=0.2,
            routed_activity_bq=72000.0,
            environmental_loss_activity_bq=72000.0,
            unrouted_activity_bq=0.0,
            origin=HT_DERIVED_HTO,
            transfer_ids=("direct-bypass",),
            origin_proof_ids=(),
        )

    for index in range(2):
        buffer.step(
            (
                AccountedReemissionLoss(
                    compartment=SOIL,
                    flux_bq_m2_s=0.1,
                    origin=PRIMARY_HTO,
                    transfer_id=f"primary-{index}",
                ),
                AccountedReemissionLoss(
                    compartment=SOIL,
                    flux_bq_m2_s=0.1,
                    origin=HT_DERIVED_HTO,
                    transfer_id=f"derived-{index}",
                    origin_proof_id="E2-LINEAGE-1",
                ),
            )
        )
    soil, _ = buffer.active_sources()
    assert soil.origin == MIXED_HTO_ORIGIN
    assert soil.flux_bq_m2_s == pytest.approx(0.2)
    assert soil.origin_proof_ids == ("E2-LINEAGE-1",)


def test_soil_and_plant_eq6_are_separate_then_linearly_superposed() -> None:
    geometry = ManualAreaSourceGeometry(
        length_m=20.0,
        width_m=20.0,
        effective_height_m=1.0,
    )
    result = superpose_secondary_sources(
        primary_air_bq_m3=5.0,
        soil_source=_source(SOIL, 0.2),
        plant_source=_source(PLANT, 0.1),
        geometry=geometry,
        receptor_downwind_m=500.0,
        receptor_crosswind_m=0.0,
        wind_speed_m_s=2.0,
        stability_class="D",
        soil_fallout_factor=1.0,
        soil_washout_factor=1.0,
        plant_fallout_factor=1.0,
        plant_washout_factor=1.0,
    )
    assert result.soil_secondary_bq_m3 > 0.0
    assert result.plant_secondary_bq_m3 > 0.0
    assert result.secondary_air_bq_m3 == pytest.approx(
        result.soil_secondary_bq_m3 + result.plant_secondary_bq_m3
    )
    assert result.total_air_bq_m3 == pytest.approx(5.0 + result.secondary_air_bq_m3)


def test_invalid_geometry_timestep_and_ledger_fail_closed() -> None:
    with pytest.raises(ValueError):
        ManualAreaSourceGeometry(length_m=0.0, width_m=10.0, effective_height_m=1.0)
    with pytest.raises(ValueError, match="at least 1 m"):
        ManualAreaSourceGeometry(length_m=10.0, width_m=10.0, effective_height_m=0.0)
    geometry = ManualAreaSourceGeometry(
        length_m=10.0,
        width_m=10.0,
        effective_height_m=1.0,
    )
    with pytest.raises(ValueError, match="divide 3600"):
        HourlyReemissionHandoffBuffer(time_step_seconds=700, geometry=geometry)
    with pytest.raises(ValueError, match="ledger"):
        HourlySecondarySource(
            compartment=SOIL,
            source_hour_index=0,
            flux_bq_m2_s=1.0,
            routed_activity_bq=10.0,
            environmental_loss_activity_bq=9.0,
            unrouted_activity_bq=0.0,
            origin=PRIMARY_HTO,
            transfer_ids=("x",),
            origin_proof_ids=(),
        )


def test_f1_machine_gate_passes() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/v4/check_ufotri_reemission_area_source_reconciliation_r1.py"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (
        "F1_RECONCILIATION_STATUS=PASS_UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION"
        in completed.stdout
    )
