"""REDCap export: data CSV + data-dictionary CSV.

The output is a **standalone** single-form instrument (``heartland_cohort``)
whose data dictionary is generated from the cohort columns, in the official
18-column REDCap data dictionary layout. It is *not* an import file for the
HEARTLAND REDCap Instrument Template (https://github.com/vickymuller-md/redcap-template),
a separately versioned instrument using ``bl_*`` / ``gdmt_*`` / ``mo_*`` /
``out_*`` field names. Mapping limits and withdrawn historical assumptions are
in ``docs/redcap_template_crosswalk.md``; no direct-import adapter is provided.
"""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

import pandas as pd

from heartland_synthetic.exports._validation import validate_cohort, write_new_files

from heartland_synthetic.registries import (
    REDCAP_BOOLEAN_COLUMNS,
    REDCAP_CATEGORICALS,
    REDCAP_DROPDOWNS,
    REDCAP_FIELD_LABELS,
    REDCAP_FIELD_NOTES,
    REDCAP_DEFAULT_NOTE,
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
        "Section Header": "Synthetic research/testing only; not clinical observations" if column == "record_id" else "",
        "Field Type": field_type,
        "Field Label": label,
        "Choices, Calculations, OR Slider Labels": choices,
        "Field Note": REDCAP_FIELD_NOTES.get(column, REDCAP_DEFAULT_NOTE),
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
    """Write REDCap data + data-dictionary CSVs for a standalone instrument.

    The pair is intended for evaluation in a new, empty REDCap project. Local
    generation does not prove institutional import success. It is not an import file for the
    HEARTLAND REDCap Instrument Template — see the module docstring.

    The output data CSV renames ``patient_id`` to ``record_id`` (REDCap
    requires the first column to be ``record_id``).

    Parameters
    ----------
    df:
        Complete cohort DataFrame (output of :func:`generate_cohort`).
        All rows are validated before any output; extra columns are rejected.
    out_prefix:
        Path prefix; two files will be written:
        ``out_prefix.with_suffix('.csv')`` and ``{out_prefix}_datadict.csv``.
        Existing targets are never overwritten. Later I/O failures may leave
        partial new output; use a fresh destination for every export.

    Returns
    -------
    tuple[Path, Path]
        Paths to the data CSV and the data-dictionary CSV.
    """
    data_df = validate_cohort(df, kind="redcap").rename(columns={"patient_id": "record_id"})
    data_df = data_df[["record_id", *(c for c in data_df.columns if c != "record_id")]]
    out_prefix = Path(out_prefix)
    data_path = out_prefix.with_suffix(".csv")
    dict_path = out_prefix.parent / f"{out_prefix.name}_datadict.csv"
    dictionary = StringIO(newline="")
    writer = csv.DictWriter(dictionary, fieldnames=REDCAP_DD_HEADER)
    writer.writeheader()
    for col in data_df.columns:
        writer.writerow(_field_definition(col, data_df[col]))
    write_new_files([(data_path, data_df.to_csv(index=False)),
                     (dict_path, dictionary.getvalue())])
    return data_path, dict_path


__all__ = ["export_redcap", "INSTRUMENT_NAME"]
