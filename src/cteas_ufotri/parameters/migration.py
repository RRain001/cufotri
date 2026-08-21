"""Lifecycle transitions and audit records for P5.1 parameter migration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from collections import Counter
from typing import Iterable

from .exceptions import ParameterMigrationError
from .schema import ParameterEntry, ParameterStatus


_ORDER = {
    ParameterStatus.PLACEHOLDER.value: 0,
    ParameterStatus.CANDIDATE.value: 1,
    ParameterStatus.REVIEWED.value: 2,
    ParameterStatus.VALIDATED.value: 3,
    ParameterStatus.ACTIVE.value: 4,
}


def _status(value: str | ParameterStatus) -> str:
    return value.value if isinstance(value, ParameterStatus) else value


@dataclass(frozen=True)
class ParameterMigrationRecord:
    """One explicit lifecycle transition with human-auditable provenance."""

    parameter_id: str
    old_status: str | ParameterStatus
    new_status: str | ParameterStatus
    changed_by: str
    timestamp: datetime | str
    reason: str

    def __post_init__(self) -> None:
        old_status = _status(self.old_status)
        new_status = _status(self.new_status)
        timestamp = self.timestamp
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ParameterMigrationError("Invalid migration timestamp") from exc
        object.__setattr__(self, "old_status", old_status)
        object.__setattr__(self, "new_status", new_status)
        object.__setattr__(self, "timestamp", timestamp)
        statuses = set(_ORDER)
        if not isinstance(self.parameter_id, str) or "." not in self.parameter_id:
            raise ParameterMigrationError("Migration record requires a dotted parameter_id")
        if self.old_status not in statuses or self.new_status not in statuses:
            raise ParameterMigrationError("Migration record contains an unknown status")
        if _ORDER[self.new_status] != _ORDER[self.old_status] + 1:
            raise ParameterMigrationError(
                f"Illegal lifecycle transition {self.old_status!r} -> {self.new_status!r}"
            )
        if not isinstance(self.changed_by, str) or not self.changed_by.strip():
            raise ParameterMigrationError("Migration record requires changed_by")
        if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
            raise ParameterMigrationError("Migration record timestamp must be timezone-aware")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ParameterMigrationError("Migration record requires a reason")

    @classmethod
    def create(
        cls,
        parameter_id: str,
        old_status: str | ParameterStatus,
        new_status: str | ParameterStatus,
        *,
        changed_by: str,
        reason: str,
        timestamp: datetime | None = None,
    ) -> "ParameterMigrationRecord":
        return cls(
            parameter_id=parameter_id,
            old_status=_status(old_status),
            new_status=_status(new_status),
            changed_by=changed_by,
            timestamp=timestamp or datetime.now(timezone.utc),
            reason=reason,
        )

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "ParameterMigrationRecord":
        raw_timestamp = value["timestamp"]
        if not isinstance(raw_timestamp, str):
            raise ParameterMigrationError("Migration timestamp must be an ISO-8601 string")
        try:
            timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ParameterMigrationError("Invalid migration timestamp") from exc
        return cls(
            parameter_id=str(value["parameter_id"]),
            old_status=str(value["old_status"]),
            new_status=str(value["new_status"]),
            changed_by=str(value["changed_by"]),
            timestamp=timestamp,
            reason=str(value["reason"]),
        )

    def to_mapping(self) -> dict[str, str]:
        return {
            "parameter_id": self.parameter_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "changed_by": self.changed_by,
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat().replace(
                "+00:00", "Z"
            ),
            "reason": self.reason,
        }


class ParameterMigrationAudit:
    """Deterministic collection of lifecycle records."""

    def __init__(self, records: Iterable[ParameterMigrationRecord] = ()) -> None:
        self._records = list(records)
        self.validate()

    def add(self, record: ParameterMigrationRecord) -> None:
        if not isinstance(record, ParameterMigrationRecord):
            raise ParameterMigrationError("Audit accepts ParameterMigrationRecord instances")
        self._records.append(record)
        try:
            self.validate()
        except Exception:
            self._records.pop()
            raise

    add_record = add

    def validate(self) -> None:
        last_status: dict[str, str] = {}
        for record in self._records:
            previous = last_status.get(record.parameter_id)
            if previous is not None and record.old_status != previous:
                raise ParameterMigrationError(
                    f"Migration audit has a lifecycle gap for {record.parameter_id!r}: "
                    f"expected old_status {previous!r}, got {record.old_status!r}"
                )
            last_status[record.parameter_id] = record.new_status

    @property
    def records(self) -> tuple[ParameterMigrationRecord, ...]:
        return tuple(self._records)

    def for_parameter(self, parameter_id: str) -> tuple[ParameterMigrationRecord, ...]:
        return tuple(record for record in self._records if record.parameter_id == parameter_id)

    def has_activation_record(self, parameter_id: str) -> bool:
        return any(
            record.parameter_id == parameter_id
            and record.new_status == ParameterStatus.ACTIVE.value
            for record in self._records
        )

    def to_mapping(self) -> list[dict[str, str]]:
        return [record.to_mapping() for record in self._records]


def migration_audit_report(
    parameters: Iterable[ParameterEntry],
    audit: ParameterMigrationAudit,
) -> dict[str, object]:
    """Build a deterministic, report-ready migration audit summary."""

    entries = sorted(parameters, key=lambda item: item.parameter_id)
    status_counts = Counter(entry.status for entry in entries)
    return {
        "schema_version": "1.0",
        "framework_status": "FRAMEWORK_COMPLETE",
        "parameter_count": len(entries),
        "status_counts": dict(sorted(status_counts.items())),
        "parameters": [
            {
                "parameter_id": entry.parameter_id,
                "module": entry.module,
                "status": entry.status,
                "source": entry.source,
                "source_type": entry.source_type,
                "reference": entry.reference,
            }
            for entry in entries
        ],
        "migration_records": audit.to_mapping(),
        "ufotri_parameter_activation": "NOT_CLAIMED",
        "physics_activation": "NOT_STARTED",
    }


def transition_parameter(
    parameter: ParameterEntry,
    new_status: str | ParameterStatus,
    *,
    changed_by: str,
    reason: str,
    timestamp: datetime | None = None,
) -> tuple[ParameterEntry, ParameterMigrationRecord]:
    """Return a new entry and its mandatory transition record."""

    if parameter._format != "migration":
        raise ParameterMigrationError("Only P5.1 migration entries may change lifecycle status")
    record = ParameterMigrationRecord.create(
        parameter.parameter_id,
        parameter.status,
        new_status,
        changed_by=changed_by,
        reason=reason,
        timestamp=timestamp,
    )
    updated = ParameterEntry(
        parameter_id=parameter.parameter_id,
        value=parameter.value,
        unit=parameter.unit,
        description=parameter.description,
        module=parameter.module,
        status=record.new_status,
        source=parameter.source,
        source_type=parameter.source_type,
        reference=parameter.reference,
        uncertainty=parameter.uncertainty,
        valid_range=parameter.valid_range,
        notes=parameter.notes,
    )
    return updated, record
