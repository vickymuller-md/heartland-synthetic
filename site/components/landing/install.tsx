/**
 * Install CTA — pip block + a minimal usage snippet. Mono style picks up
 * the Sora mono-editorial variable from layout.
 */
import { INSTALL_COMMAND, PUBLISHED_VERSION, SOFTWARE_ARCHIVE_DOI } from "@/lib/release";

export function Install() {
  return (
    <section
      id="install"
      className="border-b border-grid bg-panel"
    >
      <div className="mx-auto max-w-[1200px] px-6 py-24 md:py-32">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-12 md:gap-16">
          <div className="md:col-span-5">
            <p className="font-editorial text-[12.5px] uppercase tracking-[0.18em] text-alert">
              Install
            </p>
            <h2 className="mt-5 text-[clamp(2rem,4vw,3rem)] font-editorial font-semibold leading-[1.08] tracking-[-0.02em] text-cool">
              A short Python example,{" "}
              <span className="font-display italic font-normal text-cool/70">
                one cohort.
              </span>
            </h2>
            <p className="mt-6 max-w-md font-editorial text-[15.5px] leading-relaxed text-cool/70">
              Python 3.10+ with NumPy, pandas and SciPy. The command pins
              published v{PUBLISHED_VERSION}, including the 0.3.x structural input
              and export checks. Those checks do not authorize patient care.
              No GPU or server runtime is required.
            </p>

            <div className="mt-8 space-y-2 font-editorial text-[13px] text-cool/70">
              <p>
                <span className="text-stone">Package:</span>{" "}
                <a
                  href="https://pypi.org/project/heartland-synthetic/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline decoration-dotted underline-offset-4 hover:text-alert"
                >
                  pypi.org/project/heartland-synthetic
                </a>
              </p>
              <p>
                <span className="text-stone">Source:</span>{" "}
                <a
                  href="https://github.com/vickymuller-md/heartland-synthetic"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline decoration-dotted underline-offset-4 hover:text-alert"
                >
                  github.com/vickymuller-md/heartland-synthetic
                </a>
              </p>
              <p>
                <span className="text-stone">Cite:</span>{" "}
                <a
                  href={SOFTWARE_ARCHIVE_DOI}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline decoration-dotted underline-offset-4 hover:text-alert"
                >
                  Zenodo software v{PUBLISHED_VERSION}
                </a>
              </p>
            </div>
          </div>

          <div className="min-w-0 md:col-span-7">
            <CodeBlock
              label="pip"
              lines={[`$ ${INSTALL_COMMAND}`]}
            />
            <div className="h-4" />
            <CodeBlock
              label="generate_cohort"
              lines={[
                "from heartland_synthetic import (",
                "    generate_cohort, HeartlandCohortConfig,",
                ")",
                "",
                "cfg = HeartlandCohortConfig(",
                "    n_patients=500,",
                "    rural_fraction=0.7,",
                "    include_outcomes=True,",
                "    seed=42,",
                ")",
                "df = generate_cohort(cfg)",
                "df[\"heartland_risk_tier\"].value_counts()",
              ]}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function CodeBlock({ label, lines }: { label: string; lines: string[] }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-grid bg-terminal-deep">
      <div className="flex items-center justify-between border-b border-grid bg-terminal px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-alert/80" aria-hidden />
          <span className="h-2.5 w-2.5 rounded-full bg-signal/80" aria-hidden />
          <span className="h-2.5 w-2.5 rounded-full bg-stone/60" aria-hidden />
        </div>
        <span className="font-editorial text-[11px] uppercase tracking-[0.14em] text-stone">
          {label}
        </span>
      </div>
      <pre tabIndex={0} role="region" aria-label={`${label} code example`} className="overflow-x-auto px-5 py-5 font-mono text-[13.5px] leading-relaxed text-cool focus-visible:outline-2 focus-visible:outline-alert">
        {lines.join("\n")}
      </pre>
    </div>
  );
}
