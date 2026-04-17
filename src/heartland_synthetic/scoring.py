"""HEARTLAND Risk Score engine.

Port of ``heartland-app/lib/risk-score/engine.ts`` (Protocol v3.3 Table 1).
Maximum possible score: 18. Tier cutoffs: low 0-4, moderate 5-8, high >= 9.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

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
    if score <= 4:
        return "low"
    if score <= 8:
        return "moderate"
    return "high"


def compute_row_score(row: Mapping) -> int:
    """Sum HEARTLAND points for a single patient record."""
    return int(sum(v.points for v in RISK_VARIABLES if v.predicate(row)))


def apply_heartland_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with ``heartland_risk_score`` and
    ``heartland_risk_tier`` columns appended.

    The input frame must contain the columns referenced by each
    :data:`RISK_VARIABLES` predicate.
    """
    required = {
        "age",
        "prior_hf_hosp_6mo",
        "egfr",
        "bnp",
        "sbp",
        "diabetes",
        "lvef",
        "ckm_stage",
        "distance_to_cardiology_mi",
        "social_support_score",
    }
    missing = required - set(df.columns)
    if missing:
        raise KeyError(
            f"apply_heartland_scoring: missing required columns: {sorted(missing)}"
        )

    scores = df.apply(compute_row_score, axis=1).astype(int)
    out = df.copy()
    out["heartland_risk_score"] = scores
    out["heartland_risk_tier"] = scores.map(classify_tier)
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
