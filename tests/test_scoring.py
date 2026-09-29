"""Hand-computed tests for the HEARTLAND scoring engine."""

from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from heartland_synthetic import apply_heartland_scoring, classify_tier
from heartland_synthetic.scoring import MAX_SCORE, RISK_VARIABLES, compute_row_score


FIXTURES = Path(__file__).parent / "fixtures" / "hand_computed_cases.json"


@pytest.fixture(scope="module")
def hand_cases() -> list[dict]:
    return json.loads(FIXTURES.read_text())


def test_max_score_is_18():
    assert MAX_SCORE == 18
    assert sum(v.points for v in RISK_VARIABLES) == 18


def test_variable_count_is_10():
    assert len(RISK_VARIABLES) == 10


@pytest.mark.parametrize("score,expected", [
    (0, "low"), (1, "low"), (4, "low"),
    (5, "moderate"), (6, "moderate"), (8, "moderate"),
    (9, "high"), (12, "high"), (18, "high"),
])
def test_classify_tier_boundaries(score: int, expected: str):
    assert classify_tier(score) == expected


def test_hand_computed_cases(hand_cases: list[dict]):
    for case in hand_cases:
        score = compute_row_score(case["row"])
        tier = classify_tier(score)
        assert score == case["expected_score"], (
            f"{case['name']}: expected {case['expected_score']}, got {score}"
        )
        assert tier == case["expected_tier"], (
            f"{case['name']}: expected tier {case['expected_tier']}, got {tier}"
        )


def test_apply_heartland_scoring_dataframe(hand_cases: list[dict]):
    df = pd.DataFrame([c["row"] for c in hand_cases])
    scored = apply_heartland_scoring(df)
    assert list(scored["heartland_risk_score"]) == [c["expected_score"] for c in hand_cases]
    assert list(scored["heartland_risk_tier"]) == [c["expected_tier"] for c in hand_cases]


def test_apply_heartland_scoring_missing_column_raises():
    df = pd.DataFrame([{"age": 70}])
    with pytest.raises(KeyError, match="missing required columns"):
        apply_heartland_scoring(df)


# Explicit synthetic inputs, independent of the implementation's predicate list.
COMPLETE_ROW = {
    "age": 60,
    "prior_hf_hosp_6mo": 0,
    "egfr": 80,
    "bnp": 100,
    "sbp": 130,
    "diabetes": 0,
    "lvef": 55,
    "ckm_stage": 1,
    "distance_to_cardiology_mi": 10,
    "social_support_score": 30,
}
NUMERIC_FIELDS = (
    "age", "egfr", "bnp", "sbp", "lvef", "ckm_stage",
    "distance_to_cardiology_mi", "social_support_score",
)
TEMPORAL_VALUES = (
    np.timedelta64(0, "D"), np.timedelta64(1, "D"), np.timedelta64("NaT", "D"),
    np.datetime64("2026-01-01", "D"), np.datetime64("NaT", "D"),
    pd.Timedelta(0), pd.Timedelta(days=1), pd.NaT,
)


@pytest.mark.parametrize("field", tuple(COMPLETE_ROW))
@pytest.mark.parametrize("invalid", [None, pd.NA, np.nan, np.inf, -np.inf, "", "unknown", "0", [], {}])
def test_missing_or_non_numeric_input_never_produces_score(field, invalid):
    row = {**COMPLETE_ROW, field: invalid}
    with pytest.raises(ValueError, match=field):
        compute_row_score(row)
    with pytest.raises(ValueError, match=field):
        apply_heartland_scoring(pd.DataFrame([row]))


@pytest.mark.parametrize("field", tuple(COMPLETE_ROW))
@pytest.mark.parametrize("invalid", TEMPORAL_VALUES)
def test_temporal_inputs_and_nat_are_never_measurements(field, invalid):
    row = {**COMPLETE_ROW, field: invalid}
    with pytest.raises(ValueError, match=field):
        compute_row_score(row)
    with pytest.raises(ValueError, match=field):
        apply_heartland_scoring(pd.DataFrame([row]))


@pytest.mark.parametrize("invalid", TEMPORAL_VALUES)
def test_temporal_total_is_invalid(invalid):
    with pytest.raises(ValueError, match="score"):
        classify_tier(invalid)


