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
            Make simulation assumptions{" "}
            <span className="font-display italic font-normal text-alert">
              visible and inspectable
            </span>
            .
          </h2>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3 md:gap-8">
          <StatCard
            value="10"
            heading="HEARTLAND variables"
            note="Ten weighted criteria, including modeled distance and a legacy social-support proxy."
          />
          <StatCard
            value="3"
            heading="proposed tiers"
            note="Low 0–4, moderate 5–8, high 9–18. Point groups, not predicted probabilities."
            accent
          />
          <StatCard
            value="MIT"
            heading="open source"
            note="Open source for synthetic research and software testing. Publication is separate from clinical validation."
          />
        </div>

        <p className="mx-auto mt-16 max-w-2xl text-center font-editorial text-[15.5px] leading-relaxed text-cool/75">
          Constants and sampling rules can be inspected in the source.
          Background references motivate the domains; they do not establish
          parameter fitting or clinical calibration.{" "}
          <a href="#assumptions" className="text-cool underline underline-offset-4">Read the modeling boundaries.</a>
        </p>

        <div className="mt-20 grid grid-cols-1 gap-5 md:grid-cols-2 md:gap-6">
          <Disclaimer heading="Synthetic only">
            Generator outputs and the bundled benchmark are synthetic.
            Caller-supplied tables are not anonymized or screened for PHI.
            Do not enter real patient, personal, or health information.
          </Disclaimer>
          <Disclaimer heading="Proposed, pending validation">
            This is a research and educational implementation-support resource.
            Structural input checks and synthetic tests do not establish
            clinical validity, safety, regulatory status or patient-care authorization.
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
