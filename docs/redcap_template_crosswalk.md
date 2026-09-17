# Crosswalk: `heartland-synthetic` cohort → HEARTLAND REDCap Instrument Template

`export_redcap()` writes a **standalone** single-form instrument
(`heartland_cohort`) whose data dictionary is generated from the cohort
columns. It is **not** an import file for the
[HEARTLAND REDCap Instrument Template](https://github.com/vickymuller-md/redcap-template)
(75 fields, 5 forms, `bl_*` / `gdmt_*` / `mo_*` / `out_*` names). No
direct-import adapter is provided.

This table documents, field by field, what a mapping between the two would
look like, so the gap is explicit rather than implied. Only `record_id`,
`state`, `county_fips`, `age`, `sex`, `race` and `gdmt_classes_count` share a
name with the Template, and a shared name is not a shared coding.

## Missingness rules

| Rule | Meaning |
|-|-|
| **M1** | Template field has no source in the generator → leave blank. REDCap treats blank as missing; the Template defines no `-99` sentinel. |
| **M2** | Template field is `calc` / `@CALCTEXT` → omit from the import; REDCap recalculates it. |
| **M3** | Source exists but the target category is not derivable → `Unknown` where the Template offers a code, otherwise blank. |

## Field mapping

| Generator field | Template field | Transformation | Missingness | Notes |
|-|-|-|-|-|
| `patient_id` | `record_id` | `HS-000001` → sequential integer 1..n | — | The Template auto-assigns on import; the `HS-` prefix is not a numeric record_id |
| — | `enr_date`, `consent_date` | — | M1 | No enrolment / consent dates are generated |
| — | `facility_name`, `facility_cah`, `facility_tier` | — | M1 | The generator does not model a facility |
| `state` | `state` | identity | — | Only field with identical name and semantics |
| `county_fips` | `county_fips` | identity | — | **Synthetic and non-ANSI in both artifacts.** Never present it as a real FIPS code |
| `rural_urban_code` (1–10) | `rural_urban` (1–4) | collapse: 1-3→`1`; 4-6→`2`; 7-9→`3`; 10→`4` | — | Declared, irreversible loss of granularity |
| `age` | `age` | identity (int) | — | Template validates 18–110; the default `age_range` (45,95) fits |
| `sex` (`F`/`M`) | `sex` (1/2/3) | `M`→`1`, `F`→`2` | — | `3` is never produced by the generator |
| `race` (4 levels) | `race___1..7` (checkbox) | `White`→`race___5=1`; `Black`→`race___3=1`; `Other`→`race___6=1`; `Hispanic`→`race___7=1` (Unknown) | M3 | All other `race___N` = `0`. `Hispanic` is **not** a race — it goes to `ethnicity` |
| `race` (level `Hispanic`) | `ethnicity` (1/2/3) | `Hispanic`→`1`; all others→`3` (Unknown) | M3 | Symmetric to the FHIR mapping: never infer "Not Hispanic" |
| `prior_hf_hosp_6mo` | `bl_prior_hf_hosp_6mo` | 0/1 | — | yesno |
| `lvef` | `bl_lvef_pct` | round to int | — | Template validates 10–80; `LVEF_PARAMS` produces 5–75, so **values 5–9 would be rejected** |
| `hf_type` | `bl_lvef_category` | `hfref`→`1`, `hfmref`→`2`, `hfpef`→`3` | — | Consistent with the Template cut-offs |
| `egfr` | `bl_egfr` | identity (number) | — | Template validates 5–150; `EGFR_CLIP` (15,120) fits |
| — | `bl_np_type` | constant `1` (BNP) | — | The generator models BNP only. A documented scope limit, not a licence to convert BNP↔NT-proBNP |
| `bnp` | `bl_np_value` | identity | — | With `bl_np_type=1` the Template `calc` applies the ≥500 cut-off, identical to the scoring engine |
| `sbp` | `bl_sbp_admit` | int | — | Template validates 60–250; `SBP_CLIP` (80,200) fits |
| `diabetes` | `bl_diabetes` | 0/1 | — | yesno |
| `ckm_stage` (0–4) | `bl_ckm_stage` (0–4) | identity | — | Identical coding |
| `distance_to_cardiology_mi` | `bl_distance_cardio_mi` | round to int | — | Template validates 0–500; `DISTANCE_CLIP` (0.5,400) fits after rounding |
| `social_support_score` (ESSI 8–40) | `bl_social_support_limited` | `1` if `< 18` else `0` | — | Same cut-off as `ESSI_LIMITED_CUTOFF` |
| `social_support_score` | `bl_enrichd_score` | identity | — | **Range conflict:** the Template validates 7–35, the generator uses the published ENRICHD/ESSI scale 8–40. Values 36–40 would be rejected |
| — | `bl_pro_consent` | — | M1 | PRO consent is not modeled |
| `heartland_risk_score` | `bl_risk_score` | — | **M2** | `calc` field; REDCap recalculates. Useful as a test oracle: the recalculation must match the generator |
| `heartland_risk_tier` | `bl_risk_tier` | — | **M2** | `@CALCTEXT`; same oracle role |
| `on_acei_arb_arni` | `gdmt_arni_acei_arb_drug` | — | M1 | **Not mappable:** the generator has a binary class flag, the Template wants a specific drug + dose + target + date. Choosing a drug would be fabrication |
| `on_beta_blocker` / `on_mra` / `on_sglt2i` | `gdmt_bb_drug` / `gdmt_mra_drug` / `gdmt_sglt2_drug` | — | M1 | Same. Partial alternative: write `0` (None) when the class flag is 0 and leave blank when it is 1 |
| `gdmt_classes_count` | `gdmt_classes_count` | — | **M2** | Identical name, but a `calc` field in the Template |
| `mortality_1yr` | `out_vital_status` | 1→`2` (Deceased); 0→`1` (Alive) | — | `3` (lost to follow-up) is never produced |
| `hospitalization_1yr` | `out_hf_hosp_count` | 1→`1`; 0→`0` | — | A binary indicator mapped onto a count: this is a floor, not the real count |
| time series (`generate_time_series`) | `monthly_followup` form | one row per (patient, month) with `redcap_repeat_instrument=monthly_followup`, `redcap_repeat_instance=month`; `sbp`→`mo_sbp`, `dbp`→`mo_dbp`, `hr`→`mo_hr`, `bnp`→`mo_bnp`, `weight_kg`→`mo_weight_lb` (×2.20462), `hosp_event`→`mo_hosp_any` | — | No source for `mo_spo2`, `mo_k`, `mo_track`, `mo_kccq12_score` (M1) |
| — | `out_death_date`, `out_death_cardiovascular`, `out_hf_ed_count`, `out_days_alive_oh`, `out_gdmt_optimized`, `out_kccq12_12mo` | — | M1 | No source in the generator |

## Resulting coverage

Of the Template's 75 fields, roughly 24 are fillable from the generator, 3 are
`calc` / `@CALCTEXT` (omitted by design), and about 48 stay blank. Such an
import would load, but would produce a mostly empty project.
