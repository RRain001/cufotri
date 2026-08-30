from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import math
from pathlib import Path

import pytest

from cteas_ufotri.atmosphere.ufotri_native_trajectory_v4 import (
    NativeHourlyMeteorology,
    NativeTrajectoryTermination,
    UFOTRINativeAtmosphereError,
    build_musemet_hourly_trajectory,
    build_musemet_hourly_trajectory_family,
    meteorological_from_to_unit_vector,
    resume_musemet_hourly_trajectory,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _records() -> tuple[NativeHourlyMeteorology, ...]:
    return (
        NativeHourlyMeteorology(T0, "SITE", 270.0, 1.0, "D", 0.0, 500.0),
        NativeHourlyMeteorology(T0 + timedelta(hours=1), "SITE", 180.0, 2.0, "C", 1.2, 600.0),
        NativeHourlyMeteorology(T0 + timedelta(hours=2), "SITE", 90.0, 1.5, "E", 0.4, 450.0),
        NativeHourlyMeteorology(T0 + timedelta(hours=3), "SITE", 0.0, 0.5, "F", 0.0, 350.0),
    )


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_native_hourly_trajectory_r1.py"
    )
    spec = importlib.util.spec_from_file_location("native_hourly_trajectory_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _signature(segments):
    return [
        (
            s.trajectory_segment_index,
            s.meteorology_index,
            s.start_utc,
            s.end_utc,
            s.start_x_m,
            s.start_y_m,
            s.end_x_m,
            s.end_y_m,
            s.path_length_m,
            s.cumulative_path_length_m,
            s.stability_class,
            s.precipitation_mm_h,
            s.mixing_lid_m,
        )
        for s in segments
    ]


def test_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_UFOTRI_NATIVE_HOURLY_TRAJECTORY"
    assert all(result["manual_semantics"].values())
    assert all(result["numerical_checks"].values())
    assert not any(result["forbidden_claims"].values())


def test_meteorological_from_direction_is_converted_to_transport_toward_vector() -> None:
    west_wind = meteorological_from_to_unit_vector(270.0)
    assert west_wind[0] == pytest.approx(1.0, abs=1.0e-15)
    assert west_wind[1] == pytest.approx(0.0, abs=1.0e-15)

    south_wind = meteorological_from_to_unit_vector(180.0)
    assert south_wind[0] == pytest.approx(0.0, abs=1.0e-15)
    assert south_wind[1] == pytest.approx(1.0, abs=1.0e-15)


def test_hourly_wind_change_creates_bent_segmented_trajectory_without_rewriting_past() -> None:
    records = _records()
    two_hours = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=2.0 * 3600.0,
    )
    three_hours = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=3.0 * 3600.0,
    )

    assert len(two_hours.segments) == 2
    assert two_hours.segments[0].end_x_m == pytest.approx(3600.0)
    assert two_hours.segments[0].end_y_m == pytest.approx(0.0, abs=1.0e-10)
    assert two_hours.segments[1].start_x_m == pytest.approx(3600.0)
    assert two_hours.segments[1].end_x_m == pytest.approx(3600.0, abs=1.0e-10)
    assert two_hours.segments[1].end_y_m == pytest.approx(7200.0)
    assert _signature(two_hours.segments) == _signature(three_hours.segments[:2])


def test_segment_carries_corresponding_hourly_stability_precipitation_and_mixing_lid() -> None:
    records = _records()
    trajectory = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=3.5 * 3600.0,
    )
    for segment in trajectory.segments:
        met = records[segment.meteorology_index]
        assert segment.station_id == met.station_id
        assert segment.wind_direction_from_deg == met.wind_direction_from_deg
        assert segment.wind_speed_m_s == met.wind_speed_m_s
        assert segment.stability_class == met.stability_class
        assert segment.precipitation_mm_h == met.precipitation_mm_h
        assert segment.mixing_lid_m == met.mixing_lid_m


def test_family_starts_one_independent_trajectory_at_every_hourly_source_time() -> None:
    records = _records()
    family = build_musemet_hourly_trajectory_family(
        records,
        max_travel_time_s=1800.0,
    )
    assert len(family) == len(records)
    for index, trajectory in enumerate(family):
        assert trajectory.trajectory_start_utc == records[index].start_utc
        assert trajectory.start_meteorology_index == index
        assert trajectory.segments[0].start_x_m == 0.0
        assert trajectory.segments[0].start_y_m == 0.0
        assert trajectory.segments[0].meteorology_index == index


