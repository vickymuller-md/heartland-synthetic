"""Demographic sampling: age, sex, race, state, county_fips, RUCA."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import truncnorm

from heartland_synthetic.registries import (
    AGE_MEAN,
    AGE_SD,
    RACE_DISTRIBUTION,
    RURAL_HEAVY_STATES,
    URBAN_HEAVY_STATES,
)


def _truncnorm_sample(
    n: int, mean: float, sd: float, lo: float, hi: float, rng: np.random.Generator
) -> np.ndarray:
    a = (lo - mean) / sd
    b = (hi - mean) / sd
    return truncnorm.rvs(a, b, loc=mean, scale=sd, size=n, random_state=rng)


def sample_demographics(
    n: int,
    age_range: tuple[int, int],
    rural_fraction: float,
    female_fraction: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Return a demographics DataFrame of length ``n``.

    Columns: patient_id, age, sex, race, state, county_fips, rural_urban_code,
    is_rural.
    """
    lo, hi = age_range
    ages = _truncnorm_sample(n, AGE_MEAN, AGE_SD, lo, hi, rng).round().astype(int)

    sexes = np.where(rng.random(n) < female_fraction, "F", "M")

    race_categories = list(RACE_DISTRIBUTION.keys())
    race_probs = np.array(list(RACE_DISTRIBUTION.values()))
    race_probs = race_probs / race_probs.sum()
    races = rng.choice(race_categories, size=n, p=race_probs)

    # Rural assignment
    n_rural = int(round(n * rural_fraction))
    is_rural = np.zeros(n, dtype=bool)
    if n_rural > 0:
        rural_idx = rng.choice(n, size=n_rural, replace=False)
        is_rural[rural_idx] = True

    # State: rural patients drawn from rural-heavy pool, urban from urban pool.
    states = np.empty(n, dtype=object)
    states[is_rural] = rng.choice(RURAL_HEAVY_STATES, size=is_rural.sum())
    states[~is_rural] = rng.choice(URBAN_HEAVY_STATES, size=(~is_rural).sum())

    # USDA RUCA codes: 1-3 urban, 4-10 rural.
    urban_ruca = np.array([1, 2, 3])
    rural_ruca = np.array([4, 5, 6, 7, 8, 9, 10])
    ruca = np.empty(n, dtype=int)
    ruca[is_rural] = rng.choice(rural_ruca, size=is_rural.sum())
    ruca[~is_rural] = rng.choice(urban_ruca, size=(~is_rural).sum())

    # Synthetic county_fips: 2-digit state pseudo-code + 3-digit county
    # (not a real FIPS mapping; documented as synthetic).
    county_suffix = rng.integers(1, 999, size=n)
    state_prefix = {s: f"{10 + i:02d}" for i, s in enumerate(
        sorted(set(list(RURAL_HEAVY_STATES) + list(URBAN_HEAVY_STATES)))
    )}
    county_fips = np.array(
        [f"{state_prefix[s]}{c:03d}" for s, c in zip(states, county_suffix)]
    )

    patient_ids = np.array([f"HS-{i+1:06d}" for i in range(n)])

    return pd.DataFrame(
        {
            "patient_id": patient_ids,
            "age": ages,
            "sex": sexes,
            "race": races,
            "state": states,
            "county_fips": county_fips,
            "rural_urban_code": ruca,
            "is_rural": is_rural,
        }
    )


__all__ = ["sample_demographics"]
