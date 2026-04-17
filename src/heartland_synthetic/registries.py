"""Distribution constants with registry citations.

Every value here is anchored to a published registry or trial. Keep this module
purely declarative — no sampling logic lives here.

Sources
-------
- GWTG-HF: Get With The Guidelines - Heart Failure registry (AHA).
- PARADIGM-HF: McMurray JJV et al. NEJM 2014;371:993-1004.
- DELIVER: Solomon SD et al. NEJM 2022;387:1089-1098.
- EMPEROR-Preserved: Anker SD et al. NEJM 2021;385:1451-1461.
- STRONG-HF: Mebazaa A et al. Lancet 2022;400:1938-1952.
- CHAMP-HF: Greene SJ et al. J Am Coll Cardiol 2018;72:351-366.
- NHANES: National Health and Nutrition Examination Survey (CDC).
- ENRICHD ESSI: Enhancing Recovery in Coronary Heart Disease Patients
  Social Support Instrument (8 items, 5-pt Likert, range 8-40).
- NPPES NPI: National Plan and Provider Enumeration System.
- USDA RUCA: Rural-Urban Commuting Area codes (1-3 urban, 4-10 rural).
- KDIGO 2012 CKD staging.
- AHA 2023 Presidential Advisory on CKM Syndrome
  (DOI 10.1161/CIR.0000000000001184).
- Manemann SM et al. J Am Heart Assoc 2018;7:e008069 (social isolation HR 3.74).
"""

from __future__ import annotations


# -----------------------------------------------------------------------------
# Demographics (GWTG-HF / NHANES)
# -----------------------------------------------------------------------------
AGE_MEAN = 72.0
AGE_SD = 12.0

FEMALE_FRACTION_DEFAULT = 0.48

RACE_DISTRIBUTION = {
    "White": 0.65,
    "Black": 0.20,
    "Hispanic": 0.10,
    "Other": 0.05,
}

# Subset of states used as a coarse geography model. Rural-heavy states listed
# first so we can bias rural patients toward them.
RURAL_HEAVY_STATES = ["MT", "WY", "ND", "SD", "AR", "MS", "WV", "KY", "IA", "NE"]
URBAN_HEAVY_STATES = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]


# -----------------------------------------------------------------------------
# Clinical vitals — copula marginals
# -----------------------------------------------------------------------------
# LVEF strata by HF type (PARADIGM-HF / DELIVER / EMPEROR-Preserved)
LVEF_PARAMS = {
    "hfref": {"mean": 25.0, "sd": 7.0, "lo": 5.0, "hi": 39.0},
    "hfmref": {"lo": 40.0, "hi": 49.0},  # uniform
    "hfpef": {"mean": 60.0, "sd": 8.0, "lo": 50.0, "hi": 75.0},
}

# eGFR log-normal (STRONG-HF baseline)
EGFR_LOG_MEAN = 4.094  # ln(60)
EGFR_LOG_SD = 0.35
EGFR_CLIP = (15.0, 120.0)
EGFR_ELDERLY_SHIFT = -10.0  # applied if age >= 75

# BNP log-normal (PARADIGM-HF baseline ~600 pg/mL median)
BNP_LOG_MEAN = 6.397  # ln(600)
BNP_LOG_SD = 0.9
BNP_HFPEF_MULTIPLIER = 0.70  # HFpEF has lower BNP than HFrEF

# Vitals normals (GWTG-HF)
SBP_MEAN = 125.0
SBP_SD = 20.0
SBP_CLIP = (80.0, 200.0)
SBP_RURAL_SHIFT = 5.0  # untreated HTN bias

HR_MEAN = 78.0
HR_SD = 14.0
HR_CLIP = (45.0, 140.0)

# BMI (DELIVER baseline)
BMI_MEAN = 30.0
BMI_SD = 6.0
BMI_CLIP = (16.0, 55.0)
BMI_HFPEF_SHIFT = 3.0

# DBP derived from SBP
DBP_SBP_COEF = 0.6
# Calibrated so Pearson corr(SBP, DBP) ~ 0.65 (clinically realistic):
# 12 / sqrt(12^2 + DBP_NOISE_SD^2) = 0.65 -> DBP_NOISE_SD ~ 14.
DBP_NOISE_SD = 14.0
DBP_CLIP = (40.0, 120.0)


