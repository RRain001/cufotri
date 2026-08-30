# UFOTRI Public-Source Recovery Reassessment R1

## Purpose and scope

This is a post-G4 **evidence-only, non-stage** reassessment. It records newly recovered public archival evidence relevant to source-limited UFOTRI claims after completion of `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1`.

This report does **not** reopen A-G4, does not authorize a new internal replication stage, and does not change production code, default behavior, real CTEAS-Atmos status, empirical-validation status, production readiness, or the claim boundary on original-executable numerical equivalence.

Public sources only were used. No author, archive, laboratory, vendor, or institution was contacted by email or other private communication.

## Recovered authoritative/public evidence

### 1. KfK 4605: printed Eq. (44) semantics are directly recoverable

Authoritative source:

- W. Raskob, *UFOTRI: Program for Assessing the Off-Site Consequences from Accidental Tritium Releases*, KfK 4605, 1990.
- KITopen record: `270029395`.
- Public full text: `https://publikationen.bibliothek.kit.edu/270029395/3813413`.

The public manual explicitly prints Eq. (44) and defines its terms. The recoverable printed relation is the soil-evaporation-driven re-emission rate using actual evaporation `Eas`, top-soil water inventory `BODWA`, downward-flux correction `ABFLR`, constants `C1` and `C2`, and the exponential time factor `ZT`. The text also states that `C1` is chosen to give 10 %/h re-emission under strong insolation at 20 % soil water, `C2` halves the rate when an essential fraction of the source is HT, and the no-insolation/night term starts from `DIFF = 1 %/h` at 20 % soil water before time/water-content adjustment.

Reassessment:

- the historical statement that the **printed Eq. (44) mechanism itself** is unavailable or unrecoverable is too broad;
- the remaining source limit is narrower: exact source-code realization, numerical discretization, hidden branch ordering, and binary-level behavior of the unavailable original executable are still not proven.

No implementation change is authorized by this evidence alone.

### 2. KfK 5194: UFOTRI 4.0 loader contract, defaults, source-member topology and test JCL are publicly documented

Authoritative source:

- W. Raskob, *Description of the New Version 4.0 of the Tritium Model UFOTRI including user guide*, KfK 5194, 1993.
- KITopen record: `270034158`.
- Public full text: `https://publikationen.bibliothek.kit.edu/270034158/3813483`.

Recovered facts include:

- the program is described as standard FORTRAN-77 plus `INCLUDE` and `NAMELIST`;
- the distribution required five FORTRAN members: `TEILO`, `TEIL1`, `TEIL4`, `SCOMMON`, and `PARAM`;
- `TEILO` contained data statements, general/optional NAMELIST read statements and frame control output; `TEIL1` contained the main program; `TEIL4` contained the main UFOTRI dispersion/ingestion/dose subroutine; `SCOMMON` and `PARAM` carried COMMON blocks and dimensions;
- the manual explicitly states that the source was copied from an **UFOTRI tape** to the user's computer;
- UFOTRI used FORTRAN NAMELIST input with program-defined defaults; the user supplied only parameters deviating from defaults, and input variable names had to be identical to program variable names;
- the manual documents obligatory/optional input groups, many software-specific variable names, parameter meanings and defaults;
- a historical `TEST JCL` is printed, including the source dataset `INR303.UFOTRI.FORT`, the members `TEILO`, `TEIL1`, `TEIL4`, meteorological/start-time datasets, an executable test input deck, and test/output datasets `INR303.BEISPIEL.TRITDA1` through `TRITDA5`;
- logical units 91-93 are explicitly described as testing outputs for selected concentrations/areas/time courses; unit 95 stores dose arrays;
- the test deck preserves real internal names and selected values such as `NSTOP`, `BODFAK`, `REMRE`, `IZFREI`, `BODEIN`, `Q`, `Q1`, plant/cow parameters, dose coefficients, hydrology switches and root/soil options;
- the manual documents re-emission controls `REMRE`, `REMNI`, `REDREM`, with public defaults including 0.3 %/h during rain, 1.0 %/h at night, and a re-emission-rate factor of 1.0;
- the later UFOTRI 4.0 re-emission relation is explicitly documented as an evaporation-driven daytime term plus a basic diffusion/re-emission term, with night-time tied to the basic rate.

