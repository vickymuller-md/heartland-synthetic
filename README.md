# heartland-synthetic

**Synthetic heart-failure cohort generator with the 10 HEARTLAND risk variables
— distance-to-cardiology and social support — that Synthea and other generators
do not model.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

`heartland-synthetic` is a Python package that generates clinically-realistic
synthetic HF patient cohorts, computes the HEARTLAND Risk Score for each row,
and exports to REDCap and FHIR R4. It supports reproducible simulation studies
for the HEARTLAND Protocol and lets other researchers prototype validation
work without needing real patient data.

## Why this exists

Synthea and other synthetic-patient generators do not model the two variables
that distinguish HEARTLAND from MAGGIC / GWTG-HF / SHFM:

- **Distance to cardiology care** (rural barrier)
- **Social support** (ENRICHD ESSI scale)

Researchers working on rural HF risk stratification have had to simulate these
manually. `heartland-synthetic` fills the gap, ships with the exact scoring
engine used in the clinical-decision-support prototype, and is publishable as a
citeable artifact under MIT + Zenodo DOI.

## Install

```bash
pip install heartland-synthetic
```

Editable install for development:

```bash
git clone https://github.com/vickymuller-md/heartland-synthetic
cd heartland-synthetic
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

Python >= 3.10; core deps: `numpy`, `pandas`, `scipy`.

## Quickstart

```python
from heartland_synthetic import generate_cohort, HeartlandCohortConfig

config = HeartlandCohortConfig(
    n_patients=500,
    rural_fraction=0.7,
    hf_type_distribution={"hfref": 0.45, "hfmref": 0.15, "hfpef": 0.40},
    age_range=(45, 95),
    include_outcomes=True,
    seed=42,
)
df = generate_cohort(config)
print(df["heartland_risk_tier"].value_counts())
```

The returned DataFrame has one row per patient; every patient comes with the
HEARTLAND score and tier already computed.

## `HeartlandCohortConfig`

| Field | Default | Description |
|-|-|-|
| `n_patients` | `500` | Cohort size (must be > 0) |
| `rural_fraction` | `0.5` | Share of patients with USDA RUCA >= 4 |
| `hf_type_distribution` | `{hfref: .45, hfmref: .15, hfpef: .40}` | HF subtype mix (must sum to 1.0) |
| `age_range` | `(45, 95)` | Inclusive age bounds (min >= 18) |
| `female_fraction` | `0.48` | Share of female patients |
| `include_outcomes` | `True` | Attach `mortality_1yr` / `hospitalization_1yr` |
| `include_medications` | `True` | Attach GDMT utilization columns |
| `seed` | `None` | Integer seed; `None` yields OS-entropy randomness |

## Output schema

| Column | Type | Notes |
|-|-|-|
| `patient_id` | str | `HS-000001`-style identifier |
| `age` | int | Years |
| `sex` | str | `F` / `M` |
| `race` | str | White / Black / Hispanic / Other |
| `state` | str | US postal abbreviation |
| `county_fips` | str | Synthetic 5-digit code |
| `rural_urban_code` | int | USDA RUCA 1-10 |
| `hf_type` | str | `hfref` / `hfmref` / `hfpef` |
| `lvef` | float | % (by stratum) |
| `egfr` | float | mL/min/1.73 m^2 |
| `bnp` | float | pg/mL |
| `sbp`, `dbp`, `hr` | int | mmHg / mmHg / bpm |
| `bmi` | float | kg/m^2 |
| `diabetes`, `af` | int | 0/1 |
| `ckd_stage` | int | 1-5 (KDIGO) |
| `ckm_stage` | int | 0-4 (AHA 2023) |
| `distance_to_cardiology_mi` | float | Miles |
| `social_support_score` | int | ENRICHD ESSI 8-40 |
| `prior_hf_hosp_6mo` | int | 0/1 |
| `on_acei_arb_arni` / `on_beta_blocker` / `on_mra` / `on_sglt2i` | int | 0/1 |
| `gdmt_classes_count` | int | 0-4 |
| `heartland_risk_score` | int | 0-18 |
| `heartland_risk_tier` | str | `low` / `moderate` / `high` |
| `mortality_1yr`, `hospitalization_1yr` | int | 0/1 (only if `include_outcomes=True`) |

## Distribution sources

| Variable | Model | Source |
|-|-|-|
| Age | Truncated Normal(72, 12) | GWTG-HF |
| Sex | Bernoulli | GWTG-HF |
| Race | Categorical | GWTG-HF / NHANES |
| LVEF (HFrEF / HFmrEF / HFpEF) | Strata-specific | PARADIGM-HF / DELIVER / EMPEROR-Preserved |
| eGFR | LogNormal(ln 60, 0.35), elderly shift | STRONG-HF / CKD-EPI |
| BNP | LogNormal(ln 600, 0.9); HFpEF -30% | PARADIGM-HF |
| SBP | Normal(125, 20); rural +5 mmHg | GWTG-HF |
| DBP | `0.6 * SBP + N(0, 14)` (rho ~ 0.65) | Derived |
| HR | Normal(78, 14) | GWTG-HF |
| BMI | Normal(30, 6); HFpEF +3 | DELIVER |
| Diabetes | Bernoulli(0.42 + HFpEF/obesity bumps) | GWTG-HF |
| AF | Bernoulli(0.35 + elderly bump) | GWTG-HF |
| CKD stage | Deterministic from eGFR | KDIGO 2012 |
| CKM stage | Cascade on diabetes, CKD, BMI, age | AHA 2023 Presidential Advisory |
| Distance to cardiology | LogNormal (rural vs urban) | NPPES NPI / Atlas |
| Social support | Normal (rural 24, urban 29) | ENRICHD ESSI |
| GDMT rates | Bernoulli, rural vs urban | CHAMP-HF |
| 1-yr mortality per tier | 0.06 / 0.15 / 0.32 | MAGGIC + Manemann 2018 |
| 1-yr hospitalization per tier | 0.18 / 0.35 / 0.55 | GWTG-HF readmission |

All numeric constants live in `src/heartland_synthetic/registries.py` with
inline citations.

## Apply HEARTLAND scoring on external data

```python
from heartland_synthetic import apply_heartland_scoring
import pandas as pd

