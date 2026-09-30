"""Standalone dictionary meaning and encoding, not an institutional import test."""

import csv
from pathlib import Path

import pandas as pd
import pytest

from heartland_synthetic import HeartlandCohortConfig, generate_cohort, export_redcap
from heartland_synthetic.registries import REDCAP_CATEGORICALS, REDCAP_DROPDOWNS, REDCAP_BOOLEAN_COLUMNS


@pytest.mark.parametrize("outcomes,medications", [(False, False), (False, True), (True, False), (True, True)])
def test_dictionary_and_data_keep_exact_schema_and_choice_codes(outcomes, medications, tmp_path):
    frame = generate_cohort(HeartlandCohortConfig(n_patients=50, seed=42, include_outcomes=outcomes, include_medications=medications))
    original = frame.copy(deep=True)
    data_path, dd_path = export_redcap(frame, tmp_path / "cohort")
    with data_path.open(newline="") as handle:
        data = list(csv.DictReader(handle))
    with dd_path.open(newline="") as handle:
        dictionary = list(csv.DictReader(handle))
    fields = [row["Variable / Field Name"] for row in dictionary]
    assert len(fields) == len(set(fields)) == (31 if outcomes else 29)
    assert fields == ["record_id", *list(frame.columns)[1:]]
    assert list(data[0]) == fields
    assert dictionary[0]["Section Header"] == "Synthetic research/testing only; not clinical observations"
    assert all(row["Field Note"] for row in dictionary)
    assert all(not row["Text Validation Min"] and not row["Text Validation Max"] for row in dictionary)
    for entry in dictionary:
        field = entry["Variable / Field Name"]
        if field in REDCAP_CATEGORICALS or field in REDCAP_DROPDOWNS:
            choices = {item.split(",", 1)[0].strip() for item in entry["Choices, Calculations, OR Slider Labels"].split(" | ")}
            assert {row[field] for row in data} <= choices
        if field in REDCAP_BOOLEAN_COLUMNS:
            assert {row[field] for row in data} <= {"0", "1"}
    for source, exported in zip(frame.to_dict("records"), data):
        for field, value in source.items():
            encoded = exported["record_id" if field == "patient_id" else field]
            assert (encoded == value if isinstance(value, str) else float(encoded) == value)
    pd.testing.assert_frame_equal(frame, original)


def test_labels_and_notes_do_not_promote_proxies_to_clinical_measurements(tmp_path):
    frame = generate_cohort(HeartlandCohortConfig(n_patients=2, seed=42))
    _, path = export_redcap(frame, tmp_path / "cohort")
    with path.open(newline="") as handle:
        fields = {row["Variable / Field Name"]: row for row in csv.DictReader(handle)}
    labels = {key: value["Field Label"] for key, value in fields.items()}
    assert "not an ESSI" in labels["social_support_score"]
    assert "not a CKD diagnosis" in labels["ckd_stage"]
    assert "not adjudicated" in labels["ckm_stage"]
    assert "not a real FIPS" in labels["county_fips"]
    assert "RUCA-like" in labels["rural_urban_code"]
    assert "not an exact admission count" in fields["hospitalization_1yr"]["Field Note"]
    for field in ("on_acei_arb_arni", "on_beta_blocker", "on_mra", "on_sglt2i"):
        assert "placeholder" in fields[field]["Field Note"]
    assert "proposed" in labels["heartland_risk_score"].lower()


def test_crosswalk_withdraws_unsupported_conversions():
    text = (Path(__file__).resolve().parents[1] / "docs/redcap_template_crosswalk.md").read_text()
    for phrase in ["not an approved", "No validated mapping", "No automatic count conversion", "no current target-field coverage count", "No direct-import adapter"]:
        assert phrase.lower() in text.lower()
    for former in ["published ENRICHD/ESSI scale 8–40", "Such an import would load", "write `0` (None) when"]:
        assert former not in text
