import { Masthead, Colophon } from "@heartland/ui";
import { Abstract } from "@/components/landing/abstract";
import { Evidence } from "@/components/landing/evidence";
import { Features } from "@/components/landing/features";
import { Hero } from "@/components/landing/hero";
import { Install } from "@/components/landing/install";
import { PUBLISHED_VERSION, SOFTWARE_ARCHIVE_DOI, RELEASE_CHECK_DATE, SYNTHETIC_BOUNDARY, SYNTHETIC_DESCRIPTION } from "@/lib/release";

export default function Home() {
  return (
    <>
      <Masthead
        currentSite="synthetic"
        version={`v${PUBLISHED_VERSION}`}
        navItems={[
          { label: "Features", href: "#features" },
          { label: "Install", href: "#install" },
        ]}
        secondaryCta={{
          label: "GitHub",
          href: "https://github.com/vickymuller-md/heartland-synthetic",
          external: true,
        }}
        cta={{
          label: "pip install",
          href: "https://pypi.org/project/heartland-synthetic/",
          external: true,
        }}
      />
      <main className="flex-1">
        <Hero />
        <section aria-labelledby="release-status" className="border-y border-grid bg-panel">
          <div className="mx-auto max-w-[1200px] px-6 py-12">
            <h2 id="release-status" className="font-editorial text-2xl font-semibold text-cool">Three versions, three different artifacts</h2>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-cool/75">
              Publication checked {RELEASE_CHECK_DATE} UTC. A package installation,
              a source archive and the preserved benchmark are distinct artifacts.
              Software changes do not replace the benchmark or establish clinical validation.
            </p>
            <dl className="mt-7 grid gap-4 md:grid-cols-3">
              {[
                ["Published package", `v${PUBLISHED_VERSION}`, "The pinned install command downloads this verified PyPI release, including the 0.3.x input and export checks."],
                ["Archived source", `v${PUBLISHED_VERSION}`, "The Zenodo software archive preserves the release source. It is not a new dataset or clinical-validation receipt."],
                ["Preserved benchmark", "dataset v1.0.0", "1,000 synthetic rows, seed 42. Original provenance cites the v0.2.1 archive; CSV unchanged."],
              ].map(([label, value, note]) => (
                <div key={label} className="min-w-0 rounded-2xl border border-grid bg-terminal p-6">
                  <dt className="text-sm text-cool/70">{label}</dt>
                  <dd className="mt-2 text-2xl font-semibold text-alert">{value}</dd>
                  <dd className="mt-3 text-sm leading-relaxed text-cool/75">{note}</dd>
                </div>
              ))}
            </dl>
            <a href="/dataset/" className="mt-6 inline-block text-sm text-cool underline underline-offset-4 hover:text-alert">View benchmark provenance and download CSV</a>
            <a href={SOFTWARE_ARCHIVE_DOI} className="mt-6 ml-0 block text-sm text-cool underline underline-offset-4 hover:text-alert md:ml-6 md:inline-block">View versioned software archive</a>
          </div>
        </section>
        <Abstract />
        <Features />
        <Install />
        <Evidence />
      </main>
      <Colophon
        currentSite="synthetic"
        version={`v${PUBLISHED_VERSION}`}
        description={SYNTHETIC_DESCRIPTION}
        legal={SYNTHETIC_BOUNDARY}
        extraBlocks={[
          {
            title: "Package",
            links: [
              { label: "PyPI", href: "https://pypi.org/project/heartland-synthetic/", external: true },
              { label: "GitHub", href: "https://github.com/vickymuller-md/heartland-synthetic", external: true },
              { label: "Changelog", href: "https://github.com/vickymuller-md/heartland-synthetic/blob/main/CHANGELOG.md", external: true },
              { label: "Software Heritage", href: "https://archive.softwareheritage.org/swh:1:snp:53d48ef3e36293ebabf274cb8db4b35cb55a30d7/", external: true },
            ],
          },
        ]}
      />
    </>
  );
}