# -----------------------------------------------------------------------------
# Copula correlation matrix for [lvef, egfr, bnp, sbp, hr, bmi] (6-dim).
# DBP is intentionally excluded: it is reconstructed from SBP as
# DBP = DBP_SBP_COEF * SBP + N(0, DBP_NOISE_SD) so the SBP-DBP correlation is
# determined solely by that linear model (target rho ~ 0.65).
# -----------------------------------------------------------------------------
VITALS_ORDER = ["lvef", "egfr", "bnp", "sbp", "hr", "bmi"]

CORR_VITALS = [
    #     lvef   egfr   bnp    sbp    hr     bmi
    [ 1.00, 0.10, -0.45, 0.10, -0.15, 0.05],  # lvef
    [ 0.10, 1.00, -0.40, 0.05, -0.05, -0.05], # egfr
    [-0.45, -0.40, 1.00, -0.10, 0.15, -0.05], # bnp
    [ 0.10, 0.05, -0.10, 1.00, -0.05, 0.25],  # sbp
    [-0.15, -0.05, 0.15, -0.05, 1.00, 0.05],  # hr
    [ 0.05, -0.05, -0.05, 0.25, 0.05, 1.00],  # bmi
]

# Target Pearson correlation for the SBP->DBP linear model (clinically ~0.65).
SBP_DBP_TARGET_CORR = 0.65


# -----------------------------------------------------------------------------
# Rural variables
# -----------------------------------------------------------------------------
# Distance to cardiology (NPPES NPI derived)
DISTANCE_RURAL_LOG_MEAN = 3.555   # ln(35)
DISTANCE_RURAL_LOG_SD = 0.7
DISTANCE_URBAN_LOG_MEAN = 1.792   # ln(6)
DISTANCE_URBAN_LOG_SD = 0.6
DISTANCE_CLIP = (0.5, 400.0)

# ENRICHD ESSI (range 8-40; <18 ~= lowest tertile = "limited social support")
ESSI_URBAN_MEAN = 29.0
ESSI_URBAN_SD = 6.0
ESSI_RURAL_MEAN = 24.0
ESSI_RURAL_SD = 7.0
ESSI_CLIP = (8, 40)
ESSI_LIMITED_CUTOFF = 18  # HEARTLAND point trigger


# -----------------------------------------------------------------------------
# Comorbidities
# -----------------------------------------------------------------------------
# Diabetes base prevalence + HFpEF/obesity bumps (GWTG-HF)
DIABETES_BASE_P = 0.42
DIABETES_HFPEF_BUMP = 0.10
DIABETES_OBESITY_BUMP = 0.08

# Atrial fibrillation
AF_BASE_P = 0.35
AF_ELDERLY_BUMP = 0.10

# CKD stages from eGFR (KDIGO 2012)
# stage: 1 (>=90), 2 (60-89), 3a (45-59), 3b (30-44), 4 (15-29), 5 (<15)
def ckd_stage_from_egfr(egfr: float) -> int:
    """Return KDIGO CKD stage (1-5). Stage 3a and 3b collapsed to 3."""
    if egfr >= 90:
        return 1
    if egfr >= 60:
        return 2
    if egfr >= 30:
        return 3
    if egfr >= 15:
        return 4
    return 5


# -----------------------------------------------------------------------------
# GDMT utilization (CHAMP-HF)
# -----------------------------------------------------------------------------
# Calibrated so P(all four) ~ 0.01 and P(>=1) ~ 0.80 in mixed cohort.
GDMT_RATES = {
    "urban": {
        "acei_arb_arni": 0.55,
        "beta_blocker": 0.75,
        "mra": 0.33,
        "sglt2i": 0.20,
    },
    "rural": {
        "acei_arb_arni": 0.45,
        "beta_blocker": 0.65,
        "mra": 0.22,
        "sglt2i": 0.10,
    },
}
# Safety overrides
SGLT2I_EGFR_MIN = 20.0  # zero out if eGFR below this


# -----------------------------------------------------------------------------
# Hidden generator settings
# -----------------------------------------------------------------------------
PRIOR_HF_HOSP_P = 0.20  # baseline probability before risk-tier reinjection


# -----------------------------------------------------------------------------
# Outcome rates by HEARTLAND tier (1-year)
# -----------------------------------------------------------------------------
# Mortality: MAGGIC 1-yr survival curves stratified by risk + Manemann 2018
#   (social isolation HR 3.74) uplift for the high tier.
# Hospitalization: GWTG-HF 30-day readmission scaled to 1-year incidence using
#   published quarterly readmission patterns.
OUTCOME_RATES = {
    "low":      {"mortality_1yr": 0.06, "hospitalization_1yr": 0.18},
    "moderate": {"mortality_1yr": 0.15, "hospitalization_1yr": 0.35},
    "high":     {"mortality_1yr": 0.32, "hospitalization_1yr": 0.55},
}


