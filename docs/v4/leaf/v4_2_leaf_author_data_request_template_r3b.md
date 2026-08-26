# V4-2 R3B author-held raw-data request template

This template is a governance artifact. It has **not** been sent to any author.
Use it only after the exact corresponding author/contact channel has been
verified from the article or institutional source.

## Subject

Request for original LI-6800/LI-680X gas-exchange export for a published soybean experiment

## Request body

Dear Dr. [corresponding author],

I am conducting a research-method validation study on dynamic soybean stomatal
response and am reviewing the raw gas-exchange evidence underlying your paper:

**[article title]**  
DOI: **[article DOI]**

I am specifically interested in the original LI-6800/LI-680X export associated
with **[exact experiment / figure / run description]**. I am not asking for new
analysis, reconstructed values, fitted coefficients, or additional experiments.
If the original instrument export is still available, would you be willing to
share the existing raw file(s), or an unchanged copy of the relevant run(s)?

The fields most useful for reproducibility are, when present in the original
export:

- stomatal conductance to water vapor (`gsw`) or the corresponding resistance;
- leaf VPD (`VPDleaf` / `VpdL`) or the original humidity variables needed to derive it;
- leaf temperature (`Tleaf`);
- incident PAR/PPFD (`PAR`, `Q`, or equivalent);
- chamber/sample and reference H2O mole fractions, if available;
- chamber pressure;
- elapsed time or timestamp;
- plant, leaf, run, or biological-replicate identifier;
- treatment/event markers;
- developmental-stage information associated with the measured plants.

A partial raw export is still useful; missing fields do not need to be recreated
or inferred. If the instrument header is abbreviated, a variable dictionary,
export note, or software/export version would also be helpful if already available.

The raw file would be retained unchanged for integrity checking, with file size
and cryptographic hash recorded before any analysis. It would not be committed
to the public project repository without separate permission. Any conclusions
about model suitability would remain subject to an independent evidence review;
receiving the data would not by itself be treated as model validation.

Thank you for considering the request.

Sincerely,
[requester identity / affiliation]

## Source-specific anchors

### Mostofa et al. 2025

- Article DOI: `10.1073/pnas.2502360122`
- Public dataset DOI: `10.5061/dryad.51c59zwkh`
- Exact experiment anchor: soybean wound-response measurement corresponding to
  public workbook **Fig 3d**.
- R3A fact to mention only if useful: the public workbook contains 150 absolute
  `gsw` observations at 5-second cadence, but the row-aligned LI-COR driver
  fields are not included in that workbook.

Preferred request wording for the experiment anchor:

> the original LI-6800/LI-680X export for the soybean wound-response gas-exchange
> run used for Fig. 3d, including the same records from which the public 5-second
> `gsw` series was prepared

### Zandalinas et al. 2020

- Article DOI: `10.1104/pp.20.00511`
- Exact experiment anchor: simultaneous upper/lower soybean-leaf measurements
  performed with two LI-6800 systems during the reported light-step systemic
  stomatal-response experiment.

Preferred request wording for the experiment anchor:

> the original exports from both LI-6800 systems for the paired upper/lower-leaf
> runs used in the systemic stomatal-response light-step experiment, together
> with any existing run-pairing or synchronization notes

## Prohibited request behavior

Do not ask an author to:

- invent or reconstruct missing timestamps, plant IDs, stage labels, or humidity values;
- provide pre-fitted stomatal-response coefficients as a substitute for raw records;
- merge different experiments for this project;
- manually populate missing VPD from a reported humidity range;
- alter original files to match the V4-2 schema.

If the author can only provide a partial file, preserve and classify it as such.
