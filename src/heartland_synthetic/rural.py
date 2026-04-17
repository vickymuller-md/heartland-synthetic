"""Rural-specific variables: distance to cardiology, ENRICHD ESSI score."""

from __future__ import annotations

import numpy as np
import pandas as pd

from heartland_synthetic.registries import (
    DISTANCE_CLIP,
    DISTANCE_RURAL_LOG_MEAN,
    DISTANCE_RURAL_LOG_SD,
    DISTANCE_URBAN_LOG_MEAN,
    DISTANCE_URBAN_LOG_SD,
    ESSI_CLIP,
    ESSI_RURAL_MEAN,
    ESSI_RURAL_SD,
    ESSI_URBAN_MEAN,
    ESSI_URBAN_SD,
)


def sample_rural_variables(
    df: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    """Return distance_to_cardiology_mi, social_support_score.

    Requires column: is_rural.
    """
    n = len(df)
    is_rural = df["is_rural"].to_numpy()

    # Distance: log-normal, stratum-specific
    log_mean = np.where(is_rural, DISTANCE_RURAL_LOG_MEAN, DISTANCE_URBAN_LOG_MEAN)
    log_sd = np.where(is_rural, DISTANCE_RURAL_LOG_SD, DISTANCE_URBAN_LOG_SD)
    distance = np.exp(rng.normal(log_mean, log_sd, size=n))
    distance = np.clip(distance, DISTANCE_CLIP[0], DISTANCE_CLIP[1])

    # ENRICHD ESSI: 8 items * 5-pt Likert (range 8-40)
    essi_mean = np.where(is_rural, ESSI_RURAL_MEAN, ESSI_URBAN_MEAN)
    essi_sd = np.where(is_rural, ESSI_RURAL_SD, ESSI_URBAN_SD)
    essi = rng.normal(essi_mean, essi_sd, size=n)
    essi = np.clip(np.round(essi), ESSI_CLIP[0], ESSI_CLIP[1]).astype(int)

    return pd.DataFrame(
        {
            "distance_to_cardiology_mi": np.round(distance, 1),
            "social_support_score": essi,
        }
    )


__all__ = ["sample_rural_variables"]
