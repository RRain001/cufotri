# V3 provenance contract

Status: `ARCHITECTURE_ONLY`

Provenance records the immutable V2 candidate anchor, migration tool version,
original and resolved configuration hashes, parameter-package hash,
forcing-manifest hash, external-data-manifest hash, feature flags, and module
versions.

Null hashes mean that the corresponding input class was not used; they do not
mean that provenance collection failed. Feature flags record all registered
modules, including `false` values, so absence cannot be confused with a
default. Provenance is write-only metadata and cannot influence numerical
state or dispatch.
