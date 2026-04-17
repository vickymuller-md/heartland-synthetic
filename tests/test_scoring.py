"""Hand-computed tests for the HEARTLAND scoring engine."""

from __future__ import annotations

import json
from pathlib import Path

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
