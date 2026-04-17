import { Abstract } from "@/components/landing/abstract";
import { Colophon } from "@/components/landing/colophon";
import { Evidence } from "@/components/landing/evidence";
import { Features } from "@/components/landing/features";
import { Hero } from "@/components/landing/hero";
import { Install } from "@/components/landing/install";
import { Masthead } from "@/components/landing/masthead";

export default function Home() {
  return (
    <main className="min-h-screen bg-terminal font-editorial text-cool">
      <Masthead />
      <Hero />
      <Abstract />
      <Features />
      <Install />
      <Evidence />
      <Colophon />
    </main>
  );
}
