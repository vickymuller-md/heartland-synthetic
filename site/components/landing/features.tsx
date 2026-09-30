/**
 * "What's inside" — 8 feature cards. Mirrors heartland-app modules.tsx.
 */

type Feature = {
  title: string;
  body: string;
  icon: React.ReactNode;
  available: boolean;
};

function Glyph({ d }: { d: string }) {
  return (
    <svg
      className="h-7 w-7 text-alert"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={d} />
    </svg>
  );
}

const FEATURES: Feature[] = [
  {
    title: "Cohort generator",
    body: "`generate_cohort(config)` produces a pandas DataFrame with demographics, vitals, comorbidities, GDMT, and a HEARTLAND score per patient.",
    icon: <Glyph d="M 4 4 H 20 V 20 H 4 Z M 4 9 H 20 M 9 4 V 20" />,
    available: true,
  },
  {
    title: "HEARTLAND scoring",
    body: "Ten weights and three proposed tiers, 0–18 points. The numeric adapter uses BNP and a legacy support proxy. Candidate input checks reject missing values; no clinical validation is implied.",
    icon: <Glyph d="M 4 18 L 9 9 L 13 14 L 17 5 L 20 11 M 4 21 H 20" />,
    available: true,
  },
  {
    title: "Gaussian-copula vitals",
    body: "Six modeled variables: LVEF / eGFR / BNP / SBP / HR / BMI. Correlations and subgroup shifts are assumptions; DBP is generated separately from SBP plus noise.",
    icon: <Glyph d="M 3 12 C 6 6 10 6 12 12 C 14 18 18 18 21 12 M 3 18 C 6 12 10 12 12 18 M 12 6 C 14 12 18 12 21 6" />,
    available: true,
  },
  {
    title: "Time series",
    body: "Monthly AR(1) vitals with simulated events; rows stop after simulated death. These draws are separate from the cohort’s annual outcome flags and can disagree.",
    icon: <Glyph d="M 3 16 L 7 12 L 11 15 L 15 8 L 19 11 L 21 9 M 3 20 H 21" />,
    available: true,
  },
  {
    title: "Outcome model",
    body: "Fixed, illustrative annual event probabilities selected by tier. They are not fitted risk estimates; using them to validate the score would be circular.",
    icon: <Glyph d="M 12 3 L 15 10 H 21 L 16 14 L 18 21 L 12 17 L 6 21 L 8 14 L 3 10 H 9 Z" />,
    available: true,
  },
  {
    title: "REDCap export",
    body: "Writes data plus an 18-column dictionary for its own single-form instrument. Not a direct HEARTLAND Template import; generated files do not prove institutional import success.",
    icon: <Glyph d="M 4 4 H 16 L 20 8 V 20 H 4 Z M 16 4 V 8 H 20 M 8 13 H 16 M 8 17 H 14" />,
    available: true,
  },
  {
    title: "FHIR R4 bundles",
    body: "R4 collection examples with patient, condition, observation and medication statements. The candidate adds qualitative risk, without a probability or profile-conformance claim. Terminology and recipient acceptance require separate verification.",
    icon: <Glyph d="M 6 4 H 18 V 20 H 6 Z M 6 9 H 18 M 12 4 V 20" />,
    available: true,
  },
  {
    title: "Reproducible",
    body: "Seeded cohort and monthly generators repeat in the same runtime. Record configuration and dependency versions; random FHIR UUIDs are not byte-deterministic exports.",
    icon: <Glyph d="M 12 4 A 8 8 0 1 0 20 12 H 15 L 18 9 M 20 12 A 8 8 0 0 1 4 12" />,
    available: true,
  },
];

export function Features() {
  return (
    <section id="features" className="border-b border-grid bg-terminal">
      <div className="mx-auto max-w-[1200px] px-6 py-24 md:py-32">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-12 md:gap-12">
          <div className="md:col-span-5">
            <p className="font-editorial text-[12.5px] uppercase tracking-[0.18em] text-alert">
              What&rsquo;s inside
            </p>
            <h2 className="mt-5 text-[clamp(2rem,4vw,3.25rem)] font-editorial font-semibold leading-[1.05] tracking-[-0.02em] text-cool">
              Eight capabilities,{" "}
              <span className="font-display italic font-normal text-cool/70">
                one import.
              </span>
            </h2>
            <p className="mt-6 max-w-md font-editorial text-[15.5px] leading-relaxed text-cool/70">
              A single Python package. No microservices, no containers, no
              external APIs — install it in a virtualenv and start
              generating synthetic cohorts with a short script.
            </p>
          </div>
          <div className="md:col-span-7" />
        </div>

        <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <article
              key={f.title}
              className="group flex h-full flex-col rounded-2xl border border-grid bg-panel p-6 transition-all hover:-translate-y-0.5 hover:border-cool/40"
            >
              <div className="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-alert/10">
                {f.icon}
              </div>
              <h3 className="font-editorial text-[17px] font-semibold tracking-tight text-cool">
                {f.title}
              </h3>
              <p className="mt-2 grow font-editorial text-[14px] leading-relaxed text-cool/70">
                {f.body}
              </p>
              <p
                className={
                  "mt-5 inline-flex items-center gap-1.5 font-editorial text-[12px] " +
                  (f.available ? "text-signal" : "text-stone")
                }
              >
                <span
                  aria-hidden
                  className={
                    "h-1.5 w-1.5 rounded-full " +
                    (f.available ? "bg-signal" : "bg-stone")
                  }
                />
                {f.available ? "Implemented in source" : "On the roadmap"}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
