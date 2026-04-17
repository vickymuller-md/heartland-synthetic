"""Configuration dataclass for cohort generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


DEFAULT_HF_TYPES: dict[str, float] = {
    "hfref": 0.45,
    "hfmref": 0.15,
    "hfpef": 0.40,
}


@dataclass(frozen=True)
class HeartlandCohortConfig:
    """Parameters for :func:`heartland_synthetic.generate_cohort`.

    Attributes
    ----------
    n_patients:
        Number of synthetic patients to generate. Must be > 0.
    rural_fraction:
        Share of cohort assigned USDA RUCA code >= 4 (rural). 0.0 to 1.0.
    hf_type_distribution:
        Mix of HFrEF / HFmrEF / HFpEF. Values must sum to 1.0.
    age_range:
        Inclusive min/max age. Must satisfy ``min < max``.
    female_fraction:
        Share of female patients. 0.0 to 1.0.
    include_outcomes:
        If True, attach ``mortality_1yr`` and ``hospitalization_1yr`` columns.
        Honored in Session 2; currently ignored.
    include_medications:
        If True, attach GDMT utilization columns.
    seed:
        Integer seed for reproducibility. ``None`` draws from OS entropy.
    """

    n_patients: int = 500
    rural_fraction: float = 0.5
    hf_type_distribution: Mapping[str, float] = field(
        default_factory=lambda: dict(DEFAULT_HF_TYPES)
    )
    age_range: tuple[int, int] = (45, 95)
    female_fraction: float = 0.48
    include_outcomes: bool = True
    include_medications: bool = True
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.n_patients <= 0:
            raise ValueError("n_patients must be a positive integer")

        if not (0.0 <= self.rural_fraction <= 1.0):
            raise ValueError("rural_fraction must be in [0, 1]")

        if not (0.0 <= self.female_fraction <= 1.0):
            raise ValueError("female_fraction must be in [0, 1]")

        if set(self.hf_type_distribution.keys()) != {"hfref", "hfmref", "hfpef"}:
            raise ValueError(
                "hf_type_distribution must contain exactly keys "
                "{'hfref', 'hfmref', 'hfpef'}"
            )
        total = sum(self.hf_type_distribution.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"hf_type_distribution values must sum to 1.0, got {total:.6f}"
            )
        for k, v in self.hf_type_distribution.items():
            if v < 0:
                raise ValueError(f"hf_type_distribution[{k!r}] must be >= 0")

        lo, hi = self.age_range
        if lo >= hi:
            raise ValueError("age_range must satisfy min < max")
        if lo < 18:
            raise ValueError("age_range minimum must be >= 18 (adult cohort)")
