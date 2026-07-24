# Dose parameter provenance

The dose module is labelled `research screening dose`.

## Dose coefficients

Source: UK Health Protection Agency, HPA-CRCE-004, *Generalised derived
constraints for radioisotopes of hydrogen, carbon, phosphorus, sulphur,
chromium, manganese, cobalt, zinc, selenium, technetium, antimony, thorium and
neptunium*, Tables 1 and 2. The tables state that the coefficients are based on
ICRP (1996/2001) age-dependent models.

| Model group | Source age | HTO ingestion/inhalation (Sv Bq-1) | OBT ingestion (Sv Bq-1) |
|---|---:|---:|---:|
| infant | 1 y | 4.8e-11 | 1.2e-10 |
| child | 10 y | 2.3e-11 | 5.7e-11 |
| adult | 20 y | 1.8e-11 | 4.2e-11 |

HTO is treated as fully absorbed vapour for inhalation. OBT is applied only to
ingestion. Skin absorption is reported separately using the manual Eq. (106)
factor of 0.5 relative to inhalation.

## Habits

Breathing, drinking-water, food, milk, and beef intake rates in
`configs/default_parameters.yaml` are replaceable `PROJECT_EXTENSION`
screening habits. They are not site survey values and are not part of the HPA
dose-coefficient tables.

## Use limitation

The module multiplies intake by committed effective dose per unit intake. It
does not model individual biokinetics, clinical dose, fetal dose, collective
dose, or regulatory compliance.

