"""Reproducible random-number-generator factory."""

from __future__ import annotations

import numpy as np


def make_rng(seed: int | None) -> np.random.Generator:
    """Return a numpy Generator. ``seed=None`` yields OS-entropy randomness."""
    return np.random.default_rng(seed)
