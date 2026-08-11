import type { Metadata, Viewport } from "next";
import { Fraunces } from "next/font/google";

import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";

/**
 * The display face.
 *
 * A serif in an operations dashboard is unusual on purpose. Every other console reaches
 * for a neutral grotesk, which is why they all look alike; a public-health bulletin has
 * more in common with a printed situation report than with a SaaS admin panel, and the
 * serif is what says so. Reserved for verdicts and figures, never for interface text.
 */
const display = Fraunces({
  subsets: ["latin"],
  weight: "variable",
  axes: ["SOFT", "WONK", "opsz"],
  variable: "--font-display",
  display: "swap",
});
import type { ReactNode } from "react";

import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClimaHealth Predict — Agency Command Platform",
  description:
    "Climate-driven health risk for Ghana: which districts are rising, why, and how long before cases appear.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fbfaf8" },
    { media: "(prefers-color-scheme: dark)", color: "#0c0e0d" },
  ],
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en-GB"
      suppressHydrationWarning
      className={`${GeistSans.variable} ${GeistMono.variable} ${display.variable}`}
    >
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