df = pd.read_csv("external_cohort.csv")   # must have required columns
scored = apply_heartland_scoring(df)
```

Required columns: `age, prior_hf_hosp_6mo, egfr, bnp, sbp, diabetes, lvef,
ckm_stage, distance_to_cardiology_mi, social_support_score`.

The scoring logic is a direct port of `heartland-app/lib/risk-score/engine.ts`
(Protocol v3.3, Table 1): 10 variables, 18 points maximum, tiers
`low 0-4 / moderate 5-8 / high >= 9`.

## Monthly time series

```python
from heartland_synthetic import generate_time_series

ts = generate_time_series(df, months=12, seed=42)
# one row per (patient_id, month); rows after the first death_event are omitted
```

Columns: `patient_id, month, sbp, dbp, hr, weight_kg, bnp, hosp_event,
death_event`. Vitals follow an AR(1) mean-reverting process around each
patient's baseline. Event probabilities are tier-indexed annual rates
compounded to monthly.

## REDCap export

```python
from heartland_synthetic import export_redcap
data_csv, dict_csv = export_redcap(df, "outputs/heartland_cohort")
```

Writes two files:

- `outputs/heartland_cohort.csv` — data with `record_id` (= `patient_id`)
- `outputs/heartland_cohort_datadict.csv` — 18-column REDCap data dictionary
  (radio for categoricals, dropdown for coded integers, yesno for booleans,
  text+number validation for continuous vitals).

Import into a fresh REDCap project: *Project Setup -> Upload Data Dictionary*
then *Import Data*.

## FHIR R4 export

```python
from heartland_synthetic import export_fhir_bundle
paths = export_fhir_bundle(df, "outputs/fhir/")
# one Bundle per patient at outputs/fhir/{patient_id}.json
```

Each collection Bundle contains:

- `Patient` (with US Core Race extension)
- `Condition` for HF subtype (ICD-10 I50.2 / I50.3 / I50.4), plus
  diabetes / CKD stage / AF / prior HF hospitalization when present
- `Observation` for LVEF / eGFR / BNP / SBP / DBP / HR / BMI (LOINC)
- `MedicationStatement` for each GDMT class the patient is on (RxNorm)
- `Observation` for the HEARTLAND score and tier under the custom CodeSystem
  `http://heartlandprotocol.org/fhir/CodeSystem/risk-score`

