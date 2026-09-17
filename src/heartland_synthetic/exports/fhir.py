"""FHIR R4 Bundle export (one collection Bundle per patient).

Emits JSON files as plain Python dicts — no external FHIR SDK dependency.
Resources included per patient:
- Patient
- Condition (HF type, diabetes, AF, CKD stage, prior HF hospitalization)
- Observation (LVEF, eGFR, BNP, SBP, DBP, HR, BMI)
- MedicationStatement (ACEi/ARB/ARNI, beta-blocker, MRA, SGLT2i)
- Observation (HEARTLAND risk score total, 0-18 points)
- RiskAssessment (HEARTLAND tier, with the score Observation as ``basis``)

No resource declares ``meta.profile``: the Bundles have not been validated
against US Core 6.1 or the HEARTLAND IG, so they assert no profile conformance.
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
_US_CORE_ETHNICITY_EXT = (
    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
)
# CDC Race & Ethnicity code system used by both US Core ombCategory slices.
_OMB_SYSTEM = "urn:oid:2.16.840.1.113883.6.238"
_NULL_FLAVOR_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-NullFlavor"

# County codes produced by the generator are synthetic: the 2-digit prefix is an
# alphabetical index over the state pool, not a real state FIPS, so the code is
# not an ANSI/Census county GEOID and must never be written to
# ``Address.postalCode`` (whose normative definition is "postal code", alias
# Zip). It is carried in an extension whose system URI marks it as synthetic.
_SYNTHETIC_COUNTY_EXT = (
    "https://fhir.heartlandprotocol.org/StructureDefinition/"
    "heartland-synthetic-county-code"
)
_SYNTHETIC_COUNTY_SYSTEM = (
    "https://fhir.heartlandprotocol.org/sid/synthetic-county-code"
)
_SYNTHETIC_COUNTY_DISPLAY = (
    "Synthetic county code (not an ANSI/FIPS county GEOID)"
)

# Displays for the codes used in the US Core ombCategory slices.
_OMB_DISPLAY = {
    "2106-3": "White",
    "2054-5": "Black or African American",
    "2135-2": "Hispanic or Latino",
    "UNK": "Unknown",
}

# The cohort carries a single 4-level variable that mixes race and ethnicity and
# has no ethnicity column, so neither axis can be derived from the other. Levels
# without a code inside the US Core 6.1 required value sets map to the
# NullFlavor ``UNK`` rather than to a plausible category.
# race value -> (race ombCategory, race text, ethnicity ombCategory, eth. text)
_RACE_ETHNICITY_MAP: dict[str, tuple[str, str, str, str]] = {
    "White": ("2106-3", "White", "UNK", "Unknown"),
    "Black": ("2054-5", "Black or African American", "UNK", "Unknown"),
    "Hispanic": ("UNK", "Unknown", "2135-2", "Hispanic or Latino"),
    "Other": (
        "UNK",
        "Other (not classifiable to an OMB race category)",
        "UNK",
        "Unknown",
    ),
}
_UNKNOWN_RACE_ETHNICITY = ("UNK", "Unknown", "UNK", "Unknown")

_HEARTLAND_METHOD_TEXT = "HEARTLAND Protocol v3.2 Risk Score"
_RISK_TIER_DISPLAY = {
    "low": "Low Risk",
    "moderate": "Moderate Risk",
    "high": "High Risk",
}


def _uuid() -> str:
    return str(uuid.uuid4())


def _birth_year(age: int, reference_date: str) -> int:
    ref_year = int(reference_date[:4])
    return ref_year - int(age)


def _omb_coding(code: str) -> dict[str, str]:
    """Coding for a US Core ``ombCategory`` slice.

    ``UNK`` / ``ASKU`` come from v3-NullFlavor; OMB categories come from the CDC
    race & ethnicity system. Both are inside the US Core 6.1 required value sets.
    """
    system = _NULL_FLAVOR_SYSTEM if code in {"UNK", "ASKU"} else _OMB_SYSTEM
    return {"system": system, "code": code, "display": _OMB_DISPLAY[code]}


def _us_core_extension(url: str, code: str, text: str) -> dict[str, Any]:
    return {
        "url": url,
        "extension": [
            {"url": "ombCategory", "valueCoding": _omb_coding(code)},
            {"url": "text", "valueString": text},
        ],
    }


def _patient_resource(row: pd.Series, reference_date: str) -> dict[str, Any]:
    race_code, race_text, eth_code, eth_text = _RACE_ETHNICITY_MAP.get(
        row["race"], _UNKNOWN_RACE_ETHNICITY
    )

    resource: dict[str, Any] = {
        "resourceType": "Patient",
        "id": str(row["patient_id"]),
        "extension": [
            _us_core_extension(_US_CORE_RACE_EXT, race_code, race_text),
            _us_core_extension(_US_CORE_ETHNICITY_EXT, eth_code, eth_text),
        ],
        "gender": "female" if row["sex"] == "F" else "male",
        "birthDate": str(_birth_year(row["age"], reference_date)),
        "address": [
            {
                "extension": [
                    {
                        "url": _SYNTHETIC_COUNTY_EXT,
                        "valueCoding": {
                            "system": _SYNTHETIC_COUNTY_SYSTEM,
                            "code": str(row["county_fips"]),
                            "display": _SYNTHETIC_COUNTY_DISPLAY,
                        },
                    }
                ],
                "state": str(row["state"]),
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


def _risk_tier_concept(tier: str) -> dict[str, Any]:
    display = _RISK_TIER_DISPLAY[tier]
    return {
        "coding": [
            {
                "system": FHIR_CODES["heartland_risk_tier_system"],
                "code": tier,
                "display": display,
            }
        ],
        "text": display,
    }


def _heartland_score_observation(
    patient_id: str, score: int, tier: str, reference_date: str
) -> dict[str, Any]:
    """Observation carrying the 0-18 point total that feeds the RiskAssessment.

    The total is a heuristic point count, not a probability, so it stays in an
    Observation referenced from ``RiskAssessment.basis`` instead of being
    written to ``RiskAssessment.prediction.probabilityDecimal``.
    """
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
                "valueCodeableConcept": _risk_tier_concept(str(tier)),
            }
        ],
    }


def _heartland_risk_assessment(
    patient_id: str, tier: str, basis_observation_id: str, reference_date: str
) -> dict[str, Any]:
    """RiskAssessment carrying the HEARTLAND tier as a coded qualitative risk.

    ``prediction.probabilityDecimal`` is deliberately absent: the HEARTLAND
    total is a 0-18 point count, and R4 defines ``probability[x]`` as the
    likelihood of an outcome. No ``meta.profile`` is declared — the HEARTLAND IG
    profile is published in a separate repository and these Bundles have not
    been validated against it.
    """
    return {
        "resourceType": "RiskAssessment",
        "id": _uuid(),
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
        "occurrenceDateTime": reference_date,
        "method": {"text": _HEARTLAND_METHOD_TEXT},
        "basis": [{"reference": f"Observation/{basis_observation_id}"}],
        "prediction": [{"qualitativeRisk": _risk_tier_concept(tier)}],
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

    # HEARTLAND score total, then the tier as a RiskAssessment based on it
    tier = str(row["heartland_risk_tier"])
    score_observation = _heartland_score_observation(
        patient_id, int(row["heartland_risk_score"]), tier, reference_date
    )
    _add(score_observation)
    _add(_heartland_risk_assessment(
        patient_id, tier, score_observation["id"], reference_date
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
