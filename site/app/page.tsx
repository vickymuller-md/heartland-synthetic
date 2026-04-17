import { Masthead, Colophon } from "@heartland/ui";
import { Abstract } from "@/components/landing/abstract";
import { Evidence } from "@/components/landing/evidence";
import { Features } from "@/components/landing/features";
import { Hero } from "@/components/landing/hero";
import { Install } from "@/components/landing/install";

export default function Home() {
  return (
    <>
      <Masthead
        currentSite="synthetic"
        version="v0.2.0"
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
        <Abstract />
        <Features />
        <Install />
        <Evidence />
      </main>
      <Colophon
        currentSite="synthetic"
        version="v0.2.0"
        description="Python package that generates clinically-realistic synthetic heart-failure patient cohorts including the 10 HEARTLAND risk variables — distance-to-cardiology and social support — that Synthea does not model."
        extraBlocks={[
          {
            title: "Package",
            links: [
              { label: "PyPI", href: "https://pypi.org/project/heartland-synthetic/", external: true },
              { label: "GitHub", href: "https://github.com/vickymuller-md/heartland-synthetic", external: true },
              { label: "Changelog", href: "https://github.com/vickymuller-md/heartland-synthetic/blob/main/CHANGELOG.md", external: true },
            ],
          },
        ]}
      />
    </>
  );
}
