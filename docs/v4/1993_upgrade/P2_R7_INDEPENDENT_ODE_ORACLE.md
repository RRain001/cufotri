# P2 R7 — independent ODE oracle for the R6 conditional ledger

**Scope:** numerical cross-check only. This does **not** introduce a new
1993 plant equation, historical solve-order assertion, production coupling,
or a new physical source/sink. The frozen 1990 solver is unchanged.

## Source and declared research hypothesis

Authority for rate constants remains W. Raskob, KfK 5194 (1993),
printed §5.5.2 Eq.(32), pp.22–23 and COMA Tables 9–12, pp.86–89,
official source: https://publikationen.bibliothek.kit.edu/270034158/3813483.
See R3's pinned table SHA and R4–R6 source audit notes. The exact
triangular operator is explicitly a **synthetic, no-feedback hypothesis**,
not a claim about the original 1993 executable.

The independent test transcribes grass formation 0.0081 d^-1 and
outflows (0.024, 0.018, 0.0029, 0.0015) d^-1, and leafy formation
0.0025 d^-1 and outflow 0.032 d^-1. Each daily rate is divided by
24 h/d. The test solves the full **H, B, S1, ..., Sn** ODEs using
classical fourth-order Runge–Kutta, with 0.025 h steps over two
12 h intervals. This oracle does not call R6's matrix-exponential
convolution, sink allocation or implementation helpers.

## Acceptance boundary

The test independently checks every end-of-interval HTO/parent-OBT
inventory, each individual sink increment, whole-day branch totals,
and closed activity in Bq/m² ground. Cases cover both crops, both
day/night orderings, externally supplied Figure 11 factors
(0, 0.7, 2), and initially present/absent parent OBT: 24 combinations.
The oracle tolerance is 2e-10 relative for H/B and 2e-9 absolute
for sinks, with 2e-9 absolute ODE closure. These tolerances compare
two numerical methods on the **same assumed ODE**, not measurements.

The R6 test and this oracle are only a bounded mathematical check.
Eq.(28)–(30) source discrepancies, Eq.(33) advanced nighttime route,
Figure 11 reconstruction, dry-mass/ground-area normalization, real
receiving states, original-executable parity, external datasets and
independent scientific review remain **NOT_ESTABLISHED/NOT_RUN**.
Draft PR #159 must not be merged based on this numerical result.
