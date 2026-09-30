import type { Metadata } from "next";
import { Geist, Sora, Instrument_Serif } from "next/font/google";
import "@heartland/ui/css/theme.css";
import "./globals.css";
import { SYNTHETIC_DESCRIPTION } from "@/lib/release";

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
  description: SYNTHETIC_DESCRIPTION,
  metadataBase: new URL("https://synthetic.heartlandprotocol.org"),
  verification: {
    google: "KRMDAqi7exo5408R8MNrs3LGbdxohMbX-p7tEtaACCg",
  },
  openGraph: {
    title: "heartland-synthetic",
    description: SYNTHETIC_DESCRIPTION,
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
        className={`${geist.variable} ${sora.variable} ${instrumentSerif.variable} ${soraMono.variable} min-h-screen flex flex-col bg-terminal font-editorial text-cool antialiased selection:bg-alert/40 selection:text-cool`}
      >
        {children}
      </body>
    </html>
  );
}