@pytest.mark.parametrize("field", NUMERIC_FIELDS)
@pytest.mark.parametrize("invalid", [True, False, np.bool_(True), np.bool_(False)])
def test_boolean_is_not_a_measurement(field, invalid):
    row = {**COMPLETE_ROW, field: invalid}
    with pytest.raises(ValueError, match=field):
        compute_row_score(row)
    with pytest.raises(ValueError, match=field):
        apply_heartland_scoring(pd.DataFrame([row]))


@pytest.mark.parametrize("field", ("diabetes", "prior_hf_hosp_6mo"))
@pytest.mark.parametrize("invalid", [-1, 2, 0.5, np.float64(1.5)])
def test_binary_fields_reject_non_binary_numbers(field, invalid):
    with pytest.raises(ValueError, match=field):
        compute_row_score({**COMPLETE_ROW, field: invalid})


@pytest.mark.parametrize("value", [True, np.bool_(True), 1, 1.0, np.int64(1), np.float64(1)])
def test_binary_fields_accept_explicit_true_or_one(value):
    assert compute_row_score({**COMPLETE_ROW, "diabetes": value, "prior_hf_hosp_6mo": value}) == 4


@pytest.mark.parametrize("value", [False, np.bool_(False), 0, 0.0, np.int64(0), np.float64(0)])
def test_binary_fields_accept_explicit_false_or_zero(value):
    assert compute_row_score({**COMPLETE_ROW, "diabetes": value, "prior_hf_hosp_6mo": value}) == 0


@pytest.mark.parametrize("invalid", [-1, 5, 2.99, 3.9])
def test_ckm_is_a_complete_integer_category(invalid):
    with pytest.raises(ValueError, match="ckm_stage"):
        compute_row_score({**COMPLETE_ROW, "ckm_stage": invalid})


@pytest.mark.parametrize("stage,points", [(0, 0), (1, 0), (2, 0), (3, 2), (4, 2)])
def test_ckm_accepts_integral_numeric_categories(stage, points):
    assert compute_row_score({**COMPLETE_ROW, "ckm_stage": float(stage)}) == points


@pytest.mark.parametrize("invalid", [-1, 19, 4.5, True, False, np.bool_(True), None, pd.NA, np.nan, np.inf, -np.inf, "9", [], {}])
def test_classify_tier_rejects_invalid_total(invalid):
    with pytest.raises(ValueError, match="score"):
        classify_tier(invalid)


@pytest.mark.parametrize("score", [0.0, np.int64(0), np.float64(4.0), 5.0, 8.0, 9.0, 18.0])
def test_classify_tier_accepts_integral_real_total(score):
    expected = "low" if score <= 4 else "moderate" if score <= 8 else "high"
    assert classify_tier(score) == expected


def test_all_1024_complete_combinations_keep_weights_and_tiers():
    triggered = dict(zip(COMPLETE_ROW, (75, 1, 44.9, 500, 99.9, 1, 29.9, 3, 50.1, 17)))
    weights = (2, 3, 2, 2, 2, 1, 2, 2, 1, 1)
    rows, expected_scores = [], []
    for bits in product((False, True), repeat=10):
        row = {key: triggered[key] if on else COMPLETE_ROW[key] for key, on in zip(COMPLETE_ROW, bits)}
        expected = sum(weight for weight, on in zip(weights, bits) if on)
        assert compute_row_score(row) == expected
        rows.append(row)
        expected_scores.append(expected)
    result = apply_heartland_scoring(pd.DataFrame(rows))
    assert result["heartland_risk_score"].tolist() == expected_scores
    assert result["heartland_risk_tier"].tolist() == [
        "low" if score <= 4 else "moderate" if score <= 8 else "high"
        for score in expected_scores
    ]


@pytest.mark.parametrize("field,value,expected", [
    ("age", 74.9, 0), ("age", 75, 2),
    ("egfr", 44.9, 2), ("egfr", 45, 0),
    ("bnp", 499.9, 0), ("bnp", 500, 2),
    ("sbp", 99.9, 2), ("sbp", 100, 0),
    ("lvef", 29.9, 2), ("lvef", 30, 0),
    ("distance_to_cardiology_mi", 50, 0), ("distance_to_cardiology_mi", 50.1, 1),
    ("social_support_score", 17, 1), ("social_support_score", 18, 0),
])
def test_numeric_thresholds_are_unchanged(field, value, expected):
    assert compute_row_score({**COMPLETE_ROW, field: value}) == expected


def test_required_keys_are_checked_before_scoring():
    for field in COMPLETE_ROW:
        row = {key: value for key, value in COMPLETE_ROW.items() if key != field}
        with pytest.raises(KeyError, match=field):
            compute_row_score(row)


