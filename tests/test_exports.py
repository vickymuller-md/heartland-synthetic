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
from heartland_synthetic.exports.redcap import REDCAP_DD_HEADER

# US Core 6.1 required value sets (omb-race-category / omb-ethnicity-category),
# each including the NullFlavor subset UNK / ASKU.
OMB_RACE_CODES = {
    "1002-5", "2028-9", "2054-5", "2076-8", "2106-3", "UNK", "ASKU",
}
OMB_ETHNICITY_CODES = {"2135-2", "2186-5", "UNK", "ASKU"}
US_CORE_RACE_EXT = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"
US_CORE_ETHNICITY_EXT = (
    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
)
SYNTHETIC_COUNTY_EXT = (
    "https://fhir.heartlandprotocol.org/StructureDefinition/"
    "heartland-synthetic-county-code"
)
SYNTHETIC_COUNTY_SYSTEM = (
    "https://fhir.heartlandprotocol.org/sid/synthetic-county-code"
)


# Frozen copy of the 75 field names of the HEARTLAND REDCap Instrument Template
# (vickymuller-md/redcap-template, instruments/heartland_data_dictionary.csv).
# Kept here so the guard below runs without that repository checked out.
TEMPLATE_FIELD_NAMES = {
    "record_id", "enr_date", "consent_date", "facility_name", "facility_cah",
    "facility_tier", "state", "county_fips", "rural_urban", "age", "sex",
    "race", "ethnicity", "bl_prior_hf_hosp_6mo", "bl_lvef_pct",
    "bl_lvef_category", "bl_egfr", "bl_np_type", "bl_np_value",
    "bl_sbp_admit", "bl_diabetes", "bl_ckm_stage", "bl_distance_cardio_mi",
    "bl_social_support_limited", "bl_enrichd_score", "bl_risk_score",
    "bl_risk_tier", "bl_pro_consent", "gdmt_arni_acei_arb_drug",
    "gdmt_arni_acei_arb_dose", "gdmt_arni_acei_arb_target",
    "gdmt_arni_acei_arb_start", "gdmt_bb_drug", "gdmt_bb_dose",
    "gdmt_bb_target", "gdmt_bb_start", "gdmt_mra_drug", "gdmt_mra_dose",
    "gdmt_mra_target", "gdmt_mra_start", "gdmt_sglt2_drug", "gdmt_sglt2_dose",
    "gdmt_sglt2_start", "gdmt_hfpef_glp1", "gdmt_classes_count",
    "gdmt_generic_bridge", "gdmt_init_tier", "mo_event_number", "mo_date",
    "mo_track", "mo_weight_lb", "mo_sbp", "mo_dbp", "mo_hr", "mo_spo2",
    "mo_egfr", "mo_k", "mo_bnp", "mo_gdmt_change", "mo_gdmt_change_notes",
    "mo_red_flag_count", "mo_red_flag_types", "mo_hosp_any", "mo_hosp_hf",
    "mo_ed_any", "mo_ed_hf", "mo_kccq12_score", "out_vital_status",
    "out_death_date", "out_death_cardiovascular", "out_hf_hosp_count",
    "out_hf_ed_count", "out_days_alive_oh", "out_gdmt_optimized",
    "out_kccq12_12mo",
}
# The only names the standalone instrument shares with the Template. A shared
# name is never a compatibility claim: `sex` and `race` share a name but not a
# coding (exporter: F/M and a 4-level mixed race/ethnicity radio; Template:
# 1/2/3 and a 7-category checkbox plus a separate `ethnicity` field), and
# `gdmt_classes_count` is stored data here but a `calc` field in the Template.
TEMPLATE_SHARED_FIELDS = {
    "record_id", "state", "county_fips", "age", "sex", "race",
    "gdmt_classes_count",
}


@pytest.fixture(scope="module")
def cohort_for_exports() -> pd.DataFrame:
    cfg = HeartlandCohortConfig(n_patients=25, include_outcomes=True, seed=91)
    return generate_cohort(cfg)


def _bundles(tmp_path, df: pd.DataFrame) -> list[dict]:
    paths = export_fhir_bundle(df, tmp_path / "fhir")
    return [json.loads(p.read_text()) for p in paths]


def _resources(bundle: dict, resource_type: str) -> list[dict]:
    return [
        e["resource"] for e in bundle["entry"]
        if e["resource"]["resourceType"] == resource_type
    ]


