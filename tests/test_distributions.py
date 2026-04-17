"""Distribution-validation tests on a 10k-patient cohort."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from heartland_synthetic import HeartlandCohortConfig, generate_cohort
from heartland_synthetic.generator import OUTPUT_COLUMNS
from heartland_synthetic.registries import CORR_VITALS, VITALS_ORDER


def test_output_columns(large_cohort: pd.DataFrame):
    # Default config has include_outcomes=True, so the extended schema is expected.
    assert list(large_cohort.columns) == OUTPUT_COLUMNS + [
        "mortality_1yr",
        "hospitalization_1yr",
    ]
    assert len(large_cohort) == 10_000


def test_age_within_range(large_cohort: pd.DataFrame):
    assert large_cohort["age"].between(45, 95).all()


def test_hf_type_proportions(large_cohort: pd.DataFrame):
    props = large_cohort["hf_type"].value_counts(normalize=True).to_dict()
    assert abs(props["hfref"] - 0.45) < 0.03
    assert abs(props["hfmref"] - 0.15) < 0.03
    assert abs(props["hfpef"] - 0.40) < 0.03


def test_lvef_hfref_range(large_cohort: pd.DataFrame):
    hfref = large_cohort[large_cohort["hf_type"] == "hfref"]
    assert hfref["lvef"].between(5, 39).all()
    assert abs(hfref["lvef"].mean() - 25.0) < 2.0


def test_lvef_hfmref_range(large_cohort: pd.DataFrame):
    hfmref = large_cohort[large_cohort["hf_type"] == "hfmref"]
    assert hfmref["lvef"].between(40, 49).all()


def test_lvef_hfpef_range(large_cohort: pd.DataFrame):
    hfpef = large_cohort[large_cohort["hf_type"] == "hfpef"]
    assert hfpef["lvef"].between(50, 75).all()
    assert abs(hfpef["lvef"].mean() - 60.0) < 2.0


def test_egfr_range_and_mean(large_cohort: pd.DataFrame):
    assert large_cohort["egfr"].between(5, 125).all()
    mean = large_cohort["egfr"].mean()
    # Mean shifted downward by elderly cohort; expect ~55-62
    assert 50 < mean < 65


def test_bnp_positive(large_cohort: pd.DataFrame):
    assert (large_cohort["bnp"] > 0).all()


def test_vitals_within_clip(large_cohort: pd.DataFrame):
    assert large_cohort["sbp"].between(80, 210).all()
    assert large_cohort["dbp"].between(40, 125).all()
    assert large_cohort["hr"].between(45, 140).all()
    assert large_cohort["bmi"].between(16, 55).all()


def test_copula_correlations(large_cohort: pd.DataFrame):
    """Spearman correlations of copula vitals should be in ballpark of CORR_VITALS."""
    mat = large_cohort[VITALS_ORDER].to_numpy()
    rho, _ = spearmanr(mat)
    target = np.array(CORR_VITALS)
    d = len(VITALS_ORDER)
    for i in range(d):
        for j in range(i + 1, d):
            assert abs(rho[i, j] - target[i, j]) < 0.20, (
                f"corr[{VITALS_ORDER[i]},{VITALS_ORDER[j]}] = {rho[i, j]:.2f}, "
                f"target {target[i, j]:.2f}"
            )


def test_sbp_dbp_correlation(large_cohort: pd.DataFrame):
    """SBP-DBP Pearson correlation should be near the clinical target (~0.65)."""
    rho = large_cohort[["sbp", "dbp"]].corr(method="pearson").iloc[0, 1]
    assert 0.55 < rho < 0.75, f"SBP-DBP rho={rho:.2f}, target 0.65 +/- 0.10"


def test_tier_distribution_sensible(large_cohort: pd.DataFrame):
    tier_props = large_cohort["heartland_risk_tier"].value_counts(normalize=True)
    # All three tiers should be represented with non-trivial mass.
    assert tier_props.get("low", 0) > 0.10
    assert tier_props.get("moderate", 0) > 0.15
    # High tier is rarer; just require non-zero.
    assert tier_props.get("high", 0) > 0.0
    assert abs(tier_props.sum() - 1.0) < 1e-9


def test_ckd_stage_consistency(large_cohort: pd.DataFrame):
    # Stage 5 requires eGFR < 15
    s5 = large_cohort[large_cohort["ckd_stage"] == 5]
    assert (s5["egfr"] < 15).all() if len(s5) else True
    # Stage 1 requires eGFR >= 90
    s1 = large_cohort[large_cohort["ckd_stage"] == 1]
    assert (s1["egfr"] >= 90).all() if len(s1) else True


def test_sex_fraction(large_cohort: pd.DataFrame):
    f_frac = (large_cohort["sex"] == "F").mean()
    assert 0.44 < f_frac < 0.52


def test_small_cohort_smoke():
    df = generate_cohort(HeartlandCohortConfig(n_patients=50, seed=7))
    assert len(df) == 50
    assert df["heartland_risk_score"].between(0, 18).all()
    assert df["heartland_risk_tier"].isin(["low", "moderate", "high"]).all()
