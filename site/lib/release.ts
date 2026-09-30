// Update published identity only after registry readback, never from source version alone.
export const CANDIDATE_VERSION = "0.3.0";
export const PUBLISHED_VERSION = "0.2.2";
export const RELEASE_CHECK_DATE = "2026-09-29";
export const INSTALL_COMMAND = `pip install heartland-synthetic==${PUBLISHED_VERSION}`;
export const SYNTHETIC_DESCRIPTION =
  "Synthetic heart-failure cohorts for research and software testing, with modeled rural access, a social-support proxy, and proposed HEARTLAND point criteria.";
export const SYNTHETIC_BOUNDARY =
  "Synthetic research and educational use only. Do not supply real patient, personal, or health information. This software is not a de-identification system and does not authorize patient care. The HEARTLAND framework remains proposed pending validation against clinical outcomes.";
