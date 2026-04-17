"""Reproducibility: same seed must produce identical DataFrames."""

from __future__ import annotations

import pandas as pd

from heartland_synthetic import HeartlandCohortConfig, generate_cohort


def test_same_seed_identical_cohorts():
    cfg = HeartlandCohortConfig(n_patients=200, seed=42)
    df1 = generate_cohort(cfg)
    df2 = generate_cohort(cfg)
    pd.testing.assert_frame_equal(df1, df2)


def test_different_seeds_differ():
    df1 = generate_cohort(HeartlandCohortConfig(n_patients=200, seed=1))
    df2 = generate_cohort(HeartlandCohortConfig(n_patients=200, seed=2))
    # At minimum, heartland_risk_score vectors should differ
    assert not df1["heartland_risk_score"].equals(df2["heartland_risk_score"])


def test_seed_none_differs_across_calls():
    df1 = generate_cohort(HeartlandCohortConfig(n_patients=200, seed=None))
    df2 = generate_cohort(HeartlandCohortConfig(n_patients=200, seed=None))
    assert not df1.equals(df2)
