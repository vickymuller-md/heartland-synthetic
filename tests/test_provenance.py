"""Public provenance boundaries; these are not clinical validation tests."""

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd

from heartland_synthetic import HeartlandCohortConfig, generate_cohort, generate_time_series
from heartland_synthetic.registries import OUTCOME_RATES, ESSI_CLIP, ESSI_LIMITED_CUTOFF


ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "site/public/data/heartland-synthetic-cohort-1000-seed42.csv"


def test_frozen_benchmark_is_not_regenerated_or_relabelled():
    assert hashlib.sha256(CSV.read_bytes()).hexdigest() == "8fbce909272274129f94db2b80b179b493e64fbc382a88515a851089b2edda8e"
    with CSV.open(newline="") as handle:
        rows = list(csv.reader(handle))
    assert len(rows) == 1001
    assert len(rows[0]) == 31
    ledger = (ROOT / "docs/model_assumptions.md").read_text()
    assert "Dataset v1.0.0" in ledger
    assert "generator0.2.2" in ledger
    assert "1,000 rows/31 columns" in ledger


def test_model_parameters_remain_simulation_assumptions():
    assert ESSI_CLIP == (8, 40)
    assert ESSI_LIMITED_CUTOFF == 18
    assert OUTCOME_RATES == {
        "low": {"mortality_1yr": 0.06, "hospitalization_1yr": 0.18},
        "moderate": {"mortality_1yr": 0.15, "hospitalization_1yr": 0.35},
        "high": {"mortality_1yr": 0.32, "hospitalization_1yr": 0.55},
    }
    ledger = (ROOT / "docs/model_assumptions.md").read_text()
    assert "simulation assumptions" in ledger
    assert "circular" in ledger
    assert "not a PHI detector" in ledger
    assert "No questionnaire items" in ledger


def test_monthly_draws_do_not_consume_annual_flags():
    frame = generate_cohort(HeartlandCohortConfig(n_patients=20, seed=42))
    changed = frame.copy()
    changed["mortality_1yr"] = 1 - frame["mortality_1yr"]
    changed["hospitalization_1yr"] = 1 - frame["hospitalization_1yr"]
    pd.testing.assert_frame_equal(
        generate_time_series(frame, months=12, seed=42),
        generate_time_series(changed, months=12, seed=42),
    )


def test_disabled_medication_sampling_retains_placeholder_flags():
    frame = generate_cohort(HeartlandCohortConfig(n_patients=20, seed=42, include_medications=False))
    columns = ["on_acei_arb_arni", "on_beta_blocker", "on_mra", "on_sglt2i", "gdmt_classes_count"]
    assert (frame[columns] == 0).all().all()
    assert "placeholder zero flags" in (ROOT / "docs/model_assumptions.md").read_text()


def test_public_package_descriptions_do_not_claim_empirical_calibration_or_exclusivity():
    metadata = json.loads((ROOT / ".zenodo.json").read_text())
    text = metadata["description"]
    assert "simulation assumptions" in text
    assert "not an ESSI implementation" in text
    for path in ["README.md", "pyproject.toml", ".zenodo.json"]:
        content = (ROOT / path).read_text()
        for claim in ["clinically-realistic", "that Synthea does not model", "exact port", "never contains real patient data"]:
            assert claim not in content


def test_install_and_release_instructions_distinguish_candidate():
    readme = (ROOT / "README.md").read_text()
    assert "pip install heartland-synthetic==0.2.2" in readme
    assert "**0.3.0 candidate**" in readme
    assert "not the local candidate" in readme
    assert "git push --tags" not in readme
    assert "twine upload dist/*" not in readme
