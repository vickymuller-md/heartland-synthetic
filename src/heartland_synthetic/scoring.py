"""HEARTLAND Risk Score engine.

Weights from ``heartland-app/lib/risk-score/engine.ts`` (Protocol v3.3 Table 1).
Maximum possible score: 18. Tier cutoffs: low 0-4, moderate 5-8, high >= 9.
The numeric adapter uses BNP only and the existing synthetic social-support
proxy; it is not an ESSI implementation or a clinical plausibility check.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Integral
from typing import Callable, Mapping

import numpy as np
import pandas as pd

from heartland_synthetic.registries import ESSI_LIMITED_CUTOFF


Predicate = Callable[[Mapping], bool]


@dataclass(frozen=True)
class RiskVariable:
    key: str
    label: str
    points: int
    category: str
    predicate: Predicate


# 10 HEARTLAND variables — order matches the protocol table.
RISK_VARIABLES: list[RiskVariable] = [
    RiskVariable(
        key="age_over_75",
        label="Age >= 75 years",
        points=2,
        category="Clinical",
        predicate=lambda r: bool(r["age"] >= 75),
    ),
    RiskVariable(
        key="prior_hf_hosp_6mo",
        label="Prior HF hospitalization within 6 months",
        points=3,
        category="Clinical",
        predicate=lambda r: bool(r["prior_hf_hosp_6mo"]),
    ),
    RiskVariable(
        key="egfr_below_45",
        label="eGFR <45 mL/min/1.73m^2",
        points=2,
        category="Laboratory",
        predicate=lambda r: bool(r["egfr"] < 45),
    ),
    RiskVariable(
        key="elevated_natriuretic",
        label="BNP >=500 pg/mL",
        points=2,
        category="Laboratory",
        predicate=lambda r: bool(r["bnp"] >= 500),
    ),
    RiskVariable(
        key="sbp_below_100",
        label="SBP <100 mmHg at admission",
        points=2,
        category="Clinical",
        predicate=lambda r: bool(r["sbp"] < 100),
    ),
    RiskVariable(
        key="diabetes",
        label="Diabetes mellitus",
        points=1,
        category="Comorbidity",
        predicate=lambda r: bool(r["diabetes"]),
    ),
    RiskVariable(
        key="lvef_below_30",
        label="LVEF <30%",
        points=2,
        category="Cardiac",
        predicate=lambda r: bool(r["lvef"] < 30),
    ),
    RiskVariable(
        key="ckm_stage_3_or_4",
        label="CKM Stage 3 or 4",
        points=2,
        category="Comorbidity",
        predicate=lambda r: int(r["ckm_stage"]) in (3, 4),
    ),
    RiskVariable(
        key="distance_over_50_miles",
        label="Distance to cardiology >50 miles",
        points=1,
        category="Social/Geographic",
        predicate=lambda r: bool(r["distance_to_cardiology_mi"] > 50),
    ),
    RiskVariable(
        key="limited_social_support",
        label="Lives alone or limited social support",
        points=1,
        category="Social/Geographic",
        predicate=lambda r: bool(r["social_support_score"] < ESSI_LIMITED_CUTOFF),
    ),
]

MAX_SCORE: int = sum(v.points for v in RISK_VARIABLES)  # == 18

TIER_CUTOFFS = {"low": (0, 4), "moderate": (5, 8), "high": (9, 18)}

_REQUIRED_COLUMNS = (
    "age", "prior_hf_hosp_6mo", "egfr", "bnp", "sbp", "diabetes", "lvef",
    "ckm_stage", "distance_to_cardiology_mi", "social_support_score",
)
_BINARY_COLUMNS = {"prior_hf_hosp_6mo", "diabetes"}


def _finite_real(value: object) -> bool:
    # bool subclasses int; accepting it as a measurement would silently score it.
    # NumPy durations inherit Integral too, including the missing NaT sentinel.
    if isinstance(value, (bool, np.bool_, np.timedelta64, np.datetime64)):
        return False
    if isinstance(value, Integral):
        return True
    if isinstance(value, np.floating):
        return bool(np.isfinite(value))
    if isinstance(value, float):
        return isfinite(value)
    return False


def _validate_row(row: Mapping | pd.Series) -> None:
    if not isinstance(row, (Mapping, pd.Series)):
        raise TypeError("compute_row_score: expected a mapping or pandas Series")
    if isinstance(row, pd.Series) and row.index.has_duplicates:
        raise ValueError("compute_row_score: duplicate field names are not allowed")
    missing = [name for name in _REQUIRED_COLUMNS if name not in row]
    if missing:
        raise KeyError(f"compute_row_score: missing required columns: {missing}")
    for name in _REQUIRED_COLUMNS:
        value = row[name]
        if name in _BINARY_COLUMNS:
            valid = isinstance(value, (bool, np.bool_)) or (
                _finite_real(value) and value in (0, 1)
            )
            expected = "an explicit boolean or numeric 0/1"
        elif name == "ckm_stage":
            valid = _finite_real(value) and 0 <= value <= 4 and value == int(value)
            expected = "an integer category from 0 to 4"
        else:
            valid = _finite_real(value)
            expected = "a finite real number, not a boolean"
        if not valid:
            # Never include input values or row identifiers in errors.
            raise ValueError(f"compute_row_score: {name} must be {expected}; missing values are not scored")


def classify_tier(score: int) -> str:
    """Return HEARTLAND tier for a numeric score.

    Parameters
    ----------
    score:
        Integer score, 0 to 18.

    Returns
    -------
    str
        One of ``"low"`` (0-4), ``"moderate"`` (5-8), ``"high"`` (>= 9).
    """
    if not (_finite_real(score) and 0 <= score <= MAX_SCORE and score == int(score)):
        raise ValueError("classify_tier: score must be an integer from 0 to 18, not a boolean")
    if score <= 4:
        return "low"
    if score <= 8:
        return "moderate"
    return "high"


def compute_row_score(row: Mapping | pd.Series) -> int:
    """Sum points for one complete synthetic record; invalid inputs raise.

    Validation is structural, not clinical. No missing-value imputation or
    string coercion is performed. Predicates in RISK_VARIABLES are low-level
    definitions and do not independently validate input.
    """
    _validate_row(row)
    return int(sum(v.points for v in RISK_VARIABLES if v.predicate(row)))


def apply_heartland_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with ``heartland_risk_score`` and
    ``heartland_risk_tier`` columns appended.

    All ten required inputs must be complete and structurally valid in every
    row. One invalid row raises before returning a result; the input is never
    mutated. Duplicate column labels are rejected. Extra columns and the index
    (including duplicate labels) are preserved; existing score/tier columns are
    recomputed. An empty frame still requires all ten columns.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("apply_heartland_scoring: expected a pandas DataFrame")
    if df.columns.has_duplicates:
        raise ValueError("apply_heartland_scoring: duplicate column names are not allowed")
    missing = set(_REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise KeyError(
            f"apply_heartland_scoring: missing required columns: {sorted(missing)}"
        )

    # Avoid axis=1 dtype coercion (for example, a boolean becoming numeric).
    scores = [
        compute_row_score(dict(zip(_REQUIRED_COLUMNS, values)))
        for values in df.loc[:, list(_REQUIRED_COLUMNS)].itertuples(index=False, name=None)
    ]
    out = df.copy()
    out["heartland_risk_score"] = pd.Series(scores, index=df.index, dtype="int64")
    out["heartland_risk_tier"] = pd.Series(
        [classify_tier(score) for score in scores], index=df.index, dtype="str"
    )
    return out


__all__ = [
    "RISK_VARIABLES",
    "RiskVariable",
    "MAX_SCORE",
    "TIER_CUTOFFS",
    "classify_tier",
    "compute_row_score",
    "apply_heartland_scoring",
]
