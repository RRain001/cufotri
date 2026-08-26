# V3.1 Mass-Basis Contract — Main Merge Closure

## Status

```ini
V3_1_MASS_BASIS_CONTRACT = PASS_MAIN_MERGED
IMPLEMENTATION_PR = 3
IMPLEMENTATION_HEAD = 95f78801d0fa3b507e6bd76249b192adf8b107cb
R2_REVIEW_HEAD = 7a06733f3201cc60c4c6599799892899cdb61d7f
R2_VERDICT = PASS_INDEPENDENT_REREVIEW
MAIN_BEFORE_MERGE = d24aa03b00dcb586a2d93e678f42cb7853b7c078
MAIN_MERGE_COMMIT = 43eabee5fc5029441c00cc0221d84bf887bc4660
```

## Merge evidence

PR #3 was merged by an explicitly authorized standard GitHub merge commit.
Squash and rebase were not used, preserving all implementation and review SHAs.

The merge commit was independently read back from GitHub and verified to have:

```text
parent 1 = d24aa03b00dcb586a2d93e678f42cb7853b7c078
parent 2 = 95f78801d0fa3b507e6bd76249b192adf8b107cb
merge tree = b2d06370e5c1ec2f7322aceabbbc2e909ae6f442
implementation tree = b2d06370e5c1ec2f7322aceabbbc2e909ae6f442
```

Therefore `MERGE_TREE_DRIFT = FALSE`.

## Independent review evidence

Luna R1 returned a real HOLD on the earlier target and its finding was
remediated. Luna R2 independently reviewed exact frozen implementation SHA
`95f78801d0fa3b507e6bd76249b192adf8b107cb` and returned
`PASS_INDEPENDENT_REREVIEW` with zero blocking findings at review head
`7a06733f3201cc60c4c6599799892899cdb61d7f`.

The R2 request, handoff, and result are now retained in the main-integration
closure line. R2 review PR #6 was intentionally closed unmerged; its branch is
retained as audit evidence.

## Scientific and runtime boundaries

The V3.1 merge does not imply physical readiness or authorize V4 model physics.
It only closes the typed mass-basis/tissue-scope/area-basis/provenance contract.

```ini
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
P7_5_SEMANTICS_CHANGED = FALSE
P7_5B_SEMANTICS_CHANGED = FALSE
EXISTING_STATE_SERIALIZATION_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

## Next gate

The next stage is P7.8C / V4 Implementation Authorization Gate. Entering that
gate does not itself authorize dynamic stomata, two-pool OBT, root water-flux,
or any other new solver physics. The first V4 candidate remains
`V4_DATA_AND_STATE_CONTRACTS`, which is control-plane contract work only and
must be explicitly authorized by P7.8C.
