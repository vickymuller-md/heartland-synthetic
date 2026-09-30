"""Synthetic mapping semantics; no clinical/profile conformance assertion."""

import itertools
import json
from uuid import UUID

import pandas as pd
import pytest

from heartland_synthetic import HeartlandCohortConfig, export_fhir_bundle, generate_cohort
from heartland_synthetic.exports.fhir import _build_bundle
from heartland_synthetic.scoring import apply_heartland_scoring


def resources(bundle, kind):
    return [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == kind]


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


@pytest.mark.parametrize("outcomes,medications", list(itertools.product([False, True], repeat=2)))
def test_references_codes_and_simulation_boundary(outcomes, medications, tmp_path):
    frame = generate_cohort(HeartlandCohortConfig(n_patients=20, seed=91, include_outcomes=outcomes, include_medications=medications))
    original = frame.copy(deep=True)
    paths = export_fhir_bundle(frame, tmp_path)
    for row, path in zip(frame.to_dict("records"), paths):
        bundle = json.loads(path.read_text())
        entries = {e["fullUrl"]: e["resource"] for e in bundle["entry"]}
        assert len(entries) == len(bundle["entry"])
        for uri in entries:
            assert uri.startswith("urn:uuid:")
            assert str(UUID(uri.removeprefix("urn:uuid:"))) == uri.removeprefix("urn:uuid:")
        patient_uri = next(uri for uri, r in entries.items() if r["resourceType"] == "Patient")
        assert entries[patient_uri]["id"] == path.stem == row["patient_id"]
        for resource in [bundle, *entries.values()]:
            assert resource["meta"]["tag"] == [{"display": "Synthetic research/testing data"}]
            assert "profile" not in resource["meta"]
        for node in walk(bundle):
            if "reference" in node:
                assert node["reference"] in entries
            assert node.get("system") not in {
                "http://hl7.org/fhir/sid/icd-10-cm",
                "http://www.nlm.nih.gov/research/umls/rxnorm",
            }
            assert node.get("code") != "98979-8"
            assert not any(k.startswith("probability") for k in node)
            if "subject" in node:
                assert node["subject"]["reference"] == patient_uri
        assessment = resources(bundle, "RiskAssessment")[0]
        score = entries[assessment["basis"][0]["reference"]]
        assert score["resourceType"] == "Observation"
        assert score["valueInteger"] == row["heartland_risk_score"]
        med_resources = resources(bundle, "MedicationStatement")
        assert len(med_resources) == row["gdmt_classes_count"]
        med_labels = {
            "on_acei_arb_arni": "Simulated ACEi/ARB/ARNI class flag",
            "on_beta_blocker": "Simulated beta-blocker class flag",
            "on_mra": "Simulated mineralocorticoid receptor antagonist class flag",
            "on_sglt2i": "Simulated SGLT2 inhibitor class flag",
        }
        assert {m["medicationCodeableConcept"]["text"] for m in med_resources} == {
            label for key, label in med_labels.items() if row[key]
        }
        for med in med_resources:
            assert med["status"] == "unknown"
            assert set(med["medicationCodeableConcept"]) == {"text"}
            assert "Simulated" in med["medicationCodeableConcept"]["text"]
            assert not {"dosage", "effectiveDateTime", "dateAsserted"} & med.keys()
            assert "receipt" in med["note"][0]["text"]
    pd.testing.assert_frame_equal(frame, original)


def test_ten_boolean_components_reconstruct_all_1024_totals():
    template = generate_cohort(HeartlandCohortConfig(n_patients=1, seed=42)).iloc[0].to_dict()
    # Independent threshold-side inputs and weights, not the implementation's labels/predicates.
    fields = ["age", "prior_hf_hosp_6mo", "egfr", "bnp", "sbp", "diabetes", "lvef", "ckm_stage", "distance_to_cardiology_mi", "social_support_score"]
    pairs = [(74, 75), (0, 1), (45, 44), (499, 500), (100, 99), (0, 1), (30, 29), (2, 3), (50, 51), (18, 17)]
    weights = [2, 3, 2, 2, 2, 1, 2, 2, 1, 1]
    for flags in itertools.product([False, True], repeat=10):
        row = {**template, **{field: pair[int(flag)] for field, pair, flag in zip(fields, pairs, flags)}}
        total = sum(weight for weight, flag in zip(weights, flags) if flag)
        row.update(heartland_risk_score=total, heartland_risk_tier="low" if total <= 4 else "moderate" if total <= 8 else "high")
        bundle = _build_bundle(row)
        score = next(o for o in resources(bundle, "Observation") if o["code"].get("coding", [{}])[0].get("code") == "heartland-risk-score")
        criteria = [c for c in score["component"] if "valueBoolean" in c]
        assert len(criteria) == 10
        assert [c["valueBoolean"] for c in criteria] == list(flags)
        assert all(type(c["valueBoolean"]) is bool and set(c["code"]) == {"text"} for c in criteria)
        assert sum(w for w, c in zip(weights, criteria) if c["valueBoolean"]) == score["valueInteger"]
        labels = " ".join(c["code"]["text"] for c in criteria)
        assert "baseline" in labels and "BNP" in labels and "proxy" in labels and "legacy" in labels