def test_travel_time_termination_is_explicit_and_partial_final_hour_is_preserved() -> None:
    trajectory = build_musemet_hourly_trajectory(
        _records(),
        start_meteorology_index=0,
        max_travel_time_s=2.5 * 3600.0,
    )
    assert trajectory.termination is NativeTrajectoryTermination.MAX_TRAVEL_TIME
    assert trajectory.elapsed_s == pytest.approx(9000.0)
    assert [s.duration_s for s in trajectory.segments] == [3600.0, 3600.0, 1800.0]


def test_maximum_source_distance_is_radial_not_cumulative_path_length() -> None:
    records = (
        NativeHourlyMeteorology(T0, "SITE", 270.0, 1.0, "D", 0.0, 500.0),
        NativeHourlyMeteorology(T0 + timedelta(hours=1), "SITE", 180.0, 1.0, "D", 0.0, 500.0),
    )
    trajectory = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_source_distance_m=4000.0,
    )
    assert trajectory.termination is NativeTrajectoryTermination.MAX_SOURCE_DISTANCE
    assert trajectory.source_distance_end_m == pytest.approx(4000.0, abs=1.0e-8)
    assert trajectory.cumulative_path_length_m > trajectory.source_distance_end_m


def test_coordinate_frame_rotation_is_rigid_and_does_not_change_physical_invariants() -> None:
    records = _records()
    base = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=3.5 * 3600.0,
    )
    rotated = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=3.5 * 3600.0,
        frame_rotation_deg_ccw=90.0,
    )
    assert rotated.cumulative_path_length_m == pytest.approx(base.cumulative_path_length_m)
    assert rotated.source_distance_end_m == pytest.approx(base.source_distance_end_m)
    for original, transformed in zip(base.segments, rotated.segments):
        assert transformed.source_distance_end_m == pytest.approx(original.source_distance_end_m)
        assert transformed.end_x_m == pytest.approx(-original.end_y_m, abs=1.0e-8)
        assert transformed.end_y_m == pytest.approx(original.end_x_m, abs=1.0e-8)


def test_restart_at_hourly_boundary_matches_direct_trajectory_exactly() -> None:
    records = _records()
    direct = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=3.5 * 3600.0,
    )
    prefix = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=2.0 * 3600.0,
    )
    continuation = resume_musemet_hourly_trajectory(
        records,
        prefix.checkpoint,
        max_travel_time_s=3.5 * 3600.0,
    )
    assert _signature(prefix.segments + continuation.segments) == _signature(direct.segments)
    assert continuation.end_x_m == direct.end_x_m
    assert continuation.end_y_m == direct.end_y_m
    assert continuation.elapsed_s == direct.elapsed_s
    assert continuation.cumulative_path_length_m == direct.cumulative_path_length_m


def test_single_representative_station_contract_fails_closed() -> None:
    records = list(_records())
    records[2] = NativeHourlyMeteorology(
        records[2].start_utc,
        "OTHER_SITE",
        records[2].wind_direction_from_deg,
        records[2].wind_speed_m_s,
        records[2].stability_class,
        records[2].precipitation_mm_h,
        records[2].mixing_lid_m,
    )
    with pytest.raises(UFOTRINativeAtmosphereError, match="one representative"):
        build_musemet_hourly_trajectory(
            tuple(records),
            start_meteorology_index=0,
            max_travel_time_s=3600.0,
        )


def test_nonconsecutive_hourly_meteorology_fails_closed() -> None:
    records = list(_records())
    records[2] = NativeHourlyMeteorology(
        T0 + timedelta(hours=2, minutes=1),
        "SITE",
        90.0,
        1.5,
        "E",
        0.4,
        450.0,
    )
    with pytest.raises(UFOTRINativeAtmosphereError, match="consecutive one-hour"):
        build_musemet_hourly_trajectory(
            tuple(records),
            start_meteorology_index=0,
            max_travel_time_s=3600.0,
        )


def test_termination_limit_is_required_and_invalid_direction_fails_closed() -> None:
    with pytest.raises(UFOTRINativeAtmosphereError, match="explicit"):
        build_musemet_hourly_trajectory(_records(), start_meteorology_index=0)
    with pytest.raises(UFOTRINativeAtmosphereError, match="\[0, 360\)"):
        NativeHourlyMeteorology(T0, "SITE", 360.0, 1.0, "D", 0.0, 500.0)


def test_h2_api_contains_no_puff_or_spatial_wind_field_objects() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "cteas_ufotri"
        / "atmosphere"
        / "ufotri_native_trajectory_v4.py"
    )
    text = module_path.read_text(encoding="utf-8")
    assert "class Puff" not in text
    assert "CTEAS-Atmos" not in text
    assert "wind_field" not in text
    assert "spatially varying" not in text
