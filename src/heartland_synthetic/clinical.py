"""Clinical vitals via Gaussian copula + HF-type-conditional marginals.

The copula captures joint dependence across seven continuous vitals
[lvef, egfr, bnp, sbp, dbp, hr, bmi]. Each marginal is applied in its own
distribution keyed on hf_type / age so stratified means stay correct.
DBP is reconstructed from SBP post-copula (kept in the 7-dim structure with a
reduced effective coupling).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm, truncnorm

from heartland_synthetic.registries import (
    BMI_CLIP,
    BMI_HFPEF_SHIFT,
    BMI_MEAN,
    BMI_SD,
    BNP_HFPEF_MULTIPLIER,
    BNP_LOG_MEAN,
    BNP_LOG_SD,
    CORR_VITALS,
    DBP_CLIP,
    DBP_NOISE_SD,
    DBP_SBP_COEF,
    EGFR_CLIP,
    EGFR_ELDERLY_SHIFT,
    EGFR_LOG_MEAN,
    EGFR_LOG_SD,
    HR_CLIP,
    HR_MEAN,
    HR_SD,
    LVEF_PARAMS,
    SBP_CLIP,
    SBP_MEAN,
    SBP_RURAL_SHIFT,
    SBP_SD,
    VITALS_ORDER,
)


def _validate_corr(R: np.ndarray) -> np.ndarray:
    R = np.asarray(R, dtype=float)
    d = len(VITALS_ORDER)
    if R.shape != (d, d):
        raise ValueError(f"CORR_VITALS must be {d}x{d}; got {R.shape}")
    if not np.allclose(R, R.T, atol=1e-8):
        raise ValueError("CORR_VITALS must be symmetric")
    eigvals = np.linalg.eigvalsh(R)
    if eigvals.min() <= 0:
        raise ValueError(
            f"CORR_VITALS is not positive definite (min eigenvalue={eigvals.min():.3g})"
        )
    return R


_R = _validate_corr(np.array(CORR_VITALS))
_D = len(VITALS_ORDER)


def _copula_uniforms(n: int, rng: np.random.Generator) -> np.ndarray:
    """Sample n rows from an N(0, R) copula and return uniform marginals.

    Returns array of shape (n, len(VITALS_ORDER)) in VITALS_ORDER order.
    """
    z = rng.multivariate_normal(mean=np.zeros(_D), cov=_R, size=n)
    return norm.cdf(z)


def _inverse_lvef(u: np.ndarray, hf_types: np.ndarray) -> np.ndarray:
    """Inverse CDF mapping per HF stratum."""
    out = np.empty_like(u, dtype=float)
    for hf, params in LVEF_PARAMS.items():
        mask = hf_types == hf
        if not mask.any():
            continue
        u_sub = u[mask]
        if hf == "hfmref":
            out[mask] = params["lo"] + u_sub * (params["hi"] - params["lo"])
        else:
            mean = params["mean"]
            sd = params["sd"]
            lo = params["lo"]
            hi = params["hi"]
            a = (lo - mean) / sd
            b = (hi - mean) / sd
            out[mask] = truncnorm.ppf(u_sub, a, b, loc=mean, scale=sd)
    return out


def _inverse_egfr(u: np.ndarray, ages: np.ndarray) -> np.ndarray:
    raw = np.exp(norm.ppf(u, loc=EGFR_LOG_MEAN, scale=EGFR_LOG_SD))
    elderly = ages >= 75
    raw[elderly] = raw[elderly] + EGFR_ELDERLY_SHIFT
    return np.clip(raw, EGFR_CLIP[0], EGFR_CLIP[1])


def _inverse_bnp(u: np.ndarray, hf_types: np.ndarray) -> np.ndarray:
    raw = np.exp(norm.ppf(u, loc=BNP_LOG_MEAN, scale=BNP_LOG_SD))
    hfpef_mask = hf_types == "hfpef"
    raw[hfpef_mask] = raw[hfpef_mask] * BNP_HFPEF_MULTIPLIER
    # Clip for numerical stability
    return np.clip(raw, 10.0, 30000.0)


def _inverse_sbp(u: np.ndarray, is_rural: np.ndarray) -> np.ndarray:
    raw = norm.ppf(u, loc=SBP_MEAN, scale=SBP_SD)
    raw[is_rural] = raw[is_rural] + SBP_RURAL_SHIFT
    return np.clip(raw, SBP_CLIP[0], SBP_CLIP[1])


def _inverse_hr(u: np.ndarray) -> np.ndarray:
    raw = norm.ppf(u, loc=HR_MEAN, scale=HR_SD)
    return np.clip(raw, HR_CLIP[0], HR_CLIP[1])


def _inverse_bmi(u: np.ndarray, hf_types: np.ndarray) -> np.ndarray:
    raw = norm.ppf(u, loc=BMI_MEAN, scale=BMI_SD)
    hfpef_mask = hf_types == "hfpef"
    raw[hfpef_mask] = raw[hfpef_mask] + BMI_HFPEF_SHIFT
    return np.clip(raw, BMI_CLIP[0], BMI_CLIP[1])


def _sample_hf_types(
    n: int, mix: dict[str, float], rng: np.random.Generator
) -> np.ndarray:
    categories = list(mix.keys())
    probs = np.array([mix[c] for c in categories], dtype=float)
    probs = probs / probs.sum()
    return rng.choice(categories, size=n, p=probs)


def sample_clinical(
    demo_df: pd.DataFrame,
    hf_type_distribution: dict[str, float],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Return clinical variables aligned to ``demo_df``.

    Output columns: hf_type, lvef, egfr, bnp, sbp, dbp, hr, bmi.
    """
    n = len(demo_df)
    ages = demo_df["age"].to_numpy()
    is_rural = demo_df["is_rural"].to_numpy()

    hf_types = _sample_hf_types(n, hf_type_distribution, rng)

    u = _copula_uniforms(n, rng)  # (n, 6) in VITALS_ORDER

    assert VITALS_ORDER == ["lvef", "egfr", "bnp", "sbp", "hr", "bmi"]

    lvef = _inverse_lvef(u[:, 0], hf_types)
    egfr = _inverse_egfr(u[:, 1], ages)
    bnp = _inverse_bnp(u[:, 2], hf_types)
    sbp = _inverse_sbp(u[:, 3], is_rural)
    hr = _inverse_hr(u[:, 4])
    bmi = _inverse_bmi(u[:, 5], hf_types)

    # DBP: derived from SBP + independent Gaussian noise (clinically ~0.65 corr).
    dbp_noise = rng.normal(0.0, DBP_NOISE_SD, size=n)
    dbp = DBP_SBP_COEF * sbp + dbp_noise
    dbp = np.clip(dbp, DBP_CLIP[0], DBP_CLIP[1])

    return pd.DataFrame(
        {
            "hf_type": hf_types,
            "lvef": np.round(lvef, 1),
            "egfr": np.round(egfr, 1),
            "bnp": np.round(bnp, 0),
            "sbp": np.round(sbp, 0).astype(int),
            "dbp": np.round(dbp, 0).astype(int),
            "hr": np.round(hr, 0).astype(int),
            "bmi": np.round(bmi, 1),
        }
    )


__all__ = ["sample_clinical"]
