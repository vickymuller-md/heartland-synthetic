"""Monthly time-series generator.

Produces long-format per-patient vitals and events using an AR(1)
mean-reverting model around each patient's baseline. Rows after a
``death_event=1`` are omitted (ragged long format).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from heartland_synthetic._rng import make_rng
from heartland_synthetic.registries import (
    OUTCOME_RATES,
    TIMESERIES_PARAMS,
)


_TS_COLUMNS = [
    "patient_id",
    "month",
    "sbp",
    "dbp",
    "hr",
    "weight_kg",
    "bnp",
    "hosp_event",
    "death_event",
]


def _baseline_weights(
    bmi: np.ndarray, sex: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Derive weight (kg) from BMI and a random height (by sex)."""
    height_mean = np.array(
        [TIMESERIES_PARAMS["height_mean_m"][s] for s in sex]
    )
    height_sd = TIMESERIES_PARAMS["height_sd_m"]
    height_m = rng.normal(height_mean, height_sd, size=len(bmi))
    height_m = np.clip(height_m, 1.40, 2.10)
    return bmi * (height_m ** 2)


def _resolve_annual_rates(cohort: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Return per-patient (mortality_1yr, hosp_1yr) probabilities.

    If the cohort has outcome columns, use them (binary → collapse to tier
    rate so compounding stays stable). Otherwise fall back to tier-indexed
    :data:`OUTCOME_RATES`.
    """
    if "heartland_risk_tier" not in cohort.columns:
        raise KeyError(
            "generate_time_series: cohort must include 'heartland_risk_tier'"
        )
    tiers = cohort["heartland_risk_tier"].to_numpy()
    mortality = np.array([OUTCOME_RATES[t]["mortality_1yr"] for t in tiers])
    hosp = np.array([OUTCOME_RATES[t]["hospitalization_1yr"] for t in tiers])
    return mortality, hosp


def generate_time_series(
    cohort: pd.DataFrame,
    months: int = 12,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate monthly vitals and events for each patient.

    Parameters
    ----------
    cohort:
        DataFrame returned by :func:`generate_cohort` (must include at minimum
        patient_id, sex, bmi, sbp, dbp, hr, bnp, heartland_risk_tier).
    months:
        Number of monthly observations per patient (default 12).
    seed:
        Optional seed (otherwise OS entropy).

    Returns
    -------
    pandas.DataFrame
        Long-format DataFrame with columns listed in :data:`_TS_COLUMNS`.
        Rows after a patient's first ``death_event=1`` are omitted.
    """
    if months <= 0:
        raise ValueError("months must be a positive integer")

    required = {"patient_id", "sex", "bmi", "sbp", "dbp", "hr", "bnp",
                "heartland_risk_tier"}
    missing = required - set(cohort.columns)
    if missing:
        raise KeyError(
            f"generate_time_series: cohort missing columns: {sorted(missing)}"
        )

    rng = make_rng(seed)
    n = len(cohort)

    phi = TIMESERIES_PARAMS["phi"]
    sigma_sbp = TIMESERIES_PARAMS["sigma_sbp"]
    sigma_dbp = TIMESERIES_PARAMS["sigma_dbp"]
    sigma_hr = TIMESERIES_PARAMS["sigma_hr"]
    sigma_weight = TIMESERIES_PARAMS["sigma_weight_kg"]
    sigma_log_bnp = TIMESERIES_PARAMS["sigma_log_bnp"]

    baseline_sbp = cohort["sbp"].to_numpy(dtype=float)
    baseline_dbp = cohort["dbp"].to_numpy(dtype=float)
    baseline_hr = cohort["hr"].to_numpy(dtype=float)
    baseline_bnp = np.maximum(cohort["bnp"].to_numpy(dtype=float), 1.0)
    baseline_log_bnp = np.log(baseline_bnp)
    baseline_weight = _baseline_weights(
        cohort["bmi"].to_numpy(dtype=float),
        cohort["sex"].to_numpy(),
        rng,
    )

    mortality_1yr, hosp_1yr = _resolve_annual_rates(cohort)
    # Convert annual rate r to per-month p such that (1-p)^12 = (1-r).
    p_death_m = 1 - (1 - mortality_1yr) ** (1 / 12)
    p_hosp_m = 1 - (1 - hosp_1yr) ** (1 / 12)

    # State variables (start at baseline).
    sbp = baseline_sbp.copy()
    dbp = baseline_dbp.copy()
    hr = baseline_hr.copy()
    weight = baseline_weight.copy()
    log_bnp = baseline_log_bnp.copy()

    alive = np.ones(n, dtype=bool)
    patient_ids = cohort["patient_id"].to_numpy()

    rows: list[dict] = []
    for m in range(1, months + 1):
        # AR(1) updates only for still-alive patients.
        idx = np.where(alive)[0]
        if len(idx) == 0:
            break

        sbp[idx] = (
            baseline_sbp[idx]
            + phi * (sbp[idx] - baseline_sbp[idx])
            + rng.normal(0, sigma_sbp, size=len(idx))
        )
        dbp[idx] = (
            baseline_dbp[idx]
            + phi * (dbp[idx] - baseline_dbp[idx])
            + rng.normal(0, sigma_dbp, size=len(idx))
        )
        hr[idx] = (
            baseline_hr[idx]
            + phi * (hr[idx] - baseline_hr[idx])
            + rng.normal(0, sigma_hr, size=len(idx))
        )
        weight[idx] = (
            baseline_weight[idx]
            + phi * (weight[idx] - baseline_weight[idx])
            + rng.normal(0, sigma_weight, size=len(idx))
        )
        log_bnp[idx] = (
            baseline_log_bnp[idx]
            + phi * (log_bnp[idx] - baseline_log_bnp[idx])
            + rng.normal(0, sigma_log_bnp, size=len(idx))
        )

        hosp_event = np.zeros(n, dtype=int)
        death_event = np.zeros(n, dtype=int)
        hosp_event[idx] = (rng.random(len(idx)) < p_hosp_m[idx]).astype(int)
        death_event[idx] = (rng.random(len(idx)) < p_death_m[idx]).astype(int)

        for i in idx:
            rows.append({
                "patient_id": patient_ids[i],
                "month": m,
                "sbp": round(float(sbp[i]), 1),
                "dbp": round(float(dbp[i]), 1),
                "hr": round(float(hr[i]), 1),
                "weight_kg": round(float(weight[i]), 2),
                "bnp": round(float(np.exp(log_bnp[i])), 1),
                "hosp_event": int(hosp_event[i]),
                "death_event": int(death_event[i]),
            })

        # Mark dead patients; they do not appear in subsequent months.
        alive[idx] = ~death_event[idx].astype(bool)

    return pd.DataFrame(rows, columns=_TS_COLUMNS)


__all__ = ["generate_time_series"]
