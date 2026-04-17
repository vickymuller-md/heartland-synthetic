import type { Metadata } from "next";
import { Geist, Sora, Instrument_Serif } from "next/font/google";
import "@heartland/ui/css/theme.css";
import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-editorial",
  weight: ["200", "300", "400", "500", "600", "700", "800"],
  display: "swap",
});

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400"],
  style: ["normal", "italic"],
  display: "swap",
});

const soraMono = Sora({
  subsets: ["latin"],
  variable: "--font-mono-editorial",
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "heartland-synthetic — Synthetic HF cohorts with HEARTLAND risk variables",
  description:
    "Python package that generates clinically-realistic synthetic heart-failure patient cohorts including the 10 HEARTLAND risk variables — distance-to-cardiology and social support — that Synthea does not model.",
  metadataBase: new URL("https://synthetic.heartlandprotocol.org"),
  openGraph: {
    title: "heartland-synthetic",
    description:
      "Synthetic HF cohorts with the 10 HEARTLAND risk variables. MIT licensed, published on PyPI + Zenodo.",
    url: "https://synthetic.heartlandprotocol.org",
    siteName: "heartland-synthetic",
    locale: "en_US",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${geist.variable} ${sora.variable} ${instrumentSerif.variable} ${soraMono.variable} bg-terminal text-cool antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