# -----------------------------------------------------------------------------
# Time series (AR(1) mean-reverting around baseline)
# -----------------------------------------------------------------------------
TIMESERIES_PARAMS = {
    "phi": 0.7,                 # autoregressive coefficient (mean reversion)
    "sigma_sbp": 6.0,           # mmHg monthly shock SD
    "sigma_dbp": 4.0,
    "sigma_hr": 5.0,
    "sigma_weight_kg": 0.8,
    "sigma_log_bnp": 0.25,      # log-scale noise for BNP
    # Height by sex (m): used once to derive baseline weight from BMI.
    "height_mean_m": {"F": 1.63, "M": 1.76},
    "height_sd_m": 0.07,
}


# -----------------------------------------------------------------------------
# FHIR R4 coding tables
# -----------------------------------------------------------------------------
FHIR_CODES = {
    # ICD-10 Condition codes for HF subtypes and major comorbidities.
    "icd10": {
        "hfref": ("I50.2", "Systolic (congestive) heart failure"),
        "hfmref": ("I50.4", "Combined systolic and diastolic heart failure"),
        "hfpef": ("I50.3", "Diastolic (congestive) heart failure"),
        "diabetes": ("E11.9", "Type 2 diabetes mellitus without complications"),
        "af": ("I48.91", "Unspecified atrial fibrillation"),
        "prior_hf_hosp": ("Z86.79",
                          "Personal history of other diseases of the circulatory system"),
        "ckd": {
            1: ("N18.1", "Chronic kidney disease, stage 1"),
            2: ("N18.2", "Chronic kidney disease, stage 2 (mild)"),
            3: ("N18.30", "Chronic kidney disease, stage 3 unspecified"),
            4: ("N18.4", "Chronic kidney disease, stage 4 (severe)"),
            5: ("N18.5", "Chronic kidney disease, stage 5"),
        },
    },
    # LOINC Observation codes for clinical vitals.
    "loinc": {
        "lvef": ("10230-1", "Left ventricular Ejection fraction", "%"),
        "egfr": ("98979-8", "Glomerular filtration rate/1.73 sq M.predicted by Creatinine-based formula (CKD-EPI 2021)", "mL/min/{1.73_m2}"),
        "bnp": ("30934-4", "Natriuretic peptide B [Mass/volume] in Serum or Plasma", "pg/mL"),
        "sbp": ("8480-6", "Systolic blood pressure", "mm[Hg]"),
        "dbp": ("8462-4", "Diastolic blood pressure", "mm[Hg]"),
        "hr": ("8867-4", "Heart rate", "/min"),
        "bmi": ("39156-5", "Body mass index (BMI) [Ratio]", "kg/m2"),
    },
    # RxNorm medication class codes for GDMT.
    "rxnorm": {
        "on_acei_arb_arni": ("1998", "Angiotensin-converting enzyme inhibitor"),
        "on_beta_blocker": ("18867", "Beta blocker"),
        "on_mra": ("321064", "Mineralocorticoid receptor antagonist"),
        "on_sglt2i": ("1545653", "Sodium-glucose cotransporter 2 inhibitor"),
    },
    # Custom coding for HEARTLAND risk score.
    "heartland_system": "http://heartlandprotocol.org/fhir/CodeSystem/risk-score",
    "reference_date": "2026-01-01",
}


# -----------------------------------------------------------------------------
# REDCap field-type mapping
# -----------------------------------------------------------------------------
# Categoricals with explicit choice encoding. REDCap choice format:
# "code1, label1 | code2, label2 | ..."
REDCAP_CATEGORICALS = {
    "sex": {"F": "Female", "M": "Male"},
    "race": {
        "White": "White",
        "Black": "Black or African American",
        "Hispanic": "Hispanic or Latino",
        "Other": "Other",
    },
    "hf_type": {
        "hfref": "HFrEF (LVEF <40%)",
        "hfmref": "HFmrEF (LVEF 40-49%)",
        "hfpef": "HFpEF (LVEF >=50%)",
    },
    "heartland_risk_tier": {
        "low": "Low (0-4)",
        "moderate": "Moderate (5-8)",
        "high": "High (>=9)",
    },
}

