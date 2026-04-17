"""Top-level cohort generation orchestrator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from heartland_synthetic._rng import make_rng
from heartland_synthetic.clinical import sample_clinical
from heartland_synthetic.comorbid import sample_comorbidities
from heartland_synthetic.config import HeartlandCohortConfig
from heartland_synthetic.demographics import sample_demographics
from heartland_synthetic.gdmt import sample_gdmt
from heartland_synthetic.outcomes import sample_outcomes
from heartland_synthetic.registries import PRIOR_HF_HOSP_P
from heartland_synthetic.rural import sample_rural_variables
from heartland_synthetic.scoring import apply_heartland_scoring


OUTPUT_COLUMNS = [
    "patient_id",
    "age",
    "sex",
    "race",
    "state",
    "county_fips",
    "rural_urban_code",
    "hf_type",
    "lvef",
    "egfr",
    "bnp",
    "sbp",
    "dbp",
    "hr",
    "bmi",
    "diabetes",
    "af",
    "ckd_stage",
    "ckm_stage",
    "distance_to_cardiology_mi",
    "social_support_score",
    "prior_hf_hosp_6mo",
    "on_acei_arb_arni",
    "on_beta_blocker",
    "on_mra",
    "on_sglt2i",
    "gdmt_classes_count",
    "heartland_risk_score",
    "heartland_risk_tier",
]


def generate_cohort(config: HeartlandCohortConfig) -> pd.DataFrame:
    """Generate a synthetic HEARTLAND cohort DataFrame.

    Parameters
    ----------
    config:
        :class:`HeartlandCohortConfig` with cohort-level parameters.

    Returns
    -------
    pandas.DataFrame
        One row per patient with the columns listed in :data:`OUTPUT_COLUMNS`.
    """
    rng = make_rng(config.seed)

    demo = sample_demographics(
        n=config.n_patients,
        age_range=config.age_range,
        rural_fraction=config.rural_fraction,
        female_fraction=config.female_fraction,
        rng=rng,
    )
    clinical = sample_clinical(
        demo_df=demo,
        hf_type_distribution=dict(config.hf_type_distribution),
        rng=rng,
    )

    merged = pd.concat([demo.reset_index(drop=True), clinical.reset_index(drop=True)], axis=1)

    comorbid = sample_comorbidities(merged, rng)
    merged = pd.concat([merged, comorbid.reset_index(drop=True)], axis=1)

    rural = sample_rural_variables(merged, rng)
    merged = pd.concat([merged, rural.reset_index(drop=True)], axis=1)

    prior_hosp = (rng.random(len(merged)) < PRIOR_HF_HOSP_P).astype(int)
    merged["prior_hf_hosp_6mo"] = prior_hosp

    if config.include_medications:
        gdmt = sample_gdmt(merged, rng)
        merged = pd.concat([merged, gdmt.reset_index(drop=True)], axis=1)
    else:
        for col in (
            "on_acei_arb_arni",
            "on_beta_blocker",
            "on_mra",
            "on_sglt2i",
            "gdmt_classes_count",
        ):
            merged[col] = 0

    scored = apply_heartland_scoring(merged)

    output_cols = list(OUTPUT_COLUMNS)
    if config.include_outcomes:
        outcomes = sample_outcomes(scored, rng)
        scored = pd.concat(
            [scored.reset_index(drop=True), outcomes.reset_index(drop=True)],
            axis=1,
        )
        output_cols = output_cols + ["mortality_1yr", "hospitalization_1yr"]

    # Drop internal-only column before returning
    scored = scored.drop(columns=["is_rural"])

    # Reorder / select final output columns
    return scored[output_cols].copy()


__all__ = ["generate_cohort", "OUTPUT_COLUMNS"]
