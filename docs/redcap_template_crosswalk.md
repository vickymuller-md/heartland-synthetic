# REDCap export and Template mapping limits

Reviewed 2026-09-29 for the **heartland-synthetic 0.3.0 candidate**.
`export_redcap` produces the standalone `heartland_cohort` instrument, not an
import into the separately versioned [HEARTLAND Template](https://github.com/vickymuller-md/redcap-template).
Its 18-column dictionary contains 29 fields without annual outcomes or 31 with
both. Data preserve categorical codes, field names (except patient_id→record_id)
and modeled values. No direct-import adapter is supplied.

The former 75-field/5-form crosswalk is a historical comparison, **not an approved
conversion recipe**. Its assumptions about ESSI, CKM, county identifiers,
medication non-use, hospitalization counts and guaranteed import success are
withdrawn here. Prior text remains in version history, not as current advice.
This review does not certify the current Template's configuration or a successful
institutional import. The target dictionary was preserved, not regenerated:
`instruments/heartland_data_dictionary.csv`, repository revision
`2619d6468b5b0b0dd7cfe766363d9b8dacc88775`, SHA-256
`e962bb8dd4668c2f085f8f40e6c92a09ddeca15004f88df47f1a90f3dbd52ea6`.

## Source semantics and possible targets

Target names below identify previously compared fields, not an executable
mapping. Verify the exact target version, encodings, units, valid ranges,
longitudinal events and institutional configuration before preparing an adapter.
Do not fabricate missing source information to make an import pass.

| Source | Previously compared target | Permitted interpretation / gap |
|-|-|-|
| patient_id | record_id | Preserve source identity in an explicit crosswalk if target IDs differ. Never assume automatic numbering or replace IDs with row position without a retained map. |
| age, sex | age, sex | Age is synthetic. F/M encoding is not automatically target 1/2/3; no unmodeled category may be fabricated. |
| race | race checkboxes, ethnicity | Source mixes axes. Hispanic is an ethnicity, not a race; White/Black do not establish Not Hispanic. Other is insufficient to adjudicate a category. Missing/unknown handling must follow the target's actual configuration. |
| state, county_fips | state, county_fips | A state label does not make a synthetic county code real. Do not copy an opaque identifier into a field interpreted as geographic FIPS/GEOID or decode it. |
| rural_urban_code | rural_urban | Sampled RUCA-like code, not a geographic assessment. Any aggregation is a declared lossy simulation transform, not established equivalent classification. |
| hf_type, lvef | bl_lvef_category, bl_lvef_pct | Simulation group is not a diagnosis. Preserve numeric precision; do not round, clip or change an out-of-range value merely to satisfy target validation. |
| egfr, bnp, sbp | bl_egfr, bl_np_type/value, bl_sbp_admit | Units and measurement context must match. BNP-only source provides no NT-proBNP conversion. Synthetic baseline BP does not establish an actual admission measurement. |
| prior_hf_hosp_6mo, diabetes | bl_prior_hf_hosp_6mo, bl_diabetes | Simulated flags, not source-verified history or diagnosis. Preserve simulation status. |
| ckd_stage, ckm_stage | bl_ckm_stage or staging fields | eGFR-derived bin and legacy CKM category are not adjudicated diagnoses/stages. Matching integers do not justify clinical identity mapping. |
| distance_to_cardiology_mi | bl_distance_cardio_mi | Assumed distance, not routing or observed access. Do not round across a score threshold or claim actual travel/geography. |
| social_support_score | bl_enrichd_score, bl_social_support_limited | **No validated mapping.** One generated 8–40 value is not an ESSI questionnaire. The legacy <18 predicate is a simulation convention, not an adjudicated cutoff. Do not clip/rescale into another instrument or fill its clinical flag. |
| heartland_risk_score/tier | bl_risk_score/tier | Do not overwrite target calculated fields. Recalculation can be compared only under an explicitly matched criterion contract; a numeric match alone does not resolve proxy/missingness differences. |
| on_* class flags | gdmt_* drug/dose/date fields | A class flag identifies no drug, dose, start date or receipt. Zero may be an unsampled placeholder, so cannot automatically populate assessed None. Leave unavailable information unasserted. |
| gdmt_classes_count | gdmt_classes_count | Arithmetic sum of flags, not proof of optimization or the same calculated-field semantics. |
| mortality_1yr | out_vital_status | Simulated Bernoulli event, not observed vital status, death date, follow-up completion or consent. No automatic mapping. |
| hospitalization_1yr | out_hf_hosp_count | A binary indicator is not an exact count: 1 is a simulated event flag, not exactly one admission. No automatic count conversion. |
| monthly simulated rows | monthly_followup | Independent draws can disagree with annual flags. No actual dates, visits or repeating configuration are established; weight units require explicit conversion in any future adapter. |
| No source | consent, facility, treatment receipt, clinical outcomes | Do not invent dates, consent, staffing, track assignment, treatment delivery, losses to follow-up or outcomes. |

## Missingness and local verification

The candidate requires its complete synthetic schema; it does not coerce absent
source values to 0. Annual outcome fields are both present or both absent.
Dictionary notes identify simulation proxies, placeholder medication flags and
assumed outcomes. No ESSI validation range or new clinical threshold is added.

For a future Template adapter, leave unavailable information unasserted and
follow the target's declared missing-data codes. Never assume blank, 0, None,
Unknown or a sentinel are interchangeable. Calculated fields, repeating rows
and record identity require their own contracts and tests.

Local tests check 29/31-column consistency, choice-code membership, labels,
notes, identities, values and dtype-independent empty dictionaries. They do
not establish institutional import, permissions, calculations, round-trip
behavior or clinical approval. The earlier approximate “24 fillable /48 blank”
claim is withdrawn; no current target-field coverage count is asserted without
a version-pinned adapter and executed import receipt.
