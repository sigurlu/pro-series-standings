import type { Metadata } from "next";
import Link from "next/link";
import Script from "next/script";
import "./globals.css";

const SITE_URL = "https://www.improseries.com";
const SITE_DESCRIPTION =
  "2026 IRONMAN Pro Series standings with each athlete's ceiling — the most points they could still finish the season with.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Pro Series Standings",
    template: "%s · Pro Series Standings",
  },
  description: SITE_DESCRIPTION,
  keywords: [
    "IRONMAN Pro Series",
    "IRONMAN Pro Series standings",
    "triathlon standings 2026",
    "IRONMAN 70.3 pro rankings",
    "IRONMAN World Championship qualification",
  ],
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "Pro Series Standings",
    description: SITE_DESCRIPTION,
    url: "/",
    siteName: "Pro Series Standings",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Pro Series Standings",
    description: SITE_DESCRIPTION,
  },
  robots: {
    index: true,
    follow: true,
  },
};

// Runtime env var (no NEXT_PUBLIC_ prefix) so it's read per request on the
// server and changing it only needs a restart, not a rebuild. Unset -> no GA.
const GA_ID = process.env.GA_ID;

const REPO_URL = "https://github.com/sigurlu/pro-series-standings";
const AUTHOR = {
  name: "Sigurd Lund",
  url: "https://www.linkedin.com/in/sigurdlund/",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {GA_ID?.startsWith("G-") && (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
              strategy="afterInteractive"
            />
            <Script id="ga4" strategy="afterInteractive">
              {`window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${GA_ID}');`}
            </Script>
          </>
        )}
        <header className="site-header">
          <div className="inner">
            <Link href="/" className="brand">
              Pro Series Standings<span className="dot"> ·</span>
            </Link>
            <span className="season">2026</span>
          </div>
        </header>
        <main>{children}</main>
        <footer className="site-footer">
          <div className="inner">
            <p>
              Standings and results scraped from{" "}
              <a
                href="https://www.ironman.com/proseries/standings/2026"
                target="_blank"
                rel="noopener noreferrer"
              >
                ironman.com
              </a>
              . Not affiliated with, authorized, or endorsed by The IRONMAN
              Group.
            </p>
            <p>
              <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
                Source on GitHub
              </a>
              {" · "}
              Built by{" "}
              <a
                href={AUTHOR.url}
                target="_blank"
                rel="me noopener noreferrer"
              >
                {AUTHOR.name}
              </a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
