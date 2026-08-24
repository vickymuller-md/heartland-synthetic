# Changelog

All notable changes to `heartland-synthetic` are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [SemVer](https://semver.org/).

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
