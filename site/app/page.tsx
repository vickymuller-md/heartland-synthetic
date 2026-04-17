import { Masthead, Colophon } from "@heartland/ui";
import { Abstract } from "@/components/landing/abstract";
import { Evidence } from "@/components/landing/evidence";
import { Features } from "@/components/landing/features";
import { Hero } from "@/components/landing/hero";
import { Install } from "@/components/landing/install";

export default function Home() {
  return (
    <main className="min-h-screen bg-terminal font-editorial text-cool">
      <Masthead
        currentSite="synthetic"
        navItems={[
          { label: "Features", href: "#features" },
          { label: "Install", href: "#install" },
        ]}
        cta={{
          label: "pip install",
          href: "https://pypi.org/project/heartland-synthetic/",
          external: true,
        }}
      />
      <Hero />
      <Abstract />
      <Features />
      <Install />
      <Evidence />
      <Colophon
        currentSite="synthetic"
        description="Python package that generates clinically-realistic synthetic heart-failure patient cohorts including the 10 HEARTLAND risk variables — distance-to-cardiology and social support — that Synthea does not model."
        extraBlocks={[
          {
            title: "Package",
            links: [
              {
                label: "PyPI",
                href: "https://pypi.org/project/heartland-synthetic/",
                external: true,
              },
              {
                label: "GitHub",
                href: "https://github.com/vickymuller-md/heartland-synthetic",
                external: true,
              },
              {
                label: "Changelog",
                href: "https://github.com/vickymuller-md/heartland-synthetic/blob/main/CHANGELOG.md",
                external: true,
              },
            ],
          },
        ]}
      />
    </main>
  );
}
