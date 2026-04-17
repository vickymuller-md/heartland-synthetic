"""GDMT utilization behavior vs CHAMP-HF benchmarks."""

from __future__ import annotations

import numpy as np
from scipy.stats import chi2_contingency

from heartland_synthetic import HeartlandCohortConfig, generate_cohort


def test_p_all_four_low():
    cfg = HeartlandCohortConfig(n_patients=5_000, rural_fraction=0.5, seed=21)
    df = generate_cohort(cfg)
    p_all = (df["gdmt_classes_count"] == 4).mean()
    # CHAMP-HF: <1% on quadruple; our calibration aims for ~1-2%.
    assert p_all < 0.03


def test_p_at_least_one_class():
    cfg = HeartlandCohortConfig(n_patients=5_000, rural_fraction=0.5, seed=22)
    df = generate_cohort(cfg)
    p_any = (df["gdmt_classes_count"] >= 1).mean()
    assert p_any > 0.70


def test_rural_vs_urban_gdmt_lower():
    cfg = HeartlandCohortConfig(n_patients=5_000, rural_fraction=0.5, seed=23)
    df = generate_cohort(cfg)

    rural_mean = df.loc[df["rural_urban_code"] >= 4, "gdmt_classes_count"].mean()
    urban_mean = df.loc[df["rural_urban_code"] <= 3, "gdmt_classes_count"].mean()
    assert rural_mean < urban_mean

    # Chi-square on any-GDMT
    contingency = np.array([
        [
            (df["rural_urban_code"] <= 3).sum() - (df.loc[df["rural_urban_code"] <= 3, "gdmt_classes_count"] >= 1).sum(),
            (df.loc[df["rural_urban_code"] <= 3, "gdmt_classes_count"] >= 1).sum(),
        ],
        [
            (df["rural_urban_code"] >= 4).sum() - (df.loc[df["rural_urban_code"] >= 4, "gdmt_classes_count"] >= 1).sum(),
            (df.loc[df["rural_urban_code"] >= 4, "gdmt_classes_count"] >= 1).sum(),
        ],
    ])
    _, p, _, _ = chi2_contingency(contingency)
    assert p < 0.01


def test_sglt2i_contraindicated_below_egfr_20():
    cfg = HeartlandCohortConfig(n_patients=5_000, rural_fraction=0.5, seed=24)
    df = generate_cohort(cfg)
    low_egfr = df[df["egfr"] < 20]
    if len(low_egfr):
        assert (low_egfr["on_sglt2i"] == 0).all()


def test_include_medications_false_yields_zeros():
    cfg = HeartlandCohortConfig(
        n_patients=200, include_medications=False, seed=25
    )
    df = generate_cohort(cfg)
    for col in ("on_acei_arb_arni", "on_beta_blocker", "on_mra", "on_sglt2i", "gdmt_classes_count"):
        assert (df[col] == 0).all()
