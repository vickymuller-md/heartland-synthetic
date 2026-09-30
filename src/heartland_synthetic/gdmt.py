"""GDMT utilization: ACEi/ARB/ARNI, beta-blocker, MRA, SGLT2i.

Per-class Bernoulli rates are assumptions with CHAMP-HF as background context,
not fitted estimates. Class flags do not identify a drug, dose, indication,
contraindication assessment, treatment plan, or care delivered.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from heartland_synthetic.registries import GDMT_RATES, SGLT2I_EGFR_MIN


def sample_gdmt(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Return on_acei_arb_arni, on_beta_blocker, on_mra, on_sglt2i, gdmt_classes_count.

    Requires columns: is_rural, egfr.
    """
    n = len(df)
    is_rural = df["is_rural"].to_numpy()
    egfr = df["egfr"].to_numpy()

    def draw(key: str) -> np.ndarray:
        p = np.where(
            is_rural,
            GDMT_RATES["rural"][key],
            GDMT_RATES["urban"][key],
        )
        return (rng.random(n) < p).astype(int)

    acei = draw("acei_arb_arni")
    bb = draw("beta_blocker")
    mra = draw("mra")
    sglt2 = draw("sglt2i")

    # Legacy simulation override only; not a clinical contraindication rule.
    sglt2[egfr < SGLT2I_EGFR_MIN] = 0

    counts = acei + bb + mra + sglt2

    return pd.DataFrame(
        {
            "on_acei_arb_arni": acei,
            "on_beta_blocker": bb,
            "on_mra": mra,
            "on_sglt2i": sglt2,
            "gdmt_classes_count": counts,
        }
    )


__all__ = ["sample_gdmt"]
