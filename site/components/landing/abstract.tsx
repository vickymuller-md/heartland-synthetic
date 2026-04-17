/**
 * "Why this exists" — three stat cards + closing line, disclaimer pair.
 * Mirrors heartland-app/components/landing/abstract.tsx structure.
 */
export function Abstract() {
  return (
    <section className="border-y border-grid bg-panel">
      <div className="mx-auto max-w-[1200px] px-6 py-24 md:py-32">
        <div className="mx-auto max-w-3xl text-center">
          <p className="font-editorial text-[12.5px] uppercase tracking-[0.18em] text-alert">
            Why this exists
          </p>
          <h2 className="mt-5 text-[clamp(1.85rem,3.5vw,2.85rem)] font-editorial font-semibold leading-[1.15] tracking-[-0.015em] text-cool">
            Synthea and peers don&rsquo;t model the{" "}
            <span className="font-display italic font-normal text-alert">
              rural HF barriers
            </span>
            . This package does.
          </h2>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3 md:gap-8">
          <StatCard
            value="10"
            heading="HEARTLAND variables"
            note="Including distance-to-cardiology and social support — omitted by MAGGIC / GWTG-HF / SHFM."
          />
          <StatCard
            value="65"
            heading="passing tests"
            note="Scoring correctness, distribution validation, reproducibility, copula correlation, export roundtrips."
            accent
          />
          <StatCard
            value="MIT"
            heading="open source"
            note="PyPI + Zenodo DOI. Free for every researcher and institution that wants it."
          />
        </div>

        <p className="mx-auto mt-16 max-w-2xl text-center font-editorial text-[15.5px] leading-relaxed text-cool/75">
          Every clinical distribution is anchored to a published registry.
          Every output column cites a source in the code.{" "}
          <span className="text-cool">No black box, no hidden priors.</span>
        </p>

        <div className="mt-20 grid grid-cols-1 gap-5 md:grid-cols-2 md:gap-6">
          <Disclaimer heading="Synthetic only">
            No real patient data passes through this package. Distributions
            are drawn from published literature; nothing written to disk
            comes from a registry subject or EHR record. By design.
          </Disclaimer>
          <Disclaimer heading="Not a medical device">
            `heartland-synthetic` is a research tool for cohort simulation
            and scoring engine validation. It is not intended for clinical
            decision-making on real patients and has not been validated
            against a prospective HEARTLAND-scored cohort.
          </Disclaimer>
        </div>
      </div>
    </section>
  );
}

function Disclaimer({
  heading,
  children,
}: {
  heading: string;
  children: React.ReactNode;
}) {
  return (
    <aside
      role="note"
      className="rounded-2xl border border-grid bg-terminal p-6"
    >
      <p className="font-editorial text-[12.5px] uppercase tracking-[0.14em] text-alert">
        {heading}
      </p>
      <p className="mt-3 font-editorial text-[14px] leading-relaxed text-cool/75">
        {children}
      </p>
    </aside>
  );
}

function StatCard({
  value,
  heading,
  note,
  accent,
}: {
  value: string;
  heading: string;
  note: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-grid bg-terminal p-8 transition-colors hover:border-cool/40">
      <p
        className={
          "font-editorial text-5xl font-semibold leading-none tracking-[-0.02em] md:text-6xl " +
          (accent ? "text-alert" : "text-cool")
        }
      >
        {value}
      </p>
      <p className="mt-5 font-editorial text-[15.5px] font-medium text-cool">
        {heading}
      </p>
      <p className="mt-1.5 font-editorial text-[14px] leading-relaxed text-cool/65">
        {note}
      </p>
    </div>
  );
}
