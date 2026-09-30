# Model assumptions, provenance and limits

This ledger describes the local **0.3.0 candidate**. It separates implemented
simulation choices from evidence about real patients. No real patient,
personal, or health information should be supplied. The proposed HEARTLAND
framework remains pending validation against clinical outcomes.

## Three distinct version histories

| Artifact | Identity | What it establishes |
|-|-|-|
| Published Python package | 0.2.2 on PyPI, checked 2026-09-29 | A downloadable historical release, not the current candidate |
| Local Python candidate | 0.3.0 in source | Export and input-boundary changes under review, not a publication receipt |
| Preserved benchmark | Dataset v1.0.0, 1,000 rows/31 columns, generator0.2.2, seed42 | A fixed synthetic artifact; no new cohort or observed clinical outcomes |

The software concept DOI is `10.5281/zenodo.19635042`. The technical report has
its own concept DOI `10.5281/zenodo.22137199` and archived version1.0
`10.5281/zenodo.22137200`. Neither is a new DOI for this candidate or this CSV.
Historical records must not be described as documenting changes made later.

Frozen CSV: `site/public/data/heartland-synthetic-cohort-1000-seed42.csv`.
SHA-256: `8fbce909272274129f94db2b80b179b493e64fbc382a88515a851089b2edda8e`.
New generator development must not silently replace this file.

## Implemented model, not clinical calibration

The references named in `registries.py` are background literature. The source
does not supply parameter extraction tables, patient-level estimation data,
fitting code, calibration curves, or external clinical validation. Accordingly,
the numerical settings should be treated as **simulation assumptions**, not
study-derived estimates. Tests against those settings test implementation, not
whether the simulated population represents a clinical population.

| Domain | Actual source behavior | Interpretation boundary |
|-|-|-|
| Demographics | `demographics.py`: truncated age sampling; configured sex fraction; fixed race/ethnicity category probabilities; sampled rural/urban pools | Not population prevalence; a single legacy race/ethnicity variable cannot resolve both axes |
| Geography | `demographics.py`, `rural.py`: sampled RUCA-like codes and log-normal distances; county prefix is an alphabetical state-pool index | No Census county identification, NPPES lookup, route distance or Atlas join; synthetic codes can collide with real codes |
| Vitals | `clinical.py`: six-dimensional copula for LVEF/eGFR/BNP/SBP/HR/BMI; DBP is0.6×SBP plus noise | Correlations, clipping and subgroup shifts are chosen settings, not demonstrated clinical relationships; no NT-proBNP conversion |
| Comorbidities | `comorbid.py`: Bernoulli diabetes/AF; eGFR bins; a legacy CKM0–4 cascade using BMI/diabetes/renal bins and an age-based random transition | Not a chronic CKD diagnosis or adjudicated AHA CKM stage; the HF cohort's stage4 selection is a simulation convention |
| Social support | `rural.py`: one rounded normal draw, clipped8–40; mean24 rural/29 urban; legacy trigger<18 | No questionnaire items, ESSI instrument/version, psychometric validation or clinical-cutoff adjudication; ESSI_* identifiers survive for code compatibility only |
| Prior hospitalization | `generator.py`: Bernoulli0.20 | No historical admission records or feedback from assigned tier |
| GDMT | `gdmt.py`: independent class flags with different assumed rural/urban rates and a legacy eGFR simulation override | Not observed prescribing, a drug/dose, eligibility assessment, contraindication rule or delivered treatment; disabled sampling yields placeholder zero flags |
| Point score | `scoring.py`:10 weights,0–18 points, tiers0–4/5–8/9–18 | BNP-only numeric adapter; complete-criterion parity is not validity of the proxy or outcome prediction |
| Annual outcomes | `outcomes.py`: separate Bernoulli draws at fixed tier-indexed probabilities | Not fitted MAGGIC predictions, a Manemann hazard-ratio conversion, GWTG-HF estimates, or observed HEARTLAND outcomes |
| Monthly series | `timeseries.py`: AR(1) vitals; annual tier probabilities compounded monthly; rows stop after simulated death | Ignores the cohort's binary annual flags; event histories can disagree. Not longitudinal follow-up of observed people |

### Outcome assumptions, explicitly

| Tier | Annual mortality draw probability | Annual hospitalization draw probability |
|-|-|-|
| Low | 0.06 | 0.18 |
| Moderate | 0.15 | 0.35 |
| High | 0.32 | 0.55 |

These are fixed parameters, not empirical risk estimates. The tier selects the
probability, so testing the score against these generated outcomes is circular
and cannot validate discrimination, calibration, clinical utility or efficacy.
The monthly model uses `1 - (1 - annual_probability) ** (1 / 12)`; this is a
simulation transformation, not an estimated hazard model.

## Input checks do not authorize clinical use

Candidate0.3.0 scoring requires complete, structurally valid inputs. It rejects
missing/non-finite values, strings, temporal values, boolean measurements,
non-binary flags, invalid CKM categories and invalid totals. It neither imputes
missing values nor proves physiological plausibility or correct units. No new
physiologic range or ESSI requirement is inferred from these checks. Public
low-level predicates require already validated input.

The package can accept caller-supplied tables. It is **not a PHI detector or
de-identification system**; synthetic intent is not a technical guarantee that
external data are anonymous. This project authorizes synthetic demonstration
and testing only, not diagnosis, prognosis, treatment, or patient care.

## Export boundaries

`export_redcap` writes its own single-form dictionary/data pair. It is not a
direct importer for the separately versioned HEARTLAND Template. The historical
crosswalk has been replaced by explicit mapping limits: no ESSI/CKM/geography,
drug/dose or outcome-count conversion is inferred. Dictionary labels/notes
describe simulated proxies and flags. A shared field name is not proof of
matching encoding, clinical meaning, or successful institutional import.

FHIR output is a plain R4 collection Bundle. A score is a point count, not a
probability; the candidate expresses its tier qualitatively. No `meta.profile`
claim is emitted. JSON generation and local structural tests do not establish
full terminology/profile conformance, EHR acceptance, or a lossless exchange.
The candidate mapping withdraws inferred ICD diagnoses, drug-specific RxNorm
codes and formula-specific eGFR coding. Text-only simulated groups/class flags
do not establish clinical diagnoses or medication receipt. Ten explicit Boolean
criterion components use the existing BNP-only/legacy-proxy adapter; this is
not a clinical questionnaire. See [FHIR mapping](fhir_export_mapping.md) for
retained codes, exact internal references, source omissions and validation scope.

## Reproducibility and verification

Record the software commit/version, Python/NumPy/pandas/SciPy versions, seed and
configuration. Seeded cohort/time-series calls are repeatable in the same
runtime; cross-version byte identity is not promised. Internal samplers receive
a random-generator object, and FHIR resources use random UUIDs, so the statement
“every entry point accepts a seed” would be incorrect.

Keep the frozen CSV hash separate from freshly generated test data. Record
test counts with a dated receipt and exact source revision, not as a timeless
marketing statistic. A passing test, a repository commit, a built archive and
a public deployment are different evidence items. None establishes clinical
approval, regulatory status, HIPAA compliance, adoption, or patient outcomes.
