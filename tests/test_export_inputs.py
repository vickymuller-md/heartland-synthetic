"""Structural export gates and bounded no-overwrite behavior, not clinical validation."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from heartland_synthetic import (
    HeartlandCohortConfig, export_fhir_bundle, export_redcap, generate_cohort,
)


@pytest.fixture
def frame():
    return generate_cohort(HeartlandCohortConfig(n_patients=3, seed=42))


def run_export(kind, frame, root):
    return (export_fhir_bundle(frame, root / "fhir") if kind == "fhir"
            else export_redcap(frame, root / "cohort"))


@pytest.mark.parametrize("kind", ["fhir", "redcap"])
@pytest.mark.parametrize("field,value", [
    ("patient_id", "../outside"), ("patient_id", "/absolute"),
    ("patient_id", ".."), ("patient_id", "a/b"), ("patient_id", "a\\b"),
    ("patient_id", "=FORMULA"), ("patient_id", "a\nnext"),
    ("patient_id", "a" * 65), ("patient_id", 123), ("patient_id", None),
    ("age", np.nan), ("age", True), ("age", 50.5), ("age", 2026),
    ("age", -1),
    ("age", np.timedelta64(1, "D")), ("age", pd.NA),
    ("bnp", np.inf), ("bnp", "500"), ("bnp", 10**400),
    ("bnp", 2**53 + 1), ("bnp", np.int64(2**53 + 1)),
    ("dbp", np.nan), ("hr", False), ("bmi", np.datetime64("NaT", "D")),
    ("diabetes", 0.5), ("af", 2), ("on_mra", "1"),
    ("mortality_1yr", -1), ("hospitalization_1yr", None),
    ("ckd_stage", 1.5), ("ckd_stage", 0), ("ckm_stage", 5),
    ("rural_urban_code", 11), ("rural_urban_code", True),
    ("sex", "unknown"), ("sex", None), ("hf_type", "other"),
    ("race", ""), ("race", None), ("race", pd.NA),
    ("state", "ks"), ("state", "KSS"),
    ("county_fips", 12345), ("county_fips", "1234"),
    ("gdmt_classes_count", 9), ("heartland_risk_score", 4.5),
    ("heartland_risk_tier", "very_high"),
])
def test_invalid_later_row_writes_nothing(kind, field, value, frame, tmp_path):
    frame[field] = frame[field].astype(object)
    frame.at[frame.index[-1], field] = value
    original = frame.copy(deep=True)
    target = tmp_path / "new-output"
    with pytest.raises((ValueError, TypeError)) as error:
        run_export(kind, frame, target)
    assert "HS-000003" not in str(error.value)
    assert not target.exists()
    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize("kind", ["fhir", "redcap"])
@pytest.mark.parametrize("problem", ["missing", "duplicate_column", "extra", "record_id", "half_outcome", "duplicate_id", "case_id", "score", "tier", "count"])
def test_contract_disagreements_fail_before_io(kind, problem, frame, tmp_path):
    if problem == "missing":
        frame = frame.drop(columns="social_support_score")
    elif problem == "duplicate_column":
        frame = pd.concat([frame, frame[["age"]]], axis=1)
    elif problem in {"extra", "record_id"}:
        frame[problem] = "unreviewed"
    elif problem == "half_outcome":
        frame = frame.drop(columns="mortality_1yr")
    elif problem in {"duplicate_id", "case_id"}:
        frame.loc[1, "patient_id"] = frame.loc[0, "patient_id"].lower() if problem == "case_id" else frame.loc[0, "patient_id"]
    elif problem == "score":
        frame.loc[1, "heartland_risk_score"] = (int(frame.loc[1, "heartland_risk_score"]) + 1) % 19
    elif problem == "tier":
        frame.loc[1, "heartland_risk_tier"] = "high" if frame.loc[1, "heartland_risk_tier"] == "low" else "low"
    else:
        frame.loc[1, "gdmt_classes_count"] = (int(frame.loc[1, "gdmt_classes_count"]) + 1) % 5
    with pytest.raises((ValueError, KeyError)):
        run_export(kind, frame, tmp_path / "new")
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize("kind", ["fhir", "redcap"])
@pytest.mark.parametrize("value", [None, [], {}])
def test_dataframe_required(kind, value, tmp_path):
    with pytest.raises(TypeError):
        run_export(kind, value, tmp_path / "new")
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize("kind", ["fhir", "redcap"])
@pytest.mark.parametrize("shape", ["file", "directory", "symlink", "dangling"])
def test_existing_later_target_is_never_overwritten(kind, shape, frame, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    target = root / "cohort_datadict.csv"
    if kind == "fhir":
        (root / "fhir").mkdir()
        target = root / "fhir" / f"{frame.loc[2, 'patient_id']}.json"
    if shape == "file":
        target.write_text("preserved", encoding="utf-8")
    elif shape == "directory":
        target.mkdir()
    else:
        source = tmp_path / "original"
        if shape == "symlink":
            source.write_text("original", encoding="utf-8")
        target.symlink_to(source)
    before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
    with pytest.raises(FileExistsError):
        run_export(kind, frame, root)
    assert sorted(str(p.relative_to(root)) for p in root.rglob("*")) == before
    if shape == "file":
        assert target.read_text() == "preserved"
    if shape == "symlink":
        assert target.read_text() == "original"


@pytest.mark.parametrize("kind", ["fhir", "redcap"])
@pytest.mark.parametrize("outcomes,medications", [(False, False), (False, True), (True, False), (True, True)])
def test_generator_variants_export_without_mutation(kind, outcomes, medications, tmp_path):
    frame = generate_cohort(HeartlandCohortConfig(n_patients=3, seed=91, include_outcomes=outcomes, include_medications=medications))
    frame.index = pd.MultiIndex.from_tuples([("duplicate", 1)] * 3)
    frame = frame[frame.columns[::-1]]
    original = frame.copy(deep=True)
    paths = run_export(kind, frame, tmp_path)
    pd.testing.assert_frame_equal(frame, original)
    if kind == "fhir":
        assert len(paths) == 3
        for path in paths:
            assert json.loads(path.read_text())["resourceType"] == "Bundle"
    else:
        exported = pd.read_csv(paths[0], dtype=str)
        assert exported.columns[0] == "record_id"
        assert list(exported.record_id) == list(frame.patient_id)


@pytest.mark.parametrize("kind", ["fhir", "redcap"])
def test_empty_table_still_needs_schema(kind, frame, tmp_path):
    run_export(kind, frame.iloc[:0], tmp_path / "valid")
    with pytest.raises(KeyError):
        run_export(kind, pd.DataFrame(), tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_redcap_categories_have_matching_serialized_codes(frame, tmp_path):
    for field in ["ckd_stage", "ckm_stage", "rural_urban_code", "gdmt_classes_count"]:
        frame[field] = frame[field].astype(float)
    frame["on_mra"] = frame["on_mra"].astype(bool)
    data, _ = export_redcap(frame, tmp_path / "numeric")
    table = pd.read_csv(data, dtype=str)
    for field in ["ckd_stage", "ckm_stage", "rural_urban_code", "on_mra"]:
        assert all(value.isdigit() for value in table[field])


def test_unknown_race_is_not_a_valid_redcap_choice(frame, tmp_path):
    frame["race"] = "Unclassified"
    with pytest.raises(ValueError):
        export_redcap(frame, tmp_path / "new" / "cohort")
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize("age,year", [(0, "2026"), (1027, "0999"), (2025, "0001")])
def test_birth_year_is_zero_padded_and_not_future(age, year, frame, tmp_path):
    from heartland_synthetic.scoring import apply_heartland_scoring
    frame["age"] = age
    frame = apply_heartland_scoring(frame)
    path = export_fhir_bundle(frame, tmp_path / "fhir")[0]
    bundle = json.loads(path.read_text())
    patient = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
    assert patient["birthDate"] == year


@pytest.mark.parametrize("kind", ["fhir", "redcap"])
def test_exclusive_open_refuses_target_created_after_preflight(kind, frame, tmp_path, monkeypatch):
    original_open = Path.open
    attempted = []

    def racing_open(path, mode="r", *args, **kwargs):
        if mode == "x" and not attempted:
            attempted.append(path)
            with original_open(path, "w", encoding="utf-8") as handle:
                handle.write("created by another writer")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", racing_open)
    with pytest.raises(FileExistsError):
        run_export(kind, frame, tmp_path / "new")
    assert len(attempted) == 1
    assert attempted[0].read_text() == "created by another writer"
    assert sum(p.is_file() for p in (tmp_path / "new").rglob("*")) == 1


@pytest.mark.parametrize("kind", ["fhir", "redcap"])
def test_later_io_failure_is_not_claimed_atomic(kind, frame, tmp_path, monkeypatch):
    original_open = Path.open
    attempted = []

    def failing_open(path, mode="r", *args, **kwargs):
        if mode == "x":
            attempted.append(path)
            if len(attempted) == 2:
                raise OSError("simulated storage failure")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failing_open)
    with pytest.raises(OSError, match="simulated storage failure"):
        run_export(kind, frame, tmp_path / "new")
    assert attempted[0].is_file()
    assert not attempted[1].exists()


def test_entire_fhir_batch_serializes_before_output(frame, tmp_path, monkeypatch):
    from heartland_synthetic.exports import fhir
    original = fhir._build_bundle
    calls = []

    def with_invalid_json(row):
        bundle = original(row)
        calls.append(True)
        if len(calls) == 2:
            bundle["invalid"] = float("nan")
        return bundle

    monkeypatch.setattr(fhir, "_build_bundle", with_invalid_json)
    with pytest.raises(ValueError):
        export_fhir_bundle(frame, tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_higher_precision_float_is_rejected_only_if_lossy():
    from heartland_synthetic.exports._validation import _number
    value = np.nextafter(np.longdouble(1), np.longdouble(2))
    if value.as_integer_ratio() != float(value).as_integer_ratio():
        with pytest.raises(ValueError):
            _number(value, "bnp")
    else:
        assert _number(value, "bnp") == float(value)


@pytest.mark.parametrize("outcomes", [False, True])
def test_empty_dictionary_does_not_depend_on_source_dtypes(frame, outcomes, tmp_path):
    if not outcomes:
        frame = frame.drop(columns=["mortality_1yr", "hospitalization_1yr"])
    _, full_dd = export_redcap(frame, tmp_path / "full")
    _, sliced_dd = export_redcap(frame.iloc[:0], tmp_path / "sliced")
    _, bare_dd = export_redcap(pd.DataFrame(columns=frame.columns), tmp_path / "bare")
    assert full_dd.read_bytes() == sliced_dd.read_bytes() == bare_dd.read_bytes()
