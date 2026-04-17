"""REDCap + FHIR R4 exporter tests."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from heartland_synthetic import (
    HeartlandCohortConfig,
    export_fhir_bundle,
    export_redcap,
    generate_cohort,
)


@pytest.fixture(scope="module")
def cohort_for_exports() -> pd.DataFrame:
    cfg = HeartlandCohortConfig(n_patients=25, include_outcomes=True, seed=91)
    return generate_cohort(cfg)


# ---------------------------------------------------------------------------
# REDCap
# ---------------------------------------------------------------------------
def test_redcap_writes_two_files(tmp_path, cohort_for_exports):
    data, dd = export_redcap(cohort_for_exports, tmp_path / "cohort")
    assert data.exists() and dd.exists()
    assert data.suffix == ".csv"
    assert dd.name.endswith("_datadict.csv")


def test_redcap_data_has_record_id(tmp_path, cohort_for_exports):
    data, _ = export_redcap(cohort_for_exports, tmp_path / "cohort")
    df = pd.read_csv(data)
    assert "record_id" in df.columns
    assert "patient_id" not in df.columns
    assert len(df) == len(cohort_for_exports)


def test_redcap_datadict_structure(tmp_path, cohort_for_exports):
    _, dd = export_redcap(cohort_for_exports, tmp_path / "cohort")
    dict_df = pd.read_csv(dd)
    # One row per data column
    assert len(dict_df) == len(cohort_for_exports.columns)
    assert "Variable / Field Name" in dict_df.columns
    assert "Field Type" in dict_df.columns

    # Sanity: sex/race/hf_type/tier are radios with non-empty choices
    for cat_col in ("sex", "race", "hf_type", "heartland_risk_tier"):
        row = dict_df[dict_df["Variable / Field Name"] == cat_col].iloc[0]
        assert row["Field Type"] == "radio"
        assert "|" in str(row["Choices, Calculations, OR Slider Labels"])

    # rural_urban_code / ckd_stage / ckm_stage are dropdowns
    for dd_col in ("rural_urban_code", "ckd_stage", "ckm_stage"):
        row = dict_df[dict_df["Variable / Field Name"] == dd_col].iloc[0]
        assert row["Field Type"] == "dropdown"

    # diabetes / af / on_* are yesno
    for bool_col in ("diabetes", "af", "on_acei_arb_arni"):
        row = dict_df[dict_df["Variable / Field Name"] == bool_col].iloc[0]
        assert row["Field Type"] == "yesno"


def test_redcap_roundtrip_preserves_rows(tmp_path, cohort_for_exports):
    data, _ = export_redcap(cohort_for_exports, tmp_path / "cohort")
    reloaded = pd.read_csv(data)
    assert len(reloaded) == len(cohort_for_exports)
    # All HEARTLAND score values preserved
    assert set(reloaded["heartland_risk_score"]) == set(
        cohort_for_exports["heartland_risk_score"]
    )


# ---------------------------------------------------------------------------
# FHIR
# ---------------------------------------------------------------------------
def test_fhir_one_file_per_patient(tmp_path, cohort_for_exports):
    out = tmp_path / "fhir"
    paths = export_fhir_bundle(cohort_for_exports, out)
    assert len(paths) == len(cohort_for_exports)
    assert all(p.exists() for p in paths)
    assert len(list(out.glob("*.json"))) == len(cohort_for_exports)


def test_fhir_bundle_structure(tmp_path, cohort_for_exports):
    paths = export_fhir_bundle(cohort_for_exports, tmp_path / "fhir")
    bundle = json.loads(paths[0].read_text())
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert "entry" in bundle

    types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "Patient" in types
    # 7 vital-sign / lab Observations + 1 HEARTLAND score Observation.
    assert types.count("Observation") >= 8
    assert types.count("Condition") >= 1  # HF type always present


def test_fhir_patient_id_matches_filename(tmp_path, cohort_for_exports):
    paths = export_fhir_bundle(cohort_for_exports, tmp_path / "fhir")
    for p in paths:
        bundle = json.loads(p.read_text())
        patient = next(
            e["resource"] for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Patient"
        )
        assert patient["id"] == p.stem


def test_fhir_observations_use_loinc(tmp_path, cohort_for_exports):
    paths = export_fhir_bundle(cohort_for_exports, tmp_path / "fhir")
    bundle = json.loads(paths[0].read_text())
    for entry in bundle["entry"]:
        res = entry["resource"]
        if res["resourceType"] != "Observation":
            continue
        system = res["code"]["coding"][0]["system"]
        # LOINC vitals/labs, or the custom HEARTLAND system for the score.
        assert system in ("http://loinc.org",
                          "http://heartlandprotocol.org/fhir/CodeSystem/risk-score")


def test_fhir_medstatements_match_source_row(tmp_path, cohort_for_exports):
    paths = export_fhir_bundle(cohort_for_exports, tmp_path / "fhir")
    for p in paths:
        pid = p.stem
        row = cohort_for_exports[cohort_for_exports["patient_id"] == pid].iloc[0]
        bundle = json.loads(p.read_text())
        n_meds = sum(
            1 for e in bundle["entry"]
            if e["resource"]["resourceType"] == "MedicationStatement"
        )
        expected = int(
            row["on_acei_arb_arni"] + row["on_beta_blocker"]
            + row["on_mra"] + row["on_sglt2i"]
        )
        assert n_meds == expected