def _omb_slice(patient: dict, ext_url: str) -> tuple[str, str]:
    """Return ``(ombCategory code, text)`` of a US Core extension on Patient."""
    ext = next(e for e in patient["extension"] if e["url"] == ext_url)
    parts = {p["url"]: p for p in ext["extension"]}
    return parts["ombCategory"]["valueCoding"]["code"], parts["text"]["valueString"]


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
        assert system in (
            "http://loinc.org",
            "https://fhir.heartlandprotocol.org/CodeSystem/heartland-risk-score",
        )


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


# ---------------------------------------------------------------------------
# FHIR — address / geography
# ---------------------------------------------------------------------------
def test_patient_address_has_no_postal_code(tmp_path, cohort_for_exports):
    """county_fips is not a ZIP; postalCode must never carry it."""
    for bundle in _bundles(tmp_path, cohort_for_exports):
        for patient in _resources(bundle, "Patient"):
            for address in patient["address"]:
                assert "postalCode" not in address
                # No county name is generated, so district stays absent too.
                assert "district" not in address


def test_county_code_uses_synthetic_extension(tmp_path, cohort_for_exports):
    for bundle in _bundles(tmp_path, cohort_for_exports):
        patient = _resources(bundle, "Patient")[0]
        pid = patient["id"]
        row = cohort_for_exports[cohort_for_exports["patient_id"] == pid].iloc[0]
        address = patient["address"][0]
        ext = next(
            e for e in address["extension"] if e["url"] == SYNTHETIC_COUNTY_EXT
        )
        coding = ext["valueCoding"]
        assert coding["system"] == SYNTHETIC_COUNTY_SYSTEM
        assert coding["code"] == str(row["county_fips"])
        # Never claim an ANSI/Census identifier for a synthetic code.
        assert "census.gov" not in coding["system"]
        assert "ansi" not in coding["system"].lower()


# ---------------------------------------------------------------------------
# FHIR — US Core race / ethnicity
# ---------------------------------------------------------------------------
def test_race_ombcategory_within_us_core_vs(tmp_path, cohort_for_exports):
    for bundle in _bundles(tmp_path, cohort_for_exports):
        for patient in _resources(bundle, "Patient"):
            code, _ = _omb_slice(patient, US_CORE_RACE_EXT)
            assert code in OMB_RACE_CODES
            # Explicit negative: ethnicity and "Other Race" are outside the
            # omb-race-category required value set.
            assert code not in {"2135-2", "2131-1"}


def test_ethnicity_extension_present(tmp_path, cohort_for_exports):
    for bundle in _bundles(tmp_path, cohort_for_exports):
        for patient in _resources(bundle, "Patient"):
            code, text = _omb_slice(patient, US_CORE_ETHNICITY_EXT)
            assert code in OMB_ETHNICITY_CODES
            assert text


def test_race_text_cardinality(tmp_path, cohort_for_exports):
    """US Core requires text 1..1 on both extensions."""
    for bundle in _bundles(tmp_path, cohort_for_exports):
        for patient in _resources(bundle, "Patient"):
            for url in (US_CORE_RACE_EXT, US_CORE_ETHNICITY_EXT):
                ext = next(e for e in patient["extension"] if e["url"] == url)
                texts = [p for p in ext["extension"] if p["url"] == "text"]
                assert len(texts) == 1
                assert texts[0]["valueString"].strip()


@pytest.mark.parametrize(
    "race,expected_race_code,expected_ethnicity_code",
    [
        ("White", "2106-3", "UNK"),
        ("Black", "2054-5", "UNK"),
        ("Hispanic", "UNK", "2135-2"),
        ("Other", "UNK", "UNK"),
    ],
)
def test_race_level_maps_to_expected_codes(
    tmp_path, cohort_for_exports, race, expected_race_code,
    expected_ethnicity_code,
):
    """Hispanic goes to ethnicity, never to race; Other degrades to UNK."""
    row = cohort_for_exports.iloc[[0]].copy()
    row["race"] = race
    bundle = _bundles(tmp_path / race, row)[0]
    patient = _resources(bundle, "Patient")[0]
    race_code, _ = _omb_slice(patient, US_CORE_RACE_EXT)
    eth_code, _ = _omb_slice(patient, US_CORE_ETHNICITY_EXT)
    assert race_code == expected_race_code
    assert eth_code == expected_ethnicity_code


