"""heartland-synthetic — synthetic heart-failure cohort generator.

Generates clinically-realistic HF cohorts including the 10 HEARTLAND risk
variables (distance-to-cardiology, social support) that Synthea does not model.

Public API
----------
- :class:`HeartlandCohortConfig`
- :func:`generate_cohort`
- :func:`generate_time_series`
- :func:`apply_heartland_scoring`
- :func:`classify_tier`
- :func:`export_redcap`
- :func:`export_fhir_bundle`
- :data:`RISK_VARIABLES`
"""

from heartland_synthetic.config import HeartlandCohortConfig
from heartland_synthetic.exports import export_fhir_bundle, export_redcap
from heartland_synthetic.generator import generate_cohort
from heartland_synthetic.scoring import (
    RISK_VARIABLES,
    apply_heartland_scoring,
    classify_tier,
)
from heartland_synthetic.timeseries import generate_time_series

__all__ = [
    "HeartlandCohortConfig",
    "generate_cohort",
    "generate_time_series",
    "apply_heartland_scoring",
    "classify_tier",
    "export_redcap",
    "export_fhir_bundle",
    "RISK_VARIABLES",
]

__version__ = "0.2.0"
