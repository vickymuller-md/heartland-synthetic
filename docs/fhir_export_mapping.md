# Synthetic FHIR R4 export mapping

This mapping applies to the unreleased 0.3.0 candidate, not to the published
0.2.2 exporter. It is a research/testing collection, not a clinical record,
transaction, clinical assessment or lossless serialization of the cohort.
No resource declares `meta.profile`; use of US Core extensions or HEARTLAND
terminology does not assert conformance to those profiles.

## Identity, time and references

Each entry has a valid, unique `urn:uuid:` fullUrl, independent of its resource
id. The Patient id and filename retain the checked synthetic source id. Every
subject and basis reference is the exact fullUrl of an entry in that Bundle.
There is no implied REST endpoint. The Bundle is not an import/transaction plan.

The fixed 2026-01-01 reference date is a simulation anchor, not an encounter,
specimen collection, diagnosis, prescription or observed follow-up date.
Birth year is reference year minus modeled age, with year-only precision.
Bundle and resources carry a display-only synthetic-data tag; resource notes
describe important limitations without inventing a controlled terminology.

## Mapping and unsupported inferences

|Source|Export|Limits|
|-|-|-|
|patient_id, age, sex|Patient id, year-only birthDate, gender|Synthetic identity; sex F/M is mapped to the corresponding administrative-gender value, not a separate gender assessment.|
|race|US Core race/ethnicity extensions|The mixed source variable cannot establish both axes; unrepresented categories remain Unknown.|
|state, county_fips|Patient.address and the HEARTLAND synthetic-county extension|No ZIP, geocoding, real county or actual residence assertion.|
|hf_type, positive diabetes/af|Text-only Condition|Simulation group/flags, no subtype, chronicity, complications or coded clinical diagnosis inferred. Absent Condition does not establish clinical absence.|
|lvef|Quantity Observation, LOINC 10230-1|The code has no method qualifier; no imaging method is asserted.|
|egfr|Text-only quantity Observation|No formula, creatinine result or specimen is generated.|
|bnp, hr, bmi|Quantity Observation using the retained LOINC mappings|Illustrative measurement concepts, not tests performed. BNP uses an assumed serum/plasma concept for this illustrative export; no recorded specimen or assay provenance exists.|
|sbp, dbp|One BP panel Observation (85354-9) with systolic (8480-6) and diastolic (8462-4) components|Component values retain mm[Hg]; no top-level quantity or duplicate standalone BP observations. Baseline simulation, not an admission measurement.|
|ckd_stage|Text-only integer Observation|Legacy simulated eGFR bin, not a CKD diagnosis.|
|ckm_stage|Text-only integer Observation|Legacy simulation category, not adjudicated AHA staging.|
|social_support_score|Text-only quantity Observation|Legacy proxy, not ESSI, questionnaire items, validated cutoff or living arrangement.|
|distance_to_cardiology_mi|Text-only quantity Observation|Modeled distance, not geographic lookup or route.|
|prior_hf_hosp_6mo|Text-only boolean Observation|Modeled flag, not an active disease, admission record or adjudicated event.|
|positive on_* class flags|Text-only MedicationStatement, status unknown|Hypothetical class exposure only; no specific medicine, dose, start date, prescription or receipt. Zero flags produce no statement and may be unsampled placeholders.|
|heartland_risk_score/tier|Score Observation and qualitative RiskAssessment|Proposed point total/tier pending validation, never an outcome probability.|

The score Observation also contains **all ten Boolean criterion components**,
including false values. They use text labels, not unregistered HEARTLAND codes,
and the same predicates/weights as the checked generator score. The labels
explicitly identify baseline SBP (not admission SBP), BNP-only input, the
legacy CKM category and social-support proxy. This does not turn the simulated
inputs into a clinical questionnaire or verified clinical criteria.

`RiskAssessment.method.text` retains the historical IG definition
`HEARTLAND Protocol v3.2 Risk Score`; it is not the software or Toolkit version.
Its `basis` resolves to the score Observation. No `probability[x]` is emitted.

The export omits `rural_urban_code`, `gdmt_classes_count` and optional annual
outcome draws. The four class flags are represented only when positive.
It does not encode monthly trajectories, event chronology, doses, eligibility,
ESSI responses, true geography or source provenance that the cohort never
captured. These are not fabricated to fill a profile. Preserve the cohort and
its generation configuration separately for full simulation provenance.

## Candidate compatibility change

Legacy ICD-10-CM mappings and the `FHIR_CODES["icd10"]` / `["rxnorm"]` tables
are withdrawn. In particular, HFmrEF does not establish combined systolic and
diastolic failure; a diabetes flag does not establish type 2 without
complications; an eGFR bin does not establish CKD. Legacy RxNorm identifiers
1998, 18867, 321064 and 1545653 identify captopril, benazepril, olmesartan and
empagliflozin respectively, not the four simulated therapy classes.

Method-specific LOINC 98979-8 (eGFR) is withdrawn. LVEF 10230-1 is retained:
the official LOINC definition has no method qualifier. Consumers must not
depend on the withdrawn codes, relative
references, malformed Patient UUID URN or exact resource counts.
Blood pressure now follows the R4-required panel/component representation,
replacing two standalone measurement resources.
The published dataset, generator distributions and scoring rules are unchanged.

## Validation scope

Unit tests check internal reference resolution, mappings, limitations and
reconstruction of the point total from ten Boolean components. External R4
validation of selected synthetic fixtures checks that sample, not every
possible cohort, profile conformance, clinical validity or EHR importability.
Warnings/information are retained in the release evidence, not suppressed.
The collection does not provide full human-readable resource narratives or
real clinical performers. The eGFR UCUM annotation is descriptive, not a
unit-conversion factor for body-surface normalization. Opaque synthetic county
codes have no real-geography terminology membership check. These limitations
remain relevant even when selected fixtures have no validation errors.

Normative references: [R4 Bundle identity and reference resolution](https://hl7.org/fhir/R4/bundle.html),
[R4 References](https://hl7.org/fhir/R4/references.html),
[MedicationStatement](https://hl7.org/fhir/R4/medicationstatement.html),
[Condition](https://hl7.org/fhir/R4/condition.html).
[R4 blood-pressure profile requirements](https://hl7.org/fhir/R4/bp.html)
apply when the corresponding vital-sign codes are used, even without an
explicit `meta.profile` declaration.
RxNorm identities can be checked with the [NLM RxNav properties API](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getRxConceptProperties.html).
LOINC definitions: [LVEF 10230-1](https://loinc.org/10230-1),
[eGFR 98979-8](https://loinc.org/98979-8),
[BNP 30934-4](https://loinc.org/30934-4),
[SBP 8480-6](https://loinc.org/8480-6),
[DBP 8462-4](https://loinc.org/8462-4),
[heart rate 8867-4](https://loinc.org/8867-4),
[BMI 39156-5](https://loinc.org/39156-5).
Reviewed 2026-09-29. Validation execution and release status are tracked
separately; this document alone is not a successful-validator receipt.
