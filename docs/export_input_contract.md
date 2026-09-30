# Candidate export input and file contract

Applies to candidate0.3.0, not to published0.2.2. These APIs accept complete
synthetic cohort tables, not arbitrary patient datasets. This is structural
validation, not PHI detection, clinical validation or institutional acceptance.

## Before any output

- Require a DataFrame with unique string column names and every standard
  `generator.OUTPUT_COLUMNS` field. Only the two optional annual outcome fields
  may be added, together. Reject other columns instead of silently dropping or
  exporting an unreviewed schema. Empty tables still require the complete schema.
- IDs must be unique case-insensitively, ASCII letters/digits/dot/hyphen, start
  with a letter/digit, and be at most64 characters. Do not coerce numbers or
  paths into IDs. Reject duplicate IDs, separators, absolute paths and dot paths.
- Require complete finite numbers representable as JSON numbers; reject strings,
  missing values, boolean measurements and temporal scalars. Reject values whose
  conversion to the exported binary64 number changes their exact numeric value;
  do not round a large integer or higher-precision float into another value.
  Require whole age>=0 that produces a birth year1–reference_year at the fixed
  reference date; render the year with four digits, including leading zeros.
  This is a FHIR date boundary, not a physiological age eligibility rule.
- Binary fields accept explicit booleans or numeric0/1 only. Validate modeled
  category codes, sexF/M, uppercase two-letter state and five-digit synthetic
  county string. No real geographic identity is inferred. FHIR retains its
  existing unknown-race mapping for nonempty strings; REDCap rejects categories
  absent from its declared choices. No unknown sex is silently converted to male.
- Check the GDMT count against the four flags. Recompute the proposed score from
  all ten inputs and reject disagreement with the supplied total or tier; never
  silently fix them. No new weight, clinical cutoff, ESSI scale or range is added.
- Validate all rows before serializing or touching output. Preserve caller data
  and index. REDCap explicitly orders record_id first and normalizes binary and
  integer category serialization; FHIR ignores no extra source columns silently.

## File ownership

Create only requested target files. Preflight every exact target and refuse an
existing file, directory or symbolic link. Use exclusive file creation too, so
a target appearing after preflight is not overwritten. A nested output folder
is created only after validation and serialization succeed.

The whole batch is **not an atomic filesystem transaction**: a later I/O failure
may leave newly created earlier files. Existing targets are never intentionally
overwritten or deleted; do not promise rollback or race-free parent directories.
Use a new caller-owned directory/prefix for each export. The selected directory
and its parents are trusted caller-controlled paths, not a security sandbox.

FHIR filenames remain `{patient_id}.json`; REDCap data uses `out_prefix.with_suffix`
with `.csv` and dictionary uses `{out_prefix.name}_datadict.csv`, preserving the
existing naming behavior. No package, dataset or hosted schema changes here.

## Separate semantic gate

This contract does not repair legacy RxNorm/ICD/LOINC interpretations, synthetic
labels or the Template crosswalk. Those require a following semantic lot. Plain
R4 collections assert no IG/US Core profile conformance. Structural acceptance
here is not terminology validation, clinical approval or permission for PHI.

Technical reference: [FHIR R4 primitive data types](https://hl7.org/fhir/R4/datatypes.html),
read2026-09-29. The filename policy is deliberately narrower than the FHIR id
grammar; it is not presented as the full standard grammar.
