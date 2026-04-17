"""FHIR R4 Bundle export (one collection Bundle per patient).

Emits JSON files as plain Python dicts — no external FHIR SDK dependency.
Resources included per patient:
- Patient
- Condition (HF type, diabetes, AF, CKD stage, prior HF hospitalization)
- Observation (LVEF, eGFR, BNP, SBP, DBP, HR, BMI)
- MedicationStatement (ACEi/ARB/ARNI, beta-blocker, MRA, SGLT2i)
- Observation (HEARTLAND risk score + tier)
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from heartland_synthetic.registries import FHIR_CODES


_ICD10_SYSTEM = "http://hl7.org/fhir/sid/icd-10-cm"
_LOINC_SYSTEM = "http://loinc.org"
_RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"
_UCUM_SYSTEM = "http://unitsofmeasure.org"
_US_CORE_RACE_EXT = (
    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"
)


def _uuid() -> str:
    return str(uuid.uuid4())


def _birth_year(age: int, reference_date: str) -> int:
    ref_year = int(reference_date[:4])
    return ref_year - int(age)


def _patient_resource(row: pd.Series, reference_date: str) -> dict[str, Any]:
    race_map = {
        "White": ("2106-3", "White"),
        "Black": ("2054-5", "Black or African American"),
        "Hispanic": ("2135-2", "Hispanic or Latino"),
        "Other": ("2131-1", "Other Race"),
    }
    race_code, race_display = race_map.get(row["race"], ("2131-1", "Other Race"))

    resource: dict[str, Any] = {
        "resourceType": "Patient",
        "id": str(row["patient_id"]),
        "extension": [
            {
                "url": _US_CORE_RACE_EXT,
                "extension": [
                    {
                        "url": "ombCategory",
                        "valueCoding": {
                            "system": "urn:oid:2.16.840.1.113883.6.238",
                            "code": race_code,
                            "display": race_display,
                        },
                    },
                    {"url": "text", "valueString": race_display},
                ],
            }
        ],
        "gender": "female" if row["sex"] == "F" else "male",
        "birthDate": str(_birth_year(row["age"], reference_date)),
        "address": [
            {
                "state": str(row["state"]),
                "postalCode": str(row["county_fips"])[:5],
                "use": "home",
                "country": "US",
            }
        ],
    }
    return resource


def _condition(
    patient_id: str, code: str, display: str, reference_date: str
) -> dict[str, Any]:
    return {
        "resourceType": "Condition",
        "id": _uuid(),
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                }
            ]
        },
        "code": {
            "coding": [
                {"system": _ICD10_SYSTEM, "code": code, "display": display}
            ],
            "text": display,
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "recordedDate": reference_date,
    }


def _observation(
    patient_id: str,
    loinc_code: str,
    display: str,
    unit: str,
    value: float,
    reference_date: str,
) -> dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": _uuid(),
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs"
                        if loinc_code in {"8480-6", "8462-4", "8867-4", "39156-5"}
                        else "laboratory",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {"system": _LOINC_SYSTEM, "code": loinc_code, "display": display}
            ],
            "text": display,
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": reference_date,
        "valueQuantity": {
            "value": float(value),
            "unit": unit,
            "system": _UCUM_SYSTEM,
            "code": unit,
        },
    }


def _medication_statement(
    patient_id: str, rxnorm_code: str, display: str, reference_date: str
) -> dict[str, Any]:
    return {
        "resourceType": "MedicationStatement",
        "id": _uuid(),
        "status": "active",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": _RXNORM_SYSTEM,
                    "code": rxnorm_code,
                    "display": display,
                }
            ],
            "text": display,
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": reference_date,
    }


def _heartland_score_observation(
    patient_id: str, score: int, tier: str, reference_date: str
) -> dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": _uuid(),
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "survey",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": FHIR_CODES["heartland_system"],
                    "code": "heartland-risk-score",
                    "display": "HEARTLAND Risk Score",
                }
            ],
            "text": "HEARTLAND Risk Score",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": reference_date,
        "valueInteger": int(score),
        "component": [
            {
                "code": {
                    "coding": [
                        {
                            "system": FHIR_CODES["heartland_system"],
                            "code": "heartland-risk-tier",
                            "display": "HEARTLAND Risk Tier",
                        }
                    ]
                },
                "valueString": str(tier),
            }
        ],
    }


def _build_bundle(row: pd.Series) -> dict[str, Any]:
    reference_date = FHIR_CODES["reference_date"]
    patient = _patient_resource(row, reference_date)
    patient_id = patient["id"]

    entries: list[dict[str, Any]] = []

    def _add(res: dict[str, Any]) -> None:
        rid = res["id"]
        entries.append(
            {"fullUrl": f"urn:uuid:{rid}", "resource": res}
        )

    _add(patient)

    # Conditions
    hf_code, hf_display = FHIR_CODES["icd10"][row["hf_type"]]
    _add(_condition(patient_id, hf_code, hf_display, reference_date))
    if int(row["diabetes"]):
        code, disp = FHIR_CODES["icd10"]["diabetes"]
        _add(_condition(patient_id, code, disp, reference_date))
    if int(row["af"]):
        code, disp = FHIR_CODES["icd10"]["af"]
        _add(_condition(patient_id, code, disp, reference_date))
    ckd_stage = int(row["ckd_stage"])
    if ckd_stage in FHIR_CODES["icd10"]["ckd"]:
        code, disp = FHIR_CODES["icd10"]["ckd"][ckd_stage]
        _add(_condition(patient_id, code, disp, reference_date))
    if int(row["prior_hf_hosp_6mo"]):
        code, disp = FHIR_CODES["icd10"]["prior_hf_hosp"]
        _add(_condition(patient_id, code, disp, reference_date))

    # Observations — vitals / labs
    for key in ("lvef", "egfr", "bnp", "sbp", "dbp", "hr", "bmi"):
        loinc_code, display, unit = FHIR_CODES["loinc"][key]
        _add(_observation(
            patient_id, loinc_code, display, unit, float(row[key]), reference_date
        ))

    # Medication statements
    for key, (rxcode, display) in FHIR_CODES["rxnorm"].items():
        if int(row.get(key, 0)) == 1:
            _add(_medication_statement(patient_id, rxcode, display, reference_date))

    # HEARTLAND score
    _add(_heartland_score_observation(
        patient_id,
        int(row["heartland_risk_score"]),
        str(row["heartland_risk_tier"]),
        reference_date,
    ))

    return {
        "resourceType": "Bundle",
        "id": _uuid(),
        "type": "collection",
        "timestamp": f"{reference_date}T00:00:00Z",
        "entry": entries,
    }


def export_fhir_bundle(
    df: pd.DataFrame, out_dir: str | Path
) -> list[Path]:
    """Write one FHIR R4 collection Bundle per patient.

    Parameters
    ----------
    df:
        Cohort DataFrame (output of :func:`generate_cohort`). Must include the
        standard columns used by the Bundle builder.
    out_dir:
        Directory for the JSON outputs (created if missing). One file
        ``{patient_id}.json`` is written per patient.

    Returns
    -------
    list[pathlib.Path]
        Paths written, in cohort row order.
    """
    required = {
        "patient_id", "age", "sex", "race", "state", "county_fips",
        "hf_type", "lvef", "egfr", "bnp", "sbp", "dbp", "hr", "bmi",
        "diabetes", "af", "ckd_stage", "prior_hf_hosp_6mo",
        "heartland_risk_score", "heartland_risk_tier",
    }
    missing = required - set(df.columns)
    if missing:
        raise KeyError(
            f"export_fhir_bundle: cohort missing columns: {sorted(missing)}"
        )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for _, row in df.iterrows():
        bundle = _build_bundle(row)
        fname = f"{row['patient_id']}.json"
        path = out_dir / fname
        with path.open("w", encoding="utf-8") as fh:
            json.dump(bundle, fh, indent=2, ensure_ascii=False)
        paths.append(path)
    return paths


__all__ = ["export_fhir_bundle"]
