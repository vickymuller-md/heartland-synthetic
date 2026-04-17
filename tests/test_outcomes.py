"""Outcome model behavior: monotonicity + per-tier calibration."""

from __future__ import annotations

import pandas as pd
import pytest

from heartland_synthetic import HeartlandCohortConfig, generate_cohort
from heartland_synthetic.outcomes import sample_outcomes
from heartland_synthetic.registries import OUTCOME_RATES
from heartland_synthetic._rng import make_rng


def test_outcome_columns_present_when_requested():
    cfg = HeartlandCohortConfig(n_patients=200, include_outcomes=True, seed=31)
    df = generate_cohort(cfg)
    assert "mortality_1yr" in df.columns
    assert "hospitalization_1yr" in df.columns
    assert set(df["mortality_1yr"].unique()).issubset({0, 1})


def test_outcome_columns_absent_when_disabled():
    cfg = HeartlandCohortConfig(n_patients=200, include_outcomes=False, seed=32)
    df = generate_cohort(cfg)
    assert "mortality_1yr" not in df.columns
    assert "hospitalization_1yr" not in df.columns


def test_mortality_monotonic_by_tier():
    cfg = HeartlandCohortConfig(n_patients=10_000, include_outcomes=True, seed=33)
    df = generate_cohort(cfg)
    rates = df.groupby("heartland_risk_tier")["mortality_1yr"].mean()
    assert rates["high"] > rates["moderate"] > rates["low"]


def test_hospitalization_monotonic_by_tier():
    cfg = HeartlandCohortConfig(n_patients=10_000, include_outcomes=True, seed=34)
    df = generate_cohort(cfg)
    rates = df.groupby("heartland_risk_tier")["hospitalization_1yr"].mean()
    assert rates["high"] > rates["moderate"] > rates["low"]


def test_tier_rates_within_tolerance():
    cfg = HeartlandCohortConfig(n_patients=10_000, include_outcomes=True, seed=35)
    df = generate_cohort(cfg)
    for tier, targets in OUTCOME_RATES.items():
        subset = df[df["heartland_risk_tier"] == tier]
        if len(subset) < 100:
            continue
        assert abs(subset["mortality_1yr"].mean() - targets["mortality_1yr"]) < 0.04
        assert abs(subset["hospitalization_1yr"].mean() - targets["hospitalization_1yr"]) < 0.05


def test_sample_outcomes_missing_tier_raises():
    rng = make_rng(1)
    df = pd.DataFrame({"foo": [1, 2, 3]})
    with pytest.raises(KeyError):
        sample_outcomes(df, rng)