def test_unknown_race_value_degrades_to_unk(tmp_path, cohort_for_exports):
    row = cohort_for_exports.iloc[[0]].copy()
    row["race"] = "Not a modelled level"
    patient = _resources(_bundles(tmp_path, row)[0], "Patient")[0]
    assert _omb_slice(patient, US_CORE_RACE_EXT)[0] == "UNK"
    assert _omb_slice(patient, US_CORE_ETHNICITY_EXT)[0] == "UNK"


# ---------------------------------------------------------------------------
# FHIR — HEARTLAND score / tier
# ---------------------------------------------------------------------------
def test_risk_assessment_shape(tmp_path, cohort_for_exports):
    for bundle in _bundles(tmp_path, cohort_for_exports):
        assessments = _resources(bundle, "RiskAssessment")
        assert len(assessments) == 1
        ra = assessments[0]
        pid = _resources(bundle, "Patient")[0]["id"]
        row = cohort_for_exports[cohort_for_exports["patient_id"] == pid].iloc[0]

        assert ra["method"]["text"] == "HEARTLAND Protocol v3.2 Risk Score"
        coding = ra["prediction"][0]["qualitativeRisk"]["coding"][0]
        assert coding["system"] == (
            "https://fhir.heartlandprotocol.org/CodeSystem/heartland-risk-tier"
        )
        assert coding["code"] == row["heartland_risk_tier"]

        # basis resolves to the score Observation in the same Bundle
        basis_id = ra["basis"][0]["reference"].split("/")[-1]
        score_obs = [
            o for o in _resources(bundle, "Observation") if o["id"] == basis_id
        ]
        assert len(score_obs) == 1
        assert score_obs[0]["valueInteger"] == int(row["heartland_risk_score"])


def test_no_raw_score_in_probability_decimal(tmp_path, cohort_for_exports):
    """The 0-18 point total is not a probability — never in probability[x]."""
    for bundle in _bundles(tmp_path, cohort_for_exports):
        for ra in _resources(bundle, "RiskAssessment"):
            for prediction in ra["prediction"]:
                assert "probabilityDecimal" not in prediction
                assert "probabilityRange" not in prediction


def test_no_profile_conformance_claimed(tmp_path, cohort_for_exports):
    """No resource asserts a profile that has not been validated."""
    for bundle in _bundles(tmp_path, cohort_for_exports):
        for entry in bundle["entry"]:
            assert "profile" not in entry["resource"].get("meta", {})


def test_canonical_urls_match_ig(tmp_path, cohort_for_exports):
    for bundle in _bundles(tmp_path, cohort_for_exports):
        for url in _heartland_urls(bundle):
            assert url.startswith("https://fhir.heartlandprotocol.org/")


def _heartland_urls(node, found=None) -> list[str]:
    """Every HEARTLAND-owned URI string anywhere in the Bundle."""
    found = [] if found is None else found
    if isinstance(node, dict):
        for value in node.values():
            _heartland_urls(value, found)
    elif isinstance(node, list):
        for value in node:
            _heartland_urls(value, found)
    elif isinstance(node, str) and "heartlandprotocol.org" in node:
        found.append(node)
    return found


# ---------------------------------------------------------------------------
# REDCap — instrument boundary guards
# ---------------------------------------------------------------------------
def test_dd_header_matches_official_layout():
    """Regression guard on the official 18-column data dictionary layout."""
    assert len(REDCAP_DD_HEADER) == 18
    assert REDCAP_DD_HEADER[0] == "Variable / Field Name"
    assert REDCAP_DD_HEADER[-1] == "Field Annotation"


def test_exported_field_names_disjoint_from_template(
    tmp_path, cohort_for_exports
):
    """Static guard: this is a standalone instrument, not the HEARTLAND Template.

    The Template uses bl_* / gdmt_* / mo_* / out_* names. If exported fields are
    ever renamed to look Template-compatible, this breaks and forces an explicit
    decision instead of an implicit interoperability claim.
    """
    data, dd = export_redcap(cohort_for_exports, tmp_path / "cohort")
    columns = set(pd.read_csv(data).columns)
    dict_fields = set(pd.read_csv(dd)["Variable / Field Name"])

    assert columns & TEMPLATE_FIELD_NAMES == TEMPLATE_SHARED_FIELDS
    assert dict_fields & TEMPLATE_FIELD_NAMES == TEMPLATE_SHARED_FIELDS
    assert not {
        c for c in columns
        if c.startswith(("bl_", "mo_", "out_", "enr_", "facility_"))
    }
