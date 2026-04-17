/**
 * Evidence — registry citations anchoring each clinical distribution.
 */

type Source = {
  name: string;
  role: string;
  full: string;
};

const SOURCES: Source[] = [
  {
    name: "PARADIGM-HF",
    role: "HFrEF LVEF + BNP baselines",
    full: "McMurray JJV et al. N Engl J Med 2014;371:993–1004.",
  },
  {
    name: "DELIVER",
    role: "HFpEF LVEF + BMI baselines",
    full: "Solomon SD et al. N Engl J Med 2022;387:1089–1098.",
  },
  {
    name: "EMPEROR-Preserved",
    role: "HFpEF supporting cohort",
    full: "Anker SD et al. N Engl J Med 2021;385:1451–1461.",
  },
  {
    name: "STRONG-HF",
    role: "eGFR distribution",
    full: "Mebazaa A et al. Lancet 2022;400:1938–1952.",
  },
  {
    name: "CHAMP-HF",
    role: "GDMT utilization rates",
    full: "Greene SJ et al. J Am Coll Cardiol 2018;72:351–366.",
  },
  {
    name: "GWTG-HF",
    role: "Demographics + SBP/HR + readmission",
    full: "Get With The Guidelines-Heart Failure registry (American Heart Association).",
  },
  {
    name: "NHANES",
    role: "Race distribution",
    full: "National Health and Nutrition Examination Survey (CDC).",
  },
  {
    name: "ENRICHD ESSI",
    role: "Social-support score",
    full: "ENRICHD Social Support Instrument (8 items, 5-pt Likert, 8–40).",
  },
  {
    name: "NPPES NPI",
    role: "Distance-to-cardiology",
    full: "National Plan and Provider Enumeration System (CMS).",
  },
  {
    name: "KDIGO 2012",
    role: "CKD staging from eGFR",
    full: "Kidney Disease: Improving Global Outcomes CKD work group.",
  },
  {
    name: "AHA 2023 CKM",
    role: "Cardiovascular-Kidney-Metabolic staging",
    full: "Presidential Advisory. DOI 10.1161/CIR.0000000000001184.",
  },
  {
    name: "Manemann 2018",
    role: "Social isolation HR uplift (3.74x)",
    full: "Manemann SM et al. J Am Heart Assoc 2018;7:e008069.",
  },
];

export function Evidence() {
  return (
    <section className="border-b border-grid bg-terminal">
      <div className="mx-auto max-w-[1200px] px-6 py-24 md:py-32">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-12 md:gap-12">
          <div className="md:col-span-5">
            <p className="font-editorial text-[12.5px] uppercase tracking-[0.18em] text-alert">
              Evidence base
            </p>
            <h2 className="mt-5 text-[clamp(2rem,4vw,3rem)] font-editorial font-semibold leading-[1.08] tracking-[-0.02em] text-cool">
              Every distribution,{" "}
              <span className="font-display italic font-normal text-cool/70">
                a cited source.
              </span>
            </h2>
            <p className="mt-6 max-w-md font-editorial text-[15.5px] leading-relaxed text-cool/70">
              The constants that drive every random draw live in
              `registries.py` with inline citations. If a reviewer asks why
              a number is what it is, the answer is in the code.
            </p>
          </div>
          <div className="md:col-span-7">
            <ul className="divide-y divide-grid">
              {SOURCES.map((s) => (
                <li key={s.name} className="flex flex-col py-4 md:flex-row md:items-baseline md:justify-between md:gap-8">
                  <div>
                    <p className="font-editorial text-[15px] font-semibold text-cool">
                      {s.name}
                    </p>
                    <p className="mt-0.5 font-editorial text-[13px] text-alert/90">
                      {s.role}
                    </p>
                  </div>
                  <p className="mt-1 max-w-md font-editorial text-[13px] leading-relaxed text-cool/65 md:mt-0 md:text-right">
                    {s.full}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