Reassessment of UFR-30:

- `ORIGINAL_PARAMETER_LOADER_AND_HIDDEN_DEFAULTS` can no longer be described broadly as if software-specific field names, input structure and documented defaults are unavailable;
- the **input/loader contract is substantially recovered from authoritative public documentation**;
- what remains unavailable is the actual original loader/source member contents, any defaults not documented in the manuals, and exact executable behavior not inferable from the published interface.

Therefore UFR-30 remains an evidence limitation, but its blocker must be narrowed rather than treated as total loader/default unavailability.

### 3. KfK 4853: the test-deck lineage predates KfK 5194

Authoritative source:

- W. Raskob, *User Guide for UFOTRI*, KfK 4853, 1991.
- KITopen record: `270030531`.
- Public full text: `https://publikationen.bibliothek.kit.edu/270030531/3813429`.

KfK 4853 independently documents the FORTRAN-77/IMSL execution environment, the special hourly meteorological input record, and an earlier example job/test control deck using the same `INR303` dataset family. This establishes continuity of the published execution/test interface rather than a one-off 1993 example.

### 4. FZKA 7281: documented golden/reference test results demonstrably existed

Authoritative source:

- W. Raskob, *Test and validation studies performed with UFOTRI and NORMTRI*, FZKA 7281, 2007.
- KITopen record: `270067869`.
- Public full text: `https://publikationen.bibliothek.kit.edu/270067869/3814964`.

The report identifies `UFOTRI (version 93/4.4)` and states that UFOTRI/NORMTRI were distributed with user guides and **test procedures**. It further states that these test procedures ensured that an installation produced **exactly the results documented for the test case**. UFOTRI is reported to have had more than 20 users.

Reassessment of UFR-29:

- historical golden/reference test outputs are no longer merely hypothetical; authoritative evidence proves that documented reference results existed;
- however, the actual distribution test-result files, original executable, or original source code have still not been recovered publicly in this reassessment;
- therefore `UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED` remains unchanged.

### 5. Savannah River deployment and formal V&V package are publicly evidenced

Public sources:

- `WSRC-MS-98-00027`, *Evaluating Postulated Tritium Releases on a Large DOE Site Using ...* (OSTI public full text). It identifies personal-computer `UFOTRI version 93/4.20P`, last updated in October 1997, and the operational chain `METPRE -> TRAJEC -> SAMPLE -> UFOTRI -> EVAL`.
- `WSRC-MS-2000-00075`, *A Posteriori Verification and Validation of a Tritium Dispersion & Consequence Model*.

The V&V paper records a formal posteriori qualification process and identifies an SQA document set including an Assessment Document, Quality Plan, User Manual/Technical Documentation, Configuration Control Document, Configuration Procedure, UFOTRI Test Plan, UFOTRI Test Report, Comprehensive Technical Report, and SQA Qualification Report.

Reassessment:

- the existence of a historically configuration-controlled, formally tested branch of UFOTRI is public evidence;
- the actual Test Report / Comprehensive Technical Report / controlled executable or source package was not recovered in this public-only pass;
- these documents remain priority archival targets, but their existence does not establish numerical equivalence by itself.

### 6. Canada 1987: primary participant evidence is publicly recoverable

Primary/public evidence located:

- `JAERI-M 88-232`, M. Murata et al., *Experimental results of JAERI in the Canadian HT field release study of June 10, 1987*, 83 pages, 1988. JAEA/JOPSS and the National Diet Library list public full text (`JAERI-M-88-232.pdf`). The report covers atmospheric dispersion, soil deposition, HT->HTO conversion, HTO soil migration, evaporation/air-water exchange, vegetation transfer and derived parameters.
- `LA-11368-MS`, R. A. Jalbert and C. E. Murphy, *The Canadian experimental HT release of June 10, 1987, US measurements*, 1988, DOI `10.2172/6683617`.
- the 1988 *Fusion Technology* special issue contains the Canadian campaign papers on atmospheric dispersion/oxidation, soil interaction, vegetation, U.S. measurements, JAERI measurements, modelling, re-emission and related processes.
- public abstracts preserve key experiment facts: a 3.54 TBq (95.7 Ci) HT release over 30 minutes at about 1 m height; measurements to 400 m; HT/HTO ratios and deposition/vegetation observations.
- the original Canadian reports `CFFTP-G-88007` and `CFFTP-G-88027` are bibliographically identified but their full authoritative raw data packages were not recovered in this pass.

