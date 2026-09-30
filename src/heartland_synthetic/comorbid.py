"""Comorbidities: diabetes, AF, CKD stage (from eGFR), CKM stage."""

from __future__ import annotations

import numpy as np
import pandas as pd

from heartland_synthetic.registries import (
    AF_BASE_P,
    AF_ELDERLY_BUMP,
    DIABETES_BASE_P,
    DIABETES_HFPEF_BUMP,
    DIABETES_OBESITY_BUMP,
    ckd_stage_from_egfr,
)


def _assign_ckm_stage(
    diabetes: np.ndarray,
    ckd_stage: np.ndarray,
    bmi: np.ndarray,
    age: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Legacy synthetic 0-4 category, not clinical AHA CKM staging.

    Uses BMI, diabetes, eGFR-derived category and a random age-based transition.
    In particular, reserving 4 for selected rows in an HF cohort is a simulation
    convention, not a faithful application of the AHA disease-stage definition.
    """
    n = len(diabetes)
    stage = np.zeros(n, dtype=int)

    # Stage 1 baseline: excess adiposity
    stage[bmi >= 25] = 1

    # Stage 2: diabetes OR moderate-severe CKD (stage >= 3)
    stage2_mask = (diabetes.astype(bool)) | (ckd_stage >= 3)
    stage[stage2_mask] = np.maximum(stage[stage2_mask], 2)

    # Simulated category 3: random age-driven transition, not diagnosed disease.
    age_risk = rng.random(n) < np.clip((age - 50) / 50.0, 0.0, 0.8)
    stage3_mask = stage2_mask & age_risk
    stage[stage3_mask] = 3

    # Simulated category 4: legacy rule, not an adjudicated clinical stage.
    stage4_mask = (ckd_stage >= 4) | ((diabetes.astype(bool)) & (ckd_stage >= 3))
    stage[stage4_mask] = 4

    return stage


def sample_comorbidities(
    df: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    """Return diabetes, af, ckd_stage, ckm_stage aligned to ``df``.

    Requires columns: age, hf_type, bmi, egfr.
    """
    n = len(df)
    ages = df["age"].to_numpy()
    hf_types = df["hf_type"].to_numpy()
    bmi = df["bmi"].to_numpy()
    egfr = df["egfr"].to_numpy()

    p_diabetes = np.full(n, DIABETES_BASE_P)
    p_diabetes = p_diabetes + (hf_types == "hfpef") * DIABETES_HFPEF_BUMP
    p_diabetes = p_diabetes + (bmi > 35) * DIABETES_OBESITY_BUMP
    p_diabetes = np.clip(p_diabetes, 0.0, 1.0)
    diabetes = (rng.random(n) < p_diabetes).astype(int)

    p_af = np.full(n, AF_BASE_P) + (ages >= 75) * AF_ELDERLY_BUMP
    p_af = np.clip(p_af, 0.0, 1.0)
    af = (rng.random(n) < p_af).astype(int)

    ckd_stage = np.array([ckd_stage_from_egfr(e) for e in egfr], dtype=int)

    ckm_stage = _assign_ckm_stage(diabetes, ckd_stage, bmi, ages, rng)

    return pd.DataFrame(
        {
            "diabetes": diabetes,
            "af": af,
            "ckd_stage": ckd_stage,
            "ckm_stage": ckm_stage,
        }
    )


__all__ = ["sample_comorbidities"]
