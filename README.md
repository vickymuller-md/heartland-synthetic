# heartland-synthetic

**Synthetic heart-failure cohorts with modeled rural access, social support,
and the ten proposed HEARTLAND risk criteria.**

[![CI](https://github.com/vickymuller-md/heartland-synthetic/actions/workflows/ci.yml/badge.svg)](https://github.com/vickymuller-md/heartland-synthetic/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/heartland-synthetic.svg)](https://pypi.org/project/heartland-synthetic/)
[![Dataset on Hugging Face](https://img.shields.io/badge/dataset-Hugging%20Face-FFD21E.svg)](https://huggingface.co/datasets/vickymuller-md/heartland-synthetic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

`heartland-synthetic` generates simulated HF cohorts, computes a proposed
HEARTLAND point score, and writes standalone REDCap and FHIR R4 collection
exports. It supports research workflow development, software tests and
educational demonstrations using synthetic data. It does not establish
clinical realism, predictive validity, patient outcomes, or institutional
interoperability. Do not supply real patient, personal, or health information.

**Release line: 0.3.1 (documentation maintenance).** Input checks and export
changes were released in [0.3.0](https://pypi.org/project/heartland-synthetic/0.3.0/),
archived at [10.5281/zenodo.23050640](https://doi.org/10.5281/zenodo.23050640).
Version 0.3.1 corrects release documentation; it does not change the generator,
scoring or exporters. The preserved benchmark remains dataset v1.0.0; its original
provenance cites the v0.2.1 software archive, not the later PyPI release.
It is not renamed or regenerated when the software changes.

## Why this exists

The package makes two modeled rural-HF domains explicit:

- **Distance to cardiology care** (rural barrier)
- **Social support** (a legacy synthetic numeric proxy, not an ESSI instrument)

Researchers can inspect the simulation assumptions and point weights used by
the HEARTLAND clinical implementation companion. This is not a benchmark
establishing superiority or exclusivity over other generators or risk models.

## Install

```bash
pip install heartland-synthetic==0.3.1
```

That command targets this release line. Verify availability and file hashes on
[the versioned registry page](https://pypi.org/project/heartland-synthetic/0.3.1/);
a source version or successful build alone is not a publication receipt.
For a reviewed source checkout, use an editable development install:

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
| `include_medications` | `True` | Sample GDMT flags; if False, retain columns as simulation zeros |
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
| `ckd_stage` | int | eGFR-derived 1-5 bin; not a clinical CKD diagnosis |
| `ckm_stage` | int | Legacy 0-4 simulation category; not adjudicated AHA CKM staging |
| `distance_to_cardiology_mi` | float | Miles |
| `social_support_score` | int | Legacy synthetic proxy, generated range 8-40; not an ESSI scale |
| `prior_hf_hosp_6mo` | int | 0/1 |
| `on_acei_arb_arni` / `on_beta_blocker` / `on_mra` / `on_sglt2i` | int | 0/1 |
| `gdmt_classes_count` | int | 0-4 |
| `heartland_risk_score` | int | 0-18 |
| `heartland_risk_tier` | str | `low` / `moderate` / `high` |
| `mortality_1yr`, `hospitalization_1yr` | int | 0/1 (only if `include_outcomes=True`) |

## Model assumptions and background literature

The named studies provide background context, not proof that the numerical
settings below were extracted from or fitted to those studies. No calibration
dataset, parameter-estimation procedure, or clinical validation is supplied.
See [the model-assumptions ledger](docs/model_assumptions.md) for the code
paths, limitations and separate version histories.

| Variable | Implemented model | Background context / evidence boundary |
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
| CKD stage | Deterministic eGFR bin | KDIGO terminology only; no chronicity/albuminuria assessment |
| CKM stage | Legacy cascade on diabetes, CKD bin, BMI, age | Not an implementation of clinical AHA staging |
| Distance to cardiology | Assumed LogNormal (rural vs urban) | No NPPES lookup, routing, or Atlas join |
| Social support | Normal (rural 24, urban 29), rounded and clipped to 8-40 | Legacy simulation assumption, not an ESSI implementation |
| GDMT rates | Assumed Bernoulli, rural vs urban | CHAMP-HF context; no fitted rates or assessed prescribing |
| 1-yr mortality per tier | Assumed 0.06 / 0.15 / 0.32 | Not MAGGIC predictions or Manemann hazard-ratio conversion |
| 1-yr hospitalization per tier | Assumed 0.18 / 0.35 / 0.55 | Not fitted GWTG-HF outcome estimates |

The principal settings live in `src/heartland_synthetic/registries.py`;
sampling modules also contain clipping, rounding and category rules. The
six-dimensional copula covers LVEF/eGFR/BNP/SBP/HR/BMI; DBP is generated
separately from SBP plus noise. Associations in generated data are properties
of these assumptions, not measured clinical relationships.

## Apply HEARTLAND scoring on a synthetic input table

```python
from heartland_synthetic import apply_heartland_scoring
import pandas as pd

df = pd.read_csv("synthetic_cohort.csv")  # complete synthetic inputs only
scored = apply_heartland_scoring(df)
```

Required columns: `age, prior_hf_hosp_6mo, egfr, bnp, sbp, diabetes, lvef,
ckm_stage, distance_to_cardiology_mi, social_support_score`.

The ten weights and tier boundaries follow
`heartland-app/lib/risk-score/engine.ts` (Protocol v3.3, Table 1): 18 points
maximum, tiers `low 0-4 / moderate 5-8 / high 9-18`. The numeric adapter uses
**BNP only**, not NT-proBNP. The existing `social_support_score < 18` criterion
is retained solely as a legacy simulation proxy. It does not establish
equivalence to an ESSI version, questionnaire, item score, or clinical cutoff.
Complete boolean-criterion agreement is not clinical validation.

Since 0.3.0, scoring rejects incomplete or structurally invalid input:

- All ten required fields must be present in every row. Missing columns raise
  `KeyError`; nulls, NaN, infinity, strings, and other unsupported values raise
  `ValueError`. There is no imputation, string parsing, or default-negative rule.
- Measurements accept finite Python/NumPy integers or floating-point scalars,
  but not booleans. `diabetes` and `prior_hf_hosp_6mo` accept explicit booleans or
  numeric values exactly equal to 0 or 1. `ckm_stage` must be integral in 0–4.
- `classify_tier` accepts integral numeric totals in 0–18, never booleans,
  fractional values, or missing values. Integral floating-point values are
  supported for pandas compatibility.
- Duplicate column labels are rejected. An empty table still needs all ten
  columns and returns typed, empty score/tier columns. Row order, index
  (including duplicate labels), and extra columns are retained. Missing values
  in unrelated extra columns do not prevent scoring.
- Existing score/tier columns are recomputed on a copy. One invalid row fails
  the whole call, without changing the input or returning a partially scored
  table. Errors identify a fixed field name, not input values or row identifiers.

These checks establish **structural completeness only**. They do not check
physiologic plausibility, reconcile units, validate the social-support
instrument, or authorize processing of real patient data. The generator's
8–40 proxy range is not imposed on external numeric inputs. Predicates exposed
through `RISK_VARIABLES` are low-level definitions for already validated input;
use `apply_heartland_scoring` or `compute_row_score` for input checking. The
HEARTLAND framework remains proposed pending validation against clinical
outcomes. Do not provide real patient, personal, or health information.

## Monthly time series

```python
from heartland_synthetic import generate_time_series

ts = generate_time_series(df, months=12, seed=42)
# one row per (patient_id, month); rows after the first death_event are omitted
```

Columns: `patient_id, month, sbp, dbp, hr, weight_kg, bnp, hosp_event,
death_event`. Vitals follow an AR(1) mean-reverting process around each
patient's baseline. Event probabilities are tier-indexed annual rates
compounded to monthly. The monthly simulation uses tier-indexed assumptions,
not the cohort's binary annual outcome flags; the two event histories can
disagree. Neither is an observed outcome or a validation target for the score.

## REDCap export

Since 0.3.0, exporters require the complete generated cohort schema, including
the ten score inputs. They reject extra/duplicate columns, invalid categories,
missing or lossy numeric values, unsafe/duplicate IDs and inconsistent score,
tier or GDMT count. Optional annual outcome columns must be supplied together.
All rows are validated and serialized before output; input tables are not changed.
See the [export input contract](docs/export_input_contract.md) for exact boundaries.
These checks are structural, not clinical validation or PHI detection.

Use a fresh output directory or prefix: existing targets (including symbolic
links) are refused, never overwritten. A later I/O failure can leave partial
new output; the whole export batch is not an atomic filesystem transaction.

```python
from heartland_synthetic import export_redcap
data_csv, dict_csv = export_redcap(df, "outputs/heartland_cohort")
```

Writes two files:

- `outputs/heartland_cohort.csv` — data with `record_id` (= `patient_id`)
- `outputs/heartland_cohort_datadict.csv` — 18-column REDCap data dictionary
  (radio for categoricals, dropdown for coded integers, yesno for booleans,
  text+number validation for continuous vitals).

**Standalone instrument.** `export_redcap()` writes a self-contained REDCap
project: one single-form instrument (`heartland_cohort`) whose data dictionary
is generated from the cohort columns. It follows the official 18-column REDCap
data dictionary layout, intended for evaluation in a **new, empty** REDCap
project. A generated CSV and local tests do not demonstrate a successful
institutional import or clinical deployment.

It is **not** an import file for the
[HEARTLAND REDCap Instrument Template](https://github.com/vickymuller-md/redcap-template),
which is a separately versioned instrument. This function is not a direct
Template importer and does not prove compatibility with its current candidate.

The review of the historical crosswalk for the earlier 75-field/5-form Template is in
[`docs/redcap_template_crosswalk.md`](docs/redcap_template_crosswalk.md).
It withdraws unsupported ESSI, staging, geography, medication and outcome-count
mappings. The standalone dictionary includes simulation labels/field notes;
it does not convert source values into clinically adjudicated measurements.
It is not a current conversion or institutional import receipt.

## FHIR R4 export

```python
from heartland_synthetic import export_fhir_bundle
paths = export_fhir_bundle(df, "outputs/fhir/")
# one Bundle per patient at outputs/fhir/{patient_id}.json
```

Each collection Bundle contains:

- `Patient` with the US Core 6.1 race and ethnicity extensions as two separate
  extensions. The cohort carries one 4-level variable that mixes race and
  ethnicity, so `Hispanic` is written to ethnicity (race `UNK`) and `Other`
  is written as `UNK` on both axes — neither axis is inferred from the other.
- Text-only `Condition` for the assigned HF simulation group and positive
  diabetes/AF flags; no inferred ICD diagnoses, CKD or diabetes subtype
- Quantity `Observation` for LVEF / BNP / SBP / DBP / HR / BMI (LOINC), with
  SBP/DBP as components of one blood-pressure panel and generic text-only eGFR
  because no estimation formula was actually calculated
- Text-only `Observation` for legacy eGFR/CKM bins, support proxy, modeled
  distance and prior-hospitalization flag, with their simulation limits
- Text-only `MedicationStatement` for positive simulated class flags, with
  status `unknown`; no specific drug, dose or actual receipt is inferred
- `Observation` for the HEARTLAND score total (0-18 points) under the custom
  CodeSystem
  `https://fhir.heartlandprotocol.org/CodeSystem/heartland-risk-score`, plus all
  ten Boolean criterion components (including false), explicitly labeled as
  simulated inputs/proxies rather than a verified clinical assessment
- `RiskAssessment` carrying the tier as a coded `prediction.qualitativeRisk`
  (`https://fhir.heartlandprotocol.org/CodeSystem/heartland-risk-tier`), with
  the score `Observation` as `basis`. `prediction.probabilityDecimal` is left
  empty: the total is a point count, not a likelihood.

`Address` carries `state` and `country` only. The synthetic county code travels
in an extension whose system URI marks it as synthetic; it is never written to
`Address.postalCode`. No resource declares `meta.profile`: the Bundles have not
been validated against US Core 6.1 or the HEARTLAND IG, so they assert no
profile conformance. Valid UUID entry URLs and exact internal references make
subjects/basis resolvable within each collection. Every resource is tagged as
synthetic research/testing data; the fixed reference date is not an actual
clinical event date. This is not a lossless cohort export or EHR import plan.
See [FHIR mapping and compatibility changes](docs/fhir_export_mapping.md),
including omitted source fields and withdrawn legacy codes.

## Reproducibility

The public generators accept a seed (`HeartlandCohortConfig.seed` and
`generate_time_series(..., seed=...)`). The same seed, configuration and runtime
produce repeatable DataFrames. This is not a promise of byte-identical results
across dependency/platform versions. FHIR resources use random UUIDs and are
not byte-deterministic exports. Record runtime versions alongside the seed.

```python
cfg = HeartlandCohortConfig(n_patients=100, seed=42)
assert generate_cohort(cfg).equals(generate_cohort(cfg))
```

## Limitations

- **Synthetic use only**: the bundled benchmark and generator outputs are
  synthetic. APIs can accept caller-supplied tables; the package does not
  detect PHI or anonymize those tables. Do not provide real patient data.
- **Assumed outcomes are not clinical evidence.** Tier-indexed event rates
  are fixed simulation settings. Validating the HEARTLAND score against events
  generated from that score's tiers would be circular, not independent
  validation. Do not estimate treatment benefit, population risk or efficacy.
- **County FIPS codes are synthetic and must not be decoded.** They are not
  ANSI/Census county GEOIDs: the 2-digit prefix is an alphabetical index over
  the state pool, not a real state FIPS, so a code can collide with the real
  FIPS of a different state and contradict the `state` column. The RUCA
  assignment and state pool are modeled but not geo-accurate.
- **CKM and CKD fields are legacy simulation categories**, not adjudicated
  clinical stages or diagnoses. Their limitations are documented in the ledger.
- **GDMT utilization is point-prevalence** at a single reference date; no
  titration trajectory is modeled.
- There is no NT-proBNP, ECG, echo structural anatomy or NYHA class. BMI is
  a modeled anthropometric measure, not a laboratory assay. Social support is
  a numeric proxy with no questionnaire items or validated ESSI implementation.
- No regulatory, HIPAA-compliance, de-identification, clinical-safety or
  patient-care authorization is established by this software or its tests.

## Benchmark dataset

The public 1,000-row, seed-42 benchmark cohort is available from the
[dataset landing page](https://synthetic.heartlandprotocol.org/dataset/) and
[Hugging Face](https://huggingface.co/datasets/vickymuller-md/heartland-synthetic).
Its original provenance cites the [v0.2.1 software archive](https://doi.org/10.5281/zenodo.19635043).
That archive retained internal version metadata of 0.2.0; neither that metadata
nor the later 0.2.2 packaging release proves the original execution environment.
The original Python/dependency receipt is unavailable, so byte-identical
regeneration is not promised. Download the preserved CSV and verify SHA-256
`8fbce909272274129f94db2b80b179b493e64fbc382a88515a851089b2edda8e`.
It contains no real patient data or protected health information.

## Citation

Software:

```bibtex
@software{mullerferreira_heartland_synthetic_2026,
  author = {Muller Ferreira, Vicky},
  title  = {heartland-synthetic: Synthetic heart-failure cohort generator with HEARTLAND risk variables},
  year   = {2026},
  publisher = {Zenodo},
  doi    = {10.5281/zenodo.19635042},
  url    = {https://doi.org/10.5281/zenodo.19635042}
}
```

Technical report:

```bibtex
@techreport{mullerferreira_heartland_synthetic_report_2026,
  author = {Muller Ferreira, Vicky},
  title  = {heartland-synthetic: A Reproducible Generator and Benchmark Dataset for Rural Heart-Failure Research Workflows},
  year   = {2026},
  institution = {Zenodo},
  doi    = {10.5281/zenodo.22137199},
  url    = {https://doi.org/10.5281/zenodo.22137199}
}
```

The report concept DOI resolves to all versions. Version 1.0 is archived at
[10.5281/zenodo.22137200](https://doi.org/10.5281/zenodo.22137200).

Cite alongside the HEARTLAND Protocol:
Muller Ferreira V. *HEARTLAND Protocol v3.3.* Zenodo. DOI 10.5281/zenodo.19101219.

## Software preservation

Software Heritage snapshot (archived 2026-08-25): [`swh:1:snp:53d48ef3e36293ebabf274cb8db4b35cb55a30d7`](https://archive.softwareheritage.org/swh:1:snp:53d48ef3e36293ebabf274cb8db4b35cb55a30d7/)

This persistent SWHID identifies the repository snapshot captured on that date; archival does not imply endorsement or validation.

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

Publication is separate from a local commit or build. Before an authorized
release, review the exact commit and version in `pyproject.toml`, `__init__.py`,
the changelog and site; run tests; verify the frozen CSV hash; build into a new
empty output directory; inspect both wheel and source archive for unintended
files; validate metadata and test an isolated installation of the built wheel.
The [distribution-verification guide](docs/release_verification.md) describes
the exact inventory checker, non-editable installed-package tests and release
gates. CI tests wheel and source installations across Python 3.10–3.12; a local
run only establishes the environments actually exercised in its receipt.

The repository's release workflow uses PyPI Trusted Publishing. Review its
tag/version and environment gates before creating a release, because a public
release can trigger external publication. Do not push all tags or upload an
unreviewed `dist/*` directory. Select the exact reviewed tag/artifacts only.
Verify the resulting PyPI files, GitHub release and Zenodo record separately;
do not assume a webhook completed. Update website publication labels only
after public readback. A software release does not replace the benchmark's
provenance or automatically update its technical report or dataset record.