@pytest.mark.parametrize("hf_type", ["hfref", "hfmref", "hfpef"])
def test_source_values_and_non_diagnostic_categories(hf_type, tmp_path):
    frame = generate_cohort(HeartlandCohortConfig(n_patients=1, seed=42))
    frame.loc[0, ["hf_type", "diabetes", "af", "ckd_stage", "ckm_stage", "social_support_score", "distance_to_cardiology_mi", "prior_hf_hosp_6mo"]] = [hf_type, 1, 1, 5, 4, 16, 63.5, 1]
    frame = apply_heartland_scoring(frame)
    bundle = json.loads(export_fhir_bundle(frame, tmp_path)[0].read_text())
    conditions = resources(bundle, "Condition")
    assert len(conditions) == 3
    assert all(set(c["code"]) == {"text"} for c in conditions)
    assert all("clinicalStatus" not in c and "recordedDate" not in c for c in conditions)
    assert not any("kidney" in c["code"]["text"].lower() or "hospital" in c["code"]["text"].lower() for c in conditions)
    observations = {o["code"]["text"]: o for o in resources(bundle, "Observation")}
    assert observations["Legacy simulated eGFR bin (not a CKD diagnosis)"]["valueInteger"] == 5
    assert observations["Legacy simulated CKM category (not adjudicated staging)"]["valueInteger"] == 4
    assert observations["Legacy social-support proxy (not ESSI)"]["valueQuantity"] == {"value": 16.0}
    assert observations["Modeled distance to cardiology"]["valueQuantity"]["value"] == 63.5
    assert observations["Simulated prior HF hospitalization within 6 months"]["valueBoolean"] is True
    codes = {"lvef": "10230-1", "bnp": "30934-4", "hr": "8867-4", "bmi": "39156-5"}
    for key, code in codes.items():
        observation = next(o for o in observations.values() if o["code"].get("coding", [{}])[0].get("code") == code)
        assert observation["valueQuantity"]["value"] == frame.loc[0, key]
    lvef = next(o for o in observations.values() if o["code"].get("coding", [{}])[0].get("code") == "10230-1")
    assert "category" not in lvef and "method" not in lvef
    egfr = observations["Simulated eGFR (formula unspecified)"]
    assert "coding" not in egfr["code"] and "method" not in egfr
    assert egfr["valueQuantity"]["value"] == frame.loc[0, "egfr"]
    bnp = next(o for o in observations.values() if o["code"].get("coding", [{}])[0].get("code") == "30934-4")
    assert "Assumed serum/plasma" in bnp["note"][0]["text"]
    assert "no recorded specimen or assay provenance" in bnp["note"][0]["text"]
    bp = next(o for o in observations.values() if o["code"].get("coding", [{}])[0].get("code") == "85354-9")
    assert "valueQuantity" not in bp and len(bp["component"]) == 2
    for key, component, code in zip(["sbp", "dbp"], bp["component"], ["8480-6", "8462-4"]):
        assert component["code"]["coding"][0]["code"] == code
        assert component["valueQuantity"] == {"value": float(frame.loc[0, key]), "unit": "mm[Hg]", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}
    assert not any(o["code"].get("coding", [{}])[0].get("code") in {"8480-6", "8462-4"} for o in observations.values())


def test_duplicate_internal_identity_is_rejected_before_output(tmp_path, monkeypatch):
    from heartland_synthetic.exports import fhir
    frame = generate_cohort(HeartlandCohortConfig(n_patients=1, seed=42))
    monkeypatch.setattr(fhir, "_uuid", lambda: "00000000-0000-4000-8000-000000000001")
    with pytest.raises(ValueError, match="Duplicate internal FHIR identity"):
        export_fhir_bundle(frame, tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_unregistered_reference_fails_before_output(tmp_path, monkeypatch):
    from heartland_synthetic.exports import fhir
    frame = generate_cohort(HeartlandCohortConfig(n_patients=1, seed=42))
    original = fhir._heartland_risk_assessment

    def broken(*args):
        resource = original(*args)
        resource["basis"][0]["reference"] = "Observation/missing"
        return resource

    monkeypatch.setattr(fhir, "_heartland_risk_assessment", broken)
    with pytest.raises(KeyError):
        export_fhir_bundle(frame, tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_mapping_documents_withdrawn_inferences():
    from pathlib import Path
    mapping = (Path(__file__).resolve().parents[1] / "docs/fhir_export_mapping.md").read_text()
    for boundary in ["not a CKD diagnosis", "status unknown", "all ten Boolean", "not ESSI", "not a clinical record", "rural_urban_code", "annual"]:
        assert boundary in mapping
