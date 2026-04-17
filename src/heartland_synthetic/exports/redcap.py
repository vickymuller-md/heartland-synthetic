"""REDCap export: data CSV + data-dictionary CSV."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

from heartland_synthetic.registries import (
    REDCAP_BOOLEAN_COLUMNS,
    REDCAP_CATEGORICALS,
    REDCAP_DROPDOWNS,
    REDCAP_FIELD_LABELS,
)

INSTRUMENT_NAME = "heartland_cohort"

# REDCap Data Dictionary columns (official 18-column layout).
REDCAP_DD_HEADER = [
    "Variable / Field Name",
    "Form Name",
    "Section Header",
    "Field Type",
    "Field Label",
    "Choices, Calculations, OR Slider Labels",
    "Field Note",
    "Text Validation Type OR Show Slider Number",
    "Text Validation Min",
    "Text Validation Max",
    "Identifier?",
    "Branching Logic (Show field only if...)",
    "Required Field?",
    "Custom Alignment",
    "Question Number (surveys only)",
    "Matrix Group Name",
    "Matrix Ranking?",
    "Field Annotation",
]


def _format_choices(mapping: dict) -> str:
    return " | ".join(f"{code}, {label}" for code, label in mapping.items())


def _field_definition(column: str, series: pd.Series) -> dict[str, str]:
    label = REDCAP_FIELD_LABELS.get(column, column.replace("_", " ").title())

    field_type = "text"
    validation = ""
    min_v = ""
    max_v = ""
    choices = ""

    if column in REDCAP_CATEGORICALS:
        field_type = "radio"
        choices = _format_choices(REDCAP_CATEGORICALS[column])
    elif column in REDCAP_DROPDOWNS:
        field_type = "dropdown"
        choices = _format_choices(REDCAP_DROPDOWNS[column])
    elif column in REDCAP_BOOLEAN_COLUMNS:
        field_type = "yesno"
    elif pd.api.types.is_integer_dtype(series):
        validation = "integer"
    elif pd.api.types.is_float_dtype(series):
        validation = "number"

    return {
        "Variable / Field Name": column,
        "Form Name": INSTRUMENT_NAME,
        "Section Header": "",
        "Field Type": field_type,
        "Field Label": label,
        "Choices, Calculations, OR Slider Labels": choices,
        "Field Note": "",
        "Text Validation Type OR Show Slider Number": validation,
        "Text Validation Min": min_v,
        "Text Validation Max": max_v,
        "Identifier?": "y" if column == "record_id" else "",
        "Branching Logic (Show field only if...)": "",
        "Required Field?": "y" if column == "record_id" else "",
        "Custom Alignment": "",
        "Question Number (surveys only)": "",
        "Matrix Group Name": "",
        "Matrix Ranking?": "",
        "Field Annotation": "",
    }


def export_redcap(
    df: pd.DataFrame,
    out_prefix: str | Path,
) -> tuple[Path, Path]:
    """Write REDCap data + data-dictionary CSVs.

    The output data CSV renames ``patient_id`` to ``record_id`` (REDCap
    requires the first column to be ``record_id``).

    Parameters
    ----------
    df:
        Cohort DataFrame (output of :func:`generate_cohort`).
    out_prefix:
        Path prefix; two files will be written:
        ``{out_prefix}.csv`` and ``{out_prefix}_datadict.csv``.

    Returns
    -------
    tuple[Path, Path]
        Paths to the data CSV and the data-dictionary CSV.
    """
    out_prefix = Path(out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    data_df = df.copy()
    if "patient_id" in data_df.columns:
        data_df = data_df.rename(columns={"patient_id": "record_id"})
    # REDCap expects boolean-like fields as 0/1.
    for col in data_df.columns:
        if col in REDCAP_BOOLEAN_COLUMNS:
            data_df[col] = data_df[col].astype(int)

    data_path = out_prefix.with_suffix(".csv")
    data_df.to_csv(data_path, index=False)

    dict_path = out_prefix.parent / f"{out_prefix.name}_datadict.csv"
    with dict_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=REDCAP_DD_HEADER)
        writer.writeheader()
        for col in data_df.columns:
            writer.writerow(_field_definition(col, data_df[col]))

    return data_path, dict_path


__all__ = ["export_redcap", "INSTRUMENT_NAME"]
