import Link from "next/link";
import { HeartLineMark } from "./heart-mark";

/**
 * Masthead — mirrors the pattern used by heartland-scoring-site,
 * heartland-redcap-site, and app.heartlandprotocol.org: sticky nav with
 * wordmark, version badge, section anchors, and a two-CTA cluster
 * (outlined GitHub + primary install).
 */
export function Masthead() {
  return (
    <header className="sticky top-0 z-40 border-b border-grid bg-terminal/85 backdrop-blur supports-[backdrop-filter]:bg-terminal/70">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between gap-8 px-6 py-5">
        <Link href="/" className="group flex items-center gap-2.5">
          <HeartLineMark className="h-7 w-7 text-alert transition-transform group-hover:scale-105" />
          <span className="font-editorial text-[18px] font-semibold tracking-tight text-cool">
            heartland-synthetic
          </span>
          <span className="ml-1 hidden rounded-full border border-grid bg-panel px-2 py-0.5 font-mono text-[10.5px] tracking-tight text-cool/70 sm:inline-flex">
            v0.2.0
          </span>
        </Link>

        <nav className="hidden items-center gap-8 font-editorial text-[14px] text-cool/80 md:flex">
          <Link href="#features" className="transition-colors hover:text-alert">
            Features
          </Link>
          <Link href="#install" className="transition-colors hover:text-alert">
            Install
          </Link>
          <a
            href="https://app.heartlandprotocol.org"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-alert"
          >
            The App
          </a>
          <a
            href="https://doi.org/10.5281/zenodo.18566403"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-alert"
          >
            Research
          </a>
        </nav>

        <div className="flex items-center gap-2">
          <a
            href="https://github.com/vickymuller-md/heartland-synthetic"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden items-center gap-2 rounded-full border border-grid bg-panel px-4 py-2.5 font-editorial text-[13.5px] font-medium text-cool/85 transition-colors hover:border-cool/40 hover:text-cool sm:inline-flex"
          >
            GitHub
            <span className="text-[11px] text-stone">↗</span>
          </a>
          <a
            href="https://pypi.org/project/heartland-synthetic/"
            target="_blank"
            rel="noopener noreferrer"
            className="group inline-flex items-center gap-2 rounded-full bg-cool px-5 py-2.5 font-editorial text-[13.5px] font-medium text-terminal transition-colors hover:bg-alert hover:text-cool"
          >
            pip install
            <span className="transition-transform group-hover:translate-x-0.5">
              →
            </span>
          </a>
        </div>
      </div>
    </header>
  );
}
