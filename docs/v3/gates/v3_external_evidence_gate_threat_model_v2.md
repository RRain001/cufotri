# V3 external-evidence gate threat model v2

Date: 2026-07-26

## Security objective

The production gate may return `READY_FOR_BOUNDED_V3_PHYSICS` only when a
protected Git policy approves the exact empirical dataset and all decisive
evidence survives schema, chronology, checksum, snapshot-identity, and
preregistered holdout checks. In the absence of real approved evidence the
gate remains `BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA`.

## Trusted boundary

The following are trusted:

- reviewed gate and schema code;
- the fixed production policy path
  `validation/v3/policy/trusted_external_evidence_registry.yaml`;
- aligned protected refs `refs/heads/main` and
  `refs/remotes/origin/main`;
- a maintainer approval record committed before registry publication;
- the runtime schemas copied into the private snapshot;
- isolated snapshot files used after stable-FD acquisition.

The registry is read with `git show <trusted-sha>:<fixed-path>`. The current
working-tree registry, feature-branch registry, evidence bundle, and CLI cannot
select or replace the production policy.

## Untrusted inputs

The raw manifest, intake manifest, bundle, raw and result files, calibration,
identifiability, holdout, self-declared evidence type, authority/licence text,
`test_only`, `artifact_purpose`, `origin_class`, fixture paths, config path,
allowed raw-root declarations, and legacy readiness booleans are untrusted.
They are cross-check material, never a trust root.

Production eligibility requires an exact protected-registry match on:

```text
dataset_id
raw_manifest_sha256
evidence_type
empirical_eligibility = APPROVED
test_only = false
licence_review.status = approved
```

Source authority metadata must also agree exactly. Test-only, pytest, fixture,
synthetic, or "not empirical" markers fail closed in production even if an
untrusted manifest self-declares an eligible evidence type.

## Approval chronology and non-self-referential hashes

A Git commit cannot contain its own final commit SHA, so an entry that names
the commit containing itself is not implementable. This contract uses two
ordered commits:

1. an approval record commits the canonical entry and registry-projection
   hashes;
2. a later registry commit publishes the entry, names the earlier approval
   commit, and binds the approval-record content hash.

The canonical eligibility hashes omit the later `approval` wrapper and the
approval record's own content hash. The gate then proves:

```text
approval record commit
  < registry entry commit
  < preregistration commit
  < first holdout commit
```

Both approval and registry commits must be ancestors of protected `main`.
The approval record retrieved from its declared commit must reproduce both
canonical hashes and its committed byte hash.

## Explicitly excluded attacker capabilities

This model does not claim to defeat an attacker who can:

- modify reviewed gate source or runtime schemas;
- rewrite protected Git history or control both trusted approvers and refs;
- compromise the kernel, filesystem, Git executable, or Python runtime;
- mutate memory after verification;
- subvert the host while the final check and return instruction execute.

These are deployment and host-integrity boundaries, not manifest-level
properties.

## Production status

The production registry is intentionally empty and the production evidence
bundle is null. Therefore:

```text
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```
