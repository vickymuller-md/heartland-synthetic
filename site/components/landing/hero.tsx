import { InstallCommand } from "./install-command";

/**
 * Hero — mirrors the package-first pattern used by heartland-scoring-site
 * and heartland-redcap-site: headline naming the identity, short subhead,
 * install command as the primary CTA, secondary anchor links below.
 */
export function Hero() {
  return (
    <section className="relative overflow-hidden bg-terminal">
      <div className="mx-auto max-w-[1200px] px-6 pb-24 pt-16 md:pb-32 md:pt-24">
        <div className="grid grid-cols-1 items-center gap-16 md:grid-cols-12 md:gap-12">
          <div className="md:col-span-7">
            <p className="inline-flex items-center gap-2 rounded-full border border-grid bg-panel px-3.5 py-1.5 font-editorial text-[12px] tracking-tight text-cool/80">
              <span
                className="h-1.5 w-1.5 rounded-full bg-signal"
                aria-hidden
              />
              MIT licensed · PyPI + Zenodo · Pure Python
            </p>

            <h1 className="mt-7 text-[clamp(2.5rem,6vw,5rem)] font-editorial font-semibold leading-[1.04] tracking-[-0.025em] text-cool">
              Synthetic HF cohorts,{" "}
              <span className="font-display italic font-normal text-alert">
                with the variables Synthea leaves out.
              </span>
            </h1>

            <p className="mt-7 max-w-xl font-editorial text-[17px] leading-[1.65] text-cool/75 md:text-[18px]">
              A Python package that generates clinically-realistic
              heart-failure patient cohorts with the 10 HEARTLAND risk
              variables — including distance-to-cardiology and social
              support — that Synthea and other generators do not model.
              Ships the scoring engine, a time-series generator, and FHIR
              / REDCap exporters.
            </p>

            <div className="mt-10">
              <InstallCommand />
            </div>

            <div className="mt-10 flex flex-col items-start gap-x-10 gap-y-4 sm:flex-row sm:items-center">
              <a
                href="#features"
                className="group inline-flex items-center gap-2 font-editorial text-[15px] font-medium text-cool/85 transition-colors hover:text-alert"
              >
                What&rsquo;s inside
                <span className="transition-transform group-hover:translate-x-1">
                  ↓
                </span>
              </a>
              <a
                href="https://github.com/vickymuller-md/heartland-synthetic"
                target="_blank"
                rel="noopener noreferrer"
                className="group inline-flex items-center gap-2 font-editorial text-[15px] font-medium text-cool/85 transition-colors hover:text-alert"
              >
                View on GitHub
                <span className="transition-transform group-hover:translate-x-1">
                  →
                </span>
              </a>
            </div>

            <p className="mt-12 max-w-md font-editorial text-[12.5px] leading-relaxed text-stone">
              Synthetic data only — no PHI, by design. Distributions are
              anchored to published registries (PARADIGM-HF, DELIVER,
              CHAMP-HF, ENRICHD, GWTG-HF).
            </p>
          </div>

          <div className="md:col-span-5">
            <CodeIllustration className="mx-auto h-auto w-full max-w-[480px]" />
          </div>
        </div>
      </div>
    </section>
  );
}

/**
 * CodeIllustration — soft terminal panel with a cohort frame preview
 * and a HEARTLAND tier chip. Uses the same cream-blob motif as the
 * app hero (`medical-cross.tsx`) for visual continuity across subdomains.
 */
function CodeIllustration({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 520 520"
      fill="none"
      aria-hidden="true"
    >
      <ellipse
        cx="270"
        cy="270"
        rx="240"
        ry="232"
        fill="currentColor"
        opacity="0.55"
        className="text-panel-hi"
      />
      <path
        d="M 20 400 Q 130 360 260 390 T 510 380"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        className="text-cool/35"
      />
      <path
        d="M 20 440 Q 150 410 280 432 T 510 425"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        className="text-cool/20"
      />

      <g transform="translate(95 110)">
        <rect
          width="330"
          height="200"
          rx="18"
          fill="currentColor"
          className="text-panel"
          stroke="currentColor"
          strokeWidth="1.2"
        />
        <circle cx="22" cy="22" r="5" fill="currentColor" className="text-alert" />
        <circle cx="40" cy="22" r="5" fill="currentColor" className="text-signal" />
        <circle cx="58" cy="22" r="5" fill="currentColor" className="text-stone/60" />

        <g
          className="text-cool/55"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        >
          <line x1="22" y1="56" x2="128" y2="56" />
          <line x1="22" y1="74" x2="210" y2="74" />
          <line x1="22" y1="92" x2="176" y2="92" />
          <line x1="22" y1="110" x2="244" y2="110" />
          <line x1="22" y1="128" x2="158" y2="128" />
        </g>

        <g transform="translate(198 152)">
          <rect
            width="112"
            height="32"
            rx="16"
            fill="currentColor"
            className="text-alert/15"
          />
          <circle cx="18" cy="16" r="5" fill="currentColor" className="text-alert" />
          <text
            x="30"
            y="21"
            fontFamily="system-ui, sans-serif"
            fontSize="13"
            fontWeight="600"
            className="fill-alert"
          >
            HIGH · score 12
          </text>
        </g>
      </g>

      <g transform="translate(150 340)">
        <rect
          width="220"
          height="70"
          rx="14"
          fill="currentColor"
          className="text-panel"
          stroke="currentColor"
          strokeWidth="1"
        />
        <path
          d="M 12 35 H 60 L 68 28 L 74 44 L 80 16 L 88 58 L 94 35 H 142 L 150 28 L 156 44 L 162 16 L 170 58 L 176 35 H 208"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
          className="text-alert"
        />
      </g>
    </svg>
  );
}
