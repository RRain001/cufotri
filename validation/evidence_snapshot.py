"""Stable-FD evidence snapshots with fail-closed final source rechecks."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import stat
import tempfile
from typing import Callable, Sequence

from validation.evidence_validation import EvidenceValidationError


CopyHook = Callable[[str, Path, int], None]


@dataclass(frozen=True)
class SourceIdentity:
    """Identity and content recorded for one live source file."""

    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    sha256: str


@dataclass(frozen=True)
class SnapshotRecord:
    """Mapping between one live source and its private snapshot copy."""

    label: str
    source_path: Path | None
    resolved_source_path: Path | None
    snapshot_path: Path
    identity: SourceIdentity | None
    sha256: str


def _identity(st_result: os.stat_result, sha256: str) -> SourceIdentity:
    return SourceIdentity(
        device=st_result.st_dev,
        inode=st_result.st_ino,
        size=st_result.st_size,
        mtime_ns=st_result.st_mtime_ns,
        ctime_ns=st_result.st_ctime_ns,
        sha256=sha256,
    )


def _same_stat(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        left.st_size,
        left.st_mtime_ns,
        left.st_ctime_ns,
    ) == (
        right.st_dev,
        right.st_ino,
        right.st_size,
        right.st_mtime_ns,
        right.st_ctime_ns,
    )


class EvidenceSnapshot:
    """Copy decisive evidence through stable descriptors into a private tree."""

    def __init__(self, *, copy_hook: CopyHook | None = None) -> None:
        self._temporary: tempfile.TemporaryDirectory[str] | None = None
        self._directory: Path | None = None
        self._records: list[SnapshotRecord] = []
        self._by_source: dict[Path, SnapshotRecord] = {}
        self._copy_hook = copy_hook

    def __enter__(self) -> "EvidenceSnapshot":
        self._temporary = tempfile.TemporaryDirectory(
            prefix="cteas_evidence_snapshot_"
        )
        self._directory = Path(self._temporary.name)
        os.chmod(self._directory, 0o700)
        return self

    def __exit__(self, *_: object) -> None:
        if self._temporary is not None:
            self._temporary.cleanup()
        self._temporary = None
        self._directory = None

    @property
    def directory(self) -> Path:
        if self._directory is None:
            raise RuntimeError("EvidenceSnapshot must be used as a context manager")
        return self._directory

    @property
    def records(self) -> tuple[SnapshotRecord, ...]:
        return tuple(self._records)

    @property
    def source_file_count(self) -> int:
        return sum(record.source_path is not None for record in self._records)

    def _destination(self, label: str, suffix: str) -> Path:
        safe_label = "".join(
            character if character.isalnum() or character in "._-" else "_"
            for character in label
        )
        return self.directory / (
            f"{len(self._records):04d}_{safe_label}{suffix}"
        )

    @staticmethod
    def _checked_roots(roots: Sequence[Path]) -> tuple[Path, ...]:
        checked: list[Path] = []
        for root in roots:
            try:
                checked.append(root.resolve(strict=True))
            except (FileNotFoundError, OSError) as exc:
                raise EvidenceValidationError(
                    f"allowed evidence root does not exist: {root}"
                ) from exc
        return tuple(checked)

    @staticmethod
    def _open_source(
        path: Path,
        *,
        allowed_roots: Sequence[Path],
    ) -> tuple[int, Path, os.stat_result]:
        candidate = Path(os.path.abspath(os.fspath(path)))
        roots = EvidenceSnapshot._checked_roots(allowed_roots)
        try:
            listed = os.lstat(candidate)
        except OSError as exc:
            raise EvidenceValidationError(
                f"required file does not exist: {candidate}"
            ) from exc
        if stat.S_ISLNK(listed.st_mode):
            raise EvidenceValidationError(
                f"snapshot source symlink is forbidden: {candidate}"
            )
        if not stat.S_ISREG(listed.st_mode):
            raise EvidenceValidationError(
                f"snapshot source is not a regular file: {candidate}"
            )
        flags = os.O_RDONLY
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(candidate, flags)
        except OSError as exc:
            raise EvidenceValidationError(
                f"cannot stably open snapshot source: {candidate}"
            ) from exc
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise EvidenceValidationError(
                    f"snapshot source is not a regular file: {candidate}"
                )
            if opened.st_size <= 0:
                raise EvidenceValidationError(
                    f"snapshot source is empty: {candidate}"
                )
            if (listed.st_dev, listed.st_ino) != (
                opened.st_dev,
                opened.st_ino,
            ):
                raise EvidenceValidationError(
                    f"snapshot source identity changed while opening: {candidate}"
                )
            resolved = Path(os.path.realpath(candidate))
            if not any(resolved.is_relative_to(root) for root in roots):
                raise EvidenceValidationError(
                    f"path escapes allowed evidence roots: {candidate}"
                )
            return descriptor, resolved, opened
        except Exception:
            os.close(descriptor)
            raise

    def add_path(
        self,
        path: Path,
        *,
        allowed_roots: Sequence[Path],
        label: str,
    ) -> Path:
        """Snapshot one regular file and return the private copy path."""

        source = Path(os.path.abspath(os.fspath(path)))
        existing = self._by_source.get(source)
        if existing is not None:
            return existing.snapshot_path
        descriptor, resolved, before = self._open_source(
            source,
            allowed_roots=allowed_roots,
        )
        destination = self._destination(label, source.suffix)
        digest = hashlib.sha256()
        bytes_copied = 0
        hook_called = False
        destination_descriptor: int | None = None
        try:
            destination_descriptor = os.open(
                destination,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                view = memoryview(chunk)
                while view:
                    written = os.write(destination_descriptor, view)
                    view = view[written:]
                bytes_copied += len(chunk)
                if self._copy_hook is not None and not hook_called:
                    self._copy_hook(label, source, bytes_copied)
                    hook_called = True
            os.fsync(destination_descriptor)
            after = os.fstat(descriptor)
            if not _same_stat(before, after):
                raise EvidenceValidationError(
                    "BLOCKED_EVIDENCE_CHANGED_DURING_SNAPSHOT: "
                    f"{source}"
                )
            if bytes_copied != before.st_size:
                raise EvidenceValidationError(
                    "BLOCKED_EVIDENCE_CHANGED_DURING_SNAPSHOT: "
                    f"short copy for {source}"
                )
            calculated = digest.hexdigest()
            record = SnapshotRecord(
                label=label,
                source_path=source,
                resolved_source_path=resolved,
                snapshot_path=destination,
                identity=_identity(after, calculated),
                sha256=calculated,
            )
            self._records.append(record)
            self._by_source[source] = record
            return destination
        except Exception:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        finally:
            if destination_descriptor is not None:
                os.close(destination_descriptor)
            os.close(descriptor)

    def add_bytes(self, payload: bytes, *, label: str, suffix: str = "") -> Path:
        """Add trusted non-filesystem material, such as a Git blob."""

        destination = self._destination(label, suffix)
        descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        calculated = hashlib.sha256(payload).hexdigest()
        self._records.append(
            SnapshotRecord(
                label=label,
                source_path=None,
                resolved_source_path=None,
                snapshot_path=destination,
                identity=None,
                sha256=calculated,
            )
        )
        return destination

    @staticmethod
    def _hash_descriptor(descriptor: int) -> str:
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        return digest.hexdigest()

    def final_recheck(self) -> None:
        """Reopen every live source and compare identity plus full content hash."""

        for record in self._records:
            if record.source_path is None or record.identity is None:
                continue
            descriptor, resolved, current = self._open_source(
                record.source_path,
                allowed_roots=[record.resolved_source_path.parent],
            )
            try:
                calculated = self._hash_descriptor(descriptor)
            finally:
                os.close(descriptor)
            expected = record.identity
            current_tuple = (
                current.st_dev,
                current.st_ino,
                current.st_size,
                current.st_mtime_ns,
                current.st_ctime_ns,
                calculated,
            )
            expected_tuple = (
                expected.device,
                expected.inode,
                expected.size,
                expected.mtime_ns,
                expected.ctime_ns,
                expected.sha256,
            )
            if resolved != record.resolved_source_path or current_tuple != expected_tuple:
                raise EvidenceValidationError(
                    "BLOCKED_EVIDENCE_CHANGED_AFTER_SNAPSHOT: "
                    f"{record.source_path}"
                )

    def preserve_for_debugging(self, destination: Path) -> None:
        """Copy a snapshot for an explicitly requested local debugging workflow."""

        shutil.copytree(self.directory, destination)
