import type { Metadata } from "next";
import { Colophon, Masthead } from "@heartland/ui";

const SITE_URL = "https://synthetic.heartlandprotocol.org";
const DATASET_URL = `${SITE_URL}/dataset`;
const DOWNLOAD_PATH = "/data/heartland-synthetic-cohort-1000-seed42.csv";
const DOWNLOAD_URL = `${SITE_URL}${DOWNLOAD_PATH}`;
const GENERATOR_VERSION_DOI = "https://doi.org/10.5281/zenodo.22086443";
const GENERATOR_CONCEPT_DOI = "https://doi.org/10.5281/zenodo.19635042";
const TECHNICAL_REPORT_DOI = "https://doi.org/10.5281/zenodo.22137199";
const PROTOCOL_DOI = "https://doi.org/10.5281/zenodo.19101219";
const PYPI_URL = "https://pypi.org/project/heartland-synthetic/0.2.2/";
const HUGGING_FACE_URL =
  "https://huggingface.co/datasets/vickymuller-md/heartland-synthetic";
const RELEASE_URL =
  "https://github.com/vickymuller-md/heartland-synthetic/releases/tag/v0.2.2";

export const metadata: Metadata = {
  title: "HEARTLAND Synthetic HF Benchmark Cohort",
  description:
    "A reproducible 1,000-row synthetic heart-failure benchmark cohort generated with heartland-synthetic using seed 42. No real patient data or PHI.",
  alternates: { canonical: DATASET_URL },
  robots: { index: true, follow: true },
  openGraph: {
    title: "HEARTLAND Synthetic HF Benchmark Cohort",
    description:
      "Open 1,000-row synthetic heart-failure cohort with rural access, social support, GDMT, HEARTLAND risk variables, and modeled outcomes.",
    url: DATASET_URL,
    type: "website",
  },
};

const datasetStructuredData = {
  "@context": "https://schema.org",
  "@type": "Dataset",
  "@id": `${DATASET_URL}#dataset`,
  name: "HEARTLAND Synthetic Heart-Failure Benchmark Cohort",
  alternateName: "HEARTLAND Synthetic HF Cohort — 1,000 rows, seed 42",
  description:
    "Versioned, reproducible tabular benchmark dataset containing 1,000 entirely synthetic adult heart-failure records and 31 variables. It includes demographics, modeled rurality, heart-failure phenotype, vitals, comorbidities, distance to cardiology, social support, GDMT exposure, the unvalidated HEARTLAND risk score and tier, and modeled one-year outcomes. It was generated with heartland-synthetic using seed 42 and contains no real patient data, protected health information, or geo-accurate county identifiers. Modeled distributions and outcomes are not a substitute for clinical or registry data.",
  url: DATASET_URL,
  mainEntityOfPage: DATASET_URL,
  version: "1.0.0",
  datePublished: "2026-08-23",
  dateModified: "2026-08-26",
  inLanguage: "en",
  isAccessibleForFree: true,
  conditionsOfAccess:
    "Open access for research, education, reproducibility, and software testing. Not intended for clinical decision-making or patient care.",
  license: "https://opensource.org/license/mit",
  identifier: `${DATASET_URL}#dataset`,
  sameAs: [HUGGING_FACE_URL],
  keywords: [
    "synthetic health data",
    "heart failure",
    "rural health",
    "HEARTLAND risk score",
    "clinical simulation",
    "health equity",
    "FHIR",
    "REDCap",
  ],
  creator: {
    "@type": "Person",
    name: "Vicky Muller Ferreira, MD",
    givenName: "Vicky",
    familyName: "Muller Ferreira",
    sameAs: "https://orcid.org/0009-0009-1099-5690",
  },
  publisher: {
    "@type": "Organization",
    name: "HEARTLAND Protocol",
    url: "https://heartlandprotocol.org",
  },
  spatialCoverage: {
    "@type": "Place",
    name: "Modeled United States rural and urban settings; county identifiers are synthetic and not geographically accurate",
  },
  measurementTechnique: [
    "Deterministic pseudorandom cohort generation with seed 42",
    "Gaussian-copula sampling of continuous clinical variables",
    "Literature-anchored marginal distributions and tier-indexed modeled outcomes",
  ],
  variableMeasured: [
    "Demographics and modeled rurality",
    "Heart-failure phenotype and left ventricular ejection fraction",
    "Renal function, natriuretic peptide, vital signs, and body mass index",
    "Diabetes, atrial fibrillation, CKD stage, and CKM stage",
    "Distance to cardiology care and social support",
    "Guideline-directed medical therapy exposure",
    "HEARTLAND risk score and tier",
    "Modeled one-year mortality and hospitalization outcomes",
  ],
  isBasedOn: [GENERATOR_VERSION_DOI, RELEASE_URL, PYPI_URL],
  citation: [GENERATOR_CONCEPT_DOI, TECHNICAL_REPORT_DOI, PROTOCOL_DOI],
  distribution: [
    {
      "@type": "DataDownload",
      name: "HEARTLAND synthetic benchmark cohort — CSV",
      contentUrl: DOWNLOAD_URL,
      encodingFormat: "text/csv",
      contentSize: "110485 bytes",
      sha256:
        "8fbce909272274129f94db2b80b179b493e64fbc382a88515a851089b2edda8e",
    },
  ],
} as const;

