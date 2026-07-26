# External-evidence snapshot security contract

Date: 2026-07-26

## Acquisition

Every decisive live file is opened with `O_RDONLY`, `O_CLOEXEC`, and
`O_NOFOLLOW` where supported. Before copying, the gate requires a nonempty
regular file inside an allowed root and records:

```text
st_dev
st_ino
st_size
st_mtime_ns
st_ctime_ns
```

The file is copied only through the already opened descriptor into a private
temporary directory with mode `0700`; snapshot files use mode `0600`.
SHA-256 is computed during that copy, the destination is `fsync`ed, and a
second `fstat` must match the initial identity. A change produces
`BLOCKED_EVIDENCE_CHANGED_DURING_SNAPSHOT`.

## Snapshot coverage

One snapshot context covers:

- gate configuration and runtime schemas;
- evidence bundle and raw-data manifest;
- all raw files;
- intake manifest;
- preregistration record and frozen preregistration file;
- calibration and identifiability results;
- holdout result and every referenced result file;
- V1, V2, and validation-readiness reports;
- protected-ref registry content and committed licence/approval record.

All JSON/YAML/CSV parsing, schema validation, primary-metric recomputation,
numeric verdict evaluation, and checksum comparisons after acquisition use
these private copies. Protected policy blobs are copied directly from Git
objects, not from the working tree.

## Final decision boundary

The ready path is:

```text
create one private snapshot
-> validate snapshot schemas and content
-> match protected registry and chronology
-> recompute primary metrics from frozen observation/prediction columns
-> recompute holdout verdict from frozen comparators and thresholds
-> validate regression artifacts
-> reject dirty tracked preregistration/holdout/result paths
-> confirm protected refs did not change
-> reopen every live source with O_NOFOLLOW
-> compare path, device, inode, size, mtime, ctime, and full SHA-256
-> immediately return the snapshot-derived verdict
```

A final mismatch produces
`BLOCKED_EVIDENCE_CHANGED_AFTER_SNAPSHOT`. No decisive value is reread from
the live evidence path after the final source recheck.

## Operating constraints and residual boundary

Formal runs require a read-only evidence directory, no concurrent writers, a
local trusted filesystem rather than an untrusted network filesystem, a
private snapshot directory, and automatic cleanup on completion. Hard-link
mutation, rename replacement, symlink switching, same-size replacement, and
timestamp-restoration attempts are detected by identity, ctime, and full-hash
checks under the stated host assumptions.

The contract does not claim to eliminate theoretical TOCTOU against a
compromised kernel/filesystem or an attacker who can change data in the
instruction interval after the final syscall and before return.

```text
TOCTOU_BOUNDARY =
SNAPSHOT_BASED_WITH_FINAL_IDENTITY_AND_HASH_RECHECK
```
