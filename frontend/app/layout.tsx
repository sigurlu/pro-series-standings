import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pro Series Standings",
  description:
    "2026 IRONMAN Pro Series standings with each athlete's ceiling — the most points they could still finish the season with.",
};

const REPO_URL = "https://github.com/sigurlu/ironman-pro-series-standings";
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
