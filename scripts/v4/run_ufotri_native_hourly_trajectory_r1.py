#!/usr/bin/env python3
"""Machine gate for UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

from cteas_ufotri.atmosphere.ufotri_native_trajectory_v4 import (
    NativeHourlyMeteorology,
    NativeTrajectoryTermination,
    build_musemet_hourly_trajectory,
    build_musemet_hourly_trajectory_family,
    resume_musemet_hourly_trajectory,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _records() -> tuple[NativeHourlyMeteorology, ...]:
    directions = (270.0, 180.0, 90.0, 0.0)
    speeds = (1.0, 2.0, 1.5, 0.5)
    stability = ("D", "C", "E", "F")
    precipitation = (0.0, 1.2, 0.4, 0.0)
    lids = (500.0, 600.0, 450.0, 350.0)
    return tuple(
        NativeHourlyMeteorology(
            start_utc=T0 + timedelta(hours=index),
            station_id="SOURCE_MET",
            wind_direction_from_deg=directions[index],
            wind_speed_m_s=speeds[index],
            stability_class=stability[index],
            precipitation_mm_h=precipitation[index],
            mixing_lid_m=lids[index],
        )
        for index in range(4)
    )


def _segments_signature(segments):
    return [
        (
            item.meteorology_index,
            item.start_utc.isoformat(),
            item.end_utc.isoformat(),
            item.start_x_m,
            item.start_y_m,
            item.end_x_m,
            item.end_y_m,
            item.path_length_m,
            item.cumulative_path_length_m,
            item.stability_class,
            item.precipitation_mm_h,
            item.mixing_lid_m,
        )
        for item in segments
    ]


def build_result() -> dict:
    records = _records()
    direct = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=4.0 * 3600.0,
    )
    first_half = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=2.0 * 3600.0,
    )
    second_half = resume_musemet_hourly_trajectory(
        records,
        first_half.checkpoint,
        max_travel_time_s=4.0 * 3600.0,
    )
    restarted_signature = _segments_signature(first_half.segments + second_half.segments)

    rotated = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_travel_time_s=4.0 * 3600.0,
        frame_rotation_deg_ccw=90.0,
    )
    distance_limited = build_musemet_hourly_trajectory(
        records,
        start_meteorology_index=0,
        max_source_distance_m=1800.0,
    )
    family = build_musemet_hourly_trajectory_family(
        records,
        max_travel_time_s=3600.0,
    )

    roadmap = Path("docs/v4/roadmap/UFOTRI_NATIVE_ATMOSPHERE_RECOVERY_PLAN.md").read_text(
        encoding="utf-8"
    )

    direct_source_distances = [item.source_distance_end_m for item in direct.segments]
    rotated_source_distances = [item.source_distance_end_m for item in rotated.segments]

    manual_semantics = {
        "h2_authorized_in_roadmap": "UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1" in roadmap,
        "one_trajectory_each_hour": len(family) == len(records)
        and all(item.trajectory_start_utc == records[i].start_utc for i, item in enumerate(family)),
        "single_station_preserved": all(
            segment.station_id == "SOURCE_MET"
            for trajectory in family
            for segment in trajectory.segments
        ),
        "hourly_segment_metadata_preserved": all(
            segment.stability_class == records[segment.meteorology_index].stability_class
            and segment.precipitation_mm_h
            == records[segment.meteorology_index].precipitation_mm_h
            and segment.mixing_lid_m == records[segment.meteorology_index].mixing_lid_m
            for segment in direct.segments
        ),
        "wind_change_bends_without_rewriting_previous_segment": math.isclose(
            direct.segments[0].end_x_m, 3600.0, abs_tol=1.0e-9
        )
        and math.isclose(direct.segments[0].end_y_m, 0.0, abs_tol=1.0e-9)
        and math.isclose(direct.segments[1].start_x_m, 3600.0, abs_tol=1.0e-9)
        and direct.segments[1].end_y_m > direct.segments[1].start_y_m,
        "travel_time_termination_explicit": direct.termination
        is NativeTrajectoryTermination.MAX_TRAVEL_TIME,
        "source_distance_termination_explicit": distance_limited.termination
        is NativeTrajectoryTermination.MAX_SOURCE_DISTANCE,
    }

    numerical_checks = {
        "deterministic_restart": _segments_signature(direct.segments)
        == restarted_signature,
        "restart_endpoint_equal": math.isclose(
            direct.end_x_m, second_half.end_x_m, rel_tol=0.0, abs_tol=1.0e-9
        )
        and math.isclose(
            direct.end_y_m, second_half.end_y_m, rel_tol=0.0, abs_tol=1.0e-9
        ),
        "coordinate_rotation_preserves_source_distance": all(
            math.isclose(a, b, rel_tol=0.0, abs_tol=1.0e-8)
            for a, b in zip(direct_source_distances, rotated_source_distances)
        ),
        "coordinate_rotation_preserves_path_length": math.isclose(
            direct.cumulative_path_length_m,
            rotated.cumulative_path_length_m,
            rel_tol=0.0,
            abs_tol=1.0e-8,
        ),
        "distance_boundary_is_radial": math.isclose(
            distance_limited.source_distance_end_m,
            1800.0,
            rel_tol=0.0,
            abs_tol=1.0e-8,
        ),
        "family_members_start_at_source": all(
            not trajectory.segments
            or (
                math.isclose(trajectory.segments[0].start_x_m, 0.0, abs_tol=1.0e-12)
                and math.isclose(trajectory.segments[0].start_y_m, 0.0, abs_tol=1.0e-12)
            )
            for trajectory in family
        ),
    }

    forbidden_claims = {
        "multiple_puff_model": False,
        "spatially_varying_meteorology": False,
        "cteas_atmos_wind_field": False,
        "instantaneous_global_plume_rotation": False,
        "building_wake_closed": False,
        "thermal_lift_closed": False,
        "forcing_adapter_closed": False,
        "original_musemet_numerical_equivalence": False,
    }

    passed = (
        all(manual_semantics.values())
        and all(numerical_checks.values())
        and not any(forbidden_claims.values())
    )
    return {
        "schema_version": "v1",
        "stage": "UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1",
        "status": "PASS_UFOTRI_NATIVE_HOURLY_TRAJECTORY" if passed else "FAIL",
        "authority": [
            "KfK 4605 Section 2.1",
            "KfK 4332 Section 2 / Appendix C TRAJEC",
        ],
        "manual_semantics": manual_semantics,
        "numerical_checks": numerical_checks,
        "forbidden_claims": forbidden_claims,
        "termination_examples": {
            "travel_time": direct.termination.value,
            "source_distance": distance_limited.termination.value,
        },
    }


def main() -> None:
    result = build_result()
    print(f"UFOTRI_NATIVE_HOURLY_TRAJECTORY_STATUS={result['status']}")
    print("UFOTRI_NATIVE_HOURLY_TRAJECTORY_RESULT_JSON=" + json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_UFOTRI_NATIVE_HOURLY_TRAJECTORY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