def test_duplicate_columns_are_rejected_in_frame_and_series():
    frame = pd.DataFrame([COMPLETE_ROW])
    duplicate = pd.concat([frame, frame[["age"]]], axis=1)
    with pytest.raises(ValueError, match="duplicate"):
        apply_heartland_scoring(duplicate)
    with pytest.raises(ValueError, match="duplicate"):
        compute_row_score(duplicate.iloc[0])


def test_empty_complete_frame_has_typed_outputs_and_keeps_index():
    frame = pd.DataFrame(columns=list(COMPLETE_ROW), index=pd.Index([], name="case"))
    result = apply_heartland_scoring(frame)
    pd.testing.assert_index_equal(result.index, frame.index)
    assert result.empty
    assert pd.api.types.is_integer_dtype(result["heartland_risk_score"])
    assert pd.api.types.is_string_dtype(result["heartland_risk_tier"].dtype)
    assert "heartland_risk_score" not in frame


def test_index_payload_and_existing_scores_are_handled_without_mutation():
    frame = pd.DataFrame([COMPLETE_ROW, {**COMPLETE_ROW, "diabetes": True}], index=["duplicate", "duplicate"])
    frame.index.name = "case"
    frame["extra"] = ["first", "second"]
    frame["heartland_risk_score"] = [18, 18]
    frame["heartland_risk_tier"] = ["high", "high"]
    before = frame.copy(deep=True)
    result = apply_heartland_scoring(frame)
    pd.testing.assert_frame_equal(frame, before)
    pd.testing.assert_index_equal(result.index, before.index)
    assert result["extra"].tolist() == ["first", "second"]
    assert result["heartland_risk_score"].tolist() == [0, 1]
    assert result["heartland_risk_tier"].tolist() == ["low", "low"]


def test_one_invalid_row_fails_whole_frame_without_mutation_or_value_in_error():
    frame = pd.DataFrame([COMPLETE_ROW, {**COMPLETE_ROW, "bnp": "synthetic-private-marker"}])
    before = frame.copy(deep=True)
    with pytest.raises(ValueError, match="bnp") as exc:
        apply_heartland_scoring(frame)
    assert "synthetic-private-marker" not in str(exc.value)
    pd.testing.assert_frame_equal(frame, before)


def test_numpy_scalars_and_nullable_pandas_dtypes_work_when_complete():
    row = {key: np.float64(value) for key, value in COMPLETE_ROW.items()}
    assert compute_row_score(row) == 0
    frame = pd.DataFrame([COMPLETE_ROW]).convert_dtypes()
    assert apply_heartland_scoring(frame)["heartland_risk_score"].tolist() == [0]


def test_multiindex_non_monotonic_order_and_missing_extras_are_preserved():
    index = pd.MultiIndex.from_tuples([("z", 2), ("a", 1), ("z", 2)], names=["group", "case"])
    frame = pd.DataFrame([COMPLETE_ROW] * 3, index=index)
    frame["notes"] = [None, "synthetic", pd.NA]
    result = apply_heartland_scoring(frame)
    pd.testing.assert_frame_equal(result[frame.columns], frame)
    pd.testing.assert_index_equal(result.index, frame.index)
    assert result["heartland_risk_score"].tolist() == [0, 0, 0]


@pytest.mark.parametrize("value", [10**400, np.finfo(np.longdouble).max])
def test_finiteness_does_not_round_or_limit_numeric_precision(value):
    # Structural validation deliberately does not certify plausible clinical ranges.
    assert compute_row_score({**COMPLETE_ROW, "bnp": value}) == 2
    frame = pd.DataFrame([{**COMPLETE_ROW, "bnp": value}], dtype=object)
    assert apply_heartland_scoring(frame)["heartland_risk_score"].tolist() == [2]


@pytest.mark.parametrize("field", [name for name in NUMERIC_FIELDS if name != "ckm_stage"])
def test_no_new_physiologic_or_instrument_ranges_are_introduced(field):
    row = {**COMPLETE_ROW, field: -1}
    assert isinstance(compute_row_score(row), int)


def test_empty_frame_still_requires_all_columns():
    with pytest.raises(KeyError, match="missing required columns"):
        apply_heartland_scoring(pd.DataFrame())


@pytest.mark.parametrize("value", [10**400, np.finfo(np.longdouble).max])
def test_extreme_totals_are_rejected_without_conversion_error(value):
    with pytest.raises(ValueError, match="score"):
        classify_tier(value)
