"""1-year outcome model: mortality and hospitalization by HEARTLAND tier."""

from __future__ import annotations

import numpy as np
import pandas as pd

from heartland_synthetic.registries import OUTCOME_RATES


def sample_outcomes(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Return mortality_1yr, hospitalization_1yr aligned to ``df``.

    Rates are tier-indexed Bernoulli draws using :data:`OUTCOME_RATES`.

    Parameters
    ----------
    df:
        DataFrame containing a ``heartland_risk_tier`` column.
    rng:
        Seeded numpy Generator.

    Returns
    -------
    pandas.DataFrame
        Two-column DataFrame with ``mortality_1yr`` and
        ``hospitalization_1yr`` (int 0/1), same index/length as ``df``.
    """
    if "heartland_risk_tier" not in df.columns:
        raise KeyError(
            "sample_outcomes: 'heartland_risk_tier' missing from DataFrame"
        )

    tiers = df["heartland_risk_tier"].to_numpy()
    mortality_p = np.array([OUTCOME_RATES[t]["mortality_1yr"] for t in tiers])
    hosp_p = np.array([OUTCOME_RATES[t]["hospitalization_1yr"] for t in tiers])

    mortality = (rng.random(len(df)) < mortality_p).astype(int)
    hosp = (rng.random(len(df)) < hosp_p).astype(int)

    return pd.DataFrame(
        {"mortality_1yr": mortality, "hospitalization_1yr": hosp},
        index=df.index,
    )


__all__ = ["sample_outcomes"]
