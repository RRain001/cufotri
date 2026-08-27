# V4 OBT evidence request messages R1

Status: `PREPARED_NOT_SENT`

These provider-specific messages implement the already-frozen request package. They do not change the requested scientific fields, observation operator, evidence acceptance rules, holdout policy or identifiability requirements. Presence in this repository is not evidence that a request was sent.

## Priority A — VATO / ASNR-EDF data-owner clarification

Subject: Request for sample-level VATO grass tritium data and analytical metadata

Dear VATO data owner/curator,

I am working on the CTEAS_UFOTRI research model and am assessing whether a future OBT model with precursor, exchangeable-OBT and non-exchangeable-OBT states can be supported by matched experimental evidence. I am contacting you because the VATO programme provides a uniquely relevant grassland time series.

Could you please clarify whether exchangeable OBT and non-exchangeable OBT were directly determined for compatible first-phase VATO grass samples, with sample-level values recoverable together with TFWT and forcing metadata? If not, I would be grateful to know which OBT quantity was directly measured.

Where available, I would like to request the original machine-readable sample-level TFWT and directly measured OBT fields, sample/cut and biological/field replicate identifiers, timestamps and sampling support, tissue and mass-basis information, analytical exchange/de-exchange/drying/combustion/counting protocols, uncertainty and detection/quantification limits, missing/quality flags, aligned atmospheric HTO and environmental forcing at their original available resolution, plus a data dictionary and version/correction history.

Please do not reconstruct missing E-OBT or NE-OBT components for this request. Partial original data are useful and will be recorded as partial rather than inferred. Please also indicate local research-use, publication of derived metrics, redistribution and required-citation conditions.

The files would first undergo metadata/schema and provenance review only. Receipt would not imply model validation, parameter activation or calibration, and original numeric files would not be placed in the public Git repository without explicit permission.

Thank you for considering the request.

## Priority B1 — MicroTom / Kyushu University

Subject: Request for sample-level tritium plant data from the MicroTom experiment

Dear Prof. Katayama and Dr. Portuphy,

I am working on the CTEAS_UFOTRI research model and am assessing whether a future OBT model with precursor, exchangeable-OBT and non-exchangeable-OBT states can be supported by matched experimental evidence. I am writing regarding the MicroTom plant-tritium work associated with SSRN 5059446 / DOI 10.2139/ssrn.5059446.

If available, could you share the original machine-readable sample-level TFWT, exchangeable OBT and non-exchangeable OBT measurements from the controlled experiment, together with any separately assayed total OBT and the sample/aliquot relationship between these measurements? I would also be grateful for cultivar/plant/tissue and developmental-stage identifiers, exposure/source boundary conditions and timing, light/PAR or photosynthetic-activity records or proxies, temperature/humidity records, timestamps and sampling support, biological replicate/run identifiers, analytical methods, uncertainty and detection/quantification limits, quality flags, mass/area/water basis information, and the data dictionary/version metadata.

Please do not recreate fields that were not recorded. Partial original exports are useful and will remain explicitly partial. I would also appreciate the applicable local research-use, publication of derived metrics, redistribution and citation conditions.

The first use of any files would be limited to checksum, metadata/schema and scientific-suitability review. Receipt would not imply model validation, parameter activation or calibration, and original quantitative files would remain outside the public Git repository unless redistribution is explicitly permitted.

Thank you for considering the request.

## Priority B2 — Renard ryegrass experiment

Subject: Request for sample-level ryegrass TFWT/OBT component data from Renard et al. (2017)

Dear data owner/curator,

I am working on the CTEAS_UFOTRI research model and am assessing whether a future OBT component model can be supported by matched experimental evidence. I am writing regarding Renard et al. (2017), DOI 10.1016/j.jenvrad.2017.06.026.

If available, could you share the original machine-readable sample-level TFWT and OBT observations, including the original exchangeable-fraction/component measurements? Where total, exchangeable and non-exchangeable fields exist, I would like the original fields and documented analytical relationship rather than a newly reconstructed missing component. I would also appreciate organ/tissue and plant-age identifiers, dehydrated biomass and measured water/mass quantities used for basis conversion, hydroponic HTO exposure history and chamber/environmental conditions, timestamps and sampling support, biological replicate/run identifiers, analytical methods, uncertainty/detection limits, quality flags, data dictionary/version information and provenance.

Please do not recreate unavailable fields. Partial original data are useful and will remain explicitly partial. Please also state local research-use, publication of derived metrics, redistribution and required-citation conditions.

The first use of any received files would be limited to checksum and metadata/schema review. Receipt would not imply validation or authorize parameter fitting, and raw quantitative files would not be committed to the public Git repository without explicit permission.

Thank you for considering the request.

## Execution record requirement

A message becomes `REQUEST_SENT_AWAITING_RESPONSE` only after the execution registry records the exact recipient route, channel, message revision and UTC send timestamp. Until then all messages in this file remain `PREPARED_NOT_SENT`.
