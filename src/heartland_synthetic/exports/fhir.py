"""FHIR R4 Bundle export (one collection Bundle per patient).

Emits JSON files as plain Python dicts — no external FHIR SDK dependency.
Resources included per patient:
- Patient
- Text-only Condition (simulated HF group and positive diabetes/AF flags)
- Observation (measurements, legacy bins/proxies, prior-hospitalization flag)
- Text-only MedicationStatement (positive simulated class flags, status unknown)
- Observation (HEARTLAND total/tier and ten Boolean simulation criteria)
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
from heartland_synthetic.scoring import RISK_VARIABLES
from heartland_synthetic.exports._validation import validate_cohort, write_new_files


_LOINC_SYSTEM = "http://loinc.org"
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

_SIMULATION_NOTE = (
    "Synthetic research/testing data, not a real patient observation. "
    "The fixed reference date is a simulation anchor, not a clinical event date."
)
_CRITERION_LABELS = {
    "age_over_75": "Simulated age >=75 years (2 points)",
    "prior_hf_hosp_6mo": "Simulated prior HF hospitalization within 6 months (3 points)",
    "egfr_below_45": "Simulated eGFR <45 mL/min/1.73m^2 (2 points)",
    "elevated_natriuretic": "Simulated BNP >=500 pg/mL, BNP-only adapter (2 points)",
    "sbp_below_100": "Simulated baseline SBP <100 mmHg, not admission SBP (2 points)",
    "diabetes": "Simulated diabetes flag (1 point)",
    "lvef_below_30": "Simulated LVEF <30% (2 points)",
    "ckm_stage_3_or_4": "Simulated legacy CKM category 3 or 4 (2 points)",
    "distance_over_50_miles": "Modeled distance to cardiology >50 miles (1 point)",
    "limited_social_support": "Legacy social-support proxy <18, not ESSI or living alone (1 point)",
}


def _synthetic_meta() -> dict[str, Any]:
    return {"tag": [{"display": "Synthetic research/testing data"}]}


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
        "birthDate": f"{_birth_year(row['age'], reference_date):04d}",
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


def _condition(patient_id: str, display: str) -> dict[str, Any]:
    return {
        "resourceType": "Condition",
        "id": _uuid(),
        "code": {"text": display},
        "subject": {"reference": f"Patient/{patient_id}"},
        "note": [{"text": _SIMULATION_NOTE + " Assigned simulation group/flag, not an adjudicated diagnosis or assessed disease status."}],
    }


def _observation(
    patient_id: str,
    loinc_code: str | None,
    display: str,
    unit: str,
    value: float,
    reference_date: str,
) -> dict[str, Any]:
    resource = {
        "resourceType": "Observation",
        "id": _uuid(),
        "status": "final",
        "code": {"text": display},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": reference_date,
        "valueQuantity": {
            "value": float(value),
            "unit": unit,
            "system": _UCUM_SYSTEM,
            "code": unit,
        },
        "note": [{"text": _SIMULATION_NOTE}],
    }
    if loinc_code is not None:
        resource["code"]["coding"] = [
            {"system": _LOINC_SYSTEM, "code": loinc_code, "display": display}
        ]
    # Do not mislabel LVEF as a laboratory test or infer an imaging method.
    if loinc_code != "10230-1":
        category = "vital-signs" if loinc_code in {"8480-6", "8462-4", "8867-4", "39156-5"} else "laboratory"
        resource["category"] = [{"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
            "code": category,
        }]}]
    if loinc_code == "30934-4":
        resource["note"][0]["text"] += (
            " Assumed serum/plasma concept for this illustrative export; "
            "no recorded specimen or assay provenance."
        )
    if loinc_code is None:
        resource["note"][0]["text"] += " Sampled eGFR; no estimation formula or creatinine result was generated."
    return resource


def _medication_statement(patient_id: str, display: str) -> dict[str, Any]:
    return {
        "resourceType": "MedicationStatement",
        "id": _uuid(),
        "status": "unknown",
        "medicationCodeableConcept": {"text": display},
        "subject": {"reference": f"Patient/{patient_id}"},
        "note": [{"text": _SIMULATION_NOTE + " Positive hypothetical class flag only; no specific drug, dose, treatment dates, prescription or receipt of medication is established."}],
    }


def _blood_pressure(patient_id: str, row: dict[str, Any], reference_date: str) -> dict[str, Any]:
    code, display = FHIR_CODES["blood_pressure_panel"]
    components = []
    for key in ("sbp", "dbp"):
        code_part, label, unit = FHIR_CODES["loinc"][key]
        components.append({
            "code": {"coding": [{"system": _LOINC_SYSTEM, "code": code_part, "display": label}]},
            "valueQuantity": {"value": float(row[key]), "unit": unit, "system": _UCUM_SYSTEM, "code": unit},
        })
    return {
        "resourceType": "Observation",
        "id": _uuid(),
        "status": "final",
        "category": [{"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
            "code": "vital-signs",
        }]}],
        "code": {"coding": [{"system": _LOINC_SYSTEM, "code": code, "display": display}], "text": display},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": reference_date,
        "component": components,
        "note": [{"text": _SIMULATION_NOTE + " Modeled baseline blood pressure, not an admission measurement."}],
    }


def _modeled_observation(patient_id: str, label: str, value: dict[str, Any], reference_date: str) -> dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": _uuid(),
        "status": "final",
        "code": {"text": label},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": reference_date,
        "note": [{"text": _SIMULATION_NOTE + " Modeled input/proxy, not clinical staging, a questionnaire or an adjudicated event."}],
        **value,
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
    patient_id: str, score: int, tier: str, reference_date: str, row: dict[str, Any]
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
        "note": [{"text": _SIMULATION_NOTE + " Proposed point score pending validation. Ten simulated criteria use BNP only, baseline SBP and legacy CKM/support proxies; not a clinical questionnaire or an outcome probability."}],
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
        ] + [
            {"code": {"text": _CRITERION_LABELS[variable.key]},
             "valueBoolean": bool(variable.predicate(row))}
            for variable in RISK_VARIABLES
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
        "note": [{"text": _SIMULATION_NOTE + " Proposed point tier pending validation; not an observed risk or validated outcome likelihood."}],
    }


def _build_bundle(row: pd.Series) -> dict[str, Any]:
    reference_date = FHIR_CODES["reference_date"]
    patient = _patient_resource(row, reference_date)
    patient_id = patient["id"]

    entries: list[dict[str, Any]] = []
    full_urls: dict[str, str] = {}

    def _add(res: dict[str, Any]) -> None:
        key = f"{res['resourceType']}/{res['id']}"
        full_url = f"urn:uuid:{_uuid()}"
        if key in full_urls or full_url in full_urls.values():
            raise ValueError("Duplicate internal FHIR identity")
        full_urls[key] = full_url
        res["meta"] = _synthetic_meta()
        entries.append({"fullUrl": full_url, "resource": res})

    _add(patient)

    # Conditions
    _add(_condition(patient_id, FHIR_CODES["condition_text"][row["hf_type"]]))
    for key in ("diabetes", "af"):
        if int(row[key]):
            _add(_condition(patient_id, FHIR_CODES["condition_text"][key]))

    # Observations — vitals / labs
    for key in ("lvef", "egfr", "bnp", "hr", "bmi"):
        loinc_code, display, unit = FHIR_CODES["loinc"][key]
        _add(_observation(
            patient_id, loinc_code, display, unit, float(row[key]), reference_date
        ))
    _add(_blood_pressure(patient_id, row, reference_date))

    for label, value in [
        ("Legacy simulated eGFR bin (not a CKD diagnosis)", {"valueInteger": int(row["ckd_stage"])}),
        ("Legacy simulated CKM category (not adjudicated staging)", {"valueInteger": int(row["ckm_stage"])}),
        ("Legacy social-support proxy (not ESSI)", {"valueQuantity": {"value": float(row["social_support_score"])}}),
        ("Modeled distance to cardiology", {"valueQuantity": {"value": float(row["distance_to_cardiology_mi"]), "unit": "miles", "system": _UCUM_SYSTEM, "code": "[mi_i]"}}),
        ("Simulated prior HF hospitalization within 6 months", {"valueBoolean": bool(row["prior_hf_hosp_6mo"])}),
    ]:
        _add(_modeled_observation(patient_id, label, value, reference_date))

    # Positive class flags only; zero can be an unsampled placeholder.
    for key, display in FHIR_CODES["medication_class_text"].items():
        if int(row.get(key, 0)) == 1:
            _add(_medication_statement(patient_id, display))

    # HEARTLAND score total, then the tier as a RiskAssessment based on it
    tier = str(row["heartland_risk_tier"])
    score_observation = _heartland_score_observation(
        patient_id, int(row["heartland_risk_score"]), tier, reference_date, row
    )
    _add(score_observation)
    _add(_heartland_risk_assessment(
        patient_id, tier, score_observation["id"], reference_date
    ))

    # Relative Type/id references are not resolvable against urn:uuid entries.
    # Fail closed if a future builder introduces an unregistered reference.
    def _resolve(node: Any) -> None:
        if isinstance(node, dict):
            if "reference" in node:
                node["reference"] = full_urls[node["reference"]]
            for value in node.values():
                _resolve(value)
        elif isinstance(node, list):
            for value in node:
                _resolve(value)

    _resolve(entries)

    return {
        "resourceType": "Bundle",
        "id": _uuid(),
        "meta": _synthetic_meta(),
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
        complete standard cohort schema. All rows are checked before output;
        extra columns, inconsistent scores and invalid values are rejected.
    out_dir:
        Directory for the JSON outputs (created if missing). One file
        ``{patient_id}.json`` is written per patient. Existing targets are never
        overwritten. A later filesystem failure may leave partial new output.

    Returns
    -------
    list[pathlib.Path]
        Paths written, in cohort row order.
    """
    checked = validate_cohort(df, kind="fhir")
    out_dir = Path(out_dir)
    outputs: list[tuple[Path, str]] = []
    for values in checked.itertuples(index=False, name=None):
        row = dict(zip(checked.columns, values))
        bundle = _build_bundle(row)
        outputs.append((out_dir / f"{row['patient_id']}.json",
                        json.dumps(bundle, indent=2, ensure_ascii=False, allow_nan=False)))
    return write_new_files(outputs)


__all__ = ["export_fhir_bundle"]