## Reproducibility

Every function that draws random numbers accepts a `seed` parameter. With the
same seed, `generate_cohort` and `generate_time_series` return DataFrames that
`pandas.testing.assert_frame_equal` on.

```python
cfg = HeartlandCohortConfig(n_patients=100, seed=42)
assert generate_cohort(cfg).equals(generate_cohort(cfg))
```

## Limitations

- **Synthetic only**: this package never contains real patient data. It is not
  a substitute for real registry or EHR analysis.
- **Outcome rates are consistent with, not validated against, literature.**
  The 1-year mortality and hospitalization rates per tier are modeled from
  MAGGIC survival curves + Manemann 2018 social isolation HR + GWTG-HF
  readmission patterns. No prospective HEARTLAND-scored cohort has been
  outcome-validated yet.
- **County FIPS codes are synthetic** (not mapped to real counties); the RUCA
  assignment and state pool are modeled but not geo-accurate.
- **CKM staging is simplified** from the AHA 2023 Presidential Advisory
  (stages 0-4 via diabetes / CKD / BMI / age); the full 5-stage model with
  subclinical CVD biomarkers is not yet implemented.
- **GDMT utilization is point-prevalence** at a single reference date; no
  titration trajectory is modeled.
- Only the 10 HEARTLAND variables plus supporting clinical context are
  generated — no labs beyond BNP, eGFR, and BMI; no ECG, echo structural
  parameters, or NYHA class.

## Citation

```bibtex
@software{mullerferreira_heartland_synthetic_2026,
  author = {Muller Ferreira, Vicky},
  title  = {heartland-synthetic: Synthetic heart-failure cohort generator with HEARTLAND risk variables},
  year   = {2026},
  publisher = {Zenodo},
  doi    = {10.5281/zenodo.PENDING},
  url    = {https://github.com/vickymuller-md/heartland-synthetic}
}
```

Cite alongside the HEARTLAND Protocol:
Muller Ferreira V. *HEARTLAND Protocol v3.3.* Zenodo. DOI 10.5281/zenodo.18566403.

## License

MIT. See [LICENSE](LICENSE).

## Landing page

A Next.js static landing page that mirrors the HEARTLAND design system
lives in [`site/`](site/). It's deployed (by the maintainer) at
[synthetic.heartlandprotocol.org](https://synthetic.heartlandprotocol.org).

```bash
cd site
npm install
npm run dev          # http://localhost:3000
npm run build        # static export -> site/out/
```

Deploy on Vercel with Root Directory = `site`. Add the custom domain
`synthetic.heartlandprotocol.org`; Vercel issues the CNAME target and
manages TLS.

## Publish runbook

For the maintainer releasing a new version:

```bash
# 1. Bump version in pyproject.toml and src/heartland_synthetic/__init__.py
# 2. Update CHANGELOG.md with a new [x.y.z] section
# 3. Run the full test suite
.venv/bin/pytest -q

# 4. Build sdist + wheel
.venv/bin/pip install -e ".[publish]"
.venv/bin/python -m build
ls dist/

# 5. Authenticate gh as vickymuller-md (important: not rodrigoeac)
gh auth switch

# 6. Tag and push
git tag vX.Y.Z
git push --tags

# 7. Create the GitHub release from the tag
# (Zenodo webhook mints the DOI automatically when the release is published)
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file CHANGELOG.md

# 8. Upload to PyPI (requires PYPI_API_TOKEN)
.venv/bin/twine upload dist/*
```
