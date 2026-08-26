# V4-2 Leaf Evidence Acquisition R1

## Scope

This round searches for public empirical evidence capable of satisfying the
V4-2 matched leaf evidence packet. It is an evidence-triage stage only. No
candidate dataset is admitted by citation, abstract, article methods, or semantic
compatibility alone.

Entry main:

`702ce51fccc167127b7a318f3d8652c064e73aef`

Hard boundaries remain:

```ini
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```

## R1 search decision

No candidate was found that can be declared a complete V4-2 empirical packet
from publicly indexed metadata alone. R1 therefore ends in:

```text
HOLD_FILE_LEVEL_EVIDENCE_AUDIT_REQUIRED
```

The primary next task is file-level inspection of the two soybean datasets below.

## Priority 1 — Monnens et al. soybean VPD dataset

Dataset DOI: `10.5061/dryad.h18931zrh`

Related article DOI: `10.1111/nph.18929`

Public dataset file: `Monnens_et_al_All_data_Dryad.xlsx`

Why it is the first priority:

- the system is soybean (`Glycine max`), with two named elite genotypes;
- leaf gas exchange was measured with an LI-6800;
- stomatal conductance to water vapour was measured;
- controlled experiments manipulated VPD while temperature and other
  environmental variables such as PAR were held constant;
- field gas-exchange measurements used chamber conditions that tracked ambient
  temperature, relative humidity and light;
- the associated data repository is public.

The public article therefore establishes a strong soybean/VPD/gas-exchange
relationship. It does **not**, by itself, prove that the downloadable workbook
contains all row-level fields required by the V4-2 packet.

The file-level audit must verify at minimum:

1. `g_sw` or an equivalent target column and its measurement basis;
2. VPD and unit;
3. leaf temperature and unit at the same observation/alignment level;
4. PAR/light or a traceable constant-condition field;
5. timestamps or interval semantics;
6. genotype/plant/replicate identity sufficient to define independent groups;
7. an explicit growth-stage field or a source-supported ontology instance;
8. enough VPD support to define an admissible response domain rather than only
   a two-endpoint contrast.

Until those are proven, this dataset is a **priority candidate**, not an admitted
validation packet.

## Priority 2 — Tomeo & Rosenthal soybean gas-exchange dataset

Dataset DOI: `10.5061/dryad.2gd3b`

Related article DOI: `10.1104/pp.16.01940`

Relevant public files include:

- `CE_GasExchangeParameters.csv`
- `Field_GasExchangeParameters.csv`
- corresponding README files.

This dataset is unusually valuable for V4-2 stage semantics because the
associated study explicitly distinguishes soybean developmental states:

- late vegetative: V4/V5;
- early reproductive: R2-R4;
- late reproductive: R6;
- controlled-environment measurements before flowering.

It also contains soybean stomatal-conductance measurements and gas-exchange
parameter tables. However, the currently indexed evidence does not establish
that the tables contain row-level VPD, leaf temperature, time alignment and a
dynamic environmental response domain needed for the full candidate model.

Disposition: **stage-strong component evidence; file audit required**.

The stage evidence cannot simply be combined with an unrelated VPD dataset and
called a matched packet. Any multi-dataset use would require an explicitly
reviewed model/evidence composition rule and cannot prove joint-condition
support by itself.

## Methodological benchmark — Rizzo et al. 2026

Dataset DOI: `10.5061/dryad.5x69p8djr`

Related article DOI: `10.1111/nph.70949`

This dataset is the strongest R1 methodological benchmark. Its public metadata
explicitly identifies stomatal conductance, leaf temperature, PPFD/light, VPD,
timestamps, species/leaf sampling, and dedicated light- and VPD-response files.
The paper also emphasizes true stomatal steady state, leaf-to-leaf variability,
and the risk of fitting a steady-state model to transient measurements.

It is not an admissible final soybean packet because the listed measured species
are cowpea, eastern redbud and walnut and R1 did not identify a dataset-bound
growth-stage ontology. No cross-species parameter value may be imported from
this dataset.

Disposition: **method/protocol benchmark only**.

Its main value for V4-2 is methodological: future soybean acquisition should
prefer matched leaf-level environmental measurements, true or justified
steady-state handling, sufficient leaf/replicate coverage, and explicit
response-domain support.

## Secondary context — Peirone et al. 2018

Article DOI: `10.3389/fpls.2018.00587`

The study measured soybean stomatal conductance at multiple days after emergence,
leaf temperature at multiple dates, and characterized transpiration response to
VPD in a greenhouse phenotyping experiment. It is useful contextual evidence.

R1 did not identify a public raw machine-readable dataset proving that
stomatal conductance, leaf temperature, VPD/light and plant identity are matched
at the packet record level. Days after emergence also cannot be silently
converted into the V4-2 growth-stage ontology.

Disposition: **secondary context pending raw-data discovery**.

## R1 evidence hierarchy

```text
PRIORITY FILE AUDIT
  Monnens 2023 soybean VPD / gas exchange
  Tomeo-Rosenthal 2018 soybean gas exchange / explicit stages

METHOD BENCHMARK
  Rizzo 2026 stomatal calibration protocol and response data

SECONDARY CONTEXT
  Peirone 2018 soybean greenhouse phenotyping
```

No entry in this hierarchy authorizes calibration or implementation.

## Required R2 decision

R2 should inspect actual source files for the two soybean priority candidates and
produce a column-level evidence matrix against the specialized schema at:

`schemas/v4/v4_leaf_empirical_evidence_packet.schema.json`

For every required field R2 must classify it as:

- `DIRECT_COLUMN`
- `DECLARED_CONSTANT_WITH_PROVENANCE`
- `EXPLICIT_DERIVATION_SUPPORTED`
- `MISSING`
- `AMBIGUOUS`

Only the first three classes are potentially admissible, and any derivation must
already satisfy the V4-2 conversion/provenance rules. A missing stage ontology,
independent-group identity, matched forcing, or holdout-safe response domain
keeps the item on HOLD.

## Sources reviewed in R1

- Dryad `10.5061/dryad.h18931zrh`; Monnens, Denison & Sadok, New Phytologist,
  `10.1111/nph.18929`.
- Dryad `10.5061/dryad.2gd3b`; Tomeo & Rosenthal, Plant Physiology,
  `10.1104/pp.16.01940`.
- Dryad `10.5061/dryad.5x69p8djr`; Rizzo et al., New Phytologist,
  `10.1111/nph.70949`.
- Peirone et al., Frontiers in Plant Science, `10.3389/fpls.2018.00587`.

Search/review date: 2026-08-26.
