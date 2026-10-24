"""UFOTRI-native hourly segmented MUSEMET trajectory reconstruction.

This module is the H2 fidelity path authorized by
``UFOTRI_NATIVE_ATMOSPHERE_RECOVERY_PLAN``.  It reconstructs the directly
recoverable trajectory semantics from KfK 4605 Section 2.1 and KfK 4332:

* one trajectory starts at the release site for each hourly start time;
* one meteorological station represents the source region;
* meteorological state is homogeneous within each hourly interval;
* a released trajectory keeps its already-computed segments when later-hour
  wind direction changes;
* each new hourly segment is advanced with that hour's wind speed/direction;
* stability, precipitation and mixing-layer state are attached to the segment;
* source-distance and travel-time termination are explicit;
* restart and coordinate-frame invariance can be verified deterministically.

This is a segmented trajectory, not a multiple-puff implementation.  The fixed
Cartesian coordinates used here are an implementation representation only.  The
canonical frame is east/north relative to the source and may be rigidly rotated
for invariance testing without changing the physical trajectory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import math
from typing import Sequence

from .ufotri_native_v4 import (
    UFOTRINativeAtmosphereError,
    _finite,
    _nonnegative,
    _positive,
    _utc,
)


HOUR_S = 3600.0
_ALLOWED_STABILITY = frozenset("ABCDEF")




def _normalise_rotation_deg(value: float) -> float:
    return _finite(value, field="frame_rotation_deg_ccw") % 360.0


def _rotate_xy(x: float, y: float, rotation_deg_ccw: float) -> tuple[float, float]:
    theta = math.radians(rotation_deg_ccw)
    c = math.cos(theta)
    s = math.sin(theta)
    return c * x - s * y, s * x + c * y


def meteorological_from_to_unit_vector(
    wind_direction_from_deg: float,
    *,
    frame_rotation_deg_ccw: float = 0.0,
) -> tuple[float, float]:
    """Convert meteorological FROM direction to a source-fixed transport vector.

    Input convention is explicit: 0 deg means wind *from* north and 90 deg wind
    *from* east, increasing clockwise.  The canonical source-fixed frame is
    ``x=east, y=north``.  ``frame_rotation_deg_ccw`` only rigidly rotates that
    representation; it does not alter the physical wind.
    """

    direction = _finite(wind_direction_from_deg, field="wind_direction_from_deg")
    if not 0.0 <= direction < 360.0:
        raise UFOTRINativeAtmosphereError(
            "wind_direction_from_deg must be in [0, 360)"
        )
    toward = (direction + 180.0) % 360.0
    theta = math.radians(toward)
    east = math.sin(theta)
    north = math.cos(theta)
    return _rotate_xy(east, north, _normalise_rotation_deg(frame_rotation_deg_ccw))


@dataclass(frozen=True)
class NativeHourlyMeteorology:
    """One spatially homogeneous MUSEMET hourly meteorological record."""

    start_utc: datetime
    station_id: str
    wind_direction_from_deg: float
    wind_speed_m_s: float
    stability_class: str
    precipitation_mm_h: float
    mixing_lid_m: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "start_utc", _utc(self.start_utc, field="start_utc"))
        if not isinstance(self.station_id, str) or not self.station_id.strip():
            raise UFOTRINativeAtmosphereError("station_id is required")
        direction = _finite(
            self.wind_direction_from_deg, field="wind_direction_from_deg"
        )
        if not 0.0 <= direction < 360.0:
            raise UFOTRINativeAtmosphereError(
                "wind_direction_from_deg must be in [0, 360)"
            )
        _nonnegative(self.wind_speed_m_s, field="wind_speed_m_s")
        if not isinstance(self.stability_class, str):
            raise UFOTRINativeAtmosphereError("stability_class must be A-F")
        stability = self.stability_class.upper()
        if stability not in _ALLOWED_STABILITY:
            raise UFOTRINativeAtmosphereError("stability_class must be A-F")
        object.__setattr__(self, "stability_class", stability)
        _nonnegative(self.precipitation_mm_h, field="precipitation_mm_h")
        _positive(self.mixing_lid_m, field="mixing_lid_m")

    @property
    def end_utc(self) -> datetime:
        return self.start_utc + timedelta(seconds=HOUR_S)


class NativeTrajectoryTermination(str, Enum):
    MAX_SOURCE_DISTANCE = "MAX_SOURCE_DISTANCE"
    MAX_TRAVEL_TIME = "MAX_TRAVEL_TIME"
    METEOROLOGY_EXHAUSTED = "METEOROLOGY_EXHAUSTED"


@dataclass(frozen=True)
class NativeTrajectorySegment:
    trajectory_segment_index: int
    meteorology_index: int
    start_utc: datetime
    end_utc: datetime
    start_x_m: float
    start_y_m: float
    end_x_m: float
    end_y_m: float
    path_length_m: float
    cumulative_path_length_m: float
    source_distance_end_m: float
    wind_direction_from_deg: float
    wind_direction_toward_deg: float
    wind_speed_m_s: float
    stability_class: str
    precipitation_mm_h: float
    mixing_lid_m: float
    station_id: str

    @property
    def duration_s(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds()


@dataclass(frozen=True)
class NativeTrajectoryCheckpoint:
    trajectory_start_utc: datetime
    start_meteorology_index: int
    next_meteorology_index: int
    current_utc: datetime
    x_m: float
    y_m: float
    elapsed_s: float
    cumulative_path_length_m: float
    segment_count: int
    station_id: str
    frame_rotation_deg_ccw: float


@dataclass(frozen=True)
class NativeHourlyTrajectory:
    trajectory_start_utc: datetime
    start_meteorology_index: int
    segments: tuple[NativeTrajectorySegment, ...]
    termination: NativeTrajectoryTermination
    elapsed_s: float
    cumulative_path_length_m: float
    end_x_m: float
    end_y_m: float
    station_id: str
    frame_rotation_deg_ccw: float
    checkpoint: NativeTrajectoryCheckpoint

    @property
    def source_distance_end_m(self) -> float:
        return math.hypot(self.end_x_m, self.end_y_m)


def _validate_hourly_sequence(records: Sequence[NativeHourlyMeteorology]) -> None:
    if not records:
        raise UFOTRINativeAtmosphereError("at least one hourly meteorology record is required")
    if any(not isinstance(item, NativeHourlyMeteorology) for item in records):
        raise UFOTRINativeAtmosphereError(
            "all meteorology records must be NativeHourlyMeteorology"
        )
    station = records[0].station_id
    for index, item in enumerate(records):
        if item.station_id != station:
            raise UFOTRINativeAtmosphereError(
                "MUSEMET H2 requires one representative meteorological station"
            )
        if index:
            expected = records[index - 1].start_utc + timedelta(seconds=HOUR_S)
            if item.start_utc != expected:
                raise UFOTRINativeAtmosphereError(
                    "meteorology records must be consecutive one-hour intervals"
                )


def _time_to_circle_boundary_s(
    x_m: float,
    y_m: float,
    vx_m_s: float,
    vy_m_s: float,
    radius_m: float,
) -> float | None:
    """Return first positive line/circle intersection time from an interior point."""

    speed2 = vx_m_s * vx_m_s + vy_m_s * vy_m_s
    if speed2 == 0.0:
        return None
    c = x_m * x_m + y_m * y_m - radius_m * radius_m
    if c >= -1.0e-9:
        return 0.0
    b = 2.0 * (x_m * vx_m_s + y_m * vy_m_s)
    discriminant = b * b - 4.0 * speed2 * c
    if discriminant < 0.0:
        return None
    root = (-b + math.sqrt(discriminant)) / (2.0 * speed2)
    return root if root >= 0.0 else None


def _limits(
    *,
    max_source_distance_m: float | None,
    max_travel_time_s: float | None,
) -> tuple[float | None, float | None]:
    if max_source_distance_m is None and max_travel_time_s is None:
        raise UFOTRINativeAtmosphereError(
            "an explicit max_source_distance_m or max_travel_time_s is required"
        )
    radius = (
        None
        if max_source_distance_m is None
        else _positive(max_source_distance_m, field="max_source_distance_m")
    )
    travel = (
        None
        if max_travel_time_s is None
        else _positive(max_travel_time_s, field="max_travel_time_s")
    )
    return radius, travel


def _run_trajectory(
    records: Sequence[NativeHourlyMeteorology],
    *,
    start_meteorology_index: int,
    max_source_distance_m: float | None,
    max_travel_time_s: float | None,
    frame_rotation_deg_ccw: float,
    checkpoint: NativeTrajectoryCheckpoint | None,
) -> NativeHourlyTrajectory:
    _validate_hourly_sequence(records)
    radius, travel_limit = _limits(
        max_source_distance_m=max_source_distance_m,
        max_travel_time_s=max_travel_time_s,
    )
    rotation = _normalise_rotation_deg(frame_rotation_deg_ccw)
    if isinstance(start_meteorology_index, bool) or not isinstance(
        start_meteorology_index, int
    ):
        raise UFOTRINativeAtmosphereError("start_meteorology_index must be an integer")
    if not 0 <= start_meteorology_index < len(records):
        raise UFOTRINativeAtmosphereError("start_meteorology_index is out of range")

    station = records[0].station_id
    if checkpoint is None:
        trajectory_start = records[start_meteorology_index].start_utc
        next_index = start_meteorology_index
        current_utc = trajectory_start
        x_m = 0.0
        y_m = 0.0
        elapsed_s = 0.0
        cumulative_path = 0.0
        segment_count = 0
    else:
        if not isinstance(checkpoint, NativeTrajectoryCheckpoint):
            raise UFOTRINativeAtmosphereError(
                "checkpoint must be NativeTrajectoryCheckpoint"
            )
        if checkpoint.start_meteorology_index != start_meteorology_index:
            raise UFOTRINativeAtmosphereError("checkpoint start index mismatch")
        if checkpoint.station_id != station:
            raise UFOTRINativeAtmosphereError("checkpoint station mismatch")
        if not math.isclose(
            checkpoint.frame_rotation_deg_ccw,
            rotation,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise UFOTRINativeAtmosphereError("checkpoint coordinate frame mismatch")
        trajectory_start = checkpoint.trajectory_start_utc
        next_index = checkpoint.next_meteorology_index
        current_utc = checkpoint.current_utc
        x_m = checkpoint.x_m
        y_m = checkpoint.y_m
        elapsed_s = checkpoint.elapsed_s
        cumulative_path = checkpoint.cumulative_path_length_m
        segment_count = checkpoint.segment_count
        if next_index < len(records) and current_utc != records[next_index].start_utc:
            raise UFOTRINativeAtmosphereError(
                "checkpoint must resume on an hourly meteorology boundary"
            )

    if travel_limit is not None and elapsed_s >= travel_limit - 1.0e-12:
        raise UFOTRINativeAtmosphereError(
            "max_travel_time_s must exceed checkpoint elapsed time"
        )
    if radius is not None and math.hypot(x_m, y_m) >= radius - 1.0e-9:
        raise UFOTRINativeAtmosphereError(
            "max_source_distance_m must exceed checkpoint source distance"
        )

    segments: list[NativeTrajectorySegment] = []
    termination: NativeTrajectoryTermination | None = None

    while next_index < len(records):
        met = records[next_index]
        if current_utc != met.start_utc:
            raise UFOTRINativeAtmosphereError(
                "trajectory advancement must begin at an hourly interval boundary"
            )

        dt_s = HOUR_S
        termination_if_completed: NativeTrajectoryTermination | None = None

        if travel_limit is not None:
            travel_remaining = travel_limit - elapsed_s
            if travel_remaining <= 1.0e-12:
                termination = NativeTrajectoryTermination.MAX_TRAVEL_TIME
                break
            if travel_remaining < dt_s:
                dt_s = travel_remaining
                termination_if_completed = NativeTrajectoryTermination.MAX_TRAVEL_TIME

        ux, uy = meteorological_from_to_unit_vector(
            met.wind_direction_from_deg,
            frame_rotation_deg_ccw=rotation,
        )
        vx = ux * met.wind_speed_m_s
        vy = uy * met.wind_speed_m_s

        if radius is not None:
            boundary_dt = _time_to_circle_boundary_s(x_m, y_m, vx, vy, radius)
            if boundary_dt is not None and boundary_dt <= dt_s + 1.0e-12:
                if boundary_dt < dt_s - 1.0e-12:
                    dt_s = boundary_dt
                termination_if_completed = NativeTrajectoryTermination.MAX_SOURCE_DISTANCE

        start_x = x_m
        start_y = y_m
        end_x = start_x + vx * dt_s
        end_y = start_y + vy * dt_s
        path_length = met.wind_speed_m_s * dt_s
        end_utc = current_utc + timedelta(seconds=dt_s)
        elapsed_end = elapsed_s + dt_s
        cumulative_end = cumulative_path + path_length

        segments.append(
            NativeTrajectorySegment(
                trajectory_segment_index=segment_count,
                meteorology_index=next_index,
                start_utc=current_utc,
                end_utc=end_utc,
                start_x_m=start_x,
                start_y_m=start_y,
                end_x_m=end_x,
                end_y_m=end_y,
                path_length_m=path_length,
                cumulative_path_length_m=cumulative_end,
                source_distance_end_m=math.hypot(end_x, end_y),
                wind_direction_from_deg=met.wind_direction_from_deg,
                wind_direction_toward_deg=(met.wind_direction_from_deg + 180.0) % 360.0,
                wind_speed_m_s=met.wind_speed_m_s,
                stability_class=met.stability_class,
                precipitation_mm_h=met.precipitation_mm_h,
                mixing_lid_m=met.mixing_lid_m,
                station_id=met.station_id,
            )
        )

        x_m = end_x
        y_m = end_y
        elapsed_s = elapsed_end
        cumulative_path = cumulative_end
        current_utc = end_utc
        segment_count += 1

        if termination_if_completed is not None:
            termination = termination_if_completed
            if math.isclose(dt_s, HOUR_S, rel_tol=0.0, abs_tol=1.0e-12):
                next_index += 1
            break

        next_index += 1

    if termination is None:
        termination = NativeTrajectoryTermination.METEOROLOGY_EXHAUSTED

    cp = NativeTrajectoryCheckpoint(
        trajectory_start_utc=trajectory_start,
        start_meteorology_index=start_meteorology_index,
        next_meteorology_index=next_index,
        current_utc=current_utc,
        x_m=x_m,
        y_m=y_m,
        elapsed_s=elapsed_s,
        cumulative_path_length_m=cumulative_path,
        segment_count=segment_count,
        station_id=station,
        frame_rotation_deg_ccw=rotation,
    )
    return NativeHourlyTrajectory(
        trajectory_start_utc=trajectory_start,
        start_meteorology_index=start_meteorology_index,
        segments=tuple(segments),
        termination=termination,
        elapsed_s=elapsed_s,
        cumulative_path_length_m=cumulative_path,
        end_x_m=x_m,
        end_y_m=y_m,
        station_id=station,
        frame_rotation_deg_ccw=rotation,
        checkpoint=cp,
    )


def build_musemet_hourly_trajectory(
    records: Sequence[NativeHourlyMeteorology],
    *,
    start_meteorology_index: int,
    max_source_distance_m: float | None = None,
    max_travel_time_s: float | None = None,
    frame_rotation_deg_ccw: float = 0.0,
) -> NativeHourlyTrajectory:
    """Build one source-started precomputed segmented hourly trajectory."""

    return _run_trajectory(
        records,
        start_meteorology_index=start_meteorology_index,
        max_source_distance_m=max_source_distance_m,
        max_travel_time_s=max_travel_time_s,
        frame_rotation_deg_ccw=frame_rotation_deg_ccw,
        checkpoint=None,
    )


def resume_musemet_hourly_trajectory(
    records: Sequence[NativeHourlyMeteorology],
    checkpoint: NativeTrajectoryCheckpoint,
    *,
    max_source_distance_m: float | None = None,
    max_travel_time_s: float | None = None,
) -> NativeHourlyTrajectory:
    """Resume at an hourly boundary without recomputing prior segments."""

    return _run_trajectory(
        records,
        start_meteorology_index=checkpoint.start_meteorology_index,
        max_source_distance_m=max_source_distance_m,
        max_travel_time_s=max_travel_time_s,
        frame_rotation_deg_ccw=checkpoint.frame_rotation_deg_ccw,
        checkpoint=checkpoint,
    )


def build_musemet_hourly_trajectory_family(
    records: Sequence[NativeHourlyMeteorology],
    *,
    max_source_distance_m: float | None = None,
    max_travel_time_s: float | None = None,
    frame_rotation_deg_ccw: float = 0.0,
) -> tuple[NativeHourlyTrajectory, ...]:
    """Start one independent MUSEMET trajectory at every hourly source time."""

    _validate_hourly_sequence(records)
    return tuple(
        build_musemet_hourly_trajectory(
            records,
            start_meteorology_index=index,
            max_source_distance_m=max_source_distance_m,
            max_travel_time_s=max_travel_time_s,
            frame_rotation_deg_ccw=frame_rotation_deg_ccw,
        )
        for index in range(len(records))
    )