const configuration = [
  ["Rows", "1,000"],
  ["Columns", "31"],
  ["Seed", "42"],
  ["Modeled rural fraction", "70%"],
  ["Age range", "45–95 years"],
  ["HF phenotype mix", "45% HFrEF · 15% HFmrEF · 40% HFpEF"],
  ["Generator archive", "heartland-synthetic v0.2.2"],
] as const;

export default function DatasetPage() {
  const structuredData = JSON.stringify(datasetStructuredData).replace(
    /</g,
    "\\u003c"
  );

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: structuredData }}
      />
      <Masthead
        currentSite="synthetic"
        version="dataset v1.0.0"
        navItems={[
          { label: "Provenance", href: "#provenance" },
          { label: "Limitations", href: "#limitations" },
        ]}
        secondaryCta={{
          label: "Zenodo",
          href: GENERATOR_VERSION_DOI,
          external: true,
        }}
        cta={{
          label: "Download CSV",
          href: DOWNLOAD_PATH,
          external: false,
        }}
      />

      <main className="flex-1">
        <section className="border-b border-grid bg-terminal">
          <div className="mx-auto max-w-[1000px] px-6 py-20 md:py-28">
            <p className="font-editorial text-[12.5px] uppercase tracking-[0.18em] text-alert">
              Open benchmark dataset · No PHI
            </p>
            <h1 className="mt-5 max-w-4xl font-editorial text-[clamp(2.4rem,5vw,4.5rem)] font-semibold leading-[1.04] tracking-[-0.025em] text-cool">
              HEARTLAND Synthetic HF{" "}
              <span className="font-display italic font-normal text-alert">
                Benchmark Cohort
              </span>
            </h1>
            <p className="mt-7 max-w-3xl font-editorial text-[17px] leading-[1.7] text-cool/75">
              A reproducible, 1,000-row synthetic heart-failure cohort for
              research, education, software testing, and interoperability
              demonstrations. Every row is generated; no real patient record,
              protected health information, or geo-accurate county identifier is
              included.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <a
                href={DOWNLOAD_PATH}
                download
                className="rounded-full bg-cool px-6 py-3 font-editorial text-[14px] font-medium text-terminal transition-colors hover:bg-alert hover:text-cool"
              >
                Download CSV · 108 KB
              </a>
              <a
                href={GENERATOR_VERSION_DOI}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-full border border-grid bg-panel px-6 py-3 font-editorial text-[14px] font-medium text-cool transition-colors hover:border-cool/40"
              >
                Generator v0.2.2 DOI ↗
              </a>
              <a
                href={TECHNICAL_REPORT_DOI}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-full border border-grid bg-panel px-6 py-3 font-editorial text-[14px] font-medium text-cool transition-colors hover:border-cool/40"
              >
                Technical report DOI ↗
              </a>
            </div>
          </div>
        </section>

        <section className="border-b border-grid bg-panel">
          <div className="mx-auto grid max-w-[1000px] gap-10 px-6 py-20 md:grid-cols-2 md:py-24">
            <div>
              <p className="font-editorial text-[12.5px] uppercase tracking-[0.18em] text-alert">
                Reproduction configuration
              </p>
              <dl className="mt-6 divide-y divide-grid border-y border-grid">
                {configuration.map(([label, value]) => (
                  <div
                    key={label}
                    className="flex items-baseline justify-between gap-6 py-3.5"
                  >
                    <dt className="font-editorial text-[13.5px] text-cool/65">
                      {label}
                    </dt>
                    <dd className="text-right font-mono text-[12.5px] text-cool">
                      {value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            <div>
              <p className="font-editorial text-[12.5px] uppercase tracking-[0.18em] text-alert">
                Included domains
              </p>
              <ul className="mt-6 space-y-3 font-editorial text-[14.5px] leading-relaxed text-cool/75">
                <li>Demographics, HF phenotype, vitals, and comorbidities</li>
                <li>Modeled rurality, distance to cardiology, and social support</li>
                <li>Four GDMT-class exposure indicators</li>
                <li>HEARTLAND score and low/moderate/high tier</li>
                <li>Modeled one-year mortality and hospitalization outcomes</li>
              </ul>
            </div>
          </div>
        </section>

        <section id="provenance" className="border-b border-grid bg-terminal">
          <div className="mx-auto max-w-[1000px] px-6 py-20 md:py-24">
            <p className="font-editorial text-[12.5px] uppercase tracking-[0.18em] text-alert">
              Provenance and integrity
            </p>
            <h2 className="mt-4 font-editorial text-3xl font-semibold text-cool">
              Deterministic generation, traceable source
            </h2>
            <div className="mt-6 grid gap-6 font-editorial text-[14.5px] leading-relaxed text-cool/75 md:grid-cols-2">
              <p>
                Reproducible with the archived heartland-synthetic v0.2.2
                release using the fixed seed and configuration shown above. The
                Zenodo DOI identifies the generator archive; it is cited as
                provenance and is not presented as a DOI minted specifically for
                this CSV.
              </p>
              <p>
                SHA-256: <code className="break-all font-mono text-[12px] text-cool">8fbce909272274129f94db2b80b179b493e64fbc382a88515a851089b2edda8e</code>
              </p>
            </div>
          </div>
        </section>

        <section id="limitations" className="bg-panel">
          <div className="mx-auto max-w-[1000px] px-6 py-20 md:py-24">
            <p className="font-editorial text-[12.5px] uppercase tracking-[0.18em] text-alert">
              Limitations
            </p>
            <h2 className="mt-4 font-editorial text-3xl font-semibold text-cool">
              Simulation data, not clinical evidence
            </h2>
            <ul className="mt-6 space-y-3 font-editorial text-[14.5px] leading-relaxed text-cool/75">
              <li>The dataset contains no real patients and cannot estimate population prevalence.</li>
              <li>County FIPS values are synthetic and are not geographically accurate.</li>
              <li>The HEARTLAND risk score is a proposed, unvalidated framework.</li>
              <li>Modeled outcomes are literature-consistent assumptions, not observed events.</li>
              <li>Do not use this dataset for diagnosis, treatment, prognosis, or patient care.</li>
            </ul>
          </div>
        </section>
      </main>

      <Colophon
        currentSite="synthetic"
        version="dataset v1.0.0"
        description="Open, reproducible synthetic heart-failure benchmark cohort. No real patient data or PHI."
        legal="Built by Vicky Muller Ferreira, MD. For research and educational use only. Synthetic data; no PHI. Not a medical device. Not for clinical decision-making or direct patient care."
        extraBlocks={[
          {
            title: "Dataset",
            links: [
              { label: "Download CSV", href: DOWNLOAD_PATH, external: false },
              { label: "Generator DOI", href: GENERATOR_VERSION_DOI, external: true },
              { label: "Technical report", href: TECHNICAL_REPORT_DOI, external: true },
              { label: "PyPI v0.2.2", href: PYPI_URL, external: true },
              { label: "Hugging Face", href: HUGGING_FACE_URL, external: true },
              { label: "GitHub release", href: RELEASE_URL, external: true },
              { label: "Software Heritage", href: "https://archive.softwareheritage.org/swh:1:snp:53d48ef3e36293ebabf274cb8db4b35cb55a30d7/", external: true },
            ],
          },
        ]}
      />
    </>
  );
}
