"""Time-series generator behavior."""

from __future__ import annotations

import pandas as pd
import pytest

from heartland_synthetic import (
    HeartlandCohortConfig,
    generate_cohort,
    generate_time_series,
)


def _cohort(n: int = 100, seed: int = 51) -> pd.DataFrame:
    return generate_cohort(
        HeartlandCohortConfig(n_patients=n, include_outcomes=True, seed=seed)
    )


def test_output_schema():
    cohort = _cohort()
    ts = generate_time_series(cohort, months=12, seed=7)
    expected = {
        "patient_id", "month", "sbp", "dbp", "hr", "weight_kg", "bnp",
        "hosp_event", "death_event",
    }
    assert expected == set(ts.columns)
    assert ts["month"].between(1, 12).all()


def test_size_upper_bound():
    cohort = _cohort(n=50)
    ts = generate_time_series(cohort, months=6, seed=8)
    assert len(ts) <= 50 * 6


def test_no_rows_after_death_event():
    cohort = _cohort(n=200, seed=61)
    ts = generate_time_series(cohort, months=12, seed=9)
    for pid, group in ts.groupby("patient_id"):
        deaths = group[group["death_event"] == 1]
        if len(deaths):
            death_month = deaths["month"].min()
            later = group[group["month"] > death_month]
            assert later.empty, (
                f"Patient {pid} has rows after death_event (month {death_month})"
            )


def test_reproducibility():
    cohort = _cohort(n=50)
    ts1 = generate_time_series(cohort, months=12, seed=123)
    ts2 = generate_time_series(cohort, months=12, seed=123)
    pd.testing.assert_frame_equal(ts1, ts2)


def test_vitals_mean_near_baseline():
    cohort = _cohort(n=500, seed=71)
    ts = generate_time_series(cohort, months=12, seed=11)
    merged = ts.merge(
        cohort[["patient_id", "sbp", "dbp", "hr"]].rename(
            columns={"sbp": "sbp_b", "dbp": "dbp_b", "hr": "hr_b"}
        ),
        on="patient_id",
    )
    assert abs((merged["sbp"] - merged["sbp_b"]).mean()) < 2.0
    assert abs((merged["dbp"] - merged["dbp_b"]).mean()) < 2.0
    assert abs((merged["hr"] - merged["hr_b"]).mean()) < 2.0


def test_month_rates_compound_to_annual():
    cohort = _cohort(n=3000, seed=81)
    ts = generate_time_series(cohort, months=12, seed=13)
    observed_death_frac = (
        ts.groupby("patient_id")["death_event"].max().mean()
    )
    observed_hosp_frac = (
        ts.groupby("patient_id")["hosp_event"].max().mean()
    )
    # Expected pooled rate is roughly the cohort-weighted mean of tier rates.
    expected_death = cohort["mortality_1yr"].mean()
    expected_hosp = cohort["hospitalization_1yr"].mean()
    assert abs(observed_death_frac - expected_death) < 0.05
    assert abs(observed_hosp_frac - expected_hosp) < 0.10


def test_missing_tier_raises():
    cohort = _cohort(n=10)
    bad = cohort.drop(columns=["heartland_risk_tier"])
    with pytest.raises(KeyError):
        generate_time_series(bad, months=6, seed=1)


def test_invalid_months_raises():
    cohort = _cohort(n=10)
    with pytest.raises(ValueError):
        generate_time_series(cohort, months=0, seed=1)
