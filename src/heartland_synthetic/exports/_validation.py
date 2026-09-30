"""Complete synthetic cohort and output-file guards; no clinical adjudication."""

from __future__ import annotations

from math import isfinite
from numbers import Integral
from pathlib import Path
import re

import numpy as np
import pandas as pd

from heartland_synthetic.generator import OUTPUT_COLUMNS
from heartland_synthetic.registries import FHIR_CODES, REDCAP_BOOLEAN_COLUMNS, REDCAP_CATEGORICALS
from heartland_synthetic.scoring import _finite_real, classify_tier, compute_row_score


_OUTCOMES = {"mortality_1yr", "hospitalization_1yr"}
_MEASURES = {"lvef", "egfr", "bnp", "sbp", "dbp", "hr", "bmi",
             "distance_to_cardiology_mi", "social_support_score"}
_CATEGORIES = {"rural_urban_code": (1, 10), "ckd_stage": (1, 5),
               "ckm_stage": (0, 4), "gdmt_classes_count": (0, 4),
               "heartland_risk_score": (0, 18)}
_MEDICATIONS = ("on_acei_arb_arni", "on_beta_blocker", "on_mra", "on_sglt2i")
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,63}")


def _error(field: str) -> ValueError:
    # All callers supply fixed schema names, never user values/identifiers.
    return ValueError(f"export: invalid or inconsistent {field}")


def _number(value: object, field: str) -> float:
    if not _finite_real(value):
        raise _error(field)
    try:
        converted = float(value)
        if not isfinite(converted):
            raise _error(field)
        # NumPy int == float may coerce before comparing; compare exact integers
        # or ratios instead, including float32/longdouble on supported platforms.
        exact = (converted.is_integer() and int(converted) == int(value)
                 if isinstance(value, Integral)
                 else converted.as_integer_ratio() == value.as_integer_ratio())
    except (OverflowError, TypeError, AttributeError):
        raise _error(field) from None
    if not exact:
        raise _error(field)
    return converted


def validate_cohort(df: pd.DataFrame, *, kind: str) -> pd.DataFrame:
    """Validate all rows without mutation; return a normalized export copy."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("export: expected a pandas DataFrame")
    if df.columns.has_duplicates or any(not isinstance(c, str) for c in df.columns):
        raise ValueError("export: column names must be unique strings")
    required = set(OUTPUT_COLUMNS)
    columns = set(df.columns)
    if required - columns:
        raise KeyError(f"export: missing required columns: {sorted(required - columns)}")
    if columns - required - _OUTCOMES:
        raise ValueError("export: unrecognized columns are not allowed")
    if columns & _OUTCOMES not in (set(), _OUTCOMES):
        raise ValueError("export: annual outcome columns must be supplied together")

    reference_year = int(FHIR_CODES["reference_date"][:4])
    rows = []
    ids: set[str] = set()
    for values in df.itertuples(index=False, name=None):
        row = dict(zip(df.columns, values))
        patient_id = row["patient_id"]
        if not isinstance(patient_id, str) or not _SAFE_ID.fullmatch(patient_id):
            raise _error("patient_id")
        if patient_id.casefold() in ids:
            raise _error("patient_id uniqueness")
        ids.add(patient_id.casefold())

        for field, pattern in (("state", r"[A-Z]{2}"), ("county_fips", r"[0-9]{5}")):
            if not isinstance(row[field], str) or not re.fullmatch(pattern, row[field]):
                raise _error(field)
        for field in ("sex", "hf_type", "heartland_risk_tier"):
            if not isinstance(row[field], str) or row[field] not in REDCAP_CATEGORICALS[field]:
                raise _error(field)
        if not isinstance(row["race"], str) or not row["race"].strip():
            raise _error("race")
        if kind == "redcap" and row["race"] not in REDCAP_CATEGORICALS["race"]:
            raise _error("race")

        for field in _MEASURES:
            row[field] = _number(row[field], field)
        for field, (lo, hi) in {**_CATEGORIES, "age": (0, reference_year - 1)}.items():
            value = _number(row[field], field)
            if not value.is_integer() or not lo <= value <= hi:
                raise _error(field)
            row[field] = int(value)
        for field in REDCAP_BOOLEAN_COLUMNS & columns:
            value = row[field]
            if not isinstance(value, (bool, np.bool_)) and not (
                _finite_real(value) and value in (0, 1)
            ):
                raise _error(field)
            row[field] = int(value)

        if row["gdmt_classes_count"] != sum(row[field] for field in _MEDICATIONS):
            raise _error("gdmt_classes_count")
        score = compute_row_score(row)
        if row["heartland_risk_score"] != score:
            raise _error("heartland_risk_score")
        if row["heartland_risk_tier"] != classify_tier(score):
            raise _error("heartland_risk_tier")
        rows.append(row)

    # Keep index/column order (including duplicate labels). Types follow this
    # known schema even for an empty frame; REDCap must not infer an unvalidated
    # text field merely because an empty source column had object dtype.
    result = pd.DataFrame(rows, columns=df.columns, index=df.index)
    for field in _MEASURES:
        result[field] = result[field].astype("float64")
    for field in set(_CATEGORIES) | {"age"} | (REDCAP_BOOLEAN_COLUMNS & columns):
        result[field] = result[field].astype("int64")
    return result


def write_new_files(outputs: list[tuple[Path, str]]) -> list[Path]:
    """Preflight every target; never overwrite. Later I/O may leave partial output."""
    for path, _ in outputs:
        if path.exists() or path.is_symlink():
            raise FileExistsError("export: output target already exists; use a new destination")
    for path, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also refuses a target appearing after preflight.
        with path.open("x", encoding="utf-8", newline="") as handle:
            handle.write(content)
    return [path for path, _ in outputs]