Reassessment of UFR-27:

- it is no longer accurate to characterize the Canada benchmark as lacking all underlying primary reports/data;
- multiple primary participant reports and contemporaneous measurement papers are publicly identifiable, and at least the JAERI report is publicly listed as full text;
- `CANADA_1987_FULL_NUMERIC_REPLAY_READY=FALSE` must nevertheless remain because authoritative full point arrays, the exact UFOTRI benchmark meteorological sequence/release-clock alignment, precipitation allocation and the complete historical reference series have not yet been recovered as a closed replay packet.

### 7. ITER: later authoritative UFOTRI assessment lineage is publicly available

Public source:

- W. Raskob, I. Hasemann, L. Di Pace, *Final documentation on dose assessments for three potential European ITER candidate sites with updated source terms from ITER NSSR-2*, FZKA 6404, 2000, KITopen `270047359`.

Together with FZKA 7281, this strengthens the public validation/deployment lineage of later UFOTRI versions. It does not supply the missing original numerical details needed to convert the already-completed G2 benchmark-contract reconstruction into original-executable or full atmospheric numerical equivalence.

Therefore `ITER_FULL_ATMOSPHERIC_NUMERIC_REPLAY_COMPLETE=FALSE` remains unchanged.

## Revised blocker disposition after public-only recovery

| Item | Post-G4 public-source reassessment | What is now recovered | What remains unavailable |
|---|---|---|---|
| UFR-12 / Eq. (44) | `PRINTED_MECHANISM_RECOVERED_EXECUTABLE_SEMANTICS_SOURCE_LIMITED` | Printed 1990 Eq. (44), term definitions, calibration statements; later 1993 re-emission relation/default controls | Exact original source-code realization/discretization/binary behavior |
| UFR-27 / Canada 1987 | `PRIMARY_SOURCE_SET_EXPANDED_FULL_REPLAY_STILL_SOURCE_LIMITED` | JAERI primary report, US report identity, campaign papers, core release/measurement facts | Closed authoritative replay packet, exact historical met/release/precip series and complete point arrays |
| UFR-28 / ITER | `LATER_AUTHORITATIVE_VALIDATION_LINEAGE_RECOVERED_FULL_REPLAY_STILL_SOURCE_LIMITED` | FZKA 6404 + FZKA 7281 later UFOTRI validation/deployment evidence | Original benchmark hidden numerics / full atmospheric numerical equivalence |
| UFR-29 / original executable | `BLOCKED_SOURCE_UNAVAILABLE` | Proof source/test package existed; source member names/topology; proof documented exact test results existed | Original executable/source and actual golden output package |
| UFR-30 / loader and hidden defaults | `DOCUMENTED_LOADER_CONTRACT_SUBSTANTIALLY_RECOVERED_RESIDUAL_SOURCE_LIMITED` | NAMELIST interface, software variable names, many defaults, TEST JCL, I/O units, test deck, source-member topology | Original loader source and genuinely undocumented residual defaults/behavior |

## Search targets that were attempted but not recovered

The public-only pass did not recover copies of:

- `INR303.UFOTRI.FORT` or its members;
- `INR303.BEISPIEL.TRITDA1` ... `TRITDA5` expected/reference outputs;
- a UFOTRI executable or install image for version 93/4.x;
- the Savannah River UFOTRI Test Report / Comprehensive Technical Report / controlled package;
- full public copies of `CFFTP-G-88007` or `CFFTP-G-88027`;
- a closed authoritative Canada-1987 replay dataset containing all historical numerical inputs and measured/reference arrays.

Failure to locate these through public search is not proof that no public copy exists. It only defines the evidence boundary of this reassessment.

## Claim-boundary decision

This recovery materially improves the evidence base but does not change the top-level claims:

- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`
- `UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE=FALSE`
- `UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED`
- E4/E5 real CTEAS-Atmos work remains `DEFERRED_EXTERNAL_DEPENDENCY`.

No new internal replication stage is authorized. No existing production/default path is promoted. The immediate engineering stage remains `NO_IMMEDIATE_INTERNAL_REPLICATION_STAGE` until the external Atmos dependency is ready.
