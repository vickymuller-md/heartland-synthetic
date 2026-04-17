"""Shared pytest fixtures and tolerance tables."""

from __future__ import annotations

import pytest

from heartland_synthetic import HeartlandCohortConfig, generate_cohort


# Registry-target means for distribution checks. Tolerance is expressed as a
# relative fraction of the target mean, except where noted absolute.
DIST_TARGETS = {
    "age": {"mean": 72.0, "tol_abs": 2.0},
    "bmi": {"mean": 30.0, "tol_abs": 1.0},
    "sbp": {"mean": 127.5, "tol_abs": 3.0},   # rural bias nudges mean slightly up
    "hr": {"mean": 78.0, "tol_abs": 2.0},
    "egfr": {"mean": 60.0, "tol_abs": 5.0},   # elderly shift + clipping
    "lvef_hfref": {"mean": 25.0, "tol_abs": 2.0},
    "lvef_hfpef": {"mean": 60.0, "tol_abs": 2.0},
}


@pytest.fixture(scope="session")
def large_cohort():
    """Single 10,000-patient cohort used across distribution tests."""
    cfg = HeartlandCohortConfig(n_patients=10_000, rural_fraction=0.5, seed=2026)
    return generate_cohort(cfg)