REDCAP_BOOLEAN_COLUMNS = {
    "diabetes", "af",
    "on_acei_arb_arni", "on_beta_blocker", "on_mra", "on_sglt2i",
    "prior_hf_hosp_6mo", "mortality_1yr", "hospitalization_1yr",
}

REDCAP_DROPDOWNS = {
    "rural_urban_code": {str(i): f"RUCA {i}" for i in range(1, 11)},
    "ckd_stage": {str(i): f"Stage {i}" for i in range(1, 6)},
    "ckm_stage": {str(i): f"Stage {i}" for i in range(0, 5)},
}

REDCAP_FIELD_LABELS = {
    "patient_id": "Patient ID",
    "age": "Age (years)",
    "sex": "Sex",
    "race": "Race/ethnicity",
    "state": "US state",
    "county_fips": "County FIPS code (synthetic)",
    "rural_urban_code": "USDA RUCA code",
    "hf_type": "Heart failure type",
    "lvef": "LVEF (%)",
    "egfr": "eGFR (mL/min/1.73m^2)",
    "bnp": "BNP (pg/mL)",
    "sbp": "Systolic BP (mmHg)",
    "dbp": "Diastolic BP (mmHg)",
    "hr": "Heart rate (bpm)",
    "bmi": "BMI (kg/m^2)",
    "diabetes": "Diabetes mellitus",
    "af": "Atrial fibrillation",
    "ckd_stage": "CKD stage (KDIGO)",
    "ckm_stage": "CKM stage (AHA 2023)",
    "distance_to_cardiology_mi": "Distance to cardiology (miles)",
    "social_support_score": "ENRICHD ESSI score (8-40)",
    "prior_hf_hosp_6mo": "Prior HF hospitalization (last 6mo)",
    "on_acei_arb_arni": "On ACEi/ARB/ARNI",
    "on_beta_blocker": "On beta-blocker",
    "on_mra": "On mineralocorticoid receptor antagonist",
    "on_sglt2i": "On SGLT2 inhibitor",
    "gdmt_classes_count": "Number of GDMT classes",
    "heartland_risk_score": "HEARTLAND risk score (0-18)",
    "heartland_risk_tier": "HEARTLAND risk tier",
    "mortality_1yr": "1-year mortality",
    "hospitalization_1yr": "1-year hospitalization",
}


__all__ = [
    # demographics
    "AGE_MEAN", "AGE_SD", "FEMALE_FRACTION_DEFAULT",
    "RACE_DISTRIBUTION", "RURAL_HEAVY_STATES", "URBAN_HEAVY_STATES",
    # clinical
    "LVEF_PARAMS", "EGFR_LOG_MEAN", "EGFR_LOG_SD", "EGFR_CLIP",
    "EGFR_ELDERLY_SHIFT", "BNP_LOG_MEAN", "BNP_LOG_SD", "BNP_HFPEF_MULTIPLIER",
    "SBP_MEAN", "SBP_SD", "SBP_CLIP", "SBP_RURAL_SHIFT",
    "HR_MEAN", "HR_SD", "HR_CLIP",
    "BMI_MEAN", "BMI_SD", "BMI_CLIP", "BMI_HFPEF_SHIFT",
    "DBP_SBP_COEF", "DBP_NOISE_SD", "DBP_CLIP",
    "VITALS_ORDER", "CORR_VITALS", "SBP_DBP_TARGET_CORR",
    # rural
    "DISTANCE_RURAL_LOG_MEAN", "DISTANCE_RURAL_LOG_SD",
    "DISTANCE_URBAN_LOG_MEAN", "DISTANCE_URBAN_LOG_SD", "DISTANCE_CLIP",
    "ESSI_URBAN_MEAN", "ESSI_URBAN_SD", "ESSI_RURAL_MEAN", "ESSI_RURAL_SD",
    "ESSI_CLIP", "ESSI_LIMITED_CUTOFF",
    # comorbid
    "DIABETES_BASE_P", "DIABETES_HFPEF_BUMP", "DIABETES_OBESITY_BUMP",
    "AF_BASE_P", "AF_ELDERLY_BUMP", "ckd_stage_from_egfr",
    # gdmt
    "GDMT_RATES", "SGLT2I_EGFR_MIN",
    # outcomes + timeseries
    "OUTCOME_RATES", "TIMESERIES_PARAMS",
    # exports
    "FHIR_CODES", "REDCAP_CATEGORICALS", "REDCAP_BOOLEAN_COLUMNS",
    "REDCAP_DROPDOWNS", "REDCAP_FIELD_LABELS",
    # misc
    "PRIOR_HF_HOSP_P",
]
