# Changelog

All notable changes to `heartland-synthetic` are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [SemVer](https://semver.org/).

## [0.3.0] - 2026-09-17

### Changed
- `export_fhir_bundle`: `Patient.address` no longer writes the synthetic
  county code to `postalCode`. The code is carried in an `Address` extension
  (`https://fhir.heartlandprotocol.org/StructureDefinition/heartland-synthetic-county-code`)
  whose system URI marks it as synthetic. `Address.district` stays absent —
  no county name is generated.
- `export_fhir_bundle`: race and ethnicity are emitted as the two separate
  US Core 6.1 extensions, with `ombCategory` restricted to the required value
  sets. `Hispanic` maps to ethnicity `2135-2` with race `UNK`; `Other` maps to
  `UNK` on both axes instead of the out-of-value-set `2131-1`. Both extensions
  carry the mandatory `text` element. Previously a single race extension
  carried `2135-2` / `2131-1` and no ethnicity extension was emitted.
- `export_fhir_bundle`: HEARTLAND canonicals moved from
  `http://heartlandprotocol.org/fhir/CodeSystem/risk-score` to the IG canonical
  base, `https://fhir.heartlandprotocol.org/CodeSystem/heartland-risk-score`.
- `export_fhir_bundle`: the score `Observation` tier component is now a coded
  `valueCodeableConcept` from
  `https://fhir.heartlandprotocol.org/CodeSystem/heartland-risk-tier` instead
  of a free `valueString`.
- README and the site feature card no longer describe the REDCap export as
  "ready to import": it writes its own single-form instrument, not an import
  file for the HEARTLAND REDCap Instrument Template.

### Added
- `export_fhir_bundle`: a `RiskAssessment` per patient carrying the tier as
  `prediction.qualitativeRisk`, with the score `Observation` as `basis`.
  `prediction.probabilityDecimal` is deliberately left empty — the 0-18
  HEARTLAND total is a point count, not a likelihood. No resource declares
  `meta.profile`; the Bundles have not been validated against US Core 6.1 or
  the HEARTLAND IG.
- `docs/redcap_template_crosswalk.md` — field-level crosswalk between the
  cohort columns and the 75-field HEARTLAND REDCap Instrument Template, with
  missingness rules and the resulting coverage.
- 16 exporter tests: postalCode/district absence, synthetic county system,
  race/ethnicity value-set membership and `text` cardinality, per-level race
  mapping, unknown-level degradation to `UNK`, RiskAssessment shape, absence
  of `probabilityDecimal` and of `meta.profile`, HEARTLAND canonical prefix,
  and a static guard on the REDCap field-name boundary.

### Unchanged
- The generator is untouched: no column was added, renamed or recalibrated,
  and no seed changed. The public 1,000-row, seed-42 benchmark cohort and its
  published CSV are byte-identical; only the shape of the FHIR export changed.

## [0.2.2] - 2026-08-24

### Fixed
- Corrected package metadata for the first PyPI publication. The earlier
  GitHub/Zenodo `v0.2.1` bootstrap release retained `0.2.0` in
  `pyproject.toml` and `heartland_synthetic.__version__`.
- Replaced the pending citation placeholder with the canonical Zenodo concept
  DOI and added persistent project links to the package metadata.
- Pinned Hatchling 1.27.0 so release artifacts use Core Metadata 2.4 and pass
  the current Twine metadata validator.

### Added
- Tokenless PyPI release workflow using GitHub Actions Trusted Publishing,
  separate build and publish jobs, metadata validation, and attestations.

## [0.2.0] - 2026-04-16

### Added
- `sample_outcomes` and `include_outcomes` support in `generate_cohort`.
  Produces `mortality_1yr` and `hospitalization_1yr` by HEARTLAND tier
  (MAGGIC + Manemann 2018 + GWTG-HF).
- `generate_time_series(cohort, months, seed)` — long-format AR(1) monthly
  vitals + hospitalization/death events. Rows after a patient's first
  `death_event=1` are omitted.
- `export_redcap(df, out_prefix)` — writes REDCap data CSV + 18-column
  data dictionary (radio / dropdown / yesno / text-number).
- `export_fhir_bundle(df, out_dir)` — writes one FHIR R4 collection Bundle
  per patient (Patient, Condition, Observation, MedicationStatement,
  HEARTLAND score Observation).
- Full README with clinical documentation, distribution source table,
  examples for every public function, and publish runbook.
- MIT LICENSE, `.zenodo.json`, CHANGELOG.

### Changed
- Package version 0.1.0 -> 0.2.0.
- `pyproject.toml`: added `publish` optional-dependency group
  (`build`, `twine`).

## [0.1.0] - 2026-04-16

### Added
- Package scaffolding (src layout, hatchling build backend).
- `HeartlandCohortConfig` with validation.
- Core generator pipeline: demographics -> Gaussian-copula vitals ->
  comorbidities -> rural variables -> GDMT utilization.
- HEARTLAND scoring engine (1:1 port of `heartland-app/lib/risk-score/engine.ts`).
- `apply_heartland_scoring(df)` for external data.
- Pytest suite (42 tests): scoring, reproducibility, distributions, rural,
  GDMT.
