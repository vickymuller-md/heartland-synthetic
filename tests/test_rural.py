"""Rural variable behavior."""

from __future__ import annotations

import numpy as np
from scipy.stats import ttest_ind

from heartland_synthetic import HeartlandCohortConfig, generate_cohort


def test_rural_fraction_honored():
    cfg = HeartlandCohortConfig(n_patients=1_000, rural_fraction=0.7, seed=11)
    df = generate_cohort(cfg)
    rural_share = (df["rural_urban_code"] >= 4).mean()
    assert 0.65 < rural_share < 0.75


def test_urban_fraction_honored():
    cfg = HeartlandCohortConfig(n_patients=1_000, rural_fraction=0.1, seed=12)
    df = generate_cohort(cfg)
    rural_share = (df["rural_urban_code"] >= 4).mean()
    assert 0.06 < rural_share < 0.14


def test_rural_distance_greater_than_urban():
    cfg = HeartlandCohortConfig(n_patients=2_000, rural_fraction=0.5, seed=13)
    df = generate_cohort(cfg)
    rural_dist = df.loc[df["rural_urban_code"] >= 4, "distance_to_cardiology_mi"]
    urban_dist = df.loc[df["rural_urban_code"] <= 3, "distance_to_cardiology_mi"]
    assert rural_dist.mean() > urban_dist.mean()
    stat, p = ttest_ind(rural_dist, urban_dist, equal_var=False)
    assert p < 1e-6


def test_essi_score_range():
    cfg = HeartlandCohortConfig(n_patients=1_000, seed=14)
    df = generate_cohort(cfg)
    assert df["social_support_score"].between(8, 40).all()


def test_rural_essi_lower_than_urban():
    cfg = HeartlandCohortConfig(n_patients=2_000, rural_fraction=0.5, seed=15)
    df = generate_cohort(cfg)
    rural = df.loc[df["rural_urban_code"] >= 4, "social_support_score"]
    urban = df.loc[df["rural_urban_code"] <= 3, "social_support_score"]
    assert rural.mean() < urban.mean()
